Editable sources of the five games (each a standalone page) and `build.py` (the cover page and the packer).

Rebuild the published pack from the repo root after any change:

```
python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html games/Remi.html index.html
```

`fonts/` holds the two fonts (SIL Open Font License, licence texts `OFL-PressStart2P.txt` and `OFL-VT323.txt`) that the build packs into `index.html`.
