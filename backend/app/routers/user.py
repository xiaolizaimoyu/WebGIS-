"""用户认证模块（归属：后端 D）

只处理用户相关业务：注册 / 登录 / 当前用户信息。
- 前缀 /api/user
- 密码只存 bcrypt 哈希，绝不返回明文
- 登录成功签发 JWT，前端保存 token 后带在请求头调用受保护接口
"""
import logging
import time

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from app.core.response import BizError, ok
from app.core.security import (
    blacklist_token,
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import get_session
from app.models import User
from app.schemas import ChangePasswordIn, LoginIn, ProfileUpdateIn, RegisterIn

router = APIRouter(prefix="/api/user", tags=["用户认证"])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)

# ---------- 登录限流（防爆破，进程内实现，重启后清零） ----------
_LOGIN_MAX_FAILS = 5            # 连续失败阈值
_LOGIN_LOCK_SECONDS = 15 * 60   # 触发阈值后锁定 15 分钟
_login_failures: dict[str, dict] = {}


def _client_ip(request: Request) -> str:
    """取真实客户端 IP，兼容 vite/反代 X-Forwarded-For。"""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_login_limit(username: str, ip: str) -> None:
    """超阈值且在锁定期内则拒绝登录。"""
    rec = _login_failures.get(f"{username}:{ip}")
    if not rec:
        return
    locked_until = rec.get("locked_until", 0)
    if locked_until and locked_until > time.time():
        remain = int((locked_until - time.time()) / 60) + 1
        logger.warning("登录限流触发 username=%s ip=%s", username, ip)
        raise BizError(1004, f"登录失败次数过多，请 {remain} 分钟后再试")


def _record_login_failure(username: str, ip: str) -> None:
    """记录一次失败，达到阈值则锁定。"""
    key = f"{username}:{ip}"
    rec = _login_failures.setdefault(key, {"count": 0, "locked_until": 0})
    rec["count"] += 1
    if rec["count"] >= _LOGIN_MAX_FAILS and not rec["locked_until"]:
        rec["locked_until"] = time.time() + _LOGIN_LOCK_SECONDS
        logger.warning("账号登录失败锁定 username=%s ip=%s fails=%d", username, ip, rec["count"])


def _clear_login_failure(username: str, ip: str) -> None:
    """登录成功后清除失败记录。"""
    _login_failures.pop(f"{username}:{ip}", None)


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
def register(data: RegisterIn, request: Request, session: Session = Depends(get_session)):
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
    logger.info("注册成功 username=%s ip=%s", data.username, _client_ip(request))
    # 注册即登录：直接签发 token，前端无需再调用登录接口
    token = create_token(user.id)
    return ok({"token": token, "user": user_public(user)}, "注册成功")


@router.post("/login", summary="登录")
def login(data: LoginIn, request: Request, session: Session = Depends(get_session)):
    ip = _client_ip(request)
    _check_login_limit(data.username, ip)
    user = session.exec(select(User).where(User.username == data.username)).first()
    # 账号或密码错误统一文案，避免泄露哪个不对
    if user is None or not verify_password(data.password, user.password_hash):
        _record_login_failure(data.username, ip)
        logger.info("登录失败 username=%s ip=%s", data.username, ip)
        raise BizError(1001, "用户名或密码错误")
    _clear_login_failure(data.username, ip)
    logger.info("登录成功 username=%s ip=%s", data.username, ip)
    token = create_token(user.id)
    return ok({"token": token, "user": user_public(user)}, "登录成功")


@router.get("/me", summary="当前登录用户")
def me(user: User = Depends(get_current_user)):
    return ok(user_public(user))


@router.get("/check-username", summary="检查用户名是否可用")
def check_username(username: str, session: Session = Depends(get_session)):
    """注册时实时校验用户名是否已被占用。"""
    exists = session.exec(select(User).where(User.username == username)).first()
    return ok({"available": exists is None, "username": username})


@router.get("/{user_id}", summary="按 ID 查询用户公开信息")
def get_user(user_id: int, session: Session = Depends(get_session)):
    """供内容模块展示作者昵称/头像使用，不返回敏感字段。"""
    user = session.get(User, user_id)
    if user is None:
        raise BizError(1005, "用户不存在")
    return ok(user_public(user))


@router.post("/logout", summary="登出")
def logout(request: Request, user: User = Depends(get_current_user)):
    """将当前 token 加入黑名单，使其立即失效。"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    blacklist_token(token)
    logger.info("用户登出 user_id=%s ip=%s", user.id, _client_ip(request))
    return ok(None, "已退出登录")


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
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, user.password_hash):
        raise BizError(1003, "原密码不正确")
    if data.old_password == data.new_password:
        raise BizError(1006, "新密码不能与原密码相同")
    user.password_hash = hash_password(data.new_password)
    session.add(user)
    session.commit()
    # 改密码后吊销当前 token，前端需用新密码重新登录
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    blacklist_token(token)
    logger.info("修改密码成功 user_id=%s ip=%s", user.id, _client_ip(request))
    return ok(None, "密码修改成功，请用新密码重新登录")
