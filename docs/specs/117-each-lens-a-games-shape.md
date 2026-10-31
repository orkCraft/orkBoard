# 117. Each lens a game's shape: heat on its parts, a goal's reach before it starts

Decisions §195. The owner, 31 October: *we refer to board games everywhere: give each tab the right picture, a nod to some
game*; on the mockup of Tech's System (`docs/mockups/tech-reach/`): *the direction is right; do it for every lens, then build
it on the cheaper model.* **Builds:** the cheaper model, each part reviewed by the spec's author · **Review:** full · P1. No
mockup but Tech's: the faces' browser tests keep their screenshots (`ORKCRAFT_SHOTS_DIR`) for the owner's look. **Waves**
(parts in a wave share no file): **1** A, C, D; **2** E; **3** F, G, H, I, J; then **the lead** (the end of §9).

**What it is, and is not:** two rules every leader's map gains, read by code with no call, and each map's layout turned to the
game whose loop is its work, its cards unchanged. **Heat**: the hints code finds on a part (`map_signals`), drawn on it.
**Reach**: what a goal will change on the open tab's map and how far that goes by the map's own relation, shown while the
goal is under the pointer in the hand or picked. Not: a new tab, pane, column, drawer, dialog or count of what waits (§104.0,
§145); a free graph (System stays its columns, `systemarch.js`: *never a diagram*); a spread that moves by itself, a timer, a
score or a percentage of risk; a new colour (the edges wear the goal's element, §186); the games' names or words where a
person reads; a reach for a goal whose spec does not yet say what will change; the phone's app (spec 103); Play (spec 115);
the project's Board; the hypotheses' faces (spec 116 is not built: its cards become the tree's parts when it is, and take
both rules through the kit with no more work).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Heat and reach, read** | every hint by part; each map's relation; a goal's parts on a map; what a test checks; the two commands | `realm/map_signals.py` (`limit`, `tested` public), new `realm/map_reach.py`, new `gui/ideas_reach.py` (wired in `gui/ideas.py`); new `tests/test_map_reach.py`, new `tests/test_gui_reach.py`, `tests/test_map_signals.py` |
| **C. Dev and main's data** | a goal's age; the gate's own list of what waits; where a batch turns big | `realm/release_map.py`; `tests/test_release_map.py` |
| **D. Art's data** | an asset's weight; a kind's total; the project's budget | `realm/art_map.py`; `tests/test_art_map.py` |
| **E. The kit** | heat and reach painted on any map's cards; the hand's card under the pointer; the strip's line | new `js/table/heat.js`, `heat.css`, `reach.js`, `reach.css`; `js/table/concerns.js`, `concerns.css`, `js/table/pane.js`, `js/hand/state.js`, `js/hand/stopcard.js`; new `tests/test_reach_browser.py` |
| **F. System, a network** | a link lights when a reach crosses it | `js/arena/systemarch.js`, `js/arena/systemmap.css`; new `tests/test_system_reach_browser.py` |
| **G. Screens, rooms** | doors in and out on a screen's sides, walls where there are none | `js/table/screensmap.js`, `screenparts.js`, `screens.css`; `tests/test_screens_desktop_browser.py`, new `tests/test_rooms_browser.py` |
| **H. The loop, a rondel** | the ring closed; what a step gives and takes as tokens on it | `js/table/loopmap.js`, `loopparts.js`, new `rondel.css`; new `tests/test_rondel_browser.py` |
| **I. Art, an inventory** | a card's width its weight; a lane's total; the budget; an unnamed asset faint | `js/table/artmap.js`, new `inventory.css`; new `tests/test_inventory_browser.py` |
| **J. Dev and main, a train** | the goals as cars oldest first, their age, where the batch turns big | `js/table/releasemap.js`, new `train.css`; new `tests/test_train_browser.py` |

## 0. The words

`TERMS`: **reach** (in the lead's commit, with decisions §195). The interface:
- the strip's line, a goal shown: *<goal> changes n parts · reaches m <relation's words> · k with no test · through the
  hotspot <part>, <part>* (each clause only when it is not nothing; *1 part*, *no test* counted as written). The relation's
  words: System *through what uses them*; Screens *through the screens that lead to them*; the tree *through their jobs,
  goals and tests*; the loop *through what their currencies feed*; Dev and main *with the goals it takes to main*.
- a goal with a section for the party and no *Will be*: *<goal>: what it reaches is known once its spec says what will
  change*; a goal with no section for the party and no mark on its map: *<goal> changes nothing on <map's name>*.
- on a reached part: the shield sign (*A test checks it*, its title) or *no test*.
- Screens: a door's title *Leads here: <screen>, <screen>* / *Leads to: …*; *Where people come in* (the entry's mark).
- the loop's tokens: *+ <currency>* (gives), *− <currency>* (takes); a token's title *Gives <currency>* / *Takes <currency>*.
- Art: a lane's foot *<size> in n files*; with a budget, over the lanes *Art: <size> of the budget's <size>*, and past it
  *Art: <size>, over the budget's <size>* in the alert colour; an unnamed asset's title adds *Nothing in the code names it*.
- Dev and main: a car's age *today*, *1 day*, *n days*; the mark *From here the batch is big*.
The host returns keys and data, never these words; a hint's `words` (already plain English) is a heat square's title.

## 1. Part A: heat and reach, read (`realm/map_reach.py`, `gui/ideas_reach.py`; no model, no face)

```
map_signals.signals(state_dir, root, craft, pages=None, ref="dev", limit=MAX_SIGNALS)   # limit None: every hint (as today otherwise)
map_signals.tested(part, files, tracked, gate, root) -> bool                          # today's `_tested`, made public, unchanged

map_reach.heat(state_dir, root, craft, pages=None, ref="dev")              # {part id: [{kind, aspect, words}]}: every hint with an `on`, by part, at most three a part in map_signals' order; {} for none
map_reach.relation(state_dir, root, craft, pages=None, ref="dev")          # {part id: [part id]}: what a change of a part reaches one step out (below); {} for a map with none
map_reach.reach(rel, touched) -> {id: 0 | 1 | 2}                            # the touched 0, one step 1, two steps 2, no further; a part nearest wins
map_reach.touched(state_dir, root, slug, party, craft, pages) -> {state, ids}   # state "ok" · "no_will" · "none" (§0's words); ids the map's part ids
map_reach.guard(state_dir, root, ids, ref="dev") -> {id: bool}              # System only: True when `tested` finds a test for the part
```

1. **Heat** is `signals(..., limit=None)` grouped by `on` ("" dropped: those stay on the strip's chips), each with its
   aspect (`lens_rubrics.aspect_of`), the kinds in `ORDER` (the craft's own order where it has one), three a part. Kept per
   `(root, craft, the head of ref)` as `screen_map` keeps its read (eight entries), since a read runs git.
2. **The relation by map** (`map_parts.MAPS`' ids), directed as a change spreads:
   | map | a part reaches | read from |
   |---|---|---|
   | system | what uses it (`used_by`) | the newest snapshot (`project_map`, as `ideas.system` reads it) |
   | screens | the screens that link to it | `screen_map.read`'s `links` (`from` of each link whose `to` is it) |
   | product | a job its goals; a goal its job and its experiments; an experiment its goal | `opportunity_tree.read` (`serves`, `tests`) |
   | game-design | a step the next step of its loop (the last the first) and `cur:<id>` of each currency it gives; `cur:<id>` each step that takes it | `loop.read` |
   | release | a goal the goals `goal_main.plan(..., pick=False)` takes to main with it (its `goals` after the first) | computed for the touched goal only |
   | art, marketing | nothing | — |
3. **Touched**: the goal's page (`pages / <slug>`), its sections by party (`spec_sections.read`), **the party's section's
   *Will be* ids**, with the goal's `marks` whose `map` is this map's; each id matched to the map's parts by
   `spec_sections.same_part` (a file inside a part is the part), the parts' ids from `map_parts`. Release: the goal itself
   when it waits in dev, whatever its sections. `state`: `ok` with ids; `no_will` when the party has a section and no *Will
   be* line matched and no mark; `none` when the goal has no section for the party and no mark on the map (or, for Release,
   does not wait).
4. **Commands** (`gui/ideas_reach.py`, a mixin of the face's `IdeaKeeper` with its command table, as `ideas_tree.py`; the
   party's craft resolved as `ideas.concerns` resolves it):
   - `ideas.heat {party}` → `{map, parts: {id: [{kind, aspect, words}]}}`.
   - `ideas.reach {party, slug}` → `{map, slug, element, state, near: {id: 0|1|2}, guard: {id: bool}, links: [[from, to]]}`;
     `guard` only for System; `links` only for System: each overview link (container paths) whose two containers both hold
     a part in `near`. An unknown party or goal: the usual refusal in plain words. Nothing is written.
5. Tests: heat grouped, capped at three, "" dropped, kept per head; each relation on a small project of its kind (System's
   used_by, a link's `from`, the tree's both ways, the loop's ring closing and its currencies, Release through `plan`);
   `reach`'s two steps and nearest-wins; `touched`'s three states, a file inside a part, a mark; `guard`; both commands, a
   refusal; `signals`' limit and `tested` as before.

## 2. Part C: Dev and main's data (`realm/release_map.py`)

1. Each goal gains `at`: its commit's time (`git log -1 --format=%ct`, seconds), 0 when git cannot say.
2. The goals waiting are read as the gate reads them, `idea_gate.waiting_by_patch` (as `gui/ideas_gate.py` does), so a goal
   already sent alone through the portal is not listed again.
3. `read` gains `big_from`: `map_signals_crafts.BATCH_GOALS` (imported inside the function: that module reads this one).
4. Tests: `at`; a goal sent alone not listed; `big_from`; today's tests as they are.

## 3. Part D: Art's data (`realm/art_map.py`)

1. Each asset gains `weight`: `light` under `LIGHT` (100 KB), `heavy` at `map_signals_crafts.HEAVY_ART` bytes or more for
   art and `HEAVY_SOUND` for sound (imported inside the function), `normal` between; music, clips and fonts never `heavy`.
2. Each kind gains `bytes` (its assets' sum) beside its count.
3. `read` gains `budget`: `{bytes, of}` when the project's `orkcraft.toml` sets `[art] budget_mb` (a number above 0; `bytes`
   the Art kinds' sum, `of` the budget in bytes), else `None`; read with `tomllib`, a file that does not parse is no budget.
4. Tests: the three weights at their edges, a kind's bytes, the budget set, unset and unreadable.

## 4. Part E: the kit (`js/table/heat.js`, `reach.js`, their sheets)

1. **Heat** (`heat.js`, `heat.css`, its sheet loaded by `import.meta.url` as `concerns.js` loads its own): `ideas.heat`
   for the open tab's party, read again when `mapData.rev` moves or a task lands (as `useRead`); each card whose
   `[data-pick-id]` is in `parts` gets its kinds as hollow squares (`concerns.css`'s `.cn-hint`, 6 × 6) in **the concern's
   slot**, before its mark: `concerns.js` exports the slot's home (`homeOf`) and makes the slot when only heat needs it. The
   card gets `data-heat="<kind> <kind>"` so a map's sheet may style a kind (I, J). The squares' title: the hints' words, a
   line each. A `MutationObserver` keeps it painted, as `concerns.js` does. No count, no colour.
2. **Which goal**: `hand/state.js` gains `reachGoal = signal("")` with `markReach(slug)` / `unmarkReach(slug)` (the potion's
   `markedTool` pattern: unmark clears only its own). `hand/stopcard.js`'s card sets it on pointer enter and focus, clears it
   on leave and blur. The table's goal is `reachGoal`, else the picked goal (`frame/state.js`), else none; at the narrow
   width (no pointer) the picked or lifted goal.
3. **Reach** (`reach.js`, `reach.css`): `ideas.reach {party, slug}` for that goal and the open tab's party, kept per
   `party|slug|mapData.rev`; exports the signal `shownReach` (`{party, map, slug, element, state, near, guard, links}` or
   null) for F. Each card with `[data-pick-id]`: in `near`, an edge `<i class="rc-edge" data-near="0|1|2">` inside the card
   (inset, under its content; the card's notch would clip an outline) in `--reach: var(--ork-elem-<element>)`, solid,
   dashed, dotted; on the touched card the element's rune at its top left (`.ork-elem`); not in `near`, the card dims
   (`data-reach-dim`, opacity as the mockup's .38); System's reached parts get the shield sign or *no test* at the card's top
   left (`guard`). The edges come in nearest first, 120 ms apart (orkUI's motion tokens), none under
   `prefers-reduced-motion`. The goal leaves: everything as it was.
4. **The strip's line** (`concerns.js`'s strip, under the aspects): §0's words, its element's rune first, from `shownReach`
   and the heat (the hotspot clause: reached parts whose heat holds `hotspot`). Nothing while no goal is shown.
5. **Mounted** in `pane.js` beside `Concerns`, for every map the pane draws (System through `syspane`, the others through
   `maps.js`); the project's Board and Play are not maps of a lens: nothing there.
6. Tests (`tests/test_reach_browser.py`, a stub host answering `ideas.heat` and `ideas.reach` beside the maps' commands, as
   `test_maps_desktop_browser.py`'s `MapsHost`): heat on a card and its title; heat beside a concern's mark; the hand's card
   under the pointer lights a map's cards (solid, dashed, dotted, dimmed), and leaving clears them; a picked goal does the
   same; the guard on System; the strip's line in each `state`; reduced motion; both widths with no sideways scroll.

## 5. Part F: System, a network (`systemarch.js`)

A link whose containers are in `shownReach.links` (Tech's tab) draws its arrow and its name in `--reach` (`is-reach`); the
others as they are. Nothing else changes: the columns, the cards, the hover's one-step lighting (it stays: it says what a part
uses and what uses it, the reach says how far a change goes). Tests: a reach crossing the link lights it; one that does not
leaves it; the fit's scale keeps the edges on the cards.

## 6. Part G: Screens, rooms (`screensmap.js`, `screenparts.js`, `screens.css`)

1. Each screen card's left side shows **a door for each screen that links to it**, its right side **a door for each it links
   to**, back links and links within a step counted too: a door a gap in the card's frame, 10 px tall, at most three a side
   (more say *and n more* in the side's title). A side with none is **a wall**: the frame drawn 3 px in ink on that side. The
   entry's left side has its door from outside, marked by a small chevron (*Where people come in*).
2. So a dead end (no door out, not at the flow's end) and a screen nothing leads to (no door in, not the entry) read at a
   glance; the hints `dead_end` and `loose` are its heat besides.
3. The arrows as built; the narrow width's chips as built. Tests (`test_rooms_browser.py`): doors counted on both sides, a
   wall on each kind of screen, the entry's mark, *and n more*; `test_screens_desktop_browser.py` kept passing.

## 7. Part H: the loop, a rondel (`loopmap.js`, `loopparts.js`, `rondel.css`)

1. **The ring closes**: the chevron from the last step back to the first is drawn, as the others are.
2. **Tokens**: each step's card shows, under its line, what it gives as *+ <currency>* chips and what it takes as
   *− <currency>* chips (orkUI chips in ink, the currency's name up to 12 characters, three at most then *+n*), from the
   step's `gives` and `takes`. The economy's panel stays as built; its currency cards take heat (`no_source`, `pile_up`)
   through the kit.
3. At the narrow width (the loops as lists) the tokens too. Tests (`test_rondel_browser.py`): the closing chevron, the
   tokens and their titles, *+n*, the list's tokens.

## 8. Part I: Art, an inventory (`artmap.js`, `inventory.css`)

1. **A lane is a grid of 72 px cells**; a card spans one cell when `light`, two `normal`, three `heavy` (its picture filling
   it; a one-cell card shows its picture and its name in one line). The lanes' order and *and n more* as built.
2. **A lane's foot**: *<size> in n files* (the kind's `bytes`). With a `budget`, over the lanes *Art: <size> of the budget's
   <size>*, past it in the alert colour (§0).
3. **An asset nothing names** (`data-heat~="unused"`) lies faint, its frame dashed. Tests (`test_inventory_browser.py`):
   the spans, the foot, the budget under and over, the faint card, the narrow width.

## 9. Part J: Dev and main, a train (`releasemap.js`, `train.css`)

1. **Cars, oldest first** (by `at`), each the goal's card as built, coupled to the next by a short line; its age under its
   title (§0; from `at`, none when 0).
2. **Push your luck**: before the car at `big_from` (counted from the oldest), an upright dashed line with *From here the
   batch is big*; none while fewer wait.
3. **A stale goal** (`data-heat~="stale"`) lies faint. A goal's reach (the kit) shows the cars it takes to main. **To main**
   and *Since <version>* as built. Tests (`test_train_browser.py`): the order, the ages, the mark at its place and absent,
   the faint car, the narrow width's rows.

**The lead, after wave 3**: `tests/test_maps_desktop_browser.py` and `tests/test_concerns_desktop_browser.py` made to pass
with H, I and J together (the parts may not edit them: they share them); the shots looked at; this spec's *As built*.

## 10. Tests

Each part's above; the critical tests (`tests/test_architecture.py`: `realm/map_reach.py` imports no `gui/`),
`tests/test_board_alone.py`, `tests/test_updates.py`, and every touched module's.
