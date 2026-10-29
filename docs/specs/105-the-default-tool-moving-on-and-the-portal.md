# 105. The default tool, moving on, going on paid, and the portal to main

Decisions §177 (1–9); the mockup `docs/mockups/portals/` (v2: the frame on the default potion, its slide, the card *Go on
paid?*, the round purple portal, sealed, on the phone). Builds on spec 104 (the mana in the hand, the discard on the table).

## 0. What is there today (the engine)

- A task's tool is resolved at run time by `IdeaRunner.tool_of(slug, task)` (`core/idea_runner.py` ~396): the seat's tool
  (`party.tools[role]`), else the party's (`party.tool`), else the machine's Main tool (`settings.main_tool()`). A keeper's
  step uses `IdeaKeeper.tool_now()` (the leader's seat tool, else the Main tool); an operation's step `tiers.tool_of(step)`
  (`""`/`"main"` the Main tool). **An empty tool means *follow the Main tool*; any id was set on purpose (pinned).**
- The runner holds a task while its tool's window is spent or at the reserve (`_advance` ~320–345: `status.reset_of(…,
  NEARLY)`, `idea_target.gate`, `_hold`); a limit hit mid-run raises `Held(reset)` (`core/idea_session.py`). Nothing moves
  the work to another tool.
- `town.limits` (`gui/ideas_limits.py`): `[{provider, name, left, rows:[{window, left, reset}]}]`; billing is
  `machine.tools[t].billing` (`"subscription"|"api"`), `treasury.subscriptions()`.
- Merge to main: `ideas.gate_merge` (`gui/ideas_gate.py`, `realm/idea_gate.py` `merge`) merges dev whole. A goal has no
  branch: each task lands on dev rebased (`IdeaGit.land`), its plan keeps `commit` and `subjects`; `realm/commit_goal.py`
  recovers `{sha: {goal, task}}`.

## 1. Part A (orkUI 0.18.0): the portal and `--ork-portal`

In orkUI: `--ork-portal`, `--ork-portal-hi` (a violet clearly apart from `--ork-elem-void`), `.ork-portal` (round, a ring of
stones, a three-armed swirl turning in quarter steps, sparks; `.is-taking`, `.is-sealed`, `.is-new`, `.small`). Copied here.

## 2. Part B (engine): the tool now, and moving on

1. **The order**: the potions' order is the machine's tools in `machine.tools`' order, enabled ones only (the order
   `town.limits` already has). One function `settings.tool_order(machine)` says it; `town.limits` keeps it.
2. **The tool now** (`realm/tool_now.py`, no face): `now(machine, limits, at, paid_until=None) -> {main, now, until,
   moved_from}`: the Main tool while it has room (not spent, not at its reserve: the same tests the runner's hold uses,
   `status.reset_of(…, NEARLY)` and the reserve), else **the next tool in the order that has room and is billed by
   subscription**, else, while a yes to go on paid holds (`paid_until` in the future), the first tool billed by its API;
   else `now = None` and `until` the soonest reset among the subscriptions.
3. **Who follows it**: every resolution that today falls to the Main tool falls to *the tool now* instead:
   `IdeaRunner.tool_of`'s last step, `IdeaKeeper.tool_now`'s last step, `tiers.tool_of` for `""`/`"main"`. A seat's or a
   party's own tool (pinned) is never moved: its work holds as today and its hold says what it waits for.
4. **Between tasks, never inside one**: the tool is resolved when a task (or step) starts, as today; a run that hits its
   limit mid-run holds (`Held`) and its next start resolves again, on the tool now.
5. **Said once**: when `now` changes from the Main tool to another (or back), the host publishes `bus.TOOL_MOVED`
   `{from, to, until}` and keeps it in the snapshot as `town.mana = {main, now, until, moved: {from, to, until, at} | null}`;
   the Orkmaster's line is *Claude Code is out until Thu 18:00: the work goes on with Codex* (and back: *Claude Code is back:
   the work goes on with it*). An event in the event log too.

## 3. Part C (engine + the hand): going on paid

1. When `now` is None and an enabled tool is billed by its API, the Orkmaster's row `paid` is in the Needs you rows (a
   goal-free row, `realm/board_rows.py` as `project_q`): `{kind: "paid", tool, name, until, usd_task}` (`usd_task` the
   estimate the seats already show, `ideas_roles` `usd_task`, for that tool; none if unknown, and the words say *its cost is
   not known yet*).
2. Answers: `ideas.paid {yes: true}` keeps `paid_until = until` in the Board's state (`.orkcraft/`) and the work goes on
   with that tool; `ideas.paid {yes: false}` keeps `paid_wait = until` so the row is not asked again before that reset.
   Both end at the reset. **Nothing is run by a tool billed by its API without that yes** (B.2 picks it only while
   `paid_until` holds).
3. The card (`hand/paidcard.js`, a way `paid`): under the first lane, the Orkmaster's crowned head, its name *Go on paid?*,
   the window's sign the coins (orkUI's, or the alert), the gem its price (*$0.40*), the body *Every subscription is out
   until Thu 18:00. Go on with Claude Code paid by its API, about $0.40 a task, or wait.*, the answers **Go on, paid** and
   **Wait for Thu 18:00**, the foot *Holds until the next reset*.

## 4. Part D (the face): the frame and the line

1. `hand/mana.js`: the potion of **the tool the open tab's work goes to** carries the frame (a hotbar's chosen slot: orkUI's
   ink and edge, its corner notch; every potion keeps a transparent border the same width so nothing shifts). On the
   project's tab it is `town.mana.now` (else the Main tool); on a party's tab its pinned tool when it has one (`g.tool`),
   else `town.mana.now`. The frame slides between places (`--ork-motion-base`, off under reduced motion). Its words add
   *, the default* to that potion's label.
2. While going on paid holds, the paid tool shows as a slot after the potions: its mark, orkUI's coins, *API* and the price
   under it; the frame on it.
3. The Orkmaster's line (`table/notice.js`): when `town.mana.moved` is newer than the person last saw, a strip on the table
   under the pane's title with the crowned head and the line (body face), dismissed by a press or the next move; gone after
   a day.

## 5. Part E (engine): a goal to main on its own

1. `realm/goal_main.py` (no face): `plan(repo, state_dir, slug) -> {goals: [slug…], commits: [sha…], sealed: reason|None}`:
   the goal's tasks' ranges on dev (`commit~n..commit`, `n = len(subjects)`, from the plans, landing order), and **the goals
   it stands on** that main lacks: its `depends_on`, and any goal whose landed task touched the same files earlier and is
   not in main. Already in main is decided by patch id (`git cherry main dev`), never by sha.
2. Sealed, with its reason in words: a task of the goal not landed (*Lobby is not done yet*), a goal it stands on not done
   (*Reconnect is not done yet*), a cherry-pick that would conflict (tried in a throwaway worktree: *Lobby does not apply
   to main cleanly: player.ts*), main moved outside Orkboard and not fetched.
3. `merge(repo, state_dir, slug, push=False)`: cherry-picks the plan's commits in order onto main in a `gate-main`
   worktree (the pattern `idea_gate.merge` uses), fast-forwards main, pushes when the gate pushes today; raises the goals'
   flags after it as `gate_merge` does.
4. `gui/ideas_gate.py`: `ideas.to_main_plan {idea}` and `ideas.to_main {idea}`; `ideas.gate` counts what waits by patch
   id so a goal sent alone is not counted again. `ideas.gate_merge` (dev whole) stays for a person's own commits.

## 6. Part F (the face): the portal

1. In the discard's view (`table/discard.js` `DiscardView`), each goal ready for main is a card; pressing one or starting
   to drag it opens **the portal** over the pile on the table's right (`table/portal.js`, `.ork-portal`), the pixel-face
   label *Main* over it and the line from `ideas.to_main_plan` (*Into main: Lobby, and Reconnect it stands on*).
2. A card held over it: `.is-taking`. Dropped or pressed into it (or the portal pressed while a card is chosen; Enter on
   the keyboard): `ideas.to_main {idea}`; the card goes into the portal (a short scale-and-fade, off under reduced motion)
   and leaves the discard's ready goals.
3. Sealed: `.is-sealed`, the reason under it in the danger colour; a press on it says the reason again and plays nothing.
4. The first time (a per-viewer convenience in `localStorage`, read in try/catch): `.is-new` and the line *Drag a goal done
   into the portal to send it to main* (on the phone *Tap the portal to send it to main*).
5. Esc or a press away closes the portal and lowers the chosen card. At the narrow width the portal opens over the pile at
   the lanes' end.

## 7. Order

A (orkUI) now; B with C (one engine builder: `tool_now`, the runner and keeper, the `paid` row and command) and E (another:
git) at once; D after B and A's copy; F after E and A's copy.

## 8. Tests

- `tests/test_tool_now.py`: the order; room, spent, reserve; subscription only; paid only while it holds; pinned seats and
  parties never moved; the runner's and keeper's resolution falling to the tool now; `TOOL_MOVED` once per change.
- `tests/test_paid.py`: the row when every subscription is dry and an API tool is on; none without an API tool; yes and
  wait until the reset.
- `tests/test_goal_main.py` (git in a temp repo): a goal's range, the goals it stands on, patch-id after a pick, sealed
  reasons (not landed, conflict), the merge onto main.
- Browser: the frame on the project's and a party's tab, its slide, the line; the paid card's answers; the portal's open,
  taking, sealed, first-time line, press and keyboard path, the phone.

## As built A

orkUI 0.18.0 (orkUI fd49708): `--ork-portal` `#b27bf6`, `--ork-portal-hi` `#d5a8ff` (CIE76 52.6 from the void element);
`.ork-portal` drawn in `box-shadow` pixels from `office/portal/portal.json` (`::before` the ring, panel, eye and sparks;
`::after` the swirl alone, turning in `steps(4)` over 6 s); `is-taking`, `is-sealed` (wins over taking), `is-new`, `small`;
a `<button class="ork-portal">` works too. Needs Chromium 111, Firefox 113, Safari 16.2.

## As built E (a goal to main on its own)

Built in `orkboard/realm/goal_main.py` (new, no face), `realm/idea_gate.py` (`cherry`, `waiting_by_patch`), `gui/ideas_gate.py` (`ideas.to_main_plan`, `ideas.to_main`, registered by `gate_commands` in
`gui/ideas.py`) and `realm/event_log.py` (`goal_to_main`). Tests: `tests/test_goal_main.py` (new, a real git repo), and the command set in `tests/test_gui_ideas.py`.

What it is, and what differs from §5 or is not said there:

- **Signatures take what the page knows.** `plan(repo, state_dir, slug, *, root=None, into="dev", main="")` and `merge(repo, state_dir, slug, push=False, *, root=None, into="dev", main="")`: `root` is where the Board's pages are
  (a goal's short title as the page names it, `ideas.ideas()`'s `short`, and its `depends_on`; without it a goal is named by its slug and stands on nothing), `into` is the branch results land in, `main` the default branch when empty.
  `plan` answers `{goals, commits, sealed, titles, files}` (`titles` is `{slug: short title}`, `files` the count the picks change); `goals` is the goal first, then what it stands on. `ideas.to_main_plan` adds `idea`, `into`, `main`.
  `merge` answers `{commit, goals, commits, files, note, pushed}` and raises `GoalRefused` (a `RuntimeError`, as the gate's `GateRefused`); the command turns it into the words of an `IdeasError`.
- **The goal's commits** are `commit_goal.index`'s (each task's `commit` and its `len(subjects)-1` ancestors) that `git cherry main dev` marks `+`, in dev's order, so the person's own commits and the Board's pages between them are never picked.
- **What it stands on**: its `depends_on`, deeply, and any goal with a pending commit **before** one of the goal's commits that changed a file the same (the first-touch of each file per goal, one `git log --name-only`), and so on through what those stand on.
  A goal main has already is left out (flag raised, or done with no pending commit). A goal the Board lost is nothing to stand on.
- **Sealed**, in this order: no gate (dev is main); a goal of the plan not done (*Lobby is not done yet*: no plan, or a task not dropped and not merged; the goal first, then what it stands on); nothing to send (*Lobby is in main already*,
  or *Lobby has nothing to send to main* for a goal of checks); main behind its origin (*main is behind origin/main: pull it first*: only what is fetched, `refs/remotes/origin/main`, is read); a pick that does not apply
  (*Lobby does not apply to main cleanly: player.ts*, the goal that owns the commit that failed), tried in the `gate-main-try` worktree, detached at main, always removed. A pick that comes out empty (main has it under another patch) is skipped.
- **The merge** picks in `gate-main` (detached at main, `-c user.name=Orkline` as the gate; the author stays), then `IdeaGit._fast_forward` moves main (a checked-out main moves with `merge --ff-only` and is refused with its files when they
  are changed), pushes when `ideas.push` holds, as `gate_merge` does. Under the repository's lock; dev is not moved.
- **Flags**: after it, each goal of the plan that is done and has none, all of whose tasks' commits are in main **by patch id** (`goal_main.in_main`: `cherry`'s `-` or an ancestor), gets `gate`'s flag (`_flag_after_goal`).
- **The gate by patch id**: `ideas.gate` counts `waiting_by_patch` (`rev-list main..dev`, less what `git cherry` calls equal; the files of what is left). Where main is an ancestor of dev (nothing was picked) it is `waiting`'s answer with no `cherry`.
  `idea_gate.merge` (dev whole) takes the same list, so a dev fully picked says *Nothing in dev waits for main*.
- **Logged** as `goal_to_main` `{idea, goals, commits, files, pushed, into, main, device}` (the Today strip shows the flags it raises as it does for the gate).
- **Not done / to know**: merging dev whole after a goal went alone is a three-way merge of two histories that hold the same patches; it is clean where dev changed nothing later on those files, and may conflict where it did
  (the gate then says *merge main into dev first*). Dependencies of a different kind than `depends_on` and shared files (a person's own commit between two tasks that the goal needs) are found only by the trial's conflict.
  `ideas.to_main_plan` runs a trial worktree on every call (a few hundred ms on a small repository); Part F should ask once when the portal opens.

## As built B (engine: the tool now and moving on)

- `settings.tool_order(machine)` is the order (the enabled tools in `machine.tools`' order, which is the registry's: Claude Code, Antigravity, Codex, …); `town.limits` keeps its own sort (`harnesses.ids()`), the same order.
- `realm/tool_now.py` (no face): `now(machine, limits, at, paid_until=None, board=None) -> {main, now, until, moved_from}`. `limits` are **the quota readers' rows** (`sources.limits.Limit`, what `status.reset_of`
  reads), not `town.limits`' dicts. `board` is the Board's settings, **added to the spec's signature**: given, a tool at its reserve (`idea_target.reserve_held`) has no room either; without it only the windows
  count (`status.reset_of(…, NEARLY)`). `now` is the Main tool while it has room; else the next tool **after the Main tool in the order, round again**, that has room and is billed by subscription; else, while
  `paid_until` is in the future, the first tool in the order billed by its API; else None. `until` is when the Main tool is back (the latest of its windows' resets, else its reserve's) while the work is on
  another tool, and the soonest reset among the subscriptions while `now` is None; `moved_from` the Main tool while the work is elsewhere. A tool with no limits read has room; a Main tool billed by its API
  never runs dry (the person chose it). `tool_now.line(main, to, until, at)` is the Orkmaster's words (*Claude Code is out until Thu 18:00: the work goes on with Codex.*, *Claude Code is back: the work goes on
  with it.*; "" while every tool is out, the card asks instead); the time is `idea_target.when_words` (*18:00* today, else *Thu 18:00*, as the held tasks' lines say it).
- **Who follows it.** `IdeaRunner(follow=…)` and `IdeaKeeper(follow=…)` take a callable returning the tool now (the Board's `Ideas.follow`); `IdeaRunner.tool_of`'s and `IdeaKeeper.tool_now`'s last step is
  `follow() or Main tool` (an error or None: the Main tool, so a host that cannot say changes nothing). The runner's `pinned_tool(slug, task)` is the seat's, else the party's tool ("" follows); a pinned
  tool is never moved, and its window hold now says what it waits for (`held_why`: *Waits for Codex's limit until Thu 18:00: Codex is set for it on purpose, so the work does not move on.*; the page's `holdWords`
  says it, desktop and phone). `tiers.tool_of` and `tool_run.resolve` (`""`/`"main"`) have no host to ask, so they read `tool_now.following(main)`, the machine's tool now that `Orkboard.tick` keeps
  (`tool_now.keep`; the machine's, without a Board's yes to go on paid, and the reserve not counted). Resolved where a task or step starts, as ever; a run that hits its limit mid-run holds (`Held`) and its next start resolves again.
- **Said once** (`gui/ideas_mana.py`, a mixin of `Ideas`): `Ideas.mana_tick()` on the Board's clock compares the tool now with the last tick's and, on a change, publishes `bus.TOOL_MOVED {from, to, until}` on the
  **project's bus** (each open project is a Board with its own bus and its own yes to go on paid, so the one a person has open says it), keeps `moved` and logs `tool_moved` (`from`, `to`, `until`; `to` "" while every
  tool is out). The Main tool changed in Settings is no move; a Board that starts with its Main tool already out has moved. `town.mana = {main, now, until, moved}` is in `Ideas.snapshot` (and the no-project snapshot,
  nothing moved), next to `limits`: `until` an ISO local time while the work is on another tool, `moved = {from, to, until, at, line} | null` (`line` the Orkmaster's words, for part D). Not in the phone's snapshot.
- Where the spec's model was wrong: (1) the reserve is the **plan's** in the runner (`idea_target.gate` holds only a plan passed by itself), but the tool now is the machine's: with `board` given, Claude at its reserve
  moves a plan the person started by hand to the next tool too, where before it ran on Claude's reserve; (2) a step that says `main` has no host (`tiers`, `tool_run`), hence the kept read; (3) the keeper's call
  keeps the tool it ran on for its ledger line (`_tls.tool`, set in `_claude`), so a call that began on Claude and ended after the move is still booked to Claude.
- Tests: `tests/test_tool_now.py`; `tests/conftest.py` clears the kept read for every test; `tests/test_board_alone.py` knows `mana` in the snapshot.
- Changed since (decisions §177.10): `follow(reserve=)`: the runner asks with `reserve` True only for a plan the Board passed by itself
  (`passed_by: "auto"`, or `start_at: "night"`), the keeper always False, so the person's own work stays on the Main tool at its reserve.

## As built C (engine and the hand: going on paid)

- `realm/paid.py` (no face): `<state_dir>/paid.json` is `{"paid_until": epoch}` or `{"paid_wait": epoch}` (an answer replaces the other), each the reset the card named. `until(state_dir, at)` is what a yes holds
  until (None once the reset has come: it ended), `waiting(state_dir, at)` that a no has not ended; with no reset known an answer holds the five-hour window (`tool_now.PAID_HOLD_S`). `row(state_dir, machine, got, usd_task, at)`
  is `[]` or the goal-free row `{kind: "paid", tool, name, until, usd_task, text: "Go on paid?", blocks: true, priority: "high", at}` (`until` an ISO local time or None); it is asked when `now` is None, a tool turned on
  is billed by its API (`tool_now.api_tool`: the first in the order), no yes holds and no no waits. It is laid in Needs you by `gui/ideas_board.py` (`Ideas.paid_rows`, none in the demo), after the other goal-free
  rows. It is **not counted** in `needs_you`'s number (as `project_q`): the phone has no card for it, and a push for something it cannot answer would be a dead end.
- `usd_task` (`Ideas.usd_task_of(tool)`): the mean of the Board's last ten priced tasks that ended on that tool (`task.tool`), else the Grunt's `usd_task` the seats show (`ideas_roles._usd_task`); None while nothing is priced.
- `ideas.paid {yes: bool}` (`gui/ideas_mana.py`, in the command table, the phone may call it): refused (*Nothing asks to go on paid now*) while `now` is not None or no tool is billed by its API; else it keeps the answer
  (`paid.answer`, until `until`, the soonest reset), logs `paid_answered {tool, yes}`, ticks `mana_tick` (so a yes is `TOOL_MOVED` at once) and answers `{ok, tool, name, until}`. **Nothing is run by a tool billed by its API
  without the yes**: `tool_now.now` picks one only while `paid_until` holds, and the runner's `tool_of` is the Main tool (held by its window) until then.
- The card: `hand/paidcard.js` registers the way `paid` (`wayparts.js` loads it): the sign **alert** (orkUI has no coins sign among its 41), the Orkmaster's crowned head (`orkHead`), the name *Go on paid?*, the foot
  *Holds until the next reset*, the gem the price in dollars. The gem needed a hook the spec did not name: `way(kind, {cost})` (`hand/cost.js` `costOf`), because `price` would be turned into a share of the tool's
  window once a rate is learnt, and a tool billed by its API has none; with no `usd_task` there is no gem. Lifted: *Every subscription is out until Thu 18:00. Go on with Claude Code paid by its API, about $0.40 a
  task, or wait.* (*its cost is not known yet*; no time when no reset is known; a reset of today says its hour only), the answers **Go on, paid** (`ideas.paid {yes: true}`) and **Wait for Thu 18:00** (`{yes: false}`; *Wait*
  with no reset). Its stop is `arenawords.js` `paidStopsOf` (a goal-free stop, as `signInStopsOf`: no party, `laneOf` puts `paid` under the first lane with the whole goal's kinds), its words `paidWords` / `untilWords`.
  The phone draws no card for it yet.
- Tests: `tests/test_paid.py`, `tests/test_paid_card_browser.py` (the face, the lifted words, both answers, an unknown cost, no reset, the lane, at both widths).

## As built F (the portal)

Built in `gui/static/js/table/portal.js` and `portal.css` (new; the sheet is loaded with the table's, `frame/frame.js`), `table/discard.js` (`DiscardView` draws `ReadyCards`, `DiscardEnd` draws `Portal`). Tests: `tests/test_portal_browser.py` (new, 17 at the two
widths), and `tests/test_hand_desktop_browser.py`'s discard test now counts the ready cards. Screenshots with `PORTAL_SHOTS=<dir>`.

What it is, and what differs from §6 or is not said there:

- **Each goal ready for main is a card** (`ReadyCards`, `[data-portal-card]`): the pile's top card drawn the same (the goal's element and name, the check in its window, *Done*, *Ready for main*), `ork-leans`, a button with `aria-pressed`. It is the hand
  card's size on each width (144 x 202; at the narrow width 80 x 112, as the pile is), so `portal.css` copies the hand card's grid for the view (hand.css scopes it to the hand and the table's end). The cards do not wear `hand-done`: that class is the pile's (tests find the pile by it).
  The old rows of the ready goals (tick, element, name, type sign) are gone. **To main** (dev whole), *Done, not yet seen* and the line *Nothing reaches main without you.* are as they were.
- **Choosing**: `choose(slug)` by a press (`click`) or `dragstart` (HTML5 drag, desktop; the press path needs nothing else, so touch uses it). A card chosen wears orkUI's `ork-picked` brackets (the mockup's *taken*). Pressing the chosen card again only moves the focus to the portal
  (so Enter on it never un-chooses). The focus goes to the portal when a goal is chosen, by press or key.
- **The plan is asked once** when a goal is chosen (`ideas.to_main_plan {idea}`), kept in a signal until the portal closes; while it is asked the portal says *Checking Lobby…*, its aria-label *Checking what goes to main*, and is `aria-disabled` (a press waits for the plan, then plays or says the reason).
  A plan that failed (the host's error is toasted by `ask`) seals the portal with *What goes to main could not be checked*.
- **The line** (`lineOf`): *Into main: Lobby*; with goals it stands on, `, and ` + the others joined (`joined`: *A*, *A and B*, *A, B and C*) + ` it stands on`. Names are the plan's `titles`, the ready goal's title if it has none. The aria-label (`labelOf`) is *Send Lobby and Reconnect to main*, or *Sealed: <reason>*.
- **Where it lies**: first child of `.table-end` (the pile's place), the host `.portal-host` (line, the pixel-face label *Main*, orkUI's `<button class="ork-portal">`, the first-time line, the reason) right-aligned above the *Discard* label, wider than the pile by one gutter, growing upward. At the narrow
  width the portal is `small` (104 x 112; `useNarrow` on `(max-width: 759.98px)`), and, while it is open, the view keeps a column's width free at its right (`.table-body:has(.portal-host) .hand-discardview`), so the cards (80 px there) and the done list stay visible beside the portal
  and the pile instead of under them.
- **Playing**: a press on the portal, a drop on it, Enter or Space (it is a button) call `play()`: `ideas.to_main {idea}`; the host's error is toasted by `ask` and nothing else changes (the portal stays open for another try); `note`, when it has one, is a warning toast as `mergeGate`'s is.
  On success the card goes into the portal (`is-going`: scale to 0.2 and fade to the portal's centre over `--ork-motion-sure`, its travel set in `--dx`/`--dy`; off under reduced motion, where the card just leaves), then the portal closes and `refreshShell()` reads `ideas.gate`, which no longer lists the goals sent.
  A goal that leaves the ready goals for any reason closes the portal; so does closing the view.
- **Taking**: `dragenter`/`dragover` on the portal while a goal is chosen sets `is-taking` (a drop or `dragleave`/`dragend` takes it off); orkUI's `is-sealed` wins over it. A drop on a sealed portal says the reason and plays nothing.
- **Sealed**: `is-sealed`, the reason *Sealed: <reason>* under it in `--ork-danger` in a `role="status" aria-live="polite"` line; a press says it again (the line's text node is replaced, so a screen reader reads it again) and sends nothing. No first-time line over a sealed portal.
- **The first time**: `localStorage` `orkboard.portal.seen` (the page's `orkboard.` prefix), read and written in try/catch; it is written when the portal first opens, and a module flag keeps a device that keeps nothing to once a page load. While the portal stays open the portal shimmers (`is-new`) and says
  *Drag a goal done into the portal to send it to main*, at the narrow width *Tap the portal to send it to main*; closed and opened again, neither.
- **Esc and a press away**: while a goal is chosen, `Escape` (a listener on `document`, before the table's on `window`) closes the portal and `preventDefault`s so the view stays; a press (`pointerdown`, capture) outside the portal and the cards does the same. A listener that outlives its portal by a frame
  checks the choice first (an early version swallowed the next Esc, which goes back from the view). A second Esc goes back as before.
- **Not done / to know**: the drag's `is-taking` is tested on desktop only (a touch screen sends no HTML5 drag; its path is the press). The card's travel is not asserted in a test (reduced motion off or on, the end state is).
  `tests/test_architecture.py::test_orkboard_starts_alone` fails in this worktree for a reason outside this part: its subprocess imports `orkboard` through the editable install, which is the main checkout, and the main checkout holds other builders' not yet committed `realm/paid.py`, `realm/tool_now.py` and `gui/ideas_mana.py`.
