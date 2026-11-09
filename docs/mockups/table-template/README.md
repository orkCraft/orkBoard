# The table's template: a mockup

The mockup decision §283 asks to be drawn first, made by the owner and Claude on 9 November 2026. It is a static page on
orkUI's tokens and classes (`../../../design-system/orkui`): **nothing here is in the product**, and the product's sheets are
untouched. The window is a party game at work, with Game design, Tech, Art and Marketing at the table. The words are samples.
Every picture that Gemini will make (§283.34) is a dashed frame that names its kind (*picture: keep*).

Pictures: `shots/`, made by `shoot.py`, each at 1366 × 768 (the laptop the decision is fitted to), and the project at
1440 × 900 too. To look by hand, serve the repository's root (`python -m http.server`) and open
`http://localhost:8000/docs/mockups/table-template/index.html?scene=project`. orkUI's masks (runes, signs) are not read from
`file://`.

## The scenes

| shot | scene | what it shows (§283) |
|---|---|---|
| `1-project`, `1-project-900` | `?scene=project` | **The Orkmaster's project**, with nothing picked (16.1): a lane for each leader, with the ideas it is assessing now as small cards, then its specs' cascade and its implementation's. The column's three piles (11–13): *Ideas* as a denser fan turned like a hand's, *Specs* as small cards on their side in a deck, *Implementation* as big cards with the feet of those behind (one held for the night, at the foot). The right column (§285): its head holds the row of potions, their tops on one line, the 5 hours' share under each and the week's under each bottle smaller than the large; at its right edge the lamp's chain, half as tall, with *Here* beside it and *Stop all* under it. Under the head the discard's two piles, each under its branch's plate (27). The hand's right end holds the three places that change the table, at one size: the die (*Play*), the backpack and the book. |
| `2-project-balloon` | `&balloon=1` | **The Orkmaster's news** (9): from its crown over the start of the tabs, *Show* and ×, never over the project's name. |
| `3-idea-orkmaster` | `?scene=idea-om` | **An idea, through the Orkmaster** (16.3): the route and its price on a plate, with *Judge again now* (25); under each leader of the route a small card: ✓ face up, ! face up and asking, one face down while it assesses. Marketing, off the route, is grey. |
| `4-idea-orkmaster-hover` | `&hover=1` | **A small card's preview** (4): the same card at 144 × 202 beside it. |
| `5-idea-tech-groups` | `?scene=idea-leader` | **An idea, through Tech** (16.4) in **one row of three groups**, the owner's pick (§284.1): its verdict, *Needs your answer* (a conflict with §208, a risk), *Could be better* (*lighter*, *heavier*). |
| `6-idea-tech-rows` | `&layout=rows` | The same in **three rows**, as §283.16.4 was worded: the third row falls under the hand at 1366 × 768, and the table has to scroll. Not taken. |
| `7-ask-tech` | `?scene=ask` | **The card in play at the table's foot** (19): Tech's conflict lifted to the table's foot at the left, its slot left dashed in its group; its ways are the hand, each a card cut by the rim (one risen, Tech's pick marked by its head), *Tech decides*, *Your own words…*, then *Open…* and *Put it back*. The rest of the hand sinks and goes grey, the places too; *Stop all*, in the right column's head, is not in the hand and stays live (§285.2). |
| `8-tech-project` | `?scene=leader` | **A leader's project** (16.2): the header's three groups (*At work*: ideas and specs face down, implementation face up; *Concerns*: one on a goal, one new with a +; *Ask*: the ? card), and under it the scheme, a concern marked on its part (rooms.ts) and a goal's reach (lobby.ts solid, timer.ts dashed). |
| `9-small-face-b` | `&small=b` | **The small card's second face**: a kind's pip at the top right, the dots centred along the foot. Not taken: the owner picked the first face, `a`, with the dots at the bottom left (§284.2). |
| `10-ask-tech-pictures` | `?scene=ask&pics=1` | **The ways with the owner's pictures** (§283.34, the first sheet of `docs/pictures-wanted.md`, cut into `pictures/`): Tech's conflict lifted, its ways *The new one replaces §208*, *Keep §208* (risen, Tech's pick), *Tech decides*, *Your own words…*, each read **picture first**: its corners, the picture, then its name and its line, so the rim shows the picture and the first words of the name at rest. |
| `11-ask-risk-pictures` | `&card=risk` | The risk lifted: *Keep the last answer only* (mitigate, Tech's pick), *Accept the risk* (risen), *Do the smaller one*, *Later*, *Your own words…*. |
| `12-ways-pictures` | `?scene=pictures` | The sheet's sixteen ways as cards on the table at the size they are played (1440 × 900), each with its `way_kind`. |
| `13-inventory-deep`, `14-inventory-start` | `?scene=inventory&slot=deep\|start` | **The Orkmaster's inventory as slots** (§283.30–31) with the owner's second sheet (`pictures/settings/`): the table in its leather, a row of six slots, each its chosen way as a card read picture first under its label (*How deep*, *The build starts*, *The night*, *Lands in dev by itself*, *Push*, *Goals at once*), its ways' pips, a coin where a cheaper way exists; the slot pressed is ringed and its ways are the hand, *Yours* marked, the Orkmaster's pick starred, each with what it changes in the week, *Undo* and *Put it back*. The backpack drawn open. |
| `15-leader-inventory` | `?scene=leader-inventory&slot=answers` | **A leader's inventory as slots** (§283.33) with the owner's third sheet (`pictures/leader/`): Tech's hero (its head), its AI tool (its name: a tool has no picture, no brand is drawn), its tier, its party's size and how it answers; under them its seats' grid, each seat's head, its tool and its tier as small cards; *How it answers* pressed, *Pen*, *Choice* (Yours, the Orkmaster's pick), *Fork*, *Silent* in the hand. *Silent*'s envelope and the veteran's axe are the owner's retake (crisp, no glow, the axe's engravings no letters). |

## What it found

- **The three rows of an idea through a leader do not fit** at 1366 × 768 (shot 6): 3 × 202 px of cards and their labels
  are taller than the table, so *Could be better* falls under the hand. One row of three groups fits with three cards to
  spare (shot 5). The owner picks; §283.16.4's wording follows the pick.
- **The discard's two piles took the right column whole** while the head held the drum and *Stop all* (84 px): the lower
  pile's card was cut at 1366 × 768. With the row of potions, the chain half as tall and *Stop all* under it (§285), the head is
  about 60 px and both piles' cards lie whole.
- **A back's notch clips the ring that says a card is picked, thinking or alerting** (orkUI's `.ork-card-back` has a
  `clip-path`). Those backs must lose the notch; the change belongs in orkUI.
- **The small card reads by its colour band, rune and picture**. Both faces hold at 56 × 78. The dots are the weakest part:
  5 px squares with party colours side by side.
- **The book is the mockup's own drawing** (a closed book in leather and gilt): orkUI has no book yet (§283.A, orkUI first), shut and open as the backpack is.
- **The + card's seal shows only if the card rises 20 px over the hand's top**, over the column's foot, as the product
  does today.

- **The ways' pictures fit the big card's window as they are**: the sheet's tiles are wider than tall (about 3 : 2), as the
  window of a 144 × 202 card is; a way lives only in the hand at that size, so it needs no small picture. Read picture first,
  a way is told apart before its name is read. Two tiles of the first sheet are weak: *mitigate* (the barrel cut at the tile's
  edge, the bandage apart from it) and *not a problem* (its feather reads as the quill of *your own words*); *accept the risk*
  and *the leader decides* share a red cushion.
- **The owner's second sheet** (the pictures now in `pictures/`): every object stands on one wooden table edge, the palette is
  muted (no signal yellow, no bright green, the cushions purple), one object a tile, a margin to the frame; *mitigate* is whole.
  Its tiles are about 1.9 : 1, the window of a way's card exactly (130 × 68), so a picture fills it with nothing cut. Its
  objects stand smaller in the tile than the first sheet's, so a little less of each reads at a glance. Its third take mends
  the three weak tiles: *the leader decides* a crown on a gavel on a sound block, *take* one hand catching a falling card, *not
  a problem* a fly in a deckchair under an umbrella beside an unused swatter.
- **The pictures came as a JPEG** whose pixels are not on one grid: for the mockup they are halved with nearest neighbour and
  laid on 48 colours; orkUI takes them in only once each is snapped to its grid and its palette.

## Left for the product

The motion (the fan's lift, a way rising, a card flying to the table's foot), the keyboard path, the window under 760 px and
the phone are not in this mockup.
