# Orkboard — notes for contributors and agents

Orkboard is Orkline's Board on its own, published as a product of its own (docs/specs/37-board-and-line.md,
docs/decisions.md §50, §95): the Board with its parties and goals, the hand and Play, on the desktop, in VS Code and on a
paired phone; the window as decided is docs/specs/95-the-window-as-decided.md. **Orkline imports Orkboard, never the
other way round**: nothing here imports Orkline's package (`orkcraft`).

## Wording

- In everything a person reads — the interface (labels, hints, toasts, errors), the docs, the README — write **ork** /
  **orks** / **Ork** and **orkestration** / **orkestrate**, never "orc" or "orchestration". The product's name in the
  interface is **Orkboard**, published on its own (decisions §95); *Orkline* is the line's name. Where a page is shared
  with Orkline it says its host's name, never a fixed one.
- Code keeps its names: identifiers, module and file names (`orc_id`), CSS ids, dict keys, event ids and config values
  stay as they are. The state keeps Orkline's names, so Orkboard and Orkline read the same settings and the same Board
  of a project, and switching between them loses nothing: `~/.config/orkcraft/`, `<project>/.orkcraft/`,
  `.orkcraft.json`, `orkcraft.toml`, the `ORKCRAFT_*` variables, the keychain's `orkcraft-ideas`, the phone's
  `orkcraft.v1` and its `orkcraft-app-v*` cache. Only the package is `orkboard`.
- **One look, orkUI's office** (dark, monochrome, colour a signal; its only pictures the races' heads, small: an accent,
  never a picture): the page and the phone are always drawn in it (docs/specs/40-design-system.md). The pixel face is for
  headings and buttons, never for a person's words.
- **The frame** (decisions §104.0, §145): the window is two parts, the table (the leaders' tabs and the pane: *what and
  why*, through whose eyes) and the hand (*what the person decides*, with the deck of goals in line and the discard of
  goals done); a goal is in the deck, the hand, on the table or in the discard. The Orkmaster says what and who, a
  party's leader how, what changes and why, a member does (and asks only its leader). New faces keep to it: no left
  column, no drawer, no count of what waits, no question from a member straight to the person.
- **Orks by their orkish names, everything else by what it does**: the Taskmaster, a Grunt; the Board, Play, Release,
  Stop all. Never the other way round: no ork gets a job title, no window a camp name.
  `orkboard/realm/lexicon.py` `TERMS` is the glossary: a new concept gets its one word there, and new code writes that
  word. A renamed concept keeps its old spelling in `was`, and the interface says an old spelling in today's word: the
  page through `say()` for attributes and data. A `html` template's own text is written in today's word at the source
  (`tests/test_gui_wording.py` checks). What people or agents wrote keeps its words; Markdown, inputs, logs and
  terminals keep theirs.
- **Parties and goals** (decisions §63): the interface says *party* for what the code calls a goal or a track, and *goal*
  for what the code calls an idea; a task stays a task. Code, files, commands, keys and events keep their names.
- Labels, settings and anything about money or safety say plainly what happens.
- Tests that check a visible string use the same wording.

## Where code goes

- **The page is the one face** (`orkboard/gui/`): the desktop's `static/board.js` with the shell (`js/shell/*`,
  `js/board/*`), the phone's `static/pwa/board-app.js` with `pwa/shell-*.js`. Nothing imports Textual or Rich, and
  `tests/test_architecture.py` keeps it so.
- `orkboard/core/`, `orkboard/realm/`, `orkboard/design/` have no face: they never import `gui/`
  (`tests/test_architecture.py` checks it). A service changes the Board and publishes on the bus (`core/bus.py`). It
  never shows a toast or a dialog itself.
- Split a module before it grows past ~600 lines.
- **Orkboard and Orkline** (decisions §50): Orkline imports Orkboard's modules, never the other way round. Every import
  of the package (a lazy one too) names one of its own modules, and Orkboard starts with no module of Orkline's
  (`tests/test_architecture.py`). New engine code (the Board, a tool's run, the gate) is written here. While Orkline
  keeps its frozen copy of these modules (the testers' week, spec 37 §9), a fix the testers need is made here first and
  in Orkline the same day, this repository's commit named in Orkline's.
- **The VS Code extension** (`vscode/`) is a frame, not a second face: it starts `orkboard --serve <folder>`
  (`gui/extension.py`) and shows the page in an editor tab. It draws nothing of the Board itself; a change to what the
  Board shows is made in `gui/`. Its tests: `cd vscode && npm test`.
- The rules a model gets for a UI document are `design/ui.py` `RULES`.
- **The design system is orkUI** (github.com/orkCraft/orkUI): `design-system/orkui` is its copy, stamped and never edited
  here; a change to the look is made in orkUI, then copied (`python -m orkboard.design.orkui <orkUI>`). Orkboard's sheets
  read orkUI's tokens and carry no colour, font or corner of their own (`tests/test_design_system.py`).
- **A party's craft is its race** (decisions §53, §158): every seat of a party wears its party's race: orks engineer
  (Tech), elves make the look (Design, Art), goblins run what is live (Run, LiveOps), gnomes market, knights make the
  product (Product, a game's Game design), the undead release it; a party's leader is its race's higher form, its mark
  grown out of the head (an ork shaman, an elf dryad, an imp, a gnome fairy, a golden unicorn knight, a lich: decisions §154,
  §155, §158, §162); its tier is the gear on its head. The Orkmaster and the Taskmaster are orks; a Grunt is an ork in Tech.
- **The licence is Apache-2.0** (decisions §96), the extension's too; the names and the ork mark are not licensed
  (`NOTICE`). A file copied from another project comes unchanged, its licence beside it and a line in `NOTICE`
  (`gui/static/vendor/`, orkUI's copy).

## Alpha: merge fast, with the critical tests

- While Orkboard is in alpha, a change is merged into `main` as soon as the **critical tests** pass; the full suite and
  the browser tests are not waited for. A red full CI after the merge is fixed by the next commit to `main`.
- The critical tests: `tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py` (the gate's
  `always` in `orkcraft.toml`), and the test files of the modules the change touches.
- This section is removed when the project leaves alpha.
