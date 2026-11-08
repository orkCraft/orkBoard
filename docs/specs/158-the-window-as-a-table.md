# 158. Answers as cards in the hand; To main from the discard after the gate's tests

Decisions §270, §274 (the person's split of 8 November 2026: these two first; §268, §269, §271, §272 and §273, the table's
look and the room's things, are a goal of their own after, orkUI first). **Mockup:** `docs/mockups/answer-cards/` (the
question risen onto the table, the ways in the hand, the Pen's field); `docs/mockups/room-things/` and `table-look/` belong
to the later goal. **The goal's page** `llm-wiki/general/pages/ideas/158-the-window-as-a-table.md` holds the spec: its
leaders' sections (*Product*, *Design*, *Tech*: Why, Done when, Checks, Will be, Out, Risks, Defaults) and the Taskmaster's
*Stages*; this file says what they build in one place and is kept with it.

**Builds:** a stage a Grunt, each in its own worktree, merged into the goal's branch and then into `main` on the critical
tests and the stage's own (CLAUDE.md, alpha). The way to main (A, B, D) on the strong model, the person's answer; the rest on
the simpler ones. Tech first (A–E: Tech's leader asked §274 before anything; the hand's way cards send E's field), then
Design (F–H), then Product's week (I). The page's paths are under `orkboard/gui/static/js/`.

| Stage | What | Where |
|---|---|---|
| **A. To main only after the gate's checks** | a goal whose checks were never asked, or passed for another head of main, is refused in words; a red check names its test | `gui/ideas_gate.py` (`to_main`, `_checks_refusal`, `gate_merge`) |
| **B. The one named skip** | `untested: true` the only skip; a project with no tests refused, *To main without the tests* offered; `goal_to_main` says `tests: run \| skipped` | `gui/ideas_gate.py`, `realm/event_log.py` |
| **C. Release a craft as any** | Release removable, not locked; seated, its checks and its versions as today | `gui/ideas_track.py`, `realm/project_stage.py`, `realm/goal_types.py` |
| **D. The page's To main** | *To main* asks the checks first; the card says which test stopped it; the menu's *To main without the tests* the only face of the skip | `table/tomain.js`, `table/portal.js`, `hand/readycard.js` |
| **E. Where an answer was given** | `from: hand \| open` on `idea_answered` and `goal_answered` | `core/idea_draft.py`, `core/idea_talk.py`, `gui/ideas_phase.py`, `gui/ideas_board.py`, `hand/answers.js` |
| **F. The lifted card and its ways** | 144 × 202 risen onto the table's foot, its column card ringed; each way a hand card, its whole line at rest, the pick by its head and in words; the rest of the hand sunk, grey, inert | `hand/answers.js`, `hand/ways.js`, `hand/wayline.js`, `hand/openedcard.css`, `table/column.js` |
| **G. Your own words and the keys** | the Pen's field on the table, focused; Tab through the ways and acts; Escape back | `hand/` |
| **H. A goal in Talk lifted** | its table lays its leaders' Talk and its open question with its ways; the picture by the mockup's camera | `table/` |
| **I. The owner's week** | a line in `llm-wiki/general/journals/project.md` from the events | the journal |

## Done when

The page's leaders' *Done when* lines, each proved by the stage that names it; the critical tests and each stage's own green.

## Later

The new goal made in the Orkmaster's first lane with its settings at its corners (§270.6); the phone (§270.7); the table's
look and the room's things (§268, §269, §271–§273), a goal of their own.
