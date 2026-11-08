---
owner: board
kind: idea
track: design
order: 7
size:
priority: normal
short: A board game's shape
phase: talk
route: design, tech
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

## Tech
### Talk
- verdict: doubt — go if heat and reach are read once per Board change in a realm module and served by a mixin of their own, not per hover through ideas.page nor added to gui/ideas.py (769 lines)
- stance: Tech builds heat and reach on System and Screens on their maps as built, from data code already reads; each other map's relation and shape is a stage of its own, looked at alone
- for: No model and little new data: map_signals already finds each part's hints, spec_sections.will_be reads Will be, System has its uses, Screens its links; goalmap.js lights a picked goal's parts
- against: map_signals.signals runs git per call and is cut at 20 for a prompt; goal_main.plan takes the git lock and may make a worktree: neither can run on a hover across the hand
- instead: heat and reach on System and Screens first, from one realm module per Board change; the rondel, tree, inventory and train after, a goal each
- assumes: the hints of every craft are read at dev's head in well under a second, so heat can follow each Board change — shown by: map_signals.signals timed for each craft on this repository
