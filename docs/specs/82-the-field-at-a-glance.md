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
