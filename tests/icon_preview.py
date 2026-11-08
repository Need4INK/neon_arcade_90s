"""Preview the Android maskable icon in the common launcher shapes.

    python3 tests/icon_preview.py      # writes tests/out/android_icon_preview.png

Shows today's fallback (icon.png shrunk in a white circle) next to icon-maskable.png cut to a circle, squircle,
rounded square, teardrop and the smallest crop (the 80% safe circle). The text must stay whole in every shape.
Needs Pillow; the labels use Poppins Bold if it's installed.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont
from harness import ROOT, out

N = 240
try:
    F = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', 22)
except OSError:
    F = ImageFont.load_default()


def mask(kind):
    S = N * 4
    m = Image.new('L', (S, S), 0); d = ImageDraw.Draw(m)
    if kind == 'circle': d.ellipse([0, 0, S - 1, S - 1], fill=255)
    elif kind == 'safe': d.ellipse([S * .1, S * .1, S * .9, S * .9], fill=255)
    elif kind == 'rounded': d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * .2), fill=255)
    elif kind == 'teardrop':
        d.ellipse([0, 0, S - 1, S - 1], fill=255); d.rectangle([S // 2, S // 2, S - 1, S - 1], fill=255)
    elif kind == 'squircle':
        pts = []
        for i in range(720):
            t = 2 * math.pi * i / 720; c, s = math.cos(t), math.sin(t)
            pts.append((S / 2 + S / 2 * math.copysign(abs(c) ** .4, c), S / 2 + S / 2 * math.copysign(abs(s) ** .4, s)))
        d.polygon(pts, fill=255)
    return m.resize((N, N), Image.LANCZOS)


mk = Image.open(os.path.join(ROOT, 'icon-maskable.png')).convert('RGBA').resize((N, N), Image.LANCZOS)
old = Image.open(os.path.join(ROOT, 'icon.png')).convert('RGBA')
t = Image.new('RGBA', (N, N), (0, 0, 0, 0)); t.paste(Image.new('RGBA', (N, N), 'white'), (0, 0), mask('circle'))
small = old.resize((int(N * .62),) * 2, Image.LANCZOS); t.paste(small, ((N - small.width) // 2,) * 2)
tiles = [('Before (white circle)', t)]
for k, lab in [('circle', 'Circle'), ('squircle', 'Squircle'), ('rounded', 'Rounded square'),
               ('teardrop', 'Teardrop'), ('safe', 'Smallest crop')]:
    t = Image.new('RGBA', (N, N), (0, 0, 0, 0)); t.paste(mk, (0, 0), mask(k)); tiles.append((lab, t))
sheet = Image.new('RGB', (3 * (N + 40) + 40, 2 * (N + 80) + 40), (30, 30, 36)); d = ImageDraw.Draw(sheet)
for i, (lab, t) in enumerate(tiles):
    x, y = 40 + (i % 3) * (N + 40), 40 + (i // 3) * (N + 80)
    sheet.paste(t, (x, y), t)
    d.text((x + N / 2 - d.textlength(lab, font=F) / 2, y + N + 12), lab, font=F, fill=(235, 235, 240))
sheet.save(out('android_icon_preview.png')); print('saved', out('android_icon_preview.png'))
