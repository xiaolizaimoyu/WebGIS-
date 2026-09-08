"""积分商城模块路由（商品 / 订单）

归属：后端 F 扩展。
前缀：/api/mall
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.response import BizError, ok
from app.core.security import get_current_user
from app.db import get_session
from app.models import MallGoods, Order, PointsLog, User

router = APIRouter(prefix="/api/mall", tags=["积分商城"])


# ==================== 商品 ====================

@router.get("/goods", summary="商品列表")
def list_goods(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
               category: str = Query(None),
               session: Session = Depends(get_session)):
    stmt = select(MallGoods).where(MallGoods.status == "on").order_by(MallGoods.points_price.asc())
    if category:
        stmt = stmt.where(MallGoods.category == category)
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
