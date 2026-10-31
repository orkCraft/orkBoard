# orkUI / office / die

The die: **Play as a die** (orkBoard's decisions §190). Since 0.24.0 it is a **cube in CSS 3D**: six faces, seen from above and before under a perspective, its up face
large (its number clear), its front face under it and its right face beside it, so it reads as a cube on the table and not as a tile. It is lit from above: a face darkens
as it turns away from the light, so a die that rolls or rocks shows its depth. It is the person's to press, so it is drawn as a potion is: the thing, and its word under it
(the caller's).

    die.json   the source: the box (`size`, cells), a face's side (`face`), the perspective, the view, the shades of the up, front and right faces at rest (`tones`,
               which make the light) and the darkest, the numbers of the five sides, the roll's turns and poses, the wobble's and the landing's poses, and nine
               faces' marks, each a 16 x 16 grid of letters inside the face's rim (`faces` 1 to 6, `ok`, `no`, `new`) with what each letter is (`legend`)

A face is the card's frame in the edge's rim (a cell, its corners cut), its marks in 2 x 2 blocks of cells (pips at columns and rows 3, 7 and 11; the tick, the cross and the spark at two
cells a pixel) and the panel's colour over it at its shade. `python tools/build_die.py` writes the view, where the cube stands in its box, every face's shade and marks, and the
roll's, the wobble's and the landing's poses with every face's shade in each pose into `components.css`; `--check` says whether they are what this file makes.

## Writing one

Plain HTML and CSS: the die holds its cube and the cube's six faces, nothing else.

    <span class="ork-die face-5" aria-hidden="true"><span class="ork-die__cube"><i class="ork-die__face is-up"></i><i class="ork-die__face is-front"></i><i class="ork-die__face is-right"></i><i class="ork-die__face is-back"></i><i class="ork-die__face is-left"></i><i class="ork-die__face is-down"></i></span></span>

- **Size**: the cell is 3 px by default (a box of **69 x 72**, a face of 54), **`big`** 6 px (**138 x 144**, a face of 108); whole pixels, no size between. The cube at rest is
  centred in its box; when it rolls or rocks it rises out of it.
- **Face**: a class of the die, shown on its up face: **`face-1`** to **`face-6`** (the pips in `--ork-ink-muted`; `face-5` when there is none), **`face-ok`** (a tick in
  `--ork-success`), **`face-no`** (a cross in `--ork-danger`) and **`face-new`** (a spark in `--ork-ink`: news, not a warning). The other five faces are a die's: front 1, right 3, back 6, left 4, down 2.
- **State**, also classes of the die:
  - **`is-playing`**: the pips and the edges in the ink, the up face's marks glowing (`opacity` 0.55 and 1, six steps over 2.4 s, on and on).
  - **`is-rolling`**: the cube tumbles, a quarter turn a quick step (120 ms) in three poses, rising as it stands on an edge, six turns and round again, on and on. **To
    stop a roll on a face, take `is-rolling` off and put the face class on** (`face-ok`, `face-no`, `face-new`, `face-3`): the cube then stands on it. Put **`is-landing`** on with it
    to land it: the up face rolls in from the back and the cube drops onto the table, 300 ms in three poses, once.
  - **`is-wobbling`**: the cube rocks once on its edges, 300 ms in three poses, rising by the rise token (`--ork-motion-rise`) and staying there while the class stays. The
    page adds it on pointer enter and takes it off at the `animationend` named `ork-die-wobble` (the faces' shades end their own animations at the same time; put it on
    again after a reflow to play it again).
- **Turned**: on the table the die is not turned by itself. The page sets `rotate: calc(var(--ork-motion-lean) * -1)` on it (a die on a table lies askew, as a laid card
  does); the other way where it lands.
- **Motion**: only when the person allows motion (`prefers-reduced-motion: no-preference`): under reduced motion the glow stands at full strength, a rolling die stands
  on its face class, nothing rocks or lands.
- **No words inside**: the caller adds the word under it (*Play*, *Playing*) and says what it does to a screen reader (the die itself is `aria-hidden`; a `<button>` holds it).

It needs CSS 3D transforms (`transform-style: preserve-3d`, `backface-visibility`) and `clip-path`, which every browser that has `color-mix()` has. The drawing is changed in
`die.json`, in the table of `tests/test_orkui.py` and in orkBoard's decisions §190 together, never in the block it makes.
