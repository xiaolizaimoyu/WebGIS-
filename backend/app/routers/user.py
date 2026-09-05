"""用户认证模块（归属：后端 D）

只处理用户相关业务：注册 / 登录 / 当前用户信息。
- 前缀 /api/user
- 密码只存 bcrypt 哈希，绝不返回明文
- 登录成功签发 JWT，前端保存 token 后带在请求头调用受保护接口
"""
import logging
import time

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.config import JWT_EXPIRE_MINUTES
from app.core.response import BizError, ok
from app.core.security import (
    blacklist_token,
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import get_session
from app.models import Comment, Content, User
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


# ---------- 密码强度校验 ----------
# 常见弱密码黑名单（小写比对）
_WEAK_PASSWORDS = {
    "123456", "1234567", "12345678", "123456789", "1234567890",
    "password", "password1", "123456a", "111111", "000000",
    "abc123", "qwerty", "iloveyou", "admin123", "root123",
    "11111111", "aaaaaa", "a123456", "123123", "666666",
}


def _validate_password_strength(password: str, username: str = "") -> str:
    """校验密码强度，返回错误文案；通过则返回空串。"""
    pwd = password or ""
    # 弱密码字典
    if pwd.lower() in _WEAK_PASSWORDS:
        return "密码过于常见，请更换"
    # 与用户名相同
    if username and pwd == username:
        return "密码不能与用户名相同"
    # 长度建议：虽然 Pydantic 允许 6 位，但 6-7 位提示强度不足
    if len(pwd) < 8:
        return "密码长度建议至少 8 位"
    # 必须同时包含字母和数字
    has_alpha = any(c.isalpha() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    if not (has_alpha and has_digit):
        return "密码需同时包含字母和数字"
    # 禁止连续/重复字符（如 aaa、1234、abcd）
    def is_sequential(s: str) -> bool:
        for i in range(len(s) - 2):
            a, b, c = s[i], s[i + 1], s[i + 2]
            if b.isalnum() and c.isalnum() and (ord(b) - ord(a) == ord(c) - ord(b) == 1):
                return True
        return False
    if is_sequential(pwd.lower()):
        return "密码不能包含连续字符（如 1234、abcd）"
    return ""


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


# ---------- 接口请求体模型（本模块内联定义，不依赖后端F的 schemas.py） ----------
class RegisterConfirmIn(RegisterIn):
    """注册请求体：在 RegisterIn 基础上增加确认密码字段。"""

    confirm_password: str = Field(min_length=1, max_length=64, description="再次输入密码")


class ChangePasswordConfirmIn(ChangePasswordIn):
    """改密码请求体：在 ChangePasswordIn 基础上增加确认新密码字段。"""

    confirm_password: str = Field(min_length=1, max_length=64, description="再次输入新密码")


class ChangeUsernameIn(BaseModel):
    """修改用户名请求体：需密码确认，新用户名遵守白名单。"""

    new_username: str = Field(
        min_length=2,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="新登录账号，2-30位，仅字母数字下划线中横线",
    )
    password: str = Field(min_length=1, max_length=64, description="当前密码确认")


class DeleteAccountIn(BaseModel):
    """注销账号请求体：需二次输入密码确认。"""

    password: str = Field(min_length=1, max_length=64, description="当前密码确认")


class BatchUsersIn(BaseModel):
    """批量查询用户请求体：传 id 列表，一次取回，避免 N+1 查询。"""

    ids: list[int] = Field(min_length=1, max_length=100, description="用户 id 列表，单次最多100个")


def user_public(user: User) -> dict:
    """对外暴露的用户信息（去掉密码哈希），注册/登录/me/更新资料共用同一结构。"""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "created_at": user.created_at,
    }


def user_detail(user: User, session: Session) -> dict:
    """用户公开信息 + 发布内容数/评论数（个人主页用）。"""
    from sqlalchemy import func

    content_count = session.exec(
        select(func.count()).select_from(Content).where(Content.author_id == user.id)
    ).one()
    comment_count = session.exec(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    ).one()
    data = user_public(user)
    data["content_count"] = content_count
    data["comment_count"] = comment_count
    return data


@router.post("/register", summary="注册")
def register(data: RegisterConfirmIn, request: Request, session: Session = Depends(get_session)):
    if data.password != data.confirm_password:
        raise BizError(1009, "两次输入的密码不一致")
    exists = session.exec(select(User).where(User.username == data.username)).first()
    if exists:
        raise BizError(1002, "该用户名已被注册")
    weak_msg = _validate_password_strength(data.password, data.username)
    if weak_msg:
        raise BizError(1008, weak_msg)
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
    return ok(
        {"token": token, "expires_in": JWT_EXPIRE_MINUTES * 60, "user": user_public(user)},
        "注册成功",
    )


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
    return ok(
        {"token": token, "expires_in": JWT_EXPIRE_MINUTES * 60, "user": user_public(user)},
        "登录成功",
    )


@router.get("/me", summary="当前登录用户")
def me(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return ok(user_detail(user, session))


@router.get("/check-username", summary="检查用户名是否可用")
def check_username(username: str, session: Session = Depends(get_session)):
    """注册时实时校验用户名是否已被占用。"""
    exists = session.exec(select(User).where(User.username == username)).first()
    return ok({"available": exists is None, "username": username})


@router.get("/list", summary="用户列表（分页）")
def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    session: Session = Depends(get_session),
):
    """分页查询用户公开信息，支持按用户名/昵称模糊搜索。

    供管理后台或成员展示页使用，不返回密码等敏感字段。
    """
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = select(User)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(User.username.contains(like) | User.nickname.contains(like))
    total = len(session.exec(stmt).all())
    users = session.exec(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [user_public(u) for u in users],
    })


@router.post("/batch", summary="批量查询用户公开信息")
def batch_users(data: BatchUsersIn, session: Session = Depends(get_session)):
    """按 id 列表批量取用户公开信息，供内容/评论模块批量填充作者。

    一次查询替代循环 N 次 GET /{user_id}，避免 N+1 问题。
    不存在的 id 自动跳过，返回顺序不保证与请求一致。
    """
    users = session.exec(select(User).where(User.id.in_(data.ids))).all()
    return ok({"list": [user_public(u) for u in users]})


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
    data: ChangePasswordConfirmIn,
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, user.password_hash):
        raise BizError(1003, "原密码不正确")
    if data.old_password == data.new_password:
        raise BizError(1006, "新密码不能与原密码相同")
    if data.new_password != data.confirm_password:
        raise BizError(1009, "两次输入的新密码不一致")
    weak_msg = _validate_password_strength(data.new_password, user.username)
    if weak_msg:
        raise BizError(1008, weak_msg)
    user.password_hash = hash_password(data.new_password)
    session.add(user)
    session.commit()
    # 改密码后吊销当前 token，前端需用新密码重新登录
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    blacklist_token(token)
    logger.info("修改密码成功 user_id=%s ip=%s", user.id, _client_ip(request))
    return ok(None, "密码修改成功，请用新密码重新登录")


@router.patch("/me/username", summary="修改用户名")
def change_username(
    data: ChangeUsernameIn,
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """修改登录用户名，需输入密码确认。

    - 校验新用户名唯一性与字符白名单（由 ChangeUsernameIn 保证）
    - 改用户名后吊销当前 token，前端需用新用户名重新登录
    """
    if not verify_password(data.password, user.password_hash):
        raise BizError(1003, "密码不正确")
    if data.new_username == user.username:
        raise BizError(1006, "新用户名不能与原用户名相同")
    exists = session.exec(
        select(User).where(User.username == data.new_username)
    ).first()
    if exists:
        raise BizError(1002, "该用户名已被占用")
    old_username = user.username
    user.username = data.new_username
    session.add(user)
    session.commit()
    session.refresh(user)
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    blacklist_token(token)
    logger.info(
        "修改用户名 user_id=%s old=%s new=%s ip=%s",
        user.id, old_username, data.new_username, _client_ip(request),
    )
    return ok({"user": user_public(user)}, "用户名已修改，请用新用户名重新登录")


@router.delete("/me", summary="注销账号")
def delete_account(
    data: DeleteAccountIn,
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """注销当前账号，需二次输入密码确认。

    注：物理删除用户记录。若用户已发布内容/评论，外键约束会阻止删除，
    此处先校验密码，删除失败时返回明确提示。
    """
    if not verify_password(data.password, user.password_hash):
        raise BizError(1003, "密码不正确，无法注销")
    # 吊销当前 token
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    blacklist_token(token)
    try:
        session.delete(user)
        session.commit()
    except Exception:
        session.rollback()
        logger.warning("注销失败(存在关联数据) user_id=%s ip=%s", user.id, _client_ip(request))
        raise BizError(1007, "存在关联内容或评论，无法直接注销，请联系管理员")
    logger.warning("账号注销 user_id=%s ip=%s", user.id, _client_ip(request))
    return ok(None, "账号已注销")


@router.get("/stats", summary="用户统计")
def user_stats(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """返回用户相关统计，供后台/数据分析使用（需登录）。"""
    from datetime import datetime, timedelta

    all_users = session.exec(select(User)).all()
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    today_new = sum(1 for u in all_users if u.created_at >= today_start)
    week_new = sum(1 for u in all_users if u.created_at >= week_start)
    return ok({
        "total_users": len(all_users),
        "today_new": today_new,
        "week_new": week_new,
    })


@router.get("/{user_id}", summary="按 ID 查询用户公开信息")
def get_user(user_id: int, session: Session = Depends(get_session)):
    """供内容模块展示作者昵称/头像使用，不返回敏感字段。

    额外返回 content_count / comment_count（个人主页统计）。
    注意：动态路径 {user_id} 必须放在所有静态路径(/list /stats 等)之后，
    否则 FastAPI 会把 list/stats 当成 user_id 匹配。
    """
    user = session.get(User, user_id)
    if user is None:
        raise BizError(1005, "用户不存在")
    return ok(user_detail(user, session))
