---
owner: board
kind: idea
track: product
order: 11
size:
priority: normal
short: The past from history
phase: talk
route: product, design, tech
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

## Product
### Talk
- verdict: doubt — go once Product's tab shows its discard's past; use cases and direction have no source here: Product's tree is in .orkcraft/, absent, and there is no project.md
- stance: Product backs the three readings: a person bringing a repository with its history trusts the Board when its past is there; the tab's use cases wait for a source
- for: measured, not guessed: 0 goals in the past against 120 done; three fixes in realm/ fill the face goal 150 already built (E1, E2), and every adopted repository gains
- against: without a route backfill Product's past is its own few goals (111 of 130 pages are track: tech); a second list on the tab would repeat the discard's past
- instead: fill the discard's past by the three readings here; a goal of its own keeps Product's tree in the Board, so jobs and direction can be read
- assumes: the person reads Product's past to choose what next, not only to remember — shown by: the past opened on Product's tab before a goal is laid, in the owner's week

## Design
### Talk
- verdict: doubt — go once a goal done outside is dealt once, at the discard's top until seen, then in its past: chronicle.goals deals a flagged goal whatever its seen_at
- stance: Design backs the readings: the face is built (spec 150 E2, spec 156 D.5) and fills by itself; no list on a tab, the discard's past through the open tab is the one place (§261.9)
- for: no new screen and no step: the past reads through the open tab's eyes already; a tab's dot takes the newest as seen on its first read, so no tab lights at once
- against: 232 decisions and 120 goals fill 4 week decks; a deck deals whole down a lane-wide column with no search, so one goal is found by scrolling (heuristics 6, 7)
- assumes: the person looks for a past goal by its week, not by its words — shown by: in the owner's week, decks dealt and scrolled to their end, against a past goal looked up by name

## Tech
### Talk
- verdict: doubt — go if a flag by done is raised quiet, its day given by the host: gui/ideas_gate._raise_flag folds specs (a model call) and writes a journal line per goal, 120 at a first open
- stance: Tech builds it in realm/: chronicle reads a page's route: and decisions: keys, idea_flag.raise_flag takes a given day; gui/ideas_phase.phase_moved raises it, no new container
- for: three readers in realm/chronicle*.py, no face and no new caller of gui/; 45 history pages already carry decisions: N, so a carried decision needs no guess
- against: realm/ideas.py is 689 lines, past the 600 split, so the page's route is read in chronicle, not there; the laying commit dates history goals by import, not by build
- assumes: the history pages were laid done by import commits, not built then — shown by: git log --diff-filter=A on pages/ideas: the laid: history pages added in a few commits
