---
owner: board
kind: idea
track: design
order: 6
size:
priority: normal
short: The table's look, the room's things
phase: work
route: design, tech
spec: docs/specs/160-the-tables-look-and-the-rooms-things.md
decisions: 268, 269, 271, 272, 273, 275
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
orkUI first (§269.9): A and B are done in orkUI (/home/user/orkui), released as a new orkUI version, then copied in C; nothing in design-system/orkui is edited by hand. Models as the person answered: the sheets, drawings and tokens (A, B, C, E, F, G, H, J, K, L) on simpler models; the discard's column move (D) and the chair's seating (I) on a stronger one. Release is a craft as any (§274.1, goal 158 C): the chair offers it when it is not seated; Tech's default *Release stays seated and locked* reads as that. No stage changes an orkboard/gui/*.py, core/ or realm/ module; every .js and .css a stage touches stays under 600 lines.
- [x] A. orkUI's colours: the parties, the felts, the light's steps, the plate
  - party: Design, in orkUI (simpler model). `office/tokens.json` and `tools/build_tokens.py`: a colour per party by race (§268.3: gold, moss `#8fbf4a`, plum, night blue, rust, sea, the Orkmaster's warm wood), each party's felt lit and out (§269.2, §271.2: out flat and darker), the five light steps per felt (§269.1), the flat plate under words (§275.2), bronze and gilt. A test in orkUI's tests/test_orkui.py: every text token 4.5:1 on its plate over each felt, lit and out; every signal ring 3:1 and brighter than every party and element colour (§268.2).
  - proves: Design's "When orkUI's tokens are read, then every text token measures at least 4.5:1 on its flat plate over each party's felt, lit and out…" (orkUI's half)
- [x] B. orkUI's drawings and parts, released
  - party: Design, in orkUI (simpler model). `.ork-table` (felt, five dithered steps by a 2 px checker, flat plates, bronze frame with rivets, out), a bronze plaque, a swallowtail pennant on a pole (tall when open), the lamp's chain with its bead at rest and pulled (in place of `door/`, §271.4), the backpack shut and open (§272.1, from the gui's rect art in js/table/backpack.js) and the open backpack's leather frame with two straps and buckles. No smooth gradient, no blurred shadow or glow (hard pixel rings only), a test says so. Preview, CHANGELOG, released as orkUI 0.35.0.
  - proves: Design's Checks "Felts, steps, bronze, plaques, pennants, the chain and the backpack are orkUI's tokens and drawings…", "No smooth gradient and no blurred shadow or glow…" (orkUI's half)
- [x] C. orkUI 0.35.0 copied, the contrast test here
  - party: Tech (simpler model). `python -m orkboard.design.orkui /home/user/orkui`; tests/test_design_system.py: the copy is 0.35.0 or later with the felts, steps, plate, bronze, pennant, chain and backpack; the token contrast test over each party's felt and step, lit and out, signal rings 3:1 and brightest; no `linear-gradient`/`radial-gradient`, no blurred `box-shadow`/`filter: blur`/`drop-shadow` in the desktop's or the phone's sheets.
  - proves: Design's "When orkUI's tokens are read, then every text token measures at least 4.5:1…"; Tech's Check "design-system/orkui is orkUI's stamped copy with its new version in test_design_system.py…"
- [x] D. The discard beside the table
  - party: Tech (the stronger model). js/table/lane.js `ReleaseLane` becomes the window's right column outside the table, at its old width (`--col-w`), on every tab, its head a row for the room's things over the label *Discard* (§273.1–3); js/table/tabs.js: Release's tab joins the leaders' row in route order (§273.2), the backpack and the door leave the row's end (their places taken in G and H). Under 760 px discard.js `DiscardEnd` works as today. tests/test_discard_table_browser.py and test_table_edge_browser.py rewritten to the new places, not deleted.
  - proves: Tech's "When the page opens at 1280 × 800 on the Orkmaster's tab and on Tech's with the person Here, then the discard is the window's right column outside the table at its old width, Release's tab in the leaders' row in route order."
- [ ] E. The table's look on the desktop
  - party: Design (simpler model). js/table/table.css, lane.css, column.css, discard.css, tabs.js: the open party's felt under its table (the Orkmaster's the wood), the light from the top edge in five steps with words on flat plates, bronze frames round the table, the column, the discard and the hand, headings on plaques in the pixel face, a pennant over each leader (the open one tallest, clear of the top edge), a tab's name in the light ink and its party's colour only in the rule, pennant and glow (§275.1); a lane's light in three steps, an empty lane says whose it is (*Release is free · throw a goal here or @Release*). Lamp out (`presence.here` false): the felt flat and darker, the lanes unlit but for their rules. orkUI's tokens only.
  - proves: Design's "When the page opens at 1280 × 800 on Tech's tab with the lamp lit, then the felt is moss…" (built here, judged in L); Design's Check "A party's or element's colour is never a ring round a card…; a tab's name is in the light ink…"
- [ ] F. The cards' faces and the hand's fan
  - party: Design (simpler model). js/hand/*.css and js/table/card.js' sheet: a card's thick frame in its element's colour with a gilt inner line, the element in steps down its face, the bevelled window, the goal's strip a ribbon, a signal's ring one ring and a faint second (§269.6); the hand fans ±2° at the desktop's width and a card rises on hover, neither under reduced motion (§269.7).
  - proves: Design's Checks "No smooth gradient and no blurred shadow or glow…", "Under reduced motion the chain's pull, the hand's fan and a card's rise are at once…" (the fan and the rise)
- [ ] G. The lamp's chain
  - party: Tech (simpler model). js/table/presence.js: the door becomes orkUI's chain at the right of the discard column's head, on the same `presence.set {here: !here}`, its words *Here · until …* / *Away · until …* / *· held*; the chain moves once on a pull, at once under reduced motion; under 760 px no words, `aria-label` and `title` keep them (§271.5). door.js and `.ork-door` go. tests/test_presence_door_browser.py rewritten to the chain.
  - proves: Tech's "When the person pulls the lamp's chain at 1280 × 800 with the person Here, then one `presence.set {here: false}` is sent, and after the snapshot the chain reads *Away · until …*, the cards and signal rings unchanged."; Design's "When the page opens at 1280 × 800 with the person Here, then the right column beside the table holds the backpack and the lamp's chain over *Discard* on every tab, the chain's words *Here · until …*, Release's tab in the leaders' row." (the chain's half)
- [ ] H. The backpack at the column's head
  - party: Tech (simpler model). js/table/backpack.js draws orkUI's backpack shut and open in place of its own rects, at the left of the discard column's head; open, the table lies in its leather (stitched frame, two straps, no rivets), shut the bronze is back (§272.1); under 760 px its word in `aria-label` and `title` only. tests/test_stall_browser.py rewritten to its new place.
  - proves: Design's "When the page opens at 1280 × 800 with the person Here, then the right column beside the table holds the backpack and the lamp's chain over *Discard* on every tab…" (whole with G)
- [ ] I. The chair deals its crafts
  - party: Tech (the stronger model). js/table/chairs.js: the chair stays at the tabs' end; pressed, it is lit, the Orkmaster's question rises (*A new chair at the table · Which craft sits in it?*) and the hand holds a 144 × 202 card for each craft not yet seated (`ideas.party_presets` of group `stage`, not made; Release among them when not seated), its race's head, its whole line, its price a week (`ideas.party_price`) in the corner, the Orkmaster's pick starred and named in words; the rest of the hand sinks. A craft's card pressed seats it by `ideas.goal_save` as the parties' place does, its tab where the chair stood, the backpack opening on its chair; *Put it back* sends nothing. A card component shared with hand/answercards.js, not bending it; the parties' place stays for a party's *Edit*. A browser test.
  - proves: Design's "When the person presses the new chair at 1280 × 800, then the hand holds a card for each craft not yet seated…"; Tech's "When the person presses the new chair, then a craft's card, at 1280 × 800, then the craft is seated by `ideas.goal_save` and the backpack opens on its chair; *Put it back* sends no command and seats nothing."
- [ ] J. The project in the Orkmaster's header
  - party: Tech (simpler model). js/table/column.js and header.js: its first line the project's name (the switch beside it), its second the kind and stage in the caption face (*Game · Being made*); *The Orkmaster* only in `aria-label` and `title` (§272.5). The kind or the stage pressed deals its choices to the hand, each with its line (*Live: LiveOps and Run join the chair's crafts*), the present one marked; a card sends `ideas.project_kind_set` or `ideas.stage_set` once, *Put it back* nothing. A browser test.
  - proves: Tech's "When the person presses the kind or the stage in the Orkmaster's header at 1280 × 800, then the hand deals its choices, the present one marked…"; Design's Check "The Orkmaster's header says the project's name, then its kind and stage…"
- [ ] K. The phone's table, lamp and backpack
  - party: Tech (simpler model). The phone's `/app/` (pwa/app.css, frame.css and hand/uptop.js): its table wears the open party's felt and light from orkUI's tokens, as the desktop's; the lamp's chain stands in its top row where the door stood, a press sends `presence.set`; the backpack beside it; no words, `aria-label` and `title` hold them. No chair's deal and no header cards on the phone (§275.3). A browser test at 390 × 844.
  - proves: Tech's "When the phone opens `/app/` at 390 × 844 with the person Here, then the lamp's chain stands in its top row where the door stood…"; Design's "When the phone opens `/app/` at 390 × 844 with the person Here, then its table wears the open party's felt and light…" (built here, judged in L)
- [ ] L. The pictures
  - party: Design (simpler model). docs/mockups/table-look/shoot.py and room-things/shoot.py pointed at the product: 1280 × 800 on Tech's tab lamp lit and out, the chair's deal, the header's deal; the phone at 390 × 844 Here. The person judges them.
  - proves: Design's "When the page opens at 1280 × 800 on Tech's tab with the lamp lit, then the felt is moss…", "When the phone opens `/app/` at 390 × 844 with the person Here…" ([look] lines: the person judges the pictures)

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
### Why
- The window is flat: colour by party and a lit, framed table tell whose table at a glance (recognition over recall) while a signal stays the brightest thing.
- A lamp, a backpack and a chair as things put Here/Away, heroes and seating where they are seen, with every word still readable at AA on every felt, lit or out (§275).
### Done when
- [test] When orkUI's tokens are read, then every text token measures at least 4.5:1 on its flat plate over each party's felt, lit and out, and every signal ring 3:1 and brighter than any party or element colour.
- [test] When the page opens at 1280 × 800 with the person Here, then the right column beside the table holds the backpack and the lamp's chain over *Discard* on every tab, the chain's words *Here · until …*, Release's tab in the leaders' row.
- [test] When the person presses the new chair at 1280 × 800, then the hand holds a card for each craft not yet seated, with its race's head, its line and its price a week, the Orkmaster's pick starred and named in words.
- [look] When the page opens at 1280 × 800 on Tech's tab with the lamp lit, then the felt is moss, the light falls in five dithered steps with words on flat plates, bronze frames round it and the open leader's pennant tallest; out, the felt is flat and darker.
- [look] When the phone opens `/app/` at 390 × 844 with the person Here, then its table wears the open party's felt and light, and the lamp's chain and the backpack stand at its head without words.
### Checks
- Felts, steps, bronze, plaques, pennants, the chain and the backpack are orkUI's tokens and drawings, copied; Orkboard's sheets carry no colour of their own (tests/test_design_system.py).
- No smooth gradient and no blurred shadow or glow in the desktop's or the phone's sheets (§269.1): hard pixel rings only.
- A party's or element's colour is never a ring round a card (§268.2); a tab's name is in the light ink, its party's colour only in the rule, pennant and glow (§275.1).
- Under reduced motion the chain's pull, the hand's fan and a card's rise are at once; under 760 px the chain and backpack keep their words in aria-label and title.
- The Orkmaster's header says the project's name, then its kind and stage in the caption face; *The Orkmaster* only in its aria-label and title (§272.5).
### Will be
- changed home — the table gets party felts, stepped light, bronze, pennants; the discard becomes the window's right column, the lamp's chain and backpack at its head, the chair deals crafts
### Out
- The new goal card at the Orkmaster's lane top and its four corners (§270.6).
- To main from the discard and its gate (§274): Tech's engine, not this look.
- On the phone, the chair's deal and the header's kind and stage cards: the phone gets the look, the lamp and the backpack (§275.3).
### Risks
- high
- Dark felts (plum, oxblood, night blue) may leave little room for signal hues that are both 3:1 and brighter than every party colour.
- Flat plates under words may cut the light into patches, so the steps no longer read as one light from the top edge.
- The 188 px column head may not hold the backpack, the chain and its words at 1280 px, so the words wrap or are cut.
- The phone's sheets, drawn a second time, may drift from the desktop's felts and steps.
### Defaults
- The window is my map's screen `home` (`/`); the phone's `/app/` takes the same look; no new screen is made.
- The contrast test measures orkUI's token pairs over each felt and step, lamp lit and out, not the pixels of a picture.
- The [look] lines' pictures come from the cameras of docs/mockups/table-look/ and docs/mockups/room-things/ (shoot.py) pointed at the product.
- The chair's craft cards follow §270's hand cards: 144 × 202, the line whole at rest, the price in the corner.
### Accepted
- met: When orkUI's tokens are read, then every text token measures at least 4.5:1 on its flat plate over each party's felt, lit and out, and every signal ring 3:1 and brighter than any party or element colour.
- cannot see: When the page opens at 1280 × 800 with the person Here, then the right column beside the table holds the backpack and the lamp's chain over *Discard* on every tab, the chain's words *Here · until …*, Release's tab in the leaders' row.
- cannot see: When the person presses the new chair at 1280 × 800, then the hand holds a card for each craft not yet seated, with its race's head, its line and its price a week, the Orkmaster's pick starred and named in words.
- cannot see: When the page opens at 1280 × 800 on Tech's tab with the lamp lit, then the felt is moss, the light falls in five dithered steps with words on flat plates, bronze frames round it and the open leader's pennant tallest; out, the felt is flat and darker.
- cannot see: When the phone opens `/app/` at 390 × 844 with the person Here, then its table wears the open party's felt and light, and the lamp's chain and the backpack stand at its head without words.

## Tech
### Talk
- verdict: doubt — go only in ordered stages: orkUI's copy with a token contrast test first, then gui/ sheets, then the column move; no new host command (gui/ideas.py is 769 lines)
- stance: a face change: presence.set, track_add, party_save, stage_set and project_kind_set already serve the lamp, chair and header; the risk is the frame and five decisions at once
- for: mostly sheets and drawings in already split files (presence.js 48, backpack.js 21, chairs.js 35, discard.js 154 lines); no engine, realm or core change; orkUI's tokens make it testable
- against: the page's spec file docs/specs/160-… does not exist; moving the discard out of Release's column shifts layout browser tests pin; the backpack drawn in gui/ must move to orkUI
- instead: three steps landed one by one: orkUI tokens and contrast test; felt, light, lamp (§268, §269, §271); then backpack, chair, header and the discard column (§272, §273)
- assumes: no host command is needed for the chair's crafts and prices (party_presets plus party_price per craft) — shown by: the stages' diffs touching no orkboard/gui/*.py
### Why
- The frame moves: the discard leaves Release's lane for a column of its own, and the door, the backpack and the chair change their acts; a slip there breaks every tab.
- Done as a face change on host commands that already exist, it stays in gui/static with no new caller of the engine, and orkUI's tokens make the look testable.
### Done when
- [test] When the page opens at 1280 × 800 on the Orkmaster's tab and on Tech's with the person Here, then the discard is the window's right column outside the table at its old width, Release's tab in the leaders' row in route order.
- [test] When the person pulls the lamp's chain at 1280 × 800 with the person Here, then one `presence.set {here: false}` is sent, and after the snapshot the chain reads *Away · until …*, the cards and signal rings unchanged.
- [test] When the person presses the new chair, then a craft's card, at 1280 × 800, then the craft is seated by `ideas.goal_save` and the backpack opens on its chair; *Put it back* sends no command and seats nothing.
- [test] When the person presses the kind or the stage in the Orkmaster's header at 1280 × 800, then the hand deals its choices, the present one marked; a card sends `ideas.project_kind_set` or `ideas.stage_set` once.
- [test] When the phone opens `/app/` at 390 × 844 with the person Here, then the lamp's chain stands in its top row where the door stood, a press sends `presence.set`, its words in `aria-label` and `title` only.
### Checks
- The stages' diffs change no orkboard/gui/*.py, core/ or realm/ module: presence.set, party_presets, party_price, goal_save, stage_set and project_kind_set serve as they are.
- Every .js and .css the step touches stays under 600 lines; the door's code (door.js, `.ork-door` in presence.js) goes, not kept beside the chain.
- The browser tests that pin the old places (test_presence_door_browser, test_discard_table_browser, test_stall_browser, test_table_edge_browser) are rewritten to the new ones, not deleted.
- design-system/orkui is orkUI's stamped copy with its new version in test_design_system.py; nothing in it edited by hand.
- Under 760 px the narrow pile at the lanes' end (discard.js `DiscardEnd`) works as today; under reduced motion the chain's pull is at once.
### Will be
- changed orkboard/gui/static/js/table/lane.js — the discard is no longer Release's lane: a column of its own, the room's things at its head
- changed orkboard/gui/static/js/table/tabs.js — Release's tab joins the leaders' row; the backpack and the door leave the row's end
- changed orkboard/gui/static/js/table/presence.js — the door becomes the lamp's chain on the same `presence.set`
- changed orkboard/gui/static/js/table/chairs.js — the chair deals the crafts to the hand instead of opening the parties' place
- changed orkboard/gui/static/js/table/column.js — the Orkmaster's header says the project's name, kind and stage
- changed design-system/orkui — orkUI's copy with the felts, light steps, bronze, pennant, chain and backpack
### Out
- To main from the discard and Release as a craft a project may leave (§274): a goal of its own, on the engine.
- orkUI's tokens and drawings themselves: made in orkUI, only copied here.
- The new goal card at the Orkmaster's lane top and its four corners (§270.6).
### Risks
- medium
- Browser tests pin Release's column and the door's place; in alpha they are not waited for, so a broken frame can reach main before the full CI turns red.
- orkUI's release with the felts, chain and backpack lands late; gui/ then waits, or draws stand-ins test_design_system forbids.
- The chair's deal as a second caller of hand/answercards.js may bend it toward craft cards it was not made for.
- The spec file named in `spec` (docs/specs/160-…) does not exist yet; stages may cite sections that are nowhere.
### Defaults
- The phone's `/app/` draws its table with the page's own components (hand/uptop.js, table/), so its chain and backpack are the desktop's, small.
- The chair seats a craft as the parties' place does today (`ideas.goal_save` with the preset); the parties' place stays for a party's *Edit*.
- The chair's crafts are `ideas.party_presets` of group `stage`, not locked and not yet made, each priced by `ideas.party_price`.
- Release stays seated and locked as today; only its tab moves into the leaders' row (§274 is out).
### Accepted
- met: When the page opens at 1280 × 800 on the Orkmaster's tab and on Tech's with the person Here, then the discard is the window's right column outside the table at its old width, Release's tab in the leaders' row in route order.
- cannot see: When the person pulls the lamp's chain at 1280 × 800 with the person Here, then one `presence.set {here: false}` is sent, and after the snapshot the chain reads *Away · until …*, the cards and signal rings unchanged.
- cannot see: When the person presses the new chair, then a craft's card, at 1280 × 800, then the craft is seated by `ideas.goal_save` and the backpack opens on its chair; *Put it back* sends no command and seats nothing.
- cannot see: When the person presses the kind or the stage in the Orkmaster's header at 1280 × 800, then the hand deals its choices, the present one marked; a card sends `ideas.project_kind_set` or `ideas.stage_set` once.
- cannot see: When the phone opens `/app/` at 390 × 844 with the person Here, then the lamp's chain stands in its top row where the door stood, a press sends `presence.set`, its words in `aria-label` and `title` only.

## Decisions
§268, §269, §271, §272, §273, §275. Mockups: docs/mockups/table-look/, docs/mockups/room-things/.
