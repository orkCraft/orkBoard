---
owner: board
kind: idea
track: design
order: 3
size:
priority: normal
short: One card picked
phase: work
spec: docs/specs/156-one-pick-and-the-release-column.md
decisions: 261, 262, 263, 264, 265
route: design, product, tech
by: person
schema: 3
gate: 4827c2c · 172 files · green
asks: person
---
# One card picked, on either side

## Gist
У нас сейчас очень сложный интерфейс стола (переключатели lifecycle цели - talk, spec, work, done, крест для перехода на чистый стол и ещё выделение карт из сброса показывает совершенно другой стол, кнопка назад). Карты слева и карты справа могут быть выделенными или нет (максимум выделена одна карта из двух колонок, выделенные карты нужно сделать более явно и выделить можно карту в любом статусе: идеи, спеки, карты в работе, в сбросе) и соответственно стол может быть либо всего проекта (если карта не выбрана) либо показывает выделенную карту (если этот лидер участвует в работе над ней, иначе подсвечен серым и не выбирается пока выбрана эта карта).

## Why
Three states of their own (the pick, what is over the pane, a lifted card) mixed freely, so neither ← nor × says where it goes; the edge asks *ready for main* and *the past* three times each (decision §261).

## Done when
- From any state of the table at the wide width, one Esc (or the picked card pressed again) shows the whole project: a browser test.
- The pane's title has no × and no phase button; ← only while a file or a diff is open: a browser test.
- No `.frame-edge` at 1280 × 800; Release's tab is the row's last and the discard its lane, through the open tab's eyes: a browser test.
- The die and the drum stand inside the hand's shown height and the Release column's width; *Stop all* is a button only while a run is on: a browser test.
- The narrow page and the phone keep their layout: the 390 px tests of the touched modules.

## Stages
- [x] A. orkUI 0.31.0
- [x] B. One pick
- [x] C. The table by the phase
- [x] D. The Release column, no edge
- [x] E. The hand's right end

## Design
### Talk
- verdict: go
- stance: Design backs it: one pick, put away by Esc, the card again or the browser's back; no ×, no phase buttons. The drum's dim neighbours are the one part that hides a signal
- for: one state where three mixed, so each way back says where it goes; Stop all in words, not on a 3D face (Nielsen 1, 3, 4; WCAG 2.5.3)
- against: the drum says one share in words; a tool at warn or danger beside it is a dimmed, half-hidden colour with no word (WCAG 1.4.1, 1.4.11)
- assumes: the active tool's share is the one a person needs at a glance — shown by: a week of the owner's use, how often the drum is unrolled to read another tool
### Accepted
- not met: From any state of the table at the wide width, one Esc (or the picked card pressed again) shows the whole project: a browser test. — a picked card's choices (table/column.js Acts) take the first Esc; test_one_pick_browser.py l.81–83 presses it twice
- not met: The pane's title has no × and no phase button; ← only while a file or a diff is open: a browser test. — no × and spans only, but ← stands over every kind (table/pane.js Title l.93 `o &&`): Settings, Files, Play; no test opens one
- met: No `.frame-edge` at 1280 × 800; Release's tab is the row's last and the discard its lane, through the open tab's eyes: a browser test.
- met: The die and the drum stand inside the hand's shown height and the Release column's width; *Stop all* is a button only while a run is on: a browser test.
- cannot see: The narrow page and the phone keep their layout: the 390 px tests of the touched modules.

## Product
### Talk
- verdict: doubt — D and E undo §254's edge, built a day ago, on an audit nobody has used; I'd do them only after B and C, the Gist's own ask, have been used a week
- stance: Product backs the pick and the table by the phase: they are the owner's job (one goal or the whole project, at a glance); the Release column and the drum are a second bet
- for: three mixed states become one, so each way back says where it goes; it reaches every session of every user, and the owner's own words ask for it (§261's Why)
- against: five parts and ~40 files on one person's word, no mockup; the frame changes a second time in two days (§254, §261); spec 150 B's orkUI 0.30.0 is still open
- instead: B and C now (one pick, the table by the phase); the Release column, no edge and the drum a goal of their own after a week's use
- assumes: one pick with grey tabs reads at once, with no × and no ← — shown by: a week of the owner's use with no pick lost or misread, written in the project's journal

## Tech
### Talk
- verdict: doubt — B adds a fourth history writer (beside table.js, upmenu.js, pwa/board.js); I'd build it only if frame/state.js alone writes the pick's address and Esc, table.js in B
- stance: Tech can build it: it takes code away (edge.js, pyramid.js, three views over the pane) and keeps the pick in one seam, frame/state.js; the risk is B's history and wave 2's shared file
- for: the frame gets smaller: edge.js, edge.css, pyramid.js and the discard, talk, spec, quality overs go; `picked` stays one signal; every module touched is under 300 lines
- against: B's files miss table/table.js, whose Esc and pick-opens-its-party's-tab (l.72) go against B.1 and B.5; C and D both change table/pane.js, so wave 2 shares a file
- instead: B with frame/state.js the address's one writer and table.js in its files; then C, then D, one after the other; E after A's orkUI copy
- assumes: the pick's history entry and the narrow back entry (table.js useBackButton) keep their order — shown by: a 390 px test: a pick, a file over it, back twice closes the file, then the pick
### Accepted
- not met: From any state of the table at the wide width, one Esc (or the picked card pressed again) shows the whole project: a browser test. — table/column.js l.135 takes the first Esc for a picked card's choices (test_one_pick_browser.py l.81–83, l.162–163 press it twice); shell/shell.js l.55 is a second pick Esc, against B.1's one handler
- not met: The pane's title has no × and no phase button; ← only while a file or a diff is open: a browser test. — no × and Phases are spans, but table/pane.js Title l.93 draws ← for every `over` (`o &&`; its `code` is unused); no test opens Settings or Files to see no ←
- met: No `.frame-edge` at 1280 × 800; Release's tab is the row's last and the discard its lane, through the open tab's eyes: a browser test.
- met: The die and the drum stand inside the hand's shown height and the Release column's width; *Stop all* is a button only while a run is on: a browser test.
- cannot see: The narrow page and the phone keep their layout: the 390 px tests of the touched modules.

## Open questions
- How is a tool in danger shown? (**at full brightness, its share in words** / dimmed, its colour only, as §261.13) — a tool running out is money: said plainly, not by colour alone (WCAG 1.4.1)
  - Answered: at full brightness, its share in words (the person, 2026-11-06)
- Split the Release column off this goal? (**B and C now, D and E after a week's use** / all five parts in spec 156's waves) — D and E undo §254's edge built a day ago; the pick alone may make the table plain
  - Answered: all five parts in spec 156's waves (the person, 2026-11-06)
- How is the simpler table shown? (**the owner's week, a line in the project's journal** / one Orkline tester watched in the testers' week / not measured) — the frame changed twice in two days; a third needs a signal
  - Answered: the owner's week, a line in the project's journal; no testers (the person, 2026-11-06)
- Build C and D one after another? (**C, then D** / C and D side by side, as spec 156's wave 2) — both must change table/pane.js: C its Phases, D the `discard` view it draws (l.114); a wave's parts share no file
  - Answered: C, then D (decided by spec 156, 2026-11-06)
- What closes Settings, Projects, a log or a role over the pane at the wide width? (**← stays for every screen over the pane, §261's line changed** / ← only for a file or a diff as §261 says, each other screen gets its own close / ← only for a file or a diff, Esc alone closes the rest) — Design and Tech did not accept Done when 2: most screens over the pane have no close of their own, so taking ← away leaves Esc alone (Nielsen 3)
- Product wrote no section of its own for this goal: accept it without one? (**yes: Product's Talk stands, its part goes under Not accepted** / Product writes its section now and accepts against it) — Product's accept found no Done when of its own to judge
