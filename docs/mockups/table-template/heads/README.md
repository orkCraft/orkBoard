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

## The cartoon heads (§289, §290)

The owner drew the leaders' heads again, as a humorous flat cartoon, in Gemini (prompts in `docs/pictures-cartoon.md`).
`cartoon/sheets/` keeps the sheets as they came: `k1-bare` (the eight calm heads), `k2-16px` (the same, simpler, for 16 px),
`k3-tiers` (six leaders × bare, iron cap, violet hood), `k4-members` (grunt, elf, goblin, gnome, knight, skeleton), `k6-heroes`
(the 18 heroes), `moods` (eight heads × focused, worried, no, pleased, asleep); `k8-moods-first` is an earlier moods take, kept for
the record, not cut. Nothing here is in orkUI or the product (`design-system/orkui` is a stamped copy and is not edited here).
The cards' pictures stay pixel for the beta: sheet 4, the kinds of a question, is cut into `../pictures/question/`
(`cut_question.py`; same size, palette image and 48 colours as the pictures beside it; concern's wall and cost-grew's top coin are
trimmed a little at the top by the 1.8 : 1 crop of the almost square tiles).

**Re-cutting a take.** `cartoon/sheets.json` holds, per sheet, its file, the frame colour, the frames' columns and rows
(measured with `measure_frames.py`, which finds the grey-brown lines), the tile names, the erase boxes and the crop pads. A new
take is re-cut by editing it, then:

    python3 -I cut_cartoon.py      # every tile to cut/<name>.png: transparent, cropped to the head, full size
    python3 -I member_tiers.py     # the members' tiers by code
    python3 -I checks.py           # the check pictures

`cut/` is made again by the tool and is not kept (`.gitignore`). Names: `bare-`, `small-` (K2), `tier-<race>-<laborer|warrior|elder>`,
`member-<race>`, `member-<race>-<tier>`, `hero-<id>`, `mood-<race>-<mood>`.
`cut_cartoon.py` crops each tile to the middle of the gap around its frame (the dryad's antlers, the goblin's ear, the gnome's
beard and a plume cross the frame), then makes the ground and the frame line transparent by a flood from the crop's border and from
just inside the frame, so a head over the frame keeps its pixels and the dark inside it (eyes, mouths) stays. What was done by code:

- **Frames.** A stretch of frame between two antlers is cut off from the outside; it is seeded from the line's own pixels
  where they run frame-coloured a good way along it (an outline ends such a run). The frame colour is taken only where it is
  neutral: the dryad's hair in K2 is as light as the frame and purple, and was eaten before. The JPEG halo of the line and of the
  ground is peeled, and specks and parts of a neighbour (an antler tip that reaches into the tile above) are dropped.
- **Pads.** The dryad's crop is taller at the top (`pad` in `sheets.json`) so her antlers are whole; the knight's tiers too, for the
  plume.
- **"z".** The asleep column of `moods.jpg` has speech bubbles with a "z" beside dryad, knight, lich, imp and orkmaster: each is
  erased (box, or an ellipse where a box would bite the dryad's antler tip), with its trail of dots. Kept: the sweat drops of
  worried, and the plain bubble at the shaman's nose (no letter). Gnome and grunt asleep have none.
- **Two by hand.** The elder knight's plume was drawn over the dryad elder's cloak in the tile above: that cloak is erased by a
  polygon. The Inclusive and Sprite heroes' antlers almost touch the tile's top line, which sealed a grey pocket between them: that
  line is opened by an erase box.

**The members' tiers (no sheet, by code, `member_tiers.py`)**, as `trial/try_gear.py` did: a tier's gear is what the leader's K3 tile
adds to its bare K3 tile, kept where it is gear-coloured (iron grey, violet) with its outline (specks under 150 px dropped, and the
leader's own dark outline left out); the member's head is laid on the leader's bare head by a least-squares fit over the face
(scale 0.54 to 0.60, in `cut/member-fits.json`). Pairs: grunt, shaman; elf, dryad; goblin, imp; gnome, gnome fairy; skeleton, lich;
knight, knight. They work for the hood (all six), the grunt's, the elf's and the skeleton's iron cap; they look wrong or odd in these
places: the goblin's cap carries a dark stub on top (the imp's horns, shifted in the K3 tile, half kept); a thin stray line of
the dryad's antler stays by the elf's cap; the gnome's own blue cap shows above and beside the iron cap; the knight member's
warrior tier is only a grey plume floating above the helm (it has no horn to sit on); the elder hoods are wider than the member's
face needs and the elf's hood has dark speckles from the dryad's leaves.

**The check pictures** (`cartoon/checks/`), on the room's `#1a1816`, each head in the window's head box (48 × 44, 36 × 33, 24 × 22;
the 16 px column is the K2 drawing in 16 × 15), bottom-centred, smooth:

- `bare-and-moods-at-sizes.png`: the eight heads calm (K1) and in the five moods at 48, 36, 24 and the K2 head at 16, drawn at DPR 1
  and the whole picture scaled ×3 with nearest neighbour. `bare-and-moods-at-sizes-phone-dpr3.png`: the same drawn at DPR 3
  (the head at 3× its CSS size, smooth). The five moods of a race share one scale and sit where they are in their tiles, so the eye
  line and the top line are one across a row.
- `tiers.png`: leaders' and members' three tiers at 48 and 24, ×3. `heroes.png`: the 18 heroes at 48 and 24, ×3, each whole in the box.

**What the check pictures show, and what is not solved.**

- At 48 px every mood reads. At 36 it holds. At 24 px the moods are not told apart except pleased (the grin) and asleep (the
  tilted head); focused, no and worried are one face, and the sweat drop is a one-pixel dot. The thin outline goes to a grey line.
- The dryad's face is the smallest at every size: her antlers and her hair fill the box, so at 24 px her face is about 10 px wide.
  Her hair is cut flat at the bottom by the sheet's tile, and a few transparent notches show where hair strands met the frame.
- The knight's face is a visor slit: at 36 and 24 the mood is lost; the sweat drop outside the helm is the only worried sign.
- The tilted asleep heads (imp, gnome fairy, orkmaster, grunt) widen their race's union box, so all five moods of that race are a
  little smaller than a head drawn alone; the gnome's wing in asleep is drawn at a slant.
- At 16 px the K2 drawings read as shapes, not faces: the shaman's horns make a brown blob, the knight a yellow blob, the dryad a
  purple shape with two dots. The K2 lich is pale blue-white while the K1 skull is deep blue; the two are not one colour.
- Tiers: leaders' gear reads at 48; at 24 a cap, a hood and bare read, but the warrior of the dryad and the knight is a one-pixel
  difference (the plume). Members: see the list above.
- Heroes: fitted whole in the box, the head shrinks to about half where the tool is tall (Appetite, Pillar, Economy, Dungeon
  Master, Scene, Pivot); at 24 px the Domain shaman's stones are dots, the headband (Fitness), the stopwatch (Sprint), the tag (Store)
  and the dart (Position) are a speck. The Lantern imp is as wide as it is tall. The heroes need their own box, or the tool needs
  to be drawn apart from the head.
