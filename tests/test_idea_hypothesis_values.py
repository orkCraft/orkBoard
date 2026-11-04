"""Spec 146 C.1 (docs/specs/146-a-hypothesis-on-the-page.md; spec 133 B.3, B.5; decisions §235.2): a hypothesis's measures read by the leader whose map holds the source (step `measure_read`, one call a party at
the measure's date, begun on the clock's tick and never by a press), a value it leaves out or a call that fails left to the person, the event with no number. The model call is stubbed (`keeper.call`) as
`tests/test_idea_findings.py` does."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.core import idea_hypothesis_values as ihv, idea_keeper
from orkboard.gui.board_host import Orkboard
from orkboard.realm import board_rows, event_log, goal_result, goal_team, hypotheses, idea_spend, idea_target, ideas, library

PAST = (dt.date.today() - dt.timedelta(days=1)).isoformat()
AHEAD = (dt.date.today() + dt.timedelta(days=9)).isoformat()


@pytest.fixture
def host(fake_repo, monkeypatch) -> Orkboard:
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": [], "screens": [], "files": 0})
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas.keeper, ihv.HypothesisValuesMixin) and idea_keeper.HypothesisValuesMixin is ihv.HypothesisValuesMixin
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def run(host):
    return _party(host, "Run", "architect", ["grunt"], "engineering")


class Model:
    """The keeper's call stubbed: every call is kept; `answer` is a callable of the call, a dict, text or an Exception."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "key": getattr(k._tls, "key", "")})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        if isinstance(answer, Exception):
            raise answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


def _hyp(host, party, date=PAST, by=None, **extra):
    m = {"what": "Came back within 7 days", "from": "the store page", "by": party if by is None else by, "bars": {"holds": {"op": ">=", "n": 30, "unit": "%"}}, "date": date}
    return hypotheses.add(host.ideas.state_dir, "Players come back", "most do", measures=[m, *extra.get("more", [])])


def _wait(host, key):
    for _ in range(1000):
        if not host.ideas.keeper.busy(key):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _events(host):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == event_log.MEASURE_READ]


def _value(host, hid="players-come-back", mid="m1"):
    item = next(i for i in hypotheses.read(host.ideas.state_dir)["items"] if i["id"] == hid)
    return next(m for m in item["measures"] if m["id"] == mid)["value"]


def _tick(host):
    host.ideas.keeper.__dict__["_measures_at"] = float("-inf")
    return host.ideas.keeper.measures_due()


# -- the answer, taken strictly -------------------------------------------------------------------------------------------------------------------------

def test_the_answer_is_taken_strictly():
    ids = ["m1", "m2"]
    assert ihv.clean_values({"values": [{"id": "m1", "n": 41, "from": " the store  page "}, {"id": "m2", "n": "12", "from": "x"}, {"id": "m3", "n": 1}, {"id": "m1", "n": 2}, "x", {"id": "m2", "n": True}]}, ids) == {
        "m1": {"n": 41.0, "from": "the store page"}}
    assert ihv.clean_values({"values": []}, ids) == {} and ihv.clean_values({"values": {"m1": 1}}, ids) is None and ihv.clean_values("41", ids) is None
    assert ihv.clean_values({"values": [{"id": "m1", "n": float("inf")}]}, ids) == {}


def test_only_an_open_item_with_its_goals_done_a_party_no_value_and_its_date_reached_is_asked_and_once():
    m = lambda **kw: {"id": "m1", "what": "w", "from": "", "by": "run", "bars": {"holds": {"op": ">=", "n": 1.0, "unit": ""}, "refuted": []}, "span_days": 28, "date": PAST, "value": None, **kw}      # noqa: E731
    item = lambda **kw: {"id": "h", "state": "open", "tests": [], "measures": [m()], **kw}                                                                                                            # noqa: E731
    today = dt.date.today().isoformat()
    assert [(i["id"], p, [x["id"] for x in ms]) for i, p, ms in ihv.wanted([item()], {}, today, set())] == [("h", "run", ["m1"])]
    assert ihv.wanted([item(tests=["g"])], {"g": "work"}, today, set()) == [] and len(ihv.wanted([item(tests=["g"])], {"g": "done"}, today, set())) == 1
    assert ihv.wanted([item(measures=[m(date=AHEAD)])], {}, today, set()) == [] and ihv.wanted([item(measures=[m(by="")])], {}, today, set()) == []
    assert ihv.wanted([item(measures=[m(value={"n": 1.0})])], {}, today, set()) == [] and ihv.wanted([item(state="held")], {}, today, set()) == []
    assert ihv.wanted([item()], {}, today, {"h/m1"}) == [] and ihv.wanted([item()], {}, today, set(), {"other"}) == []


# -- asked at the date and not before -------------------------------------------------------------------------------------------------------------------

def test_the_leader_is_asked_at_the_date_and_not_before_and_its_value_is_kept(host, run):
    keeper = host.ideas.keeper
    model = Model(host, lambda call: {"values": [{"id": "m1", "n": 41, "from": "the store page, 7 days"}]})
    _hyp(host, run, date=AHEAD)
    assert _tick(host) == 0 and model.calls == []                                                             # the date is ahead
    hypotheses.measure_set(host.ideas.state_dir, "players-come-back", mid="m1", date=PAST)
    assert _tick(host) == 1
    _wait(host, "hypothesis:players-come-back")
    (call,) = model.calls
    assert call["step"] == "measure_read" and call["tools"] is True and call["key"] == f"goal:{run}" and "Came back within 7 days" in call["prompt"] and "Players come back" in call["prompt"]
    assert (call["tier"], call["effort"]) == idea_target.pick("measure_read", "balance")
    got = _value(host)
    assert got["n"] == 41.0 and got["by"] == run and got["from"] == "the store page, 7 days"
    assert _tick(host) == 0 and len(model.calls) == 1                                                         # once
    assert not keeper.measures_read("players-come-back")


def test_a_value_the_leader_leaves_out_is_left_to_the_person_and_not_asked_again(host, run):
    model = Model(host, {"values": []})
    _hyp(host, run)
    assert _tick(host) == 1
    _wait(host, "hypothesis:players-come-back")
    assert _value(host) is None and len(model.calls) == 1
    (row,) = board_rows.hypothesis(host.ideas.state_dir, host.ideas.root())
    assert row["measures"][0]["value"] is None                                                                 # the card asks the person (B.1)
    assert _tick(host) == 0 and len(model.calls) == 1
    hypotheses.value(host.ideas.state_dir, "players-come-back", "m1", 38, "person")                            # the person types it
    assert _value(host)["n"] == 38.0 and _value(host)["by"] == "person"


def test_a_failed_call_asks_the_person_and_one_that_cannot_be_made_asks_nothing(host, run):
    model = Model(host, RuntimeError("down"))
    _hyp(host, run)
    assert _tick(host) == 1
    _wait(host, "hypothesis:players-come-back")
    assert _value(host) is None and len(model.calls) == 2                                                      # one more try
    (ev,) = _events(host)
    assert ev["read"] == 0 and ev["measures"] == 1
    host.ideas.keeper.demo = True                                                                              # the demo, a spent cap: no call can be made
    hypotheses.measure_set(host.ideas.state_dir, "players-come-back", what="Another thing", bars={"holds": {"op": ">=", "n": 1}}, by=run, date=PAST)
    assert _tick(host) == 0 and len(model.calls) == 2


def test_a_measure_of_the_person_or_of_a_party_gone_is_never_asked_of_a_leader(host, run):
    model = Model(host, {"values": []})
    _hyp(host, run, by="")
    assert _tick(host) == 0
    hypotheses.measure_set(host.ideas.state_dir, "players-come-back", mid="m1", by="gone-party")
    assert _tick(host) == 0 and model.calls == []


def test_a_hypothesis_whose_goals_are_not_done_waits_for_them(host, run):
    model = Model(host, {"values": [{"id": "m1", "n": 1, "from": "x"}]})
    _hyp(host, run)
    slug = ideas.add_idea(host.ideas.root(), "Ship the loop", run, host.ideas.state_dir)
    hypotheses.attach(host.ideas.state_dir, "players-come-back", test=slug)
    assert _tick(host) == 0 and model.calls == []
    ideas.save_state(host.ideas.state_dir, slug, state="done")
    assert _tick(host) == 1
    _wait(host, "hypothesis:players-come-back")
    assert _value(host)["n"] == 1.0


def test_the_event_names_the_counts_and_never_a_number(host, run):
    Model(host, {"values": [{"id": "m1", "n": 41.5, "from": "the store page"}]})
    _hyp(host, run)
    assert _tick(host) == 1
    _wait(host, "hypothesis:players-come-back")
    (ev,) = _events(host)
    assert {"idea", "party", "measures", "read", "seconds", "cost"} <= set(ev) and (ev["idea"], ev["party"], ev["measures"], ev["read"]) == ("players-come-back", run, 1, 1)
    assert "41" not in json.dumps(ev) and "store page" not in json.dumps(ev)


def test_the_step_is_in_every_table_of_the_target():
    assert "measure_read" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    assert idea_target.READS["measure_read"] == 4 and idea_target.CONTEXT["measure_read"] == 9_000 and idea_target.CAPS["measure_read"] > 0
    assert idea_spend.STEP_STAGE["measure_read"] == "spec" and event_log.MEASURE_READ in event_log.EVENTS
    assert idea_target.pick("measure_read", "balance")[0] in ("warrior", "laborer")
