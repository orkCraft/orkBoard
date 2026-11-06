# 155. What trial 152 found: a bad page, a step nobody looked at, a doubt and a question settled without the person, the weigher, the Board in the code

Decisions §260; the findings are `docs/trials/152-a-leader-accepts.md` §3 (F1–F9). **Builds:** the cheaper model, a part a
session, each in its own worktree, reviewed by the spec's author and merged into `main` on the critical tests and the part's own
(CLAUDE.md, alpha). **Waves** (parts of a wave share no file): **1** A, B, C, E, F, G · **2** D · **3** H. No new pane, column,
drawer or dialog. **Not this spec:** F4 (the checks into main and a red from before: a goal of its own); F9's tier words on a
potion's card (that card is the trial clone's code, not this repository's); the share of the week on the result.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. One bad page never stops the Board** (§260.1, F1) | the slug from a spec's file name; a page not a slug left out of the list; `check` names it; goal 96 renamed | `realm/read_in_specs.py`, `realm/ideas.py` (`_pages` only), `realm/board_check.py`, `llm-wiki/general/pages/ideas/96-*.md` and `index.md`; `tests/test_read_in_specs.py`, `tests/test_board_check.py`, a test of `ideas.ideas` with a bad page |
| **B. A step nobody looked at; a screen's line** (§260.2, .3, F2, F3) | a task keeps what it changed that people see; the acceptance's finding; the section's and the acceptance's rule | `core/idea_runner.py`, `core/idea_accept.py`, `core/idea_sections.py`; `tests/test_idea_accept.py`, `tests/test_idea_sections.py` |
| **C. The plan and the diff** (§260.4, .9, F5, F9) | no browser test asked of a tool that has no browser; a diff's minus | `core/idea_plan.py`, `realm/idea_git.py`; `tests/test_idea_plan.py`, `tests/test_idea_git.py` |
| **D. A doubt checked, a question settled** (§260.5, .6, F6) | `ground` and `settle`, two read-only calls in Talk | a new `core/idea_ground.py`, `core/idea_talk.py`, `realm/idea_talk_parse.py`, `realm/idea_target.py`; a new `tests/test_idea_ground.py`, `tests/test_idea_talk.py` |
| **E. The weigher weighs only** (§260.7, F6) | its doubt or no opens nothing; its record line | `core/idea_verdict.py`, `realm/idea_objections.py`, `realm/idea_hearing.py`, `core/idea_talk.py` (`_held` and the record's line only); `tests/test_idea_verdict.py`, `tests/test_idea_hearing.py` |
| **F. The Board in the code is laid, its leaders seated** (§260.8, F8) | `laid` read where the pages are; a page's leader installed; a leader's head of its party | `gui/first_open_cards.py`, `gui/ideas.py` (the snapshot's `laid` only), `gui/ideas_goals.py`, `realm/board_map.py`, `realm/goal_team.py`; `tests/test_first_open*.py`, `tests/test_board_map.py`, `tests/test_goal_team.py` |
| **G. Opening writes nothing it need not; history is not news** (§260.8, F8) | no schema-only rewrite; a goal done before this machine read it is seen; no empty brief; To main first | `realm/goal_phase.py`, `gui/ideas_phase.py`, `realm/write_out.py`, `gui/static/js/table/discard.js`; `tests/test_goal_phase.py`, `tests/test_write_out.py`, `tests/test_discard_browser.py` |
| **H. This repository's Board files** | `orkboard init` once B and D are in (their rules change the seats' texts) | `.claude/`, `AGENTS.md`, `llm-wiki/general/` |

## 0. What is there today

- `realm/ideas.py` `state_folder` raises `No goal '<slug>'` for a slug not `[a-z0-9-]+`; `_pages()` yields every `*.md`'s stem;
  `ripe_tick` (`gui/ideas_route.py`) and the Board's snapshot (`gui/ideas_board.py`) read `state` of every goal, so one such page
  raises in each. `realm/read_in_specs.py` `goals_from_specs` takes `path.stem` as it is. `realm/board_check.py` reads no file name.
  `realm/living_specs.py` `slug` makes a slug (a run of anything but `[a-z0-9]` a dash).
- `core/idea_shot.py` `sees(touched)` says whether files changed what people see; `ShotMixin.shoot` (called at
  `core/idea_runner.py` after a task's tests) keeps `shot` on the task: `None` (shots off, nothing seen, or a failure), `{"none": True}`
  (seen, no picture), or the picture. `core/idea_accept.py` `_decided` makes a `[look]` line with no picture and a `[person]` line
  `unseen`; `_accepted` raises each as a finding (`_raise`, source `accept`, told at once).
- `core/idea_sections.py` `rules()`: *A line about a screen names the state it opens in, as a person first meets it* and *Prefer
  `test`*.
- `core/idea_task.py` `NO_BROWSER_HERE` is told to a task whose tool has `browsers=False` (`realm/harnesses.py`: Codex); the
  plan's rules (`core/idea_plan.py`) say nothing of it.
- `realm/idea_git.py` `stats`: `a, _, r = ln.split("\t", 2)[:3]` binds the removed count to `_` and the path to `r`.
- Talk (`core/idea_talk.py` `talk_run`): `hear_whole` (`core/idea_verdict.py`), then the cards' pool, `pass_split`, `pick_three`
  (`realm/idea_talk_parse.py`), `rec["waiting"]`. A leader's `doubt` with a why sets `rec["hearing"]` (`_held`); a `no` makes an
  objection (`realm/idea_objections.py` `made`). `talk_round` reads no file (`realm/idea_target.py` `READS`, §156.8); `diagnose`
  reads four (`core/idea_diagnose.py`). `realm/board_check.py` `reference_exists(root, ref)`.
- The weigher (`core/idea_verdict.py` `weighers`, `weigh_prompt`, `hear_verdict`): its stance has an empty `stance`, `for`,
  `against`, and its verdict counts in `made`, `_held`, `idea_hearing.of_talk`, `rejudges` and `merge_verdicts`. Talk's record line
  (`talk_run`) prints `For: —  Against: —` for it.
- `realm/first_open.py` `laid(state_dir, root)` reads `root / "pages/tracks"`; both callers (`gui/first_open_cards.py`,
  `gui/ideas.py`'s snapshot) pass the repository's root, not the Board's (`self.root()`, the Wiki or the Board's tree). A party's
  leader (`leader: architect`) is a role of `<state_dir>/roles/`, installed only by `goal_save` (`realm/library.py` `install`); with
  none, `gui/ideas_goals.py` `_goal_row` and `realm/board_map.py` (≈ line 468) fall back to the Taskmaster, whose head is its own
  race (`roles.NO_PARTY_RACE`); `board_map` passes no party to `roles.head` at all.
- `realm/goal_phase.py` `mirror` writes a page whose `schema` differs; `goal_phase.moved` calls every page with no state on this
  machine `new`, and `gui/ideas_phase.py` `phase_moved` notes each `moved` for the Board's commit. `realm/write_out.py` `brief_into`
  writes `project.md` with `Nothing yet.` (`write_out_bank.NOTHING`) when the brief is empty. `seen_at` is this machine's
  (`<state_dir>/ideas/<slug>/state.json`); `goal_place.place_of` puts a done goal not seen in the discard;
  `gui/static/js/table/discard.js` `DiscardView` draws *Done, not yet seen* before *Ready for main* and its **To main**.

## A. One bad page never stops the Board (§260.1)

1. `read_in_specs.goals_from_specs`: a goal's slug is `living_specs.slug(path.stem)` (`96-orkui-0.15.0-copied` →
   `96-orkui-0-15-0-copied`); `lay` writes the page under it; a page already laid under it is the same goal (not laid twice).
2. `ideas._pages()` yields no page whose stem is not `[a-z0-9-]+`: the Board, its ticks and every reader of `ideas.ideas` go on
   without it. Nothing else of `ideas.py` changes.
3. `board_check`: a file of `pages/ideas/` or `pages/tracks/` whose stem is not a slug is a finding: *`<file>`: a goal's file name
   is its slug: rename it `<slug>.md`* (a party's: *a party's file name*), the slug made as A.1.
4. This repository: `git mv` goal 96's page to `96-orkui-0-15-0-copied.md`, its line in `pages/ideas/index.md` with it.
5. Tests: A.1 on a spec named with dots; `ideas.ideas` with a bad page beside a good one lists the good one; `check` names the
   bad one and its slug; this repository's `orkboard check` clean.

## B. A step nobody looked at; a screen's line (§260.2, §260.3)

1. `core/idea_runner.py`, where a task's touched files are read after its tests: the task keeps `sees`, the touched files for which
   `idea_shot.sees([f])` is true, at most six, `[]` for none, whether shots are on or not (`_set_task(..., sees=[...])`).
2. `core/idea_accept.py`, beside `_decided`: `_unlooked(slug, lines, mine)` → the files, or `[]`: some task of the step has `sees`,
   no task of it has a picture (`_picture`), and no line of the step's *Done when* (all of them, not only those served) is `[look]`
   or `[person]`. In `_accepted`, after the `unseen` lines are raised and before `_keep`: with files, `self._raise(slug, party,
   f"{party}: nobody looked at step {n}", f"Nobody looked at what this step changed: {', '.join(files)}", "", "")`, once a step
   (not again on a second round). The verdict is not changed by it.
3. `_proofs_text`: when some task of the step has `sees`, one more line after the lines: *This step changed what people see. A
   `[test]` line about a screen is met only if its test opens the screen in the state the line names, as a person first meets it:
   else it is not met.*
4. `core/idea_sections.py` `rules()`: *Prefer `test`* becomes *`test` for a line about what a person sees only when its test opens
   the screen in the state the line names, as a person first meets it; else `look`. Prefer `test` for the rest.* The prompt's
   test (`tests/test_agent_rules_prompts.py`) changes with it, on purpose, by this spec.
5. Tests: B.1 (a `.css` and a `.py` touched → `sees` is the `.css`); B.2 with a step that changed a page and has only `[test]`
   lines → the finding with its files, told; with a `[look]` line → only the existing *Nobody could look at*; with a picture →
   none; with no `sees` → none; B.3's line in the prompt only with `sees`; B.4's words in the section's prompt.

## C. The plan and the diff (§260.4, §260.9)

1. `core/idea_plan.py`: the plan's prompt knows whether the tool that runs the goal's tasks can start a browser (the harness's
   `browsers`, as `core/idea_task.py` reads it); when it cannot, one rule more after *A code task changes the tests its change
   breaks…*: *The tasks' tool cannot start a browser or serve a page: never ask a task to run a browser test or a test that opens a
   local port; the gate runs them.*
2. `realm/idea_git.py` `stats`: `a, r, _ = …`, so the removed count is counted; `--no-renames`, as `diff` has.
3. Tests: C.1's rule present for a tool with `browsers=False`, absent otherwise; `stats` on a commit that removes lines.

## D. A doubt checked, a question settled (§260.5, §260.6)

1. **The steps**: `ground` and `settle` in `realm/idea_target.py` (`STEPS`, and every table a step needs: its tier pick as
   `talk_round`'s, its context and budget, `READS` 4 each, its cost). Both read only (Read, Grep, Glob: a call's default tools),
   from the repository's root.
2. **A doubt says what to look up**: `core/idea_talk.py` `rules()`: *A `doubt` that reading the code would settle says what to
   look up in `check` (a name, a file, a question of one line); else leave `check` empty.* `realm/idea_talk_parse.py`
   `clean_verdict` keeps `check` (at most 200 characters) with a `doubt` only; the stance keeps it.
3. **`ground`** (`core/idea_ground.py`, a mixin as `core/idea_diagnose.py` is): in `talk_run`, after `hear_whole` and before the
   cards' pool, for each stance with a `doubt` and a `check`, one call: the goal's words, the doubt's why, its check, the map's text
   and the files it names (`self.reads("ground", files)`); its answer `{"settled": true|false, "found": "<one line>"}`. Settled:
   the stance's verdict is `go`, its why *checked: <found>*; not: the doubt stands, its why gains *— checked: <found>*. A failed or
   unreadable call leaves the doubt as it was. Each check is logged (`event_log`, `talk_ground`: idea, party, settled).
4. **`settle`**: in `talk_run` (and `second_run`), with the cards' pool before `pass_split`, one call for all the round's cards
   that are the person's: each card's ask and choices, the goal's words; told to look in `docs/decisions.md` and `docs/specs/`
   (Grep first) for a decision or spec that settles a card, and to answer only where one says it; its answer
   `{"settled": [{"n": <card>, "pick": <choice index>, "ref": "§258.7" | "spec 154 C.1", "why": "<one line>"}]}`. Code keeps one
   only when `reference_exists(root, ref)` and the pick is a choice of the card: that card is closed as a card the leader's pick
   closes (the pool's `defaults`), its answer kept with `by` the reference; Talk's record gains a line *Answered by <ref>: <ask> —
   <choice>*. The rest go on as today. No card → no call.
5. Tests (`tests/test_idea_ground.py`, `tests/test_idea_talk.py`, with a stub call): a doubt with `check` settled becomes go, not
   settled stays with its finding, a failed call changes nothing, a doubt with no `check` calls nothing; `settle` closes a card by
   an existing reference and a choice of its own, keeps one whose reference does not exist or whose pick is not a choice, and
   calls nothing with no card; `clean_verdict` keeps `check` with a doubt only.

## E. The weigher weighs only (§260.7)

1. A weigher's stance (`weigher: true`) counts in no objection (`idea_objections.made`), no hearing (`core/idea_talk.py` `_held`,
   `idea_hearing.of_talk`'s sides) and no re-judging (`core/idea_verdict.py` `rejudges`, `merge_verdicts`); its `priority` and
   `after` are kept as today (`realm/night_order.py` reads them).
2. `weigh_prompt` asks only for `priority`, `why` and `after` (no `go`/`doubt`/`no`); `hear_verdict` keeps them.
3. Talk's record line (`talk_run`): a weigher's is `<name> weighs it: <priority> — <why>`, never `For: —  Against: —`.
4. Tests: a weigher's `no` makes no objection and its `doubt` no hearing, its priority is kept, its record line.

## F. The Board in the code is laid, its leaders seated (§260.8)

1. `first_open.laid` is called with the Board's root (`ideas.root(False)` on the host's side, as the Board reads its pages) in
   `gui/first_open_cards.py` and the snapshot of `gui/ideas.py`: a project whose Board has parties is laid at once (§232.1).
2. `realm/goal_team.py` `seat_leaders(root, state_dir)`: each party whose page names a `leader` with no role on this machine and in
   the library (`library.BY_ID`) has it installed (`library.install`); called where the Board is read on the host's side before
   the tabs are built. A leader neither installed nor in the library still falls back to the Taskmaster.
3. A party's leader wears its party's race: `realm/board_map.py` builds a leader's head with its party and lead as
   `goal_team.head_in` does.
4. Tests: `laid` true for a project whose parties are under its Wiki; a page's `leader: architect` installed and its tab's leader
   the architect, its head of the party's race; a leader not in the library falls back.

## G. Opening writes nothing it need not; history is not news (§260.8)

1. `goal_phase.mirror` writes a page only when a key other than `schema` changes; a page it writes gets today's schema, as now
   (§255.12).
2. A goal whose page is `done` and that has no state on this machine (`goal_phase.moved`'s `new`) is seen when it is first read:
   its state's `seen_at` is that moment; it is not noted `moved` for a commit. A goal of another phase is moved as today.
3. `write_out.brief_into` writes no `project.md` while every part of the brief is empty.
4. `discard.js` `DiscardView`: *Ready for main* and its **To main** before *Done, not yet seen*.
5. Tests: a schema-1 page whose phase is unchanged is not written; a done page new to this machine is seen and in history, not in
   the discard, and makes no commit; an empty brief writes no file; the discard's order (browser test).

## H. This repository's Board files

`orkboard init` here once B and D are merged (the sections' and Talk's rules change the seats' texts, spec 154 A): the files
written again, committed as the Board's files are; `orkboard check` clean.

## Done when

- [test] When Orkboard opens a project with a goal page named with dots, then the Board lists the other goals, its ticks run, and
  `orkboard check` names the page and the slug it should have.
- [test] When a step's tasks changed what people see, it has no picture and no `[look]` or `[person]` line, then its acceptance
  tells the person *Nobody looked at what this step changed*, with the files.
- [test] When a Talk leader doubts with a `check` the code settles, then the doubt is a go with what was found and no hearing waits;
  when a reference settles a person's question, then the question is closed with that reference and does not reach the hand.
- [test] When Product weighs a goal not routed to it with a no, then no objection or hearing waits and its priority is kept.
- [test] When a person first opens a clone whose Board is in its code, with parties, then no party is asked for, each leader is its
  page's with its party's race, no page is committed for its schema, and a goal done before is not in *Done, not yet seen*.
- The critical tests pass: `tests/test_architecture.py` (`core/idea_ground.py` imports no `gui/`), `tests/test_board_alone.py`,
  `tests/test_updates.py`, and each part's own.
