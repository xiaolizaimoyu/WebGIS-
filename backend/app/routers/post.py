"""内容业务模块（归属：后端 E）

只处理内容与评论：图片上传、内容发布/查询/详情、评论。
- 图片上传 /api/upload
- 内容     /api/contents
- 评论     /api/contents/{id}/comments
内容的发布类操作需要登录（Depends(get_current_user)），浏览类不需要。
"""
import html
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy import func, or_, text
from sqlmodel import Session, select

from app.core.config import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE, UPLOAD_DIR
from app.core.response import BizError, ok
from app.core.security import decode_token, get_current_user
from app.db import get_session
from app.models import Comment, Content, User
from app.schemas import CommentIn, ContentIn

router = APIRouter(prefix="/api", tags=["内容与评论"])

# 内容一级分类，见 docs/API.md
# WebGIS 新增 food（美食分享）/ lost（失物招领）
VALID_TYPES = {"activity", "meeting", "news", "ad", "food", "lost"}

# 各一级分类允许的二级子分类（category）。
# - 表中没有的类型（activity/meeting/news）不支持子分类，提交时统一清空；
# - 表中的类型 category 可空；非空时必须命中白名单，保证地图/列表筛选数据规范。
# 值用 set 是为了 O(1) 成员判断；错误提示时再排序输出。
CATEGORY_RULES = {
    "ad": {"闲置", "求助", "宣传"},
    "food": {"食堂推荐", "小吃外卖", "零食饮品"},
    "lost": {"寻物启事", "失主招领"},
}

# 列表排序与评论排序的合法取值（模块常量，避免散落的魔法字符串）
SORT_OPTIONS = ("latest", "hot")
COMMENT_ORDER_OPTIONS = ("asc", "desc")
# 列表卡片摘要长度（正文截取前 N 字 + "..."）
SUMMARY_LENGTH = 100


def _normalize_category(content_type: str, category: Optional[str]) -> Optional[str]:
    """子分类规整与校验：去空白；无子分类的类型清空；有白名单的类型校验合法性。"""
    category = (category or "").strip()
    allowed = CATEGORY_RULES.get(content_type)
    if allowed is None:
        return None
    if not category:
        return None
    if category not in allowed:
        raise BizError(2004, f"子分类 category 不合法，{content_type} 仅支持：{' / '.join(sorted(allowed))}")
    return category


def _normalize_location(longitude: Optional[float], latitude: Optional[float]) -> tuple:
    """经纬度成对校验：只传一个视为参数错误；都不传返回 (None, None)。"""
    if longitude is None and latitude is None:
        return None, None
    if longitude is None or latitude is None:
        raise BizError(400, "经纬度需成对提交（longitude 与 latitude 同时传或同时不传）")
    return longitude, latitude


def _validate_optional_type(content_type: Optional[str]) -> None:
    """type 校验：None 不校验（列表筛选用），非空则必须合法（创建/编辑用）。"""
    if content_type is not None and content_type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")


def _add_keyword_filter(filters: list, keyword: Optional[str]) -> None:
    """关键词搜索：去空白后匹配标题或正文，list_contents 与 list_my_contents 共用。"""
    keyword = (keyword or "").strip()
    if keyword:
        filters.append(or_(Content.title.contains(keyword), Content.body.contains(keyword)))


def _clean_text(value: str, field_name: str) -> str:
    """去首尾空白、拒绝纯空白、转义 HTML 特殊字符（防存储型 XSS）。标题 / 正文 / 评论共用。"""
    value = value.strip()
    if not value:
        raise BizError(400, f"{field_name}不能为空白")
    return html.escape(value)


def _get_optional_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    """FastAPI 依赖：从 Authorization 头尝试解析用户，未登录或 token 无效返回 None（不报错）。"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        user_id = decode_token(auth.removeprefix("Bearer ").strip())
        return session.get(User, user_id)
    except BizError:
        return None


# ---------- 序列化辅助 ----------
def content_to_dict(content: Content, author_name: str, comment_count: int = 0, is_author: Optional[bool] = None) -> dict:
    body = content.body or ""
    # 摘要：正文前 SUMMARY_LENGTH 字，列表卡片展示用，正文原样保留在 body 字段
    summary = body[:SUMMARY_LENGTH] + ("..." if len(body) > SUMMARY_LENGTH else "")
    d = {
        "id": content.id,
        "title": content.title,
        "body": body,
        "summary": summary,
        "type": content.type,
        "category": content.category,
        "images": content.images or [],
        # WebGIS：帖子绑定的地理位置，供前端地图渲染点位
        "longitude": content.longitude,
        "latitude": content.latitude,
        "author_id": content.author_id,
        "author_name": author_name,
        "comment_count": comment_count,
        "view_count": content.view_count,
        "created_at": content.created_at,
    }
    # 详情接口可选鉴权时传入，前端据此决定是否显示编辑/删除按钮
    if is_author is not None:
        d["is_author"] = is_author
    return d


def comment_to_dict(comment: Comment, author_name: str, is_author: Optional[bool] = None) -> dict:
    d = {
        "id": comment.id,
        "content_id": comment.content_id,
        "author_id": comment.author_id,
        "author_name": author_name,
        "body": comment.body,
        "created_at": comment.created_at,
    }
    # 评论列表可选鉴权时传入，前端据此显示删除按钮
    if is_author is not None:
        d["is_author"] = is_author
    return d


def users_nickname_map(session: Session, ids: List[int]) -> dict:
    """根据多个用户 id 批量查出 {id: nickname}，减少循环查库。"""
    ids = list(set(ids))
    if not ids:
        return {}
    rows = session.exec(select(User).where(User.id.in_(ids))).all()
    return {u.id: u.nickname for u in rows}


def comments_count_map(session: Session, content_ids: List[int]) -> dict:
    """按内容 id 批量统计评论数，返回 {content_id: comment_count}。"""
    ids = list(set(content_ids))
    if not ids:
        return {}
    rows = session.exec(
        select(Comment.content_id, func.count(Comment.id))
        .where(Comment.content_id.in_(ids))
        .group_by(Comment.content_id)
    ).all()
    return {content_id: count for content_id, count in rows}


def _query_contents_page(
    session: Session,
    filters: list,
    sort: str,
    page: int,
    size: int,
) -> tuple:
    """内容分页查询公共逻辑：返回 (items, count_map, total)。

    - sort=hot：子查询带回评论数，一次拿到排序依据和展示数据；
    - sort=latest：普通查询 + 批量统计评论数。
    list_contents 与 list_my_contents 共用，避免分页/排序/计数逻辑重复。
    """
    if sort not in SORT_OPTIONS:
        sort = "latest"  # 防御性兜底，调用方已校验，这里保证函数本身健壮
    total = session.exec(select(func.count(Content.id)).where(*filters)).one()
    if sort == "hot":
        count_sub = (
            select(Comment.content_id, func.count(Comment.id).label("cc"))
            .group_by(Comment.content_id)
            .subquery()
        )
        stmt = (
            select(Content, func.coalesce(count_sub.c.cc, 0).label("comment_count"))
            .outerjoin(count_sub, count_sub.c.content_id == Content.id)
            .where(*filters)
            .order_by(func.coalesce(count_sub.c.cc, 0).desc(), Content.created_at.desc(), Content.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = session.exec(stmt).all()
        items = [r[0] for r in rows]
        count_map = {r[0].id: r[1] for r in rows}
    else:
        stmt = (
            select(Content)
            .where(*filters)
            .order_by(Content.created_at.desc(), Content.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = session.exec(stmt).all()
        count_map = comments_count_map(session, [c.id for c in items])
    return items, count_map, total


# ---------- 图片上传 ----------
@router.post("/upload", summary="上传图片（需登录）")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BizError(400, "仅支持 jpg / jpeg / png / gif 格式图片")
    # 先用 file.size 预检，避免读取超大文件浪费内存
    if file.size is not None and file.size > MAX_IMAGE_SIZE:
        raise BizError(400, "图片不能超过 5MB")
    data = await file.read()
    await file.close()
    if len(data) > MAX_IMAGE_SIZE:
        raise BizError(400, "图片不能超过 5MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    return ok({"url": f"/uploads/{filename}", "size": len(data)})


# ---------- 内容 ----------
@router.post("/contents", summary="发布内容（需登录）")
def create_content(
    data: ContentIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _validate_optional_type(data.type)
    longitude, latitude = _normalize_location(data.longitude, data.latitude)
    category = _normalize_category(data.type, data.category)
    content = Content(
        title=_clean_text(data.title, "标题"),
        body=_clean_text(data.body, "正文"),
        type=data.type,
        category=category,
        images=data.images,
        longitude=longitude,
        latitude=latitude,
        author_id=user.id,
    )
    session.add(content)
    session.commit()
    session.refresh(content)
    return ok(content_to_dict(content, user.nickname, is_author=True), "发布成功")


@router.get("/contents", summary="内容列表（首页信息流 / 地图点位 / 搜索）")
def list_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    keyword: Optional[str] = Query(default=None, max_length=50, description="关键词搜索：匹配标题或正文，不传为不搜索"),
    sort: str = Query(default="latest", description="排序：latest(默认,按时间倒序) | hot(按评论数降序)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    has_location: bool = Query(default=False, description="WebGIS：仅返回绑定了经纬度的内容（地图点位用）"),
    author_id: Optional[int] = Query(default=None, description="按作者 id 筛选，不传为全部"),
    category: Optional[str] = Query(default=None, max_length=20, description="按二级子分类筛选，如 食堂推荐"),
    min_view_count: Optional[int] = Query(default=None, ge=0, description="按浏览量下限筛选，只返回热度不低于该值的内容"),
    session: Session = Depends(get_session),
):
    _validate_optional_type(type)
    if sort not in SORT_OPTIONS:
        raise BizError(400, f"排序参数 sort 仅支持：{' | '.join(SORT_OPTIONS)}")

    filters = [Content.type == type] if type else []
    if author_id is not None:
        filters.append(Content.author_id == author_id)
    if category:
        filters.append(Content.category == category)
    if min_view_count is not None:
        filters.append(Content.view_count >= min_view_count)
    _add_keyword_filter(filters, keyword)
    if has_location:
        # 地图只渲染拾取过地理位置的帖子，经纬度必然成对（创建时已校验），用一个条件即可
        filters.append(Content.latitude.is_not(None))
    items, count_map, total = _query_contents_page(session, filters, sort, page, size)
    name_map = users_nickname_map(session, [c.author_id for c in items])
    return ok({
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [
            content_to_dict(
                c,
                name_map.get(c.author_id, "未知用户"),
                count_map.get(c.id, 0),
            )
            for c in items
        ],
    })


@router.get("/contents/mine", summary="我的发布列表（需登录）")
def list_my_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    keyword: Optional[str] = Query(default=None, max_length=50, description="关键词搜索：匹配标题或正文，不传为不搜索"),
    sort: str = Query(default="latest", description="排序：latest(默认) | hot(按评论数降序)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """当前登录用户发布的内容，按时间倒序。

    注意：/contents/mine 必须声明在 /contents/{content_id} 之前，
    否则 "mine" 会被当成 id 解析而报 422。
    """
    _validate_optional_type(type)
    if sort not in SORT_OPTIONS:
        raise BizError(400, f"排序参数 sort 仅支持：{' | '.join(SORT_OPTIONS)}")

    filters = [Content.author_id == user.id]
    if type:
        filters.append(Content.type == type)
    _add_keyword_filter(filters, keyword)
    items, count_map, total = _query_contents_page(session, filters, sort, page, size)
    return ok({
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [content_to_dict(c, user.nickname, count_map.get(c.id, 0), True) for c in items],
    })


@router.get("/contents/stats", summary="内容统计（按分类汇总）")
def content_stats(session: Session = Depends(get_session)):
    """返回各分类的内容数量与全站评论总数，供首页仪表盘 / 分类导航使用。"""
    rows = session.exec(
        select(Content.type, func.count(Content.id)).group_by(Content.type)
    ).all()
    by_type = {t: 0 for t in sorted(VALID_TYPES)}
    for t, c in rows:
        by_type[t] = c
    total = sum(by_type.values())
    comment_total = session.exec(select(func.count(Comment.id))).one()
    return ok({"total": total, "comment_total": comment_total, "by_type": by_type})


@router.put("/contents/{content_id}", summary="编辑自己发布的内容（需登录）")
def update_content(
    content_id: int,
    data: ContentIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    content = session.get(Content, content_id)
    if content is None:
        raise BizError(2001, "内容不存在或已被删除")
    if content.author_id != user.id:
        raise BizError(2003, "只能编辑自己发布的内容")
    _validate_optional_type(data.type)
    longitude, latitude = _normalize_location(data.longitude, data.latitude)
    content.title = _clean_text(data.title, "标题")
    content.body = _clean_text(data.body, "正文")
    content.type = data.type
    content.category = _normalize_category(data.type, data.category)
    content.images = data.images
    content.longitude = longitude
    content.latitude = latitude
    session.add(content)
    session.commit()
    session.refresh(content)
    return ok(content_to_dict(content, user.nickname, is_author=True), "修改成功")


@router.delete("/contents/{content_id}", summary="删除自己发布的内容（需登录）")
def delete_content(
    content_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    content = session.get(Content, content_id)
    if content is None:
        raise BizError(2001, "内容不存在或已被删除")
    if content.author_id != user.id:
        raise BizError(2003, "只能删除自己发布的内容")
    # 清理该内容上传的图片文件，避免磁盘残留
    for img_url in (content.images or []):
        if img_url.startswith("/uploads/"):
            img_path = UPLOAD_DIR / Path(img_url).name
            if img_path.exists():
                try:
                    img_path.unlink()
                except OSError:
                    pass  # 文件清理失败不阻塞删除流程
    # 批量删除该内容下的所有评论，避免逐条 ORM delete 的 N+1 问题
    session.execute(
        text("DELETE FROM comments WHERE content_id = :cid"),
        {"cid": content.id},
    )
    session.delete(content)
    session.commit()
    return ok({"id": content_id, "deleted": True}, "删除成功")


@router.get("/contents/{content_id}", summary="内容详情")
def get_content(
    content_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    content = session.get(Content, content_id)
    if content is None:
        raise BizError(2001, "内容不存在或已被删除")
    # 浏览量自增（直接 SQL 更新保证原子性，避免 ORM 乐观锁冲突）。
    # commit 后对象会过期，直接在内存设置已知新值，省一次 refresh 查询。
    current_view = content.view_count or 0
    session.execute(
        text("UPDATE contents SET view_count = view_count + 1 WHERE id = :cid"),
        {"cid": content_id},
    )
    session.commit()
    content.view_count = current_view + 1
    author = session.get(User, content.author_id)
    comment_count = session.exec(
        select(func.count(Comment.id)).where(Comment.content_id == content.id)
    ).one()
    # 可选鉴权：已登录时返回 is_author，前端据此显示编辑/删除按钮
    is_author = content.author_id == current_user.id if current_user is not None else None
    return ok(content_to_dict(content, author.nickname if author else "未知用户", comment_count, is_author))


# ---------- 评论 ----------
@router.get("/contents/{content_id}/comments", summary="评论列表（分页）")
def list_comments(
    content_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="asc", description="asc(默认,时间正序) | desc(时间倒序,最新在前)"),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(_get_optional_user),
):
    if session.get(Content, content_id) is None:
        raise BizError(2001, "内容不存在或已被删除")
    if order not in COMMENT_ORDER_OPTIONS:
        raise BizError(400, f"排序参数 order 仅支持：{' | '.join(COMMENT_ORDER_OPTIONS)}")
    total = session.exec(
        select(func.count(Comment.id)).where(Comment.content_id == content_id)
    ).one()
    order_clause = Comment.created_at.desc() if order == "desc" else Comment.created_at.asc()
    id_clause = Comment.id.desc() if order == "desc" else Comment.id.asc()
    rows = session.exec(
        select(Comment)
        .where(Comment.content_id == content_id)
        .order_by(order_clause, id_clause)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    name_map = users_nickname_map(session, [c.author_id for c in rows])
    # 可选鉴权：已登录时每条评论附带 is_author，前端据此显示删除按钮
    return ok({
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [
            comment_to_dict(
                c,
                name_map.get(c.author_id, "未知用户"),
                c.author_id == current_user.id if current_user is not None else None,
            )
            for c in rows
        ],
    })


@router.post("/contents/{content_id}/comments", summary="发表评论（需登录）")
def create_comment(
    content_id: int,
    data: CommentIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if session.get(Content, content_id) is None:
        raise BizError(2001, "内容不存在或已被删除")
    comment = Comment(content_id=content_id, author_id=user.id, body=_clean_text(data.body, "评论内容"))
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return ok(comment_to_dict(comment, user.nickname, is_author=True), "评论成功")


@router.delete("/contents/{content_id}/comments/{comment_id}", summary="删除评论（需登录）")
def delete_comment(
    content_id: int,
    comment_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """删除自己的评论；非作者返回 2003；评论或内容不存在返回 2001。"""
    if session.get(Content, content_id) is None:
        raise BizError(2001, "内容不存在或已被删除")
    comment = session.get(Comment, comment_id)
    if comment is None or comment.content_id != content_id:
        raise BizError(2001, "评论不存在或已被删除")
    if comment.author_id != user.id:
        raise BizError(2003, "只能删除自己发表的评论")
    session.delete(comment)
    session.commit()
    return ok({"id": comment_id, "deleted": True}, "删除成功")
