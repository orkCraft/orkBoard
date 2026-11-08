# 165. Each leader's map takes a board game's shape: heat and reach first on the maps as they are, then each map's shape a stage of its own

Goal: `llm-wiki/general/pages/ideas/165-each-leaders-map-a-board-games-shape.md` (route: design, tech). The person's request is the page's *Gist*. This spec is the leaders' sections of that page as they wrote them in the Board's flow (Talk, then their sections), with the person's answers above them (decisions §280, §281); each leader's *Talk* and *Accepted* stay in the page. **Builds:** the goal's stages (the page's *Stages*, the Taskmaster's), each task by a Grunt on the simpler model, in the branch `claude/stoic-newton-c85q7q`, into a pull request.

## The person's answers (8 November 2026)

1. Heat and reach before the shapes? — **Heat and reach first, shapes after**.
2. Reach on the phone in this goal? — **Desktop now, the phone after**.
3. Dev and main's reach on hover? — **The plan kept, without its trial**.

## Design

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
