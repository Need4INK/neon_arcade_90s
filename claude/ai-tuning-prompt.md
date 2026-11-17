# Neon Arcade – tuning the CPUs from real play

Open a new chat in this project, set **Opus 5.5 · high**, fill in your notes and paste the prompt. Nothing else is needed.

## Notes to keep while you play
Be specific: which game and level, and what the CPU did. Examples:
- "Normal Othello is too easy"
- "CPU 2 takes too many discards"
- "Hard Remi pauses too long"
- "Knucklebones Easy never attacks my columns"

## Prompt
> Tune the CPUs from my play experience. Read `claude/ai-blueprint.md` and the CPU brain section of `claude/design-notes.md` from the Project. Connect the repo Need4INK/neon_arcade_90s with push access and clone it (I give permission). My notes: [paste your notes here]. For each note, find the cause in the code, make the smallest safe change to the level or personality settings, and check it with `tests/ai_tournament.py` and the matching deep checks (`referee.py`, `remi_check.py`, `remi_fair.py`, `save_fuzz.py`). Keep the levels from overlapping and don't change anything on screen. Keep a task list, record what you changed in the design notes (repo and Project), then deploy it yourself once all checks pass: push a branch, open the pull request through the REST API, wait for the GitHub checks, then merge. If a check fails and you can't fix it, hand back what you found instead. End with a short report.

## Tips
- Several small notes can go in one chat; a big change (for example a new Remi behaviour) is better in its own.
- If a chat stops at the usage limit, wait for the reset and say "continue".
- Afterwards, fully close and reopen the home-screen app to get the new version.
