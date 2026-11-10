---
owner: board
kind: idea
track: design
order: 16
size:
priority: normal
short: The readable look and the phone's feed
phase: talk
route: design, tech
asks: person
by: claude-code
schema: 3
---
# The readable look and the phone's feed: Rubik, lifted colours, round corners; the phone's tables as a feed of blocks

## Gist
The person, 10 November 2026: «Как ты думаешь как дизайнер, учитывая что мы начинаем отходить от пиксельной графики, можем ли мы в
угоду читаемости и отображению на мобилах поменять шрифты, цвета и может быть форму/закругления карточек?» — «Мне больше всего
нравится Rubik». — «Ещё одно предложение для телефона, разбить текущие столы на зоны в виде блоков и сделать скролл этих блоков как
в соц сетях». — «Я согласен с твоими предложениями по картам. 1) в начале что ждет 2) сужает 3) давай в одну строку». — «В общем мне нравится, давай тогда по
твоим рекомендациям переделываем дизайн мобилы и десктопа (только имплементация на более простых моделях)».

## Why

## Done when

## Out

## Risks

## Depends on
Decision §291 (what was decided); the mockups `docs/mockups/readable-look/` and `docs/mockups/phone/feed.html` (v2). The look is
made in orkUI first, then copied here.

## Stages

## Open questions
- Where is orkUI's change made? (**A pull request to orkUI, then copied** / The person makes it in orkUI) — CLAUDE.md: the look is made in orkUI, never here; the copy waits for it · A pull request to orkUI, then copied: This goal opens orkUI's pull request; the copy waits for its merge · The person makes it in orkUI: This goal waits until a new orkUI is out to copy
- Seen since when, on the phone? (**Since this phone's last look** / Since the last look anywhere) — the desktop's past dot is already per browser (spec 150 E2.3); one rule for both · Since this phone's last look: Kept on the phone; news read on the desktop shows again · Since the last look anywhere: The host keeps it; read once, seen on every screen
- Phone's tabs: gone at once, or kept? (**Gone in the feed's step** / Kept behind a setting a week) — alpha merges fast; two phone layouts double shell-project.js and its browser tests · Gone in the feed's step: One face; the tabs' browser tests are rewritten for the feed · Kept behind a setting a week: A way back while testers try it; two layouts kept and tested
  - Answered: Gone in the feed's step (decided by §291.5, 2026-11-10)
- Which stages go to simpler models? (**Look's copy and sizes; feed's reader stronger** / Every stage on simpler models) — sizes to tokens is wide but plain; the feed's order and narrowing is new logic · Look's copy and sizes; feed's reader stronger: The cheap, wide work goes cheap; the new reader gets a careful pass · Every stage on simpler models: Cheapest; the feed's order and its tests are more likely sent back

## Decisions
- §291: Rubik, the colours a step lifted, round corners; the phone a feed of blocks, what waits first, a head narrows it, the seen
  in one line that spreads as a deck.

## Design
### Talk
- verdict: doubt — two reworks in one goal on simpler models: I go only if the look (orkUI, then its copy) is its own stage, accepted on pictures, before the phone's feed starts
- stance: Design keeps the look; Rubik, the lifted colours and round corners fix real reading faults, and the feed must keep the hand at the foot and a plain way back
- for: Fixes measured faults: Cyrillic misread in the pixel face, 37 sizes of 9–11 px in the sheets, card frames at 1.25:1; the feed puts what waits first (§291.6)
- against: The feed replaces §223's tabs; a sideways swipe with no button fails WCAG 2.5.1, a folding header can hide focus (2.4.11), a narrowed feed must say it is narrowed
- instead: The look first, on desktop and phone, accepted on pictures; then the feed as a second step on the new look, each of its states pictured
- assumes: Rubik and the lifted colours read better on a phone in daylight — shown by: §226.5's check, the new look opened outdoors at the phone's own brightness

## Tech
### Talk
- verdict: doubt — go only if the feed's rules are a sheet of their own (pwa/app.css is 1457 lines) and its order comes from one host reader over board_recap, not a join in shell-project.js
- stance: Tech can build it: the look is orkUI's tokens copied (the sheets already take no font, colour or corner of their own); the feed is a new phone part on readers the host has
- for: test_design_system keeps every corner and font in orkUI; ideas.recap already answers "since the last look" per device; Pixelify's going removes a font from the shell
- against: The feed replaces §223's tabs in shell-project.js and shell-goal.js and their browser tests; sizes to tokens touch most of app.css, the phone's hotspot
- instead: The look first in its own step (orkUI copy, sizes to tokens); then the feed as pwa/shell-feed.js with feed.css, read from a realm reader the gate tests
- assumes: board_recap's rows carry a party and a time each, enough to post them by leader, newest first — shown by: board_recap.build's output over this repo's last week
