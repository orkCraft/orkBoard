"""Spec 86 §2: the commands a task may run (realm/task_commands.py) and how Claude Code gets them (harnesses, jobs)."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.realm import harnesses, jobs, task_commands


def bash(rules: list[str]) -> set[str]:
    return {r[len("Bash("):-1] for r in rules}


def node(root: Path) -> None:
    (root / "package.json").write_text(json.dumps({"scripts": {"test": "node --test", "build": "tsc", "lint": "eslint .",
                                                              "start": "node .", "deploy": "ship it", "test:unit": "jest"}}))


def test_every_task_may_read_and_use_local_git(tmp_path):
    got = bash(task_commands.allowed(tmp_path))
    assert {"ls", "ls *", "cat *", "grep *", "find *", "head *", "tail *", "wc *", "git status", "git diff *", "git log *",
            "git show *", "git add *", "git commit *", "git checkout *", "git switch *", "git stash *", "git merge *",
            "git rebase *"} <= got
    assert not got & {"ffmpeg *", "sox *", "python3 *", "node *", "git push *"}


def test_a_node_project_may_run_its_own_test_build_and_lint_scripts_and_nothing_else_of_them(tmp_path):
    node(tmp_path)
    got = bash(task_commands.allowed(tmp_path))
    assert {"npm test", "npm test *", "npm run build", "npm run lint", "npm run test:unit", "npm test --prefix *"} <= got
    assert not any("deploy" in r or "start" in r for r in got)
    assert not any(r.startswith("yarn") or r.startswith("pnpm") for r in got)                # no lock file: no yarn, no pnpm
    (tmp_path / "pnpm-lock.yaml").write_text("")
    assert {"pnpm build", "pnpm run lint"} <= bash(task_commands.allowed(tmp_path))


def test_the_scripts_of_a_folder_two_levels_down_count_and_node_modules_does_not(tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "package.json").write_text(json.dumps({"scripts": {"check": "svelte-check"}}))
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "package.json").write_text(json.dumps({"scripts": {"build": "x"}}))
    (tmp_path / "node_modules" / "dep").mkdir(parents=True)
    (tmp_path / "node_modules" / "dep" / "package.json").write_text(json.dumps({"scripts": {"lint": "x"}}))
    got = bash(task_commands.allowed(tmp_path))
    assert "npm run check" in got and "npm run build" not in got and "npm run lint" not in got


def test_a_placeholder_test_script_is_not_allowed(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": 'echo "Error: no test specified" && exit 1'}}))
    assert "npm test" not in bash(task_commands.allowed(tmp_path))


def test_a_makefile_gives_its_test_build_lint_and_check_targets(tmp_path):
    (tmp_path / "Makefile").write_text(".PHONY: test\ntest:\n\tpytest\nbuild: deps\n\tcc\ndeploy:\n\tscp x y\nlint :\n\truff .\nVAR := 1\n")
    got = bash(task_commands.allowed(tmp_path))
    assert {"make test", "make build", "make lint"} <= got and "make deploy" not in got and "make check" not in got


def test_the_gates_run_is_allowed_command_by_command(tmp_path):
    (tmp_path / "orkcraft.toml").write_text('[gate]\nrun = "cargo test --all && ./scripts/check.sh | tee out"\n')
    got = bash(task_commands.allowed(tmp_path))
    assert {"cargo test", "cargo test *", "./scripts/check.sh *", "tee *"} <= got


def test_python_go_and_rust_projects_run_their_tests(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "go.mod").write_text("")
    (tmp_path / "Cargo.toml").write_text("")
    got = bash(task_commands.allowed(tmp_path))
    assert {"python -m pytest *", "pytest *", "go test *", "go build *", "cargo test *", "cargo clippy *"} <= got
    assert not bash(task_commands.allowed(tmp_path / "gone")) & {"go test *", "pytest *"}


def test_a_pick_task_also_gets_the_media_tools_and_a_plain_one_does_not(tmp_path):
    plain = bash(task_commands.allowed(tmp_path, {"id": "t1"}))
    pick = bash(task_commands.allowed(tmp_path, {"id": "t1", "pick": {"candidates": 3}}))
    assert {"ffmpeg *", "sox *", "python3 *", "node *"} <= pick and not plain & {"ffmpeg *", "sox *", "python3 *", "node *"}
    assert plain <= pick


def test_denied_has_what_is_never_done_and_nothing_allowed_is_denied(tmp_path):
    denied = bash(task_commands.denied())
    for cmd in ("git push *", "rm -rf *", "sudo *", "curl *", "wget *", "ssh *", "npm install *", "npm ci", "npm ci *", "pip install *",
                "yarn install *", "pnpm install *"):
        assert cmd in denied, cmd
    node(tmp_path)
    (tmp_path / "pyproject.toml").write_text("")
    for task in (None, {"pick": {"x": 1}}):
        assert not bash(task_commands.allowed(tmp_path, task)) & denied


def test_the_list_is_one_line_for_the_log(tmp_path):
    node(tmp_path)
    line = task_commands.line(task_commands.allowed(tmp_path))
    assert line.startswith("commands allowed: ls, ") and "npm test" in line and "\n" not in line and "*" not in line


def test_claude_gets_the_lists_as_allowed_and_disallowed_tools_in_work_mode(tmp_path):
    node(tmp_path)
    h = harnesses.need("claude")
    argv = h.work("do it", tmp_path, "sonnet", allow=task_commands.allowed(tmp_path), deny=task_commands.denied())
    assert argv[argv.index("--permission-mode") + 1] == "acceptEdits"
    allow = argv[argv.index("--allowedTools") + 1].split(",")
    deny = argv[argv.index("--disallowedTools") + 1].split(",")
    assert "Bash(npm test)" in allow and "Bash(git push *)" in deny and not set(allow) & set(deny)
    assert "--allowedTools" not in h.work("do it", tmp_path, "sonnet")                    # no list given: as before


def test_work_cmd_derives_the_list_from_the_worktree_and_the_task_and_only_for_a_tool_that_takes_one(tmp_path):
    node(tmp_path)
    argv = jobs.work_cmd("claude", "p", tmp_path, "sonnet", task={"pick": True})
    allow = argv[argv.index("--allowedTools") + 1]
    assert "Bash(npm test)" in allow and "Bash(ffmpeg *)" in allow
    other = tmp_path / "other"
    other.mkdir()
    argv = jobs.work_cmd("claude", "p", tmp_path, "sonnet", root=other)                   # the project's root, not the worktree
    assert "Bash(npm test)" not in argv[argv.index("--allowedTools") + 1]
    assert "Bash(ffmpeg *)" not in argv[argv.index("--allowedTools") + 1]
    for tool in harnesses.ids():
        if tool != "claude":
            assert "Bash(npm test)" not in " ".join(jobs.work_cmd(tool, "p", tmp_path, "", "")), tool
