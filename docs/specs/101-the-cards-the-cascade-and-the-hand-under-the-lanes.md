# Spec 101 — The cards, a goal's cascade, the hand under the lanes, no deck

The owner and the PM, 28 October (decisions §167; spec 95 §2.1, §2.4, §3.1, §4, §5.1 as rewritten for it; the mockup
`docs/mockups/cards/`, its fifth round, read with §167's four changes the owner made after it: the element at the left,
bare, the name left-aligned; no deck, the + card alone under the first lane; the first tab the project's; every lane a
card and a quarter; the hand's cards half under the window's edge). The window of spec 98, re-faced. **Builds:** a
cheaper model, each part reviewed by Claude · **Review:** full · P0. **A first** (in orkUI), **then B** (the lead's copy);
**C at once with A**, **D after B** (it draws the new sign). C and D share no file; they read the seams the lead wrote:
`frame/frame.css` `--card-w` (144 px), `--col-w` (a card and a quarter) and `--cols` (the grid of the tabs, the Board
and the hand: `--lanes` lanes, then the tabs' end), `frame/frame.js` setting `--lanes` (the parties and the first lane),
`frame/kinds.js` `line` (C's, over the pane).

**What it is, and is not:** the face of the Board's cards and the hand's (§167.1), a goal as a cascade on the Board
(§167.4), the line in the first lane (§167.5), the first tab the project's (§167.6), the hand under the lanes
(§167.7), its cards half hidden (§167.8), the narrow width (§167.9). Not: the other maps' cards (System's parts keep
`card.js`'s face of today, §167.1: until their slices); *Choose a card* for a goal's way (spec 100 B and C draw it on this
face); the engine (no command changes: the line is the goals whose `place` is `deck`, moved by `ideas.move` as today).

| part | builds | files (and their tests) |
|---|---|---|
| **A. The sign `question`** | §1 | orkUI: `signs/question.svg` (the signs' grid and weight), its README row, the gallery, its tests, `CHANGELOG.md`, the version 0.15.5 |
| **B. The copy** (the lead) | §1 | `design-system/orkui/**` by `python -m orkboard.design.orkui /home/user/orkUI`; `tests/test_pwa.py`'s count if the phone's worker lists signs |
| **C. The Board** | §2, §3, §5 | `static/js/table/card.js` (the task card's new face beside today's map card), new `static/js/table/cascade.js` (a goal's strip and cascade, the line's cascade), `table/boardmap.js`, `table/data.js` (`lineNow`, a goal's tasks in front order, the lane a goal lies in), `table/tabs.js` (the first tab the project's), `table/table.js` (`--tabs` goes: the frame's `--lanes`), `table/table.css`, new `table/line.js` (the line over the pane, kind `line`), `realm/lexicon.py` (`TERMS`: `deck` folded into `in_line`, its old spelling in `was`; `cascade`); `tests/test_table_desktop_browser.py`, `tests/test_window_desktop_browser.py` (its tab and deck assertions), `tests/test_lexicon.py`, `tests/test_gui_wording.py` |
| **D. The hand** | §4, §5 | `static/js/hand/hand.js` (the grid under the lanes), `hand/stacks.js` (a stack under the lane of who asks, a lane's fan), `hand/stopcard.js` and `hand/stopface.js` (the new face), `hand/pluscard.js` (under the first lane, alone), `hand/discard.js` (under the tabs' end), `hand/data.js` (`laneOf`), `hand/hand.css` (the half under the edge), `hand/deck.js` and `hand/deckrow.js` removed, `frame/kinds.js` (only `deck` taken out); `tests/test_hand_desktop_browser.py` |

## 0. The words
*In line* (the first lane's last cascade, its hover); the project's name on the first tab; the stages' words as today
(*Planning*, *Doing*, *Checking*, *Routing*, *Joining*); *Other…*; no *deck* anywhere a person reads (spec 95 §12).
`TERMS`: `in_line` *in line* (`was`: *deck*), `cascade` *cascade* (a goal's tasks in its lane).

## 1. The sign `question` (A, B; §167.3)
A question mark drawn on orkUI's signs' grid (the 7 grid, the signs' stroke and weight, one colour: `currentColor` as
the others), beside `target` in the README's table and the gallery (*a question the person answers*). orkUI 0.15.5,
merged to orkUI's `main`; then copied here (B), `orkui.problems()` empty.

## 2. A card's face on the Board (C; §167.1)
The task card (`table/card.js`, the Board's only; System's parts keep today's map card): 144 wide (`--card-w`),
- **its header**: the goal's element (orkUI's `Elem`, bare, no frame) at the left, then the task's name left-aligned,
  in the pixel face, three lines at most (cut with an ellipsis);
- **its window**: the card's own fill, a hairline (`--ork-card-frame`), its height the sign's and a little room (about
  70 px), one sign at the signs' big size (28 px), toned down (the element's colour at about 60%: an opacity on orkUI's
  token, no colour of its own): **the task's type** (orkUI's type signs: `feature`, `bug`, `screen`, `mechanic`,
  `balance`, `page`, `sound`, … by the task's kind; the goal's type when the task has none);
- **its label row**: the stage's small sign (14 px: `page` for *Planning*, *Routing*, *Joining*; `sword` for *Doing*;
  `shield` for *Checking*) and its word; the gem at its right when it spends (a retry);
- **no foot** and **no head**: who works is on its back (the turned card, §120.1) and in its party's header. A failed
  check's card has the danger frame (as today).

## 3. A goal's cascade, the line, the first tab (C; §167.4–§167.6)
1. **The cascade** (`cascade.js`): in a party's lane, a goal is a thin strip (its element, its name on one line, the
   whole strip a button that picks the goal) over its tasks laid as a solitaire's cascade: **the front one whole** (a
   failed check first, then *Checking*, *Doing*, *Planning*; the most recent first among equals), the others as strips
   above it (about 22 px: the stage's small sign and the task's name, each a button that lifts its task). No count.
   Collapsed always but **the picked goal's**, which unfolds into whole cards in the same order. The cascades of a lane
   lie in the hand's order (the goals' urgency: a failure, then a question, then the rest by their place in line).
2. **A goal in two lanes at once** (the first lane joining its sections while its party works): its strip in both;
   picked, both strips lit alike (orkUI's `.ork-picked`).
3. **The first lane** holds what is the whole project's: the routing and joining cards (each a card a goal, under its
   strip), and last **the line** (*In line*, `lineNow()`: the nodes whose `place` is `deck`, in the Orkmaster's order):
   a cascade of goal cards (its element, its name, its goal's type in the window, *In line* in its label row; the moon in
   its window when `waits_as` is `reset`, its hour on hover); a strip pressed picks its goal; a goal dragged among them
   moves it (`ideas.move`, as `deckrow.js` did: a drop among another party's goals goes back); past about seven, *All ·
   search* opens the line over the pane (kind `line`, `line.js`: the list with a search, as `deckrow.js`'s list was).
4. **The first tab** (`tabs.js`): the project's name with the crowned head (*Party game*); its popover and **…** as
   today. The pane's title keeps *· through the Orkmaster*.
5. **The grid**: the tabs and the Board read the frame's `--cols` (every lane `--col-w`; narrower when they don't fit;
   no sideways scroll); `table.css` no longer defines `--cols` nor `table.js` `--tabs`.

## 4. The hand under the lanes (D; §167.1, §167.7, §167.8)
1. **The grid**: the hand's row reads the frame's `--cols`, its padding the tabs', so a lane's cards stand under its tab.
2. **Under the first lane** the **+** card alone (no deck: `deck.js`, `deckrow.js` and the `deck` kind go), and the
   Orkmaster's stacks fanned beside it (what is the whole goal's: today's rows with no party of their own; spec 100's
   `route`, `talk`, `decision`, `fork` when they come).
3. **A stack under the lane of who asks** (`data.js` `laneOf(row)`: a failure its task's party; a party's question its
   party; the project's questions their leader's party; else the first lane). A goal's cards from one party are one
   stack, its most urgent in front, its edges hinting more (five at most, no count). **Two goals under one lane fan
   within its width**: the urgent in front, those behind showing their edge and element only (no words), each rising
   whole on hover or a press; a stack pressed picks its goal; a picked goal's stacks lit alike (`.ork-picked`).
4. **The discard under the tabs' end** (§167.7: under the limits' chips and *Stop all*, the grid's last column), whatever
   parties the project has.
5. **A card's face** (`stopcard.js`, `stopface.js`): the header as the Board's (the element at the left, the name
   left-aligned, three lines at most); the window low with the action's sign (`alert` for a failure, `question` for a
   question, `check` in the discard) and **the asker's head** (its leader, 24 × 22) small in its corner; the label row
   the party's name and the gem at its right when it spends; the foot the question or the line (two lines at most).
6. **Half under the edge** (§167.8): at rest the hand shows its cards' header and window; the label row and the foot
   lie under the window's edge; a card rises whole on hover, on keyboard focus and on a tap, and a press lifts it as
   today (its answers, its cost's words, *Put it back*). The table gains what the hand gave back.

## 5. The narrow width (C, D; §167.9)
Under 760 px: the lanes a token wide as today, **a goal one token** with its stack's edges (its element, its front
task's type and stage), a press opening its tasks over the pane as today's lifted card; the hand **a free row in the
lanes' order** (the + card first, the stacks, the discard last), its cards at the narrow size, half under the edge as
on the desktop; no sideways scroll at 390.

## 6. Tests
Each at both widths (`tests/narrow.py`). C: a task card's header, window (the type's sign, no head) and label row (the
stage's sign and word, a gem only on a retry); a goal's strip and cascade with its front by the rule, collapsed, the
picked goal's unfolded, a strip lifting its task; a goal in two lanes lit in both; the line in the first lane in the
Orkmaster's order, the moon on a goal waiting for the reset, a drag moving it (`ideas.move`), *All · search* over the
pane past seven; the first tab the project's name; the tabs and the lanes one width, no sideways scroll; `TERMS`'
`in_line` with `was` *deck*. D: no deck; the + card under the first lane; a stack under the lane of who asks, two goals
fanned within a lane, the back one's edge only and its rise; the discard under the tabs' end; a card's header, window
(the action's sign and the asker's head) and label row (the gem at its right); the half under the edge and its rise on
hover, focus and tap; a press lifting as today. The critical tests (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`), `tests/test_design_system.py`, `tests/test_gui_wording.py`.
