# The heads: orkUI's today beside the owner's Gemini set

`compare.png`: each of the eight heads (the shaman, the dryad, the unicorn knight, the lich, the imp, the gnome fairy, the
Orkmaster, a Grunt) as orkUI draws it today (left of each pair) and as the owner's Gemini set draws it (right), cut out of its
tile and brought down to a 24 × 27 grid, at the sizes the window draws a head: 48 px (an open tab, a slot), 36 px (a tab), 16 px
(a card's corner), on the room's dark and on Tech's felt. The cut heads are the `*.png` beside it. Nothing here is in orkUI or
the product: replacing orkUI's heads is a decision of its own.

## The tiers (T1) and the heroes (H5), the owner's first take

`sheets/t1-tiers.jpg` and `sheets/h5-heroes.jpg` are the sheets as they came. `t1-h5-at-44.png`: each head cut out and brought to
44 px tall, shown four times bigger: the first column is the approved set beside T1's three tiers (bare, iron, hood), a row a race;
under them H5's eighteen heroes, in the prompt's order.

`trial/`: the tiers' gear laid by code (§288.3), tried before orkUI builds it (spec 168 J3). `cut_sheets.py` cuts every tile to
a transparent head; `try_gear.py` takes a tier's gear as what its tile adds to the bare one, kept only where it is gear-coloured
(iron grey, violet) with its outline, finds the scale and offset that lay a hero's face on the bare head, and lays the gear on the
hero. `gear-on-fitness-shaman.png` and `gear-on-sprite-dryad.png`: bare, iron, hood, large and at 44 px. It works: the H5 heroes are
drawn 6 to 15 % smaller than T1's heads, and the face finds its place without help; the hood's shadow on the face is not carried
(only the gear's own pixels are laid), which reads as well at 44 px.

What the take needs (the fix prompts are in `docs/pictures-wanted.md`, *When T1 and H5 came back*): the knight's plume took the
place of its horn, the leader's mark (§288.3); T1's gnome fairy spread its wings to the tile's edges, unlike the approved set and
H5; three imps that are not one face (the approved set's, T1's, the Lantern Imp's); H5's knights wear Release's night blue capes;
the Economy Knight is the leader itself (no coin); the Pivot Knight's compass reads as a cross; the Domain Shaman's beads do not
read at 44 px; three headbands (Fitness, Sprint, Store) are one thing at 16 px.
