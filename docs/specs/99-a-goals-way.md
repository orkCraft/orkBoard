# Spec 99 — A goal's way: parties by craft, the route, Talk, the decision, the sections, the project's questions, a leader's map in its call

The owner and the PM, 27–28 October (decisions §109, §117, §118, §121.2–§121.3, §122, §133, §134.5, §136.2, §137,
§138.1, §138.7, §140, §147, §151.1–§151.2, §151.6, §153, §156.1–§156.2, §156.7–§156.8, §156.10, §156.12–§156.13,
§157, §158; spec 95 §5–§6). The engine of the first slice's way: what a goal goes through from the blank card to its work,
with the parties it needs. **No face**: spec 100 draws it on spec 98's frame; until then the desktop shows the new
Needs you rows as today's stops do (a row of an unknown kind is a plain card with its text and its buttons' words).
**Builds:** a cheaper model, each part reviewed by Claude · **Review:** full · P0. **Waves** (parts in a wave share no
file): **1** A, B, F; **2** C (after S1's spec 98 B, which touches `realm/board_map.py` and `realm/lexicon.py`); **3** D;
**4** E and G; **5** H. **A after spec 96** (orkUI 0.15.0 copied: the new heads' files).

**What it is, and is not:** the parties as one craft each with the project's stage choosing them, Release in every
project, a squad and a size apart, the races by party; a goal routed (code or the cheaper tier) to an ordered route of
steps with its cost and its place, and no call before *Talk*; *Talk* (the route's leaders' short answers and questions
as cards, two rounds at most; a bug's Talk its diagnosis); the decision worded, confirmed with *Confirm and start*,
committed numbered to the project's decisions file in dev; the sections written by the route's leaders at once and
joined, a disagreement a fork; the work by steps, a task reading its own section; the project's questions; a leader's
map as text in every call; the night gone. Not: the faces (spec 100); the other maps' texts (Design's flow, Game design's
loop, Art's assets, Release's: S3), another party's change on a map (§156.3–§156.6, S3); *Release a version*, the
wait for the reset as a sign, *Start now*'s card, recurring goals (S6); a change while it works (§118.7: today's `say`
stays as it is); the phone's page (S5). Orkline is not changed (§121.4).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Parties** | §1 | `realm/party_recipes.py`, `realm/library.py`, `realm/roles.py` (`RACES`, `head`, `task_head`), `realm/goal_team.py`, `realm/party_presets.py`, `realm/orkmaster.py` (`deal`, `proposals`), new `realm/project_stage.py`, `gui/ideas_goals.py`; `tests/test_party_recipes.py`, `tests/test_library.py`, `tests/test_roles.py`, `tests/test_goal_team.py`, `tests/test_party_presets.py`, `tests/test_orkmaster.py`, new `tests/test_project_stage.py`, `tests/test_gui_goals.py` |
| **B. A leader's map, the project's facts** | §2 | new `realm/map_text.py`, new `realm/project_facts.py`; new `tests/test_map_text.py`, `tests/test_project_facts.py` |
| **F. The night goes** | §3 | `core/idea_night.py` (removed), `core/idea_keeper.py` (`tick` and the mixin), `gui/ideas.py` (`add`'s night and Low, `tonight`), `gui/ideas_board.py` (`night_low`, `night_allow` kept inert, `start_night`, `decline`), `realm/idea_target.py` (`refresh`, `propose` rows), `gui/keep_awake.py`, `realm/party_proposals.py` (the night's parties), `realm/idea_spend.py` (`refresh`); `tests/test_idea_night.py` and `tests/test_night_low.py` (removed), the tests §3 names |
| **C. The route** | §4, §10 | new `realm/goal_route.py`, new `gui/ideas_route.py` (wired in `gui/ideas.py`'s table and bases), `gui/ideas.py` (`add`: no call), `realm/ideas.py` (the states `routed`, `talk`, `decided`, `sections`; `route` in the state), `realm/board_map.py` (the rows `route`, `start`), `realm/lexicon.py` (§10); new `tests/test_goal_route.py`, `tests/test_gui_route.py`, `tests/test_ideas.py`, `tests/test_board_map.py`, `tests/test_lexicon.py` |
| **D. Talk** | §5 | new `core/idea_talk.py` (`TalkMixin`, wired in `core/idea_keeper.py`'s bases), new `gui/ideas_talk.py`, `realm/idea_questions.py` (a question card), `realm/board_map.py` (the rows `talk`, `cause`), `realm/idea_target.py` (the `talk_round`, `diagnose` steps); new `tests/test_idea_talk.py`, `tests/test_gui_talk.py`, `tests/test_idea_questions.py` |
| **E. The decision and the sections** | §6, §7 | new `core/idea_decide.py`, new `core/idea_sections.py` (wired in `core/idea_keeper.py`'s bases), new `realm/spec_sections.py` (the spec's format), `realm/idea_page.py` (`SECTIONS` read with the parties' sections), `realm/idea_git.py` (`BoardTree` commits the decisions file), new `gui/ideas_decide.py`, `realm/board_map.py` (the rows `decision`, `fork`); new `tests/test_idea_decide.py`, `tests/test_idea_sections.py`, `tests/test_spec_sections.py`, `tests/test_board_tree.py`, `tests/test_idea_page.py` |
| **G. The project's questions** | §8 | `realm/project_facts.py` (the answers kept), new `core/idea_project_q.py`, new `gui/ideas_project_q.py`, `realm/board_map.py` (the row `project_q`, laid by its urgency); `tests/test_project_facts.py`, new `tests/test_idea_project_q.py` |
| **H. The work by steps** | §9 | `core/idea_keeper.py` (`plan` a step), `core/idea_plan.py`, `core/idea_runner.py` (a task's party, the next step), `realm/idea_route.py` (the route's steps as history), `realm/task_brief.py` or the brief's module (a task reads its section); `tests/test_idea_keeper.py`, `tests/test_runner_35.py`, `tests/test_idea_route.py` |

E and G both touch `realm/board_map.py`: G adds only its row's function and one call in `build`, after E is in (wave 4 is
E, then G on E's head, or G with its row in a new `realm/board_rows.py` that `board_map` imports: the builder of G picks
the second when E is not yet in).

## 0. The words
New strings (the face words them, spec 100; the host returns keys and data, never words, as today): *Talk*, *Spec*,
*Work*, *Done*; *Confirm and start*; *Later, by itself*; *Start*; *Other…*; *Let <leader> decide*; *<Party> alone:
finding the cause*; *Yes*, *No, it's elsewhere*; *in line*. `TERMS` (C, §10).

## 1. Parties (A; §109.1, §122, §137.1, §151.1–§151.2, §151.6, §154, §155, §158.4–§158.5)
1. **One craft a party**: the recipes are by craft — a game: *Game design*, *Tech*, *Art*, *Release*, *LiveOps*,
   *Marketing*; an app or a site: *Product*, *Design*, *Tech*, *Release*, *Run*, *Marketing*; any other kind by the same
   rows (what it makes, its code, its look, its running, its marketing, its release). The mixed recipes (`game`,
   `mobile-features`, `web-pages`) are not offered; a party made before keeps its seats and its name (§109.1). General,
   Team and Ideation are **never offered nor made** (`add` and `goal_save` refuse them, as `add` refuses Team today); a
   party of theirs the project has stays until the person removes it (no move offered: §122.3) — see the owner's list.
2. **The project's stage** (`realm/project_stage.py`; §122.5): `idea` · `being_made` · `live`, kept in
   `<state_dir>/project.json` (`stage`), read from the project when unset (no code: `idea`; code and no store page or
   deploy: `being_made`; else `live`, the person correcting it). **The crafts by stage**: *Idea* the concept's crafts
   (Game design and Art; Product and Design), lean; *Being made* adds Tech, standard; *Live* adds LiveOps or Run, and
   Marketing (§151.7). **Release is in every project at every stage** (§137.1): proposed ticked and locked, Lean, its
   leader alone (the Release manager) on the cheaper tier (§151.6, §157.2); `party_drop` refuses it. Commands:
   `ideas.stage {}` → `{stage, read, offered: {stage: [recipe]}}`, `ideas.stage_set {stage}`.
3. **The squad and the size apart** (§151.1–§151.2): the squad is the seats the person ticks from the craft's roles, at
   most seven (one *Leads*, up to five *Does*, up to two *Checks*; `goal_team.SEATS` 7); the size is how a task goes —
   **Lean** (plan → do, one at once, no separate check: the doer runs its own tests), **Standard** (plan → do → one check,
   two at once), **Full** (plan → do → every checker it concerns, three at once). A size sets the seats' tiers by
   default (today's `tiers_for`), never the squad; with no checker in the squad, the leader checks. `ideas.party_price`
   answers a size's price a goal, never a squad's.
4. **Races by party** (§158.4–§158.5; `roles.RACES` by party, `roles.head` by the seat's party): every seat wears its
   party's race, its leader that race's higher form — Game design or Product: `knight`, leader `unicorn` (§162); Tech: `peon`,
   leader `shaman`; Art or Design: `elf`, leader `dryad`; LiveOps or Run: `goblin`, leader `imp`; Marketing: `gnome`,
   leader `fairy`; Release: `skeleton`, leader `lich`; the Orkmaster `peon-crown`. A role's own `race` (`library.Agent`)
   and its craft no longer choose its head; `task_head` follows its task's party. The heads' files are orkUI 0.15.x's
   (spec 96); a race whose file is missing falls back to its members' race at the tier.

## 2. A leader's map, the project's facts (B; §156.1–§156.2, §156.7, §156.10)
1. **`map_text.system(state_dir, root, since="")`** → the text of Tech's map at dev's head, read by code from the newest
   snapshot (`project_map.ensure`, `system_overview.read`): *The map of System at dev <short>*, then the containers
   whole (each a line: its name, stack, ways in, its links named: *commands: 40 · starts*), then the parts a line each
   (its path, its layer, *Uses* / *Used by* by name); **about 3,000 characters at most** — past it the parts keep only
   their names, and the text says so (*The parts are named only: read further what you need*). Then, when `since` (the
   commit of this party's last call) is set, *Changed since your last call*: each part new, changed or gone with its goal
   and who decided it (§112.6, read from `project_map.changed` and the goal's page). The map stands before what changes
   between calls, so its text is the same between two heads of dev (the prompt's cache keeps it). `map_text.detail(...,
   parts)` adds the named parts in full (their files, uses, used by), at most 1,500 characters more. Other maps' texts
   (S3) are `None` today: a party with no map is given none.
2. **`project_facts`** (`<state_dir>/facts.json`): facts and answers by party — `{common: {for_whom, hurts, leaves_out},
   party: {<party>: [{key, text, by: "person"|"read", at}]}}`; `common(state_dir)` (about 600 characters at most),
   `of(state_dir, party)`, `for_call(state_dir, party, route)` (the common core, its own party's, and another party's
   only when the route has it), `keep(state_dir, party, key, text, by)`. A member is given none (its leader's brief
   carries what it needs).
3. **Product's reading at the start** (§156.10): `project_facts.start_files(root)` → the README and `docs/`'s top
   level by name (`*.md`, at most 6), the first 2,000 characters of each, chosen by code; the call is G's.

## 3. The night goes (F; §131.2, §156.12)
`core/idea_night.py` goes: the night's run, its queue, its starts, the night's refresh (`refresh` step), the night's
proposals (`propose` step), the night's parties and the week's pace (`pace_tick`, a Low goal: §124.2 has no
priority). `IdeaKeeper.tick` keeps what the limits held (`hold`, `held_until`) and nothing else; `ideas.add` takes no
`night` nor `priority: low` (a goal is queued `now` or `hold`); `start_at: night` is no longer written (a plan's start
waits for the reset with `held_until` as today's reserve does). Kept inert for the phone and Orkline (spec 98 §1's
rule): `ideas.night_allow` (stored, unused), the snapshot's `reserve.night` and `board.night_low`, the queue name
`night` read as `hold`. `decline`/`declined.jsonl` (a proposal declined) goes with the proposals. Tests that pin what
went are removed with it (`tests/test_idea_night.py`, `tests/test_night_low.py`) or lose those assertions
(`test_party_proposals`, `test_ideation`, `test_week_pace` (removed if wholly the pace), `test_board_tree`,
`test_idea_target`, `test_party_size`, `test_board_35`, `test_keep_awake`).

## 4. The route (C; §117.1–§117.2, §118.2, §121.3, §133.1, §136.2, §138.3, §140.2–§140.3, §147.4, §156.6, §158.2)
1. **A goal sent** (`ideas.add {text, party?, photos?, marks?}`) makes no model call: the Orkmaster **routes it by
   code** (`goal_route.route(state_dir, text, party, marks)`): addressed to a party, the route is that party alone (it
   may add steps after: §117.1); a bug (`idea_kind.guess` *bug*) is Tech alone (the short way); else the parties by
   `orkmaster.party_for`'s rule and the kinds' words, in the craft order (the product's craft, then the look's, then the
   code's, then the running's, then the marketing's). Only when code finds no party does it make **one call on the
   cheaper tier** (step `route`, no tools, `READS 0`) naming the parties in order. Release is never a step (§137.1).
2. The state is `routed`; `state.route` is `[{party, leader}]`; the Needs you row **`route`**: `{kind: "route", idea,
   route: [{party, leader, head}], cost: {calls, usd_low, usd_high}, place, short: bool, reproduces: bool, low: bool,
   offer: [party]}`. `place` is its place in the Orkmaster's order among the goals not started (*3rd in line*); `short`
   when it is the short way (a bug, or a small goal offered it: `offer_short`), `reproduces` when the bug's report holds a
   failure's lines, a stack trace or a failing test (by code: a `Traceback`, `at …(…:n)`, `FAILED`, `Error:` with a
   path), `low` when the week's limits run low (`idea_target`'s reserve), `offer` the parties whose map the goal's marks
   touch, not on the route (§156.6; today the marks' parts of System offer Tech).
3. **The cost said before** (§121.3): `goal_route.cost(state_dir, route, short)` → the calls (Talk's rounds, the
   decision, the sections, the join, each step's plan) and the usd range from the tiers they run on (`idea_target`'s
   floor and the plans' `tier_costs`); the face says it as a share of the week (spec 98 §4.7).
4. **The route's edits, no call** (§133.1, §140.2–§140.3): `ideas.route_set {idea, route}` (a party taken off, one
   added: any of the project's but Release), the cost answered again at once.
5. **The acts**: `ideas.talk {idea}` (**Talk**: D starts), `ideas.route_later {idea}` (*Later, by itself*: only when
   `low`; the goal waits in the deck with `held_until` at the reset), and on the short way `ideas.route_start {idea}`
   (**Start**: when `reproduces`, Tech's section straight from the report, E's `sections` with one step, no Talk, no
   decision; else **Talk** is the bug's diagnosis, D §5.4).
6. **A step added after Talk** (§136.2): the route changed since the route card brings a row **`start`** `{kind:
   "start", idea, cost, was}`: the new cost and the old one beside it; `ideas.start` answers it.

## 5. Talk (D; §118.1, §121.2, §153.3, §153.5–§153.6, §156.8, §158.1–§158.3)
1. `ideas.talk` → state `talk`; **one call a leader on the route, at once, on the cheaper tier** (step `talk_round`,
   **no file read**: `tools=False`, its map's text (B §2.1) and the project's facts (B §2.2) are enough), each leader's
   voice: its **stance** (one line), **for** and **against** (a line each), and **its questions** about the goal; at its
   party's first goal (no goal of the project has had that party on its route before) also its questions about the
   project (§153.3), **inside the goal's three**: the Orkmaster's rule picks the three of all the leaders' (those the
   work cannot start without first, then by the route's order); the rest are closed by their leaders' defaults, kept.
2. **A question is a card** (`idea_questions.card`): `{id, by: party, leader, q, choices: [2..4], pick: index, why,
   project: bool}`; two to four real choices, never padded (`CHOICES`); one picked for the person with its why; the
   choices from what the project holds (a container, a screen, a fact kept), never from what is common. *Other…* is the
   face's (the field opened with the pick in it). A project question answered is kept (`project_facts.keep`, by the
   person) and never asked again.
3. The Needs you row **`talk`**: `{kind: "talk", idea, round: 1|2, stances: [{party, leader, stance, for, against}],
   questions: [card]}`; `ideas.talk_answer {idea, answers: [{id, pick?|text?}], decide?: bool}` (`decide`: *Let …
   decide* answers the rest with the picks). After the first round's answers, **a second round** only when a leader
   says the answers open a question the work cannot start without (at most three again); after it, what is left takes
   the defaults (§121.2). Then the decision (E §6). Every call is measured as today; the talk is kept in `talk.jsonl`
   behind *More* and never read back into a model beyond the round's own answers.
4. **A bug's Talk is its diagnosis** (§158.1–§158.3): Tech alone, **one round**, the cheaper tier (step `diagnose`);
   its leader reads its map's text, the parts the report touches (it may read up to `READS["diagnose"]` = 4 files of
   them) and the failure's lines or a log when the report has them; it asks **at most three questions about the cases**
   (where it happens, its choices from the map's containers and the screens; the steps; what was expected; since which
   version) and lays **its guess of the cause**: the row **`cause`** `{kind: "cause", idea, cause, where: [path], q:
   [card]}`, answered by `ideas.cause_answer {idea, yes: bool, text?}` (*Yes*, *No, it's elsewhere*, *Other…*). A *No*
   with text asks one more guess (once). A question of Tech's about the project rides in the same stack (§153.3). The
   cause found is the *Why* of Tech's section; **no decision is written** (§158.3): after it, E's sections (one step) and
   the work, on *Start* (the route card's cost said it).

## 6. The decision (E; §118.1, §134.5, §138.7, §147.2–§147.3, §156.11)
1. After Talk, **one call of the Orkmaster on the cheaper tier** (step `decide`, no tools) words the decision as the
   project's decisions file words its entries: a title line, *Why* in a few lines, its points numbered; given the
   asked words, the stances, the answers and the defaults, and the decisions file's last ten headings
   (`decisions_log.context`). State `decided`; the row **`decision`** `{kind: "decision", idea, number, title, text}`
   (`number` = `decisions_log.next_number`, read again at the commit).
2. **`ideas.confirm {idea, text?}`** (**Confirm and start**; `text` the person's correction, kept as written): the
   entry is appended to the project's decisions file (`decisions_log.path(root, chosen)`, the person's chosen path from
   the first opening, else `docs/decisions.md`; the file made with a one-line head when missing) as `## <n>. <title>
   (<date>, the person and Orkboard)`, its number read again so two goals never take one; **committed to dev** by
   `BoardTree` (its allowed paths widened by that one file), author as the Board's pages are. Then E §7 at once.
3. A decision is never written for a bug (§158.3) nor a recurring round (§122.6); a goal that changes what the project
   is never skips it (§118.2).

## 7. The sections, joined, the forks (E; §117.2–§117.3, §118.3–§118.5, §134.5, §136.2)
1. **The spec's format** (`realm/spec_sections.py`; §118.3): the page's **common part** — *Asked* (the person's words,
   as they are), *Gist* (one line, at the join), *Route* (the parties in order, each step's leader and state),
   *Depends on*, *Decisions* (its decision's number, the forks answered, each naming its section) — then **a section a
   party on the route**, `## <Party>` with its leader's `### Why`, `### Done when` (at most five theses), `### Checks`,
   `### Will be` (the change on its map: the parts of its map by their ids), `### Out`, `### Risks`, `### Defaults`,
   `### Questions`, `### Plan` (after *Start*). An older page reads as one section of its party (§118.8): its *Gist*,
   *Why*, *Done when*, *Out*, *Risks* under its party's heading, nothing rewritten.
2. **Every leader on the route writes its section at once** (parallel calls, step `section`; the first step's leader
   on the goal's party's tier, the others on the cheaper; reads bounded as today's `draft`), given its map's text with
   the parts the goal touches in detail (B §2.1), the facts for the call (B §2.2), the decision's entry
   (`decisions_log.context(root, n)`), the asked words and the answers.
3. **The Orkmaster joins them** (step `join`, the cheaper tier, no tools): writes *Gist* and *Route*, **never changes a
   section's words**; what two sections disagree on is **a fork**: the row **`fork`** `{kind: "fork", idea, sides:
   [{party, leader, says, why}], about}`, answered by `ideas.fork_answer {idea, side|text}` (the answer to *Decisions*,
   naming the sections it changes; the sections it changes are written again by their leaders, one call each).
4. **Who decided a change on the map**: once a section's *Will be* is stored, `map_text`'s *Changed since your last call* lines
   say who decided each change (the person, the leader, a member alone: §112.6), read from the goal's sections and
   decisions (B left it at the goal and *by you*).
5. **Starts by itself** when the join leaves no fork and no open question: state `plan`, then H's first step's plan and
   the start as today's autostart does (`idea_risk.decide` holds as today); with a fork, the forks first, then
   *Start* (`start` row, C §4.6) — the cost said on the route card was the whole way's, so nothing unsaid is spent.

## 8. The project's questions (G; §153.1–§153.4, §156.10, §157.1)
1. **At the first start** (the parties made: `ideas.party_save` with `first: true`): one call of Product's leader (in
   a game Game design's; with neither, none) on the cheaper tier, no tools, given `project_facts.start_files` (B §2.3):
   two or three cards — *whom it is for*, *what hurts them*, *what it leaves out* — each only where the files do not say
   it; where they do, the leader's reading is the card's pick, one press to confirm. With neither party, the Orkmaster's
   one card *What is this project for?* (today's empty folder's line).
2. The row **`project_q`** `{kind: "project_q", party, leader, questions: [card]}`: a stack of no goal's, its leader's
   head on it, laid by its top card's urgency as any stack (a question the work does not wait for: after the others);
   it holds nothing back (the first goal is sent with it unanswered). `ideas.project_answer {answers, decide?}` keeps the
   answers (`project_facts.keep`, `by: "person"`; a pick kept by *Let … decide* `by: "read"`); answered or let go, it
   leaves the hand.
3. **What is answered is the project's**: read into every leader's calls through `project_facts.for_call` (B §2.2),
   never asked again; Product's *whom* and *hurts* also kept as segments (`idea_lens.keep_segment`) for Product's map.

## 9. The work by steps (H; §109.2, §117.4, §118.5, §156.13)
1. **A goal's route is its steps**: after the join, the first step's party plans its own step (today's `plan_one`,
   given its section whole and of the others only *Done when* and *Will be*: §118.5); its tasks run on its party's
   seats; when its tasks are merged in dev, the next step's party plans its step, and so on; the goal is *done* when the
   last step's tasks are in dev (§138.1). `idea_route.steps` records each step as history (spec 68's route).
2. **A task's party** is its step's: its role, tool and tier from that party's seats (`goal_team`); `task_head` its
   party's race (A §1.4).
3. **A task reads** the spec's common part, its party's section whole, and of the others only *Done when* and *Will
   be*; its brief names those, never the whole page (§156.13).
4. A goal of one step is exactly today's flow with the new spec format.

## 10. The words (C; §121.1, spec 95 §12)
`TERMS` gains (each with its key and one line, beside spec 98's): *route*, *route card*, *step*, *phase* (*Talk*,
*Spec*, *Work*, *Done*), *section*, *stage*, *will be*, *fork*, *out of the contract*, *Release a version*, *Other…*.

## 11. Tests
A: the recipes by craft for each kind, no mixed recipe offered, General/Team/Ideation refused, an older party kept; the
stage read and set, the crafts by stage, Release in every project and locked, Lean and its leader alone; seven seats, the
size's stages and at-once apart from the squad, the price by size; every seat's head its party's race and the leader's
higher form, the fallback. B: the map's text, its bound and its cut, the same text between two heads, *Changed since
your last call* with goal and who; the facts by party and `for_call`'s three cases; the start's files. F: no night run,
refresh or proposal; `add` with no night; the inert keys kept (`tests/test_board_alone.py`). C: a goal sent makes no
call; the route by code for an addressed goal, a bug, a typed goal; the one cheaper call when code finds none; Release
never a step; the row's shape, `place`, `short`, `reproduces`, `low`, `offer`; the cost; `route_set` with no call;
*Later, by itself* only when low; the `start` row after a step added. D: one call a leader with no tools and its map's
text; stances; three questions picked by rule across leaders; a project question at a party's first goal and never
again; the card's shape, two to four choices; `talk_answer` with picks, text and *decide*; a second round only when
asked, then the defaults; the bug's diagnosis: one round, at most three questions, the cause row, *No* once more, no
decision. E: the decision's call and row; *Confirm and start* appends the numbered entry, commits it to dev with the
pages, two goals never one number; no decision for a bug; the format of the common part and the sections, an older page
read as one section; sections at once, the join never changing a section's words, a fork and its answer re-writing only
its sections; the start by itself with nothing to settle. G: the start's call only for Product or Game design, the
cards with picks from the files, the row laid after the others, answers kept and read into calls. H: the steps planned
one after another, a task's party and tool from its step's party, the brief's sections, a one-step goal as today. The
critical tests (`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and each part's
files' tests.

## As built (B)

New `realm/map_text.py` (`system(state_dir, root, since="", pages=None)`, `detail(state_dir, root, parts)`, `of(party, …)`; `LIMIT`
3,000, `DETAIL` 1,500, `CHANGED` 1,200) and `realm/project_facts.py` (`keep`, `of`, `common`, `for_call`, `answered`, `start_files`;
`<state_dir>/facts.json` with `common_by` beside `common`, so a reading never replaces the person's answer). Tests:
`tests/test_map_text.py`, `tests/test_project_facts.py`.
- **Decided here:** `system` is `None` with no `dev` branch; past 3,000 characters the parts keep their names, and past that
  *and N more parts*; *Changed since your last call* has its own 1,200; with `since` empty the text below its first line (the
  dev commit) is the same between two heads that changed no part. `pages` (the Board's pages root) gives a goal its title.
  `start_files` reads the README and up to six `docs/*.md` (never `decisions.md`), 2,000 characters each, symlinks and secret
  paths skipped. `answered` gives the keys already kept, for G.
- **Not yet: who decided a change** (§112.6) is not stored before E's *Will be*; *Changed since* says the goal, and *by you*
  for the person's own commits. **E adds the deciding party** to those lines once a section's *Will be* is stored.

## As built (F)

`core/idea_night.py` removed (the night's run, queue, starts, refresh, proposals, parties, the week's pace, `decline`). `IdeaKeeper.tick`
runs held work (`held_until`) and the queue `now` only; `ideas.add` queues `now` or `hold` (`priority: low` is still stored, it queues
`now`); `idea_target.gate()` holds a plan only for the reserve's reset (an older `start_at: night` read so); the runner's night skip and
pace went. Kept inert: `ideas.night_allow` (stored, unread, `moved: 0`), `board.night_low`, `reserve.night`, the settings `night` and
`night_low`, the queue `night` read as `hold`. **Decided here:** `older_night_plans()` hands an older passed plan waiting for the night to
the runner, its tasks waiting for the reserve's reset; a proposal already waiting is still answered (*Take* drafts at once, *No* drops it,
no `declined.jsonl`); the events `NIGHT_RUN`, `NIGHT_ALLOWED`, `PROPOSAL_MADE`, `PARTY_PROPOSED` are no longer written (their names
kept for old logs). Left for later parts: `realm/ideas.py` `queue_of`'s `night` for a raw idea with no queue, `core/idea_task.py`'s dead
pace helpers, `realm/board_map.py`'s `night` wait kind, `realm/idea_risk.py` `decide`'s unused night.
