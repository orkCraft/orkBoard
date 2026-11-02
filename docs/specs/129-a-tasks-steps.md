# 129. A task's steps: what its worker is on now, the same on Claude Code, Codex and Antigravity

Decisions §207 (1–4). **Builds:** the cheaper model, H1 and H2 side by side, the spec's author reviewing and merging ·
**Review:** the critical tests and each part's own · P1. After spec 128 (its column, its cards). The look: the card's
label row and its lifted face as `docs/mockups/goal-card/` draws a task card.

| Part | What | Where (and its tests) |
|---|---|---|
| **H1. Steps on the host** | the steps file and its rule in the working prompt; the tools' own to-do lists read where they stream; what it is doing as the fallback; the snapshot's `steps` on a task; `orkboard steps-check` | new `realm/task_steps.py` (pure: parse, merge, clean), the runner (`core/idea_runner.py`, `realm/jobs.py` where a task's run is read), the working prompts' rules, `realm/harness_claude.py` / `realm/harness_tools.py` (a working run's output format), `realm/board_map.py` (the task's `steps`), a new CLI command; `tests/test_task_steps.py`, `tests/fixtures/steps/` |
| **H2. Steps on the page** | the card's label row (pips and the step now), the lifted card's list, the column card's count, the narrow width | `table/card.js`, `table/data.js` (`stageOf`, words), `table/work.css` or a new `table/steps.css`, the lifted task's face, `table/piles.js` (the count); `tests/test_task_steps_browser.py` |

## The shape (both parts build to it)

A task in the snapshot (`mapData.nodes[].tasks[]`) carries, while it is at work or checked, `steps`:
`{items: [{text, state}], now: <index or -1>, done: <int>, total: <int>, source: "file" | "todo" | "activity", doing: <text>}`
— `items` at most 6, each `text` at most 40 characters, `state` `done`, `now` or `next`; `doing` the activity line
(*edits lobby.ts*, *runs the tests*), "" when there is none; `steps` absent when nothing is known. A task done keeps its
last steps, all `done`.

## H1. Steps on the host

1. **The rule in the working prompt** (every tool): *Keep your steps in `.ork-steps.json` at the worktree's root: a JSON
   list of at most six `{"step": "<a few words>", "state": "done" | "now" | "next"}`; write it before you start and
   again whenever a step changes.* The file is put in the worktree's `.git/info/exclude` when the worktree is made, and
   a landing never takes it (checked where a task's work is landed).
2. **Read as the task runs**: the runner reads the file every 3 s while the task's run is alive (its mtime first: no
   read when unchanged) and keeps the cleaned steps beside the task (`<state_dir>/ideas/<slug>/<tid>.steps.json`), so
   the snapshot reads them without touching the worktree. Cleaned: at most six, text cut to 40 characters on a word, at
   most one `now` (the first), unknown states `next`.
3. **The tools' own lists**, read where the output streams while it runs:
   - **Claude Code**: a working run moves to `--output-format stream-json --verbose` (its result is read from the last
     `result` event, as a reading run's already is: `harness_claude.result`); a `tool_use` of `TodoWrite` gives
     `todos: [{content, status: pending|in_progress|completed, activeForm}]` → steps (`activeForm` for the one now).
   - **Codex**: `exec --json` events whose item is a to-do/plan list (`item.type` `todo_list` with `items: [{text,
     completed}]`, on `item.started|updated|completed`; and the `update_plan` call's `plan: [{step, status}]` where a
     version prints it) → steps.
   - **Antigravity (agy)**: its `--output-format json` is one envelope at the end: no stream; the file (1) is its source.
     If `agy` gains a streaming format, it is read the same way (a reader per tool, `task_steps.reader_for(harness)`).
   The file wins when it is there; a tool's own list fills in while it is missing.
4. **What it is doing**, with neither: the worktree's changed files (`git status --porcelain`, the latest by mtime:
   *edits lobby.ts*) and, where the output streams, the last command (*runs the tests* for a test command the task's
   checks name, else *runs <its first word>*). `source: "activity"`, `items` empty, `doing` the line.
5. **The snapshot**: `board_map` gives each task at work or checked its `steps` (the shape above), from the kept file.
6. **`orkboard steps-check --tool claude|codex|agy`**: makes a scratch git repository with a two-file task (*add a
   function and its test*), runs it as a working task of that tool (the real argv, the real prompt rule), and prints
   each steps update seen with its source and time, then `ok` when at least two updates and a last one all `done`
   were seen from the file or the tool's list; else what it saw and why not. It needs the tool installed and signed
   in; it spends a little of the tool's limit (said before it runs, `--yes` to skip the question).
7. **Tests** (`tests/test_task_steps.py`): recorded outputs in `tests/fixtures/steps/` — Claude Code stream-json with
   `TodoWrite` calls, Codex `exec --json` with a to-do list's started/updated/completed items, an agy JSON envelope with
   no list — and steps files; the readers, the cleaning, the merge (file wins, list fills in, activity last), the prompt
   rule present in each tool's working prompt, the exclude line, a landing refusing the file, the snapshot's shape.
   The Claude Code working run's result still read from stream-json (its tests kept green).

## H2. Steps on the page

1. **The label row** of a task's card (the front card of a cascade, the lifted one, the plan's cards of spec 128 F):
   *Doing 2/5 · tests for join* — the stage's word, `done+1`/`total`, the pips (orkUI's cell size: 6 × 6 squares, 2 px
   apart, done filled in the ink, the one now in the goal's colour and glowing with orkUI's `.is-glowing` rhythm, next
   faint), the step now cut to one line. With `source: "activity"`: no pips, the `doing` line in the muted ink. The
   time worked moves to the card's words (`aria-label`, its title). A cascade's strips keep their stage sign only.
2. **The lifted card** lists the steps (✓ done in the muted ink, the one now lit, the next faint) beside its *Done
   when*, with the source said small (*from its own list*, *from its steps file*, *what it is doing*).
3. **The column's card** of a goal at work (spec 128 B) says its tasks' count at its foot (*3/7*: tasks done of all),
   not the steps.
4. **Under 760 px** the token shows the pips only.
5. **Words**: *Doing*, *Checking*, the step's own words (a person's words: the body face, never the pixel face).
6. **Tests** (`tests/test_task_steps_browser.py`, a fake host with `steps` on tasks): the label row's text and pips,
   the glowing one, activity without pips, the lifted list and its source, the column's count, the narrow pips, no
   steps → today's label.

**As built (H2).** `table/steps.js` holds the page's reading of `steps` (`stepsOf`: at most six items, numbers in range, an activity only with a `doing` line; none → null, so a task with no steps keeps today's label) and the little components:
`Pips` (orkUI's `.ork-pips`, squares of `--ork-3` = 6 px with `--ork-1` = 2 px between; the one now takes the goal's element colour and, while the task is at work, glows with orkUI's own `ork-glow` keyframes, 2.4 s in six steps, still under
reduced motion; done in the ink, next in the faint `--ork-frame`), `StepNow` (the body face, one line, ellipsis; the muted ink for an activity) and `StepsList`. The sheet is `table/steps.css`, linked after `goalview.css` in `frame/frame.js`.
- **The label** is three short lines in the card's 144 px, not one: the stage row (*Doing 2/5*, the flame, the gem at the right), under it the pips, under them the step now (the pips beside the stage word did not fit: *Doing 2…*). It
  shows only while the stage is *Doing* or *Checking* (a failed task stays *Doing*, its pip now lit but not glowing); a task waiting to start or done keeps today's label. The whole line (*Doing 2/5 · tests for join*) is the card's
  `aria-label`, with *worked 1 m 12 s* after it, and the time is in the `title` too (*the goal · worked 1 m 12 s*); a task with steps no longer says the time on its label, one without keeps *Doing · 1 m 12 s*. The plan's cards are the same
  `TaskCard`; a cascade's strips (`TaskEdge`) are untouched. With every step done and none now it reads *Checking 4/4* (no step line, no pip glowing).
- **The lifted card** (`TaskBack`) has a *Steps* section after *Does it*: ✓ done muted, the one now in the ink (`aria-current="step"`), the next faint, and under them the source small (`file` *from its steps file*, `todo` *from its own
  list*, `activity` *what it is doing*, its `doing` line lit, no list). A task's back has no *Done when* of its own (that is the goal's, in its spec and at the leader), so the list stands where the task's own facts are.
- **The column** (`table/piles.js` `tasksCount`): the foot of a card of a goal at work (not put off) says *done/total* of its tasks (merged of those not dropped), with `title` and `aria-label` *1 of 3 tasks finished* (not *done*: that
  matched the *Done* button's name in older tests).
- **Under 760 px** the token (`Token`) draws the pips alone, in 4 px squares so six lie in its 36 px; its label and title carry the line.
- Tests: `tests/test_task_steps_browser.py`, a `StepsHost` whose tasks carry `steps` (a steps file, an activity, a tool's list with a long step, a check with all steps done, a task with none).
