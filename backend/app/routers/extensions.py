"""扩展模块路由（问答 / 学习资料 / 组队拼车）

这些模块前端已实现 UI；拼车已迁移为数据库完整 CRUD（carpools 表），
问答与资料为内存演示数据。

前缀：
- /api/questions     校园问答
- /api/materials     学习资料
- /api/carpools      组队拼车
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from fastapi.responses import Response

from app.core.response import ok, BizError
from app.routers.material_docs import generate_material_file
from app.routers.post import _get_optional_user
from app.core.security import get_current_user
from app.db import get_session
from app.models import Carpool, CarpoolApplication, User

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
    {"id": 1, "title": "高等数学(下)期末复习笔记", "subject": "高数", "author_name": "学霸君", "download_count": 156, "likes": 128, "file_type": "pdf", "size": "2.3MB",
     "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 2, "title": "GIS空间分析实验报告模板", "subject": "GIS", "author_name": "课代表", "download_count": 89, "likes": 64, "file_type": "docx", "size": "1.1MB",
     "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
    {"id": 3, "title": "大学英语四级真题及答案", "subject": "英语", "author_name": "英语角", "download_count": 234, "likes": 203, "file_type": "pdf", "size": "5.6MB",
     "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 4, "title": "数据结构期末重点整理", "subject": "计算机", "author_name": "码农", "download_count": 178, "likes": 87, "file_type": "pdf", "size": "3.2MB",
     "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
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
         "tag": data.get("tag", "求助"), "author_id": user.id, "author_name": user.nickname,
         "view_count": 0, "answer_count": 0, "solved": False,
         "created_at": datetime.now().isoformat()}
    _questions.append(q)
    return ok(q, "发布成功")


@router.post("/questions/{qid}/answers", summary="发表回答（需登录）")
def create_answer(qid: int, data: dict, user: User = Depends(get_current_user)):
    if qid not in _answers:
        _answers[qid] = []
    new_id = max((a["id"] for answers in _answers.values() for a in answers), default=0) + 1
    a = {"id": new_id, "question_id": qid, "author_id": user.id, "author_name": user.nickname,
         "body": data.get("body", ""), "adopted": False, "created_at": datetime.now().isoformat()}
    _answers[qid].append(a)
    return ok(a, "回答成功")


@router.post("/questions/{qid}/answers/{aid}/adopt", summary="采纳答案（仅问题作者）")
def adopt_answer(qid: int, aid: int, user: User = Depends(get_current_user)):
    q = next((q for q in _questions if q["id"] == qid), None)
    if not q:
        from app.core.response import BizError
        raise BizError(404, "问题不存在")
    if q.get("author_id") != user.id:
        from app.core.response import BizError
        raise BizError(403, "只有问题作者才能采纳答案")
    answers = _answers.get(qid, [])
    a = next((x for x in answers if x["id"] == aid), None)
    if not a:
        from app.core.response import BizError
        raise BizError(404, "答案不存在")
    # 取消其它答案的采纳标记，目标答案设为已采纳
    for x in answers:
        x["adopted"] = (x["id"] == aid)
    q["solved"] = True
    return ok({"solved": True, "adopted": True, "answer_id": aid})


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


@router.post("/materials/{mid}/like", summary="点赞资料（需登录）")
def like_material(mid: int, user: User = Depends(get_current_user)):
    """点赞数 +1，返回最新点赞数，前端据此展示，避免 NaN"""
    m = next((m for m in _materials if m["id"] == mid), None)
    if not m:
        raise BizError(404, "资料不存在")
    m["likes"] = m.get("likes", 0) + 1
    return ok({"likes": m["likes"]}, "点赞成功")


# ==================== 组队拼车（carpools 表，完整 CRUD） ====================

# 拼车输入校验：标题/地点必填、手机号 11 位、座位 1-7、出发时间必须晚于当前
PHONE_RE = re.compile(r"^1\d{10}$")


def _validate_carpool(data: dict, is_create: bool = True) -> dict:
    err = lambda msg: (_ for _ in ()).throw(BizError(400, msg))
    title = (data.get("title") or "").strip()
    if not title:
        err("请填写拼车标题")
    if len(title) > 60:
        err("标题不能超过 60 字")
    frm = (data.get("from") or "").strip()
    to = (data.get("to") or "").strip()
    if not frm:
        err("请填写出发地")
    if not to:
        err("请填写目的地")
    if len(frm) > 50 or len(to) > 50:
        err("出发地/目的地不能超过 50 字")

    depart_time = (data.get("depart_time") or "").strip()
    if not depart_time:
        err("请选择出发时间")
    try:
        dt = datetime.strptime(depart_time, "%Y-%m-%d %H:%M")
    except ValueError:
        err("出发时间格式不正确，应为 YYYY-MM-DD HH:mm")
    if is_create and dt < datetime.now():
        err("出发时间不能早于当前时间")

    seats_total = data.get("seats_total")
    if seats_total is None:
        err("请设置座位数")
    try:
        seats_total = int(seats_total)
    except (TypeError, ValueError):
        err("座位数必须是整数")
    if not 1 <= seats_total <= 7:
        err("座位数需在 1-7 之间")

    price = data.get("price_per_person", 0)
    try:
        price = float(price or 0)
    except (TypeError, ValueError):
        err("费用必须是数字")
    if price < 0 or price > 1000:
        err("费用需在 0-1000 元之间")

    phone = (data.get("phone") or "").strip()
    if not phone:
        err("请填写联系电话")
    if not PHONE_RE.match(phone):
        err("手机号格式不正确，需为 11 位数字（如 13812345678）")

    return_time = (data.get("return_time") or "").strip()
    if return_time:
        try:
            datetime.strptime(return_time, "%Y-%m-%d %H:%M")
        except ValueError:
            err("返回时间格式不正确，应为 YYYY-MM-DD HH:mm")

    return {
        "title": title, "from": frm, "to": to,
        "depart_time": depart_time, "return_time": return_time,
        "seats_total": seats_total, "price_per_person": price,
        "phone": phone, "note": (data.get("note") or "").strip()[:500],
    }


def _carpool_to_dict(c: Carpool, user: Optional[User] = None) -> dict:
    """ORM -> 前端 camelCase dict（含 is_author 标记，供编辑/删除按钮显隐）"""
    return {
        "id": c.id, "title": c.title, "from": c.from_, "to": c.to,
        "depart_time": c.depart_time, "return_time": c.return_time or "",
        "seats_total": c.seats_total, "seats_left": c.seats_left,
        "price_per_person": c.price_per_person, "phone": c.phone,
        "note": c.note or "", "author_id": c.author_id,
        "author_name": c.author_name, "status": c.status,
        "created_at": c.created_at.isoformat(),
        "is_author": bool(user and user.id == c.author_id),
    }


@router.get("/carpools", summary="拼车列表")
def list_carpools(keyword: Optional[str] = None, status: Optional[str] = None,
                  page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
                  user: Optional[User] = Depends(_get_optional_user),
                  session: Session = Depends(get_session)):
    stmt = select(Carpool).order_by(Carpool.created_at.desc())
    if status:
        stmt = stmt.where(Carpool.status == status)
    all_items = session.exec(stmt).all()
    if keyword:
        kw = keyword.strip()
        all_items = [c for c in all_items if kw in c.title or kw in c.from_ or kw in c.to]
    total = len(all_items)
    start = (page - 1) * size
    items = [_carpool_to_dict(c, user) for c in all_items[start:start + size]]
    return ok({"total": total, "page": page, "size": size, "items": items})


@router.get("/carpools/my-applications", summary="我的拼车申请列表")
def my_applications(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    """当前用户提交过的全部申请（含拼车标题、状态），供取消/查看使用"""
    apps = session.exec(
        select(CarpoolApplication).where(CarpoolApplication.applicant_id == user.id)
        .order_by(CarpoolApplication.created_at.desc())
    ).all()
    items = []
    for a in apps:
        c = session.get(Carpool, a.carpool_id)
        items.append({
            **_app_to_dict(a),
            "carpool_title": c.title if c else "拼车已删除",
            "carpool_status": c.status if c else "deleted",
            "from": c.from_ if c else "",
            "to": c.to if c else "",
            "depart_time": c.depart_time if c else "",
        })
    total = len(items)
    start = (page - 1) * size
    return ok({"total": total, "page": page, "size": size, "items": items[start:start + size]})


@router.get("/carpools/{cid}", summary="拼车详情")
def get_carpool(cid: int, user: Optional[User] = Depends(_get_optional_user),
                session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    if not c:
        raise BizError(404, "拼车信息不存在")
    data = _carpool_to_dict(c, user)
    # 当前用户对该拼车的申请状态（用于"已申请/取消"按钮）
    my_app = None
    if user:
        my_app = session.exec(
            select(CarpoolApplication).where(
                CarpoolApplication.carpool_id == cid,
                CarpoolApplication.applicant_id == user.id,
            ).order_by(CarpoolApplication.created_at.desc())
        ).first()
        if my_app:
            data["my_application"] = {
                "id": my_app.id, "status": my_app.status,
                "people_count": my_app.people_count,
            }
    # 车主视角：待确认申请数
    if user and user.id == c.author_id:
        pending = session.exec(
            select(CarpoolApplication).where(
                CarpoolApplication.carpool_id == cid,
                CarpoolApplication.status == "pending",
            )
        ).all()
        data["pending_count"] = len(pending)
    else:
        data["pending_count"] = 0
    return ok(data)


@router.post("/carpools", summary="发布拼车（需登录，含完整校验）")
def create_carpool(data: dict, user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    v = _validate_carpool(data)
    c = Carpool(
        title=v["title"], from_=v["from"], to=v["to"],
        depart_time=v["depart_time"], return_time=v["return_time"],
        seats_total=v["seats_total"], seats_left=v["seats_total"],
        price_per_person=v["price_per_person"], phone=v["phone"],
        note=v["note"], author_id=user.id, author_name=user.nickname,
        status="recruiting",
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return ok(_carpool_to_dict(c, user), "发布成功")


@router.put("/carpools/{cid}", summary="编辑拼车（仅作者）")
def update_carpool(cid: int, data: dict, user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    if not c:
        raise BizError(404, "拼车信息不存在")
    if c.author_id != user.id:
        raise BizError(403, "只能编辑自己发布的拼车")
    v = _validate_carpool(data, is_create=False)
    # 总座位数不能小于已占用座位（已报名人数）
    if v["seats_total"] < c.seats_total - c.seats_left:
        raise BizError(400, f"总座位不能小于已占用座位 {c.seats_total - c.seats_left} 个")
    c.title = v["title"]
    c.from_ = v["from"]
    c.to = v["to"]
    c.depart_time = v["depart_time"]
    c.return_time = v["return_time"]
    c.seats_total = v["seats_total"]
    c.price_per_person = v["price_per_person"]
    c.phone = v["phone"]
    c.note = v["note"]
    c.status = "recruiting" if c.seats_left > 0 else "full"
    session.add(c)
    session.commit()
    session.refresh(c)
    return ok(_carpool_to_dict(c, user), "保存成功")


@router.delete("/carpools/{cid}", summary="删除拼车（仅作者）")
def delete_carpool(cid: int, user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    if not c:
        raise BizError(404, "拼车信息不存在")
    if c.author_id != user.id:
        raise BizError(403, "只能删除自己发布的拼车")
    session.delete(c)
    session.commit()
    return ok({"id": cid}, "删除成功")


@router.post("/carpools/{cid}/apply", summary="申请加入拼车（需登录，待车主确认）")
def apply_carpool(cid: int, data: dict, user: User = Depends(get_current_user),
                  session: Session = Depends(get_session)):
    """提交申请：不直接扣座位，进入待确认；车主同意后才扣减剩余座位"""
    c = session.get(Carpool, cid)
    if not c:
        raise BizError(404, "拼车信息不存在")
    if c.author_id == user.id:
        raise BizError(400, "不能申请自己发布的拼车")
    if c.status == "closed":
        raise BizError(400, "该拼车已关闭")
    if c.seats_left <= 0:
        raise BizError(400, "该拼车已满员")
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    if not name:
        raise BizError(400, "请填写姓名")
    try:
        people = int(data.get("people_count", 1))
    except (TypeError, ValueError):
        people = 1
    if not 1 <= people <= 7:
        raise BizError(400, "申请人数需在 1-7 之间")
    if not PHONE_RE.match(phone):
        raise BizError(400, "手机号格式不正确，需为 11 位数字")
    # 同一用户对同一拼车只能有一条待确认申请
    existing = session.exec(
        select(CarpoolApplication).where(
            CarpoolApplication.carpool_id == cid,
            CarpoolApplication.applicant_id == user.id,
            CarpoolApplication.status == "pending",
        )
    ).first()
    if existing:
        raise BizError(400, "您已提交过申请，等待车主确认中")
    app = CarpoolApplication(
        carpool_id=cid, applicant_id=user.id, applicant_name=name,
        phone=phone, people_count=people, remark=(data.get("remark") or "").strip()[:300],
        status="pending",
    )
    session.add(app)
    session.commit()
    session.refresh(app)
    return ok({"application_id": app.id, "status": "pending"}, "申请已提交，等待车主确认")


@router.get("/carpools/{cid}/applications", summary="拼车申请列表（仅车主）")
def list_applications(cid: int, user: User = Depends(get_current_user),
                      session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    if not c:
        raise BizError(404, "拼车信息不存在")
    if c.author_id != user.id:
        raise BizError(403, "只有车主可以查看申请")
    apps = session.exec(
        select(CarpoolApplication).where(CarpoolApplication.carpool_id == cid)
        .order_by(CarpoolApplication.created_at.desc())
    ).all()
    return ok({"items": [_app_to_dict(a) for a in apps]})


@router.post("/carpools/{cid}/applications/{aid}/approve", summary="同意申请（仅车主，扣座位）")
def approve_application(cid: int, aid: int, user: User = Depends(get_current_user),
                        session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    a = session.get(CarpoolApplication, aid)
    if not c or not a or a.carpool_id != cid:
        raise BizError(404, "申请不存在")
    if c.author_id != user.id:
        raise BizError(403, "只有车主可以处理申请")
    if a.status != "pending":
        raise BizError(400, "该申请已处理")
    if c.seats_left < a.people_count:
        raise BizError(400, f"剩余座位不足（剩余 {c.seats_left} 座，申请 {a.people_count} 人）")
    c.seats_left -= a.people_count
    if c.seats_left == 0:
        c.status = "full"
    a.status = "approved"
    session.add(c)
    session.add(a)
    session.commit()
    session.refresh(c)
    session.refresh(a)
    return ok({"seats_left": c.seats_left, "status": c.status, "application_status": a.status},
              "已同意申请，座位已扣减")


@router.post("/carpools/{cid}/applications/{aid}/reject", summary="拒绝申请（仅车主）")
def reject_application(cid: int, aid: int, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    c = session.get(Carpool, cid)
    a = session.get(CarpoolApplication, aid)
    if not c or not a or a.carpool_id != cid:
        raise BizError(404, "申请不存在")
    if c.author_id != user.id:
        raise BizError(403, "只有车主可以处理申请")
    if a.status != "pending":
        raise BizError(400, "该申请已处理")
    a.status = "rejected"
    session.add(a)
    session.commit()
    return ok({"application_status": "rejected"}, "已拒绝该申请")


@router.post("/carpools/{cid}/applications/{aid}/cancel", summary="取消申请（仅申请人本人）")
def cancel_application(cid: int, aid: int, user: User = Depends(get_current_user),
                       session: Session = Depends(get_session)):
    a = session.get(CarpoolApplication, aid)
    if not a or a.carpool_id != cid:
        raise BizError(404, "申请不存在")
    if a.applicant_id != user.id:
        raise BizError(403, "只能取消自己的申请")
    if a.status == "approved":
        raise BizError(400, "申请已被车主同意，请联系车主处理")
    if a.status not in ("pending", "rejected"):
        raise BizError(400, "该申请当前状态不可取消")
    a.status = "cancelled"
    session.add(a)
    session.commit()
    return ok({"application_status": "cancelled"}, "已取消申请")


def _app_to_dict(a: CarpoolApplication) -> dict:
    return {
        "id": a.id, "carpool_id": a.carpool_id,
        "applicant_id": a.applicant_id, "applicant_name": a.applicant_name,
        "phone": a.phone, "people_count": a.people_count,
        "remark": a.remark or "", "status": a.status,
        "created_at": a.created_at.isoformat(),
    }


