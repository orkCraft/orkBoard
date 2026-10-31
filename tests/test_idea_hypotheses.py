"""Spec 116 B (docs/specs/116-hypotheses-on-products-tree.md §3) on the keeper: `keeper.hypotheses_propose()`, one call of Product's leader on the step `hypotheses` (the cheaper tier, no
tools, its cost in its party's ledger as *spec*), given its voice, the tree's text, the jobs' ids, the common facts, the project's stage and what the leaders assumed (the *Defaults* of the
goals in line and at work, ten at most, the newest first). The answer is kept `proposed`, `by: "leader"`; past the bounds it stops and says so; a call that fails keeps nothing; one is
never asked while one is being asked. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

from orkboard.core import idea_hypotheses
from orkboard.core.idea_hypotheses import HypothesesMixin
from orkboard.core.idea_keeper import IdeaKeeper, KeeperError
from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, hypotheses, idea_spend, idea_target, ideas, library, opportunity_tree as tree, project_facts, project_stage


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def product(host):
    return _party(host, "Product", "product-manager", ["copywriter"], "product")


def job(want, when="I start a new project", so="judge the idea", segment="solo founders"):
    return {"when": when, "want": want, "so": so, "segment": segment}


def keep_tree(host):
    tree.keep(host.ideas.state_dir, [{"text": "Cut the time to a first sketch from ten minutes to two"}], [job("see a sketch"), job("share it with a friend"), job("compare two versions")], "person")


def hyp(text, signal="people come back twice in a week", **more):
    return {"text": text, "signal": signal, **more}


ANSWER = {"hypotheses": [hyp("Solo founders want a sketch before a spec", axis="desirable", on="see-a-sketch"), hyp("A sketch is easy to build", axis="feasible"), hyp("They would pay for it", axis="viable")]}


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer = host, [], ANSWER if answer is None else answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", "")})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy_goal(party):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _propose(host, party):
    got = host.ideas.keeper.hypotheses_propose()
    _wait(host, party)
    return got


def _items(host):
    return hypotheses.read(host.ideas.state_dir)["items"]


def _goal(host, title, defaults="", state="", mtime=None):
    """A goal with a section of the party `Product` holding `defaults` (lines) under *Defaults*."""
    root = host.ideas.root()
    slug = ideas.add_idea(root, title, "general", host.ideas.state_dir)
    if defaults:
        page = ideas.idea_page(root, slug)
        page.sections.append(("Product", "### Why\nBecause.\n\n### Defaults\n" + "\n".join(f"- {d}" for d in defaults)))
        ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    if state:
        ideas.save_state(host.ideas.state_dir, slug, state=state)
    if mtime is not None:
        os.utime(root / ideas.IDEAS / f"{slug}.md", (mtime, mtime))
    return slug


# -- the call: Product's leader, the cheaper tier, no tools, the tree, the facts, the stage and what the leaders assumed ----------------------

def test_the_proposal_is_one_call_of_products_leader_on_the_cheaper_tier_with_no_tools(host, product, model):
    keep_tree(host)
    assert _propose(host, product) is True
    (call,) = model.calls
    assert call["step"] == "hypotheses" and call["tools"] is False and call["key"] == f"goal:{product}"
    assert (call["tier"], call["effort"]) == idea_target.pick("hypotheses", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("hypotheses", "balance")
    assert call["prompt"].startswith("You are Product manager, the leader of this goal's party") and "Read no file" in call["prompt"]
    assert '"hypotheses"' in call["prompt"] and "3 at most" in call["prompt"] and "riskiest first" in call["prompt"]


def test_the_step_is_as_the_trees_on_the_cheaper_tier_in_the_specs_stage_of_its_partys_ledger(host, product, model):
    keep_tree(host)
    _propose(host, product)
    spent = idea_spend.of_goal(host.ideas.state_dir, product)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01
    assert idea_spend.STEP_STAGE["hypotheses"] == "spec" and "hypotheses" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("hypotheses", target) == idea_target.pick("tree", target)
    assert idea_target.READS["hypotheses"] == 0 and idea_target.CONTEXT["hypotheses"] == idea_target.CONTEXT["tree"] and idea_target.CAPS["hypotheses"] == idea_target.CAPS["tree"] <= 0.15


def test_the_call_is_given_the_tree_the_facts_the_stage_and_the_defaults_the_leaders_assumed(host, product, model):
    keep_tree(host)
    hypotheses.add(host.ideas.state_dir, "Founders have no designer", "three of five say so", by="person")
    project_facts.keep(host.ideas.state_dir, product, "for_whom", "Solo founders with no designer", "person")
    project_stage.keep(host.ideas.state_dir, "being_made")
    got = _goal(host, "Share a sketch by link", ["Anyone with the link may look — assumed that sharing is safe by default"])
    _propose(host, product)
    p = model.calls[0]["prompt"]
    assert "Hypothesis (open): Founders have no designer — we'll know when three of five say so" in p                        # the tree's text holds the hypotheses
    assert "see-a-sketch: job" in p and "Cut the time to a first sketch" in p                                              # the jobs' ids, for `on`
    assert "Solo founders with no designer" in p                                                                           # the common facts
    assert "The project's stage:\nbeing made" in p
    assert f"- {got} (Share a sketch by link)" in p and "Anyone with the link may look" in p                                  # what the leaders assumed, the goal's name before it


def test_the_defaults_are_those_of_goals_in_line_and_at_work_ten_at_most_the_newest_first(host, product, model):
    keep_tree(host)
    now = time.time()
    for n in range(12):
        _goal(host, f"Goal {n:02d}", [f"default {n:02d}"], mtime=now - 1000 + n)                                         # goal 11 is the newest
    done = _goal(host, "Done goal", ["default done"], state="done")
    work = _goal(host, "Goal at work", ["default work"], state="working", mtime=now + 10)
    _goal(host, "No defaults")
    _propose(host, product)
    p = model.calls[0]["prompt"]
    lines = [ln for ln in p.split("What the leaders assumed")[1].split("\n") if ln.startswith("  - ")]
    assert lines == ["  - Product: default work"] + [f"  - Product: default {n:02d}" for n in range(11, 2, -1)]               # ten, the newest first, at work counted
    assert "default done" not in p and done not in p and f"- {work} (Goal at work)" in p and "default 02" not in p
    assert "(none)" not in p.split("What the leaders assumed")[1] and "Goal 02" not in p


def test_with_no_defaults_the_leader_is_told_none_and_at_the_stage_idea_with_none_kept_it_is_asked_for_an_axis_each(host, product, model):
    keep_tree(host)
    project_stage.keep(host.ideas.state_dir, "idea")
    _propose(host, product)
    p = model.calls[0]["prompt"]
    assert "(none)" in p.split("What the leaders assumed")[1] and "one for each axis that matters most" in p and "desirable, viable, feasible, usable" in p
    hypotheses.add(host.ideas.state_dir, "Founders have no designer", "three of five say so", by="person")
    _propose(host, product)
    assert "one for each axis" not in model.calls[1]["prompt"]                                                              # one is kept: the riskiest only
    project_stage.keep(host.ideas.state_dir, "live")
    for h in _items(host):
        hypotheses.drop(host.ideas.state_dir, h["id"])
    _propose(host, product)
    assert "one for each axis" not in model.calls[2]["prompt"] and "The project's stage:\nlive" in model.calls[2]["prompt"]       # only the stage idea asks for an axis each


def test_a_project_with_no_tree_is_still_asked_and_told_so(host, product, model):
    _propose(host, product)
    assert tree.NOTHING in model.calls[0]["prompt"] and len(_items(host)) == 3


# -- what is kept ---------------------------------------------------------------------------------------------------------------------------

def test_the_proposal_is_kept_proposed_by_the_leader_for_its_party_and_the_status_says_so(host, product, model):
    keep_tree(host)
    assert host.ideas.keeper.hypotheses_proposal()["status"] == ""
    _propose(host, product)
    got = _items(host)
    assert [h["text"] for h in got] == ["Solo founders want a sketch before a spec", "A sketch is easy to build", "They would pay for it"]                    # the leader's order: riskiest first
    assert {(h["state"], h["by"], h["party"]) for h in got} == {("proposed", "leader", product)}
    assert [(h["axis"], h["on"]) for h in got] == [("desirable", "see-a-sketch"), ("feasible", ""), ("viable", "")] and all(h["signal"] and h["at"] for h in got)
    status = host.ideas.keeper.hypotheses_proposal()
    assert status["status"] == "done" and status["kept"] == 3 and status["error"] == "" and status["at"]
    assert tree.read(host.ideas.state_dir)["jobs"] and hypotheses.read(host.ideas.state_dir)["items"] == got               # the tree's record and the items are left as they were


def test_an_on_that_is_none_of_the_trees_and_a_goal_not_given_are_left_out_and_a_goal_given_is_kept(host, product, model):
    keep_tree(host)
    mine = _goal(host, "Share a sketch by link", ["assumed that sharing is safe"])
    model.answer = {"hypotheses": [hyp("One", on="no-such-job", rests=["no-such-goal", mine])]}
    _propose(host, product)
    (only,) = _items(host)
    assert (only["on"], only["rests"]) == ("", [mine])


def test_an_outcome_or_a_job_of_the_tree_is_a_place_a_hypothesis_may_be_on(host, product, model):
    keep_tree(host)
    outcome = tree.read(host.ideas.state_dir)["outcomes"][0]["id"]
    model.answer = {"hypotheses": [hyp("One", on=outcome), hyp("Two", on="see-a-sketch")]}
    _propose(host, product)
    assert [h["on"] for h in _items(host)] == [outcome, "see-a-sketch"]


def test_at_most_three_are_taken_the_riskiest_first_and_one_already_kept_is_not_kept_again(host, product, model):
    keep_tree(host)
    hypotheses.add(host.ideas.state_dir, "They would pay for it", "a card is out", by="person")
    model.answer = {"hypotheses": [hyp("They would pay for it"), hyp("One"), hyp("Two"), hyp("Three"), hyp("Four")]}
    _propose(host, product)
    assert [h["text"] for h in _items(host)] == ["They would pay for it", "One", "Two"] and host.ideas.keeper.hypotheses_proposal()["kept"] == 2      # `parse` takes the first three: the one kept already was one of them


def test_a_proposal_past_the_bounds_stops_adding_and_says_why(host, product, model):
    keep_tree(host)
    for n in range(hypotheses.MAX_PROPOSED - 1):
        hypotheses.add(host.ideas.state_dir, f"Waiting {n}", "a signal", by="leader", party=product)
    assert host.ideas.keeper.hypotheses_room() == 1
    _propose(host, product)                                                                                                   # the leader is told it may name one: only one is kept
    assert len(_items(host)) == hypotheses.MAX_PROPOSED and host.ideas.keeper.hypotheses_proposal() | {"at": ""} == {"status": "done", "error": "", "kept": 1, "at": ""}
    assert "1 at most" in model.calls[0]["prompt"]
    model.answer = {"hypotheses": [hyp("A"), hyp("B")]}                                                                       # a leader that names more than it was told: the bound stops it
    for h in _items(host)[-3:]:
        hypotheses.drop(host.ideas.state_dir, h["id"])
    hypotheses.add(host.ideas.state_dir, "Waiting x", "s", by="leader", party=product)
    assert host.ideas.keeper.hypotheses_room() == 2
    with_room = len(_items(host))
    _propose(host, product)
    assert len(_items(host)) == with_room + 2


def test_a_bound_reached_in_the_middle_keeps_what_fitted_and_says_why_with_none_kept_it_is_failed(host, product, model, monkeypatch):
    keep_tree(host)
    real = hypotheses.add
    seen = []

    def stingy(*a, **k):
        if len(seen) >= 1:
            raise ValueError("12 hypotheses are waiting to be kept: keep or drop some first")
        seen.append(1)
        return real(*a, **k)

    monkeypatch.setattr(hypotheses, "add", stingy)
    _propose(host, product)
    status = host.ideas.keeper.hypotheses_proposal()
    assert len(_items(host)) == 1 and (status["status"], status["kept"]) == ("done", 1) and status["error"] == "12 hypotheses are waiting to be kept: keep or drop some first"
    monkeypatch.setattr(hypotheses, "add", lambda *a, **k: (_ for _ in ()).throw(ValueError("40 hypotheses are kept: drop one first")))
    _propose(host, product)
    status = host.ideas.keeper.hypotheses_proposal()
    assert (status["status"], status["kept"], status["error"]) == ("failed", 0, "40 hypotheses are kept: drop one first") and len(_items(host)) == 1


def test_with_no_room_nothing_is_asked_and_it_is_said_in_plain_words(host, product, model):
    keep_tree(host)
    for n in range(hypotheses.MAX_OPEN):
        hypotheses.add(host.ideas.state_dir, f"Open {n}", "a signal", by="person")
    with pytest.raises(KeeperError, match="7 hypotheses are open or being tested already: judge or drop one before another is proposed"):
        host.ideas.keeper.hypotheses_propose()
    assert not model.calls and host.ideas.keeper.hypotheses_proposal()["status"] == ""


# -- a call that fails ---------------------------------------------------------------------------------------------------------------------

def test_a_call_that_does_not_answer_is_tried_once_more_keeps_nothing_and_says_why(host, product):
    keep_tree(host)
    model = Model(host, "not json at all")
    _propose(host, product)
    assert len(model.calls) == 2                                                                                              # one more try
    status = host.ideas.keeper.hypotheses_proposal()
    assert status["status"] == "failed" and "did not answer" in status["error"] and status["kept"] == 0 and _items(host) == []
    for bad in ({"hypotheses": []}, {"hypotheses": "no"}, {"hypotheses": [{"text": "no signal"}]}, {"hypotheses": [hyp("x" * 5, axis="loud")]}, {"other": 1}, []):    # strictly
        model.answer = bad
        _propose(host, product)
        assert host.ideas.keeper.hypotheses_proposal()["status"] == "failed" and _items(host) == []
    model.answer = ANSWER
    assert _propose(host, product) is True and host.ideas.keeper.hypotheses_proposal()["status"] == "done" and len(_items(host)) == 3


def test_a_stop_forgets_the_proposal_and_keeps_nothing(host, product):
    keep_tree(host)

    def stopped(call):
        raise InterruptedError()

    Model(host, stopped)
    _propose(host, product)
    assert host.ideas.keeper.hypotheses_proposal()["status"] == "" and _items(host) == []


def test_a_call_lost_with_the_process_is_not_asking_and_is_asked_again(host, product, model):
    idea_hypotheses.save_proposal(host.ideas.state_dir, "asking")                                                             # the record of a run that died
    assert host.ideas.keeper.hypotheses_proposal()["status"] == ""
    assert _propose(host, product) is True and len(model.calls) == 1


# -- asked on a press, never twice while asking -------------------------------------------------------------------------------------------

def test_a_proposal_being_asked_is_not_asked_a_second_time_and_one_done_may_be_asked_again(host, product):
    keep_tree(host)
    seen = {}

    def slow(call):
        seen["status"] = host.ideas.keeper.hypotheses_proposal()["status"]
        seen["again"] = host.ideas.keeper.hypotheses_propose()
        return ANSWER

    model = Model(host, slow)
    _propose(host, product)
    assert seen == {"status": "asking", "again": False} and len(model.calls) == 1 and len(_items(host)) == 3
    model.answer = {"hypotheses": [hyp("A fourth")]}
    assert _propose(host, product) is True and len(model.calls) == 2 and len(_items(host)) == 4


def test_nothing_is_asked_unasked(host, product, model):
    keep_tree(host)
    _goal(host, "Share a sketch by link", ["assumed"])
    host.ideas.keeper.assumed_text()
    host.ideas.keeper.hypotheses_prompt(product, 3)
    assert not model.calls and host.ideas.keeper.hypotheses_proposal()["status"] == ""


def test_no_product_party_or_no_call_to_make_is_a_plain_refusal(host, model, monkeypatch):
    with pytest.raises(KeeperError, match="Product has no party here: make it first"):
        host.ideas.keeper.hypotheses_propose()
    _party(host, "Product", "product-manager", ["copywriter"], "product")
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    with pytest.raises(KeeperError, match="spend limit"):
        host.ideas.keeper.hypotheses_propose()
    assert not model.calls and host.ideas.keeper.hypotheses_proposal()["status"] == ""                                          # nothing begun: asked at the next press


def test_the_mixin_is_a_base_of_the_keeper_and_the_status_is_kept_beside_the_items_without_hiding_them(host, product):
    assert issubclass(IdeaKeeper, HypothesesMixin)
    hypotheses.add(host.ideas.state_dir, "Founders have no designer", "three of five say so", by="person")
    idea_hypotheses.save_proposal(host.ideas.state_dir, "failed", "A reason", 2)
    assert [h["text"] for h in _items(host)] == ["Founders have no designer"]
    hypotheses.add(host.ideas.state_dir, "Another", "a signal", by="person")                                                   # the record keeps what it does not know
    assert idea_hypotheses.proposal(host.ideas.state_dir)["status"] == "failed" and idea_hypotheses.proposal(host.ideas.state_dir)["kept"] == 2
    idea_hypotheses.save_proposal(host.ideas.state_dir, "")
    assert idea_hypotheses.proposal(host.ideas.state_dir)["status"] == "" and len(_items(host)) == 2
