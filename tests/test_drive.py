"""`orkboard drive` (gui/drive.py, decisions §227): the page's own commands from a terminal, a served project's address kept for
its owner alone, the AI tools hidden unless asked for, and a scenario run against a real host and server."""
from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path

import pytest

from orkboard.gui import board_cli, drive
from orkboard.gui.drive import DriveError

SCENARIO = Path(__file__).parent / "scenarios" / "a-goal-routed.json"


def test_a_path_walks_keys_places_and_the_first_item_with_a_value():
    board = {"ideas": [{"slug": "a", "state": "routed"}, {"slug": "b", "state": "talk"}], "n": 2}
    assert drive.at(board, "ideas[slug=b].state") == "talk"
    assert drive.at(board, "ideas.0.slug") == "a"
    assert drive.at(board, "") is board
    for bad, words in (("ideas[slug=z]", "no item with slug=z"), ("nope", "no key nope"), ("ideas.9", "no place 9"),
                       ("n.x", "x under a int"), ("n[a=b]", "needs a list")):
        with pytest.raises(DriveError, match=words.replace("[", r"\[")):
            drive.at(board, bad)


def test_what_is_expected_is_every_given_check():
    assert drive.meets("routed", {"is": "routed"}) and not drive.meets("talk", {"is": "routed"})
    assert drive.meets(["tech", "art"], {"has": "art"}) and drive.meets({"a": "the tech one"}, {"has": "tech"})
    assert drive.meets(3, {"is": 3, "not": 4}) and not drive.meets(3, {"not": 3})
    assert drive.meets(None, {})


def test_kept_values_fill_the_later_steps():
    assert drive.fill({"args": {"goal": "${g}"}, "path": "ideas[slug=${g}]", "n": 1}, {"g": "jump"}) == \
        {"args": {"goal": "jump"}, "path": "ideas[slug=jump]", "n": 1}


def test_the_socket_is_the_pages_with_its_token_and_its_origin():
    assert drive.socket_of("http://127.0.0.1:5001/?t=abc&app=1") == ("ws://127.0.0.1:5001/ws?t=abc", "http://127.0.0.1:5001")
    with pytest.raises(DriveError, match="no token"):
        drive.socket_of("http://127.0.0.1:5001/")


def test_the_served_address_is_its_owners_alone_and_goes_when_it_stops(tmp_path):
    path = drive.write_session(tmp_path, {"url": "http://127.0.0.1:1/?t=x", "pid": 1})
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert drive.read_session(tmp_path)["url"].endswith("t=x")
    drive.remove_session(tmp_path)
    with pytest.raises(DriveError, match="drive start"):
        drive.read_session(tmp_path)


def test_the_ai_tools_are_hidden_unless_asked_for(tmp_path):
    folder = tmp_path / "bin"
    folder.mkdir()
    for name in ("claude", "codex", "gh", "git-helper"):
        (folder / name).write_text("#!/bin/sh\n")
    other = tmp_path / "other"
    other.mkdir()
    quiet = drive.quiet_path(os.pathsep.join([str(folder), str(other)])).split(os.pathsep)
    assert quiet[1] == str(other)                      # a folder with no tool is kept as it is
    names = {p.name for p in Path(quiet[0]).iterdir()}
    assert names == {"git-helper"}


def test_drive_is_a_word_of_the_command_line(monkeypatch, capsys):
    assert "drive" in board_cli.WORDS
    assert board_cli.run(["drive", "call", "ideas.board", "--url", "http://127.0.0.1:9/?t=x", "--timeout", "1"]) == 1
    assert "does not answer" in capsys.readouterr().err


@pytest.fixture
def served(fake_repo):
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    server = Server(Orkboard(fake_repo))
    thread = server.start_thread()
    yield server
    server.stop()
    thread.join(10)


def test_a_scenario_runs_against_a_served_project_by_the_pages_own_commands(served):
    steps = [s for s in json.loads(SCENARIO.read_text(encoding="utf-8"))["steps"] if "shot" not in s]
    link = drive.Link(served.url)
    try:
        out = io.StringIO()
        summary = drive.run_steps(link, steps, out=out)
        assert summary["ok"], out.getvalue()
        rows = [json.loads(line) for line in out.getvalue().splitlines()]
        assert [r["kind"] for r in rows] == ["call", "call", "wait", "call"] and all(r["ok"] for r in rows)
        assert link.state is not None and "needs_you" in link.state
        with pytest.raises(DriveError, match="ideas.add: "):
            link.call("ideas.add", {"text": ""})          # refused in the host's own words, as the page is
    finally:
        link.close()


def test_a_step_not_as_expected_ends_the_run_and_says_what_it_found(served):
    link = drive.Link(served.url)
    try:
        out = io.StringIO()
        summary = drive.run_steps(link, [{"call": "ideas.board", "expect": {"path": "tracks.0.slug", "is": "nope"}},
                                         {"call": "ideas.board"}], out=out)
        assert summary["ok"] is False and summary["failed"] == 1 and summary["steps"] == 0
        assert "found" in json.loads(out.getvalue().splitlines()[0])["error"]
    finally:
        link.close()


def test_the_command_line_calls_a_served_project_and_prints_the_answer(served, capsys):
    assert drive.main(["call", "ideas.board", "--path", "tracks.0.slug", "--url", served.url]) == 0
    assert json.loads(capsys.readouterr().out) == "general"
    assert drive.main(["call", "ideas.nothing", "--url", served.url]) == 1
    assert "ideas.nothing" in capsys.readouterr().err


def test_stop_takes_folder_as_the_other_acts_do_and_keeps_its_positional(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    stopped = []
    monkeypatch.setattr(drive, "stop", lambda root: stopped.append(root) or 0)
    assert drive.main(["stop", "--folder", str(tmp_path)]) == 0
    assert drive.main(["stop", str(tmp_path)]) == 0
    assert [Path(r).resolve() for r in stopped] == [tmp_path.resolve()] * 2


def test_wait_on_state_reads_the_snapshot_and_review_count_is_there_while_needs_you_holds_no_review(served):
    """Spec 149 I.4: the trial's driver waited on `needs_you` and sat 21 minutes on a card in the hand."""
    link = drive.Link(served.url)
    try:
        assert drive.wait_for(link, "state", None, "review_count", {"is": 0}, 10) == 0
        assert "review_count" in link.state and "needs_you" in link.state
        with pytest.raises(DriveError, match="not as expected"):
            drive.wait_for(link, "state", None, "review_count", {"not": 0}, 0.2, every=0.1)
    finally:
        link.close()
    assert "review_count" in drive.__doc__ and "no task at Review" in drive.__doc__


def test_a_picture_asks_the_projects_python_where_neither_pythons_playwright_nor_nodes_is_here(tmp_path, monkeypatch):
    """Spec 149 I.5: `uv sync --extra browser` installs Python's Playwright; Node's is not there."""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)
    asked = []
    monkeypatch.setattr(drive, "_shoot_with_python", lambda url, path, w, h, chromium: asked.append((url, w, h)) or True)
    assert drive._shoot_with_node("http://x/", tmp_path / "a.png", 390, 844, None) == tmp_path / "a.png" and asked == [("http://x/", 390, 844)]
    monkeypatch.setattr(drive, "_shoot_with_python", lambda *a: False)
    with pytest.raises(DriveError, match="uv sync --extra browser"):
        drive._shoot_with_node("http://x/", tmp_path / "b.png", 390, 844, None)
