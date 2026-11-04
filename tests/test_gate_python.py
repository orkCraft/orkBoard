"""Spec 143 C (decisions §250.4): a gate that could not run installs only what is missing, names the command that would make Python's tests run, and
runs pytest with a Python that has it."""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard.core.idea_task import TaskMixin
from orkboard.realm import gate_env, idea_git
from orkboard.realm.idea_git import IdeaGit

from tests.test_gate_env import pkg


def package_with_vitest_and_vscode(root: Path) -> None:
    pkg(root / "vscode", dev={"vitest": "1"}, lock="package-lock.json")           # a folder whose packages are not installed


def test_pytest_missing_offers_no_npm_row_and_vitest_missing_offers_its_row(tmp_path):
    package_with_vitest_and_vscode(tmp_path)
    assert gate_env.missing(tmp_path, "The tests could not run: `pytest` is not installed.") == []
    assert gate_env.missing(tmp_path, "The tests could not run: `vitest` is not installed.") == [{"dir": "vscode", "command": "npm ci"}]
    assert gate_env.missing(tmp_path) == [{"dir": "vscode", "command": "npm ci"}]                       # no name: as before
    assert gate_env.missing(tmp_path, "The tests could not run: `numpy` is not installed.\nModuleNotFoundError: No module named 'numpy'") == []


@pytest.mark.parametrize("what,kind", [
    ("The tests could not run: `pytest` is not installed.", "python"), ("`ruff` is not installed", "python"),
    ("`numpy` is not installed\n/usr/bin/python: No module named numpy", "python"),
    ("The tests could not run: `vitest` is not installed.", "node"), ("`@scope/pkg` is not installed", "node"),
    ("`left-pad` is not installed\nCannot find module 'left-pad'", "node"),
    ("`cargo` is not installed", ""), ("", ""),
])
def test_the_kind_of_what_is_missing(what, kind):
    assert gate_env.kind_of(what) == kind


def test_the_python_setup_is_read_by_code_for_a_lock_and_a_dev_extra_a_dev_extra_alone_and_neither(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n[project.optional-dependencies]\ndev = ["pytest"]\n')
    assert gate_env.python_setup(tmp_path) == "python -m venv .venv && .venv/bin/pip install -e '.[dev]'"
    (tmp_path / "uv.lock").write_text("")
    assert gate_env.python_setup(tmp_path) == "uv sync --extra dev"
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
    assert gate_env.python_setup(tmp_path) == "python -m venv .venv && .venv/bin/pip install pytest"
    assert gate_env.python_setup(tmp_path / "nowhere") == "python -m venv .venv && .venv/bin/pip install pytest"


def test_a_run_that_lacked_pytest_carries_its_setup_and_no_rows_and_one_that_lacked_vitest_its_row(tmp_path):
    package_with_vitest_and_vscode(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n[project.optional-dependencies]\ndev = ["pytest"]\n')
    (tmp_path / "uv.lock").write_text("")

    def tests_of(out: str) -> dict:
        env = gate_env.could_not_run(out, 1)
        run = idea_git.GateRun(False, out, True, "pytest", 1, 1.0, env)
        return TaskMixin._tests_of(SimpleNamespace(repo_root=tmp_path, _gate_runs={str(tmp_path): run}), tmp_path, out, "red")

    py = tests_of("/x/.venv/bin/python: No module named pytest\n")
    assert py["env"] == "The tests could not run: `pytest` is not installed." and py["install"] == [] and py["setup"] == "uv sync --extra dev"
    node = tests_of("sh: vitest: command not found\n")
    assert node["install"] == [{"dir": "vscode", "command": "npm ci"}] and "setup" not in node


def fake_python(folder: Path, name: str, has_pytest: bool) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    exe = folder / name
    exe.write_text(f"#!/bin/sh\nexit {0 if has_pytest else 1}\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return exe


def test_python_is_the_venvs_then_a_path_python_with_pytest_then_orklines_own(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    bin_ = tmp_path / "bin"
    monkeypatch.setattr(gate_env, "_PATH_PYTHON", {})
    monkeypatch.setenv("PATH", str(bin_))
    git = IdeaGit(root)
    assert git.python() == sys.executable                                           # no .venv, none on the PATH
    fake_python(bin_, "python3", False)
    monkeypatch.setattr(gate_env, "_PATH_PYTHON", {})
    assert git.python() == sys.executable                                           # one on the PATH, without pytest
    good = fake_python(tmp_path / "bin2", "python3", True)
    monkeypatch.setenv("PATH", f"{good.parent}{os.pathsep}{bin_}")
    assert git.python() == str(good)                                                # the one with pytest wins over `sys.executable`
    monkeypatch.setenv("PATH", str(bin_))
    fake_python(bin_, "python", True)
    monkeypatch.setattr(gate_env, "_PATH_PYTHON", {})
    assert git.python() == str(bin_ / "python")                                     # `python3` has none: then `python`
    venv = root / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "python").write_text("")
    assert git.python() == str(venv / "python")                                     # a .venv wins, with no pytest in it or not


def test_the_path_is_asked_once_per_process(tmp_path, monkeypatch):
    bin_ = tmp_path / "bin"
    monkeypatch.setattr(gate_env, "_PATH_PYTHON", {})
    monkeypatch.setenv("PATH", str(bin_))
    exe = fake_python(bin_, "python3", True)
    assert gate_env.path_python() == str(exe)
    exe.unlink()
    assert gate_env.path_python() == str(exe)                                       # kept
