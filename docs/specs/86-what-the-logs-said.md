# Spec 86 — What the logs said: run the project's commands, its tests, count a cost once, stop a loop, mind the floor

The owner, 25 October (decisions §103), from the logs of a day on a Node game: the Board said $11.22 for about $4.5;
77 of 412 turns refused; no test ran; one check sent back nine times; two of eight leader calls out of their budget.
**Builds:** Claude · **Review:** full · P0.

| part | builds | files (and their tests) |
|---|---|---|
| **A. Cost once** | §1 | `core/idea_runner.py` (`_session`), `realm/jobs.py` / `realm/tool_run.py` (`result_of`'s `before` for Claude); `tests/test_idea_runner.py`, `tests/test_jobs.py` |
| **B. Commands** | §2 | `realm/harness_claude.py` (`_claude_work`: `--allowedTools`, `--disallowedTools`), new `realm/task_commands.py` (the list), `realm/idea_git.py` (`prepare`: the dependencies linked); new `tests/test_task_commands.py`, `tests/test_idea_git.py` |
| **C. The gate** | §3 | `realm/gate_config.py` (`read`: the project's own when no `[gate]`), `core/idea_runner.py` (no tests: never lands by itself), the faces' *no tests* line (`js/shell/review.js`, `pwa/shell-review.js`); `tests/test_gate_config.py` |
| **D. Findings** | §4 | `realm/idea_checks.py` (`kind`), the check's prompt, `core/idea_runner.py` (fresh session), `js/shell/review.js`, `js/arena/waits.js`, `pwa/shell-review.js`; `tests/test_idea_checks.py`, the Review tests |
| **E. Floor** | §5 | `realm/idea_target.py` (`budget` ≥ floor, Lean's tiers), `core/idea_keeper.py`; `tests/test_idea_target.py` |

## 1. A cost counted once (A)
A Claude call that resumed a session reports the session's total: the runner keeps each task's `session_total` (the last
`total_cost_usd` of its session) and adds `cost - session_total` (never below 0); a fresh session adds its whole cost.
The same for the keeper's sessions. `calls.jsonl` keeps the tool's figure and gains `cost_own` (the difference). Old
tasks' sums are not rewritten.

## 2. The commands a task may run (B)
`task_commands.allowed(root, task)` → the `--allowedTools` rules, `denied()` → the `--disallowedTools` rules (decisions
§103.2's lists as `Bash(<cmd> *)` rules; the project's scripts read from `package.json`, `Makefile` targets named
`test|build|lint|check`, the gate's `run`). A pick task (`pick` set) adds the media tools. Denied wins. The list is one
line in the task's log. `IdeaGit.prepare` links the main checkout's `node_modules/` (each `package.json` folder) and
`.venv/` into the worktree when they exist and the worktree has none (a symlink; removed with the worktree, never
committed: `.git/info/exclude` gets them).

## 3. The project's gate (C)
`gate_config.read(root)` with no `[gate]`: `npm test` (with `--prefix` per folder that has a `test` script, at most 3) /
`python -m pytest -q` / `go test ./...` / `cargo test`, the first that holds, as `run`, and `always` empty; Orkboard's own
repository keeps its `orkcraft.toml`. None: `Gate(run="", none=True)`; the runner then never lands the result by itself
(*no tests in this project*), the faces say it where the tests are said.

## 4. Findings of the code and of the place (D)
The check's instructions: each finding has `"kind": "code"` or `"env"` (*it could not be done here: a command refused,
a tool missing, no device*). `parse_findings` reads `kind` (missing: `code`). *Fix the findings left* lists only `code`
findings; with none left of the code, *Send back* gives way to Merge and Drop, with the line *What is left is about where
it ran, not the code*; when a send back would carry the same findings left as the round before, the same. A send back
whose task's session read more than 150 k tokens in its last call starts a fresh session: the task's prompt, the diff so
far, and the why.

## 5. The floor (E)
`idea_target.floor(tier, tool)`: the median cost of the last ten one-turn keeper calls of that tier on that tool
(`calls.jsonl`), else `FLOOR = {"elder": 0.25, "warrior": 0.10, "laborer": 0.03}`; `budget(step, target)` is never under
1.5 × the floor of the step's tier. Lean (thrift): `draft`, `answer`, `talk` and `collide` on `warrior`; `goal` and `plan`
stay `elder`.

## 6. Tests
A: a resumed session's three calls add their differences; a fresh one its whole. B: the rules for a Node project, a
Python one, a pick; denied wins; the links laid and excluded. C: each kind's gate; none → never lands by itself. D: `kind`
read and defaulted; the why lists code findings only; env-only offers Merge; the same findings twice; a fresh session past
150 k. E: the floor from the log and the table; no budget under it; Lean's tiers. Each part: the critical tests and its
files' tests.

## As built (B, C, E)

- **B.** `realm/task_commands.py` (new): `allowed(root, task=None)` -> `Bash(<cmd>)` and `Bash(<cmd> *)` rules, both forms for each command so a bare `npm test` and one with arguments match: reading (`ls cat grep find head tail wc pwd cd`, `git status|diff|log|show|branch|ls-files|rev-parse`), local git (`add commit checkout switch stash merge rebase`), each `package.json` folder's (two levels deep, none in `node_modules`) `test` (unless npm's placeholder) and the scripts named `test|build|lint|check|typecheck` (and `test:…`) as `npm test` / `npm run <name>` (also `yarn`/`pnpm` where a lock file stands), the Makefile's `test|build|lint|check` targets, each command of the gate's `run`, pytest / `go test|build|vet` / `cargo test|build|check|clippy` by the files the root has; `task["pick"]` adds `ffmpeg ffprobe sox soxi python3 node`. `denied()` -> `git push`, `rm -rf`, `sudo`, `curl`, `wget`, `ssh`, `scp`, `npm install|i|ci|add`, `pip install`, `yarn|pnpm install|add`, `uv pip|add|sync`, `find … -delete|-exec rm`. `line(rules)` is the log line. `harness_claude._claude_work_rules` -> `--allowedTools` / `--disallowedTools` (comma-joined, as the other lists); `Harness.work_rules` (new field, Claude only) and `Harness.work(…, allow, deny)` append them to `_claude_work`'s argv. `jobs.work_cmd` / `run_work` gained `task=None, root=None` and give a tool that has `work_rules` the lists of `root` (default: `workdir`, a checkout of the project) and the task. **`core/idea_runner.py` `_session` is not changed here**: it passes neither, so every task gets the list for its worktree and no pick task gets the media tools until it passes `task=` (and `root=self.repo_root`). No log hook was reached; `task_commands.line` is ready for it.
- `realm/dep_links.py` (new; `idea_git.py` was at 586 lines): `link(repo_root, worktree)` symlinks `node_modules/` of each folder with a `package.json` (two levels) and `.venv/` where the main checkout has them and the worktree has none, and writes `node_modules` and `.venv` (no trailing slash: a symlink is not a directory to git) to the repository's `info/exclude` once, so `git add -A` and `dirty` never see a link. `IdeaGit.prepare` calls it after `worktree add`; `remove` removes the link with the worktree, the main checkout is whole.
- **C.** `gate_config.derive(root)`, used by `read` with no file, no `[gate]` or a bad file (its `error` kept): a project with any of `CRITICAL_TESTS` gets today's gate (`always` = those that exist, no `run`: Orkboard keeps its own, and its `orkcraft.toml` still wins); else `npm test` (folders with a testing `test` script, three at most, `npm test --prefix <dir>` below the root, joined by ` && `), else `python -m pytest -q` (`pyproject.toml` or `tests/`), `go test ./...`, `cargo test`, with `always = ()`; else `Gate(always=(), none=True)`. `Gate.none` is new; `IdeaGit.gate_run` already gives a not-`custom` gate with no files `ran=False`, so a none gate reports *no tests ran*; the runner's *never lands by itself* and the faces' line are the other parts'. `package_dirs`, `scripts_of`, `has_test` live in `gate_config` (`task_commands` uses them).
- **E.** `idea_target.FLOOR`, `floor(tier, tool="claude")`: the median cost of the last ten keeper calls of the tier on the tool in the shown project's day log (`call_log.days_root()`, new: the project of `of_project` / `keep_days`), `mode` read, purpose `plan|sort`, exit 0, at most 400 output tokens ("one turn"), four days back; fewer than three read, or no log: the table; kept five minutes. `budget(step, target)` = the cap of the Target, never under `HEADROOM` (1.5) x `floor` of the tier the Target gives the step (rounded up to the cent); a step the Target skips keeps its cap. MATRIX thrift: `draft`, `answer`, `talk`, `collide` -> `("warrior", "low")`; `goal`, `plan` stay `elder`; `kind` is not changed. **What it costs**: every Seasoned step is now 0.15 (was 0.03-0.08), `propose` balance 0.38, so a pitch's price is 0.56-1.13 (was 0.29-0.58) and Lean's pitch 0.40.
- Tests: `tests/test_task_commands.py` (new, 12), `tests/test_gate_config.py` (the derived gates, the repository's own, the none gate, a node gate run), `tests/test_idea_git.py` (the links, never committed, own or tracked ones kept, removed with the worktree), `tests/test_idea_target.py` (the floor from a log and from the table, no budget under it, Lean's tiers); pinned values updated in `test_party_size.py`, `test_idea_collide.py`, `test_idea_night.py`, `test_ideation.py`.


## As built (A, C runner, D)

- **A, cost once.** `realm/tool_run.py` `cost_once(cost, before)` is the difference, never below 0, rounded to 6 places; `before` None (a fresh session, or an old task with no `session_total`) gives the whole cost. `core/idea_session.py` (new, `SessionMixin`; `_session` moved out of the runner): a resumed session passes the task's `session_total` as `before_cost` to `jobs.run_work`, adds `cost_once(...)` to the task's `cost` and the ledger line (`idea_spend.task_line`), and keeps the tool's figure as the new `session_total` (and the call's tokens as `last_tokens`). `run_work` charges the telemetry the same difference and `call_log.record` gained `cost_own` (written only for a resumed Claude call; `call_log.totals` sums it when there). The keeper never resumes (every call is a fresh `claude -p`), so it needed nothing; Codex keeps its own `before`. `_launch` clears `session_total` and `last_tokens`; old tasks' sums are not rewritten. `_session` also passes `task=` and `root=` to `run_work` (part B's rules).
- **C, the runner's side.** `_tests_of` sets `tests["none"]` from `gate_config.read(root).none`; `look_reason` then answers *no tests in this project* and the result waits. The faces' `testsWords` say *no tests in this project* for it (`js/shell/review.js`, `pwa/shell-review.js`; so the preview, the result's card, `js/arena/waits.js` and the phone's stop and screen all show it), and the *Waits* reason of spec 84 §4 says it again.
- **D, kinds.** `idea_checks.parse_findings` keeps `kind` ("env", else "code"); `code_left`, `is_env` and `same_left` (the findings left, by lowercased where and what) are beside it. `idea_task.FINDINGS_ASK` asks for `kind` and says what `env` is (a command refused, a tool missing, no device or network). A check's send back is told only the code findings left. `_work` keeps the round before's findings and sets the task's `same_as_before` with the new ones; `ideas.review_list` exposes `findings[].kind` and `same`. Both faces: `codeLeftOf`, `placeOnly` (a check whose findings left are all of the place, or `same`): *Fix them* lists code findings only; `placeOnly` offers Merge (*Leave them* when it changed no file) and Drop, no Send back, with the line *What is left is about where it ran, not the code*; an `env` finding in the list is marked *(where it ran)*.
- **D, fresh session.** `idea_task._again_prompt` (now given the worktree and its base): a send back whose task's `last_tokens` is over `FRESH_TOKENS` (150 000, cache reads included, the last call's) resumes nothing: the task's prompt, `git diff <base>...HEAD` cut to 20 000 characters, then the why (and a check's code findings left). The new session's cost is added whole and its total becomes `session_total`.
- Merged with part B (`task_commands`, f3aef95); the round's first log line is now `task_commands.line(...)`.
- Tests: `tests/test_lands_by_itself.py` (cost once over three rounds, fresh session, `none`), `tests/test_idea_checks.py` (kind, `code_left`, `same_left`, the ask, the flag over rounds, the code-only send back), `tests/test_call_log.py` (`cost_own`, `cost_once`), `tests/test_check_review_desktop_browser.py` and `tests/test_pwa_check_review_browser.py` (place-only, mixed, same, no tests). The runner's test stub reports a running total per resumed session (`STUB_BIG` for a 200 k call).
