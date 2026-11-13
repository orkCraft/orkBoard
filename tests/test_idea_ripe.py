"""Spec 120 C (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §3.3–§3.6) on the weigher and the wait: the goal's weight (Product's priority, Tech's risk raised by `idea_risk`'s rules), what the
verdicts make (a hearing, agreed, the decision's card), the seconds of the wait, the wait kept beside the decision, counting down only while a face is open, **Hold**, the end writing the
leaders' heading and starting the sections, a spent window or a paid tool holding instead. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui import ideas_route
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, goal_team, idea_questions, idea_ripe, ideas, library, spec_sections

TECH_SAID = {"stance": "For it", "for": "A dark mode helps at night", "against": "a", "questions": [], "risk": "low"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")        # this project keeps its decisions as one file (a project with no log gets a MADR folder: spec 127 B.4)
    h.command("ideas.board_set", {"autostart": False})          # a plan made is not started: no runner here
    h.faces = lambda: 0                                          # no face is open until a test opens one
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def product(host):
    return _party(host, "Product", "product-manager", ["copywriter"], "product")


class Said(dict):
    """`said[step]` the JSON the keeper's call answers; `calls` every call made."""
    calls: list


@pytest.fixture
def model(host):
    said = Said({"talk_round": dict(TECH_SAID), "decide": {"title": "Dark mode ships", "why": "People read at night.", "points": ["Tech adds it.", "Off by default."]},
                 "section_first": {"why": "Because.", "done_when": ["It works"], "will_be": ["changed src"], "risk": "low"},
                 "plan": {"tasks": [{"id": "k1", "title": "Do it", "brief": "Do the thing.", "kind": "code", "tier": "warrior", "after": []}], "todos": []}})
    said.calls = []

    def call(tier, prompt, effort="", budget=None):
        k = host.ideas.keeper
        step, party = k.measure()["step"], getattr(k._tls, "party", "")
        said.calls.append({"step": step, "party": party, "prompt": prompt})
        answer = said.get((step, party)) or said.get(step) or {}
        return json.dumps(answer), 0.01, 10, ""

    host.ideas.keeper.call = call
    return said


def _until(host, slug, state):
    for _ in range(1500):
        if ideas.state(host.ideas.state_dir, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"never {state}: {ideas.state(host.ideas.state_dir, slug)}")


def _agreed(host, party, text="add a dark mode option") -> str:
    """A goal sent, talked through and its decision worded: at `decided`."""
    slug = host.command("ideas.add", {"text": text, "track": party})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "decided")
    return slug


def _ripe(host, slug):
    return idea_ripe.of(host.ideas.state_dir, slug)


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


# -- the goal's weight -----------------------------------------------------------------------------------------------------------------

def _stance(craft, **more):
    return {"party": craft, "leader": craft, "craft": craft, "verdict": "go", "priority": "", "risk": "", "against": "", **more}


def test_the_wait_is_kept_beside_the_decision_counts_down_is_held_and_ends(host, tech):
    state = host.ideas.state_dir
    slug = "a-goal"
    assert idea_ripe.of(state, slug) is None and idea_ripe.begin(state, slug, "normal", "medium") is None and idea_ripe.hold(state, slug) is None
    got = idea_ripe.begin(state, slug, "high", "low")
    assert got == {"left_s": 60.0, "seconds": 60, "risk": "low", "priority": "high", "held": False, "by": "", "why": ""} == spec_sections.record(state, slug)["ripe"]
    assert idea_ripe.running(state, slug) and idea_ripe.tick(state, [slug, "nobody"], 25) == [] and idea_ripe.of(state, slug)["left_s"] == 35.0
    assert idea_ripe.tick(state, [slug], -5) == [] and idea_ripe.of(state, slug)["left_s"] == 35.0                  # time never runs back
    assert idea_ripe.tick(state, [slug], 40) == [slug] and idea_ripe.of(state, slug)["left_s"] == 0.0               # ended: named until it is done
    idea_ripe.done(state, slug)
    assert idea_ripe.of(state, slug)["by"] == "leaders" and not idea_ripe.running(state, slug) and idea_ripe.tick(state, [slug], 5) == []
    idea_ripe.begin(state, slug, "normal", "low")
    assert idea_ripe.hold(state, slug, "person") == 600.0
    assert idea_ripe.of(state, slug) == {"left_s": 0.0, "seconds": 600, "risk": "low", "priority": "normal", "held": True, "by": "person", "why": ""}
    assert idea_ripe.hold(state, slug) is None and idea_ripe.tick(state, [slug], 5) == [] and not idea_ripe.running(state, slug)       # held once, the time gone
    idea_ripe.drop(state, slug)
    assert idea_ripe.of(state, slug) is None and "ripe" not in spec_sections.record(state, slug)


# -- the wait begins when the leaders all agreed -----------------------------------------------------------------------------------------

def test_all_the_leaders_agreeing_begin_the_wait_beside_the_worded_decision(host, tech, model):
    slug = _agreed(host, tech)
    assert _ripe(host, slug) == {"left_s": 600.0, "seconds": 600, "risk": "low", "priority": "normal", "held": False, "by": "", "why": ""}      # no Product party: risk low only
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is False
    (started,) = _events(host, event_log.RIPE_STARTED)
    assert started["idea"] == slug and started["seconds"] == 600 and started["priority"] == "normal" and started["risk"] == "low"
    assert idea_questions.record(host.ideas.state_dir, slug)["weight"] == {"priority": "normal", "risk": "low"}


@pytest.mark.parametrize("said", [
    {"verdict": "doubt", "why": "Is it worth it now?"},                        # any doubt or no: a hearing
    {"verdict": "no", "why": "Not before the lobby"},
    {"risk": "medium"},                                                       # no Product's word and a risk above low: the decision's card as it was
    {"risk": "high"},
])
def test_a_hearing_or_a_goal_nobody_could_weigh_begins_no_wait(host, tech, model, said):
    model["talk_round"] = {**TECH_SAID, **said}
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    if said.get("verdict") in ("no", "doubt"):
        _until(host, slug, "talk")                                            # a no or a doubt waits for the person's throw (spec 120 §3.4): the decision is not worded
    else:
        _until(host, slug, "decided")
    assert _ripe(host, slug) is None and _events(host, event_log.RIPE_STARTED) == []


@pytest.mark.weighs
@pytest.mark.parametrize("priority, risk, left", [("high", "low", 60.0), ("normal", "low", 600.0), ("high", "medium", 600.0), ("normal", "medium", None), ("high", "high", None)])
def test_product_weighing_the_goal_is_its_word_and_its_priority_makes_the_wait(host, tech, product, model, priority, risk, left):
    model["talk_round"] = {**TECH_SAID, "risk": risk}
    model[("talk_round", product)] = {"verdict": "go", "priority": priority}
    slug = _agreed(host, tech)
    got = _ripe(host, slug)
    assert (got["left_s"] if got else None) == left
    assert idea_questions.record(host.ideas.state_dir, slug)["weight"]["priority"] == priority


# -- it counts down only while a face is open ----------------------------------------------------------------------------------------


def test_hold_stops_the_wait_and_the_goal_waits_for_the_persons_start(host, tech, model):
    slug = _agreed(host, tech)
    host.faces = lambda: 1
    host.ideas.ripe_tick(10.0)
    host.ideas.ripe_tick(11.0)
    assert host.ideas.ripe_hold_goal(slug) == 599.0
    got = _ripe(host, slug)
    assert got["held"] is True and got["by"] == "person" and got["left_s"] == 0.0
    (held,) = _events(host, event_log.RIPE_HELD)
    assert held["idea"] == slug and held["left_s"] == 599.0
    for at in (12.0, 20.0, 400.0):
        host.ideas.ripe_tick(at)
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "decided" and host.ideas.ripe_hold_goal(slug) is None       # held once; nothing starts it
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is False
    got = host.command("ideas.confirm", {"idea": slug})                                                             # *Start*: the person's, as it always was
    assert got["ok"] is True and "the person and" in subprocess.run(["git", "show", "dev:docs/decisions.md"], cwd=host.repo_root, capture_output=True, text=True).stdout
    assert idea_ripe.of(host.ideas.state_dir, slug) is None                                                         # the wait is over, whoever ended it


# -- the end ---------------------------------------------------------------------------------------------------------------------------------

def _run_out(host, slug, monkeypatch):
    monkeypatch.setattr(ideas_route, "RIPE_MAX_DT", 10_000.0)
    host.faces = lambda: 1
    host.ideas.ripe_tick(0.0)
    host.ideas.ripe_tick(1.0)
    host.ideas.ripe_tick(2000.0)                                                                                    # a wait of 600 s, run out in one tick


def test_the_end_writes_the_leaders_heading_and_starts_the_sections(host, tech, model, monkeypatch):
    slug = _agreed(host, tech)
    _run_out(host, slug, monkeypatch)
    _until(host, slug, "plan")
    entry = subprocess.run(["git", "show", "dev:docs/decisions.md"], cwd=host.repo_root, capture_output=True, text=True).stdout
    head = next(line for line in entry.splitlines() if line.startswith("## 1. "))
    assert head.startswith("## 1. Dark mode ships (") and head.endswith(", the leaders, all agreed; Orkboard)") and "the person" not in head
    assert ": A dark mode helps at night" in entry and "\n3. For " in entry                                           # the leaders' stances are among the points, numbered on from the Orkmaster's two
    d = spec_sections.record(host.ideas.state_dir, slug)["decision"]
    assert d["confirmed"] is True and d["confirmed_by"] == "leaders" and d["number"] == 1
    assert _ripe(host, slug)["by"] == "leaders" and _ripe(host, slug)["left_s"] == 0.0
    (done,) = _events(host, event_log.RIPE_DONE)
    assert done["idea"] == slug
    committed = [e for e in _events(host, event_log.BOARD_COMMITTED) if e.get("what") == "decision"]
    assert committed and ideas.idea_page(host.ideas.root(), slug).parts("Tech")["Why"] == "Because."                  # committed to dev as every decision is, then the sections


def test_a_spent_window_or_a_stop_at_the_end_holds_the_goal_with_why_and_never_starts_it(host, tech, model, monkeypatch):
    slug = _agreed(host, tech)
    monkeypatch.setattr(host.ideas.keeper, "window_until", lambda: time.time() + 3600)                              # the Claude window is spent
    _run_out(host, slug, monkeypatch)
    got = _ripe(host, slug)
    assert got["held"] is True and got["by"] == "stopped" and "window is spent" in got["why"]
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "decided" and spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is False
    assert _events(host, event_log.RIPE_DONE) == [] and _events(host, event_log.RIPE_HELD)[-1]["why"].startswith("Claude's window is spent")


def test_stop_all_holds_every_wait_that_counts_down(host, tech, model):
    slug = _agreed(host, tech)
    host.command("halt", {})
    got = _ripe(host, slug)
    assert got["held"] is True and got["by"] == "stopped" and "Stopped" in got["why"]
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "decided"
