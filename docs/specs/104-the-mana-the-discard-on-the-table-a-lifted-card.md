# 104. The mana in the hand, the discard on the table, a lifted card as a card

Decisions §175.2–§175.3 and §176; the mockup `docs/mockups/mana/` (the potion, two tools and six, flush right; v3: the blue
mana, the discard on the table, a lifted card as a card). This changes spec 101 §4.4 (the discard under the tabs' end) and
§4.5 (a card lifted over the pane's foot as a panel), and spec 98 §2.3's limits' chips at the tabs' end.

## 1. What changes

- The AI tools' limits leave the tabs' end: it keeps **+** (*New party*) and **Stop all**. Each tool is a **potion** at the
  hand's right end, flush against the window's edge.
- The **discard** leaves the hand and lies on the **table**, at its last column's foot, at the right, on every tab.
- A **lifted card** is a card: the hand card grown about twice, its body holding what the panel held.

## 2. Part A (orkUI 0.17.0): the potion and the mana's blue

In orkUI (github.com/orkCraft/orkUI), never in Orkboard's copy; then copied (`python -m orkboard.design.orkui <orkUI>`).

1. **`--ork-mana`**: a dim, desaturated blue that reads on the office's dark ground at about the muted ink's brightness
   (never brighter than `--ork-ink-muted`'s lightness by more than a little; the mockup's stand-in `--mana` is its start).
   Its role in orkUI's README: *the mana's liquid while there is room to spend*, a signal, used by `.ork-potion` alone.
2. **`.ork-potion`**: a round bottle with a neck and a cork on a 14 × 18 pixel grid (the mockup's drawing), its edge
   `--ork-edge`, its glass `--ork-panel`, its cork the muted ink, its liquid filling the round body from the bottom by
   `--ork-potion-left` (0 to 1, the share left; the liquid's top a pixel row, never a slope), with a lighter highlight
   pixel column.
   - States: `.is-warn` (`--ork-alert`), `.is-danger` (`--ork-danger`), otherwise `--ork-mana`.
   - `--ork-potion-spend` (0 to 1): that share of the liquid's top hatched in the checker (orkUI's hatching), for a card
     lifted that would spend it.
   - Sizes: the cell 3 px (42 × 54) by default, `.small` 2 px (28 × 36). Crisp at any zoom (`image-rendering`, whole
     pixels; drawn as an inline SVG or as CSS grid of cells, whichever orkUI's other drawn components use).
   - No words inside: the caller says the share.
3. The gallery shows the potion at both sizes, full, at 62 %, at 18 % (warn), at 4 % (danger) and at 62 % with 4 % spend;
   the CHANGELOG's 0.17.0 says it.

## 3. Part B: the mana in the hand (`hand/mana.js`, `hand/mana.css`)

1. `Mana` at the hand row's right end, flush against the window's right edge (no gutter of the hand's own on that side but
   orkUI's smallest), from `town.limits` (the chips' data): one `.ork-potion` a tool, in the order the chips had.
   - One to three tools: one row at the default size. Four to six: two rows of three at `.small`. More than six: the first
     five and a sixth place *+n* that opens the limits over the pane (`openOver("limits", {})`).
   - Above each potion the tool's mark **in its own colour** (`marks/harness-<id>.png`, the ids `MARKED` has in
     `arena/limits.js`; a tool with no mark its initial in the body face); under it its share, `62%`, in the caption's
     size, in the warn or danger colour at those levels (`levelOf`: warn at 20 % or less, danger at 5 % or less).
   - A potion is a button: its words for a screen reader and the title *Claude Code: 62% of the week left* (the chip's words,
     `windowOf`); a press opens what used it over the pane (`openOver("limits", { provider })`), as the chip did.
   - A tool whose limits were not read: an empty potion, *?* under it, its words say so.
2. While a card is lifted and spends (`costOf(s)` names a provider and a share), that tool's potion gets
   `--ork-potion-spend` and its share reads `62% −4%`.
3. `table/tabs.js` draws no `LimitChip`; the chip's words move to `Mana`. At the narrow width the limits stay in the
   Orkmaster's **…** as today and the hand shows the potions too, at `.small`, at its row's end.
4. The hand's height is the cards' (the potions fit beside them: two rows of `.small` with marks and shares within the
   hand card's shown half); if not, the hand grows by what the potions need and no more.

## 4. Part C: the discard on the table (`table/discard.js`)

1. The pile (`Discard`, today `hand/discard.js`) moves to `table/discard.js` with its view (`DiscardView`, the `discard`
   face registered as today); the hand imports nothing of it. It lies in the table's last grid column (the one right of the
   lanes, `--cols`' `minmax(280px, 1fr)`), at its foot, aligned right, the hand card's size, on **every** tab.
2. On a party's tab, whose last column holds the party's map (`table/pane.js`, `mapOf(g)` narrow), the map ends above the
   pile: the column is a flex column, the map `flex: 1; min-height: 0` (it scrolls as today), the pile under it.
3. The pile is what it was (spec 101 §4.4): the last goal done face up, the backs under it, the lich's head and
   *n goals ready for main* while the gate holds goals; pressed, it opens over the pane. It leans and rises on hover as a
   card does (`leans`); none with nothing done and nothing ready.
4. The hand's row: the + card and the stacks at the left, the potions at the right; the width the pile had goes to the
   stacks (`.hand-end` holds only `Mana`).
5. At the narrow width the pile lies at the lanes' end on the table (the place the mockup's 390 case gives).
6. CLAUDE.md's frame line says the discard lies on the table (done with §176).

## 5. Part D: a lifted card is a card (`hand/stopcard.js` `Lifted`, `hand/hand.css`)

1. `Lifted` draws a card, not a panel: `ork-card hand-card hand-card--stop hand-card--big` with the hand card's anatomy in
   the same order (`.hand-card__head` element and name, `.hand-card__window` with the action's sign and the asker's head,
   `.hand-card__label` with the party and the gem, `.hand-card__foot`), at twice the hand card's width (`--hc-w` × 2) in its
   proportions at the least, turned by a degree (`--ork-lean` of its stack's side, 1–2°).
2. Its **body**, between the window and the foot, holds what the panel held: a way's own `Lifted` (`wayOf(s.kind).Lifted`),
   else `Body` and `Answers`; then `Spend` and *Put it back*. The body scrolls inside (`overflow: auto; min-height: 0`) when
   the card would pass its most height (`calc(100dvh - <the tabs' height> - <a gutter>)`); the card never grows wider.
3. It stands with its foot on the hand's line at its stack's place (the anchor's left as today, kept inside the window),
   over the cards beside it and the lanes' foot (`z-index` as the panel's); the slot it rose from stays as today.
4. Keyboard and reading are the panel's: `role="dialog"`, focus on it when lifted, Esc and a press away lower it,
   `aria-label` *Lifted: …*. The cards of the table it is about rise as today (`useAbout`).
5. The narrow width: the card's width is the screen's less `--ork-4` a side, rising from the hand; the body scrolls.
6. The tests that read `.hand-lifted` keep the class on the card (`hand-lifted` stays its hook).

## 6. Order

A and D at once (D needs nothing of A); C after D (both touch `hand.css` and `hand.js`); B after A's copy and C.

## 7. Tests

- orkUI: the potion's gallery entry, its states and sizes (orkUI's own tests).
- `tests/test_design_system.py`: `--ork-mana` is orkUI's; Orkboard's sheets add no colour.
- The hand's browser tests: the potions' order, rows and words; the spend on a lifted card; the press opens the limits; the
  tabs' end has no chip; the discard on the table on the Orkmaster's tab and a party's, its press; a lifted card's class,
  width (about twice a hand card), its body scrolling, Esc.
