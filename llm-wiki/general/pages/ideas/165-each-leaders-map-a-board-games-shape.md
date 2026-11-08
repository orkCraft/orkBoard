---
owner: board
kind: idea
track: design
order: 7
size:
priority: normal
short: A board game's shape
phase: spec
route: design, tech
spec: docs/specs/165-each-leaders-map-a-board-games-shape.md
by: claude-code
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
