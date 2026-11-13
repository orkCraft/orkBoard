"""Goal "The battle and the gate", stage C (decisions §303.2, §303.3): what names a decision, read from a fixture repository, and nothing written.
Stage N3: every N a *Changes:* item joins with *and*, and a `§k` that starts an item or follows a spec read as a spec's point, on a fixture and on this
repository's own log."""
from __future__ import annotations

import hashlib
import re
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


def test_a_changes_paragraph_counts_each_items_n_and_never_a_specs(tmp_path):
    root = _repo(tmp_path)
    (root / "docs/decisions.md").write_text(LOG + "\n## 4. Fourth\nChanges: 2, 174.1;\nspec 34, spec 103, 1.\n\nText after, 3 and 5.\n\n## 103. A number\nPlain.\n", encoding="utf-8")
    assert refs.rests_on(root, 2)["decisions"] == [3, 4]              # the first line's N
    assert refs.rests_on(root, 1)["decisions"] == [4]                 # a later line's N
    assert refs.rests_on(root, 103)["decisions"] == []                # `spec 103` is a spec's
    assert refs.rests_on(root, 3)["decisions"] == []                  # past the blank line it is no Changes paragraph


def test_this_repositorys_log_does_not_rest_103_on_a_decision_naming_spec_103():
    root = Path(__file__).resolve().parent.parent
    text = (root / "docs/decisions.md").read_text(encoding="utf-8")
    assert "Changes: 174, 180, 218; spec 34, spec 103." in text
    assert 219 in refs.rests_on(root, 218)["decisions"] and 219 in refs.rests_on(root, 174)["decisions"]
    assert 219 not in refs.rests_on(root, 103)["decisions"] and 219 not in refs.rests_on(root, 34)["decisions"]


# -- N3: every N an item joins with *and*; a `§k` that starts an item, or follows a spec, is a spec's point --------------------------------------

LOG_N3 = """# Decisions

## 1. One
Plain.

## 2. Two
Plain.

## 3. Three
Plain.

## 4. Four
Plain.

## 5. Five
Plain.

## 6. Six
Plain.

## 7. Seven
Plain.

## 8. Eight
Plain.

## 9. Joined by and
Changes: 3.2 and 1 (the first), 5.1–5.3 and
6 (an *and* across a line); 7 and spec 99 §8.2.

## 10. A spec's points after a spec item
Changes: 4; spec 99 §2.1,
§3.2.

## 11. A spec's points alone
Changes: §5.1, §8.

## 12. A decision named in passing
Changes: 4. The frame is unchanged (§6, §7).

## 13. A spec's deeper point
Plain, as spec 103 §1.2.5 and §8.1 say.
"""


def _log_n3(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/decisions.md").write_text(LOG_N3, encoding="utf-8")
    return tmp_path


def test_a_changes_item_names_every_n_it_joins_with_and(tmp_path):
    root = _log_n3(tmp_path)
    for n in (1, 3, 5, 6, 7):                                          # `3.2 and 1`, `5.1–5.3 and⏎6`, `7 and spec …`
        assert 9 in refs.rests_on(root, n)["decisions"], n
    assert 9 not in refs.rests_on(root, 8)["decisions"]                # `and spec 99 §8.2`: an *and* followed by a spec ends the item's numbers


def test_a_changes_item_starting_with_a_section_sign_is_a_specs_point(tmp_path):
    root = _log_n3(tmp_path)
    assert 10 in refs.rests_on(root, 4)["decisions"]
    assert 10 not in refs.rests_on(root, 2)["decisions"] and 10 not in refs.rests_on(root, 3)["decisions"]   # after `spec 99`, a line break in the list too
    assert 11 not in refs.rests_on(root, 5)["decisions"] and 11 not in refs.rests_on(root, 8)["decisions"]   # alone
    assert 12 in refs.rests_on(root, 6)["decisions"] and 12 in refs.rests_on(root, 7)["decisions"]           # inside an item's words: named in passing
    assert 13 not in refs.rests_on(root, 8)["decisions"]                                                     # `§1.2.5 and §8.1`: spec 103's both


def _real() -> tuple[Path, str]:
    root = Path(__file__).resolve().parent.parent
    return root, (root / "docs/decisions.md").read_text(encoding="utf-8")


def test_this_repositorys_log_rests_each_n_an_item_joins_with_and():
    root, text = _real()
    assert "176.3 and 167 (the discard lies on the table" in text and "where 106, 115 and 148 say" in text
    assert 273 in refs.rests_on(root, 167)["decisions"]                # §273: `Changes: 261.7 (…); 176.3 and 167 (…)`
    assert 268 in refs.rests_on(root, 148)["decisions"]                # §268: `… where 106, 115 and 148 say …`


_SPEC_LIST = re.compile(r"spec\s+\d+(?:\s+part\s+\w+)?\s*§\d+(?:\.\d+)*(?:\s*(?:,|;|and|–|-|/)\s*§\d+(?:\.\d+)*)*", re.I)


def _points(text: str) -> set[int]:
    return {int(x) for s in _SPEC_LIST.findall(text) for x in re.findall(r"§(\d+)", s)}


def _items(para: str) -> set[int]:
    """The numbers a *Changes:* paragraph writes bare (no `§` before, not a spec's own number): the ones it may name as decisions."""
    return {int(x) for x in re.findall(r"(?<![§.\d])\b(\d+)", para)} - {int(x) for x in re.findall(r"spec\s+(\d+)", para, re.I)}


def test_this_repositorys_log_rests_nothing_on_a_specs_point(tmp_path):
    """Every `spec N §k, §m` of the real log, and every real *Changes:* paragraph holding one, laid in a log where each §k is a decision of its own:
    none of them rests on a §k it writes only as a spec's (`spec 99 §6.1, §7.2`, `spec 95 §1.1, §2.3,⏎§3`, `spec 103 §1.2.5 and §2.1`)."""
    root, text = _real()
    lists = [m.group() for m in _SPEC_LIST.finditer(text)]
    changes = {k: m.group().strip() for k, sec in refs._log(root).items() if (m := refs._CHANGES.search(sec)) and _SPEC_LIST.search(m.group())}
    assert {233, 235, 254} <= set(changes) and "spec 103 §1.2.5 and §2.1" in lists and len(lists) > 100
    points = sorted(_points(text) - set(changes))
    log = "# Decisions\n" + "".join(f"\n## {k}. Real\n{para}\n" for k, para in sorted(changes.items()))
    log += "".join(f"\n## {10000 + i}. A list\nAs {s}.\n" for i, s in enumerate(lists))
    log += "".join(f"\n## {p}. A spec's point\nPlain.\n" for p in points)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/decisions.md").write_text(log, encoding="utf-8")
    wrong = {}
    for p in points:
        got = refs.rests_on(tmp_path, p)["decisions"]
        wrong[p] = [d for d in got if d >= 10000 or (d in changes and p in _points(changes[d]) - _items(changes[d]))]
    assert wrong == {p: [] for p in points}
    assert 233 not in refs.rests_on(tmp_path, 7)["decisions"] and 254 not in refs.rests_on(tmp_path, 3)["decisions"]    # the two the leader named
