# 110. Runes on the table: the table's end always laid, the + card's seal, a goal's element as its rune

Decisions §185 (1–8) and §186 (1–6). The owner, 30 October: *show the discard and the portal even while idle, make the + card's
pattern magical* (the mockup `docs/mockups/table-end/`, the full seal), then *let the runes be the elements: the most different
ones, tied to the colours; the goal's rune on the + card and on the portal*. **Builds:** Claude (the cheaper model builds, the
spec's author reviews) · **Review:** full · P1. orkUI 0.19.0 already draws the runes, `.ork-portal-ring`, `.ork-sigil` and
`.ork-card-place` (copied into `design-system/orkui`); this spec moves five runes into the elements, gives the ring and the
seal their goal's place, and lays all of it on the page.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.20.0** | the five elements become five runes; the ring and the seal are written in the seven others and keep a place at their top for the goal's rune (`__seal`); the seal's geometry for it | repository orkCraft/orkUI: `office/runes/runes.json`, `tools/build_runes.py`, `office/elements/*.svg` (now generated), `office/components.css`, `office/preview.html`, the READMEs, `CHANGELOG.md`, `tests/test_orkui.py` |
| **B. The page** | the copy; the table's end always laid at the wide width (the ring and the place); the ring open while a goal is ready, the chosen goal's rune in it; the + card's seal with the next goal's rune; `next_element` per party | `design-system/orkui` (by `python -m orkboard.design.orkui <orkUI>`), `realm/idea_element.py`, `gui/ideas_map.py`, `js/table/discard.js`, `js/table/discard.css`, `js/table/portal.js`, `js/table/portal.css`, `js/hand/pluscard.js`, `js/hand/hand.css`; `tests/test_idea_element*.py`, `tests/test_discard_table_browser.py`, `tests/test_gate_browser.py`, the + card's tests |

A is merged into orkUI's `main` before B starts: B copies orkUI's commit.

## 1. The words

No new word for the interface. *Main* and *Discard* stay the places' labels. The runes and the elements are never named in the
interface (§63.4, §186.1). In code: `rune` (orkUI), `element` (as today), `next_element` (the element a new goal of a party would be
given). Wording rules of CLAUDE.md hold: *goal*, *party*, *ork*.

## 2. Part A: orkUI 0.20.0

### 2.1 The elements are runes (`runes.json`, `build_runes.py`)

- `runes.json` gains `"elements": {"meadow": "tusks", "ice": "key", "dust": "comb", "void": "eye", "lava": "wave"}` and
  `"decoration": ["hook", "ladder", "spiral", "staff", "hourglass", "diamond", "knot"]` (the seven others, in this order).
- `build_runes.py` also writes `office/elements/<element>.svg`: the element's rune, 5 x 7, **centred in the 7 x 7 grid** (columns
  1 to 5, rows 0 to 6), `viewBox="0 0 7 7"`, in the elements' existing format (one path of unit squares, `fill="#000"`,
  `shape-rendering="crispEdges"`, exactly as `elements/void.svg` is written today). `--check` covers them. The file names, the
  tokens, `.ork-elem` and its sizes (14, `.big` 28, `.dim`) do not change: every face that draws an element draws the rune.
- The ring and the seal take their runes from `decoration` only: a check in the generator (and a test) that no element's rune is
  in `ring.runes` or `sigil.runes`.

### 2.2 The ring's place for the goal's rune

- `ring.runes` becomes the seven decorative runes at 45°, 90°, … 315° (clockwise from the top, positions 1 to 7); **position 0
  (the top) is the seal's place**: no rune is drawn there, and the generator clears the dots round the place's 7 x 7 box as it does round a rune (by `ring.clear`), so the gap is the place.
- `.ork-portal-ring__seal`: a 14 x 14 box (`position: absolute; z-index: 2`) whose top left is the place's 7 x 7 box at 2 px a
  cell (the generator's top left cell of a 7 x 7 box centred on the circle at angle 0, times 2: compute it with `placed`'s rule
  for a 7 x 7 box and write the two numbers into the CSS; a test checks them against the generator). The caller puts the goal's
  element in it: `<span class="ork-portal-ring__seal"><span class="ork-elem dust" aria-hidden="true"></span></span>`, drawn in
  the element's own colour at full strength (§186.4). Empty, it draws nothing.
- `.ork-portal-ring.is-sealed .ork-portal-ring__seal > .ork-elem` is drawn in the faint ink (as `.ork-elem.dim`).
- While `.is-open.is-waking`, the seal's rune appears with the portal's eye (the same delay and five steps' `clip-path`, or simply
  `opacity` from 0 after the runes' eight steps; reduced motion: at once).
- Asleep (no `is-open`, no `is-sealed`) the caller leaves the seal empty.

### 2.3 The seal's place for the goal's rune

- `sigil` becomes `{"size": 68, "outer": 31, "inner": 19, "ticks": 33, "band": 25, "runes": <the seven decorative runes>}`:
  the seven runes at 45°, 90°, … 315° on the band's middle (`band`), **position 0 (the top) the goal's place**. This geometry has
  been checked: every rune keeps two cells from every line (the test's `_gap >= 2`), a 7 x 7 box at the top keeps three, and the
  middle 13 cells stay clear for the +. `ticks` 33 lies inside the 68 grid.
- `.ork-sigil__seal`: a 14 x 14 box at the place's 7 x 7 box (2 px a cell, the numbers from the generator as in 2.2), holding
  `<span class="ork-elem <name>">` in its own colour at full strength. Empty, it draws nothing. `.ork-sigil.small` has no seal
  (no runes at 80 px): `.ork-sigil.small > .ork-sigil__seal { display: none; }`.
- The hover's sweep lights the eight positions in turn from the top: the conic sector is centred on each position
  (`conic-gradient(from calc(var(--_turn) - 22.5deg), …)`), eight steps, once, as today. The goal's rune does not take part (it
  is already at full strength).

### 2.4 The rest of A

- The tests (`tests/test_orkui.py`): the element table (`ELEMENTS`, spec 50 §1.1's) becomes each element's rune centred in 7 x 7;
  the test *the void is an empty ring* becomes *each element is its rune, centred, and no two elements share a rune*; the
  elements stay apart from every sign, emblem and moon (the existing tests; they pass today for these five: the nearest sign is
  six cells away); the ring and the seal use no element's rune; the seal's place and the ring's place are where the generator
  says, empty boxes clear of every line and rune; `__seal` boxes are 14 x 14 and absolute; the sweep starts at the top; version
  at least 0.20.0. Keep every other test passing; adjust the 0.19.0 tests of the sigil's geometry to the new numbers.
- `office/elements/README.md`: the five are runes (which is which, why: §186.1), drawn by `build_runes.py`; *void* is the eye,
  which keeps the old ring with its centre. `office/runes/README.md`, `office/README.md`, `README.md`: the elements, the
  decoration, the two `__seal` places.
- The gallery (`office/preview.html`): the elements' section draws the new shapes by itself; the runes' section adds the ring
  open with a goal's rune in its seal (each of two elements), sealed with one (faint), and the sigil with `__seal` holding
  `meadow` and one holding `lava`.
- `CHANGELOG.md` `## 0.20.0`; version 0.20.0 in `pyproject.toml`, `uv.lock`, `tokens.json` (then `python tools/build_tokens.py`);
  `docs/preview-office.png` made again over http (a full-page screenshot of `office/preview.html` at 1280 wide).
- Run `python tools/build_runes.py`, every `tools/build_*.py --check`, and `python -m pytest` (all must pass).

## 3. Part B: the page

### 3.1 The copy and the element to come

- `python -m orkboard.design.orkui <orkUI checkout at main>`; `tests/test_design_system.py`, `tests/test_assets.py` pass.
- `realm/idea_element.py`: `next_for(root, state_dir, party) -> str`, `pick(open_elements(root, state_dir, party))` (the same
  rule `give` uses, so the rune shown is the one the goal is given). A test in the element's tests.
- `gui/ideas_map.py`: every party node of `ideas.map` carries `next_element` (the party's `next_for`). No other change to the map.

### 3.2 The table's end at the wide width (§185.2, §185.3, §186.5)

`DiscardEnd` (`table/discard.js`) is drawn **always at the wide width** (760 px and up; `useNarrow` as in `portal.js`), on every
tab. At the narrow width it is as today (nothing with nothing done and nothing ready; the portal as today).

From the top, in the table's last column, centred over the pile (the column `portal.css`'s `.portal-host` has):
1. **The line** (`.portal__line`), only while a goal is chosen (today's words, unchanged), and the sealed reason under the ring as
   today (`.portal__sealed`).
2. **The label** *Main* (`.portal__label`): in the faint ink while the ring is asleep, as today while it is open.
3. **The ring** `.ork-portal-ring` (192 x 192), holding the portal:
   - **asleep** when `readyOf()` has no goals: no portal inside, no seal; not a button; nothing to press.
   - **open** (`is-open`) when goals are ready for main: the portal (`.ork-portal`, the default size) inside it, as today a
     `<button>` with today's handlers (drag over, drop, press). The **first time it opens on a device it wakes**: `is-waking` on
     the ring and `is-new` on the portal (the `first` signal and `SEEN_KEY` already say *the first time*; reuse them). With
     **no goal chosen**, pressing the portal opens the discard's view (`openOver("discard", {}, null, "Done")`) where the goals
     ready are chosen; the portal's label says *Choose a goal done to send it to main*. With a goal chosen, everything is as today
     (`plan`, `play`, `is-taking`, sealed). Choosing still happens in the discard's view (`ReadyCards`), and closing the view no
     longer closes the portal, only drops the choice.
   - the chosen goal's element in `.ork-portal-ring__seal` (its `.ork-elem`), `is-taking` on the ring while a card is held over
     it (with the portal's own `is-taking`), `is-sealed` on the ring while the portal is sealed.
4. **The label** *Discard* and **the pile** as today; with nothing done and nothing ready, **`.ork-card-place`** at the pile's size
   (`--hc-w`) where the pile will be, `aria-hidden`, not a button.

Layout (`discard.css`, `portal.css`, layout only): the column is wide enough for the ring (192 px): `.table-end` and
`.portal-host` take `max(var(--hc-w) + var(--ork-8), 192px)` and the parties' tabs' `data-end` padding grows to match where it
must (a party's map ends above the end as today). Nothing overlaps the hand: check at 1280 x 800 and 1024 x 768 with the
hand's tallest card lifted (the existing test helpers).

### 3.3 The + card's seal (§185.4, §186.3)

- `PlusCard` (`hand/pluscard.js`) puts `<span class="ork-sigil" aria-hidden="true"><span class="ork-sigil__seal">…</span></span>`
  before its icon; `small` at the narrow width (80 px card), none of the seal's place then. The seal holds the element the new
  goal would be given: the addressed party's `next_element` (`addressNow()`: the open tab's party, else the one named with *@*;
  none on the Orkmaster's tab with no party named, and then the place is empty). Updates as the address changes.
- `hand/hand.css`: the hatch and the band of light go (`.hand .hand-plus`'s `repeating-linear-gradient` background and its
  `::before` with `hand-plus-band`); the double frame, the corner brackets (`::after`), the lean and the green stay. The card's
  `color` is the action's green already, so the seal is green; the goal's rune is in its own colour. The large card (`is-large`,
  180 px) keeps the 136 px seal. The comment over the rules says decisions §185.4, §186.3 and that the seal is orkUI's `.ork-sigil`.

### 3.4 Tests of B

- `tests/test_discard_table_browser.py`: *none with nothing done and nothing ready* becomes *the ring asleep and the place at the
  wide width, nothing at the narrow*; the ring is open with a goal ready (and the portal inside it); the first opening wakes once;
  the place gives way to the pile when a goal is done. `tests/test_gate_browser.py` (or the portal's own browser tests): a goal
  chosen puts its element in the ring's seal; sealed is faint; pressing the open portal with none chosen opens the discard's view.
  The + card's browser test: the seal is there, the hatch is not, the seal's place holds the addressed party's `next_element`,
  and none on the Orkmaster's tab. Screenshots as the tests already take them.
- `tests/test_idea_element*.py`: `next_for` equals what `give` gives the next goal of that party. A test of the map: party nodes
  carry `next_element`.
- The critical tests (CLAUDE.md: `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and the test
  files of every module touched pass before the merge.

## 4. Later (not here)

- The phone: the narrow width draws neither place (§185.6); the phone's own face gets them with spec 94 B–E.
- A rune per goal type, or the runes on the map's cards beyond the element: not decided.

## 5. Order

A (orkUI, merged to its `main`), then B on Orkboard (one branch, merged to `main` when the critical tests and the touched modules'
tests pass, per the alpha rule).

## As built

(filled in after the build)
