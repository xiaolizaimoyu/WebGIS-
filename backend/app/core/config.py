"""全局配置（归属：后端 F，一般不需要改动）

集中管理路径、密钥、上传限制等常量，方便全项目统一引用。
"""
from pathlib import Path

# backend/ 目录绝对路径：config.py -> app/core/config.py -> app -> backend
BASE_DIR = Path(__file__).resolve().parents[2]

# ---- JWT ----
# TODO(后端F)：上线前请把 SECRET_KEY 换成随机长字符串，例如 secrets.token_hex(32)
SECRET_KEY = "campus-dev-secret-key-please-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 7 * 24 * 60  # 7 天有效

# ---- SQLite ----
DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"

# ---- 图片上传 ----
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
