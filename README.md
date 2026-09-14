# 校园活动交流平台（WebGIS 实习项目）

> 基于 **WebGIS 技术**的校园信息发布与交流平台，前后端分离架构，6 人小组并行开发完成。

面向山东理工大学西校区师生的校园综合服务平台：以**高德地图**为核心交互载体，覆盖信息发布、地图定位、社交互动、积分激励、便民服务（拼车 / 失物招领 / 学习资料）与管理员运营后台，是一套功能完整、可演示、可交付的 Web 应用系统。

---

## 一、功能特性

### 🗺️ 校园地图（WebGIS 核心）
- 首页全屏高德地图，帖子按**真实校园坐标**打点展示，可按类型筛选
- 管理员后台**地图点击拾取真实坐标**并录入地点库（一键校准校园 POI）
- 帖子点位：地点库命中显示真实坐标，未录入地点按帖子 ID 确定性随机散布（刷新不乱跳）
- 帖子详情页左右布局：左侧帖子列表 + 右侧联动地图，支持「定位到地图」点位**红色高亮**，双向联动

### 👤 用户体系
- 注册 / 登录（JWT 鉴权 + SVG 图形验证码 + 连续失败限流锁定）
- 个人中心、我的发布（编辑 / 删除）、我的收藏、我的兑换记录
- 管理员账号（admin）与管理员登录页、路由守卫

### 📝 信息发布与互动
- 多类型内容：校园会议 / 校园动态 / 美食分享 / 失物招领，支持图文上传
- 发布选点：下拉选择校园地点自动定位，或地图上点击拾取精确位置
- 评论、点赞（可赞可取消、一人一次）、收藏、关注、消息通知

### 🏆 积分激励
- 每日签到（+10 分，连续 7 天 +20 奖励）、发帖评论得积分、积分流水
- 积分商城：商品展示、搜索、积分兑换、兑换订单记录

### 🚗 便民服务
- 组队拼车：发布 / 编辑 / 删除、申请加入、车主确认 / 拒绝、申请人取消
- 失物招领：发布 / 认领联动
- 学习资料：上传 / 下载（真实 PDF 下载、双击打开）、点赞（一人一次）

### 🛡️ 管理员后台
- 数据概览统计、帖子审核（删任意帖）、用户管理（删用户）、评论管理
- **地点坐标管理**：地图点击拾取 + 名称录入，校准全站点位

### 🌤️ 其他
- 右上角**实时天气**（Open-Meteo 免费 API，浏览器定位 → 淄博）
- 登录 / 注册 / 管理员登录页统一校园雪景背景 + 毛玻璃卡片

---

## 二、技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| 前端框架 | Vue 3（Composition API）+ Vite | SPA 应用 |
| 前端组件 | Element Plus、Vue Router、Pinia、Axios | UI / 路由 / 状态 / 请求 |
| 地图 | 高德地图 JS API 2.0（GCJ-02） | 地图渲染、点击拾取、点位高亮 |
| 天气 | Open-Meteo 免费 API | 实时天气（无需 key） |
| 后端框架 | Python + FastAPI + SQLModel | REST API |
| 数据库 | SQLite（本地文件） | 数据存储（14 张表） |
| 认证 | JWT（bcrypt 密码哈希） | 用户鉴权 |
| 验证码 | SVG 图形验证码（自研） | 登录防刷 |
| 文件 | 本地磁盘存储（/uploads） | 图片、资料 PDF |

---

## 三、系统架构

```
┌──────────────────────── 前端（Vue3 · 端口 5173）────────────────────────┐
│  MainLayout 布局 │ 校园地图 │ 帖子详情 │ 积分商城 │ 拼车 │ 失物 │ 资料 │ 后台 │
└───────────────┬─────────────────────────────────────────────────────────┘
                │  Axios（/api 代理 → 8000，统一 code/msg/data）
┌───────────────┴─────────────────────────────────────────────────────────┐
│                        后端（FastAPI · 端口 8000）                       │
│  user 认证 │ post 内容 │ social 互动 │ points 积分 │ mall 商城 │          │
│  carpool 拼车 │ admin 后台 │ locations 地点库 │ extensions 扩展          │
│  ────────────────────────────────────────────────────────────────────   │
│  SQLModel ORM → SQLite（app.db，14 张表） + JWT + bcrypt + 验证码        │
└──────────────────────────────────────────────────────────────────────────┘
```

**坐标系约定**：全链路使用高德 GCJ-02 火星坐标；校园中心（118.007853, 36.814398）为山东理工大学西校区。

---

## 四、目录结构

```
├── backend/                 # 后端（FastAPI）
│   ├── app/
│   │   ├── main.py          # F：主程序入口、路由整合、启动建表
│   │   ├── db.py            # F：SQLite 引擎、建表与自动补列
│   │   ├── models.py        # F：14 张数据表模型（唯一建表来源）
│   │   ├── core/            # F：config / security(JWT·bcrypt) / response
│   │   │   └── admin.py     # D：管理员鉴权与内置账号
│   │   └── routers/
│   │       ├── user.py      # D：用户认证、验证码、限流
│   │       ├── post.py      # E：内容发布 / 评论
│   │       ├── social.py    # F：点赞 / 收藏 / 关注
│   │       ├── points.py    # F：签到与积分
│   │       ├── mall.py      # F：积分商城
│   │       ├── admin.py     # D：管理员后台
│   │       ├── locations.py # F：地点坐标库
│   │       └── extensions.py# F：学习资料 / 拼车 / 失物等扩展模块
│   └── requirements.txt
├── frontend/                # 前端（Vue3）
│   └── src/
│       ├── layouts/         # C：MainLayout 顶部导航 + 天气
│       ├── views/           # A/B/C：各业务页面（详见分工表）
│       ├── components/      # 地图组件、选点组件、天气、弹窗
│       ├── composables/     # 地点坐标共享工具
│       ├── router/ stores/ api/ assets/
├── docs/                    # 项目文档
│   ├── API.md               # 接口契约文档（前后端对接准绳）
│   ├── 运行说明.md           # 环境搭建与启动步骤
│   └── git协作说明.md        # Git 工作流约定
└── README.md
```

---

## 五、快速开始

> 环境要求：Python 3.10+、Node.js 16+。全程需要开两个终端：先启动后端，再启动前端。

### 1. 安装依赖（首次）

```powershell
# 后端
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 前端
cd ..\frontend
npm install
```

### 2. 启动后端（端口 8000）

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# 接口文档：http://127.0.0.1:8000/docs
```

### 3. 启动前端（端口 5173）

```powershell
cd frontend
npm run dev
# 打开：http://localhost:5173
```

### 4. 测试账号

| 账号 | 密码 | 角色 |
|---|---|---|
| `demo_wang`（demo_li / demo_zhao / demo_chen / demo_lin） | `123456` | 普通用户 |
| `admin` | `admin` | 管理员（可进管理后台） |

> 首次启动自动建表（14 张）并初始化演示数据、内置管理员账号、默认校园地点库（管理员可在后台校准为真实坐标）。

---

## 六、数据库设计（14 张表）

| 表 | 说明 | 表 | 说明 |
|---|---|---|---|
| users | 用户（含积分、is_admin） | points_log | 积分流水 |
| contents | 内容帖（含经纬度/地点名） | sign_records | 签到记录 |
| comments | 评论 | mall_goods | 商城商品 |
| likes | 点赞（用户×内容唯一） | orders | 兑换订单 |
| favorites | 收藏 | follows | 关注关系 |
| notifications | 消息通知 | carpools | 拼车 |
| location_points | 地点坐标库（真实坐标） | carpool_applications | 拼车申请 |

> 改动表结构统一在 `backend/app/models.py` 修改，启动时 `create_db_and_tables()` 自动建表 / 补列。

---

## 七、成员分工

> 代码文件头部均带有「归属：前端 X / 后端 X」注释；以下为按**功能模块 + 前后端**划分的最终分工。成员代号与仓库提交账号的对应关系由组长在小组内统一说明（提交量：组长 xiaolizaimoyu 112 次，成员合计 141 次）。

| 代号 | 端 | 核心职责 | 代表文件 |
|---|---|---|---|
| **前端 A** | 前端 | 校园地图页、登录/注册 | `views/MapView.vue`、`LoginView.vue`、`RegisterView.vue` |
| **前端 B** | 前端 | 实时天气、帖子详情、我的发布 | `components/WeatherWidget.vue`、`views/DetailView.vue`、`MineView.vue` |
| **前端 C** | 前端 | 整体布局/路由/请求封装、积分商城、拼车、失物招领、学习资料、通知中心、个人中心 | `layouts/MainLayout.vue`、`router/`、`api/request.js`、`views/MallView.vue`、`Carpool*View.vue`、`LostFound*View.vue`、`Materials*View.vue`、`NotificationsView.vue` |
| **后端 D** | 后端 | 用户认证/验证码/限流、管理员后台、地点坐标管理 | `routers/user.py`、`routers/admin.py`、`core/admin.py`、`routers/captcha.py` |
| **后端 E** | 后端 | 内容业务模块全部开发与优化

| `routers/post.py`（42 次提交）、`docs/API.md`（11 次）、`models.py`、`schemas.py` |
| **后端 F** | 后端 | 主程序/数据库/基础设施、积分、商城、社交互动、学习资料/拼车/失物扩展 | `main.py`、`db.py`、`models.py`、`core/*`、`routers/social.py`、`points.py`、`mall.py`、`extensions.py` |

**组长职责（xiaolizaimoyu）**：整体架构设计、分支管理与代码合并、主程序整合、Bug 修复与全链路联调、README 与交付文档整理。

**协作方式**：各成员在 `dev-字母` 分支开发 → 组长评审合并到 `main` → 每日拉取最新代码联调。

---

## 八、交付文档索引

| 文档 | 内容 |
|---|---|
| `docs/API.md` | 全部接口契约（认证/内容/互动/积分/商城/通知/管理后台/地点库） |
| `docs/运行说明.md` | 环境搭建、依赖安装、日常启动、常见问题 |
| `docs/git协作说明.md` | Git 分支规范、提交规范、拉取合并流程 |

---

*本项目为 WebGIS 课程实习小组项目，所有代码与文档由小组成员协作完成。*
