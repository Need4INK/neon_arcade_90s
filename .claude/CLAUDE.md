# Neon Arcade '90s

A phone-first pack of neon arcade games (Knucklebones, Othello, Water Sort, Sudoku, Remi) hosted on GitHub Pages, with a cover page to pick a game. Players open `index.html`; everything they need is in that one file.

## Layout
- `index.html`: the packed game pack (cover page + all five games). Built, don't hand-edit.
- `icon.png` (512px), `icon-maskable.png`, `sw.js`, `manifest.json`: home-screen icon (iPhone and default), Android icon (any launcher shape), offline support, app manifest (`start_url`/`scope` `./`, needed for Chrome to treat the site as an installable app).
- `favicon.png` (48px), `favicon-192.png`: browser-tab / favourites icon for desktop, made from `icon.png` by `icons/favicon.py`.
- `games/`: editable sources.
  - `Knucklebones.html`, `Othello.html`, `Water_Sort.html`, `Sudoku.html`, `Remi.html`: each holds only what is its own (play area, rules text, sounds, game logic). They no longer work opened on their own.
  - Shared by all five, put into each game by the build: `core.css` (page, the 390 × 797 template, bar, Rules/Settings panel and rows, action buttons, touch and hover), `stage.js` (scales and turns the template to fit the screen), `core.js` (sound, the panel, switches, "Tap again", Exit, Sound/Scanlines shared between games).
  - `build.py`: the cover page and the packer.
- `.github/workflows/checks.yml`: on every pull request GitHub rebuilds the page and runs `build_check`, `layout_compare`, `exit_check`, `core_check`, `resume_check`, `install_check`.
- `icons/icon_template.py`: generates the 1024×1024 neon app icons (presets per game).
- `icons/share_images.py`: makes `icons/qr.svg` (embedded in the share pop-up), the QR poster `icons/neon_arcade_qr.png` and the link-preview picture `og.jpg`.
- Design notes with the reasons behind every decision live in the claude.ai project (`claude/design-notes.md`).

## Making changes
- Game change: edit its file in `games/`. Something every game has (bar, panel, Settings rows, buttons, sound, template): edit `games/core.css` / `core.js` / `stage.js` once, never per game. Cover-page change: edit `games/build.py`.
- A game's styles come after `core.css`, so a game only writes a rule where it differs from the core (each file ends with a short "differs from the shared core" block). In its script a game sets `naSfx` (its sounds) and `naSync` (the function that refreshes its Settings rows), and uses the core's `sfx`, `tone`, `showPanel`, `setSw`, `naArm`/`naDisarm` ("Tap again"), `naFirstRules`.
- Rebuild the pack from the repo root:
  `python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html games/Remi.html index.html`
- The build puts the shared core into each game, packs the fonts and the QR code, and wraps the games in the cover. Each game runs in its own iframe, so games never clash. Two builds of the same sources give the same bytes.
- After changing `sw.js`, bump `CACHE` (now `neon-arcade-v2`, so next `neon-arcade-v3`). Game-only changes need no bump: the page is re-checked on every load.
- Fonts: `games/fonts/` holds `PressStart2P-Regular.ttf` and `VT323-Regular.ttf` (SIL Open Font License; the licence texts are `OFL-PressStart2P.txt` and `OFL-VT323.txt` next to them); the build packs them into `index.html` (subset to the characters used, licence kept), so the games never need Google Fonts.
- Changes go on a branch with a pull request; `main` is the live site.
- Work and test locally; push nothing to GitHub until the user says "deploy". On "deploy": push the branch, open the pull request, wait for the `checks` run on it to pass, then merge it (the user doesn't need to confirm it on GitHub). If a check fails, fix it first; don't merge around it.

## Style rules
- Shared neon look: dark `#07030f` background, magenta `#ff2bd6`, cyan `#19f3ff`, yellow `#ffe94d`, green `#39ff7a`, orange `#ff9e2c`, soft red `#e8566a`; "Press Start 2P" for labels, "VT323" for text; scanlines. British spelling ("colour", "cancelled"); the computer player is called "CPU".
- Template (iPhone 12 reference): every screen is a 390 × 797 block below the status bar, scaled as one to fit the phone (other screen shapes get plain background around it). 1-player: banner 64 (title centred) / game area 667 (game centred; Knucklebones' boards and Remi's table grow) / bar 36 (Rules / Exit / Settings, buttons flush with its bottom edge) / gap 30. 2-player flipped: banner 64 / game area 603 / banner 64 (second title) / bar 36 / gap 30. Exit is green and centred; an open Rules/Settings button turns yellow. The Rules/Settings panel opens right above the bar.
- One background in every game, painted on the html, fading in from `#07030f` at the top so it blends with the status bar.
- iPhone home-screen icons with a see-through status bar report a page 47pt shorter than the screen (797 of 844), or the full 844 once laid out full height; the cover treats both as full screen and lays the cover and games out in the page (not the fixed layer) so they reach the bottom. iOS updates the insets late after a rotation, so the cover re-checks several times after rotating and when the app returns to the foreground. Android and other browsers skip this and use the normal layout.
- Tap the cover title for the share pop-up: QR code, home-screen steps (iPhone / Android), Copy link.
- Same button sizes in every game: settings buttons 64px, double-width 134px; action buttons like Undo 6px 10px padding. Exception: Remi's Medias skin in Portrait uses 76px so "Landscape" fits. No narrow-phone or short-screen variants: every screen is the same 390 x 797 block, only scaled.
- Confirmations use "Tap again".
- Sound and Scanlines: set in any game and all five follow while the app is open (kept on the cover: `naShared`, `naShare`; `naSet` in `core.js`); never saved, so both reset when the app opens. A game that isn't on screen makes no sound (`naHid`). Turning Sound on unlocks audio the iPhone way in every game (plays with the ringer off; a silent loop for older iPhones); a game that got Sound from another game unlocks at its first tap.
- Same touch behaviour everywhere (`core.css`, and the cover): no double-tap zoom, text selection, long-press menu or grey tap flash. Mouse users get a hover glow on buttons and cover cards (never on touch screens).
- Settings end with the red button (Cancel game / New game), then the notes. Levels are "Easy / Normal / Hard" in every game. The message line sits under the play area.
- Remi has a second look, the **Medias** skin (Settings › Skin: Neon / Medias; not saved: Remi always opens in Neon, and leaving Remi switches back to Neon): a green tabletop with ivory tiles like a real set. Only the look changes (same rules, 2 jolys, same template sizes); all its CSS is scoped to `html.sk-m`, it has no scanlines or Accessibility marks, and rules text that differs per skin uses `.sn` (Neon only) / `.sm` (Medias only).
- Remi with a mouse (`mouseScroll` in `Remi.html`): the wheel slides the discard row and a wide Landscape rack sideways, and the table, discard row and rack can be dragged when they hold more than fits (grab cursor); a drag never counts as a tap. Touch screens scroll as before. Check with `tests/mouse_scroll_check.py`.
- Colour-blind help is an optional **Accessibility** switch in Settings (off by default, saved): Water Sort puts a shape on every liquid colour (`.sy.s0`–`.sy.s8`), Remi a mark bottom-left on every tile (clear of the atu-twin dot top-right; the doubles bar sits above it) (red one bar, yellow two, blue three, white none); Sudoku a bar under the numbers you entered (saved as `sdk-sym`). Check colour changes with `tests/colour_blind_check.py`.
- Games and the cover stay upright in portrait when a phone is turned sideways (touch screens, short side under 600px).
- Cover cards, top to bottom: Knucklebones green, Othello magenta, Water Sort cyan, Sudoku orange (`#ff9e2c`), Remi soft red (`#e8566a`). Two-line descriptions, a square icon as tall as the text (62px), a player-count flag tab top-right ("1–2P" / "1P").
- The URL never changes (no `#game`), so bookmarks and the home-screen app always open on the cover.

## Testing
Test every change on a small (320px) and a standard phone width before handing it back, including a landscape touch viewport and the 2-player flipped modes. Play each changed game to the end and check the browser console for errors.
To simulate the user's iPhone 12 home-screen app in headless Chrome: viewport 390×797, screen 390×844, `window.__SAFE={t:47,b:34,l:0,r:0}` on the cover (init script, top window only), and inject `.bar{padding-bottom:34px}` into each game. Real-phone clipping can't be reproduced; try layout ideas on the test page first (https://github.com/Need4INK/iPhone12_screen_test) and ask for a screenshot after deploying.
Clean-ups that must not change the look: `tests/style_snapshot.py` (save a snapshot before, one after, compare: every element's position and styles on every screen at six sizes). Ready-made checks live in `tests/` (see `tests/README.md`): `build_check.py` (index.html is a fresh build), `device_sweep.py` (36 screen sizes), `layout_compare.py` (template positions vs the last commit, all sizes and flipped modes), `resume_check.py`, `remi_check.py` (rule check auto-play), `install_check.py` (Android installability and offline), `icon_preview.py`. Deep checks (run after bigger changes): `save_fuzz.py` (damaged saved data), `referee.py` and `puzzle_check.py` (independent rule and puzzle checks), `monkey.py` (random fast taps and reloads), `exit_check.py`, `a11y_check.py`, `colour_blind_check.py`. Run them from the repo root after rebuilding.
- Saved data is never trusted: each game checks a saved game before using it and starts fresh if it is damaged; keep that when adding saved fields.
