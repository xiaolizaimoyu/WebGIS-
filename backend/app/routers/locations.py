"""地点坐标库路由（公开读取）

发布帖子的地点下拉、各列表页地图点位，统一从 /api/locations 读取
手动校准后的真实坐标；管理员通过 /api/admin/locations 维护。

返回顺序：按用途分组排序（学生公寓 → 教学楼/学院/实验楼 → 食堂 → 文体服务 → 校门其他），
组内按楼号数字升序，便于下拉选点与地图点位浏览。
"""
import re

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.response import ok
from app.db import get_session
from app.models import LocationPoint

router = APIRouter(prefix="/api", tags=["地点坐标"])

CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def _place_sort_key(name: str):
    """按用途分组：公寓 → 教学 → 食堂 → 文体服务 → 校门其他；组内优先按数字楼号升序。"""
    if '公寓' in name:
        group = 0
    elif '医院' in name:
        group = 3
    elif any(k in name for k in ('教', '学院', '院', '实验', '信息楼')):
        group = 1
    elif '餐' in name:
        group = 2
    elif any(k in name for k in ('体', '图书馆', '艺术', '服务', '鸿远', '宾馆', '红炉')):
        group = 3
    else:
        group = 4
    # 组内数字：阿拉伯数字优先，其次中文数字（一餐→1、三体→3）
    num = None
    m = re.search(r'\d+', name)
    if m:
        num = int(m.group())
    else:
        for ch, v in CN_NUM.items():
            if ch in name:
                num = v
                break
    return (group, num if num is not None else 999, name)


@router.get("/locations")
def list_locations(session: Session = Depends(get_session)):
    """返回全部地点坐标（按用途分组排序）。"""
    rows = session.exec(select(LocationPoint)).all()
    rows = sorted(rows, key=lambda r: _place_sort_key(r.name))
    return ok([{"id": r.id, "name": r.name, "lng": r.lng, "lat": r.lat} for r in rows])
