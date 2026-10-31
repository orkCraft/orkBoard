# 118. The die's up face: the last start failed, and dev has something new

Decision §196. The owner, 31 October: *how else can the die be used while it just lies: show something useful on its up face*; of
the ideas weighed, *1 and 2*: **the cross stays while the last start failed**, and **a mark when dev has changed since the person
last played it**; the cube rolls onto the face that says it. **Builds:** Claude (the cheaper model builds, the spec's author reviews)
· **Review:** full · P2. After spec 112 (the die), spec 113 (the die asleep) and orkUI 0.24.0 (the die a cube).

**What it is, and is not:** the hand's die says, by its up face, what pressing Play would show: today's five when there is nothing
to say, **the cross** (`face-no`) when the last start of dev's head failed, **the spark** (`face-new`, orkUI 0.25.0) when dev's head
is a commit the person has not tried in Play yet. When what it says changes, the cube rolls onto the new face (orkUI's
`is-landing`). Not: a count (decisions §104.0, §145: no count of what waits; the spark says *something*, never *how much*); a word
in the hand (the word under the die stays *Play* / *Playing*); a toast or a notice; the phone (it has no Play, spec 112 §3.3: the
snapshot's new key is the computer's alone, as `preview` is).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI 0.25.0: the spark** | a new face of the die, `face-new`: a four-pointed spark in the ink | repository orkCraft/orkUI: `office/die/die.json` (the face `new`, the letter `n`, the colour `--_new`), `tools/build_die.py` (only if it needs to: the faces' list), `office/components.css` (`--_new: var(--ork-ink)` beside `--_tick` and `--_cross`), `office/preview.html`, `office/die/README.md`, `office/README.md`, `README.md`, `CHANGELOG.md`, the version (0.25.0), `tests/test_orkui.py` |
| **B. The host says it** | the snapshot carries `play_face`: `""`, `"failed"` or `"new"` | `gui/ideas_assets.py` (`Play` keeps the commit last tried; `AssetsMixin.play_face()`), `gui/ideas.py` (`snapshot()`), `gui/board_host.py` (`COMPUTER_ONLY`, the project-less snapshot); `tests/test_play.py`, `tests/test_board_alone.py` |
| **C. The die shows it** | the hand's die wears the face, rolls onto it when it changes, says it to a screen reader | `js/hand/playdie.js`; `tests/test_play_die_browser.py` |

## 1. The words

Two new `title` / `aria-label` words of the die's button (its word under it stays *Play*):

- **Play: it did not start last time** (`play_face` is `failed`);
- **Play: dev has changed since you last played** (`play_face` is `new`).

*Close the preview* (the view open) and *Nothing to play yet* (asleep) come first, as today.

## 2. A: the spark (orkUI 0.25.0)

- `die.json`: a ninth face, `new`, a 16 x 16 grid as the others, the letter `n` (legend `"n": "new"`), drawn at two cells a pixel and
  centred (as the tick and the cross), this spark of 7 x 7 pixels:

      ...#...
      ...#...
      ..###..
      #######
      ..###..
      ...#...
      ...#...

  that is the cells (1 + 2x, 1 + 2y) for each `#` at (x, y), each a 2 x 2 block (columns and rows 1 to 14 of the 16).
- `components.css`: `--_new: var(--ork-ink)` on `.ork-die` beside `--_tick` and `--_cross` (colour is a signal: the spark is news,
  not a warning, so it is the ink, the brightest grey); the generated block gains `.ork-die.face-new .ork-die__face.is-up::before`.
  `build_die.py`'s `FACES` gains `"new"`. Nothing else changes.
- The gallery: `face-new` beside `face-ok` and `face-no` (on the panel, on the table, and big).
- Tests: the face's cells are the spark above; the generated block lists it; the gallery and the READMEs name it; version 0.25.0.
- Orkboard copies it (`python -m orkboard.design.orkui <orkUI>`).

## 3. B: the host says it

- `Play` keeps **the commit last tried**: when a start of commit C ends, playing or failed (not a start stopped before it came to
  anything, not a project with no preview, `none`), C is written to `<state_dir>/play_tried.json` (`{"commit": C}`, atomically) and
  kept in memory. A missing or unreadable file is no commit.
- `AssetsMixin.play_face()` answers, with `head` dev's head (`commit_goal.head(root, self._ref())`, "" when there is none):
  - `"failed"` when Play's state is `failed`, not `none`, and its commit is `head`;
  - else `"new"` when there is a commit last tried, `head` is not "", and `head` differs from it, and Play is not starting or playing
    `head` right now;
  - else `""`.
  A project never tried in Play says `""` (there is nothing it would be new against). A failure never breaks the snapshot (`""`).
- `snapshot()` carries `play_face` **outside** the Board's cached read (Play's state changes without the Board's rev): computed on
  each snapshot, its git read of dev's head cached for two seconds. `board_host.py`: `"play_face"` joins `COMPUTER_ONLY` (the phone
  never gets it) and the project-less snapshot says `""`.
- Tests (`tests/test_play.py`, with a real git repository as its other tests use): never tried `""`; tried at head `""`; head moved
  `"new"`; failed at head `"failed"`; failed, then head moved, `"new"`; starting or playing head `""`; the tried commit survives a new
  `Play` (read from the file); the phone's snapshot has no `play_face`. `tests/test_board_alone.py`'s key set gains it.

## 4. C: the die shows it

- `playdie.js`: the face is `no` when `town.play_face === "failed"`, `new` when it is `"new"`, else `5`; asleep it is `5` as today
  (grey and still). While the play view is open and its build plays, the glow is as today (the face is then `""` → `5`).
- **It rolls onto the new face**: when the face changes after the die is first drawn (not on the first snapshot), and motion is
  allowed and the die is not thrown or asleep, the die wears orkUI's `is-landing` until its `animationend` named `ork-die-land`.
- The words of §1 in `title` and `aria-label`, after *Close the preview* and *Nothing to play yet*.
- Tests (`tests/test_play_die_browser.py`, a host whose snapshot says `play_face`): `failed` → `face-no` and the words; `new` →
  `face-new` and the words; `""` → `face-5`; a later snapshot changing it puts `is-landing` on and takes it off; under reduced
  motion no `is-landing`; asleep wins over both; the phone (narrow upright) has no die as today.

## 5. Order and tests

A and B together (two repositories, no shared file), then C after Orkboard copies orkUI 0.25.0. The critical tests and every touched
module's tests pass; the die's browser tests pass.
