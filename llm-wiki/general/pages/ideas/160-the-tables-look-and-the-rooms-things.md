---
owner: board
kind: idea
track: design
order: 6
size:
priority: normal
short: The table's look, the room's things
phase: talk
route: design, tech
spec: docs/specs/160-the-tables-look-and-the-rooms-things.md
decisions: 268, 269, 271, 272, 273
by: claude-code
schema: 3
---
# The table's look and the room's things: colour by party, felt and light, the lamp, the backpack and the chair, the discard beside the table

## Gist
The person, 8 November 2026: давай сделаем все решения по столу, желательно имплементация на моделях попроще.

The table's look and the room's things, after goal 158 (the person's split of 8 November): colour is the party, the element and a signal; each leader's felt, the light from the top edge in steps, bronze frames, pennants; the lamp's chain for Here and Away; the backpack and the new chair dealing its crafts; the discard beside the table; the project's name, kind and stage in the Orkmaster's header. orkUI first. (decisions §268, §269, §271, §272, §273)

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- Party name below 4.5:1 contrast? (**light text, the party's colour in the rule under it** / the party's hue lightened to 4.5:1) — the mockup's muted closed tabs and *Release is free* blue fall under AA on dark felt (WCAG 1.4.3) · light text, the party's colour in the rule under it: Names always readable; the party is told by its rule, pennant and felt · the party's hue lightened to 4.5:1: The name keeps its hue; light hues drift toward the signals' brightness
  - Answered: light text, the party's colour in the rule under it and in its pennant (the person, 2026-11-08)
- Dithered light steps under text? (**no: words sit on a flat plate, steps between** / yes: the steps run under all, as the mockup) — a 2 px checker under 13 px text has no single contrast to test (WCAG 1.4.3, 1.4.11) · no: words sit on a flat plate, steps between: Every word's contrast is one number a test can check on each felt · yes: the steps run under all, as the mockup: The light is unbroken; small words over the checker shimmer and blur
  - Answered: no: words sit on a flat plate, the steps between them (the person, 2026-11-08)
- The phone in this goal? (**desktop only; the phone in a goal of its own** / desktop and phone together) — §270.7 already sends the phone to its own goal; pwa/ has its own shell and sheets · desktop only; the phone in a goal of its own: The page's look lands; the phone keeps today's office look a while · desktop and phone together: One look everywhere at once; twice the sheets and browser tests
  - Answered: desktop and phone, in this goal (the person, 2026-11-08)
- Which steps go to simpler models? (**sheets and drawings; column move and chair stronger** / every step on simpler models) — moving the discard column and seating a craft touch the frame's layout and money; a slip there is costly · sheets and drawings; column move and chair stronger: Felt, light, lamp sheets cheap; layout and seating get a stronger pass · every step on simpler models: Cheapest; more steps likely sent back at Accept
  - Answered: the sheets, drawings and tokens on simpler models; the discard's column move and the chair's seating on a stronger one (the person, 2026-11-08)

## Design
### Talk
- verdict: doubt — go if orkUI's tokens land first (§269.9) and a contrast test over every felt, step and element, lamp lit and out, gates gui/; the mockup fails AA in places
- stance: Design wants the three colour layers and the room's things; felt, light, bronze, lamp, backpack and chair are orkUI's drawings and tokens first, then gui/, each step tested for contrast
- for: party colour tells whose table at a glance (recognition); the chain keeps Here and Away in words; the chair deals crafts with their price before a press (§272.4, error prevention)
- against: muted tab names, blue hints and dithered steps under small text fail 4.5:1 in the mockup; the chair's craft cards cut their line; four decisions at once on simpler models
- instead: orkUI's tokens and parts with a contrast test first (§268, §269); then the table's look in gui/; then the lamp, backpack, chair and discard column (§271–§273)
- assumes: text keeps 4.5:1 and rings 3:1 on every felt, step and element face, lit and out — shown by: a test measuring each token pair over each felt and step, lamp lit and out

## Tech
### Talk
- verdict: doubt — go only in ordered stages: orkUI's copy with a token contrast test first, then gui/ sheets, then the column move; no new host command (gui/ideas.py is 769 lines)
- stance: a face change: presence.set, track_add, party_save, stage_set and project_kind_set already serve the lamp, chair and header; the risk is the frame and five decisions at once
- for: mostly sheets and drawings in already split files (presence.js 48, backpack.js 21, chairs.js 35, discard.js 154 lines); no engine, realm or core change; orkUI's tokens make it testable
- against: the page's spec file docs/specs/160-… does not exist; moving the discard out of Release's column shifts layout browser tests pin; the backpack drawn in gui/ must move to orkUI
- instead: three steps landed one by one: orkUI tokens and contrast test; felt, light, lamp (§268, §269, §271); then backpack, chair, header and the discard column (§272, §273)
- assumes: no host command is needed for the chair's crafts and prices (party_presets plus party_price per craft) — shown by: the stages' diffs touching no orkboard/gui/*.py

## Decisions
§268, §269, §271, §272, §273. Mockups: docs/mockups/table-look/, docs/mockups/room-things/.
