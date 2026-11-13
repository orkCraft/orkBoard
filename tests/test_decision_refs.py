"""Goal "The battle and the gate", stage C (decisions §303.2, §303.3): what names a decision, read from a fixture repository, and nothing written."""
from __future__ import annotations

import hashlib
from pathlib import Path

from orkboard.realm import decision_refs as refs

LOG = """# Decisions

## 1. First
Plain.

## 2. Second (the one asked)
It says §2.1 of itself and §2 again.

## 3. Third
Changes: 2. It rests on §2.4 and on spec 154 §2.
"""


def _repo(tmp_path: Path) -> Path:
    def w(rel, text):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    w("docs/decisions.md", LOG)
    w("llm-wiki/general/pages/ideas/goal-a.md", "Rests on §2 and again §2.3.\n")
    w("llm-wiki/general/pages/ideas/goal-b.md", "Only spec 154 §2 and docs/x.md §2.\n")
    w("tests/test_a.py", '"""Guards decisions §2, §3."""\n\ndef test_one():\n    """decisions §1"""\n\ndef test_two():\n    pass\n')
    w("tests/test_b.py", '"""Nothing."""\n\ndef test_x():\n    """spec 154 §2 and docs/x.md §2"""\n')
    w("tests/test_c.py", '"""Module: decisions §3."""\n\ndef test_y():\n    pass  # decisions §99\n')
    return tmp_path


def _snap(root: Path):
    return {p.as_posix(): hashlib.sha1(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_what_rests_on_a_decision_counts_each_file_once_and_never_the_decision(tmp_path):
    root = _repo(tmp_path)
    assert refs.rests_on(root, 2) == {"goals": ["goal-a"], "decisions": [3], "tests": ["tests/test_a.py"]}
    assert refs.rests_on(root, 77) == {"goals": [], "decisions": [], "tests": []}


def test_a_list_after_decisions_reads_as_both(tmp_path):
    assert refs.rests_on(_repo(tmp_path), 3)["tests"] == ["tests/test_a.py", "tests/test_c.py"]


def test_a_specs_point_is_not_a_decision(tmp_path):
    r = refs.rests_on(_repo(tmp_path), 2)
    assert "goal-b" not in r["goals"] and "tests/test_b.py" not in r["tests"]


def test_a_failing_tests_own_text_before_its_modules(tmp_path):
    root = _repo(tmp_path)
    g = {x["id"]: x for x in refs.guards(root, ["tests/test_a.py::test_one", "tests/test_a.py::test_two", "tests/test_b.py::test_x", "tests/test_c.py::test_y"])}
    assert (g["tests/test_a.py::test_one"]["decisions"], g["tests/test_a.py::test_one"]["from"]) == ([1], "function")
    assert (g["tests/test_a.py::test_two"]["decisions"], g["tests/test_a.py::test_two"]["from"]) == ([2, 3], "module")
    assert (g["tests/test_b.py::test_x"]["decisions"], g["tests/test_b.py::test_x"]["from"]) == ([], "file")
    assert g["tests/test_c.py::test_y"]["decisions"] == [3]          # §99 is not in the log


def test_the_run_files_agreeing_pile(tmp_path):
    assert refs.named_by(_repo(tmp_path), ["tests/test_a.py", "tests/test_c.py"]) == [1, 2, 3]


def test_reading_writes_nothing(tmp_path):
    root = _repo(tmp_path)
    before = _snap(root)
    refs.rests_on(root, 2)
    refs.guards(root, ["tests/test_a.py::test_one"])
    refs.named_by(root, ["tests/test_a.py"])
    assert _snap(root) == before
