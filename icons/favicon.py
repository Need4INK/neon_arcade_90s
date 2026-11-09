"""
Browser-tab / favourites icon: the phone icon (../icon.png) made small, with rounded corners.

    python3 icons/favicon.py        # writes ../favicon.png (48px) and ../favicon-192.png

Needs: Python 3 + Pillow. Re-run it after changing icon.png.
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADIUS = 0.18  # corner radius as a share of the width

if __name__ == "__main__":
    src = Image.open(os.path.join(ROOT, "icon.png")).convert("RGBA")
    mask = Image.new("L", src.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, src.width - 1, src.height - 1], int(src.width * RADIUS), fill=255)
    src.putalpha(mask)
    for size, name in ((48, "favicon.png"), (192, "favicon-192.png")):
        src.resize((size, size), Image.LANCZOS).save(os.path.join(ROOT, name), optimize=True)
        print("wrote", name, size)
