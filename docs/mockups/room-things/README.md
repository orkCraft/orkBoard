# The room's things: the lamp's chain, the backpack, the new chair

A mockup the owner and Claude made on 8 November 2026: the top row's three controls drawn as things at the table. A layer
of CSS and JS over the live page, drawn over `../table-look/` and reusing `../answer-cards/`' cards; **nothing here is in
the product**. Each of the three goes against a written decision (the door, §246.4–5; the stall's stitched edge, §267.1;
*New party* as a place over the pane, spec 98 §3.6), so each needs a new one before it is built.

## What it shows

- **The lamp's chain, where the door stood** (the owner): bronze links from the window's top edge and a bead to pull, its
  words beside it as the door's were (*Here · until 23:00*, *Away · until 19:00*). **Lit, the person is here**: the light
  down the table from its top edge (`../table-look/`). **Out, the person is away**: the table's light goes, the felt flat
  and darker, the lanes unlit but for the rule under their tabs; the cards keep their faces and a signal stays as bright.
  Pulled, the chain hangs longer and the bead lower.
- **The backpack and the chain share the head of the window's right column** (the Release column, the discard), over its
  label: 188 px holds both, the column is not widened; the tabs' row ends with the new chair.
- **The backpack**, drawn in pixels: shut (the flap down, its buckle fastened) and open (the flap thrown back, a card in
  its mouth). **Open, the table lies in its leather**: a leather frame with its stitches in place of the bronze, two straps
  with their buckles over the top edge, no rivets. Shut, the bronze is back.
- **The new chair deals its crafts to the hand**, as a question's answers are (`../answer-cards/`): pressed, it is lit,
  the Orkmaster's question rises onto the table (*A new chair at the table · Which craft sits in it?*), the hand holds a
  card a craft not yet seated (here LiveOps and Marketing, the race's head as its sign, its line, its price in the foot),
  **the Orkmaster's pick marked with a star** in the top corner, seen while the card lies cut in the hand. The rest of the
  hand sinks, grey.
- **The pick opens the backpack on that craft**: the craft is a new tab where the chair stood (its leader's head, its
  pennant, *new*), the stall opens on its chair, its heroes are the wares on the rug (Growth Hack Gnome, the default, the
  star on it and *in your hand*; Store Gnome), a price plate under each, and a hero can be changed there as any ware.

## Open

- **Two clicks to seat a craft, not one**: the chair lays the crafts, a card pressed seats it. A seated craft spends
  every week, and money is never spent by a press that does not say so (§57.3, §160.6); the price is on the card.
- **What the lamp says when the hours lead** (§246.4: the hours open and shut the door by themselves; a pull holds the
  other state until the next edge): the chain is pulled by the clock too, and *· held* after a pull, as the door said.
- **The phone** has no light over a table: its top row needs the lamp as a small mark (a bulb on its chain), not shot.
- The prices (*+9% a week*) and the heroes' lines are the mockup's; the stub host has no door and no wares.
- The backpack, the chain and the buckles are drawn here in CSS and SVG with their own colours: in the product they are
  orkUI's drawings and tokens (the chair's and the door's are already orkUI's).

## Files

- `room.css`, `room.js`: the mockup (`room.js` takes a mode: `on`, `off`, `chair`, `pack`).
- `shoot.py`: the camera (its docstring has the command; `MOCK_BEFORE=1` for the top row as it is).
- `shots/`: `before-*` as it is (the board, *New party*'s place, the stall), `after-*` the board with the lamp lit, the
  lamp out, the chair's crafts in the hand, the stall open on Marketing.
