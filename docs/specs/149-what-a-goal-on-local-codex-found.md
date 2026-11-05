# 149. What a goal on local Codex found: the person's type steers the route, a gate with a budget, a red from before, one way to main

Decisions §253. **Builds:** a cloud session, the owner's: A, D and E first (what cost the most), then B, C, F, G, H, I, J, each its own
commit into `main` as its tests and the critical ones are green (CLAUDE.md, Alpha); K on the owner's computer, last · **Review:** the
critical tests and each part's own · P1. No new pane, column, drawer or dialog. No change to orkUI: the page's sheets use its tokens.

**In the cloud:** no AI tool is signed in and none is needed; every test fakes the tools (`tests/test_tools_host.py`'s way). The browser tests
need Playwright and its Chromium: `uv sync --extra dev --extra browser --extra gui`, then `.venv/bin/python -m playwright install chromium`.
If Chromium cannot be had, say so on the part; do not report a browser test as passed that was skipped.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The route** | a type chosen is the route's kind; *fixed* says no bug; the card says what the host will do; *It is no bug* | `gui/ideas_route.py` (`route_plan`), `realm/goal_route.py` (`route`), `core/idea_kind.py` (`WORDS`), `hand/routecard.js`; `tests/test_goal_route.py`, `tests/test_gui_route.py`, `tests/test_route_card_desktop_browser.py` |
| **B. The project's kind** | a sign counts at the root, never in a fixture | `realm/project_kind.py`; `tests/test_project_kind.py` |
| **C. The gate's budget** | `browser_max`; in parallel; what was left is said and runs at the portal | `realm/gate_config.py`, `realm/idea_git.py` (`gate_run`), `realm/main_checks.py`, `orkcraft.toml`; `tests/test_gate_config.py`, `tests/test_idea_gate.py` |
| **D. A gate that did not finish** | the gate's own words, its log and event kept, *Test again* | `realm/idea_git.py` (`gate_run`), `core/idea_task.py`, `core/idea_review.py`; `tests/test_idea_gate.py`, `tests/test_gate_env_browser.py` |
| **E. A red from before** | the red tests again alone and on the base, before a session is called | `core/idea_task.py` (`_check`), `realm/idea_git.py`; `tests/test_idea_gate.py` |
| **F. What a session is told** | the sandbox said in the prompt; what is settled reaches the commit; the running product's name | `realm/harnesses.py`, `core/idea_task.py`, `realm/steps_git.py`, `realm/idea_git.py` (`commit_left`), `realm/library.py`; `tests/test_task_brief.py`, `tests/test_idea_gate.py` |
| **G. To main** | one way, its checks in it; half a goal refused; what is counted as ready | `table/discard.js`, `table/releasemap.js`, `gui/ideas_gate.py` (`gate`, `gate_merge`), `realm/idea_gate.py` (`without_board_pages`), `table/discard.css`; `tests/test_discard_table_browser.py`, `tests/test_goal_main.py` |
| **H. Done and the spend** | promised against made; the spend in what is known; dollars only where there is a price | `shell/preview.js`, its host, `realm/goal_route.py` (`cost`), `core/idea_plan.py`, `realm/spend_report.py`; `tests/test_spend_report.py` and the result page's browser test |
| **I. Small words** | a cut line, a lost underscore, a question with no choices, the drive | `realm/idea_talk_parse.py`, `realm/idea_page.py`, `hand/questioncard.js`, `gui/drive.py`, `docs/beta/run-the-whole-way.md`; `tests/test_idea_page.py`, `tests/test_drive.py` |
| **J. The goal itself** | the trial's code carried; the rune with no party addressed; a Done when names where it opens | `docs/trials/149-the-rune-square.patch`, `hand/pluscard.js`, `core/idea_sections.py`; `tests/test_rune_hue_browser.py` |
| **K. The trial again** | the same goal on the same setup | the owner's computer |

**Not this spec:** a party taken under *To* starting to pick at once; whether a small goal at Lean plans a check; Play for this repository; §250.9's
*Start again* with a line and the `laborer` tier; `OPENAI_PRICES`, still empty (spec 143 G.1). Each is the owner's to send on (§253.13).

## 0. What the trial found

Goal 4 of `docs/trials/143-four-goals-for-the-trial-again.md`, at `64f3abd4`, 5 November 2026: a clone with no remote, a HOME of its own holding only the
Codex sign-in (codex-cli 0.166.0, the ChatGPT plan), `PATH` with no other AI tool, a frozen install of Orkboard, a Tech party at Lean, every press in the page
but the checks named below. 13 calls, 3,302,029 tokens (88% read from the cache), 937 s of the model, 14% of Codex's 5 hours and 2% of its week. The goal reached main.

| Time | What | Tool, tokens | What it showed |
|---|---|---|---|
| 09:43 | First open | | asks *orkBoard is a game, Skyhop.uproject is here*: `tests/fixtures/engines/unreal/Skyhop.uproject`; `realm/project_kind.py:162` takes a `.uproject` anywhere in the tree (B) |
| 09:44 | *Test & add* Codex | `gpt-6-luna`, 11,611, 3 s | good |
| 09:45 | Start: Tech and Release at Lean | Tech's reading, `gpt-6.1-sol`, 111,311, 23 s | Release does not read: §250.6 holds. Tech's reading is in no estimate shown |
| 09:46 | The goal sent to the Orkmaster | | routed *Tech alone: finding the cause*: `idea_kind.WORDS["bug"]` holds *fixed*, the line says *not a fixed one* (A). The card's menu holds only *Drop this goal…* |
| 09:48 | Dropped, sent again: **To Tech, New feature** | | the card says *a small change*; `state.json` has `type: shaped-feature` and `route_how.kind: bug`: `route_plan` passes the text alone (A) |
| 09:49 | Talk | `diagnose`, 84,743, 23 s | *The cause: I think…*, cut mid-word at 300: *the host's per-shape hu* (I); right about the code. No Talk and no decision |
| 09:51 | The section | 85,045, 36 s | sharp *Done when*, *Checks*, *Will be*, *Out*, *Risks*; its *Why* is the cut line |
| 09:52 | The plan | 133,420, 49 s | 3 tasks, 1 check, each brief naming the *Done when* lines it proves |
| 09:53 | k1 *Host predictions* | 413,813, 123 s | gate 22 s, 97 passed, merged |
| 09:55 | k2 *Rune previews* | 463,853, 180 s | gate 237 s, **4 of 205 red**, none of them this task's (E) |
| 10:02 | k2, sent back | **588,106**, 74 s | the dearest call: mends two `Control+a` red on clean `main` on a Mac and a focus race; looks for Chrome in `/Applications` (F); gate 237 s, green, merged |
| 10:07 | k3 *Phone parity* | 428,348, 123 s | answers, then **the gate runs 900 s and is killed**: `tests/test_pwa*_browser.py` (C). *No answer within 900 s*, no `gate_ran`, no output (D) |
| | *Measured apart* | | that commit's gate at `-n 6` on 8 cores: **569 passed in 16 min 13 s**, 4,951 s of CPU in user time and 966 s in system time |
| 10:45 | `[gate] browser` narrowed by hand in the clone's `orkcraft.toml`; *Start again* | **326,936**, 118 s | the branch reset to `dev`, the green `669455a5` thrown away, the same line written again (D); gate 11 s, merged |
| 10:47 | k4 *Review parity* | 556,105, 139 s | *no blockers*; two findings about where it ran; the card says so plainly: *What is left is about where it ran, not the code* |
| 11:10 | *Leave them*: Done | Release's reading, 84,932, 29 s | §250.6 holds; the result says *This goal so far: —* and four titles (H) |
| 11:11 | **To main** on the discard's page | | `ideas.gate_merge`: 12 commits in 3 s, no check run (G). 126 tests of the goal and the critical ones green when run by hand |
| 11:12 | The fold | 13,806 | its Board commit says *1 commit ready for main* again (G) |

**Against the trial's *Good when*:** no log says *A task never edits the Board's pages*, and `task_pages_put_back` never came: held. Every task merged or stopped on a real red test: **no**, k3
stopped on a clock. The goal's tests green: yes, on `dev` and on main. The tokens of `work` well under 2.49 million: **no**, 2,777,161; without the two calls that were not the task's
(588,106 and 326,936) 1,862,119, which is. **Against `docs/beta/run-the-whole-way.md` §4:** 1 fails (the hand edit of `orkcraft.toml`), 2, 3, 5 hold, 4 has a picture of the phone at the end only,
6 knows tokens and no money.

**The goal itself:** the product's change is four lines of code and their comments in three files (`gui/ideas_map.py`, `hand/pluscard.js`, `pwa/shell-marks.js`) and about 250 lines of tests. On main, in the page: **To Tech**, with a shape chosen, the square wears the
host's hue (`ork-elem meadow k-dust`, `rgb(184, 145, 79)`, `next_hues.meadow == "dust"`). **To the Orkmaster, what the field opens with**, it is what the goal set out to change: `ork-elem dust big dim`, *Its rune:
none yet* (J). All tests green; the review found no blocker; this project has no Play, so nobody could look (`shot_taken`: *no preview*).

What went well and must stay: the first open (no dialog, a real test of the tool, the parties on one card, the table laid in seconds); no refused command, no error toast and no console error in the whole run; the section and
the plan, the best part of the run; a brief that names what it proves; §250's words (*To look at*, *Its leader takes it next*); the review card's plain sentence; *Nothing reaches main without you*.

## A. The route (§253.1)

1. **A type chosen is the route's kind.** `gui/ideas_route.py` `route_plan` passes `args.get("type")`; `goal_route.route(…, chosen="")` takes it (the catalog's id, by `goal_types.get`) in place of
   `kind_of(text)`. `failure` stays by `reproduces(text)` and counts only when the kind is `bug`. A bug chosen stays a bug with or without its lines.
2. **`fixed` goes** from `idea_kind.WORDS["bug"]`: it says a state (*a fixed width*), not a report. `fix` and `fixes` stay. A test holds the trial's line: `kind_of` is not `bug`.
3. **The card says what the host will do.** `hand/routecard.js` takes its *finding the cause* or *a small change* from `route_how.kind` and `short` (`goal_route.rows` gives them), not from `type`. A test: the row's words and
   the mode `idea_talk` begins in agree, for a goal typed and for one guessed.
4. **It is no bug.** On a route card of kind `bug` with no failure in its report, beside **Talk** and **Hold**, a quiet **It is no bug** (`ideas.route_kind {idea}`): the kind becomes `kind_of` with the bug's words left out, else `feature`; `shape` and
   `cost_of` run again and the card says the new way and cost. Nothing is called. A bug whose report holds a failure keeps today's *The long way*.

## B. The project's kind (§253.2)

`realm/project_kind.py`: a `.uproject` counts in `top_files` alone, as `engine_unreal.detect` reads it. `.xcodeproj` (line 152) and `AndroidManifest.xml` (line 154) count only outside `tests/`, `fixtures/` and `testdata/`. Tests: a fixture of each makes no
game and no mobile app; this repository reads `code`.

## C. The gate's budget (§253.3)

1. **`[gate] browser_max`** (default 12, `gate_config.Gate`). `browser_files`: a pattern that finds more modules than that is not taken whole: only the modules whose name holds the touched file's stem (`shell-marks` and `shell_marks`) come, and the rest are
   *left*. The `hand/` set (7 modules, 205 tests) comes whole; a `pwa/` file brings its own. `gate_files` and `browser_files` give what was left, by folder.
2. **In parallel.** `IdeaGit.gate_run`: with browser tests in the run and `xdist` importable by the gate's Python (asked once, as `gate_env.path_python` asks), `-n <min(cores - 2, 6)>`. The trial's 569 ran green at six workers, so these tests stand it. A test measures nothing of
   time: it checks the argument and that a run with no `xdist` runs without it.
3. **What was left is said and run later.** The log has `== browser tests left for main: 56 of pwa/`, the result card one line. The portal's **Tests** check (`realm/main_checks.py`) takes the folders whole, with `[gate.main] timeout_min`, default 30 (`jobs.TEST_TIMEOUT_S` would kill it).
4. **`orkcraft.toml`**: `browser_max = 12`, its comment saying why, with the trial's numbers.

## D. A gate that did not finish (§253.4)

1. `IdeaGit.gate_run` catches the timeout of `jobs._wait` (the `RuntimeError` of `tool_run.wait_for`; `InterruptedError` is a stop and stays one) and gives `GateRun(False, f"$ {line}\n{out}", True, line, None, seconds, env=f"The tests did not finish in {minutes} minutes: {n} files")`. It is then a gate that
   could not run (spec 107 §1.3, spec 143 C): the task goes to Review with **Test again** (`core/idea_review.py:178`), no session called, no try spent, its commit kept.
2. The run's output so far goes in `== the gate, try n`, and `gate_ran` is written, `verdict: could_not_run`. Today neither is, and the log reads as if the model hung.
3. *No answer within N s* stays the words of a model's call alone.
4. **Start again** on a task whose branch holds commits says in its `title`: *The task's work is thrown away and made again*. `idea_git.py:117` keeps doing what it does (`worktree add -B`).

## E. A red from before (§253.5)

1. In `core/idea_task.py` `_check`, on a red gate whose run has pytest's summary (`parse_tests`' `failing`, at most 20): run those tests **again alone** in the worktree; those green now are *flaky*. Run those still red **on the base** (`start_sha`'s merge base with `merge_into`, a throwaway worktree that is removed after);
   those red there too are *red before*. What is left is the task's.
2. Nothing left: the gate is green for this task. The log has `== red before this task: …` and `== flaky: …`, `gate_ran` has `red_before` and `flaky`, the result card one line. No session is called and no try is spent. Something left: the session is told only what is left, as today.
3. These runs have the gate's clock with what is left of it. A run that does not finish counts its tests as the task's.
4. The goal's result says *n tests were red before this goal*: no new card.
5. The two tests themselves are mended by J's patch (`ControlOrMeta+a`, the report's focus waited for).

## F. What a session is told (§253.6)

1. **`Harness`** gains `commits` and `browsers` (default True; Codex False: its `workspace-write` cannot write git's index, and Chromium aborts in it). `core/idea_task.py:319`: with `commits` False, *Git cannot write in this sandbox: do not commit; what you leave is committed for you*; with `browsers` False, *A browser cannot start here: do not look for one; the gate runs
   the browser tests*. Five of the trial's six task calls hit `index.lock`, and two went through `/Applications` after Chrome. A test on the brief, for Codex and for a tool that can.
2. **What is settled reaches the commit.** `realm/library.py:71` says it goes in the commit's message; on Codex every commit said its title alone, as k4 reported. A task may leave `.ork-commit.md`: `commit_left` puts it under the title and never commits the file (`steps_git.exclude`, a second line). `library.py` says so.
3. **The product's name.** `idea_git.py`: the author of `commit_left` and `commit_file`, the merge, and `BOARD_NAME`, by `brand.name()`, not a fixed *Orkline*. Its email stays a local one.

## G. To main (§253.7–8)

1. **One way.** `table/discard.js`'s **To main** takes the portal's way (`portal.js` `choose` and `ideas.to_main`, with `to_main_checks`), the goal chosen, or the first when one is ready. `ideas.gate_merge` stays for commits of no goal and Release's map.
2. **Half a goal is refused.** `gate_merge` (`gui/ideas_gate.py`) refuses, in words, while a goal with commits in dev is not ready (`NOT_YET`): *The field's Rune square is at 2 of 4: it would reach main half made.* `tests/test_goal_main.py`.
3. **What is counted.** `gate` counts as ready only the commits of goals ready and of no goal: the commits of a goal not ready are left out of `commits` and `files`. `discard.js:136` *commits that belong to no goal* is then true.
4. **The Board's own.** `without_board_pages` leaves out a commit authored by `BOARD_NAME` as well as one of `BOARD_PAGE`: the fold's `llm-wiki/<wiki>/specs/<capability>.md` is the Board's. A test: after a goal reaches main and folds, the pile says nothing.
5. **Inside the card.** `table/discard.css`: at the narrow width the pile's words are cut (*1 commi*, *ready for*): they wrap inside its window, as §250.7 says.

## H. Done and the spend (§253.9)

1. **Promised against made.** The result (`shell/preview.js` and its host) has the goal's **Done when** lines, read from its section with no model, over **What it made**, where each task has its files and lines (`diff`) and its gate (*97 passed*, *0 files*). They are not matched by a model; the person reads them side by side.
2. **The spend in what is known.** `preview.js:56`: with no price, *This goal so far: 3.1 million tokens · about 2% of Codex's week*: the tokens from the goal's `spend.jsonl`, the share from the limits read at its first call and now (`limits_read`), left out when not read twice. With a price, as today.
3. **Dollars only where there is a price.** `goal_route.cost` and `idea_plan`: `idea_target.floor(tier)` has `tool="claude"` by default, so a Codex party's *$0.28–0.83 at API prices* is Claude's table. Pass the party's tool; a tool with no price known says *about 3 calls*, with no dollars and no `$` chip.
4. **`drive spend`'s *Worth a look*** (`realm/spend_report.py`): *work done twice*: a task with two runs and the branch reset between them (the trial's k3); *sent back*: the calls after a red gate. Today it says *no step asked again*.

## I. Small words (§253.11)

1. `realm/idea_talk_parse.py:38` `_line` cuts at a word with `…` (as `idea_questions._plain` does), and `CAUSE_CHARS` is 500. The cause in *Why* is the whole cause.
2. `realm/idea_page.py:129` `thesis`: Markdown's marks go at a word's edges only: `realm/idea_element.py` stays itself (today *realm/ideaelement.py*). `tests/test_idea_page.py`.
3. `hand/questioncard.js:20`: a question with no choices says *Say it in a line: the leader keeps it for the project*, and its one place is the field, with no *Other…* to press first.
4. `gui/drive.py`'s text and `docs/beta/run-the-whole-way.md`: `ideas.board`'s `needs_you` holds no task at Review; the snapshot's `review_count` does. The trial's driver sat 21 minutes on a card in the hand. They say so; `drive wait` on `state` with `--path review_count` is the example.
5. `gui/drive.py` `shot` needs Node's `playwright`, and the project's extra is Python's: it falls back to Python's. `tests/test_drive.py`.
6. `docs/beta/run-the-whole-way.md` §1: after `uv sync`, `playwright install chromium` (the owner's cache held 1243, `uv.lock`'s Playwright 1.64.0 asks 1248, and with none every browser module skips, `tests/browser_kit.py:47`).

## J. The goal itself (§253.10)

1. **The trial's code.** `git apply docs/trials/149-the-rune-square.patch` at `main`, its tests run: `next_hues` on a party (`gui/ideas_map.py`), `runesOf` selecting from it (`hand/pluscard.js`), `nextElement` by the project (`pwa/shell-marks.js`), the two tests of E.5, and `tests/test_pwa_next_element.py`, `tests/test_rune_preview_js.py`. It leaves out the clone's `orkcraft.toml`. The patch is removed in the same commit.
2. **With no party addressed.** `runesOf`: `next_element`, `next_hue`, `next_hues` and `free_elements` are the project's, the same at every party (`ideas_map.py:61`): with no party, the first party's are read. The field opens with the rune and hue the host will give, the seal of the + card too, and *Its rune: Rune n, change it*. No party at all: as today. This changes §187.3's *"" with no party*. A browser test on `tests/test_rune_hue_browser.py`, at **To: the Orkmaster**.
3. **A Done when names where it opens.** `core/idea_sections.py`, the rule for a section's *Done when*: *A line about a screen names the state it opens in, as a person first meets it*.
4. **Spec 128 G**'s *Not built* line is struck when 1 and 2 are in.

## K. The trial again

On the owner's computer, as in §0, with the goal of `docs/trials/143-four-goals-for-the-trial-again.md` that comes next (goal 2 has a host command and a page's change in one goal). It is good when: a type chosen is what the route runs; a `pwa/` file's gate ends in under 5 minutes, saying what it left; a red from before calls no session; no session looks for `index.lock` or a browser; the discard's **To main** runs its checks; the result says the tokens and the share of the week; no hand edit of `orkcraft.toml`. What it shows goes in a decision.

## Tests and wording

Each part adds its tests beside the files it touches and keeps the critical ones green. New words: *To look at* and the rest stay as they are; *It is no bug*, *Test again*, *red before this task*, *flaky* in logs. The interface says *goal* and *party*, never *idea* or *track*.
