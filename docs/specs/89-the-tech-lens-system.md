# Spec 89 — The Tech lens's *System*: the project's parts as cards on the table, and what changed since your last look

The owner, 26 October (decisions §104, its phase 1): *you sit and do not understand what the system does.* The first of
§104's lenses, the one read from the code with no model: the Architect's **System**, the project's parts and what each
uses, laid out as the field's cards on the table, playing what landed since the person's last look, each change signed
by the goal that made it. It is measured before phase 2 (§104.14): *can the owner tell the day in a minute, and did they
see what an agent decided alone.* **Builds:** Claude · **Review:** full · P1. **After spec 88's part A** (its
`realm/commit_goal.py`); **A first, then B**.

**What it is, and is not:** a snapshot of the parts at each landing in dev, a stable layout, the difference between two
snapshots with its goals, and a party's two tabs, *System* and *Board*, for a party the Architect leads. Not: the will-be
map, the contract, forks or the hand (§104's phase 2–3); a model naming the parts (a part is its folder); the other
lenses; the phone (the measure is on the desktop); the Orkmaster's tabs (spec 88).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§5 | new `realm/project_map.py` (snapshots, layout, difference), `realm/code_map.py` (`parts` reads a given tree, unchanged in what it reads), `core/idea_runner.py` (a snapshot after a landing: one call), `realm/party_recipes.py` and `realm/library.py` (the Tech party, §5), new `gui/ideas_system.py` (`ideas.system`, `ideas.system_part`; wired in `gui/ideas.py`), `realm/lexicon.py`, `realm/event_log.py`; new `tests/test_project_map.py`, `tests/test_party_recipes.py`, `tests/test_lexicon.py`, `tests/test_event_log.py` |
| **B. Desktop** | §6 | `js/arena/arena.js` (a party's tabs), new `js/arena/systemmap.js` (the table of parts), new `js/arena/systemmap.css` (`@import`ed by `arena.css`, in `tests/test_design_system.py` `SHEETS`), `js/arena/arrows.js` (a part's uses on hover, reused), `js/arena/motion.js` (its notes); new `tests/test_system_desktop_browser.py` |

## 0. The words
`TERMS` gains **view** · *views* (`lens_view`): one map of a leader's lens (*System*). *Lens* is §53's, widened by §104.1.
New strings: *System*, *Board*, *Since your last look at <time>*, *Nothing changed since your last look*, *New*,
*Changed*, *Gone*, *Changed by <goal>*, *By you* (a commit no task landed), *Uses*, *Used by*, *n files*, *Rearrange*,
*Reading the project…*. A part's name is its folder's, as it is.

## 1. A snapshot at each landing (A)
`project_map.snapshot(state_dir, tree, commit)` writes `<state_dir>/maps/system/<commit>.json`: `code_map.parts(tree)`
(each part's `path`, `files`, `count`, `uses`, `used_by`) and the commit. The runner calls it **after a task lands in
dev**, on the task's worktree (which stands at dev's new head), before the worktree is removed; it never raises into the
runner (a failure is an event, `map_snapshot_failed`). `project_map.ensure(state_dir, root)` makes the first one when
none is kept, from a detached worktree of dev's head (removed after). The newest 60 are kept.

## 2. A layout that stays (A)
`<state_dir>/maps/system/layout.json` keeps each part's **column and row**. A column is an **area**: the parts' paths
with their common prefix taken off, grouped by their first folder; when that makes one group, by their second. A part
seen for the first time takes the next row of its column; a gone part keeps its place until *Rearrange* (the person's
press) lays them out again. At most 8 columns (the smallest areas folded into *Other*) and 14 cards a column; beyond, the
least changed parts of a column lie in a stack (×n).

## 3. What changed (A)
`project_map.changed(state_dir, root, since, ref="dev")` → the parts **new** (in `ref`'s snapshot, not in `since`'s),
**gone** (the reverse), **changed** (a file under it in `git diff --name-only <since>..<ref>`), and the uses new and
gone, each change with its goal: `commit_goal.of` (spec 88 §3) of the last commit that touched it, `{}` read as *By you*.
`since` the newest snapshot at or before the person's last look; none: nothing is marked.

## 4. The commands (A)
`ideas.system {party, since}` → `{commit, at, columns: [{name, parts: [{path, name, count, uses, used_by, row}]}],
changed: {path: {kind, goal, task}}, uses_changed: [...], goals: {slug: {title, element}}}` from the newest snapshot (made
by `ensure` when none: the face says *Reading the project…*). `ideas.system_part {path, since}` → its files (at most 60),
uses and used by, and its changes since with their goals and the tasks' *What it made* (spec 85 §4). Events
`map_opened` (`lens`, `parts`, `changed`, `hours` since the last look) and `map_part_pressed`.

## 5. The Tech party (A)
The parties the Architect leads are named **Tech** (*How it is built: its parts, its tests and the build*): the recipes
`mobile-architecture`, `backend` and `engineering-code` keep their ids and take that name and line; the `game` and `web`
kinds gain a `tech` recipe (the Architect; builders `grunt`, `tester`; checker `reviewer`), offered after the kind's
first party (decisions §90, §104.1). The engineering craft's party (`library.PARTIES`) is named Tech too. A party made
before keeps its name.

## 6. The desktop (B)
1. **A party the Architect leads has two tabs** over its table: **System** and **Board** (today's field). It opens on
   *System* when something changed since the device's last look, else on the tab last used.
2. **System** lays the parts on the table (§2), as the field's cards (128 x 180, spec 87 §2): the area's name over each
   column as a member's name is over its column; a card's name is its folder, its line *n files*, its foot *Uses k ·
   Used by m*; a card a goal changed carries the goal's element top left until it is seen.
3. **On opening, it plays what changed since the device's last look** (`localStorage`, set when the tab is left): the
   map stands as it was, then each goal in the order it landed: its new parts dealt, its changed ones sealed with its
   element, its gone ones crumble (spec 74's moments: steps, ≤ 0.42 s each, the whole at most 3 s, *a press ends it*,
   none under reduced motion, none for a goal landed while the tab was open and seen). Over the table: *Since your last
   look at <time>* and the goals with their elements, a press on one dims the others' marks.
4. **Hovering a card draws its uses** as the field's arrows (spec 82 §6), a use new since the last look in its goal's
   element; never all the uses at once.
5. **A card pressed** shows its part beside the table: its files, *Uses*, *Used by*, and its changes since the last look,
   each with its goal and *What it made*; a goal there opens the goal.
6. *Rearrange* (in the tab's corner) lays the parts out again (§2).

## 7. Tests
A: a snapshot after a landing from the task's worktree, never raising; the first from a worktree of dev, removed; 60
kept; the areas and the layout kept across snapshots, a new part at its column's end, a gone one in place until
*Rearrange*; the caps and the stack; new, changed and gone parts and uses since a commit, with their goals and *By you*;
the commands' shapes; the Tech names, the new recipes, an older party's name kept; the events. B: the two tabs and the
first tab chosen; the cards and their lines; the reveal's order, its 3 s cap, ended by a press, none under reduced
motion; a goal pressed dims the others; the uses on hover; the part beside the table; *Rearrange*. The critical tests
and each part's files' tests.
