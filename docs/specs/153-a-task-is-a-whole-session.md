# 153. A task is a whole session: the plan splits only for a reason, tells a task where to start, and claims every Done when line

Decisions §257 (1–3). **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by the spec's author and
merged into `main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves**: **1** A and C, one session (both are the
plan's: `core/idea_plan.py`), after spec 152 B is merged (it may move `make_plan` out of `core/idea_keeper.py`) · **2** B, its
plan's half with wave 1, its prompt's line after spec 151 F is merged (`core/idea_task.py` is F's) · **3** D, with spec 152 E's
runs. No face: the plan's card is as it is; nothing here changes a page.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The grain** | the plan's rule of when to split; what one task's session has cost on this project, said to the planner | `core/idea_plan.py` (`plan_prompt`), `realm/idea_spend.py` (`task_session`); `tests/test_idea_spend.py`, `tests/test_idea_keeper.py` (the prompt) |
| **B. Where to start** | a task's `files` in the plan, kept where they exist; its prompt says them first | `core/idea_plan.py` (the plan's answer, `make_plan` wherever it lies), `realm/task_brief.py` (`start_at`), `core/idea_task.py` (one call, after spec 151 F); `tests/test_idea_keeper.py`, `tests/test_task_brief.py` |
| **C. Every Done when line claimed** | a task's `proves`; the lines no task proves asked once more, then kept and said to the acceptance | `core/idea_plan.py` (`unclaimed`, `plan_one`), `realm/event_log.py`; `tests/test_idea_keeper.py` |
| **D. Measured** | tasks a step, tokens a task, what of a task's `files` it read, the lines claimed | spec 152 E's trial (`docs/trials/152-a-leader-accepts.md`) |

**Not this spec:** merging tasks by code (the rule is the planner's; D measures whether it holds); a session kept across tasks
(spec 35 §0 stands; each task has its worktree); Release's reading by code (§257.7: the tools' spec).

## 0. What is there today

- The plan's prompt (`core/idea_plan.py` `plan_prompt`): *At most `MAX_TASKS` tasks. Each is a brief another Claude session can do
  alone, in a worktree of the repository: what to change, where, and how it is tested; it names the Done when lines it proves.*
  Nothing says when to split; the planner may read the repository (`READS["plan"]` = 6).
- `make_plan` (`core/idea_keeper.py`, 598 lines; spec 152 B may move it to `core/idea_plan.py`) keeps of a task: `title`, `brief`,
  `kind`, `tier`, `after`, `short`, `pick`, `screen`. Where to start is prose in the brief; which lines a task proves is prose too.
- §253's run: three tasks of about 420 thousand tokens each for four lines in three files (§257, Why).
- `idea_spend` keeps a line a call with its step, role, tier, tokens and cost (`<state_dir>/…/spend.jsonl`).

## A. The grain (§257.1)

1. **`idea_spend.task_session(state_dir)`** → `{"tokens", "usd", "n"}`: the median tokens (and dollars, None when unpriced) of the
   project's newest 20 task calls of round 1 (`step == "task"`, not a send back, not a check), `n` how many; `None` under
   `idea_spend.TOO_FEW`.
2. **The prompt's rule**, in place of *At most `MAX_TASKS` tasks*: *Each task is a whole session of its own: on this project one has
   cost about <N> tokens<, $x>* (from 1; with none, *a first guess: 400,000 tokens*). *Split the work only (a) for a part another
   seat does (another tag), (b) for parts that run at once in this party's size (it runs <at_once> at once) and touch no file in
   common, or (c) for a base two or more tasks must wait for. Else one task does it all. At most `MAX_TASKS`.* `at_once` from
   `goal_team.way(size)` (Lean 1, Standard 2, Full 3; a party with no size: 2).
3. **Tests**: `task_session` (none under `TOO_FEW`, the median, round 1 only, checks left out, unpriced); the prompt holds the rule
   with the learned number, with the guess, and with each size's `at_once`.

## B. Where to start (§257.2)

1. **The plan's answer**: each task may give `"files": ["path", …]`, the files it starts at; the prompt's format and its rule say
   so (*the files you read that this task starts at, at most six*). `make_plan` keeps them strictly: strings, relative to the
   repository's root, no `..`, no secret's path (`idea_secrets`), that exist as files at the planner's read of the repository, at
   most 6 (`MAX_FILES`); none kept is no key.
2. **`task_brief.start_at(task)`** → one line, *Start at: `a`, `b`, `c` (its planner read them; read more as you need)*, or "".
3. **The prompt** (`core/idea_task.py`, a working task's): the line first, before the spec's part. **After spec 151 F is merged**;
   until then the plan keeps `files` and no prompt says them.
4. **Tests**: `make_plan` keeps the files that exist and drops the rest (outside the root, `..`, a secret's path, a folder, more than
   six); `start_at`; a working task's prompt starts with it (B.3's part).

## C. Every Done when line claimed (§257.3)

1. **The plan's answer**: each task gives `"proves": [n, …]`, the numbers of its section's *Done when* lines it proves (1 the first);
   the prompt numbers the lines it is given. `make_plan` keeps whole numbers 1 to `spec_sections.MAX_DONE`; a check task none.
2. **`idea_plan.unclaimed(page, party, tasks)`** → the numbers of the party's *Done when* lines that no task's `proves` names; `[]`
   for a page of before (no sections) and for a section with no *Done when*.
3. **Asked once more** (`plan_one`): when lines are unclaimed, the plan's call is made once more with its prompt and one line,
   *These Done when lines no task proves: 2. …; 4. …. Give each to a task, or a task of its own.*; what is still unclaimed after it
   is kept on the plan (`plan["unclaimed"]`) and the plan goes on. Spec 152 B's acceptance is given them: *No task claimed: …*.
   Event `plan_unclaimed` (`idea`, `step`, `lines`, `asked_again`): never a word of the goal.
4. **Tests**: `proves` kept and cleaned; `unclaimed` (all claimed, one not, a page of before, no *Done when*); the second call made
   only when a line is unclaimed and never a third; `unclaimed` kept; the event.

## D. Measured (§256.9)

In spec 152 E's runs, recorded beside its own: the tasks of each step and the reason each was split (the planner's, read from the
briefs); the tokens of each task against §253's (about 420 thousand); of each task's `files`, how many its session read and how
many it changed; the lines claimed and the second calls made. The owner reads whether the rule held; if a plan still splits with no
reason, merging by code is the next spec.

## Done when

- The plan's prompt says what one task's session costs on this project and when to split; a Lean plan of a change like §253's is
  one task.
- A task's `files` are kept only where they exist and, once spec 151 F is merged, its prompt starts with them.
- Every *Done when* line is proved by a task, or the planner was asked once more and the acceptance is told which are not.
- The critical tests pass: `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`, and each part's own.
