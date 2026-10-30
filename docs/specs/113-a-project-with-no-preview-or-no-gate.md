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

**Part A.** `gui/ideas_assets.py` `AssetsMixin.preview_kind()` reads `idea_shot.preview_of(state_dir, <the project's checkout>)` (the rule Play uses: checks.toml's `preview`, an `index.html`, a package script; files only, nothing is started) and answers its `how` (`command` or `static`) or `""`; a file it cannot read gives `""`.
`gui/ideas.py` `snapshot()` carries it as `preview` in the Board's cached read (so it is recomputed when that read is, on a change of the Board or after `SNAPSHOT_S`; no watcher of its own); the fallback read and `board_host.py`'s project-less snapshot say `""`. The phone has no Play, so `preview` is in `Orkboard.COMPUTER_ONLY`.
Tests: `tests/test_play.py` (the snapshot's `preview` for an `index.html`, none, a `dev` script, a package with no serving script, `preview = "mkdocs serve"` and a blank `preview`; the phone's snapshot has no `preview`); `tests/test_board_alone.py`'s key set gains `preview`.

**Part B.** `hand/playdie.js`: `asleepNow()` is `town.preview === ""` (an absent key, before the first snapshot or from a host that does not say, is awake). Asleep, the button carries `is-asleep`, its `title` is *Nothing to play yet* and its `aria-label` *Nothing to play yet: say how the project opens*, its word stays *Play*, the pointer-enter wobble is not started and
the glow is not shown; `hand/mana.css`: `.hand-die.is-asleep .ork-die { filter: grayscale(1); opacity: 0.4 }`, no lift on hover or focus, the word in the faint ink. Pressed, it opens the play view as before (and while that view is open its words are *Close the preview*, as always). `arena/play.js`: `useBuild` asks nothing when `asleepNow()` and answers
`{state: "failed", none: true}` itself, so the view is today's *Nothing here yet* and its how, with no `ideas.play`, no throw and no die on the pane. Tests (`tests/test_play_die_browser.py`, a `PreviewHost` whose snapshot says `preview`): the sleeping die at both widths (class, words, grey, no wobble, no lift, the press opening *Nothing here yet*, `ideas.play` never asked, no rolling die,
pressed again it closes), the die awake for `command`, `static` and no key, and the die waking when a later snapshot says there is a preview.

**Part C.** `table/data.js`: `noGate()` is `gateData.value?.same === true` (unknown before the first answer counts as a gate), and `roadParties()` answers none with no gate, so Release and Live are tabs with their lanes (`partiesNow`, `roadSlugs` and the hand's lanes follow) and `road.js` has no corner to draw. `table/discard.js` `DiscardEnd` leaves out `<Portal />` with no gate: the label *Discard*
and the pile or its place. Tests (`tests/test_road_browser.py`): no gate at both widths (no ring, portal or corner; the six tabs and six lanes; the label and the place), no gate with a goal done (the pile, no *Ready for main*), and the ring and the tabs following the gate when it appears and goes.

*Departures and choices.* (1) **Fixtures that said `same` for a gate with nothing to merge** were changed, not their assertions: `HandHost(bare=True)` (`tests/test_hand_desktop_browser.py`) and the two gate swaps in `tests/test_discard_table_browser.py` (the ring waking and sleeping) answered `same: True` with 0 commits to mean *nothing is ready for main*; since this spec `same` is *no gate*, so they
answer `same: False` with 0 commits (a gate with nothing waiting), which is what they meant; and `MapsHost` (`tests/test_maps_desktop_browser.py`), whose Release is reached through the ring's corner, now answers `ideas.gate` with a gate (it answered the table host's `same: True`). (2) `preview` is read from the project's checkout, not from dev's head as Play's worktree is; the two differ only for an `index.html` or script that dev holds and the checkout does not. (3) A sleeping die means `preview == ""` at the press: the view does not ask the host at all, so a preview added to checks.toml wakes the die
only at the next snapshot (at most `SNAPSHOT_S`, 10 s, later, or at the next change of the Board).
