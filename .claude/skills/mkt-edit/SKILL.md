---
name: mkt-edit
description: 营销阶段 C。把 daily/<日期>/footage/ 里用户录好的素材按 plan.md 的脚本剪成竖屏成片：ffmpeg 粗剪（render.py）→ whisper 逐词时间戳（transcribe.py）→ HyperFrames 包装（钩子大字、TikTok 式逐词高亮字幕、结尾 CTA 卡）→ 抽帧自检。由 start-marketing 调用，也可在用户说"剪吧""重剪""改一下剪辑"时直接用。
---

# 阶段 C：剪辑

输入：`plan.md`（脚本表，每行对应一个素材文件）和 `footage/`。
产物：`edit/edit.json`、`edit/words.json`、`edit/subs.srt`、`edit/out/base.mp4`（粗剪）、`edit/motion/`（包装工程）、`edit/out/master.mp4`（成片）、`edit/review/*.png`。

工具都已装好：ffmpeg 8.1、faster-whisper（`D:\AI agent\python`，small 模型已缓存）、HyperFrames 0.8.207（项目级 skill `/hyperframes`，CLI 用 `npx --yes hyperframes@0.8.207`）。
品牌包装模板在 `brand/motion/`（`index.html` 钩子卡 + CTA 卡，`captions.html` 逐词高亮字幕），样式说明见 `brand/product-brief.md`「视频包装样式」。

## 1. 盘点素材

对 `footage/` 每个文件跑 `ffprobe -v error -show_entries stream=codec_type,width,height,duration -of compact <文件>`。
和 `plan.md` 录制清单逐条对照：缺的、时长不够的、横竖不对的列出来。缺关键镜头（钩子、产品画面、结尾 CTA）就停下来告诉用户补录；缺次要镜头就用已有素材顶上，并在交付时说明。

需要看画面内容时抽帧：`ffmpeg -ss <秒> -i <文件> -frames:v 1 -vf scale=480:-1 edit/review/<名字>.png`，再读图片。

## 2. 粗剪 base.mp4

写 `edit/edit.json`（格式见 `scripts/render.py` 顶部说明），**不写 `subtitles`**——字幕由第 4 步包装。`output` 设为 `edit/out/base.mp4`。原则：

- 前 3 秒就是钩子画面，不要片头 logo、不要淡入。
- 每个镜头 1.5–4 秒，录屏可以更长但要用 `crop` 放大到正在操作的区域（`"crop": "中心x,中心y,放大倍数"`，倍数 1.5–2.5 常用）。
- 至少一半时长是 SoulNexus 产出或工作台画面（`CLAUDE.md` 规则 4）。
- 最后 2.5 秒留给 CTA 卡（会盖住画面），这段放产品画面或成片高光，不放关键台词。
- 总时长按 `plan.md`，TikTok 15–45 秒为主；X 上同一条成片即可（X 普通账号上限 140 秒）。
- 口播单独录的放进 `voiceover`；背景音乐只用用户放进 `footage/` 的可商用音乐。热门 BGM 在 TikTok 发布时由平台内添加（D 阶段），不要烧进视频。

```
"/d/AI agent/python/python" scripts/render.py daily/<日期>/edit/edit.json
```

**可选：上色转场（colorize）。** 黑白带运动模糊 → 彩色从左扫入 → 旋焦回正，适合"剧本/草图变成成片"的转场，或结尾高光。先出一段处理后的片段，再当普通素材写进 `edit.json`：

```
scripts/colorize/.venv/Scripts/python -I scripts/colorize/scripts/colorize.py <素材> --size 1080x1920 --duration 1.2 --max-length 4 -o daily/<日期>/edit/src/<名字>.mp4
```
`edit.json` 里 `"file": "edit/src/<名字>.mp4"`。注意：
- 前约 1 秒是糊的黑白，**不要放在第 0 秒**，钩子文字这段读不出来；放在钩子之后的转场或收尾。
- 一条片子最多用一次，用完过自检。需要 OpenGL 3.3，换机器先试跑。
- 用完问用户或看数据：带它和不带它的变体完播差多少，没有提升就不再用（见 `mkt-retro`）。

**可选：配音（TTS，ElevenLabs）。** 默认不配音；用户说要配音、或 `plan.md` 写了口播时才做。没有 `edit/vo.json` 就是纯字幕流程，不用改任何东西。
1. 把脚本里要念的话改写成口语句子（屏幕字太碎，直接念不自然），按粗剪的时间点写 `edit/vo.json`：`{"output": "edit/src/vo.m4a", "lines": [{"start": 0.4, "text": "..."}]}`。每句念完要赶在下一句开始之前，超了就缩短文字，不要加速。
2. `python scripts/tts.py daily/<日期>/edit/vo.json`。每句按"文字+音色+模型"缓存在 `edit/vo/`，重剪不会重复扣字符；改了文字才会重新合成。
3. `edit.json` 里加 `"voiceover": {"file": "edit/src/vo.m4a"}`，重跑 `render.py`。第 3 步转写 base.mp4 时字幕会自动跟着配音的时间走。
- 密钥和音色：`ELEVENLABS_API_KEY`、`ELEVENLABS_VOICE_ID` 放工作区根目录的 `.env`（一行一个 `KEY=值`）。**密钥不进 plan.md、posts.md、截图、录屏，也不贴进对话。**
- 免费档不能商用，也不能克隆音色（账户 `can_use_instant_voice_cloning` 为 False）。发布用的视频先确认已是付费档。
- 克隆自己的声音也算 AI 配音：发布时 AI 标签照开（硬规则 3）。
- 模型默认 `eleven_multilingual_v2`（官方文档里最稳的一档）；想试别的用 `--model`。

## 3. 字幕时间戳

有口播时，对**粗剪成片**转写，时间轴才和成片对得上：

```
"/d/AI agent/python/python" scripts/transcribe.py daily/<日期>/edit/out/base.mp4 daily/<日期>/edit/subs.srt --words-json daily/<日期>/edit/words.json
```

读 `words.json`，对照脚本 EN 列改错词（只改 `text`，不动时间）。产品名和模型名已作为提示词给了 whisper，仍要核对。
没有口播：不建 `words.json`，只有钩子卡和 CTA 卡；需要字幕时按脚本和剪辑单时间手写 `words.json`（每个词一条 `{"text","start","end"}`）。
对外发布只用英文字幕。

## 4. 包装 master.mp4

```
"/d/AI agent/python/python" scripts/motion.py daily/<日期> --hook "<plan.md 主钩子的屏幕字>" [--cta-title "..."] [--cta-sub "soulnexus.top"]
cd daily/<日期>/edit/motion
npx --yes hyperframes@0.8.207 check --json
npx --yes hyperframes@0.8.207 render -o ../out/master.mp4 --quality delivery --quiet
```

- 钩子有两种样式，用 `--hook-style` 选：`card`（默认，青底卡片）和 `typer`（终端打字机，一个字一个字打出来，适合"输入一句话 → 出成片"这类 AI 提示词钩子）。新样式 = 在 `brand/motion/` 加一个 `hook-<样式>.html`，再把名字加进 `motion.py` 的 choices。
- 钩子屏幕字 ≤ 8 个英文词；CTA 标题默认 "Make your AI short drama"，按选题改（例如 "Keep every character consistent"）。
- `check` 的 error 必须修完再渲染；`nested_structure_needs_subcomposition`（#cta）这条 warning 可以忽略。
- 想加模板之外的效果（转场、放大强调、贴纸）时先读 `/hyperframes` skill，再改 `edit/motion/` 里当天的文件；通用的改动回写到 `brand/motion/` 模板。
- HyperFrames 渲染失败：把 `edit.json` 的 `output` 改成 `edit/out/master.mp4` 并加 `"subtitles": "edit/subs.srt"`，用 `render.py` 出静态字幕版，并告诉用户这一条没有包装。

## 5. 自检

全部做完才交给用户：
1. `ffprobe` 确认 1080×1920、30fps、有音轨，时长符合预期。
2. 第 0.8 秒（钩子卡）、每个镜头中点、最后 1 秒（CTA 卡）各抽一帧到 `edit/review/`，读图检查：字幕一行内、没被裁、没挡住关键画面；没有出现供应商名或内部线路名；画面没有黑边。
3. 响度：`ffmpeg -i edit/out/master.mp4 -af ebur128 -f null - 2>&1 | grep "I:"`，应在 -14 LUFS 左右。低于 -15 就跑 `python scripts/loudfix.py daily/<日期>/edit/out/master.mp4`（两遍测量后精确校准，画面不重编码，原文件留作 `master.pre-loudfix.mp4`）；`render.py` 的单遍 loudnorm 对短片会偏低好几 dB，配音片尤其明显。

关键帧留在 `edit/review/`，工作台页面会和成片一起展示给用户审。改剪辑改 `edit.json` 重跑第 2–4 步；只改字幕、钩子、CTA 从第 4 步重跑。不动 `footage/`。
