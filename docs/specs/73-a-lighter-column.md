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

## As built (B)

Part B, on the desktop only; no host, phone or Python file, no new word (*New · n*, *Flags · n*, *<leader> leads*, *k wait for main* are §0's).
- **`js/arena/goals.js`** `Left` is the open party's body and no more: `.arena-pbody` > `.arena-goals` (still the region named *Goals*, or *Pitches*) > `.arena-deck` with the groups *At work* and *Planning* (the small headings), `New · n` and `Flags · n`. The leader's row (`.arena-lead`), *Process now* as a block, the *Goals n* heading (`.arena-left__head`) and the New goal pile are gone from it. `GoalRow` is one line, 28 px, 12 px in from the column's edge: `Elem` (12 px), the type's sign in its goal's colour (`.arena-goal__type`, an empty 12 px box for a goal with no type), the title (`.arena-goal__title`, one line, ellipsis), the state's sign (`.arena-goal__mark`, 12 px; empty for a goal only planned). Its old second line is its `title`: *<title> · <line>. <what a press does>*; its `aria-label` is unchanged in shape. A press picks the goal into the filter; a second press on a picked row opens its screen (`showIdea`/`showPlan` as › did); a raw goal (under *New*) has no pick and opens on a press. Enter does the same: a row is a `<button>`. The pile (edges, back) and › (`.arena-goal__open`) are gone; the hover peek is as before.
- **`js/arena/foldrow.js`** (new): `FoldRow`, the 28 px row shared by *New · n*, *Flags · n* and Ideation's *Sent · n*, *Passed · n*: orkUI's `Chev` (right while folded, down while open), the word in the pixel face's small caps (`.arena-frow__word`, the groups' label type), the count in the text face, the toggle a button named *New · 8* (`aria-label`, `aria-expanded`); what the row offers stands at its right. *New* has the same *Process now* button as before (`.arena-power`, 22 px high, words without the count, title and `disabled` as today); the row stays with no new goal, the button disabled. *Flags* has *k waits for main* / *k wait for main* (`.arena-frow__aside`, caption, muted); none at 0. A fold's rows unfold below it.
- **`js/arena/pitches.js`**: Ideation's rows are the same line (element, the space of a type, title, mark; no › any more, a press opens the pitch), its *New*, *Sent*, *Passed* the same rows, *Judge now* in *New*'s row.
- **`js/arena/partylist.js`**: the open heading has `.arena-phead__who`: the party's name, under it `.arena-phead__leads` (*Taskmaster leads*; Ideation's *Investor leads*; the name is `g.leader.name`), the work sign and *k/n* as before; its title is *<party> · <leader> leads · k of n goals done*. A closed heading is unchanged. The project line holds `NewGoalPlus` between the Orkmaster's head and the switcher; the line is a flex row whether or not the host has the Orkmaster.
- **`js/arena/newgoal.js`** (new): the **+** (`.arena-plus`, 28 × 28, `ork-btn`, orkUI's `plus`, the action's colour; `aria-label` *New goal*, title *New goal: in <party>, or another*, on the project's level or in Operations *New goal: your own, or pick its type*). A press deals *Your own goal* and the types of the party shown first, then the other parties' (`projectwords.js` `typesFirst`) with `TypesSpread`, whose cards open New goal with `{goal: "@project", party, type}`; with no type it opens New goal at once. `ideadialog.js` (`IdeaDialog` takes `party`) and `projectparty.js` (`usePartyFor(on, typeId, first)`) pick `first` until another chip is, instead of the Orkmaster's suggestion (which *Its party* still says). A host with no parties: *New party* first (`then: "idea"`), as the no-party note's button does.
- **A host from before spec 70** (`ideas.map` has no `project`): there is no Orkmaster to suggest a party, so the **+** deals only the party shown's own types and New goal is that party's own, with its *Party* select, exactly as the pile's was.
- **CSS**: the column's rules moved to the new `js/arena/column.css` (linked after `arena.css` in `shell/shell.js`; `arena.css` is 561 lines, `column.css` 56); `tests/test_design_system.py` reads it too. The open party's section ends in a 2 px rule in the frame's colour.
- Deviations and additions. (1) **Show all** stays: a quiet button above the groups, only while a goal is picked, because a second press no longer takes a pick out (Esc still does). (2) **The leader's solo** (a press on its row showed only its work) has no entry any more, as the leader's row is gone (§2.2); the field's `Solo` for a leader is still drawn when `solo` is set. The tests that looked at it set `solo` through the page's module (`solo_lead` in `tests/test_arena_desktop_browser.py`). `members.js`'s `lead` branch has no caller now. (3) A goal's row has no ›: a goal not yet read, under *New*, opens on its first press.
- Tests: new `tests/test_lighter_column_desktop_browser.py` (18); the tests that read what moved were changed to say it in today's way (rows' title for the second line, *New · n*, *Flags · n*, the + for the pile, the heading for the leader's row, two presses for ›): `test_arena_decks`, `test_arena`, `test_goal_types`, `test_ideation`, `test_lens`, `test_map`, `test_party_list`, `test_plan_change`, `test_project`, `test_route`, `test_shell`, `test_stop_link`, `test_type_top_right` (desktop).
