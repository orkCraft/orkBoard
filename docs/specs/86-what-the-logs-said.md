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
