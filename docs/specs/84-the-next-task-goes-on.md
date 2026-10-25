# Spec 84 — The next task goes on: a safe result lands by itself, what depends on nothing runs beside it

The owner, 25 October, testing: *why does the work go on only after a merge into dev?* (decisions §101). Because a task
`after` another starts from its merged work, every result waits at Review for the person's merge (`ideas.review` on by
default), and one task runs at a time (`ideas.max_parallel` 1). **Builds:** Claude · **Review:** full · P1, once the
owner says §101.4 (the default of `review`).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§3 | `core/idea_runner.py` (the land path; slots by size), `realm/idea_git.py` (risk paths of a diff), `realm/idea_risk.py`, `settings.py` (`IDEAS` defaults), `gui/ideas_review.py`; `tests/test_idea_runner.py`, new `tests/test_lands_by_itself.py` |
| **B. Faces** | §4 | `js/arena/waits.js`, `js/shell/settings.js`, `pwa/shell-review.js`, `pwa/sw.js`; the Review tests on both faces |

## 0. The words
*Waits for your look* (kept) and its reason: *tests did not run*, *findings left*, *touches <path>*, *holds pictures*,
*you asked to look at each result*. Settings: *A result that holds lands in dev by itself* (on / off). Landed: *in dev*.

## 1. A result lands when it holds (A)
In the runner's land path (where `review` is read today) a result lands in dev by itself when **all** hold: its tests
ran and are green; no findings left; its diff touches no risk path its goal's risk left out (`risk_paths` and the
goal's `risk`, spec 35 §4); it holds no media (§49.6). Else it waits for the look with the first reason of §0. The
`review` setting, on, keeps every result for the look (*you asked to look at each result*). Its default: §101.4.

## 2. What depends on nothing runs beside it (A)
The slots: `ideas.max_parallel` (the whole Board's), and a party's by its size: Lean 1, Standard 2, Full 3; a party with
no size, 1. One task per member at a time; never two tasks whose `touches` meet (§49.1); never past the window's reserve.

## 3. Not (A)
A task never starts from a result that waits for a look.

## 4. The faces (B)
*Waits for your look* says each result's reason; Settings has the switch with §0's words. A landed result leaves the
column and its card turns done on the field.

## 5. Tests
Each condition of §1 alone keeps a result for the look; all held lands it; `review` on keeps it; slots by size and the
`touches` rule; a waiting `after` task starts as soon as its predecessor lands. The critical tests and the files' tests.
