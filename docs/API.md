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
请求体：`{ "username": "2-30位字母数字下划线中横线", "nickname": "昵称", "password": "至少8位含字母和数字", "confirm_password": "再次输入密码" }`
成功 data：`{ "token": "...", "expires_in": 604800, "user": {...} }`（注册即登录）
错误：用户名被占用 `code: 1002`；密码强度不足 `code: 1008`；两次密码不一致 `code: 1009`。

**POST /api/user/login** — 登录
请求体：`{ "username": "", "password": "" }`
成功 data：`{ "token": "...", "expires_in": 604800, "user": {...} }`
错误：用户名或密码错误 `code: 1001`；连续失败 5 次锁定 15 分钟 `code: 1004`。

**POST /api/user/logout** — 登出（鉴权）
成功 data：`null`。当前 token 立即失效（加入黑名单）。

**GET /api/user/me** — 获取当前登录用户（鉴权）
成功 data：`{id, username, nickname, avatar, created_at, content_count, comment_count}`

**PUT /api/user/me** — 更新个人资料（鉴权）
请求体：`{ "nickname": "新昵称(可空)", "avatar": "头像URL(可空, 空串=清除)" }`
成功 data：更新后的用户信息。

**PUT /api/user/password** — 修改密码（鉴权）
请求体：`{ "old_password": "", "new_password": "至少8位含字母和数字", "confirm_password": "再次输入新密码" }`
成功 data：`null`。原 token 立即失效，需用新密码重新登录。
错误：原密码错误 `code: 1003`；新旧相同 `code: 1006`；密码强度不足 `code: 1008`；两次不一致 `code: 1009`。

**PATCH /api/user/me/username** — 修改用户名（鉴权）
请求体：`{ "new_username": "新用户名", "password": "当前密码确认" }`
成功 data：`{ "user": {...} }`。原 token 立即失效，需用新用户名重新登录。
错误：密码不正确 `code: 1003`；新旧相同 `code: 1006`；用户名被占用 `code: 1002`。

**DELETE /api/user/me** — 注销账号（鉴权）
请求体：`{ "password": "当前密码确认" }`
成功 data：`null`。
错误：密码不正确 `code: 1003`；存在关联内容/评论 `code: 1007`。

**GET /api/user/check-username?username=xxx** — 检查用户名是否可用
成功 data：`{ "available": true/false, "username": "xxx" }`

**GET /api/user/{user_id}** — 按 ID 查询用户公开信息
成功 data：`{id, username, nickname, avatar, created_at, content_count, comment_count}`
错误：用户不存在 `code: 1005`。

**POST /api/user/batch** — 批量查询用户公开信息
请求体：`{ "ids": [1, 2, 3] }`（单次最多 100 个）
成功 data：`{ "list": [{id, username, nickname, avatar, created_at}] }`，不存在的 id 自动跳过。

**GET /api/user/list** — 用户列表（分页）
Query：`page`（默认1）、`page_size`（默认20，上限100）、`keyword`（按用户名/昵称模糊搜索）
成功 data：`{ "total": 100, "page": 1, "page_size": 20, "list": [{id, username, nickname, avatar, created_at}] }`

**GET /api/user/stats** — 用户统计（鉴权）
成功 data：`{ "total_users": 100, "today_new": 5, "week_new": 20 }`

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
