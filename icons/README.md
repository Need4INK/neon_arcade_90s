# App icons

`icon_template.py` makes the 1024×1024 neon icons (iOS-safe, nothing important near the corners).

```
pip install pillow
python3 icon_template.py              # all presets
python3 icon_template.py othello      # one preset
```

The site's `../icon.png` is the `neon_arcade` preset shrunk to 512×512 (iPhone needs 180px, Android 512px); to remake `og.jpg` or the favicons at full sharpness, start from the 1024px `neon_arcade_icon.png` this script writes.

Presets: `neon_arcade`, `othello`, `knucklebones`, `water_sort`, `sudoku`, `remi`. `neon_arcade_maskable` makes the Android icon `../icon-maskable.png` (512px): the same picture with the text inside the central safe circle (80% wide) that every launcher shape keeps. For a new icon, copy a preset at the top of the script and change the text, size and height.

Font: Poppins Bold Italic (free, [Google Fonts](https://fonts.google.com/specimen/Poppins)). Put `Poppins-BoldItalic.ttf` next to the script.

`share_images.py` (Pillow + OpenCV) makes `qr.svg` (the QR in the cover's share pop-up), the printable poster `neon_arcade_qr.png` and the link-preview picture `../og.jpg`. Re-run it if the site address changes; it checks that the QR reads back.

`favicon.py` makes the browser-tab / favourites icon (`../favicon.png` 48px and `../favicon-192.png`) from `../icon.png`, with rounded corners. `games/build.py` links both. Re-run it after changing `icon.png`.
