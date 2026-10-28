# orkUI / office / signs

The forty-one signs: **every symbol a face draws is orkUI's** (orkBoard's spec 50 §1.6, spec 51 §1 and spec 52 §1 and spec 56 §6 and spec 59 §1, decisions §63.10, §69 and §72). A sign stands beside the
words it explains (a state, a stop, an order), in the colour of that text; it is never the only thing that says it, so the words
(or a `title`) stay and the sign is `aria-hidden`.

    check   a done thing (✓)                         cross   a failure (✗)
    work    at work (↻)                              moon    starts by itself later (a crescent)
    alert   a stop that asks (!)                     flag    a goal in main (⚑)
    before  what a task waits for (←)                after   what waits for it (→)
    play    a sound's or a clip's control (▶)        pause   a sound's or a clip's control (‖)
    sound   a sound's tile (a loudspeaker)           film    a clip's tile (a film strip)
    text    a text's tile (lines of text)

A goal type's mark (spec 52 §1 and spec 56, decisions §65.4 and §69: a type is told by its sign, never by a colour; every type has its own sign, a thing of the realm,
never a being; the thing drawn in brackets):

    feature      a new thing people can do (a wand)
    bug          a thing that goes wrong (a beetle)
    tidy         the same behaviour in simpler code (a broom)
    restructure  modules split or moved (an anvil)
    screen       a screen (a mirror)
    picture      a picture or an icon (a gem)
    logo         a mark for the product (a seal)
    target       a pain of someone's (a heart with a plaster)
    flask        an experiment (a beaker)
    horn         a launch (a firework rocket)
    chart        a number (a dial gauge)
    page         a report (a scroll)
    abtest       two versions, one decided by a number (a fork)
    landing      a page that says the product (a signpost)
    post         a post for one channel (a letter)
    tagline      one line that says the product (a quill)
    mechanic     a rule of the game (a die)
    level        a place the player comes to (a castle)
    balance      numbers weighed against each other (a pair of scales)
    character    who someone is, by rank (a crown)
    release      a version packed and sent (a chest)
    store        where the product is sold (a stall)
    tune         a sound for the game (a lyre)
    compass      a change across modules, shaped before it is written (a drafting compass)
    steps        a flow and its screens, walked, then built (an elf's curled shoe)

A squad's two columns (orkBoard's decisions §151.9) have a mark each, never a state's sign:

    sword   a squad's *Does* column (a sword)         shield  a squad's *Checks* column (a shield)

A stop's mark (0.15.5, Orkboard's decisions §167.3), like `alert`, not a goal type's:

    question   a question the person answers (a question mark)

**The window as decided draws** (0.15.0): the states of the closed set, `check`, `cross`, `work`, `moon`, `alert`, `flag`;
`before` and `after`; `play` and `pause`; a map card's kinds, `screen`, `picture`, `sound`, `film`, `text`, `page`, `logo`;
`sword` and `shield`; and, since 0.15.5, `question`. The goal types' signs stay in this folder for Orkline, which still draws them; orkBoard's copy
leaves them out.

The twenty-five pictures are also in `../emblems/` (the library), with fourteen more that no face draws (seven of them the goal types' pictures before 0.16.0).

`night`: the old name of `moon`, kept for Orkline (`night.svg` is `moon.svg`, `.ork-sign.night` draws the same mask); the window as decided writes `moon`.

*moon* is a crescent alone, the one moon of the window (it was *night*, a crescent and a star, before 0.15.0): the *void* element (`../elements/`) is a ring now and no crescent, and the icon `moon` is gone from the sprite. The moons (`../moons/`) draw a goal's progress, never a state. The close (×), the plus (+)
and the chevrons (›, ⌄) are not here: they are orkUI's icons (`../icons/icons.svg`), drawn on this same grid.

Each is a **7 x 7** grid of unit squares, one `path` (`M{x} {y}h1v1h-1z` for every pixel, row by row from the top), `viewBox="0 0
7 7"`, `fill="#000"`, `shape-rendering="crispEdges"`: no colour of its own, no metadata. They are **drawn as masks**:
`.ork-sign` in `components.css` fills a 14 x 14 box (`.big` 28 x 28, two or four pixels a cell, whole pixels) with
`background: currentColor` through `mask-image: url(signs/<name>.svg)`, so a sign takes the colour of the text it stands in and the
file's black is only the shape. `vertical-align: -3px` sets the 14 px box on the baseline of a 16 px line.

    <span class="ork-sign check" aria-hidden="true"></span> done           14 x 14, in the text's colour
    <span class="ork-sign alert big" aria-hidden="true"></span>            28 x 28
    <span style="color: var(--ork-danger)"><span class="ork-sign cross" aria-hidden="true"></span> failed</span>

A sign takes the signal colour of its text (success, danger, alert) or the muted ink, never a colour of its own: colour is a
signal, and the sign does not add one. A shape is changed here, in the table of `tests/test_orkui.py` and in orkBoard's spec 50
§1.6 (spec 51 §1 for the media signs, spec 52 §1 and spec 56 §6 for the goal types') together, never in a face.

## The goal types' signs at 28 px: `big/`, 14 x 14 in two tones (0.16.0)

At 14 px a sign is its 7 x 7, two pixels a cell. At 28 px the 7 x 7 would be four pixels a cell, coarser than every other pixel of the
window (the heads are two pixels a cell), so **each goal type's sign is drawn again at 14 x 14 for 28 px**, the same thing in more detail:
`big/<name>.svg`, in the same format as a sign (`viewBox="0 0 14 14"`, one path of unit squares, `fill="#000"`). Its source is
`../../drawings/drawings.json` (`python tools/build_big.py`); the 7 x 7 and the 14 x 14 of one name are the same thing, so a face that
draws a type's sign at both sizes shows one picture.

A big sign is drawn in **two tones**: its silhouette (`big/<name>.svg`, every pixel) in the colour of the text it stands in, as every
sign, and its light (`big/<name>-light.svg`, at most half the silhouette's pixels, always inside it) over it, in that same colour
lightened toward the ink (`color-mix(in srgb, currentColor 45%, var(--ork-ink))`, on `.ork-sign.big::after`). The light is lighter, never
darker: on the card the darker tone of `lava`, `void` or `dust` falls below 3:1. A sign still adds no colour of its own: in the element's
colour its light is the element's, lit; in the ink the two tones are one. The other signs (the states, the media, a squad's columns,
`question`) keep their 7 x 7 at 28 px.

    <span class="ork-sign bug big" aria-hidden="true"></span>      28 x 28: the stag beetle, 14 x 14 in two tones
