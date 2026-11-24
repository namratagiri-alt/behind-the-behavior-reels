"""Carousel renderer for Behind the Behavior: 1080x1350 (4:5) JPEG slides.

Spec JSON: {id, title, series, cover:{headline, accent[], sub}, items:[{title, body, illustration?}],
closing:{action, kicker}, source_line}
Output: <outdir>/<id>_01.jpg ... plus <id>_contact.jpg (for visual QC).
"""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reelengine import PAL, font, text_w, wrap, draw_rich_line, make_bg, rgba
from illustrations import SCENES as ILL

CW_, CH_ = 1080, 1350
SIGNOFF = "Understand the pattern. Change the response."

def base(series, brand, page, total, ill=None):
    bg = make_bg().crop((0, 280, 1080, 280 + CH_))
    if ill:
        im = ILL[ill]().crop((60, 420, 60 + CW_, 420 + CH_))
        bg.alpha_composite(im)
        sc = Image.new("RGBA", (CW_, CH_), (12, 14, 20, 150)); bg.alpha_composite(sc)
    d = ImageDraw.Draw(bg)
    d.text((80, 70), brand.upper(), font=font("sans_k", 28), fill=rgba(PAL["muted"], 1))
    fp = font("sans_k", 34); tw = text_w(fp, series)
    d.rounded_rectangle([70, 112, 70 + tw + 50, 170], 29, fill=rgba(PAL["accent"], 1))
    d.text((95, 120), series, font=fp, fill=(18, 18, 24, 255))
    fpg = font("sans_s", 30); pg = f"{page}/{total}"
    d.text((CW_ - 80 - text_w(fpg, pg), 76), pg, font=fpg, fill=rgba(PAL["muted"], 1))
    return bg, d

def centered(d, y, text, fnt, accents=(), maxw=900, lh=1.12, color=None):
    for ln in wrap(fnt, text, maxw):
        x = (CW_ - text_w(fnt, ln)) // 2
        draw_rich_line(d, x, y, ln, fnt, set(a.lower() for a in accents), 1, base=color)
        y += int(fnt.size * lh)
    return y

def left(d, x, y, text, fnt, maxw, color, lh=1.25):
    for ln in wrap(fnt, text, maxw):
        d.text((x, y), ln, font=fnt, fill=rgba(color, 1)); y += int(fnt.size * lh)
    return y

def build(spec_path, outdir):
    sp = json.load(open(spec_path)); os.makedirs(outdir, exist_ok=True)
    cid, series, brand = sp["id"], sp["series"], sp.get("brand", "Behind the Behavior")
    items = sp["items"]; total = len(items) + 2; paths = []
    # cover
    im, d = base(series, brand, 1, total, sp["cover"].get("illustration"))
    y = centered(d, 470, sp["cover"]["headline"], font("serif", 104), sp["cover"].get("accent", []), maxw=920, lh=1.05)
    if sp["cover"].get("sub"):
        centered(d, y + 40, sp["cover"]["sub"], font("sans_s", 40), maxw=860, color=PAL["muted"])
    fs = font("sans_b", 32); sw = "Swipe to see all " + str(len(items)) + "  >"
    d.text(((CW_ - text_w(fs, sw)) // 2, 1220), sw, font=fs, fill=rgba(PAL["accent"], 1))
    paths.append(im)
    # items
    for i, it in enumerate(items, 1):
        im, d = base(series, brand, i + 1, total, it.get("illustration"))
        fn = font("sans_k", 150)
        d.text((80, 260), f"{i:02d}", font=fn, fill=rgba(PAL["accent"], 0.9))
        y = left(d, 80, 470, it["title"], font("serif", 82), 920, PAL["ink"], lh=1.08)
        d.line([80, y + 30, 200, y + 30], fill=rgba(PAL["accent"], 1), width=5)
        y = left(d, 80, y + 70, it["body"], font("sans", 44), 920, PAL["ink"], lh=1.32)
        if it.get("try"):
            d.rounded_rectangle([70, y + 40, CW_ - 70, y + 40 + 60 + 54 * len(wrap(font("sans_b", 40), "Try: " + it["try"], 860))], 26, fill=rgba(PAL["card"], 0.95))
            left(d, 100, y + 68, "Try: " + it["try"], font("sans_b", 40), 860, PAL["teal"])
        if it.get("source"):
            fsrc = font("sans_s", 26); d.text((80, 1270), it["source"], font=fsrc, fill=rgba(PAL["muted"], 1))
        paths.append(im)
    # closing
    im, d = base(series, brand, total, total, sp["closing"].get("illustration"))
    y = centered(d, 420, sp["closing"]["action"], font("serif", 78), sp["closing"].get("accent", []), maxw=900)
    centered(d, y + 50, sp["closing"].get("kicker", "Save this for later").upper(), font("sans_b", 38), maxw=900, color=PAL["accent"])
    d.line([CW_ // 2 - 70, 1050, CW_ // 2 + 70, 1050], fill=rgba(PAL["dim"], 1), width=2)
    centered(d, 1080, SIGNOFF, font("serif_i", 46), maxw=940, color=PAL["muted"])
    paths.append(im)
    out = []
    for k, im in enumerate(paths, 1):
        p = f"{outdir}/{cid}_{k:02d}.jpg"; im.convert("RGB").save(p, quality=90); out.append(p)
    sheet = Image.new("RGB", (270 * min(5, len(out)), 338 * ((len(out) + 4) // 5)))
    for k, p in enumerate(out):
        sheet.paste(Image.open(p).resize((270, 338)), ((k % 5) * 270, (k // 5) * 338))
    sheet.save(f"{outdir}/{cid}_contact.jpg", quality=85)
    return out

if __name__ == "__main__":
    for p in build(sys.argv[1], sys.argv[2]): print(p)
