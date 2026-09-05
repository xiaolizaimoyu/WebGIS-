"""安全模块（归属：后端 F）

提供密码哈希校验与 JWT 签发/解析，以及「获取当前登录用户」的依赖。
后端 D 的登录接口、E 的发布类接口都会用到。
"""
import time
import uuid
from datetime import datetime, timedelta, timezone

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
    """为指定用户签发 JWT，含过期时间、签发时间与唯一 id。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解析 JWT，返回完整 payload。失败抛 BizError(401)。"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise BizError(401, "登录已过期，请重新登录")


# ---------- Token 黑名单（登出 / 改密码后吊销，进程内实现） ----------
_blacklisted_tokens: dict[str, float] = {}


def blacklist_token(token: str, ttl_seconds: float | None = None) -> None:
    """将 token 加入黑名单，ttl 默认取 JWT 剩余有效期。

    进程内存储，服务重启后清空（token 本身也会自然过期）。
    """
    if ttl_seconds is None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            exp = payload.get("exp")
            ttl_seconds = max(exp - time.time(), 0) if exp else JWT_EXPIRE_MINUTES * 60
        except jwt.PyJWTError:
            ttl_seconds = 0
    if ttl_seconds > 0:
        _blacklisted_tokens[token] = time.time() + ttl_seconds


def _is_token_blacklisted(token: str) -> bool:
    """检查 token 是否在黑名单中，顺便清理已过期的黑名单条目。"""
    now = time.time()
    expired_keys = [k for k, v in _blacklisted_tokens.items() if v <= now]
    for k in expired_keys:
        _blacklisted_tokens.pop(k, None)
    return token in _blacklisted_tokens


# ---------- 获取当前登录用户（供接口 Depends 使用） ----------
def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """从请求头 Authorization: Bearer <token> 解析当前用户。

    需要鉴权的接口这样声明即可：
        def xxx(user: User = Depends(get_current_user)): ...

    会校验 token 是否在黑名单（登出 / 改密码后吊销）。
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise BizError(401, "请先登录")
    token = auth.removeprefix("Bearer ").strip()
    if _is_token_blacklisted(token):
        raise BizError(401, "登录已过期，请重新登录")
    payload = decode_token(token)
    user = session.get(User, int(payload["sub"]))
    if user is None:
        raise BizError(401, "用户不存在，请重新登录")
    return user
