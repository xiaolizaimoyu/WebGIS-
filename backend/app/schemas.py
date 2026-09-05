"""接口请求体模型（归属：后端 F）

前端 POST 的 JSON 都会经过这里的字段校验（Pydantic），
格式不对会统一返回 code=400 + 具体原因。
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(
        min_length=2,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="登录账号，2-30位，仅允许字母、数字、下划线、中横线",
    )
    nickname: str = Field(min_length=1, max_length=30, description="昵称")
    password: str = Field(min_length=6, max_length=64, description="密码，至少6位")


class LoginIn(BaseModel):
    username: str = Field(max_length=30, description="登录账号")
    password: str = Field(max_length=64, description="密码")


class ContentIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=5000)
    type: str = Field(description="activity | meeting | news | ad | food | lost")
    category: Optional[str] = Field(default=None, max_length=20)
    images: List[str] = Field(default_factory=list)
    # WebGIS 新增：地图选点经纬度，可不传；传则必须经/纬成对且范围合法
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="经度")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="纬度")


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class ProfileUpdateIn(BaseModel):
    """个人资料更新：字段为 None 表示不改，avatar 传空串 "" 表示清除头像。"""

    nickname: Optional[str] = Field(default=None, min_length=1, max_length=30)
    avatar: Optional[str] = Field(default=None, max_length=200)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64)
