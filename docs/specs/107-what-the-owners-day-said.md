# 107. What the owner's day said: a gate that cannot run is not red, the logs say the whole day, and twelve looks

Decisions §182 (1–15). The owner, 29 October, after a day on a Node game (`~/halloween`): no goal reached its end; the
logs show why (§1). With them, twelve notes on the desktop window (§182.3–§182.15). **Builds:** Claude (the cheaper model
builds, the spec's author reviews) · **Review:** full · P0 for A and B, P1 the rest. The desktop only, but where a part says
the phone.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The gate** | could not run ≠ red; install and test again; documents only; the same failure again | new `realm/gate_env.py`; `realm/gate_config.py`, `realm/idea_git.py`, `realm/dep_links.py`, `realm/event_log.py`, `core/idea_runner.py`, `core/idea_task.py`, `core/idea_landing.py`, `core/idea_review.py`, `gui/ideas_review.py`, `js/shell/review.js`, `pwa/shell-review.js`; new `tests/test_gate_env.py`, `tests/test_gate_config.py`, `tests/test_idea_runner.py`, `tests/test_idea_git.py` |
| **B. The logs** | what was refused, what was shown red, the crashes, the server's log, the project, the page | `realm/event_log.py`, `gui/server.py`, `gui/logs_save.py`, the diagnostics' `about`, `core/idea_runner.py` (`ran_why`), `js/shell/errors.js`, `js/crashes.js`, `pwa/shell-drawer.js`; `tests/test_logs_save.py`, `tests/test_event_log.py` |
| **C. A log one reads** | the log as sections, its end first, the line of what happened | new `js/shell/logview.js`; `js/hand/stopface.js`, `js/shell/preview.js`, `js/hand/resultface.js`, `js/shell/shell.css`, `core/idea_review.py` (`log`), `realm/idea_git.py` (the tail) |
| **D. Drop a goal** | **…** on a goal's cards: *Drop this goal…* | `js/table/card.js`, `js/table/cascade.js`, `js/hand/routecard.js`, `js/hand/stopface.js`, `js/table/menu.js` |
| **E. A goal sent lies on the table** | routed: the Orkmaster's lane at once | `realm/goal_place.py`, `js/table/data.js`; `tests/test_goal_place.py` |
| **F. The System fits** | fitted to the pane's width; Fit / 100 % | `js/arena/systemarch.js`, `js/arena/systemmap.css`, `js/scrollcue.js` |
| **G. What works moves** | an ork at work moves; the time it has worked ticks; a change flashes once | `js/table/card.js`, `js/table/table.css`, `js/table/data.js` |
| **H. + Party, the project ▾** | the tabs' end says *Party*; the project's name opens the projects | `js/table/tabs.js`, `js/table/pane.js`, `js/table/table.css` |
| **I. Play** | its sheet back; the product's logo on the start screen; full screen | new `js/arena/play.css`; `js/arena/arena.css`, `js/arena/play.js`, `realm/assets.py`, `gui/ideas_assets.py`; `tests/test_design_system.py` (`SHEETS`) |
| **J. The bug under the glass** | Save logs a button by the mana | `js/hand/hand.js`, `js/hand/mana.css` |
| **K. @ in New goal** | a party or a file, offered as one types | `js/hand/pluscard.js`, new `js/hand/mention.js`, `gui/board_files.py` (`files.find`), `gui/ideas.py` (`ideas.add`), new `realm/goal_mentions.py`; new `tests/test_goal_mentions.py` |
| **L. The crowned ork is Orkboard's mark** | favicon, the phone's icons, the Dock, VS Code, onboarding | new `design-system/logo/orkboard/`, new `orkboard/design/mark.py`; `gui/server.py`, `gui/pwa.py`, `gui/mac_app.py`, `vscode/media/icon.png`, `js/onboarding.js`, `NOTICE` |
| **M. New goal's frame** | the green card worth looking at; never under another card | `js/hand/hand.css`, `js/hand/pluscard.js`, `js/hand/hand.js`, `js/hand/stacks.js` |
| **N. The game's loops** | loops in loops, the currencies, the feelings, what the loop says | `realm/loop.py`, `core/idea_loop.py`, `gui/ideas_loop.py`, `js/table/loopmap.js`, `js/table/maps.css`; `tests/test_loop.py` |

## 0. What the logs said (29 October, 18:14–18:49)

Five tasks of three goals (Game design ×2, Art ×1), $6.09, 4.7 M tokens. Every result came to Review red with
`passed: null, failed: null`, the person pressed **Fix** with the line the face wrote (*Fix the failing tests*), five rounds
on one task, its session grown to 1.18 M tokens, and no goal ended. The gate (`gate_config.derive`: `npm test --prefix
prototypes/ar && npm test --prefix server`) ran in each task's worktree and said `sh: vitest: command not found`:
`prototypes/ar` had never been installed in the main checkout, so `dep_links.link` (spec 86 §2) had no `node_modules` to
lay, and a task may not run `npm ci` (`realm/task_commands.py`). The session said so each round, plainly, and was sent back
each round. The task that wrote `docs/game-loop-analysis.md` and nothing else ran the AR prototype's and the server's
tests. Besides: tasks planned on *elder* ran on *warrior* (`ran_tier`) with nothing saying why; the zip had no app log (a
terminal's launch keeps none), no crash file and no line of what the page showed red.

## 1. Part A: the gate

### 1.1 Could not run (`realm/gate_env.py`, no face)

```
why = gate_env.could_not_run(out, code)        # "" or the sentence; `out` the gate's output, `code` its exit code
rows = gate_env.missing(root)                  # [{"dir": "prototypes/ar", "command": "npm ci"}]: what install would make it run
ok, out = gate_env.install(root, rows, cancel, timeout_s=900)
```

1. `could_not_run` is not empty when the run could not test anything: exit code **127**; a shell's *not found*
   (`sh: vitest: command not found`, `sh: 1: vitest: not found`, `zsh: command not found: vitest`); Windows' *'vitest' is
   not recognized as an internal or external command*; Node's `Cannot find module 'x'` / `Cannot find package 'x'` /
   `ERR_MODULE_NOT_FOUND` **for a package name** (not one starting with `.` or `/`: a missing file of the project is the
   code's); Python's `No module named pytest`. The sentence names what is missing: *The tests could not run: `vitest` is
   not installed.* (the name in backticks; without a name: *The tests could not run: a command they need is not
   installed.*).
2. `missing(root)`: each folder of `gate_config.package_dirs(root)` whose `package.json` lists `dependencies` or
   `devDependencies` and has no `node_modules` folder in the main checkout; its command by its lock: `package-lock.json` /
   `npm-shrinkwrap.json` → `npm ci`, `pnpm-lock.yaml` → `pnpm install --frozen-lockfile`, `yarn.lock` → `yarn install
   --frozen-lockfile`, `bun.lock` / `bun.lockb` → `bun install`, none → `npm install`. `dir` is `"."` for the root. Python
   is never installed by Orkboard (a `.venv` is the person's).
3. `install` runs each row's command (words, `cwd` the folder, no shell) one after another, stops at the first that fails;
   `(ok, the output's last 4000 characters)`. A command not on this computer is `(False, "npm is not installed on this
   computer")`.

### 1.2 The gate's run

1. `GateRun` (`realm/idea_git.py`) gains `seconds` (the run's) and `env` (`gate_env.could_not_run(out, code)` of a red run,
   else "").
2. **Documents only** (`gate_config`): when the gate is the project's own (`derive`, no `[gate]` in `orkcraft.toml`; a
   `Gate` gains `derived: bool`) and every file the task touched is a document (`.md`, `.mdx`, `.markdown`, `.txt`,
   `.rst`, `.adoc`), nothing runs: `GateRun(True, "no tests ran: the task changed only documents", ran=False, docs=True)`.
   A `[gate]` the project wrote runs as written.
3. In `_work` (`core/idea_runner.py`) a run with `env` **is not sent to the session**: the loop breaks after try 1 and the
   task goes to Review. `_tests_of` adds `env` (the sentence), `install` (`gate_env.missing(root)`, maybe empty) and `docs`.
4. `look_reason` (`core/idea_landing.py`): `COULD_NOT_RUN = "the tests could not run"` before `RED`; `DOCS = "it changes
   only documents"` before `NOT_RUN` (a document waits for a person's look: never landed by itself).
5. Event **`gate_ran`** (`realm/event_log.py`): `idea, task, round, attempt, command, exit, seconds, verdict` (`green` |
   `red` | `could_not_run` | `docs` | `nothing`), `missing` (the name `could_not_run` found, or ""), `linked` (how many
   dependency folders lie linked in the worktree: `dep_links.present(root, worktree)`, new: the symlinks under the
   worktree that point into the main checkout). One per try. `result_ready` gains `exit` and `verdict`.

### 1.3 Install and test again

1. `ideas.regate {slug, task, install}` (`gui/ideas_review.py`) → `runner.regate(slug, tid, install, device)`
   (`core/idea_review.py`): the task must be at Review with `tests.env`; else *That result is not waiting for its tests*.
   `result_decided` with `decision: "install"` or `"test again"`. The round does not count up (nothing was sent back).
2. `_work` with `again = {"why": "", "files": [], "regate": True, "install": bool}`: no session call (as `taken`); with
   `install`, `gate_env.install(root, missing(root), …)` first, its lines in the task's log under `== installing: <dir>:
   <command>`; then `dep_links.link(root, worktree)` again; then the gate. An install that fails goes to Review with
   `tests.env` = *The install failed:* and its last line, the output in the log.
3. The faces (`js/shell/review.js`, `pwa/shell-review.js`), a result whose `tests.env` is set:
   - `testsWords`: *could not run*, the warning's tone, no sign.
   - The reason under the answers is `tests.env` (not *Its tests are red*), Merge off.
   - The first answer is **Install and test again** (primary) when `tests.install` is not empty, its title *Runs
     `npm ci` in prototypes/ar in your project, then the tests again* (each row, joined by *, then*); else **Test again**
     (*Runs the tests again: install what they need in your project first*). Fix and Drop stay, Fix not primary.
   - Its line under the reason: *Sending it back would not help: the task cannot install anything.*

### 1.4 The same failure again

1. A send back (`again` with a why, not `regate`, not `taken`) notes the worktree's head before its session. After the
   gate, when the head did not move and the gate's tail is the round before's, `tests.same = True`.
2. The faces: *The last fix changed nothing: the tests failed the same way.* under the reason; **Fix** opens its line
   **empty** (not *Fix the failing tests*), so a send back says something new.
3. `result_decided` gains `why_kind`: `"suggested"` when the line sent is the one the face wrote, else `"typed"` (the faces
   send `suggested: true`; `ideas.back` passes it on).

## 2. Part B: the logs say the whole day

1. **What was refused**: event `command_refused` (`command`, `error` cut at `TEXT_MAX`, `device`) for each reply
   `ok: False` in `gui/server.py` (`CommandError`, and a broken command with `kind: "broken"`); the `logs.*` and `crash.*`
   commands and `watch` are not recorded.
2. **What was shown red**: event `error_shown` (`title`, `text`) for each toast of severity `error` the town shows.
3. **Why a lower tier**: `task_state` of `running` gains `ran_why` when `ran_tier` is not the task's tier (the reason
   `ran_on` / `idea_target` took: `limits`, `pace`, `budget`, `role`, `floor`, whichever it is; "" when equal).
4. **The zip** (`gui/logs_save.pack`):
   - `crashes/`: the crash files (`core/crashes.log_dir()`) written in the period, newest first, at most 2 MB in all.
   - `app.log`: the Mac app's log as now; else the server's own log: new `~/.orkcraft/logs/<product>.log` (a rotating
     `logging` file, 1 MB × 3, warnings and errors and what `capture` caught, with their tracebacks), any launch.
   - `page.json`: what the page sent with `logs.save` (`page`): the window's width and height, `devicePixelRatio`, the face
     (`desktop`, `vscode`, `app`), the open tab, what lies over the pane (`over.kind`), the System's lens if open, and the
     page's last 20 errors (`js/crashes.js` keeps them, a message and the stack's first line each).
   - `about.json` gains `build` (the installed version and, from a source checkout, its git head) and `project`: the gate
     (`run`, `from`: `orkcraft.toml` | `derived` | `none`), each package folder (`dir`, `node_modules`: bool, `lock`), and
     `.venv`: bool.
5. `saveLogs` (`js/shell/errors.js`) sends `page`; the phone's download is named `orkboard-logs.zip` (the brand's name,
   never *orkline*).

## 3. Part C: a log one reads

1. `LogView({text, label})` (new `js/shell/logview.js`) for a task's log, a stop's log and a result's test tail:
   - ANSI escapes stripped (also on the host: `core/idea_review.log`, the gate's tail).
   - Split at lines starting `== `: each a section, its heading that line. A `== round …` section (the prompt a session got)
     is folded, its heading only; *the session answered*, *the gate*, *installing* open. The last section always open.
   - Opened at its end (scrolled to the foot), `max-height: min(60vh, 640px)`, the code face at the body's size, line height
     1.5, `--ork-ink` on `--ork-panel`; a **Copy** beside its caption.
2. **The line of what happened** above the log of a failed or red card (`hand/stopface.js`, `hand/resultface.js`): the
   task's `error`, else `tests.env`, else *The tests failed:* and the first failing name, in the body's face.

## 4. Part D: drop a goal

1. A goal's cards get **…** (`table/menu.js`): the Orkmaster's lane's card (`OwnCard`), a goal in line (`LineCard`), the
   route card (`hand/routecard.js`) and the goal's face over the pane (`hand/stopface.js`'s head). Its one item for now:
   **Drop this goal…** (orkUI's `trash` icon).
2. It asks in place: **Drop this goal?** *Its page and its plan go; what it spent stays counted.* With work running: *Its
   work stops first.* **Keep it** · **Drop it** (danger). Drop sends `ideas.stop` when its tasks run, then `ideas.drop`; a
   refusal is said in the card (*The Orkmaster is reading it: drop it when it is done*).

## 5. Part E: a goal sent lies on the table at once

1. `goal_place.place_of`: `routed` (not held for the reset) is `{"place": "table", "asks_you": True}`; its route card stays
   in the hand (an asking goal on the table is in the hand too, spec 98 §2.1).
2. `ownOf` (`table/data.js`): every goal on the table whose route has no party at work yet (`routed`, `talk`, `decided`,
   `sections`, as `reading`, `planning`) lies in the Orkmaster's lane, so a goal sent shows there before the hand deals its
   card.

## 6. Part F: the System fits

1. `.arch` (`arena/systemarch.js`) is drawn at its natural size, then scaled to the scroller's width (`transform: scale`,
   origin top left, the wrapper's size set to the scaled size): `fit = min(1, width / natural)`, never under **0.5**; the
   arrows measured in the unscaled box (`arrowsOf` divides by the scale).
2. Under 0.5 it stays at 0.5 and scrolls sideways; `scrollcue.js` marks left and right as it marks above and below; a drag
   on the empty ground pans.
3. In the System's corner **Fit** and **100 %** (the person's choice kept per project in `localStorage`, wrapped in
   try/catch).

## 7. Part G: what works moves

Spec 49 §11's *motion says what changed, never decorates* gains: **and what is alive: an ork at work moves; nothing that
waits does** (§182.7).
1. A task card at work (`data-state` `running` or `testing`): its race drawing steps up and down a pixel (two frames,
   `steps(2)`, 1.2 s); a stepped dotted line marches along the card's foot in `--ork-ink-faint`; the stage word says the
   time it has worked (*Doing · 1 m 12 s*, ticking each second).
2. A card whose state changed flashes its frame twice (`steps(2)`, 0.6 s) once, then is still.
3. A party's tab with an ork at work: its leader head steps as in 1 (part H, `tabs.js`).
4. All of it off under `prefers-reduced-motion`; the time still ticks.

## 8. Part H: + Party, the project ▾

1. The tabs' end's **+** says **+ Party** (`ork-btn`, not primary: green is New goal's, §180.4), `aria-label` *New party*.
2. The first tab's project name is followed by a **▾** (orkUI's `chevron-down`, its own 44 px target under touch, *Switch
   project*): it opens the projects over the pane (`openOver("projects", …)`). The Orkmaster's **…** no longer holds
   *Switch project*; the phone's **…** keeps it.
3. A party's tab gains `data-working` while one of its tasks runs (for G 3).

## 9. Part I: Play

1. Play's sheet came back: the rules of spec 88 §6 / 90 §1.3 / 91 §5 for `.playpane`, `.play-*` (lost with
   `arena/assets.css`) in a new `js/arena/play.css`, imported by `arena.css`, in `test_design_system.SHEETS`. The build
   fills the pane.
2. **The product's logo on the start screen**: `assets.logo(root)` (new): the project's tracked image whose name is
   `logo`, `icon`, `emblem`, `brand`, `app-icon` or `favicon` (a suffix after `-`, `_`, `.` or `@` allowed), an `.svg`
   first, else the largest `.png` / `.webp`; its URL in the build (`b.logo`, served as the assets' files are). With one,
   the start screen is the logo (128 px tall, `image-rendering: pixelated` under 64 px wide) coming up in six steps, a
   light band sweeping across it in steps and two blinks, then the name under it; the sweep again every 2.4 s while it
   starts (the console's start, decisions §182.11). Without one, the name as today.
3. **Full screen** in Play's bar (the stage's `requestFullscreen`; Esc leaves).

## 10. Part J: the bug under the glass

1. In `.hand-end`, before the mana and shown when there is no mana too: a quiet button, orkUI's sign `bug` with its icon
   `search` laid over its lower right (two of orkUI's pictures, nothing drawn here), *Save the logs*.
2. A press opens a small panel over it: *What went wrong? (optional)*, one line, **Save logs** → `saveLogs(line)`.

## 11. Part K: @ in New goal

1. In New goal's field (`hand/pluscard.js`), `@` at a word's start opens a list under the caret: the parties (their names,
   as `@Party` already addresses: `hand/state.js`) first, then the project's files and folders matching what follows.
   ↑ ↓ move, Enter or Tab takes, Esc closes; at most 8 rows.
2. `files.find {q, limit}` (`gui/board_files.py`): the tracked and untracked files not ignored (`git ls-files -co
   --exclude-standard`) and their folders, matched as a subsequence of the path, a name match first; ≤ 20.
3. A file taken is written `@path/to/file`. `ideas.add` (`realm/goal_mentions.py`) turns each `@path` that exists into
   `` `path` `` in the goal's text (so the route's `_PATH` and the leaders read it), `idea_added` gains `files` (how many).
4. **Who, then what, then on what** (§182.13, the owner's second note): once a party is taken (`@Game design `), the list
   goes on at once with that party's second step, filtered by what is typed after it:
   - **What it can do**: its goal types (`mapData` goals' `types`, spec 59 §4.5: the most used first), each its sign and
     name (*New mechanic*, *Balance pass*). Taking one makes the goal that type: a chip *◆ New mechanic ×* on the field,
     `type` sent with `ideas.add` (as the phone sends it); one type at most, never a word in the text.
   - **What it already has**: the parts of its map (Design's screens, System's parts for Tech, the game's loops' steps and
     currencies for Game design; any map that stamps `data-pick-*`), the same `{map, id, name}` picking takes (spec 102
     §6): taking one adds it to the goal's marks, a chip as a picked part's.
   - At the first `@`, a word that names no party but a type (*@mech*) offers *New mechanic · Game design*: taking it takes
     the party and the type together. Backspace on an empty second step goes back to the parties. Nothing of it is needed:
     Enter on the text alone sends as today.
   - The parts come from `ideas.pickables {party, q}` (new, `gui/`): the same ids the maps stamp, ≤ 30.

## 12. Part L: the crowned ork is Orkboard's mark

1. **The mark is the Orkmaster's crowned head** (§91, `orkui/races/peon-crown@2x.png`, 48 × 44), scaled by whole numbers
   only (`orkboard/design/mark.py`, Pillow, nearest): `design-system/logo/orkboard/` holds `mark.svg` (one `rect` a pixel,
   `shape-rendering="crispEdges"`, `<title>Orkboard</title>`), `favicon.ico` (32 and 64), `icon-192.png`,
   `icon-512.png`, `apple-touch-icon.png` (180; the phone's on the office's canvas, `tokens.json`'s value), `icon-256.png`
   (transparent). `python -m orkboard.design.mark` makes them again.
2. Served by the brand (`brand.name()`): Orkboard's favicon, the phone's icons, the Mac app's icon, onboarding's mark;
   Orkline, which runs these modules, keeps its ork mark (`design-system/logo/` as it is). `vscode/media/icon.png` is the
   256. `NOTICE` names the crowned mark.

## 13. Part M: New goal's frame

1. The New goal card (`.hand-plus`) is drawn in orkUI's pieces, nothing of its own: a double frame in `--ork-action`
   (`--ork-double`), the notch (`--ork-notch`), pixel corner brackets as orkUI's `.ork-picked::after`, inside a fine 45°
   hatch of the action colour (`color-mix` with `transparent`, about 12 %), its **+** a large pixel glyph. On hover a light
   band crosses it once in six steps. To be offered to orkUI as `.ork-deck.is-main` at its next copy.
2. **Never under another card**: it is not in the first lane's fan any more; it lies at the hand's left end, whole, the
   first lane's cards fanned to its right.

## 14. Part N: the game's loops

1. `loop.json` gains `version: 2`:
   - `loops`: one to three, at most one each `span` (`core`: seconds, `session`: minutes, `meta`: days and weeks), each
     `{id, span, name, line, feeds}` (`feeds`: the span it feeds, "" for meta) with `steps`: three to six `{id, name, line,
     feel, intensity, gives, takes, rests_on}`. `feel` one of MDA's eight (`sensation`, `fantasy`, `narrative`,
     `challenge`, `fellowship`, `discovery`, `expression`, `submission`), `intensity` 1–5, `gives` / `takes` currency ids.
   - `currencies`: zero to four `{id, name, kind, line}` (`kind`: `soft`, `hard`, `energy`, `progress`, `social`, `time`).
   - `hooks`: zero to three `{when: "D1" | "D7" | "D30", line}`: why a player comes back.
   - A version 1 file (`cards`) reads as one core loop of its cards (no feel, intensity 3).
2. **What the loop says** (`loop.findings(data)`, by code, no call): a currency nothing takes (*Gold is only earned: it
   will pile up*), one nothing gives, a loop no step of which gives anything (*The core loop rewards nothing*), a span
   nothing feeds (*Nothing feeds the meta loop*), a loop whose intensities are all one (*The session loop's feeling is
   flat*).
3. The leader's proposal (`core/idea_loop.loop_prompt`) asks for version 2 (the same call, its output bounded by the
   limits above); `ideas.loop_propose {again: true}` proposes again on the person's press (*Propose again*), the person's
   own edits kept aside in `loop.json`'s `was`.
4. The map (`table/loopmap.js`): the loops as rings one in another (core inside, meta outside), each step a small card on
   its ring (name; its line, feel and intensity when pressed), a pixel dot going round the core ring while any task of the
   party runs (G); at the right **the economy**: each currency, what gives it → it → what takes it; under the rings **the
   feeling**: a stepped line of the session loop's intensities, each point its feel's word; above, **what the loop says**,
   one alert line each. Under 640 px: the loops as lists, the economy and the feeling under them.
5. The person edits a step's name, line, feel and intensity in place, and a currency's name (`ideas.loop_set` takes
   version 2).

## 15. Order and tests

A first (it blocks every goal), then B; the rest in any order. Each part keeps the critical tests green
(`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and its modules' tests; A, E, K, L
and N add their engine tests; the browser tests of the faces they change are run where they exist.
