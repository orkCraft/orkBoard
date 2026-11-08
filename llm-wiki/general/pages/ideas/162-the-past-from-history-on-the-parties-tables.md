---
owner: board
kind: idea
track: product
order: 11
size:
priority: normal
short: The past from history
phase: new
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

## Decisions
