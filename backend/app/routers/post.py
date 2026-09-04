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
from sqlalchemy import func
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
def content_to_dict(content: Content, author_name: str) -> dict:
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
    content = Content(
        title=data.title,
        body=data.body,
        type=data.type,
        category=data.category,
        images=data.images,
        longitude=longitude,
        latitude=latitude,
        author_id=user.id,
    )
    session.add(content)
    session.commit()
    session.refresh(content)
    return ok(content_to_dict(content, user.nickname), "发布成功")


@router.get("/contents", summary="内容列表（首页信息流 / 地图点位）")
def list_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    has_location: bool = Query(default=False, description="WebGIS：仅返回绑定了经纬度的内容（地图点位用）"),
    session: Session = Depends(get_session),
):
    if type is not None and type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")

    filters = [Content.type == type] if type else []
    if has_location:
        # 地图只渲染拾取过地理位置的帖子
        filters.append(Content.longitude.is_not(None))
        filters.append(Content.latitude.is_not(None))
    total = session.exec(select(func.count(Content.id)).where(*filters)).one()
    stmt = (
        select(Content)
        .where(*filters)
        .order_by(Content.created_at.desc(), Content.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = session.exec(stmt).all()
    name_map = users_nickname_map(session, [c.author_id for c in items])
    return ok({
        "total": total,
        "items": [content_to_dict(c, name_map.get(c.author_id, "未知用户")) for c in items],
    })


@router.get("/contents/mine", summary="我的发布列表（需登录）")
def list_my_contents(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """当前登录用户发布的内容，按时间倒序。

    注意：/contents/mine 必须声明在 /contents/{content_id} 之前，
    否则 "mine" 会被当成 id 解析而报 422。
    """
    total = session.exec(
        select(func.count(Content.id)).where(Content.author_id == user.id)
    ).one()
    stmt = (
        select(Content)
        .where(Content.author_id == user.id)
        .order_by(Content.created_at.desc(), Content.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = session.exec(stmt).all()
    return ok({
        "total": total,
        "items": [content_to_dict(c, user.nickname) for c in items],
    })


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
    content.category = data.category
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
    return ok(content_to_dict(content, author.nickname if author else "未知用户"))


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
