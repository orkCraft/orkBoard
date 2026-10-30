# orkUI / office / portal

The portal: **a round, magical pixel portal, the way a goal is sent into main** (orkBoard's decisions §177.4). A goal dropped or pressed into it
is merged. It is round and purple, never a door; its light, `--ork-portal`, is a signal (*a goal can be played here*), used by `.ork-portal` and its ring alone.

    portal.json   the drawing: three 26 x 28 grids of letters (`still`, `arms`, `seal`) and what each letter is (`legend`)

`still` is what stands: the ring of ink and edge stones with the frame's gaps and a panel lip, the cell-wider ring a held card shows, the panel,
the dark eye and twelve single-cell sparks. `arms` is the swirl, in four tones, the one part that turns (about the cell corner 13, 14). `seal` is the
X (two bars with a dark edge and a square knot) over the swirl while sealed. `python tools/build_portal.py` writes them into `components.css`
as `box-shadow` pixels, as `.ork-busy` is drawn; `--check` says whether they are what this file makes.

## Writing one

Plain HTML and CSS, no script and no inner markup:

    <span class="ork-portal" aria-hidden="true"></span>

- **State** is a class on the same element: none is open; **`is-taking`** while a card is held over it (the swirl brighter, in `--ork-portal-hi`,
  the ring a cell wider); **`is-sealed`** while the gate holds the goal (the swirl still, in the frame and the faint ink, no sparks, the ring dim,
  an X over it; it wins over `is-taking`); **`is-new`** shimmers the swirl once, the first time it appears (take the class off to play it again).
- **Size**: the cell is 5 px by default (**130 x 140**), **`small`** 4 px (**104 x 112**); whole pixels, no size between, the same on a phone.
- **Motion**: only the swirl turns, a quarter turn at a time (`steps(4)`), 6 s a turn. Under `prefers-reduced-motion` nothing moves: the swirl
  stands still and the shimmer is off.
- **No words inside**: the caller adds the label and the line (*Into main: Lobby*), and says what it is to a screen reader. It is a box of its
  own (`inline-block`, `flex: none`); it takes no colour of the text around it, and on a `<button class="ork-portal">` the button's own look is gone
  and `:focus-visible` draws the 2 px ink frame.

**Its place on the table** is `.ork-portal-ring` (`../runes/README.md`, 0.19.0): a ring of seven runes, with the place of a goal's element at its top (`.ork-portal-ring__seal`), laid before there is anything to send,
192 x 192, with the portal inside it (`<span class="ork-portal-ring is-open"><span class="ork-portal"></span></span>`). Asleep it is grey and still,
`is-open` lights its runes in `--ork-portal`, `is-sealed` greys them again, and `is-waking` opens it once. **0.21.0**: the ring keeps the road's corners
(`.ork-portal-ring__before` Release, `.ork-portal-ring__after` Live) and the gate of heads that stand before the portal while the way into main is checked (`.ork-portal-ring__gate`); a portal guarded by them is
`<span class="ork-portal is-sealed is-guarded">`, sealed without its X; `.ork-portal-ring.is-sending` with `.rite-<element>` plays the rite once: `../runes/README.md`.

It needs `color-mix()` and `box-shadow` lists in custom properties (Chromium 111, Firefox 113, Safari 16.2 or later).

`--ork-portal` (`#b27bf6`, a magical violet: CIELAB L* 61.9, hue 310, chroma 70) and `--ork-portal-hi` (`#d5a8ff`, L* 75.7) are far from the
void element's grey violet (CIE76 52.6 and 36.0 from `#8e88a8`); see `../README.md`. The drawing is changed in `portal.json`, in the table of
`tests/test_orkui.py` and in orkBoard's decisions §177 together, never in a face.
