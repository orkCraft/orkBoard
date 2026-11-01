"""Spec 120 B and C (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §2.3–§2.4, §3.1–§3.2) on the keeper: each leader marked heard as it answers; Product weighing a goal it is not routed on (a
verdict and a priority, no question, no section); `priority` and `risk` taken from a round's answer and dropped out of their sets; the leaders who doubted, said no or saw their pick overridden heard
again after the person's answers (step `talk_verdict`), nobody when no card was asked, a leader in the second round heard once. The model call is stubbed (`keeper.call`), as in tests/test_idea_talk.py."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from orkboard.realm import idea_objections, event_log, goal_route, idea_questions, idea_target, ideas
from orkboard.realm.idea_talk_parse import clean_judgement, clean_round
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

def test_priority_is_products_and_risk_is_techs_and_a_value_out_of_its_set_is_dropped():
    said = {"stance": "s", "priority": " High ", "risk": "medium"}

    def one(craft, **more):
        got = clean_round({**said, **more}, craft, "leader", 1, False, set(), (), craft)
        return got["priority"], got["risk"]

    assert one("product") == ("high", "") and one("tech") == ("", "medium")                                                 # each leader gives only its own
    assert one("design") == ("", "") and one("art") == ("", "") and one("") == ("", "")                                       # any other gives neither
    assert one("product", priority="urgent", risk="high") == ("", "") and one("tech", priority="high", risk="huge") == ("", "")   # out of the set: dropped
    assert one("product", priority=3) == ("", "") and one("tech", risk=None) == ("", "") and one("product", priority="LOW") == ("low", "")
    assert [one("product", priority=p)[0] for p in ("high", "normal", "low")] == ["high", "normal", "low"] and [one("tech", risk=r)[1] for r in ("low", "medium", "high")] == ["low", "medium", "high"]
    second = clean_round({"verdict": "no", "why": "w", "priority": "high", "questions": []}, "product", "leader", 2, False, set(), (), "product")
    assert (second["verdict"], second["priority"], second["rejudged"]) == ("go", "", False)                                  # the second round asks no verdict, unless it was told to
    again = clean_round({"verdict": "no", "why": "w", "priority": "low", "questions": []}, "product", "leader", 2, False, set(), (), "product", True)
    assert (again["verdict"], again["why"], again["priority"], again["rejudged"]) == ("no", "w", "low", True)


def test_a_verdict_alone_is_a_verdict_and_the_weight_its_leader_gives_and_nothing_else():
    assert clean_judgement({"verdict": "doubt", "why": " not now ", "instead": "i", "after": "g1", "priority": "low", "risk": "high", "questions": [{"ask": "x"}], "stance": "s"}, "product", ["g1"]) == {
        "verdict": "doubt", "why": "not now", "instead": "i", "after": "", "priority": "low", "risk": ""}
    assert clean_judgement({"verdict": "no", "why": "w", "after": "g1"}, "tech", ["g1"])["after"] == "g1"
    assert clean_judgement({"verdict": "no"}, "tech")["verdict"] == "go" and clean_judgement("not an object") is None and clean_judgement([]) is None


def test_the_round_names_priority_to_product_and_risk_to_tech_and_neither_to_anyone_else(host, parties, model):
    _round_one(model, parties)
    _talk(host, parties, ["product", "design", "tech"])
    by = {c["party"]: c["prompt"] for c in model.steps("talk_round")}
    assert '"priority"' in by[parties["product"]] and "`priority` (`high`, `normal` or `low`)" in by[parties["product"]] and '"risk"' not in by[parties["product"]]
    assert '"risk"' in by[parties["tech"]] and "`risk` (`low`, `medium` or `high`)" in by[parties["tech"]] and '"priority"' not in by[parties["tech"]]
    assert '"priority"' not in by[parties["design"]] and '"risk"' not in by[parties["design"]]
    stances = {s["party"]: s for s in _record(host, _slug_of(host))["stances"]}
    assert stances[parties["product"]]["craft"] == "product" and stances[parties["tech"]]["craft"] == "tech" and stances[parties["design"]]["craft"] == "design"


def _slug_of(host):
    return next(i["slug"] for i in ideas.ideas(host.ideas.root()) if _state(host, i["slug"])["state"] == "talk")


def test_the_priority_and_the_risk_are_kept_with_the_stances_and_make_the_weight(host, parties, model):
    _round_one(model, parties, priority="high", risk="medium")                                                              # every leader says both; only its own counts
    slug = _talk(host, parties, ["product", "design", "tech"])
    rec = _record(host, slug)
    assert [(s["party"], s["priority"], s["risk"]) for s in rec["stances"]] == [(parties["product"], "high", ""), (parties["design"], "", ""), (parties["tech"], "", "medium")]
    assert rec["weight"] == {"priority": "high", "risk": "medium"}


# -- heard as it goes ---------------------------------------------------------------------------------------------------------------------------

def test_each_leader_is_marked_heard_as_its_answer_is_parsed_and_nothing_else_of_it_is_shown_before_the_round_is_whole(host, parties, model):
    _round_one(model, parties)
    seen: dict = {}

    def tech(row):
        for _ in range(400):                                                    # Tech answers last: it waits for Product's and Design's marks
            heard = _record(host, seen["slug"]).get("heard", [])
            if parties["product"] in heard and parties["design"] in heard:
                break
            time.sleep(0.01)
        seen["when_tech_answered"] = list(_record(host, seen["slug"]).get("heard", []))
        seen["row"] = _row(host, seen["slug"], "talk")
        return {"stance": "tech stance", "questions": [card("tech question")]}

    model.said[("talk_round", parties["tech"])] = tech
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["product"]})["slug"]
    seen["slug"] = slug
    host.command("ideas.route_set", {"idea": slug, "route": [parties[w] for w in ("product", "design", "tech")]})
    assert _record(host, slug) == {}                                             # nothing yet
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    assert sorted(seen["when_tech_answered"]) == sorted([parties["product"], parties["design"]])        # marked while Tech was still being heard
    assert seen["row"] is None                                                   # …but not its stance or its cards: the row waits for the whole round
    assert sorted(_record(host, slug)["heard"]) == sorted(parties[w] for w in ("product", "design", "tech")) and idea_questions.talk_of(host.ideas.state_dir, slug)["heard"] == _record(host, slug)["heard"]
    told = _events(host, event_log.TALK_HEARD)
    assert sorted(e["party"] for e in told) == sorted(_record(host, slug)["heard"]) and all(e["idea"] == slug and e["weigher"] is False for e in told)


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
    assert (_state(host, slug)["route"]) == [{"party": parties["tech"], "leader": "architect"}]                          # it is not on the route
    rec = _record(host, slug)
    assert [(s["party"], s["weigher"]) for s in rec["stances"]] == [(parties["tech"], False), (parties["product"], True)]
    weigher = rec["stances"][1]
    assert (weigher["verdict"], weigher["why"], weigher["instead"], weigher["priority"], weigher["stance"], weigher["craft"]) == (
        "doubt", "Is it worth it before the lobby?", "Only the setting", "low", "", "product")
    assert [c["by"] for c in rec["waiting"]] == [parties["tech"]] and rec["second"] == []                              # its question and its second round were never taken
    assert rec["weight"]["priority"] == "low" and sorted(rec["heard"]) == sorted([parties["tech"], parties["product"]])
    (told,) = [e for e in _events(host, event_log.TALK_HEARD) if e["weigher"] is True]
    assert told["party"] == parties["product"]


@pytest.mark.weighs
def test_a_weighers_no_is_an_objection_like_any_leaders(host, parties, model):
    _noes(model, parties, per=0, product={"verdict": "no", "why": "Not before the lobby", "priority": "low"})
    slug = _talk(host, parties, ["tech"])
    (row,) = _objections(host, slug)
    assert row["party"] == parties["product"] and row["why"] == "Not before the lobby" and row["leader"] == "product-manager"


@pytest.mark.weighs
def test_a_weigher_that_does_not_answer_is_passed_over_it_never_fails_the_round(host, parties, model):
    _round_one(model, parties, per=1)
    model.said[("talk_round", parties["product"])] = "not json at all"
    slug = _talk(host, parties, ["tech"])
    assert _state(host, slug)["state"] == "talk" and _row(host, slug, "talk") is not None
    assert [s["party"] for s in _record(host, slug)["stances"]] == [parties["tech"]] and _record(host, slug)["heard"] == [parties["tech"]]
    assert len([c for c in model.steps("talk_round") if c["party"] == parties["product"]]) == 2                         # tried once more, then passed over


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


@pytest.mark.weighs
def test_the_weighers_call_is_in_the_routes_cost(host, parties):
    root, state = host.ideas.root(), host.ideas.state_dir
    route = [{"party": parties["tech"], "leader": "architect"}]
    long = goal_route.cost(state, route, False, root=root)
    assert goal_route.weigher_party(root, route) == parties["product"] and goal_route.weigher_party(root, route, True) == ""
    assert goal_route.weigher_party(root, [*route, {"party": parties["product"]}]) == ""
    assert long["calls"] == goal_route.cost(state, route, False)["calls"] + 1                                          # one more `talk_round`
    assert goal_route.cost(state, route, True, root=root) == goal_route.cost(state, route, True)


# -- the leaders heard again after the answers ------------------------------------------------------------------------------------------------

def _decide_stub(host, monkeypatch):
    went: list = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s))
    return went


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
    assert sorted(c["party"] for c in model.steps("talk_verdict")) == sorted([parties["design"], parties["tech"]]) and _gone(went) == [slug]
    assert _stance(host, slug, parties["tech"])["verdict"] == "doubt" and _stance(host, slug, parties["tech"])["why"] == "Now I am not sure"
    assert [(e["party"], e["before"], e["after"]) for e in _events(host, event_log.TALK_VERDICT)] == [(parties["design"], "go", "go"), (parties["tech"], "go", "doubt")] and "something of my own" in next(
        c for c in model.steps("talk_verdict") if c["party"] == parties["tech"])["prompt"]


def test_nobody_is_heard_again_when_no_card_was_asked_or_the_person_left_every_one_to_the_leaders(host, parties, model, monkeypatch):
    _noes(model, parties, per=0, design={"verdict": "doubt", "why": "The contrast is low"})
    went = _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["design", "tech"])                               # a doubt, and nothing to ask: a hearing (spec 120 §3.4), no decision yet
    for _ in range(300):
        if host.command("ideas.hearing", {"idea": slug}):
            break
        time.sleep(0.01)
    assert host.command("ideas.hearing", {"idea": slug}) and went == [] and model.steps("talk_verdict") == []
    _noes(model, parties, per=1, design={"verdict": "doubt", "why": "The contrast is low"})
    other = _talk(host, parties, ["design", "tech"], "add a light mode option")
    host.command("ideas.talk_answer", {"idea": other, "answers": [], "decide": True})                  # the leaders' own picks tell them nothing new
    _wait(host, other)
    assert model.steps("talk_verdict") == [] and went == [] and _stance(host, other, parties["design"])["verdict"] == "doubt"
    assert host.command("ideas.hearing", {"idea": other})


def test_a_leader_in_the_second_round_and_heard_again_is_heard_once_the_rounds_prompt_asking_its_verdict_too(host, parties, model, monkeypatch):
    seen = []

    def asks(who, **second):
        def answer(row):
            if "first round" in row["prompt"]:
                seen.append((who, row["prompt"]))
                return {"questions": [], **second}
            return {"stance": f"{who} stance", "questions": [card(f"{who} first")], "second_round": who != "tech"}
        return answer

    model.said[("talk_round", parties["product"])] = asks("product", verdict="doubt", why="now unsure", priority="low")
    model.said[("talk_round", parties["design"])] = asks("design")
    model.said[("talk_round", parties["tech"])] = asks("tech")
    model.said[("talk_verdict", parties["tech"])] = {"verdict": "no", "why": "worse with the answers", "risk": "high"}
    _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["product", "design", "tech"])
    _answer(host, slug, 1)                                                                                             # every pick overridden: all three are heard again
    rounds = [c["party"] for c in model.steps("talk_round")]
    assert sorted(rounds) == sorted([parties["product"], parties["design"], parties["tech"], parties["product"], parties["design"]])    # Tech asked no second round
    assert [c["party"] for c in model.steps("talk_verdict")] == [parties["tech"]]                                       # a leader of the second round is not called again
    who = dict(seen)
    assert "You judged the goal before these answers: `go`" in who["product"] and '"verdict": "go"' in who["product"] and '"priority": "normal"' in who["product"]
    assert "You judged the goal before these answers" in who["design"] and '"priority"' not in who["design"] and '"risk"' not in who["design"]
    assert "Read no file" in who["product"]
    product, tech = _stance(host, slug, parties["product"]), _stance(host, slug, parties["tech"])
    assert (product["verdict"], product["why"], product["priority"]) == ("doubt", "now unsure", "low") and (tech["verdict"], tech["why"], tech["risk"]) == ("no", "worse with the answers", "high")
    assert _record(host, slug)["weight"] == {"priority": "low", "risk": "high"} and _record(host, slug)["round"] == 2
    assert sorted((e["party"], e["before"], e["after"]) for e in _events(host, event_log.TALK_VERDICT)) == sorted(
        [(parties["design"], "go", "go"), (parties["tech"], "go", "no"), (parties["product"], "go", "doubt")])                  # one event for each verdict given again, changed or not
    assert [o["party"] for o in _record(host, slug)["objections"]] == [parties["tech"]] and len(_objections(host, slug)) == 1        # the no it gave now is a row


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


def test_a_verdict_that_cannot_be_had_leaves_the_verdict_as_it_was_and_the_decision_goes_on(host, parties, model, monkeypatch):
    _noes(model, parties, per=1, design={"verdict": "doubt", "why": "The contrast is low"})
    model.said[("talk_verdict", parties["design"])] = "not json at all"
    went = _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["design", "tech"])
    _answer(host, slug, 0)
    assert _stance(host, slug, parties["design"])["verdict"] == "doubt" and _gone(went) == [slug] and _events(host, event_log.TALK_VERDICT) == []
    assert len(model.steps("talk_verdict")) == 2 and _state(host, slug)["state"] == "talk"                              # tried once more, then passed over


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


def test_the_cards_of_a_party_put_on_are_the_three_of_all_the_rest_are_closed_by_its_picks(host, parties, model):
    _round_one(model, parties, per=2)
    slug = _talk(host, parties, ["product", "design"])
    assert len(_record(host, slug)["waiting"]) == 3                                                               # the three of four
    host.command("ideas.route_set", {"idea": slug, "route": [parties["product"], parties["design"], parties["tech"]]})
    _wait(host, slug)
    rec = _record(host, slug)
    assert len(rec["waiting"]) == 3 and {d["q"] for d in rec["defaults"]} >= {"tech question 0", "tech question 1"}   # Tech's two are closed by its picks: the three were taken
    assert [s["party"] for s in rec["stances"]] == [parties["product"], parties["design"], parties["tech"]]


def test_an_edit_once_talk_is_done_is_a_step_added_after_it_as_it_was(host, parties, model, monkeypatch):
    _noes(model, parties, per=0, tech=TECH_NO)
    _decide_stub(host, monkeypatch)
    slug = _talk(host, parties, ["tech"])                                                                         # no card to ask, a no to answer: Talk is done
    assert _record(host, slug)["done"] is True
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"], parties["design"]]})
    assert got["changed"] is True and _row(host, slug, "start") is not None and len(model.steps("talk_round")) == 1


def test_the_step_is_one_of_the_keepers_on_the_cheaper_tier_with_no_tools_and_no_reads():
    assert "talk_verdict" in idea_target.STEPS and idea_target.pick("talk_verdict", "thrift") == ("laborer", "")
    assert idea_target.pick("talk_verdict", "quality") == ("warrior", "medium") == idea_target.pick("talk_round", "quality")
    assert idea_target.READS["talk_verdict"] == 0 and idea_target.CONTEXT["talk_verdict"] > 0 and idea_target.CAPS["talk_verdict"] > 0
    from orkboard.realm import idea_spend
    assert idea_spend.STEP_STAGE["talk_verdict"] == "spec"
