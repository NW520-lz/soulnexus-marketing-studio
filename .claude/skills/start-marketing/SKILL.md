---
name: start-marketing
description: 每日营销流程的总入口。用户说"开始营销""继续营销""今天营销""营销进度"时使用。打开本地营销工作台页面（http://127.0.0.1:5280），用户在页面上传素材、看成片、审文案、点确认；本 skill 先跑 mkt-retro（E，回填数据与复盘），再按页面信号依次调用 mkt-research（A）→ 等录制（B）→ mkt-edit（C）→ mkt-publish（D），每个阶段之间在后台等待用户的点击。也处理"批量做 N 条"。流程规则以 brand/sop.md 为准。
---

# 开始营销

用户不碰文件：所有上传、预览、确认都在工作台页面上。你负责跑每个阶段，并通过两个命令和页面同步（下文 `PY` 指 `"/d/AI agent/python/python"`，`DAY` 指当天目录 `daily/<YYYY-MM-DD>`）：

- 改页面状态：`$PY scripts/studio.py status $DAY --stage <阶段> [--busy] --message "<一句话>"`
  阶段：`research` `recording` `editing` `review_edit` `writing_posts` `review_posts` `uploading` `review_publish` `done`。
  `--busy` 表示你正在做（页面显示转圈和 message）；不带表示轮到用户（页面显示 message 作为提示）。
- 等用户点击：用 Bash `run_in_background` 跑 `$PY scripts/studio.py wait $DAY`。它在用户点按钮时退出并打印信号 JSON（`action` + `note`），你会被唤醒。处理完一个信号后用 `status ... --handled` 标记已处理。

## 1. 打开工作台

1. `curl -s -m 2 http://127.0.0.1:5280/api/days`。没响应就用 Bash `run_in_background` 跑 `$PY scripts/studio.py serve`。
2. 用 `cmd //c start http://127.0.0.1:5280` 打开浏览器（用户说页面已开着就跳过）。
3. 定位 `DAY`：今天的目录，不存在就创建（含空 `footage/`）。用户点名某天或说"再开一条"（建 `daily/<日期>-2/`）时按用户的来。
4. 先跑阶段 E：设 `research --busy "正在回填数据和复盘"`，调用 `mkt-retro`（周一会顺带做周复盘）。有疑似限流，或周复盘提出了 SOP 修改，先在对话里告诉用户，等用户回复再往下走。没有到期的帖子就直接跳过。

## 2. 从哪里继续

读 `DAY/status.json` 和 `DAY/signals.jsonl`（没有就当作 `research`、0 条已处理）：

| 情况 | 动作 |
|---|---|
| 有未处理的信号（条数 > `handled_signals`） | 按第 3 节处理最新那条 |
| 没有 `plan.md` | 跑阶段 A |
| `busy` 为 true（上次做到一半中断了） | 重做该阶段 |
| 处于 `recording` / `review_*` | 告诉用户"在工作台页面上继续"，挂起等待 |
| `done` | 告诉用户今天已完成，问要不要再开一条 |

## 3. 阶段与信号

| 触发 | 先设状态 | 做什么 | 做完设状态并挂起等待 |
|---|---|---|---|
| 开始 / 无 plan.md | `research --busy "正在找今天的选题"` | 调用 `mkt-research` | `recording "按清单录素材，逐条拖进来，齐了点「开始剪辑」"` |
| `footage_ready` | `editing --busy "正在剪辑"` | 调用 `mkt-edit` | `review_edit "看成片，满意点「可以，写文案」"` |
| `edit_changes` | `editing --busy "按你的意见重剪"` | 按 `note` 修改，走 `mkt-edit` 第 5 节末尾的改法 | `review_edit` |
| `edit_approved` | `writing_posts --busy "正在写各平台文案"` | `mkt-publish` 第 1 步，写 `posts.md` | `review_posts "检查文案，没问题点「文案可以，去上传」"` |
| `posts_changes` | `writing_posts --busy "按你的意见改文案"` | 按 `note` 改 `posts.md` | `review_posts` |
| `posts_approved` | `uploading --busy "正在 Roxy 里上传"` | `mkt-publish` 第 2–3 步，截图存 `DAY/publish/` | `review_publish "到 Roxy 发布窗口检查后点发布，再点「我已发布」"` |
| `published` | `uploading --busy "正在记录发布链接"` | `mkt-publish` 第 4 步，结合 `note` 记 `log.md` | `done "今天完成"`，不再挂起 |

每处理完一个信号都要 `--handled`。处理中出错（素材坏了、Roxy 连不上）：设回该等待阶段（不带 `--busy`），`--message` 写清楚用户要做什么，再挂起等待。

## 3.1 批量模式

用户说"批量做 N 条""这周录 N 条"（`brand/sop.md` 默认每周两次批量制作）时：
1. 阶段 A 走 `mkt-research` 第 6 节，一次给 N 个发布日建好目录，每个目录都设成 `recording`。
2. 每个日期目录各在后台跑一个 `wait`。哪天收到信号就处理哪天，流程和第 3 节一样。
3. D 阶段改用平台定时发布：每条排到它自己那天的美东晚 7–10 点（北京时间见 `brand/sop.md` 第 1 节），不再等用户当天点发布。用户检查定时设置后点「我已发布」，`log.md` 的发布时间写定时的时间。

## 4. 和用户的对话

页面是主要界面，对话里只说必要的：每个阶段完成时一两句（做了什么、页面上该点什么）。用户在对话里直接下指令（"钩子换一个""今天不发 X"）也照做，做完同步页面状态。
等待信号期间对话可以结束；`wait` 命令一直在后台，用户点击后你会被唤醒继续。
