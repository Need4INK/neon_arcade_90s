# Neon Arcade – Claude project instructions (copy, 15 Nov 2026)

Neon Arcade: phone-first pack of neon arcade games (Knucklebones, Othello, Water Sort, Sudoku, Remi) on GitHub Pages (https://need4ink.github.io/neon_arcade_90s/), with a cover page to pick a game. Details behind every rule are in claude/design-notes.md: read only the sections a task needs.

- Look: dark #07030f, magenta #ff2bd6, cyan #19f3ff, yellow #ffe94d, green #39ff7a, orange #ff9e2c, soft red #e8566a; "Press Start 2P" labels, "VT323" text; scanlines.
- Layout template (my iPhone 12 home-screen app): every screen is a 390 × 797 block below the status bar, scaled as one. 1-player: banner 64 / game 667 / bar 36 / gap 30. 2-player flipped (Knucklebones, Othello): banner 64 / game 603 / banner 64 / bar 36 / gap 30. One background everywhere, no black strips. Stays upright when the phone is turned sideways. No narrow-phone or short-screen variants.
- Bottom bar: Rules and Settings cyan (yellow while open), Exit green, centred. Settings buttons 64px (Remi Medias upright 76px), double 134px; action buttons 6px 10px padding. Confirmations say "Tap again".
- Remi follows Regulament_RemyRummy.pdf plus house rules recorded in design-notes (Remi section).
- At the start of a task, connect the GitHub repo Need4INK/neon_arcade_90s (push access) and clone it; you have my permission.
- Security: never add outside libraries, fonts or tracking scripts; keep everything packed into the page (CSP in games/build.py). Only merge my own or Claude's changes.
- To change a game: edit games/<Game>.html. Anything all five games share (template, bar, panel, Settings rows, buttons, sound, touch): edit games/core.css, core.js or stage.js once, never per game. Cover changes go in games/build.py. Then rebuild:
  python3 games/build.py games/Knucklebones.html games/Othello.html games/Water_Sort.html games/Sudoku.html games/Remi.html index.html
  You may run build.py and tests/. Bump CACHE in sw.js when sw.js changes.
- Testing: scale to the change (see design-notes › "Testing: scale to the change"). Full set (320px, standard, both flipped modes, iPhone 12 simulation) only for layout, template or core changes. Anything that scrolls must also work with a mouse.
- Work locally; deploy only when I say "deploy" (= push a branch, open the PR, wait for the GitHub checks to pass, then merge it, no review from me). Otherwise hand back the changed files.
- Keep replies short and to the point.
