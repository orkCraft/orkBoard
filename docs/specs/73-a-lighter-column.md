# Spec 73 — A lighter column: a goal is one line, the open party's heading is its leader, New and Flags are rows, New goal at the Orkmaster

The owner, 24 October (decisions §88), on the left column as built (specs 69, 72): *the list is overloaded.* The target
is mockup **G** of the Design artifact *Orkboard: one window* (the column *Proposed* and *New goal from the Orkmaster*) and
**H** for the phone's Goals sheet; their code is not copied (the page is Preact with orkUI's classes and tokens, the
phone the PWA's plain modules). **Builds:** Claude · **Review:** light · P1.

**What it is, and is not:** the desktop's column and the phone's Goals sheet drawn lighter, from what the host answers
today. No host change, command, setting, or word in the glossary. Not: the closed parties' headings and their at-work
line (spec 72 stays), the project's level (spec 70 stays), the phone's FAB (stays), the drawer's goal screen.

Two parts, **built at once, in parallel**; they share no file.

| part | builds | files (and their tests) |
|---|---|---|
| **B. Desktop** | §1–§4 | `js/arena/goals.js` (`Left`: the rows, the folds, no leader row, no *Goals n*, no pile), `js/arena/partylist.js` (the open heading: *<leader> leads*; the **+** in the project line), `js/arena/pitches.js` (Ideation's rows the same way), `js/shell/ideadialog.js` and `js/arena/projectparty.js` (New goal from the **+**: the party shown picked, its types first), `js/arena/arena.css`; new `tests/test_lighter_column_desktop_browser.py`, and the desktop tests that read what moved (`.arena-lead`, `.arena-new`, the goal row's pile or line, *Goals n*, *New (n)*, *Flags (n)*: grep them) |
| **C. Phone** | §5 | `pwa/shell-goals.js` and `pwa/shell-goals-words.js` (the Goals sheet's rows and folds), `pwa/app.css`, `pwa/sw.js` (`CACHE` one up) with `tests/test_pwa.py`'s pin and the phone tests that pin it; new `tests/test_pwa_lighter_goals_browser.py`, and the phone tests that read a goal row's pile or line |

## 0. The words
New strings: *<leader> leads* (*Taskmaster leads*), *New*, *Flags*, *k wait for main* (*1 waits for main*), *New goal:
in <party>, or another*. Every other word is today's. *deck*, *pile* stay out of what a person reads.

## 1. A goal is one line (B; C §5)
1. A goal's row (`goals.js` `GoalRow`; Ideation's `pitches.js` row): one line, 28 px high, 12 px in from the column's
   edge: **its element** (`Elem`, 12 px), **its type's sign** in its goal's colour (none for a goal with no type: the
   space kept), **its title** (one line, cut with an ellipsis), and at its right **one state's sign** as today's mark
   chooses it (at work, asks you, failed, a flag), 12 px; nothing for a goal that is only planned.
2. Its old second line (*0/6 in dev · implementation*, *plan ready*…) is its `title` with the goal's whole title:
   *<title> · <line>*. The pile, its edges and **›** go; a press on the row picks it into the filter as today, a second
   press on a picked row opens its screen (today's › did), hovering peeks as today. Keyboard: Enter picks, Enter again
   opens.
3. Groups as today: *At work*, *Planning* (the small headings), then the folds (§3).

## 2. The open party's heading is its leader (B)
1. The open party's heading (`partylist.js`): the leader's head (24 × 22), the party's name (the text face), under it
   *<leader> leads* (muted caption), at its right the work sign while at work and *k/n*; its title *<party> · <leader>
   leads · k of n goals done*.
2. Under it, directly, the groups of §1.3: the leader's member row (`.arena-lead`), *Process now* as a block and the
   *Goals n* heading go from the column. The leader's head in the field's stage (where it stands today) is unchanged.
3. Closed headings are unchanged (spec 69, spec 72's line).

## 3. New and Flags are rows (B; C §5)
1. After *Planning*: **New · n** (folded; a press unfolds its goals' rows below it, as *New (n)* did) with **Process
   now** at its right (today's button, its words without the count; disabled as today; *Judge now* in Ideation), and
   **Flags · n** (folded) with *k wait for main* at its right (muted; none when 0). Each is one 28 px row: orkUI's chevron
   (› folded, ⌄ open), the word in the pixel face's small caps as the groups' headings are, the count in the text face.
2. A thicker rule (2 px, the frame's colour) closes the open party's body before the next heading.

## 4. New goal at the Orkmaster (B)
1. In the project line, between the Orkmaster's head and the project switcher: a **+** button (28 × 28, notched, the
   action's colour on its sign), named *New goal* (title *New goal: in <party>, or another*).
2. A press opens New goal as spec 70 §4 does on the project's level, but **with the party shown picked** (`track`), its
   types first in the type picker (then the others of the project), *Its party* showing it picked and the others as chips
   (`ideas.party_for` asked when a type is picked, as there); on the project's level (no party shown) as spec 70 §4.
3. The New goal pile at the open party's foot goes; the project level's New goal pile (spec 70) stays.

## 5. The phone (C)
The Goals sheet (`shell-goals.js`): a goal's row is one line, **44 px** high: its element (14 px), its type's sign in its
goal's colour, its title (one line, ellipsis), its state's sign, **›** (44 px wide target, opens it, as today); its old
second line goes to its `aria-label` after the title. *New* and *Flags* as rows (44 px) with *Process now* and *k wait
for main* at their right, as §3. The FAB and the rest of the sheet unchanged. No sideways scroll at 390 px.

## 6. Tests
- **B** (1 440 × 900, stub host): a goal row is one line (28 px, element, type sign, title, state sign; no pile, no ›;
  the old line in its title); a press picks, a second opens its screen; the open heading says *Taskmaster leads* and no
  `.arena-lead`, no *Goals n*; *New · 8* with *Process now* that queues as today; *Flags · 4* with *1 waits for main*;
  the 2 px rule; the **+** in the project line opens New goal with the party shown picked and its types first, *Add the
  goal* sends its `track`; no New goal pile in the column; Ideation's rows and *Judge now*; a screenshot at 1 440 × 900.
- **C** (390 × 844): rows 44 px, one line, element and type sign, › opens; *New* and *Flags* rows; no sideways scroll;
  the service worker's version.
- Each part: the critical tests (CLAUDE.md "Alpha"), its files' tests, `tests/test_gui_wording.py`,
  `tests/test_design_system.py`; C also `tests/test_pwa.py`.

## As built (C)
The phone's Goals sheet (`pwa/shell-goals.js`, `shell-goals-words.js`, `app.css`, `sw.js` `orkcraft-app-v80`, `shell-arena.js` passes `process` to `makeGoals`):
- A goal's row (`.dk`) is one line of 44 px: its element (`.dk__elem`, 14 px), its type's sign (`.dk__type`, in its goal's colour; a 14 px `.dk__gap` keeps the space for a goal with no type), its title (`.dk__title`, one line, ellipsis), its state's sign (`.dk__mark`), ✓ when picked (an orkUI sign), then › (`.dk__open`, 44 px wide, opens it). The pile, `.dk__body` and `.dk__line` are gone; the old second line is the main button's `aria-label` and `title` after the title (*<title> · <line>*).
- *New* and *Flags* are folded rows (`.gfold`, `data-fold="new"|"flags"`, 44 px; orkUI's chevron, the word in the pixel face's small caps as the headings are, the count in the text face). *New · n* holds the goals the leader has not read (`raw`, from Planning, so Planning lists the others) with **Process now** at its right (`ideas.queue` `now`, `via` `party`, as the field's button; disabled without a next one). *Flags · n* has *k waits/wait for main* at its right (`mainWaitWords`); unfolded it holds the goals that wait for main (their lines, as before) and the flags; a flag just raised unfolds it. The *Waits for main · n* heading is gone. The folds are kept while the page is open. Ideation's pitches all stay under Planning (no New row on the phone for them).
- Tests: `tests/test_pwa_lighter_goals_browser.py` (3); the phone tests that read a row's pile or line, or the headings (`test_pwa_decks_browser.py`, `test_pwa_map39_browser.py`, `test_pwa_pick_browser.py`, `test_type_top_right_browser.py`, `test_pwa_goal_types_browser.py`), and the `CACHE` pin in every phone test, are updated. Set `LIGHTER_SHOT=<file.png>` to keep a screenshot of the sheet.
