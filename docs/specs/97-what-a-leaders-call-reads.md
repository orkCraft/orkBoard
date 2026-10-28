# Spec 97 — What a leader's call reads: bounded in fact, its floor bare, the decisions file read by code

The owner, 28 October (decisions §156.8, §156.9, §156.11): *what a call may read is bounded in fact, not only in words.*
Today a leader's read-only call (`core/idea_keeper.py` → `realm/jobs.py` `run_read` → `realm/harness_claude.py`
`_claude_read`) is told *Read at most n files*, and nothing holds it to that: it may read a lockfile, `node_modules/`, a
build's output or a 300 KB decisions file; nobody counts what it read; and every call pays the person's MCP servers and
skills in its cache. **Builds:** a cheaper model, reviewed by Claude · **Review:** full · P0. **A and B at once** (they
share no file). The engine only: no face, no word a person reads, so nothing new in `TERMS`.

**What it is, and is not:** the read-only call denied the files no leader needs, run with none of the person's MCP
servers and skills, its reads counted on its line of the day's log; and the project's decisions file read by code (its
next number, an entry, the last headings). Not: *Talk reads no file* (§156.8) — that waits for the map's text in the call
(§156.1, spec 99), without which a Talk with no file reads less than today; writing a decision (§118.1, §138.7: spec
99); a working task's call (`_claude_work`), the Catapult's (`_claude_call`), a one-shot answer (`_claude_ask`): each
keeps its flags; any other tool than Claude Code (their read argv are as they are).

| part | builds | files (and their tests) |
|---|---|---|
| **A. The read-only call** | §1–§4 | `realm/harness_claude.py` (the denials, the floor, stream-json, `claude_result`), `realm/harnesses.py` (the Claude harness's `result`; `usage_split` and `capped` read either output), `realm/call_log.py` (the bound, the reads on the line, `session_of`, the floor's measure), `core/idea_keeper.py` (`ask` sets the step's bound); `tests/test_harnesses.py`, `tests/test_call_log.py`, `tests/test_idea_keeper.py` |
| **B. The decisions file** | §5 | new `realm/decisions_log.py`; new `tests/test_decisions_log.py` |

## 1. What a read-only call may not read (A; §156.8)
`_claude_read` adds `Read(...)` rules (gitignore patterns, relative to the call's folder), kept as `READ_DENIED` in
`harness_claude.py`, to its **one** `--disallowedTools` list (merged with `CLAUDE_READ_ONLY`'s and `CLAUDE_READ_WEB`'s, never
a second flag: whether the CLI adds or replaces a repeated flag is not something to lean on):
- **lockfiles**: `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `bun.lockb`,
  `uv.lock`, `poetry.lock`, `Pipfile.lock`, `Cargo.lock`, `Gemfile.lock`, `composer.lock`, `go.sum`, `Podfile.lock`,
  `pubspec.lock`, `mix.lock`, `flake.lock`, `packages.lock.json`, each as `Read(**/<name>)`;
- **vendored copies**: `node_modules`, `bower_components`, `vendor`, `third_party`, `Pods`, `.venv`, `venv`,
  `site-packages`, each as `Read(**/<dir>/**)`;
- **generated output**: `dist`, `build`, `out`, `.next`, `.nuxt`, `.svelte-kit`, `.turbo`, `.parcel-cache`, `coverage`,
  `storybook-static`, `__pycache__` as `Read(**/<dir>/**)`, and `Read(**/*.min.js)`, `Read(**/*.min.css)`,
  `Read(**/*.map)`, `Read(**/*.pyc)`;
- **the decisions file whole**: `Read(**/decisions.md)`, `Read(**/DECISIONS.md)` (a leader gets its goal's entry and
  the last headings by code, §5; never the file).
It is added on every read argv (`web` or not) and never on `_claude_work`, `_claude_call` or `_claude_ask`. The rules
already written for read folders (`_claude_read_dirs`) are unchanged.

## 2. The floor of a read-only call (A; §156.9)
`_claude_read` runs with **none of the person's MCP servers** — `--strict-mcp-config --mcp-config '{"mcpServers":{}}'`
— unless a Test bench run names its own (`ORKCRAFT_MCP_CONFIG`: `_claude_mcp()` as today wins), and **no skills** —
`--disable-slash-commands` — each only when the installed CLI lists the flag (`cli_has`). The project's CLAUDE.md stays
(no `--bare`: it needs an API key, never a subscription). The flags it added are named on the call's line (§3:
`bare: ["mcp", "skills"]`, the ones it could add), so the calls before and after are told apart.

## 3. Its reads counted (A; §156.8)
1. **The read argv prints its events**: `--output-format stream-json --verbose` in place of `--output-format json`, so
   the tool calls are in the output. One reader of Claude's output, `claude_envelope(stdout)` in `harness_claude.py`:
   the last `{"type": "result"}` event of stream-json, else the one JSON object of `--output-format json` (a cassette
   recorded before this, any other caller), else `None`. `claude_result` (the Claude harness's `result`), `usage_split`,
   `capped` and `call_log.session_of` read through it, so every caller gets what it got before: the same text, cost,
   tokens, session, usage and cap. `claude_error` already reads both.
2. `claude_reads(stdout)` → `{"files": n, "searches": m, "paths": [...], "denied": d}`: `n` the distinct `file_path`s of
   the `Read` tool uses, `m` the `Grep` and `Glob` uses, `paths` the first 30 read (relative to the call's folder when
   under it), `d` the result envelope's `permission_denials` whose tool is `Read`, `Grep` or `Glob`.
3. **The bound**: the keeper's `ask` runs its call inside `call_log.bounded(n)` (`n` = `idea_target.READS[step]`, the
   number its prompt already names), a context variable as `of_project` is. `call_log.record` writes on a read call's
   line `reads` (§3.2's dict, for a Claude read), `bound` (when one is set) and **`over: true` when `files` passed the
   bound** — the line in the day's log §156.8 asks for. Nothing else changes on the line; a line with no `reads` (a
   tool that prints no events, an older line) is read as before by every reader (`totals`, `day_log`, `analytics`).

## 4. The measure, before and after (A; §156.9)
`call_log.floor(lines)` → `{"before": {...}, "after": {...}}`: of the one-turn read calls of the keeper (`mode` `read`,
`purpose` `plan` or `sort`), split by whether the line has `bare`, each side's count and median of the usage's
`cache_creation_input_tokens` and of `cost`. `python -m orkboard.realm.call_log floor <project>` prints it for the
project's last 7 days (`.orkcraft/logs/<day>/*/calls.jsonl`). The owner runs it on their game after a day on the new
floor; its numbers go into this spec's *As built*. `idea_target`'s floor (`FLOOR_CALLS`, measured from the day log) needs
no change: it reads the newest calls, so it follows the new floor by itself.

## 5. The decisions file, read by code (B; §156.11)
`realm/decisions_log.py`, no model, no face:
- `DEFAULT = "docs/decisions.md"`; `path(root, chosen="")` → the project's decisions log: `chosen` (a path the person
  confirmed at the first opening, spec 99) when given, else `DEFAULT`; relative to `root`, never outside it.
- `found(root)` → the logs of decisions the project keeps already, to be offered as the path (never a second one): a
  `docs/adr/` or `doc/adr/` folder, and any `decisions.md` / `DECISIONS.md` at most three folders down, outside
  `code_map.SKIP`; at most 5, the shallowest first.
- `next_number(text)` → the last heading `## N.` (`## 158. …`) plus one; `1` when there is none. A heading's number is
  read only at a line's start (`^## (\d+)\.`), so a `## 12.` in a code block of an entry is the only thing that could
  mislead it, and such a block is skipped (lines between ``` fences are not read).
- `entry(text, n)` → the section `## n.` up to the next `## ` heading (fences respected), `""` when there is none; cut at
  `ENTRY_MAX` = 4,000 characters, a cut entry ending *… (cut: read the file for the rest)*.
- `headings(text, last=10)` → the last `last` headings, each `N. Title`, the title cut at 160 characters.
- `context(root, n=None, chosen="")` → the text a leader's call is given: *The project's decisions (<path>): the last
  ten:* and the headings, then *This goal's decision:* and `entry(n)` when `n` is given; `""` when the file is missing.
  At most `ENTRY_MAX` + 2,000 characters. Read once a call; a file over 2 MB is read from its end (the last 2 MB) for
  `headings` and `next_number`, and `entry` reads it whole only when `n` is not found there.

## 6. Tests
A: the denials on every Claude read argv (lockfiles, vendored, generated, the decisions file) and on no work, call or
ask argv; the floor's two flags only when the CLI lists them, the bench's MCP config winning over the empty one; the
read argv's stream-json; `claude_envelope` from stream-json, from one JSON object, from nothing; `claude_result`,
`usage_split`, `capped` and `session_of` giving the same answers from both outputs (a recorded envelope of today's and
its stream-json twin); `claude_reads` counting distinct files, searches, the denied, the paths made relative; a keeper
call's line with `reads`, `bound` and `over` (a stub call that read 3 files on a step bounded at 2), none on a work call;
`bare` on the line; `floor` splitting and taking medians; the command printing it. B: `path` with and without a chosen
path, never outside the root; `found`'s folders and files, its depth, its skips; `next_number` (none, one, many, a `##`
in a fence, a heading with no number); `entry` (found, missing, the last one, cut); `headings` (ten of many, fewer);
`context`'s text and bound; a large file read from its end. The critical tests (`tests/test_architecture.py`,
`tests/test_board_alone.py`, `tests/test_updates.py`) and each part's files' tests.

## As built (A)

Files: `realm/harness_claude.py` (`READ_LOCKFILES`, `READ_VENDORED`, `READ_GENERATED`, `READ_DENIED`, `NO_MCP`, `claude_floor`,
`_claude_read_tools`, `claude_envelope`, `claude_events`, `claude_reads`; `_claude_read` on stream-json), `realm/harnesses.py` (the
Claude harness's `result` is `claude_result`; `usage_split` and `capped` read through `claude_envelope`; the new names re-exported),
`realm/call_log.py` (`bounded`, `_reads` on a read line, `session_of` through the envelope, `floor`, `week`, `main`), `core/idea_keeper.py`
(`ask` inside `call_log.bounded(idea_target.READS.get(step))`). Tests in `tests/test_harnesses.py`, `tests/test_call_log.py`,
`tests/test_idea_keeper.py`.

- **A keeper read's argv** (Claude Code that lists the flags): `claude -p <prompt> --output-format stream-json --verbose --allowedTools
  Read,Grep,Glob --disallowedTools Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch,Read(**/package-lock.json),…,Read(**/DECISIONS.md)
  --model opus --strict-mcp-config --mcp-config {"mcpServers":{}} --disable-slash-commands --effort … --max-budget-usd … --no-session-persistence`
  (43 `Read(...)` rules in the one list). A bench run's own MCP configuration takes the empty one's place, and `bare` then names `skills` only.
- **Decided here:** `capped`'s word scan skips stream-json's `user` events (a file the call read that says *max_budget* is no cap); a stream
  that never reached its `result` gives empty text, never the raw stream; `bare` on the line is read again from the cached `cli_has` in
  `record` (the argv is `jobs.py`'s); `reads` is on a line only when the output is a stream (a cassette's single envelope has none, so no
  `over`), `bound` whenever one is set; a step not in `READS` has no bound.
- **The measure** (`python -m orkboard.realm.call_log floor <project>`): the Claude `read` lines of purpose `plan`/`sort`, ended well, at most
  `idea_target.FLOOR_OUT` output tokens, split by `bare`. **The numbers before and after are the owner's to read** on their game after a day
  on the new floor; they are written here then.

## As built (B)

New `realm/decisions_log.py` and `tests/test_decisions_log.py`, standard library only (`code_map.SKIP` imported). `path` returns an absolute
`Path` under the root (a chosen path resolving outside it, a symlink out, or the root itself falls back to `DEFAULT`); `found` counts
`docs/adr` and `doc/adr` as two folders down when ordering; a title is cut at 160 characters with no marker; an entry past `ENTRY_MAX` is
its first 4,000 characters and the *cut* line; `context` of a file with no numbered heading says *none numbered yet.*; only ``` fences are
read as fences; an unnumbered `## ` heading ends an entry and is counted by nothing. Read against Orkboard's own `docs/decisions.md`:
`next_number` 159, `context(root, 156)` 5,738 characters.
