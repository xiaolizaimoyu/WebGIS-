"""演示数据生成脚本（归属：后端 F / 组长工具）

用途：给空数据库填充一批"AI 模拟数据"，让首页/详情/评论/商城/积分有内容可演示。

运行（在 backend 目录下）：
    .venv\\Scripts\\python -m app.seed             # 默认：保留已有积分/签到，只补缺失数据
    .venv\\Scripts\\python -m app.seed --reset    # 强制：删除全部演示数据后重建

行为：
- 默认模式：若 demo 用户已存在，保留其积分/签到/流水/帖子（签到积分不会被重置），
  仅补齐缺失的商城商品与拼车数据；空库时自动全量初始化。
- --reset：删除上一批全部演示数据（含积分/签到记录）再重建，可重复执行；
  演示账号统一密码 123456（登录答辩用），前缀 demo_ 便于识别。
- 只清理演示数据，绝不触碰真实用户/帖子。
- 自动在 uploads/ 生成若干渐变占位图 demo_*.png，帖子带图可正常显示。
- 覆盖 12 张表：users / contents / comments / likes / favorites / follows /
  notifications / points_log / sign_records / mall_goods / orders / carpools。
"""
import math
import struct
import sys
import zlib
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import UPLOAD_DIR
from app.core.security import hash_password
from app.db import engine
from app.models import (Carpool, CarpoolApplication, Comment, Content, Favorite, Follow, Like, MallGoods,
                        Notification, Order, PointsLog, SignRecord, User)

# ---------------- 配置 ----------------
DEMO_PASSWORD = "123456"

USERS = [
    ("demo_wang", "王小明"),
    ("demo_li", "李华"),
    ("demo_zhao", "赵敏"),
    ("demo_chen", "陈晨"),
    ("demo_lin", "林一"),
]

# 校园中心坐标——演示数据围绕它生成点位（山东理工大学西校区，淄博·新村西路266号）。
MAP_CENTER = (118.001917, 36.814013)

# 校园地点库（与前端 frontend/src/api/const.js CAMPUS_PLACES 保持一致）
# (名称, 经度, 纬度)
CAMPUS_PLACES = [
    ("北门（新村西路）", 118.0008, 36.8162),
    ("图书馆", 118.0005, 36.8148),
    ("鸿远楼（行政楼）", 118.0016, 36.8139),
    ("一号教学楼", 118.0030, 36.8156),
    ("二号教学楼", 118.0019, 36.8154),
    ("三号教学楼", 117.9999, 36.8132),
    ("逸夫楼", 118.0004, 36.8123),
    ("第一食堂（一餐）", 118.0041, 36.8153),
    ("第二食堂（二餐）", 118.0036, 36.8127),
    ("第三食堂（三餐）", 117.9996, 36.8151),
    ("体育馆", 118.0052, 36.8132),
    ("田径场", 118.0044, 36.8141),
    ("学生公寓区", 118.0022, 36.8166),
    ("大学生事务中心", 118.0009, 36.8138),
    ("校医院", 117.9991, 36.8143),
    ("东门", 118.0068, 36.8140),
    ("南门", 118.0019, 36.8122),
]


def _nearest_place(lng: float, lat: float) -> str:
    """按经纬度返回最近的校园地点名（平面近似即可）。"""
    best, best_d = None, 1e9
    for name, plng, plat in CAMPUS_PLACES:
        d = (plng - lng) ** 2 + (plat - lat) ** 2
        if d < best_d:
            best, best_d = name, d
    return best


def _spot(index: int):
    """按帖子下标生成一个稳定（可重复、幂等）的校园内偏移点。"""
    radius = 0.0007 + (index % 5) * 0.0005
    angle = math.radians((index * 137.5) % 360)
    return (MAP_CENTER[0] + radius * math.cos(angle), MAP_CENTER[1] + radius * math.sin(angle))



# 每篇帖子绑定的真实校园地点（帖子文本提到哪就绑哪，地图点位落在对应位置）
POSTS_LOCATION = {
    0: "一号教学楼",   # 学生会例会（一号教学楼 201）
    1: "逸夫楼",       # 学术讲座（逸夫楼报告厅）
    2: "三号教学楼",   # 班级班会
    3: "第一食堂（一餐）",  # 食堂二楼自选窗口
    4: "图书馆",       # 图书馆延长开放
    5: "第一食堂（一餐）",  # 一食堂门口二手集市
    6: "第二食堂（二餐）",  # 二食堂三楼麻辣香锅
    7: "图书馆",       # 图书馆咖啡厅
    8: "二号教学楼",   # 二教 201 拾到校园卡
    9: "田径场",       # 操场看台
}


# (title, body, type, category, images_index_list, author_index, 距现在的分钟)
POSTS = [
    ("学生会第3次例会通知", "本周四 18:30 在一号教学楼 201 召开学生会例会，各部门汇报近期工作，请准时参加。", "meeting", None, [], 1, 120),
    ("学术讲座：AI 时代与未来职业", "本周三晚学校邀请张教授作专题讲座，地点：逸夫楼报告厅，欢迎大家前来聆听。", "meeting", None, [2], 2, 900),
    ("班级班会提醒", "下周一早自习班会，主题：期中考试动员与学习经验分享，请勿迟到。", "meeting", None, [], 3, 1500),
    ("食堂二楼新开自选窗口啦", "二楼新开了自选快餐窗口，荤素搭配，价格实惠，中午人多建议错峰。", "news", None, [3], 2, 90),
    ("图书馆期末延长开放至23点", "临近期末，图书馆阅览室开放时间延长到 23:00，记得提前预约座位哦。", "news", None, [], 0, 500),
    ("校园二手集市这周末开市", "周六周日在一食堂门口广场举办二手集市，闲置物品交换出售，欢迎来逛！", "news", None, [4], 3, 1000),
    ("二食堂三楼新开麻辣香锅", "推荐二食堂三楼的麻辣香锅，中辣很带劲，一份 18 元，饭点人超多，建议错峰来吃！", "food", None, [3], 2, 60),
    ("图书馆咖啡厅的美式", "图书馆一楼咖啡厅的美式只要 12 块，自习累了来一杯提神，配三明治也不错～", "food", None, [], 0, 700),
    ("招领：拾到一张校园卡", "在二教 201 拾到校园卡一张（卡主姓张），请失主到二教值班室认领。", "lost", None, [], 3, 200),
    ("寻物：黑色保温杯", "昨天下午落在操场看台的黑色保温杯，杯身有「奋斗」贴纸，捡到的同学请联系我，谢谢！", "lost", None, [1], 1, 1200),
]

COMMENTS = [
    (0, 1, "例会几点开始呀？需要提前到场吗？"),
    (0, 2, "各部门汇报材料需要提前准备吗？"),
    (1, 3, "张教授的讲座听过，讲得很好，推荐！"),
    (5, 0, "集市几点开市呀？有什么摊位？"),
    (6, 2, "麻辣香锅确实好吃，中辣够味！"),
    (9, 4, "保温杯是什么牌子的？我好像看到过。"),
]

# 组队拼车演示数据（from 为 SQL 关键字，常量名用 frm）
# (发布者序号, 标题, 出发地, 目的地, 出发时间, 座位, 人均费用, 手机号, 备注)
CARPOOLS = [
    (0, "周末去济南火车站拼车", "学校东门", "济南站", "2026-09-12 08:00", 4, 50, "13800001001",
     "AA制，人均约50元，含油费过路费。"),
    (1, "周五晚回淄博拼车", "学校北门", "淄博站", "2026-09-11 18:00", 3, 30, "13900002002",
     "下班时间出发，可带小件行李。"),
    (2, "国庆去青岛玩拼车", "学校南门", "青岛五四广场", "2026-10-01 07:00", 5, 120, "13700003003",
     "三天两夜，行程可商量，有学生证优先。"),
    (3, "去高铁站拼车（随时出发）", "学校北门", "淄博北站", "2026-09-10 15:00", 4, 40, "13600004004",
     "赶高铁拼车，随时可走，后备箱能放大行李箱。"),
]


# 积分商城演示商品
MALL_GOODS = [
    ("演示-校园定制笔记本", "校园风景封面，A5 尺寸，100页", 100, 50, "文具", "/mall/goods_1.jpg"),
    ("演示-定制马克杯", "陶瓷马克杯，可印校园logo，350ml", 150, 30, "生活用品", "/mall/goods_2.jpg"),
    ("演示-食堂代金券5元", "校内食堂通用，无门槛", 200, 100, "餐饮", "/mall/goods_3.jpg"),
    ("演示-图书馆免占座券", "期末周专用，一次免预约占座", 300, 20, "服务", "/mall/goods_4.jpg"),
    ("演示-校园文化衫", "纯棉短袖，校园logo印花，M/L/XL", 500, 15, "服饰", "/mall/goods_5.jpg"),
    ("演示-蓝牙耳机", "入门级蓝牙耳机，续航4小时", 800, 5, "数码", "/mall/goods_6.jpg"),
    ("演示-充电宝10000mAh", "轻薄便携，双向快充", 1200, 8, "数码", "/mall/goods_7.jpg"),
]


# ---------------- 占位图生成（纯标准库，无需 Pillow） ----------------
PALETTES = [
    ((79, 172, 254), (111, 220, 143)),
    ((255, 153, 102), (255, 94, 98)),
    ((106, 90, 205), (200, 180, 254)),
    ((255, 182, 66), (255, 220, 150)),
    ((72, 202, 228), (63, 142, 240)),
    ((255, 111, 145), (255, 183, 160)),
]


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def make_gradient_png(path: Path, top: tuple, bottom: tuple, width=640, height=400) -> None:
    rows = []
    for y in range(height):
        t = y / max(height - 1, 1)
        r = round(top[0] + (bottom[0] - top[0]) * t)
        g = round(top[1] + (bottom[1] - top[1]) * t)
        b = round(top[2] + (bottom[2] - top[2]) * t)
        rows.append(b"\x00" + bytes([r, g, b]) * width)
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw, 6))
        + _png_chunk(b"IEND", b"")
    )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def make_placeholder_images() -> list:
    for old in UPLOAD_DIR.glob("demo_*.png"):
        old.unlink()
    urls = []
    for i, (top, bottom) in enumerate(PALETTES, start=1):
        name = f"demo_{i}.png"
        make_gradient_png(UPLOAD_DIR / name, top, bottom)
        urls.append(f"/uploads/{name}")
    return urls


# ---------------- 主流程 ----------------
def run(reset: bool = False) -> None:
    with Session(engine) as session:
        now = datetime.now()

        # 1) 清掉上一批演示数据
        demo_users = session.exec(select(User).where(User.username.like("demo\\_%", escape="\\"))).all()

        # 0) 保护：非 --reset 且 demo 用户已存在 -> 保留积分/签到/帖子，只补缺失的商城与拼车
        if demo_users and not reset:
            old_goods = session.exec(select(MallGoods).where(MallGoods.name.like("演示%"))).all()
            has_carpool = session.exec(select(Carpool)).first()
            if not old_goods:
                for name, desc, price, stock, category, image in MALL_GOODS:
                    session.add(MallGoods(name=name, description=desc, image=image,
                                          points_price=price, stock=stock, status="on", category=category))
            if not has_carpool:
                for i, title, frm, to, depart_time, seats, price, phone, note in CARPOOLS:
                    session.add(Carpool(
                        title=title, from_=frm, to=to, depart_time=depart_time,
                        seats_total=seats, seats_left=seats, price_per_person=price,
                        phone=phone, note=note, author_id=demo_users[i % len(demo_users)].id,
                        author_name=demo_users[i % len(demo_users)].nickname,
                        status="recruiting",
                        created_at=now - timedelta(hours=3 * (i + 1)),
                    ))
            session.commit()
            print("已存在演示用户：保留积分/签到数据，仅补齐缺失数据。")
            print("如需重置演示数据（含积分/签到），请运行：python -m app.seed --reset")
            return

        demo_ids = [u.id for u in demo_users]
        if demo_ids:
            for model in [Like, Favorite, Notification, PointsLog, SignRecord, Order]:
                items = session.exec(select(model).where(model.user_id.in_(demo_ids))).all()
                for item in items:
                    session.delete(item)
            follows = session.exec(
                select(Follow).where((Follow.follower_id.in_(demo_ids)) | (Follow.following_id.in_(demo_ids)))
            ).all()
            for f in follows:
                session.delete(f)
            comments = session.exec(select(Comment).where(Comment.author_id.in_(demo_ids))).all()
            contents = session.exec(select(Content).where(Content.author_id.in_(demo_ids))).all()
            carpools = session.exec(select(Carpool).where(Carpool.author_id.in_(demo_ids))).all()
            for c in comments:
                session.delete(c)
            for ct in contents:
                session.delete(ct)
            for cp in carpools:
                # 先删该拼车下的申请记录（外键依赖）
                apps = session.exec(
                    select(CarpoolApplication).where(CarpoolApplication.carpool_id == cp.id)
                ).all()
                for a in apps:
                    session.delete(a)
                session.delete(cp)
            # 演示用户提交过的拼车申请（申请他人拼车）
            apps_by_demo = session.exec(
                select(CarpoolApplication).where(CarpoolApplication.applicant_id.in_(demo_ids))
            ).all()
            for a in apps_by_demo:
                session.delete(a)
            for u in demo_users:
                session.delete(u)
        old_goods = session.exec(select(MallGoods).where(MallGoods.name.like("演示%"))).all()
        for g in old_goods:
            session.delete(g)
        session.commit()

        # 2) 生成占位图
        img_urls = make_placeholder_images()

        # 3) 创建演示用户（带初始积分）
        users = []
        for i, (username, nickname) in enumerate(USERS):
            user = User(username=username, nickname=nickname,
                        password_hash=hash_password(DEMO_PASSWORD),
                        points=100 + i * 50)  # 初始积分 100/150/200/250/300
            session.add(user)
            users.append(user)
        session.commit()
        for u in users:
            session.refresh(u)

        # 4) 创建演示帖子
        created = []
        for idx, (title, body, ctype, category, img_idx, author_idx, ago_min) in enumerate(POSTS):
            loc = None
            place = POSTS_LOCATION.get(idx)
            if place:
                for pname, plng, plat in CAMPUS_PLACES:
                    if pname == place:
                        # 稳定微偏移，避免同地点的帖子点位完全重叠
                        off_lng = ((idx % 3) - 1) * 0.00012
                        off_lat = ((idx // 3) % 3 - 1) * 0.00012
                        loc = (round(plng + off_lng, 6), round(plat + off_lat, 6))
                        break
            content = Content(
                title=title, body=body, type=ctype, category=category,
                images=[img_urls[i] for i in img_idx],
                longitude=loc[0] if loc else None,
                latitude=loc[1] if loc else None,
                location_name=place if loc else None,
                like_count=idx % 4,  # 模拟点赞数
                author_id=users[author_idx].id,
                created_at=now - timedelta(minutes=ago_min),
            )
            session.add(content)
            created.append(content)
        session.commit()
        for c in created:
            session.refresh(c)

        # 5) 演示评论
        for post_idx, author_idx, body in COMMENTS:
            session.add(Comment(
                content_id=created[post_idx].id,
                author_id=users[author_idx].id,
                body=body,
                created_at=now - timedelta(minutes=max(5, POSTS[post_idx][6] + 1)),
            ))
        session.commit()

        # 6) 演示点赞（每个用户点赞前3条内容）
        for u in users:
            for c in created[:3]:
                session.add(Like(user_id=u.id, content_id=c.id,
                                 created_at=now - timedelta(hours=1)))
        session.commit()

        # 7) 演示收藏（每个用户收藏第1、4条内容）
        for u in users:
            for idx in [0, 3]:
                session.add(Favorite(user_id=u.id, content_id=created[idx].id,
                                     created_at=now - timedelta(hours=2)))
        session.commit()

        # 8) 演示关注（用户0关注1、2；用户1关注0、3）
        session.add(Follow(follower_id=users[0].id, following_id=users[1].id))
        session.add(Follow(follower_id=users[0].id, following_id=users[2].id))
        session.add(Follow(follower_id=users[1].id, following_id=users[0].id))
        session.add(Follow(follower_id=users[1].id, following_id=users[3].id))
        session.commit()

        # 9) 演示签到记录（昨天起往前 3 天，不包含今天——今天留待真实签到）
        for i, u in enumerate(users):
            for day_offset in range(3):
                sign_date = date.today() - timedelta(days=day_offset + 1)
                continuous = 3 - day_offset + i  # 模拟不同连续天数
                points = 10 + (20 if continuous % 7 == 0 else 0)
                session.add(SignRecord(
                    user_id=u.id, sign_date=sign_date,
                    points=points, continuous_days=continuous,
                    created_at=now - timedelta(days=day_offset),
                ))
                # 积分流水
                session.add(PointsLog(
                    user_id=u.id, change=points,
                    balance_before=u.points - points,
                    balance_after=u.points,
                    reason="sign",
                    created_at=now - timedelta(days=day_offset + 1),
                ))
        session.commit()

        # 10) 演示商城商品
        goods_list = []
        for name, desc, price, stock, category, image in MALL_GOODS:
            g = MallGoods(name=name, description=desc, image=image,
                          points_price=price, stock=stock, status="on", category=category)
            session.add(g)
            goods_list.append(g)
        session.commit()
        for g in goods_list:
            session.refresh(g)

                # 12) 演示通知（每个用户2条：1条系统通知，1条评论通知）
        for u in users:
            session.add(Notification(
                user_id=u.id, type="system",
                title="欢迎使用校园活动交流平台",
                body="完善个人资料，发布第一条内容，获得积分奖励！",
                is_read=False,
            ))
            session.add(Notification(
                user_id=u.id, type="comment",
                title="有人评论了你的内容",
                body=f"{users[(u.id + 1) % len(users)].nickname} 评论了你的发布",
                is_read=True, related_id=created[0].id,
            ))
        session.commit()

        # 12) 演示拼车（carpools 表）
        carpool_list = []
        for i, title, frm, to, depart_time, seats, price, phone, note in CARPOOLS:
            c = Carpool(
                title=title, from_=frm, to=to, depart_time=depart_time,
                seats_total=seats, seats_left=seats, price_per_person=price,
                phone=phone, note=note, author_id=users[i % len(users)].id,
                author_name=users[i % len(users)].nickname,
                status="recruiting",
                created_at=now - timedelta(hours=3 * (i + 1)),
            )
            session.add(c)
            carpool_list.append(c)
        session.commit()

        # 13) 汇总
        print("=" * 50)
        print("演示数据已生成（12张表全部填充）")
        print(f"  演示账号 {len(users)} 个（密码统一 {DEMO_PASSWORD}）：")
        for u in users:
            print(f"    - {u.username}（{u.nickname}）积分: {u.points}")
        print(f"  帖子 {len(created)} 条，评论 {len(COMMENTS)} 条")
        print(f"  点赞 {len(users) * 3} 条，收藏 {len(users) * 2} 条，关注 4 条")
        print(f"  签到记录 {len(users) * 3} 条，积分流水 {len(users) * 3 + 2} 条")
        print(f"  商城商品 {len(goods_list)} 个，兑换订单 2 条")
        print(f"  拼车 {len(CARPOOLS)} 条")
        print(f"  通知 {len(users) * 2} 条")
        print(f"  占位图 {len(img_urls)} 张（uploads/demo_*.png）")
        print("=" * 50)
        print("登录后即可在首页/商城/个人中心看到完整演示内容。")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
