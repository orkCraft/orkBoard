# orkUI / office / elements

The five elements: **a goal's mark** in orkBoard (its spec 50, decisions §63.4). A party's goals lie on the board as decks of
one element, so a person tells the goals of a party apart at a glance. A goal is given one when it is made and keeps it; a goal
not yet given one is drawn `.dim`.

    meadow.svg   a leaf        ice.svg   a flake        dust.svg   stones        void.svg   an empty ring        lava.svg   a flame

Each is a **7 x 7** grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top), `viewBox="0 0
7 7"`, `fill="#000"`, `shape-rendering="crispEdges"`: no colour of its own, no metadata. They are **drawn as masks**:
`.ork-elem` in `components.css` fills a 14 x 14 box (`.big` 28 x 28, two or four pixels a cell, whole pixels) with the element's
colour through `mask-image: url(elements/<name>.svg)`, so the file's black is only the shape.

*void* is an empty ring (0.15.0), never a crescent: the one moon is the sign `moon` (`../signs/`), and the ring is a shape no other
element, sign, emblem or moon has.

The colours are tokens, never values in a face: `--ork-elem-meadow`, `--ork-elem-ice`, `--ork-elem-dust`, `--ork-elem-void`,
`--ork-elem-lava` (`tokens.json`). They are muted, **each of a hue no signal has**: at least 20 (CIE76) from every signal
(success, alert, warning, danger) and from the action's green, and each at least 3:1 on `--ork-panel` and on `--ork-raised` (a
graphic, not text). Meadow leans toward teal (`#6fb8a8`), dust is a darker ochre (`#b8914f`), lava a warm red-brown that is never
the danger's (`#ad6a5a`, 25 from `danger`), ice (`#82aaff`) and void (`#8e88a8`) are as they were. `.dim` draws the mark in `--ork-ink-faint`.

    <span class="ork-elem meadow" aria-hidden="true"></span>          14 x 14
    <span class="ork-elem ice big" aria-hidden="true"></span>         28 x 28
    <span class="ork-elem lava dim" aria-hidden="true"></span>        not yet given one

A mark is an accent on a card, beside the goal's name: the element is shown, never named in the interface, so the mark is
`aria-hidden`. A shape is changed here, in the table of `tests/test_orkui.py` and in orkBoard's spec 50 §1.1 together, never in a face.
