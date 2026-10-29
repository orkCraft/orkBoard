"""Spec 99 D (docs/specs/99-a-goals-way.md §5) on the host: `ideas.talk_answer` and `ideas.cause_answer` answer the rows `talk` and `cause`; their arguments are
checked, a phone may send them, and a Talk goes from the press of **Talk** to the decision's seam. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, goal_team, idea_questions, ideas, library

TALK_COMMANDS = {"ideas.talk_answer", "ideas.cause_answer", "ideas.objection"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def model(host):
    """Every leader says where it stands and asks one question; Tech's diagnosis names a cause and asks one case."""
    seen: list[dict] = []

    def call(tier, prompt, effort="", budget=None):
        step = host.ideas.keeper.measure()["step"]
        seen.append({"step": step, "prompt": prompt})
        if step == "talk_round":
            out = {"stance": "For it", "for": "Players want it", "against": "It costs", "questions": [
                {"ask": "Which first?", "choices": ["Web", "Phone"], "pick": 1, "why": "most players are on phones", "blocks": True}]}
        elif step == "diagnose":
            out = {"questions": [{"ask": "Where does it happen?", "choices": ["Lobby", "Game"], "pick": 0, "why": "the report says lobby"}],
                   "cause": "the lobby's timer is not reset on reconnect", "where": ["src/app.py"]}
        else:
            out = {"title": "A goal", "questions": []}
        return json.dumps(out), 0.01, 10, ""

    host.ideas.keeper.call = call
    return seen


@pytest.fixture
def tech(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, ["architect", "grunt", "tester"])
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    goal_team.set_team(root, slug, ["grunt", "tester"], leader="architect")
    return slug


def _wait(host, slug):
    for _ in range(1000):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def test_the_commands_are_the_hosts_and_a_phones(host):
    assert TALK_COMMANDS <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in TALK_COMMANDS)


def test_the_arguments_are_checked_in_plain_words(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.talk_answer", {})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.talk_answer", {"idea": "nobody", "answers": []})
    with pytest.raises(CommandError, match="answers are a list"):
        host.command("ideas.talk_answer", {"idea": slug, "answers": "Web"})
    with pytest.raises(CommandError, match="answers are a list"):
        host.command("ideas.talk_answer", {"idea": slug, "answers": [{"pick": 0}]})                    # an answer names its card
    with pytest.raises(CommandError, match="asks nothing now"):
        host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})                # a goal not at Talk
    with pytest.raises(CommandError, match="yes is true or false"):
        host.command("ideas.cause_answer", {"idea": slug, "yes": "yes"})
    with pytest.raises(CommandError, match="text is not text"):
        host.command("ideas.cause_answer", {"idea": slug, "yes": False, "text": 3})
    with pytest.raises(CommandError, match="asks nothing now"):
        host.command("ideas.cause_answer", {"idea": slug, "yes": True})
    with pytest.raises(CommandError, match="party is missing"):
        host.command("ideas.objection", {"idea": slug, "answer": "go"})                                  # a leader's no (spec 108 §4.3)
    with pytest.raises(CommandError, match="answer is missing"):
        host.command("ideas.objection", {"idea": slug, "party": tech})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.objection", {"idea": "nobody", "party": tech, "answer": "go"})
    with pytest.raises(CommandError, match="no objection to answer"):
        host.command("ideas.objection", {"idea": slug, "party": tech, "answer": "go"})
    assert model == [] and _state(host, slug)["state"] == "routed"


def test_a_talk_from_the_press_to_the_decisions_seam_and_the_answers_are_events(host, tech, model, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    assert _row(host, slug, "route") is not None and _row(host, slug, "talk") is None
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    row = _row(host, slug, "talk")
    assert _row(host, slug, "route") is None and row["round"] == 1 and [q["q"] for q in row["questions"]] == ["Which first?"]
    assert row["questions"][0]["pick"] == 1 and row["questions"][0]["choices"] == ["Web", "Phone"] and row["questions"][0]["leader"] == "architect"
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append((s, _state(host, s)["state"])), raising=False)      # part E's seam
    assert host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": row["questions"][0]["id"], "text": "Both, phone first"}]}) == {"ok": True}
    assert went == [(slug, "talk")] and _row(host, slug, "talk") is None
    said = [e for e in event_log.read(Path(host.town.repo_root)) if e["event"] == event_log.IDEA_ANSWERED]
    assert said and said[-1]["idea"] == slug and said[-1]["talk"] is True and said[-1]["typed"] == 1 and said[-1]["round"] == 1
    assert idea_questions.record(host.ideas.state_dir, slug)["answers"][0]["answer"] == "Both, phone first"
    with pytest.raises(CommandError, match="asks nothing now"):
        host.command("ideas.talk_answer", {"idea": slug, "answers": []})                                  # answered once


def test_let_the_leaders_decide_answers_with_the_picks(host, tech, model, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: None, raising=False)
    host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    assert [(a["answer"], a["how"]) for a in idea_questions.record(host.ideas.state_dir, slug)["answers"]] == [("Phone", "decide")]


def test_a_bug_from_the_press_to_the_cause_and_the_sections(host, tech, model, monkeypatch):
    slug = host.command("ideas.add", {"text": "Saving crashes when the file is empty, see src/app.py"})["slug"]
    assert _state(host, slug)["route_how"]["short"] is True
    host.command("ideas.route_start", {"idea": slug})                                                    # no failure's lines: its Talk is the diagnosis
    _wait(host, slug)
    row = _row(host, slug, "cause")
    assert [m["step"] for m in model] == ["diagnose"] and _row(host, slug, "talk") is None
    assert row["cause"] == "the lobby's timer is not reset on reconnect" and row["where"] == ["src/app.py"] and [q["q"] for q in row["q"]] == ["Where does it happen?"]
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append((s, _state(host, s)["state"])), raising=False)       # part E's seam
    assert host.command("ideas.cause_answer", {"idea": slug, "yes": True, "answers": [{"id": row["q"][0]["id"], "pick": 0}]}) == {"ok": True}
    assert went == [(slug, "sections")] and _row(host, slug, "cause") is None


def test_talk_waits_for_nothing_it_cannot_make_the_demo_runs_no_model(host, tech, model):
    host.ideas.keeper.demo = True
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    st = _state(host, slug)
    assert st["state"] == "routed" and "demo runs no model" in st["error"] and model == []                 # the route card is its row again, with why
