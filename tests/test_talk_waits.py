"""Spec 168 D0 (decisions §283.25): Talk waits for its leaders' cards. A goal in Talk does not go on to its decision while a `need` of a leader is open, a taken one is not written yet or a fork is
open; a `better` left open does not hold it (an offer, not a question). When the last is answered the leaders are judged again (those it should), and then the decision comes. An old record (no
say) goes on as before. The model call is stubbed as in tests/test_idea_say.py; the decision (part E's seam) is replaced by a recorder."""
from __future__ import annotations

import pytest

from orkboard.realm import idea_questions, idea_say, ideas
from tests.test_idea_say import GOAL, _id, _say_round, _settle, _verdicts  # noqa: F401
from tests.test_idea_talk import Model, _talk, _wait, card, host, model, parties, _round_one  # noqa: F401

NEED = {"kind": "risk", "line": "it may break the old theme", "rests_on": "", "ways": [{"name": "Keep both", "line": "two themes"}, {"name": "Replace", "line": "one theme"}]}


@pytest.fixture
def went(host, monkeypatch):
    sent = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: sent.append(s))
    return sent


def _hearing(host, slug):
    return idea_questions.record(host.ideas.state_dir, slug).get("hearing") is True


def test_talk_waits_while_a_need_is_open_even_for_a_doubt_and_goes_on_when_the_last_is_answered(host, parties, model, went):
    design, tech = parties["design"], parties["tech"]
    _say_round(model, parties, per=0, design={"needs": [NEED]}, tech={"needs": [{**NEED, "kind": "conflict"}], "verdict": "doubt", "why": "not what was asked"})
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    assert idea_say.holding(host.ideas.state_dir, slug) and went == [] and not _hearing(host, slug)             # no decision, and the doubt opens no hearing yet
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "talk"
    model.said[("rewrite", "")] = {"gist": "Rewritten."}
    host.command("ideas.take_way", {"idea": slug, "id": _id(host, slug, design, "n"), "way": 0})
    _settle(host, slug)
    assert went == [] and idea_say.holding(host.ideas.state_dir, slug)                                           # Tech's need is still open
    _verdicts(model, parties, tech={"verdict": "go"})
    host.command("ideas.leave_say", {"idea": slug, "id": _id(host, slug, tech, "n")})
    _settle(host, slug)
    assert model.steps("talk_verdict") and went == [slug] and not _hearing(host, slug)                           # judged again first, then the decision


def test_a_taken_need_waits_for_its_rewrite_and_a_better_left_open_holds_nothing(host, parties, model, went):
    tech = parties["tech"]
    _say_round(model, parties, per=0, tech={"needs": [NEED], "better": [{"line": "say it plainly", "weight": "lighter"}]})
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    ds = host.ideas.state_dir
    assert idea_say.holding(ds, slug) and went == []
    idea_say.take(ds, slug, _id(host, slug, tech, "n"), 0)                                                       # taken, not written: still held
    assert idea_say.holding(ds, slug)
    model.said[("rewrite", "")] = {"gist": "Rewritten."}
    host.ideas.keeper.rewrite(slug)
    _settle(host, slug)
    better = _id(host, slug, tech, "b")
    assert not idea_say.holding(ds, slug) and (idea_say.record(ds, slug)["answers"].get(better) or {}).get("state") is None
    assert went == [slug]                                                                                        # the better is still open and did not hold the decision


def test_an_open_fork_holds_talk(host, parties, model, went):
    ds = host.ideas.state_dir
    _say_round(model, parties, per=0, design={"better": [{"line": "a", "weight": "same"}]}, tech={"better": [{"line": "b", "weight": "same"}]})
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    assert not idea_say.holding(ds, slug) and went == [slug]                                                     # betters alone: the decision came
    say = idea_say.record(ds, slug)
    say["fork"] = {"id": "f-1", "at": "", "ids": [], "card": {"choices": ["x", "y"]}, "answer": None}
    idea_say.save(ds, slug, say)
    assert idea_say.holding(ds, slug)


def test_an_old_record_with_no_say_goes_on_as_before(host, parties, model, went):
    _round_one(model, parties, per=0)
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    assert not idea_say.holding(host.ideas.state_dir, slug) and went == [slug]
    assert idea_say.holding(host.ideas.state_dir, "no-such-goal") is False
