# Spec 102 — The other maps and picking on them: Design's screens along their flow, Product's pains on them, Game design's loop, Art's assets, Release's dev against main, Marketing's way in; a party's map in picking

The owner and the PM, 28 October (decisions §112.6–§112.9, §134.2, §135.3–§135.4, §137.3, §141, §151.7, §152, §156.1–§156.2,
§167.1, §172, §169.1, §170; spec 95 §3.1–§3.4; spec 99 §2 and its "As built (B)"). The slice after S1 and S2b, taken (§169.1): **S3**,
each party's one map on its tab and in its leader's calls, and an idea addressed to a party pinning that map's cards. **Builds:**
a cheaper model, each part reviewed by Claude · **Review:** full · P0. **A, B and C at once** (the engine; they share no file),
**then the mockup** (`docs/mockups/s3/`) at the owner's yes, **then D, E and F at once** (the faces, on the lead's seam:
`table/maps.js`, below).

**What it is, and is not:** five maps read by code (with no model but the loop's first proposal), each as text in its
leader's calls (§156.1–§156.2) and as cards on its party's tab; picking on every map (§141, §152), System's too. Not: a
specialist's view as marks on a map (§151.4), another party's change sealed or ghosted on a map, goals meeting by the parts of
their maps (§156.3–§156.6): **S4**, on these maps. Not: the phone (S5); *Release a version*, the wait for the reset, recurring
goals (S6).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Screens and pains** | §1 | new `realm/screen_map.py` (the screens, their flow, the pains pinned; its text), `realm/idea_lens.py` (a pain's place), new `gui/ideas_screens.py` (`ideas.screens`, `ideas.pain_pin`); new `tests/test_screen_map.py`, `tests/test_gui_screens.py`, `tests/test_idea_lens.py` |
| **B. The loop** | §2 | new `realm/loop.py` (the cards, what they rest on, kept; its text), new `core/idea_loop.py` (the first proposal: one call), new `gui/ideas_loop.py` (`ideas.loop`, `ideas.loop_set`, `ideas.loop_propose`); new `tests/test_loop.py`, `tests/test_gui_loop.py` |
| **C. Assets, Release, the way in** | §3 | new `realm/art_map.py`, new `realm/release_map.py`, new `realm/way_map.py` (each its map and its text), new `gui/ideas_maps.py` (`ideas.art_map`, `ideas.release_map`, `ideas.way_map`); new `tests/test_art_map.py`, `tests/test_release_map.py`, `tests/test_way_map.py` |
| **(the lead)** | §4 | `realm/map_text.py` `of` (each party's text from A–C), `gui/ideas.py` (the commands' tables), `table/maps.js` (the seam: a map's face by its party's craft; `Pickable`) |
| **D. Design's and Product's map** | §5.1–§5.2 | new `table/screensmap.js`, new `table/screens.css`; new `tests/test_screens_desktop_browser.py` |
| **E. The loop, Art's, Release's, the way in** | §5.3–§5.6 | new `table/loopmap.js`, `table/artmap.js`, `table/releasemap.js`, `table/waymap.js`, new `table/maps.css`; new `tests/test_maps_desktop_browser.py` |
| **G. The tree** | §8 | new `realm/opportunity_tree.py` (the outcome, the jobs, their goals and experiments, kept; its text), new `core/idea_tree.py` (the first proposal: one call), new `gui/ideas_tree.py` (`ideas.tree`, `ideas.tree_set`, `ideas.tree_propose`, `ideas.tree_attach`); new `tests/test_opportunity_tree.py`, `tests/test_gui_tree.py` |
| **H. The tree's face** | §8 | new `table/treemap.js`, new `table/tree.css`; new `tests/test_tree_desktop_browser.py` (after the mockup's yes) |
| **F. Picking** | §6 | `table/maps.js`'s `Pickable` filled, new `table/picking.js` (the box, the brackets, the groups), `hand/pluscard.js` (the marks as chips), `table/syspane.js` (System's cards pickable); `gui/ideas.py` `add` takes `marks` (the lead wires); new `tests/test_picking_desktop_browser.py` |

## 0. The words
The maps' names as a person reads them, in the pane's title (*Screens*, *Loop*, *Assets*, *Dev and main*, *The way in*);
*Since <version>*; *To main*; *Pick a part to point at it* · *Stop picking*; *and n more*; *all of <map>*; *Proposed by
<leader>*; *Nothing to read yet: <what would be read>* (§112.9). A part of a map is never called a *card* where a person reads
it (spec 70 §0).

## 1. Design's screens along their flow, Product's pains on them (A; §112.7, §134.2)
1. **The screens** (`screen_map.read(state_dir, root)`), by code from dev's tree, no model: a router's table (React Router's
   `path:` and `<Route path=`, Vue Router's `path:`, Next.js `pages/` and `app/**/page.*`, SvelteKit `routes/**/+page.*`,
   Flutter's `routes:` map, Expo Router's `app/`), else a `screens/`, `pages/` or `views/` folder's files; each screen
   `{id, name, path, file}`, its `picture` the newest kept for it (a task's shot, `idea_shots`; a picture kept with a lens,
   `idea_lens.screens`), else none.
2. **The flow**: the links between screens read from their files by name (`navigate("/x")`, `router.push("/x")`, `<Link
   to="/x">`, `href="/x"`, `Navigator.pushNamed(context, "/x")`), `{from, to}`; the screens laid in **steps** from the
   entry (`/`, the first route, or the one nothing links to) by the links' order, breadth first, a screen once.
3. **A pain's place** (Product): a pain of `segments.json` gains `on`, a screen's id or a step's (`idea_lens.keep_segment`
   with `on`; `ideas.pain_pin {segment, pain, on}`), so a pain is pinned, never a free list.
4. **Its text** (`screen_map.text(…, since)`): the steps, each a line of its screens' names and paths; the pains under the
   screens they are pinned to, by segment; bounded as System's (about 3,000 characters, §156.2); the same bytes for the
   same dev. Design's and Product's calls carry it.
5. **A project with no screen to read** (a library, a backend) has no Design map: *Nothing to read yet: the app's routes or
   its screens' folder*.

## 2. Game design's loop (B; §112.8, §156.3)
1. **Four to six cards** the person and the leader keep (`<state_dir>/loop.json`: `{cards: [{id, name, line, rests_on:
   [paths], by: "person"|"leader", at}]}`), each tied to the files it rests on (`config/balance.ts`, a level's file).
2. **The first proposal**: with no loop kept, `ideas.loop_propose` (once, from Game design's tab or at its first goal)
   asks Game design's leader, one call with no tools on the cheaper tier, given `project_facts.start_files` and the
   project's config files by name (code chooses: `config/`, `*.config.*`, `balance*`, `levels/`), for four to six cards and
   what each rests on (paths that exist, checked by code); kept `by: "leader"`.
3. **Kept and changed**: `ideas.loop_set {cards}` (the person's: `by: "person"`); a card's `rests_on` only paths that exist.
4. **Its text**: the cards in order, each its name, its line and what it rests on.
5. With nothing proposed and nothing to read: *Nothing to read yet: the game's configs*.

## 3. Art's assets, Release's dev against main, Marketing's way in (C; §135.3–§135.4, §137.3, §151.7)
1. **Art's map** (`art_map.read`): `assets.listed` of Art's kinds first (art and icons, sound, music, clips), the others
   under them; a card's variants not picked under the one picked (the picks, `idea_pick`); its text: the kinds and their
   counts' words by folder (*sprites/: 40 pictures*), the changed since the last call.
2. **Release's map** (`release_map.read`): a card a goal in dev and not in main (its element, its name, its commit), ticked
   by default; what reached main since the last version under *Since <version>* (`releases.since`); **To main** as today's
   (`ideas.gate`'s merge, by code); its text: the goals waiting for main and the last version.
3. **Marketing's way in** (`way_map.read`): four steps, *channels* → *the store page or the site* → *the install* → *the
   first session*, each read from what the project holds (a store's metadata files: `fastlane/metadata/**`, `store/`,
   `metadata/`; the site's pages: a `landing/`, `site/` or `web/` folder's pages; the first session: the app's entry
   screen from §1), a step with nothing to read *Nothing to read yet: …*; its text: the four steps and what each holds.

## 4. The lead's seam
`map_text.of(party, …)` returns each craft's text (A for Design and Product, B for Game design, C for Art, Release and
Marketing, System for Tech), so every leader's call carries its map (§156.1). `table/maps.js`: `MAPS` by craft (`tech`:
System, `design` and `product`: screens, `game-design`: loop, `art`: assets, `release`: dev and main, `marketing`: the way
in), the pane drawing the open tab's; `Pickable({map, id, name, group?, children})`, a no-op wrapper until F.

## 5. The faces (D, E; after the owner's yes on `docs/mockups/s3/`)
Every map's cards wear §167.1's face (the element of the goal that changed it at the left of its header, its name, its
window with its sign or its picture, its label row) at the maps' size; a card lifted turns over (§120.1).
1. **Screens along their flow** (D): the steps as columns left to right, a screen a card (its picture in its window, else
   the `screen` sign), the links as the System's named arrows between them; a screen lifted shows its picture large, its
   path, its file, its links.
2. **Product's pains on it** (D): the same map under Product's tab, a pain a small card pinned under its screen or step,
   the segment picked over the map as a filter (*All segments*, then each); a pain dragged onto another screen pins it
   there (`ideas.pain_pin`).
3. **The loop** (E): its cards in a ring (or a row at the narrow width), each its name, its line, *Proposed by <leader>*
   or the person's; lifted: what it rests on (the files, each a press opening it over the pane), *Edit* (its name, line,
   files), **Propose** when none.
4. **Art's assets** (E): the kinds as lanes, an asset a card with its picture (a sound or a clip its sign and a play);
   lifted, it shows large and plays; the variants not picked under it.
5. **Dev and main** (E): a card a goal, ticked, **To main** at the map's foot with the gate's checks' words; *Since
   <version>* faint under its line.
6. **The way in** (E): the four steps as columns, what each holds as cards, a step with nothing to read its line.

## 6. Picking (F; §141, §152, spec 94 §1.5)
While the + card's field is addressed to a party (*→ Tech ×* or *@Tech*), that party's map is in picking, always seen
(*Pick a part to point at it* · *Stop picking*): a press on a card toggles it as a mark (orkUI's `.ork-picked` brackets,
*lifted*); on the desktop a drag from the map's empty place draws the box (a dashed line in the ink) and takes what it
covers, Shift and a press adding or taking one off; on a touch screen a tap toggles, a long press on the empty place then a
drag draws the box; a box that takes a whole group pins the group (a container's parts the container, a flow's step its
step, a lane's cards the lane, the whole map *all of <map>*, read as no mark). The marks lie on the field as chips (a name
and ×), past five the first five and *and n more*. Picking ends with *Stop picking*, Esc, sending, or the party's mark taken
off. `ideas.add` takes `marks: [{map, id, name, group?}]`, kept with the idea and read into its route's calls.

## 8. Product's map: the opportunity solution tree (G, H; decisions §172)
1. **The record** (`<state_dir>/tree.json`): `{outcomes: [{id, text}] (one or two), jobs: [{id, when, want, so, segment, by, at}] (three
   to seven), serves: [{job, goal}], tests: [{goal, experiment}]}`; `ideas.tree {}` (with each served goal's title, element, place),
   `ideas.tree_set {outcomes?, jobs?}` (the person's: `by: "person"`), `ideas.tree_attach {job, goal}` / `{goal, experiment}` (empty
   `job` detaches), `ideas.tree_propose {}` (once, as the loop's: one call of the party whose craft is `product`, no tools, the
   cheaper tier, a new step `tree`, given `project_facts.start_files` and the project's answers (`project_facts.for_call` common
   core), four parts parsed strictly, kept `by: "leader"`).
2. **Its text** (`opportunity_tree.text`): the outcome, then each job as its sentence with its segment and the goals that serve it
   (title and place: in line, at work, done), the jobs no goal serves named; bounded and byte-identical as the others; Product's
   calls carry it (`map_text.of("product")`).
3. **A goal from Product's tab** is offered under a job: the route card's lifted face shows *Serves: <job>* with a choice of the
   jobs (`ideas.tree_attach`); none chosen, none attached.
4. **The face** (H, after the mockup's yes): the outcome as a banner at the top; the jobs as columns under it, each its sentence
   and segment; the goals that serve it as the Board's goal cards under it (a press picks the goal), its experiments under a goal;
   an empty job's column says *No goal serves this yet* with **+** writing a goal for it; *Edit* on a job and the outcome.
5. **Design's map takes the pains** (§1.3, §5.2): pinned under its screens and steps, the segment a filter over it; Product's tab
   no longer shows the screens.

## 7. Tests
A: the routes of each router read; the folders' screens; the flow's links and steps; a pain pinned; the text bounded and the
same for the same dev; no screen, no map. B: the loop kept, set, its paths checked; one proposal call with no tools on the
cheaper tier given the files chosen by code; its text. C: Art's kinds first and the variants; Release's goals not in main
and *Since*; the way in's four steps and what each reads; each text. The lead: `map_text.of` for each craft. D, E: each map
at both widths, a card lifted, no sideways scroll; the pains' filter and pin. F: a press, a box, Shift, a touch's long
press, a whole group, the chips and *and n more*, the marks sent with `ideas.add`. The critical tests
(`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and each part's.
