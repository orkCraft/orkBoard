# 141. A card picked by its rune

Decisions §248. **Builds:** the cheaper model, O first (orkUI), then P in the page's areas (spec 140's and 142's agents
take P's lines in the files they own) · **Review:** the critical tests and each part's own · P1. The look: the decision's
text; orkUI's `office/README.md` for how a class is written and tested.

| Part | What | Where (and its tests) |
|---|---|---|
| **O. orkUI 0.29.0** | `.ork-picked` redrawn: no brackets; the card risen, its edge in the ink, a rune inside it lit and still; the brackets moved to a new `.ork-taken` | orkUI `office/components.css`, `office/README.md`, `CHANGELOG.md`, its version; `tests/test_orkui.py`. Then copied into Orkboard: `python -m orkboard.design.orkui /home/user/orkui` (`design-system/orkui`, its stamp `ORKUI.json`) |
| **P. The page** | `.ork-picked` stays on a goal's cards; `table/picking.js` (and `picking.css`) take `.ork-taken` | column: `table/piles.js`, `backcard.js`; hand: `hand/stacks.js`, `stopcard.js`, `choose.js`, `questions.css`; lanes: `table/card.js`, `cascade.js`; table's end: `table/portal.js`; picking: `table/picking.js`, `picking.css`; `tests/test_picking_desktop_browser.py`, `test_column_browser.py`, `test_hand_desktop_browser.py`, `test_portal_browser.py` |

## O. orkUI 0.29.0

1. **`.ork-picked`** (today `office/components.css` §*picked*: eight ink gradients as corner brackets):
   - no brackets (`::after` gone);
   - `transform: translateY(calc(var(--ork-motion-rise) * -1))` — the rise token, 3–4 px; **never `scale`** (the pixel grid);
   - `border-color: var(--ork-ink)` and a shadow `0 var(--ork-2) 0 color-mix(in srgb, var(--ork-canvas) 70%, transparent)`;
   - a rune inside it, `.ork-picked .ork-elem`, at full brightness and **still**: `animation: none; opacity: 1;
     filter: brightness(1.25)` — but `.ork-picked .ork-elem.is-glowing` keeps its pulse (a goal at work pulses, §248.2).
   - under `prefers-reduced-motion: reduce` the rise stays (it is a place, not a motion); no transition is added.
2. **`.ork-taken`**: today's brackets exactly (the eight gradients), for a map's part taken in picking (§152.4).
3. README: the two classes, what each means (*picked: a card with a rune, the goal picked; taken: a map's part taken in
   picking*); CHANGELOG 0.29.0; the version wherever orkUI keeps it. `tests/test_orkui.py`: the rule's table, if it lists
   classes; `python -m pytest` green.
4. Commit and push to orkUI's `main` (`git -C /home/user/orkui fetch origin main` first). Then in Orkboard
   `python -m orkboard.design.orkui /home/user/orkui`, and `tests/test_design_system.py` green.

If spec 139's part O (the die) is built by the same hand, both go in one orkUI version, 0.29.0.

## P. The page

1. Every place a **goal's** card carries `.ork-picked` keeps it (the list in the table above, but `picking.js`); nothing
   of the page draws the pick itself.
2. `table/picking.js` toggles **`.ork-taken`** in place of `.ork-picked` (line ~115 today), and `picking.css` follows.
3. Tests: in the browser, a picked goal's card has `.ork-picked`, its computed `transform` not `none`, no `::after`
   brackets (`getComputedStyle(el, '::after').backgroundImage` is `none`), its rune's `animation-name` `none` unless the
   task is at work; a part taken in picking has `.ork-taken` and the brackets.
