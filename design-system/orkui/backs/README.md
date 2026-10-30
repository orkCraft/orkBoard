# orkUI / office / backs

**The back**: a hand card face down (orkBoard's decisions §149.3, §160.3): the deck, the cards under a stack's top, the discard's cards
under its top. One pattern, `back.svg`, drawn on a **15 x 21** grid of unit squares (5 : 7, a card): a border in the faint ink's grey, a
lattice of pixels and an empty ring at the middle in the card's frame grey, on the card's grey (0.15.3, decisions §163; a slate grey `#2a2e31` with `#383d41` since 0.15.4, §166). **No colour**: the three greys are the
tokens `--ork-ink-faint`, `--ork-card-frame` and `--ork-card`, and a test holds the file to them. Since 0.15.1 the back draws no mark: the ork
mark that stood in the ring is gone.

    back.svg   the back: the pattern, three fills
    ork.svg    orkUI's ork mark: a 7 x 7 head on the signs' grid (one path of unit squares, a mask like a sign); kept as the mark, no longer drawn by the back

**The seal** (0.15.1, decisions §160.3): `.ork-card-back__seal` is the slot at the back's centre, in the ring. It holds the element of the
goal that waits next, `<span class="ork-elem dust">` (drawn 28 px, four pixels a cell), and, beside it, `<span class="ork-sign moon">` when
that goal waits for the reset; the pair is centred. With nothing in the slot the back is the pattern alone:

    <div class="ork-card-back"><span class="ork-card-back__seal"><span class="ork-elem dust"></span></span></div>

`.ork-card-back` in `components.css` draws it (`aspect-ratio: 5 / 7`, `image-rendering: pixelated`, the card's grey under it, the card's frame line
round it). A map card's back stays its details (decisions §120.1): this back is the hand's alone.

**The + card and the deck** (0.15.1, decisions §160.2): `.ork-card.ork-plus` is a face-up card whose face is orkUI's `plus` icon centred, 28 px,
and nothing else (the new goal's card). `.ork-deck` is a pile: the backs' edges (`.ork-card-back.edge`, `--ork-deck-i` 1, 2, ... a step of 3 px
each, the far one first), the top back, and the + card lying off its top, to the left (four fifths of its width out, a little up, turned by
the lean token), so the seal stays in view. It is a transform that is still at rest: nothing moves, and under reduced motion nothing does
either. The page gives the deck its width and leaves room at its left. With no back in it, the deck is the + card alone.

**The + card's seal** (0.19.0), `.ork-sigil`: `<span class="ork-sigil" aria-hidden="true"></span>` inside `.ork-card.ork-plus`, before its icon, is the seal of
summoning, written in orkUI's runes (`../runes/README.md`): two circles, a band of seven runes and a star of two squares under the +, in the card's
colour at a quarter's strength, with the place of the goal's element at its top (`.ork-sigil__seal`, 0.20.0: the element the new goal would be given, in its own colour). Its runes light once round the circle on hover, from the top. 0.21.0: it may hold up to four free runes (`.ork-sigil__free`) that show on hover, focus or `.ork-plus.is-choosing`, and `.ork-sigil.is-summoning` with `.rite-<element>` fills it once with the goal's colour (`../runes/README.md`). `.small` is drawn at an 80 px card. **A pile's place** before its first
card is `.ork-card-place`: a card's outline in pixel dashes in the edge, with no fill, never pressed.
