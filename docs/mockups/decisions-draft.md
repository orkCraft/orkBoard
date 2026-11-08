# Draft: six decisions from the mockups of 7–8 November 2026

A draft for the owner, **not a decision**: nothing here is in `docs/decisions.md` until the owner says yes; then each is
written there as it stands (or as changed), and this file goes. The mockups: `table-look/`, `answer-cards/`, `room-things/`.
The numbers follow §267, the last written. The owner's answers of 8 November are in them (the open questions 1–11); the
work after them is **one goal** for Design and Tech: orkUI first (its tokens, components and drawings), copied here, then
`gui/`; the phone a goal of its own, later.

---

## 268. Colour is the party, the element and a signal (8 November 2026, the owner)

Changes: 53.5 (colour means a signal), 92.2 (the table's wood as its exception); where 106, 115 and 148 say *colour is a
signal*, they read as this.

Why: the owner, on the mockup `docs/mockups/table-look/`: the window is flat; *colour is not only a signal*. So:
1. **Three layers of colour, told apart by their form, never mixed.** **The party** (its race) colours the frame of things:
   its tab's name, the rule under its tab, the light down its lane, its pennant, its table's felt. **The goal's element**
   colours the face of its cards: a band on top, a tinted face, the window round its sign. **A signal** (danger, alert,
   success) is the brightest, always a ring and an icon, never a fill.
2. **Nothing hides a signal.** A party's or an element's colour is never a ring round a card and never as bright as a
   signal. A test checks that a signal is seen on every felt and every element.
3. **The parties' colours, by race:** knights gold (Game design, Product), orks moss (Tech), elves plum (Design, Art), the
   undead night blue (Release), goblins rust (Run, LiveOps), gnomes sea (Marketing), the Orkmaster the table's warm wood.
   orkUI keeps them apart from the signals' hues; Tech's moss stays as the mockup has it (`#8fbf4a`), beside the action's
   green.
4. **Still without colour:** a person's words, a control's state, a label's meaning. The ork green stays the one green of
   a button.

The owner's call.

## 269. The table's look: a lamp at its top edge, each leader's felt, bronze frames, a pennant over each leader (8 November 2026, the owner)

Changes: 266.8 (the craft textures on the tables); 92.1 (the table's wood stays, as the Orkmaster's felt).

Why: the owner, on the same mockup: a table lit and framed as a game's, retro, with no smooth gradients. So:
1. **The light from the table's top edge**, in half rings, five steps, each step's edge dithered by a 2 px checker in the
   next step's colour. No smooth gradient anywhere (the room, the table, a lane, a card, the hand); a shadow or a glow is
   hard pixel rings, never a blur. The light is the lamp's (§271): out, it goes.
2. **Each leader's table its own felt**, in its party's colour, dark: Tech moss, Game design and Product oxblood with a
   gilt rim, Design and Art plum, Release night blue, Run and LiveOps rust, Marketing sea; the Orkmaster's the warm wood.
3. **Bronze frames** with rivets at the corners round the table, the column, the discard and the hand; the headings on
   bronze plaques, in the pixel face.
4. **A swallowtail pennant on a pole** in the party's colour over each leader, taller over the open one, clear of the
   window's top edge. Not the merchant mockup's craft pennants.
5. **A lane** has its party's light in three steps down from its tab; **an empty lane says whose it is** and how to give
   it a goal (*Release is free · throw a goal here or @Release*).
6. **A card**: a thick frame in its element's colour with a gilt inner line, the element in steps down its face, a
   bevelled window, the goal's strip a ribbon. A signal's ring is one ring and a faint second; in the column's stacked
   rows, its border.
7. **The hand** fans slightly (±2°) at the desktop's width; a card rises toward you on hover. Reduced motion: neither.
8. **Dropped:** the craft textures (§266.8) and the heads and signs drawn at twice the grid.
9. **orkUI first:** its tokens and components (the felts, the steps, `.ork-table`, `.ork-card`, a plaque, a pennant),
   copied here, then `gui/`.

The owner's call.

## 270. No big card: a lifted card stays a hand card, its answers are the hand, the table is its context (8 November 2026, the owner)

Changes: 251.1 (the opened size, 404 × 566), 251.6 (the opened card never grows); spec 147 D.1.

Why: the owner: *the words a big card holds will not be read*; a card game splits them: the table says why, the lifted
card what is asked, each answer is a card (`docs/mockups/answer-cards/`). So:
1. **A lifted card rises out of its slot onto the table's foot**, 144 × 202, in its signal's ring; the goal's card in the
   column is ringed the same.
2. **Its answers are the hand**: each a card of the same size, lying where the hand's cards lie, cut by the rim, rising
   when hovered: a way with one line of what it leads to (its point in its first words), the leader's pick marked by its
   head; *<Leader> decides* (the Silent way, §266.5); **Your own words…** (the Pen), pressed, a field on the table beside
   the question with *Send to <leader>*. A failure's ways the same (*Start again*, its cost in the corner). *Open…* and
   *Put it back* at the row's end.
3. **The rest of the hand sinks and goes grey** while a card is up, the + card, the die and the potions with it.
4. **The table is the context, no new mode**: lifting a card already turns the table to its goal. A goal not yet agreed
   lays on its table what its leaders said in Talk and its open question with its ways.
5. **A way's line is its leader's**, written to fit the card (§251).
6. **A new goal is made in the Orkmaster's first lane**, not opened: the + card lays a card of 144 × 202 at the lane's
   top, its words written in its middle, **its settings at its four corners** as every card is read (§251.2): top left its
   element, top right its kind (feature, bug, tidy, screen), bottom left who (the parties of its route, the Orkmaster's
   until changed), bottom right how much (its price, when it starts). A corner pressed deals its choices to the hand, as a
   question's answers are; the Orkmaster's pick starred.
7. Cards have two sizes on the desktop: 144 × 202 and the Orkmaster's hand 56 × 78. The phone follows in a goal of its own.

The owner's call.

## 271. The lamp is the person: its chain where the door stood, lit *Here*, out *Away* (8 November 2026, the owner)

Changes: 246.4 (the door's drawing and its place), 201.8 (orkUI's door). What Here and Away do (§246.4–5) is unchanged.

Why: the owner, on `docs/mockups/room-things/`: the door is one more sign; a lamp over the table makes the person's
presence the room's own light. So:
1. **A lamp's chain** hangs from the window's top edge at the head of its right column (the Release column, the discard),
   a bead to pull; its words beside it as the door's were: *Here · until 23:00*, *Away · until 19:00*, *· held* after a
   pull while the hours lead.
2. **Lit, the person is here**: the table's light (§269.1). **Out, away**: the light goes, the felt flat and darker, the
   lanes unlit but for the rule under their tabs; the cards keep their faces and a signal stays as bright.
3. **Pulled, it turns** as the door did (`presence.set`); the hours pull it by themselves (§246.4). The chain moves once,
   briefly; under reduced motion it is at once.
4. **orkUI draws the chain** (its bronze, the bead, pulled and at rest), in place of its door.
5. **Under 760 px** the chain and the backpack stand without their words (their `aria-label` and `title` keep them).

The owner's call.

## 272. The backpack and the new chair are things at the table's edge: the chair deals its crafts, the pick opens the backpack on it (8 November 2026, the owner)

Changes: 267.1 (the backpack at the tabs' end; the stall told by its stitched edge), 201 (the empty chair's press), spec 98
§3.6 (*New party* as a place over the pane).

Why: the owner, on the same mockup: the top row's controls as things; *the chair's press should deal the kinds of leader
to the hand, as a question's answers are, and the pick should open the backpack on that kind*. So:
1. **The backpack stands at the head of the discard's column** (§273), beside the lamp's chain (188 px holds both: the
   column is not widened). **orkUI draws it shut and open** (the flap fastened; thrown back, a card in its mouth). **Open, the table lies
   in its leather**: a stitched leather frame in place of the bronze, two straps with buckles over its top edge, no rivets;
   shut, the bronze is back.
2. **The new chair stays at the tabs' end.** Pressed, it is lit, the Orkmaster's question rises onto the table (*A new
   chair at the table · Which craft sits in it?*) and **the hand holds a card a craft not yet seated**, of those offered
   for the project's kind and stage (`project_stage.crafts`): its race's head, its line, its price a week; **the
   Orkmaster's pick starred** in the top corner. The rest of the hand sinks (§270.3); *Put it back* seats nothing.
3. **A craft's card pressed seats it**: its tab stands where the chair stood (its leader's head, its pennant, *new*), and
   **the backpack opens on its chair**: its heroes on the rug, its default starred and in the hand, a price plate under
   each; a hero is changed there as any ware (§267).
4. **Money is said before it is spent**: the craft's card says its price a week before the press (§57.3, §160.6); the
   chair's press alone seats nothing.
5. **New party's form goes**: the project's kind and stage (*Idea*, *Being made*, *Live*) are set at the Orkmaster's chair
   in the backpack, as its wares.

The owner's call.

## 273. The discard stands beside the table, not under Release: the window's right column is its own, its head the room's things (8 November 2026, the owner)

Changes: 261.7 (the discard under Release's tab, the row's last); 176.3 and 167 (the discard lies on the table, at its
right); CLAUDE.md's frame says *the discard … lies beside the table* once this is written.

Why: the owner, when the backpack and the lamp's chain needed a place: the right column's head is where they stand, so
the discard is not Release's: *we make it outside the table*. So:
1. **The discard is the window's right column, beside the table**, on every tab: what it holds is §261.7's (the done
   through the open tab's eyes, *<party>'s discard*, the portal round the card ready for main at its top, the past deeper
   in it, §261.8–9).
2. **Release's tab stands in the row with the other leaders'**, in the route's order (§266.7), not over the column.
3. **The column's head holds the room's things**: the backpack at its left, the lamp's chain at its right (§271, §272),
   over the label *Discard*. The column keeps its width.
4. The hand's right end under it is §261.11's (the die, the drum of potions).

The owner's call.
