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
