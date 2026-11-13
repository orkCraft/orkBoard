"""Spec 131 B.1–B.4 (docs/specs/131-a-leaders-slices-and-the-cascade.md; decisions §233.5–§233.9, §237.6) on the keeper and the host: a proposal in a leader's answer is kept and the answer is not changed; the steps follow the
links; three steps stop; a point changed twice is a fork; the price stops it; the decision's `changes`; what follows leaves the discard out; Confirm refuses an open fork, writes one entry, replaces the chain's slices with
their *was* and asks the sections again; Put it back changes nothing. The keeper's call is stubbed (`keeper.call`), as `tests/test_idea_slices.py` does; no real model.
"""
from __future__ import annotations

import datetime as dt
import json
import threading
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError
from orkboard.realm import board_ask, cascades, decisions_log, event_log, idea_target, ideas, slices, spec_sections
from tests.test_idea_slices import LOG, _log, _party, design, goal, host, release, tech  # noqa: F401  (the fixtures)
from tests.test_way_down import _goal


@pytest.fixture
def marketing(host):
    return _party(host, "Marketing", "growth", [], "marketing")


@pytest.fixture
def data(host):
    return _party(host, "Data", "analyst", [], "data")


class Model:
    """The keeper's call stubbed: `said[step]` the JSON (or a callable of the call) every call of that step gets; `cost` what each call costs; `after` called after each call (a fake week that runs down)."""

    def __init__(self, host):
        self.host, self.calls, self.said, self.lock, self.live, self.now, self.cost, self.after = host, [], {}, threading.Lock(), 0, 0, 0.01, None
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "key": getattr(k._tls, "key", ""),
               "as_role": getattr(k._tls, "as_role", "")}
        with self.lock:
            self.calls.append(row)
            self.now += 1
            self.live = max(self.live, self.now)
        try:
            answer = self.said.get(row["step"], {})
            answer = answer(row) if callable(answer) else answer
            if isinstance(answer, Exception):
                raise answer
            if self.after:
                self.after(row)
            return (answer if isinstance(answer, str) else json.dumps(answer)), self.cost, 10, ""
        finally:
            with self.lock:
                self.now -= 1


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host):
    k = host.ideas.keeper
    for _ in range(3000):
        if not k._busy and not k._cs()["queue"] and not k._cs()["running"]:
            return
        time.sleep(0.01)
    raise AssertionError(f"the keeper never finished: {k._busy}")


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def _cut(host, n, party, says, points):
    return slices.add_cut(host.ideas.state_dir, n, {party: {"says": says, "points": points}})[0]


def _agree(row):
    party = row["key"].removeprefix("goal:")
    return {"answer": "agrees", "says": f"{party} says it new.", "why": "It follows."}


def _run(host, party, slice_id, says="Your builds are quick and cached.", why="The cache ran into it.", points=None, step="section", idea=""):
    cid = host.ideas.keeper.cascade_propose(party, slice_id, says, why, points, step, idea)
    _wait(host)
    return cid


# -- a proposal in a leader's answer ---------------------------------------------------------------------------------------------------------

def test_a_proposal_in_a_sections_answer_is_kept_and_the_section_is_kept_unchanged(host, tech, goal, model):
    old = _cut(host, 6, tech, "Your builds are quick.", ["6.2"])
    k = host.ideas.keeper
    k._tls.cancel, k._tls.slug, k._tls.key = threading.Event(), goal, goal
    entry, section = {"party": tech, "leader": "architect"}, {"why": "It matters.", "done_when": ["When a, then b"], "checks": [], "will_be": [], "out": [], "risks": [], "risk": "low", "assumed": []}
    model.said["section_first"] = section
    plain = k._write_sections(goal, [entry], [entry])
    model.said["section_first"] = {**section, "propose": {"slice": old["id"], "says": "Your builds are quick and cached.", "why": "The cache ran into it.", "points": ["6.2"]}}
    got = k._write_sections(goal, [entry], [entry])
    _wait(host)
    assert got[tech]["parts"] == plain[tech]["parts"] and got[tech]["risk"] == plain[tech]["risk"]          # the section is kept as it came
    (rec,) = cascades.read(host.ideas.state_dir)
    assert (rec["party"], rec["slice"], rec["from_step"], rec["idea"], rec["status"]) == (tech, old["id"], "section_first", goal, "ready")
    (e,) = _events(host, event_log.SLICE_PROPOSED)
    assert (e["party"], e["from_step"], e["dropped"]) == (tech, "section_first", "")
    assert slices.standing(host.ideas.state_dir, tech)[0]["id"] == old["id"]                                # a proposal changes nothing by itself


# -- the prompts ----------------------------------------------------------------------------------------------------------------------------



def test_a_proposal_in_the_leaders_bubble_is_kept_and_the_answer_is_as_it_was(host, tech, model):
    old = _cut(host, 6, tech, "Your builds are quick.", ["6.2"])
    model.said["ask"] = {"answer": "Quick.", "sources": ["§6"], "goal": "", "propose": {"slice": old["id"], "says": "Your builds are quick and cached.", "why": "The cache ran into it."}}
    k = host.ideas.keeper
    k._start("ask", "asking", lambda: k.ask_run(tech, "Are builds quick?"), key="ask")
    _wait(host)
    assert board_ask.record(host.ideas.state_dir)["answer"] == "Quick."
    (rec,) = cascades.read(host.ideas.state_dir)
    assert rec["from_step"] == "ask" and rec["party"] == tech and rec["says"] == "Your builds are quick and cached."


# -- the steps ------------------------------------------------------------------------------------------------------------------------------

def _chain(host, tech, design, marketing, release):
    sd = host.ideas.state_dir
    slices.add_cut(sd, 5, {tech: {"says": "Your builds hold 10 seconds.", "points": ["5.1"]}, design: {"says": "Your art fits 10 seconds.", "points": ["5.1", "5.2"]}})
    slices.add_cut(sd, 6, {marketing: {"says": "Your trailers show 10 seconds.", "points": ["5.2"]}})
    slices.add_cut(sd, 7, {release: {"says": "Your notes say 10 seconds.", "points": ["6.1", "5.2"]}})
    return slices.standing(sd, tech)[0]


def test_the_steps_follow_the_links_two_steps_deep_one_leader_at_a_time(host, tech, design, marketing, release, model):
    top = _chain(host, tech, design, marketing, release)
    model.said["cascade"] = _agree
    cid = _run(host, tech, top["id"], points=["5.1"])
    rec = cascades.get(host.ideas.state_dir, cid)
    assert rec["status"] == "ready" and rec["stopped"] == "" and model.live == 1                              # one call at a time
    assert [(s["n"], s["party"]) for s in rec["steps"]] == [(1, design), (2, release), (2, marketing)]       # step 1 asks the slices on 5.1, step 2 those on what step 1 changed (5.2)
    calls = model.steps("cascade")
    assert [c["key"] for c in calls] == [f"goal:{design}", f"goal:{release}", f"goal:{marketing}"]
    for c in calls:
        assert c["tools"] is False and (c["tier"], c["effort"]) == idea_target.pick("cascade", "balance") and c["budget"] == idea_target.budget("cascade", "balance")
    assert "Tech proposes: Your builds are quick and cached., because The cache ran into it.; it changes §5.1" in calls[0]["prompt"] and "Your art fits 10 seconds. (§5.1, §5.2)" in calls[0]["prompt"]
    assert "Design: Your art fits 10 seconds. -> design says it new." in calls[1]["prompt"]                    # the second step is told what the first changed
    assert rec["changed"] == ["5.1", "5.2", "6.1"] and [c["party"] for c in cascades.chain(rec)] == [tech, design, release, marketing]
    assert all(c["before"] and c["after"] for c in cascades.chain(rec))
    assert rec["cost"] == pytest.approx(0.04) and rec["error"] == ""
    (e,) = _events(host, event_log.CASCADE_READY)
    assert (e["steps"], e["agreed"], e["forks"], e["stopped"], e["failed"]) == (3, 3, 0, "", False) and "Your builds" not in json.dumps(e)


def test_three_steps_stop_and_say_who_was_not_asked(host, tech, design, marketing, release, data, model):
    top = _chain(host, tech, design, marketing, release)
    slices.add_cut(host.ideas.state_dir, 8, {data: {"says": "Your events count 10 seconds.", "points": ["6.1", "8.1"]}})
    slices.add_cut(host.ideas.state_dir, 9, {marketing: {"says": "Your store page says 10 seconds.", "points": ["8.1"]}})
    model.said["cascade"] = _agree
    rec = cascades.get(host.ideas.state_dir, _run(host, tech, top["id"], points=["5.1"]))
    assert rec["status"] == "ready" and rec["stopped"] == "Stopped after 3 steps: Marketing was not asked" and max(s["n"] for s in rec["steps"]) == 3
    assert len(model.steps("cascade")) == 4                         # the fourth step is not asked
    (e,) = _events(host, event_log.CASCADE_READY)
    assert e["stopped"] == "steps"
    (row,) = cascades.rows(host.ideas.state_dir, host.ideas.root())
    assert row["stopped"] == "Stopped after 3 steps: Marketing was not asked"


def test_a_leader_that_disagrees_or_does_not_answer_is_a_fork_for_the_person(host, tech, design, marketing, model):
    top = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    _cut(host, 6, design, "Your art fits 10 seconds.", ["5.1"])
    _cut(host, 7, marketing, "Your trailers show 10 seconds.", ["5.1"])
    model.said["cascade"] = lambda row: {"answer": "disagrees", "why": "It breaks the look."} if row["key"] == f"goal:{design}" else "no JSON at all"
    rec = cascades.get(host.ideas.state_dir, _run(host, tech, top["id"], points=["5.1"]))
    assert rec["status"] == "ready" and {f["party"]: f["why"] for f in rec["forks"]} == {design: "It breaks the look.", marketing: "Did not answer"}
    assert len(model.steps("cascade")) == 3                                                                   # the marketing leader was tried once more
    assert [c["party"] for c in cascades.chain(rec)] == [tech]


def test_when_every_call_fails_the_cascade_failed_with_why_and_nothing_changed(host, tech, design, model):
    top = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    _cut(host, 6, design, "Your art fits 10 seconds.", ["5.1"])
    model.said["cascade"] = RuntimeError("the tool failed")
    rec = cascades.get(host.ideas.state_dir, _run(host, tech, top["id"], points=["5.1"]))
    assert rec["status"] == "failed" and rec["error"] == "No leader answered: try again" and cascades.rows(host.ideas.state_dir) == []
    assert slices.standing(host.ideas.state_dir, tech)[0]["id"] == top["id"] and _events(host, event_log.CASCADE_READY)[0]["failed"] is True


def test_one_cascade_at_a_time_and_a_second_waits_behind_the_first(host, tech, design, model):
    a = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    b = _cut(host, 6, design, "Your art fits 10 seconds.", ["6.1"])
    model.said["cascade"] = _agree
    k = host.ideas.keeper
    first, second = k.cascade_propose(tech, a["id"], "Builds are quick.", "Shown.", None, "plan"), k.cascade_propose(design, b["id"], "Art is quick.", "Shown.", None, "ask")
    _wait(host)
    assert first and second and model.live == 1 and [r["status"] for r in cascades.read(host.ideas.state_dir)] == ["ready", "ready"]


# -- the price ------------------------------------------------------------------------------------------------------------------------------

class Week:
    """A fake weekly window of the main tool: its share left runs down by `step` a call."""
    provider, window, group, error, note = "claude", "weekly", "week", None, ""

    def __init__(self, remaining):
        self.remaining, self.reset = remaining, dt.datetime.now() + dt.timedelta(days=3)




# -- the decision, what follows ---------------------------------------------------------------------------------------------------------------

def test_the_decision_is_worded_by_the_orkmaster_and_its_changes_name_the_decisions_that_changed(host, tech, design, marketing, release, model):
    _log(host)
    top = _chain(host, tech, design, marketing, release)
    model.said["cascade"] = _agree
    model.said["decide"] = {"title": "Builds are cached", "why": "The cache ran into the old line.", "points": ["Tech caches builds.", "Art follows."], "changes": []}
    rec = cascades.get(host.ideas.state_dir, _run(host, tech, top["id"], points=["5.1"]))
    (call,) = model.steps("decide")
    assert call["as_role"] == "orkmaster" and call["tools"] is False and (call["tier"], call["effort"]) == idea_target.pick("decide", "balance")
    for text in ("Tech proposes: Your builds are quick and cached.", f"{design} says it new.", "The project's decisions file"):
        assert text in call["prompt"], text
    assert rec["decision"]["title"] == "Builds are cached" and rec["decision"]["text"].startswith("Why: The cache ran into the old line.\n\n1. Tech caches builds.")
    assert set(rec["decision"]["changes"]) == {5, 6, 7}                                                       # code adds what the call left out: the decisions the changed slices and points are of


def test_the_row_lies_among_the_needs_you_rows_of_no_goal(host, tech, design, model):
    top = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    _cut(host, 6, design, "Your art fits 10 seconds.", ["5.1"])
    model.said["cascade"] = _agree
    _run(host, tech, top["id"], says="Builds are cached.", points=["5.1"])
    from orkboard.realm import board_rows
    (row,) = [r for r in board_rows.rows(host.ideas.state_dir, host.ideas.root()) if r["kind"] == "cascade"]
    assert row["line"] == "Tech and Design agree" and row["party"] == tech


# -- Confirm and Put it back -------------------------------------------------------------------------------------------------------------------

def _ready(host, tech, design, model, agree=True):
    """The log, Tech's and Design's slices, a goal at work that rests on decision 5 (its sections written by both) and a cascade of Tech's proposal made ready."""
    _log(host)
    top = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    mine = _cut(host, 6, design, "Your art fits 10 seconds.", ["5.1"])
    slug = _goal(host, tech, number=5, others=(design,))
    texts = {p: {"parts": {"Why": "Because.", "Done when": "- The winner shows"}, "risk": "low", "leader": leader} for p, leader in ((tech, "architect"), (design, "product-designer"))}
    ideas.save_state(host.ideas.state_dir, slug, route=[{"party": tech, "leader": "architect"}, {"party": design, "leader": "product-designer"}])
    way = spec_sections.record(host.ideas.state_dir, slug)
    spec_sections.save_record(host.ideas.state_dir, slug, {**way, "texts": texts})
    model.said["cascade"] = _agree if agree else {"answer": "disagrees", "why": "It breaks the look."}
    model.said["decide"] = {"title": "Builds are cached", "why": "The cache ran into it.", "points": ["Tech caches builds.", "Art follows."]}
    model.said["section"] = model.said["section_first"] = {"why": "Rewritten.", "done_when": ["When a, then b"], "checks": [], "will_be": [], "out": [], "risks": [], "risk": "low", "assumed": []}
    cid = _run(host, tech, top["id"], says="Builds are cached.", points=["5.1"], step="plan")
    return cid, top, mine, slug


def test_confirm_refuses_an_open_fork_and_writes_nothing(host, tech, design, model):
    cid, top, mine, slug = _ready(host, tech, design, model, agree=False)
    before = decisions_log.numbers(host.ideas.keeper._log_text())
    with pytest.raises(CommandError, match="Answer the fork first"):
        host.command("ideas.cascade_confirm", {"id": cid})
    with pytest.raises(CommandError, match="Answer the fork first"):
        host.command("ideas.cascade_confirm", {"id": cid, "fork_answers": {"s-other": "keep"}})
    assert decisions_log.numbers(host.ideas.keeper._log_text()) == before and cascades.get(host.ideas.state_dir, cid)["status"] == "ready"
    with pytest.raises(CommandError, match="gave no words"):
        host.command("ideas.cascade_confirm", {"id": cid, "fork_answers": {mine["id"]: "change"}})
    assert [s["id"] for s in slices.standing(host.ideas.state_dir, tech)] == [top["id"]]


def test_confirm_writes_one_entry_replaces_the_chains_slices_with_their_was_and_asks_the_sections_again(host, tech, design, model, monkeypatch):
    cid, top, mine, slug = _ready(host, tech, design, model)
    asked = []
    monkeypatch.setattr(type(host.ideas.keeper), "change_ask", lambda self, idea, party, part, text: asked.append((idea, party, text)) or "c1")
    model.calls.clear()
    got = host.command("ideas.cascade_confirm", {"id": cid})
    assert got["ok"] is True and got["number"] == 7 and got["slices"] == 2 and got["sections"] == [slug] and got["left"] == []
    _wait(host)
    log = host.ideas.keeper._log_text()
    assert log.count("## 7. Builds are cached") == 1 and "Changes: 5, 6." in log and "the person and" in log                         # one entry, by the person, its `Changes:` the record's
    sd = host.ideas.state_dir
    now = {p: slices.standing(sd, p) for p in (tech, design)}
    assert len(now[tech]) == len(now[design]) == 1 and now[tech][0]["decision"] == now[design][0]["decision"] == 7
    assert now[tech][0]["says"] == "Builds are cached." and now[tech][0]["was"] == "Your builds hold 10 seconds (§5.1)" and now[tech][0]["points"][0] == "7"
    assert now[design][0]["says"] == f"{design} says it new." and now[design][0]["was"] == "Your art fits 10 seconds (§5.1)"
    old = {s["id"]: s for s in slices.read(sd)["slices"]}
    assert old[top["id"]]["replaced_by"] == now[tech][0]["id"] and old[mine["id"]]["replaced_by"] == now[design][0]["id"]
    assert slices.read(sd)["cut"]["7"] == [tech, design] and model.steps("slice") == []                                              # cut with no call
    assert sorted(c["step"] for c in model.calls if c["step"] in ("section", "section_first")) == ["section", "section_first"]    # a call a section, the two the goal rests on
    way = spec_sections.record(sd, slug)
    assert all(t["parts"]["Why"] == "Rewritten." for t in way["texts"].values())
    assert "Decision 7: Builds are cached [sections: " in ideas.idea_page(host.ideas.root(), slug).section("Decisions")
    assert sorted(p for _i, p, _t in asked) == sorted([tech, design]) and all(i == slug and "Decision 7" in t for i, _p, t in asked)       # a goal at work: each leader re-plans what is left
    assert cascades.get(sd, cid)["status"] == "confirmed" and cascades.rows(sd) == []
    (e,) = _events(host, event_log.CASCADE_CONFIRMED)
    assert (e["decision"], e["slices"], e["forks"], e["sections"], e["party"]) == (7, 2, 0, 1, tech) and "Builds" not in json.dumps(e)
    with pytest.raises(CommandError, match="No change of a decision waits here"):
        host.command("ideas.cascade_confirm", {"id": cid})                                                                          # once
    assert host.ideas.keeper._log_text().count("## 7.") == 1




def test_a_stop_keeps_nothing_and_empties_the_queue(host, tech, design, model):
    top = _cut(host, 5, tech, "Your builds hold 10 seconds.", ["5.1"])
    _cut(host, 6, design, "Your art fits 10 seconds.", ["5.1"])
    model.said["cascade"] = InterruptedError("stopped")
    _run(host, tech, top["id"], points=["5.1"])
    assert cascades.read(host.ideas.state_dir) == [] and host.ideas.keeper._cs()["queue"] == []


def test_put_it_back_changes_nothing_and_the_slice_may_be_proposed_on_again(host, tech, design, model):
    cid, top, mine, slug = _ready(host, tech, design, model)
    before = (decisions_log.numbers(host.ideas.keeper._log_text()), slices.read(host.ideas.state_dir))
    assert host.command("ideas.cascade_back", {"id": cid}) == {"ok": True}
    assert (decisions_log.numbers(host.ideas.keeper._log_text()), slices.read(host.ideas.state_dir)) == before             # every slice stands
    assert cascades.get(host.ideas.state_dir, cid)["status"] == "put_back" and host.command("ideas.cascades", {})["cascades"] == []
    (e,) = _events(host, event_log.CASCADE_PUT_BACK)
    assert e["party"] == tech and e["forks"] == 0
    with pytest.raises(CommandError, match="No change of a decision waits here"):
        host.command("ideas.cascade_back", {"id": cid})
    with pytest.raises(CommandError, match="No change of a decision waits here"):
        host.command("ideas.cascade_confirm", {"id": cid})
    assert host.ideas.keeper.cascade_propose(tech, top["id"], "Another way.", "Shown.", None, "ask") is not None


def test_a_slice_with_a_cascade_open_or_lost_with_the_process_is_not_held_a_party_gone_is_dropped_and_a_point_changed_twice_is_a_fork(host, tech, design, marketing, model):
    old = _cut(host, 6, tech, "Your builds are quick.", ["6.2"])
    k = host.ideas.keeper
    assert k.cascade_propose("ghost", old["id"], "Faster.", "Shown.", None, "ask") is None
    first = _run(host, tech, old["id"])
    assert cascades.get(host.ideas.state_dir, first)["status"] == "ready"
    assert k.cascade_propose(tech, old["id"], "Another way.", "Because.", None, "ask") is None and len(cascades.read(host.ideas.state_dir)) == 1
    assert [e["dropped"] for e in _events(host, event_log.SLICE_PROPOSED)] == ["gone", "", "open"]
    cascades.save(host.ideas.state_dir, {**cascades.get(host.ideas.state_dir, first), "status": "put_back"})
    stale = cascades.add(host.ideas.state_dir, tech, cascades.clean_proposal({"slice": old["id"], "says": "Faster.", "why": "Shown."}, tech, slices.standing(host.ideas.state_dir, tech)), "ask")
    assert k.cascade_propose(tech, old["id"], "Faster still.", "Shown.", None, "ask") is not None      # the one lost with the process does not hold the slice
    _wait(host)
    assert cascades.get(host.ideas.state_dir, stale["id"])["status"] == "failed"
    top = _cut(host, 15, tech, "Your builds hold 10 seconds.", ["5.1"])
    _cut(host, 16, design, "Your art fits 10 seconds.", ["5.1", "6.1"])
    _cut(host, 17, marketing, "Your trailers show 10 seconds.", ["5.1", "6.1"])
    model.said["cascade"] = _agree
    rec = cascades.get(host.ideas.state_dir, _run(host, tech, top["id"], points=["5.1"]))
    (fork,) = rec["forks"]
    assert fork["party"] == design and "a second time" in fork["why"] and rec["steps"][1]["forked"] is True
