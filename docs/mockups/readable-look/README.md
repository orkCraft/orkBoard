# The readable look: a mockup

Asked by the owner on 10 November 2026: now that the pictures leave pixels for the cartoon (decisions §289, §290), can the
fonts, the colours and the cards' corners change too, so the window reads better, on a phone above all? This mockup lays
three proposed looks over the existing mockups (the table's template, `../table-template/`, and the phone's hand,
`../phone/hand.html`) by stylesheets only. **Nothing here is in the product**: orkUI's copy and the product's sheets are
untouched, and a look taken is made in orkUI first (CLAUDE.md, *The design system is orkUI*). The words are the mockups'.

Pictures: `shots/`, made by `shoot.py` (`uv run --with playwright python docs/mockups/readable-look/shoot.py`).

| shot | what it shows |
|---|---|
| `compare-phone-hand.png` | the phone upright (390 × 844, drawn at DPR 3, shown at 2): today and A, B, C side by side |
| `compare-desktop-cards.png` | the table's first row and its cards close up, a laptop at DPR 2 |
| `compare-desktop-ask.png`, `compare-desktop-project.png` | the whole window at 1366 × 768, DPR 1 |
| `specimen.png` | each look's faces on a card, Latin and Cyrillic, numbers and look-alike letters (`Il1 O0`) |

## What every proposed look shares (`looks/base.css`)

- **Type a size up**: body 15 px (today 14), caption 13 (12), a card's name in the heading face; nothing under 12 px.
- **The pixel face goes**: headings and buttons take the look's heading face; code, paths and ids keep IBM Plex Mono.
- **Colours a step lifted, the same warm room**: a card `#33373a` on the table (today `#2a2e31`: 1.47:1 against the table,
  today 1.29), its frame `#4c5257` (1.52:1 against the card, today 1.25), the faint words `#a8a39a` (4.8:1 on a card, today
  4.5), the muted `#bbb6ad` (6.0:1), the ink `#ebe7e0` (9.8:1). The parties', the elements' and the signals' colours stay
  (§268).
- **Round corners**: orkUI's notch becomes a round corner (`--ork-notch: inset(0 round r)`), a card 6–10 px, a button or a
  chip 4–6 px, a picture's place inside a card a little less; a card's top edge a faint light line.

## The three looks

| look | heading | body | corner | for it | against it |
|---|---|---|---|---|---|
| **A, the tavern** (`looks/a-tavern.css`) | Rubik 700 | Rubik 400 | 10 px | one family, soft corners that answer the cartoon's thick round outlines; a card game's weight; even Cyrillic; clear numbers | the most ordinary of the three |
| **B, the poster** (`looks/b-poster.css`) | Unbounded 500 | Onest 400 | 8 px | the most character: a game's title screen; Onest reads best at small sizes | Unbounded is wide: a card's name takes a line more (the desktop's cards), long words break |
| **C, the tale** (`looks/c-tale.css`) | Alegreya SC 700 | Alegreya Sans 400 | 6 px | a storybook, the history book's tone; the warmest | small caps at 12–14 px are small; old-style figures (`1234` drop below the line) and `Il1` alike: the numbers, the mana, the prices read worst |

## What it found

- **Pixelify's Cyrillic reads worst of all** (the specimen: *Пусть* reads as *Пуcтb*): a person's words in Russian on a
  button or a heading are a reason on their own to leave the pixel face.
- **The colours' step is small and enough**: the card stands off the table on a phone at night; the faint words pass AA
  with room at 13 px.
- **The round corner takes nothing away from the cards' pictures**, pixel or cartoon; the pixel signs and runes look like
  icons on it, and are decided with the pictures (§289.2).
- Today's sheets set 10–11 px in many places (`orkboard/gui/static`), under the tokens' sizes: a look taken also means those
  sizes come to the type tokens.

Fonts: `fonts/`, copied unchanged from Fontsource, SIL Open Font License 1.1, their licences beside them (`NOTICE`).
