# The table's look: a mockup

A mockup the owner and Claude made on 7–8 November 2026, after the owner found the window flat. It is a layer of CSS and
JS laid over the live page by a camera script; **nothing here is in the product**, and the product's sheets are untouched.
What it shows would go into orkUI (tokens and components) and `gui/` after a decision.

**It goes against a written decision**: §53.5 says colour is a signal only. The owner said, in the conversation, to drop
that idea; it is not yet written. Writing it (a new decision replacing §53.5, never an edit of it) is the first step.

## What it changes

Colour has three layers, told apart by their form, so they never mix:

1. **The party** (by its race) colours the frame of things: its tab's name and glow, the light falling into its lane, a
   rule under its tab, its pennant, **its table's felt** (each leader's table its own cloth).
2. **The goal's element** colours the face of its cards: a band on top, a tinted face, a lit window round its sign.
3. **A signal** (fails, asks) is the brightest, always rings and an icon, never a fill; nothing else may hide it.

| layer | what | where |
|---|---|---|
| the room and the light | a lamp over the table at its **top edge**: the light comes down the table in half rings, five steps, each step's edge dithered with a 2 px checker in the next step's colour (no smooth gradient anywhere) | `.shell`, `.table-pane` |
| each leader's felt | the Orkmaster's table warm wood; Tech moss; Game design and Product oxblood with a gilt rim; Design and Art plum; Release night blue; Run rust; Marketing sea | `.table[data-tab]` |
| frames | the table, the column, the discard and the hand in bronze frames with rivets at the table's corners; headings on bronze plaques | `vibe` layer |
| the leaders | the open tab in its party's colour and larger; closed tabs' names in a muted party colour; **a swallowtail pennant on a pole** in the party's colour over each leader (not the merchant mockup's craft pennants) | tabs |
| lanes | a party's light down its lane in three steps; an empty lane says whose it is (*Release is free · throw a goal here or @Release*) | `.table-lane` |
| cards | a thick frame in the element's colour with a gilt inner line; the element in steps down the face; the sign's window bevelled; a goal's strip a ribbon | `.ork-card` |
| the hand | a slight fan (cards turned ±2°), a card rising toward you on hover; the hand's rail in steps | `.hand` |

## Not in it (tried and dropped)

- **The craft textures on the tables** (§266.8: Tech's grid, Design's dots, Product's contours, Release's stones): the
  owner dropped them from this look.
- **The merchant mockup's pennants** (a 7 × 9 flag with the craft's motif): replaced by the plain swallowtail pennant above.
- **Heads and signs drawn at twice the grid** by Scale2x: dropped; the heads are their own work, see `../leader-heads/`.

## Known problems

Fixed on 8 November 2026: the pennants stand clear of the window's top edge on a visible pole (a 20 px pennant, 24 px
when open); a signal is one ring and a faint second, and the column's stacked rows show it by their border alone (the
icon says the rest); the fan is only at the desktop's width (on the phone the hand is a stack); the phone is shot with
every layer; the camera moves the pointer off the lifted card before the shot.

- The lifted card lost its signal in the product (`stopcard.js` passed `cls` three arguments): fixed on 8 November 2026,
  with a test (`tests/test_lifted_card_browser.py`); the mockup's `.hand-lifted.alert` and `.danger` rings are no longer needed.
- On the stub, Game design's, Art's and Release's tables are empty; the felt was not checked under real screens and assets.
- The fan and the lift of the hand are motion; the shots do not show them.
- On the phone the open leader's pennant sits at the screen's left edge.

## Files

- `table-look.css`, `table-look.js`: the mockup (the colour layer, the frames and flags, the retro steps, the light at the top edge).
- `shoot.py`: the camera (see its docstring): the table's stub host, before and after, at 1440 × 900 and the phone.
- `shots/`: `before-*` the window as it is, `after-*` with the mockup.

## What would make it the product

1. A decision replacing §53.5: colour is the party, the element and a signal.
2. A decision for the look: the light from the top edge in steps, each leader's felt, bronze frames and plaques, the pennants.
3. A goal (Design, Tech): the party colours, the felts and the steps as orkUI tokens and components (`.ork-table`,
   `.ork-card`, a plaque, a pennant), copied here; then `gui/` (tabs, lanes, hand, empty lanes); a test that a signal is
   always seen.
