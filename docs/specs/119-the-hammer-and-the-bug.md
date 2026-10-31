# 119. The hammer and the bug: Fix Orkboard from the phone

Decision §197. The owner, 31 October: *a tool that fixes the system itself: it takes the logs of the last hours, starts a new
Claude session on the computer and says "fix it"; Claude opens in Orkboard's repository, fixes it and pushes; the computer then
offers to update, and the restart keeps the phone's link, so from work I press Fix, then Update and restart, and go on with the
fixed Orkboard.* And: *a full Claude, not the limited agents: the code that can fix itself, with the internet and the logs; one
that shows up in my Claude app as a Remote Control session.* And of the look: *the hammer squashes the bug.* **Builds:** Claude
(the cheaper model builds, the spec's author reviews) · **Review:** full · P1. After spec 107 (Save logs), spec 112 (the bug at
the end of the tabs' row), spec 117 (the phone's rows at the foot of the crown's menu).

**What it is, and is not:** the bug at the end of the tabs' row gains **Fix it**: Orkboard puts the person's line and the logs
since it last started in a fresh git worktree of **its own checkout**, and starts **Claude Code's Remote Control** there (a full
Claude Code, `--permission-mode auto`, the internet, git), named *Fix Orkboard*; the session appears in the person's Claude app,
where they say *go* and watch it. Claude fixes, runs the critical tests and pushes to `main`. Orkboard sees `main` move and the
bug turns into **Update and restart**; the restart is the one updates already make (the phone comes back by itself), checked
first, and rolled back when the new code does not start. Not: a party, a goal or a task on the Board (this is Orkboard's own
code, not the project's); one of the Board's limited agents (`--allowedTools`); something an installed copy (brew, pipx, uv)
offers: **only a git checkout of Orkboard on `main`, with `claude` on the PATH**, gets Fix it (the person who can push its
code); an automatic restart (the person presses Update and restart: the hand decides); a cloud session (§7, later).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. orkUI: the hammer** | the icon `hammer` (14 x 14) and the sign `bug-squashed` | repository orkCraft/orkUI, then copied here. **Until it is copied** the button wears what orkUI has (§4.3) |
| **B. The fix, faceless** | the checkout, the worktree, the brief, the launch, `main` moved, the update checked and rolled back | new `core/repair.py`; `tests/test_repair.py` |
| **C. The host** | the commands, the snapshot's `repair`, the phone's allowlist, the guarded restart | new `gui/repair.py`, `gui/board_host.py`, `realm/lexicon.py`; `tests/test_repair.py`, `tests/test_board_alone.py` |
| **D. The face** | the bug's panel and its four states on the desktop; *Fix Orkboard* in the phone's rows | `js/hand/logsbtn.js`, `js/table/table.css`, `js/hand/upphone.js` (and its CSS); `tests/test_repair_browser.py` |

## 1. The words

- The panel: *What went wrong? (optional)* (as today), **Fix it** (primary, only when `repair.can`), **Save logs** (quiet; as today
  the primary when Fix it is not offered). Under Fix it, one line: *Starts Claude Code on {Orkboard}'s own code with this and the
  logs; you say go in the Claude app.*
- The button's `title` / `aria-label` by state: *Save the logs or fix {Orkboard}* (idle, can) · *Save the logs* (idle, cannot) ·
  *Claude is fixing {Orkboard}* (working) · *The fix is in: update and restart* (ready) · *The fix did not come in* (failed).
- Working, the panel says: *Claude is fixing it in the Claude app, session **Fix Orkboard**.* and *Started {time}.*, a quiet
  **Stop the fix**.
- Ready: *The fix is in: {subject of the newest commit}* (and *and {n − 1} more* when more came), **Update and restart**
  (primary), *What runs now stops, and the tasks cut off start again by themselves. The phone comes back by itself.*
- Failed: the error as it is (`repair.error`), **Try again** (it starts a new fix with the same line) and **Save logs**.
- Toasts (the host's, through `town.toast`): *Claude Code started on {Orkboard}'s code: open Fix Orkboard in the Claude app* ·
  *{Orkboard} did not start on the fix: it went back to {short sha}* (after a rollback, §5.4).
- `{Orkboard}` is `brand.name()` on the host, `PRODUCT` on the page: never a fixed name.
- The glossary (`realm/lexicon.py` `TERMS`): **fix**: *Claude Code started on Orkboard's own code with the logs, to fix it and push
  to main*.

## 2. B: the fix, faceless (`core/repair.py`)

No face, no `gui/` import (`tests/test_architecture.py`). Every git or process call takes `run=subprocess.run` (and `popen`) so
the tests pass fakes or a real temporary repository.

### 2.1 Can it

`checkout() -> Path | None`: the git checkout this copy runs from, when `core.updates.method().kind == "git"` (its `cwd`),
else None. `can() -> tuple[bool, str]`: True when there is a checkout, its branch is `main` (`git -C root rev-parse
--abbrev-ref HEAD`), it has a remote `origin`, and `shutil.which("claude")` finds Claude Code; else False and why, in plain
words (*{Orkboard} was not installed from git*, *the checkout is on {branch}, not main*, *Claude Code is not on the PATH*).
Read once per minute at most (cached with its time).

### 2.2 The place

`repair_dir()` is `~/.orkcraft/repair/` (the state folder's name stays Orkline's: CLAUDE.md). One fix at a time, in **one
fixed folder** (Claude Code asks once whether to trust a folder, so the folder never changes):

- `worktree/`: `git -C root fetch origin main`; an older `worktree/` is removed (`git worktree remove --force`, then `git
  worktree prune`); then `git -C root worktree add --detach <repair_dir>/worktree origin/main`.
- `worktree/CLAUDE.local.md`: the brief (§2.3). Claude Code reads it by itself, so the session knows its task before *go*.
- `worktree/.orkcraft-repair/logs/`: the logs, unzipped from `gui/logs_save.pack` (the host hands the bytes in; core never
  imports gui).
- Both are kept out of git: `CLAUDE.local.md` and `.orkcraft-repair/` are appended (once) to
  `$(git rev-parse --git-common-dir)/info/exclude`.
- `state.json`: `{"started_at", "base" (origin/main's sha when it started), "said", "pid"}`, written atomically.
- `claude.log`: the launched process's output.

### 2.3 The brief (`CLAUDE.local.md`)

Plain English, made by `brief(said, base, product)`:

    # Fix {Orkboard}

    The person pressed Fix in {Orkboard} and wrote: "{said or: nothing; read the logs}".
    The logs since {Orkboard} last started are in `.orkcraft-repair/logs/` (about.json, app.log, crashes/, page.json, the
    Board's analytics). You are in a git worktree of {Orkboard}'s own repository at origin/main ({base}).

    1. Find the cause in the logs and the code; say it in a sentence before you change anything.
    2. Fix it the smallest way that fixes it, following CLAUDE.md, with a test that fails without the fix.
    3. Run the critical tests: `python -m pytest -q tests/test_architecture.py tests/test_board_alone.py tests/test_updates.py`
       and the test files of the modules you touched. Never skip or delete a test to make it pass.
    4. Commit (a message that says what broke and why), then `git push origin HEAD:main`. If main moved meanwhile:
       `git pull --rebase origin main`, test again, push.
    5. Say in the session what you fixed. {Orkboard} sees main move and offers Update and restart; the person presses it.

    If you cannot find or fix it, say so in the session and push nothing.

### 2.4 The launch

`start(said, logs_zip, now, run, popen) -> dict` makes §2.2 and starts, **detached** (`start_new_session=True`, stdin
`/dev/null`, stdout and stderr to `claude.log`, cwd the worktree), the machine setting `repair_command` (a list; default
`["claude", "remote-control", "--name", "Fix Orkboard", "--permission-mode", "auto"]`), so the session outlives
Orkboard's restart and the person can follow it in the Claude app. A fix already running (its pid alive) is stopped first
(`stop()`). Returns the state. A failure to start raises `RepairError` with the cause; so does a process that exits within
3 s (the end of `claude.log`, and: *Run `claude remote-control` once in {repair_dir}/worktree to answer its questions, then
Try again* — the first Remote Control run on a computer asks to enable it and to trust the folder).

`stop()`: SIGTERM to the process group of the state's pid (then SIGKILL after 5 s), the state's `pid` set to 0. The
worktree stays (the person may want what Claude left).

### 2.5 Main moved

`landed(base, run) -> list[dict]`: `git -C root fetch origin main` then `git -C root log --format=%H%x09%s
HEAD..origin/main` → `[{"sha", "subject"}]`, newest first (empty when main has not moved past this copy's HEAD). It is asked
only while a fix is running (the host's clock, every 30 s; never on the snapshot path).

### 2.6 The update, checked

`update(run) -> Result` (the updates' `Result`): `old = HEAD`; refuses when the checkout has changes (the updates' own
`_dirty` wording); runs the git method's steps (`core.updates.method().steps`: `git pull --ff-only`, then `uv pip install -e`
when uv is there). Then **checks the new code before anything restarts** with the same Python the restart will use: `python -c
"import orkboard.gui.board_host, orkboard.gui.server"` and `python -m orkboard --version` (timeout 60 s each). When a step or the
check fails: `git -C root reset --keep <old>` and the install step again, so the running code and the checkout agree, and
`Result(False, output)`. Never raises. The version does not have to grow (unlike `updates.install`).

`remember_good(old)` / `rolled_back()`: `repair_dir()/last-good.json` keeps the sha the restart came from, for §5.4.

## 3. C: the host

### 3.1 Commands (`gui/repair.py` `Repair(host)`, as `gui/updates.py` is built)

    repair.start   {"said"?, "page"?}  → the snapshot's repair   (the logs packed: logs_save.pack(host, 1, said, page=page))
    repair.stop    {}                  → the snapshot's repair
    repair.update  {}                  → the snapshot's repair   (only when ready; on a thread, as update.install)

`repair.start` refuses (a `RepairError`, said as it is) when `can()` is False. `repair.update` runs `core.repair.update` on a
thread; on success it `remember_good(old)`, toasts, sets `host.updates.restart_wanted = True` and calls `host.updates.quit()`:
the restart `gui/updates.py` already makes (`core_updates.RESTART`, `board_host.main`). On failure the state is `failed` with
the output.

### 3.2 The snapshot

`snapshot()["repair"]`, on the host's snapshot beside `update` (and the project-less one):

    {"can": bool, "why": str, "state": "idle" | "working" | "ready" | "updating" | "failed",
     "started_at": float | None, "landed": [{"sha", "subject"}], "error": str}

`working`: a fix's process runs and nothing landed; `ready`: `landed` is not empty (whether or not the process still runs);
`updating`: `repair.update` runs; `failed`: the start, the update or its check failed. The state is read from `state.json` when
Orkboard opens, so a fix started before a restart is still followed; after a restart on the fix (`HEAD` is the newest landed
sha) the state is `idle` and `state.json` is removed (the worktree stays until the next fix).

### 3.3 The phone (an exception to spec 37 §8, decisions §197.4)

`BoardPhone.COMMANDS` gains `repair.start`, `repair.stop` and `repair.update`; the phone's snapshot keeps `repair` (it is not in
`COMPUTER_ONLY`). The phone still edits no file and runs no git itself: it asks the computer to start Claude Code, which the person
then tells *go* in their own Claude app.

### 3.4 The guarded restart (`board_host.main`)

- Before `core_updates.restart(...)`, when `last-good.json` exists, the environment of the new process gets
  `ORKCRAFT_REPAIRED=<old sha>`.
- In `main`, when `ORKCRAFT_REPAIRED` is set and `run(...)` raises before it returns (the window or the server did not come up):
  `git reset --keep <old sha>`, the install step, the variable removed, `last-good.json` kept with `"rolled_back": true`, and
  `core_updates.restart` with the same arguments: the old code opens again on the same port, so the phone comes back. On that
  start the host toasts §1's rollback words once and the repair state is `failed` (*{Orkboard} did not start on the fix: it went
  back to {short sha}*).
- When `run` comes up (the server is serving), `last-good.json` is removed.

## 4. D: the face

### 4.1 The desktop: the bug and its panel (`js/hand/logsbtn.js`)

The same button at the end of the tabs' row. Its picture by `town.repair.state` (§4.3 for the pictures until orkUI's are
copied); its panel by state, §1's words:

- `idle`: the line, **Fix it** (when `can`) and **Save logs**. Enter presses the panel's primary. Fix it sends
  `repair.start {said, page}` (the page's own `page` as `saveLogs` sends it), closes the panel and the line.
- `working`: the words, **Stop the fix** (`repair.stop`).
- `ready`: the newest subject, **Update and restart** (`repair.update`).
- `updating`: *Updating…* and nothing to press.
- `failed`: the error, **Try again** (`repair.start` with the line last sent) and **Save logs**.

The button carries `is-working`, `is-ready` or `is-failed`; ready is the one state in a colour (orkUI's signal, the token the
update's own notice uses), so the eye finds it; the others are the ink.

### 4.2 The phone (`js/hand/upphone.js`)

The paired phone's rows at the foot of the crown's menu gain, above *Notifications*, one row **Fix {Orkboard}** whose state line
is §1's title words; a tap opens the same panel's content in the menu (the line, Fix it; or Stop the fix; or Update and
restart; or the error and Try again). Save logs is not on the phone (a phone saves nothing on the computer, as today). Only when
`repair.can`.

### 4.3 The pictures

- With orkUI's `hammer` (A): idle the bug with the hammer laid over its lower right where the glass is today; working the hammer
  raised and lowered (two frames, 600 ms, `steps(1)`); ready the sign `bug-squashed` with the hammer down, in the signal; failed
  the bug whole and the hammer aside, with `cross`. Under `prefers-reduced-motion` the hammer stays raised while it works.
- **Until A is copied** (`Icon` knows no `hammer`): idle the bug with `search` as today; working the bug with the sign `work`;
  ready the sign `check` in the signal; failed the bug with `cross`. The switch is one map in `logsbtn.js`.

## 5. A: orkUI (later, in orkCraft/orkUI)

- `icons/src/hammer.svg`: a 14 x 14 pixel hammer in pixelarticons' grid and stroke, its head to the upper left; in `icons.svg`.
- `signs/bug-squashed.svg` (and `big/`, `-light`): the beetle of `bug`, flattened to half its height, its legs splayed.
- The gallery, the READMEs, the version. Orkboard copies it (`python -m orkboard.design.orkui <orkUI>`) and switches §4.3's map.

## 6. Order and tests

- B and C first (one builder), D beside them (another), on the snapshot's contract of §3.2. A when orkUI is reachable.
- `tests/test_repair.py`: `can()` for a git checkout on main with and without `claude`, on another branch, for a non-git copy;
  `start` in a real temporary repository with an `origin` (a bare repository): the worktree at origin/main, the brief, the logs,
  the exclude lines, the state, the command started detached (a fake `popen`), an older worktree removed; `stop`; `landed` after
  a commit pushed to the bare origin; `update`: fast-forwarded; refused on a dirty checkout; the check failing → reset to the
  old sha; the host's commands and snapshot states; the phone's allowlist; `main`'s rollback with a `run` that raises and a fake
  `restart`.
- `tests/test_board_alone.py`: the snapshot's key set gains `repair`; the phone's commands gain the three.
- `tests/test_repair_browser.py` (Playwright, as the other browser tests): each state's panel and words; Fix it sends
  `repair.start` with the line; a non-git host shows Save logs alone; the phone's row.
- Critical: `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`, `tests/test_repair.py`.

## 7. Later

- **A cloud session** when the computer cannot (`claude --cloud "…"` from the checkout, with the logs scrubbed as crash reports
  are, never a person's paths or prompts): only if the local one proves not enough.

## As built

**Part B.** `core/repair.py` (no `gui/` import; every call takes `run` / `popen`): `checkout()` (the git method's `cwd`), `can(run, which, way, now, fresh)` (a git checkout, `main`, an `origin`, and the first word of the machine's `repair_command` on the PATH;
the answer cached a minute, `forget_can()` clears it), `repair_dir()` · `worktree_dir()`, `brief(said, base, product)` (§2.3 verbatim; the line cut at 4000 characters, the whole of it is in the logs'
`on-screen.txt`), `start(said, logs_zip, now, run, popen, cmd, way, settle)`: stops a fix that runs, fetches `origin main`, removes an older `worktree/` (`git worktree remove --force`, the folder if it was no
worktree, `prune`), `worktree add --detach … origin/main`, appends `CLAUDE.local.md` and `.orkcraft-repair/` once to `<git-common-dir>/info/exclude`, writes the brief, unzips the logs (a name that leaves the folder is dropped, a bad zip leaves a
`README.txt`), starts the command with `start_new_session=True`, stdin `/dev/null`, stdout and stderr in `claude.log`, waits `settle` (3 s) and writes `state.json` atomically (`{"started_at", "base", "said", "pid"}`); a process that exits in
that time raises `RepairError` with the end of `claude.log` and the *Run `claude remote-control` once in …* line. `alive()` · `stop()` (SIGTERM to the process group, SIGKILL after 5 s, `pid` 0, the worktree stays; a child that ended is reaped
first, or it would answer `kill 0` as a zombie for as long as Orkboard runs). `landed(base)` and `applied(base)` (§2.5). `update(run, way)` (§2.6): `_dirty`'s refusal, the method's steps, then `python -c "import orkboard.gui.board_host,
orkboard.gui.server"` and `python -m <profile entry> --version` with `way.python or sys.executable` (60 s each); a failed step or check runs `rollback(old)` (`git reset --keep <old>` and the steps after the pull again) and says it in the result;
never raises. `last-good.json` is `remember_good(old)` · `pending(old)` · `mark_rolled_back(old)` · `rolled_back()` · `told()` · `came_up()` · `guard_environment()`; `fall_back(old, why, argv)` is the guarded restart's rollback.
`settings.py`: `repair_command` on `MachineSettings` (default `settings.REPAIR_COMMAND`, `clean_repair_command` for a broken value, in `to_dict` / `from_dict`).

**Part C.** `gui/repair.py` `Repair(host, engine=core.repair)`: `repair.start` (refuses with `can()`'s reason; packs the logs with `logs_save.pack(host, 1, said, page=page)` on the host's loop, then `core.start` on a thread; the state is
`working` at once, `failed` with the error as it is when the start fails), `repair.stop`, `repair.update` (`core.update` on a thread; on success `remember_good(head)`, a toast, `host.updates.restart_wanted = True`, `host.updates.quit()`; on failure
`failed` with the output and a red toast). `snapshot()` is §3.2's; `tick(now)` asks `landed()` every 30 s on a thread, only while a fix runs (and, with something landed, only while its process lives). A fix's state is read from `state.json` when Orkboard
opens; a copy already on the fix (`applied`) clears it. `board_host.py`: `self.repair` beside `self.updates`, its commands, `"repair"` in the one `snapshot()` (the project-less snapshot is the same return), the three commands in `BoardPhone.COMMANDS`
(`repair` is not in `COMPUTER_ONLY`), `repair.RepairError` among the caught errors, `self.repair.tick(now)` beside the updates', `run()` calls `core_repair.came_up()` once the server serves, and `main()`: the restart after an update sets
`ORKCRAFT_REPAIRED` from a fresh `last-good.json`; a `run` that raises while the variable names the sha `last-good.json` still holds goes to `core_repair.fall_back` (reset, install step, the variable removed, `rolled_back: true`, the same
arguments restarted). The next start says §1's rollback words once and the state is `failed`. `realm/lexicon.py`: the term `fix`.
Tests: `tests/test_repair.py` (real temporary repositories with a bare `origin`, a fake `popen`, the state folder the test's own; the host with a fake engine); `tests/test_board_alone.py` and `tests/test_mobile.py` gain the snapshot key and the phone's three commands.

*Departures and choices.* (1) **`fix` was already a term** (Orkline's leftover: *a change to Orkline's source, sent as a pull request*, used by no code); its comment now says §1's meaning, its word stays *Fix* / *Fixes*, rather than a second
key that would shadow it. (2) **`python -m orkboard --version`** is `python -m orkboard.gui.board_host --version` (the profile's `entry`): the package has no `__main__`. (3) `can()` looks for the first word of `repair_command`, not a fixed `claude`,
so a machine that changed the command is not told Claude Code is missing. (4) `landed(base)` leaves out what `main` already had when the fix started (`origin/main ^HEAD ^base`), or a checkout behind `main` would show *ready* at once; with `base` empty
or unknown it is `HEAD..origin/main`. (5) Commands run on the page's loop, so `repair.start` answers at once and does its fetch, worktree and 3-second wait on a thread; a process that ended with nothing landed turns the bug `failed` (*Claude Code stopped
and nothing came in to main…*), which §3.2 leaves unsaid. (6) `last-good.json` older than ten minutes is not the restart that just happened, and carries `told` so the rollback is toasted once. (7) `board_host.py` was already over 600 lines
(697); this adds about 30, the rollback itself lives in `core/repair.py`.

**Part D.** `js/hand/logsbtn.js` draws the bug and its panel by `town.repair.state` (a missing `repair` reads as `{can: false, state: "idle"}`): `repairOf()` reads the snapshot, `repairTitle()` has §1's title words (the button's `title`, `aria-label` and the panel's), `RepairBody` is the
panel's content (idle: the line, **Fix it** with its one line, **Save logs**, Save logs alone and primary when `can` is false; working: the words, *Started {time}.*, **Stop the fix**; ready: *The fix is in: {newest subject}* with *and {n − 1} more*,
**Update and restart** in the primary, the restart line; updating: *Updating…*; failed: the error in a `pre`, **Try again** with the line last sent, **Save logs**). Enter in the line presses the primary. The pictures are the one map `PICTURES` (§4.3, until orkUI's
`hammer` and `bug-squashed` are copied: idle bug + icon `search`, working and updating bug + sign `work`, ready sign `check`, failed bug + sign `cross`); the button wears `is-working` (updating too), `is-ready` or `is-failed` and carries `data-repair-state`.
`table.css`: ready is `--ork-alert`, the token the update's own notice wears (`.update-bar.is-critical`); working and failed are the ink; working steps its sign (`table-logs-work`, whole steps, none under `prefers-reduced-motion`). The commands answer the fix as the
snapshot will say it and the page shows that at once (`adopt`); the next snapshot says the same. `js/hand/upphone.js`: the row **Fix {Orkboard}** above Notifications, only when `repair.can`, its line the title words, a tap opens `RepairBody` in the menu (no Save logs; a
second tap shuts it; Fix it, Stop and Try again shut it, Update and restart leaves *Updating…* showing); `upmenu.css` has its look. Not in the spec, said here: *Updating {Orkboard} with the fix* is the updating state's title; the session's name in the working words is
`Fix {PRODUCT}`. Tests: `tests/test_repair_browser.py` (16, Chromium against `TableHost` with `repair` in its snapshot).
