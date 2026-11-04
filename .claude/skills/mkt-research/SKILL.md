---
name: mkt-research
description: 营销阶段 A。从选题池（candidates.md）和当天快查到的热点里挑选题，套格式卡（brand/formats.md），写中英文脚本、工作台出片配方、录制清单和盲预测；周一或选题池不足时做深度调研（TikTok、Instagram、X、Reddit、广告库），把选题池补满。支持一次做多条（批量模式）。由 start-marketing 调用，也可在用户说"找选题""今天拍什么""批量做 N 条"时直接用。
---

# 阶段 A：选题与脚本

产物：`daily/<日期>/research.md`（证据）、`daily/<日期>/plan.md`（要拍的东西）、`daily/<日期>/checklist.json`（工作台页面显示的录制清单），以及对 `candidates.md` 的更新。
开始前读 `brand/sop.md`（节奏、当前测试计划、闸门）、`brand/product-brief.md`、`brand/accounts.md`、`brand/formats.md`、`brand/rubric.md`、`candidates.md`。

## 1. 回看

数据回填和复盘由 `mkt-retro`（阶段 E）在这之前做完。这里只读结论：最近 7 天各 `log.md` 的 `## 复盘` 段，以及最新一份 `weekly/*.md`。今天的选题要吸收里面的"下次怎么做"。`campaigns/` 里有「准备中」的活动、但还没定挂在哪条帖子上时，今天的选题优先考虑适合挂活动的（成片好看、$2 额度能做出同款）。

## 2. 搜信号

先判断今天做哪一档：

- **快查**（平常）：只看 TikTok 和 X，找 3–5 条信号，15 分钟内结束。用来确认选题池里排前面的选题还在热，顺便捡当天新冒出来的格式。
- **深度调研**（周一，或 `candidates.md` 里「待用」少于 5 条）：下面所有来源都过一遍，找 8–12 条信号。同时更新 `brand/benchmark.md`（每个对标账号拆最近最好的 3 条），并把新选题补进 `candidates.md`，直到「待用」至少 10 条。11-11（路线图阶段 2）起，深度调研时再顺带找 2–3 个种子创作者补进 `creators.md`：做 AI 短剧、连载或 AI 视频教程，近期播放稳定，评论区活跃。

信号要**带链接和热度证据**（播放、点赞、评论数、发布时间），分两类：

- **热点**：最近 7 天在涨的话题、梗、句式、BGM、短剧套路（霸总、复仇、身份反转、穿越、狼人等）。
- **痛点**：AI 视频创作者在抱怨什么（角色变脸、失败扣积分、等太久、提示词不会写、一集要几个工具来回导、成本算不清）。

来源和做法（能用哪个用哪个，失败就换下一个，记下哪个源今天不可用）：

| 来源 | 怎么查 |
|---|---|
| TikTok | RoxyBrowser 打开**调研窗口**（见 `brand/accounts.md`），搜 `ai short drama`、`ai drama`、`ai short film`、`ai video`、`#aifilm`、`reelshort`；看近 7 天高播放视频和置顶评论。TikTok Creative Center（`ads.tiktok.com/business/creativecenter`）看 Trending hashtags / songs / Top ads（行业选 Apps、Entertainment） |
| Instagram | 调研窗口里搜同样的标签，看 Reels |
| X | 调研窗口登录了 X 就在那里搜；否则在发布窗口少量搜（Top 和 Latest 各一页）。搜 `AI short film`、`AI drama`、`kling credits`、`seedance`、`character consistency`，按 Latest 和 Top 各看一遍 |
| Reddit | `firecrawl_search` 加 `site:reddit.com`，社区：r/aivideo、r/HiggsfieldAI、r/KlingAI_Videos、r/runwayml、r/StableDiffusion |
| 竞品广告 | Meta Ad Library 搜 Higgsfield、Topview、Creatify、Arcads、Invideo；看它们正在投的素材开头和 offer |
| 短剧投放 | 用户放在 `inputs/` 的 agency / ADX 广告数据（先读）；ReelShort、DramaBox、ShortMax 近期在投素材的前 3 秒 |

Roxy 不可用时用 `firecrawl_search` / `firecrawl_scrape` 和 exa 搜索代替，并在 `research.md` 顶部写明。
只看、不互动：不点赞、不评论、不关注。

`research.md` 格式：

```markdown
# 调研 <日期>（快查 / 深度调研）
不可用的来源：…
## 信号
| # | 类型 | 来源链接 | 内容 | 热度证据 | 对我们的意义 |
## 结论
三句话：今天什么在火、创作者最痛的是什么、我们能怎么接。
```

## 3. 选题

从 `candidates.md` 里「待用」的条目和今天的信号中选 3 个候选。每个候选都要是「热点或痛点 × 一个 SoulNexus 能演示的功能」，并且套一张 `brand/formats.md` 里的格式卡（F1 制作过程 / F2 痛点对比 / F3 角色连载 / F4 成本对比）。
- 今天轮到哪张卡，按 `brand/sop.md` 的「当前测试计划」决定。
- 连载和续集优先复用 `brand/cast/` 里的常驻角色。
- 涉及价格先查 `https://soulnexus.top/api/pricing`。

按 `brand/rubric.md` 给每个候选打 5 项分。总分最高、且 ≥ 15 的进 `plan.md`，另外两个写成备选。
然后更新 `candidates.md`：用掉的那条标「已用 <日期>」，今天新想到但没用上的选题追加进去。
最后检查 `CLAUDE.md` 硬规则：借格式不借 IP、不出现供应商。

钩子和结构先用格式卡里的钩子句式；要换新句式时参考 `viral-hooks`、`viral-tiktok-content`、`viral-short-form-ideas` 这几个 skill。

## 4. 写 plan.md

```markdown
# <选题标题>  (<格式卡 F1–F4>, <时长>s, 平台: TikTok / Reels / Shorts / X)

## 为什么做
证据（链接到 research.md 的信号编号或 candidates.md 的编号）+ 要打动的人 + 看完希望他做什么。

## 钩子（前 3 秒）
主钩子：<屏幕字，英文，≤ 8 词>
画面：… 口播：…
另给 2 个备选钩子。

## 预测（发布前写完，之后不改）
- TikTok 24h 播放：0–200 / 200–1k / 1k–10k / 10k+ 选一档
- 完播率：< 10% / 10–25% / > 25% 选一档
- 一句判断：这条比 <最近一条同格式或上一条> 好还是差，为什么
（同格式已有 ≥ 5 条数据后，播放改写具体区间，例如 800–1500）

## 脚本
| 时间 | 画面 | 口播 / 字幕（EN，实际发布用） | 中文（给你理解） | 素材文件 |
|---|---|---|---|---|
（每行对应一个素材文件名，沿用格式卡的文件名）

## 工作台出片配方
在 SoulNexus 里要做出来的 AI 镜头：入口（画布 / 视频页 / 短剧工作台）、模型、英文提示词、参考图（常驻角色写明 `brand/cast/<角色>/` 里的哪张图）、比例、时长、预计花费。
做的时候同时录屏——录屏本身就是素材。

## 录制清单（阶段 B）
从格式卡的「录制清单模板」改起，逐条列：文件名、录什么、横竖、时长、注意点。规格：
- 出镜 / 手机实拍：竖屏 1080×1920，30fps，光线正面，环境安静
- 录屏：OBS 或系统录屏 1920×1080，浏览器缩放 125%，鼠标移动慢一点；剪辑时会放大局部
- 口播：可以单独录音频 `vo.m4a`，按脚本 EN 列念
- 工作台导出的成片：直接下载原文件
全部放进 `daily/<日期>/footage/`，文件名用清单里的。

## 备选选题
两条，各一句话 + 分数。
```

## 5. 写 checklist.json

把「录制清单」逐条写成 JSON 数组，文件名必须和脚本表「素材文件」列一致（工作台按它命名用户上传的文件）：

```json
[
  {"file": "01-hook.mp4", "what": "录什么、怎么录（中文，一两句）", "kind": "录屏 | 出镜 | 口播 | 工作台成片 | 音乐", "orientation": "竖屏 | 横屏 | ", "seconds": 4, "required": true}
]
```

可有可无的素材（BGM、补充镜头）写 `"required": false`。

## 6. 批量模式

用户说"批量做 N 条""这周录 N 条"时：
1. 一次选 N 个选题，格式卡尽量交替。
2. 给接下来 N 个发布日各建一个 `daily/<日期>/`，每个目录里分别写 `plan.md` 和 `checklist.json`。`research.md` 只写在第一天的目录里，其余几天的 `plan.md` 引用它。
3. 能一起录的素材（同一次打开画布、同一个角色），在各天的清单里写明"和 <日期> 的 0X 一起录"。

写完在对话里用两三句说今天（或这一批）的选题和钩子，告诉用户去工作台页面按清单上传；批量时提醒用户在页面顶部切换日期。
