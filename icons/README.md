# App icons

`icon_template.py` draws the Neon Arcade icon: a neon sign on a brick wall ("NEON" pink, "ARCADE" yellow, an arcade
joystick on top, a cyan triangle behind the words, confetti). Needs Python 3 + Pillow; no fonts (the letters are
drawn as tubes). Same output on every run.

```
pip install pillow
python3 icons/icon_template.py
```

It writes every icon the site uses. All are full-bleed squares with no rounded corners: iPhone, Android and desktop
cut their own shapes.

| File | Size | Used by |
|---|---|---|
| `../apple-touch-icon.png` | 180 | iPhone / iPad home screen (`<link rel="apple-touch-icon">`) |
| `../icon.png` | 512 | manifest `any`: Android, installed desktop app (Chrome / Edge) |
| `../icon-192.png` | 192 | manifest `any`, `<link rel="icon" sizes="192x192">` |
| `../icon-maskable.png` | 512 | manifest `maskable`: Android launchers; the sign is drawn smaller so the words and joystick stay inside the central 80% safe circle |
| `../favicon.png` | 48 | browser tab |
| `neon_arcade_icon.png` | 1024 | full-size master, not part of the site (git-ignored); `share_images.py` uses it for `og.jpg` |

`tests/icon_preview.py` shows `icon.png` with iPhone corners and `icon-maskable.png` cut to the Android shapes.

`share_images.py` (Pillow + OpenCV) makes `qr.svg` (the QR in the cover's share pop-up), the printable poster
`neon_arcade_qr.png` and the link-preview picture `../og.jpg`. Re-run it after changing the icon (run
`icon_template.py` first) or the site address; it checks that the QR reads back.
