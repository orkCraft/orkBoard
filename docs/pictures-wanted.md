# The pictures the cards want (decision §283.34–36, spec 168 J2)

The owner makes them with Gemini, a sheet at a time, in the style of orkUI's leaders' heads (the shaman, the dryad, the knight,
the lich, the imp, the gnome): attach a picture of those heads to every prompt as the style's reference. Then orkUI takes them
in (`office/pictures/<id>.png`, listed in `pictures/pictures.json`), and Orkboard copies orkUI as it does today.

**A picture never carries a card's meaning alone**: the card's words stay under it. So the tiles have no text.

**After Gemini**, for each tile: crop it, bring it down to its 32 × 32 grid with nearest neighbour (never smooth), lay it on
orkUI's palette, look at its filled silhouette at 24 px beside its sheet's neighbours. It is drawn at 2 px a cell in a big card's
window (64 × 64) and at 1 px in a small card's middle (32 × 32). A tile that loses its idea at 32 × 32 is drawn again, simpler.

## The style, said first in every prompt

```
Pixel-art icon sheet in exactly the style of the attached reference image (fantasy leader heads: an ork shaman, a dryad,
a golden knight, a lich, an imp, a gnome). Each tile is a chunky 32x32 pixel grid scaled up with nearest-neighbour:
square pixels only, no anti-aliasing, no blur, no gradients, no soft shadows, no dithering. Bold one-pixel black outline,
two or three flat tones per colour plus a single highlight, a muted earthy palette (moss green, bone, bronze, leather
brown, slate grey, dusty purple) with one bright accent per tile. Dark charcoal background (#1a1816) inside a thin
grey-brown frame, the tiles in a regular grid with equal gaps. One subject per tile, centred, big, readable as a
silhouette. Tone: a cosy tavern card game with gentle humour: small orks, goblins, gnomes and imps doing the thing
literally, visual puns and expressive faces; never gross, never violent, no real brands. Absolutely no text, letters,
numbers or logos anywhere.
```

## Sheet 1: the ways of answering a card (16, a 4 × 4 grid)

The `way_kind` every call returns (spec 168 J1), and the ways the hand often holds.

```
A 4x4 grid of 16 tiles, left to right, top to bottom:
1 replace: an ork swaps an old cracked stone tablet for a shiny new one, the old one slipping from under his arm.
2 keep: a stubborn ork hugs an old stone tablet, a little shield strapped to it.
3 smaller: a goblin with pliers shrinks a huge battle axe into a tiny hatchet, looking proud.
4 later: a snail carries a sealed card on its shell, a small ork asleep leaning on it.
5 drop: an ork tosses a crumpled scroll over his shoulder into a barrel, not looking.
6 split: an axe splits one card cleanly into two halves that fly apart.
7 go on: an ork charges forward with a torch, stepping right past a wobbly warning sign.
8 mitigate: a gnome puts a bucket under a leaking barrel and pats it.
9 accept the risk: an ork shrugs, sitting calmly next to a bomb with a short lit fuse.
10 ask more: a gnome holds an enormous ear trumpet towards the viewer.
11 the leader decides: a little throne with a crown resting on it and a gavel on the seat.
12 your own words: a quill pen writing on a parchment, a tiny ink pot beside it.
13 start again: an ork dusts himself off beside a toppled tower of blocks, rebuilding it.
14 take: a goblin catches a falling card in both hands, delighted.
15 not a problem: an ork waves away a tiny buzzing fly, unbothered.
16 make it a goal: a sealed card with a green glowing seal pops out of a top hat.
```

## Sheet 2: the Orkmaster's settings (20, a 4 × 5 grid)

Spec 168 H2–H3: *How deep*, *The build starts*, *The night*, *Lands in dev by itself*, *Push*, *Goals at once*.

```
A 4x5 grid of 20 tiles, left to right, top to bottom:
1 how deep, thrift: an ork counts three copper coins in his palm, squinting.
2 how deep, balance: a pair of brass scales, one card on each pan, level.
3 how deep, quality: a dwarf-style anvil with a glowing gem being hammered on it.
4 the build starts, at once: a small rocket with its fuse already sparking.
5 the build starts, in 30 minutes: a short candle burning, a third gone.
6 the build starts, in 2 hours: a tall candle just lit.
7 the build starts, tonight: a crescent moon over a little forge chimney.
8 the build starts, by hand: a hand pulling a big wooden lever.
9 the night, off: an ork asleep in a tiny bed, nightcap on, a candle snuffed.
10 the night, ideas and specs: an owl in spectacles reading a scroll by candlelight.
11 the night, builds: a forge glowing under a starry sky, a hammer mid-swing.
12 the night, proposals: a goblin tiptoes with a lantern and a sack of lightbulb-like ideas.
13 lands in dev by itself, on: a mine cart rolling down a little track on its own.
14 lands in dev by itself, off: the same mine cart stopped by a wooden chock.
15 push, no: a wooden chest with a big padlock.
16 push, main only: one carrier pigeon with a single sealed letter.
17 push, dev and main: two carrier pigeons each carrying a letter, one a little clumsy.
18 goals at once, one: one ork carrying one crate.
19 goals at once, a few: three orks in a line, each with a crate.
20 goals at once, many: a heap of crates with many small ork legs under it.
```

## Sheet 3: a leader's settings (10, a 5 × 2 grid)

Spec 168 H4: its party's size, how it answers, its tier for its own calls. The heroes and the tiers' heads are drawn already.

```
A 5x2 grid of 10 tiles, left to right, top to bottom:
1 party size, lean: one ork with a hammer, sleeves rolled up.
2 party size, standard: an ork with a hammer and a goblin with a magnifying glass checking his work.
3 party size, full: a busy little crowd of orks, a goblin with a magnifier and a gnome with a checklist.
4 answers with the pen: a blank parchment and a quill waiting, an expectant ork face peeking.
5 answers with a choice: a signpost with two arrows pointing different ways.
6 answers with a fork: a road splitting into three paths, each ending at a tiny different hut.
7 answers silently: an ork with a finger on his lips, a sealed envelope in the other hand.
8 tier for its calls, novice: a wooden club.
9 tier for its calls, seasoned: an iron axe.
10 tier for its calls, veteran: a great axe engraved with glowing runes.
```

## Sheet 4: the kinds of a question (8, a 4 × 2 grid)

Only where orkUI's signs do not say it already.

```
A 4x2 grid of 8 tiles, left to right, top to bottom:
1 a question: a goblin scratching his head under a floating question mark made of smoke.
2 a fork: a road splitting in two, a confused ork at the junction holding two maps.
3 a conflict with a decision: two stone tablets butting heads like rams.
4 a risk: a rickety rope bridge over a gap, one plank missing.
5 a concern: a small crack in a wall with a worried gnome pointing at it.
6 a failure: a sword snapped in two, a little ork holding the hilt, baffled.
7 the cost grew: a coin purse swelling and bursting at its seams.
8 a hypothesis: a gnome with a flask, a bubbling potion and a hopeful face.
```

## When a sheet comes back

Ask again for the tiles that drift from the reference (*keep exactly the palette, outline and pixel size of the reference;
redo tiles 4 and 9 only*). Keep the order: a tile's number is its id's place in the lists above. A picture made by Gemini is
written in orkUI's `NOTICE` with the tool and the date it was made.
