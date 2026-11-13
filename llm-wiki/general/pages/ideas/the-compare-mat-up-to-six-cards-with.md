---
owner: board
kind: idea
track: design
order: 20
size:
priority: normal
short: The compare mat
phase: talk
route: product, design, tech
by: claude-code
schema: 3
---
# The compare mat: up to six cards with their price, and above them what the…

## Gist
The compare mat: up to six cards with their price, and above them what the card in focus would make, laid small in its own layout (§300.1, §300.7, §301.4)

The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decisions §300, §301): «сравнение (до 6 карт сеткой, на мобиле 2*3, на десктопе наоборот, с контентом если это ресурсы и со стоимостью), действие - выбор одной»; «планшет сравнения сможет сверху показать результат выбора при выделении карты: например если это разная архитектура или дизайн». Split from goal 171 (the person: «да», on a goal for each mat), built on the Board's own data with its logic in the host, no mock data on the page (§301.1).

Goal 171's stage G changed `tests/test_cards_spreads2_browser.py`'s cost case: the muted card a tool cannot pay and its two ways (*play it on <another tool>*, *Wait for 04:00* with `ideas.route_later`) are held by no case now: this goal brings them back with the costs it lays.

## Why

## Done when

## Out

## Risks

## Depends on
- 171-the-mats-as-laid: the mat's frame (its felt, plates, zones, seal and address) and the hand.

## Stages

## Open questions

## Decisions
