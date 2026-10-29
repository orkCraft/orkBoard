# 108. A leader says no, and shows where it hurts: objections in Talk, concerns on every map

Decisions §183 (1–9). The owner, 29 October: *a party's leader must be able to refuse and argue with the person, not agree to
every want: Product really prioritises and says no, this is not needed, because…; Tech says this makes the architecture
worse. And every leader looks at its own map and lights where the problems are: the architecture, the design,
accessibility, the game's loop, whatever its map shows.* **Builds:** Claude (the cheaper model builds, the spec's author
reviews) · **Review:** full · P1. After spec 107 has landed (it changes the System's face, the loop's file and adds
`ideas.pickables`, which A here moves into `realm/`).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Concerns, the engine** | a map's parts and their ids, the signals by code, the leader's call, the record | new `realm/map_parts.py`, new `realm/map_signals.py`, new `realm/concerns.py`, new `core/idea_concerns.py`, new `gui/ideas_concerns.py`; `realm/lexicon.py`, `realm/event_log.py`, `realm/idea_target.py`, `core/idea_keeper.py`, the `ideas.pickables` command (spec 107 K); new `tests/test_map_parts.py`, `tests/test_map_signals.py`, `tests/test_concerns.py` |
| **B. Concerns, the faces** | the marks on any map, the strip, the card's back, *Make it a goal*, *Not a problem*, *Ask again* | new `js/table/concerns.js`, new `js/table/concerns.css`; `js/table/pane.js`, `js/table/syspane.js`, `js/table/maps.js`; `tests/test_design_system.py` (`SHEETS` reads the folder); new `tests/test_concerns_desktop_browser.py` |
| **C. Objections** | a verdict in Talk; a *no* is a card in the hand; the decision says who was overruled | `core/idea_talk.py`, `realm/idea_talk_parse.py`, `realm/board_map.py`, `core/idea_decide.py`, `gui/ideas_route.py` (or where Talk's answers are), `js/hand/*` (the card), `realm/event_log.py`; `tests/test_idea_talk.py`, `tests/test_idea_decide.py`, a browser test of the card |

## 0. What is there today

- **Talk** (spec 99 §5, `core/idea_talk.py`): each leader of a goal's route answers a round with `stance`, `for`, `against`
  (a line each) and questions (cards). The prompt asks it to *say where your party stands and ask what you need*: nothing
  in it lets a leader refuse, and `against` changes nothing. The decision (`core/idea_decide.py`) is worded by the
  Orkmaster and confirmed by the person.
- **The maps** (spec 102, spec 89): every party with a map has its text for the leader's calls (`realm/map_text.of(party,
  …)`: System, screens, the opportunity tree, the loop, art, release, the way in) and its cards drawn with `Pickable`
  (`data-pick-map`, `data-pick-id`, `data-pick-name`; System's cards stamped by `syspane.js`).
- **Nothing on a map says something is wrong.** §151.4 decided a specialist's view as marks on its party's map, the alert on
  the cards it has something to say about; spec 102 left it to S4 and it was never built. The game's loop gains findings
  by code in spec 107 N (`loop.findings`).

## 1. The word

**concern** (`TERMS`: *concern / concerns*): what a party's leader (later a specialist) says is wrong or at risk in one part
of its party's map, with why and what would fix it. Not *flag* (§50's), not *finding* (a check's, spec 43).

## 2. Part A: concerns, the engine

### 2.1 A map's parts (`realm/map_parts.py`, no face)
`parts(state_dir, root, party) -> [{map, id, name, group?}]`: every card a party's map draws, **with the ids its face stamps**
(the same function the faces' data comes from, or the same rule, tested against them). Spec 107 K's `ideas.pickables` reads
this function (its logic moves here from `gui/`).

### 2.2 Signals by code (`realm/map_signals.py`, no face, no model)
`signals(state_dir, root, party) -> [{on: id, kind, words}]`, at most 20, each grounded in what the map holds:
- **Tech (System)**: a part used by many (fan-in ≥ 8) or using many (fan-out ≥ 12); a cycle between parts; a part over
  800 lines; a shared part changed from two containers in the last 30 days (git log); a part changed ≥ 6 times in 30 days
  with no test file mapped to it (`gate_config.gate_files`' map).
- **Game design (the loop)**: `loop.findings` (spec 107 N), each on the loop, step or currency it names.
- **Design (screens)**: a screen nothing leads to; a screen that leads nowhere and is no end; a screen with no picture.
- **Product (the tree)**: a screen or step with three pains or more pinned; a pain pinned to nothing.
- **Art, Release, Marketing**: none by code yet (`[]`): their leader reads the map alone.

### 2.3 The leader's look (`core/idea_concerns.py`, a mixin of `IdeaKeeper` as `idea_talk.py` is)
`keeper.concerns(party, why)`: one call in the background, step **`concerns`** (the cheaper tier, `idea_target`; **READS 0**,
except Design: **READS 4**, the pictures of the screens changed since its last look, so it can speak of what it sees,
contrast and touch targets among it), in the party leader's voice (as Talk's round speaks), given:
- its map's text (`map_text.of`), the signals (§2.2), the project's facts (`project_facts.for_call`);
- the concerns the person answered *Not a problem* (their part and words: never raised again unless the part changed);
- the parts' ids and names it may speak of (§2.1).

The prompt (in words like these): *You lead <party>. Look at your map as the one who answers for it: where is it wrong, at
risk, or about to hurt the product? Say only what you would stand behind before the person; a signal from code is a hint,
not a verdict: drop it when it does not matter, say why it does when it does. Speak of the parts below by their ids. At
most seven; none is a fine answer.*

Answer: `{"concerns": [{"on": "<id>", "level": "alert" | "note", "what": "…", "why": "…", "fix": "…"}]}` (each a line, 200
characters at most; `alert`: it hurts now or blocks goals; `note`: worth knowing). Parsed strictly: an `on` not among the
parts is dropped.

**When** (never for a party nobody looks at): the person opens a party's map and it has no look yet, or its map changed
since the last look (spec 89 §1's snapshot at each landing; another map: its text's hash) and the last look is a day old or
more; or the person presses **Ask <leader> again**. One look at a time a party; `_may_run`, `refuse_spent` as every keeper
call; a spent window says so on the strip and waits.

### 2.4 The record (`realm/concerns.py`)
`<state_dir>/concerns/<party>.json`: `{at, map_hash, by (the leader's role), status ("ready" | "looking" | "failed"),
error, measure, concerns: [{id, on, name, level, what, why, fix, signal (the kind it came from, or "")}], dismissed: [{on,
what, at, map_hash}]}`. `dismiss(party, id)` moves one to `dismissed`; `made_goal(party, id, idea)` notes the goal made of it.

### 2.5 Commands (`gui/ideas_concerns.py`)
`ideas.concerns {party}` (the record; starts a look when §2.3 says so), `ideas.concerns_again {party}`,
`ideas.concern_dismiss {party, id}`, `ideas.concern_goal {party, id}` (an `ideas.add` with the party, the concern's `what`
and `fix` as its text, the part as its mark, the type a map's default: Tech *restructure*, Design *screen*, Game design
*balance*, else none). The snapshot carries each party's counts (`alerts`, `notes`) for the tab.

### 2.6 Events
`concerns_made {party, n, alerts, notes, signals, seconds, cost}`, `concern_opened {party, level}`, `concern_goal {party,
level, idea}`, `concern_dismissed {party, level}`. After a week: how many concerns became goals, how many were dismissed
(a leader whose concerns are mostly dismissed is told less is more in its prompt).

## 3. Part B: concerns on the maps

1. **On any map** (`js/table/concerns.js`, painted as picking paints, by `[data-pick-map][data-pick-id]`, so a map draws
   nothing of it): a card with an `alert` concern wears orkUI's alert mark (**!**) in the alert tone at its top right and
   the leader's small head beside it; a `note` a small dot in the muted ink. Several on one card: the highest level, the
   count in its label only (`aria-label`: *2 concerns of the Architect*).
2. **The strip** over the map, under the party's header: the leader's head and *The Architect: 2 alerts, 3 notes* (none:
   *The Architect sees nothing wrong*, while looking: *The Architect is looking at the map…* with orkUI's busy mark) and
   **Ask again**. A press on the counts steps through the marked cards.
3. **A press on a marked card** lifts it (as picking lifts) and its back lists the concerns: *what* (body), *why*, *fix*
   (muted), each with **Make it a goal** (primary) and **Not a problem**. Made into a goal: its mark becomes the goal's
   element's colour and a link to the goal.
4. **The party's tab** shows a small **!** when its map has an alert (no count, §145.3).
5. Under `prefers-reduced-motion` nothing moves; the marks are drawn in orkUI's pieces only.

## 4. Part C: objections in Talk

1. **The round's answer** (`idea_talk.py`, `idea_talk_parse.clean_round`) gains `verdict`: `go` | `doubt` | `no`, `why` (a
   line, required for doubt and no) and `instead` (a line, optional: a smaller or different goal that would serve). `stance`
   stays.
2. **The prompt** (round 1) says, besides what it says today: *You are not here to agree. Judge the goal as the one who
   answers for <party>: Product weighs it against the goals in line and the product's aim, Tech against the architecture
   on its map, Design against the people's way through the screens, Game design against the loop and its economy, and so
   on. Say no when it is not worth its cost now or harms what your party keeps; say it plainly, with the part, the goal in
   line or the fact it rests on; a no without one is not a no. A worse thing than a needless goal is one you let through in
   silence.* It is given its **concerns** (§2) and, for a party whose craft is Product, **the goals in line** (titles and
   parties, `lineNow`'s order, at most ten).
3. **A `no` is a card in the hand** (Needs you kind **`objection`**, before the decision): the leader's head, *The
   Architect says no*, its `why`, and `instead` when given. Answers:
   - **Drop the goal** (`ideas.drop`),
   - **Do the smaller one** (when `instead`: the goal's words become `instead`, Talk is not run again),
   - **Not now** (only for Product's no that names a goal in line: the goal waits on it, `waits_on`),
   - **Go on anyway** (the decision goes on; the entry says it).
   Several leaders' no: one card each, in the route's order. A `doubt` is no card: it is said on the decision's card.
4. **The decision** (`idea_decide.py`) is given the verdicts; the entry it words says each `no` overruled (*Against the
   Architect: it adds a third caller to `server/ws`*) and each `doubt`.
5. **Events**: `leader_objected {idea, party, verdict, has_instead}`, `objection_answered {idea, party, answer}`. After a week:
   when the person goes on anyway more than four times in five, the rule's words are too strong and are softened.

## 5. Later (not here)

Specialists' concerns (§151.4: Security's parts at risk, the Tester's cover, Accessibility's report by screen): the same
record with `by` the specialist, their own small head on the marks. The phone: none of this until §180.1 is asked again.

## 6. Order and tests

A, then B and C (B needs A; C reads A's record and stands without it). Each keeps the critical tests green
(`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and its modules' tests. A's call is
tested with a fake keeper call (as Talk's tests do): ids not on the map dropped, seven at most, dismissed ones passed in,
no call for a party not opened. C: a `no` makes the card, each answer does what it says, the decision entry names the
overruled.
