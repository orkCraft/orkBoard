# 143. What a trial with real tools found: a task told what the gate holds it to, a page's change tested, and the table's words true

Decisions §250. **Builds:** a cloud session, the owner's: A first (it is what cost the most), then B, C, D, E, F, G, each its
own commit into `main` as its tests and the critical ones are green (CLAUDE.md, Alpha) · **Review:** the critical tests and
each part's own; the trial again on the owner's computer afterwards (*The trial again*, below) · P1. No new pane, column,
drawer or dialog. No change to orkUI: it is private and its copy is made from the owner's computer; the page's sheets use
its tokens as they are.

**In the cloud:** no AI tool is signed in and none is needed. Every test here fakes the tools (`tests/test_tools_host.py`'s
way). The browser tests need Playwright and its Chromium: `uv sync --extra dev --extra browser --extra gui`, then
`.venv/bin/python -m playwright install chromium`. If Chromium cannot be had, say so on the part and run the host's tests;
do not report a browser test as passed that was skipped.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The task and the Board's pages** | the role's words; the Lean leader told it does the task; the pages put back by code at the gate | `realm/library.py`, `core/idea_task.py`, `realm/idea_git.py`; `tests/test_library.py`, `tests/test_idea_gate.py`, `tests/test_task_brief.py` |
| **B. A page's change is tested** | `[gate] browser` patterns; a skipped browser module said; a code task keeps the tests it breaks | `realm/gate_config.py`, `orkcraft.toml`, `realm/idea_git.py` (`parse_tests`), `core/idea_plan.py` or `realm/plans.py`, `gui/static/js/shell/review.js`; `tests/test_idea_gate.py`, a gate config test |
| **C. A gate that could not run** | install rows only for the tool missing; the command named; which Python | `realm/gate_env.py`, `realm/idea_git.py` (`python`), `gui/static/js/shell/review.js`; `tests/test_gate_env_browser.py`, its host test |
| **D. Antigravity's key** | no key offered; its card's words | `realm/tool_hand.py` (`KEYS`), `tools.py` (`_agy_login`); `tests/test_tool_hand.py`, `tests/test_tools.py` |
| **E. Release, and the hand's order** | Release reads when there is a release; a goal's card in front | `gui/ideas_goals.py` (`_read_goal`), `gui/static/js/hand/data.js`, `hand/stacks.js`; `tests/test_gui_goals.py`, `tests/test_hand_desktop_browser.py` |
| **F. The table's words** | a task's stage; a leader's seat; what is ready for main; words and corners that fit | `gui/static/js/table/data.js` (`STAGES`, `stageOf`), `table/steps.js` (`SEAT`), `gui/ideas_gate.py` (`gate`), `table/discard.js`, `table/discard.css`, `hand/hand.css`; `tests/test_table_desktop_browser.py`, `tests/test_discard_table_browser.py`, `tests/test_task_steps_browser.py`, `tests/test_goal_main.py` |
| **G. The spend, and the drive** | Codex's prices; no `$0.00` for what has no price; the model that ran; `drive stop --folder` | `sources/pricing.py`, `realm/spend_report.py`, `core/treasury.py`, `gui/tools_host.py`, `gui/drive.py`; `tests/test_codex_pricing.py`, `tests/test_spend_report.py` |

**Not this spec:** spec 132 B itself (the trial's code stayed in a throwaway clone; it is built again after A, by the trial);
the 37 host tests and the unfinished browser run left by spec 130 D; the models by tier that spec 130 D took out of
`js/settings.js` with no new place. Each is the owner's to send on.

## 0. What the trial found

Spec 132 B, on a clone with no remote and an empty `HOME`, Codex on its subscription, a Tech party at Lean, 4 November 2026:
17 calls, 2.94 million tokens (92% read from the cache), 12.4 minutes of the model in 26. Two tasks of four merged into `dev`.

| Task | What happened | Tokens |
|---|---|---|
| k1 *Mark words* | changed the terms and their tests (+20 lines); also wrote a plan in the Board's page, refused, undone by a second call; the gate could not run (see C); 86 passed once it could | 587,163 |
| k2 *Level marks*, first start | **wrote only a plan, in the Board's page**: *No runtime code changed.* Refused; it undid the page *to HEAD*, but `commit_left` had already committed the edit: refused again, failed | 553,146 |
| k2, *Start again* | wrote the code, edited the page again, undid it from its own commit; 55 passed, merged | 603,642 |
| k3 *Mark coverage* | wrote 221 lines of tests and a plan in the page; undid it to `HEAD`; refused again, failed; its tests never landed | 735,275 |
| k4 *Review marks* | never ran | |

On `dev`, 11 browser tests of the title's marks fail against 2 on `main`; 10 are new. The gate ran only `always`
(`tests/test_architecture.py`, `test_board_alone.py`, `test_updates.py`) for `pane.js`.

The causes, in the code as it is at `2e2039b3`:

- `realm/library.py:70`, the Architect: *Write the plan in the task's own file: the modules, what moves where, the order of the
  steps, and what each step is tested by.* The only file a task is given is the spec page (`core/idea_task.py:305`, *Its spec
  is at …*), under `BOARD_PAGE`.
- `core/idea_plan.py:244`: `t["role"] = lean or …`: at Lean the leader does every task, so the Architect's *You shape the change
  before it is written* is what a code task hears.
- `core/idea_task.py` `_check` (~255): `commit_left` commits what the session left, then `touched(…)` against `merge_into` finds
  the page, then the session is asked to *put back … as they were*. A session that undoes it to `HEAD` undoes nothing.
- `realm/gate_config.py` `gate_files`: `if not gate.custom and p.suffix != ".py": continue`.
- `realm/gate_env.py` `missing`: every package folder with no `node_modules`, whatever is missing. *`pytest` is not installed* offered
  *Install and test again*, which ran `npm ci` in `vscode/`; the run went green only because a `.venv` had been made by hand.
- `realm/idea_git.py` `python`: `.venv/bin/python`, else `sys.executable`: under `uv tool` that has no pytest. The owner's own checkout
  has a `.venv` with no pytest either.
- `realm/tool_hand.py:31`: `"agy": ("GEMINI_API_KEY", "GOOGLE_API_KEY")`, `tools.py:150`: `return True, "api"`. Check then waited 60 s for
  a Google sign-in. `agy --help` names no key.
- `gui/ideas_goals.py:176`: `_read_goal` at a party's save: Release's reading 117,327 tokens and three questions at Start; Tech's 96,622.
- `gui/static/js/table/data.js:120`: `stageOf`: anything neither checking nor running nor failed is *Planning*: a merged task too.
- `gui/static/js/table/steps.js:57`: `shaman: "a Grunt"`, `dryad: "an elf"`: a leader's seat says a member's word.
- `sources/pricing.py`: `OPENAI_PRICES: dict[str, OpenAIPrice] = {}`.

What went well and must stay: the first open (spec 130), Talk and the decision, the plan's split, the result card's plain *Sending it
back would not help: the task cannot install anything*.

## A. The task and the Board's pages (§250.1–2)

1. **The role.** `realm/library.py`, the Architect: the sentence *Write the plan in the task's own file: …* goes. In its place: the plan is
   already made; what is settled about the shape of the change goes in the commit's message. Keep *Keep each module to one job and the
   imports one way* and *split a module before it grows past ~600 lines*. Read every other role in `library.py` for the same ask
   (`grep "own file"` finds one today).
2. **The Lean leader.** Where a task's prompt is made (`core/idea_task.py`, its *# Your role* part), when the task's `role` is the party's
   leader by `goal_team.lean_role`, add a line after the role's text: *You do this task yourself. It is not to be planned: make the change
   it asks for, in this worktree.* For a task of kind `code` only; a check keeps its checker's words.
3. **The page to read.** After *Its spec is at `…`*: *That page is the Board's: read it, never write to it.*
4. **Put back by code.** In `_check`, after `commit_left`: the touched files under `BOARD_PAGE` are restored from the merge base with
   `merge_into` and committed by Orkboard (a new `IdeaGit.restore_pages(path, base, files)`, author as `commit_left`'s, message *The Board's
   pages put back: a task never edits them*). The session is not called and no try is spent. `== the Board's pages put back: <files>` goes in
   the task's log, and an event `task_pages_put_back` (idea, task, files) in `realm/event_log.py`. A file that is not a page is never touched.
5. **Nothing left.** `git.commits(path, start_sha)` counts commits, and after A.4 there are some with no change. Decide by the diff
   against `start_sha`: no difference is *You changed no file. Make the change the task asks for in this worktree.*
6. **Tests.** A task that edits a page and code: the page is as it was on `merge_into`, the code stands, the gate went on, no session call
   was made for it. One that edits only a page: told it changed no file. A page edited and committed by the session itself, and one left
   for `commit_left`: the same. The Architect's text no longer holds *own file* (`tests/test_library.py`). A Lean code task's prompt holds
   the line; a Standard task's does not; a check's does not.

## B. A page's change is tested (§250.3)

1. **The patterns.** `[gate] browser = [...]` in `orkcraft.toml`, read in `realm/gate_config.py` as a new `Gate.browser`, default empty.
   `{stem}` as `map`'s, and a new `{leaf}`, the last folder's name. Unlike `map` they are globs (`Path(root).glob`), sorted. In
   `gate_files`, a touched `.js`, `.css` or `.html` adds them before the `continue`. Only what exists; no pattern, nothing changes, for any project.
2. **This repository.** `orkcraft.toml`: `browser = ["tests/test_{stem}*_browser.py", "tests/test_{leaf}*_browser.py"]`. So `table/pane.js`
   brings `tests/test_table_desktop_browser.py`, `table/column.js` brings `test_column_browser.py` too. Run them once on a touched `pane.js` and
   say in the commit how long they took. If the gate's `timeout_min` would not hold them, raise it for this repository and say so.
3. **Skipped is not passed.** `tests/browser_kit.py` skips a whole module when no Chromium launches. `parse_tests` reads the run's skipped
   count into the task's `tests` (`skipped`); when the run is green with files of `Gate.browser` in it and some are skipped, the record says
   `no_browser: true`. The result card and the task's log say *Browser tests did not run: no Chromium here.* It does not hold the merge.
4. **The plan.** In the plan's rules (`core/idea_plan.py`, or `realm/plans.py`, wherever its prompt's rules are): *A code task changes the tests
   its change breaks, in the same task: the gate runs them when it ends. A later task may add coverage, never repair a task before it.*
5. **Tests.** A touched `table/pane.js` with the patterns: the table's browser tests are in `gate_files`; with no patterns: only `always`. A
   glob that matches nothing adds nothing. A `.py` is untouched by `browser`. `tests.no_browser` from a run that skipped; not from one that ran.

## C. A gate that could not run (§250.4)

1. **Only what is missing.** `could_not_run` already knows the name. Give `gate_env` a `kind_of(what)`, `python` for pytest and for a `No module named` from a
   Python run, `node` for what it knows today, `""` when it cannot tell. `missing(root, what="")` returns the npm rows only when `what` is not a Python tool.
   `npm ci` never runs for `pytest`.
2. **The command named.** A new `python_setup(root)`, read by code: `uv.lock` and a `dev` extra in `pyproject.toml`: `uv sync --extra dev`; a `dev` extra with no
   lock: `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`; else `python -m venv .venv && .venv/bin/pip install pytest`. Nothing runs it: §182.1 stands.
   The task's `tests` carries it (`setup`).
3. **The card.** `shell/review.js`: with no install rows the primary button is *Test again* (today's branch), and under the line a person can copy:
   *Run this in the project's folder, then Test again: `uv sync --extra dev`*. In a code face, so it is taken as written (the pixel face is for headings and buttons).
4. **Which Python.** `IdeaGit.python`: `.venv`'s when it is there (even with no pytest: the card says what to run). Else the first `python3`, then `python`, on the `PATH`
   that imports pytest (asked once, a short run, and kept for the process). Else `sys.executable`, as today.
5. **Tests.** `missing` with `pytest` and an unsatisfied `vscode/package.json`: no rows; with `vitest`: its row. `python_setup` for each of the three. `python`: a `.venv` wins; none, and a
   fake `PATH` python with pytest wins over `sys.executable`; none with pytest, `sys.executable`. The browser test: the card shows *Test again* and the command, never *Install and test again*, for pytest.

## D. Antigravity's key (§250.5)

1. **`realm/tool_hand.py`:** `KEYS` is `tool_errors.TAKES_KEYS` alone, and the comment above it says why. **`tools.py`:** `_agy_login` no longer returns `True, "api"`: it is `None, "subscription"`.
2. **The card.** `third_line("agy", "api", …)` then says what it says for a tool with no key: its `No key … takes is known here: use its subscription`. For Antigravity, in place of that:
   *Antigravity signs in with Google; it takes no key here.* Its `experimental` warning stays where it is.
3. `realm/diagnostics.py` and `_PROVIDER_KEYS` (`tools.py:215`) stay: they name what is in the environment, they do not promise it is used.
4. **Tests.** `tests/test_tool_hand.py`, `tests/test_tools.py`: with `GEMINI_API_KEY` set, `key_found("agy")` is `""`, its `api` row is not `ok`, billing is `subscription`. `tests/test_seat_tool.py` and whatever else named the pair follow.
5. **The owner's check** (on the owner's computer, not a step of this build): a key known to be good, in a shell with an empty `HOME`:
   `HOME=$(mktemp -d) GEMINI_API_KEY=… agy -p "say ok"`. If it answers, D's two lines go back and §250.5 is amended; if it asks for a sign-in, it stands.

## E. Release, and the hand's order (§250.6)

1. **When it reads.** `gui/ideas_goals.py`: `_read_goal` at a save skips a party of craft `release` (`party_recipes`, however a Release party is told today). It reads at the first of: a goal ready for main (`ideas.gate`
   finds one), or the person opening its lens. Once; a reading already kept is not read again (spec 41 §7 stands). Other parties read as they do.
2. **The order in a lane.** `hand/data.js`, where stacks are ordered by their top cards' urgency: a stack of a goal's own (a result, a stop, a decision) lies in front of a party's question with `blocks: false`.
   What blocks still comes first. The Release card must not lie over a result waiting: the trial's result showed only as a 12 px edge.
3. **Tests.** A Start with Tech and Release: Tech's reading is asked for, Release's is not, no Release card in the hand; a goal ready for main: it reads, once. Browser, at the wide width: a result and a party's question in
   one lane: the result is in front and takes the press.

## F. The table's words (§250.7)

1. **A task's stage.** `table/data.js`: `STAGES` gains `review: { word: "To look at", sign: "page" }` (the word the result card already says) and `done: { word: "Done", sign: <the sign a finished card uses> }`; `stageOf` gives them for `state === "review"` and
   `"merged"`. `FRONT` gives each a rank so a cascade's order is unchanged for the rest: to look at in front of *Checking*, done last. `tests/test_table_desktop_browser.py`.
2. **A leader's seat.** `table/steps.js` `SEAT` maps a leader's form to a member's word. A task whose head is its party's leader says *Its leader takes it next*: the host marks the head (`leader: true`, where a task's `head` is put in the snapshot, `realm/board_map.py` or `gui/ideas_map.py`), and `WaitingWindow` reads it.
   Also read `seatWords`'s other callers. §249.3's *an elf takes it next* stands for a member. `tests/test_task_steps_browser.py`.
3. **Ready for main.** `gui/ideas_gate.py` `gate`: a goal counts only when none of its tasks is failed, waiting, ready, running or to look at (the trial said *1 goal ready for main* of a goal failed at 2/4). The page reads the host's answer; it decides nothing. `tests/test_goal_main.py`.
4. **The Board's own commits.** `gate`'s `commits` leaves out commits that touch only `BOARD_PAGE` files, so a laid table with no work has no pile (§247.1: the trial's discard said *2 commits ready for main* right after Start, then *7*). They go into main with the next goal as they do. Commits of code that belong to no goal still count. `tests/test_discard_table_browser.py`.
5. **Words inside the card.** `table/discard.css`: the pile's foot wraps inside its card's window, or is cut with its whole sentence in `title`. Today its first and last words run past the art.
6. **The + card's corner.** `hand/hand.css`: `--hc-lead` in the first lane allows for the card turned (`rotate`), which today reaches 164 px while a stack starts about 148 px in: at 1440 x 900 the stack's left edge is clear of the + card's turned corner. `tests/test_hand_desktop_browser.py` holds it (its `+ 6` stays).

## G. The spend, and the drive (§250.8)

1. **Prices.** `sources/pricing.py` `OPENAI_PRICES` from OpenAI's published pricing page, with the URL and the date it was read in the module's text, as Claude's table has. **Only what the page says**: a model it does not list stays unknown and is never guessed. `tests/test_codex_pricing.py`.
2. **Unknown is not zero.** `realm/spend_report.py`: with every call unpriced, the totals say *no price known for these models*, not `$0.00 (+17 unpriced)`; with some, `$1.20 + 17 calls with no price known`. `core/treasury.py` `words`: the same for the top bar's gold, never `$0.00+` alone. `tests/test_spend_report.py`.
3. **The model that ran.** `gui/tools_host.py` (`tools.check`) and whatever else records a tier in a call's `model`: the trial's calls say `codex laborer` and `agy laborer` beside `codex gpt-6-luna`. A call's record names the model the tool ran, or is empty when it cannot be told. `tests/test_idea_spend.py`.
4. **`drive stop`.** `gui/drive.py`: `--folder` is taken as on the other acts, the positional kept. It failed in the trial, and the server went on with the key in its environment. `tests` of the drive, where `start` and `stop` are.

## The trial again

After A, B and C, on the owner's computer, with `orkboard drive start <clone> --real-tools` or by hand: the same goal, the same party. It is good when no log says *A task never edits the Board's pages*; `task_pages_put_back` may appear, and spends nothing; all four tasks end merged or stop on a real red test; the tests of the marks are green on `dev`; the tokens of `work` are well under the trial's 2.49 million. Then spec 132 B is in, by that goal.
