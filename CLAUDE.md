# Neon Arcade '90s

A phone-first pack of neon arcade games (Knucklebones, Othello, Water Sort, Sudoku, Remi) hosted on GitHub Pages, with a cover page to pick a game. Players open `index.html`; everything they need is in that one file.

## Layout
- `index.html`: the packed game pack (cover page + all five games). Built, don't hand-edit.
- `icon.png`, `sw.js`, `manifest.json`: home-screen icon, offline support, app manifest.
- `games/`: editable sources: `Knucklebones.html`, `Othello.html`, `Water_Sort.html`, `Sudoku.html`, `Remi.html` (each a standalone page) and `build.py` (the cover page and the packer).
- `icons/icon_template.py`: generates the 1024×1024 neon app icons (presets per game).
- `icons/share_images.py`: makes `icons/qr.svg` (embedded in the share pop-up), the QR poster `icons/neon_arcade_qr.png` and the link-preview picture `og.jpg`.
- Design notes with the reasons behind every decision live in the claude.ai project (`claude/design-notes.md`).

## Making changes
- Game change: edit its file in `games/`. Cover-page change: edit `games/build.py`.
- Rebuild the pack from the repo root:
  `python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html games/Remi.html index.html`
- The build adds the green Exit button to each game's bar, injects the stage (scaled layout) into each game, packs the fonts and the QR code, and wraps the games in the cover. Each game runs in its own iframe, so games never clash.
- After changing `sw.js`, bump `CACHE` (e.g. `neon-arcade-v2`).
- Fonts: `games/fonts/` holds `PressStart2P-Regular.ttf` and `VT323-Regular.ttf` (SIL Open Font License); the build packs them into `index.html` (subset to the characters used, licence kept), so the games never need Google Fonts.
- Changes go on a branch with a pull request; `main` is the live site.
- Work and test locally; push nothing to GitHub until the user says "deploy". On "deploy": push the branch, open the pull request and merge it (the user doesn't need to confirm it on GitHub).

## Style rules
- Shared neon look: dark `#07030f` background, magenta `#ff2bd6`, cyan `#19f3ff`, yellow `#ffe94d`, green `#39ff7a`; "Press Start 2P" for labels, "VT323" for text; scanlines.
- Template (iPhone 12 reference): every screen is a 390 × 797 block below the status bar, scaled as one to fit the phone (other screen shapes get plain background around it). 1-player: banner 64 (title centred) / game area 667 (game centred; Knucklebones' boards and Remi's table grow) / bar 36 (Rules / Exit / Settings, buttons flush with its bottom edge) / gap 30. 2-player flipped: banner 64 / game area 603 / banner 64 (second title) / bar 36 / gap 30. Exit is green and centred; an open Rules/Settings button turns yellow. The Rules/Settings panel opens right above the bar.
- One background in every game, painted on the html, fading in from `#07030f` at the top so it blends with the status bar.
- iPhone home-screen icons with a see-through status bar report a page 47pt shorter than the screen; the cover detects it and lays the cover and games out in the page (not the fixed layer) so they reach the bottom.
- Tap the cover title for the share pop-up: QR code, home-screen steps (iPhone / Android), Copy link.
- Same button sizes in every game: settings buttons 64px (54px on narrow phones), double-width 134px; action buttons like Undo 6px 10px padding.
- Confirmations use "Tap again".
- Games and the cover stay upright in portrait when a phone is turned sideways (touch screens, short side under 600px).
- Cover cards, top to bottom: Knucklebones green, Othello magenta, Water Sort cyan, Sudoku orange (`#ff9e2c`), Remi soft red (`#e8566a`). Two-line descriptions, a square icon as tall as the text (62px), a player-count flag tab top-right ("1–2P" / "1P").
- The URL never changes (no `#game`), so bookmarks and the home-screen app always open on the cover.

## Testing
Test every change on a small (320px) and a standard phone width before handing it back, including a landscape touch viewport and the 2-player flipped modes. Play each changed game to the end and check the browser console for errors.
To simulate the user's iPhone 12 home-screen app in headless Chrome: viewport 390×797, screen 390×844, `window.__SAFE={t:47,b:34,l:0,r:0}` on the cover (init script, top window only), and inject `.bar{padding-bottom:34px}` into each game. Real-phone clipping can't be reproduced; ask for a screenshot after deploying.
