"""Spec 120 B and C (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §2.3–§2.4, §3.1–§3.2) on the keeper: each leader marked heard as it answers; Product weighing a goal it is not routed on (a
verdict and a priority, no question, no section); `priority` and `risk` taken from a round's answer and dropped out of their sets; the leaders who doubted, said no or saw their pick overridden heard
again after the person's answers (step `talk_verdict`), nobody when no card was asked, a leader in the second round heard once. The model call is stubbed (`keeper.call`), as in tests/test_idea_talk.py."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from orkboard.realm import idea_objections, event_log, idea_questions, idea_target, ideas
from tests.test_idea_talk import TECH_NO, Model, _noes, _round_one, _row, _state, _talk, _wait, card, host, model, parties  # noqa: F401  (the fixtures and the helpers of Talk's tests)


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def _objections(host, slug):
    """The leaders' noes still unanswered, while the goal's hearing row is in Needs you (spec 120 D: one row a goal, in place of a row a no)."""
    rows = [n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == "hearing"]
    return idea_objections.pending(_record(host, slug)) if rows else []


def _record(host, slug):
    return idea_questions.record(host.ideas.state_dir, slug)


def _stance(host, slug, party):
    return next(s for s in _record(host, slug)["stances"] if s["party"] == party)


def _answer(host, slug, picks):
    """The person answers the cards waiting: `picks` is one pick for every card, or `{the card's question: a pick | {"text": …}}` (a card not named takes pick 0)."""
    def one(c: dict) -> dict:
        got = picks.get(c["q"], 0) if isinstance(picks, dict) else picks
        return {"id": c["id"], **(got if isinstance(got, dict) else {"pick": got})}

    host.command("ideas.talk_answer", {"idea": slug, "answers": [one(c) for c in _row(host, slug, "talk")["questions"]]})
    _wait(host, slug)


# -- priority and risk, taken strictly -----------------------------------------------------------------------------------------------------


def _slug_of(host):
    return next(i["slug"] for i in ideas.ideas(host.ideas.root()) if _state(host, i["slug"])["state"] == "talk")


def test_the_priority_and_the_risk_are_kept_with_the_stances_and_make_the_weight(host, parties, model):
    _round_one(model, parties, priority="high", risk="medium")                                                              # every leader says both; only its own counts
    slug = _talk(host, parties, ["product", "design", "tech"])
    rec = _record(host, slug)
    assert [(s["party"], s["priority"], s["risk"]) for s in rec["stances"]] == [(parties["product"], "high", ""), (parties["design"], "", ""), (parties["tech"], "", "medium")]
    assert rec["weight"] == {"priority": "high", "risk": "medium"}


# -- heard as it goes ---------------------------------------------------------------------------------------------------------------------------


# -- Product weighs every goal -----------------------------------------------------------------------------------------------------------------

@pytest.mark.weighs
def test_product_weighs_a_goal_it_is_not_routed_on_with_a_verdict_and_a_priority_and_asks_nothing(host, parties, model):
    _round_one(model, parties, per=1)
    model.said[("talk_round", parties["product"])] = {"verdict": "doubt", "why": "Is it worth it before the lobby?", "instead": "Only the setting", "priority": "low",
                                                      "stance": "must not be read", "questions": [card("a question of Product's")], "second_round": True}
    slug = _talk(host, parties, ["tech"])
    calls = model.steps("talk_round")
    assert sorted(c["party"] for c in calls) == sorted([parties["tech"], parties["product"]]) and all(c["tools"] is False for c in calls)
    weigh = next(c for c in calls if c["party"] == parties["product"])["prompt"]
    assert "not routed to your party" in weigh and "weigh it against the goals in line" in weigh and "Read no file" in weigh
    assert '"priority"' in weigh and '"questions"' not in weigh and "Ask nothing" in weigh                              # no question, no stance, no section later
    assert '"verdict"' not in weigh and '"instead"' not in weigh and "weigh only" in weigh                              # it weighs: no go, doubt or no (spec 155 E)
    assert (_state(host, slug)["route"]) == [{"party": parties["tech"], "leader": "architect"}]                          # it is not on the route
    rec = _record(host, slug)
    assert [(s["party"], s["weigher"]) for s in rec["stances"]] == [(parties["tech"], False), (parties["product"], True)]
    weigher = rec["stances"][1]
    assert (weigher["verdict"], weigher["why"], weigher["instead"], weigher["priority"], weigher["stance"], weigher["craft"]) == (
        "go", "Is it worth it before the lobby?", "", "low", "", "product")                                             # its doubt opens nothing (spec 155 E)
    assert not rec.get("hearing") and rec["objections"] == [] and _row(host, slug, "talk") is not None
    assert [c["by"] for c in rec["waiting"]] == [parties["tech"]] and rec["second"] == []                              # its question and its second round were never taken
    assert rec["weight"]["priority"] == "low" and sorted(rec["heard"]) == sorted([parties["tech"], parties["product"]])
    (told,) = [e for e in _events(host, event_log.TALK_HEARD) if e["weigher"] is True]
    assert told["party"] == parties["product"]


@pytest.mark.weighs
def test_product_on_the_route_is_a_leader_not_a_weigher_and_the_short_way_has_none(host, parties, model):
    _round_one(model, parties)
    slug = _talk(host, parties, ["product", "tech"])
    assert [s["weigher"] for s in _record(host, slug)["stances"]] == [False, False] and len(model.steps("talk_round")) == 2
    k = host.ideas.keeper
    assert k.weighers(slug) == []                                                                                      # Product is on its route
    other = host.command("ideas.add", {"text": "add a light mode option", "track": parties["tech"]})["slug"]
    assert k.weighers(other) == [{"party": parties["product"], "leader": "product-manager", "weigher": True}]
    ideas.save_state(host.ideas.state_dir, other, route_how={**_state(host, other)["route_how"], "short": True})        # a bug, a tidy, a balance pass
    assert k.weighers(other) == []


# -- the leaders heard again after the answers ------------------------------------------------------------------------------------------------

def _decide_stub(host, monkeypatch):
    went: list = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s))
    return went


def _hearing(host, slug):
    """The goal's hearing, once Talk has opened it (spec 120 §3.4: a doubt alone is a hearing too)."""
    for _ in range(500):
        if got := host.command("ideas.hearing", {"idea": slug}):
            return got
        time.sleep(0.01)
    raise AssertionError("no hearing opened")


def _gone(went: list, n: int = 1) -> list:
    """The decision is asked once the keeper has ended its run (the goal goes on after it): wait for the stub to be called."""
    for _ in range(300):
        if len(went) >= n:
            break
        time.sleep(0.01)
    return went


def test_a_leader_who_doubted_is_heard_again_after_the_answers_the_others_verdicts_stand(host, parties, model, monkeypatch):
    _noes(model, parties, per=1, design={"verdict": "doubt", "why": "The contrast is low"}, product={"priority": "high"})
    model.said[("talk_verdict", parties["design"])] = {"verdict": "go", "why": "", "priority": "low"}                  # a leader's verdict, the answers in
    went = _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["product", "design", "tech"])
    _answer(host, slug, 0)                                                                                            # every card by its leader's own pick
    again = model.steps("talk_verdict")
    assert [c["party"] for c in again] == [parties["design"]] and len(model.steps("talk_round")) == 3                  # only the doubt; the others are not asked again
    call = again[0]
    assert call["tools"] is False and (call["tier"], call["effort"]) == idea_target.pick("talk_verdict", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("talk_verdict", "balance")
    assert "You are" in call["prompt"] and "Read no file" in call["prompt"] and "judge it again" in call["prompt"]
    assert "Verdict: doubt" in call["prompt"] and "Why: The contrast is low" in call["prompt"] and "Stance: design stance" in call["prompt"]       # its first answer
    assert "design question 0 — A" in call["prompt"] and "product question 0 — A" in call["prompt"]                      # and the answers
    assert '"priority"' not in call["prompt"] and '"verdict": "go"' in call["prompt"]
    design = _stance(host, slug, parties["design"])
    assert (design["verdict"], design["why"], design["priority"]) == ("go", "", "") and _stance(host, slug, parties["product"])["priority"] == "high"        # Design gives no priority; Product's stands
    assert _stance(host, slug, parties["product"])["verdict"] == "go" and _record(host, slug)["done"] is True and _gone(went) == [slug] and _record(host, slug)["again"] == []
    (changed,) = _events(host, event_log.TALK_VERDICT)
    assert (changed["idea"], changed["party"], changed["before"], changed["after"]) == (slug, parties["design"], "doubt", "go")
    assert _state(host, slug)["measure"]["step"] == "talk_round" and _state(host, slug)["measure"]["cost"] == 0.04        # the calls of the verdict are in the Talk's measure


def test_a_leader_whose_pick_was_overridden_is_heard_again_one_whose_pick_was_taken_is_not(host, parties, model, monkeypatch):
    _noes(model, parties, per=1)
    model.said[("talk_verdict", parties["tech"])] = {"verdict": "doubt", "why": "Now I am not sure"}
    went = _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["product", "design", "tech"])
    _answer(host, slug, {"product question 0": 0, "design question 0": 1, "tech question 0": {"text": "something of my own"}})        # Product by its pick; Design another choice; Tech its own words
    _hearing(host, slug)                                                                                                    # Tech now doubts: a hearing, thrown to *Do it*
    host.command("ideas.throw", {"idea": slug, "moment": "talk", "dir": "right"})
    assert sorted(c["party"] for c in model.steps("talk_verdict")) == sorted([parties["design"], parties["tech"]]) and _gone(went) == [slug]
    assert _stance(host, slug, parties["tech"])["verdict"] == "doubt" and _stance(host, slug, parties["tech"])["why"] == "Now I am not sure"
    assert [(e["party"], e["before"], e["after"]) for e in _events(host, event_log.TALK_VERDICT)] == [(parties["design"], "go", "go"), (parties["tech"], "go", "doubt")] and "something of my own" in next(
        c for c in model.steps("talk_verdict") if c["party"] == parties["tech"])["prompt"]


def test_a_no_that_the_answers_took_back_is_no_objection_and_one_already_answered_is_kept(host, parties, model, monkeypatch):
    _noes(model, parties, per=1, product={"verdict": "no", "why": "Not worth it"}, tech={"verdict": "no", "why": "A third caller", "instead": "Only the setting"})
    model.said[("talk_verdict", parties["product"])] = {"verdict": "go"}
    model.said[("talk_verdict", parties["tech"])] = {"verdict": "no", "why": "Still a third caller", "instead": "Only the setting"}
    went = _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["product", "tech"])
    assert [o["party"] for o in _objections(host, slug)] == [parties["product"], parties["tech"]]
    host.command("ideas.objection", {"idea": slug, "party": parties["tech"], "answer": "go"})                           # the person went on against Tech's no
    _answer(host, slug, 0)
    rec = _record(host, slug)
    assert [(o["party"], o["answer"]) for o in rec["objections"]] == [(parties["tech"], "go")] and _objections(host, slug) == []
    assert _stance(host, slug, parties["tech"])["why"] == "Still a third caller" and _stance(host, slug, parties["product"])["verdict"] == "go"
    assert _gone(went) == [slug]                                                                                       # nothing left unanswered: the decision goes on


# -- the route edited while Talk runs (spec 120 §2.2) ---------------------------------------------------------------------------------------

def test_a_party_put_on_the_route_while_the_leaders_are_heard_is_heard_alone_and_one_taken_off_is_dropped(host, parties, model):
    import threading
    _round_one(model, parties, per=1)
    release, began = threading.Event(), threading.Event()

    def tech(row):
        began.set()
        release.wait(10)                                               # Tech is slow: the round is being heard when the route is edited
        return {"stance": "tech stance", "questions": [card("tech question 0")]}

    model.said[("talk_round", parties["tech"])] = tech
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["product"]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties["product"], parties["tech"]]})
    host.command("ideas.talk", {"idea": slug})
    assert began.wait(10)
    for _ in range(300):                                               # Product has answered by now
        if parties["product"] in _record(host, slug).get("heard", []):
            break
        time.sleep(0.01)
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})       # Product taken off, Design put on
    assert got["changed"] is False and _row(host, slug, "start") is None                                          # Talk's own edit: no step added after it
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["tech"], parties["design"]] and _state(host, slug)["route_how"]["said_route"] == _state(host, slug)["route"]
    release.set()
    _wait(host, slug)
    rec = _record(host, slug)
    assert [s["party"] for s in rec["stances"]] == [parties["tech"], parties["design"]] and sorted(rec["heard"]) == sorted([parties["tech"], parties["design"]])
    assert [c["by"] for c in rec["waiting"]] == [parties["tech"], parties["design"]]                              # Product's answer and its cards are dropped
    assert len([c for c in model.steps("talk_round") if c["party"] == parties["design"]]) == 1                    # Design, heard alone: one call
    assert len([c for c in model.steps("talk_round") if c["party"] == parties["tech"]]) == 1 and _state(host, slug)["state"] == "talk"


def test_a_party_put_on_or_taken_off_while_the_person_answers_is_heard_alone_or_dropped_with_its_cards(host, parties, model):
    _round_one(model, parties, per=1)
    slug = _talk(host, parties, ["product", "design"])
    assert [c["by"] for c in _row(host, slug, "talk")["questions"]] == [parties["product"], parties["design"]]
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["design"], parties["tech"]]})         # Product off, Tech on
    assert got["changed"] is False and _row(host, slug, "start") is None
    _wait(host, slug)
    rec = _record(host, slug)
    assert [s["party"] for s in rec["stances"]] == [parties["design"], parties["tech"]] and sorted(rec["heard"]) == sorted([parties["design"], parties["tech"]])
    assert [c["by"] for c in rec["waiting"]] == [parties["design"], parties["tech"]] and rec["done"] is False
    assert len([c for c in model.steps("talk_round") if c["party"] == parties["tech"]]) == 1                      # Tech, heard alone
    assert len([c for c in model.steps("talk_round") if c["party"] == parties["product"]]) == 1                   # Product is not called again
    assert [q["q"] for q in _row(host, slug, "talk")["questions"]] == ["design question 0", "tech question 0"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"]]})                                   # Design off too: its card goes
    assert [s["party"] for s in _record(host, slug)["stances"]] == [parties["tech"]] and [c["by"] for c in _record(host, slug)["waiting"]] == [parties["tech"]]
    assert len(model.steps("talk_round")) == 3


def test_an_edit_once_talk_is_done_is_a_step_added_after_it_as_it_was(host, parties, model, monkeypatch):
    _noes(model, parties, per=0, tech=TECH_NO)
    _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["tech"])                                                                         # no card to ask, a no to answer: Talk is done
    assert _record(host, slug)["done"] is True
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})
    assert got["changed"] is True and _row(host, slug, "start") is not None and len(model.steps("talk_round")) == 1


