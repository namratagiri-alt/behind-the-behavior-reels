"""Faceless flat editorial illustrations drawn in code (no people, no faces, no text).

Each scene function draws on an RGBA canvas of size (CW, CH), slightly larger than the
1080x1920 frame so the engine can drift the camera slowly. Colours are deliberately low
luminance so on-screen text stays readable on top.
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter

CW, CH = 1200, 2040
INK = (34, 39, 56); INK2 = (44, 50, 72); INK3 = (56, 64, 90); LINE = (78, 88, 120)
AMB = (245, 184, 65); TEAL = (88, 200, 186); CORAL = (255, 112, 92)

def A(c, a):
    return (c[0], c[1], c[2], int(255 * a))

def _base():
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def glow(im, cx, cy, r, col, a):
    g = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A(col, a))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.45)))

def desk():
    im, d = _base()
    glow(im, 300, 760, 260, AMB, 0.22)
    d.rectangle([0, 1440, CW, CH], fill=A(INK, 0.95))
    d.rectangle([0, 1430, CW, 1450], fill=A(INK3, 1))
    # lamp
    d.line([210, 1430, 260, 1060], fill=A(LINE, 1), width=14)
    d.line([260, 1060, 420, 900], fill=A(LINE, 1), width=14)
    d.polygon([(380, 860), (520, 900), (470, 990)], fill=A(INK3, 1))
    d.polygon([(470, 990), (520, 900), (760, 1430), (380, 1430)], fill=A(AMB, 0.06))
    d.ellipse([150, 1410, 280, 1450], fill=A(INK3, 1))
    # laptop
    d.polygon([(560, 1060), (980, 1060), (1000, 1380), (540, 1380)], fill=A(INK2, 1), outline=A(LINE, 1))
    d.rectangle([585, 1090, 955, 1350], fill=A(TEAL, 0.10))
    for i in range(5):
        d.rounded_rectangle([615, 1120 + i * 44, 615 + (300 - i * 37), 1140 + i * 44], 8, fill=A(TEAL, 0.22))
    d.polygon([(500, 1385), (1040, 1385), (1080, 1430), (460, 1430)], fill=A(INK3, 1))
    # mug
    d.rounded_rectangle([1050, 1300, 1150, 1430], 16, fill=A(INK3, 1))
    d.arc([1120, 1330, 1185, 1395], 270, 90, fill=A(LINE, 1), width=10)
    for k in range(3):
        d.arc([1060 + k * 28, 1190, 1110 + k * 28, 1290], 200, 340, fill=A(LINE, 0.6), width=5)
    # papers and plant
    d.polygon([(120, 1530), (420, 1500), (460, 1700), (150, 1730)], fill=A(INK2, 1))
    d.rounded_rectangle([880, 1520, 990, 1640], 12, fill=A(INK3, 1))
    for ang in (-50, -20, 10, 40):
        x = 935 + 90 * math.sin(math.radians(ang)); y = 1520 - 90 * math.cos(math.radians(ang))
        d.ellipse([x - 26, y - 46, x + 26, y + 46], fill=A(TEAL, 0.28))
    return im

def phone():
    im, d = _base()
    glow(im, 600, 1150, 380, TEAL, 0.14)
    d.rounded_rectangle([330, 620, 870, 1760], 70, fill=A(INK2, 1), outline=A(LINE, 1), width=6)
    d.rounded_rectangle([360, 690, 840, 1690], 40, fill=A((20, 24, 36), 1))
    d.rounded_rectangle([540, 650, 660, 672], 11, fill=A(INK3, 1))
    for i in range(4):
        y = 780 + i * 170
        d.rounded_rectangle([390, y, 810, y + 130], 26, fill=A(INK3, 0.95))
        d.ellipse([415, y + 35, 475, y + 95], fill=A([AMB, TEAL, CORAL, AMB][i], 0.55))
        d.rounded_rectangle([495, y + 38, 760, y + 58], 9, fill=A(LINE, 0.9))
        d.rounded_rectangle([495, y + 76, 690, y + 92], 8, fill=A(LINE, 0.55))
    for r in (120, 190, 260):
        d.arc([870 - r, 560 - r, 870 + r, 560 + r], 300, 350, fill=A(AMB, 0.35), width=8)
    return im

def shelf():
    im, d = _base()
    glow(im, 600, 900, 420, AMB, 0.12)
    rnd = random.Random(7)
    for s in range(5):
        y = 520 + s * 300
        d.rectangle([80, y, 1120, y + 26], fill=A(INK3, 1))
        x = 110
        while x < 1060:
            w = rnd.randint(90, 170); h = rnd.randint(130, 230)
            col = rnd.choice([INK2, INK2, (52, 46, 70), (40, 56, 70)])
            d.rounded_rectangle([x, y - h, x + w, y], 10, fill=A(col, 1), outline=A(LINE, 0.6), width=2)
            if rnd.random() < 0.35:
                tx, ty = x + w // 2, y + 40
                d.line([tx, y + 26, tx, ty], fill=A(LINE, 1), width=3)
                d.polygon([(tx - 34, ty), (tx + 34, ty), (tx + 34, ty + 52), (tx - 34, ty + 52)], fill=A(AMB if rnd.random() < 0.6 else CORAL, 0.75))
                d.ellipse([tx - 6, ty + 8, tx + 6, ty + 20], fill=A((20, 20, 26), 1))
            x += w + rnd.randint(18, 40)
    return im

def meeting():
    im, d = _base()
    glow(im, 600, 1000, 380, TEAL, 0.10)
    d.rectangle([0, 1500, CW, CH], fill=A(INK, 0.9))
    for cx in (230, 600, 970):
        d.rounded_rectangle([cx - 85, 1080, cx + 85, 1300], 40, fill=A(INK3, 1))
        d.rounded_rectangle([cx - 55, 1300, cx + 55, 1360], 14, fill=A(INK2, 1))
    d.ellipse([80, 1280, 1120, 1560], fill=A(INK2, 1), outline=A(LINE, 1), width=4)
    for cx in (330, 600, 870):
        d.polygon([(cx - 80, 1330), (cx + 80, 1330), (cx + 95, 1400), (cx - 95, 1400)], fill=A(INK3, 1))
        d.rectangle([cx - 66, 1336, cx + 66, 1392], fill=A(TEAL, 0.12))
    for i, (bx, by) in enumerate([(160, 760), (520, 640), (860, 780)]):
        d.rounded_rectangle([bx, by, bx + 220, by + 120], 40, fill=A([AMB, TEAL, CORAL][i], 0.22))
        d.polygon([(bx + 60, by + 120), (bx + 100, by + 120), (bx + 60, by + 170)], fill=A([AMB, TEAL, CORAL][i], 0.22))
    return im

def night():
    im, d = _base()
    d.rounded_rectangle([200, 380, 1000, 1180], 20, fill=A((16, 20, 34), 1), outline=A(LINE, 1), width=12)
    d.line([600, 380, 600, 1180], fill=A(LINE, 1), width=10); d.line([200, 780, 1000, 780], fill=A(LINE, 1), width=10)
    glow(im, 820, 540, 120, AMB, 0.25)
    d = ImageDraw.Draw(im)
    d.ellipse([770, 490, 870, 590], fill=A(AMB, 0.8)); d.ellipse([800, 475, 895, 570], fill=A((16, 20, 34), 1))
    rnd = random.Random(3)
    for _ in range(26):
        x, y = rnd.randint(220, 980), rnd.randint(400, 1160)
        if abs(x - 600) > 10 and abs(y - 780) > 10:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=A((230, 230, 240), rnd.uniform(0.3, 0.8)))
    d.rounded_rectangle([60, 1440, 1140, 1720], 40, fill=A(INK2, 1))
    d.rounded_rectangle([120, 1360, 480, 1470], 50, fill=A(INK3, 1))
    d.rounded_rectangle([60, 1520, 1140, 1760], 30, fill=A(INK, 1))
    glow(im, 380, 1400, 150, TEAL, 0.25)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([330, 1375, 430, 1430], 12, fill=A(TEAL, 0.6))
    return im

def kitchen():
    im, d = _base()
    glow(im, 600, 760, 300, AMB, 0.14)
    for x in (100, 420, 740):
        d.rounded_rectangle([x, 420, x + 300, 800], 14, fill=A(INK2, 1), outline=A(LINE, 0.7), width=3)
        d.rounded_rectangle([x + 130, 600, x + 170, 616], 8, fill=A(LINE, 1))
    d.line([600, 0, 600, 300], fill=A(LINE, 1), width=6)
    d.polygon([(520, 300), (680, 300), (720, 380), (480, 380)], fill=A(INK3, 1))
    d.rectangle([0, 1350, CW, 1420], fill=A(INK3, 1)); d.rectangle([0, 1420, CW, CH], fill=A(INK, 0.95))
    d.rounded_rectangle([420, 1360, 820, 1420], 20, fill=A((22, 26, 38), 1))
    d.line([620, 1360, 620, 1220], fill=A(LINE, 1), width=12); d.arc([620, 1180, 720, 1280], 180, 270, fill=A(LINE, 1), width=12)
    for i in range(6):
        d.ellipse([140, 1330 - i * 26, 340, 1360 - i * 26], fill=A([INK3, (70, 78, 104)][i % 2], 1), outline=A(LINE, 0.8))
    for i in range(3):
        d.rounded_rectangle([900 + i * 70, 1220, 950 + i * 70, 1350], 10, fill=A([TEAL, AMB, CORAL][i], 0.3))
    return im

def commute():
    im, d = _base()
    rnd = random.Random(11)
    for w in range(2):
        x0 = 120 + w * 520
        d.rounded_rectangle([x0, 500, x0 + 440, 1150], 50, fill=A((16, 20, 34), 1), outline=A(LINE, 1), width=14)
        for _ in range(7):
            bx = rnd.randint(x0 + 20, x0 + 380); bh = rnd.randint(150, 420)
            d.rectangle([bx, 1140 - bh, bx + rnd.randint(40, 80), 1140], fill=A(INK3, 1))
            for wy in range(1140 - bh + 20, 1130, 40):
                if rnd.random() < 0.45:
                    d.rectangle([bx + 10, wy, bx + 22, wy + 14], fill=A(AMB, 0.5))
    d.line([0, 330, CW, 330], fill=A(LINE, 1), width=16)
    for x in range(140, 1100, 190):
        d.line([x, 330, x, 420], fill=A(LINE, 1), width=6)
        d.ellipse([x - 32, 420, x + 32, 484], outline=A(LINE, 1), width=8)
    d.rectangle([0, 1300, CW, CH], fill=A(INK, 0.9))
    d.rounded_rectangle([80, 1260, 1120, 1420], 30, fill=A(INK2, 1))
    return im

def park():
    im, d = _base()
    glow(im, 900, 520, 200, AMB, 0.18)
    d.ellipse([60, 1420, 1500, 2300], fill=A(INK2, 1)); d.ellipse([-400, 1500, 800, 2400], fill=A(INK, 1))
    d.rectangle([250, 1050, 290, 1480], fill=A(INK3, 1))
    for (cx, cy, r) in ((270, 960, 200), (170, 1060, 140), (380, 1050, 150)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A((40, 70, 76), 1))
    d.line([700, 1100, 780, 1500], fill=A(LINE, 1), width=12); d.line([1060, 1100, 980, 1500], fill=A(LINE, 1), width=12)
    d.line([690, 1100, 1070, 1100], fill=A(LINE, 1), width=14)
    for sx in (800, 940):
        d.line([sx, 1100, sx, 1330], fill=A(LINE, 0.8), width=4); d.line([sx + 60, 1100, sx + 60, 1330], fill=A(LINE, 0.8), width=4)
        d.rounded_rectangle([sx - 10, 1330, sx + 70, 1350], 6, fill=A(AMB, 0.6))
    d.rounded_rectangle([420, 1500, 680, 1530], 8, fill=A(INK3, 1)); d.rectangle([440, 1530, 456, 1590], fill=A(INK3, 1)); d.rectangle([644, 1530, 660, 1590], fill=A(INK3, 1))
    return im

def money():
    im, d = _base()
    glow(im, 600, 1100, 360, AMB, 0.16)
    d.rounded_rectangle([170, 1000, 620, 1300], 40, fill=A(INK2, 1), outline=A(LINE, 1), width=5)
    d.rounded_rectangle([450, 1090, 650, 1210], 30, fill=A(INK3, 1)); d.ellipse([570, 1130, 610, 1170], fill=A(AMB, 0.6))
    d.rounded_rectangle([720, 820, 1010, 1360], 50, outline=A(LINE, 1), width=10, fill=A((24, 28, 42), 1))
    d.rectangle([760, 790, 970, 830], fill=A(INK3, 1))
    for i in range(9):
        y = 1320 - i * 34
        d.ellipse([760 + (i % 2) * 20, y - 18, 950 + (i % 2) * 20, y + 18], fill=A(AMB, 0.35 + 0.03 * i), outline=A(AMB, 0.6))
    for (x, y) in ((260, 1440), (360, 1470), (460, 1430)):
        d.ellipse([x - 50, y - 50, x + 50, y + 50], fill=A(AMB, 0.4), outline=A(AMB, 0.7), width=4)
    return im

def calendar():
    im, d = _base()
    glow(im, 600, 1100, 360, TEAL, 0.10)
    d.rounded_rectangle([170, 640, 1030, 1640], 40, fill=A(INK2, 1), outline=A(LINE, 1), width=5)
    d.rounded_rectangle([170, 640, 1030, 780], 40, fill=A(INK3, 1)); d.rectangle([170, 740, 1030, 780], fill=A(INK3, 1))
    for x in (330, 870):
        d.rounded_rectangle([x - 14, 590, x + 14, 690], 14, fill=A(LINE, 1))
    for r in range(5):
        for c in range(7):
            x = 210 + c * 116; y = 820 + r * 156
            hi = (r, c) in ((1, 0), (2, 0), (3, 0))
            d.rounded_rectangle([x, y, x + 96, y + 130], 14, fill=A(AMB if hi else INK3, 0.5 if hi else 0.9))
    return im

SCENES = {"desk": desk, "phone": phone, "shelf": shelf, "meeting": meeting, "night": night,
          "kitchen": kitchen, "commute": commute, "park": park, "money": money, "calendar": calendar}
