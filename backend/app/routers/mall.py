"""积分商城模块路由（商品 / 订单）

归属：后端 F 扩展。
前缀：/api/mall
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, or_

from app.core.response import BizError, ok
from app.core.security import get_current_user
from app.db import get_session
from app.models import MallGoods, Order, PointsLog, User

router = APIRouter(prefix="/api/mall", tags=["积分商城"])


# ==================== 商品 ====================

@router.get("/goods", summary="商品列表")
def list_goods(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
               category: str = Query(None),
               keyword: str = Query(None, description="按名称/描述/分类模糊搜索"),
               session: Session = Depends(get_session)):
    stmt = select(MallGoods).where(MallGoods.status == "on").order_by(MallGoods.points_price.asc())
    if category:
        stmt = stmt.where(MallGoods.category == category)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(MallGoods.name.like(like),
                              MallGoods.description.like(like),
                              MallGoods.category.like(like)))
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    return ok({"total": total, "page": page, "size": size,
               "items": [_goods_dict(g) for g in items]})


@router.get("/categories", summary="商品分类列表")
def list_categories(session: Session = Depends(get_session)):
    """返回商城所有商品分类（去重，按名称排序）。"""
    rows = session.exec(
        select(MallGoods.category).where(MallGoods.status == "on").distinct()
    ).all()
    categories = sorted([c for c in rows if c])
    return ok(categories)


@router.get("/goods/{goods_id}", summary="商品详情")
def get_goods(goods_id: int, session: Session = Depends(get_session)):
    g = session.get(MallGoods, goods_id)
    if not g:
        raise BizError(404, "商品不存在")
    return ok(_goods_dict(g))


# ==================== 订单 ====================

@router.post("/exchange/{goods_id}", summary="用积分兑换商品")
def exchange_goods(goods_id: int,
                   quantity: int = Query(1, ge=1, le=10, description="兑换数量"),
                   user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    goods = session.get(MallGoods, goods_id)
    if not goods or goods.status != "on":
        raise BizError(404, "商品不存在或已下架")
    if goods.stock < quantity:
        raise BizError(400, f"库存不足，当前仅剩 {goods.stock} 件")
    total_cost = goods.points_price * quantity
    if user.points < total_cost:
        raise BizError(400, f"积分不足，需要 {total_cost} 积分，当前 {user.points} 积分")

    # 扣减积分
    balance_before = user.points
    user.points -= total_cost
    session.add(user)

    # 扣减库存
    goods.stock -= quantity
    session.add(goods)

    # 创建订单（pending=待发货）
    order = Order(user_id=user.id, goods_id=goods.id, goods_name=goods.name,
                  points_cost=total_cost, quantity=quantity, status="pending")
    session.add(order)

    # 积分流水
    log = PointsLog(user_id=user.id, change=-total_cost,
                    balance_before=balance_before, balance_after=user.points,
                    reason="exchange")
    session.add(log)

    session.commit()
    session.refresh(order)
    return ok({"order_id": order.id, "goods_name": goods.name,
               "points_cost": total_cost, "quantity": quantity,
               "remaining_points": user.points})


@router.get("/orders/mine", summary="我的兑换订单")
def my_orders(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
              user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    # 批量查商品图片，避免 N+1
    goods_ids = [o.goods_id for o in items if o.goods_id]
    goods_map = {}
    if goods_ids:
        goods_rows = session.exec(select(MallGoods).where(MallGoods.id.in_(goods_ids))).all()
        goods_map = {g.id: g for g in goods_rows}
    return ok({"total": total, "page": page, "size": size,
               "items": [{"id": o.id, "goods_id": o.goods_id, "goods_name": o.goods_name,
                          "goods_image": goods_map.get(o.goods_id).image if goods_map.get(o.goods_id) else None,
                          "points_cost": o.points_cost, "quantity": getattr(o, "quantity", 1),
                          "status": o.status,
                          "created_at": o.created_at.isoformat()} for o in items]})


# 订单状态流转：pending 待发货 -> shipping 配送中 -> delivered 已送达；任意非终态可 -> cancelled
ORDER_FLOW = {
    "pending": {"shipping", "delivered", "cancelled"},
    "shipping": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}


@router.patch("/orders/{order_id}/cancel", summary="用户取消待发货订单")
def cancel_my_order(
    order_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """用户取消自己的待发货订单：退积分、恢复库存、状态改 cancelled。

    仅 pending 可取消；shipping/delivered 已发出不可取消。
    """
    order = session.get(Order, order_id)
    if order is None:
        raise BizError(2001, "订单不存在")
    if order.user_id != user.id:
        raise BizError(2003, "无权操作他人订单")
    if order.status != "pending":
        raise BizError(400, "当前状态不可取消（仅待发货可取消）")

    qty = getattr(order, "quantity", 1)
    # 退还积分
    user.points = getattr(user, "points", 0) + order.points_cost
    session.add(user)
    # 恢复库存
    if order.goods_id:
        goods = session.get(MallGoods, order.goods_id)
        if goods:
            goods.stock = getattr(goods, "stock", 0) + qty
            session.add(goods)
    # 状态变更
    order.status = "cancelled"
    session.add(order)
    # 积分流水（正向，记录退款）
    log = PointsLog(user_id=user.id, change=order.points_cost,
                    balance_before=user.points - order.points_cost,
                    balance_after=user.points,
                    reason="exchange_cancel")
    session.add(log)
    session.commit()
    return ok({"id": order_id, "status": "cancelled",
               "refunded_points": order.points_cost,
               "current_points": user.points}, "订单已取消，积分已退回")


def _goods_dict(g: MallGoods) -> dict:
    return {
        "id": g.id,
        "name": g.name,
        "description": g.description,
        "image": g.image,
        "points_price": g.points_price,
        "stock": g.stock,
        "status": g.status,
        "category": g.category,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }
