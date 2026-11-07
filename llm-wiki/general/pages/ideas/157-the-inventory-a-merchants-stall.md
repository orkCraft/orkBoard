---
owner: board
kind: idea
track: design
order: 4
size:
priority: normal
short: The inventory, a stall
phase: done
spec: docs/specs/157-the-inventory-a-merchants-stall.md
decisions: 266, 267
route: design, product, tech
by: person
schema: 3
gate: 8e2bbeb · 44 files · green
---
# The inventory, a merchant's stall; a hero lays its table

## Gist
Давай макет мерчанта сделаем более похожим на мерчанта из slay the spire и сделаем скрины как будут выглядеть столы всех 18 согласованных лидеров. Давай делаем спеку и имплементацию на моделях попроще и в мейн. Для построения этих столов в первый раз при открытии проекта нужно вызывать модель: оформить это в виде первого тикета для онбординга.

## Why
§266's inventory laid what is set on the table and its ways in the hand, so a thing had to be pressed before anyone learned what there was to take; a merchant lays every ware at once with its price. A hero's school lays its table, and what only its leader can keep is a model's pass, the person's money, so it is a goal, never a silent call (decision §267).

## Done when
- The backpack opens the stall at 1280 × 800: the merchant, the rug with a chair's wares and their plates, the hand of what you carry; a ware taken writes its setting and Undo returns it; a card on the service or the discard goes back to its default.
- A party with a non-default hero shows its hero's frame, its kept cards in their places and the empty ones' questions.
- The first open lays *Lay the tables* once and starts nothing; a hero taken lays its party's goal.
- No price on a plate the host did not estimate; the critical tests are green.

## Out
Places read by code, the ways of answering's engine, the starts by priority and the day's cap, the Orkmaster's star, the textures, the die's faces, the phone (spec 157, *Later*).

## Stages
Spec 157's parts in its waves: 1 A (the heroes), B (orkUI's heads) · 2 C (the stall's host) · 3 D (the stall's face), E (the hero's table), F (lay the tables).

## Open questions

## Decisions
§266, §267.
