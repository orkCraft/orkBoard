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


## As built (A)

- `settings.py`: `IDEAS["night_low"]` is `None`; `clean_ideas` keeps a bool and reads anything else as `None`; `night_low` is one of `BOARD` (the project's keys), so `board.json` carries it and a Board from before has `None`. `ideas.board` answers it among the Board's settings (`board_settings()`: `night_low` is `true`, `false` or `null`), which is where both faces read it.
- `realm/idea_risk.py`: `decide(risk, priority, night=False)`; `AUTOSTART` keeps low/low `"night"`, and `decide` reads it `"start"` unless `night` is true. `gui/ideas_board.py` `autostart` passes `night_allowed()` (`night_low is True`), so a Low plan of low risk starts by day, after the other priorities (the runner's order), without the word.
- `ideas.night_allow {allow}` (`gui/ideas_board.py`, registered in `gui/ideas.py`'s table; a phone's too) -> `{"ok": true, "moved": n}`; a non-bool `allow` is refused (*Low work may run at night is on or off*). The event `night_allowed` (`allow`, `moved`, `face`, `device`; `realm/event_log.py` `NIGHT_ALLOWED`). Set `false`, `_night_to_day` takes what waited for the night to the day: a raw goal in the `night` queue goes to `now` and is drafted, a passed plan with `start_at: "night"` loses it and starts (a plan already at work: the runner ticks). `moved` counts both. Set `true` or `null` moves nothing.
- `ideas.add`: `night: true` with any priority but Low is refused (*Only Low work waits for the night*). A Low goal goes to the `night` queue only with `night_low` true; with `false` or `null` it is drafted at once (`now`), after the other priorities. `hold` and a goal sent from a pitch are as before. `ideas.queue` `night` (a pitch's and a held goal's *Tonight*) sets the goal Low and is refused without the word (*Low work may run at night is off: switch it on in Settings*): a face asks first and sends `ideas.night_allow` before it. A proposal taken as Low goes to the night only with the word.
- `core/idea_night.py`: `night_allowed()`; `run_night` runs none of its five steps (the queue, the starts, the re-reading of goals, the proposals, a checker's leave proposal) without it, and `pace_tick` (spec 44) does not start. With `null` what was queued stays queued until it is answered.
- `realm/lexicon.py`: the term `night_low`, *Low work may run at night*.
- Tests: `tests/test_night_low.py` (15: the setting, the command and its event, the queue by the word, `night` refused, Tonight makes the goal Low and needs the word, low/low by day and at night, `moved`, null leaves the queue, a taken proposal, the night's runs and the pace without and with the word); `tests/test_idea_risk.py` (both readings of the nine cells). The older tests that kept a goal raw with `night: true` keep it with `hold: true`; the hosts of `tests/test_gui_ideas.py`, `test_week_pace.py` and `test_ideation.py` start with the word.

## As built (B)

- `js/shell/ideadialog.js`: `TypedGoal` has one textarea, *The goal* (`aria-label` "The goal", its hint *its first line is its title*), in place of *Its title* and *What it is for*; `text` is the field as it stands (trimmed). The type's asks, Refs, the lens, the join line and Priority are under it as before. Both `close` handlers (and `PitchGoal`'s) send `hold: true` (the typed one with its type and asks, never `join`), never `night`.
- No night box. The line under Priority (`data-night="priority"`) says *Low: runs tonight.* with `board.night_low` true and *Low: runs after the other priorities.* otherwise; the Add button's tooltips lost *or tonight when its priority is Low*; *Put it back* has the tooltip *Keep it on the party, not started*.
- `js/shell/nightask.js` (new): `NightAskDialog`, the dialog kind `night-ask` (`shell/dialogs.js`), orkUI's `Modal` titled *Low work may run at night?*; the line *Low goals then run between 01:00 and 07:00, on what is left of the window; you can change it in Settings* (the Board's own window); *Yes, at night* (`primary`, first, focused) and *No, by day* send `ideas.night_allow {allow}` through `act`, then close and run `after(allow)`. Esc, × and the backdrop answer nothing. `askAfterLow(priority)`: after `Add the goal` of a Low goal while `board.night_low` is `null`, the goal added either way; a Board that does not say (`undefined`) is never asked.
- `PitchGoal`'s *Tonight* sends `{priority: "low", night: true}`; with `null` it asks first (the pitch is added after *Yes, at night*; after *No, by day* it is kept on `hold` and the toast says *Kept, not started: Low work runs by day.*); with `false` it is not drawn.
- `js/shell/settings.js`: the switch *Low work may run at night* (`data-settings="night-low"`) after the Night window, hint *and the leaders re-read goals and propose new ones then*, with *· not asked yet* while `null`; a press sends `ideas.night_allow`.
- Tests: `tests/test_night_asked_desktop_browser.py` (8, 1 440 × 900): the question once with its words and buttons and the answer sent, *No, by day* and never again, a Normal goal and Esc ask or answer nothing, closing sends `hold`, the tooltips, the Settings switch (unset: off, *not asked yet*), a typed goal as one field (no *Its title* left) and its text sent, *Tonight* on a pitch (asked first, Low, gone after *No*). The older desktop tests that read *Its title* / *What it is for* or `night` read *The goal* and `hold`; the stubs (`StubHost`) carry `night_low` (true) and `ideas.night_allow`.

## As built (C)

- `pwa/shell-night-ask.js` (new; in `sw.js` `SHELL`; mounted in `pwa/board.js`'s `sheets`): `makeNightAsk(core)` gives the question, a sheet (`dialog.night`) titled *Low work may run at night?*, with the same line and the two 44 px choices *Yes, at night* (`primary`, first, `night-yes`) and *No, by day* (`night-no`); `core.askNight(after)`, `core.nightUnset()` and `core.nightOff()` are the Board's frame for it. A choice sends `ideas.night_allow {allow}` through `core.call`, the host's refusal is said in the sheet (`role="alert"`), then the sheet is put away, the Board read again and `after(allow)` run. Closing it answers nothing. `pwa/app.css`: `.night-ask` (as `.remove-ask`).
- `pwa/shell-ideas.js`: *Keep for tonight* is gone as the Add button's word (it is *Add the goal* at every priority); the line under Priority (`data-night="priority"`) says *Low: runs tonight.* or *Low: runs after the other priorities.* as `board.night_low` says. After a Low goal is added with `night_low` null the question opens. *Put it back*, Close and Esc with words in it send `hold: true` (the flash *Kept on the party, not started.*), never `night`; a pitch's *Hold* is as before. *Tonight* on a pitch sends `{priority: "low", night: true}`; with `null` it opens the question over the form (*Yes* sends the pitch, *No* leaves the form open without *Tonight*); with `false` it is not drawn.
- `pwa/shell-preview.js`: a held goal's *Tonight* (`ideas.queue` `night`, which makes it Low): with `null` the question first, then the queue; with `false` it is not drawn. `pwa/shell-drawer.js`: the switch *Low work may run at night* (`#night-low`) after Night, with its hint and *· not asked yet*; it sends `ideas.night_allow`.
- `sw.js` `CACHE` `orkcraft-app-v90` -> `orkcraft-app-v91`; `tests/test_pwa.py` pins it.
- Tests: `tests/test_pwa_night_asked_browser.py` (390 × 844, the arena's scene with a Board not asked): the first Low goal asks once in a sheet (words, 44 px, order, no sideways scroll), the answer sent and never asked again, *No, by day*, a Normal goal or a closed form asks nothing, Esc answers nothing, the drawer's switch, *Tonight* on a pitch (asked first, Low; *No* leaves the form without it), the service worker; `tests/test_pwa_board35_browser.py`: a held goal's *Tonight* asks first, and is gone after *No, by day*. The older phone tests that read *Keep for tonight* or `night` read *Add the goal* and `hold`; the stubs carry `night_low` and `ideas.night_allow`.
