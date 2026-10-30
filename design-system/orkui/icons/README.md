# orkUI / office / icons

The icons: `icons.svg`, one sprite of `<symbol>`s (`<svg class="ork-icon"><use href="icons/icons.svg#close"/></svg>`, the colour
is the text's, `currentColor`); the sources are `src/<name>.svg`, the sprite is made by `python tools/build_icons.py`.

**orkUI's own** (0.15.0): the icons the window draws are drawn on the signs' grid, in solid pixels (orkBoard's decisions §148.3):
a **7 x 7** grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top),
`viewBox="0 0 7 7"`, no colour of its own. They stand beside the signs and the emblems in one style, not two. Drawn at 14, 21 or
28 px (two, three or four pixels a cell) they are whole pixels.

    arrow-left       ← (the same arrow as the sign `before`)       close            × (corner to corner)
    more-horizontal  … (three dots)                                plus             +
    search           a lens and its handle                         mic              a microphone
    play             ▶                                             stop             ■
    banner           a pole and a square banner with a +          boarded          a pole crossed by two planks, two cells thick
                     cut out of it (0.22.0: + Party)                                (0.22.0: Stop all, in the danger colour)
    chevron-down, chevron-up, chevron-left, chevron-right   five cells a chevron (5 x 3 or 3 x 5), centred on the grid

`banner` and `boarded` (0.22.0, Orkboard's decisions §190) are drawn as the others are: `<svg class="ork-icon" aria-hidden="true"><use href="icons/icons.svg#banner"/></svg>` before a button's word, in the
button's colour (`boarded` wears the danger colour on a danger button). `banner`: row by row `######.`, `###.##.`, `##...#.`, `###.##.`, `######.`, `#......`, `#......`;
`boarded`: `###..##`, `#.####.`, `#..##..`, `#.####.`, `###..##`, `#......`, `#......`.

**Pixelarticons** (MIT, `LICENSE-pixelarticons.txt`, 24 x 24, a 1 px line) are the others, copied unchanged and kept in the sprite
for orkLine: `arrow-right`, `check`, `checkbox`, `clock`, `coins`, `eye`, `file`, `flag`, `folder`, `git-merge`, `lightbulb`,
`link`, `list-box`, `map`, `menu`, `pencil`, `phone`, `robot`, `sliders`, `square-alert`, `trash`, `warning-diamond`. Their licence
stays here while any of them is left. The icon `moon` is gone: the one moon is the sign `moon` (`../signs/`).
