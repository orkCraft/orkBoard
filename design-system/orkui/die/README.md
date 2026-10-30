# orkUI / office / die

The die: **Play as a die, seen from above** (orkBoard's decisions §190). A die on the table, its top face large and nearly square (its number clear), its front and right faces
thin strips that peek out, so it reads as a cube and not a box. It is the person's to press, so it is drawn as a potion is: the thing, and its word under it (the caller's).

    die.json   the drawing: the body and eight faces, each a 23 x 20 grid of letters (`body`, `faces` 1 to 6, `ok`, `no`), and what each letter is (`legend`)

`body`: the top face 20 x 17 with its two upper and its two lower corners cut, the front face three cells under it slanting right, the right face three cells beside it slanting down,
the silhouette and the top face's lower and right ridges in the edge. A face is its pips (2 x 2 cells, at columns 4, 9 and 14, rows 3, 7 and 12), or the tick (`ok`, two cells a pixel) or the
cross (`no`). `python tools/build_die.py` writes them into `components.css` as `box-shadow` pixels, as the portal is drawn; `--check` says whether they are what this file makes.

## Writing one

Plain HTML and CSS, no inner markup:

    <span class="ork-die face-5" aria-hidden="true"></span>

- **Size**: the cell is 3 px by default (**69 x 60**, the potions' pixel), **`big`** 6 px (**138 x 120**); whole pixels, no size between.
- **Face**: a class of the same element: **`face-1`** to **`face-6`** (the pips in `--ork-ink-muted`; `face-5` when there is none), **`face-ok`** (a tick in `--ork-success`) and
  **`face-no`** (a cross in `--ork-danger`).
- **State**, also classes:
  - **`is-playing`**: the pips and the edges in the ink, the pips glowing (`opacity` 0.55 and 1, six steps over 2.4 s, on and on).
  - **`is-rolling`**: the face cycles 1 to 6, 120 ms a face, in steps, on and on, whatever the face class is. **To stop a roll on a face, take `is-rolling` off and put the face
    class on** (`face-ok`, `face-no`, `face-3`): the die then stands on it. The page decides when and where.
  - **`is-wobbling`**: one wobble, 300 ms in three steps (-8, 6 and 0 degrees), rising by the rise token (`--ork-motion-rise`) and staying there while the class stays. The page adds it on pointer enter
    and takes it off at `animationend` (put it on again after a reflow to play it again).
- **Turned**: the die is not turned by itself. The page sets `rotate: calc(var(--ork-motion-lean) * -1)` on it (a die on a table lies askew, as a laid card does); the other way where it lands.
- **Motion**: under `prefers-reduced-motion` none of them moves: the glow stands at full strength, a rolling die stands on its face class, the wobble is off.
- **No words inside**: the caller adds the word under it (*Play*, *Playing*) and says what it does to a screen reader (the die itself is `aria-hidden`; a `<button>` holds it).

It needs `box-shadow` lists in custom properties and `var()` in `@keyframes` (any browser that has `color-mix()`, as the portal does). The drawing is changed in `die.json`, in the table of
`tests/test_orkui.py` and in orkBoard's decisions §190 together, never in a face.

It is turned by the page (the lean token). It carries `will-change: transform`, so it is drawn whole before it is turned: without that, the hairlines between its pixels show as a grid when it is turned.
