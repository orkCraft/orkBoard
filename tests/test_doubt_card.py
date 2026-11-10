"""Spec 168 D5 (decisions §283.25): a doubt left is a card in the hand. After the leaders judged a goal again once and a leader still doubts or says no, with nothing of its say left to answer, Talk waits for the person
(`core/idea_verdict.py` `say_release` returns there). The Board's row of the goal says so (`say.doubts`: `{party, verdict, why}`, `realm/idea_say.py` `doubts`), and the person has two ways: *Judge again now*
(`ideas.judge_again`) and *To the hearing* (`ideas.to_hearing`: the hearing opens at once, as after the second round; a service, no toast). The card leaves when the goal leaves Talk, is judged again or goes to the hearing. The
model call is stubbed as in tests/test_idea_say.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError
from orkboard.realm import event_log, idea_hearing, idea_questions, idea_say, ideas
from tests.test_idea_say import GOAL, _id, _say_round, _settle, _verdicts  # noqa: F401
from tests.test_idea_talk import Model, _talk, _wait, card, host, model, parties, _round_one  # noqa: F401

WHY = "still not now"


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


NEED = {"kind": "risk", "line": "it may break the old theme", "rests_on": "", "ways": [{"name": "Keep both", "line": "two themes"}, {"name": "Replace", "line": "one theme"}]}


def _spoken(host, parties, model):
    """Three leaders spoke: Product doubts, Design has a need (it holds Talk until it is answered), Tech goes."""
    _say_round(model, parties, per=0, product={"verdict": "doubt", "why": WHY}, design={"needs": [NEED]})
    return _talk(host, parties, ["product", "design", "tech"], GOAL)


@pytest.fixture
def waiting(host, parties, model):
    """The person took Design's way (written into the goal's words): the leaders judged again by themselves once and Product still doubts. Nothing of their say is left: Talk waits for the person. The goal's slug."""
    slug = _spoken(host, parties, model)
    _verdicts(model, parties, product={"verdict": "doubt", "why": WHY}, design={"verdict": "go"}, tech={"verdict": "go"})
    model.said[("rewrite", "")] = {"gist": "Rewritten."}
    host.command("ideas.take_way", {"idea": slug, "id": _id(host, slug, parties["design"], "n"), "way": 0})
    _settle(host, slug)
    return slug


def _doubts(host, slug):
    return idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)["doubts"]


def test_nothing_waits_for_the_person_before_the_leaders_have_judged_again_once(host, parties, model):
    slug = _spoken(host, parties, model)
    ds = host.ideas.state_dir
    assert idea_say.record(ds, slug)["judged"] == 0 and idea_say.doubts(ds, slug) == [] and _doubts(host, slug) == []


def test_a_leader_that_still_doubts_after_one_judging_with_nothing_left_to_answer_is_a_doubt_the_person_holds(host, parties, model, waiting):
    ds = host.ideas.state_dir
    assert idea_say.record(ds, waiting)["judged"] == 1
    assert _doubts(host, waiting) == [{"party": parties["product"], "verdict": "doubt", "why": WHY}] and not idea_hearing.is_open(idea_questions.record(ds, waiting))
    row = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == waiting)
    assert row["say"]["doubts"] == _doubts(host, waiting) and row["state"] == "talk"
    rec = idea_questions.record(ds, waiting)                                                      # a question of the round open again: not the person's yet
    idea_questions.save_record(ds, waiting, {**rec, "waiting": [{"id": "q1", "q": "?"}]})
    assert idea_say.doubts(ds, waiting) == []
    idea_questions.save_record(ds, waiting, rec)
    assert idea_say.doubts(ds, waiting) != []


def test_judging_again_takes_the_card_away_a_doubt_that_is_gone_or_the_hearing_that_follows_a_doubt_that_stays(host, parties, model, waiting):
    ds = host.ideas.state_dir
    _verdicts(model, parties, product={"verdict": "go"})
    host.command("ideas.judge_again", {"idea": waiting})                                          # Product comes round: nothing doubts
    _settle(host, waiting)
    assert idea_say.record(ds, waiting)["judged"] == 2 and _doubts(host, waiting) == []


def test_the_second_judging_that_still_doubts_is_the_hearing_so_no_card(host, parties, model, waiting):
    ds = host.ideas.state_dir
    host.command("ideas.judge_again", {"idea": waiting})                                          # Product still doubts: the second and last
    _settle(host, waiting)
    assert idea_questions.record(ds, waiting).get("hearing") is True and _doubts(host, waiting) == []


def test_to_the_hearing_opens_the_hearing_at_once_and_the_card_is_gone(host, parties, model, waiting):
    ds = host.ideas.state_dir
    n = len(model.steps("talk_verdict"))
    out = host.command("ideas.to_hearing", {"idea": waiting})
    assert out["ok"] and out["idea"] == waiting and out["parties"] == [parties["product"]]
    rec = idea_questions.record(ds, waiting)
    assert rec.get("hearing") is True and idea_hearing.is_open(rec) and idea_say.record(ds, waiting)["judged"] == 1, "the hearing is open and no second judging was made"
    assert len(model.steps("talk_verdict")) == n, "no leader was asked: the person went to the hearing"
    assert _doubts(host, waiting) == [] and [e["parties"] for e in _events(host, event_log.TO_HEARING)] == [[parties["product"]]]
    assert ideas.state(ds, waiting)["state"] == "talk"
    with pytest.raises(CommandError, match="nothing waits for you"):
        host.command("ideas.to_hearing", {"idea": waiting})                                       # the hearing is open: it is not the person's to open again


def test_to_the_hearing_is_refused_in_plain_words_where_nothing_waits_and_for_a_goal_that_is_gone(host, parties, model):
    slug = _spoken(host, parties, model)
    with pytest.raises(CommandError, match="nothing waits for you"):
        host.command("ideas.to_hearing", {"idea": slug})                                          # not judged again once yet
    with pytest.raises(CommandError, match="gone"):
        host.command("ideas.to_hearing", {"idea": "no-such-goal"})
    with pytest.raises(CommandError):
        host.command("ideas.to_hearing", {})
