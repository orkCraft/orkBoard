---
owner: board
kind: idea
track: design
order: 5
size:
priority: normal
short: The window as a table
phase: talk
route: product, design, tech
asks: person
spec: docs/specs/158-the-window-as-a-table.md
decisions: 268, 269, 270, 271, 272, 273, 274
by: claude-code
schema: 3
---
# The window as a table: its look, answers as cards, the room's things, the discard beside the table

## Gist
Окно в облике стола: цвет — партия, стихия, сигнал; у каждого лидера своё сукно, свет от верхнего края ступенями, бронзовые рамы, вымпелы. Без большой карты: вопрос поднимается на стол, ответы — карты в руке. Цепочка лампы вместо двери, рюкзак и стул как вещи у стола, стул раздаёт специализации и открывает рюкзак на выбранной. Отбой вне стола, Release не обязательна, To main с тестами. Название проекта, вид и стадия в шапке Оркмастера. Делаем спеку и исполнение на моделях попроще и в мейн. (decisions §268–§274)

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- Split this goal before its spec? (**§270 and §274 first, the look after** / all seven decisions in one spec) — seven decisions in one step on simpler models; To main and answer cards carry the value, felt and lamp do not
- Wait for goal 156 to land? (**yes: 158 after 156's D** / now: 158 rewrites 156's column as it is built) — 156 is in work building the discard under Release, which §273 undoes
  - Answered: No wait: 156's stages A–E are merged into main (3afc66a, 9318698), its gate green (decided by spec 156 D, 2026-11-08)
- How is the window as a table shown to work? (**the owner's week, a line in journals/project.md** / not measured) — 156 promised that line and there is no project journal yet; a fourth frame in a week needs a signal
- An answer card's line at rest? (**its whole line, written to fit the card** / its name only, the line on hover and focus) — the mockup hid it until hover: touch and the keyboard never see it (WCAG 1.4.13, 2.1.1)
- The table's look on the phone now? (**no: the desktop first, the phone a goal of its own as §270.7** / yes: every layer, as the mockup shot it) — the mockup's phone pennant sits at the screen's edge; no light over a table there
  - Answered: no: the desktop first, the phone a goal of its own (decided by §270.7, 2026-11-08)
- Which model builds §274's way to main? (**the strong one: it writes main and its skip** / the simpler ones, as the Gist says) — ideas.to_main and the act that skips the tests guard main; the look can go to simpler models
- To main where a project has no tests? (**refused in words, To main without the tests offered** / sent, the card saying no test ran) — gate_config gives a project with no tests `none`; §274.3 lets only the named act skip them
  - Answered: refused in words, To main without the tests offered (decided by §274.3, 2026-11-08)

## Product
### Talk
- verdict: doubt — go if split: §270 (answers as cards) and §274 (To main from the discard) first, the look after, and once 156 lands
- stance: Product wants §274 and §270 now; the felt, lamp, pennants and bronze are a look with no job behind them yet
- for: §274 lets a project with no Release ship to main with the gate's tests; §270 puts the person's decision in the hand
- against: seven decisions in one goal while 150 and 156 rebuild the same window; §273 undoes 156's column mid-build
- instead: To main from the discard (§274) and answers as hand cards (§270); the table's look as a goal of its own
- assumes: a person answers from hand cards without reading the big card's words — shown by: the owner's week of answers, few opened with Open…

## Design
### Talk
- verdict: doubt — go if the look (§268, §269, §271) is its own step in orkUI first (§269.9), and an answer card's line is read without hover
- stance: Design wants answers as cards (§270) and the three colour layers; felt, bronze, pennants and the lamp are orkUI's work first, a step of their own
- for: §270 cuts the 404 × 566 card no one read to one question and its ways as cards: recognition over recall, one look at what to pick
- against: dithered steps and dark felts under text risk AA contrast; a lamp's chain hides Here/Away in a picture; hover-only lines fail touch and keys
- instead: §270 and §268's colour layers now; felt, light steps, bronze, pennants and the lamp's chain as a goal of orkUI's, then gui/
- assumes: text and signals keep 4.5:1 and 3:1 on every felt, lit and out — shown by: a contrast test over each felt and step, lamp lit and out

## Tech
### Talk
- verdict: doubt — go once 156's D lands and §274 is a step of its own first: ideas.to_main skips the tests today when none were asked (_checks_refusal)
- stance: Tech builds §274 in the engine (gui/ideas_gate.py, realm/party_recipes.py, project_stage.py), §270 and §273 in table/ and hand/; the look waits for orkUI's copy (§269.9)
- for: To main by code exists (ideas.to_main, main_checks.py's worktree run): §274 makes its tests mandatory and unlocks Release, no new container or caller
- against: one goal rewrites discard.js, column.js, door.js, hand/answers.js and their browser tests while 150 and 156 build the same files; a skip to main built on simpler models
- instead: §274 alone first (the gate's tests in To main's checks, one named act to skip them, Release unlocked); then §270 and §273; the look after orkUI
- assumes: the gate's tests on a goal's way to main end in minutes, not the whole suite — shown by: a To main on this repository, its checks' time in the event log

## Decisions
§268, §269, §270, §271, §272, §273, §274.
