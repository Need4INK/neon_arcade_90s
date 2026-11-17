# Neon Arcade – AI blueprint ("a beautiful brain")

Input for building the CPU opponents and puzzle helpers. Written Nov 15 2026, after reading the current code. Plain-language goals first, then what to build, then how to prove it works. Nothing here is built yet. Your decisions, and the ones still open, are at the end.

## 1. The goal in one line
The CPU should feel like a **fair, readable, believable player** who is fun to beat. Raw strength alone is not the goal: at every level, a win should feel earned and a loss should feel deserved.

## 2. One brain or five?
**Answer: one shared "brain kit" with a separate engine for each game.**
- The **shared kit** goes in `games/core.js`, written once (project rule: anything all games share goes in the core). It covers timing, randomness, the meaning of each level, mistakes, running heavy thinking off the main screen, and test hooks.
- Each **game engine** goes in its own `games/<Game>.html`. It knows that game's rules, how to judge a position, and how far ahead to look.
- There are two kinds of brain:
  - **Opponent brain** (Knucklebones, Othello, Remi) plays against you.
  - **Coach brain** (Sudoku, Water Sort) has no opponent. It helps you get better through hints, being told when you're stuck, and puzzles that suit your skill.

## 3. Experience principles (the rules every brain follows)
1. **Fair, always.**
   - The CPU never sees hidden information: your Remi hand, the pile order, or the next die.
   - Dice and shuffles stay truly random, and luck is never rigged to help or punish anyone.
   - The CPU may remember anything a person at the table could see, such as discards or taken tiles.
2. **Levels mean the same thing in every game.**
   - **Easy:** a beginner wins most games, about 70–80%.
   - **Normal:** a fair fight for a casual player, about 50%.
   - **Hard:** a strong player still has to concentrate and wins 30% or less.
3. **Believable mistakes.** Easy makes human mistakes, like missing a combo or a corner. It never makes absurd moves, like throwing away a winning tile or playing at random. From Normal up, the CPU never makes an obvious blunder.
4. **Consistent character.** A CPU doesn't play brilliantly one turn and foolishly the next. Its mistakes come from a steady "skill level", not coin flips.
5. **Readable.** You can always see what the CPU did and roughly why, through the message line, highlights and Remi's turn summary. Nothing happens off-screen.
6. **Natural pace.**
   - A CPU turn takes about 0.4–1.2 s of visible "thinking", and up to about 1.5 s for a hard decision so it feels weighty. A forced or obvious move is quick.
   - The screen never freezes: heavy thinking runs in a background Worker.
   - Remi's Slow / Normal / Fast setting is respected.
7. **Interruptible.** Exit, Cancel game or reopening the app stops CPU thinking at once, with no late sounds or moves. The existing `gid` and `token` checks show the pattern.
8. **Small and local.**
   - No outside libraries, no network and no tracking: everything is packed into the page, as the CSP requires.
   - All AI combined adds about 40 KB or less to the page.
   - Any learning about the player stays in that phone's `localStorage` and is validated on load like every other save.
9. **Phone-first speed.** Every thinking budget is measured for the iPhone 12 at 4× CPU slow-down, not on a desktop.
10. **Never breaks the rules.** The CPU uses the same move checks as the player, and `referee.py` and `remi_check.py` must stay at 0 violations.

## 3a. Playing like a person (user, Nov 15: "behave as humanly as possible, be sharp, maybe miss sometimes")
The aim is a CPU you could mistake for a good friend across the table: sharp most of the time, sometimes human.
- **Plausible misses.**
  - Mistakes go where people make them. A tile buried deep in the discard row, an add to a formation across a crowded table, a joly swap or a far-off Othello trap is easy to overlook. Missing a plain run in its own hand, or a free corner, is not.
  - How often it misses depends on the level, its adjustment to you (6a) and how busy the moment is: more on a full table, late in a long round, or with many choices at once.
  - Hard misses rarely, and never anything obvious.
- **Imperfect memory.**
  - Easy remembers only the last few discards.
  - Normal remembers most of the round, but older tiles get fuzzy.
  - Hard remembers nearly everything.
  - This is a person's memory, not a recording.
- **Thinking time that matches the moment.**
  - A quick play when the choice is obvious. A longer pause for a hard choice: taking deep from the row, opening, or the last tiles. A short hesitation before a risky discard.
  - Varies a little each time, never the same tick, and always within the speed setting.
- **Reads you, like a person does.**
  - Notices what you take and what you pass on ("you picked up two reds"). Stops feeding you those tiles and plays safe when you're close to closing.
  - Only from what anyone at the table could see.
- **Plays the score.**
  - Riskier when behind in the match, safer when ahead.
  - Near the target: goes for the close, or blocks the leader.
- **Consistent character.** Each CPU keeps its style (6b) all match, so you learn who you're up against, the way you would with real people.
- **Small human touches** (Remi, fair):
  - **Fishing:** sometimes discards a tile next to what it's really collecting, to lure out the tile it needs.
  - **Holding back:** the Sly CPU holds tiles back to hide how close it is to closing.
  - **Mostly takes discards that fit now:** sometimes, like a person, it holds a tile it hopes to use soon.
- **Never inhuman:** no peeking, no instant replies to hard choices, no robotic identical play, no rule-breaking, and no "mistakes" that look like a bug.

### Remi discard-taking (found Nov 15)
- **Today:** CPUs take only the *last* discard, only after opening, and only when it makes a new formation at once. So they almost never take. The user takes a lot.
- **Target (Normal+):**
  - Take tiles further back in the row when the whole set taken pays off: tiles that will be laid, minus the risk of the extra tiles left in hand.
  - Take a tile that completes a formation that turn, including one built with other tiles taken from the row.
  - Bold takes eagerly, Cautious rarely, Sly when it hides its plans well.
  - Easy sometimes overlooks a good take, more often the deeper in the row it is.

## 4. The shared brain kit (`core.js`)
| Piece | What it does |
|---|---|
| `naRng(seed)` | A random generator that can be seeded, so tests repeat exactly; in normal play it is seeded from the clock. |
| `naThink(fn, {min, max, token})` | Runs a CPU decision with a minimum visible delay and a hard time cap. It cancels the decision if the game changes. |
| `naSearch` helper | Looks ahead a bit deeper each round until the time runs out, then keeps the best fully finished answer. Othello already does a simple version of this. |
| `naWorker(code)` | Runs heavy search in a background Worker created from a `blob:` URL, which the CSP already allows for Water Sort. If that fails, it runs on the main thread. |
| `naChoose(moves, level)` | The single **mistake model**. Each move gets a score, and the CPU picks with "softmax" randomness: each level has a *temperature* (how loosely it picks among good moves) and a *blind spot* rate (chance of missing the best move). There are no pure random moves. |
| `naLevel` table | The knobs for each game and level (section 6), in one place for easy tuning. |
| `naAdapt(game, level)` | Adjusts how well the CPU plays to your recent results (section 6a). It changes only the CPU's own decisions, never dice or tiles. |
| Test hooks | `window.__ai` exposes seed, level, adjustment and "pick for this state" so tests can run bot-vs-bot tournaments; tests can switch the adjustment off. |

## 5. Each game: today → target

### Knucklebones (dice, luck + tactics)
- **Today:**
  - Easy plays a random column 60% of the time.
  - Normal scores each column by points, how many of your dice it knocks out, and the risk you hit back.
  - Hard looks 3 dice ahead (expectimax).
- **Target:**
  - Easy should stop playing at random. Use the column scoring with a high temperature, so it makes mistakes like greedy stacking or ignoring attacks.
  - Hard should look deeper, cutting off unpromising lines to stay within the time budget.
  - Hard should know when the game ends. It ends when a board fills, so near the end the race to fill a board matters more than points.
  - Hard should protect stacked x2/x3 columns its opponent can still attack.
  - Optional: deny you a column by completing a row.
- **Why it matters:** with dice luck, "fair but sharp" is the whole feel. Easy should look like a person, not a coin flip.

### Othello (perfect information, deep strategy)
- **Today:**
  - Easy is **fully random**: its weakest point, since it looks broken rather than easy.
  - Normal looks 2 moves ahead, Hard 4, and up to 8 in the last 10 empty squares.
  - It judges positions with a fixed square-weight table plus mobility (how many moves each side has).
- **Target:**
  - Easy looks 1 move ahead with a high temperature. It grabs discs greedily and sometimes gives away corners, like a real beginner.
  - Normal looks about 3 moves ahead and knows corners, edges and mobility.
  - Hard judges positions differently in the opening, middle and end of the game. It weighs mobility, frontier discs (next to empty squares), stable discs (that can't be flipped again), corners and parity (who gets the last move in each region).
  - Hard looks ahead deeper each round within a 700 ms budget, in a Worker.
  - Hard plays perfectly in the last 12–14 empty squares.
  - Hard uses a tiny built-in opening book (a few dozen self-made lines, no outside data).
- **Why it matters:** this is the game where a strong AI is most visible, and the cheapest one to make excellent.

### Remi (hidden information, 3 CPUs, long rounds)
- **Today:** good rule-based play.
  - Opening uses `openFor`.
  - Takes only usable discards (`cpuWants`) and adds to formations.
  - Discards by how well a tile connects with its hand.
  - Easy picks among its 3 weakest tiles to discard.
  - Hard swaps jolys and avoids feeding the table.
  - CPUs **don't remember** what has been played and don't read their opponents.
- **Target** (biggest upgrade, three steps):
  1. **Memory (Normal+).** Track every visible tile: the discard row, tiles taken, and formations on the table.
     - Know which tiles are "dead", because both copies have been seen.
     - Don't build towards dead runs or sets.
     - Know how many jolys and 1s are still out.
  2. **Reading opponents (Hard).** From what each player takes and refuses, guess what they're collecting.
     - Never discard a tile the *next* player probably wants.
     - When someone is down to 3 tiles or fewer, switch to defence: dump high tiles and 1s that would cost 25, and keep the hand cheap.
  3. **Timing (Hard).**
     - Decide when to open: early to start adding, or hold to build a bigger opening and keep information hidden.
     - Decide when to lay down versus keep tiles for a big close.
     - Chase a close with a 1 or joly for the double bonus when it's realistic.
     - Weigh the atu bonus.
     - Choose between the board game and normal play using expected points, not just "5+ doubles".
- **How Hard thinks** (optional last step):
  - For key choices, like which tile to discard or whether to take, it imagines the hidden hands many times. Each guess must match everything seen, and the CPU plays out a few turns of each with quick rules and picks the most robust choice.
  - This uses only legal information, so it stays fair.
  - It runs in a Worker within the speed setting's delay.
- **Personality (decided):** see section 6b.

### Sudoku (coach brain)
- **Today:** puzzles graded by solving technique. Hint fills in the correct number.
- **Target:**
  - **Teaching hint, in two taps.** Tap 1 points: "Look at this box: only one cell can take a 7." Tap 2 fills the number. It uses the solving technique the grader already knows.
  - **Mistake watch** (optional): when a wrong number makes the puzzle unsolvable, a gentle nudge.
  - **Level suggestion** after a few solves: "You're ready for Hard."

### Water Sort (coach brain)
- **Today:** puzzles are generated ahead of time. There are Undo and Shuffle, and no hint.
- **Target:**
  - A solver finds the shortest path from the current position.
  - **Hint** shows the next pour, as an optional setting like Sudoku's.
  - **Stuck alert:** "No way out from here: Undo 3 moves", when the solver finds no solution.
  - The guarantee that every puzzle can be solved is proven by the same solver.

## 6. Level knobs (starting values, tuned by tournaments)
| Game | Easy | Normal | Hard |
|---|---|---|---|
| Knucklebones | Column scoring, temperature high | Column scoring + risk, temperature low | Looks 3–4 dice ahead, endgame race, temperature ≈ 0 |
| Othello | 1 move ahead, temperature high, blind to corners 30% | 3 moves ahead, full judgement, temperature low | Looks deeper until 700 ms, perfect endgame, opening book |
| Remi | Today's Easy + no memory, 1 in 4 good takes missed | Memory, safe discards | Memory + opponent reading + timing (+ imagined hands) |

## 6a. Adjusting to the player (decided Nov 15)
- **The rule:** the CPU adjusts to your results as part of each level, not as a separate setting.
  - **Easy** adjusts the most.
  - **Normal** adjusts a little.
  - **Hard** never adjusts.
- **How it adjusts:**
  - It looks at your last ~5 results against the CPU at that level, in that game.
  - Winning a lot makes the CPU sharper: lower temperature, fewer blind spots, Remi memory switched on.
  - Losing a lot makes it gentler.
  - It changes a little after each game, never in the middle of one.
- **Limits:**
  - Easy at its sharpest stays a bit weaker than plain Normal, and Normal at its sharpest stays a bit weaker than Hard. Levels never overlap.
  - Easy moves across its whole range; Normal only about a third of the way.
- **Never through luck:** dice, shuffles and puzzles stay untouched. Only the CPU's own choices change.
- **Saved per game and level** in `localStorage` (for example `kb-adapt`, `oth-adapt`, `remi-adapt`). Validated on load like other saves; a damaged value means no adjustment.
- **Not shown in the UI:** no new rows or buttons. The records stay per level, as now.
- **Puzzles (coach brain):** no hidden adjustment. Only the optional level *suggestion* after a few solves.

## 6b. Remi personalities (decided Nov 15)
Each of the three CPUs plays the same level with its own style, so the table feels alive. Each style is a small set of weights on top of the level, so the CPU's strength stays the same; only how it plays changes.

| CPU | Colour | Style | How it shows |
|---|---|---|---|
| CPU 1 | red | **Cautious** | Opens only with a solid hand. Keeps its hand cheap. Turns defensive early when someone has few tiles left. Rarely takes discards. |
| CPU 2 | yellow | **Bold** | Opens as early as allowed, takes discards eagerly, adds to formations a lot. Chases the atu and the board game. |
| CPU 3 | blue | **Sly** | Holds its tiles to hide its plans, then lays a lot at once. Goes for closing with a 1 or joly. Steers away from feeding the next player. |

- Every style follows the same rules, has the same fairness, and plays at the same level.
- Tournaments check that no style wins clearly more than the others (each within about ±5% of a third of the wins).
- The Rules don't mention the styles (decided Nov 16): players feel the difference.

## 7. How we prove it's good (acceptance tests)
- **Tournaments** (new `tests/ai_tournament.py`, building on `referee.py`), with fixed seeds:
  - Hard beats Normal at least 75% of the time, and Normal beats Easy at least 75%.
  - Every level beats a random player at least 95% of the time.
  - Remi: Hard CPUs average more points per round than Normal at the same table.
- **Zero illegal moves** in `referee.py` and `remi_check.py`.
- **Speed:** on the iPhone 12 at 4× CPU slow-down, 95% of CPU turns finish within the level's budget, and the main thread is never blocked more than 50 ms. Measured for every level.
- **Fairness check:** a test proves the CPU's decision code can't read hidden state. Remi engines get a "view" object holding only public information plus their own hand.
- **Believability check (you, on the phone):** play 5 games per level and answer:
  - Did Easy ever look stupid rather than beginner-ish?
  - Did Hard ever feel like it cheated?
  - Was the pace OK?
  - Did you understand what the CPU did?
- No drop in the existing checks (`layout_compare`, `core_check`, `resume_check`, `exit_check`).

## 8. Build order
1. **Measure first:** a tournament harness and baseline numbers for today's AIs.
2. **Shared kit in `core.js`:** seeded randomness, thinking timer, Worker runner, mistake model.
3. **Othello:** a fix for the random Easy plus a strong Hard. Quickest visible win.
4. **Knucklebones:** a human-like Easy and an endgame-aware Hard.
5. **Remi:** memory → reading opponents → timing → (imagined hands). One PR per step, each checked by `remi_check.py` and tournaments.
6. **Coaches:** Water Sort solver + hint + stuck alert, then Sudoku teaching hints.
7. **Adjusting to the player** (section 6a) across the three opponent games, once each level's base is tuned. Remi personalities come with step 5.
8. **Optional extras:** level suggestions in the puzzles.

## 9. Decisions
**Made (Nov 15):**
1. **Levels:** keep three (Easy / Normal / Hard), so the UI doesn't change. Hard gets stronger instead.
2. **Adjusting to the player:** part of each level. Easy adjusts the most, Normal a little, Hard not at all (section 6a).
3. **Remi:** the three CPUs get distinct personalities (section 6b).
6. **Records:** the improved AIs keep the "Won vs CPU" records; no reset.
7. **Remi personalities in the Rules** (Nov 16): not mentioned; players just feel the difference.
4. **CPU "voice"** (Nov 16): factual, as now. No flavour lines in the message line; the human feel comes from the play and the pace.

5. **Hints in Water Sort** (Nov 17): yes, off by default like Sudoku's.
