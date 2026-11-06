---
owner: board
kind: idea
track: design
order: 3
size:
priority: normal
short: One card picked
phase: spec
spec: docs/specs/155-one-pick-and-the-release-column.md
decisions: 260
route: design, product, tech
by: person
schema: 3
---
# One card picked, on either side

## Gist
У нас сейчас очень сложный интерфейс стола (переключатели lifecycle цели - talk, spec, work, done, крест для перехода на чистый стол и ещё выделение карт из сброса показывает совершенно другой стол, кнопка назад). Карты слева и карты справа могут быть выделенными или нет (максимум выделена одна карта из двух колонок, выделенные карты нужно сделать более явно и выделить можно карту в любом статусе: идеи, спеки, карты в работе, в сбросе) и соответственно стол может быть либо всего проекта (если карта не выбрана) либо показывает выделенную карту (если этот лидер участвует в работе над ней, иначе подсвечен серым и не выбирается пока выбрана эта карта).

## Why
Three states of their own (the pick, what is over the pane, a lifted card) mixed freely, so neither ← nor × says where it goes; the edge asks *ready for main* and *the past* three times each (decision §260).

## Done when
- From any state of the table at the wide width, one Esc (or the picked card pressed again) shows the whole project: a browser test.
- The pane's title has no × and no phase button; ← only while a file or a diff is open: a browser test.
- No `.frame-edge` at 1280 × 800; Release's tab is the row's last and the discard its lane, through the open tab's eyes: a browser test.
- The die and the drum stand inside the hand's shown height and the Release column's width; *Stop all* is a button only while a run is on: a browser test.
- The narrow page and the phone keep their layout: the 390 px tests of the touched modules.

## Stages
- [ ] A. orkUI 0.31.0
- [ ] B. One pick
- [ ] C. The table by the phase
- [ ] D. The Release column, no edge
- [ ] E. The hand's right end
