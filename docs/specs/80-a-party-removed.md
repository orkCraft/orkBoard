# Spec 80 — A party removed

The owner, 25 October (decisions §97): a party can be added and edited, never removed. So **a party is removed from its
screen, on both faces, after one question; its goals move to General or go with it; never while one is at work; General
stays**. **Builds:** Claude · **Review:** light · P2.

**What it is, and is not:** one command, one action on each face. Not: an archive or a way back (§97.5); removing a
person's own saved party (spec 43 §6, done); stopping a party's goals; a new word in the glossary (*party* is one).

Three parts. **A first**; then **B and C at once, in parallel** (they share no file).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1, §2 | `realm/ideas.py` (`drop_track`), `gui/ideas.py` (`ideas.track_drop` in the command table); `tests/test_gui_ideas.py` (or a new `tests/test_party_removed.py`) |
| **B. Desktop** | §3, §4 | the party's own screen or menu where it is edited (the left column's party, `js/arena/*` or `js/shell/*`), its words file; new `tests/test_party_removed_desktop_browser.py` |
| **C. Phone** | §3, §5 | the phone's party sheet (`pwa/shell-party.js` or `pwa/shell-where.js`), `pwa/app.css` if needed, `pwa/sw.js` (`CACHE` one up) with the tests that pin it; new `tests/test_pwa_party_removed_browser.py` |

## 0. The words
*Remove party* (the action). The question's title: *Remove <party>?* Its choices: *Move its k goals to General and
remove* (the default, first), *Remove the party and its k goals* (the danger colour), *Cancel*. An empty party: one
line *It has no goals*, and *Remove* / *Cancel*. Refusals: *k goals at work: stop them first* (*1 goal at work: stop it
first*), *General stays: it is where goals without a party go*, *That party is gone*. A toast after: *<party> removed*,
with *k goals moved to General* or *k goals removed* when there were any.

## 1. The rule (A)
`ideas.drop_track(root, slug, goals="move"|"drop", state_dir=None) -> {"moved": n, "dropped": n}`, under `LOCK`:
1. Unknown slug → `ValueError("That party is gone")`; `GENERAL` → `ValueError("General stays: it is where goals without a party go")`.
2. A goal of the party **at work** (the same test that makes its Map node's `state` `working`, realm/board_map.py, or
   the keeper or runner busy on it) → refused with *k goals at work: stop them first*, nothing changed. The host passes
   what is busy (the `Ideas` object knows its runners); the realm function takes `busy: set[str]`.
3. `move`: each goal's `track` becomes `GENERAL` (as `ideas.move` does), its order after General's last. `drop`: each
   goal as `ideas.drop(root, slug, state_dir)` (spend kept).
4. The party's page (`<root>/tracks/<slug>.md`) is deleted, the index rewritten (`_reindex`). What still names the
   party (an event, a route, a release's list, an own party's `uses`, a party proposal) is left as it is and must read
   without it: a party not found reads as its slug, never an error. `party_proposals` of that party are dropped.

## 2. The command (A)
`ideas.track_drop {slug, goals?: "move"|"drop"}` (default `move`) → `{"ok": true, "moved": n, "dropped": n, "title": t}`;
a refusal is an `IdeasError` with §0's words. `self.changed("")` after, so both faces redraw. An event in the project's
log (`event_log`), `party_removed`, with `slug`, `title`, `moved`, `dropped` and the caller's `face`.

## 3. The question (B, C)
From the party's screen or its menu, never from a bare key: *Remove party*. The question is orkUI's dialog (desktop) or
sheet (phone), with §0's choices; the party's goal count from what the face already has. A refusal from the host is said
in the question (not a second dialog) and the question stays. On success: the toast, the party is gone from the column,
the face shows General (or the first party) if the removed one was open. General has no *Remove party*.

## 4. The desktop (B)
The action sits with the party's other edits, in the danger colour at the end; the dialog's default button is the
move; Esc cancels. 1 440 × 900.

## 5. The phone (C)
The action at the foot of the party's sheet; the question a sheet with 44 px choices; no sideways scroll at 390 px.

## 6. Tests
- **A**: move (goals in General after, page gone, index without it); drop (goals gone, `spend-gone.jsonl` has their
  lines); refused for General, unknown, a goal at work (nothing changed); the event; `ideas.map` and `ideas.board` still
  answer when a route or an own party's use names the removed party.
- **B / C** (stub host): the action is absent for General; the question's choices and counts; *move* sends
  `ideas.track_drop` with `goals: "move"` and the toast; a refusal is said in the question; the removed open party falls
  back to General; C: no sideways scroll, the service worker's version.
- Each part: the critical tests (CLAUDE.md "Alpha"), its files' tests, `tests/test_gui_wording.py`,
  `tests/test_design_system.py`, `tests/test_architecture.py`; C also `tests/test_pwa.py`.

## As built (A)

- `realm/ideas.py` `drop_track(root, slug, goals="move", state_dir=None, busy=frozenset()) -> {"moved": n, "dropped": n}`, under `LOCK`. Refusals are `ValueError`s with §0's words: *General stays: it is where goals without a party go* (checked first), *That party is gone* (unknown or not a slug), *1 goal at work: stop it first* / *k goals at work: stop them first*, *Goals move or drop* (any other `goals`). A goal is at work when its slug is in `busy` or its state is `working` (the Map's test); a refusal changes nothing. `move`: each goal goes through `ideas.move` to General, in the party's order, after General's last. `drop`: each through `ideas.drop(root, slug, state_dir)`, its spend kept in `spend-gone.jsonl`. Then the page is deleted, the party's `party-proposal.json` and `party-declined.jsonl` (state `goals/<slug>/`) with it, and the index rewritten. Nothing else that names the party is touched.
- `gui/ideas_track.py` (a new mixin, `gui/ideas.py` was at its limit): `ideas.track_drop {slug, goals?}` -> `{"ok": true, "moved", "dropped", "title"}`. `track_busy` gives the party's goals the keeper (`keeper.busy`) or a runner (`_runs`) has in hand. A `ValueError` is an `IdeasError` with the same words; `goals` other than `move`/`drop` is *Goals move to General or are removed*. After it: the event `party_removed` (`slug`, `title`, `moved`, `dropped`, `face`: `desktop` or `phone`, and `device`; `realm/event_log.py` `PARTY_REMOVED`) and `self.changed("")`.
- Readers needed no change: the Map, the Board, `ideas.recap`, `ideas.week`, `ideas.parties` and `ideas.page` answer when a route (`route.json` `from`) or an own party's use names the removed party; `ideas.party` of it says *That party is gone*.
- Tests: `tests/test_party_removed.py` (move, drop with spend, empty, refusals, at work by state, keeper and runner, the event, the proposal, readers); `ideas.track_drop` is in `tests/test_gui_ideas.py` `BOARD_COMMANDS`.

## As built (B)

- `js/shell/partyremove.js` (new): `RemovePartyDialog`, the dialog kind `remove-party` (`shell/dialogs.js`), orkUI's `Modal`. Title *Remove <party>?*; the party's goal count is the Board's `tracks[].count`. With goals: *Move its k goals to General and remove* (`primary`, first, focused, so Enter takes it), *Remove the party and its k goals* (`danger`), *Cancel*; with none: *It has no goals* and *Remove* (`danger`) / *Cancel*. Esc and the backdrop cancel (the Modal's own). One goal reads *1 goal*.
- Where it is reached: *Remove party* is the `danger` button at the foot's start of Edit the party (`shell/goaldialog.js` `GoalEdit`, with `shell-modal__left`), the one dialog both *Edit the party* buttons (the party's line, a goal's screen) open; it is never drawn for `general`. The column has no heading for General, so no other way to it exists. Pressing it replaces Edit the party with the question (nothing typed there is saved).
- It sends `ideas.track_drop {slug, goals}` through `command(..., quiet = true)` (`js/link.js` gained that third argument: the town's refusal is not toasted, the caller says it). A refusal (*k goals at work: stop them first*, *That party is gone*) is said in the question (`role="alert"`, `.shell-modal__refused`, the danger colour), which stays with its buttons, and the Board is read again. On success: the dialog closes, the toast *<party> removed* with *: k goals moved to General* or *: k goals removed* when there were any, `refreshShell()` redraws the column; when the removed party was the one shown, `track` is cleared, its kept choice forgotten and what was hovered or spread left (`leaveParty`), so the column shows its first party (General has no heading of its own).
- Tests: `tests/test_party_removed_desktop_browser.py` (9): the action's place and colour, absent for General, the choices and their order and focus, move (command, toast, party gone, the first party shown), drop, an empty party, both refusals in the question with no toast, Esc.
