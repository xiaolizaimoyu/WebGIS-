"""互动模块路由（点赞 / 收藏 / 关注）

归属：后端 F 扩展。提供基础 CRUD + 业务动作（点赞/取消点赞等）。
前缀：/api/social
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.response import BizError, ok
from app.core.security import get_current_user
from app.db import get_session
from app.models import Content, Favorite, Follow, Like, User

router = APIRouter(prefix="/api/social", tags=["互动模块"])


# ==================== 点赞 ====================

@router.post("/likes/{content_id}", summary="点赞或取消点赞（切换）")
def toggle_like(content_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """用户对内容点赞/取消点赞。已点赞则取消，未点赞则点赞。"""
    content = session.get(Content, content_id)
    if not content:
        raise BizError(404, "内容不存在")

    existing = session.exec(
        select(Like).where(Like.user_id == user.id, Like.content_id == content_id)
    ).first()

    if existing:
        session.delete(existing)
        content.like_count = max(0, content.like_count - 1)
        session.add(content)
        session.commit()
        return ok({"liked": False, "like_count": content.like_count})
    else:
        like = Like(user_id=user.id, content_id=content_id)
        session.add(like)
        content.like_count = content.like_count + 1
        session.add(content)
        session.commit()
        return ok({"liked": True, "like_count": content.like_count})


@router.get("/likes/check/{content_id}", summary="检查当前用户是否点赞了某内容")
def check_like(content_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(
        select(Like).where(Like.user_id == user.id, Like.content_id == content_id)
    ).first()
    return ok({"liked": existing is not None})


@router.get("/likes/mine", summary="我点赞的内容列表")
def my_likes(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
             user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(Like).where(Like.user_id == user.id).order_by(Like.created_at.desc())
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    # 关联内容详情，供"我的点赞"页直接展示
    content_ids = [l.content_id for l in items]
    content_map = {}
    if content_ids:
        for c0 in session.exec(select(Content).where(Content.id.in_(content_ids))).all():
            content_map[c0.id] = c0
    result = []
    for l in items:
        c0 = content_map.get(l.content_id)
        if c0:
            result.append({"id": c0.id, "title": c0.title, "type": c0.type,
                           "summary": (c0.body or "")[:60],
                           "created_at": l.created_at.isoformat()})
    return ok({"total": total, "page": page, "size": size, "items": result})


# ==================== 收藏 ====================

@router.post("/favorites/{content_id}", summary="收藏或取消收藏（切换）")
def toggle_favorite(content_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    content = session.get(Content, content_id)
    if not content:
        raise BizError(404, "内容不存在")

    existing = session.exec(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.content_id == content_id)
    ).first()

    if existing:
        session.delete(existing)
        session.commit()
        return ok({"favorited": False})
    else:
        fav = Favorite(user_id=user.id, content_id=content_id)
        session.add(fav)
        session.commit()
        return ok({"favorited": True})


@router.get("/favorites/check/{content_id}", summary="检查是否收藏")
def check_favorite(content_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.content_id == content_id)
    ).first()
    return ok({"favorited": existing is not None})


@router.get("/favorites/mine", summary="我的收藏列表")
def my_favorites(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
                 user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    # 关联内容详情，供"我的收藏"页直接展示
    content_ids = [f.content_id for f in items]
    content_map = {}
    if content_ids:
        for c0 in session.exec(select(Content).where(Content.id.in_(content_ids))).all():
            content_map[c0.id] = c0
    result = []
    for f in items:
        c0 = content_map.get(f.content_id)
        if c0:
            result.append({"id": c0.id, "title": c0.title, "type": c0.type,
                           "summary": (c0.body or "")[:60],
                           "created_at": f.created_at.isoformat()})
    return ok({"total": total, "page": page, "size": size, "items": result})


# ==================== 关注 ====================

@router.post("/follows/{user_id}", summary="关注或取消关注用户（切换）")
def toggle_follow(user_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if user_id == user.id:
        raise BizError(400, "不能关注自己")
    target = session.get(User, user_id)
    if not target:
        raise BizError(404, "用户不存在")

    existing = session.exec(
        select(Follow).where(Follow.follower_id == user.id, Follow.following_id == user_id)
    ).first()

    if existing:
        session.delete(existing)
        session.commit()
        return ok({"following": False})
    else:
        follow = Follow(follower_id=user.id, following_id=user_id)
        session.add(follow)
        session.commit()
        return ok({"following": True})


@router.get("/follows/followers/{user_id}", summary="查询某用户的粉丝列表")
def followers(user_id: int, session: Session = Depends(get_session)):
    items = session.exec(select(Follow).where(Follow.following_id == user_id)).all()
    return ok({"count": len(items),
               "items": [{"follower_id": f.follower_id, "created_at": f.created_at.isoformat()} for f in items]})


@router.get("/follows/following/{user_id}", summary="查询某用户关注的人列表")
def following(user_id: int, session: Session = Depends(get_session)):
    items = session.exec(select(Follow).where(Follow.follower_id == user_id)).all()
    return ok({"count": len(items),
               "items": [{"following_id": f.following_id, "created_at": f.created_at.isoformat()} for f in items]})
