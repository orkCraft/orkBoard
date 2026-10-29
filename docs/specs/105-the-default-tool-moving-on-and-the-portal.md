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
