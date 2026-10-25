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
