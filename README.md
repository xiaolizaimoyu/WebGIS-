# 校园活动交流平台

> 该仓库为 WebGIS 实习开发小组项目

面向全校师生的校园信息发布与交流平台：登录注册、校园资讯展示（活动 / 会议 / 动态 / 广告）、帖子与广告发布（支持图文）、内容评论互动。

- 架构：**前后端分离**，通过统一 API 交互
- 前端：Vue3 + JavaScript + Vite + Vue Router + Axios + Element Plus + Pinia
- 后端：Python + FastAPI + SQLModel + SQLite + JWT(bcrypt)，图片本地存储
- 开发：6 人小组模块化解耦并行，20 天周期

## 目录结构

```
├── backend/          # 后端（FastAPI）
│   └── app/
│       ├── main.py            # F：主程序入口
│       ├── db.py              # F：数据库引擎与会话
│       ├── models.py          # F：数据表模型
│       ├── schemas.py         # F：请求体模型
│       ├── core/              # F：配置 / 安全(JWT) / 统一返回
│       └── routers/
│           ├── user.py        # D：用户认证（/api/user）
│           └── post.py        # E：内容与评论（/api/contents）
├── frontend/         # 前端（Vue3）
│   └── src/
│       ├── layouts/           # C：整体布局外壳
│       ├── router/ stores/ api/ assets/   # C：公共设施
│       └── views/             # A/B：各业务页面
├── docs/API.md       # 接口契约（前后端对接准绳）
└── README.md
```

## 快速启动

**后端**（端口 8000）：

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
# 接口文档：http://127.0.0.1:8000/docs
```

**前端**（端口 5173，已配置 /api 代理到 8000）：

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

## 6 人分工文件清单

代码文件中每个模块文件头都标有 `归属` 注释与 `TODO` 待办，请只修改自己负责的文件。

| 成员 | 归属 | 负责文件（示例） |
|---|---|---|
| 前端 A | 登录/注册模块 | `frontend/src/views/LoginView.vue`、`RegisterView.vue` |
| 前端 B | 帖子/活动/广告/评论 | `frontend/src/views/HomeView.vue`、`PublishView.vue`、`DetailView.vue`、`frontend/src/api/post.js` |
| 前端 C | 布局/路由/全局整合 | `frontend/src/main.js`、`router/`、`layouts/`、`api/request.js`、`stores/` |
| 后端 D | 用户认证 | `backend/app/routers/user.py` |
| 后端 E | 内容业务 | `backend/app/routers/post.py` |
| 后端 F | 全局整合 | `backend/app/main.py`、`core/`、`db.py`、`models.py`、`schemas.py` |

> 当前仓库代码为「第 0 天统一起点」：工程设施齐全、含一条注册→登录→发布→首页→详评最小闭环示例。请各成员在自己归属文件上继续完善、美化与扩展。
