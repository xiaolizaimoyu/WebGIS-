# Git 协作说明（校园活动交流平台 · 6 人小组）

本仓库远程：`https://github.com/xiaolizaimoyu/WebGIS-.git`（别名 `origin`）
本文件是所有成员「如何提交代码」的唯一标准，请按它操作。

---

## 0. 三条铁律（决定会不会冲突）

1. **永远只提交自己负责的文件**——用 `git add 具体路径`，**禁止** `git add .` / `git add -A`。
2. **每天开工先 `git pull`**，拿到队友最新代码；收工 / 每完成一个功能就提交一次。
3. **公共文件别乱动**——`frontend` 的布局/路由/axios 封装属于**前端 C**；`backend` 的 models/db/main 属于**后端 F**。缺能力就找 C / F，不要自己偷改。

---

## 1. 首次使用（每人只做一次）

```bash
git clone https://github.com/xiaolizaimoyu/WebGIS-.git
cd WebGIS-
git config user.name "你的真名"      # 换成本名，提交记录才显示得出来
git config user.email "你的邮箱"
```

> 需要先把 5 名同学加为 GitHub 仓库协作者：仓库 Settings → Collaborators。

---

## 2. 每个工作日的固定动作

```bash
git switch main        # 回到主分支
git pull               # 拉取队友最新代码（开工必做！）

git switch -c dev-B    # 第一次建自己的分支；以后直接：git switch dev-B

# ……改你自己负责的文件，本地跑通、演示没问题后……

git status             # 看改了哪些文件，确认没误伤别人
git add <你的文件们>    # 见下方第 3 节，只加自己的文件
git commit -m "feat(前端B): 完成首页分类筛选"
git push -u origin dev-B   # 第一次推送用这行；以后用 git push
```

**提交节奏**：每完成一个最小功能提交一次，最迟 2–3 天一次。
**每条 commit 只说一件事**，这样出问题能单独回退。

---

## 3. 六人文件归属与提交命令

> 以下命令请在**仓库根目录**（能看到 `backend/` 和 `frontend/` 的地方）执行。
> `git add` 多个文件用**空格**分隔，不能用顿号或换行。

### 前端 A —— 登录 / 注册
```bash
git add frontend/src/views/LoginView.vue frontend/src/views/RegisterView.vue frontend/src/api/user.js
```

### 前端 B —— 首页 / 发布 / 详情 / 评论
```bash
git add frontend/src/views/HomeView.vue frontend/src/views/PublishView.vue frontend/src/views/DetailView.vue frontend/src/api/post.js
```

### 前端 C —— 布局 / 路由 / 全局整合
```bash
git add frontend/src/main.js frontend/src/App.vue frontend/src/router frontend/src/layouts frontend/src/stores frontend/src/assets frontend/src/api/request.js frontend/src/api/const.js frontend/vite.config.js frontend/package.json frontend/package-lock.json frontend/.npmrc frontend/index.html frontend/README.md
```

### 后端 D —— 用户认证（/api/user）
```bash
git add backend/app/routers/user.py
```

### 后端 E —— 内容业务（/api/contents）
```bash
git add backend/app/routers/post.py
```

### 后端 F —— 全局整合
```bash
git add backend/app/main.py backend/app/db.py backend/app/models.py backend/app/schemas.py backend/app/core backend/requirements.txt backend/README.md
```

---

## 4. commit 信息规范

```
feat(前端A):  新增功能      fix(后端D): 修复bug
style(前端B): 样式美化      docs:       更新文档
refactor:     重构不改行为
```

例：`git commit -m "feat(前端A): 登录页增加记住我选项"`

---

## 5. 组长定期合并成员分支（每 2–3 天一次）

```bash
git switch main
git pull
git merge dev-A     # 逐个合并 6 个分支
git merge dev-B
git merge dev-C
git merge dev-D
git merge dev-E
git merge dev-F
git push            # 把合并结果推送到 GitHub
```

- 文件已按成员隔离，正常**几乎不会冲突**。
- 万一提示 `CONFLICT`：让相关成员一起打开冲突文件，找到 `<<<<<<<` `=======` `>>>>>>>` 标记，保留两边要的代码、删掉标记，然后：
  ```bash
  git add <冲突文件>
  git commit -m "fix: 合并 dev-X 解决冲突"
  ```

---

## 6. 常用问题自救

| 情况 | 解决 |
|---|---|
| `fatal: pathspec ... did not match any files` | 路径没写全 或 用顿号分隔了。改为在根目录、用空格分隔、路径写完整 |
| 不小心 `git add` 错了文件 | `git restore --staged <文件>`（只是取消暂存，不删文件） |
| commit 信息写错了（还没 push） | `git commit --amend -m "新信息"` |
| commit 提交错了（还没 push），想撤掉、保留改动 | `git reset --soft HEAD~1` |
| 本地改动不想要了 | `git restore <文件>`（**会丢改动**，慎用） |
| 想不起改过哪些 | `git status`；看历史 `git log --oneline` |
| 看某位成员的提交 | `git log --author=张三 --oneline` |

---

## 7. 千万别提交的东西

以下已由 `.gitignore` 自动忽略，**不需要**也不应提交：
`node_modules/`、`.venv/`、`dist/`、`uploads/`、`*.db`、`__pycache__/`、`.env`
（不要用 `git add -f` 去强制添加它们。）
