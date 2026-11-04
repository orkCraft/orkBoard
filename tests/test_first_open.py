"""The first open, in the Orkmaster's order (docs/specs/130-the-first-open-is-the-orkmasters.md part A.4–A.5; decisions §232.1, §232.3, §232.8): the question asked
now, the project's kind answered from a card, a new empty folder, and the table laid at Start only."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import first_open, ideas, tool_hand


@pytest.fixture
def empty(tmp_path) -> Orkboard:
    b = Orkboard()
    yield b
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def board(fake_repo) -> Orkboard:
    b = Orkboard(fake_repo)
    yield b
    sys.modules.pop("orkboard.core.idea_runner", None)


# -- the order (A.4) -------------------------------------------------------------------------------------------------

def test_the_questions_come_in_the_orkmasters_order():
    at = lambda **k: first_open.step(**{"open": True, "git": True, "kind_kept": True, "hand": 1, "tools_skipped": False, "laid": False, **k})    # noqa: E731
    assert at(open=False) == "project" and at(open=False, laid=True) == "project"
    assert at(git=False) == "git"
    assert at(kind_kept=False) == "kind"
    assert at(hand=0) == "tools"                                                         # only when the hand is empty: the tools are this computer's
    assert at(hand=0, tools_skipped=True) == "parties"                                   # the card closed with none added: the Board goes on
    assert at() == "parties"
    assert at(laid=True, git=False, kind_kept=False, hand=0) == "laid"                   # laid: nothing is asked, however the rest stands
    assert [first_open.line(s, "skyhop", "a web app") for s in ("project", "git", "kind", "tools")] == [
        "Which project shall we work on?", "No git in skyhop yet. Start git here?", "skyhop is a web app. Right?", "Which AI tool shall the orks think with?"]
    assert first_open.line("kind", "skyhop") == "What is skyhop for?" and first_open.line("laid") == ""


def test_with_no_project_open_the_orkmaster_asks_which(empty):
    got = empty.command("first_open.ask", {})
    assert got["step"] == "project" and got["line"] == "Which project shall we work on?" and got["recent"] == [] and not got["laid"]
    empty.machine.projects_recent = [str(Path.cwd())]
    assert empty.command("first_open.ask", {})["recent"] == [{"path": str(Path.cwd()), "name": Path.cwd().name}]
    assert empty.snapshot()["laid"] is False                                              # no project: nothing is laid


def test_a_folder_without_git_is_asked_to_start_git_then_what_it_is(empty, tmp_path):
    folder = tmp_path / "skyhop"
    folder.mkdir()
    (folder / "package.json").write_text('{"name": "skyhop", "dependencies": {"react": "1"}}', encoding="utf-8")
    assert empty.command("projects.open", {"path": str(folder)})["git"] is False
    got = empty.command("first_open.ask", {})
    assert got["step"] == "git" and got["line"] == "No git in skyhop yet. Start git here?" and got["name"] == "skyhop"
    empty.command("projects.start_git", {"path": str(folder)})
    got = empty.command("first_open.ask", {})
    assert got["step"] == "kind" and got["kind"]["id"] and got["line"] == f"skyhop is {got['kind']['words']}" + (f", {got['kind']['how']}" if got["kind"]["how"] else "") + ". Right?"
    assert not got["kind"]["empty"]


def test_the_kind_is_answered_yes_or_another_and_then_the_tools_are_asked(board):
    got = board.command("first_open.ask", {})
    assert got["step"] == "kind"
    with pytest.raises(CommandError, match="A kind is one of"):
        board.command("first_open.kind", {"kind": "banana"})
    assert board.command("first_open.ask", {})["step"] == "kind"                          # a refused answer changes nothing
    kept = board.command("first_open.kind", {"kind": got["kind"]["id"]})
    assert kept["ok"] and kept["kind"] == got["kind"]["id"]
    assert board.command("first_open.ask", {})["step"] == "tools" and board.command("first_open.ask", {})["hand"] == 0      # a machine with no tool in its hand
    said = board.command("first_open.tools_skip", {})
    assert said["line"] == "No AI tool: the Board opens, and nothing is worked on until you add one"
    assert board.command("first_open.ask", {})["step"] == "parties"
    tool_hand.add(board.machine, "claude", "subscription")
    assert board.command("first_open.ask", {})["hand"] == 1


def test_an_empty_folder_asks_what_it_is_for_in_one_line(empty, tmp_path):
    import subprocess
    folder = tmp_path / "blank"
    folder.mkdir()
    subprocess.run(["git", "init"], cwd=str(folder), check=True, capture_output=True)
    empty.command("projects.open", {"path": str(folder)})
    got = empty.command("first_open.ask", {})
    assert got["step"] == "kind" and got["kind"]["empty"] and got["line"] == "What is blank for?"
    with pytest.raises(CommandError, match="in a line"):
        empty.command("first_open.kind", {"about": "  "})
    done = empty.command("first_open.kind", {"about": "a small game"})                      # no model here: code's guess, said so (`read: false`)
    assert done["ok"] and done["kind"] == "code" and done["read"] is False
    assert empty.command("first_open.ask", {})["step"] == "tools"


# -- a new, empty folder (A.4) ----------------------------------------------------------------------------------------

def test_a_new_empty_folder_is_made_and_opened(empty, tmp_path):
    got = empty.command("projects.new_folder", {"parent": str(tmp_path), "name": "  my   game "})
    assert got["ok"] and got["git"] is False and Path(got["path"]).name == "my game"
    assert (tmp_path / "my game").is_dir() and empty.command("projects.list", {})["current"] == got["path"]
    assert empty.command("first_open.ask", {})["step"] == "git"
    for args, why in (({"parent": str(tmp_path), "name": "my game"}, "there already"), ({"parent": str(tmp_path), "name": "a/b"}, "plain name"),
                      ({"parent": str(tmp_path), "name": ".hidden"}, "plain name"), ({"parent": str(tmp_path), "name": ""}, "plain name"),
                      ({"parent": str(tmp_path / "none"), "name": "x"}, "not there")):
        with pytest.raises(CommandError, match=why):
            empty.command("projects.new_folder", args)


def test_a_new_folder_that_may_not_be_a_project_is_not_left_behind(empty, tmp_path):
    keys = tmp_path / "home" / ".ssh"                                                      # the test's home (conftest): its keys' folder is never a project's
    keys.mkdir(parents=True)
    with pytest.raises(CommandError, match="settings or keys"):
        empty.command("projects.new_folder", {"parent": str(keys), "name": "keys"})
    assert not (keys / "keys").exists()


# -- the table is laid at Start (A.5) ---------------------------------------------------------------------------------

def test_the_table_is_not_laid_until_start(board, fake_repo):
    state_dir = fake_repo / ".orkcraft"
    assert board.snapshot()["laid"] is False and first_open.laid(state_dir, fake_repo) is False
    assert board.command("first_open.ask", {})["laid"] is False
    ideas.add_track(fake_repo, ideas.GENERAL_TITLE)                                       # General is written when a goal is first added: no party of the person's
    assert first_open.laid(state_dir, fake_repo) is False
    assert first_open.lay(state_dir) is True and first_open.lay(state_dir) is False        # once
    assert first_open.laid(state_dir, fake_repo) and (state_dir / "project.json").is_file()


def test_start_lays_the_table_once_and_the_snapshot_says_so(board, fake_repo, monkeypatch):
    monkeypatch.setattr("orkboard.gui.ideas_project_q.read_in.first_start", lambda *a, **k: None)
    state_dir = fake_repo / ".orkcraft"
    assert board.snapshot()["laid"] is False
    got = board.command("ideas.project_ask", {})                                           # what Start sends after the parties are made
    assert got["ok"] is True
    assert board.snapshot()["laid"] is True and first_open.kept(state_dir)
    assert board.command("first_open.ask", {})["step"] == "laid" and board.command("first_open.ask", {})["laid"]
    board.command("ideas.project_ask", {})                                                 # again: nothing changes
    assert first_open.kept(state_dir)


def test_the_other_keys_of_the_projects_file_are_left_as_they_are(fake_repo):
    from orkboard.realm import project_kind, project_stage
    state_dir = fake_repo / ".orkcraft"
    project_kind.keep(state_dir, "code")
    project_stage.keep(state_dir, "live")
    first_open.lay(state_dir)
    assert project_kind.kept(state_dir) == "code" and project_stage.kept(state_dir) == "live" and first_open.kept(state_dir)
    project_stage.keep(state_dir, "idea")                                                  # the others write it whole too: `laid` survives them
    assert first_open.kept(state_dir)


def test_a_project_with_parties_of_its_own_is_laid_at_once(fake_repo):
    ideas.add_track(fake_repo, "Tech")
    state_dir = fake_repo / ".orkcraft"
    assert first_open.laid(state_dir, fake_repo) and not first_open.kept(state_dir)
    b = Orkboard(fake_repo)
    try:
        assert b.snapshot()["laid"] is True and b.command("first_open.ask", {})["step"] == "laid"
    finally:
        sys.modules.pop("orkboard.core.idea_runner", None)
