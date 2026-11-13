# Orkboard — notes for contributors and agents

Orkboard is the Board with its parties and goals, the hand and Play, on the desktop, in VS Code and on a paired phone; the
window as decided is docs/specs/95-the-window-as-decided.md. It began as Orkline's Board (docs/specs/37-board-and-line.md)
and keeps nothing for Orkline now (decisions §305): no code, setting or branch of it, and nothing imports Orkline's
package (`orkcraft`).

## Wording

- In everything a person reads — the interface (labels, hints, toasts, errors), the docs, the README — write **ork** /
  **orks** / **Ork** and **orkestration** / **orkestrate**, never "orc" or "orchestration". The product's name in the
  interface is **Orkboard**, published on its own (decisions §95).
- Code keeps its names: identifiers, module and file names (`orc_id`), CSS ids, dict keys, event ids and config values
  stay as they are. The state keeps its first names, so a machine's settings, a project's Board and a paired phone
  carry on as they were: `~/.config/orkcraft/`, `<project>/.orkcraft/`,
  `.orkcraft.json`, `orkcraft.toml`, the `ORKCRAFT_*` variables, the keychain's `orkcraft-ideas`, the phone's
  `orkcraft.v1` and its `orkcraft-app-v*` cache. Only the package is `orkboard`.
- **One look, orkUI's office** (dark; colour is the party, the element and a signal, decisions §268; its pictures are orkUI's
  own: the races' heads, the heroes and a card's picture of its kind, decisions §283, never the only thing that says what a card
  means): the page and the phone are always drawn in it (docs/specs/40-design-system.md). The face is Rubik for headings,
  buttons and text, IBM Plex Mono for code, paths and ids (decisions §291).
- **The frame** (decisions §104.0, §145): the window is two parts, the table (the leaders' tabs and the pane: *what and
  why*, through whose eyes, the goals in line in its first lane) and the hand (*what the person decides*, under the
  lanes, with the places at its right, each opening a table: the die, the backpack, the history book); the discard of goals
  done stands beside the table, at the window's right, in two piles (for dev, for main), its head what never changes the
  table: the AI tools' mana in a row, the lamp's chain and Stop all (decisions §273, §283, §285); a goal is on the table, in the hand or in the discard (decisions §167, §176); Release is a craft as any,
  To main the person's act from the discard after the gate's tests (decisions §274). The Orkmaster says what and who, a
  party's leader how, what changes and why, a member does (and asks only its leader). New faces keep to it: no list
  column (the Orkmaster's column is the first lane pinned, whole cards: decisions §206), no drawer, no count of what waits, no
  question from a member straight to the person.
- **Orks by their orkish names, everything else by what it does**: the Taskmaster, a Grunt; the Board, Play, Release,
  Stop all. Never the other way round: no ork gets a job title, no window a camp name.
  `orkboard/realm/lexicon.py` `TERMS` is the glossary: a new concept gets its one word there, and new code writes that
  word. A renamed concept keeps its old spelling in `was`, and the interface says today's word: a `html` template's own text is
  written in today's word at the source (`tests/test_gui_wording.py` checks); the page has no `say()` and rewrites nothing. What people or agents wrote keeps its words; Markdown, inputs, logs and
  terminals keep theirs.
- **Parties and goals** (decisions §63): the interface says *party* for what the code calls a goal or a track, and *goal*
  for what the code calls an idea; a task stays a task. Code, files, commands, keys and events keep their names.
- Labels, settings and anything about money or safety say plainly what happens.
- Tests that check a visible string use the same wording.

## Where code goes

- **A spec is a goal's** (decisions §255.17): a new spec in `docs/specs/` is written with its goal's page
  (`llm-wiki/general/pages/ideas/<the spec's file name>`) in the same commit; `orkboard import --goals docs/specs` lays it. This
  repository's Board is in its code (`[board] in_code` in `orkcraft.toml`), and the rules any AI tool follows for it are
  Orkboard's block in `AGENTS.md`; this file's own rules win over them (its *Alpha* over the block's *main is the person's*).
- **The page is the one face** (`orkboard/gui/`): the desktop's `static/board.js` with the shell (`js/shell/*`,
  `js/board/*`); the phone draws the same page in `static/pwa/frame.js`'s frame (spec 94). Nothing imports Textual or Rich, and
  `tests/test_architecture.py` keeps it so.
- `orkboard/core/`, `orkboard/realm/`, `orkboard/design/` have no face: they never import `gui/`
  (`tests/test_architecture.py` checks it). A service changes the Board and publishes on the bus (`core/bus.py`). It
  never shows a toast or a dialog itself.
- Split a module before it grows past ~600 lines.
- **The log and the specs keep what holds** (decisions §306): a decision or spec wholly replaced, or about something
  removed, is removed from `docs/` (git keeps it); this wins over the Board block's *never edit a past decision*.
- **Nothing for Orkline** (decisions §305): no code, setting, comment or branch is kept for Orkline or another product
  that might run these modules; the package imports nothing named `orkcraft` (`tests/test_architecture.py`).
- **The VS Code extension** (`vscode/`) is a frame, not a second face: it starts `orkboard --serve <folder>`
  (`gui/extension.py`) and shows the page in an editor tab. It draws nothing of the Board itself; a change to what the
  Board shows is made in `gui/`. Its tests: `cd vscode && npm test`.
- **An ordinary test checks a path through a public entry** (decisions §309): one to three tests a path, its branches one
  parametrized test; none for the inside (private names, order of calls, inner messages, constants); a duplicate or an unstable one is
  removed. The critical tests and `tests/test_gui_wording.py` are kept.
- **Browser tests are a person's paths** (decisions §308): what they pressed and what changed on the Board, at one width; no
  pixel, size, colour, animation timing or markup order; pure logic of the page in node (`tests/test_*_js.py`); a test that is
  red always is mended or removed.
- **The design system is orkUI** (github.com/orkCraft/orkUI): `design-system/orkui` is its copy, stamped and never edited
  here; a change to the look is made in orkUI, then copied (`python -m orkboard.design.orkui <orkUI>`). Orkboard's sheets
  read orkUI's tokens and carry no colour, font or corner of their own (`tests/test_design_system.py`).
- **A party's craft is its race** (decisions §53, §158): every seat of a party wears its party's race: orks engineer
  (Tech), elves make the look (Design, Art), goblins run what is live (Run, LiveOps), gnomes market, knights make the
  product (Product, a game's Game design), the undead release it; a party's leader is its race's higher form, its mark
  grown out of the head (an ork shaman, an elf dryad, an imp, a gnome fairy, a golden unicorn knight, a lich: decisions §154,
  §155, §158, §162); its tier is the gear on its head. The Orkmaster is a half-ork, half-goblin, the table's dealer (decisions §295); the Taskmaster is an ork; a Grunt is an ork in Tech.
- **The licence is Apache-2.0** (decisions §96), the extension's too; the names and the ork mark are not licensed
  (`NOTICE`). A file copied from another project comes unchanged, its licence beside it and a line in `NOTICE`
  (`gui/static/vendor/`, orkUI's copy).

## Alpha: merge fast, with the critical tests

- While Orkboard is in alpha, a change is merged into `main` as soon as the **critical tests** pass; the full suite and
  the browser tests are not waited for. A red full CI after the merge is fixed by the next commit to `main`.
- The critical tests: `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py` (the gate's
  `always` in `orkcraft.toml`), and the test files of the modules the change touches.
- This section is removed when the project leaves alpha.

<!-- orkboard:begin schema=3 hash=d66e05148fe1 -->
@AGENTS.md

The Board's rules are in AGENTS.md; this project's own rules in this file win over them.
<!-- orkboard:end -->
