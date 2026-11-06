# What the runs are held to (written before them, 6 November 2026)

The flow under test: Orkboard frozen at `452c44c0`, §256–§259 and specs 151–154 in it. Spec 152 E and 153 D ask that this be
written before the runs. Spec 154's forked skills are Claude Code's: on Codex they are not exercised, and this says so.

| Run | Project | Goal | What it is for |
|---|---|---|---|
| **Base** | clone at `64f3abd4`, Orkboard of 5 November | goal 4 of `docs/trials/143` (the Rune square) | yesterday's run: spec 149 §0, §253 |
| **A** | clone at `64f3abd4`, the same commit, only `orkboard init`'s files committed | the same goal, the same words | the flow is what changed; no solution in the repository |
| **B** | clone of `main` at `452c44c0`, the Board in the code, 122 goals | goal 2 of `docs/trials/143` (the tiers' models on a potion's card), named by spec 149 K | the flow on the repository as it is |

Both: codex-cli 0.166.0, the ChatGPT plan, a Tech party at Lean, a HOME of its own, every press in the page.

**The base's numbers:** 13 calls, 3,302,029 tokens, 88% from the cache, 937 s of the model, 14% of the 5 hours, 2% of the week.
By step: diagnose 84,743 · section 85,045 · plan 133,420 · work 2,788,772 (7 calls: k1 413,813, k2 463,853, k2 sent back 588,106, k3 428,348,
k3 again 326,936, k4 review 556,105) · goal 196,243 · fold 13,806.

## What would show the flow holds

| # | From | The question | Good when |
|---|---|---|---|
| 1 | §257.1, 153 D | How many tasks, and why each split? | one task unless a reason is written; A's 3 + review of the base gone |
| 2 | §257.1, 153 D | A task's tokens against about 420 thousand | a whole session costs less than the base's three together (1.31 million) |
| 3 | §257.2, 153 D | Of a task's named `files`, how many were read, how many changed | named files exist and are where it starts |
| 4 | §257.3, 153 D | Each *Done when* line claimed? second calls of the planner? | every line claimed or said as not claimed |
| 5 | §257.4 | Do *Done when* lines carry `[test]` `[look]` `[person]`? | a screen's line is `[look]`, never a bare one |
| 6 | §257.5, §253.10 | **Does the base's miss get caught?** A's field at *To: the Orkmaster* | the line exists and is proven, or *Nobody could look at* reaches the person |
| 7 | §256.1, 152 E | Every task's role | none the leader's; the leader at its own tier |
| 8 | §256.3, 152 E | The acceptance against the review it replaces (556,105) | cheaper, and what it sent back was right; how long a step waited for it |
| 9 | §257.6 | Did a task touch the Board's pages, the phase, BOARD.md? | no, with `AGENTS.md` now in the project |
| 10 | 149 K | a type chosen is the route; a `pwa/` gate under 5 minutes, saying what it left; a red from before calls no session; no session hunts `index.lock` or a browser; *To main* runs its checks; the result says tokens and the share of the week; no hand edit of `orkcraft.toml` | each holds |
| 11 | 151 | Does the project's Board stay readable? | `orkboard check` clean at the end; B's 122 goals do not get worked on their own |

## What is kept, a run

`logs/watch.log`, `logs/drive-log.jsonl`, `logs/server.log`, `logs/page-console.log`, `logs/spend.json`, `logs/calls/`, each task's log, `shots/` at each stage,
phone and desktop. Whole prompts and answers stay in `.orkcraft/logs/<day>/` of the clone.

## What these runs cannot say

Spec 152 E's run at Standard with two checkers is not one of these. A and B are at Lean. B's goal is larger than the base's, so only its steps and tokens a task compare, not its sum.
