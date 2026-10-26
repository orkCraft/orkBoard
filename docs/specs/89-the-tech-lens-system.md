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

## As built (A)

Files: new `realm/project_map.py` (snapshots, layout, difference), new `gui/ideas_system.py` (`SystemMixin`, wired in `gui/ideas.py`: its
import, the class's bases, `**system_commands(self)`); `core/idea_runner.py` and `core/idea_review.py` (one call each after a landing:
`project_map.landed`), `realm/party_recipes.py` and `realm/library.py` (Tech), `realm/code_map.py` (its docstring only: `parts(tree)`
already read any tree), `realm/lexicon.py` (`lens_view`), `realm/event_log.py` (three events). Tests: new `tests/test_project_map.py`;
`tests/test_party_recipes.py`, `tests/test_library.py`, `tests/test_lexicon.py`, `tests/test_event_log.py`. No model anywhere.

**The commands' answers** (the shapes B reads; `ref` is the project's `merge_into`, `dev` by default; `since` is the device's last look,
a commit of dev, short or full, or an ISO time, read as the newest snapshot at or before it; none, or no snapshot at or before it:
nothing is marked and the answer's `since` is `""`):

- `ideas.system {party?, since?}` → `{commit, short, at, ref, since, columns, changed, uses_changed, goals}`. `commit` is dev's head (its
  snapshot is made by `ensure` when not kept: the face says *Reading the project…* while it waits), `at` its commit time (ISO), `since`
  the snapshot's commit it was read as. With no `ref` branch: `commit` `""`, `columns` `[]`, nothing marked.
  - `columns`: `[{name, parts: [card], stack: [card]}]` in the layout's order, `parts` by `row` (rows may skip: a gone part keeps its
    place), at most 14 cards a column; `stack` the rest (×n), the least changed (`changed` first among the cards, then the newest
    change, then by row). `card` = `{path, name, count, uses, used_by, row, gone}`: `name` the folder's (the top's files, path `"."`:
    the project's folder name; its column's `name` too), `uses`/`used_by` part paths, `gone` true for a part gone since `since` that
    still has its place (its data from `since`'s snapshot), to crumble in.
  - `changed`: `{path: {kind, goal, task, at}}`, `kind` `"new"` · `"changed"` · `"gone"`; `goal`/`task` of the last commit that touched
    a file of its folder since (`goal` `""`: *By you*); `at` that commit's time (ISO): the order the goals landed in.
  - `uses_changed`: `[{from, to, kind, goal, task, at}]`, `kind` `"new"` · `"gone"`, the goal of `from`'s last change.
  - `goals`: `{slug: {title, element}}` of every goal named above.
  - Event `map_opened` (`lens` `system`, `party`, `parts` (cards and stacked), `changed` (parts marked), `hours` since `since`, None
    for none, `device`).
- `ideas.system_part {path, since?, party?}` → `{path, name, count, files, uses, used_by, gone, kind, since, changes, goals}`: `files`
  the folder's own source files (at most 60), `gone` true when dev's head has it no more (read from `since`'s snapshot), `kind` its
  change since (`""` none), `changes` `[{goal, task, at, made}]` one a goal's task (and one *By you*, `goal` `""`), in the order they
  landed, `at` the newest commit of each, `made` the task's *What it made* (spec 85 §4; `""` for the person's). A path that is no part of
  dev's head nor of `since`'s snapshot: *That part is not in the project*. Event `map_part_pressed` (`lens`, `party`, `changed` the
  kind, `goals` how many, `device`).
- `ideas.system_rearrange {party?, since?}` → *Rearrange*: the layout laid out anew from dev's head (the gone parts' places taken
  away), answered as `ideas.system`; no event.

**The store.** `<state_dir>/maps/system/<commit>.json` = `{commit, at, taken, parts: [code_map.parts]}`, the newest 60 kept (by when they
were taken); `layout.json` = `{prefix, columns, areas: {area: column}, parts: {path: {column, row}}}`. The runner's call
(`project_map.landed(state_dir, root, tree, commit)`) reads the task's worktree after `land` and before it is removed, in the runner's
own thread; any failure is `map_snapshot_failed` (`commit` (12), `why`) and the landing stands. `project_map.changed(state_dir, root,
since, ref)` → `{since, commit, parts: {path: {kind, goal, task, sha, at}}, uses: [...]}`.

**Decided here, not in the text above:**
- `ensure` keeps dev's head current, not only the first: a head with no snapshot takes the newest one's parts when no source file
  changed between them (a Board page's commit, a README), else is read from the detached worktree `<state_dir>/maps/tree` (removed after).
  So a person's own commit and a result merged at Review are on the map too; a merge at Review also snapshots from its worktree
  (`core/idea_review.py`, the same one call).
- The areas: the common prefix is taken over the parts **but the top's** (`"."`), which is §2's *by their second* in one rule (parts all
  under `src/` beside the top's config files are grouped by the folder under `src/`); the top's own column first, then by name, *Other*
  last. A new area when 8 columns stand goes to *Other*; when there is none yet, the smallest column becomes *Other*.
- A part changed is one with a file **directly** in its folder in the diff (a sub-folder is a part of its own); any file, not only source.
- The Tech recipe of `game` and `web` is one id, `tech` (`kind_of` prefers the project's kind). A party made before is matched by its
  leader and team (`has`), never by its name, so an older *Backend* or *Mobile app: architecture* party keeps its name and is not
  offered again.

## As built (B)

Files: `js/arena/arena.js` (a party the Architect leads, `g.leader.slug == "architect"`, has *System* | *Board* over its table; Board is the
field as it was), new `js/arena/systemmap.js` (the words of §0, `useSystem`, `usePartyTab`, `PartyTabs`, `SystemMap`), new
`js/arena/systemmap.css` (`@import`ed by `arena.css`, in `tests/test_design_system.py` `SHEETS`), `js/arena/arrows.js` (`across`, a use's
route; `fine` exported; a line's `el` drawn as `data-elem`; what it does for tasks unchanged), `js/arena/motion.js` (its notes); new
`tests/test_system_desktop_browser.py` (a stub host with a Tech party and the three commands in A's shapes). No host change.

- **The tab.** `ideas.system` is asked when the party opens (its first answer chooses the tab): it opens on *System* when the answer marks
  anything (`changed` or `uses_changed`), else on the tab last **pressed** on this device (`localStorage` `orkboard.party.tab.<project>.<party>`;
  System at first). Only a press is kept, so a person who keeps to Board is brought to System only when something changed. A host that
  answers `ideas.system` without `columns` (before spec 89) has no tabs: the Board as it was.
- **The look.** `localStorage` `orkboard.system.look.<project>` = `{commit, at}`: dev's head as shown and the time, written when the System
  tab is left (another tab, another party, the page hidden). `commit` is sent as `since`; `at` is the *<time>* of *Since your last look at
  <time>* (*14:20* today, *25 Oct, 14:20* another day). Left, the answer is shown as seen at once (nothing marked, the gone parts' cards
  off, their places kept) and read again with the new look. Read again with the same look when a task lands on the Board (a merge moves
  dev; not on every refresh of the map, so `map_opened` is not sent for each), nothing played for it.
- **The table.** One grid for all the columns (128 px each, the rows 180 px, so a row reads straight across and a use's line runs in the
  gaps): the area's name over its column with a 2 px rule as wide as it (the member's look). A part lies at its `row`; a skipped row is an
  empty place. A column with a `stack` lays its cards one after another, then the stack's front (edges, ×n); a press opens it (every part
  of it), the fold beside the area's name shuts it. A card: top left the goal's element and *New* / *Changed* (*By you*: the word only,
  no element) while marked; its folder's name; *n files*; *Uses k · Used by m* (broken between the two when it does not fit). *Gone* is a
  card only while it crumbles; after, its place is empty until *Rearrange*.
- **The reveal.** The map stands as it was 0.3 s (a new part not yet there, a gone one still standing, a changed one unmarked), then each
  goal in the order of its newest change (`at`): new dealt (0.3 s, steps(6), 20 ms apart, six at most), changed sealed (its element 28 px,
  0.42 s, steps(6)), gone crumble (0.42 s, steps(3)); a goal 0.52 s after the one before, closer for many so the whole is at most 2.8 s;
  any press or key ends it. Only on the first answer the tab shows; none under reduced motion or while the page is hidden.
- **The goals over the table**: buttons with their elements (*By you* last when it is newest), `aria-pressed`; one pressed draws the
  others' marks dim (`Elem` dim, the edge back to the frame's). *Nothing changed since your last look* when `since` is set and nothing is
  marked; nothing said on a device with no look.
- **The uses on hover** (a fine pointer, or the focus): from the card to each part it uses and from each that uses it, `across`: out of the
  side facing the other card into the gutter, along it to the gap over the other's row, across, down into its top; the field's dashed
  2 px ink line and head, drawn in steps; a use new since the look in its goal's element. The ends light as a hovered task's do.
- **A part pressed** shows `ideas.system_part {path, party, since?}` in a 300 px pane beside the table (the table narrows): its name and
  path with *New* / *Changed* / *Gone*, its changes under *Since your last look at <time>* (a goal with its element, a press opens the goal;
  *By you*; *What it made*), *n files* with the files, *Uses* and *Used by* (each part by its name, a press shows that part). Close or Esc.
- *Rearrange* is in the bar's right corner (the tab's): `ideas.system_rearrange {party, since?}`, the answer replaces the table, nothing
  played. *Reading the project…* (with orkUI's busy mark) until the first answer.
