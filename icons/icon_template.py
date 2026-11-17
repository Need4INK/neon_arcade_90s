"""
Neon Arcade app icon: a neon sign on a brick wall ("NEON" pink, "ARCADE" yellow, an arcade joystick on top,
a cyan rounded triangle behind the words, small confetti shapes).

    python3 icons/icon_template.py      # writes every icon the site uses (run from anywhere)

Writes, all full-bleed squares with no rounded corners (iOS, Android and desktop cut their own shapes):
    ../icon.png              512  manifest "any" (Android, desktop Chrome/Edge installed app)
    ../icon-192.png          192  manifest "any" + <link rel="icon" sizes="192x192">
    ../apple-touch-icon.png  180  iPhone / iPad home screen
    ../icon-maskable.png     512  manifest "maskable": sign drawn smaller so the words and joystick stay
                                  inside the central 80% safe circle every Android launcher shape keeps
    ../favicon.png            48  browser tab
    neon_arcade_icon.png    1024  full-size master (not part of the site; for og.jpg or a store page)

Needs: Python 3 + Pillow. No fonts: the letters are drawn as tubes from the GLYPHS table below.
Drawn at 2x and scaled down so the tubes stay sharp. The output is the same on every run (fixed seeds).
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

S, Z = 1024, 2            # design size, supersampling
N = S * Z
CX, CY = 512, 505         # the sign is scaled around this point
SIGN = 1.32               # sign size on the normal icon (NEON ~87% of the width)
SIGN_MASKABLE = 1.0       # smaller for Android so it fits the safe circle

PINK, YEL, CYAN, GRN, ORG, MAG = (255, 70, 225), (255, 233, 77), (25, 243, 255), (57, 255, 122), (255, 158, 44), (255, 43, 214)
WHITE, RED, PURP = (235, 240, 255), (255, 45, 70), (170, 80, 255)


# ---------- lettering: strokes in unit coords (y down, cap height 1) ----------
def arc(cx, cy, rx, ry, a0, a1, n=40):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPHS = {  # letter: (width as share of the height, strokes)
    "N": (.74, [[(0, 1), (0, 0), (.74, 1), (.74, 0)]]),
    "E": (.58, [[(.58, 0), (0, 0), (0, 1), (.58, 1)], [(0, .5), (.48, .5)]]),
    "O": (.92, [arc(.46, .5, .46, .5, 0, 360, 72)]),
    "A": (.84, [[(0, 1), (.42, 0), (.84, 1)], [(.17, .66), (.67, .66)]]),
    "R": (.64, [[(0, 1), (0, 0), (.36, 0)] + arc(.36, .26, .26, .26, -90, 90) + [(0, .52)], [(.32, .52), (.64, 1)]]),
    "C": (.80, [arc(.48, .5, .48, .5, 42, 318, 60)]),
    "D": (.78, [[(0, 1), (0, 0), (.3, 0)] + arc(.3, .5, .48, .5, -90, 90) + [(0, 1)]]),
}


def word_strokes(word, cx, cy, H, gap):
    x = cx - (sum(GLYPHS[c][0] * H for c in word) + gap * (len(word) - 1)) / 2
    out = []
    for c in word:
        wf, strokes = GLYPHS[c]
        out += [[(x + px * H, cy - H / 2 + py * H) for px, py in s] for s in strokes]
        x += wf * H + gap
    return out


# ---------- shapes ----------
def zig(x, y, n, w, h):
    return [(x + i * w, y + (h if i % 2 else 0)) for i in range(n + 1)]


def reg(cx, cy, r, n, rot):
    return [(cx + r * math.cos(math.radians(rot + 360 * i / n - 90)), cy + r * math.sin(math.radians(rot + 360 * i / n - 90))) for i in range(n)]


def rounded(v, f=.18):  # closed polygon with curved corners
    def bez(a, p, b, n=16):
        return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * p[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * p[1] + t * t * b[1])
                for t in [i / n for i in range(n + 1)]]
    out = []
    for i in range(len(v)):
        a, p, b = v[i - 1], v[i], v[(i + 1) % len(v)]
        out += bez((p[0] + (a[0] - p[0]) * f, p[1] + (a[1] - p[1]) * f), p, (p[0] + (b[0] - p[0]) * f, p[1] + (b[1] - p[1]) * f))
    return out + [out[0]]


# ---------- the sign ----------
class Sign:
    def __init__(self, k):
        self.k, self.tubes = k, []
        self.clear = Image.new("L", (N, N), 0)   # where the triangle breaks (behind words and joystick)

    def tf(self, x, y):
        return (CX + (x - CX) * self.k) * Z, (CY + (y - CY) * self.k) * Z

    def poly(self, d, pts, w):
        p = [self.tf(x, y) for x, y in pts]; w = w * Z * self.k
        d.line(p, fill=255, width=int(round(w)), joint="curve")
        for x, y in p: d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)

    def bubble(self, word, cx, cy, H, col, T, t):  # outlined tube letters
        st = word_strokes(word, cx, cy, H, T + H * .07)
        o, h = Image.new("L", (N, N), 0), Image.new("L", (N, N), 0)
        do, dh, dc = ImageDraw.Draw(o), ImageDraw.Draw(h), ImageDraw.Draw(self.clear)
        for s in st:
            self.poly(do, s, T); self.poly(dh, s, T - 2 * t); self.poly(dc, s, T + 30)
        self.tubes.append((ImageChops.subtract(o, h), col))

    def line(self, pts, col, w=8, closed=False, broken=False):
        m = Image.new("L", (N, N), 0)
        self.poly(ImageDraw.Draw(m), pts + [pts[0]] if closed else pts, w)
        if broken: m = ImageChops.subtract(m, self.clear)
        self.tubes.append((m, col))

    def ring(self, cx, cy, r, col, w=8):
        self.line(arc(cx, cy, r, r, 0, 360, 90), col, w)

    def dot(self, x, y, r, col):
        m = Image.new("L", (N, N), 0)
        ImageDraw.Draw(m).ellipse([*self.tf(x - r, y - r), *self.tf(x + r, y + r)], fill=255)
        self.tubes.append((m, col))

    def joystick(self, cx, by):  # by = top of the base
        ImageDraw.Draw(self.clear).rounded_rectangle([*self.tf(cx - 150, by - 190), *self.tf(cx + 150, by + 60)], 40 * Z, fill=255)
        self.line([(cx - 110, by), (cx + 110, by), (cx + 125, by + 42), (cx - 125, by + 42)], CYAN, 10, closed=True)  # base
        self.line(arc(cx, by, 30, 22, 180, 360, 30), CYAN, 9)                     # collar
        self.line([(cx + 4, by - 20), (cx + 27, by - 93)], WHITE, 11)             # shaft
        self.ring(cx + 36, by - 126, 33, RED, 11)                                  # ball
        self.line(arc(cx + 36, by - 126, 17, 17, 200, 260, 12), WHITE, 7)        # shine
        self.line(arc(cx - 68, by, 15, 13, 180, 360, 20), YEL, 8)                 # buttons
        self.line(arc(cx + 70, by, 15, 13, 180, 360, 20), GRN, 8)


def build(k):
    s = Sign(k)
    s.joystick(512, 322)
    s.bubble("NEON", 512, 465, 150, PINK, T=52, t=10)
    s.bubble("ARCADE", 512, 632, 92, YEL, T=34, t=8)
    s.line(rounded(reg(505, 495, 370, 3, 192)), CYAN, 11, broken=True)
    # confetti: positions are for the first draft (sign 1.2); pulled in so they keep clear of the edges
    P = lambda x, y: (CX + (x - CX) * 1.2 / 1.32, CY + (y - CY) * 1.2 / 1.32)
    for x, y, c, rot in ((190, 300, YEL, 20), (860, 655, GRN, 30)):
        s.line(reg(*P(x, y), 22, 3, rot), c, 8, closed=True)
    s.line(reg(*P(170, 610), 20, 4, 15), WHITE, 8, closed=True)
    s.ring(*P(845, 300), 18, WHITE)
    s.ring(*P(560, 835), 18, YEL)
    s.line(zig(*P(290, 805), 4, 24, 18), GRN, 8)
    s.line(zig(*P(650, 770), 4, 24, 18), MAG, 8)
    for x, y, c in ((790, 220, ORG), (300, 735, ORG), (250, 175, CYAN)):
        s.dot(*P(x, y), 6, c)
    return s


# ---------- wall and light ----------
def noise(seed, amount):
    rnd = random.Random(seed)
    return Image.frombytes("L", (S, S), rnd.randbytes(S * S)).point(lambda v: max(0, v - 255 + amount) // 4).convert("RGB")


def wall():
    rnd = random.Random(7)
    im = Image.new("RGB", (S, S), (12, 9, 30)); d = ImageDraw.Draw(im)
    bh, bw = 66, 176
    for r in range(S // bh + 2):
        off = (bw // 2) * (r % 2)
        for c in range(-1, S // bw + 2):
            x0, y0, v = c * bw - off, r * bh, rnd.randint(-5, 5)
            d.rounded_rectangle([x0 + 4, y0 + 4, x0 + bw - 4, y0 + bh - 4], 7, fill=(30 + v, 25 + v, 70 + v))
    im = ImageChops.subtract(ImageChops.add(im, noise(1, 40)), noise(2, 40))
    # no darkening towards the edges: on a dark home screen or dock a dark rim makes the icon look smaller
    w = Image.new("L", (S, S), 0); ImageDraw.Draw(w).ellipse([180, 170, 840, 830], fill=80)
    return ImageChops.add(im, Image.composite(Image.new("RGB", (S, S), PURP), Image.new("RGB", (S, S), 0), w.filter(ImageFilter.GaussianBlur(190))))


def render(k=SIGN):
    """The icon as a 1024x1024 RGB image (k = sign size)."""
    sign = build(k)
    base = wall().resize((N, N), Image.BICUBIC)
    black = Image.new("RGB", (N, N), 0)
    glow = Image.new("RGB", (N, N), 0)
    for mask, col in sign.tubes:
        for rad, f in ((90, .4), (28, .35), (8, .3)):
            g = mask.filter(ImageFilter.GaussianBlur(rad * Z)).point(lambda v, f=f: int(min(255, v * f * 1.4)))
            glow = ImageChops.add(glow, Image.composite(Image.new("RGB", (N, N), col), black, g))
    out = ImageChops.add(base, ImageChops.multiply(glow, base.point(lambda v: min(255, v * 3))))  # light on the bricks
    out = ImageChops.add(out, glow.point(lambda v: v * 30 // 100))
    for mask, col in sign.tubes:
        body = tuple(min(255, int(c * .85 + 255 * .15)) for c in col)
        hot = tuple(min(255, int(c * .4 + 255 * .6)) for c in col)
        out = Image.composite(Image.new("RGB", (N, N), body), out, mask.filter(ImageFilter.GaussianBlur(.35 * Z)))
        core = mask.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(1.0 * Z))
        out = Image.composite(Image.new("RGB", (N, N), hot), out, core.point(lambda v: v * 90 // 100))
    return out.resize((S, S), Image.LANCZOS)


def save(im, size, path):
    im.resize((size, size), Image.LANCZOS).save(path, optimize=True)
    print("wrote", os.path.relpath(path, ROOT), size)


if __name__ == "__main__":
    icon = render(SIGN)
    save(icon, 1024, os.path.join(HERE, "neon_arcade_icon.png"))
    for size, name in ((512, "icon.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (48, "favicon.png")):
        save(icon, size, os.path.join(ROOT, name))
    save(render(SIGN_MASKABLE), 512, os.path.join(ROOT, "icon-maskable.png"))
