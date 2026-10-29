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

## As built A

orkUI 0.17.0 (orkUI bcbaaa2, copied e64a2f5): `--ork-mana` is `#7b97b8` (L* 61.5, a little under the muted ink; the mockup's
`#5f7fa6` fell to 3.3:1 on a card); `.ork-potion` is CSS only (three 14 × 18 masks in `office/potion/`), the level stepping by
an eighth of the body rounded up (so 4 % shows a row), the spend a one-cell checker.

## As built D

`Lifted` (`hand/stopcard.js`) draws `ork-card hand-card hand-card--stop hand-card--big hand-lifted` (an `aside`, the element's `el-*`, `asks` and `fails` as the hand card has them): `.hand-card__head` (the element and the name, which is also
`.hand-lifted__title`), `.hand-card__window` (the action's sign, the asker's head over its corner), `.hand-card__label` (the party and the gem), `.hand-lifted__body`, `.hand-card__foot`. Its CSS is `.hand .hand-card--big` in
`hand/hand.css` (the old panel's rules and `.hand-lifted__top` are gone); `way.css` hides the route's and the start card's own `Spend` inside `.hand-lifted__body`. Tests: `tests/test_lifted_card_browser.py` (anatomy, twice a
hand card's width, the screen's width less a gutter a side, the lean, the foot on the hand's line, a long body scrolling, Esc); `tests/test_design_system.py` allows `--hc-tabs` and `--hc-lean`.

What differs from §5, or is not said there:

- **The foot says what the card is** (`.hand-lifted__kind`: *Plan ready*, *Route*, *Decision 118*), not the hand card's question or line. The body holds that text in full, so the foot repeating it would say it twice, and the tests
  that read `.hand-lifted__kind` keep reading it. The party in the label row is the card's own party (`s.party.name`, the stop's label with none), always, where the panel said it only on another party's tab.
- **The gem is on the label row and in the cost's words** (`Spend`), as the hand card and the panel each had it: a lifted card that spends shows it twice.
- **The turn** is `--ork-motion-lean` × 0.25 (1.5°) on the desktop, × 0.17 (1°) at the narrow width, to the left (-1) or right (1) by which half of the hand its stack lies in (`--hc-lean`, set from the anchor in `Lifted`);
  orkUI has no `--ork-lean` token. It turns about the foot's middle on the desktop and about the card's centre at the narrow width, so the full-width card's corners stay inside the gutter.
- **Its height** is the hand card's 5 : 7 at twice the width at the least on the desktop (403 px), and at most `100dvh` less the hand, `--hc-tabs` (52 px, 56 px narrow) and `--ork-4`. At the narrow width it has no least height:
  at 5 : 7 a screen-wide card would be 500 px of nothing for a short question. The name takes up to four lines in the body face, its row `minmax(--ork-6, auto)`, not the hand card's fixed three.
- The foot stands on the hand's line (`bottom: 100%` of the hand, no gap, where the panel stood `--ork-4` above it); the slot, `useAbout`, focus, Esc and a press away are as they were.
- `hand.js` finds the anchor in `.hand-places`, since the lifted card now has the class `hand-card` too (tests that locate `.hand-card[data-kind]` while a card is lifted say `.hand-places .hand-card` for the one in the hand).
- The body's scroll has no visible bar (the project hides them elsewhere); a long body's *Put it back* is reached by scrolling, Esc lowers the card at once.

## As built B (the mana in the hand)

Built in `orkboard/gui/static/js/hand/mana.js` and `hand/mana.css` (loaded by `frame/frame.js` with the other sheets); tests in `tests/test_hand_mana_browser.py`.

- **`Mana`** reads `town.value?.limits` (the chips' data and order) and draws one `.ork-potion` a tool inside a button `.hand-pot` (`data-provider`, `data-level`), the tool's mark above it, the share under it. Marks are the coloured
  `marks/harness-<id>.png` with the `@2x` as `srcset` (`MARKED` from `table/data.js`, the same list as `arena/limits.js`); a tool with no mark shows its initial in the body face. The share is `62%` in the caption size, in
  `--ork-alert` at `levelOf` warn and `--ork-danger` at danger. The words are the chip's, with the window in words: *Claude Code: 62% of the week left* (`windowWords`: `week` the week, `5h` the 5-hour window, `daily` the day),
  as `title` and `aria-label`; the potion itself is `aria-hidden`. A press is `openOver("limits", { provider }, from, "<name>: what used it")`, as the chip's. A tool not read is an empty potion (`--ork-potion-left:0`), *?* under it,
  *Claude Code: limits not read yet*.
- **Rows**: one to three tools one row at the default size; four to six two rows of three, `.small` (`data-rows`); more than six: the first five and *+n* (*n more tools: what is left of them*), which opens
  `openOver("limits", {}, …)`. At the narrow width (under 760 px) every potion is `.small`.
- **The spend**: `costOf(s)` (`hand/cost.js`) now also says `tool` (the id the host's rate names, `rate.tool`, Claude with none), `spend` (0 to 1 of the window, the card's high price over the learnt rate; 0 for a card that saves or with no
  rate) and `taken` (`4%`); `spend.js` gets `shareOf`. `Hand` passes the lifted stop to `Mana`; that tool's potion gets `--ork-potion-spend`, its share reads `62% −4%` (on the same line: the potion's cell widens, the hand's height does not
  change) and its words add *This card takes about 4% of it*.
- **Place**: `.hand-end` holds `<Discard />` and then `<Mana />`; the hand row has no right gutter, so the potions touch the window's right edge. At the narrow width `.hand-end` is `display: contents`, the pile keeps its place
  (it takes the least a card shows, its card over the row's spacer) and the potions are the row's last place. `table/tabs.js` draws no chip at the tabs' end (+ and *Stop all* only); `LimitChip` stays exported, because
  `table/pane.js` draws it in the Orkmaster's **…** at the narrow width.
- **Height**: the hand keeps the cards' height for one row. Two rows (four tools and more) need 152 px (156 on the phone's type) against the cards' shown 133–146 px, so `.hand:has(.hand-mana[data-rows="2"]) .hand-places`
  grows to `max(the cards', room + top + --hc-pots)`: on the desktop the hand is about 20 px taller with six tools, on the phone with four or more about 70 px taller (the cards tighten to their left edges as they already do).
  `--hc-cap` and `--hc-pots` are the hand's own sizes (named in `tests/test_design_system.py` with the others).
- **A hand with no goal at all** (the + card large in the pane's middle, no row) shows the potions alone at its right end (`.hand-mana-only`), so the limits are not lost on a project's first day.
- **Not done here** (C and D): the discard stays in `.hand-end`, beside the potions; a lifted card is still the panel.
