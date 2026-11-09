# The pictures the cards want (decision §283.34–36, spec 168 J2)

The owner makes them with Gemini, a sheet at a time, in the pixel style of orkUI's leaders' heads (the shaman, the dryad, the
knight, the lich, the imp, the gnome): attach a picture of those heads to every prompt as the style's reference. Each tile is an
item card's picture: an object or an action with a joke in it, not a character (the owner, on the first sheet). Then orkUI takes them
in (`office/pictures/<id>.png`, listed in `pictures/pictures.json`), and Orkboard copies orkUI as it does today.

**A picture never carries a card's meaning alone**: the card's words stay under it. So the tiles have no text.

**The rules the first sheet set** (decision §287): a tile is wide, about 1.9 : 1, the window of a way's card (130 × 68); every
object stands on one wooden table edge along the tile's foot; one object and at most one small joke, filling about 70% of the
tile's height; the leaders' heads' colours, muted, with no large area of a signal's colour; a black outline, light from the top
left. A human hand is the person's act, an ork's green hand the orks'. **Attach the approved first sheet beside the heads** to
every later prompt: it is the set's reference.

**Sheet 1 is made** (its third take): `docs/mockups/table-template/pictures/` holds its sixteen tiles as the mockup cut them.

**After Gemini**, for each tile: crop it, bring it down to its 32 × 32 grid with nearest neighbour (never smooth), lay it on
orkUI's palette, look at its filled silhouette at 24 px beside its sheet's neighbours. It is drawn at 2 px a cell in a big card's
window (64 × 64) and at 1 px in a small card's middle (32 × 32). A tile that loses its idea at 32 × 32 is drawn again, simpler.

## The style, said first in every prompt

```
Pixel-art item cards for a comedic fantasy card game. Two attached references: the leader heads (an ork shaman, a dryad,
a golden knight, a lich, an imp, a gnome) for the pixel style and the colours, and an approved sheet of sixteen item
tiles: match that sheet EXACTLY in tile shape (wide, about 1.9:1), pixel size, outline, palette, the dark slate
background, the wooden table edge along every tile's foot and the grey-brown frames. Every object stands on that table
edge and fills about 70% of the tile's height, wholly inside its own tile's frame (nothing pokes out into a neighbour);
every tile keeps the approved sheet's shape, about 1.9:1, never wider; light from the top left. Each tile is a chunky 32x32
pixel grid scaled up with nearest-neighbour: square pixels only, no anti-aliasing, no blur, no gradients, no soft
shadows, no dithering. Bold one-pixel black outline, two or three flat tones per colour plus a single highlight, a muted
earthy palette (moss green, bone, bronze, leather brown, slate grey, dusty purple) with one bright accent per tile. Dark
charcoal background (#1a1816) inside a thin grey-brown frame, the tiles in a regular grid with equal gaps.
THE HERO OF EVERY TILE IS AN OBJECT OR AN ACTION, NOT A CHARACTER: an item, a tool, a contraption caught in the middle
of what it does. No full figures; at most a hand, a boot or a tiny cameo at the edge. The humour is in the object: absurd
exaggeration, a visual pun, a silly detail (a bandage, a tiny party hat, too many padlocks, a smug fly), the kind of
joke an item card makes in a funny tabletop game. One subject per tile, centred, big, readable as a silhouette at 32x32.
Never gross, never violent, no real brands. Absolutely no text, letters, numbers or logos anywhere (no "zzz" either).
```

## Sheet 1: the ways of answering a card (16, a 4 × 4 grid)

The `way_kind` every call returns (spec 168 J1), and the ways the hand often holds.

```
A 4x4 grid of 16 tiles, left to right, top to bottom:
1 replace: a shiny new stone tablet shoving an old cracked one off its pedestal, a puff of dust.
2 keep: an old stone tablet chained to its pedestal with far too many padlocks.
3 smaller: a huge battle axe and the same axe shrunk to toothpick size beside it, a pair of pliers between them.
4 later: a sealed letter riding on a snail's shell, the snail wearing a tiny nightcap.
5 drop: a crumpled scroll in mid-air above a barrel, a fly already circling it.
6 split: a playing card cut cleanly in two, the axe still stuck in the table between the halves.
7 go on: a boot stepping over a knocked-down warning sign, a torch held high.
8 mitigate: a leaking barrel with a cork jammed in, a bandage taped over the crack and a bucket under it.
9 accept the risk: a round bomb with a short lit fuse, wearing a tiny party hat, sitting on a velvet cushion.
10 ask more: an enormous brass ear trumpet pointed straight at the viewer.
11 the leader decides: a crown resting on a gavel on a velvet cushion.
12 your own words: a quill dancing over a parchment, an ink pot on little legs beside it.
13 start again: a toppled tower of toy blocks, one block being set back on top by a hand.
14 take: a hand bursting out of the frame to snatch a falling card.
15 not a problem: a tiny smug fly being waved away by a huge feather fan.
16 make it a goal: a card springing out of a magician's top hat in a burst of sparkles.
```

## Sheet 2: the Orkmaster's settings (20, a 4 × 5 grid)

Spec 168 H2–H3: *How deep*, *The build starts*, *The night*, *Lands in dev by itself*, *Push*, *Goals at once*.

```
A 4x5 grid of 20 wide tiles (four across, five down), left to right, top to bottom, each object on the table edge:
1 how deep, thrift: a coin purse tied with three knots, a moth fluttering out of it.
2 how deep, balance: brass scales with a feather on one pan and an anvil on the other, somehow perfectly level.
3 how deep, quality: a gem on a small anvil polished to a blinding sparkle, tiny sunglasses lying beside it.
4 the build starts, at once: a small rocket strapped to a playing card, its fuse already sparking.
5 the build starts, in 30 minutes: a candle a third burnt down, a snail racing it along the table.
6 the build starts, in 2 hours: a very tall fresh candle, a spider just starting a web at its base.
7 the build starts, tonight: a little forge on the table, a crescent moon in a nightcap hanging above its chimney.
8 the build starts, by hand: a human hand pulling a big wooden lever with a small red knob.
9 the night, off: a blacksmith's hammer tucked into a tiny bed under a blanket, wearing a nightcap.
10 the night, ideas and specs: a scroll beside a lit candle, round spectacles resting on the scroll.
11 the night, builds: an anvil glowing under a few stars, a hammer swinging all by itself mid-strike.
12 the night, proposals: a lantern beside an open sack spilling small glowing lightbulb-shaped ideas, tiny tiptoe footprints leading away.
13 lands in dev by itself, on: a little mine cart rolling down a short track on its own, a playing card riding in it like a passenger.
14 lands in dev by itself, off: the same mine cart stopped by a brick, a clamp on its wheel.
15 push, no: a wooden chest with an absurd number of padlocks.
16 push, main only: one determined carrier pigeon standing on the table with one sealed letter.
17 push, dev and main: two carrier pigeons tangled together with two sealed letters.
18 goals at once, one: one crate on a tiny hand cart.
19 goals at once, a few: three crates stacked neatly.
20 goals at once, many: an absurdly tall tower of crates, wobbling.
```

## Sheet 3: a leader's settings (10, a 5 × 2 grid)

Spec 168 H4: its party's size, how it answers, its tier for its own calls. The heroes and the tiers' heads are drawn already.

```
A 5x2 grid of 10 wide tiles (five across, two down), left to right, top to bottom, each object on the table edge:
1 party size, lean: a single hammer lying on the table, looking a little proud of itself.
2 party size, standard: a hammer and a magnifying glass crossed like swords.
3 party size, full: a tool belt overflowing with hammers, magnifying glasses and a rolled checklist.
4 answers with the pen: a blank parchment and a quill waiting, an ink pot tapping its little foot.
5 answers with a choice: a small signpost with two arrows pointing opposite ways.
6 answers with a fork: a dinner fork standing upright, each of its three prongs spearing a tiny different map.
7 answers silently: a sealed envelope with a zipper across its flap.
8 tier for its calls, novice: a wooden club with a bandage wrapped round it.
9 tier for its calls, seasoned: an iron axe with a few honest notches in its blade.
10 tier for its calls, veteran: a great axe engraved with softly glowing runes, a laurel wreath hung on its handle.
```

## Sheet 4: the kinds of a question (8, a 4 × 2 grid)

Only where orkUI's signs do not say it already.

```
A 4x2 grid of 8 tiles, left to right, top to bottom:
1 a question: a treasure chest whose keyhole is shaped like a question mark.
2 a fork: a map torn in two, each half showing a different road.
3 a conflict with a decision: two stone tablets butting heads like rams, sparks flying.
4 a risk: a rickety rope bridge with one plank missing.
5 a concern: a crack in a stone wall with a small bandage stuck over it.
6 a failure: a sword snapped in two, its halves tied back together with a bow.
7 the cost grew: a coin purse bursting at its seams, coins popping out.
8 a hypothesis: a bubbling flask with a tiny glowing lightbulb floating inside.
```

## When a sheet comes back

Ask again for the tiles that drift from the reference (*keep exactly the palette, outline and pixel size of the reference;
redo tiles 4 and 9 only*). Keep the order: a tile's number is its id's place in the lists above. A picture made by Gemini is
written in orkUI's `NOTICE` with the tool and the date it was made.

## The heads (decision §288)

Every head the window draws, made in the same way as the cards' pictures, with **the owner's first set of eight heads attached**
beside the old reference. A head is drawn **bare** (no hood, no band, no cap: orkUI lays each tier's gear over it by code), on a
tile of **12 : 11**, front-facing, the same height and its eyes on one line across every sheet, wholly inside its tile, in its party's
colour, on a flat mid-grey (#3a3a3a) to be cut out. No text.

The party colours: Tech moss `#8fbf4a` (orks), Product and Game design muted brass gold `#d9b45c` with deep oxblood (knights),
Design and Art plum `#c47fc0` (elves), Release night blue `#7f93e6` (the undead), Run and LiveOps rust `#e08a4a` (goblins),
Marketing sea `#5cc8c0` (gnomes), the Orkmaster warm wood `#a9825a`.

**The style, said first in every heads' prompt:**

```
Fantasy head portraits for a card-game interface, matching EXACTLY the attached approved set of eight heads in pixel size,
outline, shading, palette, framing and proportions. Each head on a tile of 12:11 (slightly wider than tall), front-facing,
the same height, its eyes on the same line in every tile, wholly inside its tile with a one-pixel margin (horns, antlers,
wings stay inside). Crisp square pixels scaled with nearest-neighbour: no anti-aliasing, no blur, no gradients, no soft
shadows. Bold one-pixel black outline, two or three flat tones per colour plus one highlight, light from the top left.
Bare heads: no hood, cap, band or helmet unless it is part of the race's own face (the knight's helm). A flat mid-grey
background (#3a3a3a) in every tile, a thin grey-brown frame around each tile. No text, letters, numbers or captions.
```

**Sheet H1, fixes to the approved set** (attach the set itself): *Keep this sheet exactly as it is. Redraw only tile 3 (the knight)
with its cape in deep oxblood red-brown instead of blue, tile 5 (the imp) with its collar in dark rust brown instead of teal, and
tile 8 (the Grunt) bare-headed, no cap. Nothing else changes.*

**Sheet H2, the members** (a 3 × 2 grid, bare heads, calm):
```
A 3x2 grid of 6 tiles, left to right, top to bottom:
1 an ork member: olive-green skin, small tusks, ears out at the sides, a plain young face (Tech, moss #8fbf4a).
2 an elf member: pale skin, long pointed ears, long plum #c47fc0 hair.
3 a goblin member: rust #e08a4a skin, wide flat ears, a wide toothy grin.
4 a gnome member: a round nose, a big white beard, a small sea-green #5cc8c0 scarf at the collar.
5 a knight member: a plain closed helm in muted brass with a visor slit and breath holes, no horn, no wings.
6 a skeleton member: a bare skull on a short jaw in night blue #7f93e6 and slate.
```

**Sheets H3 and H4, the moods** (the leaders and the Orkmaster: five columns of moods, a row a head):
```
A 5x4 grid of 20 tiles: each row is the same head as in the attached approved set, kept exactly; the five columns are its
moods, left to right: focused (narrowed eyes, a firm mouth), worried (raised brows, a bead of sweat), no (a frown, the mouth
turned down), pleased (a wide smile), asleep (eyes closed, a small tilt). Rows: 1 the ork shaman, 2 the elf dryad,
3 the golden unicorn knight (its mood shown by the visor's eye-glow and a small tilt), 4 the lich (its mood by its eye-lights).
```
H4 is the same with three rows: 1 the imp, 2 the gnome fairy, 3 the Orkmaster.

**Sheets T1 and T2, the tiers** (the gear each race wears; orkUI takes the gear from the difference between a tier's tile and
the bare one, then lays it by code over every mood and hero of that race, §288.3). The tiers as orkUI has them: *laborer* the race
as it is; *warrior* iron on the head; *elder* a pointed violet hood (the knight is iron already: its tiers are its plume).
```
A 3x6 grid of 18 tiles: each row is one head from the attached approved set, kept EXACTLY the same face, eyes, colours and
position in all three columns; only the gear on the head changes, left to right: 1 bare (as it is), 2 a dark iron cap
fitted to the head, 3 a pointed violet hood over the head. Horns, antlers, wings and ears stay visible through or beside the
gear. Rows: 1 the ork shaman, 2 the elf dryad, 3 the golden unicorn knight (its tiers: 1 no plume, 2 a short iron-grey plume,
3 a tall violet plume), 4 the lich, 5 the imp, 6 the gnome fairy.
```
T2 is the same with the six members of sheet H2 as its rows (the ork, the elf, the goblin, the gnome, the knight, the skeleton).

**Sheets H5–H6, the heroes' portraits** (18; each its leader's race and party colours, calm; three a row in 6 × 3):
```
A 6x3 grid of 18 tiles, left to right, top to bottom, each a hero: its leader's head from the attached set, changed as said.
1 Scene Shaman: the ork shaman with a small clapperboard tucked between its horns.
2 Spike Shaman: the ork shaman with a spiky crest of hair and two thin war-paint stripes.
3 Domain Shaman: the ork shaman with boundary-stone beads hanging from its horns.
4 Fitness Shaman: the ork shaman with a sweatband across its brow.
5 Jobwise Knight: the unicorn knight's helm with a quill-feather plume.
6 Pivot Knight: the unicorn knight's helm in silver with a compass rose on its brow.
7 Appetite Knight: the unicorn knight's helm in copper with a fork-and-knife crest.
8 Pillar Knight: the unicorn knight's helm in stone grey, its crest shaped like a column's capital.
9 Economy Knight: the unicorn knight's helm in gold with a coin-slot visor.
10 Dungeon Master Knight: the unicorn knight's helm in dark iron with a many-sided die as its crest.
11 Diamond Dryad: the dryad with a small diamond hanging between her antlers.
12 Atom Dryad: the dryad with tiny dots circling her antlers like orbits.
13 Sprint Dryad: the dryad with wind-swept hair and a thin sweatband.
14 Inclusive Dryad: the dryad wearing a large round monocle lens.
15 Sprite Dryad: the dryad with two paintbrushes tucked in her antlers and a dab of paint on her cheek.
16 Lantern Imp: the imp with a small lantern hanging from one horn.
17 Store Gnome: the gnome fairy with a shopkeeper's visor cap pushed back.
18 Position Gnome: the gnome fairy with a dart stuck in its cap and a tiny target on its scarf.
```
**Sheets H7–H11, the heroes' moods**: as H3, four heroes a sheet (rows), the five moods (columns); the last sheet two heroes.

**When T1 and H5 came back** (the first take, 9 November 2026; the look in `docs/mockups/table-template/heads/README.md`). From
now on **T1's first column is the reference** for every later sheet (the moods H3–H4, the members T2, the heroes' moods H7–H11):
attach it instead of the first set, so the imp, the lich and the gnome fairy stay one face each.

T1, two rows again (attach T1 and the approved set):
```
Keep this sheet exactly as it is. Redraw only two rows, keeping every other row untouched.
Row 3, the golden unicorn knight: keep its golden horn with the blue ring at its base in all three tiles, exactly as in the
first tile. Tile 2 adds a short iron-grey plume and tile 3 a tall violet plume, each springing from the BACK of the helm,
behind the horn, never covering it. A short deep oxblood red-brown cape at the shoulders in all three, the same in each.
Row 6, the gnome fairy: redraw all three tiles from the gnome fairy of the attached approved set, its face, beard and small
sea-green wings kept exactly, the wings close beside its head as there, not spread to the tile's edges; then the same three
gears as the other rows: 1 bare, 2 the dark iron cap, 3 the pointed violet hood. Both rows wholly inside their tiles with
a clear margin: nothing touches the frame.
```

H5, seven tiles again (attach H5 and T1's first column as the reference; if Gemini changes more than it is asked, send it in two
halves: 3, 6, 9 and the capes, then 13, 16, 17):
```
Keep this sheet exactly as it is. Redraw only the tiles named here, each keeping its head exactly as the attached reference
draws it; every other tile stays untouched.
Tiles 5 to 10, the six knights: each cape at the shoulders in deep oxblood red-brown instead of blue; nothing else changes.
Tile 3, Domain Shaman: three large square boundary stones on a cord hanging from each horn, big enough to read at 16 pixels.
Tile 6, Pivot Knight: the silver helm with a large compass needle as its crest in place of the horn (a long diamond-shaped
arrow, its upper tip red), big enough to read at 16 pixels.
Tile 9, Economy Knight: the gold helm with a large gold coin standing on its edge as its crest in place of the horn, and a
coin slot cut across its brow.
Tile 13, Sprint Dryad: no band; a small round stopwatch hanging from one antler, her hair swept back by the wind.
Tile 16, Lantern Imp: the imp of the attached reference, the same face, ears and horns, a small lit lantern hanging from the
tip of its right horn.
Tile 17, Store Gnome: no band and no visor; a small paper price tag on a string hanging from one of its wings.
```

## The cartoon (decision §289)

**Every sheet's prompt, whole and ready to copy (the style said in each): `docs/pictures-cartoon.md`.** What follows is the first two
sheets as they were first written, with the style block apart.

The look's pictures are a humorous flat cartoon, the heads first. Attach the owner's test sheet of six
(`docs/mockups/table-template/heads/cartoon/test-sheet-six.jpg`) as the style to match. What the test showed at the window's sizes:
the eyes read even at 16 px on a phone; the dryad and the knight came with shoulders and the lich with a body (a head only, please);
the lich's dark hood is lost on the dark room and the gnome wore a hat (the bare head: gear is laid by code); a 16 px head on a plain
screen blurs (sheet K2 draws it simpler).

**The style, said first in every cartoon prompt:**

```
Fantasy head portraits for a card-game interface, matching EXACTLY the attached test sheet in line, colour, shading and humour:
a humorous flat cartoon, thick even dark outlines, flat colours with one shade each, no texture, no gradients, big expressive
eyes, comic proportions. A HEAD ONLY, no neck, no shoulders, no body; front-facing; every head the same height with its eyes on
the same line in every tile, wholly inside its tile with a clear margin (horns, antlers and wings stay inside). Bare heads: no hood,
no hat, no cap, no helmet unless the helm is the race's own face (the knight). Every head reads on a very dark background: no dark
mass without a light rim. A flat mid-grey background (#3a3a3a) in every tile, a thin grey-brown frame around each tile. No text.
```

**Sheet K1, the bare set of eight** (a 4 × 2 grid, calm):
```
A 4x2 grid of 8 tiles, left to right, top to bottom:
1 the ork shaman: olive-green skin, tusks, ram's horns curling down the sides, the ork's own face (as in the test sheet).
2 the elf dryad: pale skin, long plum #c47fc0 hair cut short at the jaw so no shoulders show, stag antlers.
3 the golden unicorn knight: a closed brass-gold helm, its eyes seen in the visor's slit, one unicorn horn, small white wings
  at the helm's sides; the helm ends at the chin, no shoulders, no armour.
4 the lich: a bare skull in light night blue #7f93e6 with glowing pale-blue eyes and a light rim, no hood, no body.
5 the imp: rust-red skin, small black horns, wide pointed ears, a wide toothy grin (as in the test sheet).
6 the gnome fairy: bald head, a big white beard, a round nose, small sea-green #5cc8c0 wings close beside the head; no hat.
7 the Orkmaster: an older ork, olive-green skin, heavy brows, tusks, a small brass crown with three points; a head only.
8 a Grunt: a young ork, olive-green skin, small tusks, ears out at the sides, a plain eager face; no cap.
```

**Sheet K2, the same eight at 16 pixels** (attach K1; a 4 × 2 grid): *The same eight heads, kept the same characters and colours,
redrawn simpler to read at 16 pixels: only the face, the eyes and the race's mark (horns, antlers, the horn and wings, the crown);
outlines twice as thick, the eyes a little bigger, no strands of hair, no small teeth, no wrinkles.*

Then, from K1 as the reference: the tiers' gear (T1–T2 again: bare, a dark iron cap with a light rim, a pointed violet hood), the
members (H2 again), the heroes (H5–H6 again) and the moods (H3–H4, H7–H11 again), with this style block in place of the pixel one.
