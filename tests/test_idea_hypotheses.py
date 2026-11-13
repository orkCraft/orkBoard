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

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, hypotheses, idea_target, ideas, library, opportunity_tree as tree


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


def test_at_most_three_are_taken_the_riskiest_first_and_one_already_kept_is_not_kept_again(host, product, model):
    keep_tree(host)
    hypotheses.add(host.ideas.state_dir, "They would pay for it", "a card is out", by="person")
    model.answer = {"hypotheses": [hyp("They would pay for it"), hyp("One"), hyp("Two"), hyp("Three"), hyp("Four")]}
    _propose(host, product)
    assert [h["text"] for h in _items(host)] == ["They would pay for it", "One", "Two"] and host.ideas.keeper.hypotheses_proposal()["kept"] == 2      # `parse` takes the first three: the one kept already was one of them


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


def test_no_product_party_or_no_call_to_make_is_a_plain_refusal(host, model, monkeypatch):
    with pytest.raises(KeeperError, match="Product has no party here: make it first"):
        host.ideas.keeper.hypotheses_propose()
    _party(host, "Product", "product-manager", ["copywriter"], "product")
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    with pytest.raises(KeeperError, match="spend limit"):
        host.ideas.keeper.hypotheses_propose()
    assert not model.calls and host.ideas.keeper.hypotheses_proposal()["status"] == ""                                          # nothing begun: asked at the next press


# -- spec 133 A: the proposal answers when it holds, each way it is refuted and what changes ---------------------------------------------
