# orkUI / office / pictures

**The kinds of a question, as pictures** (0.43.0): the owner's colour take (sheet `races/art/cartoon/p4-question-kinds.jpg`), each a whole tile on a wooden table edge against slate (Orkboard's decision §287): `question-mystery`
(a locked chest), `-fork` (a map torn in two), `-clash` (two stones butting heads), `-gap` (a rope bridge with a plank gone), `-crack` (a mended crack in a wall), `-mend` (a sword tied with a bow), `-cost` (a burst purse),
`-idea` (a flask with a bulb).

`<name>.png` is **130 px wide at 1x** (the window of a way's card is 130 x 68 in §287), `@2x` 260 and `@3x` 390; they are **kept whole, cut to the inside of the frame, not trimmed to the thing**, opaque. **The tiles on the sheet are
nearly square (about 1 : 0.97), not the 1.9 : 1 of §287's wide tile**, so each file keeps its own proportion (130 x 126 at 1x); the card's window will crop them (or the sheet be taken again wide). Made by
`tools/build_things_from_art.py` from `races/art/things.json` (`mode: tile`). Nothing in `components.css` draws them yet.
