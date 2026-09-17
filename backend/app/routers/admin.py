"""管理员路由（归属：后端 D）

前缀 /api/admin，所有接口都需 Depends(get_current_admin)。
功能：概览统计、帖子审核（列出/删除任意帖）、用户管理、评论删除。
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.admin import get_current_admin
from app.core.response import BizError, ok
from app.db import get_session
from app.models import Comment, Content, Order, Favorite, Like, LocationPoint, User

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
    # 级联清理：评论 / 点赞 / 收藏，避免孤儿数据与外键残留
    for c0 in session.exec(select(Comment).where(Comment.content_id == content.id)).all():
        session.delete(c0)
    for l0 in session.exec(select(Like).where(Like.content_id == content.id)).all():
        session.delete(l0)
    for f0 in session.exec(select(Favorite).where(Favorite.content_id == content.id)).all():
        session.delete(f0)
    session.delete(content)
    session.commit()
    return ok({"id": content_id, "deleted": True}, "管理员已删除该帖")


def _user_with_stats(user: User, session: Session) -> dict:
    """用户信息 + 发帖数/评论数（管理员视角）。"""
    content_count = session.exec(
        select(func.count()).select_from(Content).where(Content.author_id == user.id)
    ).one()
    comment_count = session.exec(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    ).one()
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "is_admin": getattr(user, "is_admin", False),
        "content_count": content_count,
        "comment_count": comment_count,
        "created_at": user.created_at,
    }


@router.get("/users", summary="用户管理列表（分页）")
def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """分页列出所有用户（含发帖数/评论数/is_admin），可按用户名/昵称搜索。"""
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(User)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(User.username.contains(like) | User.nickname.contains(like))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    users = session.exec(
        stmt.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [_user_with_stats(u, session) for u in users],
    })


@router.delete("/users/{user_id}", summary="删除用户")
def admin_delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """管理员删除用户。禁止删除自己和其他管理员，避免误操作。

    注：若该用户已发布内容/评论，外键约束可能阻止删除，返回 1007。
    """
    target = session.get(User, user_id)
    if target is None:
        raise BizError(1005, "用户不存在")
    if target.id == admin.id:
        raise BizError(1012, "不能删除当前登录的管理员账号")
    if getattr(target, "is_admin", False):
        raise BizError(1012, "不能删除其他管理员账号")
    try:
        session.delete(target)
        session.commit()
    except Exception:
        session.rollback()
        raise BizError(1007, "该用户存在关联内容/评论，无法直接删除")
    return ok({"id": user_id, "deleted": True}, "用户已删除")


@router.delete("/comments/{comment_id}", summary="删除任意评论")
def admin_delete_comment(
    comment_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """管理员删除任意评论（内容审核）。"""
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise BizError(2001, "评论不存在或已被删除")
    session.delete(comment)
    session.commit()
    return ok({"id": comment_id, "deleted": True}, "管理员已删除该评论")


# ==================== 订单发货管理（积分商城） ====================

# 订单状态流转规则：与 mall.py ORDER_FLOW 保持一致
_ADMIN_ORDER_FLOW = {
    "pending": {"shipping", "delivered", "cancelled"},
    "shipping": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}


class OrderStatusIn(BaseModel):
    status: str  # shipping | delivered | cancelled


@router.get("/orders", summary="订单发货管理列表（分页）")
def admin_list_orders(
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """管理员查看所有兑换订单，可按状态筛选，用于发货管理。"""
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    orders = session.exec(
        stmt.order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [
            {
                "id": o.id,
                "user_id": o.user_id,
                "goods_id": o.goods_id,
                "goods_name": o.goods_name,
                "points_cost": o.points_cost,
                "quantity": getattr(o, "quantity", 1),
                "status": o.status,
                "created_at": o.created_at,
            }
            for o in orders
        ],
    })


@router.patch("/orders/{order_id}/status", summary="更新订单发货状态")
def admin_update_order_status(
    order_id: int,
    data: OrderStatusIn,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """管理员更新订单发货状态：pending -> shipping -> delivered，或置为 cancelled。

    合法流转见 _ADMIN_ORDER_FLOW。非法流转返回 400。
    """
    order = session.get(Order, order_id)
    if order is None:
        raise BizError(2001, "订单不存在")
    if data.status not in _ADMIN_ORDER_FLOW:
        raise BizError(400, f"未知状态：{data.status}")
    if data.status not in _ADMIN_ORDER_FLOW.get(order.status, set()):
        raise BizError(400, f"状态非法流转：{order.status} -> {data.status}")
    order.status = data.status
    session.add(order)
    session.commit()
    return ok({"id": order_id, "status": data.status}, "订单状态已更新")


# ==================== 地点坐标管理（发布选点/地图点位校准） ====================

class LocationSaveIn(BaseModel):
    """新增或更新一个地点坐标（按名称 upsert）。"""

    name: str
    lng: float
    lat: float


@router.post("/locations", summary="新增/更新地点坐标")
def admin_save_location(
    data: LocationSaveIn,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    """按名称新增或更新地点坐标（同名覆盖），用于手动校准校园真实位置。"""
    name = (data.name or "").strip()
    if not name:
        raise BizError(400, "地点名称不能为空")
    if not (-180 <= data.lng <= 180) or not (-90 <= data.lat <= 90):
        raise BizError(400, "经纬度超出有效范围")
    row = session.exec(select(LocationPoint).where(LocationPoint.name == name)).first()
    if row:
        row.lng = data.lng
        row.lat = data.lat
        row.updated_at = datetime.now()
        msg = "地点坐标已更新"
    else:
        max_sort = session.exec(select(func.max(LocationPoint.sort))).first() or 0
        session.add(LocationPoint(name=name, lng=data.lng, lat=data.lat, sort=int(max_sort or 0) + 1))
        msg = "地点坐标已新增"
    session.commit()
    return ok({"name": name, "lng": data.lng, "lat": data.lat}, msg)


@router.delete("/locations/{loc_id}", summary="删除地点坐标")
def admin_delete_location(
    loc_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_admin),
):
    row = session.get(LocationPoint, loc_id)
    if row is None:
        raise BizError(2002, "地点不存在或已被删除")
    session.delete(row)
    session.commit()
    return ok({"id": loc_id, "deleted": True}, "地点坐标已删除")
