# 138. The day read from the resets

Decisions §245 (and §246.4–5 for the door). **Builds:** the cheaper model: A on the page; B on the host with spec 139 C;
C after B · **Review:** the critical tests and each part's own · P1. No mockup for C yet: it is drawn after B is used
(the owner's call, 4 November).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The potion and the column linked; the hour under a potion** | a potion hovered or focused lights the column's cards that wait for its tool and dims the others; a card hovered hatches its next step off its tool's potion; the hour a potion comes back under it when it runs low | `hand/mana.js`, `hand/mana.css`, `hand/state.js` (a signal `litTool`), `table/piles.js` and `table/column.css` (the dim), `hand/cost.js`; `tests/test_hand_mana_browser.py`, `test_column_browser.py` |
| **B. The person's hours; each put-off goal's window** | the setting *When I am at the computer*; the presence (spec 139 C.1); the queue of §239 giving each goal the window that fits it; a step that asks laid in the hours while Away; the rows' *not before 14:05* | `realm/idea_target.py`, `gui/ideas_route.py` (`route_tick`, `_backlog_next`), the settings (`shell/settings.js` and the host's settings' keys), `table/piles.js`/`column.js` (the pile's list rows); `tests/test_idea_target.py`, `test_idea_route.py`, new `tests/test_hours.py` |
| **C. The day over the pane** | a potion pressed opens a line of time with *Now*: behind it what used the tool today, ahead its resets and the goals waiting for them, the hours a band | `table/over.js` (the `limits` view), a new `table/dayline.js` + `dayline.css`; a browser test |

## A. The potion and the column linked; the hour under a potion

1. **`litTool`** (`hand/state.js`): the provider of the potion hovered or focused, "" otherwise (set on pointer enter /
   focus, cleared on leave / blur, as `markedTool` is).
2. **The column** (`table/piles.js`): while `litTool` is set, a card whose goal waits for that tool stays as it is and
   every other card gets `.is-dim` (`opacity` of orkUI's muted ink, never hidden; `column.css`). A goal waits for a tool
   when its node says so: `held_until` with its tool, a `waits` whose tool is it, a To review card whose spec starts on
   it, or a goal at work held by that tool's spent window. Where the snapshot does not say a goal's tool, the default
   tool's potion lights it.
3. **The potion's words** add *goals wait for its reset* when any does (never how many, §67).
4. **A card hovered** in the column hatches its next step's share off its tool's potion (`--ork-potion-spend`, as a
   lifted card does through `hand/cost.js`), when the node carries a cost.
5. **The hour under a potion**: at the danger's level or empty (`levelOf` of the lower share), the now share's place
   says **back 14:00** (the shortest window's reset, the machine's local time; *back Mon 09:00* when it is the week
   that is out or the reset is not today). The words keep both shares as today.
6. Tests: hovering a potion dims the cards not waiting for it; the hour shows at the danger's level and not above it.

## B. The person's hours; each put-off goal's window

1. **The hours**: a setting **When I am at the computer** (Settings, a section of its own): rows of days and a span
   (*Weekdays 19:00–23:00*, *Sat–Sun all day*), empty by default. Kept in the settings' file as `hours: [{days:
   [0..6], from: "19:00", to: "23:00"}]`. `idea_target.in_hours(settings, now)` and `next_edge(settings, now)`.
2. **Presence** is spec 139 C.1, read from the hours.
3. **Away lays a step that asks**: a step that will ask the person (a goal's Talk, a review its work waits for) does
   not start while presence is Away; it waits for **the first reset inside the hours**, or the hours' start if no reset
   is read. A step that asks nothing (a plan's tasks, the leaders' sections after Talk, Checks) goes on. While Away, the
   push sends only money's and safety's cards (a cost grown past what was agreed, paid going on, a run to stop).
4. **Each put-off goal's window** (§239's queue): before starting the next goal, its next step's cost (§121.3, the
   route's) is read against what the coming window holds above the reserve (`idea_target.reserve`); if it does not
   fit, its `held_until` moves to the next reset and the queue looks at the goal after it. The order never changes.
5. **The hour on its row**: in the pile's list (§206.3) each put-off goal's row says **not before 14:05** (its
   `held_until`, local time; the day's name when not today); a goal at work held by a spent window says **the work goes
   on at 14:00**. Never a countdown.
6. Tests: `in_hours`/`next_edge` across midnight and a week; a goal that does not fit waits for the next window and
   the next in order goes; Away holds a Talk until the hours and not a task; no hours set is today's behaviour.

## C. The day over the pane

1. A potion pressed opens over the pane (as today: *<tool>: what used it*) **a line of time with *Now* across it**:
   behind *Now* what used the tool today (today's rows, as they are drawn now, laid on the line by their hour); ahead,
   today and tomorrow, the tool's windows' resets as marks and the goals waiting for them as cards on the reset they
   wait for (their rune, short name and the step in words: *Talk*, *spec*, *work*); the person's hours as a lighter
   band. A row a tool, the one pressed on top, the others with goals waiting under it.
2. It decides nothing: a card pressed opens its goal; nothing is dragged.
3. Test: the line has *Now*, the resets, a waiting goal on its reset, the hours' band when set.
