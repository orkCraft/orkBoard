# Spec 77 — The field is a game table: Orkboard's wood under the work

The owner, 25 October (decisions §92): orkPage gave Orkboard the game table's wood (`#ac8266`) for its colour; put it in
the product as *the table cards are played on*. Of the trial's options (the field a table, the hand's shelf, the backs of a
pile, the moments of spec 74, the phone) the owner picked the first. **Built:** Claude · **Review:** light · P3.

Wording: CLAUDE.md. **This file is the contract.**

| part | builds | files (and their tests) |
|---|---|---|
| **A0. orkUI** | §1 | orkUI 0.8.0: `office/tokens.json` (and `tokens.css`), `components.css` `.ork-table`, `preview.html`, `README.md`, `tests/test_orkui.py` |
| **A. The field** | §2 | `design-system/orkui/` (the copy), `js/arena/arena.js`; `tests/test_design_system.py` |

## 1. The table (A0)
Three tokens: `--ork-table` `#16110d` (the top: the canvas warmed, chroma 3), `--ork-table-rim` `#4e3a2c` (the rim) and
`--ork-table-rim-hi` `#7a5d49` (its lit lip, 3:1 on the top and on the canvas). All three quieter than the quietest signal
and at least 20 (CIE76) from every signal, the ork's green and the dust element. Text on the top holds AA (ink, the muted
and faint ink, danger, alert, success). `.ork-table`: the top as the background, the rim an inset 3 px, the lip 1 px
inside the rim at its top. A surface, never a mark: nothing on it takes the wood.

## 2. The field (A)
The desktop's field, `.arena-body` (the party at work: its phases, rows and stacks), wears `ork-table`. The party's
members above it, Waits for your look beside it and the hand below it stay on the canvas: the table is where the work is
dealt. Orkboard's sheets carry no colour of their own (`tests/test_design_system.py`), the wood included.

## 3. Not in this spec
The hand's wooden shelf, the backs of a pile and the deck in wood, the phone's field, the wood in the top bar's name
(decisions §92.4).
