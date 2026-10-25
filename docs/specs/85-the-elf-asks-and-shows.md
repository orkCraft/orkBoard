# Spec 85 — Progress is seen: the elf asks about the look, what changed shows its picture

The owner, 25 October (decisions §102), testing: more to look at and check; the designer should ask more about style
and pictures; *I watch the cards move and do not feel the work progress.* **Builds:** Claude · **Review:** full · P2.

**What it is, and is not:** questions of the look at a visual goal's draft, a *Pick one* of a screen's looks, a picture
of what a task changed, and a goal's count. Not: a model judging the pictures; a question round for code; pictures sent
anywhere (they stay on the machine, §49.6's candidates' place).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§4 | `core/idea_draft.py` (the look's questions), `realm/goal_types.py` (`visual`), `core/idea_keeper.py` (a screen's pick first), `core/idea_picking.py`, new `core/idea_shot.py` (the picture: the project's preview, Playwright), `realm/board_map.py` (`done`, `of`, a task's `shot`); new `tests/test_look_questions.py`, `tests/test_idea_shot.py` |
| **B. Desktop** | §5 | `js/arena/stops.js` (a question with picked answers), `js/arena/stacks.js` (a card's picture, its count, done turned), `js/arena/waits.js`; new `tests/test_look_desktop_browser.py` |
| **C. Phone** | §5 | `pwa/shell-stops.js`, `pwa/shell-arena-field.js`, `pwa/shell-review.js`, `pwa/sw.js`; new `tests/test_pwa_look_browser.py` |

## 0. The words
*The elf asks about the look* (the stop's title is the member's name: *<Name> asks about the look*). Answers picked as
today's questions (spec 54). *Pick a look* (a screen's pick). *k of n done*. *What it made*.

## 1. Questions of the look (A)
A goal is **visual** when its type is one of screen, flow-feature, landing, level, character, icon, logo, or its party
has a design seat working on it. Its draft asks, beside the leader's questions (`MAX_QUESTIONS` stays 3 in all), up to
three of the look, asked by the party's design member (the elf) or, with none, the leader: the mood, the palette, the
references; each with its answer picked and two or three others; *Pictures you like* as an answer that takes a picture.

## 2. A screen's look picked first (A)
The plan of a screen's, a flow's or a landing's goal begins with one *Pick one* task: two or three looks of its main
screen (static pages the elf draws, the candidates of §64), before any builder's task; the builders' tasks come `after`
it and get the look picked with its note.

## 3. A picture of what changed (A)
A task whose diff touches what people see (the project's pages, components, styles, assets) gets a picture after its
tests: `idea_shot` opens the project's own preview (the command its kind uses, or `.orkcraft/checks.toml`'s `preview`
line) on the task's worktree in the pre-installed Chromium and draws the screen the task names; no model. Kept with the
task's candidates; none when no preview can be opened (said: *no picture: no preview*).

## 4. How far a goal is (A)
`ideas.map`'s goal carries `done` and `of` (its tasks merged and in all); a task merged keeps `made` (its first subject).

## 5. The faces (B, C)
The look's questions are stops in the hand with the elf's head. A card with a picture shows it as its face; *Waits for
your look* shows it large. A goal's stack and line say *k of n done*; a done card turns over once to *What it made*.

## 6. Tests
A visual goal's draft gets the look's questions, a code goal none, never more than three in all; a screen's plan begins
with its pick; a picture made from a stub preview, none without; `done`/`of`; the faces draw them. The critical tests and
each part's files' tests.


## As built (A)

- `realm/idea_look.py` (new): `visual(state_dir, root, slug)` is true for a goal whose type is `screen`, `flow-feature`, `landing`, `level`, `character`, `icon` or `logo`, and for a goal with **no** type whose party has a design seat (a member of craft design: the leader first, then the builders, then the checkers); a goal of any other type (a bug, a clean up, a balance pass, a sound, a tagline …) is not visual whoever is in its party. `asker(...)` is the party's design member, else its leader. The code's `look` is not a goal type: `goal_types.py` is unchanged.
- The draft (`core/idea_draft.py`): a visual goal's prompt carries `draft_lines` (the mood, the palette, the references; one choice of the references is exactly *Pictures you like*) and a `look` array beside `questions`. `write_draft` keeps the look's questions first, up to `LOOK_MAX` = 3, then the leader's, **three in all** (`MAX_QUESTIONS`); a goal that is not visual never reads `look`. The state keeps `asks_by` (the role that asks each question, "" the goal's leader) and `asks_look` (how many of the first are of the look; both added to `STATE_DEFAULT`, cleared by the answer). The Map's `asked[n]` carries `by` (so the elf's head) and `look`; the Needs you row's `asked[n]` carries `look`.
- `ideas.answer` takes `photos` (as `ideas.add`'s: base64, at most `MAX_PHOTOS` kept beside the goal, a refusal in the words of `idea_photos.decode`); the answer prompt reads them (`idea_photos.prompt_lines`).
- A screen's look (`idea_look.screens`: `screen`, `flow-feature`, `landing`): `make_plan(..., look=<title>)` puts a task first, written by code: id `k1`, tag `design`, *Pick a look*, `pick = {n: 3, kind: image, ask, target: design/looks/<goal>, look: true}`, and every other task `after` it; a plan whose model made a pick of its own is left as it is (one pick a goal at a time), at most 8 tasks. **The looks are pictures** (SVG or PNG of the screen at phone width), the one kind of Pick one that holds a screen; no `page` kind was added. `look: true` (kept by `idea_pick.clean_ask` and `pick.json`) makes `PickMixin._take` write the picked file at the target **with the file's own extension** (`design/looks/<goal>.svg`), the note told to the tasks after it as ever. The plan prompt says so (`idea_look.instruction`).
- The picture (`core/idea_shot.py` `ShotMixin.shoot`, called by `IdeaRunner._work` after the task's tests and diff; `realm/idea_shots.py` keeps it): `sees(touched)` is true for a page, a stylesheet, a component, a picture or a file under `components/ pages/ views/ screens/ templates/ static/ public/ assets/ styles/ ui/` (not under `tests/`, `docs/`, `design/`, `node_modules/`). `preview_of` reads, in this order, `<state>/checks.toml` `preview` (with `preview_port`, `preview_path`, `preview_size`), a static `index.html` at the worktree's root (served by Python on a free port), the package's `dev`, `preview` or `start` script (`npm run`, with `PORT` set). The command opens in the worktree's process group; the port is the one it prints or `PORT`; up to `OPEN_S` = 20 s, then `draw` runs the Chromium (`$ORKCRAFT_CHROMIUM`, `/opt/pw-browsers/chromium`, one on the PATH, else Playwright's own) headless with `--screenshot` at 1 280 × 800 (`--no-sandbox` only as root), `DRAW_S` = 25 s; the preview is killed with its group. **No Playwright at run time**: the browser is run as a program. The task keeps `shot` = `{id: "<task>-shot-r<round>", file, w, h, at}`, `{none: true}` (a visual change, no picture: *no picture: no preview*) or None (nothing people see changed, or `ideas.shots` is false); the PNG is a one-file pick beside the task's candidates (`picks/<task>-shot-r<n>/pick.json` with `shot: true`), so the signed media route serves it and `idea_pick.history/current` never list it. A task may name its screen (`"screen": "/settings"`, kept by `make_plan` when it is a path). The event `shot_taken` (`idea`, `task`, `ok`, `why`, `seconds`, `round`). `shoot` never raises.
- The Map (`realm/board_map.py`): a goal's (an idea's) `done` and `of` beside `progress`; a task's `made` (a merged task's first commit subject, cut at 120) and `shot` (`{id, file, w, h}` or `{none: "no picture: no preview"}`); `gui/ideas_map.py` and `ideas.review_list` give each picture its signed `url`.
- Words: `lexicon.py` `goal_look` and `task_picture`.
- Tests: `tests/test_look_questions.py` (34: visual by type and by seat, the asker, three in all with the look first, a code goal's `look` unread, `asks_by`/`asks_look`, the Map's `by`/`look`, the answer's photos, a screen's plan begins with its pick, a model's own pick kept, eight tasks, the prompt's lines, `clean_screen`), `tests/test_idea_shot.py` (24: what is seen, the preview's order, a bad checks file, a PNG of a static page at the asked size, a command that serves a page opened, drawn and killed, no preview and no browser said and time-boxed, the picture kept beside the candidates and served, in the runner a page change keeps its picture, a change of code none, no preview says so, `ideas.shots` off, a look picked written with its extension), `tests/test_board_map.py` (3 more), `tests/test_gui_ideas.py` (`review_list` shape).

## As built (B)

- `js/arena/arenawords.js`: a stop of a question of the look (`asked[0].look`, from the row or from the idea's Map node) has the title *<Name> asks about the look* (`lookTitle`, the asker's name, else the leader's) and the asker's head and tip, now read from the node when the row has none (`firstAsk`'s row carries no asker). `PICTURES` = *Pictures you like*.
- `js/arena/stops.js`: a quick answer that is *Pictures you like* opens the form with it filled in (a press cannot take a picture); the other choices answer in one click as before.
- `js/board/ask.js` `Questions` (the form of `AskDialog`): each question's `choices` are buttons that fill its box (`aria-pressed`); a question that offers *Pictures you like* has *Add a picture* under it (`[data-pictures]`, thumbnails with ×, up to 4); `onSend(answers, pictures)`; the goal's own questions take none. `js/board/pictures.js` (new): `shrink`, `usePictures`, `PictureAdd`, taken out of `ideadialog.js` (which imports them). `shell/askdialog.js` sends `photos: [{data}]`, a refusal toasts.
- `js/arena/stacks.js` `CardBody`: a card whose task has `shot.url` wears it as its face (`img.arena-task__shot`, the card's whole box, `.has-shot`, its words on a panel that lets it through); every card says *k of n done* (`doneWords` in `goalwords.js`, `.arena-task__count`, none for a goal with no plan); the card that leaves **merged** (`sign` check) turns over once, `span.arena-task__made[data-made]` *What it made* + the merged task's `made` read from the Map now (0.2 s in steps after the ✓'s frame; none without `made`, none for a drop; still under reduced motion). `js/arena/waits.js`: a result with `shot.url` shows it as a button the width of the column, in its own shape (`.arena-result__shot`, opens the result), `shot.none` says *no picture: no preview*, a result leaving merged says *What it made: …*.
- `js/arena/look.css` (new; `@import`ed by `column.css`, in `tests/test_design_system.py` `SHEETS`; tokens only). The goal rows of the left column are **not** changed: their text and title are pinned by the older tests, so *k of n done* is on the cards, not on the row.
- Tests: `tests/test_look_desktop_browser.py` (13, 1 440 × 900, the arena's stub host): the elf's stop (title, small elf head, its tip), a question that is not of the look keeps its title, a choice answers in one click, *Pictures you like* opens the form which takes a picture and sends it as `photos` with the answer, a form without that choice has no *Add a picture*, a card with a picture (face, 5:7, words over it, a press still opens the task), the count and a goal with no plan, Waits for your look (large, in its shape, none says so, none at all as before), the merged card turns once and a drop or an empty `made` does not, reduced motion.

## As built (C)

- `pwa/shell-stops.js`: a question of the look (`asked[0].look` from the row, else the idea's node) has the title *<Name> asks about the look* and the asker's small head (read from the node); a choice answers in one tap, *Pictures you like* opens the form (`needs.PICTURES`); a look stop's `more` is `moreOf(r)`.
- `pwa/shell-needs.js` `askForm`: each question's choices as buttons (`.q-choices`, 44 px) that fill its box; a question that offers *Pictures you like* has *Add a picture* (`[data-act=add-picture]`) and thumbnails with ×, the pictures shrunk by `shell-idea-field.js` `shrink` and sent as `photos`.
- `pwa/shell-arena-words.js` `taskItem`: `count` (`goalDone`: *k of n done*), `shot`, `made`; `pwa/shell-decks.js` `cardFace`: a token with a picture wears it (`img.tcard__shot`, `.has-shot`, 74 px, 5:7), every token says *k of n done* (`.tcard__count`), the ghost of a stack that merged turns over once to *What it made* (`.deck__made[data-made]`; `shell-arena-field.js` `observe` gives the ghost the merged task's `made`).
- `pwa/shell-review.js` `shotOf(r)` / `moreOf(r)`: a result's picture large, the width of its card, in its own shape (`figure.result-shot`), or *no picture: no preview*; under the look stop and on the result's own screen (`shell-preview.js`).
- `pwa/app.css` (the block *What the elf asks and shows (spec 85 C)*); `sw.js` `CACHE` `orkcraft-app-v92` -> `orkcraft-app-v93`, `tests/test_pwa.py` pins it. No new phone file, so `SHELL` is unchanged.
- Tests: `tests/test_pwa_look_browser.py` (10, 390 × 844): the elf's stop and its one-tap answer, a question not of the look, *Pictures you like* (the form, the choices, a picture, `photos` sent), a token's picture and count, none for a goal with no plan, a result's picture large under its stop and *no picture: no preview*, a result with no word about a picture, a merged stack turning once and a drop not, no sideways scroll, the service worker's version.
