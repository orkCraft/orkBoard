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
   - `banner`: rows `#.#####`, `#.##.##`, `#.#...#`, `#.##.##`, `#.#####`, `#......`, `#......` (a pole at the left, a square
     cloth with a + cut out of it). Read the mockup's `BANNER` (`docs/mockups/buttons/index.html`); keep its cloth 5 × 5, its +
     three cells each way; if the mockup and these rows differ, the mockup wins.
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
   build plays. At the narrow width the die is `small`? No such size: keep 3 px and let the hand's row wrap as the potions do. The phone
   (PWA) has no Play: no die there.
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

(filled in after the build)
