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
| `1-project`, `1-project-900` | `?scene=project` | **The Orkmaster's project**, with nothing picked (16.1): a lane for each leader, with the ideas it is assessing now as small cards, then its specs' cascade and its implementation's. The column's three piles (11–13): *Ideas* as a denser fan turned like a hand's, *Specs* as small cards on their side in a deck, *Implementation* as big cards with the feet of those behind (one held for the night, at the foot). The right column (7): its head holds the drum, *Stop all* and the lamp's chain; under it the discard's two piles, each under its branch's plate (27). The hand's right end holds the die, the backpack and the book. |
| `2-project-balloon` | `&balloon=1` | **The Orkmaster's news** (9): from its crown over the start of the tabs, *Show* and ×, never over the project's name. |
| `3-idea-orkmaster` | `?scene=idea-om` | **An idea, through the Orkmaster** (16.3): the route and its price on a plate, with *Judge again now* (25); under each leader of the route a small card: ✓ face up, ! face up and asking, one face down while it assesses. Marketing, off the route, is grey. |
| `4-idea-orkmaster-hover` | `&hover=1` | **A small card's preview** (4): the same card at 144 × 202 beside it. |
| `5-idea-tech-groups` | `?scene=idea-leader` | **An idea, through Tech** (16.4) in **one row of three groups**: its verdict, *Needs your answer* (a conflict with §208, a risk), *Could be better* (*lighter*, *heavier*). |
| `6-idea-tech-rows` | `&layout=rows` | The same in **three rows**, as §283.16.4 is worded: the third row falls under the hand at 1366 × 768, and the table has to scroll. |
| `7-ask-tech` | `?scene=ask` | **The card in play at the table's foot** (19): Tech's conflict lifted to the table's foot at the left, its slot left dashed in its group; its ways are the hand, each a card cut by the rim (one risen, Tech's pick marked by its head), *Tech decides*, *Your own words…*, then *Open…* and *Put it back*. The rest of the hand sinks and goes grey. |
| `8-tech-project` | `?scene=leader` | **A leader's project** (16.2): the header's three groups (*At work*: ideas and specs face down, implementation face up; *Concerns*: one on a goal, one new with a +; *Ask*: the ? card), and under it the scheme, a concern marked on its part (rooms.ts) and a goal's reach (lobby.ts solid, timer.ts dashed). |
| `9-small-face-b` | `&small=b` | **The small card's second face**: a kind's pip at the top right, the dots centred along the foot (the first face, `a`, has the dots at the bottom left). |

## What it found

- **The three rows of an idea through a leader do not fit** at 1366 × 768 (shot 6): 3 × 202 px of cards and their labels
  are taller than the table, so *Could be better* falls under the hand. One row of three groups fits with three cards to
  spare (shot 5). The owner picks; §283.16.4's wording follows the pick.
- **The discard's two piles take the right column whole**: with the head at 84 px, the lower pile's card is cut by a few
  pixels at 1366 × 768. Either the upper pile shows the feet of its cards (as *Implementation* does), or the head stays
  this low.
- **A back's notch clips the ring that says a card is picked, thinking or alerting** (orkUI's `.ork-card-back` has a
  `clip-path`). Those backs must lose the notch; the change belongs in orkUI.
- **The small card reads by its colour band, rune and picture**. Both faces hold at 56 × 78. The dots are the weakest part:
  5 px squares with party colours side by side.
- **The book is a placeholder**: orkUI has no book yet (§283.A, orkUI first).
- **The + card's seal shows only if the card rises 20 px over the hand's top**, over the column's foot, as the product
  does today.

## Left for the product

The motion (the fan's lift, a way rising, a card flying to the table's foot), the keyboard path, the window under 760 px and
the phone are not in this mockup.
