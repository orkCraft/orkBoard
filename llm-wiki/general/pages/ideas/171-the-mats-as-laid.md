---
owner: board
kind: idea
track: design
order: 18
size:
priority: normal
short: The mats as laid
phase: work
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
- [x] A. H7, the hand's belief, in docs/hypotheses.md
  - party: Product. H7 after H6, in their form (*Status*, *The belief*, *What would prove it, what would refute it*, *How we test it*, *If it holds*): the person settles a goal's turns from the hand of moves that wait, not by looking for them on the table. **Holds** when, over the days on `?table=cards`, most moves are played from a hand card (`move_played` with `from: hand`); **refuted** when the person finds what waits by opening mats from the table or the old pane. Its signal `move_played` (idea, kind, from, device), which keeps no word of the person's or a leader's; the days are thin until goal 170's last step turns the cards on (Product's risk), and it says so. Nothing else changes. Tests: tests/test_hypotheses_file.py, tests/test_gui_hypotheses.py.
  - proves: Product's *Will be* (new hyp:h7); Product's check *H7 in docs/hypotheses.md says what holds it, what refutes it and how it is tested, its signal `move_played`…*
- [x] B. The moves that wait: realm/board_turns.py and ideas.turns
  - party: Tech (a simpler model). A new pure `orkboard/realm/board_turns.py` (no git, no model, no write, under 600 lines) reads the Board's pages (`realm/idea_page.py`, `realm/page_talk.py`, `realm/spec_sections.py`) and gives the moves that wait, a list a goal: `asks: person` with an unanswered question (each question a turn with its ways), `phase: talk` with every party of its `route` having its `### Talk` (`page_talk.read_talk`), `phase: spec` with every party of its route having written its section (*Why*, *Done when*); a goal at `work` or `done`, on Hold, or with nothing waiting has none. A new `orkboard/gui/ideas_mats.py` (a class over the Board's `Ideas`, as gui/ideas_say.py's `Say`, with its `mats_commands(self)`) answers `ideas.turns {}` → `{turns: [{goal, kind, at, questions?}]}`, registered by one entry in gui/ideas.py's table. Tests: a new tests/test_board_turns.py on a fixture Board (the four goals of Tech's line; every file's bytes the same after; no model called), tests/test_architecture.py.
  - proves: Tech's "When ideas.turns is asked on a fixture Board, then a goal with asks: person, one at talk with every Talk said and one at spec with every section written each get a turn, one at work none; no model runs, no file is written"; Tech's check *realm/board_turns.py is pure…*; Product's and Tech's default *a move waits when its page says so*
- [x] C. The verdicts and the leaders' tables answered: ideas.verdicts, ideas.tables
  - party: Tech (a simpler model). In gui/ideas_mats.py: `ideas.verdicts {}` gives each goal's tokens, one for each leader of its route that has said its `### Talk`, as `page_talk.read_talk` reads it (verdict, why, stance, for, against, instead, assumes), none for a leader that has not; `ideas.tables {}` gives each party's framework: Tech's Architecture read from this repository's code by a new pure `orkboard/realm/code_layers.py` (tools/record_tables.py's reading moved there, the tool calling it), Product's Jobs to be done from the tree (`realm/opportunity_tree.py`, `tree.json`): its jobs when kept, else its zones empty, each saying who fills it (*Product lays its jobs*; the persona's *Product asks the person who the people are*), never an example. Read only: no model, no lease, nothing spent. Tests: a new tests/test_ideas_mats.py on this repository and on a fixture Board with a tree.
  - proves: Tech's "When ideas.verdicts and ideas.tables are asked on this repository, then each token is a leader's ### Talk as realm/page_talk.py reads it, Architecture is read from its code, Jobs to be done from the tree, no word ending « · example»"; Tech's check *Reading the hand, the verdicts and the tables runs no model, takes no lease and spends nothing*; Product's default *Jobs to be done reads its jobs from the tree… no new store*
- [x] D. One Undo in the history: core/idea_undo.py, ideas.undo and the sealed kinds
  - party: Tech (a simpler model). A new `orkboard/core/idea_undo.py`, the one writer of an Undo record: a closed table of the hand's moves by kind, each one-press kind (Drop, Hold, a question's way, and any other the hand offers) with its reverse, each other sealed (Merge into main, Send to a branch, Ship a release, a paid pass); no kind is neither. A one-press move played keeps the page's bytes before and after in `<state_dir>/goals/<slug>/undo.json`, written through the Board's tree (`realm/board_tree.py`), and publishes on the bus (`core/bus.py`), no toast. In gui/ideas_mats.py: `ideas.undo {idea}` puts the bytes back only while the page is still the after, else refuses in plain words (*It changed since: nothing undone*) and changes nothing; `ideas.take_back {slug}` is a Drop's Undo. The moves' own commands (`ideas.drop`, `ideas.queue` for Hold, `ideas.answer`) are wrapped where gui/ideas.py's `guarded` runs a command (one line calling ideas_mats): it keeps the Undo and logs `move_played` (idea, kind, from: `hand` or `mat` as the page sends it, device); a sealed kind is refused unless the page sends its seal (`sealed: true`). `move_played` and `move_undone` join realm/event_log.py's closed `EVENTS`, never a word. Tests: a new tests/test_idea_undo.py (Drop, Hold and a question's way each undone byte for byte; a page changed since refused, unchanged; every kind one-press with its reverse or sealed), tests/test_event_log.py.
  - proves: Tech's "When a one-press move (Drop, Hold, a question's way) is played and then ideas.undo is asked, then the goal's page is byte for byte as before; if the page changed since, Undo refuses, says so and changes nothing"; Tech's "When the hand's ways are listed by kind, then each one-press kind has its reverse in core/idea_undo.py and each other is sealed…"; Product's fourth and fifth lines (the host's half); Tech's checks *Only core/idea_undo.py writes an Undo record…* and *move_played and move_undone join realm/event_log.py's closed EVENTS…*
- [x] E. ideas.reply and ideas.ask_leader answered
  - party: Tech (a simpler model). In gui/ideas_mats.py: `ideas.reply {slug, leader, text}` (the person's reply to a leader's token on a goal) and `ideas.ask_leader {slug, leader, text}` or `{party, framework, card, text}` (a leader not on the card, or a part of a leader's framework) served by core/idea_ask.py's call (`keeper.board_ask`, the goal or the part named in the question), no new keeper. Each is a paid pass: sealed in D's table, the page saying its cost on its tool's potion before it runs; the answer comes back as the token's slip, kept in the leader's journal as idea_ask keeps it. Refusals are idea_ask's, in plain words. Tests: tests/test_ideas_mats.py (the call begun with the goal named; refused unsealed; its cost said first; the model faked as the idea_ask tests fake it).
  - proves: Tech's check *ideas.reply and ideas.ask_leader say their cost before the pass runs*; Product's fourth line's *a paid pass moves only on its seal*; Tech's *Will be* (gui/ideas_mats.py with the cards' commands, one line in gui/ideas.py)
- [x] F. The page reads the host: proposed() gone
  - party: Tech (a simpler model). `proposed()` leaves js/link.js and every reader of it in js/cards and js/hand: cards/verdict.js reads `ideas.verdicts`, cards/tables/state.js reads `ideas.tables` (tables/jtbd.js lays an empty zone with who fills it, never an example), around.js's reply and ask send E's commands with their cost and seal; what only a mat of its own goal reads lies empty, saying who fills it (Tech's *Out*): the costs (hand/turncards.js, cards/dealer.js, spreads/cost.js), the order (spreads/duel.js), the battles (spreads/battle.js, hand/turnstops.js) and the dropped (cards/dropped.js, this page's own drops kept). pwa/shell-proposals.js's `proposed(core)` is another thing and stays. Tests: a new tests/test_cards_no_mock.py that reads js/ and pwa/ (no `proposed(` from link.js; nothing reached off `?mock=1` imports js/mock/), and a browser test on tests/browser_kit.py's `gui` fixture with `?table=cards`, no `?mock=1` (nothing fetched under js/mock/ or static/mock/; Jobs to be done's zones empty with who fills them; no « · example» on the page).
  - proves: Tech's "When the table of cards opens (?table=cards) on a fixture Board, no ?mock=1, then the page fetches nothing under js/mock/ or static/mock/, js/link.js has no proposed(), and each part it reads is a host's answer"; Product's "When the table of cards opens (?table=cards) on a Board that keeps no job, as this repository's, then Product's Jobs to be done lays its zones empty, each naming who fills it, and no word on the page ends in « · example»"; Tech's check *Off ?mock=1 the page imports nothing of js/mock/…* (its first half)
- [x] G. js/mock the tests' fixtures, recorded from a real host
  - party: Tech (a simpler model). js/mock/parts/ goes (examples, spreads, tables, verdicts, turns, kit): js/mock/mocklink.js answers only the host's own command names, from a recording of a real host; tools/record_mock.py records `ideas.turns`, `ideas.verdicts` and `ideas.tables` too and is run on this repository (static/mock/board.json); static/mock/tables.json and tools/record_tables.py's mock output go, the tool kept only if it still serves the recording. The 14 `?mock=1` browser tests (tests/test_cards_*_browser.py, tests/test_mock_link_browser.py) read the recording, never an example; what one of them pressed that only an example laid (a goal for main, a battle, a dropped goal) is laid by that test itself, in the recording it serves or on the `gui` fixture's Board. Tests: the 14 browser tests green; a test that js/mock/ answers no command name the host has not (gui/ideas.py's table read).
  - proves: Tech's check *on ?mock=1, js/mock/ answers only the host's own command names, never a part the host has no command for*; Tech's risk on the contract tested against itself (each name checked against the host's table); Tech's *Will be* (js/mock the browser tests' fixtures only)
- [x] H. The mat's frame as a playmat, and its seal
  - party: Tech (a simpler model). A new js/cards/matframe.js with its sheet takes over spreads/shell.js's `SpreadFrame` and the leaders' tables' frame (tables/index.js), so every mat opened lies in one frame (§300.15, the shots battle-2 and gate): its owner's felt with its bronze frame (orkUI's `.ork-table[data-party]`), its head and every word on a plate (`.ork-plate`), a card, a zone's label or a button, its zones printed in bronze (`--ork-bronze*`) with their labels on the frame and an empty zone's sign faint inside, the phases along its foot only where it is about one goal (the gate, the battle), the emblem's place under the zones left empty. Its seal at its foot's right for D's sealed kinds (Merge into main, Send to <branch>, Ship <release>, a paid pass): dim with its why until a way is picked, told by its rim and its why, never by opacity, its words 4.5:1 either way; pressed it sends the move with `sealed: true`. A mat open is a dialog over the pane: the table, the discard and the head inert and dimmed; Tab goes through its head, its zones' cards, its ways, the seal and Close, each with its word and a visible focus; Esc closes it, the focus back on the card that opened it. Labels 12 px at least; orkUI's tokens only, no gradient, no blurred shadow, no motion under prefers-reduced-motion. *seal* enters realm/lexicon.py `TERMS` with this code. Today's spreads and tables lie in it as they are (Design's default). Tests: tests/test_cards_mat_browser.py (felt, plates, zones' labels, the table inert, the seal dim then lit, Tab's order, Esc's focus), tests/test_design_system.py, tests/test_gui_wording.py.
  - proves: Design's "When the person opens a mat at 1440×900 … then it lies on its owner's felt, every word on a plate or a card, its zones labelled on their frame, the table under it dimmed and inert" (the desk's half); Design's "When a mat is open and the person goes by keys alone…" (but the hand's ways, K); Design's "When a mat whose move cannot be undone … is open, then its seal lies at its foot's right, dim with its why until a way is picked, its words 4.5:1 either way" (the seal's half); Design's checks *No word on the felt alone*, *The felt, the bronze and the plates are orkUI's…* and *The mockup's 10 and 11 px labels … are 12 px at least…*
- [x] I. A mat's address; on the phone the whole screen
  - party: Tech (a simpler model). A mat opened has its address (its goal and its seat, §299.3) in the page's URL, so a reload, a phone's Back, the feed and the journal open it; Esc or Back takes the address off and closes it. On a phone (card.js's `narrow()`, ≤700 px) a mat opens as the whole screen with *Back* in its frame, no sideways scroll, in place of today's fall back to an L of words (§300.16). An opened card (L) shows no row of its mats: one line says where it lies now, its address, and pressed it opens that mat (§300.3). Tests: tests/test_cards_mat_browser.py at 390×844 (a mat opened, the page reloaded on its address and the mat open again, Back closing it, no sideways scroll), tests/test_cards_phone_browser.py.
  - proves: Design's "When the person opens a mat at 1440×900, or at 390×844 from its address after a reload, then … on the phone the whole screen with Back, no sideways scroll" (the phone's half); Design's third line's *Esc or Back closes it and the focus is on the card that opened it* (Back's part); Tech's *Will be* (js/cards: the mat's address)
- [x] J. The closed mats' slots and the three kinds of card
  - party: Tech (a simpler model). In cards/mat.js the small shape beside a closed mat's line goes; a closed mat (an M that is a mat) lays its layout's slots faint behind its words (§299.5, §300.1; the shot closed): thin dashed outlines in orkUI's frame, `aria-hidden`, each layout its own (two cards for *What changed* and compare, a layer and rows for Architecture, columns for Jobs to be done, one against two for the battle, a row for the stages), three at its right where its words leave under a third of its height; a word has none. Every card drawn on a mat is a goal, a decision or a part, its top right corner saying which by its sign and in its accessible name; nothing else is drawn as a card (§300.4: a check is the decision it guards, a price an act, a stage a line of its card's L). Tests: tests/test_cards_mat_browser.py at 1440×900 (slots behind each closed mat's words, aria-hidden, three at the right where little is left, none on a word, no shape beside a line; each card's kind in its corner and its name).
  - proves: Design's "When the table of cards opens (?table=cards) at 1440×900 as the person first meets it, then each closed mat lays its layout's slots faint behind its words, aria-hidden, three at its right where under a third is left; a word has none, and no shape beside a line is left"; Design's check *Every card on a mat is a goal, a decision or a part…*; Tech's *Will be* (js/cards: the slots closed, the three kinds of card)
- [x] K. The hand: a card for each move that waits, and the open mat's ways
  - party: Tech (a simpler model). On the table of cards hand/turnstops.js reads `ideas.turns` (asked once a refresh, as `ideas.feed` is) in place of the proposed turns: one card a goal that waits for the person, grouped by goal, pressed it lifts its ways (a question's) or opens the mat its move lies on; the other Needs you kinds keep their rows as today (Tech's default). While a mat is open the hand is that mat's ways only, a fan (§302.1, §302.4: the battle's, the gate's, a turn's, a question's), moved out of the frame's foot (H), and the mat's focus takes in the hand; the moves that wait lie as a pile at the hand's left by its thickness, never a number, pressed they come back; the mat closed, every card is back. A move pressed sends its command with `from: hand` or `from: mat`; a one-press move's toast says what it did with *Undo* (`ideas.undo`, its refusal said as the host says it); a sealed one goes only on its seal. The Undo's words enter `TERMS`. Tests: tests/test_cards_hand_browser.py on the `gui` fixture with `?table=cards` (the fixture goals that wait each one card, none for a goal that waits for nobody; a mat opened then closed, none lost; Drop then Undo, the page as before; `move_played` in the event log with its `from`), tests/test_cards_turns_browser.py.
  - proves: Product's first, second and fifth lines, and its fourth line's page half; Design's third line's *the hand's ways*; Design's fourth line's *any other move's way is one press, its toast saying what it did with Undo*; Product's checks *Every card in the hand traces to a field of a goal's page…* and *No count of what waits…*; Tech's *Will be* (js/cards: the hand following the mat open)
- [x] L. The mats in the fit test at three sizes
  - party: Tech (a simpler model). tests/test_cards_fit_browser.py's `SURFACES` gain an open mat (its felt and its seal), a closed mat's M and the hand with a mat open, each at 1280×800, 1440×900 and 390×844: no text under 12 px, 4.5:1 on its ground, no act clipped, Tab reaching every act with a visible focus. What fails is fixed in matframe's sheet, mat.js's or the hand's, orkUI's tokens only; a zone squeezed at 390 gives its label a line of its own, never a way clipped. The gate on the step: tests/test_architecture.py, tests/test_board_alone.py, tests/test_updates.py green, no module the step touched past 600 lines, gui/ideas.py and gui/board_host.py grown by one line at most.
  - proves: Design's check *Each mat surface in tests/test_cards_fit_browser.py at 1280×800, 1440×900 and 390×844…*; Tech's check *tests/test_architecture.py: core and realm import no gui; … gui/ideas.py and gui/board_host.py grow by one registering line at most*
- [x] L2. Tech's not accepted: a question's way with no pass, and no paid pass as one-press
  - party: Tech (a simpler model). A question's way played from the hand writes the person's answer under its question with no pass begun, as gui/ideas_phase.py `outside_answer` does, its Undo through core/idea_undo.py, tested played through its command (`from: hand`) and undone byte for byte; a test plays every command of gui/ideas_mats.py's one-press table with `keeper.call` faked to fail and finds no model reached; a one-press kind it catches moves to the sealed table with its cost said.
  - proves: Tech's *Done when* lines 4 and 5, made again
- [x] L3. Tech's not accepted, the second time: every question's way dealt on the table of cards is one press or sealed
  - party: Tech (a simpler model). On ?table=cards a goal whose question is an old Needs-you card (asks, goal, talk or cause: hand/data.js) gets its turn card from ideas.turns instead, so no way the hand deals there sends ideas.talk_answer or ideas.answer (a pass); every question's way there is ideas.answer_way, one press with its Undo, and a leader's pass after it a sealed move with its cost said. Tested on the gui fixture's real host, no ?mock=1, not on a turn laid by hand.
  - proves: Tech's *Done when* line 5, made again (the last time: what is still not met goes under Not accepted)
- [ ] M. Tech accepts the step
  - party: Tech. Its pass of its own (its role file, its section, the gate's record of B to L, the files they changed), against its *Done when* and *Will be*; what it does not accept is one more stage, twice at most.
  - proves: Tech's *Done when* and *Will be*, accepted
- [ ] N. Design accepts on pictures
  - party: Design. The real page drawn at 1440 and 390 (an open mat with its seal, closed mats, the hand with no mat open and with one): laid beside closed, hand and battle-2 (desk and phone) in docs/mockups/mats/shots, the frame unchanged (§104.0, §145); its *Done when* tests and checks read on the gate's record; what it does not accept is one more stage, twice at most.
  - proves: Design's "When the frame, a closed mat and the hand are drawn on the real page at 1440 and 390, then laid beside closed, hand and battle-2 … they read as drawn"; Design's *Done when* and *Will be* (changed home), accepted
- [x] N2. Design's not accepted: zones on the track mat, the hand's titles whole, the gate unscaled on the phone, the fit test measuring a mat's words
  - party: Tech (a simpler model). The track mat lays its done, now and to come as Zones labelled on their frame (`.mf-zl`), the phases' row on a plate (tested in tests/test_cards_mat_browser.py on an open mat); a crowded hand at 1440 keeps each card's title whole from its first letter, the places still in the window (handcards.css `.hand-slot`); the gate mat at 390 is laid unscaled, its words 12 px at least drawn, no check cut at the screen's edge, in the fit test at 390 measuring the size drawn; the fit test's ground() stops at an opaque plate or card so a mat's words are measured at 4.5:1.
  - proves: Design's *Done when* lines 2 and 5, made again
- [x] N3. Design's not accepted, the second time: the track mat's zone whole at 390
  - party: Tech (a simpler model). The track mat's field starts at its top as the gate's does, so its zone's label and meeple lie whole on the zone's frame at 390×844; tests/test_cards_mat_browser.py checks the zone labels at 390 too; the fit test flags a word cut off by its field instead of skipping it.
  - proves: Design's *Done when* lines 2 and 5, made again (the last time: what is still not met goes under Not accepted)
- [ ] O. Product accepts the step
  - party: Product. Its pass of its own (its role file, its section, the gate's record of A to L, the files they changed), against its *Done when* and *Will be* (H7); what it does not accept is one more stage, twice at most.
  - proves: Product's *Done when* and *Will be*, accepted

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
### Why
- Product answers what the person decides; the hand is where those decisions wait, so a move the hand misses or invents is a decision lost or a false one.
- §301 ends the examples: a table that shows the project's own data, or says plainly who fills an empty zone, is the studio that sees your real product (H1), not a mock of one.
- It rests on a belief no one has shown (Talk's assumes), so Product writes it as H7 with its signal, never as a reason to build more.
### Done when
- [test] When the table of cards opens (?table=cards) as the person first meets it, then each fixture goal that waits for the person (a question, its Talk all said, its spec all written) is one card in the hand, grouped by goal, and a goal waiting for nobody has none
- [test] When the person opens a mat from its hand card and closes it again, then while it is open the hand holds that mat's ways only, and once it is closed every card of the moves that wait is back, none lost
- [test] When the table of cards opens (?table=cards) on a Board that keeps no job, as this repository's, then Product's Jobs to be done lays its zones empty, each naming who fills it, and no word on the page ends in « · example»
- [test] When the person presses a one-press move (Drop, Hold, a question's way) and then Undo, then the goal's page is byte for byte as before; Merge into main, Send to a branch, Ship a release and a paid pass move only on their seal
- [test] When the person plays a move from a hand card or from its mat, then the event log keeps `move_played` with the goal, the move's kind and where it was pressed (hand or mat), never a word, so H7 can be counted
### Checks
- Every card in the hand traces to a field of a goal's page (phase, asks, gate, a Talk or section part); reading the hand runs no model and spends nothing (§301.2).
- No count of what waits: the moves that wait lie as a pile at the hand's left by its thickness, never a number (§302.1, CLAUDE.md).
- Merge into main is the person's press only: no pass, timer or night run presses it, and its seal says it goes into main (§301.3).
- H7 in docs/hypotheses.md says what holds it, what refutes it and how it is tested, its signal `move_played`, which keeps no word of the person's or a leader's.
- The seal's and Undo's words say plainly what happens and enter `realm/lexicon.py` `TERMS` with the code that draws them (§300.17, CLAUDE.md).
### Will be
- new hyp:h7 — the belief the hand rests on (the person settles a goal's turns from the hand of moves that wait, not by looking on the table), its signal `move_played`, in docs/hypotheses.md
### Out
- Each mat of its own goal: Discussion, compare, the battle and gate, the discard, the project's deck, the backpack and team, the frameworks' mats, the story map, the history book; Run's chart (§300.11).
- A zone narrowing the hand to its kind and the blank *New <kind>* card (§302.2, §302.3): the project's deck's goal.
- The persona card and Product's question to the person that makes it (the first answer above): the project's deck's goal; here its zone only says who fills it.
### Risks
- risk: medium
- The hand read from the files may miss a move the old Needs you rows hold (a hearing, a fork, a collision, a sign-in); a turn not in the hand is a decision the person never meets.
- Behind ?table=cards the person keeps the old table by default; H7's signal comes only from days on the cards, thin until goal 170's last step turns them on.
- On this repository the zones lie empty (no job, no persona kept): the person may read the table as broken, not as Product's to fill.
- An Undo after another move changed the same page cannot put it back byte for byte; it must say so, never undo half.
### Defaults
- A move waits when a goal's page says so: `asks: person`, its route's Talk all said at `talk`, every section written at `spec`; the other Needs you kinds keep their stops as today.
- H7 is the next free number (H1 to H6 taken); `move_played` (idea, kind, from, device) joins `realm/event_log.py`'s closed list.
- Product's Jobs to be done reads its jobs from the tree (§172, `tree.json`) and its persona from the person's answer to Product's question: no new store.
- Undo is the history's (§302.4, the fifth answer above): a move another has changed since cannot be undone, and says so.

## Design
### Talk
- verdict: doubt — go only if each mat lands in a stage of its own, in test_cards_fit_browser.py's surfaces and accepted on its pictures beside its shot; on weaker models a mat drifts unseen
- stance: Design wants the mats: one layout a kind, one move at its foot's right, learnt once on both faces; held to its 44 shots a mat at a time, read in one order by keys and a screen reader
- for: A mat is known by its layout, its move always at its foot's right (Nielsen 4, 6); an opened card loses its row of mats (8); no total on a battle; every gesture a button with its word and a key
- against: The seal makes a mat's move two presses and the hand's one (§300.2, §300.15; Nielsen 4, 7); the phone's battle shot lays the seal before its ways, its ways turned (WCAG 2.4.3, §300.15)
- instead: The mats on a goal's path first (hand, Discussion, battle and gate, discard), each accepted on desk and phone pictures; the grid, scheme, flow and backpack once those pass
- assumes: a closed mat is told by its faint slots alone at an M's size (§300.1) — shown by: on ?mock=1 at 1440 the person names five closed mats' kinds with their lines covered
### Why
- A mat is where the person has a move: one frame, its layout and its move at its foot's right, learnt once on every mat and on both faces (Nielsen 4, 6); a frame drawn twice is ten mats learnt ten times.
- The felt's dither is an image ground the contrast check skips, so the frame decides whether a mat's words can be read at all (WCAG 1.4.3) and whether keys and a screen reader go through it in one order (2.1.1, 2.4.3).
- Only a move that cannot be undone asks twice (the person's answer): the seal guards it, every other move is one press with its Undo at hand (Nielsen 3, 5).
### Done when
- [test] When the table of cards opens (?table=cards) at 1440×900 as the person first meets it, then each closed mat lays its layout's slots faint behind its words, aria-hidden, three at its right where under a third is left; a word has none, and no shape beside a line is left
- [test] When the person opens a mat at 1440×900, or at 390×844 from its address after a reload, then it lies on its owner's felt, every word on a plate or a card, its zones labelled on their frame, the table under it dimmed and inert; on the phone the whole screen with Back, no sideways scroll
- [test] When a mat is open and the person goes by keys alone, then Tab reaches its head, its zones' cards, the hand's ways, the seal and Close, none of the dimmed table, each with its word and a visible focus; Esc or Back closes it and the focus is on the card that opened it
- [test] When a mat whose move cannot be undone (Merge into main, Send to <branch>, Ship <release>) is open, then its seal lies at its foot's right, dim with its why until a way is picked, its words 4.5:1 either way; any other move's way is one press, its toast saying what it did with Undo
- [look] When the frame, a closed mat and the hand are drawn on the real page at 1440 and 390, then laid beside closed, hand and battle-2 (desk and phone) in docs/mockups/mats/shots they read as drawn: the felt, bronze zones and their labels, plates, the seal, the phases, no new colour
### Checks
- Each mat surface in tests/test_cards_fit_browser.py at 1280×800, 1440×900 and 390×844: no text under 12 px, 4.5:1 on its ground, no act clipped, Tab reaching every act with a visible focus (the person's answer).
- No word on the felt alone: every word of a mat lies on a plate, a card, a zone's label or a button, so its ground is a colour the check measures.
- The felt, the bronze and the plates are orkUI's (`.ork-table[data-party]`, `.ork-plate`, `--ork-bronze*`): no colour, font or corner of Orkboard's own, no smooth gradient, no blurred shadow (tests/test_design_system.py); cards dealt with no motion under prefers-reduced-motion.
- Every card on a mat is a goal, a decision or a part, its top right corner saying which by its sign and in its accessible name; nothing else is drawn as a card (§300.4).
- The mockup's 10 and 11 px labels (a zone's, the phases, a cost to undo, a way's line) are 12 px at least; the dim seal is told by its rim and its why, never by opacity.
### Will be
- changed home — every mat laid as a playmat over the pane (the felt, plates, zones, the seal, the phases), the closed mats' slots behind their words, the hand following the mat open; on the phone a mat is the whole screen
### Out
- Each mat's own layout and move (Discussion, compare, the battle and the gate, the discard, the deck, the backpack and team, the frameworks' mats, the story map, the book): their goals; here the frame they lie in.
- A zone narrowing the hand to its kind and the blank *New <kind>* card (§302.2, §302.3): the project's deck's goal.
- The mats' cartoon pictures and emblems (§301.5, N1, E1 to E3): the emblem's place is laid, empty until orkUI's copy has them.
### Risks
- risk: medium
- The felt's dither is an image ground tests/test_cards_fit_browser.py skips: a word laid on the felt alone passes unmeasured (WCAG 1.4.3).
- The mat makes the table inert yet the hand must stay live under it: a focus trap of the mat alone loses the hand's ways to keys, none lets Tab wander into the table.
- At 390 the frame's rim, the zones' labels and the hand's row may leave a zone no room: a zone squeezed under its label, a way clipped.
- Simpler models drift from the shots: the mockup's 10 and 11 px labels and its seal dimmed by opacity .45 built as drawn.
### Defaults
- Today's spreads and tables (js/cards/spreads/, js/cards/tables/) lie in the frame as they are; each one's own layout and move change in its goal.
- A mat open is a dialog over the pane whose focus takes in the hand under it; the table, the discard and the head are inert and dimmed.
- After a one-press move its toast says what it did with Undo, as the host's toasts do now; the history keeps the Undo after the toast goes, so its seconds take nothing away (WCAG 2.2.1).
- The phases lie along a mat's foot only where it is about one goal (the Discussion, the battle, the gate); the emblem's place under the zones stays empty until orkUI has it.
### Accepted
- met: When the table of cards opens (?table=cards) at 1440×900 as the person first meets it, then each closed mat lays its layout's slots faint behind its words, aria-hidden, three at its right where under a third is left; a word has none, and no shape beside a line is left
- met: When the person opens a mat at 1440×900, or at 390×844 from its address after a reload, then it lies on its owner's felt, every word on a plate or a card, its zones labelled on their frame, the table under it dimmed and inert; on the phone the whole screen with Back, no sideways scroll
- met: When a mat is open and the person goes by keys alone, then Tab reaches its head, its zones' cards, the hand's ways, the seal and Close, none of the dimmed table, each with its word and a visible focus; Esc or Back closes it and the focus is on the card that opened it
- met: When a mat whose move cannot be undone (Merge into main, Send to <branch>, Ship <release>) is open, then its seal lies at its foot's right, dim with its why until a way is picked, its words 4.5:1 either way; any other move's way is one press, its toast saying what it did with Undo
- met: When the frame, a closed mat and the hand are drawn on the real page at 1440 and 390, then laid beside closed, hand and battle-2 (desk and phone) in docs/mockups/mats/shots they read as drawn: the felt, bronze zones and their labels, plates, the seal, the phases, no new colour

## Tech
### Talk
- verdict: doubt — go only if each one-press move has its reverse in one Undo part over realm/event_log.py, or carries the seal; the host's Undo is a few toasts, no history
- stance: Tech lays the frame, the address, the hand and the three kinds on js/cards; the mats' commands in a gui module of their own, served by core and realm; js/mock for tests only
- for: One contract: the cards read seven parts only the mock holds and send eight commands no host answers (ideas.tables, ideas.reply…); verdicts are read free (realm/page_talk.py)
- against: js/cards is goal 170's stage T, built, never accepted, D to J open; gui/ideas.py (775 lines) and board_host.py (805) past 600; 14 browser tests open ?mock=1
- instead: The host's half first: the hand's turns and the verdicts answered, ideas.reply and ideas.ask_leader taken, proposed() gone from js/link.js; the felt and seal after 170's T
- assumes: every move that waits is read from the Board's files (phase, asks, gate, Talk), no leader's pass — shown by: ideas.turns on this repository lays the hand ?mock=1 shows, no model run
### Why
- §301.1 makes the mock's contract the host's: the cards read seven parts only js/mock/parts lays and send eight commands no host answers, so today every mat shows a recording, not this Board.
- The person's Undo «историями оркборда» (§302.4) needs each one-press move's reverse kept by core with one writer, not a toast's seconds; a move it cannot reverse carries the seal.
- gui/ideas.py (775) and gui/board_host.py (805) are past 600: the mats' commands come in a module of their own, read from realm, so the goal adds no caller to a hotspot.
### Done when
- [test] When the table of cards opens (?table=cards) on a fixture Board, no ?mock=1, then the page fetches nothing under js/mock/ or static/mock/, js/link.js has no proposed(), and each part it reads is a host's answer
- [test] When ideas.turns is asked on a fixture Board, then a goal with asks: person, one at talk with every Talk said and one at spec with every section written each get a turn, one at work none; no model runs, no file is written
- [test] When ideas.verdicts and ideas.tables are asked on this repository, then each token is a leader's ### Talk as realm/page_talk.py reads it, Architecture is read from its code, Jobs to be done from the tree, no word ending « · example»
- [test] When a one-press move (Drop, Hold, a question's way) is played and then ideas.undo is asked, then the goal's page is byte for byte as before; if the page changed since, Undo refuses, says so and changes nothing
- [test] When the hand's ways are listed by kind, then each one-press kind has its reverse in core/idea_undo.py and each other is sealed (Merge into main, Send to a branch, Ship a release, a paid pass): no kind is neither
### Checks
- tests/test_architecture.py: core and realm import no gui; realm/board_turns.py is pure (no git, no model, no write); each new module under 600 lines; gui/ideas.py and gui/board_host.py grow by one registering line at most.
- Off ?mock=1 the page imports nothing of js/mock/ (a test reads js/ and pwa/); on it, js/mock/ answers only the host's own command names, never a part the host has no command for.
- Reading the hand, the verdicts and the tables runs no model, takes no lease and spends nothing (§301.2); ideas.reply and ideas.ask_leader say their cost before the pass runs.
- Only core/idea_undo.py writes an Undo record; it publishes on the bus (core/bus.py), shows no toast, and every new command answers keys and data, a refusal in plain words.
- move_played and move_undone join realm/event_log.py's closed EVENTS with idea, kind and from only, never a word (Product's H7 signal).
### Will be
- new orkboard/gui/ideas_mats.py — the cards' commands (ideas.turns, ideas.verdicts, ideas.tables, ideas.undo, ideas.reply, ideas.ask_leader, ideas.take_back), one line in gui/ideas.py
- new orkboard/realm/board_turns.py — the moves that wait, read from the pages (phase, asks, gate, Talk): the hand's one source, pure
- new orkboard/core/idea_undo.py — each one-press move's reverse kept in the history, its one writer, publishing on the bus
- changed orkboard/realm/event_log.py — move_played and move_undone in its closed list
- changed orkboard/gui/static/js/link.js — proposed() gone: js/cards and js/hand read the host's answers
- changed orkboard/gui/static/js/cards — the mat's frame, its address and slots closed, the hand following the mat open, the three kinds of card
- changed orkboard/gui/static/js/mock — the browser tests' fixtures only, answering the host's commands from a recording of a real host
### Out
- Each mat's own move and what it alone reads (ideas.battle_settle, ideas.sort, ideas.order, ideas.tool_for; costs, battles, order): their mats' goals; meanwhile those zones lie empty, saying who fills them.
- The project's deck as a host part and a zone narrowing the hand (§300.12, §302.2, §302.3): the deck's goal.
- The old table and its Needs you rows retired, cards/on.js flipped: goal 170's last step (§296.10).
### Risks
- risk: medium
- An Undo that writes a page beside the Board's tree (realm/board_tree.py) is lost at its next flush or commits half: the reverse must go through the Board's one writer.
- The hand read from the pages may disagree with the old Needs you rows (realm/board_map.py) on one goal: two readers of one turn, one of them wrong.
- With tools/record_mock.py re-recorded, the 14 ?mock=1 browser tests may pass on a recording the host no longer answers: the contract tested against itself.
- gui/ideas.py and gui/board_host.py are hotspots: a weaker model may add the commands there rather than in gui/ideas_mats.py.
### Defaults
- A move waits when its page says so (asks: person; every route's Talk said at talk; every section written at spec), as Product's; the other Needs you kinds stay the old rows' until goal 170's last step.
- Undo keeps a page's bytes before and after in `<state_dir>/goals/<slug>/undo.json`, written through the Board's tree, and reverses only while the page is still the after; ideas.take_back is a Drop's Undo.
- ideas.reply and ideas.ask_leader are served by core/idea_ask.py's call (a model's pass, its cost said before it runs): no new keeper.
- ?mock=1 stays the browser tests' door: js/mock/ answers the host's own commands from a recording of a real host (tools/record_mock.py), never proposed(); off it the page imports nothing of js/mock/.
### Accepted
- met: When the table of cards opens (?table=cards) on a fixture Board, no ?mock=1, then the page fetches nothing under js/mock/ or static/mock/, js/link.js has no proposed(), and each part it reads is a host's answer
- met: When ideas.turns is asked on a fixture Board, then a goal with asks: person, one at talk with every Talk said and one at spec with every section written each get a turn, one at work none; no model runs, no file is written
- met: When ideas.verdicts and ideas.tables are asked on this repository, then each token is a leader's ### Talk as realm/page_talk.py reads it, Architecture is read from its code, Jobs to be done from the tree, no word ending « · example»
- met: When a one-press move (Drop, Hold, a question's way) is played and then ideas.undo is asked, then the goal's page is byte for byte as before; if the page changed since, Undo refuses, says so and changes nothing
- met: When the hand's ways are listed by kind, then each one-press kind has its reverse in core/idea_undo.py and each other is sealed (Merge into main, Send to a branch, Ship a release, a paid pass): no kind is neither
