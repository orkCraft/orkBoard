# 139. The die, the door and the bug

Decisions §246. **Builds:** the cheaper model: O (orkUI) first; A (the page) after it; B (the host's Stopped and Resume)
and C (the door, with spec 138's B) after A · **Review:** the critical tests and each part's own · P1. The look:
`docs/mockups/die-and-door/` (the die at about 34°, its front face's marks, the quarter turn, the door and its line).

| Part | What | Where (and its tests) |
|---|---|---|
| **O. orkUI's die** | the steeper view; the front face's marks `front-stop`, `front-resume`; the right face blank; the quarter turn `is-turning` | orkUI `office/die/die.json`, `tools/build_die.py` (it writes the die's block of `office/components.css`), `office/die/README.md`, `tests/test_orkui.py`; one version with spec 141 O (0.29.0); copied into Orkboard |
| **A. The die's front face, the bug moved** | the front face a button of its own: *Stop all* (muted at rest, danger while something runs); the door's Stop all gone from the top row; the bug's icon gone, *Report a problem…* in the Orkmaster's **…**, *Report* where a crash is shown, the fix's line under the pane's title | `hand/playdie.js`, `hand/mana.css`, `table/door.js` (its Stop all), `table/tabs.js`, `hand/logsbtn.js`, `table/pane.js` (the menu's items), `table/notice.js`, `crashes.js`; `tests/test_play_die_browser.py`, `test_repair_browser.py`, `test_leaders_table_browser.py`, `test_table_desktop_browser.py` |
| **B. Stopped and Resume** | Stopped a state of the project; nothing starts by itself while it holds; Resume starts again what the halt stopped; a goal started by hand resumes | `realm/halt.py`, `gui/board_host.py` (`halt`, a new `resume`, the snapshot's `stopped`), `gui/ideas_route.py` (`route_tick`), the runner that starts tasks (`core/idea_task.py` or where a plan's tasks start); `hand/playdie.js` (the front face's Resume); new `tests/test_halt_resume.py`, `test_play_die_browser.py` |
| **C. The door: Here or Away** | the door at the top row's end, open *Here*, shut *Away until 19:00*; the hours lead, a press holds until the next edge; one state for the person | `table/door.js` (rewritten), `table/tabs.js`, `hand/uptop.js` (the phone's top row), the host's `presence` (with spec 138 B's hours); `tests/test_door_presence.py`, a browser test |

## O. orkUI's die

1. **The view**: the cube at rest seen at about **34°** from above and turned about **−20°** (today 18° and −14°: the
   front face is then a strip of about 16 px at the 3 px cell); the box grows to hold it (the mockup's `.mk-tilt`: the
   die's height 30 cells). The front face at the 3 px cell is then about 33 px tall, at the 6 px cell (`big`) about 66 px.
   The wobble's, the roll's and the landing's poses are made again from `die.json` by `tools/build_die.py` for the new view.
2. **The front face's marks**, classes of the die as the up face's are: **`front-stop`** (a square of 8 × 8 cells at the
   face's middle) and **`front-resume`** (a circular arrow, the mockup's grid), in **`--_front`**: the muted ink by default,
   **`.is-orks-running`** the danger's, **`.is-orks-stopped`** the ink. With neither class the front face keeps today's 1.
3. **The right face blank** when a front mark is set (one mark on the orks' side).
4. **`.is-turning`**: a quarter turn round the up axis (`rotateZ` 0 → 90°, three steps, `--ork-motion-quick` × 3), once,
   ending at `animationend` named `ork-die-turn`; the page swaps the front mark then. Under reduced motion no turn.
5. README, CHANGELOG, `tests/test_orkui.py` (the die's table) and `tools/build_die.py --check` green; pushed; copied.

## A. The die's front face, the bug moved

1. **Two buttons in the die**: the up face is Play as today (`playdie.js`); **the front face is a second `<button>`**
   laid over the front face's box (measured: a transformed face's `getBoundingClientRect` is its projection; the two
   boxes split at the middle of the up face's bottom and the front's top, as the mockup's `lay`). Its words: `aria-label`
   *Stop all: stop every run of this project's orks*; `title` the same.
2. **Its state**: the die gets `front-stop`; `is-orks-running` while `isWorking` (`table/moods.js`) says a task runs,
   else muted. Pressed: `command("halt")` as the door did; until part B, the front face then says *Stopped* (muted) as
   the door said *All stopped*, and goes back to *Stop all* when work starts (`goalStarted`, `isWorking`), as today.
3. **Under the die two words**, as under a potion: *Play* · *Stop all* (*Playing*, *Stopped*); *Stop all* in the danger
   colour only while running.
4. **The door's Stop all leaves the top row** (`table/tabs.js`: no `StopDoor`); the door comes back as part C.
5. **The bug leaves the top row** (`hand/logsbtn.js` no longer rendered in `tabs.js`): its panel (*What went wrong?
   (optional)*, **Fix it** when `repair.can`) opens from **Report a problem…**, a new item of the Orkmaster's **…**
   (`table/pane.js`'s items, after Files; the icon `bug`). On the phone the crown's menu (`hand/upmenu.js`) has the same
   item. A crash the page shows (`crashes.js`) has a **Report** button opening the same panel with the crash's text in
   its line. **While a fix runs** (`town.repair.state` running) the Orkmaster's line under the pane's title
   (`table/notice.js`) says *Fixing Orkboard: <its line>*; a fix done that waits for the person is dealt as a card to the
   hand if the host sends one, else the line says *Orkboard was fixed: restart to take it* until put away.
6. Tests: the die has two buttons with their labels; the front's colour is the danger's only with a task running; a press
   on the front sends `halt`; the top row has no door and no bug; the menu has *Report a problem…* and opens the panel.

## B. Stopped and Resume

1. **`halt.py` keeps what it stopped**: `halt_all()` records each killed run's owner (`who`) and, where the caller gives
   it, a way to start it again (a task's `(slug, tid)`); `stopped()` says whether the project is stopped; `resume()`
   clears it and returns what was stopped.
2. **The host**: `halt` sets the project **stopped** (kept in the state dir so a restart keeps it); a new command
   **`resume`** clears it and starts again each task killed by the halt from its start (its worktree's commits kept), as a
   plan's task starts; the snapshot carries **`stopped: true|false`**. While stopped, **nothing starts by itself**: the
   clock's passes (`route_tick`, the backlog's queue of §239, a ripe decision's start, a plan's next task) return at
   once. A goal started by the person (`ideas.talk`, `ideas.start`, `ideas.confirm`, `ideas.start_now`, `ideas.add` with
   a start) clears it first and the page says *The orks are back at work* (a toast).
3. **The page**: while `stopped`, the die's front face is `front-resume` with `is-orks-stopped`, its button *Resume:
   the orks go back to work*, the word *Stopped*; pressed it sends `resume`. On each change the die turns (`is-turning`)
   and the mark swaps at its end.
4. Tests (`tests/test_halt_resume.py`, pure where it can): halt records and `stopped` holds; `route_tick` starts nothing
   while stopped; `resume` restarts the killed task; a goal started by hand clears stopped. The browser: the front face
   says Resume while stopped and sends `resume`.

## C. The door: Here or Away

Built with spec 138's part B (the hours). The door is orkUI's `.ork-door` unchanged; only what it says changes.
1. **The host's presence**: `presence = {here: bool, until: iso|"", held: bool}` in the snapshot, from the person's hours
   (spec 138 B.1) and a hold: `presence.set {here}` holds the other state until the hours' next edge (then the hold
   ends by itself); with no hours set, the door is the person's alone, *Here* at first, and a press sets it with no end.
   Kept per person (the settings' file), so the computer and the phone read the same.
2. **The door** (`table/door.js` rewritten as `PresenceDoor`): at the top row's end; **open** with *Here* and its line
   (*until 23:00* when the hours give an edge), **shut** with *Away* and *until 19:00*; *· held* when a press holds it.
   `aria-pressed` = here; its `title` says what a press does. On the phone's top row (`hand/uptop.js`) the small door.
3. **What Away changes** is spec 138 B.3's (the steps that ask wait for the hours, no push but money's and safety's).
4. Tests: presence from the hours and a hold, the hold ending at the edge; the door's words; the phone has the door.
