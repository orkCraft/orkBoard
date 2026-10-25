# Spec 84 — The next task goes on: a safe result lands by itself, what depends on nothing runs beside it

The owner, 25 October, testing: *why does the work go on only after a merge into dev?* (decisions §101). Because a task
`after` another starts from its merged work, every result waits at Review for the person's merge (`ideas.review` on by
default), and one task runs at a time (`ideas.max_parallel` 1). **Builds:** Claude · **Review:** full · P1.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§3 | `core/idea_runner.py` (the land path; slots by size), `realm/idea_git.py` (risk paths of a diff), `realm/idea_risk.py`, `settings.py` (`IDEAS` defaults, the one-time `review_v` migration; `tests/test_settings.py`), `gui/ideas_review.py`; `tests/test_idea_runner.py`, new `tests/test_lands_by_itself.py` |
| **B. Faces** | §4 | `js/arena/waits.js`, `js/shell/settings.js`, `pwa/shell-review.js`, `pwa/sw.js`; the Review tests on both faces |

## 0. The words
*Waits for your look* (kept) and its reason: *tests did not run*, *findings left*, *touches <path>*, *holds pictures*,
*you asked to look at each result*. Settings: *A result that holds lands in dev by itself* (on / off). Landed: *in dev*.

## 1. A result lands when it holds (A)
In the runner's land path (where `review` is read today) a result lands in dev by itself when **all** hold: its tests
ran and are green; no findings left; its diff touches no risk path its goal's risk left out (`risk_paths` and the
goal's `risk`, spec 35 §4); it holds no media (§49.6). Else it waits for the look with the first reason of §0. The
`review` setting, on, keeps every result for the look (*you asked to look at each result*). **Its default is off**
(§101.4, the owner's call): `settings.py` `IDEAS` and `core/idea_runner.py` `DEFAULTS`. The machine's settings file
holds every key of `ideas` once anything was saved (`settings.save` writes `to_dict()`), so a default alone moves no
Board that ran before: **once**, on load, a settings file without `ideas.review_v` (new key, `2`) has its `review` set
off and `review_v` written; a project's `board.json` that names `review` is migrated the same way. Said once in the
window and on the phone: *Results that hold now land in dev by themselves; Settings → Board to look at each one*. After
that, `review` is what the person sets.

## 2. What depends on nothing runs beside it (A)
The slots: `ideas.max_parallel` (the whole Board's), and a party's by its size: Lean 1, Standard 2, Full 3; a party with
no size, 1. One task per member at a time; never two tasks whose `touches` meet (§49.1); never past the window's reserve.

## 3. Not (A)
A task never starts from a result that waits for a look.

## 4. The faces (B)
*Waits for your look* says each result's reason; Settings has the switch with §0's words. A landed result leaves the
column and its card turns done on the field.

## 5. Tests
The default is off, and an old settings file with `review: true` and no `review_v` is moved off once and never again; each condition of §1 alone keeps a result for the look; all held lands it; `review` on keeps it; slots by size and the
`touches` rule; a waiting `after` task starts as soon as its predecessor lands. The critical tests and the files' tests.


## As built

- `core/idea_landing.py` (new, `LandingMixin` of `IdeaRunner`; the runner was past ~600 lines): `look_reason(slug, tests, left, files, red, gated)` is §1's one test, and its answer is the task's new field `look` ("" when the result lands). The first that holds: *no tests in this project* (`tests.none`, set by `_tests_of` from `gate_config.read(root).none`), *tests did not run*, *the tests are red*, *findings left*, *touches <path>* (each file of `git diff <base>...HEAD` through `idea_risk.assess` with the `risk_paths` setting; a trigger the goal's page `risk_triggers` did not list, except *wide*, names the file), *holds pictures* (an image, sound or video suffix in the diff, `.svg` too), *you asked to look at each result* (`ideas.review`). A check that changed no file is judged on its findings only (`gated` False). The result then waits at `review` with `look`; `merge` and `back` clear it.
- Red tests after the one fix now wait for the look whatever `review` says (they failed the goal with `review` off: with the default off that would have failed every red result). `tests/test_idea_runner.py` `test_a_gate_still_red_…` says so.
- Defaults: `settings.IDEAS` and `idea_runner.DEFAULTS` have `review` False. `settings.REVIEW_V` = 2 and `ideas.review_v`: `MachineSettings.from_dict` sets `review` off once for an `ideas` section without it (and `review_notice` True when it had asked, or the file was an old one with no `ideas`; a new machine says nothing); `settings.board_of` does the same for a project's `board.json` that names `review` without `review_v` and writes it back. `clean_ideas` never touches `review`, so a save or a switch is kept; `BOARD` gained `review_v`.
- The notice: `MachineSettings.review_notice` (saved, machine-wide). `ideas.board` carries `review` and `review_notice`; `ideas.board_set {review}` is the switch, `{review_notice: false}` clears the flag (it saves the machine's settings). Desktop `js/shell/store.js` `sayReview` toasts *Results that hold now land in dev by themselves; Settings → Board to look at each one* once per page and clears it; the phone's `pwa/board.js` flashes it the same.
- Slots (`LandingMixin.room`, called by `tick` for each ready task): the Board's `max_parallel` raised to the candidate party's cap where that is more (the default `max_parallel` is 1, so a size alone gives its party its slots); the party's cap by `size_of(slug)`: lean 1, standard 2, full 3, and a party with no size the Board's `max_parallel` (1 by default; a tester's `max_parallel: 2` still runs two); a party is the goal page's `track` (the goal itself without one). In a sized party a role its team picked (`task.role`) runs one task at a time; the role's own `max_parallel` is held as before. A task never starts beside a running one whose paths meet its own (`claims.meets`, narrowed): a task's paths are its `files` and the backticked paths of its brief; two tasks of one goal meet only by their own paths, two goals by their tasks' paths or else the goals' page `touches`. The window's reserve, the week and the sign-in are as they were; `after` still means merged, so a task never starts from a result that waits.
- Faces: `ideas.review_list` rows carry `look` (and `same`, `findings[].kind`, `tests.none`). Desktop `js/arena/waits.js` says *Waits: <reason>* under each result; `js/shell/settings.js` has the switch *A result that holds lands in dev by itself* (on while `review` is off) with a line of what holds. Phone: `pwa/shell-drawer.js` has the same switch, `pwa/shell-review.js` a *Waits* fact, `pwa/shell-stops.js` *waits: <reason>* in the result's line. `sw.js` `CACHE` v90 -> v91 (`tests/test_pwa.py`).
- Tests: `tests/test_lands_by_itself.py` (each condition alone, a goal's named risk landing, all holding landing, the default in a bare runner, a waiting `after` task never starting and going on after the merge, slots by size 1·2·3 and none, one task per member, files that meet, goals that touch the same and different files, cost once, a fresh session past 150 k); `tests/test_settings.py` (the move, once, the notice, `board.json`); `tests/test_call_log.py` (`cost_own`); `tests/test_board_35.py` (`board_set`); `tests/test_shell_browser.py` and `tests/test_pwa_board35_browser.py` (the switch, the notice once).
