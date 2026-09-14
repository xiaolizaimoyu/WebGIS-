"""地点坐标库路由（公开读取）

发布帖子的地点下拉、各列表页地图点位，统一从 /api/locations 读取
手动校准后的真实坐标；管理员通过 /api/admin/locations 维护。
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.response import ok
from app.db import get_session
from app.models import LocationPoint

router = APIRouter(prefix="/api", tags=["地点坐标"])


@router.get("/locations")
def list_locations(session: Session = Depends(get_session)):
    """返回全部地点坐标（按 sort 排序）。"""
    rows = session.exec(
        select(LocationPoint).order_by(LocationPoint.sort, LocationPoint.id)
    ).all()
    return ok([{"id": r.id, "name": r.name, "lng": r.lng, "lat": r.lat} for r in rows])
