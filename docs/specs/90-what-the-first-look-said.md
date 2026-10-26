# Spec 90 — What the first look said: Play opens the page, the right column for what is opened, Assets fills the table, a party removed from its menu, System as architecture

The owner, 26 October (decisions §105), on their game (a Node party game: `client/` on Vite and React, `server/` on
Express, `config/` shared) after specs 87–89. **Builds:** A and D a cheaper model reviewed by Claude; B, E Claude ·
**Review:** light (A, D), full (B, E) · P0. **A, B, D and E1 at once** (they share no file); **E2 after B and E1**.

**What it is, and is not:** the preview's page found by asking each port; a black start screen for Play; the drawer
docked as the window's right column, shown only with something open, and what stood there moved; Assets laid across the
table; the tabs and faces on the table; *Remove party* on a party's menu and on its column at the Orkmaster's level;
System read as containers, their stacks, their links, their ways in, their layers and what they share, with the folders
as *Feature modules*. Not: the contract or the spec in the hand (§104's phase 2); the phone's Assets (spec 88 C stays);
a model anywhere.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Play's page** | §1 | `core/idea_shot.py` (`opened`: every printed port and `PORT`; new `page_of(ports, path)`), `gui/ideas_assets.py` (the failure's words), `js/arena/play.js`, `js/arena/assets.css` (the start screen); `tests/test_idea_shot.py`, `tests/test_play.py`, `tests/test_assets_desktop_browser.py` |
| **B. The right column** | §2, §3, §4 | `js/arena/arena.js` (the layout: no right column with nothing open; *Waits*, the gate, the canvases and the limits moved), `js/shell/shell.css` and `js/shell/shell.js` (the drawer docked, ~480 px, pushing), `js/shell/preview.js` (an asset's and a part's tab), `js/arena/assets.js`, `js/arena/assets.css` (sections across the width; a card opens in the column), `js/arena/systemmap.js` (a part opens in the column), `js/arena/stops.js` and `js/arena/arenawords.js` (*n goals ready for main* as a card; a result to look at as a card, as the hand has it), `js/arena/gate.js` (the quiet line), `js/shell/topbar.js` and `js/arena/limits.js` (the limits under *Spend*), `js/arena/canvases.js` (a canvas is an asset), `js/arena/arena.css`, `js/arena/systemmap.css` (the tabs and faces on the table); new `tests/test_right_column_desktop_browser.py`, and the desktop tests that read the right column, the drawer's width, *Waits*, the gate or the limits |
| **D. Remove party** | §5 | `js/arena/partylist.js` (a party's menu: right click and **…**), `js/arena/project.js` (its column's **…**), `js/shell/partyremove.js` (opened from both, unchanged in what it asks); `pwa/shell-party.js` checked (the phone has it at the party's sheet's foot); new `tests/test_party_menu_desktop_browser.py` |
| **E1. The architecture (host)** | §6.1–§6.6 | new `realm/system_overview.py` (containers, stacks, links, ways in, layers, shared), new `realm/stacks_known.py` (the list of known libraries and folder roles), `realm/project_map.py` (a snapshot keeps the overview beside the parts), `gui/ideas_system.py` (`ideas.system` answers `overview`; *Feature modules* is today's answer); new `tests/test_system_overview.py`, `tests/test_project_map.py` |
| **E2. The architecture (desktop)** | §6.7 | `js/arena/systemmap.js`, `js/arena/systemmap.css`, `js/arena/arena.js` (the Tech party's tabs: *System*, *Feature modules*, *Board*); `tests/test_system_desktop_browser.py` |

## 0. The words
New strings: *Starting <project>…* (under the name on the start screen), *The build started, but no port gives a page.
Name it in .orkcraft/checks.toml: preview_port or preview_path.*, *n goals ready for main* (*1 goal ready for main*),
*Merge into main*, *Remove party…*, *Feature modules*, *Shared*, *Ways in*, *HTTP: n routes*, *socket: n events*, *Its
face*, *Its doors*, *Its data*, *Its settings*. `TERMS` gains **container** · *containers* (`container`): a part of the
project that is built and runs on its own (a client, a server). *Waits for your look* is no longer a place.

## 1. Play opens the page (A)
1. `opened` keeps **every port the command prints** (today's `URL` pattern) and `PORT`, and once one listens asks
   `page_of(ports, path)`: for each in the order printed, then `PORT`, a `GET` of `path` (`preview_path`, else `/`) with a
   1 s timeout; the first that answers 2xx with `text/html` is the page. It keeps asking until `OPEN_S`. §102's pictures
   (`idea_shot.draw`) use the same choice.
2. None gives a page: Play answers `{state: "failed", why: "nopage", ports: [...]}`, and the face says §0's line, the
   ports it tried under it, and *Stop the build*.
3. **The start screen** (`play.js`): while Play is `starting`, the pane is the canvas colour, black; the project's name in
   the pixel face, large and centred, comes up from nothing in steps and holds, *Starting <project>…* under it in the
   faint ink. When Play answers `playing`, the name fades in steps and the frame comes up from black (the `iframe`'s own
   background black until its page is drawn). Under reduced motion: no steps, the name and then the page. The frame is
   never shown before the page answered.

## 2. The right column (B)
1. **The drawer is the window's right column**: docked at the right of the pane, about 480 px (`max(480px, 34%)`, at most
   640), the pane narrowed by it, never covered; its tabs as today (spec 39 §3). **With nothing open there is no right
   column**: the pane takes the width. Closing the last tab (× or Esc) closes it.
2. An asset (spec 88), a part of System (spec 89), a task, its log, a result's code, a diff, a document open in it, as
   the drawer's tabs.
3. What stood in the right column: *Waits for your look* goes (a result that needs a look is the hand's card, as the hand
   already has it: kind `look`); *Merge dev into main* goes to the hand as **one card**, *n goals ready for main*, its
   answer *Merge into main* (the gate's command as today), and to a quiet line in the project's line; the canvases
   (spec 78) are a kind of Assets, *Canvases*, their cards spec 78's; the AI tools' limits (`limits.js`) are under *Spend*
   in the top bar.

## 3. Assets fills the table (B)
The kinds lie as **sections one under another**, a section's name over its cards, its cards **wrapping across the whole
width**; a stack folds a folder as now. A card pressed opens in the right column (§2), never over the window.

## 4. The table starts at the pane's top (B)
A party's tabs (*System*, *Board*, and §6's) and its members' faces lie on the table's wood, the table beginning at the
pane's top: the tabs as tabs at its edge, the faces as now over their columns.

## 5. Remove party (D)
A party's row in the left column has a menu, opened by a right click or its **…** (shown on hover and focus):
*About this party*, *Edit the party*, *Remove party…*. The Orkmaster's level gives each party's column the same **…**.
*Remove party…* opens spec 80's question (`partyremove.js`), unchanged. General has none. On the phone it stays at the
party's sheet's foot (spec 80 §5).

## 6. System is the architecture (E)
`system_overview.read(tree)` → `{containers, links, shared}`, no model, from the tree a snapshot reads:
1. **Containers**: each folder (two levels at most, none in `code_map.SKIP`) with a `package.json`, `pyproject.toml`,
   `go.mod` or `Cargo.toml`, named by its folder (the root's own code: *Root*); a folder under one belongs to it.
2. **Stack**: its dependencies matched against `stacks_known.LIBS` (a few hundred names: frameworks, servers, engines,
   databases, test runners), each `{name, role}` (*UI*, *server*, *realtime*, *data*, *build*, *test*, *game*); the
   unknown ones are counted, not named.
3. **Links**: in each container's sources, the calls out (`fetch("/api/…")`, `axios.*("/…")`, `io(…)`, `socket.emit("x")`)
   and the answers (`app|router.get|post|…("/…")`, `@app.route`, `socket.on("x")`, `io.on`); a link from a container to
   another is the routes and events one calls and the other answers, `{from, to, http: [...], socket: [...]}`.
4. **Ways in**: `index.html`, a `main` or `bin`, a file that calls `listen(`, the scripts `dev`, `start`, `build`.
5. **Layers**: inside a container, its parts (spec 89's) by the imports: what no part uses on top, what most use at the
   bottom; and by `stacks_known.ROLES` (folder names: `views|pages|screens|components|ui` its face, `routes|api|
   controllers|handlers` its doors, `db|models|store|schema|repositories` its data, `config|settings` its settings).
6. **Shared**: a part used by two containers or more (an import across them, or a path both resolve), its own card.
7. **The desktop (E2)**: the Tech party's tabs are **System**, **Feature modules** (spec 89's table of folders, as it
   is) and **Board**. *System* lays the containers as columns on the table: over each its name and its stack's cards
   (small, a role each), under it its layers top to bottom as rows of parts, its ways in marked; the shared parts between
   the columns they serve; the links as the field's arrows between containers, named (*HTTP: 6 routes · socket: 4
   events*), a press on one lists its routes and events in the right column. The reveal and the marks are spec 89's.

## 7. Tests
A: a command printing two ports, the first a server answering 404 at `/`, the second a page: the second is shown; none
gives a page: the failure and its ports; the start screen's states, never a frame before the page, reduced motion. B: no
right column with nothing open, opened by an asset and a part, pushing the pane, closed by Esc; no *Waits* column; the
gate's card and its line; the limits under *Spend*; canvases among Assets; Assets' sections across the width; the tabs
on the table. D: the menu by a right click and by **…**, at the Orkmaster's column, the question opened, none on
General. E1: a monorepo of a Vite client, an Express server and a shared config: its three containers, their stacks, the
HTTP and socket link with its routes and events, the ways in, the layers, the shared part; a Python project with one
container; nothing in skipped folders. E2: the three tabs, the containers, the arrows and their routes. The critical
tests and each part's files' tests.

## As built (A)

Files: `core/idea_shot.py` (`page_of`, `opened`, `make`), `gui/ideas_assets.py` (the failure), `realm/event_log.py` (the words of `shot_taken`'s and
`play_started`'s `why`), `js/arena/play.js`, `js/arena/assets.css` (a block at the end, between `spec 90 A begins` and `spec 90 A ends`).
Tests: `tests/test_idea_shot.py`, `tests/test_play.py`, `tests/test_assets_desktop_browser.py`. No model.

- **`page_of(ports, path="/", timeout=1.0)`** → the first port of `ports` (in the order given) whose `GET path` answers 2xx with `text/html`, else None.
  It talks to `127.0.0.1` with `http.client` (no proxy is ever asked), follows up to three redirects that stay on the port, and passes over a port
  that refuses, times out, answers 4xx/5xx or gives JSON or plain text.
- **`opened(how, worktree, seconds, env, path="/", tried=None)`** keeps every port the command prints (today's `URL` pattern, in the order printed) and
  `PORT` last (the configured `preview_port` when there is one). About every 0.25 s it asks `page_of` over those that listen, until `seconds`
  (`OPEN_S`); it yields the **page's port**, or None. `tried`, when given, is filled with the ports asked (printed order, then `PORT`) if something
  listened but none gave a page, so a caller tells *no page* from *did not open* (nothing listened, or the command ended). A static page is
  unchanged. `make` (§102's picture) passes the screen's path and draws the page's port; with no page it answers `(False, "no page")`, and
  `shot_taken`'s `why` may be `no page` (the task then keeps `{"none": true}` as for `no preview`).
- **`ideas.play`**: a start that listens but gives no page answers `{state: "failed", why: "nopage", error: <§0's line>, ports: [...]}` (`peek`
  repeats it until Play is pressed again; no worktree is left), and `play_started` says `ok: false, why: "nopage"`. `none`, `did not open` and the
  rest are as before. A playing build's `url` is `http://127.0.0.1:<the page's port><preview_path>`.
- **The start screen** (`Play`): `starting` is `.playpane.is-black` (orkUI's `--ork-canvas`) holding `.play-intro`: the project's name (the switcher's
  name for the open project, else its folder's, else *the project*) in the pixel face at 56 px, centred, `play-name-in` (`0.8s steps(8)`), and
  *Starting <project>…* in `--ork-ink-faint` under it (`0.4s` later, the same steps). On `playing` after a start the `iframe` is mounted at once
  (its page has answered) with `.play-intro.is-fading` over it, black, `0.45s steps(5)` to nothing while the frame comes up in `steps(5)`, and
  then the overlay is gone (a 0.7 s timer is the net); the `iframe`'s background and its stage are `--ork-canvas`. A Play already running when the
  tab opens shows its frame at once, without the start screen. No `iframe` exists at `idle`, `starting`, `nopage` or `failed`. Under
  `prefers-reduced-motion` there are no animations: the name is there at once, and on `playing` the frame replaces it with no overlay.
- **`nopage`** (`.playpane[data-state="nopage"]`): *The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or
  preview_path.*, *Ports tried: 3001, 5173* under it, and *Stop the build* (`ideas.play_stop`, then *Open the build* is there again).
- **Decided here:** the busy mark of *Starting the build…* is gone (the name coming up is the sign that it starts; the constant `STARTING` stays
  exported); `STARTING`'s words are no longer shown.
- **Tests:** `page_of` by order, HTML, status, redirect and a dead port; a stub command printing two ports (Express's on `PORT` 404 at `/`, the
  second a page) opens the second, in `opened`, in Play and in the picture; none gives a page → `tried` and `nopage` with two ports; the start
  screen's states in Chromium (black, the name's face, size, centre and steps, the faint ink, no frame before `playing`, a MutationObserver
  recording every frame put in the page, the overlay leaving), reduced motion, and the `nopage` line.

## As built (D)
**Files.** New `js/arena/partymenu.js` (`PartyMenu`, a wrapper around a party's row or column head; `itemsOf(slug)`): the **…** button (`aria-label` *More about <party>*, `aria-haspopup="menu"`, opacity 0 at rest, 1 on hover, on focus within and while open) and the list (`role="menu"`, fixed under **…** or at the pointer for a right click, kept inside the window). Items: *About this party* (`aboutAt` cleared, `showGoal(slug, {via: "map"})`, as the party line's), *Edit the party* (`openDialog("goal", {slug})`), *Remove party…* (`openDialog("remove-party", {slug})`, in the danger colour; `partyremove.js` is not touched, its question is the one Edit the party's foot opens). General's list (`itemsOf("general")`) has no *Remove party…*; General has no row in the column nor a column at the level (`goalList()` never lists it), so no menu is drawn for it. Keyboard: Enter or Space on **…** opens it and focuses the first item, ↑ ↓ (Home, End) move and wrap, Esc closes and returns the focus to **…**, Tab leaves, a press away or on another row closes it, one menu stands at a time. The sheet is `column.css` (`.arena-pmenu*`: orkUI's tokens only, no heading, so no pixel face).
**`partylist.js`:** one import and each party's `Heading` wrapped in `<PartyMenu>` (the open party's too); Operations, *New party* and the *At work* line are not. **`project.js`, exactly:** one import and, in `Field`, `ColumnHead` wrapped in `<PartyMenu at="arena-pcol__headwrap">` inside `.arena-project__heads`; nothing of the level's layout, tabs, columns or links is changed. The wrapper takes the head's old flex (`flex: 1 0 172px; max-width: 260px`, in `column.css`, not `arena.css`) and the head fills it, so the heads still lie over their columns (the test measures it). Part B, editing the level's layout, meets this only at that one line.
**Phone:** checked, unchanged: `pwa/shell-party.js` has *Remove party* at the party's sheet's foot (`remove.can(g.slug)` excludes General).
**Tests:** new `tests/test_party_menu_desktop_browser.py` (7: right click on a row and the question; **…** hidden at rest, shown on hover and focus; Enter, Space, arrows, Esc and the focus back; *Edit the party* and *About this party*; click away and one at a time; the Orkmaster's columns and their heads' places; General). Two selectors in `tests/test_project_desktop_browser.py` and `tests/test_assets_desktop_browser.py` read `.arena-project__heads .arena-pcol__head` (the head is no longer a direct child).
