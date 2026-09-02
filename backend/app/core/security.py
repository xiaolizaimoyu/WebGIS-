"""安全模块（归属：后端 F）

提供密码哈希校验与 JWT 签发/解析，以及「获取当前登录用户」的依赖。
后端 D 的登录接口、E 的发布类接口都会用到。
"""
import bcrypt
import jwt
from fastapi import Depends, Request
from sqlmodel import Session

from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, SECRET_KEY
from app.core.response import BizError
from app.db import get_session
from app.models import User


# ---------- 密码哈希 ----------
def hash_password(password: str) -> str:
    """明文密码 -> bcrypt 哈希串（加盐，安全性足够）。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与哈希串是否匹配。"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------- JWT ----------
def create_token(user_id: int) -> str:
    """为指定用户签发 JWT，含过期时间。"""
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> int:
    """解析 JWT，返回其中的用户 id。失败抛 BizError(401)。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise BizError(401, "登录已过期，请重新登录")


# ---------- 获取当前登录用户（供接口 Depends 使用） ----------
def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """从请求头 Authorization: Bearer <token> 解析当前用户。

    需要鉴权的接口这样声明即可：
        def xxx(user: User = Depends(get_current_user)): ...
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise BizError(401, "请先登录")
    user_id = decode_token(auth.removeprefix("Bearer ").strip())
    user = session.get(User, user_id)
    if user is None:
        raise BizError(401, "用户不存在，请重新登录")
    return user
