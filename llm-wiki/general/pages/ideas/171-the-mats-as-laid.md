---
owner: board
kind: idea
track: design
order: 18
size:
priority: normal
short: The mats as laid
phase: talk
route: product, design, tech
by: claude-code
schema: 3
---
# The mats as laid: ten layouts, the move on its mat, the project's deck, the backpack as mats, the team by the hero's steps

## Gist
The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decision §300): «по сути вся работа с картами происходит в
планшетах, а столы - это наборы планшетов»; «карта или фишка - это сущности планшета. Только фишка подразумевает вопрос и ответ на
него, а карта идёт как контент планшета»; then laid the mats one by one (the hand, a rating, a compare, a battle, the gate, a flow, a
scheme, slots, the discard), «Гейт в теории тогда можно объединить с битвой, тоже карты тестов сверху», a chart's drops for live ops
and a story map «с хребтом из JTBD»; «персона у product лидера должна быть той же и у дизайнера и у маркетолога»; the project's deck
«в рюкзаке оркмастера»; «рюкзак лидера это набор планшетов»; the team «да, шаги»; then: «записываем все решения в main и делаем
полностью имплементацию всех незаимплементированных решений и идей на более слабых моделях, и все вливаем в main».

What is built: decision §299 (an opened card's address, a mat's slots behind its words, the upright battle) and decision §300 (its
points 1 to 10 and 12 to 17), on the table of cards on mocks (`js/cards/`, `?mock=1`), the host's part the contract the mocks hold
(`js/mock/parts/`). Run's chart (§300.11) waits for a measure Run reads; it is out of this goal.

Then, after Product's and Design's Talk (decision §301): «мы снимаем мок-данные и уже пишем бизнес-логику по всему»; «планшет
сравнения сможет сверху показать результат выбора при выделении карты: например если это разная архитектура или дизайн». So the
mats are built on the Board's own data, their logic in the host, no mock data on the page; compare shows above its cards what the
card in focus would make.

Split (the person: «да»): this goal builds what every mat stands on, the mat's frame as a playmat (§300.15: the felt, the plates,
the printed zones, the seal, the phases), its address and its slots closed (§299.3, §299.5, §300.1), the move on its mat and the hand
a card for each move that waits (§300.2, §300.3), the cards' three kinds (§300.4), and the page's mats reading the host, not mocks
(§301.1, §301.2). Each mat is a goal of its own: the discussion, compare, the battle and the gate, the discard, the project's deck,
the backpack and the team, the frameworks' mats, the story map, the history book.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- Where does Product's persona come from? (**A job's segment, as its card** / A persona card of its own / Examples until people are heard) — §300.12 makes the persona Product's card, yet the tree (§172) gives a job only a segment; one keeper wants one source · A job's segment, as its card: A job names its persona; the segment's words are the card, no new field · A persona card of its own: Its own words, set on each job; segment and persona kept in step · Examples until people are heard: Example personas only; Design and Marketing lay no real one yet
  - Answered: From a question to the person: Product asks the person who the people are, and the person's answer is the persona's card (the person: «вообще из вопроса игроку») (the person, 2026-11-12)
- What fills the story map on mocks? (**Real goals under proposed jobs** / Examples only, marked example / Real goals, no job kept) — the mocks are to be as near the real page as can be (goal 170 M); a proposed card lies faint until kept (§300.12) · Real goals under proposed jobs: This Board's goals laid faint under jobs read from its specs, until kept · Examples only, marked example: Example jobs and goals; its layout judged, not this product's map · Real goals, no job kept: The Board as it is: every goal in one column, no job kept yet
  - Answered: Real goals, no mock data: a mat with nothing yet lays its empty zones with who fills them (decided by §301, 2026-11-12)
- A way, then the seal? (**Seal only what cannot be undone** / Seal every mat, as drawn / A way pressed is the move) — §300.15 makes a mat's move pick-then-seal while the hand's way is one press (§300.2): one move, two gestures · Seal only what cannot be undone: One press as in the hand; the seal guards a merge into main and New wins · Seal every mat, as drawn: Two presses on every mat and one in the hand, as §300.15 has it · A way pressed is the move: One press everywhere; a merge into main still asks first (§300.9)
  - Answered: Seal only what cannot be undone (Merge into main, Send to a branch, Ship a release); every other move is one press, its Undo in Orkboard's history (the person: «можешь историями оркборда») (the person, 2026-11-12)
- Each mat checked against its shot? (**Pictures, a stage a mat** / One picture pass at the end / The person presses ?mock=1) — Weaker models drift from a mockup without a picture to hold them (goal 170's risk); docs/mockups/mats/shots holds 44, desk and phone · Pictures, a stage a mat: Each mat accepted on desk and phone pictures before the next begins · One picture pass at the end: Fewer passes; a drift found when all are built, many mats made again · The person presses ?mock=1: No picture kept; the person finds the drift by pressing, after the merge
  - Answered: Pictures, a stage a mat: each mat drawn on the real page at 1440 and 390, laid beside its shot in docs/mockups/mats/shots, accepted by Design's pass; each mat added to tests/test_cards_fit_browser.py (the person: «давай вариант а») (the person, 2026-11-12)
- A move with no Undo yet? (**One Undo part, the rest sealed** / The toasts' Undo, the book later / Every move sealed for now) — the person's answer gives each one-press move its Undo in the history; the host's are a few toasts (unthrow, undo_rewrite, put_back_undo) · One Undo part, the rest sealed: core keeps each move's reverse; a pass begun or money spent carries the seal · The toasts' Undo, the book later: The toasts' Undo as today; Drop and Start one press with nothing to undo · Every move sealed for now: Nothing lost; every move two presses until the history book's goal lands
  - Answered: One Undo part, the rest sealed: core keeps each one-press move's reverse in the history; a move it cannot reverse (a pass begun, money spent, Merge into main, Send to a branch, Ship a release) carries the seal (decided by §302.4, 2026-11-12)
- Which table do the mats land on? (**Behind ?table=cards until the last mat** / The cards the default now / Both tables kept a while) — cards/on.js draws the cards on ?mock=1 and ?table=cards only; §299.4 retires the goal's pane, yet its acts' mats are later goals · Behind ?table=cards until the last mat: Today's table stays; cards/on.js flipped once the discard and battle land · The cards the default now: One table now; acts with no mat yet (the gate, To main) gone until theirs land · Both tables kept a while: 170's D to F go on; every goal changes two tables until one goes
  - Answered: Behind ?table=cards until goal 170's last step turns the table of cards on and the old faces go (decided by §296.10, 2026-11-12)
- Does §302's hand come in here? (**§302.1 and .4 here, zones later** / All of §302 here / §302 a goal of its own) — §302 came after this Gist and changes §300.2's hand; a zone's narrowing reads the project's deck (§300.12), a goal of its own · §302.1 and .4 here, zones later: The hand follows the open mat now; a zone narrows it once the deck lands · All of §302 here: The hand reads the project's deck early; this goal takes the deck's host part · §302 a goal of its own: This goal builds §300.2's hand; §302 rewrites the same hand right after
  - Answered: §302.1 and §302.4 here: the hand follows the open mat and holds its ways; a zone narrows it once the project's deck lands, in that goal (the person: «давай вариант а») (the person, 2026-11-12)

## Decisions

## Product
### Talk
- verdict: go
- stance: Product keeps the story map (§300.10) and the persona, job, struggle and measure cards (§300.12); its jobs across must be the tree's (§172), and its into a job the tree's attach
- for: One move a mat makes each screen a decision the person takes; the hand, Discussion, battle, gate and discard lie on every goal's path, pressed on mocks before the host is written
- against: Ten layouts, a deck, a backpack and a team at once, on goal 170's stage T still open; §297 to §300 each changed the one before in a day, many points taken by default
- instead: the mats on every goal's path first (hand, Discussion, battle, gate, discard); the story map, the deck and the team once goal 163 keeps the jobs on the Board
- assumes: the person settles a goal's turns faster on its mats than on today's pane — shown by: on ?mock=1 one goal rated, gated and merged from the hand alone, the old pane never opened

## Design
### Talk
- verdict: doubt — go only if each mat lands in a stage of its own, in test_cards_fit_browser.py's surfaces and accepted on its pictures beside its shot; on weaker models a mat drifts unseen
- stance: Design wants the mats: one layout a kind, one move at its foot's right, learnt once on both faces; held to its 44 shots a mat at a time, read in one order by keys and a screen reader
- for: A mat is known by its layout, its move always at its foot's right (Nielsen 4, 6); an opened card loses its row of mats (8); no total on a battle; every gesture a button with its word and a key
- against: The seal makes a mat's move two presses and the hand's one (§300.2, §300.15; Nielsen 4, 7); the phone's battle shot lays the seal before its ways, its ways turned (WCAG 2.4.3, §300.15)
- instead: The mats on a goal's path first (hand, Discussion, battle and gate, discard), each accepted on desk and phone pictures; the grid, scheme, flow and backpack once those pass
- assumes: a closed mat is told by its faint slots alone at an M's size (§300.1) — shown by: on ?mock=1 at 1440 the person names five closed mats' kinds with their lines covered

## Tech
### Talk
- verdict: doubt — go only if each one-press move has its reverse in one Undo part over realm/event_log.py, or carries the seal; the host's Undo is a few toasts, no history
- stance: Tech lays the frame, the address, the hand and the three kinds on js/cards; the mats' commands in a gui module of their own, served by core and realm; js/mock for tests only
- for: One contract: the cards read seven parts only the mock holds and send eight commands no host answers (ideas.tables, ideas.reply…); verdicts are read free (realm/page_talk.py)
- against: js/cards is goal 170's stage T, built, never accepted, D to J open; gui/ideas.py (775 lines) and board_host.py (805) past 600; 14 browser tests open ?mock=1
- instead: The host's half first: the hand's turns and the verdicts answered, ideas.reply and ideas.ask_leader taken, proposed() gone from js/link.js; the felt and seal after 170's T
- assumes: every move that waits is read from the Board's files (phase, asks, gate, Talk), no leader's pass — shown by: ideas.turns on this repository lays the hand ?mock=1 shows, no model run
