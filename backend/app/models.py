"""数据表模型（归属：后端 F，全项目唯一建表来源）

三张表：
- users     用户
- contents  内容（活动/会议/动态/广告 统一一张表，type 区分）
- comments  评论

改动表结构请统一在此修改，并由 db.create_db_and_tables() 重建。
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """用户表"""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, description="登录账号，唯一")
    nickname: str = Field(description="展示昵称")
    password_hash: str = Field(description="bcrypt 哈希，绝不返回给前端")
    created_at: datetime = Field(default_factory=datetime.now)


class Content(SQLModel, table=True):
    """内容表：活动 activity / 会议 meeting / 动态 news / 广告 ad，由 type 区分"""

    __tablename__ = "contents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(description="标题")
    body: str = Field(description="正文")
    type: str = Field(index=True, description="activity | meeting | news | ad")
    category: Optional[str] = Field(default=None, description="二级子分类，如广告：闲置/求助/宣传")
    images: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="图片 URL 列表，如 ['/uploads/xxx.png']",
    )
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
