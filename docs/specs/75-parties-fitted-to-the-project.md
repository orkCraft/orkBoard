# Spec 75 — The Orkmaster fits the parties to the project, each in three sizes; a party's size is its Target

The owner, 25 October (decisions §90): the Orkmaster reads what the project is (code or not: a mobile app, a team's
wiki, a designer's folder, an empty folder), proposes the parties that kind needs, each **Lean**, **Standard** or
**Full** with its price a goal; a party's size is its Target, and the Target leaves the top bar. **Builds:** Claude ·
**Review:** full · P1.

**What it is, and is not:** a reader of the project's files (no model), recipes over the library's agents, one cheap
model call for an empty folder's one line, a party's `size`, and the faces of New party and *About this party*. Not: a
chat with the Orkmaster beyond that one line; a party made without the person's press; the library removed (it stays
under *More*); roles' own tiers changed (a role set to a tier keeps it).

Three parts, **built at once, in parallel**: B and C against their stub hosts with the shapes of §6; they share no file.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Host** | §1–§4, §6 | new `realm/project_kind.py` (what the project is), new `realm/party_recipes.py` (the recipes, the three sizes), `realm/orkmaster.py` (the proposals), `realm/idea_target.py` (`target_for`: a party's size, else the setting), the places a goal's task tier is chosen (`core/idea_runner.py`, `core/idea_keeper.py`, `realm/board_map.py`, `realm/party_price.py`, `gui/ideas_roles.py`: grep `target_of(`), `gui/ideas_project.py` (`ideas.proposals`), `gui/ideas_party.py` / `gui/ideas_goals.py` (`size` saved with a party), `core/` a new small step for the empty folder's line (the judge's pattern of spec 71: `core/idea_collide.py`), `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_project_kind.py`, `tests/test_party_recipes.py`, `tests/test_party_size.py` |
| **B. Desktop** | §5 on the desktop | `js/shell/goalwizard.js` (New party opens on the proposals), new `js/shell/proposals.js`, `js/arena/projectdeal.js` (the Orkmaster's deal: the proposals first), `js/shell/goalview.js` / `js/shell/goaldialog.js` (*About this party* / *Edit the party*: the size), `js/shell/topbar.js` and `js/board/target.js` (the Target leaves the top bar), `js/shell/settings.js` (it stays there, reworded), `js/arena/arena.css` or `column.css`, `js/shell/shell.css`; new `tests/test_proposals_desktop_browser.py`, and the desktop tests that read the top bar's Target or New party's first screen |
| **C. Phone** | §5 on the phone | `pwa/shell-goal-new.js` (New party opens on the proposals), `pwa/shell-project.js` (the deal), `pwa/shell-goal.js` (*About this party*: the size), `pwa/shell-drawer.js` (the Target, reworded, where it is), `pwa/app.css`, `pwa/sw.js` (`CACHE` one up) with the pins; new `tests/test_pwa_proposals_browser.py`, and the phone tests that read the Target or New party's first screen |

## 0. The words
`TERMS` gains `party_size` (*size*: a party's Lean, Standard or Full: how many agents, of what tiers, and so its Target)
and `project_kind` (*what the project is*). New strings: *Lean*, *Standard*, *Full*, *one agent*, *n agents*, *≈$a–b a
goal*, *Orkmaster proposes*, *for this project*, *What is this project for?*, *a line is enough: a mobile app for…, our
team's wiki, my design files*, *Read it*, *More: the library*, *Your own party*, *Its size*, *A party with no size of its own
works as*, and the kinds' words: *an empty folder*, *a mobile app*, *a web app*, *a backend*, *a game*, *data work*,
*a team's wiki*, *a designer's folder*, *texts*, *code*. *Thrift / Balance / Quality* stay the Target's words in Settings.

## 1. What the project is (A, no model)
`project_kind.read(root)` → `{"kind": id, "signs": [≤ 4 short strings: what it saw, e.g. "ios/", "android/", "mkdocs.yml",
"212 pictures"]}`; read only names and counts (never contents but `package.json`'s dependencies' names), at most 2 000
entries walked, `.git` and dot folders skipped, the Board's own `.orkcraft/` and the Wiki's pages left out. In this order,
the first that holds:
- `empty`: no file but dot files, a README and the Board's;
- `mobile`: `ios/` or `android/`, `pubspec.yaml`, `react-native` or `expo` in `package.json`, an `.xcodeproj`;
- `game`: `project.godot`, `ProjectSettings/` (Unity), `*.uproject`;
- `web`: `package.json` with `react`, `next`, `vue`, `svelte`, `vite` or `astro`, or `index.html` at the root;
- `backend`: `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, a `Dockerfile`, with no
  `web` sign;
- `data`: `dbt_project.yml`, or more `*.ipynb` and `*.sql` files than other code;
- `wiki`: `.obsidian/`, `mkdocs.yml`, a `docs/` or `pages/` of Markdown, or Markdown more than half of the files, with no
  code;
- `design`: pictures and design files (`*.png *.jpg *.svg *.fig *.sketch *.psd *.ai *.pen`) more than half of the files,
  with no code;
- `texts`: documents (`*.md *.txt *.docx *.pdf`) more than half, with no code;
- `code`: any other code; and anything else, `code` too.

## 2. The recipes and the sizes (A)
1. `party_recipes.RECIPES[kind]`: the parties that kind is proposed, in order, each `{id, name, line, leader, build:
   [ids, most needed first], check: [ids, most needed first]}` of the library's agents (`realm/library.py`); a recipe may
   name the library's presets (Ideation, Release, Mobile app, Game, Website) by building on their seats. The builder writes
   them; at least: `empty`: Ideation. `mobile`: *Mobile app: features* (product-manager; grunt, artist, aso, ui-kit;
   reviewer, accessibility-reviewer), *Mobile app: architecture* (architect; grunt, tester; reviewer, security-reviewer),
   Release. `web`: *Web: pages* (product-designer; grunt, ui-kit, copywriter, seo; reviewer, accessibility-reviewer),
   Release. `backend`: *Backend* (architect; grunt, tester; reviewer, security-reviewer), and *Data* when it has SQL.
   `game`: Game, Release. `data`: *Data* (analyst; data-engineer, sql, experimenter; data-reviewer). `wiki`: *Wiki*
   (product-manager; copywriter; editor), Ideation. `design`: *Design* (product-designer; artist, ui-kit;
   accessibility-reviewer), Ideation. `texts`: *Texts* (growth; copywriter, seo; editor), Ideation. `code`: *Engineering*
   (architect; grunt, tester; reviewer). Ideation's and Release's seats are their presets' (Ideation is whole in every
   size: four views and the skeptic; its size sets their tiers).
2. **The sizes** of a recipe (`party_recipes.sized(recipe, size)` → `{leader, team, size}`):
   - **lean**: the leader alone (no team); its tasks go to the Grunt as any party's with no taker; the party works as
     **thrift**;
   - **standard**: the leader, the first two builders and the first checker; works as **balance**;
   - **full**: the leader, every builder and checker of the recipe up to its leader's seats (`library.seats_of`); works
     as **quality**.
   Ideation and Release keep their whole seats in every size (their size only sets the Target).
3. A recipe's party already in the project (the same leader and a team that holds the recipe's standard team) is
   proposed last, `have: true`.

## 3. A party's size is its Target (A)
1. A party keeps `size` (`lean` · `standard` · `full`) on its page's front matter; `ideas.goal_save {…, size}` saves
   it; a party with none (made before this spec) has none.
2. `idea_target.target_for(settings, party)`: the party's size's Target (`lean` → thrift, `standard` → balance, `full` →
   quality), else `idea_target.target_of(settings)` (the setting, as today). Every place a goal's task, draft or plan picks
   its tier from the Target uses its goal's party's: grep `target_of(` and change those that act for one goal; the ones for
   the whole Board (Operations, the week's words) keep the setting.
3. `ideas.party_price` and the proposals' prices read the size's Target.

## 4. The proposals (A)
1. **`ideas.proposals {about?}`** → 
   ```
   {"kind": {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]},
    "ask": false,                                  // true for an empty folder with no `about` yet: the faces ask the line
    "proposals": [{"id": "mobile-features", "name": "Mobile app: features", "line": "Screens and what people do on them",
                   "why": "ios/ and android/ are here",               // ≤ 120, the kind's signs in words
                   "have": false,
                   "sizes": {"lean": {"leader": "product-manager", "team": [], "agents": 1, "target": "thrift",
                                       "price": {"low": 0.4, "high": 1.2}, "heads": [{"race": "lich", "tier": "warrior"}]},
                             "standard": {…, "agents": 4, "target": "balance", …},
                             "full": {…, "agents": 7, "target": "quality", …}}}]}
   ```
   `price` is `ideas.party_price`'s low and high for that leader, team and Target; `heads` the members' heads in seat order
   (the leader first).
2. **An empty folder's line**: with `about` (≤ 300 characters), one call of the cheaper tier (the Orkmaster's role, as
   spec 71's judge) answers one kind of §1's list but `empty` (`{"kind": "wiki"}`, read strictly; anything else: `code`); the
   proposals are that kind's, Ideation first. With no model available: `code`'s, said so (`"read": false`). The line is
   never kept beyond the call's event.
3. `ideas.map`'s `project` gains `"kind": {...}` (§4.1's, no call) and its `deal` (spec 70) puts the proposals' ids first.
4. Events: `proposals_shown` (kind, n, ask) · `proposal_taken` (kind, recipe, size) · `party_resized` (party, from, to);
   no line of the person's.

## 5. The faces (B, C)
1. **New party opens on the proposals** (desktop `goalwizard.js` with a new `proposals.js`; phone `shell-goal-new.js`):
   at the top the Orkmaster's head and *Orkmaster proposes* · *for this project* · the kind's words and signs (muted); then
   a card per proposal: its name, its line, its why, and **a three-way switch Lean · Standard · Full** (Standard picked),
   under it for the size picked: the heads, *one agent* / *n agents*, *≈$a–b a goal*; **Make it** saves that party
   (`ideas.goal_save` with the leader, the team and `size`, as a tile's party saves today; the gather of spec 63 as today).
   A proposal `have` is muted with *You have one*. Under them: **More: the library** opens today's tiles and seats (a party
   of one's own), with the size switch added there too.
2. **An empty folder** (`ask: true`): the card is one line, *What is this project for?* (a text field, its hint *a line is
   enough: …*), **Read it** asks `ideas.proposals {about}` and draws its proposals; Ideation is proposed beside it at once.
3. **The Orkmaster's deal** (spec 70 §3) shows the proposals first, each with Standard's price; a press opens New party
   on it.
4. **Its size** in *About this party* / *Edit the party* (desktop `goalview.js`/`goaldialog.js`; phone `shell-goal.js`):
   the same three-way switch with each size's price; a change saves `size` (and, when the person asks *with its team*, the
   size's team: *Lean* empties the team only after *Its members leave the party* is confirmed; never while a member has
   work open, as spec 52's swap holds).
5. **The Target** leaves the desktop's top bar (`topbar.js`'s `TargetChip`) and the phone's place for it; Settings keeps
   it under *A party with no size of its own works as* (Thrift, Balance, Quality, as today's words).

## 6. Tests
- **A**: each kind from a folder made in the test (an empty one; `ios/`; `project.godot`; a React `package.json`;
  `pyproject.toml`; notebooks; an Obsidian vault; 30 pictures and a `.fig`; Markdown documents; plain `.c` files), the
  order when two hold (a React Native app is `mobile`); the walk's limit and what it never reads; the recipes name only the
  library's agents; the three sizes of a recipe (lean: no team; standard: two builders and a checker; full: within its
  seats; Ideation whole in each); `target_for` (a size's, else the setting) and a goal's task picking its party's tier;
  `ideas.proposals` for a mobile folder (three proposals, prices rising with size), for an empty one (`ask: true`), with
  `about` (a stub harness answering `wiki`; garbage → `code`; no model → `read: false`); `goal_save` keeps `size`; the
  events hold no line; `ideas.map` carries `kind`; the two hundred goals' map stays under its 200 ms.
- **B** (1 440 × 900, stub host): New party opens on three proposals for a mobile project, the switch changes heads,
  agents and price, *Make it* sends the leader, team and `size`; an empty project asks the line and *Read it* draws a wiki's
  proposals; *More: the library* shows the tiles; the deal shows the proposals first; *About this party*'s size switch saves
  it; the top bar has no Target, Settings has it reworded; an older host (no `ideas.proposals`): today's New party.
- **C** (390 × 844): the same as sheets; no sideways scroll; the service worker's version.
- Each part: the critical tests (CLAUDE.md "Alpha"), its files' tests, `tests/test_gui_wording.py`,
  `tests/test_design_system.py`; C also `tests/test_pwa.py`.

## As built (A)

The host, 25 October. Branch `claude/spec-75-host`. Files: new `realm/project_kind.py`, `realm/party_recipes.py`, `core/idea_kind.py`; changed
`realm/idea_target.py`, `realm/orkmaster.py`, `realm/goal_team.py`, `realm/party_price.py`, `realm/board_map.py`, `realm/event_log.py`, `realm/lexicon.py`,
`realm/ideas.py` (one key), `core/idea_keeper.py`, `core/idea_runner.py`, `core/idea_review.py`, `gui/ideas_project.py`, `gui/ideas_goals.py`,
`gui/ideas_party.py`, `gui/ideas_roles.py`, `gui/ideas_map.py`, `gui/ideas_review.py`, `gui/ideas_pick.py`, `gui/ideas_pitch.py`, `gui/ideas.py` (two hooks).

**`project_kind.read(root, fresh=False)`** → `{"kind": id, "signs": [≤ 4 strings, each ≤ 40 characters]}`; `scan(root)` also gives `facts` (`sql`, `notebooks`,
`files`, `code`, `pictures`, `documents`, `markdown`, `seen`). The ids in the order they are tried: `empty` · `mobile` · `game` · `web` · `backend` · `data` · `wiki`
· `design` · `texts` · `code`, as §1 has them, with these exact readings: the walk is breadth first (the top level first), counts every entry it sees (files and
folders), stops at `LIMIT = 2000`, skips dot folders (`.git`, `.orkcraft/`, `.obsidian/`), `node_modules/`, `__pycache__/`, `Pods/` and the Wiki's `pages/tracks`
and `pages/ideas`; `empty` is "no file but a README (any extension), a LICENSE and `orkcraft.toml`" (folders that hold no file count for nothing); `mobile`
also by an `AndroidManifest.xml` anywhere, with no `ios/` or `android/`; `web`'s dependencies are `react next vue svelte vite astro`; `backend`'s files are
read at the top level; `data` is `dbt_project.yml` or `*.ipynb` + `*.sql` outnumbering the other code; **`wiki` is tried before `texts`**: a folder of Markdown
(more than half, no code) is a `wiki`, and `texts` is what is left of documents (`.docx .pdf .txt` mixed with Markdown, none of them most); `wiki`, `design` and
`texts` all need *no code*. Signs are words like `ios/`, `pubspec.yaml`, `package.json: react`, `.xcodeproj`, `.obsidian/`, `docs/`, `212 pictures`,
`3 notebooks`, `2 .c files`. Kept by the root and the modified times of the root, its top-level folders and its `package.json` (`_cache`); `ideas.map` reads it
through that, `ideas.proposals` reads it `fresh`.

**The recipes** (`party_recipes.RECIPES[kind]`, a list of `{id, name, line, leader, build, check, whole, because, when}`; `build` and `check` most needed first):

| kind | id | name | leader | build | check | |
|---|---|---|---|---|---|---|
| `empty` | `ideation` | Ideation | investor | product-view, market-view, tech-view, design-view | skeptic | whole |
| `mobile` | `mobile-features` | Mobile app: features | product-manager | grunt, artist, aso, ui-kit | reviewer, accessibility-reviewer | |
| `mobile` | `mobile-architecture` | Mobile app: architecture | architect | grunt, tester | reviewer, security-reviewer | |
| `mobile` `web` `game` | `release` | Release | release-manager | release-engineer, release-notes, aso | release-checker | whole |
| `web` | `web-pages` | Web: pages | product-designer | grunt, ui-kit, copywriter, seo | reviewer, accessibility-reviewer | |
| `backend` | `backend` | Backend | architect | grunt, tester | reviewer, security-reviewer | |
| `backend` | `backend-data` | Data | analyst | data-engineer, sql, experimenter | data-reviewer | when the folder has `.sql` |
| `game` | `game` | Game | game-designer | grunt, artist, level-designer, sound-designer | playtester | |
| `data` | `data-work` | Data | analyst | data-engineer, sql, experimenter | data-reviewer | |
| `wiki` | `wiki` | Wiki | product-manager | copywriter | editor | |
| `design` | `design-screens` | Design | product-designer | artist, ui-kit | accessibility-reviewer | |
| `texts` | `texts` | Texts | growth | copywriter, seo | editor | |
| `wiki` `design` `texts` | `ideation` | Ideation | investor | (the four views) | skeptic | whole |
| `code` | `engineering-code` | Engineering | architect | grunt, tester | reviewer | |

The kinds list them in that order (`mobile`: features, architecture, release; `web`: pages, release; `game`: game, release; `wiki`, `design`, `texts`: theirs, then
Ideation; `backend`: backend, then data). Ids never coincide with a library preset's (`engineering`, `design`, `data` are craft presets), so a row of the deal
whose id is not a preset's is a proposal. `sized(recipe, size)` → `{"leader", "team", "size"}`: `lean` `[]`; `standard` the first two builders + the first checker;
`full` every builder and checker up to `library.seats_of(leader)` (Web's fourth builder, SEO, and Mobile features' fourth, the design system designer, have no seat);
a `whole` recipe is its whole seats in every size. `has(recipe, tracks)`: same leader, the standard team inside the party's team.

**A party's size.** `goal_team.size_of(root, slug)` / `set_size(root, slug, size)`; `size` is a front-matter key of the party's page. `ideas._track` rows (so
`ideas.board`'s parties, `ideas.goal`) and `ideas.map`'s `goals[]` carry `"size": "lean" | "standard" | "full" | ""` (`""`: made before sizes).
`ideas.goal_save {…, size?, proposal?}`: `size` is kept with the party (refused: *A size is lean, standard or full*); when the request also carries a `team` that
lets a member go (an existing party), a member with work open refuses it (*<Name> has work open: it cannot leave*) and nothing is saved; no `size` sent keeps the
size it has. `proposal` (a recipe id; a recipe's id sent as `preset` does as well) on a **new** party with a `size` says `proposal_taken`.
`idea_target.target_for(settings, party)` (a party row, a page, a size as text, or `None`): the size's Target (`SIZE_TARGET`), else `target_of(settings)`.
Who uses it: the keeper's `target()` (the running step's goal's party: the effort, the tier, the budget, the plan's estimate and a plan change's price), the
runner's `ran_on(task, slug)` (a new keyword argument `size_of=` of `IdeaRunner` gives it the idea's party's size; `Ideas.size_of_idea`), `board_map.build`'s heads,
the plan's, a task's, Review's and a pick's heads, Agents' queue, a party's leader head, `ideas.party` and a pitch's face. Whole-Board uses keep the setting: the
night's proposals and reserve, Operations (`core/op_runner.py`), `ideas.roles`' heads.

**`ideas.party_price {leader, team, every, craft?, size?}`**: `size` prices it at the size's Target (refused with a size that is none), else the setting's.

**`ideas.proposals {about?}`** (`about`: text, cut to 300 characters; not text: *about is not text*) →
```
{"kind": {"id", "words", "signs"}, "ask": bool, "read"?: bool,
 "proposals": [{"id", "name", "line", "why" (≤ 120), "have",
                "sizes": {"lean" | "standard" | "full": {"leader", "team": [ids], "agents": 1 + len(team), "target": "thrift" | "balance" | "quality",
                                                         "price": {"low", "high"}, "heads": [{"race", "tier"}]}}}]}
```
`kind.words`: *an empty folder · a mobile app · a game · a web app · a backend · data work · a team's wiki · a designer's folder · texts · code*. `why`: what was
seen in words (*ios/ and android/ are here*, *the folder is empty*, *by what you said*, *nothing here says more*), a colon, then why that party fits. The proposals the
project has come last (`have: true`); the others in the recipes' order. An empty folder with no `about`: `ask: true`, Ideation only. An empty folder with
`about`: one call of the cheaper tier (`idea_target` step `kind`, the matrix row of `collide`; a $0.03 cap at balance; `core/idea_kind.py`; the `orkmaster` role;
no tools) reads one kind but `empty`; the answer is `{"kind": id}` or `code`; the proposals are that kind's with **Ideation first**, and `read: true` is said;
when no call could be made (the demo, no model, a spent limit or window, an error) the kind is `code` and `read: false`. A folder that is not empty ignores
`about` and has no `read`. Nothing is written but the event; the line is in the call's prompt only (its ledger line has the step, the role, the tier, the cost).

**`ideas.map`'s `project`** gains `"kind": {id, words, signs}` (read from the cache, no walk) and its `deal` puts the proposals the project has not first: each as
the deal's own row when its id is a preset's (`ideation`, `release`, `game`: `{"id", "why", "n"}` as spec 70 has it), else `{"id": <recipe id>, "why": "proposal",
"n": 0}`; the other rows follow, the ones the project has still last. (`orkmaster.deal_first(deal, tracks, kind_id, facts)`.)

**Events**: `proposals_shown {kind, n, ask, read (true · false · null), device}` on every `ideas.proposals`; `proposal_taken {kind (the project's, else the first that
proposes the recipe), recipe, size, device}`; `party_resized {party, from ("" · lean · standard · full), to, device}` when `goal_save` changes the size of a party
that was there. None holds a line of the person's.

**Deviations from §4.1** (none in the shape): `price` is `{low, high}` only (no `learned`, `ideas`, `checks`); the prices are `party_price.price` with no `every`
(so a checker's share is the project's, else a half); a lean Ideation or Release still has its whole team (`agents` 6 and 5). Words added to `TERMS`: `party_size`,
`project_kind`.

## As built (B)

Part B, on the desktop only; no host, phone or Python file. The page reads the Orkmaster's reading of the project from `ideas.map`'s `project.kind` (`proposalsOn()`): a host without it is today's New party, today's deal and no *Its size*.
- **`js/shell/proposals.js`** (new): New party's first screen. `Proposals` asks `ideas.proposals` once (an answer that is not a list of proposals, or a refusal, falls back to the library), draws the Orkmaster's head (`project.orkmaster`), *Orkmaster proposes* · *for this project*, the kind's words and signs (muted), and a card (`.shell-prop`, `data-proposal`) per proposal: name, line, why (muted), the size switch (Standard picked), under it the size's heads, *one agent* / *n agents*, *≈$a–b a goal* (`priceWords`; on the subscription its share of the window, as the page says spends) and **Make it**, which sends `ideas.goal_save {title: name, about: line, leader, team, every: [], priority: "normal", size, proposal: id, preset?: id when the id is a library preset}`, the heads gathering as spec 63 has it (the card's heads are the boxes). A proposal `have` is muted, *You have one*. `ask: true`: *What is this project for?* (`.shell-props__ask`, the hint of §0), **Read it** sends `{about}` and draws that answer; the line stays to be read again; `read: false` says *No model could read the line: these are the proposals for code.* **More: the library** opens today's screen. Also here: `SIZES`, `SIZE_TARGET`, `WorksAs` (*Works as Balance: the default…*, the Target's words), `agentsWords`, `askProposals`, `savedParty` (the close, the gather, the shown party, shared with the library's *Save party*).
- **`js/orkui.js`** `Switch`: the three-way switch, orkUI's buttons as a `radiogroup` (`role="radio"`, `aria-checked`, one tab stop, arrows, Home, End; `sub` is a muted second line, the price). Used for the size and for the Target in Settings. CSS in `shell/shell.css` (the picked one is orkUI's ink fill).
- **`goalwizard.js`**: opens on `Proposals` (a `preset` asked for, e.g. the deal's library card, keeps today's screen); with the reading the library screen has **Its size** (the switch, Standard picked, *Works as …*), `usePartyPrice` sends `size`, and *Save party* sends `size`. `goaldialog.js` passes `proposal`.
- **The deal** (`arena/projectdeal.js`): pressing *New party* asks `ideas.proposals` first and deals the proposals (each with Standard's price in `.arena-type__price`, its why, *You have one* muted) in the deal's order — a proposal the deal lacks goes first; a deal id that is neither a proposal nor a library preset is skipped —, then the library's parties. A proposal's card opens New party on that proposal (`{proposal}`: its card is lit and brought into view); a library card opens the library as before. CSS in `column.css`.
- **Its size** (`shell/partysize.js`, new): `SizeField` — the switch with each size's price (three `ideas.party_price` calls with `size`, and the team the size would have), a line (*Works as Thrift: …*, or *No size of its own yet: it works as Balance* for a party made before) and **With its team**. With it ticked, a pick sets the size's team: from the host's proposal for the same leader when there is one (asked then), else the party's own members cut to the size (Standard: first two builders and first checker; Full: all; Lean: none), so a party cannot grow past its members without a proposal; members that would leave ask first (*Its members leave the party: …* · **Make it Lean** · **Keep them**), and one with work open (the map party's member whose state is not `free`) refuses at once (*<Name> has work open: it cannot leave*). **About this party** (`PartySize`, section *Its size* after *The party*) saves at once (`ideas.goal_save {slug, about, priority, size[, leader, team, every]}`); **Edit the party** holds the field and *Save party* sends `size` (and the team, as any team change). The host's own refusal comes as its toast and the dialog stays.
- **The Target** left the top bar (`topbar.js`); `board/target.js` is now `TARGETS` and `TargetSetting`, in Settings' Board group as a switch named *A party with no size of its own works as* (Thrift · Balance · Quality, the picked one's line under it). The chip's `.shell-top .board-target` rules are gone; `ops.js`'s menu keeps `.board-target__*`.
- Tests: new `tests/test_proposals_desktop_browser.py` (17, the stub host with §4.1's shapes); `tests/test_shell_browser.py`'s Target-chip test now reads Settings. Known on main: `test_shell_browser.py::test_a_file_todo_…` fails.
- Unsure: (1) `size` is sent on `ideas.party_price` (host A reads it, §3.3) — the About prices rest on it. (2) *Its size* has no *back to the proposals* from *More: the library* (close and open again). (3) Words beyond §0 that I added: *With its team*, *Its members leave the party* (both from §5.4), *Keep them*, *Make it Lean/Standard/Full*, *Works as Thrift/Balance/Quality: …*, *No size of its own yet: it works as …*, *No model could read the line: these are the proposals for code.*, *Reading the project…*.
