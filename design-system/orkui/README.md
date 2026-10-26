# orkUI / office

Dark, monochrome, dense. **Colour is a signal** (danger, alert, success), except the one ork green of the primary action,
the muted heads of the races and the table's wood.
The **pixel face** (Pixelify Sans) is for buttons and headings only, never below 12 px, whole pixels, no ligatures, no faux
bold, never for a number or a person's text; **everything else is IBM Plex Mono** (12/18 on the desktop, 16/22 on the phone),
but a long text read through.

## Reading

A spec, a document, anything read through rather than glanced at, is set in `.ork-read`: the **paper** (`--ork-paper`
`#141414`, a step above the canvas) in the **reading ink** (`--ork-ink-read` `#c4c4c4`, about 10:1, not full ink's 16:1, so
the letters do not glare) and the **reading face** IBM Plex Sans (15/26 on the desktop, 17/28 on the phone), a line of about
68 characters. Headings, bold and links keep full ink, so the outline stands out; quotes are muted; code stays in Plex Mono.
The interface around a page (its labels, buttons, lists) stays in Plex Mono.

Nothing is round: edges 1 px, corners notched by 2 px (`clip-path` on a control's `::before`, so the hit area is whole),
dialogs framed `3px double`. Selected is raised with a 2 px ink bar, never a white box. Every arrow and icon is a pixel mark.

## The ork legend (a one-character mark never stands alone: its word is beside it)
`@` Taskmaster · `o` Grunt · `?` idea · `*` goal · `+` task

## Where each ork stands
`ork.txt` an empty screen · `ork-asleep.txt` the work waits for the night · `ork-asks.txt` the first thing on the list is a
question · `ork-failed.txt` the only content is a failure · `ork-working.txt` an ork is working and there is nothing to read.
On an empty screen the ork and its sentence are one block, centred on both axes in the pane's free area.

## The table
`.ork-table` is the surface the work lies on (orkboard's field, where the tasks are dealt): a dark walnut top
(`--ork-table`) in a wooden rim 3 px wide (`--ork-table-rim`), its near lip lit by 1 px (`--ork-table-rim-hi`). The wood is
a material, never a mark: no control, state, label or person's text takes it, and what lies on the table keeps its own
colours (a card its panel, a signal its signal). Text on the table holds AA as on the canvas; the lit lip stands 3:1 on the
top and on the canvas, so the table's bound reads. One table a screen, under the work, never a panel or a dialog.

## Busy
`.ork-busy` says that work is under way where it stands (a card at work, a head that works): 12 px, drawn as an hourglass,
a 6 x 6 grid of 2 px pixels in the faint ink (`--ork-ink-faint`) only. It draws no colour and is never brighter than the
text beside it: work in progress is the quiet state (a question, a failure and money keep their signals). Its sand falls
one grain a second (six frames, `steps`, never a smooth fall); after the last the glass turns over in two steps (90, then
180 degrees) and starts again, about 7 s a round. Under reduced motion it stands still, half run (three grains down).
One per thing at work; never on a control. Pure CSS, no script. The moon stays a goal's progress (`moons/`).

## The races
`races/` holds the seven races in three tiers and the peon's crown (generated; `../races/README.md`): 24 x 22 beside a word in a row, 48 x 44 @2x.
They are the look's raster art with the marks below, in colour but muted: no head is more colourful than a signal, and a state
goes beside the head in its signal colour, never onto it.
`.ork-race` puts a head beside its word: `<span class="ork-race"><img class="ork-race__head" src="races/elf-elder.png"
srcset="races/elf-elder@2x.png 2x" alt=""><span class="ork-race__word">… <span class="ork-race__tier">…</span></span></span>`, 24 x 22
in a row, `.ork-race.big` 48 x 44, `.ork-race.mid` 36 x 33 (3 px a cell, from the @2x image: a member's head), `.ork-race.small` 12 x 11
(a cell a pixel: an accent in a line of text, beside a task or in a chip). A head is an accent, not a picture: the smallest that
says it. `big`, `mid` and `small` go on the head alone too (`.ork-race__head.mid`).

## The marks
`marks/` holds the AI tools' marks (Claude, Codex, Antigravity, Cursor, Hermes, Pi, Pipeline) and the level chevrons (Novice,
Seasoned, Veteran): 16 x 16 and @2x 32 x 32, copied unchanged from orkLine (`marks/README.md`). `<img class="ork-mark"
src="marks/harness-claude.png" srcset="marks/harness-claude@2x.png 2x" alt="">` draws one at 16 x 16, `.ork-mark.big` 32 x 32 from the
@2x file. A mark is an accent beside its name, never alone; its colours are the tool's own, so a person tells the tools apart.

## The elements
`elements/` holds a goal's five marks in orkBoard (spec 50): meadow (a leaf), ice (a flake), dust (stones), void (a crescent), lava (a
flame), each a 7 x 7 grid of unit squares (`elements/README.md`). `<span class="ork-elem meadow" aria-hidden="true"></span>` draws one at
14 x 14, `.ork-elem.big` at 28 x 28, as a mask in the element's colour (`--ork-elem-meadow` … `--ork-elem-lava`: muted, none the success
green nor the alert or danger hue, each 3:1 on panel and raised); `.dim` draws it in `--ork-ink-faint`, for a goal not yet given one.
No size between 14 and 28: whole pixels. The element is shown on a card, never named in the interface.

## The moons
`moons/` holds a goal's progress in orkBoard (spec 74): new, crescent, half, gibbous and full, by its tasks merged, from four 7 x 7 masks
(`disk`, `crescent`, `half`, `gibbous`; `moons/README.md`). `<span class="ork-moon half" aria-hidden="true"></span>` draws one at 14 x 14,
`.ork-moon.big` at 28 x 28: the dark side in `--ork-frame`, the lit part over it in `--ork-ink-muted`, the full moon's in `--ork-ink`
(`.new` has none). No colour and no new token; no size between 14 and 28: whole pixels. A moon is `aria-hidden`, shown beside a goal's
words and never named.

## The signs
`signs/` holds the thirty-six signs of orkBoard's window (spec 50 §1.6, spec 51 §1, spec 52 §1, spec 56, spec 59): check (done), cross (failed), work (at work), night
(held for tonight, a moon and a star), alert (a stop that asks), flag (a goal in main), before (what a task waits for), after (what waits for it),
and the media signs play and pause (a sound's or a clip's control), sound (a sound's tile), film (a clip's tile) and text (a text's tile),
and a goal type's mark, each type its own: feature, bug, tidy, restructure, screen, picture, logo, target, flask, horn, chart, page, abtest, landing, post, tagline, mechanic, level, balance, character, release, store, tune,
each a 7 x 7 grid of unit squares (`signs/README.md`). `<span class="ork-sign check" aria-hidden="true"></span>` draws one at 14 x 14, `.ork-sign.big`
at 28 x 28, as a mask in `currentColor`: the colour of the text it stands in (ink, muted, success, danger or alert; a sign adds no colour
of its own). `vertical-align: -3px` sets it on the baseline of a 16 px line. No size between 14 and 28: whole pixels. A sign stands beside
its words (or a `title`) and is `aria-hidden`. The close (×), the plus (+) and the chevrons (›, ⌄) are icons (`icons/icons.svg`).

## The parts of the one window
`.ork-gem` a price or a mark before a move (inverted, 22 px; `.alert`, `.danger`, `.dim`; 24 px on a phone) · `.ork-stat` a
measured number (outlined, 20 px) · `.ork-crystals` a row of `<i>` diamonds for what is left of a tool (`.on`, `.kept` hatched
for what is kept for tonight) · `.ork-frame` the double frame of a raised thing (`.alert`, `.danger`). Tokens only, as every
component: ink, alert and danger are the signals, nothing new.

Pointer targets are at least 24 x 24 px; on the phone a control is 40 px drawn and 44 px to hit (`min-height: var(--ork-tap)`).
