# orkUI / office / elements

The five elements: **a goal's mark** in orkBoard (its spec 50, decisions §63.4). A party's goals lie on the board as decks of
one element, so a person tells the goals of a party apart at a glance. A goal is given one when it is made and keeps it; a goal
not yet given one is drawn `.dim`.

**Since 0.20.0 an element is a rune** (orkBoard's decisions §186): the five most different of orkUI's twelve runes (`../runes/`), tied to the colours, so the
mark on a card and the rune on the table's ring and the + card's seal are one picture, and the table says in runes which element a goal has. They are drawn
by `tools/build_runes.py` from `runes/runes.json` (`elements`), never by hand:

    meadow.svg   tusks     ice.svg   a key     dust.svg   a comb     void.svg   an eye     lava.svg   a wave

Each is the rune's **5 x 7** grid **centred in a 7 x 7** grid (columns 1 to 5, rows 0 to 6) of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel,
row by row from the top), `viewBox="0 0 7 7"`, `fill="#000"`, `shape-rendering="crispEdges"`: no colour of its own, no metadata. They are **drawn as
masks**: `.ork-elem` in `components.css` fills a 14 x 14 box (`.big` 28 x 28, two or four pixels a cell, whole pixels) with the element's
colour through `mask-image: url(elements/<name>.svg)`, so the file's black is only the shape. The file names, the tokens, the classes and the sizes
are as they were: every face that draws an element draws its rune.

*void* is the eye, which keeps the old ring (0.15.0) and gives it a centre: a ring of five by five with a pupil in the middle, never a crescent (the one moon is the sign `moon`,
`../signs/`), and a shape no other element, sign, emblem or moon has. The seven runes that are no element's (hook, ladder, spiral, staff, hourglass, diamond,
knot) are the decoration of the ring and the seal, which never carry an element's rune.

The colours are tokens, never values in a face: `--ork-elem-meadow`, `--ork-elem-ice`, `--ork-elem-dust`, `--ork-elem-void`,
`--ork-elem-lava` (`tokens.json`). They are muted, **each of a hue no signal has**: at least 20 (CIE76) from every signal
(success, alert, warning, danger) and from the action's green, and each at least 3:1 on `--ork-panel` and on `--ork-raised` (a
graphic, not text). Meadow leans toward teal (`#6fb8a8`), dust is a darker ochre (`#b8914f`), lava a warm red-brown that is never
the danger's (`#ad6a5a`, 25 from `danger`), ice (`#82aaff`) and void (`#8e88a8`) are as they were. `.dim` draws the mark in `--ork-ink-faint`.

    <span class="ork-elem meadow" aria-hidden="true"></span>          14 x 14
    <span class="ork-elem ice big" aria-hidden="true"></span>         28 x 28
    <span class="ork-elem lava dim" aria-hidden="true"></span>        not yet given one

**The glow** (0.21.0): `<span class="ork-elem lava is-glowing" aria-hidden="true"></span>` is a goal's rune while its task is at work: its opacity goes from 62 % to full and back in six steps
over 2.4 s, no halo; under reduced motion it stands, at full strength. It is the only thing about an element that moves by itself.

A mark is an accent on a card, beside the goal's name: the element is shown, never named in the interface, so the mark is
`aria-hidden`. A shape is changed in `runes/runes.json`, then `python tools/build_runes.py`, in the table of `tests/test_orkui.py` and in orkBoard's decisions together, never in a face.
