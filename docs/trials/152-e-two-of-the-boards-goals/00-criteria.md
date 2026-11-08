# What the runs are held to (written before them, 8 November 2026)

The flow under test: Orkboard frozen at `4bcd6c76` (origin/main of 8 November, 11:00: specs 155–159 in it, spec 158 A–B's *to main only after the gate's checks* among them).
Spec 152 E and spec 153 D ask that this be written before the runs. Trial 152 (6 November) measured two goals at Lean; its
§5 left **a run at Standard with two checkers** and **a party's acceptance between two parties** to do. These two runs are that.

| Run | Project | Goal | Size | What it is for |
|---|---|---|---|---|
| **A** | clone of `4bcd6c76`, the Board in the code | *Cut the import cycle between realm and core* (phase new, by the person) | every party at **Lean** | a pure refactor whose Done when is provable by code: does the flow stay as cheap as trial 152 B? |
| **B** | a second clone of `4bcd6c76` | *The checks into main and a red from before* (phase new, trial 152 F4) | every party at **Standard** (Tech's squad: grunt, tester, reviewer) | the checker's step and, if routed to two parties, the acceptance between them |

Both: codex-cli 0.166.0 on the ChatGPT plan, **Codex the only harness** (Claude Code, Antigravity, Cursor off; the PATH holds
`codex` alone), a HOME of its own, every press through the page's own commands (`orkboard drive call`), the goal taken from its
page as it lies on the Board (not typed again). The driver is a Claude Code session; it spends nothing of Orkboard's.

**The person's questions.** The owner is away and asked the driver to answer. A question a written decision or spec settles is
answered by its reference. Any other is answered with the option Orkboard marks first (its recommendation) and recorded as
*answered by the driver for the owner, 8 November*; each such answer is listed in the report for the owner to undo.

**What is not done.** The goals' code is not merged into this repository's `main`: it stays in the clones' branches, named in the
report. Only the report, its logs and two contact sheets go to `main`; every other picture stays local.

## The numbers they are read against

Trial 152 (`docs/trials/152-a-leader-accepts.md` §2): A 11 calls, 1,969,107 tokens, one task session 1,384,853, acceptance 102,333;
B 14 calls, 1,113,745, one task session 589,488, acceptance 107,905. §253's base: 13 calls, 3,302,029, the Lean review 556,105.

## What would show the flow holds

| # | From | The question | Good when |
|---|---|---|---|
| 1 | §257.1, 153 D | How many tasks, and why each split? | one task a party unless a reason is written |
| 2 | §257.1, 153 D | A task's session tokens | A under trial 152 A's 1.38 million; B's per task said |
| 3 | §257.2, 153 D | Of a task's named `files`, how many read, how many changed | named files exist and are where it starts |
| 4 | §257.3, 153 D | Each *Done when* line claimed? second calls of the planner? | every line claimed or said as not claimed |
| 5 | §257.4, §260.3 | Do lines carry `[test]` `[look]` `[person]`; is B's page line (*the page says a red*) a `[look]` or a screen's test? | a screen's line is never a bare `[test]` with no state |
| 6 | §256.1, 152 E | Every task's role | none the leader's; the leader at its own tier |
| 7 | §256.3, 152 E | **At Standard: the checker's step** — its tokens, what it found, how long a step waited for it; then the acceptance | the check runs once a task, finds what is there, and the acceptance does not repeat it |
| 8 | §256.3 | **Between parties** (if B is routed to two): the first party's step accepted before the second starts | the order holds, and the second party's work does not start on an unaccepted step |
| 9 | §260 (spec 155) | Talk's `ground`/`settle`; the weigher weighs only; a doubt answered by one `rg` does not reach the person | no question to the person that the code answers |
| 10 | §257.6 | Did a task touch the Board's pages, the phase, BOARD.md? | no |
| 11 | 149 K, 155 | the gate ends under its timeout; a red from before calls no session; *To main* runs its checks and the page says their end | each holds (B's goal is F4 itself: whether *To main* is reachable on a red from before is measured, not assumed) |
| 12 | A's own Done when | the cycle cut, every prompt unchanged by a character | proven by a test that compares the prompts, not by a word |
| 13 | 151 | `orkboard check` clean at the end; no other goal of the 120 worked on its own | holds |

## What is kept, a run

`logs/watch.log`, `logs/server.log`, `logs/page-console.log`, `logs/spend.json`, `logs/calls/`, each task's log, the goal's page,
`plan.json`, `talk.jsonl`, `way.json`, the journals' lines, `shots/` at each stage (desktop 1440 × 900, the phone at 390 at the
start and the end). Whole prompts and answers stay in `.orkcraft/logs/<day>/` of each clone.

## What these runs cannot say

Two runs are not a distribution. Codex may be in use elsewhere on the same plan, so the share of the window is read as tokens.
Spec 154's skills are Claude Code's and are not touched on Codex.
