# The pictures the cards want (decision §283.34–36, spec 168 J2)

The owner makes them with Gemini, a sheet at a time, in the pixel style of orkUI's leaders' heads (the shaman, the dryad, the
knight, the lich, the imp, the gnome): attach a picture of those heads to every prompt as the style's reference. Each tile is an
item card's picture: an object or an action with a joke in it, not a character (the owner, on the first sheet). Then orkUI takes them
in (`office/pictures/<id>.png`, listed in `pictures/pictures.json`), and Orkboard copies orkUI as it does today.

**A picture never carries a card's meaning alone**: the card's words stay under it. So the tiles have no text.

**After Gemini**, for each tile: crop it, bring it down to its 32 × 32 grid with nearest neighbour (never smooth), lay it on
orkUI's palette, look at its filled silhouette at 24 px beside its sheet's neighbours. It is drawn at 2 px a cell in a big card's
window (64 × 64) and at 1 px in a small card's middle (32 × 32). A tile that loses its idea at 32 × 32 is drawn again, simpler.

## The style, said first in every prompt

```
Pixel-art item cards for a comedic fantasy card game, in exactly the pixel style of the attached reference image
(fantasy leader heads: an ork shaman, a dryad, a golden knight, a lich, an imp, a gnome). Each tile is a chunky 32x32
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
A 4x5 grid of 20 tiles, left to right, top to bottom:
1 how deep, thrift: a coin purse tied with three knots, a moth flying out of it.
2 how deep, balance: brass scales holding a feather and an anvil, somehow perfectly level.
3 how deep, quality: a gem on an anvil polished to a blinding sparkle, a pair of tiny sunglasses beside it.
4 the build starts, at once: a rocket strapped to a card, its fuse already sparking.
5 the build starts, in 30 minutes: a candle a third burnt down, a snail racing it.
6 the build starts, in 2 hours: a very tall fresh candle, a cobweb starting at its base.
7 the build starts, tonight: a crescent moon in a nightcap above a forge chimney.
8 the build starts, by hand: a big wooden lever with a red knob and a leather glove resting on it.
9 the night, off: a blacksmith's hammer tucked into a tiny bed with a nightcap.
10 the night, ideas and specs: a scroll by candlelight with spectacles resting on it.
11 the night, builds: an anvil glowing under the stars, a hammer swinging all by itself.
12 the night, proposals: a lantern and an open sack spilling glowing lightbulb-like ideas, little tiptoe footprints.
13 lands in dev by itself, on: a mine cart rolling down its track all alone, a card waving from it like a flag.
14 lands in dev by itself, off: the same mine cart stopped by a brick and a wheel clamp.
15 push, no: a wooden chest with an absurd number of padlocks.
16 push, main only: one determined carrier pigeon with one sealed letter.
17 push, dev and main: two carrier pigeons tangled together with two letters.
18 goals at once, one: one crate on a tiny hand cart.
19 goals at once, a few: three crates stacked neatly.
20 goals at once, many: an absurdly tall tower of crates wobbling.
```

## Sheet 3: a leader's settings (10, a 5 × 2 grid)

Spec 168 H4: its party's size, how it answers, its tier for its own calls. The heroes and the tiers' heads are drawn already.

```
A 5x2 grid of 10 tiles, left to right, top to bottom:
1 party size, lean: a single hammer.
2 party size, standard: a hammer and a magnifying glass crossed like swords.
3 party size, full: a tool belt overflowing with hammers, magnifiers and a checklist.
4 answers with the pen: a blank parchment and a quill waiting, an ink pot tapping its little foot.
5 answers with a choice: a signpost with two arrows pointing opposite ways.
6 answers with a fork: a dinner fork with three prongs, each prong holding a tiny different map.
7 answers silently: a sealed envelope with a zipper across its flap.
8 tier for its calls, novice: a wooden club with a bandage on it.
9 tier for its calls, seasoned: an iron axe with a few honest notches.
10 tier for its calls, veteran: a great axe engraved with glowing runes and a laurel wreath hung on it.
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
