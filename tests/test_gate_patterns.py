"""Spec 143 B (decisions §250.3): a page's change is tested by its browser tests: `[gate] browser` patterns (realm/gate_config.py), a browser module
skipped for want of a Chromium said on the result and never counted as passed (`tests.no_browser`)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from orkboard.core.idea_task import TaskMixin
from orkboard.realm import gate_config, idea_git

from tests.test_idea_route import host  # noqa: F401
from tests.test_releases import board  # noqa: F401  (a board with goals)

ROOT = Path(__file__).resolve().parent.parent
BROWSER = ("tests/test_{stem}*_browser.py", "tests/test_{leaf}*_browser.py")


def toml(root: Path, text: str) -> None:
    (root / "orkcraft.toml").write_text(text, encoding="utf-8")


def tree(root: Path, *names: str) -> None:
    for n in names:
        (root / n).parent.mkdir(parents=True, exist_ok=True)
        (root / n).write_text("")


def test_a_touched_page_file_brings_the_browser_tests_of_its_name_and_its_folder_sorted_and_only_those_that_exist(tmp_path):
    tree(tmp_path, "tests/test_table_desktop_browser.py", "tests/test_table_cards_browser.py", "tests/test_column_browser.py",
         "tests/test_architecture.py", "tests/test_other_browser.py")
    gate = gate_config.Gate(always=("tests/test_architecture.py",), browser=BROWSER)
    assert gate_config.gate_files(gate, ["orkboard/gui/static/js/table/pane.js"], tmp_path) == \
        ["tests/test_architecture.py", "tests/test_table_cards_browser.py", "tests/test_table_desktop_browser.py"]
    assert gate_config.gate_files(gate, ["js/table/column.js"], tmp_path) == \
        ["tests/test_architecture.py", "tests/test_column_browser.py", "tests/test_table_cards_browser.py", "tests/test_table_desktop_browser.py"]
    assert gate_config.gate_files(gate, ["js/table/pane.css", "js/x/page.html"], tmp_path)[1:] == \
        ["tests/test_table_cards_browser.py", "tests/test_table_desktop_browser.py"]


def test_with_no_patterns_a_glob_that_finds_nothing_or_a_py_file_browser_adds_nothing(tmp_path):
    tree(tmp_path, "tests/test_table_desktop_browser.py", "tests/test_architecture.py")
    only = ["tests/test_architecture.py"]
    assert gate_config.gate_files(gate_config.Gate(always=tuple(only)), ["js/table/pane.js"], tmp_path) == only
    assert gate_config.gate_files(gate_config.Gate(always=tuple(only), browser=("tests/test_{stem}_nothing.py",)), ["js/table/pane.js"], tmp_path) == only
    assert gate_config.gate_files(gate_config.Gate(always=tuple(only), browser=BROWSER), ["orkboard/table/pane.py"], tmp_path) == only
    assert gate_config.gate_files(gate_config.Gate(always=tuple(only), browser=BROWSER), ["pane.js"], tmp_path) == only     # no folder: no `{leaf}`


def test_the_browser_patterns_are_read_from_the_toml_a_bad_one_is_said_and_this_repository_names_its_own(tmp_path):
    toml(tmp_path, '[gate]\nbrowser = ["tests/test_{stem}*_browser.py"]\n')
    assert gate_config.read(tmp_path).browser == ("tests/test_{stem}*_browser.py",)
    toml(tmp_path, "[gate]\nbrowser = 3\n")
    assert "browser must be a list of strings" in gate_config.read(tmp_path).error
    assert gate_config.read(ROOT).browser == BROWSER
    assert "tests/test_table_desktop_browser.py" in gate_config.gate_files(gate_config.read(ROOT), ["orkboard/gui/static/js/table/pane.js"], ROOT)


def run_tests_of(tmp_path: Path, out: str, browser: tuple[str, ...]) -> dict:
    stub = SimpleNamespace(repo_root=tmp_path, _gate_runs={str(tmp_path): idea_git.GateRun(True, out, True, "pytest", 0, 1.0, browser=browser)})
    return TaskMixin._tests_of(stub, tmp_path, out, None)


def test_a_green_run_that_skipped_browser_files_says_no_browser_and_one_that_ran_or_had_none_does_not(tmp_path):
    toml(tmp_path, '[gate]\nbrowser = ["tests/x_browser.py"]\n')
    skipped = "$ pytest\n2 passed, 3 skipped in 0.4s\n"
    got = run_tests_of(tmp_path, skipped, ("tests/test_table_browser.py",))
    assert got["skipped"] == 3 and got["passed"] == 2 and got["green"] is True and got["no_browser"] is True
    ran = run_tests_of(tmp_path, "5 passed in 40s\n", ("tests/test_table_browser.py",))
    assert ran["skipped"] == 0 and "no_browser" not in ran
    assert "no_browser" not in run_tests_of(tmp_path, skipped, ())                    # no file of `browser` was in the run


def test_the_plans_rules_keep_a_code_task_with_the_tests_its_change_breaks(board):
    prompt = " ".join(board.ideas.keeper.plan_prompt(board.root, board.a2).split())
    assert "A code task changes the tests its change breaks, in the same task" in prompt
    assert "A later task may add coverage, never repair a task before it." in prompt
