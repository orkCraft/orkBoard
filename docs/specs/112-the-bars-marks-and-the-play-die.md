# 112. The bar's marks and the Play die

Decisions §190 (1–5). The owner, 31 October, on `docs/mockups/buttons/` (sections *The family* and *Play as a die*) and
`docs/mockups/play-die/` (the target: read its CSS and script). **Builds:** Claude (the cheaper model builds, the spec's author
reviews) · **Review:** full · P2. After spec 111.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.22.0** | the icons `banner` and `boarded`; the die `.ork-die` (its body, its six faces, its tick and cross, its states) | repository orkCraft/orkUI: `office/icons/src/`, `tools/build_icons.py`, new `office/die/die.json` and `tools/build_die.py`, `office/components.css`, `office/preview.html`, READMEs, `CHANGELOG.md`, `tests/test_orkui.py` |
| **B. The page** | + Party and Stop all wear the icons; Play leaves the pane's head for a die in the hand; the throw, the roll, the landing on the outcome, then today's logo and frame | `js/table/tabs.js`, `js/table/pane.js`, new `js/hand/playdie.js`, `js/hand/hand.css` or `mana.css`, `js/arena/play.js`, `js/arena/play.css`; their tests |

## 1. The words

No new word but *Playing* (the die's word while the preview is open) and the landing's line, *It started* / *It did not start*,
said under the die for a moment. The die's button: `aria-label` *Play: the project's preview of dev* (*Close the preview* while
open); the tick and the cross are announced by the start screen's own words, as today.

## 2. Part A: orkUI 0.22.0

1. **Icons** on the 7 × 7 grid (orkUI's own, solid pixels, `src/<name>.svg`, built into `icons.svg`):
   - `banner`: rows `######.`, `###.##.`, `##...#.`, `###.##.`, `######.`, `#......`, `#......` (a pole at the left, a square
     cloth 5 × 5 against it with a + cut out of it), as the mockup's `BANNER` (`docs/mockups/buttons/index.html`).
   - `boarded`: the mockup's `PLANKS` (a pole at the left, two planks two cells thick crossing over it).
   Their README lines; the icons' tests (orkUI's own set) count them.
2. **The die**, `<span class="ork-die face-5" aria-hidden="true"></span>`: drawn as the portal is, in `box-shadow` pixels
   generated from a source (`office/die/die.json`, `tools/build_die.py --check`), because it has many colours and its face changes.
   - The body: a 23 × 20 grid: the top face 20 × 17 with its two upper corners and two lower corners cut, the front face three cells
     under it slanting right, the right face three cells beside it slanting down, the silhouette and the top face's lower and right
     ridges in the edge grey; fills `--ork-card-frame` (top), `--ork-card` (front), `--ork-panel` (right), `--ork-edge` (edges).
     The mockup's `dieSvg` (in `docs/mockups/play-die/index.html`) is the drawing: port it exactly (W 20, H 17, D 3).
   - The faces: `face-1` … `face-6` (pips 2 × 2 cells at columns 4, 9, 14 and rows 3, 7, 12, as the mockup), `face-ok` (the tick
     at two cells a pixel, `--ork-success`), `face-no` (the cross, `--ork-danger`); pips `--ork-ink-muted`.
   - Sizes: 3 px a cell (69 × 60) by default, `.big` 6 px (138 × 120); whole pixels.
   - States: `.is-playing` (pips and edges in the ink, the pips glowing: `opacity` 0.55 ↔ 1 in six steps over 2.4 s);
     `.is-rolling` (the face cycles 1 → 6, 120 ms a face, in steps, until the class is taken off); `.is-wobbling` (one wobble:
     −8°, 6°, 0° in three steps over 300 ms, rising by the rise token; the page adds it on pointer enter and takes it off at
     `animationend`). Under reduced motion none of them moves (the glow stands at full).
   - The die is not turned by itself: the page turns it (the lean token).
   - The motion tests' list of what may idle (`infinite`) gains the glow and the roll by name, as 0.21.0's list does.
3. The gallery: the two icons in the Icons section; a section *Die* with the six faces, the tick and the cross, both sizes, playing,
   rolling (a button to roll and stop), wobbling. READMEs, `## 0.22.0`, version 0.22.0 (pyproject, uv.lock, tokens.json and
   `build_tokens.py`), `docs/preview-office.png` again. Every generator's `--check` and `pytest` pass.

## 3. Part B: the page

1. **The bar** (`table/tabs.js`): + Party's icon is `banner` (its hover unfurls it once: a `scaleX` of the cloth is not possible on a
   sprite icon, so a one-time three-step `clip-path` reveal from the pole, or none; say which in As built); Stop all wears `boarded`
   before its word, in its danger colour.
2. **Play leaves the pane's head** (`table/pane.js`: the `table-play` button goes; its `play` function moves to the die).
3. **The die in the hand** (new `hand/playdie.js`, drawn by `hand/hand.js` at the hand's right end, before the potions): a `<button>`
   holding `.ork-die face-5` turned by the lean token (`rotate: calc(var(--ork-motion-lean) * -1)`) and its word under it, as a potion's
   share is; `is-wobbling` on pointer enter (once); pressed: if the play view is open (`over.value?.kind === "play"`) it closes it,
   else it opens it (`openOver("play", …)` as `pane.js` did). `.is-playing` and the word *Playing* while the play view is open and its
   build plays. At the narrow width it keeps its 3 px and stands beside the potions as they stand. The phone (PWA) has no Play: no
   die there.
4. **The start screen** (`arena/play.js`, `arena/play.css`): when the play view opens on a build that is not running (`starting`):
   - a `.ork-die big is-rolling` flies from the hand's die (its rectangle) to the middle of the black pane (a three- to seven-step
     transform, about 420 ms) and rolls, the hand's die hidden meanwhile; the stage line (`StageLine`) stands under it as today; the
     logo is not shown while it starts;
   - when the build plays: the rolling stops on `face-ok`, turned by the lean token the other way, a three-step landing (about 300 ms),
     the line *It started* for a moment; then today's intro (`Intro`: the logo up in six steps, two blinks, the name) for about a
     second, then today's fade and the frame rising; the hand's die is back, `is-playing`;
   - when it failed: the die stops on `face-no`, tips over (three steps) and today's failure view takes its place; the hand's die is back;
   - when the view opens on a build already playing: no throw, no intro (as today), the hand's die wobbles twice;
   - under reduced motion: today's start screen exactly (the logo while it starts), no die on the pane.
5. Tests (the play view's browser tests: find them with grep `play-intro`, `ideas.play`): the bar's icons; no Play in the pane's head;
   the die in the hand opens and closes the view; the throw and the roll while starting (the rolling die present, the logo absent);
   the landing on `face-ok` then the intro then the frame; the landing on `face-no` then the failure; warm opens at once; reduced motion
   is today's screen. The critical tests and every touched module's tests pass.

## As built

**Part B.** orkUI 0.22.0 copied (`python -m orkboard.design.orkui`, commit 8264abb). *The bar:* `tabs.js` draws `banner` for + Party and `boarded` before *Stop all* (both added to `orkui.js`'s 7-grid set, drawn at 14 px as the mockup has them, not
the 21 px of the old +). The banner's hover is the **one-time three-step `clip-path` reveal from the pole** (`table.css`: 3, 5, then 7 columns of the icon in 360 ms, per hover or focus; none under reduced motion), not "none". *Play leaves the pane's head:*
the `table-play` button and its CSS are gone. *The die:* new `hand/playdie.js` (`PlayDie`, `pressPlay`, and the seam signals `thrown`, `playing`, `warmed` with `dieRect()`), drawn by `hand.js` between the bug and the potions, also in the hand with no goal
(`hand-mana-only`); its CSS is in `hand/mana.css` (turned by `rotate: calc(var(--ork-motion-lean) * -1)`, lifted by the rise token while hovered or focused, hidden with `visibility` while its copy is out, the narrow width keeps 3 px and stands with the potions). The
wobble is a state with a key (the span is made again for each wobble so orkUI's animation replays), once on hover, twice when the view opens on a playing build, none under reduced motion. The upright phone has no die. *The start screen* (`arena/play.js`, `play.css`): the throw
is a phase machine `ph` (`fly` 420 ms → `roll` until the answer → `ok` / `no` landed 600 / 700 ms → `ok-leave` fade 300 ms, `no-leave` tip 360 ms → `logo` → `out`); the flight is a Web Animations `steps(7)` from the hand die's rectangle, the roll and landing
are CSS in whole steps; the iframe is the same element all through (keyed, never reloaded) under the black overlay, which covers the bar too. Tests: new `tests/test_play_die_browser.py` (the bar's icons at both widths, the banner's hover and reduced motion, the die's place and press,
no Play in the head, the throw, the tick, the logo, the frame, the cross and failure, warm with two wobbles, the stopped roll, retrying, reduced motion, the phone); the older browser tests that pressed *Play* in the pane's head press the die.

*Departures and choices.* (1) **A build that is not running is started by the die's press itself**: the view asks with `peek`, and when the host says `stopped` it starts at once (`ideas.play`), where before it showed *Open the build* and waited for a second press. The
spec's "pressed when the preview is not running, it is thrown" needs this; *Open the build* stays for a build stopped or failed. (2) The intro after the tick lasts 1.8 s with a logo (the name comes in after the logo's two blinks, at 1.4 s) and 1 s with the name alone, where the spec says
about a second. (3) The black overlay covers the pane's bar as well as the stage (the mockup's frame sits under the black), so *Plays dev at …* shows when the frame rises. (4) A project with no preview (*Nothing here yet*) is thrown and lands on the cross like a failure, then says so. (5) The
start screen's old `came` / `gone` bookkeeping went: the fade after the intro is the throw's last phase; under reduced motion nothing fades, as before.
(6) **The die takes room.** At 1280 px the hand's last track grows by the die (about 40 px), so the first lane's fan (the Orkmaster's stacks, 16 px of fan before) collapses: its stacks lie one over the other until the window is wider; at 390 px
the row has no room left for five stacks, a die and two potions, so the room kept for the last card gives way first (`.hand-row::after` shrinks, the slots shrink first by their `flex-shrink`) and the die's right edge lies 6 px over the first potion's empty border. Tests that pressed a stack by the left edge of its card
(`test_decision_fork_desktop_browser.py` `press`, one step of `test_hand_desktop_browser.py`) press it by the keyboard now (`focus`, Enter), and one of `test_hand_mana_browser.py` moves the pointer off the cards first, as its neighbours already did; `test_discard_table_browser.py`
lets `.hand-end` hold the die. If the fan matters more than the die's 69 px, the way out is a smaller die at 1280 or the bug button moved out of the hand's end: the owner's to say.
