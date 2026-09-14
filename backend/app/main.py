"""后端主程序（归属：后端 F）

职责：创建 FastAPI 应用、跨域配置、路由整合、静态资源(上传图片)、全局异常统一、启动建表。
不写具体业务。

启动：python -m uvicorn app.main:app --reload --port 8000
文档：http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.admin import ensure_admin_account
from app.core.config import UPLOAD_DIR
from app.core.response import BizError, err
from app.db import Session, create_db_and_tables, engine
from app.models import LocationPoint
from app.routers import post as post_router
from app.routers import user as user_router
from app.routers import admin as admin_router
from app.routers import locations as locations_router
from app.routers import social as social_router
from app.routers import points as points_router
from app.routers import mall as mall_router
from app.routers import extensions as extensions_router

# 默认校园地点库（与前端 const.js CAMPUS_PLACES 一致，作为初始化底子，
# 管理员可在后台逐一点击地图校准为真实坐标）
DEFAULT_CAMPUS_PLACES = [
    {"name": "北门（新村西路）", "lng": 118.006732, "lat": 36.816583},
    {"name": "图书馆", "lng": 118.006431, "lat": 36.815182},
    {"name": "鸿远楼（行政楼）", "lng": 118.007535, "lat": 36.814284},
    {"name": "一号教学楼", "lng": 118.008939, "lat": 36.81599},
    {"name": "二号教学楼", "lng": 118.007836, "lat": 36.815786},
    {"name": "三号教学楼", "lng": 118.005829, "lat": 36.813579},
    {"name": "逸夫楼", "lng": 118.006331, "lat": 36.81268},
    {"name": "第一食堂（一餐）", "lng": 118.010043, "lat": 36.815693},
    {"name": "第二食堂（二餐）", "lng": 118.009541, "lat": 36.81309},
    {"name": "第三食堂（三餐）", "lng": 118.005528, "lat": 36.815479},
    {"name": "体育馆", "lng": 118.011146, "lat": 36.813595},
    {"name": "田径场", "lng": 118.010344, "lat": 36.814493},
    {"name": "学生公寓区", "lng": 118.008137, "lat": 36.816988},
    {"name": "大学生事务中心", "lng": 118.006832, "lat": 36.814182},
    {"name": "校医院", "lng": 118.005027, "lat": 36.814677},
    {"name": "东门", "lng": 118.012752, "lat": 36.8144},
    {"name": "南门", "lng": 118.007835, "lat": 36.812584},
]


def _init_location_points() -> None:
    """地点库为空时写入默认校园地点，后续由管理员在后台校准为真实坐标。"""
    from sqlmodel import select

    with Session(engine) as session:
        if session.exec(select(LocationPoint)).first() is not None:
            return
        for idx, p in enumerate(DEFAULT_CAMPUS_PLACES):
            session.add(LocationPoint(name=p["name"], lng=p["lng"], lat=p["lat"], sort=idx))
        session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时：准备上传目录、创建数据表。"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
    # 确保内置管理员账号存在（admin/admin，is_admin=True）
    with Session(engine) as session:
        ensure_admin_account(session)
    # 初始化默认地点坐标库
    _init_location_points()
    yield


# 保证 StaticFiles 挂载时目录已存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="校园活动交流平台 API",
    description="前端请阅读根目录 docs/API.md 了解接口契约",
    version="0.1.0",
    lifespan=lifespan,
)

# 跨域：开发期前端跑在 5173（vite 代理到 8000 已绕开跨域，这里兜底）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 整合各路由模块
app.include_router(user_router.router)
app.include_router(post_router.router)
app.include_router(social_router.router)
app.include_router(points_router.router, prefix="/api/points")
app.include_router(points_router.notify_router)
app.include_router(mall_router.router)
app.include_router(extensions_router.router, prefix="/api")
app.include_router(admin_router.router)
app.include_router(locations_router.router)

# 上传图片的静态访问：/uploads/xxx.png
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ---------- 全局统一返回（前端只认 body 里的 code/msg/data） ----------
@app.exception_handler(BizError)
async def biz_error_handler(_: Request, exc: BizError):
    """业务错误：HTTP 200 + code != 0，msg 直接展示给用户。"""
    return JSONResponse(status_code=200, content=err(exc.code, exc.msg))


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    """Pydantic 请求校验失败：转成统一格式，code=400。"""
    first = exc.errors()[0] if exc.errors() else {}
    msg = first.get("msg", "参数校验失败")
    return JSONResponse(status_code=200, content=err(400, f"参数错误：{msg}"))


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """FastAPI 内部异常（如 404 路由）转统一格式。"""
    return JSONResponse(status_code=exc.status_code, content=err(exc.status_code, str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    """兜底：任何未捕获异常都不暴露堆栈给前端。"""
    # 开发期建议打印日志排查：print(exc)
    return JSONResponse(status_code=500, content=err(500, "服务器内部错误，请稍后重试"))


@app.get("/", summary="服务健康检查")
def root():
    return {"code": 0, "msg": "校园活动交流平台 API 运行中", "data": None}
