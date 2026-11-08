---
owner: board
kind: idea
track: design
order: 5
size:
priority: normal
short: Answers as cards, To main after the tests
phase: work
route: product, design, tech
spec: docs/specs/158-the-window-as-a-table.md
decisions: 270, 274
by: claude-code
schema: 3
gate: b79367b · 145 files · red
---
# Answers as cards in the hand, To main from the discard after the gate's tests

## Gist
Окно в облике стола: цвет — партия, стихия, сигнал; у каждого лидера своё сукно, свет от верхнего края ступенями, бронзовые рамы, вымпелы. Без большой карты: вопрос поднимается на стол, ответы — карты в руке. Цепочка лампы вместо двери, рюкзак и стул как вещи у стола, стул раздаёт специализации и открывает рюкзак на выбранной. Отбой вне стола, Release не обязательна, To main с тестами. Название проекта, вид и стадия в шапке Оркмастера. Делаем спеку и исполнение на моделях попроще и в мейн. (decisions §268–§274)

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
- [x] A. To main only after the gate's checks
  - party: Tech (the strong model, the person's answer). `gui/ideas_gate.py` `to_main` and `_checks_refusal`: a goal whose checks were never asked, or passed for another head of main, is refused in words; a red check names its test, the trial worktree is gone; `gate_merge` takes nothing to main untested either. Tests in tests/test_goal_main.py, test_main_checks.py.
  - proves: Tech's "When ideas.to_main is called for a goal in dev whose checks were never run…", "When the gate's Tests check is red on a goal's way to main…"; Product's "When one of the gate's tests is red on a goal's way to main…" (the engine's half)
- [x] B. The one named skip
  - party: Tech (the strong model). `untested: true`, a literal boolean, is the only argument that skips the checks; a project whose gate has no tests (`gate_config` gives `none`) is refused in words, *To main without the tests* offered; `goal_to_main` adds `tests: run | skipped` and the checks' time (`realm/event_log.py`'s line said too).
  - proves: Tech's "When a project's gate has no tests, then To main is refused in words; only ideas.to_main with untested: true sends it…"; Product's "When a project's gate has no tests…" (the engine's half)
- [x] C. Release a craft as any
  - party: Tech. `gui/ideas_track.py` `track_drop` drops its refusal for Release; `realm/project_stage.py` no longer marks Release's card `locked`; `realm/goal_types.py` `release_party` still makes Release the one place to release while seated, and a seated Release's `[gate.main]` (the skeletons, §188) still runs before main. Tests in tests/test_party_removed.py, test_releases.py.
  - proves: Tech's "When the person removes the Release party, then it is removed with no refusal, and a goal in dev still reaches main by ideas.to_main after the gate's tests."
- [x] D. To main and To main without the tests on the page
  - party: Tech (the strong model). `js/table/tomain.js` and `portal.js`: *To main* always asks the checks first and sends only when green; the card says in words which test stopped it; the no-tests refusal offers *To main without the tests* in the card's menu, the only face that sends `untested: true`; `readycard.js` and any other caller of `ideas.to_main` ask the checks first. A browser test on a project with no Release seated.
  - proves: Product's "When the person sends a goal in dev to main from the discard on a project with no Release seated…", "When one of the gate's tests is red…", "When a project's gate has no tests…"
- [x] E. Where an answer was given
  - party: Tech. `ideas.answer` (`core/idea_draft.py`, `core/idea_talk.py`, `gui/ideas_phase.py`, `gui/ideas_board.py`) takes `from: hand | open` and writes it on `idea_answered` and `goal_answered`; `hand/answers.js` sends `open` after *Open…* (the hand cards of F send `hand`). Tests of those modules.
  - proves: Tech's "When the person answers a goal's open question from a hand way card or after Open…, then its idea_answered event carries from: hand or from: open."
- [ ] F. A lifted card stays a hand card, its ways are the hand
  - party: Design. The lifted card rises 144 × 202 onto the table's foot in its signal's ring, its goal's card in the column ringed the same; each way a 144 × 202 hand card with its name (pixel face) and whole line (body face) at rest, the leader's pick marked by its head and in words, a priced way's cost in its corner; *<Leader> decides*, *Open…*, *Put it back* at the row's end; the rest of the hand sinks, grey and inert; reduced motion at once; orkUI's tokens only. `hand/answers.js`, `hand/ways.js`, `hand/wayline.js`, `hand/openedcard.css`, `table/column.js`. A browser test at 1280 × 800.
  - proves: Design's "When the person lifts a goal card with one open question at 1280 × 800, then it stays 144 × 202…", "When that card is up, then each way is a 144 × 202 card in the hand…"; Product's "When the person lifts a goal card with one open question at 1280 × 800, then each way is a hand card showing its whole line…"
- [ ] G. Your own words and the keys
  - party: Design. *Your own words…* opens a field on the table beside the question, focused, *Send to <leader>* under it; Tab rings each way, *<Leader> decides*, *Your own words…*, *Open…* and *Put it back* in turn; Escape and *Put it back* return focus to the lifted card. A browser test.
  - proves: Design's "When the person tabs through a lifted card's answers…", "When the person presses *Your own words…*…"
- [ ] H. A goal in Talk lifted
  - party: Design. Its table lays its leaders' Talk and its open question with its ways; the picture shot by docs/mockups/answer-cards/shoot.py pointed at the product, at 1280 × 800.
  - proves: Design's "When a goal still in Talk is lifted at 1280 × 800, then its table shows its leaders' Talk…" (a [look] line: the person judges the picture)
- [ ] I. The owner's week
  - party: Product, after a week of the owner's use. Read `goal_to_main` (tests run or skipped, the checks' time) and `idea_answered` / `goal_answered` (`from`) in the event log; write a line in llm-wiki/general/journals/project.md on answering from hand cards and sending to main from the discard.
  - proves: Product's "When the owner's week of use ends, then journals/project.md holds a line…"

## Open questions
- Split this goal before its spec? (**§270 and §274 first, the look after** / all seven decisions in one spec) — seven decisions in one step on simpler models; To main and answer cards carry the value, felt and lamp do not
  - Answered: §270 and §274 first, the look after (a goal of its own, orkUI first) (the person, 2026-11-08)
- Wait for goal 156 to land? (**yes: 158 after 156's D** / now: 158 rewrites 156's column as it is built) — 156 is in work building the discard under Release, which §273 undoes
  - Answered: No wait: 156's stages A–E are merged into main (3afc66a, 9318698), its gate green (decided by spec 156 D, 2026-11-08)
- How is the window as a table shown to work? (**the owner's week, a line in journals/project.md** / not measured) — 156 promised that line and there is no project journal yet; a fourth frame in a week needs a signal
  - Answered: the owner's week, a line in journals/project.md (the person, 2026-11-08)
- An answer card's line at rest? (**its whole line, written to fit the card** / its name only, the line on hover and focus) — the mockup hid it until hover: touch and the keyboard never see it (WCAG 1.4.13, 2.1.1)
  - Answered: its whole line, written to fit the card (the person, 2026-11-08)
- The table's look on the phone now? (**no: the desktop first, the phone a goal of its own as §270.7** / yes: every layer, as the mockup shot it) — the mockup's phone pennant sits at the screen's edge; no light over a table there
  - Answered: no: the desktop first, the phone a goal of its own (decided by §270.7, 2026-11-08)
- Which model builds §274's way to main? (**the strong one: it writes main and its skip** / the simpler ones, as the Gist says) — ideas.to_main and the act that skips the tests guard main; the look can go to simpler models
  - Answered: the strong one for §274's way to main; the rest on the simpler ones (the person, 2026-11-08)
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
### Why
- The person's two jobs here are deciding and shipping: answering a leader's question and sending done work to main.
- §270 puts the decision in the hand as cards one can read at a glance; §274 lets any project ship to main, with or without Release.
- Both rest on bets no one has tested (cards read without the big card, gate tests short enough to wait for): the week must show them.
### Done when
- [test] When the person sends a goal in dev to main from the discard on a project with no Release seated, then the gate's tests run first and main gets the goal only when they are green.
- [test] When one of the gate's tests is red on a goal's way to main, then main is unchanged and the card says, in words, which test stopped it.
- [test] When a project's gate has no tests, then To main is refused in words and *To main without the tests* is offered; only that act skips them, and its event says the tests were skipped.
- [test] When the person lifts a goal card with one open question at 1280 × 800, then each way is a hand card showing its whole line, the leader's pick marked, and the answer's event says hand or Open….
- [person] When the owner's week of use ends, then journals/project.md holds a line on answering from hand cards and sending to main from the discard.
### Checks
- No path reaches main without the gate's tests but the one named act *To main without the tests* (ideas.to_main, _checks_refusal).
- A goal whose checks were never asked no longer goes to main untested.
- Every way on an answer card is its leader's line, readable at rest without hover or focus (§270.5, the person's answer).
- The goal_to_main and goal_answered events keep what the week needs: tests run or skipped, answered from the hand or after Open….
- Release, when seated, still runs its skeleton checks before main and alone releases a version (§274.4).
### Will be
- changed 158-the-window-as-a-table — its two hypotheses (answers from hand cards, To main with the gate's tests) get their signal in the event log and the week's line
### Out
- The table's look: felt, light steps, bronze, pennants, the lamp, the chair and the backpack (§268, §269, §271–§273, a goal of their own).
- The phone (§270.7, a goal of its own).
- The new goal card at the Orkmaster's lane top with its four corners (§270.6).
### Risks
- medium
- The gate's tests may take long enough on a way to main that the person skips them, making the named skip the habit.
- Hand cards may hide a way's cost or consequence that the big card said, so answers get picked blind.
- Tests of 150 and 156 on the same discard and hand files may break while this lands.
### Defaults
- §270.6 (the new goal card's corners) is left out: the person's split named answers as cards and To main, not making a goal.
- The week's signal is the event log read by the owner, not a new counter or screen.
- *Open…* stays on the answer row, so the big card's words are still one press away.
- A skipped-tests To main is still logged as goal_to_main, with a field saying the tests were skipped.

## Design
### Talk
- verdict: doubt — go if the look (§268, §269, §271) is its own step in orkUI first (§269.9), and an answer card's line is read without hover
- stance: Design wants answers as cards (§270) and the three colour layers; felt, bronze, pennants and the lamp are orkUI's work first, a step of their own
- for: §270 cuts the 404 × 566 card no one read to one question and its ways as cards: recognition over recall, one look at what to pick
- against: dithered steps and dark felts under text risk AA contrast; a lamp's chain hides Here/Away in a picture; hover-only lines fail touch and keys
- instead: §270 and §268's colour layers now; felt, light steps, bronze, pennants and the lamp's chain as a goal of orkUI's, then gui/
- assumes: text and signals keep 4.5:1 and 3:1 on every felt, lit and out — shown by: a contrast test over each felt and step, lamp lit and out
### Why
- The 404 × 566 opened card asks the person to read and recall; §270 shows one question and its ways as cards: recognition over recall, one look to pick.
- Cards that show their line only on hover fail touch and the keyboard (WCAG 1.4.13, 2.1.1); the person chose the whole line at rest.
### Done when
- [test] When the person lifts a goal card with one open question at 1280 × 800, then it stays 144 × 202 on the table's foot in its signal's ring, and its goal's card in the column wears the same ring.
- [test] When that card is up, then each way is a 144 × 202 card in the hand showing its name and whole line at rest, the leader's pick marked by its head and in words, not colour alone.
- [test] When the person tabs through a lifted card's answers, then each way, *<Leader> decides*, *Your own words…*, *Open…* and *Put it back* take a ringed focus in turn; Escape puts it back.
- [test] When the person presses *Your own words…*, then a field opens on the table beside the question, focused, with *Send to <leader>* under it.
- [look] When a goal still in Talk is lifted at 1280 × 800, then its table shows its leaders' Talk and its open question with its ways, and the rest of the hand is sunk and grey.
### Checks
- Way cards, the pick's mark and the signal ring draw only orkUI's tokens: text 4.5:1, ring and mark 3:1 (tests/test_design_system.py).
- Under reduced motion a card's rise, the hand's sinking and the answer's flight are at once.
- While a card is up the sunk hand is inert and never takes focus; *Put it back* and Escape return focus to the card that was lifted.
- A way's line is never cut on the card: one too long for it is refused where it is written (§270.5), not ellipsised.
- The pixel face is for a way's name and the buttons only; the leader's line is in the body face.
### Will be
- changed home — the lifted card leaves 404 × 566 for 144 × 202, its answers become hand cards and the rest of the hand sinks (§270.1–§270.5)
### Out
- The table's look: felt, light steps, bronze, pennants, the lamp's chain, the chair and the backpack (§268, §269, §271–§273).
- The phone (§270.7, a goal of its own).
- The new goal card at the Orkmaster's lane top and its four corners (§270.6).
### Risks
- medium
- A way's name and whole line may not fit 144 × 202 at the body size; the type would be shrunk below readable instead of the line shortened.
- Four ways plus *decides*, *Your own words…*, *Open…* and *Put it back* may overflow the hand's width at 1280 px.
- Focus may be lost when the lifted card goes back or the answer flies to the table.
- Hand cards may drop a way's cost the opened card's foot showed, so priced ways are picked blind.
### Defaults
- The window is my map's screen `home` (the page's path `/`); no new screen is made.
- A priced way shows its cost in the card's corner, as *Start again* does; picking it answers, no separate *Answer* press.
- A question with more than one ask keeps *Send the picks* and *Open…* as today; cards are for one question's ways.
- The picture for the [look] line is the camera of docs/mockups/answer-cards/ (shoot.py) pointed at the product.
### Accepted
- met: When the person lifts a goal card with one open question at 1280 × 800, then it stays 144 × 202 on the table's foot in its signal's ring, and its goal's card in the column wears the same ring.
- met: When that card is up, then each way is a 144 × 202 card in the hand showing its name and whole line at rest, the leader's pick marked by its head and in words, not colour alone.
- met: When the person tabs through a lifted card's answers, then each way, *<Leader> decides*, *Your own words…*, *Open…* and *Put it back* take a ringed focus in turn; Escape puts it back.
- met: When the person presses *Your own words…*, then a field opens on the table beside the question, focused, with *Send to <leader>* under it.
- not met: When a goal still in Talk is lifted at 1280 × 800, then its table shows its leaders' Talk and its open question with its ways, and the rest of the hand is sunk and grey. — product-talk.png at 1280 × 800: the lifted card covers the Design lane's ways (cut to "Each…", "One c…"), and the sunk hand is hidden under the ways row, not seen grey

## Tech
### Talk
- verdict: doubt — go once 156's D lands and §274 is a step of its own first: ideas.to_main skips the tests today when none were asked (_checks_refusal)
- stance: Tech builds §274 in the engine (gui/ideas_gate.py, realm/party_recipes.py, project_stage.py), §270 and §273 in table/ and hand/; the look waits for orkUI's copy (§269.9)
- for: To main by code exists (ideas.to_main, main_checks.py's worktree run): §274 makes its tests mandatory and unlocks Release, no new container or caller
- against: one goal rewrites discard.js, column.js, door.js, hand/answers.js and their browser tests while 150 and 156 build the same files; a skip to main built on simpler models
- instead: §274 alone first (the gate's tests in To main's checks, one named act to skip them, Release unlocked); then §270 and §273; the look after orkUI
- assumes: the gate's tests on a goal's way to main end in minutes, not the whole suite — shown by: a To main on this repository, its checks' time in the event log
### Why
- Main is what people run: today ideas.to_main lets a goal through untested when its checks were never asked (_checks_refusal returns ""), so §274's promise is a hole in code.
- §274 moves the one way to main from a party (Release, locked in track_drop and project_stage) to one engine call guarded by the gate, with a single named skip.
- §270 needs the answer's event to say where it was given, or the owner's week has no signal to read.
### Done when
- [test] When ideas.to_main is called for a goal in dev whose checks were never run or not passed for main's head now, then it is refused in words and main's head is unchanged.
- [test] When the gate's Tests check is red on a goal's way to main, then main is unchanged, the worktree is gone, and the refusal names the test that failed.
- [test] When a project's gate has no tests, then To main is refused in words; only ideas.to_main with untested: true sends it, and its goal_to_main event says tests: skipped.
- [test] When the person removes the Release party, then it is removed with no refusal, and a goal in dev still reaches main by ideas.to_main after the gate's tests.
- [test] When the person answers a goal's open question from a hand way card or after Open…, then its idea_answered event carries from: hand or from: open.
### Checks
- Every path to main runs through to_main's refusal: gate_merge and to_main take no goal to main untested but by untested: true, a literal boolean (tests/test_goal_main.py, test_main_checks.py).
- With Release seated, a [gate.main] written by it (the skeletons, §188) still runs before main; only Release's leader releases a version (releases.py unchanged).
- realm/ and core/ import nothing of gui/, and orkboard/gui/ideas_gate.py stays under ~600 lines (tests/test_architecture.py).
- goal_to_main keeps its fields and adds tests: run or skipped, and the checks' time, so the week can read both bets.
- The page's To main and To main without the tests send only these two acts; no other face or command reaches goal_main.merge.
### Will be
- changed orkboard/gui/ideas_gate.py — to_main refuses until the gate's checks pass, one untested act skips them; Release's lock goes from ideas_track.py and project_stage.py
### Out
- The table's look and the discard's move beside the table: felt, light, bronze, pennants, lamp, chair, backpack (§268, §269, §271–§273).
- The phone (§270.7, a goal of its own).
- The new goal card at the Orkmaster's lane top and its four corners (§270.6).
### Risks
- medium
- Making to_main refuse without passed checks breaks callers that send straight (tests, the phone's quick act, CLI) until they ask the checks first.
- The gate's Tests on a trial worktree may take minutes; a slow way to main makes the named skip a habit.
- Unlocking Release touches goal_types.release_party and goal_route's routing; a project without it must not lose dev (§274.1).
- 150 and 156's browser tests on portal.js, discard.js and hand/answers.js may break while this lands.
### Defaults
- The gate's tests are gate_config.main_checks as today (The merge, then Tests or [gate.main]), not the full suite.
- The skip is one argument, untested: true, on ideas.to_main; the page names it *To main without the tests*; nothing else reads it.
- The answer's source is a field from on idea_answered (hand or open), not a new event.
- The hero is the default (Sh.man): Tech keeps no table page for this goal.
### Accepted
- met: When ideas.to_main is called for a goal in dev whose checks were never run or not passed for main's head now, then it is refused in words and main's head is unchanged.
- met: When the gate's Tests check is red on a goal's way to main, then main is unchanged, the worktree is gone, and the refusal names the test that failed.
- met: When a project's gate has no tests, then To main is refused in words; only ideas.to_main with untested: true sends it, and its goal_to_main event says tests: skipped.
- met: When the person removes the Release party, then it is removed with no refusal, and a goal in dev still reaches main by ideas.to_main after the gate's tests.
- met: When the person answers a goal's open question from a hand way card or after Open…, then its idea_answered event carries from: hand or from: open.

## Decisions
§270, §274 (this goal, the person's split of 8 November); §268, §269, §271, §272, §273 a goal of their own, after.
