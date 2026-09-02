"""用户认证模块（归属：后端 D）

只处理用户相关业务：注册 / 登录 / 当前用户信息。
- 前缀 /api/user
- 密码只存 bcrypt 哈希，绝不返回明文
- 登录成功签发 JWT，前端保存 token 后带在请求头调用受保护接口
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.response import BizError, ok
from app.core.security import create_token, get_current_user, hash_password, verify_password
from app.db import get_session
from app.models import User
from app.schemas import LoginIn, RegisterIn

router = APIRouter(prefix="/api/user", tags=["用户认证"])


def user_public(user: User) -> dict:
    """对外暴露的用户信息（去掉密码哈希）。"""
    return {"id": user.id, "username": user.username, "nickname": user.nickname}


@router.post("/register", summary="注册")
def register(data: RegisterIn, session: Session = Depends(get_session)):
    exists = session.exec(select(User).where(User.username == data.username)).first()
    if exists:
        raise BizError(1002, "该用户名已被注册")
    user = User(
        username=data.username,
        nickname=data.nickname,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return ok(user_public(user), "注册成功")


@router.post("/login", summary="登录")
def login(data: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == data.username)).first()
    # 账号或密码错误统一文案，避免泄露哪个不对
    if user is None or not verify_password(data.password, user.password_hash):
        raise BizError(1001, "用户名或密码错误")
    token = create_token(user.id)
    return ok({"token": token, "user": user_public(user)}, "登录成功")


@router.get("/me", summary="当前登录用户")
def me(user: User = Depends(get_current_user)):
    return ok(user_public(user))
