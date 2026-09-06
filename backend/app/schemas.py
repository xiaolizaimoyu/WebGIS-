"""接口请求体模型（归属：后端 F）

前端 POST 的 JSON 都会经过这里的字段校验（Pydantic），
格式不对会统一返回 code=400 + 具体原因。
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=30, description="登录账号，2-30位")
    nickname: str = Field(min_length=1, max_length=30, description="昵称")
    password: str = Field(min_length=6, max_length=64, description="密码，至少6位")


class LoginIn(BaseModel):
    username: str
    password: str


class ContentIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=5000)
    type: str = Field(description="meeting | news | food | lost（已下线 activity / ad）")
    category: Optional[str] = Field(default=None, max_length=20)
    images: List[str] = Field(default_factory=list)
    # 地图选点坐标（可空；两端需同时给才生效）
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class ProfileUpdateIn(BaseModel):
    """个人资料更新：字段为 None 表示不改，avatar 传空串 "" 表示清除头像。"""

    nickname: Optional[str] = Field(default=None, min_length=1, max_length=30)
    avatar: Optional[str] = Field(default=None, max_length=200)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64)
