#!/usr/bin/env python3
"""Romanize multilingual Whisper captions without translating their words.

Whisper detects the spoken language. uroman converts non-Latin writing systems
to Latin-script phonetic text; English/Latin text is preserved as-is.
"""
from __future__ import annotations
import argparse
import html
import re
from pathlib import Path

TIMING = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})")

def romanizer():
    try:
        import uroman as ur
    except ImportError as exc:
        raise SystemExit("Missing uroman. Install it with: python -m pip install uroman") from exc
    return ur.Uroman()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="Whisper SRT file")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--html", type=Path, help="Optional HyperFrames HTML to receive timed caption cues")
    args=p.parse_args()
    raw=args.input.read_text(encoding="utf-8-sig")
    blocks=re.split(r"\n\s*\n", raw.strip())
    ur=romanizer()
    output=[]; cues=[]
    for block in blocks:
        lines=block.splitlines()
        ti=next((i for i,line in enumerate(lines) if TIMING.match(line.strip())),None)
        if ti is None:
            continue
        match=TIMING.match(lines[ti].strip())
        start,end=match.groups()
        spoken=" ".join(x.strip() for x in lines[ti+1:] if x.strip())
        # uroman transliterates scripts; it does not translate meaning.
        roman=ur.romanize_string(spoken).strip()
        roman=re.sub(r"\s+"," ",roman)
        # Preserve Latin words/casing and normalize punctuation spacing.
        output.extend([lines[0], lines[ti], roman, ""])
        def seconds(stamp):
            h,m,tail=stamp.split(":"); sec,ms=tail.split(",")
            return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
        cues.append((seconds(start),seconds(end),roman))
    if not cues:
        raise SystemExit(f"No valid timed captions found in {args.input}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(output).rstrip()+"\n",encoding="utf-8")
    if args.html:
        doc=args.html.read_text(encoding="utf-8")
        if "id=\"fixreach-spoken-captions\"" not in doc:
            style="""
.caption-cue{position:absolute;z-index:20;left:54px;right:54px;bottom:145px;opacity:0;text-align:center;padding:18px 24px;border-radius:18px;background:#000d;color:#fff;font-size:34px;line-height:1.15;font-weight:900;text-shadow:0 2px 8px #000;pointer-events:none}
"""
            doc=doc.replace("</style>",style+"</style>",1)
            nodes=[]
            for i,(start,end,text) in enumerate(cues,1):
                nodes.append(f'<div class="caption-cue" id="fixreach-caption-{i}" data-caption-start="{start:.3f}" data-caption-end="{end:.3f}">{html.escape(text)}</div>')
            anchor='</div>\n<audio id="voice"'
            if anchor not in doc:
                raise SystemExit("Could not find FixReach composition insertion point for timed captions")
            doc=doc.replace(anchor,"\n".join(nodes)+"\n</div>\n<audio id=\"voice\"",1)
            hook="window.__timelines=window.__timelines||{};"
            js="""
document.querySelectorAll('.caption-cue').forEach(cue=>{const a=Number(cue.dataset.captionStart),b=Number(cue.dataset.captionEnd);tl.set(cue,{opacity:1},a);tl.set(cue,{opacity:0},b);});
"""
            doc=doc.replace(hook,js+hook,1)
        args.html.write_text(doc,encoding="utf-8")
    print(f"Romanized {len(cues)} timed caption cues to Latin script (no translation).")

if __name__=="__main__": main()
