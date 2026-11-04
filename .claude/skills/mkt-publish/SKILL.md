---
name: mkt-publish
description: 营销阶段 D。为成片写 TikTok、X、Instagram、YouTube Shorts 文案，用 RoxyBrowser 打开对应账号窗口上传视频、填文案、打 AI 标签，停在发布按钮前等用户确认（或按 accounts.md 设置定时/自动发布），把链接记进 log.md。也处理"看评论""回评论"。
---

# 阶段 D：发布

输入：`edit/out/master.mp4`、`plan.md`、`brand/accounts.md`。产物：`posts.md`、`log.md`。

## 1. 写 posts.md

每个平台一节，英文：

- **TikTok**：caption 一到两句（钩子的延续，不复述画面）+ 3–5 个标签（1–2 个大标签如 `#aivideo`，其余是细分标签如 `#aishortdrama` `#aifilmmaking`）。置顶评论一条：讲清怎么做的 + `soulnexus.top`。个人号满 1000 粉之前主页没有可点击链接，不写 "link in bio"（见 `brand/sop.md` 第 4 节）。
- **X**：正文第一行就是钩子；可以接 2–4 条串推讲制作过程、成本、提示词；链接放在最后一条（带 UTM），不放在第一条。
- **Instagram Reels**：同 TikTok，标签可多到 5–8 个。
- **YouTube Shorts**：标题 ≤ 60 字符，描述里放带 UTM 的链接。

有「进行中」的活动挂在这条帖子上时（见 `campaigns/` 和 `brand/sop.md` 第 7 节）：TikTok 和 IG 的置顶评论换成活动模板，caption 末尾加一句活动 CTA，X 在最后一条串推里加活动说明。文案里只写关键词和 $2 能做什么，不写码。

链接一律用 `brand/accounts.md` 的 UTM 格式。逐条检查 `CLAUDE.md` 硬规则（不提供应商、标 AI）。用户在工作台页面审 `posts.md`（点「文案可以」或提修改意见）后再进下一步。

## 2. 打开账号

先确认 RoxyBrowser 桌面端已打开。两个 MCP：`roxybrowser-openapi`（管理窗口：按 ID 打开浏览器窗口）和 `roxybrowser-playwright-mcp`（`browser_connect_roxy` 连上窗口，然后 `browser_navigate` / `browser_snapshot` / `browser_click` / `browser_type` / `browser_file_upload` / `browser_take_screenshot` 操作）。工具 schema 没加载时用 ToolSearch 搜 `roxy`。上传文件用成片的绝对路径。
只用 `accounts.md` 里的**发布窗口**（所有平台主号都在这个窗口，每个平台开一个标签页），不新建窗口、不换代理，不在这个窗口里做大量搜索。窗口里账号没登录就停下来请用户登录，不代填密码、不处理验证码。

两个 MCP 都连不上时：告诉用户，把成片路径和 `posts.md` 交给他手动发，然后跳到第 4 步记录。

## 3. 上传

| 平台 | 入口 | 必做 |
|---|---|---|
| TikTok | `https://www.tiktok.com/tiktokstudio/upload` | 上传文件 → 填 caption → 打开 "AI-generated content" 开关 → 谁可以看：Everyone → 允许评论 |
| X | `https://x.com/compose/post` | 附视频 → 正文；串推逐条添加 |
| Instagram | 网页版 Create → Post/Reel | 上传 → caption → 高级设置里打开 AI 标签（有就打开） |
| YouTube | `https://studio.youtube.com` → Create → Upload | 标题、描述 → "Altered or synthetic content" 选 Yes → Shorts 自动识别（竖屏 ≤ 3 分钟） |

上传后每个平台截一张图存到 `daily/<日期>/publish/<平台>.png`（工作台页面会展示），确认预览正常、文案没被截断。
平台上要选热门音乐的话在 TikTok 编辑页里加，音量调低，不盖过口播。

**发布方式按 `accounts.md`：**
- `confirm`（默认）：停在发布/定时按钮前，截图存好，由用户在 Roxy 里点发布，再在工作台点「我已发布」。
- 用户要求定时或批量模式：用平台自带的定时发布（TikTok Studio、X 网页版都支持），时间按 `brand/sop.md` 第 1 节（美东晚 7–10 点）。
- `auto`：可以直接点发布。

## 4. 记录 log.md

```markdown
# 发布记录 <日期>
| 平台 | 账号 | 发布时间（北京） | 链接 | 状态 | 24h 播放 | 72h 播放 | 完播率 | 点赞 | 评论 | 意向评论 | 分享 | 主页/链接点击 | 备注 |

## 复盘
```

发布成功后打开帖子拿到真实链接再填。播放等数据和 `## 复盘` 留空，由 `mkt-retro`（阶段 E）到期后补。

## 5. 看评论 / 回评论（用户要求时）

打开当天帖子读评论，挑出：提问（怎么做的、多少钱、什么模型）、负面、潜在用户。草拟回复写进 `log.md` 的「评论」小节给用户看，用户确认后再回。回复像人说话，回答具体问题，不贴链接刷屏，不和人吵。
