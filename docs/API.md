# 接口契约文档

前后端对接准绳。所有接口统一前缀 **`/api`**（Vite 已把 `/api` 代理到后端 8000 端口）。

## 统一返回格式

```json
{
  "code": 0,        // 0 = 成功；非 0 = 失败
  "msg": "ok",      // 提示文案，前端可直接展示
  "data": {}        // 业务数据，失败时为 null
}
```

前端 `axios` 拦截器已统一处理：`code !== 0` 自动弹错误提示并 reject。业务代码只需处理成功分支。

## 鉴权说明

- 登录接口返回 `data.token`（JWT，默认 7 天有效）。
- 调用「需要鉴权」接口时，前端在请求头带 `Authorization: Bearer <token>`（已由拦截器自动注入）。
- Token 失效/缺失返回 `code: 401`，前端自动清理登录态并跳转登录页。

## 数据字典：内容类型 type

| 值 | 含义 | category 二级分类 |
|---|---|---|
| `activity` | 校园活动 | 可空 |
| `meeting` | 校园会议 | 可空 |
| `news` | 校园动态 | 可空 |
| `ad` | 校园广告 | `闲置` / `求助` / `宣传` / 自定义 |

## 接口列表

### 用户认证（后端 D）

**POST /api/user/register** — 注册
请求体：`{ "username": "学号或用户名", "nickname": "昵称", "password": "至少6位" }`
成功 data：注册后的用户信息 `{id, username, nickname}`

**POST /api/user/login** — 登录
请求体：`{ "username": "", "password": "" }`
成功 data：`{ "token": "...", "user": {id, username, nickname} }`
错误：密码错误返回 `code: 1001`。

**GET /api/user/me** — 获取当前登录用户（鉴权）
成功 data：`{id, username, nickname}`

### 图片上传（内容模块，鉴权）

**POST /api/upload** — 上传单张图片（multipart/form-data，字段名 `file`）
成功 data：`{ "url": "/uploads/xxxx.png" }`
渲染时需拼接文件前缀：`http://127.0.0.1:8000` + url。
限制：仅 jpg/jpeg/png/gif，≤ 5MB。

### 内容发布与查询（后端 E）

**POST /api/contents** — 发布内容（鉴权）
请求体：`{ "title": "标题", "body": "正文", "type": "activity", "category": "闲置|...可空", "images": ["/uploads/a.png"] }`
成功 data：新内容完整对象。

**GET /api/contents** — 内容列表（首页信息流）
Query：`type`（可选，不传=全部）、`page`（默认1）、`size`（默认10）
成功 data：`{ "total": 100, "items": [内容对象] }`（按发布时间倒序，含作者信息）

**GET /api/contents/{id}** — 内容详情
成功 data：内容对象（含作者昵称）。

### 评论（后端 E）

**GET /api/contents/{id}/comments** — 评论列表
成功 data：评论数组（含作者昵称，按时间正序）。

**POST /api/contents/{id}/comments** — 发表评论（鉴权）
请求体：`{ "body": "评论内容" }`
成功 data：新评论对象。

## 内容对象结构

```json
{
  "id": 1,
  "title": "标题",
  "body": "正文",
  "type": "activity",
  "category": null,
  "images": ["/uploads/x.png"],
  "author_id": 1,
  "author_name": "作者昵称",
  "created_at": "2026-09-02T12:00:00"
}
```

## 业务错误码约定

| code | 含义 |
|---|---|
| 401 | 未登录 / Token 失效 |
| 1001 | 用户名或密码错误 |
| 1002 | 用户名已存在 |
| 2001 | 内容不存在 |
| 2002 | 分类 type 不合法 |
| 400 | 参数校验失败（msg 为具体原因） |
