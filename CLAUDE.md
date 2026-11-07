# Neon Arcade '90s

A phone-first pack of neon arcade games (Knucklebones, Othello, Water Sort, Sudoku) hosted on GitHub Pages, with a cover page to pick a game. Players open `index.html`; everything they need is in that one file.

## Layout
- `index.html`: the packed game pack (cover page + all four games). Built, don't hand-edit.
- `icon.png`, `sw.js`, `manifest.json`: home-screen icon, offline support, app manifest.
- `games/`: editable sources: `Knucklebones.html`, `Othello.html`, `Water_Sort.html`, `Sudoku.html` (each a standalone page) and `build.py` (the cover page and the packer).
- `icons/icon_template.py`: generates the 1024×1024 neon app icons (presets per game).

## Making changes
- Game change: edit its file in `games/`. Cover-page change: edit `games/build.py`.
- Rebuild the pack from the repo root:
  `python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html index.html`
- The build only adds the yellow Menu button to each game's bar and wraps the games in the cover. Each game runs in its own iframe, so games never clash.
- After changing `sw.js`, bump `CACHE` (e.g. `neon-arcade-v2`).
- Changes go on a branch with a pull request; `main` is the live site.

## Style rules
- Shared neon look: dark `#07030f` background, magenta `#ff2bd6`, cyan `#19f3ff`, yellow `#ffe94d`, green `#39ff7a`; "Press Start 2P" for labels, "VT323" for text; scanlines.
- Each game has a Rules / Menu / Settings bar at the bottom; Menu is yellow and centred.
- Same button sizes in every game: settings buttons 64px (54px on narrow phones), double-width 134px; action buttons like Undo 6px 10px padding.
- Confirmations use "Tap again".
- Games and the cover stay upright in portrait when a phone is turned sideways (touch screens, short side under 600px).
- Cover cards, top to bottom: Knucklebones green, Othello magenta, Water Sort cyan, Sudoku orange (`#ff9e2c`). Two-line descriptions, a square icon as tall as the text (62px), a player-count flag tab top-right ("1–2P" / "1P").
- The URL never changes (no `#game`), so bookmarks and the home-screen app always open on the cover.

## Testing
Test every change on a small (320px) and a standard phone width before handing it back, including a landscape touch viewport. Play each changed game to the end and check the browser console for errors.
