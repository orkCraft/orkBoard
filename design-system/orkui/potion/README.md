# orkUI / office / potion

The potion: **a pool shown as a bottle** (orkBoard's decisions §176, spec 104 part A). Orkboard draws each AI tool's limit as one: the
liquid is what is left of the week, and the mana's blue while there is room to spend. It is the one picture of an amount in the window; the
crystals (`.ork-crystals`) stay what is left of a tool in tens.

    silhouette.svg   the whole bottle, the cork included (the edge's mask: the box is the edge's colour, its top row the cork's)
    body.svg         the glass inside: the neck, the shoulders and the round body (the liquid's mask)
    shine.svg        the highlight's cells: the body's left-most cell in each of the liquid's eight rows

Each is a **14 x 18** grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top), `viewBox="0 0 14 18"`,
`fill="#000"`, `shape-rendering="crispEdges"`: no colour of its own, no metadata. The cork is row 0 (four cells), the rim row 1, the neck
rows 2 to 5 (two cells wide), the shoulders rows 6 to 8, the body rows 9 to 16 (ten cells at its widest, four at its foot), the base row 17.

## Writing one

Plain HTML and CSS, no script and no inner markup. The share is a custom property on the element itself:

    <span class="ork-potion" style="--ork-potion-left:.62" aria-hidden="true"></span>
    <span class="ork-potion is-warn" style="--ork-potion-left:.18" aria-hidden="true"></span>
    <span class="ork-potion is-danger small" style="--ork-potion-left:.04" aria-hidden="true"></span>
    <span class="ork-potion" style="--ork-potion-left:.62;--ork-potion-spend:.04" aria-hidden="true"></span>

- **`--ork-potion-left`** (0 to 1, the share left; 1 when it is not set) fills the body from the bottom. The body is **eight rows**, so the
  level steps by an eighth, **rounded up**: any share above 0 shows a row (4 % is one row, 18 % two, 62 % five, 100 % the whole body). The
  liquid's top is always a whole row, never a slope.
- **`--ork-potion-spend`** (0 to 1, 0 when not set) hatches that share at the liquid's top, in a checker of whole cells (the pixel form of
  orkUI's hatching), for a card that would spend it: the same rounding, one row at least, never more than the liquid.
- **Colour**: the liquid is `--ork-mana` while there is room; `.is-warn` makes it `--ork-alert` and `.is-danger` `--ork-danger`. The caller
  decides the levels. The highlight is the liquid's colour lightened toward the ink, as the big signs' light is. The edge is `--ork-edge`,
  the glass `--ork-panel`, the cork `--ork-ink-muted`.
- **Size**: the cell is 3 px by default (**42 x 54**), `.small` 2 px (**28 x 36**); whole pixels, no size between, the same on a phone.
- **No words inside**: the caller says the share, on the control that holds it (`title`, `aria-label`) or beside it; the potion itself is
  `aria-hidden`. It is a box of its own (`inline-block`, `flex: none`) and takes no colour of the text around it.

It needs `round()`, `clamp()`, `mask` and `color-mix()`, which every browser of the last three years has (Chromium 125, Firefox 118, Safari 15.4+).

`--ork-mana` (`#7b97b8`, a dim desaturated blue: CIELAB L* 61.5, about as bright as the muted ink's 69 and a little below it, chroma 20) is
used by `.ork-potion` alone; see `../README.md`. A shape is changed here, in the table of `tests/test_orkui.py` and in orkBoard's spec 104
together, never in a face.
