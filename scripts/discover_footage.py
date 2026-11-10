#!/usr/bin/env python3
"""Discover, rank and download scene-matched reference footage automatically.

Sources:
- YouTube search via yt-dlp (no URL supplied by the operator)
- Optional Pexels API search when PEXELS_API_KEY is configured

Writes production/footage/sources.json and production/footage/scene-NN.mp4.
"""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"production/footage"
SCENES=[
 {"id":1,"query":"home repair technician frustrated missed calls phone empty calendar"},
 {"id":2,"query":"plumber electrician home service technician answering customer phone"},
 {"id":3,"query":"home repair professional customer consultation quality service"},
 {"id":4,"query":"home maintenance technician inspecting plumbing electrical repair tools"},
 {"id":5,"query":"professional home repair technician completing service happy homeowner"},
 {"id":6,"query":"small business owner home services workshop repair team"},
]
def run(cmd):
 try:
  return subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
 except subprocess.TimeoutExpired as exc:
  return subprocess.CompletedProcess(cmd,124,exc.stdout or "",(exc.stderr or "")+"\\nTimed out after 180 seconds")
def yt_candidates(query):
 p=run(["yt-dlp","--flat-playlist","--dump-single-json","--no-warnings","--socket-timeout","15","--retries","1",f"ytsearch5:{query}"])
 if p.returncode: return []
 try: data=json.loads(p.stdout)
 except Exception: return []
 entries=data.get("entries") or []
 out=[]
 for e in entries:
  if not e: continue
  vid=e.get("id"); webpage=e.get("webpage_url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None)
  if not webpage: continue
  out.append({"url":webpage,"title":e.get("title",""),"duration":e.get("duration") or 0,
   "width":e.get("width") or 0,"height":e.get("height") or 0,"source":"youtube"})
 return out
def pexels_candidates(query):
 key=os.getenv("PEXELS_API_KEY")
 if not key: return []
 try:
  import urllib.request, urllib.parse
  url="https://api.pexels.com/videos/search?"+urllib.parse.urlencode({"query":query,"per_page":8,"orientation":"portrait"})
  req=urllib.request.Request(url,headers={"Authorization":key})
  with urllib.request.urlopen(req,timeout=25) as res: data=json.loads(res.read())
  out=[]
  for v in data.get("videos",[]):
   files=sorted(v.get("video_files",[]),key=lambda f:(f.get("height",0),f.get("width",0)),reverse=True)
   if files:
    f=files[0];out.append({"url":f.get("link"),"title":v.get("url","Pexels clip"),"duration":v.get("duration",0),"width":f.get("width",0),"height":f.get("height",0),"source":"pexels"})
  return out
 except Exception as e:
  print(f"Pexels search skipped: {e}",file=sys.stderr);return []
def score(c):
 w,h=c.get("width",0),c.get("height",0);d=c.get("duration",0)
 portrait=1 if h>=w and h>=720 else 0
 quality=min(h/1080,1) if h else 0
 duration_fit=1 if not d or 4<=d<=35 else max(0,1-abs(d-15)/60)
 return portrait*4+quality*2+duration_fit
def main():
 OUT.mkdir(parents=True,exist_ok=True);manifest=[]
 for scene in SCENES:
  candidates=pexels_candidates(scene["query"])+yt_candidates(scene["query"])
  candidates=[c for c in candidates if c.get("url")]
  candidates.sort(key=score,reverse=True)
  if not candidates:
   manifest.append({"scene":scene["id"],"query":scene["query"],"status":"no_candidate"})
   continue
  selected=candidates[0];dest=OUT/f"scene-{scene['id']:02d}.mp4"
  if selected["source"]=="pexels":
   import urllib.request
   try: urllib.request.urlretrieve(selected["url"],dest)
   except Exception as e: print(f"Pexels download failed for scene {scene['id']}: {e}",file=sys.stderr);selected=None
  else:
   p=run(["yt-dlp","--no-warnings","--no-playlist","-f","bv*[height>=720]+ba/b[height>=720]/best","--merge-output-format","mp4","--download-sections","*0-18","--force-keyframes-at-cuts","-o",str(dest),selected["url"]])
   if p.returncode: print(p.stderr[-1200:],file=sys.stderr);selected=None
  manifest.append({"scene":scene["id"],"query":scene["query"],"status":"downloaded" if selected and dest.exists() else "download_failed","file":str(dest.relative_to(ROOT)) if dest.exists() else None,"selected":selected,"alternates":candidates[1:5]})
 (OUT/"sources.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
 print(json.dumps({"scenes":len(SCENES),"downloaded":sum(x["status"]=="downloaded" for x in manifest),"manifest":"production/footage/sources.json"},indent=2))
if __name__=="__main__": main()
