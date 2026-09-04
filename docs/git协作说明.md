# Git 协作说明（校园活动交流平台 · 6 人小组）

远程仓库：`https://github.com/xiaolizaimoyu/WebGIS-.git`（别名 `origin`）

**协作模式：成员从组长仓库拉取主线 → 在各自分支上改自己负责的文件 → 推分支 → 组长统一合并回 main。**

```
成员电脑                      GitHub                   组长电脑
 git pull origin main   →   main（主线）
 建/切自己的分支 dev-X   →   在 dev-X 上写代码
 git push dev-X         →   dev-X        →  组长 git merge dev-X → main → push
```

---

## 0. 三条铁律（决定会不会冲突）

1. **永远只改、只提交自己负责的文件**（见第 3 节清单）。
2. **开工先 `git pull origin main`**，把组长合并好的最新主线拉到本地再动；收工或完成一个功能就提交一次。
3. **公共文件别乱动**：`frontend` 的布局/路由/axios/store 归**前端 C**；`backend` 的 models/db/main 归**后端 F**。缺公共能力→找 C/F 加，不自己偷改。

---

## 1. 成员首次准备（每人一次，在自己电脑）

```bash
git clone https://github.com/xiaolizaimoyu/WebGIS-.git
cd WebGIS-
git config user.name "你的GitHub用户名"      # 只设一次，之后提交都显示你
git config user.email "你的GitHub注册邮箱"    # 必须与你 GitHub 账号 Emails 里的一致，贡献才归你
```

> 需要：① 你被加为该仓库 **Collaborators**（否则无法 push）；② 你的邮箱已在 GitHub **Settings → Emails** 中登记。

---

## 2. 成员每个工作日的循环动作

```bash
# ① 先回到主线并拉到最新（组长合并后的结果）
git switch main
git pull origin main

# ② 进入你的分支：首次用 -c 创建；之后每次用 switch 进入
git switch -c dev-B            # 首次：从最新 main 分出你的分支（B 同学示例）
#   ── 以后每轮这样同步你分支上的最新主线 ──
git switch dev-B
git merge main                 # 把主线最新代码并入你的分支（无冲突会自动完成）

# ③ 改你自己负责的文件，本地跑通、自测没问题后
git status                     # 确认只改了你的文件
git add <你的文件1> <你的文件2>  # 只 add 自己的！用空格分隔
git commit -m "feat(前端B): 完成了…"     # 提交人自动是你
git push -u origin dev-B       # 首次推送；以后 git push
```

**提交节奏**：每完成一个最小功能提交一次，最迟 2–3 天一次；每条 commit 只说一件事。

**commit 信息格式**：`feat(前端B): 新增xxx` / `fix(后端D): 修复xxx` / `style(前端B): 美化` / `docs: 说明`。

---

## 3. 每个成员负责的文件（add 时照这个来）

| 成员 | 只提交这些文件 |
|---|---|
| 前端 A | `frontend/src/components/map`、`frontend/src/views/MapView.vue` |
| 前端 B | `frontend/src/views/HomeView.vue`、`PublishView.vue`、`DetailView.vue`、`MineView.vue`、`frontend/src/api/post.js` |
| 前端 C | `frontend/src/main.js`、`App.vue`、`router/`、`layouts/`、`stores/`、`assets/`、`api/request.js`、`api/const.js`、`frontend/vite.config.js`、`package.json`、`package-lock.json`、`.npmrc`、`index.html`、`frontend/README.md` |
| 后端 D | `backend/app/routers/user.py` |
| 后端 E | `backend/app/routers/post.py` |
| 后端 F | `backend/app/models.py`、`schemas.py`、`db.py`、`seed.py`、`backend/README.md` |

> 各文件头都有 `归属` 注释。改别人的文件 = 冲突源头，请克制。

---

## 4. 组长：定期把成员分支合并进 main（每 2–3 天一次）

在组长电脑：

```bash
git switch main
git pull origin main
git merge dev-F     # 逐个合并，按成员顺序
git merge dev-E
git merge dev-A
git merge dev-B
git merge dev-C
git merge dev-D
git push origin main
```

- 文件已按成员隔离，正常**很少冲突**。
- 万一报 `CONFLICT`：让相关成员一起看，打开冲突文件，保留两边要的、删掉 `<<<<<<<` / `=======` / `>>>>>>>` 标记，然后：
  ```bash
  git add <冲突文件>
  git commit -m "fix: 合并 dev-X 解决冲突"
  git push origin main
  ```

---

## 5. 常见问题自救

| 情况 | 解决 |
|---|---|
| `fatal: pathspec ... did not match` | `git add` 多个文件要用**空格**分隔、路径写全（别用顿号）；在仓库根目录执行 |
| `nothing to commit, working tree clean` | 你没有真实改动；先改代码再提交 |
| 提交作者显示不对 | 检查 `git config user.name/user.email` 是否设成自己；提交邮箱须与 GitHub 账号一致 |
| 误 `git add` 了别人文件 | `git restore --staged <文件>`（取消暂存，不删内容） |
| commit 信息写错（未 push） | `git commit --amend -m "新信息"` |
| push 被拒（rejected） | 别人推过 main/你的分支落后 → `git pull --rebase origin main` 后再 push；若仍不行把输出发组长 |
| 想不起改了哪些 | `git status`；看历史 `git log --oneline` |
| 本地改动不想要了 | `git restore <文件>`（会丢改动，慎用） |

---

## 6. 千万别提交的东西

以下已由 `.gitignore` 忽略，**不要**也不应提交：`node_modules/`、`.venv/`、`dist/`、`uploads/`、`*.db`、`__pycache__/`、`.env`。
（不要用 `git add -f` 强制添加。）

> 补充：`latest-full` 是组长暂存“待各成员认领的新功能代码”的临时分支，成员可 `git fetch origin latest-full` 后 `git checkout origin/latest-full -- <自己文件>` 取回各自文件；等大家提交完，组长会删除该临时分支。
