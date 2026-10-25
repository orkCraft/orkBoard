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
