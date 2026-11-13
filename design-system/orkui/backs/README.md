# orkUI / office / backs

**The back**: a hand card face down (orkBoard's decisions §149.3, §160.3, §254.5, §263): the deck, the cards under a stack's top, the discard's cards
under its top, the Orkmaster's fan. One back for them all, **after a tarot back** (0.32.0, redrawn closer to it): **filigree in the four corners** (a scroll that
curls into itself, a tendril along the top and one down the side, each ending in a small curl, a leaf at the very corner), **a thin line down each long side with a
lozenge at its middle**, **a moon in a circle at the top and at the bottom** of the card's axis with a bead and a small lozenge between it and the ring, and
**four small stars** round the ring, all drawn in the faint ink's grey in strokes of one cell, and **orkUI's ring of runes in its middle**, drawn by CSS.
**No colour**: the two greys are the tokens `--ork-card` (the ground) and `--ork-ink-faint` (the strokes), and a test holds the files to them.

    back.svg        the back: 80 x 112 unit squares (5 : 7; a stroke about 1.8 px on a 144 px card, an engraving's line), crispEdges, the card's grey and the faint ink's
    back-small.svg  40 x 56: the long sides and their lozenges alone, for a back under about 100 px wide (56 x 78), where a scroll would be a smudge
    plus-lines.svg       (0.33.0) a mask, the strokes alone: the back's corners, the sides' first stretch and a smaller moon, which `.ork-card.ork-plus::before`
                         draws in the card's own colour at 42% round its seal of summoning (the stars and the bead lie under the seal, so they are left out)
    plus-lines-small.svg the small back's sides as a mask, for a + card whose seal is `.small`
    ork.svg         orkUI's ork mark: a 7 x 7 head on the signs' grid (one path of unit squares, a mask like a sign); kept as the mark, no longer drawn by the back

**Since 0.43.0 the backs also have the owner's cartoon take** (O5, kept as drawn: plum ground, the gold filigree, the soft glow round the seal), beside the SVGs: `back.png` (the big card's back), `back-small.png` and `plus.png` (the + card's back, with its gold plus), each
`@2x` and `@3x`, transparent, trimmed to the card with its cream rim and rounded corners, cut from `races/art/cartoon/o5-backs.jpg` by `tools/build_things_from_art.py` (the flat ground and the faint plates under two of the cards are cut away). 1x: `back.png` and
`plus.png` fit in 144 x 202 (the card at 144 px wide), `back-small.png` in 96 x 134 (a back under about 100 px wide); **the sheet's cards are about 9 : 14, a little narrower than the CSS card's 5 : 7**, so each fits by its height. Nothing in `components.css` draws them yet; `.ork-card-back` still draws the SVGs.

**Generated** (`tools/build_back.py`, `--check`): the drawing is made of strokes (arcs, spirals, lines, lozenges, stars) in the top left quarter and mirrored about
the card's two middle lines, so the four corners, the two sides, the top and the bottom are one drawing. It leaves the ring's room (58% of the width round the
centre) empty. Change the drawing there, never the SVGs.

**The ring of runes** is CSS, not the SVG: `.ork-card-back::before` is the mask of the runes' ring `.ork-sigil` draws (`../runes/sigil-runes.svg`, the seven runes of the seal) in `--ork-ink-faint`, centred, **58% of the
back's width**, behind the seal slot. `.ork-card-back.small` swaps the background to `back-small.svg`, draws the ring at **66%** and the seal's element at 14 px.

**The seal** (0.15.1, decisions §160.3): `.ork-card-back__seal` is the slot at the back's centre, in the ring. It holds the element of the
goal that waits next, `<span class="ork-elem dust">` (drawn 28 px, four pixels a cell; 14 px on `.small`), and, beside it, `<span class="ork-sign moon">` when
that goal waits for the reset; the pair is centred. With nothing in the slot the back is the pattern and its ring alone:

    <div class="ork-card-back"><span class="ork-card-back__seal"><span class="ork-elem dust"></span></span></div>
    <div class="ork-card-back small"></div>

`.ork-card-back` in `components.css` draws it (`aspect-ratio: 5 / 7`, `image-rendering: pixelated`, the card's grey under it, the card's frame line
round it). A page that drew its own ring over a back (a `.ork-sigil` in it) drops it: the back has one. A map card's back stays its details (decisions §120.1): this back is the hand's alone.

**The + card and the deck** (0.15.1, decisions §160.2): `.ork-card.ork-plus` is a face-up card whose face is orkUI's `plus` icon centred, 28 px,
and nothing else (the new goal's card). `.ork-deck` is a pile: the backs' edges (`.ork-card-back.edge`, `--ork-deck-i` 1, 2, ... a step of 3 px
each, the far one first), the top back, and the + card lying off its top, to the left (four fifths of its width out, a little up, turned by
the lean token), so the seal stays in view. It is a transform that is still at rest: nothing moves, and under reduced motion nothing does
either. The page gives the deck its width and leaves room at its left. With no back in it, the deck is the + card alone.

**The + card's seal** (0.19.0), `.ork-sigil`: `<span class="ork-sigil" aria-hidden="true"></span>` inside `.ork-card.ork-plus`, before its icon, is the seal of
summoning, written in orkUI's runes (`../runes/README.md`): two circles, a band of seven runes and a star of two squares under the +, in the card's
colour at a quarter's strength, with the place of the goal's element at its top (`.ork-sigil__seal`, 0.20.0: the element the new goal would be given, in its own colour). Its runes light once round the circle on hover, from the top. 0.21.0: it may hold up to four free runes (`.ork-sigil__free`) that show on hover, focus or `.ork-plus.is-choosing`, and `.ork-sigil.is-summoning` with `.rite-<element>` fills it once with the goal's colour (`../runes/README.md`). `.small` is drawn at an 80 px card. **A pile's place** before its first
card is `.ork-card-place`: a card's outline in pixel dashes in the edge, with no fill, never pressed.
