# Spec 78 — The project's level is played on the table too: its goals are the field's cards

The owner, 25 October (decisions §93): a press on the Orkmaster turned the cards into tickets — the project's level
drew its goals as 132 × 72 decks in ruled columns on the bare canvas, a tracker's board, while the party's field is a
table the cards are dealt on (spec 77). The level keeps the field's look: the same table, the same cards.
**Built:** Claude · **Review:** light · P3.

Wording: CLAUDE.md. **This file is the contract**; it changes spec 70 §2.2 (the decks) and nothing else of it.

| part | builds | files (and their tests) |
|---|---|---|
| **A. The level** | §1, §2 | `js/arena/project.js`, `js/arena/arena.css`; `tests/test_project_desktop_browser.py`, `tests/test_design_system.py` |

## 1. The table
The party heads (leader's head, name, *k/n*, a press opens the party) stand in one row on the canvas above the table and
stay at its top while the level scrolls down; they scroll sideways with their columns, each as wide as its column. Under
them the columns lie on orkUI's `.ork-table` (`.arena-project__cols`), as the party's members stand above its field.
No rules between the columns: a column is its cards. The New party and New goal piles stay on the canvas, as the hand does.

## 2. The cards
A goal is the field's card (`.arena-task` in an `.arena-stk`, 5:7, 104 × 146 at most, two to a row as a member's row
of stacks): its element top left, its state's sign beside it, its type's sign top right in its goal's colour; under the
line its type's name (*Goal*, a pitch *Pitch*, without one), its title (two lines), its state's words at its foot.
A card's look follows its state as a field card's does: at work drawn lit, a failure on its danger edge, a Planning goal
not yet at work dashed, a goal done (*Waits for main*, *Flags*) muted. Groups, the Flags fold, the press, the links on
hover or focus (spec 70 §2.3, spec 71 §6) are as they were.

## 3. Not in this spec
The phone's project sheet (its goals stay rows, spec 70 §2.4; the phone's field is not a table yet, spec 77 §3).
