"""管理员模块（归属：后端 D）

提供：
- ensure_admin_account：启动时确保内置 admin 账号存在（admin/admin）
- get_current_admin：FastAPI 依赖，校验当前登录用户是管理员

管理员登录仍走 /api/user/login（验证码 + 限流），后端通过 user_public 返回
is_admin 标识，前端据此路由到管理后台。
"""
from fastapi import Depends, Request
from sqlmodel import Session, select

from app.core.response import BizError
from app.core.security import get_current_user, hash_password
from app.db import get_session
from app.models import User

# 内置管理员账号（用户明确要求 admin/admin）
_ADMIN_USERNAME = "admin"
_ADMIN_PASSWORD = "admin"
_ADMIN_NICKNAME = "系统管理员"


def ensure_admin_account(session: Session) -> None:
    """确保内置 admin 账号存在；不存在则创建（密码 admin，is_admin=True）。

    幂等：已存在则跳过，不覆盖密码与权限。启动时调用。
    """
    exists = session.exec(
        select(User).where(User.username == _ADMIN_USERNAME)
    ).first()
    if exists is not None:
        return
    admin = User(
        username=_ADMIN_USERNAME,
        nickname=_ADMIN_NICKNAME,
        password_hash=hash_password(_ADMIN_PASSWORD),
        is_admin=True,
    )
    session.add(admin)
    session.commit()


def get_current_admin(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """FastAPI 依赖：校验当前登录用户是管理员，否则返回 1011。

    用法：def xxx(admin: User = Depends(get_current_admin)): ...
    """
    user = get_current_user(request, session)
    if not getattr(user, "is_admin", False):
        raise BizError(1011, "需要管理员权限")
    return user
