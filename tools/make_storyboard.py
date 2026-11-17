#!/usr/bin/env python3
"""Render a storyboard sheet from storyboard/shotlist.json.

usage: make_storyboard.py <clips_dir> <out_dir>
clips_dir holds c1.mp4 ... and song.wav
"""
import json, subprocess, sys, os, textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SL = json.load(open(os.path.join(ROOT, "storyboard", "shotlist.json")))
CLIPS, OUT = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)

GRADES = {
    "mono_red": "hue=s=0.12,eq=contrast=1.3:brightness=-0.03,colorbalance=rh=0.05:bh=-0.03",
    "cool": "eq=contrast=1.12:saturation=0.8,colorbalance=bs=0.12:bm=0.06:rs=-0.06",
    "red": "eq=contrast=1.2:saturation=1.4,colorbalance=rs=0.1:rm=0.06",
    "fire": "eq=contrast=1.22:saturation=1.45,colorbalance=rs=0.08:rm=0.05,unsharp=5:5:1.0",
    "none": "null",
}
ACT_COL = {"HOOK": (255, 214, 0), "CALM": (90, 170, 255), "BREATH": (150, 120, 255),
           "DROP": (255, 60, 40), "RAGE": (255, 120, 0), "END": (200, 200, 200)}
PW, PH = 270, 480

def frame(shot, i, t_off=0.5):
    path = os.path.join(OUT, "frames", f"{i:02d}.png")
    if shot["clip"] == "black":
        Image.new("RGB", (PW, PH), (0, 0, 0)).save(path); return path
    dur = (shot["e"] - shot["s"]) * shot["speed"]
    t = shot["in"] + dur * t_off
    # 9:16 crop from 1920x1080: 607.5 wide
    cw = 1080 * 9 / 16
    x = max(0, min(1920 - cw, shot["x"] * 1920 - cw / 2))
    vf = f"crop={cw:.0f}:1080:{x:.0f}:0,scale={PW}:{PH},{GRADES[shot['grade']]}"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}",
                    "-i", os.path.join(CLIPS, shot["clip"] + ".mp4"), "-frames:v", "1", "-vf", vf, path], check=True)
    return path

F = lambda s, b=False: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if b else ''}.ttf", s)
shots = SL["shots"]; off = SL["song_in"]; total = SL["song_out"] - off
COLS = 5; TXT = 250; PAD = 16
rows = (len(shots) + COLS - 1) // COLS
W = COLS * (PW + PAD) + PAD
HEAD = 330
H = HEAD + rows * (PH + TXT + PAD) + PAD
img = Image.new("RGB", (W, H), (16, 16, 20)); d = ImageDraw.Draw(img)
d.text((PAD, 14), SL["title"], font=F(34, True), fill="white")
d.text((PAD, 58), f"{len(shots)} shots · {total:.2f}s · 1080x1920 @ {SL['fps']}fps · song {off}s to {SL['song_out']}s · cuts on the beat (~103 BPM)",
       font=F(17), fill=(180, 180, 190))

# waveform + shot timeline
import wave
wf = wave.open(os.path.join(CLIPS, "song.wav")); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(float)
a = a[int(off * sr):int(SL["song_out"] * sr)]
TX, TY, TW, TH = PAD, 100, W - 2 * PAD, 150
n = TW; seg = len(a) // n
amp = np.array([np.abs(a[k * seg:(k + 1) * seg]).max() for k in range(n)]); amp /= amp.max()
for sh in shots:
    x0 = TX + (sh["s"] - off) / total * TW; x1 = TX + (sh["e"] - off) / total * TW
    d.rectangle([x0, TY, x1, TY + TH], fill=tuple(int(c * 0.28) for c in ACT_COL[sh["act"]]))
for k in range(n):
    h = amp[k] * TH / 2
    d.line([TX + k, TY + TH / 2 - h, TX + k, TY + TH / 2 + h], fill=(220, 220, 230))
for i, sh in enumerate(shots, 1):
    x0 = TX + (sh["s"] - off) / total * TW
    d.line([x0, TY, x0, TY + TH + 18], fill=ACT_COL[sh["act"]], width=2)
    d.text((x0 + 2, TY + TH + 2), str(i), font=F(13, True), fill=ACT_COL[sh["act"]])
for t in range(0, int(total) + 1):
    x = TX + t / total * TW; d.text((x, TY - 16), f"{t}s", font=F(11), fill=(130, 130, 140))
# lyric markers (song time)
for lt, lyr in [(5.0, "\"F*ck it\""), (6.1, "\"Let's go\""), (7.6, "\"Take it real slow\"")]:
    x = TX + (lt - off) / total * TW
    d.text((x + 3, TY + 3), lyr, font=F(13, True), fill=(255, 255, 255))
lx = PAD
for act, c in ACT_COL.items():
    d.rectangle([lx, 290, lx + 16, 306], fill=c); d.text((lx + 22, 289), act, font=F(15, True), fill=c); lx += 130

for i, sh in enumerate(shots, 1):
    r, c = divmod(i - 1, COLS)
    x = PAD + c * (PW + PAD); y = HEAD + r * (PH + TXT + PAD)
    img.paste(Image.open(frame(sh, i)), (x, y))
    col = ACT_COL[sh["act"]]
    d.rectangle([x, y, x + PW - 1, y + PH - 1], outline=col, width=3)
    d.rectangle([x, y, x + 46, y + 34], fill=col); d.text((x + 6, y + 4), f"{i:02d}", font=F(22, True), fill="black")
    d.rectangle([x + 50, y + 4, x + 50 + 9 * len(sh["act"]) + 12, y + 26], fill=(0, 0, 0))
    d.text((x + 56, y + 6), sh["act"], font=F(14, True), fill=col)
    ty = y + PH + 6
    d.text((x, ty), sh["title"], font=F(17, True), fill="white")
    so, eo = sh["s"] - off, sh["e"] - off
    sp = f" · {sh['speed']}x" if sh["speed"] != 1 else ""
    d.text((x, ty + 24), f"{so:5.2f}–{eo:5.2f}s ({eo - so:.2f}s){sp}", font=F(13), fill=(255, 220, 120))
    src = "-" if sh["clip"] == "black" else f"{SL['clips'][sh['clip']].replace('Demon_Slayer_-_', '')} @ {sh['in']}s"
    d.text((x, ty + 42), src, font=F(12), fill=(150, 150, 160))
    yy = ty + 62
    for line in textwrap.wrap(sh["desc"], 34)[:3]:
        d.text((x, yy), line, font=F(12), fill=(225, 225, 230)); yy += 16
    yy += 4
    for line in textwrap.wrap("FX: " + sh["fx"], 34)[:3]:
        d.text((x, yy), line, font=F(12), fill=(140, 200, 255)); yy += 16
    d.text((x, y + PH + TXT - 26), "IN: " + sh["trans"], font=F(12, True), fill=col)

img.save(os.path.join(OUT, "storyboard.png")); print("saved", os.path.join(OUT, "storyboard.png"), img.size)
