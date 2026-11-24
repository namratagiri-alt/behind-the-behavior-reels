"""Faceless psychology Reel engine.

Input: a reel spec JSON (see reels/*.json). Output: MP4 (1080x1920, H.264/AAC),
cover JPEG, SRT subtitles, transcript, QC report.

Everything is generated locally: narration (Kokoro TTS, Apache-2.0 model),
graphics (PIL), music bed (synthesized), so all assets are original and licensed.
"""
import json, math, os, subprocess, sys, re, wave, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SR = 24000
MODELS = os.environ.get("KOKORO_DIR", "/home/claude/models")

# ---------- brand system ----------
PAL = {
    "bg1": (14, 16, 22), "bg2": (27, 30, 42),
    "ink": (244, 239, 230), "muted": (150, 156, 172), "dim": (70, 76, 92),
    "accent": (245, 184, 65), "coral": (255, 112, 92), "teal": (88, 200, 186),
    "card": (34, 38, 52),
}
F = {
    "serif": "/usr/share/fonts/truetype/google-fonts/ofl/crimsontext/CrimsonText-SemiBold.ttf",
    "serif_i": "/usr/share/fonts/truetype/google-fonts/ofl/crimsontext/CrimsonText-SemiBoldItalic.ttf",
    "sans": "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
    "sans_b": "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "sans_k": "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "sans_s": "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf",
}
_fc = {}
def font(k, size):
    key = (k, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(F[k], size)
    return _fc[key]

# safe zone: IG UI covers roughly top ~220px and bottom ~420px
SAFE_TOP, SAFE_BOTTOM = 230, H - 430
CAPTION_Y = 1365
SCENE_DY = 120
SIGNOFF = "Understand the pattern. Change the response."

def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x):
    x = max(0.0, min(1.0, x)); return 3 * x * x - 2 * x * x * x
def prog(t, start, dur=0.45):
    return ease((t - start) / dur) if dur > 0 else float(t >= start)
def rgba(c, a):
    return (c[0], c[1], c[2], int(255 * max(0, min(1, a))))

def text_w(fnt, s):
    b = fnt.getbbox(s); return b[2] - b[0]

def wrap(fnt, text, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_w(fnt, trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def draw_rich_line(d, x, y, line, fnt, accents, a, base=None, acc=None):
    """Draw a line where words in `accents` are colored accent."""
    base = base or PAL["ink"]; acc = acc or PAL["accent"]
    cx = x
    for i, w_ in enumerate(line.split(" ")):
        clean = re.sub(r"[^\w%$']", "", w_).lower()
        col = acc if clean in accents else base
        d.text((cx, y), w_, font=fnt, fill=rgba(col, a))
        cx += text_w(fnt, w_ + " ")

def centered_rich(d, cy, text, fnt, accents, a, maxw=900, lh=1.12, dy=0):
    lines = wrap(fnt, text, maxw)
    lhpx = int(fnt.size * lh)
    y0 = cy - lhpx * len(lines) // 2 + dy
    for i, ln in enumerate(lines):
        x = (W - text_w(fnt, ln)) // 2
        draw_rich_line(d, x, y0 + i * lhpx, ln, fnt, accents, a)
    return y0 + lhpx * len(lines)

# ---------- background ----------
def make_bg(seed=0):
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    g = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        g[..., i] = PAL["bg1"][i] * (1 - y) + PAL["bg2"][i] * y
    r = np.sqrt(x ** 2 + ((y - 0.42) * 1.6) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 2 * 14
    g += glow[..., None] * np.array([1.0, 0.85, 0.6])
    rng = np.random.default_rng(seed)
    g += rng.normal(0, 2.2, (H, W, 1))
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")

def make_glow(r=520):
    y, x = np.mgrid[-r:r, -r:r]
    a = np.clip(1 - np.sqrt(x**2 + y**2) / r, 0, 1) ** 2.2 * 38
    arr = np.zeros((2*r, 2*r, 4), np.uint8); arr[..., 0] = 245; arr[..., 1] = 184; arr[..., 2] = 65; arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


# ---------- animated background FX ----------
def make_glow_c(r, col, peak):
    y, x = np.mgrid[-r:r, -r:r]
    a = np.clip(1 - np.sqrt(x**2 + y**2) / r, 0, 1) ** 2.2 * peak
    arr = np.zeros((2*r, 2*r, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = col
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

class BackgroundFX:
    """Layered ambient motion: color glows, a drifting 'neural' particle network,
    rotating orbit rings, and a pulse + light sweep at each scene change.
    Everything is kept dim so on-screen text and subtitles stay readable."""
    def __init__(self, seed, scene_starts, voice_env):
        rng = np.random.default_rng(seed)
        self.glows = [
            (make_glow_c(520, PAL["accent"], 40), 260, 180, 0.35, 0.27, 900, 0.0),
            (make_glow_c(430, PAL["teal"], 26), 330, 260, 0.22, 0.31, 700, 2.1),
            (make_glow_c(380, PAL["coral"], 20), 300, 300, 0.27, 0.19, 1150, 4.2),
        ]
        n = 58
        self.px = rng.uniform(0, W, n); self.py = rng.uniform(150, H - 150, n)
        self.depth = rng.uniform(0.35, 1.0, n)
        ang = rng.uniform(0, 2 * np.pi, n)
        sp = rng.uniform(8, 22, n) * self.depth
        self.vx = np.cos(ang) * sp; self.vy = np.sin(ang) * sp - 6 * self.depth
        self.phase = rng.uniform(0, 2 * np.pi, n)
        self.cols = [PAL["accent"] if rng.random() < 0.3 else (PAL["teal"] if rng.random() < 0.3 else PAL["ink"]) for _ in range(n)]
        self.starts = scene_starts[1:]
        self.env = voice_env

    def energy(self, t):
        i = int(t * FPS)
        return float(self.env[min(i, len(self.env) - 1)]) if len(self.env) else 0.0

    def draw(self, frame, t):
        e = self.energy(t)
        for g, ax, ay, fx_, fy_, cy, ph in self.glows:
            gx = int(W / 2 + ax * math.sin(t * fx_ + ph)); gy = int(cy + ay * math.cos(t * fy_ + ph))
            frame.alpha_composite(g, (gx - g.width // 2, gy - g.height // 2))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        # orbit rings behind the main visual, rotating in opposite directions
        cx, cy = W // 2, 880
        for r, speed, a0 in ((430, 9, 46), (540, -6, 34)):
            rot = t * speed
            for k in range(0, 360, 30):
                d.arc([cx - r, cy - r, cx + r, cy + r], rot + k, rot + k + 16, fill=rgba(PAL["muted"], a0 / 255), width=2)
            th = math.radians(t * speed * 2.2 + (0 if speed > 0 else 180))
            ox, oy = cx + r * math.cos(th), cy + r * math.sin(th)
            d.ellipse([ox - 7, oy - 7, ox + 7, oy + 7], fill=rgba(PAL["accent"], 0.55))
            d.ellipse([ox - 16, oy - 16, ox + 16, oy + 16], outline=rgba(PAL["accent"], 0.18), width=2)
        # particle network (positions wrap around the frame)
        x = (self.px + self.vx * t) % W
        y = (self.py + self.vy * t - 150) % (H - 300) + 150
        link = 175; boost = 0.75 + 0.6 * e
        for i in range(len(x)):
            for j in range(i + 1, len(x)):
                dx, dy = x[i] - x[j], y[i] - y[j]
                if abs(dx) < link and abs(dy) < link:
                    dist = math.hypot(dx, dy)
                    if dist < link:
                        a = (1 - dist / link) * 0.22 * min(self.depth[i], self.depth[j]) * boost
                        d.line([x[i], y[i], x[j], y[j]], fill=rgba(PAL["muted"], a), width=1)
        for i in range(len(x)):
            tw = 0.55 + 0.45 * math.sin(t * 1.7 + self.phase[i])
            rr = 1.5 + 3.2 * self.depth[i]
            a = 0.25 + 0.4 * self.depth[i] * tw * boost
            d.ellipse([x[i] - rr, y[i] - rr, x[i] + rr, y[i] + rr], fill=rgba(self.cols[i], min(a, 0.85)))
        # scene-change pulse ring + diagonal light sweep
        for s0 in self.starts:
            lt = t - s0
            if 0 <= lt < 0.9:
                q = ease(lt / 0.9)
                r = 80 + 900 * q
                d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgba(PAL["accent"], 0.32 * (1 - q)), width=int(3 + 5 * (1 - q)))
            if 0 <= lt < 0.55:
                q = ease_io(lt / 0.55)
                bx = -300 + (W + 600) * q
                for k, aa in ((0, 0.10), (40, 0.07), (80, 0.04)):
                    d.polygon([(bx + k, 0), (bx + k + 90, 0), (bx + k - 210, H), (bx + k - 300, H)], fill=rgba(PAL["ink"], aa))
        frame.alpha_composite(lay)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
def load_watermark(width, opacity):
    path = os.path.join(ASSETS, "purpllewave_logo.png")
    if not os.path.exists(path):
        print("WARNING: watermark missing at", path, file=sys.stderr); return None
    im = Image.open(path).convert("RGBA")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    a = im.getchannel("A").point(lambda v: int(v * opacity)); im.putalpha(a)
    return im

# ---------- scene renderers: f(d, t, D, data) ----------
def sc_headline(d, t, D, data):
    acc = set(w.lower() for w in data.get("accent", []))
    fnt = font("serif", data.get("size", 104))
    lines = data["lines"]
    lh = int(fnt.size * 1.08)
    total = lh * sum(len(wrap(fnt, l, 920)) for l in lines)
    y = 760 - total // 2
    for i, l in enumerate(lines):
        p = prog(t, (0.0 + i * 0.12) if data.get("_fast") else (0.12 + i * 0.35), 0.3 if data.get("_fast") else 0.55)
        for wl in wrap(fnt, l, 920):
            x = (W - text_w(fnt, wl)) // 2
            draw_rich_line(d, x, y + int((1 - p) * 40), wl, fnt, acc, p)
            y += lh
    if data.get("kicker"):
        p = prog(t, 0.6, 0.5)
        f2 = font("sans_s", 34)
        s = data["kicker"].upper()
        d.text(((W - text_w(f2, s)) // 2, y + 50), s, font=f2, fill=rgba(PAL["muted"], p))

def sc_compare(d, t, D, data):
    # price tag card with old price struck through and new price
    p = prog(t, 0.05, 0.5)
    cx, cy = W // 2, 720
    w_, h_ = 640, 640
    x0, y0 = cx - w_ // 2, cy - h_ // 2 + int((1 - p) * 60)
    d.rounded_rectangle([x0, y0, x0 + w_, y0 + h_], 48, fill=rgba(PAL["card"], p * 0.95),
                        outline=rgba(PAL["dim"], p), width=3)
    d.ellipse([cx - 22, y0 + 46, cx + 22, y0 + 90], outline=rgba(PAL["muted"], p), width=5)
    fl = font("sans_b", 40)
    lab = data.get("label", "").upper()
    d.text((cx - text_w(fl, lab) // 2, y0 + 130), lab, font=fl, fill=rgba(PAL["muted"], p))
    fo = font("sans_b", 150)
    old = data["old"]
    po = prog(t, 0.35, 0.4)
    ox = cx - text_w(fo, old) // 2; oy = y0 + 210
    d.text((ox, oy), old, font=fo, fill=rgba(PAL["ink"], po * (0.45 + 0.55 * (1 - prog(t, D * 0.42, 0.3)))))
    ps = prog(t, D * 0.38, 0.35)
    if ps > 0:
        ow = text_w(fo, old)
        d.line([ox - 10, oy + 105, ox - 10 + (ow + 20) * ps, oy + 95], fill=rgba(PAL["coral"], 1), width=12)
    pn = prog(t, D * 0.55, 0.4)
    fn = font("sans_k", 190)
    new = data["new"]
    s = 0.85 + 0.15 * pn
    d.text((cx - text_w(fn, new) // 2, y0 + 380 + int((1 - pn) * 30)), new, font=fn, fill=rgba(PAL["accent"], pn))
    if data.get("badge"):
        pb = prog(t, D * 0.65, 0.35)
        fb = font("sans_k", 46); bt = data["badge"]
        bw = text_w(fb, bt) + 60
        bx, by = x0 + w_ - bw + 30, y0 - 30
        d.rounded_rectangle([bx, by, bx + bw, by + 84], 42, fill=rgba(PAL["coral"], pb))
        d.text((bx + 30, by + 12), bt, font=fb, fill=rgba((20, 20, 24), pb))

def sc_axis(d, t, D, data):
    y = 760; x0, x1 = 120, 960
    p = prog(t, 0.05, 0.6)
    d.line([x0, y, x0 + (x1 - x0) * p, y], fill=rgba(PAL["muted"], 1), width=6)
    fl = font("sans_s", 44)
    def marker(frac, val, label, col, start, up=True):
        q = prog(t, start, 0.45)
        if q <= 0: return
        x = x0 + (x1 - x0) * frac
        d.line([x, y - 40, x, y + 40], fill=rgba(col, q), width=8)
        fv = font("sans_k", 104)
        vy = y - 175 if up else y + 70
        d.text((x - text_w(fv, val) // 2, vy + int((1 - q) * 20)), val, font=fv, fill=rgba(col, q))
        for i, ln in enumerate(wrap(fl, label, 440)):
            ly = (y - 240 - 44 * (len(wrap(fl, label, 440)) - 1 - i)) if up else (y + 175 + 44 * i)
            d.text((x - text_w(fl, ln) // 2, ly), ln, font=fl, fill=rgba(PAL["muted"], q))
    marker(data["ref_frac"], data["ref"], data["ref_label"], PAL["ink"], D * 0.12, up=True)
    marker(data["point_frac"], data["point"], data["point_label"], PAL["accent"], D * 0.45, up=False)
    pg = prog(t, D * 0.62, 0.5)
    if pg > 0 and data.get("gap_label"):
        xa = x0 + (x1 - x0) * data["point_frac"]; xb = x0 + (x1 - x0) * data["ref_frac"]
        yy = y + 290
        d.line([xa, yy, xa + (xb - xa) * pg, yy], fill=rgba(PAL["coral"], pg), width=6)
        fg = font("serif_i", 58); s = data["gap_label"]
        d.text(((xa + xb) / 2 - text_w(fg, s) / 2, yy + 20), s, font=fg, fill=rgba(PAL["coral"], pg))

def sc_bars(d, t, D, data):
    ft = font("serif", 76)
    pt = prog(t, 0.05, 0.5)
    if data.get("title"):
        centered_rich(d, 430, data["title"], ft, set(), pt)
        fi_ = font("sans_s", 28)
        tag = ("SOURCE: " + data["source"]).upper() if data.get("source") else "ILLUSTRATIVE, NOT MEASURED DATA"
        d.text(((W - text_w(fi_, tag)) // 2, 505), tag, font=fi_, fill=rgba(PAL["dim"], pt))
    fl = font("sans_s", 40)
    for i, b in enumerate(data["bars"]):
        y = 620 + i * 260
        q = prog(t, D * (0.15 + 0.3 * i), 0.9)
        d.text((120, y), b["label"], font=fl, fill=rgba(PAL["muted"], min(1, q * 3)))
        d.rounded_rectangle([120, y + 70, 960, y + 140], 35, fill=rgba(PAL["card"], 1))
        col = PAL["accent"] if b.get("hi") else PAL["teal"]
        wv = int(840 * b["value"] * q)
        if wv > 70:
            d.rounded_rectangle([120, y + 70, 120 + wv, y + 140], 35, fill=rgba(col, 1))
        if b.get("display") and q > 0.6:
            fv = font("sans_k", 48)
            d.text((960 - text_w(fv, b["display"]), y - 6), b["display"], font=fv, fill=rgba(col, min(1, (q - 0.6) * 2.5)))
    if data.get("footer"):
        pf = prog(t, D * 0.75, 0.5)
        centered_rich(d, 1180, data["footer"], font("serif_i", 56), set(), pf, maxw=860)

def sc_countdown(d, t, D, data):
    p = prog(t, 0.05, 0.45)
    fb = font("sans_k", 112); s = data["text"]
    d.text(((W - text_w(fb, s)) // 2, 470 + int((1 - p) * 40)), s, font=fb, fill=rgba(PAL["coral"], p))
    secs = max(0, data.get("start_secs", 14399) - int(t))
    hh, mm, ss = secs // 3600, (secs % 3600) // 60, secs % 60
    clock = f"{hh:02d}:{mm:02d}:{ss:02d}"
    fc = font("sans_b", 150)
    pulse = 0.75 + 0.25 * (0.5 + 0.5 * math.cos(t * 2 * math.pi))
    d.text(((W - text_w(fc, clock)) // 2, 640), clock, font=fc, fill=rgba(PAL["ink"], p * pulse))
    if data.get("sub"):
        q = prog(t, D * 0.45, 0.5)
        centered_rich(d, 1040, data["sub"], font("serif_i", 64), set(), q, maxw=860)

def sc_stack(d, t, D, data):
    items = data["items"]; n = len(items)
    fi = font("sans_b", 64)
    for i, it in enumerate(items):
        q = prog(t, D * (0.06 + 0.17 * i), 0.45)
        y = 430 + i * 190
        x = 140 + int((1 - q) * 120)
        d.rounded_rectangle([x, y, x + 800, y + 150], 30, fill=rgba(PAL["card"], q),
                            outline=rgba(PAL["accent"] if i == n - 1 else PAL["dim"], q), width=3)
        fnum = font("sans_k", 54)
        d.text((x + 40, y + 42), f"{data.get('start', 1) + i}", font=fnum, fill=rgba(PAL["accent"], q))
        d.text((x + 120, y + 40), it, font=fi, fill=rgba(PAL["ink"], q))
    if data.get("footer"):
        q = prog(t, D * (0.1 + 0.17 * n), 0.6)
        centered_rich(d, 430 + n * 190 + 110, data["footer"], font("serif", 64),
                      set(w.lower() for w in data.get("accent", [])), q, maxw=880)

def sc_chain(d, t, D, data):
    items = data["items"]; n = len(items)
    fi = font("sans_b", 56); gap = min(230, 820 // max(1, n))
    for i, it in enumerate(items):
        q = prog(t, D * (0.05 + 0.8 * i / n), 0.45)
        y = 360 + i * gap
        tw = text_w(fi, it) + 80; x = (W - tw) // 2
        d.rounded_rectangle([x, y, x + tw, y + 110], 55, fill=rgba(PAL["card"], q),
                            outline=rgba(PAL["accent"], q), width=3)
        d.text((x + 40, y + 22), it, font=fi, fill=rgba(PAL["ink"], q))
        if i < n - 1:
            qa = prog(t, D * (0.05 + 0.8 * (i + 0.6) / n), 0.3)
            ax = W // 2
            d.line([ax, y + 120, ax, y + 120 + (gap - 130) * qa], fill=rgba(PAL["muted"], qa), width=5)

def sc_split(d, t, D, data):
    fl = font("sans_b", 40); ft = font("serif", 54)
    for i, side in enumerate([data["left"], data["right"]]):
        q = prog(t, D * (0.05 + 0.35 * i), 0.5)
        x0 = 70 + i * 480
        nl = max(len(wrap(ft, data["left"]["text"], 380)), len(wrap(ft, data["right"]["text"], 380)))
        d.rounded_rectangle([x0, 380, x0 + 460, 380 + 200 + 66 * nl], 36, fill=rgba(PAL["card"], q))
        col = PAL["teal"] if i == 0 else PAL["coral"]
        d.text((x0 + 40, 420), side["label"].upper(), font=fl, fill=rgba(col, q))
        yy = 520
        for ln in wrap(ft, side["text"], 380):
            d.text((x0 + 40, yy), ln, font=ft, fill=rgba(PAL["ink"], q)); yy += 66

def sc_chat(d, t, D, data):
    fm = font("sans", 46); y = 400
    msgs = data["messages"]
    for i, m in enumerate(msgs):
        q = prog(t, D * (0.05 + 0.8 * i / len(msgs)), 0.35)
        lines = wrap(fm, m["text"], 600)
        bh = 40 + 58 * len(lines); bw = max(text_w(fm, l) for l in lines) + 70
        me = m.get("from") == "me"
        x = W - 100 - bw if me else 100
        d.rounded_rectangle([x, y, x + bw, y + bh], 40,
                            fill=rgba(PAL["accent"] if me else PAL["card"], q))
        for j, l in enumerate(lines):
            d.text((x + 35, y + 18 + 58 * j), l, font=fm, fill=rgba((20, 20, 24) if me else PAL["ink"], q))
        if m.get("meta"):
            fmeta = font("sans", 30)
            d.text((x if not me else x + bw - text_w(fmeta, m["meta"]), y + bh + 10), m["meta"], font=fmeta, fill=rgba(PAL["muted"], q))
        y += bh + 70

def sc_question(d, t, D, data):
    p = prog(t, 0.1, 0.6)
    acc = set(w.lower() for w in data.get("accent", []))
    end = centered_rich(d, 720, data["text"], font("serif", data.get("size", 86)), acc, p, maxw=900, dy=int((1 - p) * 30))
    if data.get("kicker"):
        q = prog(t, D * 0.55, 0.5)
        fk = font("sans_s", 36); s = data["kicker"].upper()
        d.text(((W - text_w(fk, s)) // 2, end + 70), s, font=fk, fill=rgba(PAL["accent"], q))
    if data.get("_last") and data.get("signoff", SIGNOFF):
        q = prog(t, D * 0.62, 0.6)
        fs = font("serif_i", 46); so = data.get("signoff", SIGNOFF)
        d.line([W // 2 - 60, 1060, W // 2 + 60, 1060], fill=rgba(PAL["dim"], q), width=2)
        d.text(((W - text_w(fs, so)) // 2, 1085), so, font=fs, fill=rgba(PAL["muted"], q))

SCENES = {"headline": sc_headline, "compare": sc_compare, "axis": sc_axis, "bars": sc_bars,
          "countdown": sc_countdown, "stack": sc_stack, "chain": sc_chain, "split": sc_split,
          "chat": sc_chat, "question": sc_question}

# ---------- audio ----------
_kokoro = None
def tts(text, voice, speed):
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(f"{MODELS}/kokoro-v1.0.onnx", f"{MODELS}/voices-v1.0.bin")
    s, sr = _kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    assert sr == SR
    return s.astype(np.float32)

def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a, 0.0
    s, e = max(0, idx[0] - int(0.03 * SR)), min(len(a), idx[-1] + int(0.06 * SR))
    return a[s:e], s / SR

def word_times(text, dur):
    words = text.split()
    wts = []
    for w_ in words:
        wt = len(re.sub(r"\W", "", w_)) + 1.5
        if w_.endswith((",", ";", ":")): wt += 3
        if w_.endswith((".", "?", "!")): wt += 4.5
        wts.append(wt)
    tot = sum(wts); out, c = [], 0.0
    for w_, wt in zip(words, wts):
        st = c / tot * dur; c += wt
        out.append((w_, st, c / tot * dur))
    return out

def synth_music(dur, seed=3):
    """Original ambient bed: slow minor-key pad, very soft."""
    n = int(dur * SR); t = np.arange(n) / SR
    roots = [57, 53, 60, 55]  # A3 F3 C4 G3
    chord = {57: [0, 3, 7], 53: [0, 4, 7], 60: [0, 4, 7], 55: [0, 4, 7]}
    out = np.zeros(n, np.float32); seg = 4.0
    for k in range(int(dur / seg) + 1):
        r = roots[k % 4]; s0 = int(k * seg * SR); s1 = min(n, int((k + 1) * seg * SR + 1.5 * SR))
        if s0 >= n: break
        tt = t[s0:s1] - k * seg
        env = np.minimum(1, tt / 1.2) * np.clip((seg + 1.5 - tt) / 1.5, 0, 1)
        for iv in chord[r]:
            f = 440 * 2 ** ((r + iv - 69) / 12)
            for det in (-0.6, 0.6):
                out[s0:s1] += (np.sin(2 * np.pi * (f + det) * tt) * 0.5 + np.sin(4 * np.pi * (f + det) * tt) * 0.08) * env
        fb = 440 * 2 ** ((r - 12 - 69) / 12)
        out[s0:s1] += np.sin(2 * np.pi * fb * tt) * env * 0.6
    # cheap reverb
    for dl, g in ((0.11, 0.35), (0.23, 0.25), (0.37, 0.18)):
        k = int(dl * SR); out[k:] += out[:-k] * g
    out /= (np.max(np.abs(out)) + 1e-9)
    return out * 0.9

def tick(n_s=0.12):
    n = int(n_s * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(1)
    s = rng.normal(0, 1, n) * np.exp(-t * 60) * 0.25 + np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 45) * 0.2
    return s.astype(np.float32)

def write_wav(path, a):
    a = np.clip(a, -1, 1); pcm = (a * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------- captions ----------
def caption_groups(words, maxchars=20, maxw=4):
    groups, cur = [], []
    for w_ in words:
        cur.append(w_)
        txt = " ".join(x[0] for x in cur)
        if len(cur) >= maxw or len(txt) >= maxchars or w_[0].endswith((".", "?", "!", ",")):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

def draw_caption(d, t, groups):
    for g in groups:
        if g[0][1] - 0.05 <= t < g[-1][2] + 0.12:
            fnt = font("sans_k", 66)
            words = [w_[0] for w_ in g]
            total = sum(text_w(fnt, w_ + " ") for w_ in words) - text_w(fnt, " ")
            x = (W - total) // 2
            # backing plate for readability
            d.rounded_rectangle([x - 34, CAPTION_Y - 22, x + total + 34, CAPTION_Y + 94], 28, fill=(10, 11, 15, 170))
            for (w_, st, en) in g:
                active = st <= t < en
                col = PAL["accent"] if active else PAL["ink"]
                d.text((x, CAPTION_Y), w_, font=fnt, fill=rgba(col, 1))
                x += text_w(fnt, w_ + " ")
            return

# ---------- main ----------
def build(spec_path, outdir):
    spec = json.load(open(spec_path))
    os.makedirs(outdir, exist_ok=True)
    rid = spec["id"]; voice = spec.get("voice", "af_heart"); speed = spec.get("speed", 1.0)
    gap = spec.get("gap", 0.22)
    LEAD = 0.15  # voice starts almost immediately so the hook lands inside 0-3 s
    tail = 0.9
    scenes, voice_track, t_cursor, all_words = [], [], LEAD, []
    voice_track.append(np.zeros(int(LEAD * SR), np.float32))
    nsc = len(spec["scenes"])
    for idx, sc in enumerate(spec["scenes"]):
        a, _ = trim(tts(sc["say"], voice, speed))
        dur = len(a) / SR
        wt = [(w_, t_cursor + s_, t_cursor + e) for (w_, s_, e) in word_times(sc["say"], dur)]
        all_words.extend(wt)
        hold = sc.get("hold", 0)
        if idx == nsc - 1:  # takeaway scene must last 5-8 s on screen
            hold = max(hold, 5.6 - (dur + gap + tail))
        D = dur + gap + hold
        scenes.append({"D": D, "voice_start": t_cursor, "voice_end": t_cursor + dur, **sc})
        voice_track.append(a); voice_track.append(np.zeros(int((gap + hold) * SR), np.float32))
        t_cursor += D
    voice_track.append(np.zeros(int(tail * SR), np.float32))
    vt = np.concatenate(voice_track)
    total = len(vt) / SR
    c = 0.0
    for i, s_ in enumerate(scenes):
        s_["start"] = c
        c = c + s_["D"] + (LEAD if i == 0 else 0.0)
        s_["end"] = c
    scenes[-1]["end"] = total
    # audio mix
    vt = vt / (np.max(np.abs(vt)) + 1e-9) * 0.89
    hop = SR // FPS
    nfr = len(vt) // hop
    venv = np.sqrt(np.mean(vt[: nfr * hop].reshape(nfr, hop) ** 2, axis=1))
    venv = np.convolve(venv, np.ones(5) / 5, mode="same"); venv = venv / (venv.max() + 1e-9)
    music = synth_music(total + 0.5)[: len(vt)]
    fade = np.minimum(1, np.arange(len(vt)) / (1.5 * SR)) * np.minimum(1, (len(vt) - np.arange(len(vt))) / (1.5 * SR))
    # duck music under voice
    env = np.convolve(np.abs(vt), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    duck = 1 - np.clip(env * 6, 0, 0.55)
    mix = vt + music * fade * duck * 0.085
    tk = tick()
    for s in scenes[1:]:
        i0 = int(s["start"] * SR)
        mix[i0:i0 + len(tk)] += tk[: len(mix) - i0] * 0.6
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.93
    wav = f"{outdir}/{rid}_mix.wav"; write_wav(wav, mix)

    groups = caption_groups(all_words)
    # SRT
    def ts(x):
        h, r = divmod(x, 3600); m, s_ = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s_):02d},{int((s_ % 1) * 1000):03d}"
    with open(f"{outdir}/{rid}.srt", "w") as f:
        for i, g in enumerate(groups, 1):
            f.write(f"{i}\n{ts(g[0][1])} --> {ts(g[-1][2])}\n{' '.join(w_[0] for w_ in g)}\n\n")
    with open(f"{outdir}/{rid}_transcript.txt", "w") as f:
        f.write(" ".join(sc["say"] for sc in spec["scenes"]) + "\n")

    bg = make_bg()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from illustrations import SCENES as ILL_SCENES
    ILL = {n: ILL_SCENES[n]() for n in {sc.get("illustration") for sc in scenes} if n}
    yy, xx = np.mgrid[0:H, 0:W]
    sa = np.clip(1 - np.sqrt(((xx - W / 2) / (W * 0.78)) ** 2 + ((yy - 950) / (H * 0.30)) ** 2), 0, 1) ** 0.8 * 215
    SCRIM = Image.fromarray(np.dstack([np.full((H, W), 12), np.full((H, W), 14), np.full((H, W), 20), sa]).astype(np.uint8), "RGBA")
    FX = BackgroundFX(sum(map(ord, rid)), [sc["start"] for sc in scenes], venv)
    series = spec.get("series", "").upper(); brand = spec.get("brand", "").upper()
    nframes = int(total * FPS)
    mp4 = f"{outdir}/{rid}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", "-shortest", mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fh = font("sans_b", 26); fbrand = font("sans_k", 30)
    # series label: sentence case, as large as fits (max 44 px), inside an amber pill
    series_txt = spec.get("series", "")
    series_txt = series_txt[:1].upper() + series_txt[1:]
    psize = 44
    while psize > 30 and text_w(font("sans_k", psize), series_txt) > W - 180 - 60:
        psize -= 2
    fpill = font("sans_k", psize)
    bb = fpill.getbbox(series_txt); pill_th = bb[3] - bb[1]; pill_off = bb[1]
    pill_w = text_w(fpill, series_txt) + 60; pill_h = pill_th + 34
    WM = load_watermark(120, 0.72) if spec.get("watermark", False) else None
    for fi in range(nframes):
        t = fi / FPS
        frame = bg.copy()
        FX.draw(frame, t)
        for si, s_ in enumerate(scenes):
            if s_["start"] <= t < s_["end"]:
                ill = s_.get("illustration")
                if ill:
                    ox = int(60 + 45 * math.sin(t * 0.13)); oy = int(60 + 45 * math.cos(t * 0.11))
                    crop = ILL[ill].crop((ox, oy, ox + W, oy + H))
                    lt_ = t - s_["start"]; D_ = s_["end"] - s_["start"]
                    same_prev = si > 0 and scenes[si - 1].get("illustration") == ill
                    same_next = si + 1 < len(scenes) and scenes[si + 1].get("illustration") == ill
                    q = (1 if same_prev else prog(lt_, 0, 0.5)) * (1 if (same_next or si == len(scenes) - 1) else 1 - prog(lt_, D_ - 0.3, 0.3))
                    if q < 0.999:
                        crop.putalpha(crop.getchannel("A").point(lambda v, q=q: int(v * q)))
                    frame.alpha_composite(crop)
                    frame.alpha_composite(SCRIM)
                break
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        # header: brand line + high-visibility series label (topic pill)
        d.text((90, SAFE_TOP), brand, font=fbrand, fill=rgba(PAL["muted"], 1))
        px0, py0 = 80, SAFE_TOP + 46
        d.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], pill_h // 2, fill=rgba(PAL["accent"], 1))
        d.text((px0 + 30, py0 + (pill_h - pill_th) // 2 - pill_off), series_txt, font=fpill, fill=(18, 18, 24, 255))
        if WM is not None:
            layer.alpha_composite(WM, (W - 40 - WM.width, 172))
        for s in scenes:
            if s["start"] <= t < s["end"]:
                lt = t - s["start"]; D = s["end"] - s["start"]
                fade_out = 1 - prog(lt, D - 0.22, 0.22) if s is not scenes[-1] else 1
                sl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sl)
                SCENES[s["type"]](sd, lt, D, {**s.get("data", {}), "_fast": s.get("role") == "hook", "_last": s is scenes[-1]})
                if fade_out < 1:
                    alpha = sl.getchannel("A").point(lambda v: int(v * fade_out)); sl.putalpha(alpha)
                sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.paste(sl, (0, SCENE_DY)); layer = Image.alpha_composite(layer, sh); d = ImageDraw.Draw(layer)
                break
        # progress bar
        d.rectangle([90, SAFE_BOTTOM + 40, 90 + int((W - 180) * t / total), SAFE_BOTTOM + 46], fill=rgba(PAL["accent"], 0.8))
        draw_caption(d, t, groups)
        frame = Image.alpha_composite(frame, layer).convert("RGB")
        proc.stdin.write(frame.tobytes())
    proc.stdin.close(); proc.wait()
    make_cover(spec, f"{outdir}/{rid}_cover.jpg", bg)
    json.dump({"id": rid, "duration_s": round(total, 2), "scenes": [{"type": s["type"], "role": s.get("role", ""), "start": round(s["start"], 2), "end": round(s["end"], 2), "voice_start": round(s["voice_start"], 2), "voice_end": round(s["voice_end"], 2), "on_screen_text": bool(s.get("data", {}).get("lines") or s.get("data", {}).get("text")), "illustration": s.get("illustration", "")} for s in scenes],
               "words": len(all_words)}, open(f"{outdir}/{rid}_timeline.json", "w"), indent=1)
    return mp4, total

def make_cover(spec, path, bg):
    c = spec["cover"]
    im = bg.copy(); d = ImageDraw.Draw(im)
    acc = set(w.lower() for w in c.get("accent", []))
    fk = font("sans_b", 40); s = spec.get("series", "").upper()
    d.text(((W - text_w(fk, s)) // 2, 600), s, font=fk, fill=PAL["accent"])
    centered_rich(d, 940, c["headline"], font("serif", 132), acc, 1, maxw=900, lh=1.05)
    if c.get("sub"):
        fs = font("sans_s", 44)
        d.text(((W - text_w(fs, c["sub"])) // 2, 1250), c["sub"], font=fs, fill=PAL["muted"])
    fb = font("sans_s", 32); b = spec.get("brand", "").upper()
    d.text(((W - text_w(fb, b)) // 2, 1340), b, font=fb, fill=PAL["muted"])
    wm = load_watermark(140, 0.8) if spec.get("watermark", False) else None
    if wm is not None:  # bottom-right corner of the 3:4 area shown on the profile grid
        im.alpha_composite(wm, (W - 60 - wm.width, 240 + 1440 - 60 - wm.height))
    im.convert("RGB").save(path, quality=92)

if __name__ == "__main__":
    mp4, dur = build(sys.argv[1], sys.argv[2])
    print(mp4, round(dur, 2))
