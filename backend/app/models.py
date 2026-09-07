"""数据表模型（归属：后端 F，全项目唯一建表来源）

共 12 张表：
- users          用户（含积分）
- contents       内容（会议/动态/美食/失物，type 区分）
- comments       评论
- likes          点赞（用户-内容多对多）
- favorites      收藏
- notifications  通知（评论/点赞/系统）
- points_log     积分流水
- sign_records   签到记录
- mall_goods     积分商城商品
- orders         兑换订单
- follows        关注（用户-用户）
- carpools       组队拼车（发布/编辑/删除/申请）

改动表结构请统一在此修改，并由 db.create_db_and_tables() 自动建表/补列。
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


# ==================== 用户与内容（核心3表） ====================

class User(SQLModel, table=True):
    """用户表"""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, description="登录账号，唯一")
    nickname: str = Field(description="展示昵称")
    avatar: Optional[str] = Field(default=None, max_length=200, description="头像图片 URL（/uploads/xx），可空")
    password_hash: str = Field(description="bcrypt 哈希，绝不返回给前端")
    points: int = Field(default=0, description="积分余额，签到/发帖/评论增加，兑换商品扣减")
    created_at: datetime = Field(default_factory=datetime.now)


class Content(SQLModel, table=True):
    """内容表：会议 meeting / 动态 news / 美食 food / 失物招领 lost，由 type 区分（已下线 activity/ad）"""

    __tablename__ = "contents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(description="标题")
    body: str = Field(description="正文")
    type: str = Field(index=True, description="meeting | news | food | lost")
    category: Optional[str] = Field(default=None, description="二级子分类，可空")
    images: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="图片 URL 列表，如 ['/uploads/xxx.png']",
    )
    longitude: Optional[float] = Field(default=None, description="经度，未绑定位置为空")
    latitude: Optional[float] = Field(default=None, index=True, description="纬度，未绑定位置为空")
    view_count: int = Field(default=0, description="浏览量")
    like_count: int = Field(default=0, description="点赞数（冗余，避免每次 count 查询）")
    author_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Comment(SQLModel, table=True):
    """评论表"""

    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_id: int = Field(foreign_key="contents.id", index=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    body: str = Field(description="评论内容")
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== 互动（点赞/收藏/关注） ====================

class Like(SQLModel, table=True):
    """点赞表：一个用户对一条内容只能点一次赞"""

    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "content_id", name="uq_user_content_like"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content_id: int = Field(foreign_key="contents.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Favorite(SQLModel, table=True):
    """收藏表：一个用户可以收藏多条内容"""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "content_id", name="uq_user_content_fav"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content_id: int = Field(foreign_key="contents.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Follow(SQLModel, table=True):
    """关注表：follower 关注 following"""

    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_follow_pair"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="users.id", index=True, description="关注者")
    following_id: int = Field(foreign_key="users.id", index=True, description="被关注者")
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== 通知 ====================

class Notification(SQLModel, table=True):
    """通知表：评论通知/点赞通知/系统通知"""

    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, description="被通知的用户")
    type: str = Field(description="comment | like | system | follow")
    title: str = Field(description="通知标题")
    body: str = Field(default="", description="通知内容")
    is_read: bool = Field(default=False, description="是否已读")
    related_id: Optional[int] = Field(default=None, description="关联的内容/评论ID，可空")
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== 积分与签到 ====================

class PointsLog(SQLModel, table=True):
    """积分流水表：每次积分变动都记录一条"""

    __tablename__ = "points_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    change: int = Field(description="变动积分，正数增加，负数扣减")
    balance_before: int = Field(description="变动前积分余额")
    balance_after: int = Field(description="变动后积分余额")
    reason: str = Field(description="变动原因：sign | post | comment | exchange | like | admin")
    created_at: datetime = Field(default_factory=datetime.now)


class SignRecord(SQLModel, table=True):
    """签到记录表：每个用户每天只能签一次"""

    __tablename__ = "sign_records"
    __table_args__ = (UniqueConstraint("user_id", "sign_date", name="uq_user_sign_date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    sign_date: date = Field(description="签到日期")
    points: int = Field(default=10, description="本次签到获得积分")
    continuous_days: int = Field(default=1, description="连续签到天数")
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== 积分商城 ====================

class MallGoods(SQLModel, table=True):
    """积分商城商品表"""

    __tablename__ = "mall_goods"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="商品名称")
    description: str = Field(default="", description="商品描述")
    image: Optional[str] = Field(default=None, max_length=200, description="商品图片 URL，可空")
    points_price: int = Field(description="兑换所需积分")
    stock: int = Field(default=-1, description="库存，-1 表示无限库存")
    status: str = Field(default="on", description="商品状态：on=上架，off=下架")
    category: Optional[str] = Field(default=None, description="商品分类，可空")
    created_at: datetime = Field(default_factory=datetime.now)


class Order(SQLModel, table=True):
    """兑换订单表：用户用积分兑换商品的记录"""

    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    goods_id: int = Field(foreign_key="mall_goods.id", index=True)
    goods_name: str = Field(description="兑换时商品名称快照")
    points_cost: int = Field(description="消耗积分")
    status: str = Field(default="pending", description="订单状态：pending=待处理，processed=已完成，cancelled=已取消")
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== 组队拼车 ====================

class Carpool(SQLModel, table=True):
    """拼车表：组队拼车发布/编辑/删除/申请（第 12 张表，归属：后端 C）"""

    __tablename__ = "carpools"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=60, description="拼车标题")
    from_: str = Field(max_length=50, description="出发地（from 为 SQL 关键字，模型用 from_ 映射）")
    to: str = Field(max_length=50, description="目的地")
    depart_time: str = Field(max_length=20, description="出发时间 YYYY-MM-DD HH:mm")
    return_time: str = Field(default="", max_length=20, description="返回时间，可空")
    seats_total: int = Field(default=4, description="总座位数 1-7")
    seats_left: int = Field(default=4, description="剩余座位数")
    price_per_person: float = Field(default=0, description="人均费用（元）")
    phone: str = Field(max_length=20, description="联系电话（11 位手机号）")
    note: str = Field(default="", max_length=500, description="备注说明")
    author_id: int = Field(foreign_key="users.id", index=True, description="发布者用户 ID")
    author_name: str = Field(max_length=30, description="发布者昵称快照")
    status: str = Field(default="recruiting", description="recruiting 招募中 / full 已满员 / closed 已关闭")
    created_at: datetime = Field(default_factory=datetime.now)
