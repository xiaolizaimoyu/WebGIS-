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


@router.get("/goods/{goods_id}", summary="商品详情")
def get_goods(goods_id: int, session: Session = Depends(get_session)):
    g = session.get(MallGoods, goods_id)
    if not g:
        raise BizError(404, "商品不存在")
    return ok(_goods_dict(g))


# ==================== 订单 ====================

@router.post("/exchange/{goods_id}", summary="用积分兑换商品")
def exchange_goods(goods_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    goods = session.get(MallGoods, goods_id)
    if not goods or goods.status != "on":
        raise BizError(404, "商品不存在或已下架")
    if goods.stock == 0:
        raise BizError(400, "商品已兑完")
    if user.points < goods.points_price:
        raise BizError(400, f"积分不足，需要 {goods.points_price} 积分，当前 {user.points} 积分")

    # 扣减积分
    balance_before = user.points
    user.points -= goods.points_price
    session.add(user)

    # 扣减库存
    if goods.stock > 0:
        goods.stock -= 1
        session.add(goods)

    # 创建订单
    order = Order(user_id=user.id, goods_id=goods.id, goods_name=goods.name,
                  points_cost=goods.points_price, status="processed")
    session.add(order)

    # 积分流水
    log = PointsLog(user_id=user.id, change=-goods.points_price,
                    balance_before=balance_before, balance_after=user.points,
                    reason="exchange")
    session.add(log)

    session.commit()
    session.refresh(order)
    return ok({"order_id": order.id, "goods_name": goods.name,
               "points_cost": goods.points_price, "remaining_points": user.points})


@router.get("/orders/mine", summary="我的兑换订单")
def my_orders(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
              user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    return ok({"total": total, "page": page, "size": size,
               "items": [{"id": o.id, "goods_id": o.goods_id, "goods_name": o.goods_name,
                          "points_cost": o.points_cost, "status": o.status,
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
