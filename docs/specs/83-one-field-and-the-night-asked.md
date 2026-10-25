# Spec 83 — New goal in one field; the night only for Low work, on the person's word

The owner, 25 October (decisions §100), testing: New goal still shows its title and what it is for apart; only Low work
is offered the night, and only with the person's explicit permission. **Builds:** Claude · **Review:** light · P1
(§5 waits for the owner's call on its default).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §2, §3, §5 | `realm/idea_risk.py` (`AUTOSTART`), `gui/ideas.py` (`ideas.add`: `night` only with Low), `gui/ideas_board.py` (`autostart`, `ideas.queue`), `core/idea_night.py` (the night's own runs behind the switch), `settings.py` (`night_runs`), `realm/lexicon.py`; `tests/test_idea_risk.py`, `tests/test_gui_ideas.py`, `tests/test_idea_night.py` |
| **B. Desktop** | §1, §4 | `js/shell/ideadialog.js`, `js/shell/settings.js`; `tests/test_shell_browser.py` and the New goal tests that read *Its title* |
| **C. Phone** | §4 | `pwa/shell-ideas.js`, `pwa/shell-preview.js`, `pwa/shell-drawer.js`, `pwa/sw.js` (`CACHE` one up) and its pins; `tests/test_pwa_new_goal53_browser.py` |

## 0. The words
*The goal* (its hint *its first line is its title*, as the phone's). *Tonight* (a box, only with Low: *Run it tonight
(01:00–07:00)*). *Put it back* keeps its words: its tooltip *Keep it on the party, not started*. Settings: *At night,
leaders re-read goals and propose new ones* (on / off). Gone: *Its title*, *What it is for* (New goal's; New party keeps
its own), *Keep for tonight* as the Add button's word, *or tonight when its priority is Low*.

## 1. One field (B)
The typed goal (`TypedGoal`) has one textarea, *The goal*, in place of *Its title* and *What it is for*; the type's asks,
Refs, the join line and Priority under it, as today. What it sends is the field's text (its first line the title), as
the phone does.

## 2. The Board never puts work off to the night (A)
`AUTOSTART["low"]["low"]` is `"start"`: a Low goal of low risk starts by day, after the other priorities (the runner's
order, as today). `night_by="board"` is no longer written; goals queued so before stay as they are. Spec 44's pace (the
Board's own night going by day) has nothing left to move and keeps reading only what was queued before.

## 3. The night is asked (A)
`ideas.add {night: true}` is kept only with `priority: "low"`; with another priority, *Only Low work waits for the
night*. `ideas.queue {night}` and a pitch's *Tonight* set the goal's priority Low as they put it off. Closing New goal
with words in it sends `hold: true` (kept, not started), never `night`.

## 4. The faces (B, C)
New goal: the *Tonight* box appears when Low is picked, unticked; ticked, the Add button says *Add for tonight*. The
pitch's and a held goal's *Tonight* say *Tonight, as Low work*. *Put it back* keeps (§3). Settings has §5's switch.

## 5. The night's own runs (A)
`core/idea_night.py`'s re-reading of goals, its proposals and a checker's leave proposal run only with
`ideas.night_runs` on. The PM proposes **off** by default (§100.5: the owner's call); a Board that had them before keeps
them on until the person turns them off.

## 6. Tests
- **A**: low/low starts; `night` refused without Low; `queue`'s and a pitch's Tonight make it Low; close sends hold; the
  night's runs off and on.
- **B / C**: one field, its text sent; the box only with Low; *Put it back* sends `hold`; no *Its title* left.
- Each part: the critical tests, its files' tests, `tests/test_gui_wording.py`; C also `tests/test_pwa.py`.
