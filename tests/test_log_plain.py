"""A log is read in the page, which draws no terminal (docs/specs/107-what-the-owners-day-said.md §3): the task's log and the gate's tail come without the escape codes."""
from __future__ import annotations

from types import SimpleNamespace

from orkboard.core.idea_review import ReviewMixin
from orkboard.realm.idea_git import parse_tests, plain

RED = "\x1b[31mFAILED\x1b[0m tests/test_clock.py::test_reset\n\x1b[1m\x1b[31m1 failed\x1b[0m, \x1b[32m3 passed\x1b[0m in 0.1s\n"


def test_plain_takes_a_terminals_codes_out_and_leaves_the_words():
    assert plain("\x1b[32mok\x1b[0m \x1b]0;a title\x07done \x1b[2K\x1b[1;33mwarn\x1b[m") == "ok done warn"
    assert plain("a < b && c > d\ttabbed\n") == "a < b && c > d\ttabbed\n" and plain(None) == ""


def test_the_gates_tail_and_its_counts_are_read_without_the_codes():
    got = parse_tests(RED)
    assert got["failed"] == 1 and got["passed"] == 3 and got["failing"] == ["tests/test_clock.py::test_reset"]      # the codes did not hide the names or the summary
    assert "\x1b" not in got["tail"]


def test_a_tasks_log_comes_without_the_codes(tmp_path):
    path = tmp_path / "k1.log"
    path.write_text("== the gate, try 1\n" + RED, encoding="utf-8")
    log = ReviewMixin.log(SimpleNamespace(_log_path=lambda slug, tid: path), "demo", "k1")
    assert log.startswith("== the gate, try 1\nFAILED tests/test_clock.py::test_reset\n") and "\x1b" not in log
