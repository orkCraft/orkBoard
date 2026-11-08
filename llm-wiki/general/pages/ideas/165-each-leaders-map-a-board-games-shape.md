---
owner: board
kind: idea
track: design
order: 7
size:
priority: normal
short: A board game's shape
phase: work
route: design, tech
spec: docs/specs/165-each-leaders-map-a-board-games-shape.md
by: claude-code
gate: 29ac654 · 40 files · red (560 passed; 4 browser tests red on main too: test_concerns_desktop_browser picking, test_screens_desktop_browser files_name, wide and narrow)
schema: 3
---
# Each leader's map takes a board game's shape

## Gist
Build decision §280 (the owner, 8 November; first taken on 31 October as §195 on the branch claude/spec-117, lost in a merge; that branch holds its first spec, docs/specs/117-each-lens-a-games-shape.md, and claude/tech-reach-mockup Tech's mockup): two rules on every map, heat (the hints code finds on a part drawn on it) and reach (a goal under the pointer or picked lights the parts its Will be names, one and two steps out, and dims the rest); each map's shape is its work's game (System a network game, Screens a dungeon's rooms, the tree a tech tree, the loop a rondel, Art's assets an inventory, Dev and main a train and push your luck, the way in heat only); no games' names, timer, score or new colour. Since then §206.4 shows a goal picked as each leader's view of what it changes (js/table/goalmap.js) and goal 161 laid the table's felt and light: reach grows from the first, the shapes lie on the second. Implementation on the simpler models.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
Heat and reach first, on the maps as they are (A–K, §281.4), desktop only (§281.5); then each shape a stage of its own with its picture at 1280 × 800 (L–Q). Every stage on the simpler model, its tests beside it. Goal 164 runs at the same time: only G touches one of its files (`realm/lexicon.py`); C and F read a party's craft through `map_parts.craft_of` (which reads `realm/goal_team.py`) and change nothing of it; no stage touches `seat_hero_rules.py`, `heroes.py`, `goal_team.py`, `ideas_stall.py`, `seat_rubric_rules.py`, `agent_rules_text.py` or `partyseats2.js`. Not planned (no *Done when* line asks for it): §280.2's System link lit when a reach crosses it.
- [ ] A. Every hint, uncut, and the test rule public
  - party: Tech (simpler model). `orkboard/realm/map_signals.py`: `signals(..., limit=MAX_SIGNALS)`, `limit=None` gives every hint (the cut stays the default, so `core/idea_concerns.py` is unchanged); `_tested` renamed `tested` (public, its docstring says it is map_reach's *no test* rule too), its one caller in `_tech` follows. Tests in tests/test_map_signals.py: `limit=None` on a map of more than 20 hints gives them all; the default still gives MAX_SIGNALS; `tested` as `_tested` was. Rests on §183.4, §280.1.
  - proves: Tech's Checks "Heat reads each craft's hints uncut; map_signals.signals keeps its cut at MAX_SIGNALS…"; the "not cut at 20" half of Tech's first line
- [ ] B. Heat, kept per Board change
  - party: Tech (simpler model). New `orkboard/realm/map_reach.py` (no import of `gui/`, under 600 lines): `heat(state_dir, root, craft, pages, ref)` → `[{on, kind}]` from `map_signals.signals(..., limit=None)`, a hint with no `on`, or whose `map` is another map's, dropped; and `Kept`, the host's memory: `answer(what, key)` gives what was kept (or None) and never runs git; `refresh(rev, read_head, compute)` reads dev's head once only when the Board rev moved, and computes again only what the new rev or head changed. Nothing written to the state. Tests in a new tests/test_map_reach.py: two refreshes with the same rev, `commit_goal.git` patched to fail, run no git; `answer` holds every hint, more than 20.
  - proves: Tech's "When dev's head and the Board are unchanged since the last read, then a map's heat is answered from what was kept with no git command run, and holds every hint of its craft, not cut at 20." (the realm's half); Tech's Default "kept in the host's memory per craft, dev head and Board rev"
- [ ] C. Reach on System and Screens
  - party: Tech (simpler model). `realm/map_reach.py` `reach(state_dir, root, pages, party, craft, ref)` → `{slug: {lit, one, two, no_test}}` for every goal not done whose section for `party` (`spec_sections.read`) has a *Will be* (`spec_sections.will_be`); `lit` the map's parts its lines and its marks on this map name. System (`project_map.ensure`): a part named by `spec_sections.same_part`, `one` the parts in its `used_by`, `two` theirs, none twice; `no_test` each of them `map_signals.tested` finds nothing for. Screens (`screen_map.read`): a screen named by its id, name or path without case or signs (as js/table/goalmap.js `names`), `one` and `two` its links both ways. No *Will be*, nothing named, a map that cannot be read: no entry, never an error. Tests in tests/test_map_reach.py: `changed orkboard/realm` on a fixture repository; a goal with no *Will be*; one naming nothing; an unreadable map. Rests on §280.1, §206.4.
  - proves: Tech's "When a goal's Tech section says `changed orkboard/realm`, then its reach on System is that part lit, the parts that use it one step out and theirs two out, each with no test mapped marked *no test*."; the realm's half of Tech's "When a goal's section has no *Will be*, names no part of the open map, or the map cannot be read…"
- [ ] D. Reach on the loop, the tree, Art and the way in
  - party: Tech (simpler model). A new `orkboard/realm/map_reach_crafts.py` beside map_reach (as map_signals_crafts is): `lit` by the ids `map_parts.parts` gives each map; the loop's `one` the step before and after in its loop (`loop.read`), `two` the next out; the tree's `one` a job's hypotheses (`hyp:<id>`) and goals, or a hypothesis' or a goal's job, `two` the next out (`opportunity_tree.read`, `hypotheses.read`); Art and the way in `lit` only, `no_test` always empty off System. `map_reach.reach` calls it by craft. Tests in a new tests/test_map_reach_crafts.py, one map each. Rests on §280.1 and Tech's Defaults.
  - proves: Tech's Default "The relation one and two steps out: … the loop the step before and after; the tree a part's parent and children; Art and the way in none"; Design's Check "Heat and reach are painted over the cards a map marks `Pickable`" (the ids are the stamped ones)
- [ ] E. Dev and main's reach from the plan kept
  - party: Tech (simpler model). `realm/map_reach_crafts.py`: for Release's map, each goal `release_map.read` holds (in dev, not in main): `goal_main.plan(repo, state_dir, slug, root=pages, pick=False)`, `lit` the goal's own card, `one` the other goals it takes along. Read in the refresh only (B's `Kept`), once per Board change, never on a request. Tests in tests/test_map_reach_crafts.py: `goal_main.plan` patched to record its calls: `pick=False` each time, one call a goal a Board change, no worktree under the state dir. Rests on §281.6, §280.2.
  - proves: Tech's "When the reach of a goal waiting for main is read for Dev and main, then goal_main.plan runs with pick=False once per Board change, no worktree is made, and the goals it takes along are its reach."; Design's Check "Hovering a goal never takes git's trial run on Dev and main (§281.6)" (the realm's half)
- [ ] F. `ideas.heat` and `ideas.reach`, off the request's thread
  - party: Tech (simpler model). New `orkboard/gui/ideas_reach.py`, `ReachMixin` and `reach_commands(self)`: `ideas.heat {party}` → `{party, map, heat: [{on, kind}]}`, `ideas.reach {party}` → `{party, map, goals: {slug: {lit, one, two, no_test}}}`, each from B's `Kept`; when `self.rev` moved, one refresh thread at a time (dev's head through `commit_goal.head`) and the answer is what was kept before, or empty, never a wait. A party gone or with no map: empty, no error. `gui/ideas.py` gains only the mixin's import, its place in the class's bases and `**reach_commands(self)`. Keys and data only, no interface words. Tests in a new tests/test_ideas_reach.py (a request runs no git and starts at most one refresh; a second request at the same rev starts none) and tests/test_architecture.py. Rests on §280.1, §281.6.
  - proves: Tech's first line whole; Tech's "When a goal's section has no *Will be*, names no part of the open map, or the map cannot be read, then its reach is empty and the host answers without an error."; Tech's Checks on `gui/ideas.py`, the 600 lines and "read off the request's thread"
- [ ] G. *reach* in TERMS (touches goal 164's `realm/lexicon.py`)
  - party: Tech (simpler model). `orkboard/realm/lexicon.py` `TERMS`: one line `_t("reach", "reach", "reaches")` beside `hint`, its comment *what a goal not yet started would change on a leader's map, one and two steps out (spec 165, decisions §280.1)*. Only that line: goal 164 adds its heroes' names to the same file, so it is rebased on 164's commit when that lands first. Tests in tests/test_lexicon.py. Rests on §280.1, §63.
  - proves: Tech's and Design's Check "*reach* is one word in `TERMS`"
- [ ] H. Heat's squares on every map
  - party: Tech (simpler model). New `orkboard/gui/static/js/table/heat.js` and `heat.css`, painted as concerns.js paints (concerns.js exports its `homeOf`, nothing else of it changes): reads `ideas.heat` when a map opens and when `mapData.rev` moves; on each card `[data-pick-id]` with hints, a slot beside the concern's mark holding at most three hollow squares, the first three kinds in the hints' order, each `role="img"` with its kind in words in `aria-label` and `title` (a `HEAT_WORDS` map for every kind map_signals and map_signals_crafts give, e.g. `fan_in` *used by many parts*; no game's name); a press falls through to the card. Mounted in `js/table/pane.js` around the map inside `Concerns`. orkUI's tokens only. Browser tests in a new tests/test_heat_desktop_browser.py at 1280 × 800, Tech's System and Design's screens, the host faked. Rests on §280.1, §183.5, §280.3.
  - proves: Design's "When the page opens at 1280 × 800 on any leader's tab with no goal picked, then each part with hints by code wears at most three hollow squares beside its concern's mark, each saying its hint's kind in words in its label and title."
- [ ] I. The hand names the goal under the pointer
  - party: Tech (simpler model). New `orkboard/gui/static/js/hand/reachhover.js`, installed once from `js/hand/stacks.js`: a signal `reachGoal` (a slug or ""), set from a hand card's `data-goal` after the pointer rests about 150 ms on it (not for `pointerType` touch) and at once on focus; cleared when the pointer leaves the hand, on blur out of it and on Esc. A touch press lifts the card as today and sets nothing. No command sent. Browser tests in tests/test_hand_desktop_browser.py. Rests on §280.1 and Design's Defaults.
  - proves: Design's Checks "Hover and focus light the same reach…; a touch press on a hand card lifts it, it lights nothing" (the hand's half)
- [ ] J. Reach lit, dimmed and said
  - party: Tech (simpler model). New `orkboard/gui/static/js/table/reach.js` and `reach.css`: the party's `ideas.reach` read when its map opens and when `mapData.rev` moves, kept in a signal; the goal shown is `reachGoal`, else the goal picked; its entry stamps `data-reach="lit|one|two|dim"` on each `[data-pick-id]` card, touching only cards whose state changes; the edge in the goal's element (`--ork-elem-<hue>`), solid, dashed and dotted in orkUI's pixel dashes and dots; under reduced motion at once. A line over the map, `aria-live="polite"`, in words: *changes* the lit parts' names, *reaches* the others, *no test* those marked; no count. No entry, no goal: nothing stamped, no line. Mounted in `js/table/pane.js` beside H's host. Browser tests in a new tests/test_reach_desktop_browser.py at 1280 × 800 with System open: hover and focus light the same; the commands the faked host gets while hovering are none; leaving, Esc, a goal with no *Will be* clear it all; a touch press lights nothing. Rests on §280.1, §280.3, §280.4, §281.5 (the phone's slices untouched). Then Tech's leader accepts A–J.
  - proves: Design's "When the pointer rests on, or the keyboard focuses, a goal's card in the hand with Tech's System open…", "When the pointer leaves the hand, Esc is pressed, or the card hovered is a goal whose spec has no *Will be*…"; Tech's "When the pointer rests on, or the keyboard focuses, a hand card with System open at 1280 × 800 and no goal picked, then the page sends no command to the host…"
- [ ] K. Dimmed, yet read; the edges seen
  - party: Design (simpler model). `js/table/reach.css` and `heat.css` only: a dimmed card lowers its frame and window, never its name's ink; the dashed edge one step out reads apart from orkUI's disabled (the element's colour at full strength, the name unchanged); squares clear of a small card's name. Browser tests in tests/test_reach_desktop_browser.py measuring every dimmed name against its card (4.5:1) and each edge against the felt (3:1), lamp lit and out (the pane's `is-out`), as tests/test_stall_browser.py measures; tests/test_design_system.py stays green (no colour of its own). Pictures of System with a goal hovered, lamp lit and out. Rests on §280.1, §280.3, decisions §183.5. Then Design's leader accepts its first four lines.
  - proves: Design's "When a goal's reach dims the rest of a map, lamp lit and out, then every dimmed part's name measures at least 4.5:1 over its card, and the solid, dashed and dotted edges 3:1 against the felt."; Design's Check "No new colour…"
- [ ] L. Screens as rooms
  - party: Design (simpler model). `js/table/screensmap.js`, `screenparts.js`, `screens.css`: each screen a room, a door on its left for each link in and on its right for each link out (a link back to an earlier step a door too), a wall on a side with none; its card, its `Pickable` stamp, its lift and the pains unchanged. `heat.js` draws no `loose` or `dead_end` square on the screens' map (the wall says it). Browser tests in tests/test_screens_desktop_browser.py: doors as the links, walls where none, the same `data-pick-id`s, heat and reach still painted. Its picture at 1280 × 800, no goal picked, in the pull request. Rests on §280.2, §281.4, §50.5.
  - proves: Design's [look] line, Screens' part; Design's Default on `loose` and `dead_end`
- [ ] M. The loop, a closed ring
  - party: Design (simpler model). `js/table/loopmap.js`, `loopparts.js` and the loop's sheet: each loop's steps on a ring that closes, last step to first; what a step gives and takes as small tokens on it (the currencies' names, in words for a screen reader); cards, stamps and lift unchanged. Browser tests beside the loop's (tests/test_loop*_browser.py, or a new tests/test_loop_ring_browser.py). Its picture at 1280 × 800. Rests on §280.2, §281.4.
  - proves: Design's [look] line, the loop's part
- [ ] N. Art's weights and budget, read
  - party: Tech (simpler model). `orkboard/realm/art_map.py` `read`: each asset gains `weight` (`light`, `normal`, `heavy`, by its `bytes` against constants per kind named in the module), each kind its total `bytes`, the map `budget_mb` from `orkcraft.toml` `[art] budget_mb` (read as the project's other sections are; None unset). `art_map.text` unchanged (the same bytes for the same dev). Tests in tests/test_art_map.py. Rests on §280.2.
  - proves: the data of Design's [look] line, Art's part
- [ ] O. Art's cards by weight
  - party: Design (simpler model). `js/table/artmap.js` and its sheet: a card's width by its weight, three widths from orkUI's spacing; a lane's foot its total in MB and, with a budget, *of <n> MB*; an asset no goal's reach lights (J's store) lies faint, its name still 4.5:1. Cards, stamps and lift unchanged. Browser tests in a new tests/test_art_weight_browser.py. Its picture at 1280 × 800. Rests on §280.2, §280.4.
  - proves: Design's [look] line, Art's part
- [ ] P. Dev and main's ages, read
  - party: Tech (simpler model). `orkboard/realm/release_map.py` `read`: each goal gains `at`, the time of its oldest commit main lacks (from the log release_map reads already, no git call more a goal). Tests in tests/test_release_map.py. Rests on §280.2.
  - proves: the data of Design's [look] line, Dev and main's part. Tech's leader accepts N and P.
- [ ] Q. Dev and main's goals as cars
  - party: Design (simpler model). `js/table/releasemap.js` and its sheet: the goals as cars in one row, oldest first, each its age in words (*3 days*); past the eighth car a mark where the big batch starts, said in words in its `aria-label` and `title`, no count; ticks and To main as they are. Browser tests in a new tests/test_release_cars_browser.py. Its picture at 1280 × 800. Rests on §280.2, §280.4, §281.6. Then Design's leader looks at L, M, O and Q's pictures.
  - proves: Design's [look] "When each shape's stage lands, then its tab at 1280 × 800 with no goal picked shows its shape with its cards unchanged: Screens as rooms with doors and walls, the loop a closed ring, Art's cards by weight, Dev and main's goals as cars, oldest first."

## Open questions
- Heat and reach before the shapes? (**Heat and reach first, shapes after** / All of §280 at once) — a person learns the one grammar on maps they know before every tab's layout moves · Heat and reach first, shapes after: The maps keep their layouts; each shape then lands and is looked at alone · All of §280 at once: Every tab's map changes in one goal, looked at in one pass
  - Answered: Heat and reach first, shapes after (the person, 2026-11-08)
- Reach on the phone in this goal? (**Desktop now, the phone after** / The phone in this goal) — the phone has no pointer to hover and one column (§226); its slice (§222) needs a look of its own · Desktop now, the phone after: The phone's slices stay as they are until a goal of their own · The phone in this goal: Heat and reach on the phone's slices on a pick, drawn once for both
  - Answered: Desktop now, the phone after (the person, 2026-11-08)
- Dev and main's reach on hover? (**The plan kept, without its trial** / The full plan, on a pick only) — goal_main.plan takes the git lock and may make a worktree; a hover must not wait on git · The plan kept, without its trial: Hover lights the goals it takes along; a conflict shows only at To main · The full plan, on a pick only: Hover lights nothing on Dev and main; a pick waits for git's trial
  - Answered: The plan kept, without its trial (the person, 2026-11-08)

## Decisions
- §281: the person's answers in Talk (8 November 2026)

## Design
### Talk
- verdict: doubt — every tab's map changes at once on the cheaper model; go if heat and reach land first on today's layouts, then each shape a stage of its own, looked at in a picture
- stance: Design holds the look of every map here; heat and reach serve choosing between goals, if each square names its kind and dimming keeps names readable
- for: one grammar on every tab: what code saw on a part and how far a goal spreads, seen before Start, with no call and no new colour (H1 status, H6 recognition)
- against: hover across the fanned hand repaints the whole pane; hollow squares by kind say nothing unnamed; the dungeon's wall says loose and dead_end twice beside their squares
- instead: heat and reach on every map now; the shapes after, a goal a map, starting with Screens' rooms
- assumes: a person compares goals by their reach before Start — shown by: goals picked or hovered on a map before their Start, over a week of use
### Why
- Today what code sees on a part reaches only the leader's prompt, and what a goal will change is seen only once it is picked: the map hides the system's status (H1) until a call is made.
- One grammar on every tab (squares for heat, solid, dashed and dotted edges for reach) is learned once and recognised everywhere (H4, H6), with every name still readable at AA when dimmed.
- The shapes come after, each alone in a picture, so a person never meets every tab's layout moved at once (§281.4).
### Done when
- [test] When the page opens at 1280 × 800 on any leader's tab with no goal picked, then each part with hints by code wears at most three hollow squares beside its concern's mark, each saying its hint's kind in words in its label and title.
- [test] When the pointer rests on, or the keyboard focuses, a goal's card in the hand with Tech's System open at 1280 × 800, then the parts its *Will be* names wear a solid edge in its element, one step out dashed, two dotted, the rest dimmed, and a line says *changes*, *reaches* and *no test* in words.
- [test] When a goal's reach dims the rest of a map, lamp lit and out, then every dimmed part's name measures at least 4.5:1 over its card, and the solid, dashed and dotted edges 3:1 against the felt.
- [test] When the pointer leaves the hand, Esc is pressed, or the card hovered is a goal whose spec has no *Will be*, then the open map shows no reach: nothing lit, nothing dimmed, no line.
- [look] When each shape's stage lands, then its tab at 1280 × 800 with no goal picked shows its shape with its cards unchanged: Screens as rooms with doors and walls, the loop a closed ring, Art's cards by weight, Dev and main's goals as cars, oldest first.
### Checks
- Heat and reach are painted over the cards a map marks `Pickable` (`data-pick-map`, `data-pick-id`), as concerns.js paints: no map module draws them, so a shape's stage leaves them as they are.
- No new colour: the edge is the goal's element's orkUI token, the dashes and dots orkUI's pixel ones; Orkboard's sheets carry none of their own (tests/test_design_system.py).
- No game's name, timer, score, percentage or count of what waits in the interface (§280.3, §280.4); *reach* is one word in `TERMS`, and the words are *changes*, *reaches*, *no test*.
- Hover and focus light the same reach; under reduced motion lighting and dimming are at once; a touch press on a hand card lifts it, it lights nothing.
- Hovering a goal never takes git's trial run on Dev and main (§281.6), and the phone's slices are unchanged (§281.5).
### Will be
- changed home — every leader's map gains heat's squares and a goal's reach on hover, focus or pick; then each map's shape, Design's screens as rooms with doors and walls
### Out
- Heat and reach on the phone's slices (§281.5, a goal of its own).
- A legend panel or a new drawer: each square says its kind in its own label and title.
- Dev and main's conflict on hover: it shows only at To main (§281.6).
### Risks
- high
- orkUI's dashed edge already means disabled (`.ork-btn:disabled`, `.ork-field:disabled`): a part one step out may read as switched off.
- Moving the pointer across the fanned hand may flicker the pane, each card passed lighting and dimming the map.
- Three squares beside the concern's mark may crowd a small card's corner and cover its name.
- A shape built on the simpler model may move the cards so picking, concerns and the lifted card lose their place.
### Defaults
- Design's map in this repository is the window, screen `home` (as in goal 161); no new screen is made.
- The reach lights after the pointer rests about 150 ms on a hand card and at once on focus; leaving the card or Esc clears it.
- Where the rooms' wall shows a screen nothing leads to or one that leads nowhere, the `loose` and `dead_end` squares are not drawn a second time.
- The [look] line's pictures are each shape stage's own at 1280 × 800; Tech's mockup (docs/mockups/tech-reach/ on its branch) the only reference.
### Accepted
- met: When the page opens at 1280 × 800 on any leader's tab with no goal picked, then each part with hints by code wears at most three hollow squares beside its concern's mark, each saying its hint's kind in words in its label and title.
- met: When the pointer rests on, or the keyboard focuses, a goal's card in the hand with Tech's System open at 1280 × 800, then the parts its *Will be* names wear a solid edge in its element, one step out dashed, two dotted, the rest dimmed, and a line says *changes*, *reaches* and *no test* in words.
- met: When a goal's reach dims the rest of a map, lamp lit and out, then every dimmed part's name measures at least 4.5:1 over its card, and the solid, dashed and dotted edges 3:1 against the felt.
- met: When the pointer leaves the hand, Esc is pressed, or the card hovered is a goal whose spec has no *Will be*, then the open map shows no reach: nothing lit, nothing dimmed, no line.
- met: When each shape's stage lands, then its tab at 1280 × 800 with no goal picked shows its shape with its cards unchanged: Screens as rooms with doors and walls, the loop a closed ring, Art's cards by weight, Dev and main's goals as cars, oldest first.

## Tech
### Talk
- verdict: doubt — go if heat and reach are read once per Board change in a realm module and served by a mixin of their own, not per hover through ideas.page nor added to gui/ideas.py (769 lines)
- stance: Tech builds heat and reach on System and Screens on their maps as built, from data code already reads; each other map's relation and shape is a stage of its own, looked at alone
- for: No model and little new data: map_signals already finds each part's hints, spec_sections.will_be reads Will be, System has its uses, Screens its links; goalmap.js lights a picked goal's parts
- against: map_signals.signals runs git per call and is cut at 20 for a prompt; goal_main.plan takes the git lock and may make a worktree: neither can run on a hover across the hand
- instead: heat and reach on System and Screens first, from one realm module per Board change; the rondel, tree, inventory and train after, a goal each
- assumes: the hints of every craft are read at dev's head in well under a second, so heat can follow each Board change — shown by: map_signals.signals timed for each craft on this repository
### Why
- Heat and reach are the first faces that read map_signals and every goal's *Will be* at once; read per hover they would run git under the pointer and take the git lock for Dev and main.
- Kept once per dev head and Board change in a realm module and served by a mixin of its own, they add no logic to gui/ideas.py (769 lines) and no caller of git to the hand.
### Done when
- [test] When dev's head and the Board are unchanged since the last read, then a map's heat is answered from what was kept with no git command run, and holds every hint of its craft, not cut at 20.
- [test] When a goal's Tech section says `changed orkboard/realm`, then its reach on System is that part lit, the parts that use it one step out and theirs two out, each with no test mapped marked *no test*.
- [test] When the pointer rests on, or the keyboard focuses, a hand card with System open at 1280 × 800 and no goal picked, then the page sends no command to the host: the reach shown is the one read at the last Board change.
- [test] When the reach of a goal waiting for main is read for Dev and main, then goal_main.plan runs with pick=False once per Board change, no worktree is made, and the goals it takes along are its reach.
- [test] When a goal's section has no *Will be*, names no part of the open map, or the map cannot be read, then its reach is empty and the host answers without an error.
### Checks
- tests/test_architecture.py: the new realm module imports nothing of gui/; gui/ideas.py gains only the mixin's import and its commands line; each new module stays under 600 lines.
- Heat reads each craft's hints uncut; map_signals.signals keeps its cut at MAX_SIGNALS for the leader's prompt (core/idea_concerns.py unchanged).
- The reach is one answer per Board change (each goal, each party: lit, one step, two steps, no test); hover and focus read it from the page's store, never from the host.
- `reach` is one word in lexicon `TERMS`; no game's name in a command, key, event or string the page shows.
- Heat and Dev and main's plans are read off the request's thread; a map that asks before they are kept gets what was kept before, or nothing, never a wait.
### Will be
- changed orkboard/realm — map_reach.py reads heat and reach per map, kept per dev head and Board change; map_signals gives its hints uncut and its test rule public
- changed orkboard/gui — ideas_reach.py, a mixin of its own serving `ideas.reach` and `ideas.heat`; ideas.py only registers it
- changed orkboard/gui/static/js/table — heat.js and reach.js paint over the cards a map marks Pickable, as concerns.js does; no map module draws them
- changed orkboard/gui/static/js/hand — a hand card's hover and focus name the goal whose reach the open map shows; a touch press lifts it and lights nothing
### Out
- The maps' shapes (rooms, ring, inventory, train): later stages, each with its own picture (§281.4).
- Heat and reach on the phone's slices (§281.5).
- Git's trial run for Dev and main's reach: a conflict shows only at To main (§281.6).
### Risks
- medium
- Reading every craft's hints at a new dev head may take seconds on a big repository; until they are kept, a map opens with no squares.
- goal_main.plan with pick=False still takes the git lock: read for every goal waiting for main at each Board change, it may delay a task landing.
- A *Will be* id written loosely (a file, not a folder) lights its folder's part by spec_sections.same_part, or nothing: a reach may look smaller than the change.
- Painting on every hover across the fanned hand may repaint the pane; the painter must touch only the cards whose state changes.
### Defaults
- Heat and reach are kept in the host's memory per craft, dev head and Board rev; nothing new is written to the state for them.
- The relation one and two steps out: System what uses a part; Screens the links both ways; the loop the step before and after; the tree a part's parent and children; Art and the way in none.
- *no test* uses map_signals' own rule (the gate's map, a test named after a file, a tests folder), made public, never copied.
- Reach is read for every goal not done whose spec has a *Will be*; Dev and main's for the goals in dev not yet in main.
### Accepted
- met: When dev's head and the Board are unchanged since the last read, then a map's heat is answered from what was kept with no git command run, and holds every hint of its craft, not cut at 20.
- met: When a goal's Tech section says `changed orkboard/realm`, then its reach on System is that part lit, the parts that use it one step out and theirs two out, each with no test mapped marked *no test*.
- met: When the pointer rests on, or the keyboard focuses, a hand card with System open at 1280 × 800 and no goal picked, then the page sends no command to the host: the reach shown is the one read at the last Board change.
- met: When the reach of a goal waiting for main is read for Dev and main, then goal_main.plan runs with pick=False once per Board change, no worktree is made, and the goals it takes along are its reach.
- met: When a goal's section has no *Will be*, names no part of the open map, or the map cannot be read, then its reach is empty and the host answers without an error.
