# Spec 81 — A party's AI tool, picked from a list; its size is its team

The owner, 25 October (decisions §98), testing: pick a party's AI tool when it is made, from a list that drops down; the
size changes the party itself: Lean one agent, Standard the main seats, Full the whole team on middle tiers and up.
**Builds:** Claude · **Review:** full · P1.

**What it is, and is not:** a party's `tool`, the runner and the leader running on it, the list on New party and Edit the
party, and `party_recipes.sized` giving tiers as well as seats. Not: a tool per member (a later call: a seat keeps the
party's); a new tool registered; the Main tool's own reach (decisions, Operations) changed.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1, §2, §3, §5 | `realm/goal_team.py` (`tool_of` / `set_tool`, front matter `tool`), `realm/party_recipes.py` (`sized` → tiers), `realm/harnesses.py` (`for_party`: the list's rows), `core/idea_runner.py` and `core/idea_keeper.py` (`HARNESS` → the goal's party's tool), `realm/idea_target.py`, `gui/ideas_goals.py` (`goal_save {tool, size}`), `gui/ideas_project.py` (`ideas.tools`), `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_party_tool.py`; `tests/test_party_recipes.py`, `tests/test_party_size.py` |
| **B. Desktop** | §4 | `js/shell/proposals.js`, `js/shell/goalwizard.js`, `js/shell/goaldialog.js`, `js/shell/partysize.js`; new `tests/test_party_tool_desktop_browser.py` and the proposals' tests |
| **C. Phone** | §4 | `pwa/shell-proposals.js`, `pwa/shell-goal-new.js`, `pwa/shell-party.js`, `pwa/app.css`, `pwa/sw.js` (`CACHE` one up) and its pins; new `tests/test_pwa_party_tool_browser.py` |

## 0. The words
*AI tool* (the glossary's `ai_tool`; never *harness* in the interface). The list's label *Its AI tool*; its first row
*Main tool (Claude Code)*; its groups *Ready*, *Not signed in*, *Not installed*; a tool with no tiers: *runs its own
model*. Sizes: *Lean · one agent, Seasoned*; *Standard · n agents: the leader Veteran, the rest Seasoned*; *Full · n
agents, Seasoned and up*. The size switch's change: *Joins: …* / *Leaves: …*; refused: *<Name> has work open: it cannot
leave* (spec 75's).

## 1. A party's tool (A)
1. The party's page keeps `tool` (a `harnesses.REGISTRY` id) in its front matter; none or `""` is the Main tool.
   `goal_team.tool_of(root, slug)` / `set_tool(root, slug, tool)`; `ideas.goal_save {…, tool?}` keeps it (refused: *No AI
   tool <id>*). `ideas._track` rows and `ideas.map`'s `goals[]` carry `"tool"`.
2. The runner and the keeper run a goal's task and its leader's steps on `tool_of(its party) or harnesses.main(settings)`,
   not `HARNESS`. A tier becomes a model through that tool's `Harness.pick` (Settings' tier models first). A tool with an
   empty tier table runs its CLI's default; the tier is still recorded for the price.
3. A tool not signed in when a task would start holds the task as a sign-in does today (§58): the sign-in opens, the
   task waits for it. A tool not installed is never saved.
4. **`ideas.tools`** → `{"main": id, "tools": [{"id", "name", "ready", "signed_in", "installed", "experimental",
   "tiers": bool}]}`, ready first, then not signed in, then not installed, each group in the registry's order. It reads what
   Settings' tool rows read; no call to a tool.

## 2. A size is a team of tiers (A)
`party_recipes.sized(recipe, size)` → `{"leader", "team", "tiers": {agent: tier}, "size"}`:
- **lean**: `team = []`; the leader at `warrior` (Seasoned). A task with no taker in a lean party goes to **the leader's
  role**, not the Grunt's.
- **standard**: the leader at `elder`, the first two builders and the first checker at `warrior` (§98.3, the owner's
  call: the main seats on the better tier, not every seat on `laborer`).
- **full**: every seat up to `library.seats_of`; builders `warrior`, the leader and the checkers `elder`.
- a `whole` recipe (Ideation, Release) is sized too: lean its leader alone, standard two builders and the checker, full
  all of them.
The tiers live with the party (`goal_team` `tiers` in the front matter) and are what the runner and keeper pick from for
that party's seats; a role the person set to a tier by hand in Agents keeps it. The Target of a size (spec 75 §3) stays.

## 3. A change of size (A)
`ideas.goal_save {slug, size}` on an existing party with a recipe of its own (its `proposal`, or the leader's recipe)
sets the size's team and tiers in one save; a member with work open refuses it and nothing changes. A party made from the
library with no recipe keeps its team; its size sets the tiers and the Target only. Event `party_resized` gains `joins`,
`leaves`.

## 4. The faces (B, C)
1. **New party** (a proposal's card and *More: the library*): under the size switch, *Its AI tool*, a list that drops
   down: orkUI's `.ork-select` with `<optgroup>`s on the desktop, the phone's own select; *Main tool* picked. A row not
   signed in, picked, opens its sign-in (the flow of spec 45) and stays picked; a row not installed is disabled with its
   group's word. The price under the switch reads the tool's tiers.
2. **Edit the party** (desktop `goaldialog.js`) and *About this party* (phone): the same list; a change saves `tool`.
3. **The size switch** shows the heads that join and leave before the press, then saves in one press (no second
   confirm), §0's refusal said in place.

## 5. Tests
- **A**: `tool` kept and read; a task and a leader's step run on the party's tool (a stub registry), on the Main tool
  without one; a tool without tiers; a tool not signed in holds the task; `ideas.tools`' order and groups; `sized` for
  each size (lean one agent, its tasks to the leader; standard's tiers; full none below `warrior`; Ideation in three
  sizes); a resize with a member at work refused; the events.
- **B / C** (stub host): the list's groups and default, a not-installed row disabled, a not-signed-in row opens the sign-in,
  the tool sent with `goal_save`; the size switch's joins and leaves; C: no sideways scroll at 390 px, the service
  worker's version.
- Each part: the critical tests (CLAUDE.md "Alpha"), its files' tests, `tests/test_gui_wording.py`,
  `tests/test_design_system.py`, `tests/test_architecture.py`; C also `tests/test_pwa.py`.


## As built (A)

- `realm/goal_team.py`: `tool_of(root, slug)` / `set_tool(root, slug, tool)` (front matter `tool`; "" the Main tool; *No AI tool <id>* for one that is none), `tiers_of` / `set_tiers` / `clean_tiers` (front matter `tiers`, JSON `{agent: tier}`), `seat_role(role, tiers)` (the role as the party's seat runs it: its model is the party's tier when it is "" (By Target) or the library's tier it was installed with; any other model is the person's, set by hand, and stays), `lean_role(root, slug)` (the leader's slug in a Lean party with a leader, else ""), `recipe_of` / `set_recipe` (front matter `recipe`: the recipe a party was made from, so a Lean party can grow back). `seats()` lets Ideation be its whole seats, *two views and the skeptic* (the first two of `library.VIEWS`) or none (the sized teams); any other part of it is still refused with the same words.
- `realm/party_recipes.py`: `sized(recipe, size)` → `{"leader", "team", "tiers", "size"}`: Lean `team` [], the leader `warrior`; Standard the leader `elder`, the first two builders and the first checker `warrior`; Full every seat up to `library.seats_of`, builders `warrior`, the leader and the checkers `elder`. A `whole` recipe is sized the same way (Ideation Standard: Product view, Market view, the Skeptic; Release Standard: two builders and the checker). `tiers_for(leader, team, size)` gives any party's seats their tiers (Lean: every seat `warrior`; Standard: the main seats, the others as the library has them; the Taskmaster is no seat).
- `realm/harnesses.py` `for_party(installed, signed_out, main_id)` → `{"main", "tools": [{id, name, ready, signed_in, installed, experimental, tiers}]}`, ready first, then installed and not signed in, then not installed, the registry's order within a group; `tiers` is False for a tool with an empty tier table. `ideas.tools` (`gui/ideas_project.py`) reads `shutil.which(h.bin)` (nothing is run) and `host.sign_ins.blocked(id)`, the main tool from `settings.main_tool`. `Ideas.tools_installed()` is the one place the path is read.
- `core/idea_runner.py` (small): `IdeaRunner(…, party_of=)` (`Ideas.party_of_idea`: `{"tool", "tiers"}` of the idea's party), `party(slug)`, `tool_of(slug)` (the party's tool, else `settings.main_tool()`), used for the window (`status.reset_of`), the sign-in hold, `_launch`'s `tool`, `_work`'s `harnesses.need`, `jobs.run_work`, the spend line. `ran_on(task, slug)` picks from `goal_team.seat_role(self._role(task), tiers)`. `_hold_sign_in(task, line, harness)` records the tool; `HARNESS` stays as the tool a held task without one is taken to have been on. `core/idea_keeper.py`: `tool_now()` (the running step's goal's party's tool, else the Main tool) for `_claude` and `_spent`; `core/idea_lead.py` `leader()` returns the seat role (the leader's step runs on the tier its size gave it). `plan_one` / `revise_one` give every task of a Lean party the leader's role (`lean_role`); `plan_one`'s estimate prices the seats' tiers.
- `realm/party_resize.py` (new): `recipe_for(leader, team, kept)` (the kept recipe, else the leader's recipe whose seats hold the whole team), `resized(root, slug, size)` → `{recipe, size, team, tiers, joins, leaves}`, `resizes`. `ideas.goal_save {slug, size}` on a party with a recipe and no `team` sent sets the size's team and tiers in one save (the party's `every` kept for those who stay; the joiners installed as roles); a member with work open who would leave refuses it (*<Name> has work open: it cannot leave*) before anything is written; a party with no recipe keeps its team, `size` sets its tiers and Target. A `proposal` / `preset` that is a recipe's id is kept (`recipe`). `tool` is validated before anything is saved: *No AI tool <id>*, *<Title> is not installed* (not for the tool the party has already), *tool is not text*. `ideas.party_sizes {slug}` → `{size, sizes: {lean|standard|full: {recipe, team, tiers, joins, leaves}}}`, `joins` / `leaves` as `{slug, name, head}` (a read: nothing is written).
- Readers: `ideas._track` rows (so `ideas.board`, `ideas.goal`) and `ideas.map`'s `goals[]` carry `"tool"`. Heads wear the seat's tier: `board_map` (the party's members, leader, a plan's tasks), `party_work.who`, `roles.task_head(…, tiers)` (plan, Agents' queue, a task, a pick, a canvas), `ideas._goal_row` leader. `party_price.price(…, tiers=)` prices the seats at them (`ideas.party_price` takes them from `size`); `orkmaster.proposals`' sizes carry `tiers` and their heads wear them.
- Events: `party_resized` gains `joins`, `leaves` (agent slugs); `goal_saved` gains `tool`.
- Not done: the Ideation judge still asks its four views and the skeptic whatever the party's size (only its team, tiers and Target change); the keeper's own window and sign-in hold (`idea_keeper.window_until`, `idea_sign_in.py`) still read Claude's; Agents' per-role `harness` still reads the modules' `HARNESS`; an experimental tool not turned on in Settings is listed like another (only its `experimental` flag says so).
- Tests: `tests/test_party_tool.py` (the tool kept and read; refused; the list's groups and order; the task and the leader's step on the party's tool and on the Main tool; a tool with no tiers; a tool not signed in holds the task; the tiers and a hand-set role; Lean's tasks to the leader; a resize with who joins and leaves, its events, `every` kept, a member at work refused; a library party with no recipe; Ideation and Release sized), `tests/test_party_recipes.py`, `tests/test_party_size.py`, `tests/test_party_price.py`, `tests/test_ideation.py`, `tests/test_gui_ideas.py` (`BOARD_COMMANDS` has `ideas.tools`, `ideas.party_sizes`).

## As built (B)

- `js/shell/toolpick.js` (new): `useTools()` (`ideas.tools`, quiet; asked again when a sign-in begins or ends; null for a host without it, and then no field is drawn), `ToolPick` (**Its AI tool**: orkUI's `.ork-select` around a native `<select class="ork-field">`; first option *Main tool (Claude Code)* (the Main tool's own name; *· runs its own model* when it has no tiers), then `<optgroup>`s *Ready*, *Not signed in*, *Not installed* (their options disabled unless it is the value) as the host sorts them; a tool with no tiers reads *<Name> · runs its own model*), `toolRow`, `runsOwn`. A row not signed in, picked, calls `signIn(id)` (`tools.sign_in`, spec 45) and stays picked, with *Not signed in: its sign-in opens, and the party's work waits for it.* under it.
- `proposals.js`: each card has the field under the size switch (its own pick per card, the Main tool at first); a tool with no tiers puts *runs its own model* where the price was (the heads and the agents stay); **Make it** sends `tool` only when one is picked. `goalwizard.js` (*More: the library*): the field after *Its size*; with a tool with no tiers *Runs its own model: its price is its own.* replaces the price line; *Save party* sends `tool`. `goaldialog.js` (*Edit the party*): the field with the party's tool (`ideas.board`'s `tracks[].tool`); *Save party* sends `tool` only when it changed ("" for the Main tool).
- `partysize.js` (rewritten): no *With its team*, no *Its members leave the party* / *Make it Lean* / *Keep them*. `useMoves(slug)` asks `ideas.party_sizes` (again when the saved size or party changes); under the switch `Moves` lists, for each size but the picked one that changes who is in the party, *Lean · Leaves: <heads> Grunt, Tester* / *Full · Joins: …* (`ul.shell-size__moves`, `li[data-size-move]`, `span[data-move]`, the heads small beside the names), so the change is shown before the press. A press saves in one: About this party sends `{slug, about, priority, size}` (the host gives the team) and refreshes; Edit the party sets the size and, when the size changes who is in, the team the host said (`onChange(to, team|null)`), sent with *Save party*. A member of the party with work open that the size would let go is refused at once, in place (*Grunt has work open: it cannot leave*, `role="alert"`); the host's own refusal (a result with `error`, or a rejected reply; `command(…, quiet = true)`) is said in the same place, not toasted, and the size stays. The price of each size is asked for the team that size would have.
- `shell.css`: `.shell-size__moves`, `.shell-size__move`, `.shell-size__heads`, `.shell-tool`.
- Tests: `tests/test_party_tool_desktop_browser.py` (7, the proposals test's stub host with `ideas.tools`): the groups and the Main tool picked, each card's own pick, `tool` sent and not sent, no tiers (*runs its own model*), a tool not signed in (the sign-in command, stays picked), the library, Edit the party (sent only on a change), a host without the list. `tests/test_proposals_desktop_browser.py`: the stub gained `ideas.tools`, `ideas.party_sizes`, `tools.sign_in`, a host refusal of a size; the three *With its team* tests became: the joins and leaves before the press and one press, a member at work refused in place, a host refusal said in place; Edit the party sends the size and the team it gave.

## As built (C)

- `pwa/shell-party-tool.js` (new; in `sw.js` `SHELL`): `loadTools(core)` (`core.st.tools`), `toolPick(core, {label, onPick})` → `{el, set, get, draw}` (the phone's own `<select class="ork-field">` in `div.field.tool-field[data-sec=tool]`, hidden until the list is known; the same options and groups as the desktop's; 44 px), `runsOwn`, `toolRow`, `sizeMoves(core)` → `{el, load(slug, size, sig)}` (`ul.size-moves`, a line per other size that changes who is in, heads small; kept per party, size and team in `core.st.moves`; hidden for a host without `ideas.party_sizes`). The phone opens nothing on the computer (`tools.sign_in` is the desktop's): a tool not signed in, picked, stays picked and says *Not signed in: sign in on the computer. The party's work waits for it.*.
- `shell-proposals.js`: each card has `toolPick` after the switch (a pick per card), the tool with no tiers shows *runs its own model* in place of the price, `act.make(p, size, card, button, tool)`; `load` asks the tools with the proposals. `shell-goal-new.js`: **Make it** sends `tool` when picked; *More: the library* has the field after *Its size* and *Save party* sends `tool`. `shell-party.js` (*About this party*): **Its AI tool** (a section with the select; a change saves `{slug, tool}` at once, a refusal said in place), and **Its size** gets the moves under its switch; one press saves `{slug, size}`, a refusal of the host is said under the switch (`p.size-note[role=alert]`) and the size stays.
- `app.css`: `.tool-field`, `.size-moves`, `.size-move`, `.size-note`; no sideways scroll at 390 px. `sw.js` `CACHE` `orkcraft-app-v90` -> `orkcraft-app-v91`; `tests/test_pwa.py` pins it. Not built: the field in *Edit the party* (shell-goal.js) — the tool is changed in *About this party*.
- Tests: `tests/test_pwa_party_tool_browser.py` (10, 390 x 844, spec 75's stub host with `ideas.tools` and `ideas.party_sizes`): the groups, the default and the disabled rows; each card's own pick; `tool` sent / not sent; no tiers; a tool not signed in (no sign-in command from the phone); the library; a host without the list; About this party's tool saved at once; the moves before the press and one press; a refusal said in place; a host without `ideas.party_sizes`; the service worker's version.
