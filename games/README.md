Editable sources of the five games and `build.py` (the cover page and the packer).

A game file holds only what is its own (play area, rules, sounds, saved data). What all five share is kept once and put into each game by the build, so a game file does not work when opened on its own:

- `core.css`: the page, the 390 × 797 template, the bottom bar, the Rules/Settings panel and its rows, action buttons, touch and hover behaviour.
- `stage.js`: scales the template to the screen (and keeps it upright on a sideways phone).
- `core.js`: sound, the panel, switches, "Tap again", Exit, Sound/Scanlines shared between games.

Rebuild the published pack from the repo root after any change:

```
python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html games/Remi.html index.html
```

`fonts/` holds the two fonts (SIL Open Font License, licence texts `OFL-PressStart2P.txt` and `OFL-VT323.txt`) that the build packs into `index.html`.
