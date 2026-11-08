# Two of the Board's own goals on local Codex, at Lean and at Standard

Spec 152 E and spec 153 D's second measure, on 8 November 2026, Orkboard frozen at `4bcd6c76`. Trial 152 left *a run at Standard with two
checkers* to do; this is it, with a run at Lean beside it. What the runs were held to was written before them
(`152-e-two-of-the-boards-goals/00-criteria.md`); the owner was away, and the driver (a Claude Code session) pressed for them. Codex was the
only AI tool.

**In short.** Both goals reached Done and their code is good: checked by hand, A's 7,289 prompts are the original code's to a character, B's
tests are 194 green where the base has 181. But **neither goal could go to main** (F1), **neither went through Talk** (F3), **opening the Board
stripped six goal pages of their gate, route and person's question** (F2, as trial 160 F1.3 found the same morning), and **at Standard one goal
spent 43% of the five hours and ran into Codex's limit; the acceptance it then could not make let the goal through as Done** (F5).

## 1. The runs

| Run | Goal (as it lies on the Board) | Size | Sent → Done | Ended |
|---|---|---|---|---|
| **A** | *Cut the import cycle between realm and core* (phase new) | every party Lean | 11:02 → 11:16, **14 min** | Done; **To main sealed** (F1) |
| **B** | *The checks into main and a red from before* (phase new, trial 152 F4) | every party Standard | 11:46 → 12:18, **33 min** | Done after the limit; **To main sealed** (F1) |

Each in its own clone of `4bcd6c76` (the Board in the code, 125 goals), a HOME of its own, a PATH holding `codex` alone, codex-cli 0.166.0 on the
ChatGPT plan, every press a page command (`orkboard drive call`). The goal was sent as the page sends a laid goal: `ideas.queue now` (F3 says why
nothing else could be pressed). The driver's two presses for the owner: *Start* of A's plan, *Add and start* (the Reviewer) of B's
(`driver-notes.log`). No question reached the hand in either run, so the driver answered none.

## 2. The numbers

| Step | Trial 152 A | **A (Lean)** | **B (Standard)** |
|---|---|---|---|
| Talk, the sections | 42,399 · 122,389 | none (F3) | none (F3) |
| The draft (the spec in one call) | | 99,062 | 97,016 |
| The plan | 106,438 | 119,445 · 1 task | 66,851 · 2 tasks (do, review) |
| **Tasks' sessions** | 1 · 1,384,853 | **1 · 2,977,286** | **k1 3,607,814, again after a red gate 1,065,971** |
| The check (Standard's reviewer) | | | **k2 1,649,835**: found 2, fixed 2 |
| The leader's acceptance | 102,333 | 103,063 · accepted, **5 of 5 lines unseen** (F4) | 74,996 · **2 sent back** |
| Fixes sent back | | | k3 418,474 · k4 578,599 |
| Acceptance, round 2 | | | **failed: Codex's limit** (F5) |
| Release's reading | 94,218 | 85,792 | failed: the limit |
| **All calls** | **11 · 1,969,107** | **5 · 3,384,648** | **10 · 7,559,556** (2 failed) |
| Read from the cache | 87% | 95% | 97% |
| The task's gate | 88 s | 181 s green | 132 s red, 111 s green · 25 s · 54 s · 48 s |
| Codex's five hours | | 79% → 46% | **46% → 3%** |
| Product's change | +9 −6, 3 files | **36 files**, +677 −451 (15 new modules) | 12 files, +454 −55 |

A session's cost is its turns times its context, as trial 152 F5 said: A's ran 43 commands with 317 thousand characters of output, B's k1 51
with 304 thousand; each is read again on every later turn. **A whole session is not cheaper than trial 152's: A's is 2.2 times its.** The goal is
larger (36 files), but 15 of the new modules are 5 to 66 lines (`seat_page_rules.py`, 8), split well under CLAUDE.md's 600.

## 3. Findings

### F1. To main is sealed by a goal done before this machine read it

Both goals: *Sealed: A leader is a skill is not done yet* (A), *What a goal on local is not done yet* (B). Goal 154 and goal 149 are `phase: done`
on the Board and `done` in the state, but `realm/goal_main.py` `lacks()` asks `_done()`, which needs **a plan on this machine** whose tasks all
merged; a goal done in history has none, so it is always lacking. **No way on in the page:** `depends_on` is front matter, `ideas.edit` writes a
section only, and *To main without the tests* (`untested`) stops at the same seal. As trial 152 F4, only a hand edit goes on.

**The draft put the dependencies there itself:** neither goal names one; the draft added `depends_on: ["154-…"]` and `["149-…"]`, both done.
(*What a goal on local* is the short title cut mid-phrase.)

### F2. The first write after opening strips the skills' record from the pages

Within ten seconds of the first party's size saved, both runs committed `board: The table, its edge and the past through the open tab — moved`:
`gate:` removed from goals 154–159, `route:` from 155–159, **`asks: person` from goal 156** (its two questions for the owner stay in its page;
the flag that says they wait is gone), and `project.md` and the project's journal written. The commit lands on `dev`, so the next *To main* takes it
to main. Trial 160 F1.3 found the same from another side (`goal_phase.keys`, the writer's `MANAGED` keys); this run adds that a bare open did not
do it here, the first write did.

### F3. A goal laid from the Board cannot go through Talk from the page

On the desktop, a laid goal lies face down in *In analysis* with `queue: hold` and no `held_for`; its lifted card offers *Next* and *Drop this
goal…* only (`table/column.js` shows *Talk* only when `held_for == "hold"`). The phone's *Process now* (`ideas.queue now`, `shell-preview.js`) is
the one press, and it drafts: `core/idea_keeper.py` `read_now` → `draft`, one call that writes the whole spec, then the plan. **No route, no leader
in Talk, no section**, `phase: work` at once with `asks: person`. Both goals went to Tech alone; **B's page part (*the discard says a red*) had no
Design** and no `[look]` line. Spec 155's `ground` and `settle`, the weigher and spec 152's party-to-party acceptance (criteria 8 and 9) were never
reached. Trial 160 F1.2 saw the other half: a page laid at `phase: talk` with its route is shown as a fresh route card.

### F4. An acceptance that saw nothing says *met*

A's acceptance: **accepted, 5 of 5 *Done when* lines `unseen`**, each with the reason *the four-file limit*: it read 4 of the 36 files the step
changed. It wrote five findings, *Nobody could look at: …*, as `told`, but none reached the hand, and the goal's result shows **all five lines
`ok`** with no proof (`A/quality.json`). B's first acceptance did the same for two lines while sending two others back. Trial 152 F2 and trial
160 F4 are the same: the leader's yes does not mean someone looked.

### F5. Standard ran Codex dry; the acceptance that could not run let the goal through

B used 43 points of the five hours in 33 minutes (46% → 3%). The reserve (30% by day) did not hold anything: `idea_target.gate` applies it only to
a plan the Board passed by itself, and the sent-back fixes k3 and k4 started at 12:12 and 12:14, with the window at 29%, as the person's press of
an hour before. The second acceptance then hit *You've hit your usage limit … try again at 3:00 PM*; `core/idea_accept.py` makes a failed call
`gone_on` with one finding (*Architect could not accept this step: its call failed*), and the goal went **Done, Ready for main**, every line `ok`.
The only sign on the page is the potion's *back 15:00*.

### F6. Smaller

- The reviewer's task card says *a Grunt* (B's sheet, tile 4); the reviewer is seated (`role: reviewer` in the events).
- Each task is planned at `elder` and runs at `warrior` (*role model warrior*); the plan's tier is not the one that ran.
- `python` is not on the session's PATH (`python3` is): 3 of the sessions' failed commands are exit 127.
- A's Grunt changed a timing test outside its brief (`test_idea_talk.py`'s stagger: a fixed 150 ms replaced by the stub's barrier) and said so.
- The drafted *Done when* lines carry no `[test]`, `[look]` or `[person]` (§257.4), and each ends *The change was reviewed…*, at Lean too.

## 4. What held

| From | Held |
|---|---|
| §257.1 | A: one task. B: one do and one review, as Standard asks; the two fixes are the acceptance's, each named |
| §257.2 | every named file existed and was read; A changed all five code files it named, B all but `CLAUDE.md` |
| §257.6 | no task wrote a goal page, a phase or BOARD.md (B's sessions read pages 11 times, read only) |
| §256.1 | every task's role is `grunt` or `reviewer`; the leader planned nothing |
| §256.3 | B's acceptance sent back two real gaps (*the reason and failed tests on reopening the discard*; *only an explicit Test again retries*), both fixed and green |
| 149 C, D, E | every gate under its timeout (25–181 s); B's red gate went back to the same session, which made it green |
| 149 F | no session hunted `index.lock` or a browser |
| Standard's check | the reviewer found 2 and fixed 2, its gate green |
| The code, by hand | A: the fixture equals the original code's output in 7,289 cases; `seat_frames` and `agent_rules_text` import no `core`; 341 of 342 touched and critical tests green, the one red is red on the base too (`test_agent_rules_browser.py`). B: 194 green against the base's 181 on the same files |

## 5. Against the criteria

| # | Question | Result |
|---|---|---|
| 1 | Tasks and why split | **holds** |
| 2 | Session tokens | **no**: A 2.98 million against 1.38 |
| 3 | Named files read and changed | **holds** |
| 4 | Each line claimed | not seen: the planner's `proves` is not kept in either plan |
| 5 | A screen's line marked | **no**: no line marked (F6), B's page line bare |
| 6 | Every task's role | **holds**; the tier not (F6) |
| 7 | Standard's check, then the acceptance | **holds** in round 1; round 2 failed on the limit (F5) |
| 8 | Between parties | **not reached**: one party each (F3) |
| 9 | Talk's ground and settle | **not reached** (F3) |
| 10 | No task touched the Board | **holds** |
| 11 | To main | **no**: sealed in both (F1) |
| 12 | A's prompts unchanged, by a test | **holds**, checked by hand against the original code |
| 13 | The Board readable | `check` not run in the clones; **F2** |

## 6. For the owner to decide

1. **F2 and F1 first**: one rewrites what the skills write on every open, the other blocks every goal with a dependency from history. Both are
   small in the code (`goal_phase.keys` keeping keys it does not own; `goal_main.lacks` reading the page's phase).
2. **F3**: should *Process now* on a goal laid by the person go through the Orkmaster and Talk, and the face-down card offer *Talk*?
3. **F4 and F5**: an acceptance with every line unseen, or one that failed, sends the goal on as Done with every line `ok`. A finding *told* that
   reaches no hand. Fixes sent back counted as the person's press, past the reserve.
4. **The two goals' code** is in the clones' branches on the owner's computer, never pushed: A `idea/cut-the-import-cycle-between-realm-and-core/k1`
   (`c3cc0e89`), B `dev` (k1–k4). A is a clean refactor; B overlaps spec 158 A–B's *to main only after the gate's checks*. Whether either is taken
   into this repository is the owner's.

## 7. What is where

`152-e-two-of-the-boards-goals/`: `00-criteria.md` · `A/`, `B/`, each: `00-contact-sheet.png`, `calls-table.txt`, `calls/` (each call's tool,
model, tokens: no prompt, no answer), `spend.txt`, `spend.json`, `events.jsonl` (history's entries left out), `watch.log`, `plan.json`,
`goal-page.md`, `quality.json` (the result and its findings), `driver-notes.log` (the driver's presses).

Not here, on the owner's computer in the session's scratch until it is cleaned: every picture of each stage (`shots/`, a picture every four minutes
and at each stage, phone and desktop), the clones with each call's whole prompt and answer (`.orkcraft/logs/<day>/`), the servers' logs, and the
by-hand test runs (`verify/`).
