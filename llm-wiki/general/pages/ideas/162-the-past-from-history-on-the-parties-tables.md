---
owner: board
kind: idea
track: product
order: 11
size:
priority: normal
short: The past from history
phase: spec
route: product, design, tech
spec: docs/specs/162-the-past-from-history-on-the-parties-tables.md
by: claude-code
schema: 3
---
# The past from history on the parties' tables

## Gist
I want to run everything through Orkboard from now on and see on the Board what was done before: the goals and decisions of past days in the discard column's past, and on the Product and Design tabs a running list of the closed use cases and of the product's direction.

Today a fresh Orkboard over this repository shows almost nothing of that. A check on main 48c14d3b, reading the Board as a first open does (goal_phase.moved, move_to and seen_at, then realm/chronicle.read with the decisions file's text), gave: 129 pages moved, 120 of them done and seen at once (history, not the discard: that part is right). The past, whole project: 232 decisions in 4 week decks and 0 goals. The past on the product, design and tech tabs: 0 goals and 0 decisions.

Why, in the code:
1. realm/chronicle.py goals() skips a goal with no flag (idea_flag.flag_of). Only Orkboard's gate raises one (gui/ideas_gate.py _raise_flag), so a goal done by an AI tool's skill, by hand or before this machine read it is in no chapter.
2. chronicle.held() reads the route from Orkboard's state only. A page's route: is never read into it (trial 160 F1.2), so a goal is only its track's. 111 of 130 pages are track: tech, and 7 carry route:.
3. chronicle_decisions.parties(state_dir) knows a decision's parties only when Orkboard decided it, so a party's tab drops every decision written outside.

What I expect:
- A goal done outside the window gets its place in the past: a flag by done, dated by the commit that moved its page to done, never by the time of the read. It stays history, not the discard. A flag is never undone.
- A page's route: counts for a party's eyes while the state has none of its own.
- A decision a goal carries is seen by that goal's parties. Whether a decision of no goal gets parties from its text is for Talk.
- Whether to backfill route: on the old pages once is my question.
- The Product tab is where I read the closed use cases and the direction. Product and Design say in Talk what it must show.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- What shows Product's past on its tab? (**Discard's past, tree later** / Discard's past only / The tree in this goal) — Product's tree is kept in .orkcraft/, absent here; the discard's past is built (150 E2) and needs only the readings · Discard's past, tree later: Product's done goals now; a goal of its own lays jobs and direction · Discard's past only: Done goals and their decisions; use cases stay goal titles · The tree in this goal: Jobs and outcome on Product's table; the goal grows by keeping the tree
  - Answered: Discard's past, tree later (the person, 2026-11-08)
- A decision of no goal: whose? (**The Orkmaster's tab only** / By its words, by code) — a party's past that misplaces a decision is worse than a thin one; all 232 stay whole on the Orkmaster's tab · The Orkmaster's tab only: No guessing: a party's past holds what its goals carried · By its words, by code: Every tab fills; a decision may land on the wrong party
  - Answered: The Orkmaster's tab only (the person, 2026-11-08)
- Backfill route: on the history pages? (**Once, one commit you read** / No, route from today on) — 111 of 130 pages are track: tech, so Product's and Design's tabs miss the goals they shaped · Once, one commit you read: 119 history pages gain route:; each party's past fills · No, route from today on: Old goals stay their track's; a party's past starts thin
  - Answered: Once, one commit you read (the person, 2026-11-08)
- How does a long deck deal? (**Seven, then All · search** / Every card in place / A goal of its own) — 232 decisions and 120 goals fill 4 week decks; the line already ends in All · search past seven (§167.5) · Seven, then All · search: Findable: seven in place, the deck over the pane with a search (changes §261.9) · Every card in place: As built: each deck deals whole; one goal is found by scrolling the column · A goal of its own: Fills now: the long deck's reading waits for a goal the person lays later
  - Answered: Seven, then All · search (the person, 2026-11-08)
- How is a history goal dated? (**Its last Spec commit** / The commit that laid it / Its decision's day) — the 119 history pages were laid done by import, not done then; a flag is never undone, so its day is chosen once · Its last Spec commit: Each in the week its last part was built; the laying commit where none · The commit that laid it: As Gist says; the 119 fall in the weeks they were laid, not built · Its decision's day: The log's day; only 45 of 119 carry decisions:, the rest need another
  - Answered: Its decision's day; where its page carries no decisions:, the latest decision (§N) its spec names; where none, the day it was laid. Git dates cannot serve: this repository's history begins on 6 November and all 119 history pages were laid by one commit (20d880cf) on 8 November (the person, 2026-11-08)
- Fold the old goals into living specs? (**No, a quiet flag** / Fold each, as the gate does) — gui/ideas_gate._raise_flag runs a leader's fold, a model call, and a journal line for each goal it flags: 120 at a first open · No, a quiet flag: No call at a first open; the living specs keep what they hold today · Fold each, as the gate does: Living specs gain the old goals; 120 leader calls in the background
  - Answered: No, a quiet flag (the person, 2026-11-08)

## Decisions
- §277: the person's six answers in Talk (8 November 2026)

## Product
### Talk
- verdict: doubt — go once Product's tab shows its discard's past; use cases and direction have no source here: Product's tree is in .orkcraft/, absent, and there is no project.md
- stance: Product backs the three readings: a person bringing a repository with its history trusts the Board when its past is there; the tab's use cases wait for a source
- for: measured, not guessed: 0 goals in the past against 120 done; three fixes in realm/ fill the face goal 150 already built (E1, E2), and every adopted repository gains
- against: without a route backfill Product's past is its own few goals (111 of 130 pages are track: tech); a second list on the tab would repeat the discard's past
- instead: fill the discard's past by the three readings here; a goal of its own keeps Product's tree in the Board, so jobs and direction can be read
- assumes: the person reads Product's past to choose what next, not only to remember — shown by: the past opened on Product's tab before a goal is laid, in the owner's week
### Why
- The person runs everything through Orkboard now; a Board that shows 0 goals in its past over 120 done is not trusted to choose what next.
- Product's tab is where the person reads what was closed (§277.6); today it holds no goal and no decision of its own.
- Measured, not guessed: three readings fill a face already built (spec 150 E2), and every repository brought with its history gains.
### Done when
- [test] When a fresh Orkboard reads this repository after the route backfill, then Product's past holds goal 116 in the week of 26 October 2026 (§194's day), with §194 under it.
- [test] When a fresh Orkboard first reads this repository, then every done page but a release goal is in the whole project's past and none in the discard, with no model call and no journal line.
- [test] When a done page carries no decisions:, then it is dated by the latest §N its spec names, else by the day it was laid; a second read and a phase moved back keep that day and the flag.
- [test] When a party's past is read, then a decision no done goal carries is on no party's tab and stands whole in the past read with no party (the Orkmaster's tab).
- [person] When the owner reads the one backfill commit, then each history page's route: names the parties that shaped it, and Product's tab holds the goals Product shaped.
### Checks
- A page's route: counts only while the state holds no route for the goal; where both are, the state's wins.
- A flag raised by done says so (`by: done`), is never undone and never redated by a later read.
- The backfill is one commit that adds route: to laid: history pages only, no other key or section touched.
- No decision is given a party by its words: a party's decisions are its goals' carried ones and those its leaders decided.
- The discard deals no history goal: a flag by done is history, seen at once.
### Will be
- none — Product's tree (realm/opportunity_tree.py, map `product`) is untouched: its jobs and the direction wait for a goal of their own (§277.6)
### Out
- Product's tree on the tab: jobs, outcome and the product's direction (§277.6, a goal of its own).
- Folding the old goals into the living specs, or any leader's call for them (§277.1).
- Giving a decision of no goal parties by its words (§277.4).
### Risks
- medium
- The backfill's routes are judgments from specs written before parties; a wrong one puts a goal on a tab it did not shape.
- 45 of 119 history pages carry decisions:; the rest are dated by a §N their spec names, which may be cited, not decided, and so later than built.
- Product's past stays thin if the backfill names Product rarely: 11 pages are track: product today, this goal among them.
- 120 flags raised at a first open may slow it; a quiet flag must not wait on the read.
### Defaults
- The backfill names Product where a spec touches the owner's list, the brief, hypotheses, trials or Product's tree; Design where it has a face part; Tech where code was built.
- A page with several decisions: is dated by the newest of them.
- The day it was laid is the laying commit's day (20d880cf, 8 November 2026) for a page with no §N at all.
- The Orkmaster's tab is the past read with no party (chronicle.read with party "").

## Design
### Talk
- verdict: doubt — go once a goal done outside is dealt once, at the discard's top until seen, then in its past: chronicle.goals deals a flagged goal whatever its seen_at
- stance: Design backs the readings: the face is built (spec 150 E2, spec 156 D.5) and fills by itself; no list on a tab, the discard's past through the open tab is the one place (§261.9)
- for: no new screen and no step: the past reads through the open tab's eyes already; a tab's dot takes the newest as seen on its first read, so no tab lights at once
- against: 232 decisions and 120 goals fill 4 week decks; a deck deals whole down a lane-wide column with no search, so one goal is found by scrolling (heuristics 6, 7)
- assumes: the person looks for a past goal by its week, not by its words — shown by: in the owner's week, decks dealt and scrolled to their end, against a past goal looked up by name
### Why
- The readings fill 4 week decks with 232 decisions and 120 goals; a deck dealt whole down a lane-wide column is found by scrolling (heuristics 6, 7).
- §277.5 gives the past the line's way: seven in place, then *All · search*; one face for a long list, learned once (heuristic 4).
- A goal must lie in one place: a history goal dealt twice, or a tab lit by a first read, tells the person something false.
### Done when
- [test] When a deck of the past holding more than seven cards is pressed on Design's tab, then it deals its newest seven and an eighth card *All · search*; a deck of seven or fewer deals whole, with none.
- [test] When *All · search* is pressed, then the whole deck opens over the pane under the deck's name, its search field focused; words narrow it to the cards they are in, and Esc gives the lane back.
- [test] When a goal's card is pressed in that deck over the pane, then the view closes and the goal is picked, the table showing it as it was; a decision's card opens its entry, as from the lane.
- [test] When a fresh Orkboard first opens on this repository, then each history goal's card lies once, in its week's deck, never among the goals done and not yet seen, and no party's tab wears the dot.
- [look] When the Orkmaster's tab is open at 1366 × 768 with a week deck dealt, then its seven cards and *All · search* read as one deck in the lane, the All card the line's own face.
### Checks
- *All · search* is the line's face (cascade.js `table-lstrip--all`): the sign `search`, the words *All · search*, an aria-label naming the deck.
- Keyboard: Tab reaches *All · search*, Enter opens it; Esc and ← close the view and focus goes back to the card that opened it (WCAG 2.4.3, 2.4.7).
- No count of a deck's cards anywhere, in the lane or over the pane; a search that finds nothing says so in words.
- Every new word is in today's word (`TERMS`, `tests/test_gui_wording.py`); the sheets carry no colour, font or corner of their own (`tests/test_design_system.py`).
- The past over the pane opens only from *All · search*: a deck pressed still deals in place (§261.9 as §277.5 changes it).
### Will be
- changed orkboard/gui/static/js/table/pastlane.js — a deck past seven deals its newest seven, then *All · search*, which opens the whole deck over the pane with a search (§277.5)
### Out
- The past on the phone or at the narrow width (§238.6, §261.14).
- Product's tree, jobs and direction on Product's tab (§277.6, a goal of its own).
- Any new list, screen or count on a party's tab: the past stays the discard's (§261.9).
### Risks
- medium
- The deck over the pane brings back a past over the pane that §261.9 took away; opened from anywhere but *All · search*, the two ways to the past return.
- Goals and decisions are dealt goals first (pastlane.js `itemsOf`): the newest seven must be by day across both, or a deck's seven hide its newer decisions.
- A deck of 60 and more cards over the pane is long to scroll; with the search not focused first, the view is the scroll it was meant to end.
- 120 flags raised at a first open may slow the chronicle's read; the lane must draw what it has and not wait on it.
### Defaults
- The deck over the pane is the kind `chronicle` with the deck in its props, no new kind in frame/kinds.js; its title the deck's name through the open tab.
- Its search asks the host (`ideas.chronicle_find`, kept to that deck's cards), so a spec's and a decision's words are found, not titles only.
- The newest seven are by day across goals and decisions; on one day, goals before decisions, as the lane deals them today.
- Will be names the file as the part, since Design's screen map is kept in .orkcraft/, absent here.

## Tech
### Talk
- verdict: doubt — go if a flag by done is raised quiet, its day given by the host: gui/ideas_gate._raise_flag folds specs (a model call) and writes a journal line per goal, 120 at a first open
- stance: Tech builds it in realm/: chronicle reads a page's route: and decisions: keys, idea_flag.raise_flag takes a given day; gui/ideas_phase.phase_moved raises it, no new container
- for: three readers in realm/chronicle*.py, no face and no new caller of gui/; 45 history pages already carry decisions: N, so a carried decision needs no guess
- against: realm/ideas.py is 689 lines, past the 600 split, so the page's route is read in chronicle, not there; the laying commit dates history goals by import, not by build
- assumes: the history pages were laid done by import commits, not built then — shown by: git log --diff-filter=A on pages/ideas: the laid: history pages added in a few commits
### Why
- The past is read by code from a goal's flag, its route and its decision; today Orkboard's own gate and state write all three, so a repository worked by other tools has no past.
- Tech fixes the readers in realm/, not the face: one quiet flag and three readers, no model call, no new container, realm/ideas.py (689 lines, past the split) left as it is.
- A flag is dated once and never undone (§277.1), so its day must be right at its first read.
### Done when
- [test] When phase_moved first reads a page laid done, then its flag is raised once, `by: done`, at the day history_day gives, with no keeper fold, no journal line and no `idea_flagged` event.
- [test] When a Board read before this change opens again, then each done goal with no plan and no flag gets that quiet flag once, and a goal done in dev waiting for the gate gets none.
- [test] When history_day dates a page, then it takes the newest of its decisions: in the log, else the highest §N in the log its spec file names, else the day of the commit that laid it.
- [test] When chronicle.read is asked for a party, then a goal whose page route: names it is in its past while the state has no route, and each decision that goal carries stands under it.
- [test] When chronicle_find is given a deck's id with a query, then it finds only among that deck's goals and decisions in the party's past, and every word must be in an item found.
### Checks
- realm/history_day.py, chronicle.py and idea_flag.py import no gui/ and run no git: the laid day comes from the host's tree (`tests/test_architecture.py`).
- realm/ideas.py is not grown: a page's route: and decisions: are read in chronicle from one `ideas.ideas_and_pages` read of the pages.
- `idea_flag.raise_flag` stays once-only with a given day: a goal that has a flag gets it back unchanged, its `at` and `by` never rewritten.
- `chronicle.last` by party agrees with `chronicle.read`: a decision a party's goal carries is the party's in both; one of no goal is in no party's.
- The gate's `always` and the touched modules' tests pass: test_chronicle, test_idea_flag, test_goal_phase, test_board_tree, test_ideas_chronicle.
### Will be
- new orkboard/realm/history_day.py — a page's day by §277.2: its decisions:, else its spec's highest §N, else the day laid; pure code
- changed orkboard/realm/idea_flag.py — raise_flag takes a given day for a flag by done
- changed orkboard/realm/chronicle.py — held() reads a page's route:, goals() carry its decisions:, a party's decisions include its goals' carried ones
- changed orkboard/realm/chronicle_find.py — a search kept to one chapter, the deck *All · search* opened
- changed orkboard/realm/board_tree.py — the day of the commit that added each page, in one git log
- changed orkboard/gui/ideas_phase.py — phase_moved raises the quiet flag, and once for the done goals read before with none
### Out
- The route backfill's judgments: which parties shaped each history page is Product's line; Tech writes no route: by code.
- Reading a page's route: into the Board's state or realm/ideas.py: it counts in the chronicle only (§277.3).
- The deck's face in pastlane.js and the view over the pane: Design's.
### Risks
- medium
- 120 flags at a first open run in phase_sync on the host's thread; each tally reads the goal's files, so the first read must not hold the snapshot.
- The laid day needs git for each page: read in one `git log --diff-filter=A` over pages/ideas, not 119 calls, or the first open waits.
- A spec's highest §N may be cited, not decided: a goal dated later than built, and the day is never redated.
- The catch-up flags a done goal with no plan: a goal done in Orkboard whose plan was lost would get a flag by done, not by the gate.
### Defaults
- A page whose decisions: names several takes the highest in the log; a §N its spec names counts only when the log holds it.
- The laid day is the author day of the commit that added the page; for a page moved to done after it was read, the day of the commit that moved it.
- The quiet flag's commit is that commit; a history page calls no `collide_released` and logs only `goal_moved_outside`, as today.
- A goal moved to done outside after it was read gets the same quiet flag and §277.2's day; it stays in the discard until seen, as today.
