# Neon Arcade – AI build plan

How to build `claude/ai-blueprint.md`, one step per chat. Written Nov 15 2026.

## How to use it
1. Open a **new chat in this project**.
2. Set the **model** and **effort** listed for the step.
3. Paste the step's **prompt**. Answer any questions it asks.
4. When it hands back, test on your phone (what to look for is listed in each step).
5. Say **"deploy"**. The chat ships it and marks the step done below.
6. Not sure where you are? In any chat (Opus 5.5, low effort) ask: **"What's my next AI build step?"** It reads this plan and tells you.

**Model choice:**
- **Opus 5.5** does clear engineering: tools, Othello, Knucklebones, the player adjustment and the puzzle helpers.
- **Fable 5.2** does the subtle work: Remi's hidden-information play, the personalities and the final review, where judgement matters most.

## Running steps in parallel
Some steps change different files, so two chats can work at once: one **Opus** chat and one **Fable** chat side by side.
- **Order:**
  1. **Step 0 alone, first.** Everything else builds on it.
  2. **Then, side by side:** Opus does steps 1 and 2, one after the other in its chat. Fable does step 3.
  3. **Then, side by side:** Fable does steps 4a, 4b, then 5. Opus does step 7.
  4. **Then step 6** (Opus), once steps 1–5 are done. It touches all three opponent games.
  5. **Step 8 last** (Fable).
- **Remi steps run one after another.** 3, 4 and 5 all change the same file.
- **Deploy one chat at a time.** Every step rebuilds `index.html`, so two deploys at once would clash. Say "deploy" in one chat, wait until it's merged, then in the other.
- **Before pushing, update from `main`** (the chat must do this when it hears "deploy"): fetch the latest `main`, rebase onto it, rebuild `index.html`, re-run the quick checks, then push. If the plan's Progress table or the design notes changed meanwhile, merge them; never overwrite them.
- **Parallel chats don't save usage, only waiting time.** Two chats use up the five-hour session about twice as fast. Opus and Fable have separate weekly limits, so pairing one of each spreads the load best.
- **Test one change at a time on the phone** where you can, so you know which step caused anything odd.

## Progress
| Step | What | Model · effort | Status |
|---|---|---|---|
| 0 | Tools and shared brain kit | Opus 5.5 · high | done (Nov 15, PR #78) |
| 1 | Othello | Opus 5.5 · high | done (Nov 16, PR #80) |
| 2 | Knucklebones | Opus 5.5 · medium | done (Nov 16, PR #81) |
| 3 | Remi A: memory and discard-taking | Fable 5.2 · high | done (Nov 16, PR #82) |
| 4a | Remi B1: the three personalities | Fable 5.2 · xhigh | done (Nov 16, PR #83) |
| 4b | Remi B2: playing like a person | Fable 5.2 · xhigh | done (Nov 16, PR #84) |
| 5 | Remi C: Hard imagines hidden hands | Fable 5.2 · xhigh | done (Nov 17, PR #85) |
| 6 | Adjusting to the player | Opus 5.5 · high | done (Nov 17, PR #86) |
| 7 | Puzzle helpers | Opus 5.5 · medium | done (Nov 17, PR #87) |
| 8 | Final review and tuning | Fable 5.2 · high | to do |

Every prompt below assumes the chat follows the project instructions: connect and clone the repo, work locally, and deploy only on "deploy". On "deploy", it first updates from `main` and rebuilds, because another chat may have deployed meanwhile (see "Running steps in parallel"). After a successful deploy, it ends with: "Step N done. Next: step M, open a new chat with <model> · <effort> and paste its prompt" (or "All steps done"). It also keeps a task list beside the chat (one line per part of the step, ticked off as it goes), so you can see how far along it is without interrupting.

---

### Step 0 · Tools and shared brain kit · Opus 5.5 · high
**Prompt:**
> Build step 0 of `claude/ai-build-plan.md` (blueprint: `claude/ai-blueprint.md`, sections 4 and 7). First, copy both docs from the Project into the repo's `claude/` folder. Make `tests/ai_tournament.py` and record baseline numbers for today's CPUs in all three games. Then add the shared brain kit to `games/core.js` without changing how any CPU plays yet. This is a core change, so run the full test set. Hand back a short report with the baseline numbers.

**Check on your phone:** nothing should look or play differently.

### Step 1 · Othello · Opus 5.5 · high
**Prompt:**
> Build step 1 of `claude/ai-build-plan.md`: the Othello CPU from `claude/ai-blueprint.md` (sections 3, 3a, 5 Othello, 6, 7), using the core brain kit. Before starting, ask me open decision 6 (records). Prove the levels with `tests/ai_tournament.py` and measure thinking time at 4× CPU slow-down. Hand back a short report.

**Check:** Easy should feel like a beginner, not random. Can you beat Hard? Is the pace natural?

### Step 2 · Knucklebones · Opus 5.5 · medium
**Prompt:**
> Build step 2 of `claude/ai-build-plan.md`: the Knucklebones CPU from `claude/ai-blueprint.md` (sections 3, 3a, 5 Knucklebones, 6, 7). Prove the levels with the tournament and keep `referee.py` clean. Hand back a short report.

**Check:** Does Easy play like a person? Does Hard race to fill its board at the end?

### Step 3 · Remi A: memory and discard-taking · Fable 5.2 · high
**Prompt:**
> Build step 3 of `claude/ai-build-plan.md`: Remi CPU memory, safe discards and the new discard-taking from `claude/ai-blueprint.md` (sections 3, 3a incl. "Remi discard-taking", 5 Remi steps 1–2). CPUs may see only public information plus their own hand: add the fairness check. No personalities yet. Keep `remi_check.py` at 0 violations and prove Normal and Hard improve with the tournament. Hand back a short report.

**Check:** Do the CPUs now take from the discards, sometimes deep in the row? Do they stop feeding you tiles you collect?

### Step 4a · Remi B1: the three personalities · Fable 5.2 · xhigh
**Prompt:**
> Build step 4a of `claude/ai-build-plan.md`: the three Remi personalities (Cautious, Bold, Sly) from `claude/ai-blueprint.md` section 6b, on top of step 3's CPUs. Before starting, ask me open decision 7 (personalities in the Rules). Tournaments must show the three styles within ±5% of each other, and `remi_check.py` must stay at 0 violations. Hand back a short report.

**Check:** After a few rounds, can you tell CPU 1, 2 and 3 apart?

### Step 4b · Remi B2: playing like a person · Fable 5.2 · xhigh
**Prompt:**
> Build step 4b of `claude/ai-build-plan.md`: "playing like a person" for the Remi CPUs from `claude/ai-blueprint.md` section 3a: plausible misses, imperfect memory, thinking time that fits the moment, reading the player, playing the score, fishing and holding back. Keep the personalities from step 4a. Before starting, ask me open decision 4 (CPU voice). Keep the levels' tournament gaps and `remi_check.py` at 0 violations. Hand back a short report.

**Check:** Do the CPUs feel like people? Do they ever miss something believable, and never something silly?

### Step 5 · Remi C: Hard imagines hidden hands · Fable 5.2 · xhigh
**Prompt:**
> Build step 5 of `claude/ai-build-plan.md`: Remi Hard timing and "imagined hands" from `claude/ai-blueprint.md` (section 5 Remi step 3 and "How Hard thinks"). Use a Worker and stay within each speed's delay on the iPhone 12 at 4× slow-down. Prove Hard beats Normal with the tournament. Hand back a short report.

**Check:** Is Hard tough but fair? Does the pace still feel right at each speed?

### Step 6 · Adjusting to the player · Opus 5.5 · high
**Prompt:**
> Build step 6 of `claude/ai-build-plan.md`: adjusting to the player (section 6a of `claude/ai-blueprint.md`) in Knucklebones, Othello and Remi. Validate saves (`save_fuzz.py`), keep the levels from overlapping and add no UI. Hand back a short report.

**Check:** Win a few Easy games in a row. Does the CPU get a bit sharper? Does Hard stay the same?

### Step 7 · Puzzle helpers · Opus 5.5 · medium
**Prompt:**
> Build step 7 of `claude/ai-build-plan.md`: the coach brains from `claude/ai-blueprint.md` (section 5, Sudoku and Water Sort). Before starting, ask me open decision 5 (Water Sort hint). Run `puzzle_check.py`. Hand back a short report.

**Check:** Does Sudoku's hint teach you something before filling the cell? Does Water Sort warn you when you're stuck?

### Step 8 · Final review and tuning · Fable 5.2 · high
**Prompt:**
> Do step 8 of `claude/ai-build-plan.md`. Review all the AI work against `claude/ai-blueprint.md` with fresh eyes. Re-run every tournament and the deep checks, and tune the level knobs where the numbers miss their targets. List anything that feels un-human or unfair. Record what was built in the design notes. Hand back a short report.

**Check:** Play 5 games per level per game and use the blueprint's believability questions (section 7).
