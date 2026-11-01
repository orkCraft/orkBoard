# 123. The leaders at the table: the open leader large with its marks and its bubble, the header one row, faces, chairs, the dark edges, Stop all a door

Decisions §201. The owner, 1 November, on `docs/mockups/lens-heads/` (its yes): the leaders are the person's fellow players at
the table (§199.2); who decides sits at the table, who does is the leader's squad on its lens. **Builds:** Claude (the cheaper
model builds, the spec's author reviews) · **Review:** full · P1. After spec 120 (the cards handed, the hearing) and spec 121
(the evening line). Spec 122 stays the leaders' voices.

**What it is, and is not:** the tabs' row as the leaders' side of the table (heads larger, faces, chairs, the empty chair, the
door), the open leader's concerns and question by its head, the party's header in one row, the dark edges. Not: the phone's
menu (§195, unchanged); the Board's cards (a member at work already turns on its card, spec 95 §3.2); a hearing's or a
sketch's faces (they keep theirs); a new pane, column, drawer or dialog (§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI** | the room token; the chair (occupied back, the empty chair); the door (shut, open); the leaders' and the Orkmaster's five faces | repository orkCraft/orkUI 0.27.0: `office/tokens.json` (`tools/build_tokens.py`), new `office/chair/` and `office/door/` (with their build, as `office/potion/`), `races/races.json` (`faces`, `tools/build_races.py`), `office/components.css`, `office/preview.html`, READMEs, `CHANGELOG.md`; `tests/test_orkui.py`, `tests/test_races.py` |
| **B. The copy** | orkUI 0.27.0 copied; `Head` draws a mood | `python -m orkboard.design.orkui /home/user/orkui`; `gui/static/js/orkui.js` (`Head` `mood`, `Chair`, `Door`); `tests/test_design_system.py` |
| **C. The concerns by the head** | the strip goes; the record is still read; stepping and the aspects exported | `gui/static/js/table/concerns.js`, `concerns.css`; `tests/test_concerns_desktop_browser.py` |
| **D. The header, one row** | no *Leads*; the sword and the shield with their tool; roles under the heads; the aspects at the right; *Ask again* in the **…** | `gui/static/js/table/header.js`, `data.js` (`squadOf`), `table.css`; `tests/test_table_desktop_browser.py` (or where the header is tested) |
| **E. The bubble** | the quick question as the open leader's bubble; the evening line in it | `gui/static/js/table/ask.js`, `ask.css`, `pane.js` (the line goes); `tests/test_ask_desktop_browser.py` |
| **F. The tabs as the table's far side** | heads 36 and 48, the open head a button with its marks, faces, chairs, the empty chair, the door, the dark edges, no dividers | `gui/static/js/table/tabs.js`, new `table/moods.js` (no face: the mood of a leader), new `table/door.js` (the door's state), `table.css`, `hand/hand.css` (the room under the hand), `frame/frame.css`; new `tests/test_leaders_table_browser.py` |

## 0. What is there today

- **The tabs** (`table/tabs.js`): the project's tab (the crowned head, the project's name, **▾** a sibling button in its cell),
  a tab a party (its leader's head 24 x 22, the party's name, the sword and the shield with their tools' marks, `tabmarks.js`),
  `+ Party` (orkUI's `banner` icon), `Stop all` (`boarded`, `command("halt")`, the host toasts *Stopped n runs*), the logs'
  bug. A tab is a `<button role=tab>`; the open one `aria-selected`, orkUI's raised fill and bar. Alert: `hasAlert(g)` from
  the snapshot's `g.concerns {alerts, notes, status}`.
- **The pane** (`table/pane.js`): its title, then for a party `Header` (`header.js`: name, *Leads* | *Does* | *Checks*
  groups of `Seat`s, each head 24 with its tool's mark, the size, **…**), `AskLine` (`ask.js`: *Ask the Architect…*, the
  answer under it), `PickStrip`, `Concerns` (`concerns.js`: `Strip` with the head, *1 alert, 2 notes*, **Ask again**, the
  aspects' row `cn-aspects`, the evening line `Since`; `Inner` paints the marks on the map). On the Orkmaster's tab
  `AskLine` (*Ask the Orkmaster…*) over the Board.
- **A head** (`orkui.js` `Head {race, tier, size}`): `""` 24 x 22, `mid` 36 x 33, `big` 48 x 44, from orkUI's
  `races/<race>-<tier>[@2x].png`. A seat's popover `SeatPop` (`seatpop.js`).
- **The edges**: the frame, the tabs and the hand on `--ork-canvas`; the Board and the maps on orkUI's `.ork-table`.

## 1. The words

No new term: *chair* and *door* are pictures (*seat* stays the squad's word). The interface:
- The open head: `aria-label` *Ask the <Leader>* (*Ask the Orkmaster*), `aria-haspopup="dialog"`, `aria-expanded`.
- Its marks: *The <Leader>: 1 alert, step through it* · *The <Leader>: 2 notes, step through them* (the numbers in the
  label only, §67); while it looks: `title` *The <Leader> is looking at the map*.
- The bubble: its head row the leader's name and role (*Grukk, the Architect*; *the Orkmaster*), × *Put away*; the field
  *Ask the <Leader>…*; the answer, its sources, **Make it a goal**, *Ask more*; the evening line *Since your last look:* as
  today; its foot *Its seat: <tool> · <tier word>* with **Change** (the seat's popover); a failure in its words.
- The header: *Does* and *Checks* with the tool (`title` *Does on Claude Code*), a seat's `aria-label` *<role>, runs on
  <tool>*; the party's **…** gains *Ask again* (*The <Leader> looks at the map again*).
- The empty chair: its label **New party**, `aria-label` *New party*.
- The door: **Stop all** (`title` *Stop every ork, script and browser at once*); open: **All stopped** (`title` *All
  stopped: the door shuts when work starts again*), `aria-disabled="true"`.

## 2. Part A: orkUI 0.27.0 (repository orkCraft/orkUI, made first, then copied)

1. **`--ork-room`**: near black under the canvas, `#090807` (never `#000`), in `tokens.json` and `tokens.css` (generated by
   `tools/build_tokens.py`), the README's contrast lines for the ink, the muted and the faint ink on it (each holds AA).
2. **The chair** (`office/chair/chair.json`, generated by a `tools/build_chair.py` with `--check`, as the potion): masks in the
   signs' format (one path of unit squares), two tones each, a `::before` and an `::after` as `.ork-potion` draws them:
   - `.ork-chair` (an occupied chair's back, 22 x 12 cells at 2 px, 44 x 24): two posts 2 cells wide full height (their knobs
     the top row), the top rail 2 cells high a cell under the top, the panel between them below the rail; the posts and rail
     `--ork-table-rim-hi`, the panel `--ork-table-rim`. `.ork-chair.big`: 26 x 14 cells (52 x 28).
   - `.ork-chair.is-empty` (the whole chair, 18 x 18 cells, 36 x 36): two posts (x 2–3 and x 14–15, rows 0–9), the rail
     (rows 1–2) and the panel between them (rows 3–8), the seat full width (rows 9–10), the front legs (x 1–2 and x 15–16,
     rows 11–17); its tones `--ork-frame` and `--ork-raised`; `.is-lit` (`:hover` and `:focus-visible` too, on the element
     itself or `.is-lit` set by the page): `--ork-edge` and `--ork-table-rim`, and the chair pulled out (`translateY(-2px)
     rotate(-4deg)` from its foot, `--ork-motion-base` on the spring) inside `prefers-reduced-motion: no-preference`.
     `.ork-chair.is-empty.small`: 18 x 18 at 1 px.
   - Still at rest, no colour of its own beyond the tokens named.
3. **The door** (`office/door/door.json`, its build): `.ork-door` (14 x 20 cells at 2 px, 28 x 40): the frame (posts 2 cells,
   lintel 2 rows) `--ork-table-rim-hi`; shut, the leaf `--ork-raised` and its knob (2 x 1 at x 9, row 10) `--ork-ink-faint`;
   `.is-open`: the opening `--ork-ink-faint` at 0.7 and the leaf seen edge on (x 2–3) `--ork-raised`. `.small`: 1 px a cell.
   Open and shut are states; nothing swings.
4. **The faces** (`races/races.json` gains `faces`): for each leader race (`shaman`, `dryad`, `imp`, `fairy`, `unicorn`,
   `lich`) and the Orkmaster's `peon` crown, the eyes' row, their four cells, the mouth's row (none for the knight's helm) and
   the skin's role; five moods drawn as cell edits on the 12 x 11 grid, sprites `<race>-<tier>-<mood>.png` and `@2x` for every
   tier of those races (and `peon-crown-<mood>`): **focused** (a dark brow over the four eye cells), **worried** (the outer eye
   cells skin, the inner brow dark, a small open mouth), **no** (the inner brow dark, a flat mouth of four cells), **pleased**
   (the eyes closed upward: the eye cells skin and the brow cells dark, a smile), **asleep** (the eyes shut: the eye cells a
   third of the way from the skin to the dark). The mockup's `face()` is the sketch; orkUI's drawer may refine a cell, keeping
   each mood told apart at 24 x 22. The members' races get no faces.
5. **The gallery** (`office/preview.html`): the room behind a row of chairs with heads, the empty chair at rest and lit, the
   door shut and open, the faces' sheet; **tests** (each drawing's cells, the tones are tokens, the faces' files for every
   leader race and tier, `--check` of every build); READMEs; `CHANGELOG.md`; version 0.27.0 in `pyproject.toml`, `uv.lock`,
   `tokens.json`, `tokens.css`.

## 3. Part B: the copy

`python -m orkboard.design.orkui /home/user/orkui` (never an edit of `design-system/orkui`). `orkui.js`: `Head` gains `mood`
(`""` calm; else `races/<race>-<tier>-<mood>[@2x].png` when the race is a leader's or the crown, else calm); `Chair({big,
empty, small, lit})` and `Door({open, small})` render orkUI's markup, `aria-hidden`. `tests/test_design_system.py`: the copy is
≥ 0.27.0 and stamps `chair/`, `door/`, a face of each leader race; the sheets still carry no colour of their own.

## 4. Part C: the concerns by the head (`concerns.js`)

1. `Strip` goes. `Inner` keeps reading the record (`ideas.concerns`, its poll while `looking`) and painting the marks.
2. Exported: `stepMarked(party, level = "", aspect = "")` (the strip's `step`: scroll into view and lift, picking wins),
   `Aspects({g})` (the rubric's short words and the aspects' chips, as `cn-aspects` drew them, a press stepping through its
   cards), `lookOf(party)` → `{status, alerts, notes, error, since}` from the record (the snapshot's `g.concerns` while no record),
   `askAgain(party)` (the strip's **Ask again**).
3. The evening line `Since` is drawn in the bubble (E).

## 5. Part D: the header, one row (`header.js`)

1. **`squadOf(g)`** (`data.js`): `groupsOf` without the lead: `[{band: "build" | "check", word, seats}]`, at most six.
2. The row: **Does** — orkUI's `sword` sign, the word, the tool's ink mark when every seat of the side runs on one tool — then
   its seats; a divider; **Checks** — `shield`, the word, its tool — its seats; the size chip; a growing gap; `Aspects` (C); the
   party's **…** (*Edit*, *Ask again*, *Remove party*). A seat: its head 24 x 22, its own tool's mark only when it differs from
   its side's, the busy mark while it works, its role under it (`m.name`, the caption face, muted, cut with an ellipsis at
   76 px); pressed, its popover (`SeatPop`) as today. No party name in the row (the tab and the title say it).
3. Under 760 px: the sides' words go (the signs and their `title` stay), the aspects keep only those with an open concern and
   wrap under the seats; no sideways scroll; every seat 44 px to press.

## 6. Part E: the bubble (`ask.js`)

1. `AskLine` goes from the pane (`pane.js`, both tabs). `ask.js` exports `askOpen` (a signal: the tab whose bubble is open, or
   `null`) and `AskBubble({tab, parties})`, drawn by the tabs (F) under the open head, positioned from the head's box
   (`position: fixed`, its tail at the head's centre, at most 440 px wide, kept inside the window), on orkUI's raised panel
   with the edge.
2. Its states, as `AskLine`'s are today: **asking** (the field focused in the press itself; Enter asks `ideas.ask {party, q}`;
   the field kept on close), **reading** (the question muted, *The <Leader> is reading the map* with orkUI's `ork-think`),
   **answered** (the question muted, the answer, the sources as chips, **Make it a goal**, *Ask more*), **failed** (its error).
   The answer stays until put away (`ideas.ask_clear`), as it stays under the line today: a bubble closed with an answer in it
   shows nothing more on the head (no count, no dot), and opening it shows the answer.
3. **The evening line**: when the record has `since` and the person has not seen it today for this party (a `localStorage`
   key a party a day, in try/catch: a convenience only), the bubble opens by itself once when the tab is opened, holding
   `Since` over the field; seen once, it is drawn at the bubble's top while the day lasts.
4. Its foot (a party's, not the Orkmaster's): *Its seat: <tool> · <tier word>* and **Change**, which opens `SeatPop` for the
   leader's seat.
5. Esc, × or a press outside closes it (the head keeps the focus back). The desktop only: under 760 px wide and on a touch
   window (§181.8, as `AskLine` was) no head opens a bubble.

## 7. Part F: the tabs as the table's far side (`tabs.js`, `moods.js`, `door.js`, `table.css`)

1. **The heads**: a party's tab and the project's draw the leader's head at `mid` (36 x 33), the open tab's at `big` (48 x 44).
   The open tab has no fill and no bar: its head, 3 px lower than the others' (over the table's rim), its name in the ink and,
   under it, the leader's own name (`g.leader.name`; the project's tab: *the Orkmaster*); the others' names muted. A tab's
   width is the column's (§143); the row grows to the open head's height (about 60 px; under 760 px 52).
2. **The open head is a button of its own** in the tab's cell (as the project's **▾** is: no button holds a button), over the
   head's place, opening the bubble (E, desktop only). Beside it, its marks: the alert sign (alert tone) when `lookOf(...)`
   has an alert, the muted dot when it has a note, each a button stepping through (`stepMarked(party, "alert" | "note")`);
   while the leader looks, its face focused and `title` saying so. The other tabs keep their alert sign as today.
3. **The faces** (`moods.js`, no face, unit-tested in a browser test): `moodOf(g, snapshot)` → `asleep` when the AI tool of
   the party's leader has no window left (`windowsOf`, the limits) or no tool; `no` when the party's leader holds a side of an
   open hearing whose kind is `drop` or `smaller` (spec 120 §4); `worried` when `hasAlert(g)`; `focused` when `isWorking(g)` or
   its leader is looking at its map; `pleased` for 60 s after a goal of the party reached the discard while the page was open
   (never for one found there on coming back, §89.0); else calm. The Orkmaster: `asleep` when the main tool is spent,
   `focused` while a Talk or a decision runs, else calm. A face changes with its state and stands still.
4. **The chairs**: each leader's head stands in a `Chair` (`big` for the open one) on the row's foot, the head over the
   chair's rail. Under 760 px: no chairs.
5. **The empty chair** replaces `+ Party`: a cell after the parties (narrower: 132 px; under 760 px a 36 px cell holding the
   chair `small`), `Chair({empty, lit: hovered or focused})` and **New party** (two lines when it must); pressed, the one place
   of the parties (`openParties({}, from)`, as `+ Party`). Hidden when every craft of the project's kind is at the table
   (the parties' recipe for its kind: `roles`' crafts, the same list *New party* offers; no empty chair when it would offer
   nothing).
6. **The door** replaces `Stop all`'s button (`door.js`): `Door({open})` and its word, the danger colour while shut. Pressed:
   `command("halt")`; on its answer the door is open (**All stopped**, muted, `aria-disabled`), until any party has a task
   running again (`isWorking`) or a goal is started from this page, then shut. The state is the page's (a second window keeps
   its own: the host's toast says what happened). Under 760 px: `Door({small})` and **Stop**.
7. **The dark edges**: the tabs' row and the hand on `--ork-room`; the frame under them too; a 3 px rim
   (`--ork-table-rim`) under the tabs and over the hand; the table (`.ork-table`) as it is. No divider between the tabs; the
   lanes keep theirs. The logs' bug stays at the row's end, after the door.
8. Reduced motion: the empty chair is not pulled out; the head's lean is a place, not a motion; the faces still change.

## 8. Order and tests

A first (orkUI, its tests and `--check`s, pushed to its main), then B (the copy), then C and D (they share `table.css` only by
new rules), then E, then F (it draws E's bubble and C's marks). Each keeps the critical tests green (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`) and its modules' tests; the browser tests whose selectors move
(`.cn-strip`, `.table-ask`, `.table-plus`, `.table-stop`, the header's groups) are changed to what is drawn now, never
skipped. New `tests/test_leaders_table_browser.py` (Chromium, the table's stub host, 1280 x 800 and 390 x 844): the open head
48 and the others 36, no fill on the open tab, the leader's name under its party's; the header with no *Leads*, the sword and
the shield with their tools, a role under each head; the open head pressed opens the bubble focused, Enter asks, the answer
and *Make it a goal*, Esc closes; the marks step through the marked parts; the faces' files by mood (a working party
focused, an alert worried, a spent tool asleep); a chair under each head at the wide width and none under 760 px; the empty
chair opens the parties' place and is gone when no craft is left; the door halts, opens, says *All stopped*, refuses a
second press, shuts when a task runs; the tabs' row and the hand on the room's colour, no divider between the tabs; no
sideways scroll at 390; under reduced motion nothing pulled out.

## 9. What it changes

§110.6 and spec 95 §2.2–§2.5 (the heads 36 and 48, no lit box, no *Leads*, the header one row), spec 106 §3 (the line becomes
the bubble), spec 108 §3 (the strip: its counts to the head, **Ask again** to the **…**), spec 109 §4 (the aspects in the
header's row), spec 121 §6 (the evening line in the bubble), §190.1 (the banner and the planks: the empty chair and the
door), §149.4 (the leaders' faces), spec 95 §8–§9 (the dark edges; the chair and the door among the drawn things).
