# 144. A spec's wait is one setting and a clock time; a change to a spec goes through the Orkmaster and comes back as one card

Decisions §224.3–§224.4 and §225 (the desktop; the phone's faces wait for §222's mockup). **Builds:** the cheaper model,
A, then B, then C, then D, each its own commit into `main` as its tests and the critical ones are green (CLAUDE.md, Alpha) ·
**Review:** the critical tests and each part's own · P1. No new pane, column, drawer or dialog. No change to orkUI.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The look's wait (host)** | the setting *Give me time to look*; a spec made waits for it before its plan is passed by itself; a clock time, kept with the plan; written and ticked by code | `settings.py` (`IDEAS`, `BOARD`), `gui/ideas_board.py` (`autostart`, a `look_tick` beside `night_tick`), `gui/ideas_route.py` (the host's clock), `realm/event_log.py`, `gui/ideas_roles.py` / `realm/board_map.py` (the node's `start_at`); new `tests/test_look_wait.py` |
| **B. The look's wait (page)** | the setting in Settings; To review's card and line at a clock time, never a countdown | `gui/static/js/shell/settings.js`, `table/piles.js`, `table/column.js`, `realm/lexicon.py`; `tests/test_column_browser.py`, the settings' browser test |
| **C. A change through the Orkmaster (host)** | `ideas.spec_change`: the Orkmaster routes the person's words to the leaders whose sections they touch; they rewrite; one record; Accept writes them all and begins the wait again | new `realm/spec_change.py`, new `core/idea_spec_change.py`, new `gui/ideas_spec_change.py`, `realm/board_map.py` (its Needs you row); new `tests/test_spec_change.py` |
| **D. A change through the Orkmaster (page)** | the field on the Orkmaster's head of a goal picked; *It goes to …* before it is sent; one card in the hand, a tab a leader, *Now* and *Proposed*; *Accept and start* | `gui/static/js/hand/*` (a card beside `changecard.js`), `table/*` (the Orkmaster's head of a goal picked, `ask.js`); new `tests/test_spec_change_browser.py` |

**Not this spec:** the phone's screens of §222–§224 (they wait for the owner's look at `docs/mockups/phone/goal-lens-v4.html`);
the decision's own wait before its spec is written (spec 120 §3.5, `realm/idea_ripe.py`: it stays as built, §240); a change of one
leader (§224.5: spec 128 E, as built).

## 0. What is there today

- A decision all leaders agreed on waits 60 s or 10 min before its spec is written (`realm/idea_ripe.py`, `ripe` in `way.json`),
  ticked only while a face is open (`gui/ideas_route.py` `ripe_tick`). That is the decision's wait, not the spec's.
- A spec made is a plan (`state == "plan"`): `gui/ideas_board.py` `autostart` passes it at once when `idea_risk.decide` says
  `start`, or holds it for the night (`start_at: "night"`, `held_for_night`) when *Work at night* is on. There is no wait for a
  look: a spec the person would read starts before they can.
- The column's To review (`table/piles.js`) reads `n.back.ripe` for its bar and says *starts by itself in 4 min* /
  *next in 4 min*: a countdown, and of the decision's wait, which has ended by then.
- A change to a goal goes to one leader (`realm/leader_change.py`, `core/idea_leader_change.py`, `hand/changecard.js`).
  Nothing routes a person's words to several leaders at once.

## A. The look's wait (host) (§225.1, §224.3)

1. **The setting.** `IDEAS["look_wait"]`, one of `"30m"`, `"2h"`, `"tonight"`, `"none"`; `"2h"` at first. It is the project's (add
   it to `BOARD`, so `.orkcraft/board.json` keeps it) and set by the Board's settings command as `autostart` and `night` are
   (`ideas.board_set` and `board_settings` in `gui/ideas_board.py`, through `settings.clean_ideas`; its refusal *Give me time to look is 30 min, 2 h, until tonight or do not wait*). An unknown value reads as `"2h"`.
2. **When it applies.** In `autostart`, where today it would `pass_plan(slug, "auto")` (what is `start`, not `wait`, not `night`):
   with `look_wait` not `"none"` and no `look_until` yet on the plan, it writes `look_until` (epoch seconds) and `start_at`
   (the same, as an ISO time the faces read) on the plan (`ideas.edit_plan`), publishes, records `look_waits` (idea, until), and
   returns `"look"`. It does not pass the plan. `"30m"` and `"2h"` count from now; `"tonight"` is the night window's next start
   (`settings.IDEAS["night"]`'s first half, today or tomorrow, the person's local time) and reuses nothing of the night's hold.
   A plan the person passes (*Start now*, `ideas.start_now`, any press) is passed as today and its `look_until` dropped.
   *Pick and build now* (`build_now`) never waits: it is a press.
3. **When it ends.** A `look_tick(now)` beside `night_tick`, called from the host's clock where `ripe_tick` is: each plan with
   `look_until <= now`, not passed, not stopped, `state == "plan"`, is decided again by `autostart` with the wait marked done
   (`look_done: true`), so the money rule, the night, the collisions and the open questions still hold it. A clock time, not a
   countdown: the time passes with no face open too (§224.3 says *starts by itself at 13:40*; the decision's wait keeps its
   *only while a face is open*). The event `look_ended` (idea, how: `started` · `night` · `wait`).
4. **Held while it is being changed** (§224.3): while a change through the Orkmaster (C) is open on the goal (from the first
   word sent until Accept, Drop it or a failure), `look_tick` skips it; Accept begins the wait again from the accepting (a new
   `look_until`, C.5).
5. **The node.** The plan's `start_at` and `look_until` reach the snapshot as the night's `start_at` does (`gui/ideas_roles.py:246`
   and wherever the column's node is built); `start_at == "night"` keeps its meaning.
6. **Tests** (`tests/test_look_wait.py`, a fake clock): `"none"` passes at once as today; `"30m"` writes `look_until` 1800 s ahead and
   passes nothing; `look_tick` before it passes nothing, after it passes the plan; `"tonight"` gives the night's next start;
   `autostart` off still waits for the person; a press passes at once and drops `look_until`; *Work at night* on and the night
   closed: when the look ends the plan is held for the night, not started; a change open on the goal: the tick skips it.

## B. The look's wait (page) (§225.1, §224.3)

1. **Settings** (`js/shell/settings.js`, *This project*): one row *Give me time to look* with four choices,
   *30 min · 2 h · until tonight · do not wait*, and under it the line *If you do not look, it starts: you give every spec 2 hours*
   (the choice's words in it; *do not wait*: *A spec starts as soon as it is made*).
2. **To review** (`table/piles.js`, `column.js`): a card whose node has `look_until` in the future says *Starts by itself at 13:40*
   (its title, `sayOf`) and the line under the pile *next at 13:40*; never *in 4 min*. Its bar is quiet and has no number. A card
   with no `look_until` reads as today. The decision's wait in *In analysis* (`waitRuns`) is not touched.
3. **Words** in `TERMS` (`realm/lexicon.py`): `look_wait` *Give me time to look*. The browser test of the column: a node with
   `look_until` says the clock time and no minutes; the settings test: the four choices and the line.

## C. A change through the Orkmaster (host) (§224.4, §225.2–3)

1. **The command.** `ideas.spec_change {idea, text}` on a goal whose spec is made or being made (the states `ripe` allows a change
   in: `leader_change.CHANGE_STATES` less `working`). It answers at once `{ok, id, parties, estimate}`: `parties` the leaders it goes
   to, `estimate` its calls and cost, read by code before any model: `ideas.spec_change_preview {idea, text}` answers the same with
   nothing started, for the field's *It goes to Tech, Art · about 3 calls* (§224.4). The parties come from the Orkmaster's route
   (the route step, at the route's tier) given the person's words and the spec's sections; `@Tech` in the words is §224.5's one
   leader and goes to `ideas.change` as built.
2. **The way.** In the background (`core/idea_spec_change.py`, the keeper's thread as `core/idea_leader_change.py` is): the route
   names the parties; each named party's leader rewrites its own section from the words (the same call and cleaning as
   `idea_leader_change` makes for its *Will be* lines, its plan change for tasks not started); the join says whether the sections
   agree (one line). A tool out of room or paid stops it with the tool's words (`status: failed`).
3. **The record.** `realm/spec_change.py`, `<state_folder>/spec_changes.json`, as `leader_change.py`'s file:
   `{id, idea, text, status (asking · ready · failed), parties: [{party, before: {lines}, after: {lines}, change}], agree, estimate,
   made_at, error}`. Its Needs you row is `kind: "spec_change"`, asked by the Orkmaster (`asker: "orkmaster"`), one a goal.
4. **The acts.** `ideas.spec_change_take {idea, id}`: every party's lines written into its section (`leader_change.write_lines`), each
   plan change taken (`idea_change`), the person's words written into the goal's Decisions once; then A.4's wait begins again from
   now (`look_until` anew) and, when the limits run low, the plan waits as the hand's *after the reset* does (§221.5: the reading
   done, the work waiting). `ideas.spec_change_more {idea, id}` (*Talk more*): the record dropped, the field opened with the words.
   `ideas.spec_change_drop {idea, id}` (*Drop it*): dropped, nothing else changes. Events `spec_change_asked`, `spec_change_answered`
   (take · more · drop), in `realm/event_log.py`.
5. **Tests** (`tests/test_spec_change.py`, the tools faked as `tests/test_tools_host.py` does): a change touching two sections goes to
   their two parties, comes back as one record with two tabs' lines, Accept writes both sections and one Decisions line and sets a
   new `look_until`; *Drop it* changes no file; `@Tech` goes to `ideas.change`; a failed route is `failed` with the tool's words;
   while the record is `asking` the look's tick skips the goal.

## D. A change through the Orkmaster (page) (§224.4, §225.2–3)

1. **Where it is written.** On a goal picked, the Orkmaster's head (the pane's, where a goal's leaders' heads are) opens the bubble
   (`table/ask.js`'s field) addressed to the Orkmaster; before it is sent, under the field, `ideas.spec_change_preview`'s
   *It goes to Tech, Art · about 3 calls* (debounced, as the field's other hints are). Sent: the goal's card in To review says
   *Held while its leaders rewrite*.
2. **The card.** One card in the hand for the goal (`kind: "spec_change"`), its asker the Orkmaster's crowned head. Lifted: the
   person's words, then a tab a party (its head and name) with *Now* and *Proposed*, the join's line, the cost, and
   **Accept and start** (the limits allow), or *Accept · starts after the reset, Mon 09:00* (they run low: the tool's next reset, as
   the potions say it), *Talk more*, *Drop it*. While `asking`, the card says *Its leaders are rewriting* and has *Drop it* only.
3. **Tests** (`tests/test_spec_change_browser.py`, a stub host): the preview line under the field; the card's tabs and its three
   acts; Accept sends `ideas.spec_change_take`; the low-limits words with a stub reset.
