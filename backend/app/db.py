"""数据库引擎与会话（归属：后端 F）

SQLModel 基于 SQLAlchemy。SQLite 免安装，启动时自动建库建表。

说明：SQLite 的 create_all 只建“新表”，不会给“已存在的表”加新列。
因此这里加了自动补列（_sync_columns）：启动时把 models 里定义但表中缺失的列，
用 ALTER TABLE ADD COLUMN 补上 —— 这样以后“给某张表加字段”不再需要删库，
**用户注册的账号、发布的帖子都会保留**。
"""
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL

# check_same_thread=False：SQLite 允许 FastAPI 的多线程访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def _sync_columns() -> None:
    """给已存在的表补齐 models 中新增但库里缺失的列（幂等）。"""
    from app import models

    inspector = inspect(engine)
    tables = {
        "users": models.User,
        "contents": models.Content,
        "comments": models.Comment,
    }
    for table_name, model in tables.items():
        if not inspector.has_table(table_name):
            continue  # 新表交给 create_all
        existing = {c["name"] for c in inspector.get_columns(table_name)}
        for column in model.__table__.columns:
            if column.name in existing:
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            # 新列以可空方式追加，不设置默认值，避免破坏已有行
            ddl = f'ALTER TABLE {table_name} ADD COLUMN "{column.name}" {col_type}'
            with engine.connect() as conn:
                conn.execute(text(ddl))
            print(f"[db] 已为表 {table_name} 自动补列：{column.name} ({col_type})")


def create_db_and_tables() -> None:
    """建表（幂等），并对旧表自动补缺失列。"""
    # 必须先 import models 让表模型注册进 SQLModel.metadata
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _sync_columns()


def get_session():
    """FastAPI 依赖：为每个请求提供独立的数据库会话。"""
    with Session(engine) as session:
        yield session
