# 130. The first open is the Orkmaster's: the project and the AI tools asked as cards, the parties on the Orkmaster's large card, the table laid at Start; the column narrows to its upright card; goals put off after the reset

Decisions §232 (1–12), §236 (1–5) and §239.3–4 (with §239.5's words), read against §245–§249 (*Read against the later decisions*, below). The owner,
3–4 November: *the AI tools can be turned on and off, added and removed while working on a project, not only at the start: better straight from the
bottles*; *opening the project's folder could be a talk with the Orkmaster, like the questions with the leaders, which also teaches them*; *never the
discard beside Settings: it looks like a bug*; and of the column: *the cards turned by 90° cut a little on their left, so the ring of runes is seen but they
do not take so much room*. **Builds:** A on the host first (the spec's author reviewing and merging), E beside it, then B, C and D on the cheaper model, each
part on the owner's yes on `docs/mockups/setup/` (given, §232; the column's tuck is drawn first, E.2) · **Review:** the critical tests and each part's own, with a browser test of the first open from
an empty folder to the laid table (after D) · P1. After spec 128 (the column), spec 138 A and spec 139 (the die and the door the unlaid table does not
have), and with spec 142 A (the column's upright card with no window: this spec changes only its width and the face-down card's place). No new pane,
column, drawer or dialog (§104.0, §145): the cards are the hand's, the place of the parties is the one place there already is.

**orkUI draws first** (§127.3, §232.12): the empty slot `.ork-potion.is-empty` (the silhouette in pixel dashes, `.is-lit` in the ink), the small size
switch, a head's shadow `.ork-race__head.is-empty`, the three levels' tiles. **Until orkUI has them, the face uses the page's own layout with orkUI's
tokens** (`var(--ork-*)` only: no colour, font or corner of its own, `tests/test_design_system.py`), each such place marked in its module with the comment
`orkUI first: <the class>` so the copy (`python -m orkboard.design.orkui <orkUI>`) finds what to drop. A part is never held for orkUI.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Host** (no face) | `machine.tool_order`, read by `harnesses.main`; the AI tools' own commands `tools.*` out of the onboarding (its names kept as aliases); the adding card's rows, the key found in the environment by name, Test & add, Put back between tasks, the order, the billing; the project's questions answered from a card (`first_open.*`, `projects.new_folder`); the *laid* state | `settings.py`, `realm/harnesses.py`, new `realm/tool_hand.py`, new `realm/first_open.py`, new `gui/tools_host.py`, new `gui/first_open_cards.py`, `gui/onboarding.py`, `gui/board_host.py`, `gui/ideas.py` (`snapshot`: `laid`), `gui/ideas_project_q.py` (`project_start`: lays), `realm/lexicon.py`; new `tests/test_tool_hand.py`, new `tests/test_tools_host.py`, new `tests/test_first_open.py`, `tests/test_board_alone.py` (the snapshot's keys) |
| **B. The hand** (face) | the potions' empty slot; the card that adds one tool; a potion's own card with the order, the billing, Check and Put back; the Orkmaster's setup cards (the project, git, the kind) | `gui/static/js/hand/mana.js`, `hand/state.js`, new `hand/toolcard.js`, new `hand/addtool.js`, new `hand/setupcards.js`, `hand/hand.css`, `hand/mana.css`; new `tests/test_add_tool_browser.py`, `tests/test_gui_wording.py` |
| **C. The table** (face) | the parties as the Orkmaster's large card, a party one line with its heads; a head's seat with its tool and its level; the places covering the table's end; no empty pile; the laying's motion | `gui/static/js/table/parties.js` (and its split), `table/partyseats2.js`, `table/seatpop.js`, `frame/place.js`, `table/table.js`, `table/column.js`, `table/piles.js`, new `table/laying.js`; new `tests/test_parties_card_browser.py`, `tests/test_table_desktop_browser.py` |
| **D. Settings and the onboarding** (face) | Settings keeps what is neither a tool nor a party; the onboarding's table of checkboxes goes; the start screen becomes the Orkmaster's first card | `gui/static/js/shell/settings.js`, `js/settings.js`, `js/onboarding.js` (`ToolsStep`), `shell/projects.js` (`StartScreen`, `OpenFolderPlace`), `shell/toolpick.js`; new `tests/test_first_open_browser.py` |
| **E. The column, and the put-off** (host and face) | the column's width of its own; a face-down card tucked under the window's left edge; **Hold** on the route card and the pile's line *waits for the reset* | `gui/static/js/frame/frame.css`, `table/column.css`, `table/column.js`, `table/piles.js`, `hand/routecard.js`, `hand/hand.css`; `gui/ideas_route.py` (`route_hold`, `route_stop`), `realm/board_map.py`; new `tests/test_column_tuck_browser.py`, new `tests/test_pile_waits_browser.py`, new `tests/test_route_hold.py` |

A stands alone and is useful alone: the page that still calls the onboarding's commands is not broken. **E is the first part** that the decisions
(§236.5, §239.3–4) name; it stands alone too and is merged on A's day or before. B needs A, C needs A's `laid`, D needs B and C. Each part is merged into
main as its own tests and the critical ones are green (CLAUDE.md, Alpha).

## 0. What is there today

- **The tools are set once, on a form.** The onboarding's first screen is `js/onboarding.js` `ToolsStep`: a table of checkboxes (a row a tool found: its
  mark, version, sign-in, a *Subscription | API* select, **Check**, an experimental tool's warning), *Request a tool*, and the Security reviewer's checkbox;
  its host is `gui/onboarding.py` `Onboarding` (it opens on a machine never set up: `wanted()`), whose commands were `onboarding.tools`, `.check`,
  `.detect`, `.request`, `.skip`, `.close`, `.cancel`; `.check` made one short request on the tool's cheapest tier (`CHECK_PROMPT`). Later the tools are set
  nowhere in Orkboard's own Settings (`js/shell/settings.js` has no tool rows); `js/settings.js` (the town's Settings copy, still loaded by the onboarding
  for `USAGE_WHAT`) has *AI tools* rows.
- **The potions can only be read.** `hand/mana.js` draws one `.ork-potion` a tool in the limits, `PLACES = 6` (two rows of three); a press opens what
  used it over the pane; the framed potion is the tool the open tab's work goes to (§177.1). Nothing adds, removes or orders a potion. The order the work
  moves on in was **the registry's**: `settings.tool_order(machine)` listed the tools turned on in `machine.tools`' order (`realm/tool_now.py` reads it),
  and `harnesses.main(enabled, chosen)` named the first on in the registry's order.
- **The tools' state is `machine.tools`** (`{id: {enabled, billing}}`, `settings.ToolChoice`) and `machine.main_tool` (`""`: the first on); the keys a tool
  takes before its sign-in are `realm/tool_errors.py` `TAKES_KEYS`; the sign-in is spec 45's (`tools.sign_in*`, `core/sign_ins.py`); a tool's found state is
  `tools.detect()` (`ToolStatus`: found, version, `logged_in`, the billing guessed from a key in the environment).
- **The folder is a form.** With no project open the pane is `shell/projects.js` `StartScreen` (*Open a project*, **Open folder…**, *Recent*), its
  `OpenFolderPlace` a path field and the system's dialog (`folders.pick`); `projects.open` answers `{git}`; `projects.start_git`; `ideas.proposals` reads
  the kind by the folder's names (`realm/project_kind.py`, an empty folder asks one line, `core/idea_kind.py`); the kind the person sets is kept in
  `<state_dir>/project.json` (`project_kind.keep`).
- **The parties are a place of two halves** (`table/parties.js` `Parties`, `openParties`, `useFirstStart`; spec 100 §4): proposals on the left, the party's
  size and its AI tool as selects (`shell/toolpick.js`), **Start** → `ideas.party_save {first: true}` → `ideas.project_ask` (`gui/ideas_project_q.py`
  `project_start`: reads the project's own notes in, begins the first start's questions).
- **The table is always laid** (§185): the leaders' row, the column, the ring and the discard's place at the table's end, the + card and the deck in the
  hand, whether or not the project has a party. There is **no state** for it: nothing says *not yet*. Spec 140 A.1 (§247.1) draws the ring and the discard
  only when they hold something.
- **The column** (`table/column.js`, `column.css`, `frame/frame.css`): the grid's first track is `var(--col-w)`, **180 px**, a lane's (`--card-w` 144 px × 1.25);
  a face-up card is 112 px wide, a face-down card **157 × 112** (`.col-card--down`, its seal centred at 50%, its thin edges `.col-edges` 151 px, its play
  button at `left: 78px`), so the column has two right edges and 68 px empty beside every face-up card; a card hovered slides out `translateX(6px)` (face
  down) or `36px` and a turn (face up); `.col-scroll` is `overflow-x: hidden`. The hand's first lane lies under the column: `hand/hand.css`
  `--hc-first` is built on `--col-w` too.
- **A goal put off** (`gui/ideas_route.py`): the route card offers **Talk**, and **Later** (`ideas.route_later`, `held_until` at the reset) only when the
  limits run low (spec 140 B, decisions §247.2, named it so: `TERMS` `later`, `hold`); `route_tick` / `_backlog_next` start the put-off goals one at a time
  after the reset (§239.1–2, built). A routed goal with no `held_until` waits for **Talk** (and starts by itself only through `route_auto`, spec 120).
  **Nothing offers to put a goal by with no start of its own, and no pile says why a goal waits** (§239.3–4 are not built).

## Read against the later decisions

- **§247.2** names §239.3's *Keep it* **Hold** (*nothing starts it until Start now*; its card says *Held*); *Keep it* stays only in the drop question
  (`table/dropgoal.js`). So E builds **Hold**, not *Keep it*; `TERMS` already has `hold` (was *Later today*) and `later` (was *Later, by itself*).
- **§247.1** (the portal and the discard drawn only when they hold something) is **kinder than §232.1**: the ring and the discard's place do not appear at
  Start, they appear with their first content. C lays at Start the leaders' chairs, the empty chair, the door, the die and the + card, and not the ring.
- **§246** (the die is what moves, the door is the person, the bug in the Orkmaster's menu): the unlaid table has no die and no door (§232.1); both appear
  at Start. The Orkmaster's **…** menu holds Settings (§232.9, §246.6), so Settings stays reachable before Start, over the whole table (C.4).
- **§249.1** gives the column's upright card no window and keeps the face-down card's size (§236.4's *157 × 112* is the face-down card's now): E changes the
  face-down card's **place** and the column's **width** only; the upright card's height is spec 142 A's.
- **§237.8** (the hand is kept for what is urgent) is for today's decisions' cards; the Orkmaster's setup cards (B.4) are the first open's questions, in the
  hand because the person is asked (§206.6), and go when answered.
- **§244** (the Board lives in the project's repository): `laid` lives in `project.json`, which travels with the Board's branch (`realm/board_branch.py`
  `TOP_FILES`), so a project cloned elsewhere is laid; `tool_order` is the machine's and does not travel.
- **§248** (a card with a rune is picked by its rune): the setup cards have no rune and are not picked, only lifted.

## A. Host

### A.1 `machine.tool_order` (decisions §232.5)

`settings.MachineSettings.tool_order: list[str]`, kept in the machine's settings file as `tool_order` (`~/.config/orkcraft/settings.json`: the name Orkline
reads); `settings.clean_tool_order(raw)` keeps the known tools, each once, in the order given, and `[]` for anything that is no list. **The order the work moves
on in**: the person's, the potions' left to right, the first tool the main tool's place.

- `settings.tool_order(machine)` → the tools **turned on**, **in `machine.tool_order`'s order, the tools it does not name after them in the registry's** (a
  stable sort): a file with no order, or a tool turned on by an older Orkboard, reads as before. `realm/tool_now.py` reads this and changes nowhere.
- `harnesses.main(enabled, chosen="", order=())`: `chosen` when it is on, else **the first in `order` that is on**, else the first on in the registry's, else
  None. `settings.main_tool(machine)` passes `machine.tool_order`. Nothing else calls `harnesses.main`.
- **The first tool in an empty hand is the main tool** (`machine.main_tool` is set to it); **the order's first tool is the main tool** (`tools.order` sets
  `main_tool` to it, A.3), so the framed potion (§177.1) and the first of the order are one.
- Orkline's `settings.py` takes the same key **the same day** (CLAUDE.md, *Orkboard and Orkline*: reading and keeping it; Orkline's potions need not use it),
  this repository's commit named in Orkline's, or Orkline's save drops it.

### A.2 `realm/tool_hand.py` (pure: it reads the machine, the tools found and the environment's *names*; it runs no tool and writes nothing)

`HAND_MAX = 6`; `KEYS = {**tool_errors.TAKES_KEYS, "agy": ("GEMINI_API_KEY", "GOOGLE_API_KEY")}` (the variables a tool takes a key from; Antigravity's pair is
what `tools.detect` already reads as an API key); `TEST_COST = "about $0.001"`.

| Function | What it gives |
|---|---|
| `hand(machine)` | the tools in the hand in the person's order (`settings.tool_order`): **a tool is in the hand or not, there is no third state** (§232.4) |
| `key_found(tool, env=None)` | the **name** of the first variable of `KEYS[tool]` that is set and non-empty, `""` with none. **The value is never returned, logged, kept or sent**; no key is typed into Orkboard (§232.10) |
| `third_line(tool, billing, logged_in, env=None)` | the card's third line `{state, line, needs, var, warn, cost}`: on *subscription* `ok` *Signed in to your subscription*, `signed_out` *Not signed in* with `needs: "sign_in"` (spec 45's sign-in; Test & add waits), `unknown` (the sign-in cannot be told without a request: it may go on, the request tells); on *api* `ok` *Uses the key in your environment: CODEX_API_KEY* with `cost` *Paid per token, by that key*, or `no_key` *No key found: set CODEX_API_KEY in your environment, then Test again* (`needs: "key"`, `var`); a tool no key of which is known says *No key <Tool> takes is known here: use its subscription*. `warn` (subscription only): **a key that would win over the subscription is said before it costs**, *ANTHROPIC_API_KEY is set in your environment: Claude Code uses it before your subscription and is paid per token.* |
| `card(statuses, machine, env=None)` | the card that adds one tool `{ready, n, max, full, tools, first}`: the tools found that are **not in the hand**, ready first, then not signed in, then not installed (toolpick.js's three groups, `READY` · `SIGNED_OUT` · `NOT_INSTALLED`), each group in the registry's order; a row `{id, title, mark, group, version, risk, install, login, billing, lines: {subscription, api}, pickable}`, a tool not installed with how to install it and **never pickable**; `first` the first ready tool that is not experimental (`""` with none: nothing is picked for the person); `ready: false` until the tools were looked for |
| `refusal(row, machine, billing, env=None, risk_read=False)` | why Test & add may not go on, in the card's words, `""` when it may: *That AI tool is not found here*, *<Tool> is in your hand already*, *Your hand holds 6 AI tools: put one back to add <Tool>*, *<Tool> is not installed: <how>*, *<Tool> is experimental: read its warning first*, *<Tool> is not signed in: sign in first (<how>)*, the no-key line |
| `add(machine, tool, billing)` | the tool turned on, paid as said, **at the end of the order**; the main tool when the hand was empty |
| `next_after(order, tool)` | the tool the work goes on with when `tool` is out: the next in the order, round again (`tool_now`'s rule), None when it is alone |
| `put_back_plan(machine, tool, parties)` | what putting it back would do, said before it is done: `{tool, title, last, next, parties: [{slug, name, goes_on_with, line}], line, ask}`; `line` *The orks stop using it after the task at work*; a party's `line` *Art is set to Claude Code: it goes on with Codex, the next in your hand*; **the last tool** has `ask` *Without it nothing is worked on: goals wait in the Orkmaster's column until you add a tool* |
| `take_out(machine, tool)` → undo | the tool turned off and out of the order; the main tool's place passes to the first left (`""` when none); the record `{tool, billing, at, main}` |
| `restore(machine, undo)` | the tool back **at its place, paid as it was**, the main tool again when it was; ValueError *There is nothing to undo* for a record that is none |
| `reorder(machine, order)` | the person's order: **a permutation of the hand** (nothing added, nothing left out: ValueError *The order names the AI tools in your hand, each once*); its first tool is the main tool |

### A.3 `gui/tools_host.py` (the AI tools' own commands) and the onboarding's names kept

`ToolsHost(host, detect=None, detect_others=None, ask=None, on_found=None)` owns what `Onboarding` owned of the tools: the tools found (`statuses`, `others`), the
look on a thread (`scan`), the Check (`checks`) and the request for a tool (`request`); and what is new (`adding`). `Onboarding` **composes it**
(`self.tools_host`, `statuses` / `others` / `checks` / `_finder` read through to it; its `_found` callback sets what the first screen's rows pick), and Orkline's
onboarding composes the same. `ToolsError` is the commands' refusal in words; `Orkboard.command` turns it, like `OnboardingError`, into a `CommandError`.

| Command | Arguments → answer |
|---|---|
| `tools.look` | `{}` → look for the tools again (one was just installed) |
| `tools.card` | `{}` → `tool_hand.card(...)`; **begins the look when it was not made** (`ready: false`, the page is pushed when it is in) |
| `tools.check` | `{tool}` → one short request (`CHECK_PROMPT`, the tool's cheapest tier, `"laborer"`) on a thread; `checks[tool]` is `running`, then `{state: ok, ms}` or `{state: failed, kind, line, action, detail, sign_in}` in the tool's words (`tool_errors`); refused: *That AI tool is not found here* |
| `tools.test_add` | `{tool, billing?, risk_read?}` → refuses by `tool_hand.refusal` (words, nothing run); else **one short request** as Check, on a thread, `adding[tool]` `{state: running, billing, cost}`; **when it answers** `tool_hand.add`, the settings saved, the tool now read again (`host._follow_main`), `adding[tool]` `{state: added, ms, title, n, full, line}` (*<Tool> is in your hand. Add another AI tool?*; at the sixth tool *<Tool> is in your hand.*); **when it fails** `adding[tool]` is the failure in the tool's words and **nothing is added**. `billing` defaults to the tool's guess |
| `tools.order` | `{order}` → `tool_hand.reorder`, saved; the snapshot's `tools` |
| `tools.billing` | `{tool, billing}` → how a tool **in the hand** is paid: *api* only with a key found (*No key found: …*), *subscription* only when not signed out; saved; `{…tools, line}` |
| `tools.put_back_plan` | `{tool}` → `tool_hand.put_back_plan` for a tool in the hand: said under **Put back** before it is pressed (*The orks stop using it after the task at work*, each party set to the tool by name and what it goes on with, the last tool's question); **changes nothing** |
| `tools.put_back` | `{tool, sure?}` → **between tasks, never inside one** (§177.2): a task at work goes on with the tool until it is done, because a tool is resolved when a task starts (`realm/tool_now.py`, `tool_run.resolve`), and no later one starts on it; each party **of the open projects** set to it by name (`goal_team.tool_of`) is set to the next tool in the hand (`goal_team.set_tool`); the parties of a closed project are not touched. **The last tool** answers `{ok: false, ask, plan}` with nothing changed **unless `sure` is true**. Answers `{ok: true, plan, undo}` |
| `tools.put_back_undo` | `{undo}` → the toast's **Undo**: `tool_hand.restore`, and the parties set to the tool again; refused with the hand full or a record that is none |
| `tools.request` | `{name, link?, note?}` → a filled-in GitHub issue's URL, nothing sent from here (was `onboarding.request`) |

**The onboarding's names are aliases**, so the page that still calls them (`js/onboarding.js` until D) is not broken: `onboarding.check` → `tools.check`,
`onboarding.detect` → `tools.look`, `onboarding.request` → `tools.request` (`onboarding.tools`, `.skip`, `.close`, `.cancel` are the first screen's own and stay).
`onboarding.check` and `.detect` still say *The onboarding is not open* when it is not, and `onboarding.check` answers the onboarding's snapshot and says its
refusal as an `OnboardingError`. **A test says so** (`tests/test_tools_host.py`): both names are in `host.commands`, run one thing, and the old rows read the same Check.
The aliases go with D. Nothing is renamed: `tools.sign_in`, `.sign_in_cancel` and `.sign_in_done` (spec 45) are in the same namespace and untouched.

**The snapshot** gains `tools` (the computer's own: it is in `COMPUTER_ONLY`, as `laid` is, the phone shows the tools as today and sets none, §232.10; none of `tools.*`,
`first_open.*` or `projects.new_folder` is in `BoardPhone.COMMANDS`): `{hand: [{id, title, mark, billing, main, version, check}], order, main, max, full,
adding: {tool: {…}}}`. **Nothing secret is in it**: a key is named at most, in a card's line, never read out (a test sets a key's value and finds it in no snapshot,
no card and no settings file).

### A.4 The project's questions (`realm/first_open.py`, `gui/first_open_cards.py`; decisions §232.3, §232.8)

`first_open.step(open, git, kind_kept, hand, tools_skipped, laid)` → the question the Orkmaster asks now, **in this order** (§232.8):
`project` (no folder open) → `laid` (the table is laid: nothing is asked, however the rest stands) → `git` (a folder with none) → `kind` (the project's kind
not answered: `project_kind.kept` is empty) → `tools` (**only when the hand is empty**: the tools are this computer's, the second project skips it; skipped
while `tools_skipped`) → `parties`. `first_open.line(step, name, kind_words)` is the Orkmaster's line in its bubble: *Which project shall we work on?*, *No git in
<name> yet. Start git here?*, *<name> is <kind>, <how>. Right?* (*What is <name> for?* for an empty folder), *Which AI tool shall the orks think with?*, *Who shall
work on it? The parties are on the table.* No answer is typed that a press could give.

`gui/first_open_cards.py` `FirstOpen(host)` (desktop only; `host.first_open`):

- `first_open.ask {}` → `{step, line, name, recent, kind, hand, laid}`: `recent` the recent projects while the step is `project` (the answers beside **Open a
  folder…**, which is `folders.pick` → `projects.open`, and **A new, empty folder…**); `kind` `{id, words, signs, how, empty}` while it is `kind` (`how` is
  `project_kind.in_words(signs)`, the chips are `signs`); `hand` how many tools are in the hand.
- `first_open.kind {kind}` or `{about}` → *Yes* sends the kind read, **It is something else…** another of the list; `about` is an empty folder's one line, read by
  `ideas.proposals {about}` (the cheaper tier; with no model, a spent budget or a stop, `code`, `read: false`). Kept with `project_kind.keep`; refused: *A kind
  is one of …*, *Say in a line what it is for*. `{ok, kind, read?}`.
- `first_open.tools_skip {}` → the adding card closed with no tool added: this run goes on to the parties (`tools_skipped`, not kept) → `{ok, line}` with
  *No AI tool: the Board opens, and nothing is worked on until you add one*.
- `projects.new_folder {parent, name}` → an empty folder made in `parent` (the folder the system's dialog chose) and **opened** (`projects.open`): `{ok, path, git}`.
  Refused in words, nothing left behind: a name that is empty, a path, a dot-name or too long (*Name the folder with a plain name: no slash, no leading dot*), a
  `parent` that is not there, a folder there already, one that `project_folder.refusal` forbids (the folder is removed again).
- The rest of the talk uses what is there: `projects.open`, `projects.start_git`, `ideas.proposals`, `ideas.party_save {first: true}`, `ideas.project_ask`.

### A.5 The table is laid at Start (decisions §232.1)

`realm/first_open.py` `laid(state_dir, root)`: **true once the project's first Start was pressed** (`laid: true` in `<state_dir>/project.json`, the file's other keys
left as they are: `project_kind.keep` and `project_stage.keep` write that file whole and keep it), **or when the project has a party of its own already**
(a page in its parties' folder but General's: General is written when a goal is first added, and is not a party the person made; this is the project made by
Orkline or an earlier Orkboard, laid at once). `lay(state_dir)` writes it, true only the first time.

`ideas.project_ask` / `ProjectQMixin.project_start` (**what Start sends**, after `ideas.party_save {first: true}`) lays the table first, and bumps the board's
revision once so the page plays the laying. The Board's snapshot gains **`laid`** (`gui/ideas.py` `snapshot`: from the cached part, true when the read breaks: a
broken page never hides the table); with no project open the host's own snapshot says `laid: false`. The phone's snapshot does not carry it (`COMPUTER_ONLY`: the first open is the computer's).

### A.6 The words (`realm/lexicon.py` `TERMS`)

`tool_order` (*the order the work moves on in*), `add_ai_tool` (*Add an AI tool*), `test_and_add` (*Test & add*), `add_another` (*Add another*),
`go_on_to_the_parties` (*Go on to the parties*), `put_back` (*Put back*), `which_project` (*Which project shall we work on?*), `table_laid` (*The table is
laid*). The rest of §232.11's words (*The project is*, *The project is here*, *The party's AI tool*, *Its level*) are B and C's, added with their faces. **The word
*shelf* is the code's only** (the mockup's `id="shelf"`); the interface says *AI tools*, *Add an AI tool*, *Put back*, never *shop*, *buy* or *belt*.

### A.7 Tests (A; all on the host, no browser)

`tests/test_tool_hand.py`: the order kept and cleaned; `settings.tool_order` by the person's order then the registry's; `harnesses.main` with an order, a chosen tool
that is on, a chosen tool that is off, an order that names none on; a key found by name and its value in no card; the third line's five states and the warning; the card's
three groups, the not-installed row never pickable, `first`; every refusal's words; `add`, `reorder` (a refused order changes nothing), `next_after`,
`put_back_plan` (the last asks), `take_out`/`restore` (the place, the billing, the main tool). `tests/test_tools_host.py`: the commands and the aliases (both names run
one Check; the old rows read it; the request is the same; the refusal reaches the page as a `CommandError`); the card begins its look; Test & add puts the tool in
the hand after it answers, saves it, makes the first the main tool, and offers the card no tool in the hand; a failed test adds nothing and says why in the tool's
words; each refusal comes before a request is made (a test's fake asks nothing); a key's value is in no snapshot and no file; a full hand adds no more; the order and
its first as the main tool; the billing by a key only when it is there; `tools.put_back_plan` says it and changes nothing; Put back sets the open projects' parties to the next tool and Undo sets them back; the last
tool asks, and nothing changes until `sure`; `tool_now` reads the order after a put back; **the phone allows none of it**. `tests/test_first_open.py`: the questions'
order, each step's state on a real folder (no project; no git; the kind read, answered *Yes*, refused; the empty folder's one line; the tools asked only with an empty
hand and not after `tools_skip`), `projects.new_folder` (made, opened, each refusal, nothing left behind), the table not laid until Start, laid once, laid at once
for a project with a party of its own, General alone no party, the file's other keys kept. `tests/test_board_alone.py`: the snapshot's keys now include `tools` and
`laid`.

## B. The hand

1. **The empty slot** (`hand/mana.js`): the potions' row ends with **an empty slot**: a potion's place in pixel dashes with a **+**, faint at rest (§185.1), lit
   (`.is-lit`, in the ink) while the Orkmaster asks for a tool (`first_open.ask` says `tools`); **not drawn when the hand holds six tools** (`tools.full`).
   The potions themselves are the hand's tools in `tools.order`'s order (the limits' rows, then a tool in the hand with no limits read is a muted potion,
   spec 140 C1: *Limits not read*). *orkUI first: `.ork-potion.is-empty`.* A press lifts the adding card (2); with the keyboard it is a button with *Add an AI tool*.
2. **The card that adds one tool** (`hand/addtool.js`, lifted as every hand card is, §176.4; it never grows wider than a hand card): *Add an AI tool · n of up to 6*
   (`tools.card`'s `n`, `max`). **AI tool**: the card's rows in its three groups (*Ready*, *Not signed in*, *Not installed*, `toolpick.js`'s words), a tool not
   installed with how to install it and not picked, **the first ready tool (`first`) picked**. **Paid by**: *Subscription* (picked: the tool's guess when it is
   *api*) or *API key*. **A third line that follows them**: the picked row's `lines[billing]`: `line`, with **Sign in** (`tools.sign_in {harness}`; Test & add
   waits for it) when `needs` is `sign_in`; the `warn` above it in the warn colour; for `no_key` the variable named and no field to type in (§232.10). **Test &
   add** (disabled while `needs` or `adding[tool].state === "running"`; on an API key *about $0.001* under it): `tools.test_add {tool, billing, risk_read}`; a
   failure says why on the card in the tool's words (`adding[tool]`: `line`, `action`, **Sign in** when `sign_in`); it answers when the tool is in the hand: **the
   card turns** (`fieldturn.js`'s motion): *<Tool> is in your hand. Add another AI tool?* with **Add another** (the card again, without the tools in the hand) and
   **Go on to the parties** (the first open; later **Done**); at the sixth tool it goes on by itself. An experimental tool asks its warning first (*Turn on … at my
   own risk*, `risk_read`); **Request a tool** stays (`tools.request`); *Found on this computer. Nothing else was run, and no key was read.* Closing the card with no
   tool added sends `first_open.tools_skip` and says *No AI tool: the Board opens, and nothing is worked on until you add one*.
3. **A potion pressed lifts its tool's card** (`hand/toolcard.js`; what a press did, *what used it*, becomes a link on it): the tool's mark, name and potion, its two
   shares in words (§192.3); **Paid by** *Subscription · API key* (the same third line; `tools.billing`); **the order the work moves on in**: the hand's potions as
   marks with this one framed and **←** **→** (`tools.order`; dragging a potion does the same; the first is the main tool); **Check** (`tools.check`, the result
   of `checks[tool]`); its tiers' models (Settings' *AI tools* rows, moved here: `ideas.tier_models` as they are set today); and **Put back**, with what follows said
   under it from `tools.put_back_plan` (its `line` and each party's `line`; read when the card opens, nothing changes). A tool is put back
   **between tasks, never inside one**, with **Undo** in the toast (`tools.put_back_undo {undo}`); **the last tool** asks first (`ask`) and is sent again with
   `sure: true`.
4. **The Orkmaster's setup cards** (`hand/setupcards.js`, `hand/state.js`): the Orkmaster's bubble says `first_open.ask`'s `line` (§201, `ork-think` while it reads) and the
   answers are cards in the hand, as every question for the person is (§206.6): **Open a folder…** (the system's dialog opened from the card: `folders.pick` /
   `folders.picked`, then `projects.open`), **A new, empty folder…** (the dialog chooses the parent, a one-line name, `projects.new_folder`) and the recent
   projects; for a folder with no git **Start git here** (`projects.start_git`) and **Choose another folder**; the kind: the signs read as chips, **Yes** and **It is
   something else…** (the kinds' list in the card; `first_open.kind`); an empty folder: *What is it for?* in one line. The page asks `first_open.ask` when the snapshot's
   `repo`, `laid`, `tools.hand` or the kind changes, never on a timer.
5. **Words** (`TERMS`, with their faces): *The project is*, *The project is here*, *The party's AI tool*, *Its level* (C); the rest are A.6's. `tests/test_gui_wording.py`
   checks them in the `html` templates' own text.
6. **Tests**: `tests/test_add_tool_browser.py` (a fake `tools.detect`): the empty slot is faint, lit when asked and gone at six; the card's groups and the first ready tool
   picked; the third line for each state; Test & add waits for a sign-in and for a key; the card turns on success and *Go on to the parties* leaves; a failure says why;
   a potion's card orders with ← and → and by dragging; Put back with its Undo, the last tool's question; the setup cards' answers move the question on.

## C. The table

1. **The parties are the Orkmaster's large card on the table** (`table/parties.js` becomes it: the one place of the parties, spec 100 §4; its half-and-half layout
   goes): dealt from the Orkmaster's head onto the table, the same card the first time and later from the empty chair and a party's *Edit*. It is wider than a lifted
   card (§176.4's *never grows wider* is a hand card's): **about 620 px at the wide width**, and never covers the potions; at the narrow width the card is the screen,
   one party a block. At its top **The project is** and the kinds' list (`ideas.proposals`' kinds, with what it was read from: `how`); under it the stages (*Idea*,
   *Being made*, *Live*; `ideas.stage`), the stage the project is at marked *The project is here* and set by a press on another's heading (`ideas.stage_set`).
2. **A party is one line** and its heads under it (`partyseats2.js`): **the line** its tick; its leader's head with **its AI tool's mark in the corner**, framed when the party
   follows the main tool and showing the tool it is on now, bare when a tool is set for the party (§192.4); its name; and **its size, a small switch** (*Lean · Standard ·
   Full*, the label face, one line high) at the line's end; the price of a goal is the switch's words (hover and the screen reader: *Standard: about $0.40–0.90 a goal*,
   `ideas.party_price`); its line of what it does is the name's words (hover), not drawn. **Under it its team**: **Does** after orkUI's sword and **Checks** after its
   shield (§189's), each a row of the seats' heads at the small size (24 × 22), the seats the size gives (spec 81 §2) as heads and **the seats the craft has and the size
   leaves empty as shadows** (the head's silhouette, dark, no face and no gear; *orkUI first: `.ork-race__head.is-empty`*), up to five who do and two who check.
   **Changing the size changes the heads at once**, nothing saved until Start or Save; under *Lean* the Checks are dimmed with *Lean: the leader does it, and checks it
   itself*. **A shadow is not pressed**, for now. **A member's head wears a tool's mark only when its tool differs from the party's.** **Release** is ticked and locked
   (*in every project*), its size locked at Lean. **The stages not reached** lie in one line of heads and names (*offered when the project is live*), a tick seating one now.
3. **At its foot** what the ticked parties cost together, said plainly (*Together ≈ $1.30–3.00 a goal at the API's prices. On a subscription it is taken from its limits
   instead.*), and **Start** the first time (it makes the parties by `ideas.party_save` then `ideas.project_ask`, A.5: the table is laid), **Save** after (*From the next
   task*).
4. **A head or a mark pressed opens its seat** (`table/seatpop.js`, §110.7), any head of a party, the leader's too; hover only marks it, so a phone and a keyboard reach
   it. The seat says its role and what it does; **its AI tool**: on the leader's seat **the party's AI tool** (*Main tool (<name>): follows it* first, then the tools in
   the hand; *The leader and every member set to As the party run on it*), on a member's **its own** (*As the party (<tool>)* first, then the tools in the hand); and **its
   level as three heads**, the seat's race in its three gears (§158's tier is the gear on the head; *orkUI first: the three levels' tiles*), each with its word (*Novice*,
   *Seasoned*, *Veteran*) and what a task (a leader's step) costs at it; under a leader set to Novice a line says the cost in quality plainly (*reads less of the project
   before it plans*). **Take off the seat** for a member, never for the leader. A seat set by hand keeps what was set and the party's size stays picked (spec 81 §2).
5. **Nothing of the table lies beside a form** (§232.2): a place over the pane (§142: Settings, Open a project, the update, Pair a phone, Remove party) covers **the whole
   table, its end included** (`frame/place.js`, `table/table.js`): no ring and no discard beside it. The Orkmaster's column and the hand stay as they are, since the work
   goes on under it (§142's *nothing traps the focus*).
6. **The window not yet laid, and the laying** (`table/laying.js`; the snapshot's `laid`): until the first Start the leaders' row holds **the Orkmaster alone** (no tabs, no
   empty chair, no door, no die); its column holds **no pile, only its bubble**; the table's end has no ring and no discard's place; the hand has **no + card and no deck,
   only the Orkmaster's cards and the AI tools at its right**. **A pile's heading appears with its first card**, never empty (this makes §206.3 precise). At **Start**
   (`laid` turns true while the page is open) the table is laid once, in order: the leaders sit down in their chairs, the empty chair and the door and the die appear, the + card
   comes to the hand with its seal lit once (§185.4's hover, played by itself), and the Orkmaster says *The table is laid. What shall we make first? Play the + card.* in
   its bubble; the ring and the discard's place come with their first content (§247.1). **Reduced motion: all at once.** A project opened with `laid` already true is laid
   at once, with no motion.
7. **Tests**: `tests/test_parties_card_browser.py` (the card's width, the kinds' list and the stage's mark, a party's line and its heads with the shadows, the size switch
   changes the heads at once and saves nothing, Start makes the parties and lays the table, the seat's tool and level); `tests/test_table_desktop_browser.py` (a place
   covers the table's end; the unlaid window has no tabs, die, ring, + card or piles; the laying's order and its reduced-motion form).

## D. Settings and the onboarding

1. **Settings keeps what is neither a tool nor a party**, in two groups (`shell/settings.js`): **This project** (Start plans by themselves, Work at night, A result that
   holds lands in dev, Push after merging, the Target) and **This computer** (Keep the computer awake, Your phone, Updates, the logs, When I am at the computer), and one line
   where the rest went: *AI tools are in your hand: press a potion, or the empty slot beside them. Parties, their size and their AI tool: the empty chair, or a party's
   Edit.* Settings is not a card (§232.9: a card is a decision waiting for the person). `js/settings.js`'s *AI tools* rows go.
2. **The onboarding's table of checkboxes, its Next and its Skip go** (`js/onboarding.js` `ToolsStep`, and the `onboarding.*` aliases of A.3 with them, `onboarding.tools`
   with its `next`); **the Security reviewer's hooks** (today's checkbox, off in focus) **are not asked here**. The first open is A.4's order: the window not yet laid (C.6) →
   the project (B.4) → the AI tools (B.2, **only when the hand is empty**) → the parties' card (C) → **Start** → the table laid.
3. **The start screen is the Orkmaster's first card** (`shell/projects.js` `StartScreen`, `OpenFolderPlace`): with no project open the pane shows the unlaid window (C.6) and
   the setup cards (B.4); *Open a project…* with a project open stays a place (C.5). *Ctrl+O* opens the same dialog.
4. **Not now** (§232.10): a key typed into Orkboard (the keychain's `orkcraft-ideas`, given to the tool's run) is a decision of its own later; a shadow pressed to seat a role
   beyond the size; any of this on the phone, which shows the tools as today (§223's bottle) and sets none.
5. **Tests**: `tests/test_first_open_browser.py`: **the first open from an empty folder to the laid table**: no project → *Which project shall we work on?* → *A new, empty
   folder…* → git → the kind's line → an empty hand's tools card → Test & add → *Go on to the parties* → Start → the table laid and the Orkmaster's line; the second
   project skips the tools; Settings has the two groups and the one line; `tests/test_gui_wording.py` follows.

## E. The column, and the put-off

### E.1 The column has a width of its own (decisions §236.3)

`frame/frame.css`: the grid's first track in `.frame[data-column]` is **`var(--column-w)`**, no longer a lane's `--col-w`; the table gains what the column gives up. The three piles
share one right edge. `hand/hand.css`'s first track (`--hc-first`) follows `--column-w` where it lay under the column, **so the hand's lanes keep standing under the table's
lanes**; check it at 1280 and 1920 px: a lane that moved is a bug of this part.

### E.2 A face-down card is tucked under the window's left edge (§236.1–2, 4)

- **The tuck is one constant**: `--column-tuck` on `.frame` in `frame/frame.css`, and `--column-w: calc(max(112px, 157px − var(--column-tuck)) + 16px)` beside it (the upright card's
  width, or the face-down card's shown part if wider, and 8 px gutters). **The owner's pick between 45 px and 30 px tucked is not made yet** (§236.5: *drawn first, the column
  at 45 px and at 30 px*, `docs/mockups/column-tuck/`, to be drawn by the spec's author; E.1, E.3 and E.4 do not wait for it): **the cheaper model builds with 45 px, which is §236.1's own *about 45 px of it under the edge, 112 px
  showing* (the column 128 px), and writes no other number**: at 30 px 127 px of the card shows and the column is 143 px. The pick is one line, `--column-tuck`, and nothing else
  changes; the browser test reads the property, so it needs no change either.
- **Geometry**: a face-down card (`.col-card--down`, 157 × 112, unchanged) lies with **`--column-tuck` of it under the window's left edge**, so `157 − --column-tuck` of it shows; the cut
  is the window's own edge (the column's box, `.col-scroll`'s `overflow-x: hidden`: no margin, no frame at its left), so it reads as a deck slid under the table's edge, never a box cut
  short. **Its seal is whole in what shows**: centred in the shown part (not the card's), its rune upright, and the running ring (`ork-sigil-sweep`) never under the edge; the ring's
  middle (§241: the heads, the play) and `.col-play` follow the seal's centre. **The pile's thin edges** (`.col-edges`) **are cut the same**. The upright card (112 px) is not tucked.
- **Hovered or focused it slides out whole**, to the right over the table (a transform of `--column-tuck`, so its whole 157 px shows; at once under reduced motion), and goes back when
  left; **its focus ring is drawn inside what shows**. A press does what it does (§206.3: the pile's list). Sideways is still *not agreed yet* (§206.3); the narrow width has no column.
- **Test** (`tests/test_column_tuck_browser.py`): the face-down card's left edge is `−--column-tuck` from the column's and its shown width is `157 − --column-tuck` (112 at 45); the seal's
  centre is the shown part's centre and the ring is inside the window; the card slides out whole on hover and on focus and goes back; the column's width is `--column-w` (128 at 45) and the
  three piles share one right edge; under reduced motion nothing animates; a face-up card is the same width as before.

### E.3 Hold on the route card (decisions §239.3, named by §247.2)

**Host** (`gui/ideas_route.py`): `ideas.route_hold {idea}` (`RouteMixin.route_hold`, in `route_commands`): a goal at its route card (`_routed`) is **held**: `ideas.save_state(...,
held_for="hold", held_until="")`, the board told; **nothing is spent** and nothing starts it by itself: `route_stop` says *it is held* (so `route_auto` does not send it to Talk) and
`route_tick` / `_backlog_next` (§239.1) never look at it (they read `held_until`). **Talk** (`ideas.talk`) clears it. It is offered **at any time**, beside **Talk**; **Later** stays beside
it when the limits run low. Event `route_held` (`event_log`). Refused as `route_later` is for a goal not at its route card. The goal's card says *Held* (`TERMS` `hold`); the pile's list shows it
under *In analysis* as it shows a goal put off.
**Face** (`hand/routecard.js`): the button **Hold**, `title` *Nothing starts it until you press Talk*, beside **Talk**. *Keep it* is **not** said (§247.2: only the drop question's).
**Test** (`tests/test_route_hold.py`): a held goal is not sent to Talk by `route_auto`, not started by the queue after the reset, started by **Talk**, and costs nothing; the wording test finds
*Hold* and no *Keep it* on the card.

### E.4 The pile says why it waits (decisions §239.4)

**Face** (`table/piles.js`, `column.js`): under *In analysis*, while goals put off wait for the reset, the pile's under-line (`.col-under`, the place of *writing: …* and *talked over: …*)
says **`waits for the reset · <day> <time>`** (`say()`'d, a state, never a count: the day's name when it is not today, the time in the machine's local time, as the potions' *back 14:00*).
It is read from the snapshot's ideas (`board_map`'s `held_until` of the goals in state `routed` with no `held_for`): the **earliest** of them. No line when none waits. *Hold*'s goals do not
make it. The hour on each row of the list is spec 138 B.5's.
**Test** (browser, `tests/test_pile_waits_browser.py`): the line shows with a goal put off and goes with none; it names the reset's day and time; a held goal is not named.

### E.5 The words

`TERMS`: `waits_for_the_reset` (*waits for the reset · <day> <time>*, §239.5). *Keep it* is **not** added (§247.2); *Hold* and *Later* are there.

## Order of building, and what each part must not do

1. **E.1–E.4 and A first**, either order; each merged as its own tests and the critical ones are green. **B after A; C after A; D after B and C.** A part never changes a decision's text: a
   point that cannot be built as written is said to the spec's author, not decided here. Nothing in B–E calls a tool: only Test & add and Check do, and the person pressed them.
2. **The faces' tests never call a real tool**: `tools.detect`, `tools.detect_others` and the request's `ask` are faked (`tests/test_tools_host.py`'s way).
3. **Every part keeps the frame** (CLAUDE.md): no list column, no drawer, no count of what waits, no question from a member straight to the person. The AI tools' mana stays at the hand's right,
   the discard on the table at its right, Release and Live in the portal ring's corners.
4. **Wording**: *ork* / *orks*, never the other word; the interface says *AI tool*, never a harness; *party* for what the code calls a goal or a track, *goal* for an idea. Code keeps
   its names (`tool_order`, `orc_id`, `.orkcraft/`). Labels say plainly what happens, and anything about money says it (*paid per token, by that key*, *about $0.001*).
5. **Open for the owner** (not decided here): the column's tuck, **45 px or 30 px** (E.2: a constant, built at 45); a shadow pressed to seat a role beyond the size and a key typed into
   Orkboard (§232.10).
