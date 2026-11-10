#!/usr/bin/env python3
import base64, re, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "content/claude-fixreach.html"
OUT = ROOT / "renders/claude-fixreach"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)
html = HTML.read_text(encoding="utf-8")
m = re.search(r'<audio[^>]+src="data:audio/[^;]+;base64,([^"]+)"', html)
if not m:
    raise SystemExit("Embedded audio track not found")
audio = base64.b64decode(m.group(1))
audio_path = OUT / "voiceover.mp3"
audio_path.write_bytes(audio)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width":720,"height":1280}, device_scale_factor=1)
    page.add_init_script("window.requestAnimationFrame = () => 0;")
    page.goto(HTML.resolve().as_uri(), wait_until="load")
    page.wait_for_function("Object.values(IM).every(group => Object.values(group).every(img => img.complete && img.naturalWidth > 0))", timeout=120000)
    page.evaluate("""() => {
      document.getElementById('go').style.display='none';
      document.getElementById('rp').style.display='none';
      document.getElementById('stage').style.transform='none';
    }""")
    fps = 30
    duration = 58.6
    total = round(duration * fps)
    for n in range(total):
        t = n / fps
        page.evaluate("(t) => R(t)", t)
        page.screenshot(path=str(FRAMES / f"frame-{n:05d}.jpg"), type="jpeg", quality=88, animations="disabled")
    browser.close()

silent = OUT / "picture.mp4"
final = OUT / "FixReach-Claude.mp4"
subprocess.run(["ffmpeg","-y","-framerate","30","-i",str(FRAMES/"frame-%05d.jpg"),"-vf","scale=1080:1920:flags=lanczos,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-an",str(silent)], check=True)
subprocess.run(["ffmpeg","-y","-i",str(silent),"-i",str(audio_path),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(final)], check=True)
subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_name,width,height,r_frame_rate","-show_entries","format=duration","-of","default=noprint_wrappers=1",str(final)], check=True)
print(f"Rendered {final}")
