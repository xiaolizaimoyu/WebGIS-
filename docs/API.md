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
| `activity` | 校园活动 | 不支持（传了会被忽略清空） |
| `meeting` | 校园会议 | 不支持（传了会被忽略清空） |
| `news` | 校园动态 | 不支持（传了会被忽略清空） |
| `ad` | 校园广告 | `闲置` / `求助` / `宣传`（可空） |
| `food` | 美食分享 | `食堂推荐` / `小吃外卖` / `零食饮品`（可空） |
| `lost` | 失物招领 | `寻物启事` / `失主招领`（可空） |

> category 非空时必须命中上表白名单，否则返回 `code: 2004`。

## 数据字典：地理位置（WebGIS）

- 内容可绑定地理位置：`longitude`（经度，-180~180）、`latitude`（纬度，-90~90），为发布时地图选点拾取的坐标（高德 gcj-02）。
- 两个字段必须**成对提交**：都不传 = 不绑定位置（存 null）；只传一个返回 `code: 400`。
- 所有内容查询接口（列表/我的发布/详情）都会返回这两个字段，无位置时为 `null`，前端地图只渲染非 null 的点位。

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
成功 data：`{id, username, nickname, avatar, created_at}`（avatar 可空）

**PUT /api/user/me** — 更新个人资料（鉴权）
请求体：`{ "nickname": "新昵称", "avatar": "/uploads/xx.png" }`
说明：字段缺省/传 `null` = 不改；`avatar` 传空串 `""` = 清除头像。
成功 data：更新后的用户对象。

**PUT /api/user/password** — 修改密码（鉴权）
请求体：`{ "old_password": "原密码", "new_password": "至少6位新密码" }`
失败：原密码不正确返回 `code: 1003`。修改成功后下次登录需用新密码。

### 图片上传（内容模块，鉴权）

**POST /api/upload** — 上传单张图片（multipart/form-data，字段名 `file`）
成功 data：`{ "url": "/uploads/xxxx.png" }`
渲染时需拼接文件前缀：`http://127.0.0.1:8000` + url。
限制：仅 jpg/jpeg/png/gif，≤ 5MB。

### 内容发布与查询（后端 E）

**POST /api/contents** — 发布内容（鉴权）
请求体：`{ "title": "标题", "body": "正文", "type": "activity|meeting|news|ad|food|lost", "category": "子分类，可空", "images": ["/uploads/a.png"], "longitude": 116.39742, "latitude": 39.90923 }`
- `type` 不在六类之内返回 `code: 2002`；`category` 非空但不在白名单返回 `code: 2004`。
- `longitude/latitude` 可空，必须成对传，只传一个返回 `code: 400`。
成功 data：新内容完整对象。

**GET /api/contents** — 内容列表（首页信息流 / 地图点位 / 搜索 / 热门排序）
Query：`type`（可选，不传=全部，非法值返回 2002）、`keyword`（可选，≤50 字符，模糊匹配标题或正文）、`sort`（可选，`latest`默认按时间倒序 / `hot`按评论数降序，非法值返回 400）、`page`（默认1）、`size`（默认10，最大100）、`has_location`（可选，`true` 时只返回绑定了经纬度的内容，供地图点位/热力图拉取）、`author_id`（可选，按作者筛选，用户主页展示该用户发布的内容）
成功 data：`{ "total": 100, "total_pages": 10, "items": [内容对象] }`（含作者信息、经纬度、评论数与浏览量）

**GET /api/contents/mine** — 我的发布列表（鉴权）
Query：`type`（可选，不传=全部，非法值返回 2002）、`page`、`size`
成功 data：`{ "total": N, "total_pages": M, "items": [...] }`，仅当前登录用户发布的内容，按时间倒序。

**GET /api/contents/stats** — 内容统计（按分类汇总，无需鉴权）
成功 data：`{ "total": 15, "by_type": {"activity": 3, "ad": 2, "food": 5, "lost": 1, "meeting": 1, "news": 3} }`，供首页仪表盘/分类导航使用。

**PUT /api/contents/{id}** — 编辑自己发布的内容（鉴权，仅作者本人）
请求体：同发布 `{title, body, type, category?, images?, longitude?, latitude?}`（全量提交，校验规则同发布）
失败：非本人操作返回 `code: 2003`。

**DELETE /api/contents/{id}** — 删除自己发布的内容（鉴权，仅作者本人）
删除该内容时会**连带删除其下所有评论**，不可恢复。
失败：非本人操作返回 `code: 2003`。

**GET /api/contents/{id}** — 内容详情（每次访问自增 view_count 浏览量）
成功 data：内容对象（含作者昵称、评论数与浏览量）。
已登录用户访问时额外返回 `is_author: true/false`，前端据此决定是否显示编辑/删除按钮；未登录时该字段不出现。

### 评论（后端 E）

**GET /api/contents/{id}/comments** — 评论列表（分页）
Query：`page`（默认1）、`size`（默认20，最大100）
成功 data：`{ "total": N, "total_pages": M, "items": [评论对象] }`（按时间正序）。

**POST /api/contents/{id}/comments** — 发表评论（鉴权）
请求体：`{ "body": "评论内容" }`
成功 data：新评论对象。

**DELETE /api/contents/{id}/comments/{comment_id}** — 删除评论（鉴权，仅作者本人）
成功 data：`{ "id": comment_id, "deleted": true }`。
失败：非本人评论返回 `code: 2003`；评论/内容不存在返回 `code: 2001`。

## 内容对象结构

```json
{
  "id": 1,
  "title": "标题",
  "body": "正文",
  "type": "activity",
  "category": null,
  "images": ["/uploads/x.png"],
  "longitude": 116.39742,
  "latitude": 39.90923,
  "author_id": 1,
  "author_name": "作者昵称",
  "comment_count": 3,
  "view_count": 42,
  "created_at": "2026-09-02T12:00:00"
}
```

> `longitude/latitude` 未绑定位置时为 `null`；`comment_count` 为评论总数（列表/详情均返回）；`view_count` 为浏览量，详情接口每次访问自增。

## 业务错误码约定

| code | 含义 |
|---|---|
| 401 | 未登录 / Token 失效 |
| 1001 | 用户名或密码错误 |
| 1002 | 用户名已存在 |
| 1003 | 原密码不正确（修改密码时） |
| 2001 | 内容不存在 |
| 2002 | 分类 type 不合法 |
| 2003 | 只能编辑/删除自己发布的内容（非作者操作） |
| 2004 | 子分类 category 不合法（不在该类型白名单内） |
| 400 | 参数校验失败（msg 为具体原因，如经纬度未成对提交） |
