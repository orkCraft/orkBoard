# Spec 87 — Quieter work, longer names: the hourglass, a card read whole, a to-do when it is needed, a party's seats its stages

The owner, 26 October (decisions §104.1, §104.2, §104.9, §104.10, §104.14), looking at the mockup *Orkboard — the map on
the table*: *the spinners take all the attention; a task's name is cut after two lines; a to-do I could not do at once
hung in the hand through the whole work; a party is its leader and a couple of members.* **Builds:** a cheaper model,
reviewed by Claude · **Review:** light · P1. **A0 first** (orkUI's repository); **A, B and C at once** once A0's copy is in
(they share no file).

**What it is, and is not:** orkUI's busy mark drawn as an hourglass; a desktop card of 128 x 180 whose name shows four
lines; a task's name written short; a to-do dealt into the hand only when the next task cannot start without it; the
projects' switcher saying a mark, not counts; a party's sizes as its leader's stages. Not: the map, its tabs or the hand's
lifted card (§104's phases); the phone's tokens (spec 67 stays); a party's members taken away (a party made before keeps
them).

| part | builds | files (and their tests) |
|---|---|---|
| **A0. orkUI** (repository orkCraft/orkUI) | §1 | `components.css` (`.ork-busy`), `office/preview.html`, `README.md` (*Busy*), the version (minor up), `CHANGELOG.md`; its tests. Then, in orkBoard, the copy: `python -m orkboard.design.orkui <orkUI>` (only `design-system/orkui/` changes) |
| **A. Host** | §3, §4, §5 | `core/idea_keeper.py` (the plan's prompt: a task's name; `make_plan`: the cut), `realm/board_map.py` (a to-do's stop only when it blocks; `todo_lines`), `realm/library.py` (`Stages`: one seat a stage), `realm/party_recipes.py` (`sized`, `tiers_for`); `tests/test_ideation.py`, `tests/test_board_map.py`, `tests/test_library.py`, `tests/test_party_size.py`, and the tests that pin a size's team |
| **B. Desktop** | §2, §4.3, §6 | `js/arena/arena.css` (the card), `js/arena/stacks.js` (the name's title), `js/arena/stops.js` (a to-do last), `js/shell/projects.js` (a mark, not counts), `js/board/idea.js` (the plan's *Before* lines); new `tests/test_quiet_desktop_browser.py`, and the desktop tests that read a card's size or the switcher's counts |
| **C. Phone** | §4.3, §6 | `pwa/shell-stops.js` (a to-do last), `pwa/shell-projects.js` (a mark), `pwa/app.css`, `pwa/sw.js` (`CACHE` one up) with `tests/test_pwa.py`'s pin; new `tests/test_pwa_quiet_browser.py` |

## 0. The words
*Before <task>: <to-do>* (a to-do's line in a goal's plan until it is dealt: *Before Spawn the boss: record the boss's
sounds*). The projects' switcher says no number. `TERMS` gains nothing.

## 1. The hourglass (A0)
`.ork-busy` keeps its name, its size (12 px) and its place (one per thing at work, never on a control), and is drawn as
**an hourglass**: a 6 x 6 cell grid at 2 px, the faint ink (`--ork-ink-faint`) only. Its sand falls **one grain a second**
(six frames, `steps`); after the last the glass **turns over in two steps** (90°, 180°) and starts again: about 7 s a
round. Under `prefers-reduced-motion` it stands still, half run. It draws no colour and is never brighter than the text
beside it: work in progress is the quiet state; a question, a failure and money keep their signals (spec 74 §0.3). The
moon stays a goal's progress (`moons/`). The README's *Busy* says so; the preview shows it beside a card.

## 2. A card read whole (B)
On the desktop a field card is **128 x 180 at most** (5:7; was 104 x 146: `.arena-stk` `max-width`), its name clamped at
**four lines** (was two: `.arena-task__name`), its top row, its goal's line and its foot as they are; a picture face
(spec 85) takes the card's whole box as now. Its whole name is its `title` (on hover). The project's level (spec 79) and
a spread (spec 50 §3.6) take the same size. The phone's tokens stay 74 px (spec 67).

## 3. A task's name, written short (A)
The plan's prompt asks each task's `title` in **60 characters at most, the verb first** (*Spawn enemies from the wave
director*). `make_plan` keeps a title of up to 80 characters as it is and cuts a longer one at the last word under 80,
with *…*. A task's brief is unchanged.

## 4. A to-do when it is needed (A, B, C)
1. `board_map` gives a to-do's stop (kind `todo`) **only when it blocks**: the goal is at work and a task the to-do is
   `for` is not merged and has every task it comes `after` merged (today's `blocks`). Before that the stop is not given.
2. Until then the to-do is **a line of the goal's plan**: `todo_lines(plan, tasks)` → *Before <task>: <to-do>*, in the
   plan's order; the goal's plan (`js/board/idea.js`) and its phone screen show them under the tasks. A to-do already
   done is not said.
3. **In the hand a to-do lies last**: after the questions, the forks, the plans and the failures; the hand's order is
   otherwise as spec 54 and decisions §67 say.

## 5. A party's seats are its stages (A)
`Stages` keeps its three words and gives **one seat a stage**: `seats` is `{"lead": 1, "build": 1, "check": 1}` for every
leader (`build_seats` and `check_seats` go). `party_recipes.sized`: **lean** the leader alone (as now); **standard** the
leader and its first builder; **full** the leader, its first builder and its first checker. `tiers_for` follows: lean
every seat Seasoned; standard the leader Veteran, the builder Seasoned; full the leader and the checker Veteran, the
builder Seasoned. A party made before keeps its team as saved; *Edit the party*'s size switch says who leaves, as
spec 81 does, and takes no one away by itself. The recipes' builders and checkers stay listed, most needed first: the
first of each is the one a size takes.

## 6. The projects' switcher says a mark (B, C)
Each open project in the switcher says **one mark**, never a count: the alert sign when something of it waits for the
person (`needs_you` > 0), else the hourglass (`.ork-busy`) when a task of it is at work (`working` > 0), else nothing.
The host's `projects` rows are unchanged.

## 7. Tests
A0: the hourglass's frames and its still state. A: a title over 80 cut at a word; the prompt's line; a to-do's stop only
when it blocks, and its *Before* line until then, none once done; the seats one a stage; each size's team and tiers; an
older party keeps its team. B: a card's size and four lines with a long name, its `title`; a to-do last in the hand; the
switcher's marks and no number. C: the same on the phone, and the service worker's version. The critical tests and each
part's files' tests.

## As built (B)

- `js/arena/arena.css`: a field card is 128 px wide at most (`.arena-stk` `max-width`, `.is-wide` `flex-basis`), so 5:7 gives 128 × 179 (the box is `aspect-ratio: 5 / 7`, not a fixed 180); `.arena-task__name` is clamped at **four** lines (was two); a spread's card is 128 × 180 (was 120 × 168). The project's level and the Orkmaster's field draw their cards in `.arena-stk` and take the size with it. The phone's tokens are untouched.
- `js/arena/stacks.js` `CardBody`: the name's `<span class="arena-task__name">` carries `title=<the task's whole title>` (the button's own tooltip, `cardTip`, is as before); a spread's cards use `CardBody`, so they carry it too.
- `js/arena/stops.js`: `todoLast(stops)` (exported) puts every `todo` stop after all the others, in the order they came; `Stops` applies it, so a to-do is the outermost card of the fan on the right (the hand's `urgencyOf`/`byUrgency` in `arenawords.js` are not changed). It is last of all, results (below 1 024 px) included.
- `js/shell/projects.js`: each open project in the switcher ends with `Mark` (`projectMark(p)`): `span[data-mark=alert]` holding orkUI's `.ork-sign.alert` in the alert colour (`ok-tone-fire`) when `needs_you` > 0, else `span[data-mark=busy]` holding `.ork-busy` when `working` > 0, else nothing; `role="img"` with *waits for you* / *at work*. The counts' words (`countsWords`) are gone; `review` is not said.
- `js/board/idea.js`: `todoLines(plan)` (exported) gives *Before <task>: <to-do>* for a to-do not done and a task not merged, in the plan's task order (then the to-dos'), shown as `ul.board-plan__before > li[data-before]` under the tasks of the plan (`Plan`). **The host's `todo_lines` was not on `main` when this was built**: `todoLines` uses `plan.todo_lines` when it is a list of strings, and otherwise reads the plan's `todos` (`for`, `title`, `done`) and `tasks` (`id`, `title`, `state`), so it works either way. The existing *To-dos before it starts* block (with `.is-target`) stays: a to-do stop opens the plan scrolled to it.
- Tests: `tests/test_quiet_desktop_browser.py` (5: a card 128 px wide, 5:7, four lines, the whole name its `title`; a spread's cards 128 × 180; a to-do last of the hand and outermost in the fan; the plan's *Before* lines and `todoLines` on a plan with a done to-do, a merged task and a given `todo_lines`; the switcher's marks, no number, the alert sign in its own colour). Updated: `test_arena_decks_desktop_browser.py` (128 × 180, the spread), `test_arena_desktop_browser.py`, `test_project_desktop_browser.py` (128 px), `test_map_desktop_browser.py` (four lines), and the hand's order in `test_one_hand_desktop_browser.py`, `test_shell_browser.py`, `test_party_proposals_desktop_browser.py` (a to-do last).

## As built (C)
The phone (§4.2, §4.3, §6), in `orkboard/gui/static/pwa/`:
- **A to-do lies last in the hand** (`shell-stops.js` `todoLast`): after `byUrgency` the stops of kind `todo` move behind every other stop (questions, forks, plans, failures, proposals and the results to look at), the rest in spec 54's order. `byUrgency` in `shell-arena-words.js` is not touched.
- **The switcher says one mark** (`shell-projects.js` `markOf`): an open project's row is its name and, at the right, `span.project-mark` with orkUI's alert sign when `needs_you` > 0, else `.ork-busy` when `working` > 0, else nothing; `review` says nothing. The mark is a `role="img"` with *needs you* / *at work* for a screen reader and as its `title`. *this one* stays on the shown project. `countWords` is gone.
- **The plan's *Before* lines** (`shell-preview.js` `beforeLines`, drawn by `planList`): a `ul.before-lines` right under the tasks, *Before <task>: <to-do>*, one line for each task a to-do is `for`, in the plan's order; a to-do with `done`, and a task merged or dropped, is left out. **Decided differently:** the host's part A (`todo_lines` in `realm/board_map.py`) was not on `main` when this was built, so the lines are computed from the plan's `todos` and `tasks` on the phone; when `todo_lines` arrives the phone may read it instead. The plan's list *To-dos before it starts* stays: a to-do's stop opens the plan scrolled to it.
- `app.css`: `.project-list .project-row` as a row, `.project-mark`, `.before-lines`, `.before-line` (orkUI's caption and muted ink); no colour of its own. The phone's 74 px tokens do not change. `.ork-busy` is orkUI's as it is today; part A0's hourglass reaches the phone with the orkUI copy.
- `sw.js`: `CACHE` is `orkcraft-app-v94` (`tests/test_pwa.py`, `tests/test_pwa_look_browser.py` pin it).
- Tests: new `tests/test_pwa_quiet_browser.py` (the marks and no number, a to-do last, the *Before* lines until merged or done, the version); `tests/test_pwa_shell_browser.py` (the hand's order), `tests/test_pwa_goal_types_browser.py` and `tests/test_pwa_projects37_browser.py` (the rows without counts) follow. `test_a_linked_spec_opens_read_only_rendered_with_no_edit_or_git_control` already failed on `main` before this change (not this part's).
