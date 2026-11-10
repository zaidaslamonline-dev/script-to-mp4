#!/usr/bin/env python3
"""Render the single FixReach 9:16 campaign with the supplied Sid/Lala transparent poses.

The renderer uses deterministic Pillow compositing and FFmpeg encoding. It does not
invent character artwork: all character frames are loaded from assets/characters.
"""
from __future__ import annotations
import argparse, json, math, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 720, 1280, 24
ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "assets" / "characters"

POSES = {
    "lala_frustrated": "LALA-13_Frustrated-Hand-on-Forehead.png",
    "lala_phone": "LALA-08_Holding-Smartphone-Left-Hand-Gesture.png",
    "lala_question": "LALA-09_Asking-Question-Both-Palms-Up.png",
    "lala_point": "LALA-11_Making-Point-Index-Finger-Raised.png",
    "lala_happy": "LALA-17_Thumbs-Up-Approval.png",
    "lala_cash": "LALA-24_Counting-and-Holding-Cash.png",
    "sid_surprised": "SID-20_Surprised-Open-Mouth.png",
    "sid_explain": "SID-05_Explaining-Palm-Up-Mouth-Open.png",
    "sid_point": "SID-07_Pointing-Right-Mouth-Open.png",
    "sid_emphasis": "SID-17_Emphasising-Point-Speaking.png",
    "sid_phone": "SID-13_Smartphone-and-Open-Hand-Gesture.png",
    "sid_win": "SID-24_Celebrating-Both-Fists-Raised.png",
}
SCENES = [
    {"start":0.0,"end":12.0,"title":"ENQUIRIES ARE COMING IN…","kicker":"BUT WHERE ARE THE BOOKINGS?","lala":"lala_frustrated","sid":None,"accent":"#ff5b55","cards":["MISSED CALLS","EMPTY CALENDAR"]},
    {"start":12.0,"end":25.0,"title":"PHONE GARAM. BUSINESS THANDA.","kicker":"PRICE ONLY  •  OUT OF AREA  •  MAYBE LATER","lala":"lala_phone","sid":"sid_surprised","accent":"#ff9b3d","cards":["PRICE ONLY?","OUT OF SERVICE AREA?","CALL BACK LATER?"]},
    {"start":25.0,"end":39.0,"title":"IT'S NOT ABOUT MORE LEADS.","kicker":"IT'S ABOUT BETTER-QUALIFIED ENQUIRIES.","lala":"lala_question","sid":"sid_emphasis","accent":"#d7ff48","cards":["QUANTITY  ↓","QUALITY  ↑"]},
    {"start":39.0,"end":65.0,"title":"FIXREACH HELPS YOU FOCUS","kicker":"THREE SIMPLE QUALIFYING QUESTIONS","lala":"lala_point","sid":"sid_explain","accent":"#50e6c2","cards":["01  WHAT'S THE PROBLEM?","02  WHERE'S THE LOCATION?","03  WHEN IS SERVICE NEEDED?"]},
    {"start":65.0,"end":78.0,"title":"NOW YOU KNOW WHO NEEDS HELP.","kicker":"PLAN THE RIGHT HOME-SERVICE VISIT.","lala":"lala_happy","sid":"sid_win","accent":"#d7ff48","cards":["CLEARER CUSTOMER NEED","BETTER VISIT PLANNING"]},
    {"start":78.0,"end":92.84,"title":"REPAIR BUSINESS OWNERS","kicker":"WANT BETTER-QUALIFIED LEADS?","lala":"lala_cash","sid":"sid_point","accent":"#50e6c2","cards":["FIXREACH","COMMENT “LEADS”","GET YOUR FREE CAMPAIGN AUDIT"]},
]

def font(size, bold=True):
    candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fit_text(draw, text, max_width, start=58, minimum=28, bold=True):
    for size in range(start, minimum-1, -2):
        f=font(size,bold)
        if draw.textbbox((0,0),text,font=f)[2] <= max_width: return f
    return font(minimum,bold)

def parse_srt(path):
    if not path or not path.exists(): return []
    raw=path.read_text(encoding="utf-8",errors="replace").replace("\r","")
    blocks=re.split(r"\n\s*\n",raw.strip())
    out=[]
    def stamp(s):
        h,m,rest=s.split(":"); sec,ms=rest.split(",")
        return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
    for b in blocks:
        lines=b.splitlines()
        if len(lines)<3 or "-->" not in lines[1]: continue
        a,z=[x.strip().split()[0] for x in lines[1].split("-->")]
        out.append((stamp(a),stamp(z)," ".join(lines[2:]).strip()))
    return out

def load_pose(key, cache):
    if not key: return None
    if key not in cache:
        path=CHAR_DIR/POSES[key]
        if not path.is_file(): raise SystemExit(f"Missing supplied character pose: {path}")
        im=Image.open(path).convert("RGBA")
        # Trim transparent margins without altering the character artwork.
        bbox=im.getbbox()
        if bbox: im=im.crop(bbox)
        cache[key]=im
    return cache[key]

def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy,radius=radius,fill=fill,outline=outline,width=width)

def make_frame(t, duration, captions, pose_cache, bg_cache):
    idx=next((i for i,s in enumerate(SCENES) if s["start"] <= t < s["end"]),5)
    s=SCENES[idx]; local=t-s["start"]; span=s["end"]-s["start"]
    if idx not in bg_cache:
        bg=Image.new("RGB",(W,H),(9,12,24)); px=bg.load()
        c=[int(s["accent"][i:i+2],16) for i in (1,3,5)]
        for y in range(H):
            k=0.08+0.16*(y/H)
            col=tuple(int((12,16,31)[j]*(1-k)+c[j]*k) for j in range(3))
            for x in range(W): px[x,y]=col
        bg_cache[idx]=bg
    im=bg_cache[idx].copy().convert("RGBA")
    d=ImageDraw.Draw(im,"RGBA")
    # Subtle animated accent bars / radial energy lines.
    phase=(t*0.8)%(2*math.pi)
    for n in range(7):
        x=int((n*137 + t*45)%(W+180))-90
        d.rounded_rectangle((x,0,x+3,H),radius=2,fill=(255,255,255,12))
    d.ellipse((W-250+int(math.sin(phase)*18),-190, W+160,220),fill=(255,255,255,12))
    # Header / scene counter.
    d.text((44,38),"FIXREACH  /  LOCAL SERVICE GROWTH",font=font(19),fill=(255,255,255,190))
    d.text((W-95,38),f"0{idx+1}/06",font=font(20),fill=(255,255,255,210))
    # Character stage with gentle entrance and breathing movement.
    keys=[s["lala"],s["sid"]]
    slots=[(24,440,310),(390,430,290)] if keys[1] else [(170,410,390),(0,0,0)]
    for key,(x,y,target_h) in zip(keys,slots):
        if not key: continue
        pose=load_pose(key,pose_cache)
        h=target_h; w=int(pose.width*h/pose.height)
        character=pose.resize((w,h),Image.Resampling.LANCZOS)
        entrance=max(0,min(1,local/0.65))
        bob=int(math.sin(t*2.2+(0 if key.startswith("lala") else 1.4))*7)
        x=int(x+(1-entrance)*(-35 if key.startswith("lala") else 35))
        im.alpha_composite(character,(x,y+bob))
    d=ImageDraw.Draw(im,"RGBA")
    # Bold kinetic typography panel.
    title_y=145
    title=s["title"]
    tf=fit_text(d,title,W-72,54,34)
    box=d.textbbox((0,0),title,font=tf)
    tw=box[2]
    rounded(d,((W-tw)//2-22,title_y-12,(W+tw)//2+22,title_y+box[3]+20),18,(3,7,18,175),outline=tuple(int(s["accent"][i:i+2],16) for i in (1,3,5))+(180,),width=2)
    d.text(((W-tw)//2,title_y),title,font=tf,fill="white",stroke_width=1,stroke_fill=(0,0,0,90))
    kf=fit_text(d,s["kicker"],W-72,25,18)
    kw=d.textbbox((0,0),s["kicker"],font=kf)[2]
    d.text(((W-kw)//2, title_y+82),s["kicker"],font=kf,fill=s["accent"])
    # Animated UI cards, staggered.
    cards=s["cards"]
    card_y=850 if idx in (0,1,2,4) else 835
    for j,label in enumerate(cards):
        if idx==3: card_y=790+j*90
        elif idx==5: card_y=840+j*86
        else: card_y=850+j*82
        slide=max(0,min(1,(local-j*0.16)/0.42))
        left=int(54+(1-slide)*90)
        rounded(d,(left,card_y,left+W-108,card_y+62),18,(4,10,22,220),outline=tuple(int(s["accent"][i:i+2],16) for i in (1,3,5))+(230,),width=2)
        d.text((left+22,card_y+15),label,font=fit_text(d,label,W-160,26,18),fill="white")
    # Captions, timed from Whisper SRT.
    cap=next((c for c in captions if c[0] <= t < c[1]),None)
    if cap:
        txt=cap[2].upper()
        cf=fit_text(d,txt,W-90,29,19)
        bb=d.textbbox((0,0),txt,font=cf); cw=bb[2]
        rounded(d,((W-cw)//2-20,1120,(W+cw)//2+20,1190),14,(0,0,0,220))
        d.text(((W-cw)//2,1132),txt,font=cf,fill="white")
    # Brand accent progress indicator.
    d.rounded_rectangle((44,H-32,W-44,H-22),radius=5,fill=(255,255,255,45))
    d.rounded_rectangle((44,H-32,44+int((W-88)*min(1,t/duration)),H-22),radius=5,fill=s["accent"])
    return im.convert("RGB")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--voiceover",type=Path,required=True)
    ap.add_argument("--captions",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--duration",type=float,default=92.84)
    args=ap.parse_args()
    missing=[str(CHAR_DIR/POSES[k]) for s in SCENES for k in (s["lala"],s["sid"]) if k and not (CHAR_DIR/POSES[k]).is_file()]
    if missing:
        sys.exit("Character pack not installed in assets/characters. Missing required poses:\n"+"\n".join(missing))
    if not args.voiceover.is_file(): sys.exit(f"Voiceover missing: {args.voiceover}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    caps=parse_srt(args.captions)
    pose_cache={}; bg_cache={}
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(args.voiceover.resolve()),"-map","0:v:0","-map","1:a:0","-vf","scale=1080:1920:flags=lanczos,fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","19","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(args.output.resolve())]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    frames=math.ceil(args.duration*FPS)
    try:
        for n in range(frames):
            t=n/FPS
            frame=make_frame(t,args.duration,caps,pose_cache,bg_cache)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        code=proc.wait()
    except BrokenPipeError:
        code=proc.wait()
    if code: raise SystemExit(f"FFmpeg render failed with exit code {code}")
    print(json.dumps({"status":"rendered","output":str(args.output),"duration_seconds":args.duration,"fps":30,"resolution":"1080x1920","scenes":len(SCENES),"character_poses":len(POSES)}))

if __name__=="__main__": main()
