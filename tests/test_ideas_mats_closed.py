"""Goal 171 L2: the hand's one-press table is closed. Every command of `ONE_PRESS_BY` is played through its command (`from: "hand"`) with every model entry made to fail: none reaches a model,
and its Undo puts the Board back. Goal "The battle and the gate" G: a red gate's Fix it after dev (`ideas.gate_fix_goal`) is one of them; H: its stage again (`fix_stage`) is sealed."""
from __future__ import annotations

import sys

import pytest

from orkboard.core import idea_undo
from orkboard.gui import ideas_mats
from orkboard.gui.board_host import Orkboard
from orkboard.realm import harnesses, ideas

PAGE = ("---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nasks: person\nschema: 3\n---\n# Goal\n\n## Gist\nA goal.\n\n"
        "## Open questions\n- Which store first? (**App Store** / Google Play) — most users\n")
PLAYED = {"ideas.drop": {"slug": "goal"}, "ideas.queue": {"slug": "goal", "queue": "hold"}, "ideas.answer_way": {"slug": "goal", "answers": ["Google Play"]},
          "ideas.gate_fix_goal": {"idea": "goal"}}
ENTRIES = ("ask", "call", "work_call", "_claude", "_claude_work", "board_ask", "read_now", "draft", "answer", "read_goal", "talk_answer")


def _red_main(host):
    """`ideas.gate_fix_goal`'s Board: the goal done in dev, its way to main red on a failing test."""
    ideas.save_state(host.ideas.state_dir, "goal", state="done")
    host.ideas._main_checks["goal"] = {"running": False, "checks": [{"name": "Tests", "state": "failed", "words": "1 failed", "files": ["tests/test_a.py"],
                                                                     "failures": [{"id": "tests/test_a.py::test_b", "classification": "new"}]}]}


LAID = {"ideas.gate_fix_goal": _red_main}           # what a command needs on the Board before it is played


def _board(host) -> dict:
    """Every goal's page and state, byte for byte."""
    root, state = host.ideas.root(), host.ideas.state_dir
    files = [p for p in (root / ideas.IDEAS).glob("*.md") if p.name != "index.md"] + list((state / "ideas").glob("*/state.json"))
    return {p.as_posix(): p.read_bytes() for p in sorted(files)}


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    root = h.ideas.root()
    ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    (root / ideas.IDEAS / "goal.md").write_text(PAGE, encoding="utf-8")
    ideas.save_state(h.ideas.state_dir, "goal", state="raw")
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.mark.parametrize("name", sorted(ideas_mats.ONE_PRESS_BY))
def test_a_one_press_command_runs_no_model(host, monkeypatch, name):
    reached: list[str] = []

    def fail(entry):
        def boom(*a, **k):
            reached.append(entry)
            raise AssertionError(f"a model was reached through {entry}")
        return boom
    for entry in ENTRIES:
        if hasattr(host.ideas.keeper, entry):
            monkeypatch.setattr(host.ideas.keeper, entry, fail(f"keeper.{entry}"))
    monkeypatch.setattr(harnesses.Harness, "ask", fail("Harness.ask"))
    LAID.get(name, lambda h: None)(host)
    before, board = idea_undo.snapshot(host.ideas.root(), host.ideas.state_dir, "goal"), _board(host)
    host.command(name, {**PLAYED[name], "from": "hand"})
    assert reached == [] and not host.ideas.keeper.busy("goal")
    kept = idea_undo.read(host.ideas.state_dir, "goal")
    assert kept["before"] == (before if "laid" not in kept else {"page": None, "state": None})          # its Undo is kept: the goal's own bytes, or none of the goal it laid
    host.command("ideas.undo", {"idea": "goal"})
    assert _board(host) == board and reached == []                                                     # its reverse puts every page and state back


def test_new_wins_is_one_press_runs_no_model_and_its_reverse_puts_the_decision_back(host, monkeypatch):
    """Goal "The battle and the gate" I: `ideas.conflict` `replace` from the hand is a one-press kind (`new_wins`); `keep` and `other` are sealed."""
    from orkboard.realm import spec_sections

    def boom(*a, **k):
        raise AssertionError("a model was reached")
    for entry in ENTRIES:
        if hasattr(host.ideas.keeper, entry):
            monkeypatch.setattr(host.ideas.keeper, entry, boom)
    monkeypatch.setattr(harnesses.Harness, "ask", boom)
    sd = host.ideas.state_dir
    ideas.save_state(sd, "goal", state="decided")
    spec_sections.save_record(sd, "goal", {"decision": {"title": "T", "confirmed": False, "changes": [], "conflicts": [{"number": 2, "point": "p", "answer": ""}]}})
    before = spec_sections.record(sd, "goal")
    args = {"idea": "goal", "number": 2, "choice": "replace", "from": "hand"}
    assert idea_undo.way(ideas_mats.move_kind("ideas.conflict", args)) == "press"
    assert [idea_undo.way(ideas_mats.move_kind("ideas.conflict", {**args, "choice": c})) for c in ("keep", "other")] == ["sealed", "sealed"]
    assert ideas_mats.move_kind("ideas.conflict", {**args, "from": ""}) == ""
    host.command("ideas.conflict", args)
    assert spec_sections.record(sd, "goal") != before
    host.command("ideas.undo", {"idea": "goal"})
    assert spec_sections.record(sd, "goal")["decision"] == before["decision"]
