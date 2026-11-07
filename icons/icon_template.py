"""
Neon Arcade '90s icon generator (1024x1024 PNG, iOS-safe: nothing important near the corners).

Usage:
    python3 icon_template.py                  # builds every preset below
    python3 icon_template.py neon_arcade      # builds one preset

To make a new icon, copy a preset and change the text/sizes:
    "title": list of (text, font_size, centre_y) - one line or two
    "tag":   (text, font_size, centre_y) or None to hide it
Keep each title line under ~950 px wide (the script prints the widths).

Needs: Python 3 + Pillow, and the font Poppins Bold Italic (free, Google Fonts, OFL licence).
If the font is elsewhere, change FONT below.
"""
import os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Poppins-BoldItalic.ttf"),
]
FONT = next((p for p in FONT_CANDIDATES if os.path.exists(p)), FONT_CANDIDATES[0])

PRESETS = {
    "neon_arcade":  {"title": [("NEON", 262, 300), ("ARCADE", 226, 525)], "tag": ("’90s", 262, 805)},
    "othello":      {"title": [("OTHELLO", 220, 450)],                    "tag": ("’90s", 262, 805)},
    "knucklebones": {"title": [("KNUCKLE", 190, 300), ("BONES", 262, 520)], "tag": ("’90s", 262, 805)},
    "water_sort":   {"title": [("WATER", 230, 300), ("SORT", 262, 520)],    "tag": ("’90s", 262, 805)},
}

S = 1024
HORIZON = 690


def blank(mode="L"):
    return Image.new(mode, (S, S), 0)


def build(cfg, out_path):
    random.seed(7)
    canvas = Image.new("RGB", (S, S))

    def add_glow(mask, color, radii):
        nonlocal canvas
        for rad in radii:
            m = mask.filter(ImageFilter.GaussianBlur(rad)) if rad else mask
            canvas = ImageChops.add(canvas, Image.composite(Image.new("RGB", (S, S), color), blank("RGB"), m))

    # Background gradient
    d = ImageDraw.Draw(canvas)
    for y in range(S):
        t = y / S
        d.line([(0, y), (S, y)], fill=(int(12 + 40 * t), int(4 + 6 * t), int(38 + 50 * (1 - abs(t - 0.6)))))

    # Stars + sparkles
    stars = blank(); st = ImageDraw.Draw(stars)
    for _ in range(140):
        x, y = random.randint(0, S), random.randint(0, 660)
        r = random.choice([1, 1, 1, 2, 2, 3])
        st.ellipse([x - r, y - r, x + r, y + r], fill=random.randint(120, 255))
    add_glow(stars, (200, 220, 255), (4, 0))
    sp = blank(); spd = ImageDraw.Draw(sp)
    for x, y, L in [(150, 150, 26), (880, 210, 20), (820, 110, 14), (230, 640, 16), (790, 630, 22), (120, 420, 12), (905, 450, 14)]:
        spd.line([(x - L, y), (x + L, y)], fill=255, width=3)
        spd.line([(x, y - L), (x, y + L)], fill=255, width=3)
    add_glow(sp, (120, 240, 255), (8, 2, 0))

    # Striped sun
    cx, cy, R = S // 2, 590, 480
    sun = blank("RGB"); sd = ImageDraw.Draw(sun)
    for yy in range(cy - R, cy + R):
        t = (yy - (cy - R)) / (2 * R)
        sd.line([(0, yy), (S, yy)], fill=(255, int(220 - 190 * t), int(60 + 120 * t)))
    sm = blank(); smd = ImageDraw.Draw(sm)
    smd.ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    gap, yy = 4, cy - 40
    while yy < HORIZON:
        smd.rectangle([0, yy, S, yy + gap], fill=0)
        yy += 28; gap += 3
    smd.rectangle([0, HORIZON, S, S], fill=0)
    add_glow(sm, (255, 40, 120), (60,))
    canvas.paste(sun, mask=sm.point(lambda v: int(v * 0.8)))

    # Cyan wireframe mountains
    pts_l = [(-40, 690), (40, 450), (130, 560), (215, 500), (400, 690)]
    pts_r = [(624, 690), (800, 510), (890, 570), (985, 430), (1064, 690)]
    mtn = blank(); md = ImageDraw.Draw(mtn)
    fillm = blank(); fd = ImageDraw.Draw(fillm)
    for pts in (pts_l, pts_r):
        fd.polygon(pts, fill=255)
        md.line(pts, fill=255, width=4)
        for p in pts[1:-1]:
            md.line([p, (p[0] + (p[0] - S / 2) * 0.08, HORIZON)], fill=160, width=2)
    canvas.paste((18, 6, 45), mask=fillm)
    add_glow(mtn, (0, 220, 255), (14, 4, 0))

    # Perspective grid + horizon line
    grid = blank(); gd = ImageDraw.Draw(grid)
    for i in range(-12, 13):
        gd.line([(S / 2 + i * 22, HORIZON), (S / 2 + i * 190, S)], fill=255, width=3)
    y, step = HORIZON, 8
    while y < S:
        gd.line([(0, y), (S, y)], fill=255, width=3)
        y += step; step *= 1.35
    fade = blank(); fdd = ImageDraw.Draw(fade)
    for yy in range(HORIZON, S):
        fdd.line([(0, yy), (S, yy)], fill=int(255 * min(1, (yy - HORIZON) / 220)))
    grid = ImageChops.multiply(grid, fade)
    for rad, col in ((10, (255, 0, 170)), (3, (255, 60, 200)), (0, (255, 140, 230))):
        add_glow(grid, col, (rad,))
    hl = blank(); ImageDraw.Draw(hl).line([(0, HORIZON), (S, HORIZON)], fill=255, width=5)
    add_glow(hl, (255, 0, 200), (20, 6))

    # Helper: draw centred text into a mask
    def text_mask(items, stroke=0, filled=True, offset=(0, 0)):
        m = blank(); dr = ImageDraw.Draw(m)
        for txt, size, y in items:
            f = ImageFont.truetype(FONT, size)
            w = dr.textlength(txt, font=f)
            dr.text((S / 2 - w / 2 + offset[0], y + offset[1]), txt, font=f, fill=255 if filled else 0,
                    stroke_width=stroke, stroke_fill=255, anchor="lm")
        return m

    # Title: pink glow, dark backing, pink outline, gold->pink gradient fill, highlight
    title = cfg["title"]
    for txt, size, _ in title:
        w = ImageDraw.Draw(blank()).textlength(txt, font=ImageFont.truetype(FONT, size))
        print(f"  {txt!r}: {w:.0f}px wide")
    fill = text_mask(title)
    add_glow(fill, (255, 20, 170), (30, 10))
    back = text_mask(title, stroke=22, offset=(8, 10))
    canvas.paste((20, 4, 40), mask=back.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.9)))
    canvas.paste((255, 70, 200), mask=text_mask(title, stroke=10, filled=False))
    top = min(y for _, _, y in title) - 80
    span = max(y for _, _, y in title) + 100 - top
    grad = blank("RGB"); gdr = ImageDraw.Draw(grad)
    for yy in range(S):
        t = min(1, max(0, (yy - top) / span))
        gdr.line([(0, yy), (S, yy)], fill=(255, int(240 - 150 * t), int(120 + 110 * t)))
    canvas.paste(grad, mask=fill)
    canvas.paste((255, 250, 235), mask=fill.filter(ImageFilter.MinFilter(9)).point(lambda v: int(v * 0.45)))

    # Tag ('90s) in cyan
    if cfg.get("tag"):
        tag = [cfg["tag"]]
        tback = text_mask(tag, stroke=18, offset=(6, 8))
        canvas.paste((14, 4, 34), mask=tback.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.9)))
        tm = text_mask(tag)
        add_glow(tm, (0, 200, 255), (28, 10))
        canvas.paste((40, 220, 255), mask=text_mask(tag, stroke=10, filled=False))
        canvas.paste((215, 250, 255), mask=tm)

    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    canvas.save(out_path)
    print(f"saved {out_path}")


if __name__ == "__main__":
    names = sys.argv[1:] or list(PRESETS)
    for n in names:
        build(PRESETS[n], f"{n}_icon.png")
