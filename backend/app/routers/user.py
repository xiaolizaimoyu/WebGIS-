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
from app.schemas import ChangePasswordIn, LoginIn, ProfileUpdateIn, RegisterIn

router = APIRouter(prefix="/api/user", tags=["用户认证"])


def user_public(user: User) -> dict:
    """对外暴露的用户信息（去掉密码哈希），注册/登录/me/更新资料共用同一结构。"""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "created_at": user.created_at,
    }


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


@router.put("/me", summary="更新个人资料（昵称/头像）")
def update_profile(
    data: ProfileUpdateIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # 字段为 None = 不改；avatar 传空串 "" = 清除头像
    if data.nickname is not None:
        user.nickname = data.nickname
    if data.avatar is not None:
        user.avatar = data.avatar or None
    session.add(user)
    session.commit()
    session.refresh(user)
    return ok(user_public(user), "资料已更新")


@router.put("/password", summary="修改密码")
def change_password(
    data: ChangePasswordIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, user.password_hash):
        raise BizError(1003, "原密码不正确")
    user.password_hash = hash_password(data.new_password)
    session.add(user)
    session.commit()
    return ok(None, "密码修改成功，下次请用新密码登录")
