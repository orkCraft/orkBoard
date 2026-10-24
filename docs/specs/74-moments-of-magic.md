# Spec 74 — Moments of magic: the seal at Review, a collision that crumbles, the empty Board in the void, the moon

The owner, 24 October (decisions §89): *a goal reads like a spell; a little more of that, but not a theme over the
work.* Talking to a model is more and more like casting; Orkboard says so **in a few moments tied to an event, never as a
backdrop**: what a moment shows must say what happened (motion.js: *motion says what changed, never decorates*). The
office look stays as it is: dark, monochrome, colour a signal. **Builds:** a cheaper model, reviewed by Claude ·
**Review:** light · P3. **A and B at once**, they share no file; **C waits** for orkUI's marks (§7).

**What it is, and is not:** a seal on a merged result, a sent-back result that goes back to the field, a collision's
line that crumbles when it is answered, faint stars on the empty Board, one line of words there, and (C) the moon as a
goal's progress and tonight's sign. Not: a background on the Board, a shimmer, runes on a press, a circle at the gate, a
first-goal fanfare, any colour new to orkUI, magic on a control before it is pressed, or *spell* as a word of the
interface (it is not a concept: `TERMS` gains nothing).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Desktop** | §1–§5 on the desktop | `gui/static/js/arena/waits.js`, `goalwords.js` (`leaveOf`), `arena.css`, `project.js`, `arrows.js`, `arena.js` (the empty Board), `motion.js` (its notes); new `tests/test_arena_magic_desktop_browser.py` |
| **B. Phone** | §1, §2, §4, §5 on the phone | `gui/static/pwa/*` (the Review deck's leave, the empty Board), `pwa/app.css`, `pwa/sw.js` `CACHE` one up; new `tests/test_pwa_magic_browser.py` |
| **C. The moon** | §6 | after orkUI has `moons/` and the night sign (§7): its copy (`python -m orkboard.design.orkui`), a goal row's and a goal's screen's moon, both faces |

## 0. The rules of every moment
1. **Tied to an event**, played once, in steps (`steps(n)`), ≤ 0.42 s; never on the first read of a goal, never for what
   changed while the page was hidden, none under `prefers-reduced-motion` (the end state at once).
2. **orkUI's tokens only** (`tests/test_design_system.py`): ink, muted, faint, frame, the elements' colours, the signals.
   The void's own colour (`--ork-elem-void`) stays the void element's: it is no general colour of magic.
3. **A signal stays a signal**: a collision, a failure, money, Stop all keep their colour and their stillness while
   they hold. **A control is plain before it is pressed**; a moment plays after the press, never to invite one.
4. A result's card at Review is **dry while it waits**: its tests, its diff, its round. The moment is the person's
   answer, after it.
5. Already built (24 October, `main` `ba337b2`): an arrow (spec 50 §3.4) and a collision's line (spec 71 §6) are drawn
   from their start in four steps, 160 ms, when they come.

## 1. The seal: a merged result (A, B)
A result merged from Waits for your look (desktop) or the phone's Review leaves as now (`.is-leaving`, ≈ 0.3 s, the card
fades where it stands; *merged into dev*), but its flash is **the goal's element, stamped**: the element `.big` (28 x 28)
in its colour (a goal with none: `.dim`), from `scale(2)` at 0.4 opacity to `scale(1)` at full in **three steps over the
first third**, then held while the card fades. The same total time (`FADE_MS`): the column's settle does not wait
longer. A dropped result keeps its ✗; a result that leaves by the filter (`fade`) keeps no flash.

## 2. Sent back: the result goes back to the field (A, B)
A result sent back (its task is in the field again: queued, at work or waiting, not merged, not dropped) **leaves toward
the field**: it moves 24 px toward it (desktop: left, the field's side; phone: down) as it fades, three steps, the same
0.3 s, no flash. `resultLeaveOf` (desktop; `leaveOf` stays the field cards') returns `back` for it, the phone's leave the same; today such a result simply goes.

## 3. A collision that crumbles (A)
The project's level draws a collision's line in the alert colour while its stop is open (spec 71 §6). When the line goes
**while the page is seen** (its stop answered or withdrawn, not a goal shown away by the filter, not the first read),
`useLinks` keeps it **0.42 s more** as a leaving line (`is-leaving`) that **crumbles**: its stroke breaks into pixels and
goes, three steps (`stroke-dasharray` none → 2 2 → 2 6 → 2 14, opacity to 0). Then it is gone. A collision that stays
open never moves. Under reduced motion it goes at once. The phone draws no lines: nothing there.

## 4. The empty Board in the void (A, B)
The Board with no party (*No parties yet*: `arena.js`'s empty Operations, the phone's `needsGoal`) is the one place the
void shows: its free area gets **faint pixel stars** behind the words and buttons, taking no pointer. 2 x 2 px squares in
`--ork-frame` and `--ork-ink-faint`, sparse (about one per 6 000 px²), placed by a fixed pattern (the same on every
draw); **one in eight** is in `--ork-ink` and twinkles: opacity 0.25 ↔ 1, `steps(4)`, 4 s, each its own delay. Reduced
motion: the twinkling ones still, at 0.6. Not on Loading, an error, a preview gone, or any screen with content.

## 5. The words there (A, B)
Under *No parties yet* one line, muted, in the text face: **Make a party, then write it a goal in plain words, like a
spell. Its orks do the work; you look at it before it goes in.** The buttons keep their words (*New party*, *New goal*).
The line is the only place *spell* is said; it names no concept.

## 6. The moon: a goal's progress (C, after §7)
A goal's **moon** says how much of it is done: its tasks merged of its tasks, rounded to quarters: new (none), crescent,
half, gibbous, full (all merged; it waits at the gate or for Review). The lit part in `--ork-ink-muted`, the full moon's
in `--ork-ink`, the dark part in `--ork-frame`; no colour. **Where**: a goal's row (desktop 12 x 12 between its title
and its state's sign; the phone's row likewise at 14 x 14) and its screen's head (28 x 28 beside *k of n tasks*). A raw
goal and a pitch have none (no tasks yet); a release has none. The moon grows with a merge as the column's quiet reward
does: no motion of its own.
**Tonight's sign** (`night`, a clock today) becomes orkUI's moon-and-star (§7) everywhere it is drawn: a task held for
tonight, a goal or a pitch that starts tonight, Tonight's rows; its words stay (*tonight · after 22:00*).

## 7. In orkUI first (C)
`moons/`: five 7 x 7 marks, `new`, `crescent`, `half`, `gibbous`, `full`, each two paths (the lit cells, the dark
cells) or two files, drawn as `.ork-moon.<phase>` 14 x 14 and `.big` 28 x 28 as the elements are (masks, whole pixels,
no size between); the crescent the void element's crescent turned to the right. `signs/night.svg` redrawn as a crescent
and one star in the 7 x 7 grid. Their table in `tests/test_orkui.py`; orkUI's README's marks. Copied here unchanged;
then part C builds §6.

## 8. Tests
- **A** (`tests/test_arena_magic_desktop_browser.py`, a stub host as the decks' tests): a merged result's flash holds the
  goal's element `.big` (and a dropped one's ✗); a sent-back result leaves with `data-sign="back"` and no flash; a
  collision taken from `project.collisions` keeps its line with `is-leaving` for a moment, then none, and none at all
  under reduced motion; the empty Board has its stars layer (`aria-hidden`, no pointer) and the line of §5; a Board with
  a party has no stars.
- **B** (`tests/test_pwa_magic_browser.py`): the same for the phone's Review deck and its empty Board; `CACHE` one up.
- Both: no new colour (`tests/test_design_system.py`), the wording tests (`tests/test_gui_wording.py`).
