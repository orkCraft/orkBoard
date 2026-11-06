# 152. A leader leads and accepts: a party is its leader and one who does, the sizes as decided, a step accepted by its leader, a base accepted early, the rules and the words

Decisions §256 (1–3, 8; 9's first spec) and §257 (4–6). **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by
the spec's author and merged into `main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves** (parts of a wave
share no file): **1** A · **2** B (after A) · **3** C · **4** F (after C) · **5** D (after F and spec 151 F) · **6** E. No new pane, column, drawer, dialog nor card kind (§104.0, §145): what
the person decides comes through the quality card that is there (spec 132). F changes the page's format (a *Done when* line's
proof) and so the pages' schema, D the Board's rules and so the rules' schema: **both 2** (§255.12, §257.4).

**With spec 151** (§256.8), being built: its parts A, B, C and D are merged when this is written, E, F, H and G are not. A, B and
C touch none of the files of E, F and H. D touches `realm/lexicon.py` and `core/idea_task.py`, which 151 F changes, and so waits
for F. 151 C holds every seat's prompt to a stored text (`tests/prompts_151/`, `tests/test_agent_rules_prompts.py`): a part here
that changes a leader's words writes those texts again (`ORKCRAFT_WRITE_PROMPTS=1`) for the prompts it means to change and no
other, and its review reads their diff. The acceptance is working state (the plan) and
journal lines, which 151 B already mirrors into the Board's folder: nothing here writes `.orkcraft/` differently, and F's mark on
a *Done when* line is the one change to a page.
E's goal is not one of 151 G's.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The leader leads, one does** | the leader's tier its own at every size; never a task's doer; a party holds one who does; the checks by size; Release's seats; the leaders' words; the faces of Lean | `realm/party_recipes.py` (`tiers_for`, Release's squad), `realm/goal_team.py` (`WAY`, `checkers`, `lean_role` gone, the minimum), `realm/project_stage.py` (Release's tier), `realm/idea_checks.py` (`with_check_tasks` by size), `core/idea_plan.py` (`plan_one`), `core/idea_revise.py`, `core/idea_leader_change.py`, `realm/library.py` (the leaders' words), `gui/ideas_goals.py` and `realm/party_resize.py` (the minimum), `gui/ideas_map.py` (`marks_of`), `gui/static/js/table/partyseats2.js`, `gui/static/js/frame/firstopen.js`; `tests/test_party_recipes.py`, `tests/test_goal_team.py`, `tests/test_idea_checks.py`, `tests/test_idea_keeper.py`, `tests/test_library.py`, `tests/test_party_size.py`, `tests/test_gui_goals.py`, `tests/test_map_party_marks.py`, `tests/test_parties_card_browser.py`, `tests/prompts_151/` (only the leaders' words A.6 changes) |
| **B. A step accepted by its leader** | after a step's tasks land, its leader accepts it against its section, a line met, not met or *cannot see* (§257.5); back twice at most, then findings; the next step and the goal's end wait for it; its journal; its cost said before | new `core/idea_accept.py` (`AcceptMixin`, wired in `core/idea_keeper.py`'s bases and `tick`), `realm/idea_route.py` (`accepted`, `next_step`), `core/idea_runner.py` (the goal's end waits; its handover moved out first: it is past 600 lines), `realm/idea_target.py` (step `accept_step`), `realm/idea_spend.py` (`STEP_STAGE`), `realm/findings.py` (source `accept`, `ripe`), `realm/journals.py` and `realm/journal_notes.py` (the kinds and their writers), `realm/goal_route.py` (`_calls`), `realm/party_price.py`, `gui/static/js/arena/arenawords.js` and `gui/static/js/table/data.js` (*is accepting*); new `tests/test_idea_accept.py`, `tests/test_idea_route.py`, `tests/test_runner_35.py`, `tests/test_findings.py`, `tests/test_journals.py`, `tests/test_goal_route.py`, `tests/test_party_price.py` |
| **C. A base accepted early** | a task two or more of its step wait for is accepted as it lands; they wait for it | `core/idea_accept.py` (`bases`), `core/idea_plan.py` (`readiness`); `tests/test_idea_accept.py`, `tests/test_idea_keeper.py` |
| **D. The rules, the roles and the words** | *Accept* in the rules' way of a goal and in BOARD.md; each leader's role file's part on accepting; the rules' schema 2; the Lean task's line gone; a task told the Board's rules are not its own (§257.6); `TERMS` | `core/idea_accept.py` (`instruction`), 151 C's `realm/agent_rules_text.py` (`seat_text`, `agents_body`, `board_md`, `SCHEMA`), `core/idea_task.py` (`LEAN_DOES`, `_does_it_itself`), `realm/lexicon.py`; `tests/test_agent_rules.py`, `tests/test_agent_rules_prompts.py` (a stored acceptance prompt), `tests/test_task_pages.py`, `tests/test_lexicon.py` |
| **E. Measured** | a goal at Lean and one at Standard on this repository, against §253's run | `docs/trials/152-a-leader-accepts.md`; a clone, the owner's computer or a cloud session |
| **F. A Done when line says how it is proven** | `[test]`, `[look]`, `[person]` on a section's *Done when* lines (§257.4); a test line's test written first; the acceptance by proof; the pages' schema 2 | `realm/spec_sections.py` (a line's proof), `core/idea_sections.py` (the section's answer and `instruction`), `realm/task_brief.py` (a test line's task told to write its test first), `core/idea_accept.py` (by proof), `realm/goal_phase.py` (`SCHEMA`); `tests/test_spec_sections.py`, `tests/test_idea_sections.py`, `tests/test_task_brief.py`, `tests/test_idea_accept.py`, `tests/test_goal_phase.py`, `tests/prompts_151/section_*.txt` (written again: the section's prompt changes on purpose) |

**Not this spec** (§256.9, a spec each): the leader's dossier (§256.4); the reuse of what a leader said, the cache and the batch
(§256.5); the recipes of a craft's way (§256.7); the tools (§256.6). Nor `realm/way_down.py`'s estimate of what a change pulls (it
prices checks, not acceptances, until the dossier's spec).

## 0. What is there today

- **The tiers by size** (`party_recipes.tiers_for`): Lean every seat `warrior`, the leader too; Standard the leader `elder`, the
  first who does `warrior`, the others as the library has them; Full the leader and the checkers `elder`, those who do `warrior`;
  Release's leader alone `warrior` at every size. `project_stage.py` reads Release's tier as `tiers_for(RELEASE_MANAGER, [], "lean")`.
  The leaders' library tiers: `elder`, but the analyst (Run, LiveOps) and the Release manager `warrior`.
- **Who does a task** (`core/idea_plan.py` `plan_one`): at Lean every task's `role` is the leader (`goal_team.lean_role`); else the
  squad's seat that takes its tag, the leader added to the squad for the tags no one else takes (`team = [*team, lead]`), else the
  project's role of the tag, else Grunt (`roles.role_for`). `core/idea_revise.py` and `core/idea_leader_change.py` do the same.
  A Lean leader's code task is told *You do this task yourself* (`core/idea_task.py` `LEAN_DOES`, spec 143 A.2).
- **The checks** (`idea_checks.with_check_tasks`, from `core/idea_plan.py`): a check task for every checker of the squad whose
  check applies, whatever the size; at Lean then given to the leader with the rest. `goal_team.WAY` and `goal_team.checkers` say
  §151.2's table and are read only by the faces. With no checker no check task is planned.
- **A step's end** (spec 99 §9): the runner's tick holds a goal whose step's tasks are all in and whose route has another
  (`idea_route.steps_left`) at `working`, and the keeper's tick has the next party plan (`plan_next`); with none left the runner
  ends it (`_finish`: `done`). `core/idea_runner.py` is 630 lines, `core/idea_keeper.py` 598.
- **What a goal made against what it promised** (§253.9): `goal_result.of`/`judge`, by code, for the person's reading.
- **Findings** (spec 132 D): `findings.add` (sources `verdict`, `check`, `lens`, `concern`, `hypothesis`, `measure`), told by
  their leaders (`finding`), sorted by the Orkmaster (`finding_level`), answered on the quality card (*Fix it there*, *Not now*,
  *Another level…*).
- **The faces**: *Lean: the leader does it, and checks it itself* (`table/partyseats2.js` `LEAN_LINE`, every seat a shadow at
  Lean), *Lean · the leader does it* (`frame/firstopen.js` `seatLine`); a Lean party's shield stands faint (`gui/ideas_map.py`
  `marks_of`); *<leader> is planning* (`arena/arenawords.js`).

## A. The leader leads, one does (§256.1–2)

1. **The leader's tier is its own** (`party_recipes.tiers_for(leader, team, size)`): the leader `elder` at every size (Lean
   too), the Release manager `warrior` at every size (§151.6); those who do and the checkers as today (Lean: those who do
   `warrior`; Standard: the first who does `warrior`; Full: those who do `warrior`, the checkers `elder`). A model the person set
   on a seat stays (`goal_team.seat_role`, unchanged). `project_stage.py`'s Release tier reads the Release manager's own tier,
   not a Lean party's. The leader's calls run on each step's tier under the Target as at every size (`idea_target.keeper_pick`:
   a leader at `elder` takes the step's own), and so a Lean party's Talk is no longer raised to `warrior` by its leader's seat.
2. **The leader never does a task**: `goal_team.lean_role` goes, and with it its callers' branch (`plan_one`, `core/idea_revise.py`,
   `core/idea_leader_change.py`). A task's `role` is the squad's seat that takes its tag; the leader is **not** added to the squad
   for that (`team = [*team, lead]` goes); a tag no seat takes goes to the project's role of the tag, else Grunt
   (`roles.role_for`, unchanged), and the plan's `missing` (spec 52 §2.6) says so as today. `core/idea_task.py`'s `LEAN_DOES`
   and `_does_it_itself` stay until D (no task's role is a Lean leader any more, so they never apply; 151 F touches the file).
3. **A party holds one who does**: `goal_team.MIN_DOES = 1`. `ideas.goal_save` and the party's making (`gui/ideas_goals.py`) refuse
   a squad with no seat whose band is `build`: *A party needs one who does besides its leader*; `party_resize` never leaves
   none. Every craft's recipe holds one. A party made before with none keeps its seats; its tasks go as 2 says (Grunt at the end).
4. **The checks by size**: `idea_checks.with_check_tasks(tasks, kept_, checks, make, size="")`: `lean` none; `standard` the first
   check of the squad's order that applies; `full` every check that applies; `""` (a party made before sizes) every one, as
   today. `plan_one` passes the party's size (`goal_team.size_of`); the revise and the change the same where they add checks.
   `goal_team.WAY` gains `accept` as every size's last stage (`("plan", "do", "accept")`, `("plan", "do", "check", "accept")`);
   `goal_team.checkers` never names the leader in `by`: with no checker it answers `{"by": [], "leader": True, "own_tests": False}`
   at every size, Lean too (`leader` now says that the leader's acceptance is the only check).
5. **Release's seats** (§256.2, §157): the recipe's `squad` is `["release-engineer", "release-notes"]` (Novice each; the checker
   stays a seat the person may tick); Lean and locked as today. A Release party made before keeps its seats.
6. **The leaders' words** (`realm/library.py`): no leader's instruction has it make a thing: the Art director's *Draw and record
   nothing yourself unless the party is lean.* becomes *Draw and record nothing yourself.*; find any other (*yourself*, *you
   write*, *you build*, *unless the party is lean*) and say instead what it plans and accepts. The role files 151 C wrote follow
   by their hash at the host's next start (151 C.5); the stored prompts that hold those words are written again (see above).
7. **The faces**: `LEAN_LINE` *Lean: one does it, the leader accepts it*; `seatsOf(v, "build", "lean")` the first who does on,
   the rest shadows, `seatsOf(v, "check", "lean")` none on; `seatLine` at Lean *Lean · 1 does · the leader accepts*; at Standard
   and Full with no checker on, *· the leader accepts* where *· n check* would stand. `marks_of`: the shield is the tool of the
   seats that check, else the leader's (its acceptance), **at every size**: at Lean `checks_tool` is the leader's tool and
   `checks_default` follows the leader's side; `lean` stays in the answer for the page.
8. **Tests**: `tiers_for` gives the leader `elder` at Lean and the Release manager `warrior` at every size; `project_stage`'s
   Release tier; no task of a Lean, Standard or Full plan has the leader's role, a tag no seat takes goes to the project's role
   or Grunt and is in `missing`; the same in a revise and a change; `goal_save` refuses a squad with no one who does, a party of
   before with none still plans; `with_check_tasks` by size (none, the first, every, every with no size) on a squad with two
   checkers; `WAY` and `checkers`; Release's recipe; the Art director's words; `marks_of` at Lean (the leader's tool on the
   shield); the parties' card's Lean line (`tests/test_parties_card_browser.py`).

## B. A step accepted by its leader (§256.3)

1. **When.** `idea_route.accepted(plan, n)`: the step's acceptance is `accepted` or `gone_on` (`plan["accepts"][str(n)]["verdict"]`).
   A step **is due** when its tasks are all in (`step_done`, one at least merged) and it is not accepted. `idea_route.next_step`
   answers only for a step done **and** accepted; the runner ends the goal (`_finish`, `done`) only when its last step is
   accepted: while it is due the goal stays `working` and the runner keeps it as it keeps one with a step left. **First** the
   runner's handover (the block of `tick` that holds a goal between steps and ends it) moves out of `core/idea_runner.py` into a
   module of its own or `core/idea_landing.py`, its behaviour unchanged (the runner is past ~600 lines), then the one condition is
   added. The keeper's `tick`: a goal `working`, not busy, its step due → `accept_due(slug)` begins it in the background
   (`_start(slug, "accepting", …)`) **before** `plan_next`; one line in `tick`, the rest in `core/idea_accept.py`. `core/idea_keeper.py` is
   598 lines: if the wiring takes it past 600, `make_plan` and its helpers move to `core/idea_plan.py` first, re-exported from the keeper
   as the plan's other helpers are. A step whose
   tasks were all dropped is not accepted. A goal of before (one step, no `plan.route`) is accepted the same. The goal's state is
   not new: it stays `working` (§255.3's phase `work`), and `accepting` is a busy run's name as `planning` is.
2. **The call** (`core/idea_accept.py`, `AcceptMixin` of `IdeaKeeper`, as `idea_findings.py`'s): step **`accept_step`**, as the
   step's party's leader (the goal lies in that party since its step was planned: `PlanMixin._into`), its voice first
   (`keeper.ask`). `idea_target`: `MATRIX["accept_step"]` `elder` at every Target, effort `low` · `medium` · `high`;
   `READS["accept_step"] = 4` (it may open the files its step changed and its pictures, no other); `CONTEXT` 14,000;
   `CAPS` 0.30; `idea_spend.STEP_STAGE["accept_step"] = "work"`. It is given, cut in this order (`idea_target.cut`):
   - its section whole (*Why*, *Done when*, *Checks*, *Will be*, *Out*: `spec_sections`), and of a page of before its *Done when*;
   - what code read of the promise: `goal_result.judge` for its party (each *Will be* line `ok` · `differs` · `missing`, and
     `extra`) and each *Done when* line with the tasks under it (§253.9);
   - each task of the step: its title, state, files with their lines added and removed, its gate's record (passed, failed, what
     it left, red before: §253.5), a checker's findings left (Standard, Full), its pictures' paths (`idea_shots`);
   - what it said of this goal in Talk (its journal's `stance` entry of the goal, `journals.of_goal`: the first piece of
     §256.4), its slices (`idea_slices.parts`), its journal (`idea_journal.parts`).
   It answers `{"verdict": "accepted" | "back", "done_when": [{"n", "met", "why"}], "back": [{"what", "where", "task", "done_when"}],
   "learned": ["…"]}`, cleaned strictly (`clean`): `back` at most 4, each line at most 200 characters; `learned` at most 2 lines
   (`journals.TEXT_CHARS`); `back` with no item reads as accepted; `task` a task of the step or ""; `done_when` a line's number
   or 0; a line's `met` is `true`, `false` or `"unseen"` (§257.5: it **cannot see** it: a picture or Play it needs is not there, or
   only the person can judge it), anything else read as `false`. An answer that is not read: one more try.
3. **What it does.** Kept on the plan: `plan["accepts"][str(n)] = {"round", "verdict", "at", "done_when", "back", "cost"}`.
   - **Accepted**: the step goes on (the next step's plan, or the goal's end). Its leader's journal: `accepted` (*You accepted
     <party>'s step of “<goal>”: 3 of 3 Done when met*) and each `learned` line as `learned` (`journal_notes.accepted`).
   - **Back** (rounds 1 and 2): each item one more task of the step through the runner's `revise_tasks` `add` (spec 62):
     *Fix: <what>*, its brief the item's what and where and the *Done when* line it fails, its tag and tier those of the task it
     names (else the step's first task's), stamped as `PlanMixin._stamp` stamps a step's task (`step`, `party`, `craft`,
     `leader`, `section`), its role by 2. They run and land as any task; then the step is due again (round + 1). Journal
     `sent_back` (*You sent back 2 things of <party>'s step of “<goal>”*).
   - **After the second back**: what is still left is the goal's findings: `findings.add` (new source **`accept`**, `on` the
     *Done when* line's number or the item's where, `party`, `idea`), told at once (`findings.told`: `what`, `shows` the where,
     `promised` the *Done when* line), sorted by the Orkmaster as any finding (spec 132 D.2) and laid on the quality card; the
     step is `gone_on` and the goal goes on. The person decides there (*Fix it there*, *Not now*, *Another level…*).
   - **A line it cannot see** (§257.5), whatever the verdict: one finding `accept` a line, `found` *Nobody could look at: <line>*,
     told at once as the others; never accepted in silence. It does not send the step back.
   - **A call that fails** (no answer after one more try, a disk that refuses): the step is `gone_on` with one finding `accept`,
     *<leader> could not accept this step: its call failed*. **A stop** keeps nothing: the next tick begins it again.
   - `findings.ripe`: a goal's findings are in only when its last step is accepted or gone on.
   - Event `step_accepted` (`idea`, `step`, `party`, `verdict`, `round`, `back`, `seconds`, `cost`, `failed`): never a word of
     the goal. `journals.LEADER_KINDS` gains `accepted`, `sent_back`, `learned`; 151 B mirrors them into the Board's folder as it
     mirrors every kind, and `read_in` takes a line of them added outside as it takes any.
4. **The cost said before** (§121.3): `goal_route._calls` gains `("accept_step", 1, True)` on the long and
   the short way, so the route card's cost counts one acceptance a step; `party_price.price` adds the leader's acceptance, one call
   a goal at the floor of `accept_step`'s tier until `TOO_FEW` goals have priced it, then what they spent.
5. **The face**: *<leader> is accepting* where *<leader> is planning* is said (`arena/arenawords.js`); `table/data.js`'s
   `PHASE_OF` reads `accepting` as `work`. A fix task reads as any added task. No new card.
6. **Tests** (`tests/test_idea_accept.py` and the touched modules'): a step due only when its tasks are in and not accepted; the
   next step and the goal's end wait for the acceptance, and a goal of before is accepted too; the prompt holds the section, the
   promise read by code, each task's files, gate and pictures, the stance of Talk, and no member's part; `clean` (four at most,
   an empty back accepted, a bad answer tried once more); accepted → the journal's lines and the next step; back → fix tasks
   stamped into the step, round two; after the second back → findings `accept` told, the step gone on; a failed call → its
   finding; a stop → nothing kept; `ripe`; the route card's calls and `party_price` with the acceptance; the handover moved and
   unchanged (`tests/test_runner_35.py`).

## C. A base accepted early (§256.3)

1. `idea_accept.bases(plan, n)`: the tasks of step `n` that two or more tasks of the step name in `after`.
2. **They wait for it** (`core/idea_plan.py` `readiness`): a task counts a base it waits for as in only when the base is merged
   **and** accepted or gone on (`plan["accepts"]["<n>:<tid>"]`); every other `after` as today.
3. The keeper's tick: a base merged and not accepted is accepted alone, by B's call with that task's part only (its files, gate,
   pictures, and the *Done when* lines it serves), back and the findings as B.3 (its fix tasks are bases for the same tasks). The
   step's acceptance (B) then reads the bases accepted early as one line each, not their parts again.
4. **Tests**: `bases` (a fan of two, a chain of three: none, a fan inside a chain); a dependent waits for the base's acceptance and
   not for anything else; a base sent back makes its dependents wait for its fixes; the step's acceptance with a base accepted.

## D. The rules, the roles and the words (§256.8, §257.6; after F and spec 151 F are merged)

1. **The role file**: `idea_accept.instruction(craft)` is the acceptance's fixed text, one function its prompt is built from
   (151 C.3's way); `agent_rules_text.seat_text("leader", craft)` gains *## Accepting a step* after *## Your section of the spec*,
   so `roles/<craft>-leader.md` and Claude Code's `ork-<craft>-leader` carry it; the acceptance's prompt on a fixture goal is
   stored beside 151 C's (`tests/prompts_151/accept_tech.txt`) and held by `tests/test_agent_rules_prompts.py`.
2. **The rules' way of a goal** (`agent_rules_text.agents_body`'s step 4, and `board_md` in full), after its *Work*: *Accept: after a party's stages, before
   the next party's, its leader checks them against its section's Done when and Will be, in a pass of its own (its role file, its
   section, the gate's record, the files they changed). What it does not accept is one more stage, twice at most; what is still
   left goes in the pull request under “Not accepted”.* The block stays within its 60 lines. **The Board's schema 2**
   (§255.12): `agent_rules_text.SCHEMA` moves to 2, and with it the block's, BOARD.md's and the role files' marks; `orkboard check` (151 E) says a project's v1 rules are
   older, and `uvx orkboard init` writes them again. A page of schema 1 is read as it is (its format did not change).
3. `core/idea_task.py`: `LEAN_DOES` and `_does_it_itself` go, and `tests/test_task_pages.py`'s test of a Lean leader told it does the task
   (spec 143 A.2). **A task is told the Board's rules are not its own** (§257.6): in a project whose rules are written
   (`agent_rules`'s own test of that), a working task's prompt holds, after its role: *You are one task of a goal Orkboard leads: the
   Board's rules in AGENTS.md are for a tool that leads a goal, not for you. Do not take a goal, move its phase or write the Board's
   pages, and do not read BOARD.md for this task.* A check task and a pick task the same.
4. **`TERMS`**: `acceptance` (*acceptance*, *acceptances*: a leader's check of its step against its section; the person's at
   Review stays *Merge*); A.7's and B.5's lines say it in this word.
5. **Tests**: the role file's part and its prompt one text; the block with *Accept* within 60 lines and `schema=2`; BOARD.md;
   a v1 block said by `check` where it is built; no Lean line in a task's prompt; the task's line where the rules are written and
   not where they are not; the term.

## F. A Done when line says how it is proven (§257.4; after C)

1. **The mark** (`realm/spec_sections.py`): a *Done when* line may start with one of `PROOFS = ("test", "look", "person")` in
   brackets: `- [test] A goal sent with a type keeps it as its route's kind`. `proof_of(line)` → the proof or "" (no mark: its leader
   judges it); `items` keeps the mark in the line's text, `bare(line)` gives it without. `clean_section` takes a *Done when* given as
   strings (no mark) or as `{"line", "proof"}` (a proof that is none of `PROOFS` is dropped, the line kept) and writes the mark.
2. **The section's call** (`core/idea_sections.py` `instruction(craft)`): its *Done when* rule says how each line is proven: `test`
   when a test the gate runs can prove it, `look` when only a picture or Play shows it (a screen's state, a sound), `person` when only
   the person can judge it (a word's tone, a price), and to prefer `test`; its answer's format gives `{"line", "proof"}`. The stored
   section prompts of 151 C (`tests/prompts_151/section_*.txt`) are written again for this change and no other; the role files follow
   by their hash.
3. **The task** (`realm/task_brief.py`, what a task reads of its section): under its section's *Done when*, one line: *A [test] line
   you prove: write its test first, see it fail, then make it pass.*
4. **The acceptance by proof** (`core/idea_accept.py`): its given lines carry their proof; `[test]` lines are given with the gate's
   record and the tests the step's tasks added (by name, from their diffs); `[look]` lines with the step's pictures, and with none
   (no preview, no Play) the line is `unseen` without the leader's word; `[person]` lines are `unseen` at once, their finding asking
   the person (B.3). A line with no mark as B.2 has it.
5. **The pages' schema 2** (`realm/goal_phase.py` `SCHEMA = "2"`): a page of schema 1 is read as it is (its lines have no mark);
   the Board writes 2 when it next writes a page.
6. **Tests**: `proof_of`, `bare`, `items` with marks; `clean_section` with strings, objects, a bad proof; the section's prompt
   stored again; the task's line under *Done when*; the acceptance given each line by proof, a `[look]` line with no picture and a
   `[person]` line `unseen` with their findings; a schema 1 page read.

## E. Measured (§256.9)

`docs/trials/152-a-leader-accepts.md`, written before the runs: spec 149's way (a clone, local Codex or Claude Code, every press
through the page), **one goal at Lean** of §253's kind (one party, a small change) and **one at Standard** with two checkers in
the squad. Recorded: the calls by step, the tokens and the share of the window, the acceptance's tokens against the Lean review it
replaces (§253.13: 556,105), what it sent back and whether it was right, how long a step waited for it, and every task's role
(none the leader's). Then the owner reads it beside §253's run (13 calls, 3.30 million tokens) and says what the next spec of
§256.9 takes from it.

## Done when

- No task is a leader's, at any size: a task's role is a seat of its squad that does, else the project's role of its tag, else
  Grunt; a party cannot be saved with no one who does; Release has two who do.
- Lean plans no check task; Standard one checker's a task, the first it concerns; Full every one it concerns; a leader's seat is
  not lowered by its size.
- Every step that landed something is accepted by its leader once, a base as it lands; a step goes back twice at most; what is
  left is the goal's findings on the quality card; a failed acceptance is a finding; the next step and the goal's end wait for it.
- The route card's cost counts the acceptances.
- The rules' way of a goal has *Accept*, each leader's role file its part on accepting, and the Board's schema is 2.
- A section's *Done when* lines say how each is proven; a `[test]` line's task writes its test first; a line nobody could look at
  is a finding, never accepted in silence; the pages' schema is 2.
- Orkboard's own task, in a project with the Board's rules, is told they are not its own.
- E's runs are written: at Lean the acceptance costs under a tenth of the review it replaces.
- The critical tests pass: `tests/test_architecture.py` (`core/idea_accept.py` imports no `gui/`), `tests/test_board_alone.py`,
  `tests/test_updates.py`, and each part's own.
