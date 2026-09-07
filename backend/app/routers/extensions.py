"""扩展模块路由（问答 / 学习资料 / 组队拼车）

这些模块前端已实现 UI，后端提供基础接口骨架，返回空列表或演示数据，
确保前端调用不报错。后续可按需扩展为完整 CRUD + 数据库表。

前缀：
- /api/questions     校园问答
- /api/materials     学习资料
- /api/carpools      组队拼车
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from fastapi.responses import Response

from app.core.response import ok, BizError
from app.routers.material_docs import generate_material_file
from app.core.security import get_current_user
from app.db import get_session
from app.models import User

router = APIRouter(tags=["扩展模块"])

# ---------- 内存演示数据（后续可迁移到数据库） ----------
_questions = [
    {"id": 1, "title": "高数期末复习重点有哪些？", "body": "马上要期末考试了，求学长学姐分享一下高数下册的复习重点和必考题型，万分感谢！",
     "tag": "高数", "author_name": "小学弟", "view_count": 328, "answer_count": 5, "solved": True,
     "created_at": (datetime.now() - timedelta(hours=2)).isoformat()},
    {"id": 2, "title": "学校附近哪家外卖好吃又便宜？", "body": "求推荐学校周边性价比高的外卖，预算15元以内，最好是辣的！",
     "tag": "生活", "author_name": "吃货同学", "view_count": 156, "answer_count": 12, "solved": False,
     "created_at": (datetime.now() - timedelta(hours=5)).isoformat()},
    {"id": 3, "title": "GIS专业考研选哪个方向比较好？", "body": "本人地理空间信息工程专业，想考研，请问遥感、GIS开发、空间分析哪个方向就业前景更好？",
     "tag": "考研", "author_name": "迷茫的大三", "view_count": 489, "answer_count": 8, "solved": True,
     "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 4, "title": "图书馆怎么预约座位？", "body": "第一次去图书馆，请问座位预约系统怎么用？需要下载什么APP吗？",
     "tag": "求助", "author_name": "新生小白", "view_count": 203, "answer_count": 6, "solved": False,
     "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
]

_answers = {
    1: [
        {"id": 1, "question_id": 1, "author_name": "学霸学姐", "body": "重点看第三章多元函数微分学和第五章重积分，每年必考。建议把课后题做两遍。", "adopted": True, "created_at": "2026-09-06T11:00:00"},
        {"id": 2, "question_id": 1, "author_name": "助教", "body": "曲线曲面积分也是重点，虽然难但分值高，建议多练。", "adopted": False, "created_at": "2026-09-06T12:30:00"},
    ],
    2: [
        {"id": 3, "question_id": 2, "author_name": "外卖达人", "body": "推荐东门的「川味小炒」，人均12，麻辣香锅超好吃！", "adopted": False, "created_at": "2026-09-06T08:00:00"},
    ],
}

_materials = [
    {"id": 1, "title": "高等数学(下)期末复习笔记", "subject": "高数", "author_name": "学霸君", "download_count": 156, "file_type": "pdf", "size": "2.3MB",
     "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 2, "title": "GIS空间分析实验报告模板", "subject": "GIS", "author_name": "课代表", "download_count": 89, "file_type": "docx", "size": "1.1MB",
     "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
    {"id": 3, "title": "大学英语四级真题及答案", "subject": "英语", "author_name": "英语角", "download_count": 234, "file_type": "pdf", "size": "5.6MB",
     "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 4, "title": "数据结构期末重点整理", "subject": "计算机", "author_name": "码农", "download_count": 178, "file_type": "pdf", "size": "3.2MB",
     "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
]

_carpools = [
    {"id": 1, "title": "周末去济南火车站拼车", "destination": "济南站", "departure": "学校东门", "departure_time": "2026-09-07 08:00",
     "people_needed": 3, "people_joined": 1, "contact": "微信: xxx", "author_name": "旅行达人", "note": "AA制，人均约50元",
     "created_at": (datetime.now() - timedelta(hours=3)).isoformat()},
    {"id": 2, "title": "周五晚去淄博站拼车", "destination": "淄博站", "departure": "学校北门", "departure_time": "2026-09-12 18:00",
     "people_needed": 2, "people_joined": 2, "contact": "QQ: xxx", "author_name": "回家党", "note": "已有2人，还差2人",
     "created_at": (datetime.now() - timedelta(hours=6)).isoformat()},
    {"id": 3, "title": "国庆去青岛玩拼车", "destination": "青岛", "departure": "学校", "departure_time": "2026-10-01 07:00",
     "people_needed": 4, "people_joined": 1, "contact": "电话: xxx", "author_name": "旅游爱好者", "note": "三天两夜，行程可商量",
     "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
]


# ==================== 校园问答 ====================

@router.get("/questions", summary="问题列表")
def list_questions(keyword: Optional[str] = None, tag: Optional[str] = None,
                   page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
                   session: Session = Depends(get_session)):
    items = _questions
    if tag:
        items = [q for q in items if q["tag"] == tag]
    if keyword:
        items = [q for q in items if keyword in q["title"] or keyword in q["body"]]
    total = len(items)
    start = (page - 1) * size
    return ok({"total": total, "page": page, "size": size, "items": items[start:start + size]})


@router.get("/questions/{qid}", summary="问题详情")
def get_question(qid: int):
    q = next((q for q in _questions if q["id"] == qid), None)
    if not q:
        from app.core.response import BizError
        raise BizError(404, "问题不存在")
    return ok(q)


@router.get("/questions/{qid}/answers", summary="回答列表")
def list_answers(qid: int):
    return ok({"items": _answers.get(qid, [])})


@router.post("/questions", summary="发布问题（需登录）")
def create_question(data: dict, user: User = Depends(get_current_user)):
    new_id = max(q["id"] for q in _questions) + 1
    q = {"id": new_id, "title": data.get("title", ""), "body": data.get("body", ""),
         "tag": data.get("tag", "求助"), "author_name": user.nickname,
         "view_count": 0, "answer_count": 0, "solved": False,
         "created_at": datetime.now().isoformat()}
    _questions.append(q)
    return ok(q, "发布成功")


@router.post("/questions/{qid}/answers", summary="发表回答（需登录）")
def create_answer(qid: int, data: dict, user: User = Depends(get_current_user)):
    if qid not in _answers:
        _answers[qid] = []
    new_id = max((a["id"] for answers in _answers.values() for a in answers), default=0) + 1
    a = {"id": new_id, "question_id": qid, "author_name": user.nickname,
         "body": data.get("body", ""), "adopted": False, "created_at": datetime.now().isoformat()}
    _answers[qid].append(a)
    return ok(a, "回答成功")


# ==================== 学习资料 ====================

@router.get("/materials", summary="资料列表")
def list_materials(keyword: Optional[str] = None, subject: Optional[str] = None,
                   page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50)):
    items = _materials
    if subject:
        items = [m for m in items if m["subject"] == subject]
    if keyword:
        items = [m for m in items if keyword in m["title"]]
    total = len(items)
    start = (page - 1) * size
    return ok({"total": total, "page": page, "size": size, "items": items[start:start + size]})


@router.get("/materials/{mid}", summary="资料详情")
def get_material(mid: int):
    m = next((m for m in _materials if m["id"] == mid), None)
    if not m:
        from app.core.response import BizError
        raise BizError(404, "资料不存在")
    return ok(m)


@router.get("/materials/{mid}/download", summary="下载资料（真实文件）")
def download_material(mid: int):
    """按资料 ID 动态生成真实 PDF/DOCX 文件返回浏览器下载，下载次数 +1"""
    m = next((m for m in _materials if m["id"] == mid), None)
    if not m:
        raise BizError(404, "资料不存在")
    try:
        data, filename, media_type = generate_material_file(mid, m["title"])
    except ValueError:
        raise BizError(404, "该资料暂未提供下载文件")
    m["download_count"] += 1
    # 中文文件名需 RFC 5987 编码，保证浏览器正确保存
    from urllib.parse import quote
    filename_quoted = quote(filename)
    disposition = 'attachment; filename="{}*; filename*=UTF-8\'\'{}"'.format(filename_quoted, filename_quoted)
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": disposition})


# ==================== 组队拼车 ====================

@router.get("/carpools", summary="拼车列表")
def list_carpools(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50)):
    total = len(_carpools)
    start = (page - 1) * size
    return ok({"total": total, "page": page, "size": size, "items": _carpools[start:start + size]})


@router.get("/carpools/{cid}", summary="拼车详情")
def get_carpool(cid: int):
    c = next((c for c in _carpools if c["id"] == cid), None)
    if not c:
        from app.core.response import BizError
        raise BizError(404, "拼车信息不存在")
    return ok(c)


@router.post("/carpools", summary="发布拼车（需登录）")
def create_carpool(data: dict, user: User = Depends(get_current_user)):
    new_id = max(c["id"] for c in _carpools) + 1
    c = {"id": new_id, "title": data.get("title", ""), "destination": data.get("destination", ""),
         "departure": data.get("departure", ""), "departure_time": data.get("departure_time", ""),
         "people_needed": data.get("people_needed", 3), "people_joined": 1,
         "contact": data.get("contact", ""), "author_name": user.nickname,
         "note": data.get("note", ""), "created_at": datetime.now().isoformat()}
    _carpools.append(c)
    return ok(c, "发布成功")
