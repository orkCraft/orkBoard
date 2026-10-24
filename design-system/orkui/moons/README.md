# orkUI / office / moons

The moons: **a goal's progress** in orkBoard (its spec 74 §6, decisions §89). A goal shows how far its tasks are merged as the phase of
a moon, beside its words: new (none), crescent, half, gibbous, full (all). The phase is drawn in two layers, so a moon is never
a colour of its own: the dark side, then the lit part over it.

    disk.svg   the whole moon (the dark side, and the full moon's lit part)        crescent.svg   the lit part of a crescent
    half.svg   the lit part of a half                                              gibbous.svg    the lit part of a gibbous

Each is a **7 x 7** grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top), `viewBox="0 0
7 7"`, `fill="#000"`, `shape-rendering="crispEdges"`: no colour of its own, no metadata. They are **drawn as masks**:
`.ork-moon` in `components.css` fills a 14 x 14 box (`.big` 28 x 28, two or four pixels a cell, whole pixels) with `--ork-frame`
through `mask-image: url(moons/disk.svg)`, the dark side, and its `::after` fills the same box over it with the lit part through the
phase's file. The lit part is `--ork-ink-muted`; the full moon's is `--ork-ink`; `.new` has none. No new token: a moon takes the
colours of the frame and the ink, and colour stays a signal. A crescent is the *void* element's (`../elements/`) turned to the right.

    <span class="ork-moon new" aria-hidden="true"></span>             14 x 14, the dark side alone
    <span class="ork-moon half" aria-hidden="true"></span>
    <span class="ork-moon full big" aria-hidden="true"></span>        28 x 28

A moon is an accent beside the goal's words: it is shown, never named in the interface, so it is `aria-hidden`. A shape is changed here,
in the table of `tests/test_orkui.py` and in orkBoard's spec 74 §6 together, never in a face.
