"""Spec 128 D (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md; decisions §206.6): a leader's question says for whom; one another party can answer is not dealt to the
hand, it is *passing* (the snapshot's `passing`) for `PASS_S` seconds, then that party's leader answers it in one cheap call with no tools and the answer is given to the Talk as the
person's would be, marked *answered by* the party. `ideas.pass_take` makes it the person's, `ideas.pass_now` answers it at once; a call that fails, a party that cannot answer, a
question about money, Stop all: the person's. The model call is stubbed (`keeper.call`) and the clock is injected (`keeper.pass_clock`, the watcher off)."""
from __future__ import annotations

import sys
import time

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import idea_pass, idea_questions, ideas
from tests.test_idea_talk import Model, _party, _row, _state, _talk, _wait, card


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    k = h.ideas.keeper
    k.pass_watch = False                                   # the clock is moved by hand: `k.pass_tick(...)`
    k.pass_clock = Clock()
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def parties(host):
    return {"design": _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")}


@pytest.fixture
def model(host):
    return Model(host)


def _round(model, parties, design_q, tech_q=None):
    """Design asks `design_q` (cards), Tech `tech_q` (default: one question for the person); the pass call is answered by `model.pass_said`."""
    model.said[("talk_round", parties["design"])] = {"stance": "d", "for": "d", "against": "d", "questions": design_q, "second_round": False}
    model.said[("talk_round", parties["tech"])] = {"stance": "t", "for": "t", "against": "t", "second_round": False,
                                                    "questions": [card("Which store first?", choices=("App Store", "Google Play"))] if tech_q is None else tech_q}
    model.calls_ask = []

    def passed(_row):
        k = model.host.ideas.keeper
        model.calls_ask.append({"key": getattr(k._tls, "key", ""), "tools": getattr(k._tls, "tools", True), "tier": _row["tier"], "prompt": _row["prompt"]})
        return model.pass_said(model.calls_ask[-1]) if callable(model.pass_said) else model.pass_said
    model.pass_said = {"can": True, "pick": 1, "why": "the map says so"}
    model.said[("ask", "")] = passed


def _wait_pass(host, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if not any(key.startswith("pass:") for key in list(host.ideas.keeper._busy)):
            return
        time.sleep(0.01)
    raise AssertionError("the passing call never ended")


def _record(host, slug):
    return idea_questions.record(host.ideas.state_dir, slug)


FRAMEWORK = card("Which UI framework?", choices=("Preact", "Vanilla"), **{"for": "tech"})


# -- a question says for whom --------------------------------------------------------------------------------------------------------

def test_a_question_carries_for_a_party_and_is_the_persons_by_default():
    asked = idea_questions.card({"ask": "Which?", "choices": ["A", "B"], "pick": 0, "for": "Tech"}, id="x", by="design", leader="l")
    assert asked["for"] == "tech"
    for said in (None, "", "person", "PERSON", "no way: not a slug", 3):
        plain = idea_questions.card({"ask": "Which?", "choices": ["A", "B"], "pick": 0, **({} if said is None else {"for": said})}, id="x", by="design", leader="l")
        assert "for" not in plain and idea_questions.for_of({"for": said}) == "person"


def test_money_safety_and_what_cannot_be_undone_are_the_persons_whatever_for_says():
    parties = {"design": "Design", "tech": "Tech"}
    ok = {"id": "c", "by": "design", "q": "Which UI framework?", "choices": ["Preact", "Vanilla"], "why": "", "for": "tech", "project": False}
    assert idea_pass.target_of(ok, parties) == "tech" and idea_pass.target_of({**ok, "for": "Tech"}, parties) == "tech"
    for q in ("What is the budget for hosting?", "Delete the old accounts?", "Store the password in the clear?", "Is this irreversible?", "Charge users a subscription?"):
        assert idea_pass.person_only({**ok, "q": q}) and idea_pass.target_of({**ok, "q": q}, parties) == ""
    assert idea_pass.target_of({**ok, "for": "design"}, parties) == "" and idea_pass.target_of({**ok, "for": "ghosts"}, parties) == ""        # itself, a party that is none
    assert idea_pass.target_of({**ok, "project": True}, parties) == ""                                                                      # a project question is kept as a fact: the person's


# -- passing ---------------------------------------------------------------------------------------------------------------------------

def test_a_question_for_tech_from_design_is_passing_not_in_the_hand(host, parties, model):
    _round(model, parties, [FRAMEWORK])
    slug = _talk(host, parties, ["design", "tech"])
    row = _row(host, slug, "talk")
    assert [q["q"] for q in row["questions"]] == ["Which store first?"]                         # the hand has Tech's own question for the person alone
    rec = _record(host, slug)
    assert [c["q"] for c in rec["passing"]] == ["Which UI framework?"] and rec["passing"][0]["to"] == parties["tech"] and rec["passing"][0]["by"] == parties["design"]
    passing = host.ideas.snapshot()["passing"]
    assert passing == [{"id": f"{slug}~{rec['passing'][0]['id']}", "idea": slug, "task": "", "by": parties["design"], "to": parties["tech"], "q": "Which UI framework?",
                        "left_s": idea_pass.PASS_S, "answering": False}]
    host.ideas.keeper.pass_clock.now += 4
    assert host.ideas.snapshot()["passing"][0]["left_s"] == idea_pass.PASS_S - 4
    assert not model.steps("ask")                                                              # nothing is asked before the wait is over


def test_after_the_wait_the_party_answers_in_one_cheap_call_and_it_is_applied_as_a_persons_would_be(host, parties, model):
    _round(model, parties, [FRAMEWORK])
    slug = _talk(host, parties, ["design", "tech"])
    k = host.ideas.keeper
    k.pass_clock.now += idea_pass.PASS_S - 1
    k.pass_tick()
    assert not model.steps("ask") and host.ideas.snapshot()["passing"]
    k.pass_clock.now += 1
    k.pass_tick()
    _wait_pass(host)
    (call,) = model.steps("ask")
    assert call["tools"] is False and call["tier"] == "warrior" and model.calls_ask[0]["key"] == f"goal:{parties['tech']}"        # the cheaper tier, no tools, as the party
    assert "Which UI framework?" in call["prompt"] and "Vanilla" in call["prompt"] and "Read no file" in call["prompt"]
    assert host.ideas.snapshot()["passing"] == []
    rec = _record(host, slug)
    assert rec["passing"] == [] and [(a["q"], a["answer"], a["how"], a["answered_by"], a["by"]) for a in rec["answers"]] == [
        ("Which UI framework?", "Vanilla", "pick", parties["tech"], parties["design"])]
    assert any("answered for you" in t["text"] and "Vanilla" in t["text"] for t in ideas.talk(host.ideas.state_dir, slug))
    talk = idea_questions.talk_of(host.ideas.state_dir, slug)
    answered = [q for s in talk["stances"] for q in s["questions"] if q["state"] == "answered"]
    assert [(q["answer"], q["answered_by"]) for q in answered] == [("Vanilla", parties["tech"])]
    assert [q["q"] for q in _row(host, slug, "talk")["questions"]] == ["Which store first?"] and _state(host, slug)["state"] == "talk"      # the person's card still waits
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": _row(host, slug, "talk")["questions"][0]["id"], "pick": 0}]})         # …and answering it goes on
    _wait(host, slug)
    assert _state(host, slug)["state"] != "talk" or _row(host, slug, "talk") is None
    assert {a["q"] for a in _record(host, slug)["answers"]} == {"Which UI framework?", "Which store first?"}


def test_pass_take_makes_it_the_persons_at_once_and_no_call_is_made(host, parties, model):
    _round(model, parties, [FRAMEWORK])
    slug = _talk(host, parties, ["design", "tech"])
    (row,) = host.ideas.snapshot()["passing"]
    assert host.command("ideas.pass_take", {"id": row["id"]}) == {"ok": True}
    assert host.ideas.snapshot()["passing"] == []
    assert sorted(q["q"] for q in _row(host, slug, "talk")["questions"]) == ["Which UI framework?", "Which store first?"]                  # dealt to the hand as any is
    assert "for" not in next(q for q in _row(host, slug, "talk")["questions"] if q["q"] == "Which UI framework?")
    host.ideas.keeper.pass_clock.now += 60
    host.ideas.keeper.pass_tick()
    assert not model.steps("ask") and not _record(host, slug)["passing"]
    with pytest.raises(CommandError):
        host.command("ideas.pass_take", {"id": row["id"]})                                    # not passing any more


@pytest.mark.parametrize("said", [{"can": False}, {"can": True, "pick": 7}, {"pick": 0}, "not json at all", RuntimeError("the tool failed")], ids=["cannot", "no choice", "no can", "junk", "fails"])
def test_a_party_that_cannot_answer_or_a_call_that_fails_gives_the_question_to_the_person(host, parties, model, said):
    _round(model, parties, [FRAMEWORK])

    def fail(_call):
        if isinstance(said, Exception):
            raise said
        return said
    model.pass_said = fail
    slug = _talk(host, parties, ["design", "tech"])
    host.ideas.keeper.pass_clock.now += idea_pass.PASS_S
    host.ideas.keeper.pass_tick()
    _wait_pass(host)
    rec = _record(host, slug)
    assert rec["passing"] == [] and not any(a.get("answered_by") for a in rec.get("answers") or [])
    assert sorted(q["q"] for q in _row(host, slug, "talk")["questions"]) == ["Which UI framework?", "Which store first?"]                  # one hop: it is not passed again
    assert len(model.steps("ask")) == 1 and host.ideas.snapshot()["passing"] == []


def test_stop_all_stops_a_call_under_way_and_the_question_is_the_persons(host, parties, model):
    _round(model, parties, [FRAMEWORK])
    slug = _talk(host, parties, ["design", "tech"])
    k = host.ideas.keeper

    def slow(_call):
        k.stop_all()                                       # Stop all arrives while the call is out
        return {"can": True, "pick": 0}
    model.pass_said = slow
    k.pass_clock.now += idea_pass.PASS_S
    k.pass_tick()
    _wait_pass(host)
    rec = _record(host, slug)
    assert rec["passing"] == [] and not rec.get("answers") and "Which UI framework?" in [q["q"] for q in _row(host, slug, "talk")["questions"]]

