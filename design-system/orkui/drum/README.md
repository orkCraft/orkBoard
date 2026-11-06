# orkUI / office / drum

The drum: **a row of potions laid as a drum seen from the front** (orkBoard's decisions §261.13 and §262.1, spec 156 part A; orkUI 0.31.0). Orkboard draws the AI tools' limits as a drum
under the discard: the tool at work in front at its own size, the tools beside it behind it, small and dim, so three bottles stand where one used to, and one that runs low steps out beside the
front where it is seen. Plain HTML and CSS, no script and no inner markup of its own: the drum holds `.ork-potion`s (`potion/README.md`) and nothing else.

    <span class="ork-drum" style="--ork-drum-front:1" aria-hidden="true">
      <span class="ork-potion" style="--ork-drum-at:0;--ork-potion-left:.8"></span>
      <span class="ork-potion size-medium" style="--ork-drum-at:1;--ork-potion-left:.62"></span>
      <span class="ork-potion size-small" style="--ork-drum-at:2;--ork-potion-left:.4"></span>
    </span>

- **Places**: each potion says its place in the row, **`--ork-drum-at`** (0 for the first); the drum says which is in front, **`--ork-drum-front`** (its index, 0 when not set).
- **The front** is at its own size: 3 px a cell, any of the four bottles (`size-medium`, `size-small`, `size-vial` or the large) with its own `--ork-potion-left`, `is-warn`, `is-danger`.
  **Its two neighbours** (the places one before and one after it) are drawn at **`.small`, 2 px a cell** (the drum sets the cell, so no class is needed and a bottle is **never scaled**), each
  **half behind the front** (its middle on the front's edge) at **brightness 0.62**. **The others are hidden** (opacity 0, standing behind the neighbours); a hidden potion is still in the markup,
  so the page may draw them all. The drum sets `pointer-events: none` on its potions: the page makes the drum itself the thing to press.
- **A neighbour `.is-alert`** (the page's choice: a tool at the warn or the danger level) stands **at full brightness, beside the front and not behind it**, with room under it for its share in
  words (the 18 px under the bottles: the caller's text, in its level's colour). The drum is then wider (`:has(> .is-alert)`). Put `.is-alert` on a neighbour only.
- **The box at rest is 88 x 90**: the front's 42 at the middle, a neighbour's 28 half behind it, 18 above for the caller's mark and 18 under for its share (the bottles stand 18 px above the
  box's foot). **With an alert neighbour it is 124 x 90**; the front then stands 62 px from the left, so an alert on either side has 48 px to speak in.
- **Turning**: change `--ork-drum-front` and the drum turns: each potion **slides one place round** (a `transform` on `--ork-motion-base`, `--ork-motion-ease`); under
  `prefers-reduced-motion` it moves at once. The cell (2 or 3 px) and the brightness change at once and are never tweened: no scale, no half pixel. A potion that goes more than one place away
  fades behind its neighbour; turn by one place at a time.
- **`.is-open`** lays the drum as a plain row (`inline-flex`, a gap of `--space-2`): every potion at **its own size** (3 px, `.small` 2 px if the potion has it), nothing dimmed, in the order of the
  markup, the box as wide as the row, the potions pressable (`pointer-events` back).
- **No colour, font or corner of its own**: the potions' tokens only (`tests/test_orkui.py` checks that the drum's rules hold no colour).
