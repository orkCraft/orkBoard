# Spec 83 — New goal in one field; the night only for Low work, on the person's word

The owner, 25 October (decisions §100), testing: New goal still shows its title and what it is for apart; only Low work
is offered the night, and only with the person's explicit permission: one standing permission, asked once (the
owner's answer). **Builds:** Claude · **Review:** light · P1.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §2, §3, §5 | `realm/idea_risk.py` (`AUTOSTART`), `gui/ideas.py` (`ideas.add`: `night` only with Low), `gui/ideas_board.py` (`autostart`, `ideas.queue`, `ideas.night_allow`), `core/idea_night.py` (the night's own runs behind the permission), `settings.py` (`night_low`), `realm/lexicon.py`; `tests/test_idea_risk.py`, `tests/test_gui_ideas.py`, `tests/test_idea_night.py` |
| **B. Desktop** | §1, §4 | `js/shell/ideadialog.js`, `js/shell/settings.js`; `tests/test_shell_browser.py` and the New goal tests that read *Its title* |
| **C. Phone** | §4 | `pwa/shell-ideas.js`, `pwa/shell-preview.js`, `pwa/shell-drawer.js`, `pwa/sw.js` (`CACHE` one up) and its pins; `tests/test_pwa_new_goal53_browser.py` |

## 0. The words
*The goal* (its hint *its first line is its title*, as the phone's). The question, once: *Low work may run at night?*,
its line *Low goals then run between 01:00 and 07:00, on what is left of the window; you can change it in Settings*,
its answers *Yes, at night* / *No, by day*. Settings: *Low work may run at night* (on / off), its hint *and the leaders
re-read goals and propose new ones then*. *Put it back*'s tooltip *Keep it on the party, not started*. A Low goal's
state: *tonight* with the permission, *after the other priorities* without. Gone: *Its title*, *What it is for* (New
goal's; New party keeps its own), *Keep for tonight* as the Add button's word, *or tonight when its priority is Low*.

## 1. One field (B)
The typed goal (`TypedGoal`) has one textarea, *The goal*, in place of *Its title* and *What it is for*; the type's asks,
Refs, the join line and Priority under it, as today. What it sends is the field's text (its first line the title), as
the phone does.

## 2. One standing permission (A)
`ideas.night_low`: `null` (not asked yet, the default and what every Board has after this spec, older ones included),
`true` or `false`. **`ideas.night_allow {allow: bool}`** sets it (`event_log` `night_allowed`, with `allow` and `face`)
and answers `{"ok": true, "moved": n}`.
- `true`: a Low goal goes at night as before (`AUTOSTART` low/low `"night"`; a Low plan's start and a Low goal's draft
  wait for the night window); spec 44's pace may still move it by day when the week is ahead.
- `false` or `null`: nothing goes at night. `AUTOSTART` low/low reads `"start"`: a Low goal starts by day, after the
  other priorities (the runner's order, as today). Goals already queued for the night are moved to *now* when it is set
  `false` (`moved`); with `null` they stay queued until it is answered.
- Only Low work: a goal of another priority is never put to the night. `ideas.add {night: true}` with another priority
  is refused, *Only Low work waits for the night*; a pitch's and a held goal's *Tonight* set the goal Low.
- Closing New goal with words in it sends `hold: true` (kept, not started), never `night`.

## 3. The question (B, C)
When a Low goal is added and `night_low` is `null`, the face asks §0's question once (orkUI's dialog; a sheet on the
phone), the goal added either way; the answer sends `ideas.night_allow`. *Tonight* on a pitch or a held goal with
`null` asks it the same way first; with `false` it is not drawn. Settings (both faces) shows the switch, unset drawn off
with *not asked yet*.

## 4. The faces (B, C)
New goal has no night box: Low reads *Add* as any priority, with the line under Priority *runs tonight* or *runs after
the other priorities* as the permission says. *Put it back* keeps (§2).

## 5. The night's own runs (A)
`core/idea_night.py`'s re-reading of goals, its proposals and a checker's leave proposal run only with `night_low`
`true` (§100.5): one permission for what runs at night.

## 6. Tests
- **A**: `null` and `false`: low/low starts by day, the night's runs do not run; `true`: low/low waits for the night,
  the night's runs run; setting `false` moves the queued goals; `night` refused without Low; a pitch's Tonight makes it
  Low; close sends hold; the event.
- **B / C**: one field, its text sent; the question asked once on the first Low goal and never again; its answer sent;
  the Settings switch; *Put it back* sends `hold`; no *Its title* left.
- Each part: the critical tests, its files' tests, `tests/test_gui_wording.py`; C also `tests/test_pwa.py`.
