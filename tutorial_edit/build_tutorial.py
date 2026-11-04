import asyncio, json, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / '热门视频人物替换教程2026-11-04 112906.mp4'
OUT = ROOT / 'output'
OUT.mkdir(parents=True, exist_ok=True)
FONT = 'C:/Windows/Fonts/arialbd.ttf'
FONT_REG = 'C:/Windows/Fonts/arial.ttf'
segments = [
    (313,  'THE RESULT', 'Change the character, keep the moves', 'Want to change the character in a video? Here is the result, and how I made it.'),
    (8,    'STEP 01', 'Add a reference video', 'First, add your reference video to the SoulNexus canvas.'),
    (218,  'STEP 02', 'Add your character image', 'Next, add an image of the character you want to use.'),
    (225,  'STEP 03', 'Connect both references', 'Connect the video and character image to your generation node.'),
    (260,  'STEP 04', 'Describe the replacement', 'In your prompt, reference both inputs and describe what should stay the same, like movement and background.'),
    (282,  'STEP 05', 'Generate your video', 'Choose your video model and settings, then generate your new clip.'),
    (304,  'THE RESULT', 'Review the generated clip', 'Once it is ready, play the result and check how the character and movement look.'),
    (318,  'TRY IT YOURSELF', 'Create on SoulNexus', 'Try it on SoulNexus. Use footage and character images you have permission to use.'),
]

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def card(index, label, title, narration):
    im = Image.new('RGBA', (720, 1280), (10, 18, 32, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((38, 65, 320, 118), radius=20, fill=(0, 217, 252, 255))
    d.text((58, 77), label, font=ImageFont.truetype(FONT, 25), fill=(0, 19, 28, 255))
    d.text((40, 155), 'SOULNEXUS  /  TUTORIAL', font=ImageFont.truetype(FONT_REG, 22), fill=(158, 185, 205, 255))
    d.rounded_rectangle((25, 300, 695, 825), radius=28, fill=(29, 43, 62, 255))
    d.text((42, 877), 'HOW TO', font=ImageFont.truetype(FONT, 24), fill=(0, 217, 252, 255))
    lines = textwrap.wrap(title, width=23)
    font = ImageFont.truetype(FONT, 46)
    for j, line in enumerate(lines):
        d.text((40, 930 + 61*j), line, font=font, fill=(255,255,255,255), stroke_width=0)
    for j, line in enumerate(textwrap.wrap(narration, width=43)):
        d.text((42, 1067 + 32*j), line, font=ImageFont.truetype(FONT_REG, 25), fill=(215, 228, 238, 255))
    d.text((42, 1228), 'soulnexus.top', font=ImageFont.truetype(FONT_REG, 21), fill=(145, 169, 185, 255))
    path = OUT / f'card{index}.png'
    im.save(path)
    return path

async def main():
    outputs=[]
    timings=[]
    for i,(start,label,title,words) in enumerate(segments):
        voice = OUT / f'voice{i}.mp3'
        if not voice.exists() or voice.stat().st_size == 0:
            await edge_tts.Communicate(words, 'en-US-AnaNeural', rate='+8%', pitch='+5Hz').save(str(voice))
        raw = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(voice)],text=True)
        duration = max(3.0, float(raw)+0.7)
        # Source canvas crop excludes the browser bar, account balance, and assistant panel.
        if i in (0,7):
            crop='crop=480:750:1000:220,scale=322:490:force_original_aspect_ratio=decrease'
        elif i == 4:
            crop='crop=1500:690:420:300,scale=650:500:force_original_aspect_ratio=decrease'
        else:
            crop='crop=1780:1020:40:150,scale=650:500:force_original_aspect_ratio=decrease'
        png=card(i,label,title,words)
        part=OUT / f'part{i}.mp4'
        graph=f'[1:v]{crop},setsar=1[screen];[0:v][screen]overlay=(W-w)/2:315+(495-h)/2:shortest=1,format=yuv420p[v];[2:a]adelay=250|250,apad[a]'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',str(png),'-ss',str(start),'-i',str(SRC),'-i',str(voice),'-filter_complex',graph,'-map','[v]','-map','[a]','-t',f'{duration:.3f}','-c:v','libx264','-preset','veryfast','-crf','19','-r','30','-c:a','aac','-b:a','160k',str(part)])
        outputs.append(part)
        timings.append({'source_start':start,'duration':round(duration,3),'title':title,'voiceover':words})
    manifest=OUT/'concat.txt'
    manifest.write_text(''.join("file '"+p.as_posix()+"'\n" for p in outputs),encoding='utf-8')
    final=OUT/'soulnexus_tiktok_tutorial.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(manifest),'-c','copy','-movflags','+faststart',str(final)])
    (OUT/'edit_notes.json').write_text(json.dumps(timings,ensure_ascii=False,indent=2),encoding='utf-8')
    print(final)

asyncio.run(main())
