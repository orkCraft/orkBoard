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
- What lays a battle on this Board? (**The decision's conflicts** / Conflicts and the Orkmaster's route / The gate now, the battle later) — only keeper.decide's call names a conflict (§254.6), and no Talk on this Board has said no: a battle from other words would be invented · The decision's conflicts: The hand's conflict card becomes a battle; skill-run goals lay none · Conflicts and the Orkmaster's route: Routing names a goal's decisions too; heavier, it takes goal 166 in · The gate now, the battle later: Gate and H7's from land now; the battle waits for a source here
  - Answered: The decision's conflicts: the hand's conflict card becomes a battle; skill-run goals lay none (the person, 2026-11-13)
- What prices an old card's undoing? (**What rests on it, read by code** / An empty zone, who fills it / The Orkmaster prices each) — no host prices a card yet (171 left every cost empty); the goals and tests naming §N are what a rewrite breaks, free to read (§301.2) · What rests on it, read by code: The goals, decisions and tests naming its §; no mana shown · An empty zone, who fills it: The zone says the Orkmaster prices it; the battle shows no cost · The Orkmaster prices each: A mana price on each old card; a paid pass a battle, its cost said first
  - Answered: What rests on it, read by code: the goals, decisions and tests naming its §; no mana shown (the person, 2026-11-13)
- What lies above the gate's line? (**What its tests name** / A map Tech keeps / The checks by name, as today) — 298 of 523 test files already name the decisions they guard (decisions §N), read free by code (§301.2); a check stays the decision it guards (§300.4) · What its tests name: Failing tests' decisions face up; a test naming none lies as its file · A map Tech keeps: Exact; one more file each new test must keep up · The checks by name, as today: No reading; cards that stand for no decision, against §300.4
  - Answered: What its tests name: failing tests' decisions face up; a test naming none lies as its file (the person, 2026-11-13)
- Which ways does a battle deal? (**The host's three, one face** / §299.6's four, as drawn / Both faces kept) — ideas.conflict answers replace, keep and other; one choice on two faces with different ways is learnt twice (Nielsen 4) · The host's three, one face: The conflict card opens the battle: New wins, Old wins, your words · §299.6's four, as drawn: Merge and Not a battle join the host; Merge a leaders' paid pass · Both faces kept: §254.6's pair stays as it is; the battle mat lays four beside it
  - Answered: The host's three, one face: the conflict card opens the battle: New wins, Old wins, your words (the person, 2026-11-13)
- What does the gate's Fix it do? (**By where it is** / Its stage again, always / A Fix goal, always) — a red on the way to dev leaves the goal unmerged on goal/<slug>; on the way to main it is done, and the host refuses a done goal's change: «make a new goal of it» · By where it is: Stage again before dev; a Fix goal after, as the host says of a done goal · Its stage again, always: One card always; a done goal reopened, against the host's «make a new goal» · A Fix goal, always: Findings' path as built; even a goal not in dev gets a second card
  - Answered: By where it is: its stage again before dev; a Fix goal after, as the host says of a done goal (the person, 2026-11-13)

## Decisions

## Product
### Talk
- verdict: doubt — go if the battle shows only what the host keeps: the decision's conflicts (§254.6) and a cost to undo read by code; no host prices a card yet (171 left every cost empty)
- stance: Product wants the gate as §300.8 lays it and H7's signal whole (171's line 5, to_main's from); a battle on the conflicts the host holds, each way played counted as move_played
- for: The gate lies on every goal's path and its ring goes against §300.8; rewriting past decisions is a real job (§297 to §302 each changed earlier ones in a day); H1's disagreement, logged
- against: Four things in one goal (battle, gate, H7's from, four tests); only keeper.decide lays a conflict, which skill-run goals never call, and no Talk here has said no: this Board meets no battle
- instead: the gate as a battle and H7's from first, on every goal's path; the battle mat once this Board's goals name the decisions they go against (goal 166)
- assumes: the person settles a rewrite of past decisions on a battle, not in chat as §297 to §302 were — shown by: more decisions changed through New wins than outside it, over the owner's weeks

## Design
### Talk
- verdict: doubt — go if a conflict keeps one face: the battle in place of §254.6's lifted pair, on ideas.conflict's ways, sealed only where a pass runs (§302.4); the gate as §300.8 at once
- stance: Design wants the gate in 171's frame now, decisions above, the stack below, its ways in the hand; a battle only as the one face of a conflict, its seal only on a way that runs a pass
- for: The gate lies on every goal's path, still a ring and its checks drawn as decision cards named by no decision; one upright layout for battle and gate is learnt once (Nielsen 4, 6)
- against: A conflict would get two faces, §254.6's lifted pair (three ways) and the battle (four); a decision has no leader's token, so its row lies empty; Settle it would seal New wins, one press
- instead: the gate laid as §300.8 with H7's from now; the battle as the hand's conflict card's own mat, its ways ideas.conflict's three, §254.6's lifted pair gone
- assumes: a failing test's file names the few decisions it guards (decisions §N) — shown by: the §N each test file names, read by code: how many name one to three, how many none

## Tech
### Talk
- verdict: doubt — go if the battle answers only through ideas.conflict (no battle_settle, one writer of the decision) and the gate's §N are read in a realm module, dev's red keeping test ids
- stance: Tech builds the gate on the checks' failed test ids (main_checks keeps them, goal_branch must too) and H7's from in played(); the battle only as a face of board_map's conflict rows
- for: Each part reads what the host keeps: board_map's conflict rows, main_checks' failure ids, 277 of 523 test files naming one to three §N; H7's from is a small bug in played() and toMain()
- against: battle_settle would be a second writer of the decision beside ideas.conflict; a cost to undo read in the snapshot scans 523 tests and 8.5k lines; board_map.py (564 lines) takes no more
- instead: the gate as §300.8 with H7's from now (played, gate.js, a realm reader of tests' §N); the battle as ideas.conflict's mat in a goal of its own
- assumes: a test file's §N is the decision its tests guard, not one it only cites — shown by: twenty red tests' ids read against the §N their files name
