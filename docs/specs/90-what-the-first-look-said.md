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

## As built (B)

- **The right column** (`shell.css`, `shell.js`, `tabs.js`): `.shell-drawer` is a flex item of `.shell-main`, `clamp(480px, 34%, 640px)` wide, docked at the right; the pane
  (`.arena`) is narrowed by it, never covered. With no tab shown there is no right column. Esc and *Close the right column* (the strip's ×, the word *drawer* gone) put it away
  and keep its tabs, as spec 39 did; the last tab's × closes it. Below 1 024 px there is no room for two: it still takes the window. A toast stands at the top of the pane, at
  its right and left of the right column when one is out, so that it covers neither the hand nor what is open.
- **Its new kinds** (`store.js`, `preview.js`): `asset` (`path`: the asset's id; `assets.js` `AssetView`, the lifted card of spec 88 without its scrim or Close: the name,
  *Changed by*, *Now* / *Before*, the stage, *Not picked (n)*) and `part` (`path`, `slug`: its party; `systemmap.js` `PartView`, spec 89's part beside the table, its uses named
  from the System last shown). A part under *Uses* or *Used by* opens in the same passing tab; a part pressed again closes it.
- **What stood in the right column** (`arena.js`; `waits.js` removed): a result to look at is the hand's card on the party shown at every width (`handOf` `withResults`, kind
  `result`, *To look at*, Review's answers on it; its *Waits: …* as the card's note); opened, the right column shows its picture large (spec 85 §3), read from the Map when Review's
  list lacks it. The gate is one card, `arenawords.js` `gateStop` (kind `gate`, its label *dev → main*, its title *n goals ready for main* or *k commits ready for main*, the goals'
  titles as its text, the Orkmaster's head), its answer *Merge into main* (`gate.js` `mergeGate`, the gate screen's command, which keeps the press for the flags); a press beside
  the button opens the gate's screen. The quiet line is `gate.js` `GateLine` under the project's line in the left column (one line in `partylist.js`): *n goals in dev wait for
  main* (*main is up to date*), a press opens the gate's screen, and *results go into dev ⌄*. The flags raised travel from that line when nothing was pressed (`flags.js`).
  A result's and the gate's card say their kind in the muted ink, not the alert colour (decisions §54.1). *While you were away* and *Last week* lie at the top of the field
  (`.arena-cards`); the *Last week* link is in the limits' panel.
- **The limits under Spend** (`topbar.js`): beside *Spend* the tightest tool's share (*Codex 40 %*, the warning colour at 20 % or less, danger at 5 %); a press opens a panel
  under it with `limits.js`' lines and *Last week*; Esc or a press elsewhere closes it. The hand takes the field's whole width.
- **Assets** (`assets.js`, `assets.css`, `canvases.js`): the kinds are `.assets-sec` sections one under another, each a heading over its cards wrapping across the table's
  width (`.assets-sec__cards`, 128 px cards); an opened stack wraps its files on a line of its own. A card pressed opens in the right column (`.is-on` while it is shown).
  The canvases are the last section, *Canvases n* (n: the new ones), spec 78's cards, *Seen · k* folded after them, and a kind of the filter; the right column's fold row went.
- **The table from the pane's top** (`arena.js`, `arena.css`, `systemmap.css`): `.arena-play` is the one `.ork-table`, under the party's line: System and Board's tabs at its
  edge (no rule under them) and the members' faces on its wood; the field and the System's scroll are no tables of their own. The project's level is unchanged (`project.js`
  is part D's).
- Tests: `tests/test_right_column_desktop_browser.py` (§7 B); the desktop tests that read Waits, the gate's box, the limits, the drawer's width or the lifted asset now read the
  hand's cards, the gate's line, the panel under Spend, the right column and its region.
