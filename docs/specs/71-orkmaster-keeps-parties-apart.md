# Spec 71 — The Orkmaster keeps the parties from colliding: an overlap before the work, a spec changed under another party, a goal that waits for another party's

The owner, 24 October (decisions §86): *the Orkmaster coordinates the parties' work and the changes in their specs, so
they do not collide.* Each party's leader sees its own goals; two parties' goals that change the same thing meet only at
the gate. So the Orkmaster (spec 70) **finds** what two open goals of different parties both touch, **asks** the person
what goes first, **tells** a party when another party's spec changed under it, and lets a goal **wait** for another
party's flag. Code finds, a model of the cheaper tier judges, the person decides. **Builds:** Claude · **Review:** full ·
P2. Built after spec 70 was seen at work (the owner's call, 24 October); **A, B and C at once, in parallel**, B and C against their stub hosts with the shapes of §8.

**What it is, and is not:** one finder (code), one judge (a model call, cheap tier, only when the finder found
something), one kind of stop in the hand (`collide`), a goal's `depends_on` that may name another party's goal, and its
lines on the project's level. Not: the Orkmaster editing another party's spec or plan; anything held, merged or re-planned
without the person's answer; a model call on every event; reading the stores, the web or another project.

Three parts, **built at once**: B and C build against the shapes of §8 with their tests' stub hosts, and are merged after A. They share no file.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§5 | new `realm/collide.py` (what a goal touches, the overlaps, the kept answers), new `core/idea_collide.py` (the judge: the prompt, the call, the answer read), `realm/orkmaster.py` (its role: `orkmaster` installed as a role of the project, `warrior`, takes no task), `realm/board_map.py` (Needs you's `collide`; a node's `waits_for` across parties), `realm/ideas` readers of `depends_on` (a goal of another party held until its flag), `gui/ideas_project.py` (`ideas.collide_answer`), the hooks at a plan made and at a spec changed after the start (`core/idea_change.py`'s caller), `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_collide.py`, `tests/test_idea_collide.py` |
| **B. Desktop** | §6 on the desktop | the hand's `collide` stop (its two goals, its answers), the project level's links (spec 70 §2.3) drawn for a collision and a wait, a goal row's *waits for <party> · <goal>*; new `tests/test_collide_desktop_browser.py` |
| **C. Phone** | §6 on the phone | the same as the phone's hand and goal rows draw a stop and a wait; `pwa/sw.js` `CACHE` one up; new `tests/test_pwa_collide_browser.py` |

## 0. The words
`TERMS` gains `collide` (*collision*: two goals of different parties that change the same thing). New strings: *<party>
«<goal>» and <party> «<goal>» change the same thing*, *<one> first*, *One goal*, *Leave it*, *<party> changed «<goal>»:
«<goal>» in <party> rests on what it was*, *Re-plan it*, *waits for <party> · <goal>*, *Orkmaster asks*.

## 1. What a goal touches (A, code)
`collide.touches(root, state_dir, slug)`: the paths and modules its page's `touches` names (as `core/idea_keeper.py`
reads it), its plan's tasks' files when they name some, and the files its merged tasks changed; normalised (a module
`orkboard/realm/x.py` and its folder `orkboard/realm/` overlap; `tests/` and docs are left out unless both goals are only
docs). Read, never written.

## 2. The overlap, before the work (A)
1. When a plan is made (the event `plan_made`), `collide.overlaps(…, slug)` compares the goal's touches with every open
   goal (not done, not dropped, not a pitch, not a release) **of another party**; none: nothing more (no model).
2. One or more: **the judge** (`core/idea_collide.py`, the Orkmaster's role, the cheaper tier) gets the two goals' titles,
   *Done when* and touches (≤ 3 000 characters) and answers `{"collide": bool, "why": "…" (≤ 200), "first": slug|""}`;
   `collide: false` drops it (kept as answered, never asked again for that pair); `true` is a stop.
3. **The stop** (`collide`, Needs you, `blocks: false`, priority `normal`): the two goals, the why, the suggested first;
   answers **<one> first** (the other's `depends_on` gains it: held until its flag, §4), **One goal** (the later goal's
   text joins the earlier's as a change, spec 62's way; the later is dropped with *joined into «…»*), **Leave it**. Kept
   by the pair (`<state_dir>/collide.json`, the last 200 answers): a pair answered is never asked again.

## 3. A spec changed after the start (A)
When a goal's spec changes after its plan (spec 62's change), its touches are compared with the open goals of other
parties as in §2.1, judged as in §2.2 with the change's words; a collision is a stop *<party> changed «<goal>»: «<goal>»
in <party> rests on what it was*, with **Re-plan it** (that goal's leader re-plans what is left, spec 62's way, the change
told to it) and **Leave it**.

## 4. A goal waits for another party's (A)
A goal's `depends_on` may name a goal of another party; its start is held (as `depends_on` holds today within a party)
until that goal's flag (spec 50 §2.2), and the map's node says `waits_for: [{goal, party}]`. Set by *<one> first* or by
the person (the goal's screen).

## 5. Measured and priced (A)
Events: `collide_found` (pair, by: plan|change, judged: bool, collide: bool, tokens, cost) · `collide_answered` (pair,
answer). The party's work for the project says the Orkmaster's stops answered, taken (not *Leave it*) and its cost a
week. A finder that finds nothing costs nothing; the judge runs only on what it finds.

## 6. Faces (B, C)
- The hand's `collide` stop: the Orkmaster's head, *Orkmaster asks*, the two goals (each with its party, a press opens
  it), the why, its answers as buttons saying what happens.
- The project's level (spec 70): a collision is a link between the two decks in the signal's colour while the stop is
  open; a wait a link with the arrow of *waits for*.
- A goal's row in its party: *waits for <party> · <goal>* with orkUI's ← sign; a press opens that goal.

## 7. Tests
- **A**: touches read and normalised; no overlap no call; an overlap judged (a stub harness), `false` kept and not asked
  again, `true` a stop; each answer (first: the wait held until the flag; one goal: joined and dropped; leave it); a spec
  change judged and *Re-plan it*; a goal of another party in `depends_on` held and then started at the flag; events hold
  no goal's words.
- **B**, **C**: the stop and its answers; the link on the project's level; the wait's line.

## 8. The shapes (A answers them; B and C build against them)
1. **The stop** is a Needs you row (`ideas.board`'s `needs_you`, the map's node `needs_you` gains `"collide"` in `NEEDS`),
   on the goal asked about (the later of the two by its plan's `made_at`, or the goal whose spec did not change):
   ```
   {"kind": "collide", "idea": "sign-in-screen", "goal": "mobile", "title": "Sign-in screen", "priority": "normal",
    "blocks": false, "at": "2026-10-24T10:00:00",
    "text": "Mobile app «Sign-in screen» and Backend «Auth API» change the same thing",
    "collide": {"id": "auth-api|sign-in-screen", "by": "plan",            // plan · change
                "why": "Both change how a session token is issued",          // the judge's, ≤ 200
                "first": "auth-api",                                         // the judge's suggestion, or ""
                "goals": [{"idea": "auth-api", "party": "backend", "party_name": "Backend", "title": "Auth API", "element": "ice"},
                          {"idea": "sign-in-screen", "party": "mobile", "party_name": "Mobile app", "title": "Sign-in screen", "element": "dust"}],
                "answers": ["first:auth-api", "first:sign-in-screen", "one", "leave"]}}   // by change: ["replan", "leave"]
   ```
   With `by: "change"` the `text` is *<party> changed «<goal>»: «<goal>» in <party> rests on what it was* and `goals[0]` is
   the goal whose spec changed. Sorted as a plan's row is (`sort_needs`: not last, not blocking). Counted in the
   snapshot's `needs_you` as a plan's is.
2. **`ideas.collide_answer {id, answer}`**: `answer` one of the stop's `answers`; `first:<slug>` makes the other goal
   wait for `<slug>` (§4), `one` joins the later into the earlier (§2.3), `replan` re-plans what is left of the goal asked
   about (spec 62's way, the change told), `leave` keeps them as they are. Answers `{ok: true}`; refused *That is
   answered already* (an id kept as answered), *No such question* (an id not open), *Pick one of its answers*.
3. **A wait across parties** on the map's node: `"waits_for": [{"goal": "auth-api", "party": "backend", "party_name":
   "Backend", "title": "Auth API", "flag": ""}]` (`flag` the date once it is raised; the wait ends then); `[]` with none.
4. **The project's level**: `ideas.map`'s `project` gains `"collisions": [{"id": "auth-api|sign-in-screen", "a":
   "auth-api", "b": "sign-in-screen"}]`, the open ones; and a wait is read from the nodes' `waits_for`.
5. The Orkmaster's head on its stop: `project.orkmaster` (spec 70 §1.1).

## As built (A)
Part A, the host; no desktop or phone file. The shapes of §8 are as written; what A adds or fixes is below.
- **`realm/collide.py`** (new, code only). `touches(root, state_dir, slug)`: the page's `touches`, the plan's tasks' `files` (a list of paths) and a path in
  backticks in the brief of a task not merged yet (one with a `/`), the `files` of the merged tasks; normalised by `norm` (forward slashes, no `./`, a glob
  tail `/*` is its folder, a folder ends with `/`, a last name with no dot is a folder, prose is no path), sorted, ≤ 40. `shared(a, b)`: the same path or a
  folder and what is in it; `tests/` (and `test_*`) and docs (`docs/`, `*.md`, `.rst`, `.txt`) are left out unless both goals touch docs only.
  `overlaps(root, state_dir, slug, planned=False)` → `[{"other", "paths"}]` with the open goals (not `done`/`passed`/`sent`/`proposed`, not General's, not an
  Ideation party's, not a release) of **other parties**; `planned`: only goals that have a plan. `later_of(state_dir, a, b)`: the later by the plan's `made_at`; a goal
  with no plan is later than one with a plan; a tie is `a`. `pair_id(a, b)` = `"a|b"` sorted.
- **`<state_dir>/collide.json`**: `{"open": [stop], "answered": [{id, by, answer, at, note?}]}`; a stop is `{id, by, asked, other, why (≤ 200), first, at}`
  (`asked` the goal the question is on, `other` the one beside it; `goals` in the row is `[other, asked]`). The last 200 answers and 50 open stops are kept.
  `answered`'s `answer` is the stop's answer, or `no` when the judge said they do not collide. `known(state_dir, pair, by)`: open, or answered: a plan made never asks
  a pair answered by anything; a spec changed (`change`) may ask once a pair that was answered by `plan` (the one deviation from "never again": a changed spec is new).
- **§8.1 the row** is built by `collide.rows(root, state_dir, tracks=, state_of=)`, put in `ideas.board`'s `needs_you` (after the goals', `sort_needs` unchanged:
  not last, not blocking) and on the Map's node (`board_map.build`; `NEEDS` ends with `"collide"`, so a node that has a `plan` row too says `plan`); the snapshot's
  `needs_you` counts it. A stop whose goal is gone, done, sent or passed is not shown. `ideas.board`'s `ideas[]` rows are unchanged.
- **§8.2 `ideas.collide_answer {id, answer}`** (`gui/ideas_project.py` `ProjectMixin`): refusals in the spec's order; `device` is read for the event. `first:<slug>` →
  `collide.add_dependency` (the other goal's `depends_on` JSON and a line of its *Depends on* section; `changed` is not marked) and `autostart` of it decided again
  (refused *«x» waits for «y» already* when it would close a cycle); `one` → the later goal's *Gist* (`Joined from «title»: …`) and new *Done when* lines join the
  earlier's through `idea_change.update` (spec 62's `changed`, one line in *Decisions*), then `ideas.drop` of the later; refused *«x» has started: leave it, or let it
  finish* when a task of the later has started; the answer's `note` is `joined into «<earlier title>»`. `replan` → `collide.set_told` (`ideas/<slug>/collide_told.txt`),
  then `keeper.revise` when the plan is passed, else `keeper.plan`; the leader's `plan_prompt` and `revise_prompt` read it (*The Orkmaster tells you: …*), and it is
  cleared when the plan or the plan change is saved. `leave` writes nothing. An answer that raises (the keeper busy) puts the stop back, open.
- **§8.3 the node's `waits_for`**: `[{goal, party, party_name, title, flag}]`, from `depends_on` entries that exist and are in another party; `flag` is the flag's `at`
  once raised (the entry stays, the wait is over), `""` before; `[]` with none; on a Map of one party too. `waits_on` (spec 35, done or not) is unchanged.
- **§4 the hold**: `collide.holds(root, state_dir, slug)` (other parties' `depends_on` goals without a flag) makes `autostart` return `wait`; the person's own **Start** is
  not held. `_raise_flag` calls `collide_released(slug)`: each goal of another party that names it is decided again (`autostart`). Within a party `depends_on` is still
  only shown.
- **§8.4 `ideas.map` `project`** gains `collisions: [{"id", "a", "b"}]` (the open ones, the pair sorted, also on `{goal}`) and, beyond §8, `collide_week:
  {asked, answered, taken, usd}` (§5: the stops opened, answered, answered but *Leave it*, and the judge's cost in 7 days, from the event log; `usd` null when none priced).
- **The finder and the judge** (`ProjectMixin.collide_plan`, `collide_changed`, `collide_run`): at `plan_made` (a line in `Ideas._state_event`) and, from the bus
  (`settle_change`), when a goal's `changed` (spec 62) gets a section it had not, in a background thread, one thread per pair at a time. No overlap: no call, no
  event. `core/idea_collide.py` `judge(keeper, asked, beside, by, words)`: one call, no tools, as the `orkmaster` role on the Target's new step `collide`
  (`idea_target`: thrift laborer, balance warrior·low, quality warrior·medium; ≤ 3 000 characters of context, $0.05 cap; spend stage `plan`), the two goals' titles,
  *Done when*, touches and the shared paths (by a change: the changed sections' words, ≤ 1 200), the answer `{"collide": bool, "why", "first"}` read strictly
  (`collide` must be a bool; `first` not one of the two is ""). `orkmaster.install(state_dir)` writes `roles/orkmaster.md` (`warrior`, takes no task type) the first time
  it judges; `orkmaster.role` reads it, else the default. `core/idea_judge.py`'s `role_as`/`speak_as`/`pick_as` know the role. A judge that cannot run (demo, budget, a spent
  window, no model, an answer that is no JSON) is logged and skipped; `collide_found` says `judged: false`; the plan goes on; the pair is asked again next time.
  **A plan is not held for the question**: the person's answer comes after the judge, and a plan may have auto-started meanwhile (then *One goal* is refused).
  A change is compared with goals that have a plan only.
- **Events** (`realm/event_log.py`): `collide_found` {pair, by, judged, collide, tokens, cost}, `collide_answered` {pair, answer (`first:<slug>` · `one` · `replan` ·
  `leave`), device}. Slugs only, no goal's words. `TERMS` has `collide` (*collision*, *collisions*).
- **Tests**: new `tests/test_collide.py` (14) and `tests/test_idea_collide.py` (22), `test_lexicon.py` (+1). Not done: push words for a `collide` row (the phone's push says
  *waits for your answer*; `phone_push.KIND_WORDS` is tied to the page's table), and the Orkmaster's cost on a party's work (the week is `project.collide_week`).

## As built (B)
Part B, the desktop, against the stub host of `tests/test_collide_desktop_browser.py` with the shapes of §8; no Python and no `pwa/` file touched.
- **The stop** (`js/arena/collide.js`, `collidewords.js`; `stops.js`, `arenawords.js`): `collide` is a kind of stop as `plan` and `change` are. Its card is the small one: the Orkmaster's small head from
  `project.orkmaster` (`stopsOf` takes it as its fourth argument, `handOf` gives it) beside *Orkmaster asks*, the two goals one line each (element, *<party> · <goal>*; a press opens that goal), the judge's why
  as the stop's note (two lines), and one button for each of `collide.answers`: *<goal> first*, *One goal*, *Leave it*, *Re-plan it*, each with what happens in its title; the judge's `first` is the primary
  one (none suggested: the first). A press sends `ideas.collide_answer {id, answer}`. The statement (`text`) is the stop's aria-label, not drawn. A press outside the buttons opens the goal asked about; the
  stop is as urgent as a plan's (1) and rings that goal's cards as a plan does. A stop of another party says its party as every other.
- **The row** (`goalwords.js` `goalMark`, `goals.js`, `column.css`): a goal with an open `waits_for` (its `flag` empty) and no stronger sign wears orkUI's `before` sign; *waits for <party> · <goal>* is in its
  title whatever sign it wears. A button over the sign (`.arena-goal__go`, 20 × 28, nothing drawn) opens the first goal waited for: its party shown, that goal the one picked. A raised flag ends the wait. A goal
  with a collision stop asked about wears the alert sign (`needs_you: "collide"`).
- **The level** (`project.js` `useLinks`, `collidewords.js` `orkLinks`, `arrows.js`): the Orkmaster's links are drawn always, not only on a hover: an open collision (`project.collisions`) is a plain line in
  `--ork-alert` between its two decks, no head; a wait is the dashed ink arrow from the goal waited for to the one that waits. A link whose deck is not shown (a flag under its fold) is not drawn; the links are
  redrawn when the level's width changes. `segment` now says its `tip`.
- **An older host**: no `collide` row, no `waits_for`, no `project.collisions`: no stop, no sign, no link (a test).
- Words are in `collidewords.js`; `KIND_WORD.collide` is *Orkmaster asks*. Screenshots: `desk-collide-stop.png`, `desk-collide-project.png`.
