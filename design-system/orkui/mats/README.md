# orkUI / office / mats

**The mats' emblems** (0.43.0): twelve white silhouettes of the owner's, one for each thing a table's mat is about, traced to vectors like the signs (`../signs/README.md`): `hand` (a fan of cards),
`discussion` (a round table with four stools), `compare` (three cards side by side), `battle` (two crossed swords), `gate` (a portcullis in an arch), `flow` (stepping discs), `scheme` (five nodes joined),
`slots` (a grid of nine in a frame), `discard` (stacks of cards on a tray), `storymap` (a winding road with three doors), `team` (four stools at a bench), `timeaxis` (a scroll with a ruler's ticks).

Each `<name>.svg` is one flat shape with its inner details cut out as gaps: **one `<path fill-rule="evenodd">`, `fill="#000"`, in a square `viewBox="0 0 64 64"`**, the silhouette fitted by its longer side
and centred (margin 3), no `shape-rendering`, a few KB at most: a mask with no colour of its own, to be coloured as the text beside it. They come from the sheet `races/art/cartoon/e1-emblems.jpg` by
`tools/build_signs_from_art.py` (`uv run --with pillow --with numpy python tools/build_signs_from_art.py`, `--check`), whose source `../signs/art.json` names the tiles. Nothing in `components.css` draws them yet.
