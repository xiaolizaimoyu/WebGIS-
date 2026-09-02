# 前端（Vue3 + Vite + Element Plus）

校园活动交流平台前端。请在 `frontend/` 目录下操作。

## 安装与启动

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173 （已配置 /api、/uploads 代理到后端 8000）
```

## 目录说明与模块归属

| 文件/目录 | 归属 | 职责 |
|---|---|---|
| `src/main.js` `src/App.vue` | 前端 C | 应用装配 |
| `src/router/` | 前端 C | 路由 + 登录守卫 |
| `src/stores/` | 前端 C | Pinia 用户状态 |
| `src/api/request.js` | 前端 C | axios 封装（Token、统一解包、401 处理） |
| `src/api/`（user/post/const） | A/B/C 共用 | 接口调用与分类常量 |
| `src/layouts/MainLayout.vue` | 前端 C | 顶部导航 + 页面外壳 |
| `src/assets/style.css` | 前端 C | 全局样式 |
| `src/views/LoginView.vue` | 前端 A | 登录页（模板，可自行美化） |
| `src/views/RegisterView.vue` | 前端 A | 注册页（模板，可自行美化） |
| `src/views/HomeView.vue` | 前端 B | 首页信息流（模板，可扩展卡片/筛选） |
| `src/views/PublishView.vue` | 前端 B | 发布页（模板） |
| `src/views/DetailView.vue` | 前端 B | 详情 + 评论（模板） |

> 各页面文件头都有 TODO 提示可扩展点。不要改动他人归属文件。
