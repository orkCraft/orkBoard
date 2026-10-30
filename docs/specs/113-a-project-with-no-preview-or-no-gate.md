# 113. A project with no preview or no gate

Decision §191 (1–4). The owner, 31 October. **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:**
full · P2. After spec 112 (the Play die) and spec 111 (the road at the portal).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The preview known** | the snapshot says whether the project has a preview | the host's snapshot (find where `play`/`town` state is served: grep `snapshot` in `gui/board_host.py`, `gui/ideas_assets.py`), `core/idea_shot.preview_of`; `tests/test_board_alone.py` (the snapshot's keys), the assets' tests |
| **B. The die asleep** | with no preview, the die is grey and still, *Nothing to play yet*, pressed opens today's *Nothing here yet* without a throw | `js/hand/playdie.js`, its CSS; `js/arena/play.js`; the play view's browser tests |
| **C. No gate, no ring** | with no gate, the table's end is the discard alone: no ring, no portal, no Release corner; Live stays a tab | `js/table/discard.js`, `js/table/portal.js`, `js/table/road.js`, `js/table/data.js` (`roadParties`), their CSS; the discard's, the portal's and the road's browser tests |

## 1. The words

*Nothing to play yet* (the asleep die's `title` and `aria-label`, with *: say how the project opens* after it for a screen reader).
No other new words: *Nothing here yet* and its how are today's (`arena/play.js` `NOTHING`, `NOTHING_HOW`).

## 2. A: the preview known

- The snapshot the page reads carries `preview: "command" | "static" | ""` for the project (from `idea_shot.preview_of` on the
  project's checkout, the same rule Play uses; a cheap read: no process is started). Recomputed when the snapshot is rebuilt; no
  watcher of its own.
- Tests: a project with `preview = "…"` in its checks file, one with `index.html`, one with a `dev` script, one with none.

## 3. B: the die asleep

- `playdie.js`: with `preview === ""` the die carries `is-asleep` (CSS in the hand's sheet: `filter: grayscale(1); opacity: 0.4`,
  no wobble on hover, no `is-playing`), its word *Play*, its `title` *Nothing to play yet*; pressed, it opens the play view as today
  (which says *Nothing here yet* and how), and **no throw** is played (`arena/play.js` starts no die when the view opens on a project
  with no preview).
- Tests: the asleep die (class, words, no wobble), the press opening *Nothing here yet* with no rolling die on the pane; a project
  with a preview unchanged.

## 4. C: no gate, no ring

- The page knows: `gateData.value.same` (the gate's own answer, `idea_gate.same`). With no gate:
  - `DiscardEnd` draws the label *Discard* and the place or the pile only: no *Main*, no ring, no portal, no corners;
  - `roadParties()` returns none, so Release and Live stay tabs (as at the narrow width) and keep their lanes;
  - nothing else changes (the discard's view has no *Ready for main*, as today with no gate).
- Tests: a host whose gate says `same` at the wide width: no `.ork-portal-ring`, the Release and Live tabs in the row, the discard's
  place; with a gate, as spec 111.

## 5. Order and tests

A, then B and C (one branch). The critical tests and every touched module's tests pass; new browser tests run five times in a loop.

## As built

(filled in after the build)
