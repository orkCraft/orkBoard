# 114. The mana in two windows; a tab says whether its party follows the default

Decision §192 (1–5). The owner, 31 October, on `docs/mockups/mana-two/` (the target: read its script, the four bottles' rows and
the rules `sizeOf`, `toneOf`). **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:** full · P2.
After spec 113.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.23.0** | the potion in four sizes: `.ork-potion` gains `size-medium`, `size-small`, `size-vial` (the large is today's) | repository orkCraft/orkUI: `office/potion/` (three more sets of masks, or a source and a generator as the die's), `office/components.css`, `office/preview.html`, READMEs, `CHANGELOG.md`, `tests/test_orkui.py` |
| **B. The page** | the two windows in each potion; the colour by the lower share; two shares under it and the words; the tabs' marks framed when they follow the default | `js/hand/mana.js`, `js/hand/mana.css`, `js/arena/arenawords.js` (`limitLine`, the windows), `js/table/tabmarks.js`, `gui/ideas_map.py` (`marks_of`); their tests |

## 1. The words

Under a potion: the now share (*30%*) and *week 82%* (or *of the month 55%* for a tool with one window named so). The potion's words:
*<Tool>: <n>% of the <window> left, until <time>; <m>% of the week, until <day time>*, and *, the default* as today. A tab's marks'
words: *Does on the default (now <tool>)* · *Does on <tool>, set for this party* · *waits for <tool> until <time>*; the same for
*Checks*.

## 2. A: orkUI 0.23.0

- The four bottles of the mockup (`SIZES` in `docs/mockups/mana-two/index.html`): large 14 × 18 (today's, unchanged), medium 12 ×
  14, small 10 × 10, vial 8 × 9 (the rows' widths there; the cork the top row, the neck to the `neck` row, the liquid's rows below
  it). Each with its silhouette, body and shine masks as today's, generated from one source if that is simpler (as the die's). The
  liquid's rows by `--ork-potion-left` rounded up, as today; `--ork-potion-spend` hatches as today.
- `.ork-potion.size-medium|size-small|size-vial`: the drawing and its box at the same 3 px (`.small` 2 px) a cell; the box stands on
  its floor in a slot the page gives. Tests as the potion's; version 0.23.0; the gallery's potion section shows the four sizes.

## 3. B: the page

1. **The windows**: from each tool's limits (`l.rows`: each window's share left and its reset; read how `limitLine` and `windowOf`
   use them), the shortest window is the liquid (`--ork-potion-left`) and the longest the bottle's size (above 0.6 large, above 0.3
   medium, above 0.1 small, else vial). One window: large, its level. Unread: as today.
2. **The slot**: each potion in a box of the large bottle's size, the bottle centred on its floor, so the row never moves.
3. **The colour**: `levelOf(min(now, week))` (today's levels) for the liquid's `is-warn`/`is-danger` and the now share's colour.
4. **Under it**: the now share bold, the week's muted under it; the potion's words as §1.
5. **The tabs** (`gui/ideas_map.py` `marks_of`, `js/table/tabmarks.js`): the map's party node says, per side, whether it follows the
   default (`does_default`, `checks_default`: the party's or the roles' tool is "") and the tool now (the default now: `town.mana.now`,
   else the machine's main tool). A following side's mark is drawn in a 1 px frame in the ink with orkUI's notch (the default potion's
   frame), the tool it is on now; a set side's mark is bare, and dim with orkUI's `moon` sign beside it while that tool is dry (its
   potion at 0) — the words as §1. Hovering the default potion marks the framed marks as well as its own tool's.
6. Tests: the windows (a tool with two, one, none read), the sizes at the thresholds, the colour by the lower share (a full vial is
   danger), the shares under it, the words; the tabs' framed and bare marks, the mark changing when the default moves on (a scripted
   `town.mana.now`), the dim mark and moon on a dry set tool, the default potion's hover. The critical tests and every touched
   module's tests pass.

## As built

(filled in after the build)
