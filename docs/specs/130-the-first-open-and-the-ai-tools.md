# 130. The first open and the AI tools

Decisions §232 (1–12), changing §142, §176, §177, §185, §192 and §206. **Builds:** the cheaper model, part by part,
the spec's author reviewing and merging · **Review:** the critical tests and each part's own · P1.
The look is `docs/mockups/setup/index.html`, its eight looks. Copy the look into Preact, not the mockup's HTML.
This spec supplies the contracts and implementation choices: a builder needs CLAUDE.md, §232 and this spec, then the
source files named in its part. Specs 75, 81 and 100 §4 are replaced where described below; spec 128 is the format.

| Part | What | Where (and its tests) |
|---|---|---|
| **0. orkUI first** | the empty potion place, small size switch, head shadow, three levels | request in orkUI; local fallback in B's and C's sheets; `tests/test_design_system.py` |
| **A. Host** | ordered tools, discover/test/add/remove/billing/models; project answers, parties saved, laid state | `orkboard/settings.py`, `orkboard/realm/harnesses.py`; new `orkboard/realm/tool_settings.py`, `orkboard/gui/tools.py`, `orkboard/gui/tools_check.py`, `orkboard/gui/tools_models.py`, `orkboard/gui/setup.py`, `orkboard/gui/ideas_setup.py`, `orkboard/realm/project_setup.py`; exact seams in A; new `tests/test_tools_hand.py`, `tests/test_first_open.py`, `tests/test_setup_parties.py` |
| **B. The hand** | project questions, empty slot, adding card, tool card | `orkboard/gui/static/js/hand/mana.js`, `hand/state.js`, `hand/hand.js`; new `hand/setupcards.js`, `hand/toolcards.js`, `hand/toolbilling.js`, `hand/toolmodels.js`, `hand/toolcards.css`; new `tests/test_setup_hand_browser.py`, `tests/test_tools_hand_browser.py` |
| **C. The table** | large parties card, heads and seats, covered end, no empty piles, laying | `orkboard/gui/static/js/table/parties.js`, `table/partyseats2.js`, `table/seatpop.js`, `table/table.js`, `table/column.js`, `table/piles.js`, `frame/place.js`; exact seams in C; new `tests/test_setup_table_browser.py`, `tests/test_setup_seats_browser.py` |
| **D. Settings and the onboarding** | two Settings groups, old tool rows and first screen removed, common frame without a project | `orkboard/gui/static/board.js`, `js/shell/settings.js`, `js/settings.js`, `js/onboarding.js`, `shell/projects.js`, `shell/shell.js`; new `tests/test_setup_settings_browser.py`, `tests/test_first_open_browser.py` |

In the table and below, `hand/`, `table/`, `frame/` and `shell/` expand to
`orkboard/gui/static/js/hand/`, `orkboard/gui/static/js/table/`, `orkboard/gui/static/js/frame/` and
`orkboard/gui/static/js/shell/`; `js/` expands to `orkboard/gui/static/js/`. Python paths are written in full.
Every function named **new** is to be added, not searched for as an existing function. No module grows past about
600 lines: the new modules named here take the extracted responsibilities.

**Order.** Agree these contracts, request 0, then A, B and C can be built side by side. B uses the A replies below;
C uses the same replies and its own fixture for the laying phases. D's Settings and removal of the old screen can be
built alongside them against snapshots, but D's final wiring and first-open browser test follow A, B and C.
Merge A, then B and C in either order, then D; each part is a separate merge as soon as its tests and the critical
ones pass. B owns all `hand/` files, C owns all `table/` and `frame/` files, D owns the listed `shell/` files and
`js/settings.js` / `js/onboarding.js`, A owns Python and the glossary. B's new model editor does not import the old
Settings editor; D removes the latter. No two parts edit the same production file.

**Scope and precedence.** Desktop and the VS Code page, at wide and narrow widths. No new phone controls, cache
version or phone layout. A phone retains its existing bottles and reads; it cannot call these setup/tool mutations.
No key input, keychain write, new tool registration or press on a shadow. Six means six tool ids, including API tools;
there is no seventh paid slot and no `+n` overflow in the new desktop hand. §232 wins over that leftover caption in
mockup look 4 and its reference to the phone's arrows. Settings is a place, the parties a large card on the table,
and tool/project questions are hand cards. Work continues while any of them is open.

## The words

1. `orkboard/realm/lexicon.py` `TERMS`: keep `ai_tool` and `party_size`; add `tool_order` with the words **the order
   the work moves on in**. Add terms for **Add an AI tool**, **Test & add**, **Add another**, **Go on to the parties**,
   **Put back**, **Which project shall we work on?**, **The project is**, **The project is here**, **The party's AI tool**,
   **Its level**, **The table is laid**. Use snake-case ids matching those phrases (`add_ai_tool`, `test_and_add`,
   `add_another`, `go_on_to_parties`, `put_back`, `which_project`, `the_project_is`, `project_here`, `party_ai_tool`,
   `its_level`, `table_laid`). Preserve existing terms and their `was` spellings. The word `shelf` stays in code only.
2. The interface says **AI tools**, **AI tool**, **Paid by**, **Subscription**, **API key**, **Main tool**, **Ready**,
   **Not signed in**, **Not installed**, **Sign in**, **Check**, **Test again**, **What used it**, **Request a tool**,
   **Undo**, **Done**, **Close**. No shop, buy, belt or harness in the interface. A tool is in the hand or it is not;
   a pending test is not a third enabled state. A removed tool's existing task may finish.
3. Tiers keep their code ids: `laborer` → **Novice**, `warrior` → **Seasoned**, `elder` → **Veteran**. Sizes keep
   `lean` → **Lean**, `standard` → **Standard**, `full` → **Full**. Stages keep `idea` → **Idea**,
   `being_made` → **Being made**, `live` → **Live**. Code's `goal` is a party, `idea` is a goal; no keys are renamed.
4. Labels/headings/buttons use orkUI's label face; the person's line, folder names, tool errors and explanations use
   its body/code faces. All new visible strings are specified in the owning part below. Values in angle brackets
   are substituted, escaped text, never HTML. Prices in the mockup are examples; none is a production constant except
   the explicitly approximate **about $0.001** test estimate.

## 0. What orkUI must draw first

orkUI is another repository, `github.com/orkCraft/orkUI`. Ask its maintainer for these four pieces, with a preview at
normal and small sizes, dark/light office tokens, keyboard focus, disabled states and reduced motion. This document
is the request's content; building this spec does not itself send a message or change that repository.

| Piece to ask for | States and anatomy | Fallback drawn here until the copy contains it |
|---|---|---|
| `.ork-potion.is-empty` | potion silhouette in pixel dashes, no liquid or cork fill; + in its middle; `.is-lit` in the ink, faint otherwise | B's `hand/toolcards.css` `.hand-tool-empty`: an empty place made with dashed edges using `--ork-edge`, `--ork-ink-faint`, `--ork-ink`; existing `Icon` plus. Keep the bottle's slot dimensions; do not invent a bottle sprite. |
| small three-way size switch | one label line high, Lean / Standard / Full; picked ink fill, hover, focus and locked options | C's `table/parties.css` `.parties-size-small`: three existing `.ork-btn` buttons in a radiogroup; `--ork-type-label`, `--ork-line`, `--ork-edge`, `--ork-ink`, `--ork-on-ink`, existing `--ork-notch`. Prices in title and accessible label, not a second line. |
| `.ork-race__head.is-empty` | race's head silhouette, no face or gear, 24 × 22; no hover or pressed state | C's `.parties-seat-shadow`: mask an existing Novice head's alpha in `--ork-ink-faint`, low opacity; no hand-drawn head. A noninteractive span with the role's empty-seat label. |
| three levels' tiles | one race in its three gears, word and price under each, selected frame, focus and disabled | C's `.seat-levels`: three existing `.ork-card`/button pieces in a grid, existing heads, `--ork-panel`, `--ork-edge`, `--ork-ink`, `--ork-notch`, type and spacing tokens. |

Reuse the existing Orkmaster bubble and tail (`table/ask.js`, `table/ask.css`); a fifth tail design is not needed.
Motion uses `--ork-motion-base` and orkUI's turn/sigil sweep. Local sheets supply layout, masks of existing assets,
and token-based states only, no palette, font family, corner polygon or raster of their own. Do not edit
`design-system/orkui`. Once orkUI ships the pieces, copy it with `python -m orkboard.design.orkui <orkUI>`, keep its
stamp, replace the four fallback selectors with those classes, and run `tests/test_design_system.py` and B/C's tests.
0's delivery does not block A–D: the fallbacks are the defined implementation until then.

## A. Host

### A.1. Files and ownership

| File | Functions/classes to change or add |
|---|---|
| `orkboard/settings.py` | `MachineSettings`, `to_dict`, `from_dict`, `main_tool`, `tool_order`: persist the order and removal redirects below. Extract tool cleaning to the new module so this already 600-line file does not grow. |
| new `orkboard/realm/tool_settings.py` | `clean_order`, `order_of`, `main_of`, `effective_tool`, `key_names`, `billing_of`, `put_back`, `restore`: pure machine-data transformations; no GUI imports. |
| `orkboard/realm/harnesses.py` | `main(enabled, chosen="", order=None)` accepts the order, keeps old two-argument callers; `for_party` gains optional enabled ids, no implicit Claude for an empty explicit set. |
| new `orkboard/gui/tools.py` | `Tools` with `commands`, `snapshot`, `detect`, `test_add`, `check`, `cancel`, `order`, `billing`, `put_back`, `undo`, `request`; one service per `Orkboard`, usable with no project and no onboarding. |
| new `orkboard/gui/tools_check.py` | `CheckRunner.start`, `cancel`, `_run`, `_finish`; extract `Onboarding.check`, `_check_run`, `_checked` here, keep injectable ask/clock and host-thread completion. |
| new `orkboard/gui/tools_models.py` | `rows(machine, tool)` and `set_model(machine, tool, tier, model)` supply the tier editor's reads/writes. |
| `orkboard/gui/onboarding.py` | `Onboarding.wanted`, `commands`, `_save_machine`: Orkboard with the new service has no active tools step or auto-enabled detection; old command aliases delegate explicitly to the service, never bulk-enable discovered tools. Keep public constants and non-Board subclass hooks. |
| `orkboard/gui/board_host.py` | `Orkboard.__init__`, `snapshot`, `shown`, `command`, `tick`, `_mana`, `_follow_main`, `COMPUTER_ONLY`; register tools/setup, publish their state, catch their errors, refresh completion; `BoardPhone.allowed` denies the new commands. Extract registration/snapshot helpers into `gui/setup.py` and `gui/tools.py`, not more logic in this already large host. |
| `orkboard/gui/board_projects.py` | `Projects._open_cmd`, `_show`, `_start_git`, `commands`; new `_create_cmd` for an empty child folder, notify setup when a project changes. |
| new `orkboard/gui/setup.py` | `Setup.enter`, `snapshot`, `commands`, `answer`, `tools_done`, `_read`, `_read_done`; machine-host coordinator of the project questions, not the later `project_q` questions. |
| new `orkboard/realm/project_setup.py` | `read`, `begin`, `confirm`, `laid`, `finish`: merge keys in `.orkcraft/project.json`, keeping kind, stage and other existing keys. |
| new `orkboard/gui/ideas_setup.py` | `SetupMixin.setup_parties`, `setup_save`, `seat_price`, `setup_commands`; validate a whole parties draft before writing it; added to `Ideas` in `orkboard/gui/ideas.py`. |
| `orkboard/gui/ideas_project.py`, `orkboard/gui/ideas_party.py`, `orkboard/gui/ideas_goals.py` | `ProjectMixin.tools`, `party_presets`; `PartyMixin.party_price`; `GoalsMixin.goal_save`, `_tool_asked`, `_tools_asked`, `_tiers_kept`, `_size_kept`: enabled tools only for new picks, explicit seat levels preserved, price the actual draft. Extract shared validation/application into new `orkboard/gui/ideas_party_save.py` `prepare` / `apply` for both single saves and setup saves. |
| `orkboard/realm/party_recipes.py`, `orkboard/realm/party_presets.py`, `orkboard/realm/goal_team.py` | `sized`, `tiers_for`, `_row`; `tiers_of`, `set_tiers`, `seat_role`, new `tier_overrides_of` / `set_tier_overrides`: occupied teams and hand-set levels below. |
| `orkboard/realm/party_price.py` | `price`, `task_usd`, new `seat_price`: use explicit tool and level when quoting a draft; do not price a different saved team. |
| `orkboard/gui/ideas_roles.py`, `orkboard/core/idea_lead.py` | `RolesMixin.party_of_idea`, `tiers_of_idea`; `LeadMixin.leader`: pass explicit seat overrides into `goal_team.seat_role(r, tiers, tier_overrides=None)` for actual task/leader selection as well as heads. |
| `orkboard/realm/tool_now.py`, `orkboard/gui/ideas_mana.py` | `now`, `api_tool`, `follow`; `ManaMixin.tool_now`, `mana`, `mana_tick`: order, effective billing, removed pins and no-tool holds. |
| `orkboard/core/idea_runner.py`, `orkboard/core/idea_keeper.py` | runner `tick`, `tool_of`, `pinned_tool`, `_launch`, `_work`; keeper `_may_run`, `tool_now`, `_claim`, `_claude`, `_claude_work`: resolve before launch, freeze a task/step's tool, model and billing; no new model work with an empty hand. |
| `orkboard/core/op_runner.py`, `orkboard/realm/tool_run.py` | `OpRunner.tick` and `tool_run.resolve` / `ask`: use the same empty-hand guard for automatic operations and direct `main` calls; explicit test calls are the exception. |
| `orkboard/gui/ideas_map.py`, `orkboard/realm/board_map.py`, `orkboard/realm/lexicon.py` | `MapMixin.project_of`, `marks_of`, `board_map.build`, `TERMS`: laid and effective seat data, the words above. |

### A.2. Machine tools and the boundary between tasks

1. Persist `machine.tool_order: [id]` and `machine.tool_replacements: {removed_id: next_id | ""}` beside existing
   `tools`, `main_tool`, `tier_models`; they live in the same `~/.config/orkcraft/settings.json`. `tools[id].enabled`
   means exactly **in the hand**. Keep disabled entries' billing/models for a later add; no other enabled bit.
   `clean_order` removes unknown/duplicate/off ids and appends enabled ids missing from an explicit order in registry
   order. With no saved order, migrate the old enabled `main_tool` first, then the other enabled ids in registry order.
   Persist the normalized order on the next mutation. Never enable a tool just because it is installed. Six is the
   limit for this registry's six tools. `main_tool` is kept for shared-state compatibility and mirrors the first id,
   or `""`; `harnesses.main` returns `None` and `settings.main_tool` returns `""` for an explicit empty hand.
2. `settings.tool_order(machine)` reads the list; quota output order does not decide it. Resolve `main` from that
   first id; use the next subscription with room, wrapping once, when it is dry. Preserve §177's reserve rule:
   automatic work moves at the reserve, a person's work and keeper steps may spend it. A party/member pinned to an
   enabled tool still waits when it is dry. Every subscription dry still asks **Go on, paid** / **Wait** through the
   existing paid card; reorder/removal never supplies that yes. An API tool chosen as main by the person is an
   explicit paid choice. Effective API billing from an environment key counts as API for this rule too.
3. Removing a tool disables it and removes it from the order immediately for future launches; it never cancels a
   running process. Record a redirect to the next remaining id after its old position, wrapping once; `""` if none.
   `effective_tool` resolves a pin through these redirects, detects cycles, and returns `""` with no tool. If the
   redirect ends empty and tools have since been added, use the new main. A pin whose id is enabled resolves to itself.
   This machine-local redirect covers closed projects when they reopen without rewriting their party pages. Its
   effective tool is shown on the head; saving a new pick replaces the old pin. Re-adding a removed tool clears its
   redirect. A removal redirect is an explicit change, distinct from a dry pinned subscription waiting.
4. Resolve and capture `tool`, `model`, `billing` at `_launch`, in the plan task, and at `_claim` in the keeper's
   thread-local step context. `_work` uses the captured values: today it resolves again, which can switch a task
   after its launch. The task's internal retry and gate keep them. A new task/step resolves again; a person starting
   a failed task again is a new launch. Change of billing/order/models/seat levels affects only new launches. Test
   removal between `_launch` and `_work`, not only before a task starts. A local service never kills a CLI sign-in
   or logs the person out on **Put back**.
5. With no tool, leave goals/tasks queued, not failed, and do no automatic model calls. The bubble/hold says
   **No AI tool: add one from the empty slot beside the potions**. A loaded goal remains in the column. Remove every
   production `or "claude"`/`or HARNESS` fallback along the named runner/keeper/main-call path for an explicit empty
   hand; compatibility tests with no machine provider may still inject their harness. No GUI service is imported
   by core or realm to implement this guard.
6. `key_names(tool, environ)` returns names of nonempty variables from `tool_errors.TAKES_KEYS`, in its tuple order,
   never values: currently Claude's `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`; Codex's `CODEX_API_KEY`; Cursor's
   `CURSOR_API_KEY`. Do not invent variables for Antigravity, Hermes or pi. Those tools' API option is disabled with
   **No environment key is supported for this tool yet**. The first present variable is `key_name`. No keychain read
   or write, no key/secret field in commands, snapshots, events or saved settings. Discovery uses `shutil.which`
   and retained sign-in status, not `tools.detect()` (which runs `--version`). No credential value is needed to draw
   the card. Unknown sign-in is represented as `null`, said as **Sign-in not checked yet**; the person can **Sign in**
   or explicitly **Check**. A successful subscription check supplies the positive status.
7. Requested billing is `subscription | api`; effective billing is `api` when a listed environment key wins, else
   the requested value. Before a paid check or billing save the host returns that warning and requires the current
   acknowledgement (`ack_key` equal to the shown variable name). A changed key name invalidates it. No extra
   confirmation dialog: the **Test & add** or **Save** press after the warning is the acknowledgement. Selecting
   Subscription cannot clear the environment or promise subscription billing. Re-read presence before launching;
   an environment change that newly makes automatic work paid holds it for the existing paid decision.

### A.3. Tool commands and snapshot (B's stub contract)

All new tool commands are desktop host commands, work without a project, and return JSON. Invalid input returns
`{ok:false, error:<plain line>, code:<id>}` without mutation. Shared codes: `unknown_tool`, `not_installed`,
`not_in_hand`, `full`, `sign_in`, `no_key`, `key_changed`, `risk`, `stale`, `busy`. Errors remain on the calling card.
Serialize mutations in the host thread; a worker posts its completion through `host.call`. `rev` is a monotonically
increasing host-lifetime integer, incremented on a changed tool state. Clients replace state only with a newer rev.

**`ToolState`** is the top-level snapshot's new `tools` field and the reply of `tools.state {}` / `tools.detect {}`:
`{rev, order:[id], main:id|"", max:6, rows:[ToolRow], checks:[CheckRow]}`. `rows` contains the whole registry,
Ready then Not signed in then Not installed, registry order within a group. `ToolRow` is
`{id, name, mark, installed:bool, signed_in:true|false|null, ready:bool, in_hand:bool, billing, effective_billing,
key_names:[name], key_name:name|"", key_supported:bool, warning:string, install:string, login:string,
experimental:bool, risk:string, tiers:bool, removing:bool}`. `ready` means installed and known signed in; `removing`
means off with a captured task/step still using it, not another place in the hand. `tools.detect` refreshes names,
PATH presence and cached sign-in status only; it spends nothing. The environment is the running host's environment;
**Test again** cannot import variables newly exported in an unrelated terminal.

`CheckRow` is `{id, tool, action:"add"|"check", state:"running"|"ok"|"failed"|"cancelled", ms:int|null,
billing, effective_billing, kind:string, line:string, action_line:string, detail:string, sign_in:bool}`.
Absent error fields are `""`/false; details are bounded to 4,000 characters and secrets redacted before serialization.
Reuse `tool_errors` classification, failure words and `sign_in.CHECK_PROMPT`. Successful tests use the registry's
lightest model (`laborer`, ignoring a person's more expensive tier override for this test), CLI default when the
registry has no tiers. Only a press sends this one request, never opening a card or selecting a tool.

| Command → service method | Arguments | Reply and effect |
|---|---|---|
| `tools.state` / `tools.detect` → `snapshot` / `detect` | `{}` | `ToolState`; no subprocess or model request. |
| `tools.test_add` → `test_add` | `{tool, billing, request:<unique client id>, risk_read?:true, ack_key?:name}` | `{ok:true, check:<id>, tools:ToolState}` immediately with a running check. Validate installation, risk, sign-in (false blocks), API key and capacity before the request; reserve one of six places while checking. On success enable and append, save settings, publish state. Failure adds nothing. Same request id returns the same check, never a second spend. |
| `tools.check` → `check` | `{tool, billing?, request, ack_key?, risk_read?:true}` | Same reply, action `check`; checks a picked candidate or a tool in the hand, never adds or saves billing. This is how an unknown sign-in is checked. Known false subscription status waits for sign-in. A candidate's experimental warning requires risk_read before this check too. |
| `tools.cancel` → `cancel` | `{check:<id>}` | `{ok:true, tools:ToolState}`; cancels its add intent and releases its reserved place; a late worker cannot add it. An already completed check stays completed. |
| `tools.order` → `order` | `{order:[all in-hand ids exactly once], rev}` | `{ok:true, tools:ToolState}`; reject missing/extra/duplicate ids or stale rev. Save order/main together, publish every open Board's changed effective marks. |
| `tools.billing` → `billing` | `{tool, billing, rev, ack_key?}` | `{ok:true, tools:ToolState}`; require in-hand id, current rev and the same key/sign-in conditions as adding; save the choice for future launches only. |
| `tools.card` → new `Tools.card` | `{tool}` | `{tool:ToolRow, models:[ModelRow], affected:[AffectedRow], next:id\|"", last:bool, rev}`; no run. Read for one tool in hand, fresh before removal. |
| `tools.model` → new `Tools.model` | `{tool, tier:"laborer"\|"warrior"\|"elder", model:string, rev}` | `{ok:true, models:[ModelRow], tools:ToolState}`; `""` resets to latest; validate through `settings.clean_tier_models`, preserve the other tools/tiers. |
| `tools.put_back` → `put_back` | `{tool, rev, sure?:true}` | Last tool without `sure`: `{ok:false, code:"last_tool", error:<A.5's last-tool words>, last:true, affected:[AffectedRow], rev}`. Success `{ok:true, tools:ToolState, undo:<token>, affected:[AffectedRow]}`; no process stopped. |
| `tools.undo` → `undo` | `{token}` | `{ok:true, tools:ToolState}`; restore removed membership, billing, redirect and its old position (bounded by today's list), preserving unrelated changes. Token lives 30 seconds; duplicate use is idempotent. Refuse full hand or a later edit to the same id with `stale`; never overwrite that edit. |
| `tools.request` → `request` | `{name:string, link?:string, note?:string}` | `{url:string}`; reuse `Onboarding.request`'s 80/300/1,000-character bounds and issue URL construction. Opens a filled request only; sends nothing. |

`AffectedRow` is `{project:<folder name>, path:<open project path>, party:<slug>, name:<party name>,
seat:<role slug>|"", seat_name:string, from:id, to:id|"", running:bool}`. List each explicit party/seat pin on the
tool in **all open projects**, not only the current tab. Closed projects use the persisted redirect when opened.
`next` is the immediate next remaining tool in order, not a claimed available subscription; a dry one still waits,
and an API successor still follows the paid-consent rule. A row with `seat:""` is the party's own pin.

`ModelRow` is `{tier, label, chosen:string, now:string, options:[[value,label]], price:string}`. Keep the Settings
editor's shape; build options from `Harness.models`, `Harness.families` and `model_families`' cached catalogue,
not an invented host `town.settings` (Orkboard does not register it). No model-list subprocess on opening the card;
a stale/absent catalogue gives the registry families and **Another model…**. `price` is empty when unknown.

Retain existing `tools.sign_in {harness, auto?:bool, by?:"browser"|"terminal"}`, `tools.sign_in_done {harness}`,
`tools.sign_in_cancel {harness}` in `orkboard/gui/board_host.py`: start returns a sign-in entry, done/cancel an entry
or null. An entry is `{harness,tool,mark,state,by,auto:bool,type,since:number,where,why,command,waiting:int}` from
`orkboard/core/sign_ins.py` `SignIns.start`, `done`, `cancel`, `_public`; top-level `sign_in` remains its list of
unfinished entries. Keep `shell/signin.js` as their renderer. They do not add the tool. On completion update
`ToolRow.signed_in` and rev.
B uses `signIn` / `SignInButton` and does not implement a second login. `onboarding.check`, `.detect`, `.request`
may delegate for old callers; `.tools` and `.skip` must never enable untested tools in the new Board flow.

### A.4. Project questions, parties and the laid state (B/C/D's stub contract)

1. `.orkcraft/project.json` gains `setup:{version:1, confirmed:bool, laid:bool, start_id:string, tools_done:bool}`.
   `begin` writes `laid:false` before the new setup can save any party. Missing setup on a project with any party
   other than the legacy `general` means laid immediately, including parties made by Orkline; no animation on open.
   Missing setup with only General/no party means unlaid. An explicit false wins while a first Start is incomplete,
   even if it already wrote a party. A true never becomes false after a party is removed. Writes preserve the other
   `project.json` keys. Machine `onboarded` cannot stand for a project's laid state.
2. Top-level desktop snapshot gains `setup:SetupState`, even with no project, and `tools:ToolState` above.
   `SetupState` is `{version:1, path:string, name:string, phase:"folder"|"git"|"reading"|"about"|"kind"|"tools"|"parties"|"done",
   rev:int, laid:bool, confirmed:bool, kind:{id,words,signs:[string]}, how:string,
   stage:{stage,read,kept}, read:bool|null, error:string, laid_id:string}`.
   Empty path/name, empty kind id/words/signs, `how:""`, stage `idea`/`idea`/false and `read:null` are the no-project
   defaults. `laid_id` is the successful Start's id, empty for imported/legacy laid projects. Also add
   `ideas.map.project.laid` and `.laid_id` from the same reader; never infer laid in JS from `goals.length` when
   the field exists. Top-level `mana` gains `order:[id]` and `empty:bool`; empty gives `main:""`, `now:null`,
   `paid:null`. Keep existing mana/limit fields and quota history. The desktop hand filters those limits by tools.order.
3. `Setup.enter(project)` picks folder with none, done for laid, git for no git, reading for a new unconfirmed
   project, then about for empty or kind for another kind. Reading uses `project_kind.read_full` and
   `project_stage.current`: names/counts (walk at most 2,000 entries; skip .git, .orkcraft, dependency directories;
   only package.json dependency names may be read). `how` is joined signs through `project_kind.in_words`, never
   an invented framework claim. `reading` is published before the worker begins; completions carry path/rev and
   cannot replace a different project's setup. No paid call to read a nonempty folder.
4. `setup.answer {path, rev, answer:"yes"|"kind"|"about", kind?:id, about?:string}` →
   `{ok:true, setup:SetupState}` or `{ok:false, code:"stale"|"invalid"|"no_tool", error:string}`.
   `yes` confirms the displayed kind/stage; `kind` chooses a KINDS id and confirms it; `about` takes one line of at
   most 300 characters, calls `orkboard/core/idea_kind.py` `read` once through the keeper, and returns phase kind for confirmation.
   No tool/no available call: return `{ok:true, setup:SetupState}` with phase kind, `read:false`, the kind picker open
   and **No AI tool could read the line. Pick a kind.** in setup.error;
   do not secretly run Claude. Nothing keeps the line beyond the current call. Empty-hand users can pick a kind first,
   then add a tool in the decided order; there is no circular requirement to run the empty-folder call before adding one.
   The kinds are `empty`, `mobile`, `game`, `web`, `backend`, `data`, `wiki`, `design`, `texts`, `code`, with the words
   in The words / B.4. Confirmation persists kind/stage and setup.confirmed. Next is tools only if the hand is empty
   and setup.tools_done is false, otherwise parties. A second project skips tools when this computer has one.
5. `setup.tools_done {path, rev}` → `{ok:true, setup:SetupState}`: marks this project's tools step answered,
   moves to parties, permits zero tools. Used on Go on to the parties, close without a tool, or the sixth success.
   Reopening before Start stays at parties. Pressing the empty slot can still add a tool at any point.
6. Keep `projects.list {}` → `{current:path|null, open:[{path,name,git,working,needs_you,review}], recent:[{path,name}]}`;
   `projects.open {path,device:"desktop"}` → `{ok:true,git:bool}` or `{error:string}`; `projects.start_git {path}` →
   `{ok:true,said:string}` or `{error:string}`; `projects.use {path}` → `{ok:true}`. The next snapshot carries setup.
   On git failure stay at the same card. Start git uses `realm/project_folder.py` `start_git`, including its first
   commit; say that before the press. Choose another folder abandons this question, never starts git.
7. Keep `folders.pick {start?:path}` → `{token}` and `folders.picked {token}` → `{state:"open"}` |
   `{state:"done",path}` | `{state:"none"}` | `{state:"error",why}` (`gui/folder_dialog.py`, `start` / `result`).
   For **A new, empty folder…**, pick its parent with that dialog, then ask only **Folder name** and **Create folder**
   on the same card. New `projects.create {parent, name}` → `{ok:true,path,git:false}` or `{error:string}`. It makes
   one child with `Path.mkdir(exist_ok=False)`, refuses blank names, `.`/`..`, separators, a taken path and an
   unreadable parent, then opens it through Projects.open. Never erase or reuse a nonempty folder. The native picker
   cancel changes nothing; unsupported native dialog exposes the path field on the card (**Folder**, **Open folder**).
8. New `ideas.setup_parties {kind?:id}` → `{kind:{id,words,signs}, stage:{stage,read,kept}, laid:bool,
   parties:[PartyDraft], revision:string}`. A preview `kind` reads that kind's recipes without saving it. `PartyDraft`
   is `{id,slug:string,name,line,craft,stage,locked:bool,on:bool,leader,build:[role],check:[role],size,team:[role],
   every:[role],tool:id|"",tools:{role:id},tiers:{role:tier},tier_overrides:{role:tier},
   sizes:{lean|standard|full:{leader,team,tiers,size}},seats:[Seat]}`. Include every existing party, also custom/old
   ones absent from today's recipes, then unmatched offered recipes; match by recipe id, then leader for a legacy
   party. `slug:""` means not yet made. `Seat` is `{slug,name,band:"lead"|"build"|"check",does:string,
   head:{race,tier},tool:id|"",tool_effective:id|"",follows:"main"|"party"|"own",tier_override:tier|""}`;
   seats includes candidate empty roles, leader first. `build` / `check` are the craft's candidates, not occupancy.
   `revision` is a digest of the project's kind, stage and party configurations; stale saves are refused.
9. Size semantics here restore spec 81 §2 as §232 requires: Lean leader only, Seasoned; Standard leader Veteran,
   first two builders and first checker Seasoned; Full up to five builders Seasoned and two checkers Veteran,
   leader Veteran. Release stays leader only, Lean, Seasoned by default. `party_recipes.sized` currently returns the
   same squad at every size: change that, and `tiers_for`'s current Standard first-builder-only result. Existing
   parties are not resized on reading. A press on a size replaces its draft team with that size's team; hand-set
   levels and tools of seats that remain survive. Keep explicit levels separately as `tier_overrides` in party
   front matter, over size tiers; no write to a shared Agents role. `seat_role` honours this explicit override first,
   then an existing hand-set Agents model, then size tiers. Removing a seat prunes its tool/level overrides.
10. New `ideas.setup_save {path, revision, request:<id>, first:bool, kind:id, stage:id, parties:[{id,slug,on,
    name,line,leader,size,team,every,tool,tools,tier_overrides}]}` → `{ok:true, saved:[{id,slug}], laid:bool,
    laid_id:string, project_ask:{ok:true,asked:bool,why?:string}}` or `{ok:false,code,error,party?:id,saved?:[{id,slug}]}`.
    Only on rows are created/updated; made rows cannot be unticked here (Remove party remains its own place).
    Validate the whole draft first: exact role ids, at most five/two, tool membership, tiers, valid kind/stage,
    Release present/locked/Lean, no removal of a member with work open (**<Name> has work open: it cannot leave**).
    The leader cannot be removed. Save through shared `prepare` / `apply`, suppress per-party model reads until the
    batch finishes. Keep a `.orkcraft/setup-save.json` journal of request, normalized draft and saved id→slug rows;
    retry of the same request resumes without making duplicate parties. On write failure return `save_failed`,
    keep explicit laid false on first Start and keep the journal. Do not claim a failed Save rolled back completed
    filesystem writes; return `saved` with the error for retry. Block a different request until it is recovered.
    On all saves succeeding keep kind/stage, then `project_setup.finish` records laid true and first request as
    laid_id; only the first Start calls existing `ideas.project_ask {}` (via `ProjectQMixin.project_ask`). Its reply
    is `{ok:true,asked:bool,why?:string}`; no tool/error there does not undo Start. Retry returns the stored result
    and never asks twice. Save after Start does not ask it. Machine onboarded becomes true at successful Start.
11. New `ideas.seat_price {leader,team,size,seat,tool,tiers}` → `{unit:"task"|"step", levels:[{tier,usd:number|null}]}`,
    three levels in Novice/Seasoned/Veteran order. Use `party_price.seat_price` with `idea_target.floor(tier, tool)`
    for an unmeasured seat, and matching tool/tier measurements when present; never use another tier's average.
    Extend `ideas.party_price {leader,team,every,size,tool,tools,tiers}` to price the draft's occupied seats, not
    `goal_team.price_team`'s old squad approximation; reply retains `{low,high,learned,ideas,checks,pitch?,way,hints,types}`,
    with low/high null for unknown price. A no-tier tool uses its own measured cost or unknown. `ideas.goal_save`
    additionally accepts `tier_overrides` for an existing seat changed outside the large card; returns `{slug,notes?}`.
    Check tool availability and busy removals on every such save, even without size. Its existing fields/commands stay.
12. `ideas.map.goals[]` gains `tool_effective`, `follows_main`, `tier_overrides`; each leader/member head row gains
    `tool_effective`, `follows` and `tier_override` with the Seat meanings above. Stored `tool`, `tools`, `tiers`
    stay. `MapMixin.marks_of` uses the effective result, preserving framed default and bare pinned marks and dry
    waits. `tools` and `setup` are added to `COMPUTER_ONLY`; `BoardPhone.allowed` explicitly rejects `ideas.setup_parties`,
    `ideas.setup_save`, `ideas.seat_price` despite its broad `ideas.*` allowance, as well as new tools/setup commands.
    Existing phone reads and its existing party commands keep their contracts; no new controls are exposed there.

### A.5. Words and tests

Tool refusal lines: **That AI tool is not found here**, **<Tool> is not in your hand**, **Your hand already has six
AI tools**, **<Tool> is experimental: read its warning first**, **The AI tools changed. Try again.** For the last
removal: **Without it nothing is worked on: goals wait in the Orkmaster's column until you add a tool**.
Tool failures retain the tool's own words (redacted, plain text). Project validation returns a plain reason on its
card, never a toast claiming success. Setup errors do not become a goal's failure card.

New tests, with fake harnesses/clocks/environment and temporary settings/projects (no real tool or sign-in):

- `tests/test_tools_hand.py`: migration and cleaning, explicit empty order, first-added main, exact reorder and
  stale rev, six including pending adds, duplicate request, cancel/late success, missing/not-signed-in/risky cases,
  environment names but no values in JSON/events/settings/errors, precedence warning/ack, effective API excluded
  from subscription fallback, models saved/reset, last removal with/without sure, Undo and concurrent edits. Remove
  with two projects open and one closed; named party/member consequences, redirected pin on reopen. Freeze the tool
  through a launch race/internal retry; subsequent task/step uses the new tool; empty hand invokes no keeper,
  runner or Operations model; after add work can proceed. Preserve the all-dry paid permission and pinned-dry wait.
- `tests/test_first_open.py`: no project, native cancel/failure, create child/refuse existing path, no-git yes/no,
  read/signs/stage, stale reading completion on switch, empty-folder line once/no-tool fallback, kind confirm,
  second project's tools skip, close with zero tools, setup restart, imported parties immediately laid, explicit
  false after interrupted Start, true after all parties later leave. No model call before an explicit test/about
  or Start; phone rejects all new mutations and receives no setup/tool detail.
- `tests/test_setup_parties.py`: all three teams/tiers, Release, draft read writes nothing, custom parties retained,
  size change preserves seat overrides and independent Agents roles, seat pricing by tool/tier, invalid/busy last
  row refuses before any write, write failure/retry avoids duplicates, first Start asks once and stays successful
  when project_ask cannot call a model. Snapshot marks match the effective party/member tools and levels.
- Existing regression files: `tests/test_settings.py`, `tests/test_tools.py`, `tests/test_tool_now.py`,
  `tests/test_sign_in.py`, `tests/test_projects.py`, `tests/test_party_tool.py`, `tests/test_seat_tool.py`,
  `tests/test_party_recipes.py`, `tests/test_party_presets.py`, `tests/test_party_size.py`, `tests/test_party_price.py`,
  `tests/test_project_kind.py`, `tests/test_project_stage.py`, `tests/test_idea_project_q.py`, `tests/test_gui_ideas.py`.
  Update expectations that size keeps the whole squad; do not silently change old saved parties in fixtures.

## B. The hand

### B.1. Files, functions and the seams with C/D

1. `hand/state.js` owns new computed `setupState`, `toolsState`, `tableLaid`, plus `setupCard`, `toolCard` signals
   and `openSetupCard`, `openToolCard`, `closeToolCard` functions. Read `town.setup` / `town.tools`; `setupCard` holds
   the current local answer/form, keyed by path/rev, never the persisted truth. `toolCard` is null or
   `{kind:"add"|"tool"|"added", tool:string, check:string, anchor:Element|null}`. These use their own lift key prefix
   `setup:` / `tool:`, not a made-up `needs_you` goal. Opening one lowers the other lifted hand card and closes the
   new-goal field. New `setupState` absent means the older page behavior; an explicit unlaid state wins.
2. B exports these for C/D without importing their components: `tableLaid` (boolean), `setupState` and
   `openSetupCard()`. C's `frame/laying.js` exports new `layPhase` (`ready|leaders|places|plus`) and `useLaying()`;
   B uses `layPhase` only to reveal the + card in `Hand`. Until C is merged, B tests inject that module's stub.
   C tests inject B's signals with A.4's shapes. D always mounts one `Frame`; no circular import through projects.
3. `hand/hand.js` `Hand` and `useKeys`: draw the setup hand even before `mapData` exists. With unlaid true, show
   `SetupCards`, `ToolCards`, `Mana`; no `Stacks`, `PlusCard`, `Middle`, PlayDie or keyboard-to-new-goal handler.
   Once laid show today's stacks/questions and the hand-sized + at its first place; disable today's automatic
   large `Middle` for the first-open empty Board, so the + is actually dealt into the hand. No hidden + focus target.
   A tool card can open above an ordinary working hand, including while Settings is open.
4. New `hand/setupcards.js`: `SetupCards`, `ProjectCard`, `GitCard`, `KindCard`, `AboutCard`, `NewFolderCard`;
   new `hand/toolcards.js`: `ToolCards`, `AddToolCard`, `ToolCard`, `AddedCard`, `RequestToolCard`, `LastToolAsk`;
   new `hand/toolbilling.js`: `BillingField`, `billingWords`, `canTest`; new `hand/toolmodels.js`: `TierModels`,
   `TierModel`. Keep the four files below 600 lines each. `hand/toolcards.css` owns lifted card layout, empty slot
   fallback and turns; `hand/mana.css` owns row geometry; `hand/hand.css` owns the setup hand's position.

### B.2. The empty slot and adding one tool

1. `hand/mana.js` `Mana`, `Pot`, `PaidPot`, `framedOf`, new `slotsOf` and `EmptySlot`: draw ids from
   `tools.order`, join quota rows by provider. Unknown limits get `?`, never a fabricated 100%. API tools get coins
   in their own slot; `mana.paid` marks that same id, never a duplicate. Preserve `potionOf`, two-window words,
   `Who`, cost hatching, tab hover marks and the frame following the selected party's effective tool / `mana.now`.
   The first tool is main; the frame may have moved to a subscription with room, as §177 already says.
   Keep the old read-only renderer as new `LegacyMana` in `hand/legacymana.js`; use it when `town.tools` is absent
   or `js/link.js` `isPaired()` is true. Narrow desktop alone does not mean phone. No add/card/drag control on a phone.
2. Append exactly one empty slot while fewer than six ids are in hand; count it for layout: one to three places in
   a row, four two by two, five/six two by three. At six tools there is no empty slot. Render it even with zero
   quota rows/no project. Label/title **Add an AI tool**, + visible; faint at rest, ink when hovered/focused or
   setup.phase is tools. Press opens AddToolCard at its box. Pot/PaidPot press now opens ToolCard; **What used it**
   there calls existing `openOver("limits", {provider:id}, from, "<Tool>: what used it")`.
3. AddToolCard is a hand card about 300 px wide, at the potions' left, foot at the hand, its body scrolling inside
   its frame. Three lines: **AI tool**, **Paid by**, the status. Native select with Ready / Not signed in /
   Not installed optgroups, excluding ids in the hand and pending adds; first ready selected, else first installed.
   Not installed choices are disabled, their install commands shown below the list as text, never executed. No
   installed candidate: **No AI tool found. Install one, then Test again.** Test again calls `tools.detect`.
4. Heading **Add an AI tool · <n> of up to 6**, n = in-hand count + 1. Subscription selected initially. Signed in:
   **✓ Signed in to your subscription**; false: **⚠ Not signed in**, Sign in, Test & add disabled. Unknown:
   **Sign-in not checked yet**, Check and Sign in; Test & add waits for a positive check. API present:
   **✓ Uses the key in your environment: <VAR>** and **Paid per token, by that key**. Missing:
   **No key found: set <VAR> in your environment, then Test again**. Under it **Restart Orkboard from that environment
   if it was already open.** For several accepted names list them joined by **or** in the missing message.
   Subscription with a winning key: **⚠ <VAR> is set in your environment: <Tool> uses it before your subscription
   and is paid per token.** Show this before an enabled test/save; send its name as ack_key on that press.
5. Under Test & add: **Sends one short request to its lightest model.** Effective API adds **about $0.001**.
   The unknown-sign-in **Check** uses the same warning and estimate before its press. Before any test:
   **Found on this computer. Nothing else was run, and no key was read.** After a test replace
   that last sentence with **Only the test you asked for was run.** No key's value is shown or accepted anywhere.
   If risk is nonempty, show it verbatim before testing and **Turn on <Tool> at my own risk** / **Keep it off**;
   accepting sets only the add draft's risk_read. No install, sign-in or test is triggered by selecting a row.
6. Test & add sends A.3's command once, disables its fields while running (**Checking…**), reads check results
   from town.tools. Failed: line/action and expandable **Details**, tool's text, optional Sign in; no new potion.
   Success: the potion appears and this same card turns to **<Tool> is in your hand. Add another AI tool?** with
   **Add another** and **Go on to the parties** during setup, **Done** later. Add another resets billing/risk/check
   for the next candidate. Sixth success calls setup.tools_done in setup, closes later. Unknown quota stays `?`.
7. Close/Esc/press away puts the card down. During a running add, first tools.cancel prevents a late add. Closing
   with an empty hand during setup says **No AI tool: the Board opens, and nothing is worked on until you add one**,
   then setup.tools_done opens the parties; it does not mark laid. A folded setup question remains a card to press
   again, never leaves the person with an empty screen. RequestToolCard uses `tools.request`, fields **Tool name**,
   **Link (optional)**, **What would orks do with it? (optional)** and **Open the request**; say **Opens a GitHub issue
   in your browser, filled in. Nothing is sent until you submit it there.**

### B.3. A tool's card

1. Read `tools.card`, show its name/mark/potion and `potionOf`'s two shares and resets, or API/unknown words. Same
   BillingField; changing it is a draft, **Save** calls tools.billing after displaying the third line. **Check**
   calls tools.check with the shown billing and warning acknowledgement. No paid request merely on changing Paid by.
2. **The order the work moves on in** shows every in-hand mark, this tool framed, **←** / **→**, accessible names
   **Move <Tool> left** / **Move <Tool> right**. Bounds disabled. A move sends the full order/current rev; accept
   the host reply before drawing the new order. Dragging a potion drops before/after another and sends the identical
   command; Escape cancels a drag. Native buttons/radios remain available to keyboard users. Explain the first:
   **The main tool: the work starts on it.** The others: **After <previous tool>**. Retain the paid warning for an API
   successor rather than promising free automatic work.
3. TierModels uses A's model rows: **Novice**, **Seasoned**, **Veteran**, **Another model…**, **Use it**,
   **Reset to latest**, **Runs on <model>**; tool without tiers: **Runs its own model**. Send tools.model; this card
   is the only tier-model editor on the new page. Keep **What used it** as the limits link.
4. **Put back** has **The orks stop using it after the task at work** below it. Each affected party says
   **<Party> is set to <Tool>: it goes on with <Next>, the next in your hand**; a seat says
   **<Party> · <Role> is set to <Tool>: it goes on with <Next>, the next in your hand**. Prefix another open project's
   name. No successor: **<Party> waits until you add an AI tool**. Add **It waits for its limit** for a dry pinned
   successor and **Paid work still waits for your yes** where automatic movement would use API without permission.
5. LastToolAsk stays on the card: **Put back the last tool?**, A.5's sentence, **Put it back anyway** sends sure true,
   **Keep it** returns to the card. Fresh rev on confirmation; stale error redraws consequences. Success closes and
   toasts **<Tool> is out of your hand** with **Undo** calling tools.undo for 30 seconds. A failed Undo says the host
   reason and never pretends the tool is restored.

### B.4. The Orkmaster's project cards and tests

ProjectCard: **Which project shall we work on?**, **Open a folder…**, **A new, empty folder…**, recent names with
paths, using A.4.6–7. Use `shell/projects.js` `chooseFolder` for its polling, not an auto-open on mount. Folder picker
cancel stays at the question. GitCard: **No git in <name> yet. Start git here?**, **Start git here**, **Choose another
folder**; say **Start git here makes a first commit of the folder's files as they are**. Reading belongs to the
bubble (**Reading <name>**, ork-think); disable duplicate answers while it runs. KindCard: **<name> is <kind>,
<how>. Right?** (omit the comma/how when empty), signs as chips, the stage in words, **Yes**, **It is something
else…** opens the list in place. List words: **an empty folder**, **a mobile app**, **a game**, **a web app**,
**a backend**, **data work**, **a team's wiki**, **a designer's folder**, **texts**, **code**. AboutCard:
**What is it for?**, one line, **A line is enough: a mobile app for…, our team's wiki, my design files**, **Read it**,
**Pick a kind instead**. Use A.4's explicit no-tool fallback. A chosen kind is a press, not another text question.

B owns browser tests with an injected `town.tools`/`town.setup` and recording command stub, at 1280 × 800 and
390 × 844 desktop viewport (no touch-phone mode):

- `tests/test_tools_hand_browser.py`: empty slot at zero/five, absent at six; four/five/six geometry; API occupies one
  place; absent quota shows `?`; three groups, disabled install, first ready, risk/sign-in/key warning before test,
  no key input; one command per click, failure, success/turn/next/sixth, cancel/late reply, Request a tool. Reorder
  by arrows/drag, billing/model save/reset, consequences, last refusal/sure, Undo, What used it link. Opening the card
  makes no test call. Keyboard focus returns to its potion/slot; no global focus trap.
- `tests/test_setup_hand_browser.py`: all project answers and exact arguments; new folder/cancel/git refusal,
  chips/correction/empty line fallback; no +/die/deck or typing shortcut before laid; setup answer held when folded;
  tools skipped on second project; zero-tool close leads to parties, not a laid Board. A late previous-project
  answer does not replace the current one. Setup/tool lifted cards scroll inside their width; potions stay reachable.
- Keep `tests/test_hand_mana_browser.py`, `tests/test_mana_two_windows_browser.py`, `tests/test_sign_in_browser.py`
  green, updating potion click's expected destination to the card and testing the old limits destination via its link.

## C. The table

### C.1. The large parties card

1. `table/parties.js` keeps exported `openParties(props, from)` and `Parties`, and its `drawn("parties", …)`
   registration. Replace `useFirstStart` with new `useSetupParties`: auto-open only when setup.phase is parties,
   not merely because there are no parties. First Start, empty chair and a party's Edit use the same component;
   props.party scrolls that party into view and marks its row. A close before Start leaves a hand card **Choose the
   parties** to reopen it. New local functions `useDraft`, `changeKind`, `changeStage`, `changeSize`, `changeSeat`,
   `saveDraft` replace `useBeginning`, `changesOf` and the old immediate stage/kind saves.
2. `useDraft` reads ideas.setup_parties once on opening. All changes remain local until Start/Save, including seats,
   kind/stage, and new parties. Kind change previews `ideas.setup_parties {kind}`; retain edits for matching ids and
   all made parties, drop only unmade proposals not offered by the new kind. Stage change ticks newly reached
   unmade parties unless the person explicitly unticked one; never unticks a made/explicitly picked party. Keep
   the original revision for Save. A stale reply shows **The parties changed. Read them again.** and **Read again**
   reloads with the draft retained until that press. No goal_save per size/head click.
3. `table/parties.css`: one `.ork-card` about 620 px wide, dealt from the Orkmaster head, inside the table, never
   overlapping the potions. Table scrolls when its height is insufficient; the card's foot/Start remains reachable.
   At under 760 px it fills the pane width, each party a block, one continuous card: remove the old left/right
   screens and `screen` state. At its top **The parties for <name>**, **The project is**, kinds select, signs as
   chips; **Idea**, **Being made**, **Live**, selected stage **The project is here**, other heading press sets it.
4. `table/partyseats2.js` replaces `PartyRight`, old `LeaderRow`/`RoleCard`/`Column` with new `PartyRow`, `TeamHeads`,
   `SeatHead`, `ShadowHead`; replace `SizeSwitch` with its small variant. Keep `SIZES`, `Tick`, `headOf`, `toolFor`,
   but read draft tiers and effective tools. One row: tick, leader head with mark in corner, name, size at the end.
   Name's title is its line of work. Size title/aria-label **Standard: about $0.40–0.90 a goal** (real price).
   No full tool name or price column. Price each of the three prospective teams using ideas.party_price; include
   tool/tools/tiers in cache key; ignore stale quote responses. Sum all ticked quotes; missing quote never sums as 0.
5. Under the line, Does with sword and Checks with shield; heads 24 × 22. Candidate seats up to five/two remain in
   their order; unoccupied ones are shadows, no tab stop, no pointer handler. Occupied heads are buttons with
   **<Party> · <Role>: its seat** and open on click, Enter or Space, not hover. Size changes heads immediately from
   sizes[size].team/tiers; local overrides apply afterwards. Lean dims Checks with **Lean: the leader does it,
   and checks it itself**. Release tick locked (**in every project**), size Lean locked. Unreached stages are one
   compact line of heads/names/ticks with **offered when the project is live** (or **offered when the project is
   being made**); ticking expands that party now. A member's mark is drawn only if its effective tool differs
   from the party's. The leader's framed mark follows main, bare mark is pinned; no tool means no fictional mark.
6. Foot **Together ≈ $<low>–<high> a goal at the API's prices. On a subscription it is taken from its limits instead.**
   Unknown: **Together: a price is not known for every party yet.** Start/Save calls ideas.setup_save exactly once
   with the draft, path, revision and stable request id retained for retry. While saving **Saving…**; error stays
   on the card and no laying begins. On success close, refreshShell; first Start's host already called project_ask,
   so do not call it a second time in JS. Later Save says **From the next task**. Preserve existing party facts via
   `Facts` in an expandable **What it keeps of the project** in that party's leader seat, after its main controls;
   existing `ideas.project_facts {party}` → `{facts:[{key,text,by}]}` and `ideas.project_fact_set {party,key,text}` →
   `{ok:true,dropped?:true,facts:[…]}` keep their explicit **From the next goal** behavior. Move `Facts`/`factKey` to new
   `table/partyfacts.js` to keep partyseats2 small; facts are separate persisted notes, not part of the Start draft.

### C.2. A seat's tool and three levels

`table/seatpop.js` `SeatPop` gains `draft`, `onChange` alongside existing `{g,slug,from,onClose}`; new `SeatTools`,
`SeatLevels`, `applySeat` helpers. With draft it works for an unmade party too and changes that draft only. Outside
the large card it reads the map's Seat data and saves **Set** with `ideas.goal_save {slug,tool?,tools?,tier_overrides?}`,
then **From the next task** and Undo restoring only the changed fields. It never sets an Agents-wide role model.

- Leader: **The party's AI tool**, first option **Main tool (<name>): follows it** with value `""`, then only in-hand
  ids from town.tools; **The leader and every member set to As the party run on it**. Save party `tool`, not
  `tools[leader]`; clear any old leader-specific entry when the person applies this choice. No tool: **Main tool
  (none yet): follows it**. Legacy conflicting leader override remains visible until that explicit choice.
- Member: **Its AI tool**, first **As the party (<tool>)**, value `""` deletes its tools entry; own picks set it.
  Disabled removed values are shown as **<Tool> is out of your hand** until the person changes them, with the effective
  successor's words. Tool choice never adds a tool or opens sign-in: adding belongs to the empty slot.
- **Its level**, three buttons using the seat's race/higher leader race and laborer/warrior/elder gear. New
  `table/seatlevels.css` owns fallback tiles. Each label includes Novice/Seasoned/Veteran and **≈$<price> a task**
  or **a step** for the leader, from ideas.seat_price. Unknown: **Price not known**. Selected radio, one tab stop,
  arrows/Home/End. A leader on Novice says **Reads less of the project before it plans**. New level overrides the
  size for that seat; the size remains picked. Closing a draft popover preserves its changed draft, Save still required.
- **Take off the seat** only for members; remove in draft or send existing goal_save with team/every and size outside
  it so the host checks busy members. Keep **Its role's text** opening existing `openOver("role", {slug,party}, from,
  name)`; an unmade role uses the library role read, with empty party. Esc/press away closes the popover before the
  parties card; return focus to the head. Hover marks a head only. `table/data.js` `toolOf` and `groupsOf` read new
  effective fields, falling back to old fields only for an older host.

### C.3. Covering the end and laying the table

1. `frame/place.js` adds new `coversTable(over)`: `settings`, `projects`, `update`, `pair`, `party` (Remove party),
   `week` and `parties` cover the end. Open a project is already `projects` with `props.open:true`, not a new kind.
   Keep `table/over.js` `isForm` for form padding: parties has card padding of its own. These explicit names cover
   every current `Place`; test them together. Reads such as limits/diff/log keep their
   existing layout; do not cover the Orkmaster column or the hand with an overlay.
2. `table/table.js` `Table` sets `data-laid` and `data-place` from the explicit state and coversTable; `table/pane.js`
   `Pane` removes DiscardEnd from the visible/focusable tree while covered or unlaid and gives the place the full
   table body width (no reserved end gutter). `table/table.css`, `frame/frame.css` and `table/discard.css` remove
   that gutter for data-place. Returning restores the same map, picked goal, tab, scroll and live discard. The
   form's scroll is local, no dimming or modal focus trap. A ready portal cannot be clicked through the form.
3. `table/column.js` `Column`/`Top`: unlaid shows the Orkmaster and its setup bubble only. New `SetupBubble` in
   `table/setupbubble.js` uses the existing bubble classes and head: folder **Which project shall we work on?**;
   git/kind/about the current question; reading **Reading <name>** with ork-think; tools **Who shall the orks run on?**;
   parties **For <kind> at <stage>, I'd seat these. Change what you like.** No empty piles, headings or switch-project
   control with no current project. The narrow desktop shows this same bubble under its Orkmaster head.
4. `table/piles.js` `Pile` returns null when items is empty; `Column` filters PILES to nonempty as well, before and
   after Start. No **Nothing here**. Existing analysis/review/work classification, flights and ordering stay.
5. New `frame/laying.js` `useLaying` compares setup path/laid/laid_id, storing the observed id per path in sessionStorage.
   Initial true, imported true, reload true or switching to a laid project renders ready immediately. Only a live
   false→true for the current path with a new nonempty laid_id plays: `leaders` for one `--ork-motion-base` interval,
   then `places` for one interval, then `plus`, then `ready` after the seal's existing sweep. No model wait gates
   the animation. `table/tabs.js` `Tabs` reveals leaders sitting first, then empty chair and Stop all's door;
   `table/pane.js` reveals ring/discard at places; B's Hand reveals + at plus. `frame/frame.js` `Frame` mounts this
   hook once and loads `frame/laying.css` (new); CSS uses transforms/opacity and orkUI tokens. Clear timers on project
   change/unmount; reduced motion goes directly ready. Seal is §185's one sweep, no indefinite glow or new rune art.
6. At ready put **The table is laid. What shall we make first? Play the + card.** in SetupBubble once; clear on first
   new-goal press or when an ordinary leader question takes its place. No tab, chair, door, ring, discard, die or
   + before laid. After Start PlayDie may return at its normal hand position; Release/Live stay at the ring's corners
   at wide width, not new leader tabs. `table/tabs.js`, `table/pane.js`, `frame/frame.js` must all tolerate an absent
   map before a project is selected; no request for ideas.* just to draw that frame.

### C.4. Tests

- `tests/test_setup_table_browser.py`, 1280 × 800 and 390 × 844 desktop: one parties card, no old two-pane layout,
  kind/stage changes make no writes, sizes change heads/quotes, no interactive shadows, Release locked, later
  parties expandable, custom party kept, prices only in size labels/foot, Start/Save exact batch, refusal retained,
  saved false→true motion ordered once, reload/switch no replay, reduced motion immediate. Each place covers ring
  and discard at wide width, hand/column stay usable; back restores map/tab/pick/scroll. Empty piles have no heading
  before or after Start; first card creates its heading, last card leaving removes it.
- `tests/test_setup_seats_browser.py`: unmade and made leaders/members; click/keyboard opens, hover does not; default
  framed, pin bare, member differing mark only, three race/gear heads and prices; leader saves party tool, member
  saves seat tool; explicit tier survives size change; novice warning; no leader removal; busy member refusal;
  no writes from draft until Save; outside-card Set/Undo use exact commands, Escape focus restoration.
- Keep `tests/test_column_browser.py`, `tests/test_places.py`, `tests/test_map_party_marks.py`,
  `tests/test_hand_mana_browser.py` green. For the hand dependency use B's stub described below until B is merged.

## D. Settings and the onboarding

### D.1. Files and functions

1. `shell/settings.js` `SettingsPlace`: two semantic groups **This project** and **This computer**, two columns
   at wide width, stacked at narrow width (`shell/shell.css`). Project: **Start plans by themselves**, **Work at
   night**, **A result that holds lands in dev by itself**, **Push after merging (sends your code to origin)**,
   `TargetSetting`'s **A party with no size of its own works as** (Thrift/Balance/Quality). Keep existing hints for
   risk, night and merge behavior; these controls still save immediately, Settings has **Done**, not Start/Save.
   Computer: `AwakeField` (**Keep the computer awake**), **Your phone** / Pair a phone, `UpdatesField` (**Updates**),
   **Download today's logs** / Today / The last 7 days. Without a project omit its controls and say **Open a project
   to change its settings**; computer controls still work.
2. One line, verbatim: **AI tools are in your hand: press a potion, or the empty slot beside them. Parties, their
   size and their AI tool: the empty chair, or a party's Edit.** Draw as text, not new tool/party controls. Settings
   keeps `Place` and the normal pane Back/Esc. It is never a lifted card. C owns covering its table end.
3. `js/settings.js`: remove `ToolsField`, `TierModelsField`, `TierModel` and their call in `SettingsDialog`, unused
   tool imports and OTHER; B now owns the tier-model editor. Keep `USAGE_WHAT` export used by other modules and the
   unrelated settings' exports; do not remove another product's settings screens or change the host brand.
4. `js/onboarding.js`: remove `ToolsStep` and its table/check/request components from the Board route. B's
   RequestToolCard replaces RequestTool. `Onboarding` returns null when `town.setup.version === 1`; do not call
   onboarding.skip from Skipping to enable found tools or make a town. Keep non-Board Who/MCP/Town/Raising exports
   used by shared legacy pages; no ToolsStep entry in new Board STEPS. `SignIn` is still mounted once in Shell.
   No hooks/Security reviewer checkbox, Next, Skip, tutorial or class selection in this first open.
   `orkboard/gui/static/board.js` `Board` must choose Shell whenever `t.setup.version === 1`, even if a transitional
   snapshot still has onboarding; today's outer `t.onboarding` conditional otherwise hides the entire new frame.
5. `shell/projects.js`: keep projectList/currentProject, project switching and chooseFolder polling. `StartScreen`
   becomes a small adapter to `openSetupCard`, no folder form in the pane when setup is present. `startForm` is
   retired from the new route; old-host fallback may still use it. `OpenFolderPlace` stays for a project already
   open, including its native dialog, recent list and no-git form, but its successful open lets host setup choose
   what comes next for a new project. A failed/cancelled open does not close the current project or its work.
6. `shell/shell.js` `Shell` always draws `Frame` with setup capability, even with no project; remove `Start`'s
   separate form-only frame on that route. Ctrl/⌘+O with no current project calls openSetupCard; with one opens
   the existing projects place. Keep resetForProject/resetFiles/resetGit on path changes and avoid refreshShell
   without a project. Old host without setup keeps the old route until upgraded; no capability guessed from
   onboarded, empty parties or screen width. D makes no edits in hand/frame/table: use B/C's exports.

### D.2. Commands, state and tests

D introduces no host command or snapshot field. Its adapters use A's setup/tools fields and B's exported opener;
Settings keeps these existing wires, without changing their host implementations:

| Command and arguments | Reply |
|---|---|
| `ideas.board_set {autostart?:bool,work_at_night?:bool,review?:bool,target?:"thrift"\|"balance"\|"quality"}` | `{target,autostart:bool,night:string,review:bool,review_notice:bool,night_low:bool\|null,work_at_night:bool}` from `orkboard/gui/ideas_board.py` `BoardMixin.board_set` / `board_settings`. |
| `ideas.into {push:bool}` | `{ok:true}`; retain `act`/refreshShell after saving. |
| `awake.state {}` / `awake.set {mode:"off"\|"carts"\|"phone"}` | `{mode,why,holding:bool,battery:bool,can:bool,how,machine,paired:bool}` from `orkboard/gui/keep_awake.py` `KeepAwake.state` / `_set`. |
| `update.check {}` / `update.policy {policy:"auto"\|"critical"\|"ask"}` | null when no offer and idle; otherwise `{version,critical:bool,major:bool,notes:[string],critical_notes:[string],current,state,error,installed,can:bool,how,policy}` from `orkboard/gui/updates.py` `Updates.check` / `policy` / `snapshot`. `state` is `idle\|installing\|installed\|failed`. |

Pair a phone uses `openPlace("pair", {}, "Pair a phone")`; logs use
`shell/errors.js` `saveLogs("", 1|7)`. Do not add tool data to either Settings group or send a tool mutation from D.

- `tests/test_setup_settings_browser.py`: both groups/labels/wires, Target kept, no tool rows/models, moved line,
  Settings full width without table end, column and hand still interactive, no-project computer settings,
  Back/Esc and narrow width; old ToolsStep/Next/Skip/hooks absent. Sign-in still works from B's card.
- `tests/test_first_open_browser.py`: one full path with fake tools and an actual temporary host/project: start
  without project → create an empty folder → Start git → What is it for (no-tool fallback to kind) → add one
  signed-in tool with one fake light-model request → add second or Go on → parties → size/member tool/level
  changes → Start → project_ask once → laid table with +/chairs/door/end and no empty pile headings. Assert files
  persisted and first new goal reaches the column. Reopen same project: no setup or motion; open another new
  project: skip tools, still ask project and parties. Repeat with zero tools through Start and verify no automatic
  model work; add later and check work can resume. Also existing imported parties, no-git refusal, failed test,
  closing an add, last removal/Undo, settings during a task, reduced motion, keyboard-only and narrow desktop.
  No real paid call, native dialog, external issue submission or account login in these tests.

## Stubs, acceptance and merge

Each part can be reviewed alone. Stub data is a contract fixture in its own test file, not a fallback in production:
A injects fake registry/ask/PATH/environment/clock. B's fixture supplies A.3 ToolState with Claude/Codex ready,
Antigravity signed out and its risk, Cursor absent, both no-key and named-key variants; A.4 SetupState for every
phase; a C `layPhase` stub. C supplies one game kind at Being made, Game design/Art/Tech/Release, later LiveOps/
Marketing, a custom made party, sizes and seats exactly as A.4, and a B `tableLaid`/setup signal stub. D supplies
B's opener and C's Frame export until integrated. All stubs reject unlisted commands and check argument names;
tests must fail if a component falls back to an old bulk onboarding or town.settings tool mutation.

The acceptance sequence is §232's: unlaid frame → project → tools only for an empty hand → parties → Start → laid.
The eight mockup looks must all be represented by a browser assertion or saved test screenshot. Tests compare the
visible result, not copied mockup CSS. No counts of waiting work, no list column, no member questioning the person,
no discard beside Settings. Reduced motion and keyboard paths are required for the same actions.

For each implementation part run `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`,
its named unit/browser tests, `tests/test_gui_wording.py` and `tests/test_design_system.py`. Browser tests belonging
to a part are its own checks; do not wait for the unrelated full browser suite or full CI before its alpha merge.
For this documentation-only change run:
`uv run --extra dev python -m pytest -q tests/test_decisions_log.py tests/test_doc_formats.py`.
