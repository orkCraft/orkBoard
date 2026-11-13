---
owner: board
kind: idea
track: tech
order: 113
size:
priority: normal
short: The battle and the gate
phase: spec
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
### Why
- The gate and the battle are where the person decides whether work goes on and whether a past decision gives way: Product answers that each is the Board's own (§301.1, §303), never invented, and what a rewrite breaks is said before it is played.
- H7 counts only when every sealed move keeps its goal and where it was pressed; goal 171 left the gate's seal blind (its line 5), so Product's signal was half.
- The battle rests on a belief no one has shown (Talk's assumes), so Product writes it as H8 with its signal, and the battle grows (Merge, a price) only if it holds.
### Done when
- [test] When the person seals Merge into main on the gate mat (?table=cards, the mat opened from the goal's card), then the real `ideas.to_main` logs `move_played` with the goal read from `idea`, kind `merge_main` and `from: mat` (`hand` when its hand card opened the mat); Send to dev on the real `ideas.goal_to_dev` likewise as `send_branch`
- [test] When the person plays a battle's way (New wins, Old wins, Your words) from its mat or its hand card, then the event log keeps `move_played` with the goal, the way's kind and its from, and `conflict_answered` its choice; Your words' text is in neither
- [test] When the table of cards opens (?table=cards) on a fixture Board where one goal's decision keeps a conflict with §N and a goal run by the skills keeps none, then the first has one battle card in the hand, §N above its line, and the second has no battle
- [test] When the person opens that battle from its hand card, then under §N lie the goals, the decisions and the tests that name §N, as the fixture's files hold them, with no mana or price shown, and opening it starts no pass and spends nothing
- [test] When the gate goes red, then Fix it on a goal unmerged on its own branch puts its stage back to work on that goal, and on a goal done on its way to main lays a new Fix goal naming it, the done goal's page byte for byte as before
### Checks
- Reading a battle, what rests on an old card and the gate's decisions runs no model and spends nothing (§301.2); only Old wins and Your words, which begin the keeper's reword, say their cost before they run (§303.4).
- What rests on §N traces to files: each goal, decision and test counted under it names §N; no mana, price or potion is drawn on an old card (§303.2).
- `move_played` and `conflict_answered` keep no word of the person's or a leader's: Your words' text never enters the event log (H7, H8).
- H8 in docs/hypotheses.md says what holds it, what refutes it and how it is tested, its signal `conflict_answered` against the decisions written with *Changes:* outside a battle; H7's *How we test it* says the gate's seals now count.
- The battle's ways and Fix it say plainly what happens (New wins replaces §N, Old wins rewords the new decision within it, a Fix goal is a new goal) and enter `realm/lexicon.py` `TERMS` with the code that draws them (CLAUDE.md).
### Will be
- changed hyp:h7 — its signal whole: the gate mat's seals (Merge into main, Send to dev) and the battle's ways keep the goal and from, so a move on the gate is no longer counted as nobody's
- new hyp:h8 — the belief the battle rests on (a past decision is rewritten on a battle, not in chat), its signal `conflict_answered` against decisions changed outside it, in docs/hypotheses.md
### Out
- §299.6's Merge and Not a battle, and any mana or price on an old card (§303.2, §303.4): only if H8 holds.
- A battle for a goal run by the skills, or laid from other words (a Talk's no, a goal naming the decisions it goes against: goal 166).
- Judging H7 or H8: their signals are kept here; the verdict is the owner's weeks, not this goal.
### Risks
- risk: medium
- This Board's goals are run by the skills and lay no battle (§303.1): the battle is met only on goals the window's keeper decides, and H8's signal may stay empty for weeks.
- What rests on §N read as text may count a mention as a guard (Tech's assumes): a §N cited in a decision's *Why* inflates the cost the person weighs.
- The discard's older faces (`table/portal.js`, `hand/devplay.js`) still press the seals with no from; read as "", they must never be counted as `mat`.
- Each red on the way to main lays a new Fix goal: reds in a row crowd the Orkmaster's lane with goals the person did not lay.
### Defaults
- A battle's way logs `move_played` as any move: New wins a one-press kind of its own in `core/idea_undo.py` with its Undo; Old wins and Your words the sealed `paid_pass`, the keeper's reword.
- What rests on §N: the goals whose pages name §N, the other decisions whose text names it and the test files naming `decisions §N`, each counted once, §N itself not.
- `from` is `hand` when the gate mat or the battle was opened from its hand card, `mat` when from the goal's card on the table; the discard's older faces keep "" as today.
- H8 is the next free number (H1 to H7 taken); its signal needs no new event (`conflict_answered` keeps idea, number, choice and device).

## Design
### Talk
- verdict: doubt — go if a conflict keeps one face: the battle in place of §254.6's lifted pair, on ideas.conflict's ways, sealed only where a pass runs (§302.4); the gate as §300.8 at once
- stance: Design wants the gate in 171's frame now, decisions above, the stack below, its ways in the hand; a battle only as the one face of a conflict, its seal only on a way that runs a pass
- for: The gate lies on every goal's path, still a ring and its checks drawn as decision cards named by no decision; one upright layout for battle and gate is learnt once (Nielsen 4, 6)
- against: A conflict would get two faces, §254.6's lifted pair (three ways) and the battle (four); a decision has no leader's token, so its row lies empty; Settle it would seal New wins, one press
- instead: the gate laid as §300.8 with H7's from now; the battle as the hand's conflict card's own mat, its ways ideas.conflict's three, §254.6's lifted pair gone
- assumes: a failing test's file names the few decisions it guards (decisions §N) — shown by: the §N each test file names, read by code: how many name one to three, how many none
### Why
- The gate lies on every goal's path and is still a ring taller than its field at 1440×900 (a check cut, its label under the field: Design's note on 171); laid upright as the battle is, it fits, and one layout is learnt once for both (Nielsen 4, 6).
- A conflict gets one face, the battle, its three ways the host's in one set of words, so a choice is never learnt twice; a way that starts a pass asks through the seal with its cost said, a free one is one press with its Undo (Nielsen 3, 5; §303.4).
- What a rewrite breaks is said in words by kind before a way is played, never as a price or by a colour alone (Nielsen 1, 2; WCAG 1.4.1; §303.2).
### Done when
- [test] When the person opens the gate mat at 1440×900 and at 1280×800 (?table=cards, from the goal's card) with one test failing, then it lies upright, every card and label inside its field: the §N that test names face up with the gate's no, the agreeing checks a pile, a test naming none as its file, the line, the goal's stack below in Yours; Fix it and The test is out of date in the hand; Send to <branch> a dim seal with its why; with every check agreeing, the pile alone above and the seal lit
- [test] When the person presses a goal's conflict card in the hand at 1440×900 (?table=cards, a fixture decision in conflict with §N), then the battle opens upright and no lifted pair is drawn: §N face up above (three at most, the rest a pile), under it in words what rests on it by kind, no mana, price or potion; the line of the route's crafts with the new card's tokens below and No total; the new card in Yours; New wins, Old wins and Your words in the hand, each with its line
- [test] When the person plays the battle by keys alone, then Tab goes through the old cards, the line, Yours, the hand's ways, the seal and Close, each with a visible focus; New wins is one press, its toast saying what it did with Undo; Old wins and Your words light the seal with their cost said before anything runs, Your words its field in the hand's place first; Esc closes it and the focus is on the conflict card
- [test] When the battle or the gate is opened at 390×844 from its address after a reload, then it is the whole screen with Back, upright in the desktop's order (what it goes against or guards, the line, Yours), its ways a row at its foot that scrolls, the seal after them in Tab's order too; no sideways scroll, no card cut, no text under 12 px
- [look] When the battle and the gate (one test failing, and all agreeing) are drawn on the real page at 1440 and 390, then laid beside battle-2, gate and gate-ok (desk and phone) in docs/mockups/mats/shots they read as drawn in 171's frame: the felt, bronze zones and their labels, plates, upright, the seal, the phases; three ways, no Merge, no Not a battle, no ring
### Checks
- tests/test_cards_fit_browser.py's SURFACES gain the battle and the gate (one failing, all agreeing) at 1280×800, 1440×900 and 390×844: no text under 12 px, 4.5:1 on its ground, no act clipped, no card or label outside the field, Tab reaching every act with a visible focus.
- Every card on the battle and the gate is a goal, a decision or a part (§300.4): §N a decision with its § for its picture, a test naming no §N a part with its file in IBM Plex Mono, the stack the goal; its corner says which by its sign and in its accessible name.
- What rests on an old card is words by kind with their counts, its list in the card's slip; no mana, price, potion or total, and no colour alone says its weight (WCAG 1.4.1).
- The ways' words enter realm/lexicon.py `TERMS` with the code that draws them: New wins, Old wins, Your words, each keeping its old spelling in `was` (The new one replaces §<n>, Keep §<n>, Other…); Fix it's line says what it does where the goal is: its stage again, or a new Fix goal (tests/test_gui_wording.py).
- The ring is gone (no `.sp-ring`, no check placed on a circle); the sheets keep orkUI's tokens, no new colour, no smooth gradient or blurred shadow (tests/test_design_system.py); cards dealt with no motion under prefers-reduced-motion.
### Will be
- changed home — the battle and the gate laid upright in 171's mat frame on the host's data: the conflict card opens the battle, its lifted pair gone on the table of cards, its three ways in the hand; the gate's ring gone
### Out
- §299.6's Merge and Not a battle, and any mana or price on an old card (§303.2, §303.4).
- The old table (no ?table=cards): its conflict card keeps its lifted pair until the cards are the default; only its ways take the battle's words.
- The battle's and the gate's cartoon pictures and emblem (§301.5): the emblem's place stays empty until orkUI's copy has them.
### Risks
- risk: medium
- At 1280×800 three old cards with their lines of what rests on them, the line and the new card may outgrow the field upright, as the ring did at 1440×900: S cards and one line under each must hold it.
- New wins is one press while Old wins and Your words go through the seal: three ways alike in the hand that act differently (Nielsen 4); each card's line must say which asks first.
- Until the cards are the default, the old table keeps the lifted pair: a person there still meets a conflict on a face of its own.
- A failing test file naming several §N lays several decisions face up for one red: three at most, the rest a pile, or the red is lost among them.
### Defaults
- A decision has no leader's token: above the line nothing is drawn for an old decision (no dash, no empty slot); the gate's line is one column, the gate's, its no on each failing §N, No total beside it.
- What rests on §N lies under its card in one line by kind (*rests on it: 3 goals · 5 decisions · 12 tests*), a kind with none left out, *nothing rests on it* when none; pressed, the card's slip lists them.
- The seal follows the way picked: dim *pick a way* until Old wins or Your words, then lit with that way and its cost; the gate's ways keep the rule (a pass sealed with its cost, a new Fix goal one press), with none picked its seal Send to <branch> (Merge into main on the way to main), dim with *1 check disagrees* while one fails.
- The zones' labels: the battle's *What it goes against* and *Yours*, the gate's *What its tests guard* and *Yours*; Your words' field opens in the hand's place (§286).

## Tech
### Talk
- verdict: doubt — go if the battle answers only through ideas.conflict (no battle_settle, one writer of the decision) and the gate's §N are read in a realm module, dev's red keeping test ids
- stance: Tech builds the gate on the checks' failed test ids (main_checks keeps them, goal_branch must too) and H7's from in played(); the battle only as a face of board_map's conflict rows
- for: Each part reads what the host keeps: board_map's conflict rows, main_checks' failure ids, 277 of 523 test files naming one to three §N; H7's from is a small bug in played() and toMain()
- against: battle_settle would be a second writer of the decision beside ideas.conflict; a cost to undo read in the snapshot scans 523 tests and 8.5k lines; board_map.py (564 lines) takes no more
- instead: the gate as §300.8 with H7's from now (played, gate.js, a realm reader of tests' §N); the battle as ideas.conflict's mat in a goal of its own
- assumes: a test file's §N is the decision its tests guard, not one it only cites — shown by: twenty red tests' ids read against the §N their files name
### Why
- Each part reads what the host already keeps: the decision's conflicts in its record (way.json), the gate's failing test ids (main_checks keeps them; the way to dev must too), the §N that 303 of 533 files in tests/ name. Nothing is mocked, and no model prices anything (§301, §303).
- The decision keeps one writer: a battle's ways go only through ideas.conflict, and New wins' Undo only through core/idea_undo.py. A second writer (battle_settle) would split what the keeper confirms.
- H7's signal is a small bug in played() (it reads the goal from `slug` only) and in toMain (it sends no `from`): until that is fixed, every move on the gate counts as nobody's.
### Done when
- [test] When `ideas.battle` is asked for a fixture goal whose decision keeps a conflict with §N, then it answers §N's title and point and what rests on it: the goals, decisions and test files naming §N, each once, never §N itself or a `spec <n> §k`. No model runs, no lease is taken, no file is written
- [test] When a battle's way is played from the hand (`ideas.conflict` with `from: hand`), then New wins (replace) goes in one press and `ideas.undo` puts the decision's record back while it is as the move left it; Old wins and Your words are refused without `sealed: true`; gui/ and js/ hold no `ideas.battle_settle`
- [test] When the gate goes red on the way to dev in a fixture repository, then the goal's branch record keeps the failing test ids and the test files the gate ran, and `ideas.gate_guards` lays each failing test's `decisions §N` with its ids, a test naming none as its file, the other §N of the run's files as agreeing
- [test] When Fix it is played on a red gate, then on a goal unmerged on its branch `ideas.gate_fix_stage` goes only sealed and puts one task of the failing tests in its plan, the goal at work (runner faked, no model); on a done goal `ideas.gate_fix_goal` lays a goal `fixes: <slug>` in one press, which its Undo removes, the done page byte for byte as before
- [test] When the gate mat's seal is pressed (`ideas.to_main` or `ideas.goal_to_dev` with `{idea, sealed: true, from}`), then `move_played` logs the goal read from `idea`, its kind and `from` as sent (`mat` or `hand`); a seal with no `from` (the discard's older faces) logs `from: ""`
### Checks
- tests/test_architecture.py: realm/decision_refs.py is pure (no git, no model, no write, no gui); each new module stays under 600 lines; gui/ideas.py grows by one registering line at most, core/idea_runner.py (618) only by its mixin's line.
- Reading a battle and the gate's guards runs no model, takes no lease and writes nothing. It stays out of the snapshot (`ideas.board`) and is asked only when its mat opens.
- The decision has one writer: a battle's ways reach it only through gui/ideas_conflict.py. Only core/idea_undo.py writes an Undo record, and it publishes on the bus.
- The hand's tables stay closed (tests/test_ideas_mats_closed.py): new_wins and fix_goal are one press, each with its reverse, and reach no model; fix_stage and the reword (Old wins, Your words) are sealed; no kind is neither.
- Off ?mock=1, js/cards draws no battle and no gate from js/mock. `.sp-ring` and `battle_settle` are gone, and `move_played` keeps only idea, kind and from.
### Will be
- new orkboard/realm/decision_refs.py — what names a decision, read from files: the goals, decisions and tests naming §N (an old card's cost to undo), and the §N a failing test guards; pure
- new orkboard/gui/ideas_battle.py — ideas.battle and ideas.gate_guards (read only, asked when the mat opens), ideas.gate_fix_stage, ideas.gate_fix_goal; one line in gui/ideas.py
- new orkboard/core/idea_fix_stage.py — Fix it before dev: one task of the failing tests added to the goal's plan and the goal set to work, a mixin of the runner, which is past 600 lines
- changed orkboard/gui/ideas_mats.py — played() also reads the goal from `idea`; ideas.conflict's three ways and the two Fix it commands join its tables, so H7's from is whole
- changed orkboard/core/idea_undo.py — new_wins (puts the decision's record back, forgets its wait) and fix_goal (removes the goal laid) are one press; fix_stage is sealed
- changed orkboard/realm/goal_branch.py — a red on the way to dev keeps its failing test ids and the test files the gate ran, as main_checks keeps its failures
- changed orkboard/realm/main_checks.py — its Tests check keeps the test files it ran beside its failures, so the gate's agreeing pile is read, never guessed
- changed orkboard/gui/static/js/cards/spreads/battle.js — the host's battle from the conflict card: §N above with what rests on it, ideas.conflict's three ways; no battle_settle
- changed orkboard/gui/static/js/cards/spreads/gate.js — upright on ideas.gate_guards in 171's frame, its ring gone; its seals and Fix it send `from`
- changed orkboard/gui/static/js/table/portal.js — toMain sends the `from` it is given; the discard's own press still sends none
### Out
- §299.6's Merge and Not a battle, any mana price on an old card, and a battle laid from other words (a Talk's no, goal 166): §303.
- The old table's conflict pair (no ?table=cards): its ideas.conflict presses keep no `from` and no Undo, as today, until the cards are the default.
- A finer guard than the text: a §N a test names is taken as one it guards, and Tech keeps no map of tests to decisions (§303.3).
### Risks
- risk: medium
- core/idea_runner.py (618 lines) is a hotspot: the stage run again belongs in its mixin, and a weaker model may write it into the runner itself.
- New wins' Undo during the leaders' wait: the wait's tick rewrites way.json, so an Undo that compares the whole file is refused at once.
- A test file can name up to 15 §N, so one red may lay many: read the failing test's own text first and its module docstring after, three face up at most.
- The four browser cases come back on a recording of the host (tools/record_mock.py): unless it is recorded again from ideas.battle and ideas.gate_guards, they pass on a contract the host no longer answers.
### Defaults
- A test names decision N where it writes `decisions §N` (and any §M listed right after); `spec <n> §k` and `<file>.md §k` are a spec's points; a number the log lacks is left out. The failing test's own function text is read first, else its file's module docstring.
- New wins' Undo compares and puts back only way.json's `decision` and forgets the wait it began (`idea_ripe.drop`); it is refused once the decision has changed.
- Fix it is two commands; the page sends the one that fits where the goal is, and the host refuses the other in words. `ideas.gate_fix_stage`: sealed, its cost (the task budget under the Target) said first. `ideas.gate_fix_goal`: one press, laid as `ideas.add` lays a goal, no model, routed to Tech.
- The battle's card is laid from the snapshot's `conflict` rows (realm/board_map.py), one card for each goal; realm/board_turns.py gains no battle kind, so a conflict has one reader.
