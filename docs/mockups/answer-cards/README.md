# No big card: a question and its answers as hand cards

A mockup the owner and Claude made on 8 November 2026. Its hypothesis, the owner's: the words an opened card holds at
404 × 566 (spec 147 D.1, decisions §251.1 and §251.6) are not read; a card game splits them instead, **the table says why,
the lifted card says what is asked, and each answer is a card of its own**. Cards would then have two sizes, 144 × 202 and
the Orkmaster's hand 56 × 78. It is a layer of CSS and JS over the live page, drawn over `../table-look/`; **nothing here is
in the product**.

## What it shows

- **The question stays a hand card** (144 × 202) in its signal's ring, **a row above its answers**: its goal's rune and the
  kind's sign at the top, the goal's name, the question, who asks at its foot.
- **Each answer is a card** of the same size, standing on the hand's rim: a way (the compass) with one line of what it
  leads to, the leader's pick marked by its head (*its pick*); **the leader decides** (its head as the sign: the Silent way,
  §266.5); **Your own words…** (the Pen), a dashed card until pressed, then a field under the row with *Send to Game design*.
  A failure has its one way, *Start again*, its cost in the corner.
- **Open…** and **Put it back** at the row's end; the rest of the hand dimmed while a card is up.
- **No new mode for the context** (the owner): lifting a card already turns the table to its goal, so the table is the
  context; **the goal's card in the column is ringed** in the card's signal.

## What it found

- **A goal in analysis has an empty table** (*Its tasks are dealt to the leaders when it is agreed*): the context of a
  question asked in Talk is not on it. If the table is the context, the goal's table must show what the asker said and why
  it asks (its view in Talk, the Open question with its ways) before it is agreed.
- **The cards cover the table's lower left**, the first lanes. With the context on the table, the row may need the hand's
  width instead (the question over its slot, the answers along the hand).
- A way's line (*One clock on the server; …*) is the mockup's own words: today a way has only a button's title. A way card
  needs the leader to write a line per way, short enough for the card (§251: words written to fit).
- A failure has one way: one card. *Open…* (its log) could be a second card.
- **Not shot**: the phone (later, the owner's call), a new goal (the + card opens at 404 × 566 too: it needs a place, likely
  the Orkmaster's first lane), the motion (a card rising on hover, the answer flying to the table).

## What would make it the product

A decision replacing §251.1's opened size and §251.6 (*the opened card never grows*): a lifted card stays 144 × 202, its
answers cards of the same size, the table its context; then a goal for Design and Tech (orkUI's card, `hand/stopcard.js`,
`hand/answers.js`), and Talk's view on a goal's table.

## Files

- `answer-cards.css`, `answer-cards.js`: the mockup (the JS reads the product's lifted card, hides it and lays the cards).
- `shoot.py`: the camera (its docstring has the command; `MOCK_BEFORE=1` for the opened card as it is).
- `shots/`: `before-*` the opened card, `after-*` the cards; both with the table's look, so only the lifted card differs.
