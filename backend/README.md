# 后端服务（FastAPI + SQLModel + SQLite）

校园活动交流平台后端。请在 `backend/` 目录下操作。

## 安装与启动

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

- 接口地址：`http://127.0.0.1:8000`
- 自动接口文档：`http://127.0.0.1:8000/docs`（可在线调试每个接口）
- 数据库文件：首次启动自动生成 `backend/app.db`
- 上传图片目录：`backend/uploads/`（首次启动自动创建，已加入 .gitignore）

## 模块归属

| 文件 | 归属 | 职责 |
|---|---|---|
| `app/main.py` | 后端 F | 应用实例、CORS、静态资源、全局异常、建表 |
| `app/db.py` | 后端 F | 数据库引擎、会话依赖、建表方法 |
| `app/models.py` | 后端 F | 数据表模型（users / contents / comments） |
| `app/schemas.py` | 后端 F | 接口请求体模型（注册/登录/发布/评论） |
| `app/core/` | 后端 F | 配置 / JWT 安全 / 统一返回 |
| `app/routers/user.py` | 后端 D | 注册、登录、当前用户 |
| `app/routers/post.py` | 后端 E | 图片上传、内容发布查询、评论 |

> 原则：不修改他人文件。如需给内容加字段或表，联系后端 F 在 `models.py` 统一调整。
