---
owner: board
kind: idea
track: product
order: 13
size:
priority: normal
short: A craft's heroes
phase: talk
route: product, design, tech
asks: person
by: claude-code
schema: 3
---
# A craft's heroes work on what is built

## Gist
Build decisions §278 and §279 (the owner, 8 November; first taken on 7 November on the branch claude/class-leaders-frameworks-nw3xxx, which never reached main): a craft keeps only the heroes whose framework stands on what Orkboard builds today (its craft's map and aspects, and data gathered by code, Play, the brief or the mana's record), no least number and six at most; the fifteen heroes named there (Product, Design, Tech, Run, Marketing, Release), the ones not taken and the later ones; the Orkmaster's star read from the project's kind and stage; a game's heroes at Game design (Dungeon Master Knight, Economy Knight, Pillar Knight) and Art (Sprite Dryad), LiveOps' chair empty until its map, a game's star; a hero with nothing to stand on in the project's kind is not offered there. Today §266.3 (three to six a craft) is what main builds. The new faces are drawn in orkUI before they are used (§266.4) and the heroes' names go in TERMS. Implementation on the simpler models.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- Does the star seat its hero? (**Marks the ware only** / Seats new parties / Seats every unchosen party) — Spike Shaman (the dearest) and Store Gnome lay frames, a model's pass each; a cost moved by itself is the person's (§57.3) · Marks the ware only: Nothing changes by itself; each craft's default stays until taken · Seats new parties: A new app's Tech starts on Spike Shaman, the dearest; old parties keep theirs · Seats every unchosen party: Projects on update switch heroes; each new frame laid in a pass
- When a party's hero is cut? (**Default seated, said once** / Default seated silently / Kept until another is taken) — the person took it and the hand marks it Yours (§266.1); a swap unseen breaks H1 · Default seated, said once: The stall's line names the cut hero and why; its table file stays as was · Default seated silently: As goal_team.hero_of does today; the hand shows another hero unasked · Kept until another is taken: The cut hero still works for who carries it; the shelf marks it retired
- How does Lantern Imp sit at Run? (**Run's default, no table** / Its own table, a pass) — Run has no map to lay, and no pass is spent by itself (§57.3); its rubric then says what Play gathers · Run's default, no table: Run's rubric becomes traces, errors and slow places; no model's pass · Its own table, a pass: Every Run party lays Lantern's four places in a model's pass on update

## Decisions

## Product
### Talk
- verdict: go — a game's Game design and Art chairs have no hero today, Pivot Knight's frame waits on analytics never read; what the new heroes stand on is built (loop, assets, brief)
- stance: Product keeps four heroes (Angel Invest, Jobwise, Appetite, Pillar) and lets Pivot Knight go: a ware that lays places nothing fills is a promise the stall should not sell
- for: it cuts before it adds: six heroes with no map or data go, and the indie game maker (§218.2) gets heroes on the Loop and Assets maps already built, in every game
- against: no person has yet been seen taking a hero in the stall; seven new schools widen a shelf whose worth is untested, and Product's tree still lives in .orkcraft/ only (goal 163)
- instead: first the cut and a game's two defaults (Dungeon Master Knight, Sprite Dryad, on the Loop and Assets maps); the five new schools once a hero taken is seen
- assumes: a hero's school changes its leader's say enough for a person to pick one — shown by: two heroes' Talk on one goal differ in verdict or questions, and a tester takes one

## Design
### Talk
- verdict: doubt — a cut hero a party carries falls back silently (goal_team.hero_of); go once the stall says so and the seven new faces are in orkUI first (§266.4)
- stance: Design keeps Pixel-Perfect and Sprint Dryad, gains Inclusive Dryad; a hero not for the kind lies locked with its why (§279.5: said, not hidden), never just missing
- for: the shelf loses wares whose places nothing fills (Diamond's research, Sprint's five people); a game's Art gets Sprite Dryad on the Assets map already drawn
- against: seven new faces, none in orkUI yet (heroes.head falls back to the race's head: three knights alike); Inclusive Dryad stands on one a11y hint the default reads
- instead: first the cut and Sprite Dryad with its face; Inclusive Dryad once §209.3–4's contrast and focus path are read on Play
- assumes: Inclusive Dryad says more than the default's Accessibility aspect on one a11y hint — shown by: both heroes' Talk on one screen goal differ in verdict or questions

## Tech
### Talk
- verdict: go — one catalog (realm/seat_hero_rules.py, 196 lines) and the stall's filter; no new caller of gui, no cycle; Run's default and the JS copy of the names must be mended with it
- stance: Tech builds it as data: kinds on each hero, Pillar Knight one hero at two crafts, Dungeon Master Knight and Sprite Dryad as their crafts' defaults (their hints are the rubric's)
- for: Game design and Art get heroes whose frame is their rubric already (no_reward to heavy), so they cost no pass; six frames nothing fills leave the catalog and the leaders' role files
- against: cutting Uptime Imp leaves Run no default: ideas_stall._default reads default(craft).id and breaks; partyseats2.js LEADERS keeps its own names; six test files pin the cut ids
- instead: land the whole catalog now, a non-default hero offered only when orkUI's copy has its face (heroes.head's file), so §266.4 holds by code, not by the order of commits
- assumes: project_kind reads a project's kind rightly enough to lock heroes by it — shown by: the testers' project.json seldom carry the person's `kind` correction
