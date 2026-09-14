"""管理员路由（归属：后端 D）

前缀 /api/admin，所有接口都需 Depends(get_current_admin)。
功能：概览统计、帖子审核（列出/删除任意帖）、用户管理、评论删除。
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.admin import get_current_admin
from app.core.response import BizError, ok
from app.db import get_session
from app.models import Comment, Content, User

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def _content_to_dict(content: Content, author_name: str) -> dict:
    """管理员视角的帖子信息（与 post.py content_to_dict 结构一致，保持独立避免循环依赖）。"""
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


def _users_nickname_map(session: Session, ids: list[int]) -> dict:
    """批量 {id: nickname}，减少循环查库。"""
    ids = list(set(ids))
    if not ids:
        return {}
    rows = session.exec(select(User).where(User.id.in_(ids))).all()
    return {u.id: u.nickname for u in rows}


@router.get("/stats", summary="管理员概览统计")
def admin_stats(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """返回用户/帖子/评论总数及今日新增，供管理后台首页展示。"""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)

    total_users = session.exec(select(func.count()).select_from(User)).one()
    total_contents = session.exec(select(func.count()).select_from(Content)).one()
    total_comments = session.exec(select(func.count()).select_from(Comment)).one()
    today_new_users = session.exec(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    ).one()
    today_new_contents = session.exec(
        select(func.count()).select_from(Content).where(Content.created_at >= today_start)
    ).one()
    return ok({
        "total_users": total_users,
        "total_contents": total_contents,
        "total_comments": total_comments,
        "today_new_users": today_new_users,
        "today_new_contents": today_new_contents,
    })


@router.get("/contents", summary="帖子审核列表（分页）")
def admin_list_contents(
    page: int = 1,
    page_size: int = 20,
    type: Optional[str] = None,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """分页列出所有帖子（含他人帖），供管理员审核。可按 type 筛选。"""
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(Content)
    if type:
        stmt = stmt.where(Content.type == type)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    items = session.exec(
        stmt.order_by(Content.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    name_map = _users_nickname_map(session, [c.author_id for c in items])
    return ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [_content_to_dict(c, name_map.get(c.author_id, "未知用户")) for c in items],
    })


@router.delete("/contents/{content_id}", summary="删除任意帖子")
def admin_delete_content(
    content_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """管理员删除任意帖子，绕过作者校验。级联删除该帖下所有评论。"""
    content = session.get(Content, content_id)
    if content is None:
        raise BizError(2001, "内容不存在或已被删除")
    comments = session.exec(
        select(Comment).where(Comment.content_id == content.id)
    ).all()
    for c in comments:
        session.delete(c)
    session.delete(content)
    session.commit()
    return ok({"id": content_id, "deleted": True}, "管理员已删除该帖")
