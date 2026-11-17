#!/usr/bin/env python3
"""Render the final velocity edit from storyboard/shotlist.json.

usage: render_edit.py <clips_dir> <fonts_dir> <out.mp4> [--preview]
clips_dir: c1.mp4 ... + song.mp4
"""
import json, os, subprocess, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SL = json.load(open(os.path.join(ROOT, "storyboard", "shotlist.json")))
CLIPS, FONTS, OUTF = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = "--preview" in sys.argv
W, H = (540, 960) if PREVIEW else (1080, 1920)
FPS = SL["fps"]; OFF = SL["song_in"]
TOTAL = int(round((SL["song_out"] - OFF) * FPS))
MARGIN = 1.12                       # base frames are rendered 12% larger for zoom/shake headroom
BW, BH = int(W * MARGIN) // 2 * 2, int(H * MARGIN) // 2 * 2
rng = np.random.default_rng(7)
S = W / 1080.0                       # pixel-size scale factor for effects

GR = {
    "mono_red": "hue=s=0.12,eq=contrast=1.32:brightness=-0.03,colorbalance=rh=0.05:bh=-0.03",
    "cool": "eq=contrast=1.14:saturation=0.82,colorbalance=bs=0.12:bm=0.06:rs=-0.06",
    "red": "eq=contrast=1.22:saturation=1.45,colorbalance=rs=0.1:rm=0.06",
    "fire": "eq=contrast=1.24:saturation=1.5:gamma=0.97,colorbalance=rs=0.08:rm=0.05",
    "villain": "eq=contrast=1.3:saturation=1.7:gamma=1.35:brightness=0.03,colorbalance=rs=0.12:rm=0.05",
    "none": "null",
}

# ---------------------------------------------------------------- source frames
def fetch(shot, n):
    """Return list of n base frames (BH,BW,3 uint8) for a shot, applying speed / velocity ramp."""
    if shot["clip"] == "black":
        return [np.zeros((BH, BW, 3), np.uint8)] * n
    dur = n / FPS
    ramp = shot["act"] in ("RAGE", "DROP") and shot["speed"] >= 1.0 and n >= 10
    span = dur * shot["speed"] * (1.35 if ramp else 1.0)
    src = os.path.join(CLIPS, shot["clip"] + ".mp4")
    clip_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                              "-of", "csv=p=0", src]))
    span = min(span, clip_len - shot["in"] - 0.05)
    cw = 1080 * 9 / 16
    x = max(0, min(1920 - cw, shot["x"] * 1920 - cw / 2))
    vf = (f"fps=60,crop={cw:.0f}:1080:{x:.0f}:0,scale={BW}:{BH}:flags=lanczos,"
          f"unsharp=5:5:0.9:5:5:0.0,{GR[shot['grade']]}")
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{shot['in']:.3f}", "-t", f"{span + 0.05:.3f}",
                          "-i", src, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, BH, BW, 3)
    m = len(fr)
    out = []
    for i in range(n):
        u = i / max(1, n - 1)
        r = (1 - (1 - u) ** 2.2) if ramp else u          # velocity: fast in, eases to slow
        t = r * span
        out.append(fr[min(m - 1, int(t * 60))])
    return out

# ---------------------------------------------------------------- effects
def view(base, zoom, dx=0.0, dy=0.0):
    """Crop base frame at given zoom (1.0 = output frame size) and offset, resize to output."""
    cw, ch = W / zoom, H / zoom
    cx = BW / 2 + dx; cy = BH / 2 + dy
    x0 = np.clip(cx - cw / 2, 0, BW - cw); y0 = np.clip(cy - ch / 2, 0, BH - ch)
    M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
    return cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def radial_blur(img, amt, k=8):
    if amt <= 0: return img
    acc = img.astype(np.float32)
    for j in range(1, k):
        z = 1 + amt * j / k
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return (acc / k).astype(np.uint8)

def motion_blur(img, length, angle=0.0):
    length = int(length * S)
    if length < 3: return img
    small = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    L = max(3, length // 2)
    k = np.zeros((L, L), np.float32); k[L // 2, :] = 1
    k = cv2.warpAffine(k, cv2.getRotationMatrix2D((L / 2 - .5, L / 2 - .5), angle, 1), (L, L))
    k /= k.sum()
    small = cv2.filter2D(small, -1, k, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)

def gblur(img, sigma):
    sigma *= S
    if sigma <= 0.3: return img
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 4)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)

CELL = max(6, int(14 * S))
_yy, _xx = np.mgrid[0:H, 0:W]
_dist = np.sqrt(((_xx % CELL) - CELL / 2 + .5) ** 2 + ((_yy % CELL) - CELL / 2 + .5) ** 2).astype(np.float32)
def halftone(img, mix=0.75):
    sw, sh = W // CELL + 1, H // CELL + 1
    small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA)
    col = cv2.resize(small, (sw * CELL, sh * CELL), interpolation=cv2.INTER_NEAREST)[:H, :W]
    lum = col.astype(np.float32).mean(2) / 255.0
    rad = CELL * 0.72 * np.sqrt(lum) + 0.5
    mask = np.clip(rad - _dist, 0, 1)[..., None]
    ht = (col.astype(np.float32) * 1.15 * mask + 12 * (1 - mask))
    return np.clip(img.astype(np.float32) * (1 - mix) + ht * mix, 0, 255).astype(np.uint8)

def rgb_split(img, px, vertical=False):
    px = int(px * S)
    if px == 0: return img
    out = img.copy()
    ax = 0 if vertical else 1
    out[..., 0] = np.roll(img[..., 0], -px, axis=ax)
    out[..., 2] = np.roll(img[..., 2], px, axis=ax)
    return out

def block_glitch(img, n=7):
    out = img.copy()
    for _ in range(n):
        h = int(rng.integers(int(20 * S), int(120 * S))); y = int(rng.integers(0, H - h))
        sh = int(rng.integers(-int(120 * S), int(120 * S)))
        out[y:y + h] = np.roll(img[y:y + h], sh, axis=1)
        if rng.random() < .35: out[y:y + h, :, rng.integers(0, 3)] = 255
    return out

def glow(img, thresh=170, strength=0.55, sigma=28):
    f = img.astype(np.float32)
    lum = f.mean(2, keepdims=True)
    bright = f * np.clip((lum - thresh) / (255 - thresh), 0, 1)
    b = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(b, (0, 0), sigma * S / 4)
    b = cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(255 - (255 - f) * (255 - b * strength) / 255, 0, 255).astype(np.uint8)  # screen

def flash(img, a, color=(255, 255, 255)):
    if a <= 0: return img
    c = np.array(color, np.float32)
    return np.clip(img.astype(np.float32) * (1 - a) + c * a, 0, 255).astype(np.uint8)

_vy, _vx = np.mgrid[0:H, 0:W].astype(np.float32)
_vr = np.sqrt(((_vx - W / 2) / (W / 2)) ** 2 + ((_vy - H / 2) / (H / 2)) ** 2)
def vignette(img, k):
    m = np.clip(1 - k * np.clip(_vr - 0.55, 0, None) ** 1.6, 0, 1)[..., None]
    return (img.astype(np.float32) * m).astype(np.uint8)

def grain(img, amt=7):
    n = rng.normal(0, amt, (H // 2, W // 2, 1)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(img.astype(np.float32) + n, 0, 255).astype(np.uint8)

class Embers:
    def __init__(s, n=70):
        s.n = n; s.p = np.zeros((n, 6), np.float32); [s.spawn(i, True) for i in range(n)]
    def spawn(s, i, anywhere=False):
        s.p[i] = [rng.uniform(0, W), rng.uniform(0, H) if anywhere else H + 20 * S,
                  rng.uniform(-1.5, 1.5) * S, -rng.uniform(4, 14) * S, rng.uniform(1.2, 4.5) * S, rng.uniform(0.4, 1)]
    def step(s, img, intensity=1.0):
        layer = np.zeros((H // 2, W // 2, 3), np.float32)
        for i in range(s.n):
            x, y, vx, vy, r, a = s.p[i]
            s.p[i, 0] += vx + math.sin(y * 0.01) * 1.2 * S; s.p[i, 1] += vy
            if s.p[i, 1] < -20: s.spawn(i)
            col = (float(255 * a), float((150 + 80 * rng.random()) * a), float(40 * a))
            cv2.circle(layer, (int(x / 2), int(y / 2)), max(1, int(r / 2)), col, -1, cv2.LINE_AA)
        halo = cv2.GaussianBlur(layer, (0, 0), 6 * S)
        layer = layer + halo * 2.2
        layer = cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR) * intensity
        return np.clip(img.astype(np.float32) + layer, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- text
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(size * S))
_text_cache = {}
def text_layer(lines, fname, size, fill, stroke, glow_col=None, spacing=1.12):
    key = (tuple(lines), fname, size, fill, stroke, glow_col)
    if key in _text_cache: return _text_cache[key]
    f = font(fname, size)
    pad = int(60 * S)
    sizes = [f.getbbox(t[0] if isinstance(t, tuple) else t) for t in lines]
    lw = max(b[2] - b[0] for b in sizes) + pad * 2
    lh = int(sum((b[3] - b[1]) * spacing for b in sizes)) + pad * 2
    im = Image.new("RGBA", (lw, lh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = pad
    for t, b in zip(lines, sizes):
        txt, col = (t if isinstance(t, tuple) else (t, fill))
        tw = b[2] - b[0]
        d.text(((lw - tw) / 2 - b[0], y - b[1]), txt, font=f, fill=col, stroke_width=int(stroke * S), stroke_fill=(0, 0, 0))
        y += int((b[3] - b[1]) * spacing)
    if glow_col:
        g = Image.new("RGBA", im.size, glow_col + (0,)); g.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(18 * S)))
        im = Image.alpha_composite(g, Image.alpha_composite(g, im))
    _text_cache[key] = im
    return im

def put_text(img, layer, cy, scale=1.0, alpha=1.0, dx=0, dy=0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    a = np.asarray(layer).astype(np.float32)
    h, w = a.shape[:2]
    x0 = int(W / 2 - w / 2 + dx); y0 = int(cy - h / 2 + dy)
    sx0, sy0 = max(0, -x0), max(0, -y0); x0c, y0c = max(0, x0), max(0, y0)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    if x1 <= x0c or y1 <= y0c: return img
    sub = a[sy0:sy0 + (y1 - y0c), sx0:sx0 + (x1 - x0c)]
    al = sub[..., 3:4] / 255.0 * alpha
    out = img.astype(np.float32)
    out[y0c:y1, x0c:x1] = out[y0c:y1, x0c:x1] * (1 - al) + sub[..., :3] * al
    return out.astype(np.uint8)

def pop(fi, start, dur_in=4):
    """pop-in scale curve: overshoot 1.35 -> 1.0"""
    k = fi - start
    if k < 0: return None
    if k >= dur_in: return 1.0
    u = k / dur_in
    return 1.0 + 0.35 * (1 - u) ** 2

# Captions: (start_frame, end_frame, kind, payload)
def T(t): return int(round(t * FPS))
CAPTIONS = []
hook_words = [("they", 0.13), ("called", 0.33), ("him", 0.52), ("the", 0.95), ("soft", 1.12), ("one...", 1.35)]

# ---------------------------------------------------------------- timeline
shots = SL["shots"]
for sh in shots:
    sh["fs"] = T(sh["s"] - OFF); sh["fe"] = T(sh["e"] - OFF)
shots[-1]["fe"] = TOTAL
HIHAT = [T(t - OFF) for t in (6.0, 8.25, 10.75, 13.0)]   # bounce + flash accents
embers = Embers()

enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-ss", str(OFF), "-t", f"{TOTAL / FPS:.3f}", "-i", os.path.join(CLIPS, "song.mp4"),
                        "-map", "0:v", "-map", "1:a",
                        "-af", f"afade=t=out:st={TOTAL / FPS - 0.35:.3f}:d=0.35",
                        "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "slow", "-crf", "23" if PREVIEW else "16",
                        "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", OUTF], stdin=subprocess.PIPE)

def trans_kind(i):
    return shots[i]["trans"].lower() if i < len(shots) else ""

for si, sh in enumerate(shots):
    n = sh["fe"] - sh["fs"]
    frames = fetch(sh, n)
    hot = sh["act"] in ("DROP", "RAGE") or sh["title"] == "The Mark (Ignited)"
    tin = sh["trans"].lower(); tout = trans_kind(si + 1)
    print(f"shot {si + 1:02d} {sh['title']:<22} frames {sh['fs']}-{sh['fe']}", flush=True)
    for k in range(n):
        fi = sh["fs"] + k
        u = k / max(1, n - 1)
        rem = n - 1 - k                                   # frames until cut
        # --- camera: push-in, punch, shake
        if sh["title"] == "Into the Pupil":
            zoom = 1.0 + 0.55 * u ** 1.6
        elif sh["clip"] == "black":
            zoom = 1.0
        else:
            zoom = (1.02 + 0.07 * u) if not hot else (1.03 + 0.08 * u)
        dx = dy = 0.0
        if hot and "hard" not in tin:
            zoom += 0.16 * math.exp(-k / 2.2)            # impact punch-in
            amp = (34 if sh["act"] == "DROP" else 20) * math.exp(-k / 3.5) * S
            dx, dy = rng.uniform(-amp, amp), rng.uniform(-amp, amp)
        for hh in HIHAT:                                  # bounce accent
            if 0 <= fi - hh < 5:
                zoom += 0.09 * (1 - (fi - hh) / 5)
                a2 = 14 * S; dx += rng.uniform(-a2, a2); dy += rng.uniform(-a2, a2)
        # --- out-transition applied to the tail of this shot (zoom-type ones need to scale)
        if "zoom-blur" in tout and rem < 2: zoom *= (1.07, 1.18)[1 - rem]
        img = view(frames[k], max(zoom, 1.0 / MARGIN), dx, dy)
        if sh["title"] == "Into the Pupil":
            img = radial_blur(img, 0.02 + 0.22 * u ** 2)
            if rem < 3: img = flash(img, (0.45, 0.8, 1.0)[2 - rem])
        # tail of outgoing shot
        if rem < 2:
            j = 1 - rem   # 0 then 1 (last frame)
            if "zoom-blur" in tout: img = radial_blur(img, (0.08, 0.2)[j])
            elif "glitch" in tout: img = block_glitch(rgb_split(img, (18, 40)[j]))
            elif "halftone" in tout: img = halftone(gblur(img, (6, 14)[j]), (0.5, 0.85)[j])
            elif "whip" in tout and j == 1: img = motion_blur(img, 180, 8)
        # head of incoming shot
        if k < 3:
            if "zoom-blur" in tin and k < 2: img = radial_blur(img, (0.16, 0.06)[k])
            elif "glitch" in tin and k < 2: img = block_glitch(rgb_split(img, (34, 14)[k]))
            elif "halftone" in tin: img = motion_blur(img, (130, 70, 25)[k], -12);  img = halftone(img, 0.6) if k == 0 else img
            elif "whip" in tin and k < 2: img = motion_blur(img, (140, 45)[k], 8)
        # --- look
        if hot:
            img = glow(img, 160, 0.6)
            img = embers.step(img, 0.9)
            if k < 2: img = rgb_split(img, (16, 7)[k])
        elif sh["clip"] != "black":
            img = glow(img, 200, 0.3)
        for hh in HIHAT:
            if fi == hh: img = rgb_split(flash(img, 0.35), 22)
            if fi == hh + 1: img = rgb_split(img, 10, True)
        if "flash" in tin and k < 3: img = flash(img, (1.0, 0.65, 0.3)[k])
        if sh["clip"] != "black":
            img = vignette(img, 0.9 if sh["act"] in ("BREATH", "CALM", "HOOK") else 0.6)
            img = grain(img, 6)
        # --- captions
        t = fi / FPS
        if 0.13 <= t < 3.17:                               # hook, word-by-word
            shown = [w for w, ts in hook_words if t >= ts]
            l1 = " ".join(w for w in shown[:3]); l2 = " ".join(w for w in shown[3:])
            lay = text_layer([l1 or " ", l2 or " "], "Montserrat-Black.ttf", 88, (255, 255, 255), 9)
            last_ts = max(ts for w, ts in hook_words if t >= ts)
            img = put_text(img, lay, H * 0.30, pop(fi, T(last_ts), 3) and 1 + (pop(fi, T(last_ts), 3) - 1) * 0.3)
        if 3.25 <= t < 4.5:
            lay = text_layer([("big ", (255, 255, 255))], "Montserrat-Black.ttf", 96, (255, 255, 255), 8)
            lay2 = text_layer([("mistake.", (255, 40, 40))], "Montserrat-Black.ttf", 96, (255, 40, 40), 8, (255, 0, 0))
            p = pop(fi, T(3.25)); jit = rng.uniform(-3, 3) * S
            img = put_text(img, lay, H * 0.30, p, 1, jit, 0)
            if t >= 3.5: img = put_text(img, lay2, H * 0.30 + 100 * S, pop(fi, T(3.5)), 1, -jit, 0)
        if 5.65 <= t < 6.55:
            lay = text_layer(["LET'S GO"], "Anton.ttf", 210, (255, 255, 255), 6, (255, 90, 0))
            img = put_text(img, lay, H * 0.62, pop(fi, T(5.65)), 1, rng.uniform(-6, 6) * S, rng.uniform(-6, 6) * S)
        for word, ts, te, y in [("TAKE", 7.15, 7.35, 0.58), ("IT", 7.35, 7.52, 0.58), ("REAL", 7.52, 7.72, 0.58)]:
            if ts <= t < te:
                lay = text_layer([word], "Anton.ttf", 240, (255, 255, 255), 6, (255, 60, 0))
                img = put_text(img, lay, H * y, pop(fi, T(ts), 3))
        if 7.72 <= t < 8.5:
            lay = text_layer(["SLOW"], "Anton.ttf", 300, (255, 230, 210), 7, (255, 30, 0))
            sc = pop(fi, T(7.72), 5) * (1 + 0.04 * (t - 7.72))
            img = put_text(img, lay, H * 0.58, sc, 1, rng.uniform(-4, 4) * S, 0)
        enc.stdin.write(img.tobytes())

enc.stdin.close(); enc.wait()
print("done", OUTF, TOTAL, "frames")
