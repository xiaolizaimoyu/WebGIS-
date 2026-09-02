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
VALID_TYPES = {"activity", "meeting", "news", "ad"}


# ---------- 序列化辅助 ----------
def content_to_dict(content: Content, author_name: str) -> dict:
    return {
        "id": content.id,
        "title": content.title,
        "body": content.body,
        "type": content.type,
        "category": content.category,
        "images": content.images or [],
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
    if data.type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")
    content = Content(
        title=data.title,
        body=data.body,
        type=data.type,
        category=data.category,
        images=data.images,
        author_id=user.id,
    )
    session.add(content)
    session.commit()
    session.refresh(content)
    return ok(content_to_dict(content, user.nickname), "发布成功")


@router.get("/contents", summary="内容列表（首页信息流）")
def list_contents(
    type: Optional[str] = Query(default=None, description="按 type 筛选，不传为全部"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
):
    if type is not None and type not in VALID_TYPES:
        raise BizError(2002, f"分类 type 不合法，仅支持：{' / '.join(sorted(VALID_TYPES))}")

    filters = [Content.type == type] if type else []
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
