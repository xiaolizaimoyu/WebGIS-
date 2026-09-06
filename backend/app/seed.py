"""演示数据生成脚本（归属：后端 F / 组长工具）

用途：给空数据库填充一批“AI 模拟数据”，让首页/详情/评论有内容可演示。

运行（在 backend 目录下）：
    .venv\\Scripts\\python -m app.seed

行为：
- 幂等：每次运行会先删除上一批“演示数据”再重建，可重复执行；
  演示账号统一密码 123456（登录答辩用），前缀 demo_ 便于识别。
- 只清理演示数据，绝不触碰真实用户/帖子。
- 自动在 uploads/ 生成若干渐变占位图 demo_*.png，帖子带图可正常显示。
"""
import math
import struct
import zlib
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import UPLOAD_DIR
from app.core.security import hash_password
from app.db import engine
from app.models import Comment, Content, User

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
# 与前端 const.js 的 MAP_CONFIG.center 保持一致（坐标方向：经度, 纬度）。
MAP_CENTER = (118.001917, 36.814013)


def _spot(index: int):
    """按帖子下标生成一个稳定（可重复、幂等）的校园内偏移点，模拟不同场所位置。"""
    radius = 0.0007 + (index % 5) * 0.0005  # 约 80~350 米
    angle = math.radians((index * 137.5) % 360)
    return (MAP_CENTER[0] + radius * math.cos(angle), MAP_CENTER[1] + radius * math.sin(angle))


# 这些下标的帖子不绑坐标（演示“无位置内容不出现在地图”）
NO_COORD = {4}

# (title, body, type, category, images_index_list, author_index, 距现在的分钟)
# 说明：已下线「校园活动 activity / 校园广告 ad」两类，仅保留
#       会议 meeting / 动态 news / 美食 food / 失物招领 lost。
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
    ("寻物：黑色保温杯", "昨天下午落在操场看台的黑色保温杯，杯身有“奋斗”贴纸，捡到的同学请联系我，谢谢！", "lost", None, [1], 1, 1200),
]

# (帖子在 POSTS 中的下标, 评论作者下标, 评论内容)
COMMENTS = [
    (0, 1, "例会几点开始呀？需要提前到场吗？"),
    (0, 2, "各部门汇报材料需要提前准备吗？"),
    (1, 3, "张教授的讲座听过，讲得很好，推荐！"),
    (5, 0, "集市几点开市呀？有什么摊位？"),
    (6, 2, "麻辣香锅确实好吃，中辣够味！"),
    (9, 4, "保温杯是什么牌子的？我好像看到过。"),
]

# ---------------- 占位图生成（纯标准库，无需 Pillow） ----------------
PALETTES = [
    ((79, 172, 254), (111, 220, 143)),   # 蓝→绿
    ((255, 153, 102), (255, 94, 98)),    # 橙→红
    ((106, 90, 205), (200, 180, 254)),   # 蓝紫→浅紫
    ((255, 182, 66), (255, 220, 150)),   # 金黄→浅黄
    ((72, 202, 228), (63, 142, 240)),    # 青→蓝
    ((255, 111, 145), (255, 183, 160)),  # 粉→橙
]


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def make_gradient_png(path: Path, top: tuple, bottom: tuple, width=640, height=400) -> None:
    """生成一张竖向渐变 PNG（无第三方依赖）。"""
    rows = []
    for y in range(height):
        t = y / max(height - 1, 1)
        r = round(top[0] + (bottom[0] - top[0]) * t)
        g = round(top[1] + (bottom[1] - top[1]) * t)
        b = round(top[2] + (bottom[2] - top[2]) * t)
        rows.append(b"\x00" + bytes([r, g, b]) * width)  # filter=0
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
    """生成 demo_1.png..demo_n.png，返回相对 URL 列表。"""
    # 先清掉旧的演示占位图
    for old in UPLOAD_DIR.glob("demo_*.png"):
        old.unlink()
    urls = []
    for i, (top, bottom) in enumerate(PALETTES, start=1):
        name = f"demo_{i}.png"
        make_gradient_png(UPLOAD_DIR / name, top, bottom)
        urls.append(f"/uploads/{name}")
    return urls


# ---------------- 主流程 ----------------
def run() -> None:
    with Session(engine) as session:
        # 1) 清掉上一批演示数据（只清 demo_ 账号产生的内容与账号）
        demo_users = session.exec(select(User).where(User.username.like("demo\\_%", escape="\\"))).all()
        demo_ids = [u.id for u in demo_users]
        if demo_ids:
            comments = session.exec(select(Comment).where(Comment.author_id.in_(demo_ids))).all()
            contents = session.exec(select(Content).where(Content.author_id.in_(demo_ids))).all()
            for c in comments:
                session.delete(c)
            for ct in contents:
                session.delete(ct)
            for u in demo_users:
                session.delete(u)
            session.commit()

        # 2) 生成占位图
        img_urls = make_placeholder_images()

        # 3) 创建演示用户
        now = datetime.now()
        users = []
        for username, nickname in USERS:
            user = User(username=username, nickname=nickname, password_hash=hash_password(DEMO_PASSWORD))
            session.add(user)
            users.append(user)
        session.commit()
        for u in users:
            session.refresh(u)

        # 4) 创建演示帖子（created_at 从最近到稍早，制造时间线）
        created = []
        for idx, (title, body, ctype, category, img_idx, author_idx, ago_min) in enumerate(POSTS):
            loc = None if idx in NO_COORD else _spot(idx)
            content = Content(
                title=title,
                body=body,
                type=ctype,
                category=category,
                images=[img_urls[i] for i in img_idx],
                longitude=loc[0] if loc else None,
                latitude=loc[1] if loc else None,
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
            session.add(
                Comment(
                    content_id=created[post_idx].id,
                    author_id=users[author_idx].id,
                    body=body,
                    created_at=now - timedelta(minutes=max(5, POSTS[post_idx][5] + 1)),
                )
            )
        session.commit()

        # 6) 汇总
        print("演示数据已生成")
        print(f"  演示账号 {len(users)} 个（密码统一 {DEMO_PASSWORD}）：")
        for u in users:
            print(f"    - {u.username}（{u.nickname}）")
        print(f"  帖子 {len(created)} 条，评论 {len(COMMENTS)} 条")
        print(f"  占位图 {len(img_urls)} 张（uploads/demo_*.png）")
        print("  登录后即可在首页/我的发布中看到这些演示内容。")


if __name__ == "__main__":
    run()
