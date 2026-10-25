# Spec 82 — The field at a glance: a row is what runs at once

The owner, 25 October (decisions §99), testing: which card is at work is not seen; once every card said *wait*; the
members' frames are narrower than their columns; later cards should lie lower, the first row what is done now and
depends on nothing; a card at work needs something that turns; a new card comes into the hand unseen; the arrows say
nothing and should go in steps. **Builds:** Claude · **Review:** light · P1.

**What it is, and is not:** the desktop's field (`js/arena/*`) and one orkUI component. Not: the phone's field (its
tokens, decisions §81, stay; a later call); the project's level (spec 79); what a task is or when it runs
(spec 84).

| part | builds | files (and their tests) |
|---|---|---|
| **A0. orkUI** | §1 | orkUI: `components.css` `.ork-busy`, `preview.html`, `README.md`, `tests/test_orkui.py`; then the copy (`python -m orkboard.design.orkui <orkUI>`) |
| **A. Rows** | §2, §3 | `realm/map_stage.py` (`row_of`), `js/arena/arenawords.js` (`rowsOf`, `ROWS`), `js/arena/field.js`, `js/arena/stacks.js`, `js/arena/arena.css`; `tests/test_map_stage.py`, new `tests/test_field_rows_browser.py` |
| **B. Cards, members, arrows, hand** | §4–§7 | `js/arena/stacks.js`, `members.js`, `arrows.js`, `stops.js`, `motion.js`, `arena.css`; new `tests/test_field_glance_browser.py`, and the tests that read a member's frame or the arrows |

A0 first; A and B at once (they share `arena.css`: A its rows' block, B the rest).

## 0. The words
Rows: *Now*, *Next*, *Later*. A held card's foot: *held: window*, *held: tonight*, *held: sign in*, *held: week*. The
table's line: *Nothing at work: k results wait for your look* · *Nothing at work: <tool>'s window is at p %, back at
HH:MM* · *Nothing at work: held for tonight (HH:MM)* · *Nothing at work: <tool> waits for its sign-in*.

## 1. The busy mark (A0)
`.ork-busy`: a 12 px mark of four pixels going round a 3 × 3 square, `steps()` at 0.8 s a turn, the ink colour; under
`prefers-reduced-motion` it stands still as its three dots. No colour of its own; Orkboard's sheets still carry none.

## 2. Rows across the field (A)
1. `map_stage.row_of(tasks)`: a task open and not waiting on an open task (running, testing, ready, held, at Review,
   picking) is row 1; a task waiting is 1 + the highest row of the open tasks it waits for; merged ones count for nothing.
   Rows past 3 are row 3 (*Later*).
2. The field is one grid: a column per member (as today, `--cols`) and a row per §0 row; every stack of a row sits in
   that grid row, so a row reads straight across the table. Its label stands at the table's left edge, in the pixel
   face, muted for *Next* and *Later*. An empty row is not drawn.
3. Inside a cell, the stacks are as today (a stack per goal, front card by `RANK`).

## 3. Waits and held (A)
`is-wait` splits: `is-held` (a dashed edge and its reason's sign at the foot, §0) and a waiting card (only in rows 2+,
its foot *after X*). When no card of the party is running or testing, a line over the table says why, the first that
holds of §0's (results at Review; a window; the night; a sign-in), else nothing.

## 4. A card at work (B)
A running or testing card wears `.ork-busy` top left in place of its state's sign, its foot *working n min* /
*testing*; its edge the ink edge, as today.

## 5. A member is a face (B)
`.arena-member` loses its frame and its 200 px cap: the head (40 px) and name centred over the column, the marks beside
the name, and under them a 2 px rule the full width of the column (`--ork-edge`); while the member works the rule is ink
and its head wears `.ork-busy`; while it calls, the danger colour (`is-calling` as today). The peek on hover stays.

## 6. Arrows in steps (B)
`arrows.js` draws a `<polyline>` per edge: down from the bottom centre of the card waited for, across at the middle of
the gap between the two rows, down into the top centre of the waiting card; square corners, 2 px, the head as today.
Still on hover and focus only. A same-row edge (none after §2) draws nothing.

## 7. A new stop rises (B)
A stop that was not in the hand at the last draw rises: out of the fan, upright and whole, its foot on the hand's top
line, 0.2 s up; it stays 2.5 s (longer while hovered), then goes to its fan place (0.3 s). Several at once rise one after
another, 0.6 s apart. Under reduced motion: no move, its edge the alert colour for 2.5 s. The first draw after the page
opens raises nothing.

## 8. Tests
- **A0**: the class, its steps, still under reduced motion, no colour of its own.
- **A** (stub host, 1 440 × 900): `row_of` on a chain, a fork and a join, merged tasks ignored, a held task in row 1;
  two goals' independent tasks in the same row across two members' columns at the same height; labels; an empty row
  absent; the nothing-at-work line for each reason.
- **B**: a running card's busy mark and foot; a held card's reason; a member's rule as wide as its column (±1 px), ink
  while it works; an arrow's points all horizontal or vertical; a new stop risen then in its place, two in turn, none on
  the first draw; reduced motion.
- Each part: the critical tests, its files' tests, `tests/test_gui_wording.py`, `tests/test_design_system.py`.

## As built (A0)

- orkUI 0.10.0 (`.ork-busy`, `preview.html`, `README.md`, `tests/test_orkui.py` there) copied into `design-system/orkui` (`python -m orkboard.design.orkui <orkUI>`, commit 472655f); nothing of it is written here. `.ork-busy` is 12 px, four pixels going round a 3 × 3 square, a step a frame at 0.8 s a turn, the ink and the faint ink; under `prefers-reduced-motion` it stands still as three dots.

## As built (A)

- `realm/map_stage.py` `row_of(tasks) -> {id: row}`: a task not *waiting* (running, testing, ready, held, review, picking, failed, and a merged or dropped one) is row 1; a waiting task is 1 + the highest row of the open tasks (not merged, not dropped, found in the plan) it waits for, none open: 1; a cycle reads as no wait; rows past `ROWS` (3) are 3. `realm/board_map.py` gives every task of `ideas.map` its `row` beside `wave` (the one other change on the host).
- `js/arena/arenawords.js`: `phaseFor(n, t)` reads the host's `row` (1–3, a `row` that is not a whole number from 1 is not read) and falls back to `phaseOf` (the goal's own wave) with none; `columnOf` uses it; `ROW_LABEL` (*Now*, *Next*, *Later*); `heldOf(t, n)` -> `{kind: window | night | sign_in | week | files | "", word, sign}`, `heldWords(t, n)` (the long words, now the held card's tooltip: *tonight · after 01:00*, *waits for limits · after 14:20*). `taskFoot` of a held task is *held: window* · *held: tonight* · *held: sign in* · *held: week*; a hold for the same files (or one not known) keeps its own words.
- The field is one grid (`.arena-cols__grid`, `arena.css`): a track per member (`--cols`), six lines for the rows (a label line and a cards line each: Now 1–2, Next 3–4, Later 5–6), a seventh for *✓ k in dev*; a line with nothing in it is no height, so an empty row is not drawn. A member's column (`field.js` `Column`, still `.arena-stack[data-agent]` with the motion of `useColumn`) is a **subgrid** of those seven lines and its stacks lie in its cells (`stacks.js` `Cells`: `.arena-phase.is-cell[data-row]`, `align-self: stretch`), so a row reads straight across; a row's label (`RowLabel`: `.arena-row__lbl`, pixel face, ink for *Now*, muted for *Next* and *Later*, `grid-column: 1 / -1`) stands at the table's left edge, only for a row some member has a stack in. The grid scrolls (not each column); while a plan is dealt in (`.arena-stack.is-dealing`) it does not clip. A member shown alone keeps `Rows` (its own labels, across the field's whole width). The stacks and the front card's `RANK` are as before.
- The cards: `is-wait` (waiting) and `is-held` (held) are two classes (`stacks.js` `stateCls`); a held card is dashed on the canvas ground and its foot has the reason's sign (`night`, `pause` for a window and for the week, `alert` for a sign-in, `before` for the same files) and wraps (*held: tonight* is two short lines on a card 104 px wide); a waiting card in a cell is solid-edged and says what it waits for as before (spec 67 §3: *waits for 2*, the names in its tooltip and its label, *after X* in `taskFoot`). `.is-wait` stays dashed outside the field's cells (the project's decks, a Planning card, the Agents chip use it).
- The line over the table (`js/arena/idle.js`: `idleOf(nodes, limits)`, `IdleLine`, `p.arena-idle[role=status]`, in `Columns` over the stage labels): none while a task of the party runs or tests; else the first that holds of *Nothing at work: k results wait for your look* (tasks at `review`; *1 result waits…*), *Nothing at work: <tool>’s window is at p %, back at HH:MM* (a task held for the window; the tool is the tightest of `town.limits`, p its used share, the time the goal's `waits.until` or that limit's reset; either left out when not known), *Nothing at work: held for tonight (HH:MM)* (the time when `waits.until` has one), *Nothing at work: <tool> waits for its sign-in*; none for a week hold or nothing known.
- `js/arena/glance.css` (new; `@import`ed by `column.css` so that `shell.js` loads it, `arena.css` being past 600 lines; added to `tests/test_design_system.py` `SHEETS`): the label, the cell, the line, the held card; the rest of A is in `arena.css`.
- Tests: `tests/test_map_stage.py` (`row_of`: chain, past three, fork, join, merged and dropped ignored, held and every other state row 1, a cycle), `tests/test_board_map.py` (a task's `row`), new `tests/test_field_rows_browser.py` (1 440 × 900, a stub that gives rows with the real `row_of`): the cards of four members' columns, of two goals, at one height in Now and the two in Later at one height, the columns as wide as their members, the labels at the table's left edge over their rows (pixel face, Next and Later muted), an empty row gone and back, a host row before a goal's own wave, rows past three, a host with no `row` still by waves, the line for each reason (and none for a week hold, nothing known, something at work). Updated: `tests/test_arena_desktop_browser.py` (labels, the held foot).

## As built (B)

- A card at work (`stacks.js` `CardBody`): `<span class="ork-busy">` first in the card's top line, before the goal's element, for `running` and `testing`; no state sign, the foot *working n min* / *testing*, the edge as before. Tests that waited for `document.getAnimations()` to be empty skip `ork-busy`'s (it never ends).
- A member is a face (`members.js`, `arena.css`): `button.arena-member` has no frame, no clip and no 200 px cap and is as wide as its column (`.arena-mcol`); the head `.arena-tport` is 40 × 40 and centred, the state's sign on its top right corner (`.arena-sign`; `work` is `.ork-busy` in it, the others as before), the name and the level's and the tool's marks (`.arena-mark--r`, `--h`, now in the line, not on the head) centred under it (`.arena-member__line`), the two numbers (`.arena-num`: runs/sent back, price) stand to the right of the head, and `.arena-member__rule` (2 px, `--ork-edge`; ink while `data-state="work"`; `--ork-danger` while `needs`, a failure and a question alike) closes it at the column's full width. The row is 64 px as before. `is-struck` and `is-calling` are as before; the peek is as before.
- The arrows (`arrows.js`): `steps(key, a, b)` gives a `<polyline>` of four points (down from the bottom centre of the card waited for, across at the middle of the strip under its row, down to the head) and the head `<polygon>` (9 px, as today); nothing when the waiting card does not lie lower (the same row, and a spread's cards side by side: no arrow, their lines say it). The strip's middle is the bottom of the first card's cell (`.arena-phase.is-cell`) + 8 px (the label's line is 16 px). `ArrowLines` draws a `<line>` for a diagonal `segment` (the project's level, spec 79, which is not touched) and a `<polyline>` for `steps`; hover and focus only, as before; a card is *shown* when it lies in the field's grid's view (`.arena-cols__grid`, not a column's).
- The hand (`stops.js` `useRising`, `glance.css`): a stop whose key was not in the hand at the last draw (the keys are kept over the parties' pages; the first draw once the Board is read, and the first after another project is shown, raise nothing) gets `.is-up` (the hover's place: upright, `translateY(-184px)`, 0.2 s up), stays 2.5 s (while the pointer or the focus is on it, for as long; it is checked every 0.3 s), then `.is-down` (0.3 s back); stops that come together rise 0.6 s apart in the hand's order. Under reduced motion nothing moves and each gets `.is-called` for 2.5 s: its edge and a 2 px inset line in the alert colour (a stop is alert already; the line is what shows). `motion.js` is not changed.
- Tests: new `tests/test_field_glance_browser.py` (the busy mark and its place, a testing card, still under reduced motion; each held reason's words, sign and dashed edge, a waiting card solid; a member's head, name, marks, rule as wide as the column ±1 px, no frame; the rule's colour for next, at work and calling and the head's busy mark following the state; the arrows' points all horizontal or vertical, down-across-down, between the rows, into the top centre, none for the same row; a new stop up and back with the timings, two in turn 0.6 s apart, none on the first draw, one that stays while hovered, reduced motion). Updated: `test_arena_desktop_browser.py` (a member's face), `test_arena_decks_desktop_browser.py` (the arrows, `<polyline>`; a spread draws none), and the five tests that count animations.
