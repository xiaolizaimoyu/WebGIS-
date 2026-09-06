"""积分与签到模块路由（积分流水 / 签到 / 通知）

归属：后端 F 扩展。
前缀：/api/points（积分+签到），/api/notifications（通知）
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.response import BizError, ok
from app.core.security import get_current_user
from app.db import get_session
from app.models import Notification, PointsLog, SignRecord, User

router = APIRouter(tags=["积分与签到"])

# 统一前缀在 main.py include_router 时指定


# ==================== 签到 ====================

@router.post("/sign/do", summary="每日签到")
def do_sign(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """今日签到，获得积分。重复签到返回已签到状态。"""
    today = date.today()
    existing = session.exec(
        select(SignRecord).where(SignRecord.user_id == user.id, SignRecord.sign_date == today)
    ).first()

    if existing:
        return ok({"signed": True, "points": 0, "continuous_days": existing.continuous_days,
                   "msg": "今日已签到"})

    # 计算连续签到天数：检查昨天是否签到
    yesterday = today - timedelta(days=1)
    yesterday_record = session.exec(
        select(SignRecord).where(SignRecord.user_id == user.id, SignRecord.sign_date == yesterday)
    ).first()
    continuous = (yesterday_record.continuous_days + 1) if yesterday_record else 1

    # 连续7天额外奖励20积分
    points = 10
    bonus = 0
    if continuous > 0 and continuous % 7 == 0:
        bonus = 20
    total_gain = points + bonus

    # 记录签到
    record = SignRecord(user_id=user.id, sign_date=today, points=total_gain, continuous_days=continuous)
    session.add(record)

    # 更新用户积分 + 记录流水
    balance_before = user.points
    user.points += total_gain
    session.add(user)

    log = PointsLog(user_id=user.id, change=total_gain, balance_before=balance_before,
                    balance_after=user.points, reason="sign")
    session.add(log)

    session.commit()
    return ok({"signed": True, "points": total_gain, "bonus": bonus,
               "continuous_days": continuous, "total_points": user.points})


@router.get("/sign/status", summary="获取签到状态")
def sign_status(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    today = date.today()
    today_record = session.exec(
        select(SignRecord).where(SignRecord.user_id == user.id, SignRecord.sign_date == today)
    ).first()

    # 最近7天签到记录
    seven_days_ago = today - timedelta(days=6)
    records = session.exec(
        select(SignRecord).where(SignRecord.user_id == user.id, SignRecord.sign_date >= seven_days_ago)
        .order_by(SignRecord.sign_date)
    ).all()

    return ok({
        "signed_today": today_record is not None,
        "continuous_days": today_record.continuous_days if today_record else 0,
        "total_points": user.points,
        "recent_records": [{"date": r.sign_date.isoformat(), "points": r.points} for r in records],
    })


# ==================== 积分流水 ====================

@router.get("/points/log", summary="我的积分流水列表")
def points_log(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
               user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(PointsLog).where(PointsLog.user_id == user.id).order_by(PointsLog.created_at.desc())
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    return ok({"total": total, "page": page, "size": size, "balance": user.points,
               "items": [{"id": l.id, "change": l.change, "balance_before": l.balance_before,
                          "balance_after": l.balance_after, "reason": l.reason,
                          "created_at": l.created_at.isoformat()} for l in items]})


# ==================== 通知 ====================

notify_router = APIRouter(prefix="/api/notifications", tags=["通知"])


@notify_router.get("", summary="我的通知列表")
def list_notifications(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                       only_unread: bool = Query(False),
                       user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    stmt = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    if only_unread:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    total = len(session.exec(stmt).all())
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    unread_count = len(session.exec(
        select(Notification).where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
    ).all())
    return ok({"total": total, "page": page, "size": size, "unread_count": unread_count,
               "items": [{"id": n.id, "type": n.type, "title": n.title, "body": n.body,
                          "is_read": n.is_read, "related_id": n.related_id,
                          "created_at": n.created_at.isoformat()} for n in items]})


@notify_router.post("/{notify_id}/read", summary="标记单条通知为已读")
def mark_read(notify_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    n = session.get(Notification, notify_id)
    if not n or n.user_id != user.id:
        raise BizError(404, "通知不存在")
    n.is_read = True
    session.add(n)
    session.commit()
    return ok(None)


@notify_router.post("/read-all", summary="全部标记为已读")
def mark_all_read(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    items = session.exec(
        select(Notification).where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
    ).all()
    for n in items:
        n.is_read = True
        session.add(n)
    session.commit()
    return ok({"marked": len(items)})
