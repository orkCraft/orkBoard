# orkUI / office / die

The die: **Play as a die** (orkBoard's decisions §190). Since 0.24.0 it is a **cube in CSS 3D**: six faces, seen from above and before under a perspective, its up face
large (its number clear), its front face under it and its right face beside it (since 0.29.0 seen steeper: about 34 degrees from above, turned 20), so it reads as a cube on the table and not as a tile. It is lit from above: a face darkens
as it turns away from the light, so a die that rolls or rocks shows its depth. It is the person's to press, so it is drawn as a potion is: the thing, and its word under it
(the caller's).

    die.json   the source: the box (`size`, cells), the cell of the sizes `big` and `small` (`cells`, 0.31.0), a face's side (`face`), the perspective, the view, the shades of the up, front and right faces at rest (`tones`,
               which make the light) and the darkest, the numbers of the five sides, the roll's turns and poses, the wobble's and the landing's poses, the quarter turn's steps (`turn`), and the sizes' cells (`cells`: `big` 6, `small` 2), and twelve
               faces' marks (ten for the up face, `faces` 1 to 6, `ok`, `no`, `new`, `play`, and, since 0.29.0, `front-stop` and `front-resume` for the front one), each a 16 x 16 grid of letters inside the face's rim with what each letter is (`legend`)

A face is the card's frame in the edge's rim (a cell, its corners cut), its marks in 2 x 2 blocks of cells (pips at columns and rows 3, 7 and 11; the tick, the cross and the spark at two
cells a pixel; the play arrow's marks lie at columns 4 to 12 and rows 2 to 12, see below) and the panel's colour over it at its shade. `python tools/build_die.py` writes the view, where the cube stands in its box, every face's shade and marks, and the
roll's, the wobble's and the landing's poses with every face's shade in each pose into `components.css`; `--check` says whether they are what this file makes.

## Writing one

Plain HTML and CSS: the die holds its cube and the cube's six faces, nothing else.

    <span class="ork-die face-5" aria-hidden="true"><span class="ork-die__cube"><i class="ork-die__face is-up"></i><i class="ork-die__face is-front"></i><i class="ork-die__face is-right"></i><i class="ork-die__face is-back"></i><i class="ork-die__face is-left"></i><i class="ork-die__face is-down"></i></span></span>

- **Size**: the cell is 3 px by default (a box of **72 x 90**, a face of 54), **`big`** 6 px (**144 x 180**, a face of 108) and, since 0.31.0, **`small`** 2 px (**48 x 60**, a face of 36); whole pixels, no size between. `big` and `small` are `cells` in `die.json`, written by `tools/build_die.py` (`--check` holds them); the cube's pieces are all in cells, so a die is never scaled. The cube at rest is
  centred in its box; when it rolls or rocks it rises out of it.
- **Face**: a class of the die, shown on its up face: **`face-1`** to **`face-6`** (the pips in `--ork-ink-muted`; `face-5` when there is none), **`face-ok`** (a tick in
  `--ork-success`), **`face-no`** (a cross in `--ork-danger`) **`face-new`** (a spark in `--ork-ink`: news, not a warning) and **`face-play`** (0.27.0: the play arrow, a right-pointing triangle in the pips' colour `--_pip`, so the muted ink at rest and, with `is-playing`, the ink and the glow; Orkboard's decision §200).
  The arrow is 17 marks of 2 x 2 cells: column 4 rows 2, 4, 6, 8, 10, 12; column 6 rows 3, 5, 7, 9, 11; column 8 rows 5, 7, 9; column 10 rows 6, 8; column 12 row 7. It is centred on the 16 x 16 face
  in the rows (2 to 13) and **a cell right of the middle in the columns** (4 to 13), where a triangle's weight (its centroid, half a cell left of the middle) looks centred. The other five faces are a die's: front 1, right 3, back 6, left 4, down 2 (the front one's 1 gives way to a front mark, the right one's 3 to blank).
- **The front face's mark** (0.29.0, Orkboard's decisions §246), a class of the die: **`front-stop`** (a square of 8 x 8 cells at the face's middle) or **`front-resume`** (a circular arrow, 14 x 14 cells), in
  **`--_front`**: the muted ink by default, **`.is-orks-running`** the danger's (something runs: Stop all can be pressed), **`.is-orks-stopped`** the ink (the orks are stopped: Resume). With neither class the
  front face keeps its 1. **With a front mark set the right face is blank** (one mark, on the orks' side).
- **The right face's Resume** (0.30.0, Orkboard's decisions §254.4): **`.right-resume`** with **`.front-stop`** draws the resume mark on the right face (the same 14 x 14 cells as `front-resume`, `sides` in `die.json`) in **`--_side`**, the faint ink (`--ork-ink-faint`) by default, so Resume is seen at the side before the quarter turn that brings it to the front. Without `.front-stop` it draws nothing.
- **The turn** (0.29.0): **`.is-turning`** turns the cube a quarter round its up axis (`rotateZ` to 90 degrees, three poses of 30 degrees, `--ork-motion-quick` x 3 = 360 ms), once, the faces' shades turning with it. It
  ends at the `animationend` named `ork-die-turn`; the page takes the class off and swaps the front mark then (the right face, blank, has come to the front). Under reduced motion there is no turn and no `animationend`:
  the page swaps the mark at once.
- **State**, also classes of the die:
  - **`is-playing`**: the pips and the edges in the ink, the up face's marks glowing (`opacity` 0.55 and 1, six steps over 2.4 s, on and on).
  - **`is-rolling`**: the cube tumbles, a quarter turn a quick step (120 ms) in three poses, rising as it stands on an edge, six turns and round again, on and on. **To
    stop a roll on a face, take `is-rolling` off and put the face class on** (`face-ok`, `face-no`, `face-new`, `face-play`, `face-3`): the cube then stands on it. Put **`is-landing`** on with it
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
