# orkUI / office

Dark, monochrome, soft and warm. **Colour is a signal** (danger, alert, success), except the one ork green of the primary action and
the muted heads of the races. The ground is lifted (canvas `#151412`) and the ink softened (`#dedbd6`, 13.3:1 on the canvas,
not 16:1), so the screen does not glare; the greys are warm in a **half tint** (0.15.0: each grey of the full warm of 0.13.0 taken
halfway to the neutral grey of its own lightness: parchment ink on dark greys with a breath of brown, one tint across the
canvas, panels, table and inks, never a mark), and the table is a warm grey a step above the canvas. Ink on canvas, panel,
raised and table is 13.33, 12.30, 10.94 and 12.82:1; the muted ink 7.78, 7.17, 6.38, 7.48; the faint ink (0.15.3: `#98948e`, a step lighter, so it holds AA on the card) 6.10, 5.63, 5.01, 5.87 and 4.54 on the card;
`edge` 5.39, 4.97, 4.42, 5.18 (3:1 holds on every ground).
**`room`** (0.27.0, `#090807`: near black, a step under the canvas, never `#000`, so the screen does not glare) is the dark of the room the leaders sit in and of the hand's
floor: the ink is 14.49:1 on it, the muted ink 8.45, the faint ink 6.63 (each holds AA 4.5:1) and the edge 5.85 (3:1 holds).
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

**The faces** (0.27.0, Orkboard's decision §201): each leader race (shaman, dryad, imp, fairy, unicorn, lich), at every tier, and the Orkmaster's crown wear five faces besides
the calm one, `focused`, `worried`, `no`, `pleased` and `asleep`: `races/<race>-<tier>-<mood>.png` and `@2x` (`races/shaman-elder-worried.png`, `races/peon-crown-no@2x.png`),
the head's own grid with a few cells of its eyes' and mouth's rows edited (`faces` in `races/races.json`), 24 x 22 and 48 x 44 as every head. A face is a **state** the page
chooses, never an idle motion; the unicorn's helm has no mouth; the members' races have none; the tier changes the gear and never the face. `<img class="ork-race__head" src="races/shaman-elder-worried.png"
srcset="races/shaman-elder-worried@2x.png 2x" alt="">` draws one as it draws the calm head.

## The marks
`marks/` holds the AI tools' marks (Claude, Codex, Antigravity, Cursor, Hermes, Pi, Pipeline) and the level chevrons (Novice,
Seasoned, Veteran): 16 x 16 and @2x 32 x 32, copied unchanged from orkLine (`marks/README.md`), and (0.15.0) each in **ink**:
`harness-claude-ink.png`, `rank-2-ink@2x.png`, ... the shape in `--ork-ink` and no other colour, 40 files in all. `<img class="ork-mark"
src="marks/harness-claude.png" srcset="marks/harness-claude@2x.png 2x" alt="">` draws one at 16 x 16, `.ork-mark.big` 32 x 32 from the
@2x file. A mark is an accent beside its name, never alone. The coloured ones keep the tool's own colours, so a person tells the tools
apart where a tool is chosen (a seat's popover); the ink ones go under a head, on a limit's chip and beside a rank.

## The elements
`elements/` holds a goal's five marks in orkBoard (spec 50): meadow (the tusks rune), ice (the key), dust (the comb), void (the eye) and lava (the wave), each a rune of `runes/` centred in a 7 x 7 grid of unit
squares (0.20.0, generated by `tools/build_runes.py`; `elements/README.md`). `<span class="ork-elem meadow" aria-hidden="true"></span>` draws one at
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
`signs/` holds the forty-two signs of orkBoard's window (spec 50 §1.6, spec 51 §1, spec 52 §1, spec 56, spec 59): check (done), cross (failed), work (at work), **moon**
(starts by itself later, a crescent alone: it was `night`, a crescent and a star, before 0.15.0; the one moon of the window), alert (a stop that asks), flag (a goal in main),
before (what a task waits for), after (what waits for it), and the media signs play and pause (a sound's or a clip's control), sound (a sound's tile), film (a clip's tile) and text
(a text's tile), **sword** and **shield** (0.15.0: a squad's *Does* and *Checks* columns, never a state's sign), **question** (0.15.5: a question the person answers, drawn beside `alert` and `target`), **bug-squashed** (0.26.0: a bug fixed, the beetle squashed flat, drawn where the bug stood; it has a 14 x 14 of its own at 28 px and is no goal type's), and a goal type's mark, each type its own: feature, bug, tidy,
restructure, screen, picture, logo, target, flask, horn, chart, page, abtest, landing, post, tagline, mechanic, level, balance, character, release, store, tune, compass, steps,
each a 7 x 7 grid of unit squares (`signs/README.md`, which says which the window as decided draws and that the goal types' signs stay for Orkline). `<span class="ork-sign check" aria-hidden="true"></span>` draws one at 14 x 14, `.ork-sign.big`
at 28 x 28, as a mask in `currentColor`: the colour of the text it stands in (ink, muted, success, danger or alert; a sign adds no colour
of its own). `vertical-align: -3px` sets it on the baseline of a 16 px line. No size between 14 and 28: whole pixels. A sign stands beside
its words (or a `title`) and is `aria-hidden`.

## The big signs and the tools (0.16.0)
At 28 px a goal type's sign is its own **14 x 14** drawing (`signs/big/`), two pixels a cell like every other pixel of the window, in
**two tones**: the silhouette in the colour of its text and its light over it, that colour lightened toward the ink
(`color-mix(in srgb, currentColor 45%, var(--ork-ink))`), never darker (the darker tone of `lava` falls below 3:1 on the card). The other
signs keep their 7 x 7 at 28 px. The objects are chosen to be told by their shape alone and to say the craft of the race whose party
does the work: a stag beetle, a hand mirror, a heart with a plaster, a firework rocket, a dial gauge, a die, a castle, a pair of
scales, a lyre, a drafting compass (a change shaped first), an elf's curled shoe (a flow walked). `tools/` holds each race's tool for a
pick of four, four variants each (the orks' drum with its spanner, the elves' bow with a brush for its arrow, the goblins' pick, the
gnomes' handbell, the knights' treasure map, the skeletons' hourglass), drawn the same way at 28 px by `.ork-tool` (`tools/README.md`).
Both come from `../drawings/drawings.json` (`python tools/build_big.py`).

## The potion and the mana (0.17.0)
`.ork-potion` is a pool drawn as a round bottle with a neck and a cork on a **14 x 18** grid (`potion/`, `potion/README.md`): 3 px a cell
(42 x 54), `.small` 2 px (28 x 36), whole pixels. `<span class="ork-potion is-warn" style="--ork-potion-left:.18" aria-hidden="true"></span>`
fills the body from the bottom by `--ork-potion-left` (0 to 1; eight rows, so an eighth a step, rounded up, the top always a whole row);
`--ork-potion-spend` (0 to 1) hatches that share at the liquid's top in a cell checker; `.is-warn` and `.is-danger` turn the liquid
`--ork-alert` and `--ork-danger`. The edge is `--ork-edge`, the glass `--ork-panel`, the cork `--ork-ink-muted`, a highlight on the liquid
lighter toward the ink. No words inside: the caller says the share.

**Four sizes** (0.23.0): `size-medium` (12 x 14), `size-small` (10 x 10) and `size-vial` (8 x 9) beside the large, each a bottle drawn on its own grid,
never the large scaled, at the same cell (3 px, `.small` 2 px): 36 x 42, 30 x 30 and 24 x 27. `<span class="ork-potion size-small is-danger" style="--ork-potion-left:.4" aria-hidden="true"></span>`.
The liquid steps by each bottle's own rows (medium eight, small and vial five), rounded up. Generated: `python tools/build_potion.py` from `potion/sizes.json`.

**`--ork-mana`** `#7b97b8` is the liquid while there is room to spend: a dim, desaturated blue (CIELAB L* 61.5, hue 265, chroma 20),
about as bright as `--ork-ink-muted` (L* 69; it is a little darker), so it does not pull the eye. It is a signal (*there is room*),
used by `.ork-potion` alone, never a text colour, a fill or an element's: 5.63:1 on the panel, 4.54 on the card, 3:1 or more on every ground,
CIE76 29.5 from `ice`, 11.9 from `void`, 67 or more from every signal.

## The portal (0.18.0)
`.ork-portal` is a round, magical pixel portal, the way a goal is sent into main (`portal/`, `portal/README.md`): a ring of stones round a dark panel,
a three-armed swirl turning to a dark eye, twelve sparks outside, on a **26 x 28** grid, 5 px a cell (130 x 140), `.small` 4 px (104 x 112).
`<span class="ork-portal" aria-hidden="true"></span>`; `.is-taking` (a card held over it: the swirl brighter, the ring a cell wider), `.is-sealed`
(still, dim, an X over it, no sparks) and `.is-new` (shimmers once). Only the swirl turns, a quarter turn at a time, 6 s a turn; nothing moves under
reduced motion. No words inside: the caller adds the label and the line.

**`--ork-portal`** `#b27bf6` is the swirl's and the sparks' light, a magical violet (CIELAB L* 61.9, hue 310, chroma 70); **`--ork-portal-hi`** `#d5a8ff`
(L* 75.7) is the brighter one while a card is held over it. A signal (*a goal can be played here*), used by `.ork-portal` and its ring alone, never a text colour, a
fill or an element's: `--ork-portal` is 5.71:1 on the panel and 4.60 on the card, `--ork-portal-hi` 8.80 and 7.09, 3:1 or more on every ground; CIE76
52.6 from the void element's `#8e88a8` (a goal's element is never mistaken for the portal; `-hi` 36.0), 37.8 from `ice`, 57.8 from `mana`, 84 or more
from every signal.

## The runes, the portal's ring, the sigil and a card's place (0.19.0, the elements and the places of a goal 0.20.0)
Twelve runes on a **5 x 7** grid, orkUI's own: they spell nothing, and none is a letter of a real alphabet (`runes/`, `runes/README.md`). `.ork-rune.<name>`
is 10 x 14, `.big` 20 x 28, in the text's colour. They are the table's one vocabulary of magic. **Five of them are the five elements** (tusks meadow, key ice,
comb dust, eye void, wave lava); the other seven are the **decoration** (hook, ladder, spiral, staff, hourglass, diamond, knot), the only runes the ring and the seal are
written in. **`.ork-portal-ring`** is the portal's place, 192 x 192: a dotted circle with seven decorative runes and, at its top, the place of a goal's element
(**`.ork-portal-ring__seal`**, 14 x 14: the caller puts the goal's `.ork-elem` in it, in its own colour; faint when `.is-sealed`), still and grey while asleep, its runes `--ork-portal` when `.is-open` (the portal in it), `--ork-portal-hi` when
`.is-taking`, grey again when `.is-sealed`; `.is-waking` lights them one after another, then opens the portal's eye. **`.ork-sigil`** is the + card's
seal of summoning, 136 x 136 (`.small` 72 x 72 at an 80 px card, with no runes and no seal): two circles, a band of seven runes and a star of two squares in the card's own
colour at a quarter's strength, so the + stays the one bright thing; at its top **`.ork-sigil__seal`** (14 x 14) holds the goal's element at full strength. On hover its
runes light once round the circle, from the top. **0.21.0** adds the glow (`.ork-elem.is-glowing`), the seal's up to four free runes (`.ork-sigil__free.at-90`, `-270`, `-180`, `-45`, shown on hover, focus or `.ork-plus.is-choosing`) and its rite
(`.ork-sigil.is-summoning` or `.ork-portal-ring.is-sending` with `.rite-<element>`, once), the ring's corners (`.ork-portal-ring__before` and `__after`, with `.is-asleep`, `.is-working`, `.ork-portal-ring__tick`, `.ork-portal-ring__alert`)
and its gate of at most three skeleton heads (`.ork-portal-ring__gate`, `.ork-portal-ring__guard` with `.is-working` or `.is-red`), and a portal guarded without its X (`.ork-portal.is-sealed.is-guarded`): `runes/README.md`. **`.ork-card-place`** is a pile's
place before its first card (the discard's), a card's outline in pixel dashes, never pressed. Nothing turns under reduced motion.

**The wait (0.27.0).** `.ork-sigil.is-waiting` draws the seal's ring of runes as a wait held at a share (`runes/README.md`): `<span class="ork-sigil is-waiting" style="--ork-sigil-share:.375" aria-hidden="true">`, the share 0 to 1
(the page sets it), the ring lit from the goal's rune at the top, clockwise, in the sigil's `currentColor`, **in eighths** (the share rounded down to an eighth: a place of the band, 45 degrees, a step; the first
place is the goal's own, as in the rite), the rest in the faint ink. Nothing moves by itself.

## The die (0.22.0, a cube since 0.24.0)
`.ork-die` is Play as a die (`die/`, `die/README.md`): since 0.24.0 a cube in CSS 3D, six faces seen from above and before under a perspective, its up face large, its front
face under it and its right face beside it, lit from above (a face darkens as it turns away). Its box is 24 x 30 cells at 3 px (**72 x 90**), `.big` 6 px (**144 x 180**), a face
18 x 18 cells (0.29.0: seen steeper, 34 degrees from above and turned 20, the box taller to hold it). It holds its cube and the cube's six faces: `<span class="ork-die face-5" aria-hidden="true"><span class="ork-die__cube"><i class="ork-die__face is-up"></i>`
… `<i class="ork-die__face is-down"></i></span></span>`. The view, the shades, the marks and every pose are generated from `die/die.json` by `tools/build_die.py`. The up face
shows `.face-1` to `.face-6` (pips in the muted ink), `.face-ok` (a tick in `--ork-success`), `.face-no` (a cross in `--ork-danger`) `.face-new` (a spark in `--ork-ink`: news, not a warning) or `.face-play` (0.27.0: the play arrow, a right-pointing triangle in the pips' colour, so the muted ink at rest and the ink and the glow while `.is-playing`). `.is-playing` turns the pips and the edges to the ink
and makes the up face glow (six steps, 2.4 s); `.is-rolling` tumbles the cube, a quarter turn each 120 ms in three poses, until the class is taken off (the page then sets the face it
stops on); `.is-wobbling` rocks it once on its edges, 300 ms in three poses; `.is-landing` rolls the up face in from the back and drops the cube, 300 ms in three poses. `.front-stop` and `.front-resume` (0.29.0) put the orks' mark on the front face, in `--_front` (the muted ink; `.is-orks-running` the danger's, `.is-orks-stopped` the ink), and the right face is then blank;
`.is-turning` turns the cube a quarter round its up axis, once. On the table
the page turns it with the lean token. Nothing moves under reduced motion.

## The room, the chair and the door (0.27.0)
**`--ork-room`** is the dark the leaders sit in (above). **`.ork-chair`** is a leader's seat at the table, drawn at a sign's weight in two greys (`chair/`, `chair/README.md`):
`<span class="ork-chair" aria-hidden="true"></span>` is an occupied chair's back alone, 22 x 12 cells at 2 px (44 x 24), the head standing over it; `.big` 26 x 14 (52 x 28), the open
leader's; `<span class="ork-chair is-empty" aria-hidden="true"></span>` the whole chair with nobody on it, 18 x 18 (36 x 36), `.small` 1 px a cell (18 x 18): a new party's place. The posts
and the rail are `--ork-table-rim-hi` and the panel `--ork-table-rim` (an empty chair `--ork-frame` and `--ork-raised`); `.is-lit` (hovered or focused too) takes it to `--ork-edge`
and `--ork-table-rim` and pulls it out from its foot (up 2 px, turned -4 degrees, on the base time and the spring), only inside `prefers-reduced-motion: no-preference`.
**`.ork-door`** is Stop all's mark (`door/`, `door/README.md`): `<span class="ork-door" aria-hidden="true"></span>`, 14 x 20 cells at 2 px (28 x 40), `.small` 1 px; the frame
in `--ork-table-rim-hi`, shut the leaf in `--ork-raised` with a knob in `--ork-ink-faint`; `.is-open` the opening in `--ork-ink-faint` at 0.7 and the leaf seen edge on. Shut and
open are states, nothing swings. Both are masks (generated: `tools/build_chair.py`, `tools/build_door.py`), no colour of their own, no words inside.

## The icons
`icons/icons.svg` is the sprite of the window's icons (`icons/README.md`). Fifteen are **orkUI's own** (0.15.0), drawn on the signs' 7 x 7 grid in solid pixels: `arrow-left`, `close` (×),
`more-horizontal` (…), `plus`, `search`, `mic`, `play`, `stop`, `banner` and `boarded` (0.22.0: a pole with a square banner with a + cut out of it, a pole crossed by two planks), `hammer` (0.26.0: Orkboard's *Fix it*; `.ork-icon.is-striking` raises it one cell and brings it down, 600 ms in two poses, only when motion is allowed) and the four chevrons; at 14, 21 or 28 px (two, three or four pixels a cell) they are whole pixels. The other 22 are
Pixelarticons (MIT), kept for Orkline. The gallery shows both.

## The parts of the one window
`.ork-gem` a price, a share of the limits or a mark before a move (inverted, 22 px; `.alert`, `.danger`, `.dim`; 24 px on a phone; **`.share`** a share of the limits, *4%*,
in the label's token on the frame's colour, and `.share.alert` / `.share.danger` when it warns) · `.ork-stat` a
measured number (outlined, 20 px) · `.ork-crystals` a row of `<i>` diamonds for what is left of a tool (`.on`, `.kept` hatched
for what is kept for tonight) · `.ork-frame` the double frame of a raised thing (`.alert`, `.danger`) · **`.ork-picked`** a card with a rune, picked (0.29.0, Orkboard's decisions §248): the card risen by `--ork-motion-rise` (a place, never a scale: the pixel grid), its edge in the ink with a
shadow under it, the rune inside it (`.ork-elem`) lit and still; a rune at work (`.is-glowing`) keeps its pulse; the rise stays under reduced motion · **`.ork-taken`** a map's part taken in picking
(a part has no rune of its own): pixel brackets at its four corners, 2 px thick and 8 px long, in the ink only (what `.ork-picked` drew before 0.29.0) · **`.ork-box`** the box being drawn: a dashed 2 px line in the ink. Tokens only, as every
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

## The turn and the give (0.27.0)
How a card shows its two sides (Orkboard's decisions §198.8 and §198.9, its spec 120 part G). **`.ork-turn`** is a card with two sides and the turn between them, face down by default, `.is-up` shows the face:
`<div class="ork-turn [is-up]"><div class="ork-turn__back ork-card-back">…</div><div class="ork-turn__face ork-card">…</div></div>`. The box keeps a card's 5 : 7 (the page gives it a width), the sides lie one over the other
(`position: absolute`, `backface-visibility: hidden`). The turn is a rotation about the vertical axis (the back to -180 degrees, the face from 180 to 0, under a perspective of 60 em), played **once** by the play token on the spring
curve when the class is put on or taken off; the side turned away is `visibility: hidden` at its end, so it leaves the tab order. A side is never `.ork-leans` (its transform is the turn's). Under reduced motion nothing
rotates: the two sides swap at once. **`.ork-gives`** is a head's one beat as it plays a card: on `.ork-race__head`, or any element, it rises by the rise token and settles, once (`animation-iteration-count: 1`), in the base token; the page puts the
class on when it happens and takes it off at the `animationend` named `ork-give` (put it on again after a reflow to play it again). Nothing plays under reduced motion.

## The back
`backs/back.svg` is the one back of a hand card face down (the deck, the cards under a stack's top, the discard's), 15 x 21 pixels (5 : 7) in the card's frame grey and the faint ink's grey on
the card's grey: **no colour** (`backs/README.md`). Since 0.15.1 it carries no mark: at its middle lies the **seal slot**, `.ork-card-back__seal`, which holds the element of the goal that waits
next (`<span class="ork-elem dust">`, drawn 28 px) and, beside it, the sign `moon` when that goal waits for the reset, the pair centred; with nothing in it the back is the pattern alone.
`<div class="ork-card-back"><span class="ork-card-back__seal"><span class="ork-elem dust"></span></span></div>` draws it; at 120 x 168 a pixel is 8 px, whole. A map card's back stays its details.
`.ork-card.ork-plus` is the new goal's card, face up, its face the `plus` icon centred at 28 px and nothing else; `.ork-deck` is a pile (the backs' edges, `--ork-deck-i`, the top back) with the
+ card lying off its top, to the left, a little up and turned by the lean token: a transform, still at rest and under reduced motion. The page gives the deck its width and room at its left.

Pointer targets are at least 24 x 24 px; on the phone a control is 40 px drawn and 44 px to hit (`min-height: var(--ork-tap)`).
