# Tests

Headless-Chrome checks used in the Nov 2026 quality check. Run them from the repo root after rebuilding `index.html`; each prints a short report. Screenshots and pictures go to `tests/out/` (not committed).

Needs Python 3 with `playwright` (and `pillow` for the icon preview). Chrome is taken from `$CHROME`, `/usr/bin/google-chrome`, or Playwright's own Chromium.

| Script | What it checks |
|---|---|
| `harness.py` | Shared helpers: local server, phone sizes (`iphone12`, `small` 320×568, `big` 430×932, `sideways` 844×390, `desk` 1280×800), opening a game, console errors. `iphone12` simulates the user's home-screen app (see its docstring). |
| `layout_compare.py [ref]` | Template positions of every game (and both flipped 2-player modes) at all five sizes, compared with `index.html` at a commit (default `HEAD`). Use it after any change to catch layout shifts. |
| `resume_check.py` | Saved games come back after a reload (Knucklebones also mid-CPU turn, Othello, Water Sort, Sudoku); a finished game adds to the record and starts fresh. |
| `remi_check.py [rounds]` | Remi auto-play at Easy/Norm/Hard with a rule check (all 106 tiles accounted for, every formation valid), then reload after a draw keeps the drawn tile. |
| `install_check.py` | Manifest and Android installability errors (none expected) served from a subfolder like the live site and from the root, then offline opening at `/`, `/index.html`, `?fbclid=x`. |
| `icon_preview.py` | `icon-maskable.png` cut to the common Android launcher shapes (writes `tests/out/android_icon_preview.png`). |

Notes: Water Sort keeps its state inside the page's closure, so deep scripted tests of it need a test-only copy of the game that exposes it (never committed). Real-phone things (iPhone clipping, Android launchers) still need a real device.
