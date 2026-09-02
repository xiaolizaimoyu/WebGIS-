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

from app.core.config import UPLOAD_DIR
from app.core.response import BizError, err
from app.db import create_db_and_tables
from app.routers import post as post_router
from app.routers import user as user_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时：准备上传目录、创建数据表。"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
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
