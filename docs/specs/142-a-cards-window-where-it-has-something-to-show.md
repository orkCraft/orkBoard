# 142. A card's window where it has something to show

Decisions §249. **Builds:** the cheaper model: A, B, C on the page (each in its area); D after C (host and page) ·
**Review:** the critical tests and each part's own · P1. The look: `docs/mockups/card-windows/` (sections 1–4).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The column's card** | no window: rune and whole name (3 lines), then the foot; the height its content's | `table/piles.js`, `table/column.css`; `tests/test_column_browser.py` |
| **B. The hand's card** | no window: the kind's sign top left in its signal's colour, who asks a 16 px head top right, the title in three whole lines, the label row | `hand/stopcard.js`, `hand/hand.css` (`--hc-window`, the grid), `hand/stacks.js` (the fan's heights), `hand/choose.js`; `tests/test_hand_desktop_browser.py`, `test_hand_context_narrow_browser.py` |
| **C. A lane's window: waiting, at work, failed** | waiting: the seat's head faint and *an elf takes it next*; at work: the steps (§207); failed: the alert and its reason | `table/card.js`, `table/steps.js`, `table/work.css`; `tests/test_task_steps_browser.py`, `test_table_desktop_browser.py` |
| **D. A lane's window: what it made, by craft** | the host serves a task's `made`; the page draws Tech's bars, Design's screen, Art's asset, Release's checks, Product's hypothesis, Run's and LiveOps' event | the host's snapshot of a task (`gui/ideas_map.py` or where `tasks[]` are built), a new `realm/task_made.py`; `table/card.js`, a new `table/made.js` + `made.css`; `tests/test_task_made.py`, a browser test |

## A. The column's card

`piles.js` (the face-up card, line ~129: *its rune and short name at its top, its type in the window, and its foot*):
the window is not drawn; the header holds the rune and the **whole name** (`n.title`, three lines at most with
`line-clamp: 3`; the short name only where the title is missing); the foot as today (with spec 140 A2's change if it is
in). The card's height is its content's (no fixed 157 px); its width 112 px. The front of To review keeps its wait bar.
Face-down cards unchanged. Test: no `.col-win` (or the window's class) in a face-up card; a long title is whole in three
lines; the card is shorter than 157 px.

## B. The hand's card

`stopcard.js` (lines ~74–80, ~125: `hand-card__window` with `hand-card__fig`, the `Mark` big and the asker's `Head`):
1. **No window**: the grid is `corner / title / label` (`hand.css` `.hand-card`'s `grid-template-rows`, no
   `--hc-window`).
2. **The corner**: the kind's `Mark` at its small size top left, coloured by its kind as the card's frame is (the
   question's and the hearing's alert, a failure's danger, the rest the muted ink); **who asks** the asker's `Head`
   at 16 px top right (`hand-card__asker`, kept when there is a head).
3. **The title** three whole lines (`line-clamp: 3`), never cut mid-line; the label row as today (the party, the gem).
4. The card's height about two thirds of today's; the stacks' fan (`stacks.js`, `hand.css`) and the hand's row height
   follow; the + card the same height. The lifted card (`hand-lifted`) is unchanged. The narrow width (`upright`, under
   760 px) keeps its own sizes, the same anatomy.
5. Tests: no `.hand-card__window`; the corner has the sign and the head; a three-line title is not clipped
   (`scrollHeight <= clientHeight` on the title); the hand is shorter than before.

## C. A lane's window: waiting, at work, failed

`table/card.js` (`Window`, line ~52: one big type sign): by the task's state, from the snapshot as it is:
1. **Waiting** (not started): the head of the seat that will take it (the task's `seat`/role → the party's race and
   tier, `orkui.js` `Head`), at 32 px, `opacity` 0.45, and under it *<a race> takes it next* (*an elf*, *a Grunt*: the
   race's word from `TERMS`).
2. **At work**: the steps (§207, `steps.js`): the pips, the step now in two lines, the worker's head with the busy mark.
   Where a task has no `steps`, its *doing* line, else today's sign.
3. **Failed**: orkUI's `alert` sign in the danger colour and the failure's reason in one or two lines (the task's error
   line as the lifted card says it).
4. **Otherwise** (done, checked, no data): today's type sign, until part D.
5. The window's height fixed (about 92 px at the lane card's 156 px width), so a lane's cards line up. Tests: each of
   the three states draws its content.

## D. A lane's window: what it made, by craft

1. **The host**: a task done or checked carries **`made`** in the snapshot, read by code (`realm/task_made.py`, pure
   where it can; cached per task's head commit):
   - **Tech** (a party of the Tech craft): `{kind: "diff", files: [{path, added, removed}]}` from `git diff --numstat` of
     the task's commits (its worktree's range), the three with the most lines;
   - **Design**: `{kind: "screen", before: url|"", after: url}` from the task's screen shot (Play's shot or the sketch's
     canvas file, where the Board keeps them for the goal), served by the server's file route;
   - **Art**: `{kind: "asset", url, w, h, name}` for the first image file the task's commits added or changed;
   - **Release**: `{kind: "checks", items: [{name, state}]}` from the gate's checks of §188.3 for its goal;
   - **Product**: `{kind: "hypothesis", text, state}` from the project's hypotheses (§235) the goal tests;
   - **Run, LiveOps**: `{kind: "event", title, date}` the dated event the goal waits for (§215), when any.
   Nothing is called on a model; a missing source leaves `made` absent.
2. **The page** (`table/made.js`): Tech's files as names (code face, cut with an ellipsis) and six pixel bars each,
   added in orkUI's success, taken in its danger; Design's before → after thumbnails, the before faint; Art's image at
   its pixels (`image-rendering: pixelated`, scaled by a whole number) on a checker; Release's ticks; Product's quoted
   hypothesis and its state chip; the event's date and title. The mockup's section 3 is the look.
3. Tests: `task_made` for a numstat, an added image and none; the browser draws each kind.
