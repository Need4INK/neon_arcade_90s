# App icons

`icon_template.py` makes the 1024×1024 neon icons (iOS-safe, nothing important near the corners).

```
pip install pillow
python3 icon_template.py              # all presets
python3 icon_template.py othello      # one preset
```

Presets: `neon_arcade`, `othello`, `knucklebones`, `water_sort`, `sudoku`, `remi`. For a new icon, copy a preset at the top of the script and change the text, size and height.

Font: Poppins Bold Italic (free, [Google Fonts](https://fonts.google.com/specimen/Poppins)). Put `Poppins-BoldItalic.ttf` next to the script.

`share_images.py` (Pillow + OpenCV) makes `qr.svg` (the QR in the cover's share pop-up), the printable poster `neon_arcade_qr.png` and the link-preview picture `../og.jpg`. Re-run it if the site address changes; it checks that the QR reads back.
