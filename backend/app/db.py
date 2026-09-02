"""数据库引擎与会话（归属：后端 F）

SQLModel 基于 SQLAlchemy。SQLite 免安装，启动时自动建库建表。
其他模块通过 `session: Session = Depends(get_session)` 拿到会话。
"""
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL

# check_same_thread=False：SQLite 允许 FastAPI 的多线程访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """根据 models.py 中定义的模型创建所有表（幂等，重复启动安全）。"""
    # 必须先 import models 让表模型注册进 SQLModel.metadata
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI 依赖：为每个请求提供独立的数据库会话。"""
    with Session(engine) as session:
        yield session
