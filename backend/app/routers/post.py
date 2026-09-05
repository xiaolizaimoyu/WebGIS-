"""内容业务模块（归属：后端 E）

只处理内容与评论：图片上传、内容发布/查询/详情、评论。
- 图片上传 /api/upload
- 内容     /api/contents
- 评论     /api/contents/{id}/comments
内容的发布类操作需要登录（Depends(get_current_user)），浏览类不需要。
"""
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.core.config import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE, UPLOAD_DIR
from app.core.response import BizError, ok
from app.core.security import get_current_user
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
CATEGORY_RULES = {
    "ad": ["闲置", "求助", "宣传"],
    "food": ["食堂推荐", "小吃外卖", "零食饮品"],
    "lost": ["寻物启事", "失主招领"],
}


def _normalize_category(content_type: str, category: Optional[str]) -> Optional[str]:
    """子分类规整与校验：去空白；无子分类的类型清空；有白名单的类型校验合法性。"""
    category = (category or "").strip()
    allowed = CATEGORY_RULES.get(content_type)
    if allowed is None:
        return None
    if not category:
        return None
    if category not in allowed:
        raise BizError(2004, f"子分类 category 不合法，{content_type} 仅支持：{' / '.join(allowed)}")
    return category


def _normalize_location(longitude: Optional[float], latitude: Optional[float]):
    """经纬度成对校验：只传一个视为参数错误；都不传返回 (None, None)。"""
    if longitude is None and latitude is None:
        return None, None
    if longitude is None or latitude is None:
        raise BizError(400, "经纬度需成对提交（longitude 与 latitude 同时传或同时不传）")
    return longitude, latitude


def _ensure_valid_type(content_type: str) -> None:
    """type 合法性校验（创建 / 编辑共用）。"""
    if content_type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")


# ---------- 序列化辅助 ----------
def content_to_dict(content: Content, author_name: str, comment_count: int = 0) -> dict:
    return {
        "id": content.id,
        "title": content.title,
        "body": content.body,
        "type": content.type,
        "category": content.category,
        "images": content.images or [],
        # WebGIS：帖子绑定的地理位置，供前端地图渲染点位
        "longitude": content.longitude,
        "latitude": content.latitude,
        "author_id": content.author_id,
        "author_name": author_name,
        "comment_count": comment_count,
        "created_at": content.created_at,
    }


def comment_to_dict(comment: Comment, author_name: str) -> dict:
    return {
        "id": comment.id,
        "content_id": comment.content_id,
        "author_id": comment.author_id,
        "author_name": author_name,
        "body": comment.body,
        "created_at": comment.created_at,
    }


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


# ---------- 图片上传 ----------
@router.post("/upload", summary="上传图片（需登录）")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BizError(400, "仅支持 jpg / jpeg / png / gif 格式图片")
    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise BizError(400, "图片不能超过 5MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    return ok({"url": f"/uploads/{filename}"})


# ---------- 内容 ----------
@router.post("/contents", summary="发布内容（需登录）")
def create_content(
    data: ContentIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _ensure_valid_type(data.type)
    longitude, latitude = _normalize_location(data.longitude, data.latitude)
    category = _normalize_category(data.type, data.category)
    content = Content(
        title=data.title,
        body=data.body,
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
    return ok(content_to_dict(content, user.nickname), "发布成功")


@router.get("/contents", summary="内容列表（首页信息流 / 地图点位 / 搜索）")
def list_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    keyword: Optional[str] = Query(default=None, max_length=50, description="关键词搜索：匹配标题或正文，不传为不搜索"),
    sort: str = Query(default="latest", description="排序：latest(默认,按时间倒序) | hot(按评论数降序)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    has_location: bool = Query(default=False, description="WebGIS：仅返回绑定了经纬度的内容（地图点位用）"),
    session: Session = Depends(get_session),
):
    if type is not None and type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")
    if sort not in ("latest", "hot"):
        raise BizError(400, "排序参数 sort 仅支持：latest | hot")

    filters = [Content.type == type] if type else []
    keyword = (keyword or "").strip()
    if keyword:
        filters.append(or_(Content.title.contains(keyword), Content.body.contains(keyword)))
    if has_location:
        # 地图只渲染拾取过地理位置的帖子
        filters.append(Content.longitude.is_not(None))
        filters.append(Content.latitude.is_not(None))
    total = session.exec(select(func.count(Content.id)).where(*filters)).one()
    if sort == "hot":
        # 热门排序：先按评论数降序，再按时间降序稳定排
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
        # 热门排序时 comment_count 从子查询已拿到，直接用
        hot_counts = {r[0].id: r[1] for r in rows}
    else:
        stmt = (
            select(Content)
            .where(*filters)
            .order_by(Content.created_at.desc(), Content.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = session.exec(stmt).all()
        hot_counts = None
    name_map = users_nickname_map(session, [c.author_id for c in items])
    count_map = comments_count_map(session, [c.id for c in items])
    return ok({
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [
            content_to_dict(
                c,
                name_map.get(c.author_id, "未知用户"),
                hot_counts.get(c.id, count_map.get(c.id, 0)) if hot_counts else count_map.get(c.id, 0),
            )
            for c in items
        ],
    })


@router.get("/contents/mine", summary="我的发布列表（需登录）")
def list_my_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """当前登录用户发布的内容，按时间倒序。

    注意：/contents/mine 必须声明在 /contents/{content_id} 之前，
    否则 "mine" 会被当成 id 解析而报 422。
    """
    if type is not None and type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")

    filters = [Content.author_id == user.id]
    if type:
        filters.append(Content.type == type)
    total = session.exec(
        select(func.count(Content.id)).where(*filters)
    ).one()
    stmt = (
        select(Content)
        .where(*filters)
        .order_by(Content.created_at.desc(), Content.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = session.exec(stmt).all()
    count_map = comments_count_map(session, [c.id for c in items])
    return ok({
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [content_to_dict(c, user.nickname, count_map.get(c.id, 0)) for c in items],
    })


@router.get("/contents/stats", summary="内容统计（按分类汇总）")
def content_stats(session: Session = Depends(get_session)):
    """返回各分类的内容数量，供首页仪表盘 / 分类导航使用。"""
    rows = session.exec(
        select(Content.type, func.count(Content.id)).group_by(Content.type)
    ).all()
    by_type = {t: 0 for t in sorted(VALID_TYPES)}
    total = 0
    for t, c in rows:
        by_type[t] = c
        total += c
    return ok({"total": total, "by_type": by_type})


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
    _ensure_valid_type(data.type)
    longitude, latitude = _normalize_location(data.longitude, data.latitude)
    content.title = data.title
    content.body = data.body
    content.type = data.type
    content.category = _normalize_category(data.type, data.category)
    content.images = data.images
    content.longitude = longitude
    content.latitude = latitude
    session.add(content)
    session.commit()
    session.refresh(content)
    return ok(content_to_dict(content, user.nickname), "修改成功")


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
    # 连带删除该内容下的所有评论，避免留下孤儿评论
    comments = session.exec(select(Comment).where(Comment.content_id == content.id)).all()
    for c in comments:
        session.delete(c)
    session.delete(content)
    session.commit()
    return ok({"id": content_id, "deleted": True}, "删除成功")


@router.get("/contents/{content_id}", summary="内容详情")
def get_content(content_id: int, session: Session = Depends(get_session)):
    content = session.get(Content, content_id)
    if content is None:
        raise BizError(2001, "内容不存在或已被删除")
    author = session.get(User, content.author_id)
    comment_count = session.exec(
        select(func.count(Comment.id)).where(Comment.content_id == content.id)
    ).one()
    return ok(content_to_dict(content, author.nickname if author else "未知用户", comment_count))


# ---------- 评论 ----------
@router.get("/contents/{content_id}/comments", summary="评论列表")
def list_comments(content_id: int, session: Session = Depends(get_session)):
    if session.get(Content, content_id) is None:
        raise BizError(2001, "内容不存在或已被删除")
    rows = session.exec(
        select(Comment)
        .where(Comment.content_id == content_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    ).all()
    name_map = users_nickname_map(session, [c.author_id for c in rows])
    return ok([comment_to_dict(c, name_map.get(c.author_id, "未知用户")) for c in rows])


@router.post("/contents/{content_id}/comments", summary="发表评论（需登录）")
def create_comment(
    content_id: int,
    data: CommentIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if session.get(Content, content_id) is None:
        raise BizError(2001, "内容不存在或已被删除")
    comment = Comment(content_id=content_id, author_id=user.id, body=data.body)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return ok(comment_to_dict(comment, user.nickname), "评论成功")


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
