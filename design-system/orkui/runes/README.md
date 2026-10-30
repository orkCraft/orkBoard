# orkUI / office / runes

**The runes**: twelve marks on a **5 x 7** grid, orkUI's own (orkBoard's decisions §185). They spell nothing and are read by no one, and none is a
letter of a real alphabet: no arrow, no Y on a stem, no lightning, no diamond on legs (`tests/test_orkui.py` keeps a list of shapes no rune may
take). They are the table's one vocabulary of magic: the portal's ring and the + card's seal of summoning are written in them, so a goal is
summoned at the + and leaves through a ring in the same runes.

    runes.json         the source: the twelve runes and the geometry of the ring and the seal (python tools/build_runes.py writes the rest)
    <name>.svg         key, eye, hook, tusks, ladder, spiral, staff, hourglass, diamond, comb, knot, wave: 5 x 7
    ring-dots.svg      the portal's ring: a dotted circle with a gap under each rune                    96 x 96
    ring-runes.svg     the portal's ring: eight runes upright on it, clockwise from the top            96 x 96
    sigil-lines.svg    the seal: two circles, a star of two squares, eight ticks                        68 x 68
    sigil-runes.svg    the seal: eight runes in the band between its circles                            68 x 68
    sigil-small.svg    the seal at an 80 px card: a circle, a diamond, four ticks, no runes             36 x 36

Every file is a grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top), `fill="#000"`,
`shape-rendering="crispEdges"`: masks with no colour of their own, like the signs. The lines are the cells whose centre lies on them, so the
seal's lines keep the eight symmetries of its centre; every number rounds half up. A rune is changed in `runes.json`, then
`python tools/build_runes.py` (`--check` says whether the files are what the source makes), in the table of `tests/test_orkui.py` and in
orkBoard's decisions together, never in a face.

## A rune

    <span class="ork-rune key" aria-hidden="true"></span>          10 x 14 (2 px a cell)
    <span class="ork-rune knot big" aria-hidden="true"></span>     20 x 28 (4 px a cell)

`.ork-rune.<name>` is drawn in the colour of its text. A face draws one only where it means nothing (an accent), never as a word.

## The portal's ring: the portal's place

`.ork-portal-ring` is the portal's place on the table, laid before there is anything to send: **192 x 192** (96 x 96 cells at 2 px), one size
(the narrow width draws no ring). The portal goes inside it:

    <span class="ork-portal-ring" aria-hidden="true"></span>                                                          asleep
    <span class="ork-portal-ring is-open"><span class="ork-portal" aria-hidden="true"></span></span>                  open
    <span class="ork-portal-ring is-sealed"><span class="ork-portal is-sealed" aria-hidden="true"></span></span>      sealed

- **Asleep** (no class): the dots in the edge, the runes in the faint ink, nothing moves and nothing has colour. Nothing to send.
- **`is-open`**: the portal is in it (a goal can be played). The runes are `--ork-portal`, and the dots go under the portal's own ring.
- **`is-taking`** with `is-open`: the runes in `--ork-portal-hi` while a card is held over it (give the portal `is-taking` too).
- **`is-sealed`**: the portal with its X, and the runes grey again. Asleep has no portal and sealed has one, so they never read alike.
- **`is-waking`** with `is-open`: the opening, played once. The runes light one after another, a quick step each (`--ork-motion-quick`, eight
  steps), the dots go, then the portal's eye opens in five steps. Give the portal `is-new` for its shimmer. Take the class off to play it again.
- Under `prefers-reduced-motion` nothing turns: a waking ring is open at once.

## The sigil: the + card's seal of summoning

`.ork-sigil`: `<span class="ork-sigil" aria-hidden="true"></span>` inside `.ork-card.ork-plus`, before its icon: a circle, a band of eight runes and a star of
two squares, **136 x 136** (68 x 68 cells at 2 px), centred under the +. It takes the card's text colour (`currentColor`): the lines at about
a quarter of its strength, the runes a little more, so the + stays the one bright thing. On the card's hover or focus the lines are a step
brighter, and the runes light once, one after another clockwise from the top right, in eight steps (`--ork-motion-play` and `-base`), then rest
a little brighter. **`.small`** is the seal at an 80 px card, **72 x 72** (36 x 36 cells), with a circle, a diamond and four ticks and no runes.
Under reduced motion the runes do not turn: when hovered, they are just brighter. A 180 px card keeps the 136 px seal.

## A card's place

`.ork-card-place`: `<span class="ork-card-place" aria-hidden="true"></span>` marks where a pile will lie (the discard before its first card): a card's outline in pixel
dashes (2 px by 4) in the edge at under half its strength, with no fill, at 5 : 7. The page gives it its width. It cannot be pressed and it never moves.
