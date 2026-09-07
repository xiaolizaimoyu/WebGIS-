"""数据库引擎与会话（归属：后端 F）

SQLModel 基于 SQLAlchemy。SQLite 免安装，启动时自动建库建表。

注意：SQLite 的 create_all 只建"新表"，不会给"已存在的表"加新列。
因此这里加了自动补列（_sync_columns）：启动时把 models 里定义但表中缺失的列，
用 ALTER TABLE ADD COLUMN 补上 —— 以后"给某张表加字段"不再需要删库重建，
用户注册的账号、发布的帖子都会保留。

其他模块通过 `session: Session = Depends(get_session)` 拿到会话。
"""
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL

# check_same_thread=False：SQLite 允许 FastAPI 的多线程访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def _sync_columns() -> None:
    """给已存在的表补齐 models 中新增但库里缺失的列（幂等）。

    补列后自动将已有行的 NULL 值更新为模型默认值（如 points=0, like_count=0），
    避免旧数据因新列为 NULL 导致业务代码报错。
    """
    from app import models

    inspector = inspect(engine)
    tables = {
        "users": models.User,
        "contents": models.Content,
        "comments": models.Comment,
        "likes": models.Like,
        "favorites": models.Favorite,
        "follows": models.Follow,
        "notifications": models.Notification,
        "points_log": models.PointsLog,
        "sign_records": models.SignRecord,
        "mall_goods": models.MallGoods,
        "orders": models.Order,
    }
    # 字段默认值映射（补列后用于回填旧数据）
    default_values = {
        "points": 0,
        "like_count": 0,
        "view_count": 0,
        "stock": 0,
        "is_read": 0,
        "status": "on",
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
                # 回填默认值
                if column.name in default_values:
                    default = default_values[column.name]
                    if isinstance(default, str):
                        conn.execute(text(f'UPDATE {table_name} SET "{column.name}" = :v WHERE "{column.name}" IS NULL'), {"v": default})
                    else:
                        conn.execute(text(f'UPDATE {table_name} SET "{column.name}" = {default} WHERE "{column.name}" IS NULL'))
                conn.commit()
            print(f"[db] 已为表 {table_name} 自动补列：{column.name} ({col_type})，并回填默认值")


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
