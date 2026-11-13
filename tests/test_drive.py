"""`orkboard drive` (gui/drive.py, decisions §227): the page's own commands from a terminal, a served project's address kept for
its owner alone, the AI tools hidden unless asked for, and a scenario run against a real host and server."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from orkboard.gui import drive
from orkboard.gui.drive import DriveError

SCENARIO = Path(__file__).parent / "scenarios" / "a-goal-routed.json"


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

