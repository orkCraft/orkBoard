---
owner: board
kind: idea
track: tech
order: 113
size:
priority: normal
short: The battle and the gate
phase: talk
route: product, design, tech
by: claude-code
schema: 3
---
# The battle and the gate: a new card against the decisions it goes against,…

## Gist
The battle and the gate: a new card against the decisions it goes against, the gate a battle nobody disputes, its checks' tokens on the decisions they guard (§299.6, §300.8)

The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decisions §300, §301): «битва (твоя карта снизу, а над ней 1+ карты прошлых решений), действие - соглашаешься или нет переписать прошлые решения»; «Гейт в теории тогда можно объединить с битвой, тоже карты тестов сверху». Split from goal 171 (the person: «да», on a goal for each mat), built on the Board's own data with its logic in the host, no mock data on the page (§301.1).

Goal 171's stage G removed four browser cases of `tests/test_cards_battle_browser.py` that only the mock's battles held (the battle card in the hand with its emblem, *vs §240* and *Settle it*; the spread with its axes and its cost to undo; a way sending `ideas.battle_settle`, Esc giving the focus back; the phone's stack): this goal brings them back on the host's answer.

Goal 171 left one line of Product's not accepted to this goal (its *Done when* line 5, H7's signal): Merge into main on the gate mat sends `ideas.to_main {idea, sealed: true}` with no `from` (`js/table/portal.js`), and `gui/ideas_mats.py` `played()` reads the goal only from `slug`, so its `move_played` keeps no goal and no from. Here `played()` reads the goal from `idea` as well, and the gate mat's seal sends `from: "mat"` (or `"hand"` when its hand card opened it), tested on the real `to_main` and `goal_to_dev`.

The first goal taken after 171 (the person, 12 November 2026, on the gate still drawn as a ring after 171's stage H: «давай вариант а»): until it lands, the page's gate goes against §300.8.

## Why

## Done when

## Out

## Risks

## Depends on
- 171-the-mats-as-laid: the mat's frame (its felt, plates, zones, seal and address) and the hand.

## Stages

## Open questions

## Decisions
