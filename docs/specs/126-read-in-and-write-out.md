# 126. Read in and write out: a project's own decisions, specs and notes into the journals, and the Board's out in common formats

Decisions §204 (1–5). The owner, 1 November: *make our specs and journals ready in a convenient, common format, for a quick
import of existing documentation and decisions.* **Builds:** Claude (the cheaper model builds, the spec's author reviews) ·
**Review:** full · P1. After spec 125 (the journals). No new face (§104.0, §145): the terminal, the host's commands and the
first start.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The formats** (built by the spec's author) | MADR 4, Nygard's ADRs and the Board's one file, read and written; the journals take a day and know their refs | new `realm/doc_formats.py`, `realm/journals.py` (`add(..., at=)`, `refs`, the leader's kind `decision`), `gui/board_cli.py` (`import`, `export` wired to B's and C's `run_cli`); new `tests/test_doc_formats.py`, `tests/test_journals.py` |
| **B. Read in** | find the shapes, read them into the journals once; the brief's sources at the first start; the host's commands; `orkboard import` | new `realm/read_in.py` (`scan`, `take`, `run_cli`), `realm/project_facts.py` (`start_files`), `gui/ideas_project_q.py` (`project_start`: read in once), new `gui/ideas_read_in.py` (commands), `gui/ideas.py` (its mixin and commands); new `tests/test_read_in.py` |
| **C. Write out** | the decisions as MADR or Nygard files, a memory bank, each journal as Markdown; `orkboard export` | new `realm/write_out.py` (`write`, `run_cli`); new `tests/test_write_out.py` |
| **D. The project's own decisions format** | a decision written as the next ADR file of the project's folder; the leaders read the folder | `realm/decisions_log.py` (`found`, `path`, `context`, `headings`, the folder), `core/idea_decide.py` (`write_decision`, `_decisions`, `_log_text`); `tests/test_decisions_log.py`, `tests/test_idea_decide.py` (or where they are) |

B, and C with D, are built side by side in their own worktrees; they share no file but `gui/ideas.py` (B only: its
mixin) and `tests/`. Neither changes A's files: a change they need is said to the spec's author.

## A. The formats (`realm/doc_formats.py`, built)

`front_matter`, `parse_record` (MADR or Nygard, by shape; None for a README, an index, a template), `parse_log` (the Board's
`## N. Title (when, who)`), `records(folder)`, `folder_format(folder)`, `next_number(folder)`, `file_name(n, title)`,
`render_madr(rec)`, `render_nygard(rec)`. A record is `{number, title, status, date, deciders, context, decision,
consequences, body, path, format, extra}` (see the module). `journals.add(..., at="YYYY-MM-DD")` keeps the day a thing
happened; `journals.refs(state_dir, scope)` the refs kept, struck ones too. A leader's journal gains the kind `decision`.
`gui/board_cli.py` has `orkboard import [folder] [--dry-run]` and `orkboard export [folder] [--to DIR] [--as madr|nygard]`,
calling `read_in.run_cli(root, dry=)` and `write_out.run_cli(root, to, fmt)`; each returns `(exit code, text)`.

## B. Read in (`realm/read_in.py`, no model, no network)

### B.1 The shapes (`scan(root) -> {"found": [...], "decisions": [...], "specs": [...], "context": [...], "releases": [...]}`)

Paths are from the project's root; a link, a secret (`hooks.warder.is_secret`) and a file over 1 MB are never read.

| Framework | Where | Gives |
|---|---|---|
| ADRs (MADR or Nygard) | the folders `docs/decisions`, `docs/adr`, `doc/adr`, `docs/architecture/decisions`, `adr`, `decisions` holding `NNNN-*.md` (`doc_formats.records`) | decisions |
| the Board's own file | `decisions_log.found`'s `decisions.md` files (`doc_formats.parse_log`) — only when the project's journal has no `decision` yet (a project that ran Orkline before) | decisions |
| GitHub Spec Kit | `.specify/memory/constitution.md`; `specs/*/spec.md` and `.specify/specs/*/spec.md` with their `tasks.md` | context; specs |
| Kiro | `.kiro/steering/product.md`, `tech.md`, `structure.md`; `.kiro/specs/*/requirements.md` with `tasks.md` | context; specs |
| OpenSpec | `openspec/project.md`; `openspec/specs/*/spec.md` (current: done); `openspec/changes/archive/*/proposal.md` (done); `openspec/changes/*/proposal.md` (in work) | context; specs |
| BMAD | `docs/prd.md`, `docs/architecture.md`; `docs/stories/*.story.md` (`Status: Done` is done) | context; specs |
| Cline's memory bank | `memory-bank/projectbrief.md`, `productContext.md`, `systemPatterns.md`, `techContext.md`, `activeContext.md`, `progress.md` | context |
| agents' files | `AGENTS.md`, `CLAUDE.md` at the root | context |
| Keep a Changelog | `CHANGELOG.md`: each `## [x.y.z] - YYYY-MM-DD` (not `Unreleased`) | releases |
| an Orkboard export | `<dir>/journals/*.md` written by C (front matter `orkboard-journal: <scope>`) wherever `scan` finds one under `docs/` or `.orkcraft/export/` | the journals' entries as they were |

- **found**: `[{framework, kind, path, n}]` for the terminal's lines and the host.
- **a decision**: a `doc_formats` record with `craft` — `tech` for an ADR folder unless its front matter `tags` or its
  title name another craft by `CRAFT_WORDS` (`design`/`ui`/`ux` → design · `art` → art · `release`/`deploy` → release ·
  `marketing`/`growth` → marketing · `product`/`pricing` → product · `game`/`loop`/`level` → game-design).
- **a spec**: `{framework, name, title, done, path, date}`: `done` when its `tasks.md` has checkboxes and all are ticked, an
  OpenSpec current spec or archived change, a BMAD story with `Status: Done`; the title its first `# ` heading, else its
  folder's name; the date the file's last commit day (`git log -1 --format=%cs -- <path>`, quietly ""), else "".
- **context**: `[{framework, path, text}]`, the first 2,000 characters, in the order of the table.

### B.2 Taking it (`take(root, state_dir, scan=None) -> {"decisions": n, "leaders": n, "done": n, "releases": n, "journals": n}`)

Every entry carries `ref` = its source's path (and `#<number>` for one record of the Board's file, `#<version>` for a
release); **an entry whose ref is already in that journal (`journals.refs`) is skipped**, so `take` runs any number of
times.
- a decision → the project's journal, kind `decision`, `at` its date when it is a day (`YYYY-MM-DD`), its line
  `Decision {number}: {title}` + ` ({status})` when the status is not `accepted` (*superseded*, *rejected*, *deprecated*,
  *proposed*) + `: {first line of its decision}` cut to the line's 300; **and** into the journal of the project's party of its
  craft (`goal_team.craft_of`; none, nothing), kind `decision`, the same line.
- a spec done → the project's journal, kind `done`, `Spec “{title}” ({framework}) was done` (in work: nothing; offering
  them as goals is a later spec).
- a release → kind `done`, `Version {x.y.z} was released` + `: {its first bullet}`, `at` its date.
- an Orkboard export's journal → each entry into its scope as it was (its kind, text, day, idea, on, and its own id as ref).

### B.3 The brief's sources (`project_facts.start_files`)

The first start's call reads, before the README and `docs/`'s top level, the context files `scan` found (the table's order:
a constitution, the steering's product, a memory bank's brief and product context, OpenSpec's project, a PRD, `AGENTS.md`),
`START_DOCS` files at most in all, each its first 2,000 characters, by their paths: the leader marks a card `said` where they
say it (spec 99 §8). `CLAUDE.md` is not one (it speaks to agents, not of the product).

### B.4 When, and the host

- **Once at the first start**: `gui/ideas_project_q.py` `project_start` calls `read_in.take` quietly (`try`/`except`) before
  the questions, so the journals hold the project's history before the first goal. Never again by itself.
- `ideas.read_in_scan {}` → `{"found": [...]}`; `ideas.read_in_take {}` → `take`'s counts (`gui/ideas_read_in.py`, a mixin of
  `Ideas`; data, never interface words).
- `run_cli(root, dry)` → `(0, text)`: the found shapes, one line each (`ADRs (MADR) · docs/decisions · 14 decisions`), then
  `Read in: 14 decisions (9 also into leaders' journals), 3 specs done, 5 releases` (`--dry-run`: *Would read in: …*, nothing
  written); `(0, "Nothing to read in: …")` naming the shapes looked for when none is found. The state folder is
  `<root>/.orkcraft`.

## C. Write out (`realm/write_out.py`)

`write(root, state_dir, to, fmt="madr") -> {"decisions": n, "journals": n, "memory_bank": n, "path": to}`; `to` defaults to
`<root>/.orkcraft/export`. It writes only inside `to` (made when missing), each file whole; a file it did not write is never
touched (each file it writes says so in its front matter or first line); never into `docs/decisions` or the project's ADR folder.

- **`decisions/`**: every decision the project keeps — the Board's file (`decisions_log.path`, `doc_formats.parse_log`) or
  the project's ADR folder (D) — as `doc_formats.file_name(number, title)` rendered by `render_madr` (or `render_nygard` with
  `--as nygard`): `deciders` from the entry's *who* (*the person and Orkboard* → `[the person]`; *the leaders, all agreed* →
  `[the leaders]`), `date` the entry's when, `extra` `{ork-source: <path>}`; plus `decisions/README.md` listing them (number,
  title, link), saying it was written by Orkboard.
- **`memory-bank/`** (Cline's six files), each a short Markdown page written by code:
  `projectbrief.md` the brief's six lines (`project_facts.common`) and the parties; `productContext.md` whom it is for, what
  hurts them, why this, what it must always be (and Product's digest when there is one); `systemPatterns.md` Tech's digest
  and the last ten Tech entries; `techContext.md` Tech's facts (`project_facts.of(state_dir, <tech party>)`);
  `activeContext.md` the goals in work (`ideas.ideas` with their state, not done) and the project's journal's last ten;
  `progress.md` the project's journal's `done` and `dropped`, newest first, 40 at most. A part with nothing says *Nothing yet*.
- **`journals/<scope>.md`**: each journal (the project's as `project.md`): front matter `orkboard-journal: <scope>`, `party`,
  `leader` (its name), `digest` (as a quoted line), `exported: <ISO time>`; then `# {party title}'s journal`, and one line an
  entry: `- {YYYY-MM-DD} · {kind} · {text}` followed by `<!-- id={id} idea={idea} on={a,b} ref={ref} -->`; struck ones left
  out. B reads it back.
- `run_cli(root, to, fmt)` → `(0, "Wrote 14 decisions, 6 memory bank files and 5 journals to <to>")`.

## D. The project's own decisions format

- `decisions_log.found` also finds `docs/decisions` and `docs/architecture/decisions` when they hold `NNNN-*.md` records
  (`doc_formats.records`), shallowest first as today.
- **A folder chosen as the decisions' place** (the person's choice, `chosen`, or the only log `found` finds when none is
  chosen and `docs/decisions.md` does not exist): `decisions_log.is_folder(root, chosen)`; `context`, `headings` and
  `next_number` read the folder's records (the last ten titles as `N. Title`, a goal's entry its record's text).
- **`write_decision` in a folder** (`core/idea_decide.py`): the decision written as a new file
  `doc_formats.file_name(doc_formats.next_number(folder), title)` (the number read again inside the repository's lock, as
  today), rendered in `doc_formats.folder_format(folder)` (MADR when the folder has none yet): `status: accepted`, `date`
  today (`YYYY-MM-DD`), `decision-makers` `[the person]` or `[the leaders]`, the body as the *Decision Outcome*, `extra`
  `{ork-goal: <slug>}` when a goal's; committed with the Board's pages through `tree` exactly as the one file is (find how
  `BoardTree.edit_file` makes a file that is not there; else its nearest way to add one). `{number, commit, path, held,
  pages}` as today, `path` the new file.
- With a one-file log nothing changes.

## Tests

- `tests/test_doc_formats.py`, `tests/test_journals.py` (A, built).
- `tests/test_read_in.py`: a project with each shape (made in `tmp_path`) found by `scan`; MADR and Nygard decisions into the
  project's journal on their day, with their status, and into the craft's leader's journal; a spec done and one in work; a
  changelog's releases (not *Unreleased*); an Orkboard export read back; `take` twice reads nothing twice, a struck entry too;
  secrets, links and large files never read; `start_files` reads the context files first; the first start reads in once;
  the commands; `orkboard import` and `--dry-run`.
- `tests/test_write_out.py`: the decisions as MADR and Nygard files that `doc_formats.parse_record` reads back the same; the
  README; the memory bank's six files (and *Nothing yet*); each journal's file read back by B's reader into an empty state
  equal (kind, text, day, idea, on); nothing written outside `to`; `orkboard export`.
- D: `found` finds a MADR folder; a decision written into a MADR folder and into a Nygard folder as the next file in its
  format, read back by `doc_formats.records`; `context`/`headings` from a folder; the one-file log unchanged.
- The critical tests and the test files of every module touched.

## As built (1 November)

- **B** (`realm/read_in.py`): `scan` returns a sixth key, `journals` (an Orkboard export's); a marker `<state>/read_in.json` keeps the
  first start's read-in to once; the brief's sources follow the table's order; an ADR folder's decisions default to Tech, the Board's
  own file to no craft. **A record the Board wrote into the project's ADR folder (D) is never read in again**: one with `ork-goal`, or
  whose number is already a decision in the project's journal, is skipped (the review's fix).
- **C** (`realm/write_out.py`, `realm/write_out_bank.py`): an entry's comment stands on its own line's end
  (`- 2026-10-30 · overruled · text <!-- id=… idea=… on=a,b ref=… -->`), which B's reader takes on the line or the next (the
  review's fix, `tests/test_read_in_write_out.py`); the project's journal is `orkboard-journal: _project`; `to` is refused when it is
  or holds one of the project's ADR folders; a file in `to` Orkboard did not write is left and named in `skipped`.
- **D**: `BoardTree.add_file(folder, make, message)` (`realm/idea_git.py`) makes the next record under the repository's lock with an
  exclusive create and commits it with the Board's pages; a decision written from the Board's one file keeps its date as written
  (the one file had no year: spec 127 A).
