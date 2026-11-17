# Neon Arcade – AI blueprint ("a beautiful brain")

The goals, principles and targets behind the CPU opponents and puzzle helpers (written Nov 15 2026, built Nov 15–17). How it is built and the measured numbers: `claude/design-notes.md` › CPU brain. Tuning from real play: `claude/ai-tuning-prompt.md`.

## 1. The goal in one line
The CPU should feel like a **fair, readable, believable player** who is fun to beat. Raw strength alone is not the goal: at every level, a win should feel earned and a loss should feel deserved.

## 2. One brain kit, one engine per game
- The **shared kit** lives in `games/core.js` (timing, randomness, the meaning of each level, mistakes, Workers, test hooks).
- Each **game engine** lives in its own `games/<Game>.html`: that game's rules, how to judge a position, how far ahead to look.
- **Opponent brain** (Knucklebones, Othello, Remi) plays against you. **Coach brain** (Sudoku, Water Sort) helps you get better through hints and being told when you're stuck.

## 3. Experience principles
1. **Fair, always.** The CPU never sees hidden information (your Remi hand, the pile order, the next die). Dice and shuffles stay truly random; luck is never rigged. The CPU may remember anything a person at the table could see.
2. **Levels mean the same thing in every game.** Easy: a beginner wins most games, about 70–80%. Normal: a fair fight for a casual player, about 50%. Hard: a strong player has to concentrate and wins 30% or less.
3. **Believable mistakes.** Easy makes human mistakes (missing a combo or a corner), never absurd ones (throwing away a winning tile, playing at random). From Normal up, no obvious blunders.
4. **Consistent character.** Mistakes come from a steady skill level, not coin flips.
5. **Readable.** You can always see what the CPU did and roughly why (message line, highlights, Remi's turn summary).
6. **Natural pace.** About 0.4–1.2 s of visible thinking, up to about 1.5 s for a hard decision; forced or obvious moves are quick. The screen never freezes (heavy thinking in a Worker). Remi's Slow / Normal / Fast is respected.
7. **Interruptible.** Exit, Cancel game or reopening stops CPU thinking at once, with no late sounds or moves.
8. **Small and local.** No outside libraries, network or tracking. Learning about the player stays in that phone's `localStorage` and is validated on load.
9. **Phone-first speed.** Budgets are measured for the iPhone 12 at 4× CPU slow-down.
10. **Never breaks the rules.** Same move checks as the player; `referee.py` and `remi_check.py` stay at 0 violations.

## 3a. Playing like a person (user: "behave as humanly as possible, be sharp, maybe miss sometimes")
A CPU you could mistake for a good friend across the table: sharp most of the time, sometimes human.
- **Plausible misses** where people make them: a tile deep in the discard row, an add across a crowded table, a joly swap, a far-off Othello trap. Never a plain run in its own hand or a free corner. More on a busy table; Hard rarely, never anything obvious.
- **Imperfect memory.** Easy remembers the last few discards, Normal most of the round with older tiles fuzzy, Hard nearly everything.
- **Thinking time that matches the moment**, varying a little each time, within the speed setting.
- **Reads you** from what anyone could see: what you take and pass on; plays safe when you're close to closing.
- **Plays the score.** Riskier when behind, safer when ahead; near the target goes for the close or blocks the leader.
- **Small human touches** (Remi): fishing (discarding next to what it collects), holding back (Sly), mostly taking discards that fit now.
- **Remi discard-taking:** takes further back in the row when the whole set taken pays off; Bold eagerly, Cautious rarely, Sly when it hides its plans; Easy sometimes overlooks a good take, more often the deeper it is.
- **Never inhuman:** no peeking, no instant replies to hard choices, no robotic identical play, no "mistakes" that look like a bug.

## 4. Targets per game
- **Knucklebones:** Easy like a person (greedy stacking, forgetting to attack), not a coin flip; Hard looks deeper and knows the game ends when a board fills.
- **Othello:** Easy one move ahead and loose (gives away corners); Normal about 3 ahead with corners, edges and mobility; Hard judges by phase, searches within 700 ms in a Worker, plays the last 12–14 empties perfectly, small self-made opening book.
- **Remi:** memory of everything visible (dead tiles, jolys and 1s still out); Hard reads opponents, defends when someone is close, times its opening and close, weighs the atu and the board game by expected points, and imagines the hidden hands (only from legal information) for key choices, in a Worker within the speed setting's delay.
- **Sudoku coach:** a teaching hint in two taps; a gentle nudge when a number makes the puzzle unsolvable; a level suggestion after a few solves.
- **Water Sort coach:** a solver for the shortest way on; an optional Hint; a stuck alert ("No way out from here: Undo 3 moves").

## 5. Adjusting to the player (decided Nov 15)
- Part of each level, not a setting: Easy adjusts the most, Normal a little (about a third of the way), Hard never.
- Looks at your last ~5 results at that level in that game; winning makes it sharper, losing gentler; changes after each game, never during one.
- Levels never overlap: Easy at its sharpest stays below plain Normal, Normal at its sharpest below Hard.
- Never through luck: dice, shuffles and puzzles untouched. Saved per game (`kb-adapt`, `oth-adapt`, `remi-adapt`), validated on load. No UI. Puzzles get no hidden adjustment, only the optional level suggestion.

## 6. Remi personalities (decided Nov 15)
Each CPU plays the same level with its own style; strength stays the same, only how it plays changes.

| CPU | Colour | Style | How it shows |
|---|---|---|---|
| CPU 1 | red | **Cautious** | Opens only with a solid hand. Keeps its hand cheap. Turns defensive early. Rarely takes discards. |
| CPU 2 | yellow | **Bold** | Opens as early as allowed, takes discards eagerly, adds a lot. Goes for the board game. |
| CPU 3 | blue | **Sly** | Holds tiles to hide its plans, then lays a lot at once. Goes for closing with a 1 or joly. Steers away from feeding the next player. |

No style wins clearly more than the others (each within about ±5 points of a third of the wins). The Rules don't mention the styles.

## 7. Acceptance tests
- **Tournaments** (`tests/ai_tournament.py`, fixed seeds): Hard beats Normal and Normal beats Easy at least 75%; every level beats a random player at least 95% (Knucklebones can't: the dice decide too much; its realistic targets are in the design notes). Remi: Hard averages more points per round than Normal at the same table.
- **Zero illegal moves** in `referee.py` and `remi_check.py`.
- **Speed:** on the iPhone 12 at 4× slow-down, 95% of CPU turns within the level's budget; the main thread never blocked more than 50 ms.
- **Fairness:** `remi_fair.py` proves the Remi decision code can't read hidden state.
- **Believability (the user, on the phone):** 5 games per level: Did Easy ever look stupid rather than beginner-ish? Did Hard ever feel like it cheated? Was the pace OK? Did you understand what the CPU did?
- No drop in the existing checks (`layout_compare`, `core_check`, `resume_check`, `exit_check`).

## 8. Decisions (user)
1. Three levels (Easy / Normal / Hard); Hard got stronger instead of adding a level.
2. Adjusting to the player is part of each level (section 5).
3. Remi CPUs have distinct personalities (section 6), not mentioned in the Rules.
4. CPU "voice": factual, as before; the human feel comes from the play and the pace.
5. Water Sort Hint: yes, off by default like Sudoku's.
6. Records: the "Won vs CPU" records were kept, no reset.
