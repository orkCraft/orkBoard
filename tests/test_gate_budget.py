"""Spec 149 C (decisions §253.3): the gate's budget. `[gate] browser_max`, the modules left and said, parallel workers where xdist is there, and the way into
main taking what the gate left, whole, with a clock of its own."""
from __future__ import annotations

import json
import stat
import subprocess
import threading
from pathlib import Path

import pytest

from orkboard.realm import gate_config, gate_env
from orkboard.realm.idea_git import IdeaGit

PATTERNS = '["tests/test_{stem}*_browser.py", "tests/test_{leaf}*_browser.py"]'


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def toml(root: Path, extra: str = "") -> None:
    (root / "orkcraft.toml").write_text(f"[gate]\nalways = []\nbrowser = {PATTERNS}\n{extra}", encoding="utf-8")


def repo_with(tmp_path: Path, pwa: int, hand: int, extra: str = "browser_max = 3\n") -> Path:
    """A repository with `pwa` modules named test_pwa_*_browser.py (one of them test_pwa_shell_marks_browser.py) and `hand` named test_hand_*_browser.py."""
    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    (root / "pwa").mkdir()
    (root / "hand").mkdir()
    for i in range(pwa - 1):
        (root / "tests" / f"test_pwa_n{i}_browser.py").write_text("def test_ok():\n    pass\n")
    (root / "tests" / "test_pwa_shell_marks_browser.py").write_text("def test_ok():\n    pass\n")
    for i in range(hand):
        (root / "tests" / f"test_hand_n{i}_browser.py").write_text("def test_ok():\n    pass\n")
    for name in ("pwa/shell-marks.js", "pwa/shell-other.js", "hand/card.js"):
        (root / name).write_text("// x\n")
    toml(root, extra)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "t@x")
    git(root, "config", "user.name", "T")
    git(root, "add", "-A")
    git(root, "commit", "-m", "start")
    return root


def test_browser_max_is_12_by_default_and_a_bad_one_is_said(tmp_path):
    toml(tmp_path)
    assert gate_config.read(tmp_path).browser_max == 12
    toml(tmp_path, "browser_max = 5\n[gate.main]\ntimeout_min = 45\n")
    assert (gate_config.read(tmp_path).browser_max, gate_config.read(tmp_path).main_timeout_min) == (5, 45)
    toml(tmp_path, 'browser_max = "many"\n')
    assert "browser_max" in gate_config.read(tmp_path).error
    toml(tmp_path, "browser_max = 0\n")
    assert "browser_max" in gate_config.read(tmp_path).error
    assert gate_config.MAIN_TIMEOUT_MIN == 30 and gate_config.read(tmp_path).main_timeout_min is None


def test_this_repositorys_own_orkcraft_toml_sets_the_budget():
    gate = gate_config.read(Path(__file__).resolve().parent.parent)
    assert gate.error == "" and gate.browser_max == 12 and gate.main_timeout_min == 30


def test_a_pattern_over_the_budget_gives_only_the_modules_named_after_the_file_and_leaves_the_rest(tmp_path):
    root = repo_with(tmp_path, pwa=15, hand=3)
    gate = gate_config.read(root)
    taken, left = gate_config.browser_split(gate, "pwa/shell-marks.js", root)
    assert taken == ["tests/test_pwa_shell_marks_browser.py"] and len(left) == 14
    assert gate_config.browser_files(gate, "pwa/shell-other.js", root) == []
    assert gate_config.browser_left(gate, ["pwa/shell-marks.js"], root) == {"pwa/": 14}
    taken, left = gate_config.browser_split(gate, "hand/card.js", root)             # three modules, within the budget: whole
    assert len(taken) == 3 and left == []
    assert gate_config.browser_left(gate, ["hand/card.js"], root) == {}


def test_what_one_touched_file_brings_is_not_left_by_another(tmp_path):
    root = repo_with(tmp_path, pwa=15, hand=0)
    gate = gate_config.read(root)
    (root / "tests" / "test_pwa_shell_other_browser.py").write_text("def test_ok():\n    pass\n")
    assert gate_config.browser_left(gate, ["pwa/shell-marks.js"], root) == {"pwa/": 15}
    assert gate_config.browser_left(gate, ["pwa/shell-marks.js", "pwa/shell-other.js"], root) == {"pwa/": 14}


def test_with_no_budget_over_it_a_pattern_is_whole_and_the_way_into_main_takes_every_pattern_whole(tmp_path):
    root = repo_with(tmp_path, pwa=15, hand=0)
    gate = gate_config.read(root)
    assert len(gate_config.browser_files(gate, "pwa/shell-marks.js", root, whole=True)) == 15
    assert len(gate_config.gate_files(gate, ["pwa/shell-marks.js"], root, whole=True)) == 15
    assert len(gate_config.gate_files(gate, ["pwa/shell-marks.js"], root)) == 1


def fake_python(root: Path, tmp_path: Path, xdist: bool) -> Path:
    """A `.venv/bin/python` that answers `-c` with whether it has xdist and writes the arguments of a pytest run to a file."""
    seen = tmp_path / "argv.json"
    exe = root / ".venv" / "bin" / "python"
    exe.parent.mkdir(parents=True)
    exe.write_text(f"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then exit {0 if xdist else 1}; fi\nprintf '%s\\n' \"$@\" > {seen}.txt\necho '1 passed in 0.1s'\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return seen


def run_gate(root: Path, touch: str):
    g = IdeaGit(root)
    path, _ = g.prepare("demo", "k1", "main")
    (path / touch).write_text("// changed\n")
    g.commit_left(path, "k1")
    return g.gate_run(path, "main", threading.Event())


@pytest.mark.parametrize("cores,xdist,args", [(8, True, ["-n", "6"]), (4, True, ["-n", "2"]), (16, True, ["-n", "6"]), (2, True, []), (8, False, [])])
def test_browser_tests_run_in_parallel_only_with_xdist_and_cores_to_spare(tmp_path, monkeypatch, cores, xdist, args):
    root = repo_with(tmp_path, pwa=15, hand=3)
    seen = fake_python(root, tmp_path, xdist)
    gate_env._XDIST.clear()
    monkeypatch.setattr("os.cpu_count", lambda: cores)
    run = run_gate(root, "hand/card.js")
    got = Path(f"{seen}.txt").read_text().split()
    assert run.ok and run.browser and ("-n" in got) == bool(args)
    assert args == (got[got.index("-n"):got.index("-n") + 2] if args else [])
    assert ("-n" in run.command) == bool(args)


def test_a_run_with_no_browser_test_has_no_workers(tmp_path, monkeypatch):
    root = repo_with(tmp_path, pwa=15, hand=3)
    (root / "tests" / "test_architecture.py").write_text("def test_ok():\n    pass\n")
    toml(root, 'browser_max = 3\n')
    (root / "orkcraft.toml").write_text((root / "orkcraft.toml").read_text().replace("always = []", 'always = ["tests/test_architecture.py"]'))
    git(root, "add", "-A")
    git(root, "commit", "-m", "an always")
    seen = fake_python(root, tmp_path, True)
    gate_env._XDIST.clear()
    monkeypatch.setattr("os.cpu_count", lambda: 8)
    (root / "x.py").write_text("x = 1\n")
    git(root, "add", "-A")
    run = run_gate(root, "x.py")
    assert run.ok and not run.browser and "-n" not in Path(f"{seen}.txt").read_text().split()


def test_what_the_gate_left_is_said_in_its_log_and_on_the_run_and_the_way_into_main_leaves_nothing(tmp_path):
    root = repo_with(tmp_path, pwa=15, hand=0)
    fake_python(root, tmp_path, False)
    run = run_gate(root, "pwa/shell-marks.js")
    assert run.left == "14 of pwa/" and run.out.rstrip().endswith("== browser tests left for main: 14 of pwa/")
    g = IdeaGit(root)
    path = g.reopen("demo", "k1")
    whole = g.gate_run(path, "main", threading.Event(), 1800, whole=True)
    assert whole.left == "" and "left for main" not in whole.out and len(whole.command.split()) > 8
