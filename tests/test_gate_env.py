"""Spec 107 §1.1 (realm/gate_env.py): a gate that could not run is told from one that is red; what install would make it run; the install itself."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from orkboard.realm import dep_links, gate_env


@pytest.mark.parametrize("out,code,name", [
    ("> vitest run\n\nsh: vitest: command not found\n", 127, "vitest"),
    ("sh: 1: vitest: not found\n", 127, "vitest"),
    ("/bin/sh: 1: vitest: not found\n", 127, "vitest"),
    ("bash: line 1: vitest: command not found\n", 127, "vitest"),
    ("zsh: command not found: vitest\n", 127, "vitest"),
    ("'vitest' is not recognized as an internal or external command,\noperable program or batch file.\n", 1, "vitest"),
    ("Error: Cannot find module 'vitest'\nRequire stack:\n- /w/x.js\n", 1, "vitest"),
    ("Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'vitest' imported from /w/vitest.config.js\n", 1, "vitest"),
    ("Error: Cannot find module '@scope/pkg/lib/x.js'\n", 1, "@scope/pkg"),
    ("/usr/bin/python: No module named pytest\n", 1, "pytest"),
    ("ModuleNotFoundError: No module named 'requests.adapters'\n", 1, "requests"),
])
def test_a_command_or_package_that_is_not_there_is_named(out, code, name):
    assert gate_env.could_not_run(out, code) == f"The tests could not run: `{name}` is not installed."


def test_code_127_with_no_name_still_could_not_run():
    assert gate_env.could_not_run("something odd\n", 127) == "The tests could not run: a command they need is not installed."


@pytest.mark.parametrize("out,code", [
    ("Error: Cannot find module './foo'\n", 1),                              # a file of the project: the code's fault
    ("Error: Cannot find module '/work/src/foo.js'\n", 1),
    ("Error: Cannot find module '../lib/bar'\n", 1),
    ("FAILED tests/test_a.py::test_x - assert 1 == 2\n1 failed, 3 passed in 0.5s\n", 1),
    ("sh: vitest: command not found\n", 0),                                  # a run that passed tested the code
    ("", 1),
])
def test_a_red_run_that_tested_the_code_is_not_one_that_could_not_run(out, code):
    assert gate_env.could_not_run(out, code) == ""


def test_a_missing_file_of_the_project_does_not_hide_a_missing_package_after_it():
    out = "Error: Cannot find module './foo'\nError: Cannot find module 'vitest'\n"
    assert "`vitest`" in gate_env.could_not_run(out, 1)


def pkg(folder: Path, deps: dict | None = None, dev: dict | None = None, lock: str = "", **more) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    data = {"name": folder.name or "x", "scripts": {"test": "vitest"}, **more}
    if deps is not None:
        data["dependencies"] = deps
    if dev is not None:
        data["devDependencies"] = dev
    (folder / "package.json").write_text(json.dumps(data))
    if lock:
        (folder / lock).write_text("")
    return folder


@pytest.mark.parametrize("lock,command", [
    ("package-lock.json", "npm ci"), ("npm-shrinkwrap.json", "npm ci"), ("pnpm-lock.yaml", "pnpm install --frozen-lockfile"),
    ("yarn.lock", "yarn install --frozen-lockfile"), ("bun.lock", "bun install"), ("bun.lockb", "bun install"), ("", "npm install"),
])
def test_missing_names_the_command_of_the_folders_lock(tmp_path, lock, command):
    pkg(tmp_path / "prototypes" / "ar", dev={"vitest": "^1"}, lock=lock)
    assert gate_env.missing(tmp_path) == [{"dir": "prototypes/ar", "command": command}]


def test_missing_is_dot_for_the_root_and_skips_what_is_installed_or_lists_nothing(tmp_path):
    pkg(tmp_path, deps={"left-pad": "1"}, lock="package-lock.json")
    pkg(tmp_path / "server", dev={"vitest": "1"}, lock="yarn.lock")
    (tmp_path / "server" / "node_modules").mkdir()                              # installed
    pkg(tmp_path / "tools")                                                     # lists no dependency
    pkg(tmp_path / "docs", deps={}, dev={})
    assert gate_env.missing(tmp_path) == [{"dir": ".", "command": "npm ci"}]


def test_a_workspace_member_under_an_installed_root_is_not_missing(tmp_path):
    pkg(tmp_path, dev={"vitest": "1"}, workspaces=["packages/*"])
    (tmp_path / "node_modules").mkdir()
    pkg(tmp_path / "packages" / "a", deps={"x": "1"})
    assert gate_env.missing(tmp_path) == []


def test_python_is_never_installed(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "requirements.txt").write_text("pytest\n")
    assert gate_env.missing(tmp_path) == []


def say(code: str) -> str:
    return f"{sys.executable} -c {json.dumps(code)}"


def test_install_runs_each_row_in_its_folder_one_after_another_and_logs_them(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    rows = [{"dir": "a", "command": say("import os; open('made.txt', 'w').write(os.getcwd()); print('first')")},
            {"dir": "b", "command": say("print('second')")}]
    lines: list[str] = []
    ok, out = gate_env.install(tmp_path, rows, threading.Event(), 60, log=lines.append)
    assert ok and (tmp_path / "a" / "made.txt").read_text().endswith("a") and "first" in out and "second" in out
    assert "".join(lines).startswith(f"== installing: a: {rows[0]['command']}\n") and f"== installing: b: {rows[1]['command']}" in "".join(lines)


def test_install_stops_at_the_first_row_that_fails_and_keeps_the_last_4000_characters(tmp_path):
    rows = [{"dir": ".", "command": say("import sys; print('x' * 6000); print('the end'); sys.exit(3)")},
            {"dir": ".", "command": say("open('never.txt', 'w')")}]
    ok, out = gate_env.install(tmp_path, rows, threading.Event(), 60)
    assert not ok and len(out) <= gate_env.OUT_KEEP and out.rstrip().endswith("the end")
    assert not (tmp_path / "never.txt").exists()


def test_install_without_the_tool_says_so(tmp_path):
    ok, out = gate_env.install(tmp_path, [{"dir": ".", "command": "no-such-installer-xyz ci"}], threading.Event(), 60)
    assert (ok, out) == (False, "no-such-installer-xyz is not installed on this computer")


def test_install_with_nothing_to_install_is_ok(tmp_path):
    assert gate_env.install(tmp_path, [], threading.Event(), 60) == (True, "")


def test_install_that_takes_too_long_says_so(tmp_path):
    ok, out = gate_env.install(tmp_path, [{"dir": ".", "command": say("import time; time.sleep(30)")}], threading.Event(), 1)
    assert not ok and "took longer" in out


def test_install_stopped_raises(tmp_path):
    cancel = threading.Event()
    threading.Timer(0.5, cancel.set).start()
    with pytest.raises(InterruptedError):
        gate_env.install(tmp_path, [{"dir": ".", "command": say("import time; time.sleep(30)")}], cancel, 60)


def test_present_counts_the_links_into_the_main_checkout(tmp_path):
    main, tree = tmp_path / "main", tmp_path / "tree"
    pkg(main, dev={"x": "1"})
    pkg(main / "web", dev={"x": "1"})
    (main / "node_modules").mkdir()
    (main / "web" / "node_modules").mkdir()
    (main / ".venv").mkdir()
    (tree / "web").mkdir(parents=True)
    assert dep_links.present(main, tree) == 0
    (tree / "node_modules").symlink_to(main / "node_modules", target_is_directory=True)
    (tree / "web" / "node_modules").mkdir()                                       # the task's own folder: not a link
    (tree / ".venv").symlink_to(tmp_path, target_is_directory=True)               # a link, but not into the main checkout
    assert dep_links.present(main, tree) == 1
    (tree / "web" / "node_modules").rmdir()
    (tree / "web" / "node_modules").symlink_to(main / "web" / "node_modules", target_is_directory=True)
    assert dep_links.present(main, tree) == 2


@pytest.mark.skipif(os.name == "nt", reason="sh")
def test_the_real_shell_message_is_read(tmp_path):
    got = subprocess.run(["sh", "-c", "nonexistent-tool-xyz"], capture_output=True, text=True, cwd=tmp_path)
    assert got.returncode == 127
    assert gate_env.could_not_run(got.stdout + got.stderr, got.returncode) == "The tests could not run: `nonexistent-tool-xyz` is not installed."
