# orkUI / office

Dark, monochrome, soft and warm. **Colour is a signal** (danger, alert, success), except the one ork green of the primary action and
the muted heads of the races. The ground is lifted (canvas `#151412`) and the ink softened (`#dedbd6`, 13.3:1 on the canvas,
not 16:1), so the screen does not glare; the greys are warm in a **half tint** (0.15.0: each grey of the full warm of 0.13.0 taken
halfway to the neutral grey of its own lightness: parchment ink on dark greys with a breath of brown, one tint across the
canvas, panels, table and inks, never a mark), and the table is a warm grey a step above the canvas. Ink on canvas, panel,
raised and table is 13.33, 12.30, 10.94 and 12.82:1; the muted ink 7.78, 7.17, 6.38, 7.48; the faint ink (0.15.3: `#98948e`, a step lighter, so it holds AA on the card) 6.10, 5.63, 5.01, 5.87 and 4.54 on the card;
`edge` 5.39, 4.97, 4.42, 5.18 (3:1 holds on every ground).
The **pixel face** (Pixelify Sans) is for titles, headings and buttons only, never below 12 px, whole pixels, no ligatures, no
faux bold, never for a number or a person's text. **The interface's text is IBM Plex Sans**: body 14/20, caption 12/16 and the
label 12/16 in weight 600 and capitals (on the phone 16/22, 13/18 and 14/16). **IBM Plex Mono** stays the face of code, paths,
diffs, logs and terminals (`--ork-font-code`, `--ork-font-text`). A long text read through is set in Plex Sans, too (15/26).

## Reading

A spec, a document, anything read through rather than glanced at, is set in `.ork-read`: the **paper** (`--ork-paper`
`#1a1816`, a step above the canvas) in the **reading ink** (`--ork-ink-read` `#cac7c1`, 10.5:1, not full ink's 12.8:1 on the
paper, so the letters do not glare) and the **reading face** IBM Plex Sans (15/26 on the desktop, 17/28 on the phone), a line of about
68 characters. Headings, bold and links keep full ink, so the outline stands out; quotes are muted; code stays in Plex Mono.
The interface around a page (its labels, buttons, lists) is set in the interface's own scale.

Nothing is round: edges 1 px, corners notched by 2 px (`clip-path` on a control's `::before`, so the hit area is whole),
dialogs framed `3px double`. A row selected is raised, a card selected keeps its fill, each with a 2 px ink bar, never a white box. **A card is a slate grey on the warm table** (0.15.3, decisions §163; a hint cold since 0.15.4, §166): `card` `#2a2e31` and `card-frame` `#383d41`, blue-greys (CIELAB hue 249 and 251, chroma 2.7 and 3.4, never near an element's: 68 from `ice`, 43 from `void`) a step lighter than `raised`, the table's warmth and the card's cold 175 degrees apart in hue (0.15.3 had neutral `#2e2e2e` and `#3c3c3c`); every card, the lifted card, the back and the + card are drawn on them; the grounds, panels, tabs and the table stay the half tint. Every arrow and icon is a pixel mark.

## The ork legend (a one-character mark never stands alone: its word is beside it)
`@` Taskmaster · `o` Grunt · `?` idea · `*` goal · `+` task

## Where each ork stands
`ork.txt` an empty screen · `ork-asleep.txt` the work waits for the night · `ork-asks.txt` the first thing on the list is a
question · `ork-failed.txt` the only content is a failure · `ork-working.txt` an ork is working and there is nothing to read.
On an empty screen the ork and its sentence are one block, centred on both axes in the pane's free area.

## The table
`.ork-table` is the surface the work lies on (orkboard's field, where the tasks are dealt): a warm grey top
(`--ork-table`, `#1a1816`, a step above the canvas) in a rim 3 px wide (`--ork-table-rim`), its near lip lit by 1 px
(`--ork-table-rim-hi`); all three are warm greys (rim `#3a3832`, lip `#47443e`), no wood. The table is a surface, never a mark: no control, state, label or
person's text takes it, and what lies on the table keeps its own colours (a card its panel, a signal its signal). Text on the
table holds AA as on the canvas (ink 12.8:1); the rim and the lip are steps of the same grey (the lip 1.8:1 on the top), so a
card is set off by its own frame line, not by the table. One table a screen, under the work, never a panel or a dialog.

## Busy
`.ork-busy` says that work is under way where it stands (a card at work, a head that works): 12 px, drawn as an hourglass,
a 6 x 6 grid of 2 px pixels in the faint ink (`--ork-ink-faint`) only. It draws no colour and is never brighter than the
text beside it: work in progress is the quiet state (a question, a failure and money keep their signals). Its sand falls
one grain a second (six frames, `steps`, never a smooth fall); after the last the glass turns over in two steps (90, then
180 degrees) and starts again, about 7 s a round. Under reduced motion it stands still, half run (three grains down).
One per thing at work; never on a control. Pure CSS, no script. The moon stays a goal's progress (`moons/`).

## The races
`races/` holds twelve races in three tiers and the Orkmaster's crowned peon, 37 heads (generated; `../races/README.md`), each **one 12 x 11
grid** as the window always had them (0.15.2 brought them back, decisions §161): 24 x 22 beside a word in a row, 48 x 44 @2x. Seven are
the old heads, as they were (`peon` the ork, `elf`, `goblin`, `gnome`, `knight`, `lich`, `skeleton`); five are drawn in the same manner:
the leaders' higher forms, each its race's head with a
mark drawn inside the grid (`shaman`: ram's horns and a braid on a deeper green, the ork's face, `dryad`: a stag's antlers, `imp`: small
horns and small dark wings on lava's red-brown, `fairy`: large light round wings, `unicorn`: the knight's helm in gold with one horn and white feathered wings at its sides, Product's leader over its knights; the
`lich` leads Release as it is). The race is told by its face, its colour and its detail, the tier by its gear (the race as it is, iron,
a hood), not by the silhouette. No head wears the action's green: the ork's skin is `#939e56` and its shade `#7f8743`, the only old
colours that changed (the old ork was `action` itself); every sprite edge stands at least 3:1 on canvas, panel and raised, and no head
is more colourful than a signal: a state goes beside the head in its signal colour, never onto it.
`.ork-race` puts a head beside its word: `<span class="ork-race"><img class="ork-race__head" src="races/elf-elder.png"
srcset="races/elf-elder@2x.png 2x" alt=""><span class="ork-race__word">… <span class="ork-race__tier">…</span></span></span>`, the head at
**24 x 22**, `.ork-race.big` 48 x 44 (from the @2x image), `.ork-race.mid` 36 x 33 (3 px a cell, a member on a card). There is no
`small`: a head is drawn at its own sizes, never between them and never smaller. A head is an accent, not a picture. `big` and `mid` go on
the head alone too (`.ork-race__head.big`); `.ork-race__head.bare` is the same box for a head drawn without its gear. The gallery shows
every race at every tier at 24 x 22 and 48 x 44, the six leaders in a row, and a window whose tabs wear the leaders by party (Game design
the unicorn over knight members, Tech the shaman over peons, Art the dryad over elves, Release the lich over skeletons, the Orkmaster the
crowned peon).

## The marks
`marks/` holds the AI tools' marks (Claude, Codex, Antigravity, Cursor, Hermes, Pi, Pipeline) and the level chevrons (Novice,
Seasoned, Veteran): 16 x 16 and @2x 32 x 32, copied unchanged from orkLine (`marks/README.md`), and (0.15.0) each in **ink**:
`harness-claude-ink.png`, `rank-2-ink@2x.png`, ... the shape in `--ork-ink` and no other colour, 40 files in all. `<img class="ork-mark"
src="marks/harness-claude.png" srcset="marks/harness-claude@2x.png 2x" alt="">` draws one at 16 x 16, `.ork-mark.big` 32 x 32 from the
@2x file. A mark is an accent beside its name, never alone. The coloured ones keep the tool's own colours, so a person tells the tools
apart where a tool is chosen (a seat's popover); the ink ones go under a head, on a limit's chip and beside a rank.

## The elements
`elements/` holds a goal's five marks in orkBoard (spec 50): meadow (a leaf), ice (a flake), dust (stones), void (an empty ring, never a crescent: the one moon is the sign `moon`), lava (a
flame), each a 7 x 7 grid of unit squares (`elements/README.md`). `<span class="ork-elem meadow" aria-hidden="true"></span>` draws one at
14 x 14, `.ork-elem.big` at 28 x 28, as a mask in the element's colour (`--ork-elem-meadow` … `--ork-elem-lava`: muted, **each of a hue no signal has**, at least 20 (CIE76) from every
signal and from the action's green, each 3:1 on panel and raised: meadow `#6fb8a8` toward teal, dust `#b8914f` a darker ochre, lava `#ad6a5a` a warm
red-brown that is never the danger's, ice `#82aaff`, void `#8e88a8`); `.dim` draws it in `--ork-ink-faint`, for a goal not yet given one.
No size between 14 and 28: whole pixels. The element is shown on a card, never named in the interface.

## The moons
`moons/` holds a goal's progress in orkBoard (spec 74): new, crescent, half, gibbous and full, by its tasks merged, from four 7 x 7 masks
(`disk`, `crescent`, `half`, `gibbous`; `moons/README.md`). `<span class="ork-moon half" aria-hidden="true"></span>` draws one at 14 x 14,
`.ork-moon.big` at 28 x 28: the dark side in `--ork-frame`, the lit part over it in `--ork-ink-muted`, the full moon's in `--ork-ink`
(`.new` has none). No colour and no new token; no size between 14 and 28: whole pixels. A moon is `aria-hidden`, shown beside a goal's
words and never named.

## The signs
`signs/` holds the thirty-nine signs of orkBoard's window (spec 50 §1.6, spec 51 §1, spec 52 §1, spec 56, spec 59): check (done), cross (failed), work (at work), **moon**
(starts by itself later, a crescent alone: it was `night`, a crescent and a star, before 0.15.0; the one moon of the window), alert (a stop that asks), flag (a goal in main),
before (what a task waits for), after (what waits for it), and the media signs play and pause (a sound's or a clip's control), sound (a sound's tile), film (a clip's tile) and text
(a text's tile), **sword** and **shield** (0.15.0: a squad's *Does* and *Checks* columns, never a state's sign), **question** (0.15.5: a question the person answers, drawn beside `alert` and `target`), and a goal type's mark, each type its own: feature, bug, tidy,
restructure, screen, picture, logo, target, flask, horn, chart, page, abtest, landing, post, tagline, mechanic, level, balance, character, release, store, tune,
each a 7 x 7 grid of unit squares (`signs/README.md`, which says which the window as decided draws and that the goal types' signs stay for Orkline). `<span class="ork-sign check" aria-hidden="true"></span>` draws one at 14 x 14, `.ork-sign.big`
at 28 x 28, as a mask in `currentColor`: the colour of the text it stands in (ink, muted, success, danger or alert; a sign adds no colour
of its own). `vertical-align: -3px` sets it on the baseline of a 16 px line. No size between 14 and 28: whole pixels. A sign stands beside
its words (or a `title`) and is `aria-hidden`.

## The icons
`icons/icons.svg` is the sprite of the window's icons (`icons/README.md`). Twelve are **orkUI's own** (0.15.0), drawn on the signs' 7 x 7 grid in solid pixels: `arrow-left`, `close` (×),
`more-horizontal` (…), `plus`, `search`, `mic`, `play`, `stop` and the four chevrons; at 14, 21 or 28 px (two, three or four pixels a cell) they are whole pixels. The other 22 are
Pixelarticons (MIT), kept for Orkline. The gallery shows both.

## The parts of the one window
`.ork-gem` a price, a share of the limits or a mark before a move (inverted, 22 px; `.alert`, `.danger`, `.dim`; 24 px on a phone; **`.share`** a share of the limits, *4%*,
in the label's token on the frame's colour, and `.share.alert` / `.share.danger` when it warns) · `.ork-stat` a
measured number (outlined, 20 px) · `.ork-crystals` a row of `<i>` diamonds for what is left of a tool (`.on`, `.kept` hatched
for what is kept for tonight) · `.ork-frame` the double frame of a raised thing (`.alert`, `.danger`) · **`.ork-picked`** a card taken: pixel brackets at its four corners,
2 px thick and 8 px long, in the ink only · **`.ork-box`** the box being drawn: a dashed 2 px line in the ink. Tokens only, as every
component: ink, alert and danger are the signals, nothing new.

## The motions
How a card answers a hand (orkBoard's decisions §149). The times, the curves, the angle, the rise, the press and the shards' count are **tokens**, a group `motion` of
`tokens.json` (`--ork-motion-quick` 120ms, `-base` 180ms, `-sure` 250ms, `-play` 400ms, `-deal-gap` 40ms, `-spring` `cubic-bezier(.34,1.56,.64,1)`, `-ease`, `-lean` 6deg, `-rise` 4px,
`-press` 0.96, `-shards` 6); the components read only them, and only transforms move. **`.ork-card.ork-leans`** leans toward the pointer by the page's `--ork-lean-x` and
`--ork-lean-y` (-1 to 1) at most the lean token and rises on a pixel shadow (hovered, or `.is-lifted`), gives to the press token when pressed and springs back; `.is-read` is flat.
**`.ork-deal`** (dealt, one after another, `--ork-deal-i`), **`.ork-play`** (lifts, flies to `--ork-play-x/-y`, lands with an overshoot), **`.ork-seal`** (the stamp lands a little
large and settles), **`.ork-crumble`** (six pixel squares in `<i>` fall, they do not fade) and **`.ork-fan`** (spread, one after another; `.closing` closes it the same way) are
keyframes on the tokens: the page adds the class when it happens. **No idle motion**: a card at rest is flat. Under `prefers-reduced-motion` every one is still. The gallery plays
each on a press.

## The back
`backs/back.svg` is the one back of a hand card face down (the deck, the cards under a stack's top, the discard's), 15 x 21 pixels (5 : 7) in the card's frame grey and the faint ink's grey on
the card's grey: **no colour** (`backs/README.md`). Since 0.15.1 it carries no mark: at its middle lies the **seal slot**, `.ork-card-back__seal`, which holds the element of the goal that waits
next (`<span class="ork-elem dust">`, drawn 28 px) and, beside it, the sign `moon` when that goal waits for the reset, the pair centred; with nothing in it the back is the pattern alone.
`<div class="ork-card-back"><span class="ork-card-back__seal"><span class="ork-elem dust"></span></span></div>` draws it; at 120 x 168 a pixel is 8 px, whole. A map card's back stays its details.
`.ork-card.ork-plus` is the new goal's card, face up, its face the `plus` icon centred at 28 px and nothing else; `.ork-deck` is a pile (the backs' edges, `--ork-deck-i`, the top back) with the
+ card lying off its top, to the left, a little up and turned by the lean token: a transform, still at rest and under reduced motion. The page gives the deck its width and room at its left.

Pointer targets are at least 24 x 24 px; on the phone a control is 40 px drawn and 44 px to hit (`min-height: var(--ork-tap)`).
