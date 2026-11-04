# SoulNexus 海外营销工作区

这个目录只做一件事：每天产出并发布宣传 SoulNexus（https://soulnexus.top）的短视频和帖子，把海外用户带到产品里注册、出片、付费。
产品源码在 `../SoulNexus`，这里不改代码。

## 用法

用户说"开始营销"或"继续营销"，调用 `start-marketing` skill。它打开本地营销工作台页面（`scripts/studio.py`，http://127.0.0.1:5280）：用户在页面上看脚本、上传素材、审成片和文案、点确认，不用自己操作文件；Claude 按页面信号跑各阶段：

| 阶段 | 做什么 | skill | 产物（`daily/YYYY-MM-DD/`） |
|---|---|---|---|
| E 复盘（每天最先跑） | 回填最近 7 天帖子的 24h/72h 数据，对照预测写复盘，判断限流；周一出周报、提议改 SOP | `mkt-retro` | 各天 `log.md` 的数据和 `## 复盘`、`weekly/<周>.md` |
| A 选题 | 从选题池挑选题、套格式卡（周一深度调研补池），写中英文脚本、预测和录制清单；可批量做 N 条 | `mkt-research` | `research.md`、`plan.md`、`checklist.json` |
| B 录制 | 用户按页面上的录制清单录屏/出镜/在 SoulNexus 出片，逐条拖进页面 | （用户） | `footage/*`（页面按清单命名） |
| C 剪辑 | ffmpeg 粗剪，whisper 转字幕，HyperFrames 加钩子卡、动态字幕、CTA 卡 | `mkt-edit` | `edit/out/master.mp4`、`edit/review/*.png` |
| D 发布 | 写各平台文案，经 RoxyBrowser 发布窗口上传并截图，用户点发布后记录链接 | `mkt-publish` | `posts.md`、`publish/*.png`、`log.md` |

## 事实来源

- **推广 SOP（节奏、测试计划、闸门、引流、限流判定、复盘规则）：`brand/sop.md`**
- 格式卡（固定结构 + 录制清单模板 + 成绩）：`brand/formats.md`；常驻角色：`brand/cast/`
- 选题打分：`brand/rubric.md`；选题池：`candidates.md`；对标账号和增长案例：`brand/benchmark.md`
- 活动（评论领额度）：`campaigns/`，规则在 `brand/sop.md` 第 7 节。**里面有兑换码，任何内容都不能进对外文案、评论、截图或录屏**
- 种子创作者：`creators.md`
- 产品定位、功能、对外口径：`brand/product-brief.md`
- 账号、Roxy 窗口、发布方式：`brand/accounts.md`
- 历史表现：各天的 `log.md`（A 阶段选题前先读最近 7 天）

## 硬规则

1. **不出现上游供应商**：任何对外内容（脚本、字幕、文案、画面）不得出现供应商名、线路代号、进货价。可以写公开模型名（Seedance、MiniMax、Nano Banana、GPT Image）。
2. **热点借格式，不借 IP**：不用受版权保护的角色、影视片段、音乐原曲，不用真人明星或网红的脸和声音。借的是梗、句式、话题和情绪。
3. **AI 内容要标注**：TikTok 打开 "AI-generated content" 标签；X/IG 文案里写明 made with AI。
4. **画面必须来自产品**：每条视频里至少一半时长是 SoulNexus 真实产出或工作台录屏，结尾有明确 CTA（bio link / 带 UTM 的链接）。
5. **默认人工点发布**：D 阶段把视频和文案填好，停在发布按钮前，用户确认后才点。只有 `brand/accounts.md` 里标了 `auto` 的账号可以直接发。
6. **不做灰产**：不刷量、不批量养号、不在别人评论区刷广告、不私信轰炸。
7. 对外文案英文为主；脚本同时给中文（给用户理解）和英文（实际发布）。
