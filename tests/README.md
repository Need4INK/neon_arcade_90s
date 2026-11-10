# Tests

Headless-Chrome checks used in the Nov 2026 quality check. Run them from the repo root after rebuilding `index.html`; each prints a short report. Screenshots and pictures go to `tests/out/` (not committed).

Needs Python 3 with `playwright` (and `pillow` for the icon preview). Chrome is taken from `$CHROME`, `/usr/bin/google-chrome`, or Playwright's own Chromium.

| Script | What it checks |
|---|---|
| `harness.py` | Shared helpers: local server, phone sizes (`iphone12`, `small` 320×568, `big` 430×932, `sideways` 844×390, `desk` 1280×800), opening a game, console errors. `iphone12` simulates the user's home-screen app (see its docstring). |
| `layout_compare.py [ref]` | Template positions of every game (and both flipped 2-player modes) at all five sizes, compared with `index.html` at a commit (default `HEAD`). Use it after any change to catch layout shifts. |
| `resume_check.py` | Saved games come back after a reload (Knucklebones also mid-CPU turn, Othello, Water Sort, Sudoku); a finished game adds to the record and starts fresh. |
| `remi_check.py [rounds]` | Remi auto-play at Easy/Norm/Hard with a rule check (all 106 tiles accounted for, every formation valid, no CPU takes a discard before opening, every CPU opening has 45+ with a run and a set or is a set of 1s), then reload after a draw keeps the drawn tile, and an empty pile is refilled from the discards. |
| `install_check.py` | Manifest and Android installability errors (none expected) served from a subfolder like the live site and from the root, then offline opening at `/`, `/index.html`, `?fbclid=x`. |
| `icon_preview.py` | `icon-maskable.png` cut to the common Android launcher shapes (writes `tests/out/android_icon_preview.png`). |
| `colour_blind_check.py` | How far apart the colours that carry meaning stay under the three kinds of colour blindness (Water Sort liquids, Remi tile colours, Othello discs). Needs `numpy` and `scikit-image`. |
| `a11y_check.py` | Text contrast and tap-target sizes on the cover and every game (game, Rules, Settings), plus colour-blind screenshots of Water Sort and Remi in `tests/out/`. Dimmed (switched-off) buttons are listed too; those are expected. |
| `save_fuzz.py game port` | Damaged saved data: each saved value garbled, cut, or with fields deleted / of the wrong type, and storage blocked. The game must still open and play. |
| `referee.py oth\|kb [games]` | Auto-played Othello and Knucklebones games checked move by move against an independent copy of the rules. |
| `puzzle_check.py sdk\|ws` | Sudoku puzzles have exactly one solution (independent solver) and play through; Water Sort levels are solved by a separate solver and played by tapping with Accessibility on. |
| `monkey.py game port seed [x] [rounds]` | Random fast taps, double taps and reloads, then consistency and stuck-CPU checks. Run one or two at a time (many at once time out). |
| `exit_check.py` | Several instant taps on Exit or on a card never leave the arcade or need a second Exit. |

Notes: Water Sort keeps its state inside the page's closure, so deep scripted tests of it need a test-only copy of the game that exposes it (never committed). Real-phone things (iPhone clipping, Android launchers) still need a real device.
