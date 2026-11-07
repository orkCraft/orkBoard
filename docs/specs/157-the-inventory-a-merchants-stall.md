# 157. The inventory, a merchant's stall; a hero lays its table; the first goal lays the tables

Decisions §266, §267. **Mockup:** `docs/mockups/merchant/` (its section 1, the stall; section 2, the eighteen tables; the shots in
`shots/`). **Builds:** the cheaper model, a part a session, each in its own worktree, reviewed by the spec's author and merged into
`main` on the critical tests and the part's own (CLAUDE.md, alpha). **Waves** (parts of a wave share no file): **1** A, B · **2** C ·
**3** D, E, F. The page's paths are under `orkboard/gui/static/js/`.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The heroes** | the catalog of the sixteen heroes and Release Night King; a party's hero; a hero's frame and lens; the kept table's file; the words | new `realm/heroes.py`, new `realm/hero_table.py`, `realm/ideas.py` (`_track`), `realm/goal_team.py`, `realm/lens_rubrics.py`, `realm/lexicon.py`; new `tests/test_heroes.py`, new `tests/test_hero_table.py`, `tests/test_lens_rubrics*.py` if any |
| **B. orkUI: the heroes' heads** | the sixteen heads and their moods into orkUI's races, then copied | orkUI (`races/`, `races.json`), then `python -m orkboard.design.orkui <orkUI>`; `tests/test_design_system.py` |
| **C. The stall's host** | `ideas.stall`, `ideas.stall_take`, `ideas.stall_back`, `ideas.hero_table`; the hero in the Board's snapshot | new `gui/ideas_stall.py`, `gui/ideas.py` (the mixin and its commands), `realm/board_map.py` (the leader's `hero`); new `tests/test_stall.py` |
| **D. The stall's face** | the backpack, the stitched table, the merchant, the rug, the price plates, the hand of what you carry, the service, the discard taking a card, Settings' last line | new `table/stall.js` + `table/stall.css`, new `hand/carry.js`, `frame/state.js`, `table/tabs.js`, `table/pane.js`, `hand/hand.js`, `table/lane.js`, `table/discard.js`, `shell/settings.js`; new `tests/test_stall_browser.py`, `test_leaders_table_browser.py`, `test_hand_desktop_browser.py`, `test_discard_table_browser.py`, `test_gui_wording.py`, `test_design_system.py` |
| **E. The hero's table** | a party whose hero is not its craft's default shows its hero's frame | new `table/heromap.js` + `table/heromap.css`, `table/maps.js`; new `tests/test_hero_table_browser.py` |
| **F. Lay the tables** | the first goal after the first open; a goal laid when a hero is taken; the leader keeps its frame; the role and the Board's file say so | new `realm/lay_tables.py`, `gui/first_open_cards.py`, `gui/ideas_stall.py` (its `stall_take` calls F's `lay`), `realm/agent_rules.py` (the role's school, BOARD.md's line); new `tests/test_lay_tables.py`, `tests/test_agent_rules*.py` |

## A. The heroes (§266.3, §267.2–3)

1. **`realm/heroes.py`**, no face, no model. A frozen dataclass `Hero(id, craft, name, school, flow, size, decides, says_no, default,
   layout, places, framework, short, aspects)`: `craft` one of the `lens_rubrics.RUBRICS` keys; `decides` and `says_no` 1–3 (*asks* →
   *itself*, *seldom* → *often*); `size` `lean`, `standard` or `full`; `layout` `lanes` or `rows`; `places` a tuple of `(name, ask)`;
   `aspects` 4–6 `{id, name, ask}` (no `signals`: code's signals stay with the craft's default rubric). `HEROES` (an ordered dict) and
   `of(craft)`, `get(id)`, `default(craft)`. The ids are the mockup's (`docs/mockups/merchant/index.html` `HEROES`, `tables.js`):

   | id | craft | name | school | flow | size | decides | says no | default | places (layout) |
   |---|---|---|---|---|---|---|---|---|---|
   | `uni-ost` | product | Angel Invest Knight | Opportunity solution tree | outcome → opportunities → solutions | standard | 2 | 2 | yes | the craft's map |
   | `uni-jtbd` | product | Jobwise Knight | Jobs to be done | job → struggle → goal | lean | 2 | 1 | | The job · Struggles · Hired instead · Our goals (lanes) |
   | `uni-lean` | product | Pivot Knight | Lean Startup | hypothesis → test → pivot or persevere | standard | 1 | 3 | | Believe · Testing · Learned · Decide (lanes) |
   | `uni-shape` | product | Appetite Knight | Shape Up | shape → bet → build in the appetite | lean | 3 | 2 | | Pitches · Bet this cycle · Not now · The hill (lanes) |
   | `dry-heur` | design | Pixel-Perfect Dryad | Nielsen's heuristics | walk → the ten rules → fix | standard | 2 | 2 | yes | the craft's map |
   | `dry-diamond` | design | Diamond Dryad | Double Diamond | discover → define → develop → deliver | full | 1 | 2 | | Discover · Define · Develop · Deliver (lanes) |
   | `dry-atom` | design | Atom Dryad | Atomic design | tokens → parts → screen | lean | 3 | 3 | | Tokens · Atoms · Molecules · Organisms · Screens (rows) |
   | `dry-sprint` | design | Sprint Dryad | Design sprint | map → sketch → decide → test | standard | 2 | 1 | | Map · Sketch · Decide · Prototype · Test (lanes) |
   | `sh-c4` | tech | Sh.man | C4 and hotspots | containers → parts → hotspots | standard | 2 | 2 | yes | the craft's map |
   | `sh-ddd` | tech | Domain Shaman | Domain-driven design | words → borders → code | full | 1 | 3 | | Contexts · Links · The words (lanes) |
   | `sh-xp` | tech | Spike Shaman | Extreme programming | test → code → refactor | standard | 3 | 2 | | Red · Green · Refactor · Released small (lanes) |
   | `sh-fit` | tech | Fitness Shaman | Evolutionary architecture | fitness → change → check | full | 2 | 3 | | The fitness functions · Breaking · Checked changes (lanes) |
   | `imp-slo` | run | Uptime Imp | SLOs and error budgets | objective → budget → alert | lean | 2 | 3 | yes | the craft's map |
   | `imp-obs` | run | Lantern Imp | Observability first | trace → read → fix | standard | 2 | 2 | | Slow traces · Errors · Read · Fixed (lanes) |
   | `fairy-aarrr` | marketing | Growth Hack Gnome | AARRR | acquire → activate → retain | standard | 2 | 2 | yes | the craft's map |
   | `fairy-aso` | marketing | Store Gnome | The store page first | title → shots → test | lean | 3 | 1 | | The title · The shots · The words · Tests (lanes) |
   | `release` | release | Release Night King | DORA's keys, readiness and semver | dev → the gate → main | standard | 1 | 3 | yes, fixed | the craft's map |

   Each place's `ask` is one plain question (XP's *Red*: *Which test fails, written before its code?*). A default hero's
   `framework`, `short` and `aspects` are its craft's rubric (`lens_rubrics.RUBRICS[craft]`), never copied; the others' are the
   school's, written here. No real person's name in a hero's name (§266.3); a school may keep its own (*Nielsen's heuristics*).
2. **A party's hero**: the track page's front matter key `hero` (`realm/ideas.py` `_track` reads it, "" when none);
   `goal_team.hero_of(root, party) -> Hero` (the key's hero when it is of the party's craft, else the craft's default) and
   `goal_team.set_hero(root, party, hero_id)` (refuses a hero of another craft and Release's; writes the key; the craft's default
   writes the key away). The craft is `map_parts.craft_of`'s.
3. **The lens follows the hero**: `lens_rubrics.rubric(craft, hero=None)`: the hero's frame when a non-default hero of that craft is
   given, else today's; `prompt_lines` and `scorecard` take the same `hero`; every caller today passes none and is unchanged.
4. **`realm/hero_table.py`**: the kept frame, `<wiki>/pages/tables/<party>.md`. Front matter `owner: board`, `kind: table`,
   `party`, `hero`, `laid` (an ISO date), `schema: 1`; then a `## <place>` section a place, in the hero's order, its lines
   `- <title> — <line>` with an optional trailing `{goal: <slug>, state: hot|bad|good|ghost}`. `read(root, party) ->
   {hero, laid, stale, places: [{name, ask, cards: [{title, line, goal, state}]}]}` (every place of the hero's, empty when the file
   lacks it; a place the file has and the hero does not is dropped; `stale` when the file's `hero` is not the party's now; no
   file: every place empty, `laid` ""). `write(root, party, hero, places)` writes it whole. Text only, a line at most 160 chars,
   at most 12 cards a place.
5. **The words** (`TERMS`): *Inventory*, *hero*, *Yours*, *Yours before*, *Back to default*, *in your hand*, *What leaves this
   computer*, *Lay the tables*, *frame* (a hero's places). Tests: the catalog's shape (17 heroes, one default a craft, places
   only on non-defaults, ids unique), `set_hero`/`hero_of` round trip and refusals, `rubric(craft, hero)`, the table file's round
   trip and its tolerance (a missing place, a foreign place, a stale hero).

## B. orkUI: the heroes' heads (§267.6)

Made in orkUI (`github.com/orkCraft/orkUI`): `heads/make_heads.py`'s sixteen heads (the default heroes keep their race's elder
head: their variant is the empty one) with their five moods, at orkUI's sizes, named `hero-<id>` in `races/` and `races.json`;
then copied with `python -m orkboard.design.orkui <orkUI>`. **When orkUI is not reachable from the session, B is not built**: the
page draws every hero with its race's elder head (C.4 sends the head to use), and the pull request says so under *Not built*.

## C. The stall's host (§267.1, §266.2)

1. **`gui/ideas_stall.py`**, a mixin of `Ideas` with its `stall_commands`. **The wares this step trades are what the engine has**
   (§267.5); each a *slot* with its ways:
   - the Orkmaster's chair (`chair: ""`): *How deep* `target` (thrift · balance · quality), *Give me time to look* `look_wait`
     (`look_wait.CHOICES`), *Starts by itself* `autostart` (on · off), *Works at night* `work_at_night` (on · off), all through
     `board_set`'s own checks; *Push after merging* `push` (off · on) through `ideas.into`'s.
   - a leader's chair (`chair: <party slug>`): *Its hero* (`heroes.of(craft)`), *Its AI tool* (the potions' order or one tool
     signed in, `goal_team.set_tool`), *Its seats' tier* (laborer · warrior · elder, every seat of the party's team through
     `goal_team.set_tiers`).
   - Release's chair: its hero fixed (Release Night King) and the gate (`[gate] always` read from `orkcraft.toml`), both locked.
2. **`ideas.stall {chair}`** → `{chair, whose, say, shelves: [{id, label, sub, kind, slot, wares: [{id, word, line, head?, stats?,
   price, before}]}], hand: [{slot, label, word, line, head?, yours, fixed}]}`. `kind` is `heroes` (the top shelf) or `small` (the
   right). A hero's ware carries `head` (C.4) and `stats` `{school, flow, size, decides, says_no}`. **`price`**: `{mine: true}` for
   what is carried; `{locked: "<why>"}`; `{money: "<words>"}` where money is spent; else `{share: <int, signed>}` **only from an
   estimator the host already has** (`realm/party_price.price` for a party's tier and its hero's one pass, the potion's week of
   `ideas_mana`) and `{word: "lighter"|"heavier"|"one pass"|"same cost"}` when there is none. **No price is made up.** `say` is the
   merchant's line: on a leader's chair its hero's school and what it lays; on the Orkmaster's, how prices read. `before` marks
   the value carried before the last take of that slot (kept for the host's run).
3. **`ideas.stall_take {chair, slot, value}`** writes through the slot's own writer, publishes `changed`, returns
   `{stall, undo: {slot, value: <old>}}`; **`ideas.stall_back {chair, slot}`** writes the slot's default (the setting's
   `settings.IDEAS` value, the craft's default hero, the potions' order, the recipe's tier) and returns the same. A locked slot,
   an unknown value or chair: `IdeasError` in plain words. Taking a hero calls F's `lay_tables.lay_party` (a no-op until F).
4. **The hero in the snapshot**: `board_map.build`'s leader of a party carries `hero: {id, name, school, default, head}`; `head` is
   `{race, tier}` of orkUI's `hero-<id>` when orkUI has it (`races.json`), else the race's elder.
5. **`ideas.hero_table {party}`** → `hero_table.read`'s object with the hero's `layout` and the party's goals' elements by slug.
6. Tests (`tests/test_stall.py`, on the `host` fixture of `tests/test_board_35.py`): each chair's shelves and hand; a take and its
   undo for a setting, a hero, a tier; `stall_back`; a locked slot refused; no `share` without an estimator; the snapshot's hero.

## D. The stall's face (§267.1)

1. **The backpack**: a button at `.table-tabs__end` (`table/tabs.js`), before *New party*, its pixel art the mockup's
   (`PACK_SHUT`, `PACK_OPEN`, drawn as an SVG of rects in ink tokens), its title *Inventory: how the project is set*.
   `frame/state.js` gains `inventory` (a signal, the chair open or null; Esc closes it first). Open, **the table's edge is stitched**
   (`stall.css`, a dashed border in `--ork-edge`), the tabs stay, a tab pressed picks the chair (the Orkmaster's column head the
   whole project).
2. **The stall** (`table/stall.js` + `stall.css`, the mockup's `.stall`, `.bubble`, `.merchant`, `.rug`, `.shelf`, `.ware`,
   `.price`, `.f-relic`): `table/pane.js` draws it instead of the map while `inventory` is open, from `ideas.stall {chair}`. The
   merchant is the Orkmaster's crowned head at 96 × 88 (orkui.js `Head`, `big`), its mood `focused` when a card is lifted,
   `worried` while a ware of +2% or more is hovered, `pleased` after a take. A hero's ware is the mockup's `f-hero` face (head,
   name, school, the stats' bars); a small ware the `f-relic`. **The plate**: a vial (orkUI's potion `size-vial`) and `+n%` /
   `−n%` in the success colour, money in the warning colour with its words, *in your hand* dashed, *not here* with a lock and the
   why on hover, a word when the host sends one.
3. **The hand of what you carry** (`hand/carry.js`): while the inventory is open `hand/hand.js` draws it instead of the stacks:
   a card a slot of `stall.hand` (the slot's label, its word, its line, *yours*), fanned as the stacks fan; a card pressed is
   lifted; hovering a ware draws its card's ghost (dashed) with the ware's word and spends its share on the first potion's
   drawing (the mana module's existing preview, if any; else none); a ware pressed flies to its card (a clone animated with
   `--ork-motion-play`, none under `prefers-reduced-motion`) and `ideas.stall_take` is sent; the receipt line under the table says
   what changed with **Undo** (sends `stall_take` with `undo`'s value).
4. **Back to default**: the service at the merchant's feet (a dashed card, *Back to default*, *free*): a card of the hand dropped
   on it, or the service pressed with a card lifted, sends `ideas.stall_back`; **the discard** (`table/lane.js` and
   `table/discard.js`) takes a dropped card the same way while the inventory is open (HTML drag and drop, as `hand/mana.js`
   `useDragOrder`), and nothing else changes on it.
5. **Settings' last line**: `shell/settings.js` ends with *How the project is set: Inventory*, which opens it.
6. Words in templates are today's words (`test_gui_wording.py`); the sheet uses orkUI's tokens only (`test_design_system.py`;
   a custom property of its own is added to that test's allowlist). Tests (`tests/test_stall_browser.py`, a stub host answering
   `ideas.stall`, `stall_take`, `stall_back`): the backpack opens and Esc closes; the rug's shelves and plates; a ware pressed sends
   the take and Undo the old value; a hand card dropped on the service and on the discard sends `stall_back`; at 1280 × 800
   nothing overflows the table.

## E. The hero's table (§267.2)

1. **`table/maps.js`**: `mapOf(g)` returns the hero's map when `g.leader.hero` is not its craft's default; else today's map.
2. **`table/heromap.js` + `heromap.css`** from `ideas.hero_table {party}`: `lanes` lays a lane a place, its name in the pixel
   face and its `ask` faint under it; `rows` a row a place, its name at the left. A card is a map card of the mockup's `.mc`
   (`tables.css`): title, line, its goal's element at the top left when it has a goal, its `state` as the border (alert, danger,
   success, dashed). **An empty place** says its question and nothing else. Over the table, when nothing is kept yet or the file
   is `stale`: one line, *<hero> lays this table with the goal Lay the tables* (or *Lay <party>'s table*), the goal's name a press
   that picks it.
3. Tests (`tests/test_hero_table_browser.py`, a stub snapshot with a party whose hero is `sh-xp`): its four lanes and their asks,
   a kept card in its lane with its element and state, an empty place's question, the stale line; a default hero shows today's map.

## F. Lay the tables (§267.3–4)

1. **`realm/lay_tables.py`**: `lay_first(root, state_dir)` lays, once a project, the goal *Lay the tables* (`ideas.add_idea`,
   priority `low`, route the parties seated whose hero is not Release's, its Gist: what it lays, a line a party with its hero and
   its places), and records it in `<state_dir>/project.json` (`tables_laid`) so it is never laid twice; `lay_party(root, state_dir,
   party)` lays *Lay <party>'s table* (route that party alone) unless a goal of that name waits in line. Neither starts anything:
   the goal waits as any goal (§57.3).
2. **The first open** (`gui/first_open_cards.py`): when the first open is done (the table laid, `first_open.lay` true) the host
   calls `lay_first`. `gui/ideas_stall.py`'s `stall_take` of a hero calls `lay_party`.
3. **The leader keeps it** (`realm/agent_rules.py`): a leader's role file says its hero, its school and its places, and that its
   pass on a goal of its party keeps `pages/tables/<party>.md` (A.4's format), the lines short, a card a thing it read, no number
   it did not read. BOARD.md's *Where the Board lies* gains the line `pages/tables/<party>.md`: a party's table as its hero lays it.
4. Tests (`tests/test_lay_tables.py`): `lay_first` once, its route and Gist; `lay_party` not twice in line; the role file names its
   hero and places; BOARD.md's line.

## Done when

- The backpack opens the stall at 1280 × 800: the merchant, the rug with a chair's wares and their plates, the hand of what you
  carry; a ware taken writes its setting and Undo returns it; a card on the service or the discard goes back to its default (a
  browser test against a stub host, and `tests/test_stall.py` against the real host).
- A party with a non-default hero shows its hero's frame, its kept cards in their places and the empty ones' questions (a browser
  test).
- The first open lays *Lay the tables* once and starts nothing; a hero taken lays its party's goal (unit tests).
- No price on a plate the host did not estimate (a unit test); the critical tests are green.

## Later (§267.5)

Places read by code (hotspots from git, the tests' runs, a trace, a funnel's numbers, the store page's files); the ways of
answering's engine and the leaders' questions on the rug (§266.5–6); the starts by priority and the day's cap as settings, the cloud
run on the rug (§266.2); the Orkmaster's star; the textures (§266.8); the die's faces (§266.9); the phone's inventory.
