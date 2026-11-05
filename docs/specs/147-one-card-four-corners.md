# 147. One card, 5 : 7, read by its four corners

Decisions §251. **Builds:** the cheaper model: A first (the corners every later part uses); then B and C, each in its
area; then D (after C) and E (after B); F last · **Review:** the critical tests and each part's own · P1. The look:
`docs/mockups/card-ratio/` (sections 1–6).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The corners** | one corner row at the top and one at the foot of every card; a lane's card and the discard's wear them | a new `table/corners.js` + `corners.css`; `table/card.js`, `table/discard.js`, `table/work.css`; `tests/test_table_desktop_browser.py`, `test_cascade_card_browser.py`, `test_discard_table_browser.py`, a new `test_corners_browser.py` |
| **B. The Orkmaster's column** | two piles of backs (a loose pile, a squared deck with its next to start named), *At work* standing at 144 × 202 with its corners; 160 px, 13 px under the edge; never scrolls, *At work* gives way | `table/piles.js`, `table/column.js`, `table/column.css`, `frame/frame.css`, `realm/lexicon.py`; `tests/test_column_browser.py`, `test_column_tuck_browser.py` |
| **C. The hand's card** | 144 × 202 cut at 100 under its title, its corners; why, who, how much below the cut, shown when it rises; the narrow page's hand laid by leader | `hand/stopcard.js`, `hand/stacks.js`, `hand/hand.css`, `hand/hand.js`; `tests/test_hand_desktop_browser.py`, `test_hand_context_narrow_browser.py`, `test_hand_mana_browser.py` |
| **D. The opened card and a new goal** | 404 × 566 with its corners, the body scrolling, the cost of the way picked; a new goal's card with its corners dashed until they fill | `hand/stopcard.js` (the lifted card), `hand/answers.js`, `hand/pluscard.js` and the field's modules, `hand/hand.css`, `realm/lexicon.py`; `tests/test_lifted_card_browser.py`, `test_field_*_browser.py` |
| **E. A goal's start and a goal that asks you** | the back turns up and stands in *At work*, the Orkmaster deals the goal's card to its parties' lanes; a back that asks you is dealt to the hand | `table/column.js`, `table/flight.js`, `table/laying.js`, `hand/hand.js`; a new `tests/test_start_deal_browser.py` |
| **F. The phone** | the crown's piles as the column's (a list that may scroll), the hand laid by leader at 80 × 112 cut at 62, the opened card 5 : 7 at the screen's width but while typing | `hand/upmenu.js`, `hand/uprow.js`, `hand/upright.js`, `hand/upright.css`, `hand/upmenu.css`; `tests/test_phone_menu_browser.py`, `test_phone_look_browser.py` and the `upright` tests |

## A. The corners

1. **`table/corners.js`** exports `CornerTop({ rune, kind, signal })` and `CornerFoot({ who, much, ask })`: two rows
   20 px tall (24 px on an L card), `space-between`. `rune` is the goal's element (`Elem`, 14 px); `kind` an orkUI `Sign`
   (14 px) coloured by `signal` (`alert`, `danger`, `success`, else the muted ink); `who` one to three `Head`s at 16 px
   with an optional word (*a Grunt*); `much` a gem (`ork-gem share`) or a short time (*12 min left*, *took 2 h*), or
   *asks you* in the alert. A pure `muchOf(state)` picks the one figure: before it is agreed its cost, at work its time
   left, done the time it took, waiting for you *asks you*; nothing known draws nothing. `corners.css` is layout only.
2. **A lane's card** (`table/card.js`) is 5 : 7 at the frame's `--card-w` (144 × 202): `CornerTop` (its goal's rune, the
   task's kind sign), the title in two lines, the window onto the work as §249.3 has it (unchanged inside), `CornerFoot`
   (the seat's head and its word, the time left or the time it took). Its former label row is the foot.
3. **The discard's card** (`table/discard.js`): `CornerTop` (rune, the done sign in success), the name in four lines, the
   line *N tasks, in main since HH:MM* when the snapshot has it, `CornerFoot` (the heads that did it, the time it took).
4. Tests (`test_corners_browser.py`): every card on the table, in the column's *At work*, in the hand and the discard has
   one top row and one foot row with the rune first and the kind last; the sign and the head are 14 and 16 px on every
   card; a lane card is 5 : 7.

## B. The Orkmaster's column

1. **The sizes** (`frame/frame.css`): `--column-tuck: 13px`; `--column-w: 160px` (the card's 144 and its gutters).
2. **In analysis** (`piles.js` `DownCard`, `column.css`): backs 157 × 112 on their side, 13 px under the edge; the pile
   **loose**: the cards behind the front at −2.5°, 2°, −1.2°; the front card's ring runs (`ACTIVE`, as today); under the
   title the goal being read (`underOf`, as today).
3. **To review**: the same backs, a **squared deck** (the cards behind 3 px apart, unturned). Each back's seal is orkUI's
   `.ork-sigil.is-waiting` with `--ork-sigil-share` its wait's share (`shareOf`), the lit runes in its goal's colour; a
   goal waiting for the person: the ring full, still, in the alert, and the card's frame in the alert. Under the title
   **`next in <time>: <goal>`** for the next to start by itself (`nextWords`, a `TERMS` entry `next_in`); a goal held or
   asking is never *next*. A back pressed picks its goal (its spec in the pane), as a face-up card did.
4. **At work · later**: face up, standing, **144 × 202**: `CornerTop` (rune, the goal's kind), the name in up to four
   lines, what it does now (two lines), the wait's bar where it waits, `CornerFoot` (the leaders at work, how much). The
   foot row is 26 px with the card's padding: a card behind the front shows exactly it.
5. **It never scrolls** (`column.css` `.col-scroll` `overflow: hidden`; `column.js` measures with a `ResizeObserver`): a
   pure `giveWay({ room, front, behind })` → `{ steps: [26 | 3 …], sunk: px }`: every card behind *At work*'s front a
   foot (26) while it fits; then edges (3), the furthest first; then the pile sinks by what is still missing, rounded up
   so the hand's rim falls between two lines of the front card (its top 32 px, then 20 px a line), the cards behind it
   moved 3 px to the right each. *To review*'s and *In analysis*'s cards keep their places. A card hovered or focused
   slides out whole (as today: 36 px and 2°; a back by the tuck).
6. Tests: the column has no scrollbar at 650, 790 and 940 px of window; at 650 *At work*'s front shows its rune row and
   its cards behind are edges or slivers; at 940 every card behind shows its foot; *To review* names the next to start;
   a goal that asks is a back with the alert ring and frame; `giveWay` in a JS unit test or through the page.

## C. The hand's card

1. **The card** (`stopcard.js`, `hand.css`): 144 × 202. `CornerTop` (its goal's rune, the kind's sign in its signal's
   colour, as the frame is), the title in three whole lines; then, under the cut, the card's foot words (*why*: the
   question or the line, today kept for a screen reader only) in up to three lines, and `CornerFoot` (the asker's head,
   the card's cost as `cardCost` gives it). **Not on the face**: the asker's head at the top, the party's label, the gem
   at rest.
2. **The cut**: `--hc-shown: 100px` (the card's padding, the corner row and three lines of 20 px); `.hand-places` clips
   at the hand's height; the hand is as tall as the cards' 100 px, the die and the potions need (`mana.css`), and where
   they need more the cards keep their top and show more, the cut kept between two lines. A card hovered or focused
   rises by `202 − shown` and shows itself whole (`--hc-rise`); under reduced motion it is whole at once.
3. **The stacks' fan** (`stacks.js`) and the + card follow the new heights; the + card keeps its 5 : 7 standing over the
   table's foot (§249.2).
4. **The narrow page** (under 760 px): the card 80 × 112 cut at 62 (corner row 16, the title in two lines of 18); the hand
   **laid by leader**: before each lane's cards a 22 px separator with the leader's 16 px head (the Orkmaster's crown head
   for the column's lane), in the lanes' order.
5. Tests: a hand card shows its rune and kind at the top and no head there; its title is not clipped; the hand's visible
   height is the cut plus its padding; hovered, the card shows its foot row (who, how much); the narrow hand has a head
   before each leader's group.

## D. The opened card and a new goal

1. **The opened card** (`stopcard.js`'s lifted card and the kinds that open like it): 404 × 566 (`aspect-ratio: 5 / 7`,
   never taller), `CornerTop` large (the goal's rune and name, the kind's sign and word), the title, a **body that
   scrolls** (`overflow-y: auto`, a fade at its foot), the field and the buttons above `CornerFoot` (the asker's head and
   *the <party> leader asks*, the cost of the way picked). Picking an answer (`answers.js`) changes the foot's cost to that
   way's when the answer has one, else the card's cost.
2. **A new goal's card** (the + card's field, `pluscard.js` and its modules): the same 404 × 566 card. Its corners are
   dashed slots that say what will stand there (`TERMS`: *the rune: given when it is laid*, *who: the Orkmaster routes
   it*, *how much: after its estimate*); the kind's corner fills when a kind is picked (the goal types of §65, where the
   field offers them), who when the party is known, the rest when the goal is laid. The field's own controls are as
   today, inside the body.
3. Tests: the opened card is 5 : 7 and its body scrolls with a long question while its foot stays in view; picking a way
   changes the foot's cost; a new goal's card has three dashed corners and the kind's fills when one is picked.

## E. A goal's start and a goal that asks you

1. **The start** (`column.js`, `flight.js`, `laying.js`): when a goal passes from *To review* to *At work* between two
   snapshots, its back turns face up (orkUI's `.ork-turn`) and stands at *At work*'s front; then a card of the goal flies
   from it to the strip of each party doing it (its tasks' parties) and folds into the strip, where its tasks rise as
   §70 lays them. One motion that travels (§70.2): six steps at most, about 0.3 s a step, none under reduced motion, a
   hidden page or into a lane under the pointer; several starts in one snapshot deal the first and lay the rest.
2. **A goal that asks you**: its card in the hand comes from its back in *To review* (the alert ring): the back lifts,
   turns up and stands on its way, and lands in the hand under the asking leader's lane (the flight of spec 128 C.2 from
   the column instead of a lane).
3. Tests (`test_start_deal_browser.py`): a snapshot moving a goal from review to work turns its card and flies one card
   per party (counted by the flight's elements) and none under reduced motion; two starts at once fly one.

## F. The phone

1. **The crown's piles** (`upmenu.js`): the column's cards as part B draws them, the backs 13 px under the screen's edge,
   each pile's words beside it (*reading:*, *next in*); a list that may scroll.
2. **The hand** (`uprow.js`, `upright.css`): laid by leader, the 80 × 112 card cut at 62, a 22 px separator with the
   leader's head before each group; pressed, a card rises and shows the rest; tapped, it opens.
3. **The opened card**: 5 : 7 at the screen's width; while the keyboard is up (`visualViewport` shorter than the window),
   its top corners and its title in two lines, then the field, as tall as the screen leaves.
4. Tests: the crown's menu has the two piles of backs and *At work* standing; the phone's hand has a head before each
   group; the opened card is 5 : 7 without a keyboard.
