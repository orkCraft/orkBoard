"""Spec 99 D (docs/specs/99-a-goals-way.md §5) on the keeper: Talk (the route's leaders heard at once, no tools, their map's text and the project's facts; the three
cards picked by rule across leaders; a project question at a party's first goal and never again; a second round only when asked; the defaults kept) and a bug's Talk
(its diagnosis: one call, at most three case questions, the cause, *No* with words once more, no decision). The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import sys
import threading
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_talk import TalkMixin
from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, idea_questions, idea_target, ideas, library, project_facts
from orkboard.realm.idea_talk_parse import clean_diagnosis, clean_round, fact_text, pick_three, touched


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
def parties(host):
    return {"product": _party(host, "Product", "product-manager", ["copywriter"], "product"),
            "design": _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering"),
            "release": _party(host, "Release", "release-manager", [], "engineering")}


def card(ask, pick=0, blocks=False, choices=("A", "B"), **more):
    return {"ask": ask, "choices": list(choices), "pick": pick, "why": "because", "blocks": blocks, **more}


class Model:
    """The keeper's call stubbed: `said[(step, party)]` the JSON a leader answers (a callable of the round), `calls` every call made."""

    def __init__(self, host):
        self.host, self.calls, self.said, self.lock = host, [], {}, threading.Lock()
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
               "party": getattr(k._tls, "party", ""), "thread": threading.current_thread().name, "at": time.monotonic()}
        with self.lock:
            self.calls.append(row)
        time.sleep(0.15)                                         # long enough for the calls of a round to overlap
        row["end"] = time.monotonic()
        answer = self.said.get((row["step"], row["party"])) or self.said.get((row["step"], ""))
        if callable(answer):
            answer = answer(row)
        if isinstance(answer, str):
            return answer, 0.01, 10, ""
        return json.dumps(answer if answer is not None else {"title": "A goal", "questions": []}), 0.01, 10, ""

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]


@pytest.fixture
def model(host):
    return Model(host)


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _wait(host, slug):
    for _ in range(1000):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _talk(host, parties, which, text="add a dark mode option"):
    """A goal routed to `which` parties and sent to Talk; returns its slug once the round has been heard."""
    slug = host.command("ideas.add", {"text": text, "track": parties[which[0]]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties[w] for w in which]})
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    return slug


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def _round_one(model, parties, per=1, **extra):
    for who in ("product", "design", "tech"):
        model.said[("talk_round", parties[who])] = {"stance": f"{who} stance", "for": f"{who} for", "against": f"{who} against",
                                                      "questions": [card(f"{who} question {n}") for n in range(per)], "second_round": False, **extra}


# -- one call a leader, at once, no tools ------------------------------------------------------------------------------------------

def test_one_call_a_leader_at_once_on_the_cheaper_tier_with_no_tools_and_each_in_its_voice(host, parties, model):
    _round_one(model, parties)
    slug = _talk(host, parties, ["product", "design", "tech"])
    calls = model.steps("talk_round")
    assert sorted(c["party"] for c in calls) == sorted(parties[w] for w in ("product", "design", "tech")) and len(model.calls) == 3
    assert all(c["tools"] is False for c in calls) and len({c["thread"] for c in calls}) == 3                            # a thread each
    assert max(c["at"] for c in calls) < min(c["end"] for c in calls)                                                  # at once: all begun before any ended
    assert {(c["tier"], c["effort"]) for c in calls} == {idea_target.pick("talk_round", "balance")} == {("warrior", "low")}
    voices = {c["party"]: c["prompt"] for c in calls}
    for who, name in (("product", "Product"), ("design", "Design"), ("tech", "Tech")):
        assert "You are" in voices[parties[who]] and f"speak for {name}" in voices[parties[who]]                       # its voice, then its party's words
    assert "Product, then Design, then Tech" in voices[parties["tech"]] and "Read no file" in voices[parties["tech"]]
    assert _state(host, slug)["state"] == "talk" and _state(host, slug)["measure"]["step"] == "talk_round" and _state(host, slug)["measure"]["cost"] == 0.03


def test_a_leader_is_given_the_goal_the_facts_for_its_call_and_its_maps_text_but_not_another_partys_facts(host, parties, model):
    project_facts.keep(host.ideas.state_dir, "product", "for_whom", "Players of party games", "person")
    project_facts.keep(host.ideas.state_dir, "design", "mood", "Dark and quiet", "person")
    project_facts.keep(host.ideas.state_dir, "tech", "runs_on", "A single VPS", "person")
    _round_one(model, parties)
    _talk(host, parties, ["product", "tech"], "add a dark mode option")
    by = {c["party"]: c["prompt"] for c in model.steps("talk_round")}
    assert "add a dark mode option" in by[parties["product"]] and "Whom it is for: Players of party games" in by[parties["tech"]]       # the common core
    assert "A single VPS" in by[parties["tech"]] and "A single VPS" in by[parties["product"]]                                           # a party on the route
    assert "Dark and quiet" not in by[parties["tech"]] and "Dark and quiet" not in by[parties["product"]]                              # Design is not on this route
    assert "Your party's map" not in by[parties["product"]]                                                                            # a party with no map is given none


def test_tech_is_given_its_maps_text(host, parties, model, monkeypatch):
    from orkboard.realm import map_text
    monkeypatch.setattr(map_text, "system", lambda state_dir, root, since="", pages=None: "The map of System at dev abc1234\ncontainers: web")
    _round_one(model, parties)
    _talk(host, parties, ["product", "tech"])
    by = {c["party"]: c["prompt"] for c in model.steps("talk_round")}
    assert "Your party's map:\nThe map of System at dev abc1234" in by["tech"] and "The map of System" not in by["product"]


def test_a_leader_that_does_not_answer_is_tried_once_more_and_then_fails_the_round_back_to_the_route_card(host, parties, model):
    _round_one(model, parties)
    model.said[("talk_round", "design")] = "not json at all"
    slug = _talk(host, parties, ["product", "design"])
    st = _state(host, slug)
    assert st["state"] == "routed" and "did not answer: try again" in st["error"] and idea_questions.record(host.ideas.state_dir, slug) == {}
    assert len([c for c in model.steps("talk_round") if c["party"] == "design"]) == 2                              # tried once more
    row = _row(host, slug, "route")
    assert row is not None                                                                                          # its route card is its row again


# -- the three cards ------------------------------------------------------------------------------------------------------------------

def test_the_three_are_picked_across_leaders_those_the_work_cannot_start_without_first_then_by_the_routes_order(host, parties, model):
    model.said[("talk_round", parties["product"])] = {"stance": "s", "questions": [card("p1"), card("p2"), card("p3")]}
    model.said[("talk_round", parties["design"])] = {"stance": "s", "questions": [card("d1", blocks=True), card("d2")]}
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "questions": [card("t1", blocks=True), card("t2", blocks=True), card("t3")]}
    slug = _talk(host, parties, ["product", "design", "tech"])
    row = _row(host, slug, "talk")
    assert [q["q"] for q in row["questions"]] == ["d1", "t1", "t2"]                                                  # the blocking three, in the route's order
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert {d["q"] for d in rec["defaults"]} == {"p1", "p2", "p3", "d2", "t3"}
    assert all(d["answer"] == "A" and d["why"] == "because" for d in rec["defaults"])                               # closed by their leaders' picks


def test_with_none_blocking_the_routes_order_takes_the_first_three(host, parties, model):
    model.said[("talk_round", parties["product"])] = {"stance": "s", "questions": [card("p1"), card("p2")]}
    model.said[("talk_round", parties["design"])] = {"stance": "s", "questions": [card("d1"), card("d2")]}
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "questions": [card("t1")]}
    slug = _talk(host, parties, ["product", "design", "tech"])
    assert [q["q"] for q in _row(host, slug, "talk")["questions"]] == ["p1", "p2", "d1"]


def test_pick_three_is_a_rule_of_code():
    pool = [({"id": str(n)}, blocks, "") for n, blocks in enumerate([False, True, False, True, True, False])]
    chosen, closed = pick_three(pool)
    assert [c["id"] for c, _b, _k in chosen] == ["1", "3", "4"] and [c["id"] for c, _b, _k in closed] == ["0", "2", "5"]
    assert pick_three([]) == ([], []) and len(pick_three(pool, 1)[0]) == 1


def test_the_row_is_the_stances_and_the_cards(host, parties, model):
    _round_one(model, parties)
    slug = _talk(host, parties, ["product", "tech"])
    row = _row(host, slug, "talk")
    assert row["round"] == 1 and [s["party"] for s in row["stances"]] == [parties["product"], parties["tech"]]
    assert row["stances"][0] == {"party": parties["product"], "leader": "product-manager", "stance": "product stance", "for": "product for", "against": "product against"}
    first = row["questions"][0]
    assert first == {"id": f"r1-{parties['product']}-1", "by": parties["product"], "leader": "product-manager", "q": "product question 0", "choices": ["A", "B"], "pick": 0,
                     "why": "because", "project": False}
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["place"] == "table" and node["asks_you"] is True and node["state"] == "talk"                         # on the table, asking: in the hand too
    last = ideas.talk(host.ideas.state_dir, slug)[-1]
    assert last["who"] == "keeper" and last["section"] == "Talk" and "product stance" in last["text"] and "tech stance" in last["text"]            # kept in talk.jsonl


def test_a_card_is_parsed_strictly():
    ok = idea_questions.card({"ask": "Which?", "choices": ["a", "b", "c", "d"], "pick": "c", "why": "it is"}, id="x", by="tech", leader="architect")
    assert ok == {"id": "x", "by": "tech", "leader": "architect", "q": "Which?", "choices": ["a", "b", "c", "d"], "pick": 2, "why": "it is", "project": False}
    for bad in ({"ask": "Which?", "choices": ["only"], "pick": 0}, {"ask": "Which?", "choices": list("abcde"), "pick": 0},          # one choice; five: never more than four
                {"ask": "Which?", "choices": ["a", "A"], "pick": 0}, {"ask": "Which?", "choices": ["a", ""], "pick": 0},               # the same twice; padded
                {"ask": "Which?", "choices": ["a", "b"], "pick": 2}, {"ask": "Which?", "choices": ["a", "b"]},                         # a pick that is none; no pick
                {"ask": "", "choices": ["a", "b"], "pick": 0}, {"ask": "Which?", "choices": "a/b", "pick": 0}, "text", None):
        assert idea_questions.card(bad, id="x", by="tech", leader="architect") is None
    assert idea_questions.card({"ask": "q", "choices": ["server/lobby.ts", "a (b)"], "pick": True}, id="x", by="t", leader="l") is None      # a bool is no index
    assert idea_questions.card({"ask": "q", "choices": ["server/lobby.ts", "a (b)"], "pick": 1}, id="x", by="t", leader="l", project=True)["project"] is True


def test_what_a_leader_says_is_taken_strictly():
    got = clean_round({"stance": "  where we  stand ", "for": 3, "against": "x" * 500, "questions": [card("a"), card("a"), {"ask": "no choices"}, card("b")],
                       "second_round": "yes", "project_questions": [card("p", key="stack")]}, "tech", "architect", 1, False, set())
    assert got["stance"] == "where we stand" and got["for"] == "" and len(got["against"]) == 200 and got["more"] is False       # `second_round` is a bool
    assert [c["q"] for c, _b, _k in got["cards"]] == ["a", "b"]                                                          # the same once, a non-card dropped, no project question (not its first goal)
    assert clean_round({"questions": []}, "tech", "architect", 1, False, set()) is None and clean_round("x", "tech", "architect", 1, False, set()) is None
    assert clean_round({"questions": [card("a")]}, "tech", "architect", 2, False, set())["cards"][0][0]["id"] == "r2-tech-1"
    first = clean_round({"stance": "s", "project_questions": [card("p", key="stack"), card("q", key="Bad Key"), card("r", key="done"), card("s", key="stack")]},
                        "tech", "architect", 1, True, {"done"})
    assert [(c["id"], k, c["project"]) for c, _b, k in first["cards"]] == [("p-tech-stack", "stack", True)]


# -- a project question -------------------------------------------------------------------------------------------------------------

def test_a_project_question_is_asked_at_a_partys_first_goal_inside_the_three_kept_when_answered_and_never_asked_again(host, parties, model):
    _round_one(model, parties, per=0)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "questions": [card("t goal", blocks=True)],
                                                   "project_questions": [card("Where does it run?", blocks=True, key="runs_on", choices=("A VPS", "A phone"))]}
    first = _talk(host, parties, ["tech"])
    prompt = model.steps("talk_round")[0]["prompt"]
    assert "first goal in this project" in prompt and "project_questions" in prompt
    cards = _row(host, first, "talk")["questions"]
    assert [(c["q"], c["project"]) for c in cards] == [("t goal", False), ("Where does it run?", True)]                 # inside the goal's three
    host.command("ideas.talk_answer", {"idea": first, "answers": [{"id": cards[0]["id"], "pick": 0}, {"id": cards[1]["id"], "pick": 1}]})
    kept = project_facts.of(host.ideas.state_dir, parties["tech"])
    assert [(f["key"], f["by"]) for f in kept] == [("runs_on", "person")] and kept[0]["text"] == "Where does it run? — A phone"
    assert "runs_on" in project_facts.answered(host.ideas.state_dir)
    _wait(host, first)
    model.calls.clear()
    second = _talk(host, parties, ["tech"], "add a light mode option")
    assert "first goal in this project" not in model.steps("talk_round")[0]["prompt"]                                 # no longer the party's first goal
    assert [c["project"] for c in _row(host, second, "talk")["questions"]] == [False]


def test_a_project_question_answered_is_not_asked_again_even_by_another_party_and_a_left_to_the_leaders_one_is_kept_read(host, parties, model):
    project_facts.keep(host.ideas.state_dir, "product", "for_whom", "Players", "person")
    model.said[("talk_round", parties["product"])] = {"stance": "s", "project_questions": [card("Whom?", key="for_whom"), card("What hurts?", key="hurts", blocks=True)]}
    slug = _talk(host, parties, ["product"])
    assert [c["id"] for c in _row(host, slug, "talk")["questions"]] == [f"p-{parties['product']}-hurts"]                # the answered key is not a card
    host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    kept = {f["key"]: f["by"] for f in project_facts.of(host.ideas.state_dir, parties["product"])}
    assert kept == {"for_whom": "person", "hurts": "read"}                                                           # *Let … decide*: a pick kept as read


def test_the_facts_text_keeps_the_answer_whole():
    assert fact_text("Where?", "A VPS") == "Where? — A VPS"
    long = fact_text("q" * 300, "answer")
    assert long.endswith("— answer") and len(long) <= project_facts.FACT_CHARS
    assert fact_text("q", "a" * 400) == "a" * project_facts.FACT_CHARS


# -- the answers, a second round, the defaults, the decision's seam -----------------------------------------------------------------------

def test_the_answers_are_taken_together_pick_or_text_or_decide_and_a_question_not_asked_is_refused(host, parties, model):
    _round_one(model, parties, per=2)
    slug = _talk(host, parties, ["product", "design"])
    cards = _row(host, slug, "talk")["questions"]
    assert len(cards) == 3
    k = host.ideas.keeper
    with pytest.raises(idea_keeper.KeeperError, match="Answer every question"):
        k.talk_answer(slug, [{"id": cards[0]["id"], "pick": 0}])
    with pytest.raises(idea_keeper.KeeperError, match="not asked now"):
        k.talk_answer(slug, [{"id": "r1-nobody-9", "pick": 0}])
    with pytest.raises(idea_keeper.KeeperError):
        k.talk_answer(slug, [], False)
    assert _row(host, slug, "talk") is not None                                                                       # nothing was taken
    sent = []
    k.draft = lambda s, person=False: sent.append(s) or True                                                           # today's draft takes the goal on (E's seam is not built)
    k.talk_answer(slug, [{"id": cards[0]["id"], "pick": 1}, {"id": cards[1]["id"], "text": " my own  words "}, {"id": cards[2]["id"], "pick": 9, "text": ""}], decide=True)
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert [(a["id"], a["answer"], a["how"]) for a in rec["answers"]] == [(cards[0]["id"], "B", "pick"), (cards[1]["id"], "my own words", "text"), (cards[2]["id"], "A", "decide")]
    assert rec["waiting"] == [] and rec["done"] is True and sent == [slug]
    said = ideas.talk(host.ideas.state_dir, slug)[-1]
    assert said["who"] == "you" and "my own words" in said["text"] and said["section"] == "Talk"
    assert _row(host, slug, "talk") is None


def test_after_the_last_round_the_goal_waits_for_the_decision_the_seam_is_e_when_the_keeper_has_it_else_today_draft(host, parties, model, monkeypatch):
    _round_one(model, parties)
    slug = _talk(host, parties, ["tech"])
    cards = _row(host, slug, "talk")["questions"]
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append((s, _state(host, s)["state"])), raising=False)       # part E's seam
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": cards[0]["id"], "pick": 0}]})
    assert went == [(slug, "talk")] and _state(host, slug)["state"] == "talk"
    other = _talk(host, parties, ["tech"], "add a light mode option")
    monkeypatch.delattr(host.ideas.keeper, "decide")
    model.said[("draft", "")] = {"title": "A goal", "questions": []}
    host.command("ideas.talk_answer", {"idea": other, "answers": [], "decide": True})
    _wait(host, other)
    assert any(c["step"] == "draft" for c in model.calls) and _state(host, other)["state"] in ("ready", "asks", "plan", "reading", "planning")      # it still moves


def test_a_goal_with_nothing_to_ask_goes_straight_on_to_the_decision(host, parties, model, monkeypatch):
    _round_one(model, parties, per=0)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s), raising=False)
    slug = _talk(host, parties, ["tech"])
    for _ in range(300):
        if went:
            break
        time.sleep(0.01)
    assert went == [slug] and _row(host, slug, "talk") is None and not host.ideas.keeper.busy(slug)                    # after the run has ended: E's run may begin


def test_a_second_round_only_when_a_leader_asked_for_it_given_the_answers_at_most_three_again_then_the_defaults(host, parties, model, monkeypatch):
    _round_one(model, parties, per=1)
    seen = []

    def asks(who):
        def answer(row):
            if "first round" not in row["prompt"]:
                return {"stance": "s", "questions": [card(f"{who} first")], "second_round": True}
            seen.append(row["prompt"])
            return {"questions": [card(f"{who} again 0", blocks=True), card(f"{who} again 1")]}
        return answer
    model.said[("talk_round", parties["product"])] = asks("product")
    model.said[("talk_round", parties["design"])] = asks("design")
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s), raising=False)
    slug = _talk(host, parties, ["product", "design", "tech"])
    cards = _row(host, slug, "talk")["questions"]
    assert len(model.steps("talk_round")) == 3
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": c["id"], "pick": 1} for c in cards]})
    _wait(host, slug)
    second = model.steps("talk_round")[3:]
    assert sorted(c["party"] for c in second) == sorted([parties["product"], parties["design"]]) and went == []              # only the leaders who asked, at once
    assert all("first round" in p and "— B" in p and "Read no file" in p for p in seen) and len(seen) == 2                    # given the answers; still no file
    assert all("Product, then Design, then Tech" in p for p in seen)                                                          # told the whole route
    row = _row(host, slug, "talk")
    assert row["round"] == 2 and [q["q"] for q in row["questions"]] == ["product again 0", "product again 1", "design again 0"]    # the blocking first, three again
    assert len(row["stances"]) == 3                                                                                           # the first round's stances stay
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert {d["q"] for d in rec["defaults"] if d["round"] == 2} == {"design again 1"}                                         # what is left takes the picks
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": c["id"], "pick": 0} for c in row["questions"]]})
    assert len(model.steps("talk_round")) == 5 and went == [slug] and _row(host, slug, "talk") is None                         # never a third round
    assert _state(host, slug)["measure"]["step"] == "talk_round" and _state(host, slug)["measure"]["cost"] == 0.05            # every call measured


def test_no_second_round_when_the_person_left_it_to_the_leaders_or_nobody_asked(host, parties, model, monkeypatch):
    _round_one(model, parties, per=1, second_round=True)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s), raising=False)
    slug = _talk(host, parties, ["tech"])
    host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    assert len(model.steps("talk_round")) == 1 and went == [slug]


def test_a_second_round_that_could_not_be_heard_is_skipped(host, parties, model, monkeypatch):
    model.said[("talk_round", parties["tech"])] = lambda row: {"stance": "s", "questions": [card("t")], "second_round": True} if "first round" not in row["prompt"] else "garbage"
    went = []
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(s), raising=False)
    slug = _talk(host, parties, ["tech"])
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": _row(host, slug, "talk")["questions"][0]["id"], "pick": 0}]})
    for _ in range(300):
        if went:
            break
        time.sleep(0.01)
    assert went == [slug] and _state(host, slug)["state"] == "talk" and _state(host, slug)["error"] == ""


def test_talk_is_refused_in_plain_words_and_the_goal_stays_at_its_route_card(host, parties, model):
    _round_one(model, parties)
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    host.ideas.keeper.limits = lambda: []
    host.ideas.keeper.window_until = lambda: time.time() + 3600                                                                       # Claude's window is spent
    host.command("ideas.talk", {"idea": slug})
    assert _state(host, slug)["state"] == "routed" and "window is spent" in _state(host, slug)["error"] and model.calls == []
    assert _row(host, slug, "route") is not None
    with pytest.raises(idea_keeper.KeeperError, match="not at Talk"):
        host.ideas.keeper.talk(slug)


def test_talk_runs_for_a_route_of_one_party_with_one_call(host, parties, model):
    _round_one(model, parties)
    slug = _talk(host, parties, ["design"])
    assert len(model.calls) == 1 and _row(host, slug, "talk")["stances"][0]["stance"] == "design stance"


def test_the_mixin_is_a_base_of_the_keeper_and_speaks_for_the_party_of_its_thread(host, parties):
    k = host.ideas.keeper
    assert TalkMixin in type(k).__mro__ and type(k).__mro__.index(TalkMixin) < type(k).__mro__.index(idea_keeper.LeadMixin)
    k._tls.party = parties["design"]
    try:
        assert k.leader()["slug"] == "product-designer"
    finally:
        k._tls.party = ""


# -- a bug's Talk is its diagnosis -----------------------------------------------------------------------------------------------------------

BUG = "Saving crashes when the file is empty, see src/app.py"


def _bug(host, parties, model, said=None, text=BUG):
    model.said[("diagnose", "")] = said or {"questions": [card(f"case {n}", choices=("here", "there")) for n in range(4)], "cause": "src/app.py does not guard an empty file",
                                              "where": ["src/app.py", "../etc/passwd", "nope.py", "src/app.py"]}
    slug = host.command("ideas.add", {"text": text})["slug"]
    assert _state(host, slug)["route_how"]["short"] is True and _state(host, slug)["route_how"]["reproduces"] is False
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    return slug


def test_a_bugs_talk_is_one_call_of_tech_alone_with_a_few_reads_at_most_three_case_questions_and_the_cause(host, parties, model):
    slug = _bug(host, parties, model)
    calls = model.calls
    assert len(calls) == 1 and calls[0]["step"] == "diagnose" and calls[0]["party"] == parties["tech"] and calls[0]["tools"] is True
    assert (calls[0]["tier"], calls[0]["effort"]) == ("warrior", "low") and idea_target.READS["diagnose"] == 4
    assert "Read at most 4 files" in calls[0]["prompt"] and "Start from these files: src/app.py" in calls[0]["prompt"]       # the files the report names
    assert "Saving crashes when the file is empty" in calls[0]["prompt"] and "no decision is written" in calls[0]["prompt"]
    row = _row(host, slug, "cause")
    assert row["cause"] == "src/app.py does not guard an empty file" and row["where"] == ["src/app.py"]                       # paths that exist, once
    assert [q["q"] for q in row["q"]] == ["case 0", "case 1", "case 2"] and [q["id"] for q in row["q"]] == ["case-1", "case-2", "case-3"]
    assert row["q"][0]["by"] == parties["tech"] and row["q"][0]["project"] is False and _row(host, slug, "talk") is None
    assert _state(host, slug)["state"] == "talk" and _state(host, slug)["measure"]["step"] == "diagnose"
    assert "I think src/app.py does not guard" in ideas.talk(host.ideas.state_dir, slug)[-1]["text"]


def test_a_yes_goes_on_to_the_sections_without_a_decision_the_cause_is_kept(host, parties, model, monkeypatch):
    slug = _bug(host, parties, model)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append((s, _state(host, s)["state"])), raising=False)       # part E's seam
    monkeypatch.setattr(host.ideas.keeper, "decide", lambda s: went.append(("decide", s)), raising=False)
    row = _row(host, slug, "cause")
    host.command("ideas.cause_answer", {"idea": slug, "yes": True, "answers": [{"id": row["q"][0]["id"], "pick": 1}]})
    assert went == [(slug, "sections")] and len(model.calls) == 1                                                       # no decision; no more call
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert rec["cause"]["text"] == "src/app.py does not guard an empty file" and rec["cause"]["confirmed"] is True and rec["cause"]["by"] == "leader"
    assert [(a["q"], a["answer"], a["how"]) for a in rec["answers"]] == [("case 0", "there", "pick"), ("case 1", "here", "decide"), ("case 2", "here", "decide")]
    assert _row(host, slug, "cause") is None


def test_yes_with_words_is_the_persons_own_cause_without_another_guess(host, parties, model, monkeypatch):
    slug = _bug(host, parties, model)
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: None, raising=False)
    host.command("ideas.cause_answer", {"idea": slug, "yes": True, "text": "the empty file is read twice"})
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert rec["cause"]["text"] == "the empty file is read twice" and rec["cause"]["by"] == "person" and len(model.calls) == 1


def test_no_with_words_asks_one_more_guess_once_and_a_second_no_goes_on(host, parties, model, monkeypatch):
    slug = _bug(host, parties, model)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append(s), raising=False)
    model.said[("diagnose", "")] = lambda row: ({"cause": "the saver in src/save.py truncates first", "where": ["src/app.py"], "questions": [card("never")]}
                                               if "first guess" in row["prompt"] else None)
    host.command("ideas.cause_answer", {"idea": slug, "yes": False, "text": "it is in src/app.py's saver"})
    _wait(host, slug)
    assert len(model.calls) == 2 and "Your first guess, which the person says is wrong" in model.calls[1]["prompt"] and "it is in src/app.py" in model.calls[1]["prompt"]
    assert "case 0 — " in model.calls[1]["prompt"] and went == []                                                       # given the cases answered
    row = _row(host, slug, "cause")
    assert row["cause"] == "the saver in src/save.py truncates first" and row["q"] == [] and row["where"] == ["src/app.py"]       # the new guess; the cases are answered
    host.command("ideas.cause_answer", {"idea": slug, "yes": False, "text": "no, in the config"})
    assert len(model.calls) == 2 and went == [slug]                                                                    # once: no third guess
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert rec["cause"]["text"] == "no, in the config" and rec["cause"]["by"] == "person" and rec["cause"]["guesses"] == 2


def test_no_with_no_words_goes_on_with_no_cause_found(host, parties, model, monkeypatch):
    slug = _bug(host, parties, model)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append(s), raising=False)
    host.command("ideas.cause_answer", {"idea": slug, "yes": False})
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert went == [slug] and len(model.calls) == 1 and rec["cause"]["by"] == "none" and rec["cause"]["text"] == ""


def test_a_second_guess_that_cannot_be_had_leaves_the_persons_words(host, parties, model, monkeypatch):
    slug = _bug(host, parties, model)
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append(s), raising=False)
    model.said[("diagnose", "")] = "garbage"
    host.command("ideas.cause_answer", {"idea": slug, "yes": False, "text": "in the config"})
    for _ in range(300):
        if went:
            break
        time.sleep(0.01)
    assert went == [slug] and idea_questions.record(host.ideas.state_dir, slug)["cause"]["text"] == "in the config"


def test_a_bug_never_writes_a_decision_and_without_e_the_goal_still_moves_by_todays_draft(host, parties, model):
    slug = _bug(host, parties, model)
    model.said[("draft", "")] = {"title": "A goal", "questions": []}
    host.command("ideas.cause_answer", {"idea": slug, "yes": True})
    _wait(host, slug)
    assert not hasattr(host.ideas.keeper, "decide") and idea_questions.record(host.ideas.state_dir, slug)["mode"] == "bug"       # the decision is E's, and a bug has none
    assert any(c["step"] == "draft" for c in model.calls) and not any(c["step"] in ("decide", "talk_round") for c in model.calls)


def test_a_bug_asks_the_project_question_it_cannot_be_done_without_at_techs_first_goal_and_no_other(host, parties, model):
    said = {"questions": [card("case")], "cause": "x in src/app.py", "where": ["src/app.py"],
            "project_questions": [card("Which runtime?", blocks=False, key="runtime"), card("Where does it run?", blocks=True, key="runs_on"), card("Which db?", blocks=True, key="db")]}
    slug = _bug(host, parties, model, said)
    assert [(q["q"], q["project"]) for q in _row(host, slug, "cause")["q"]] == [("case", False), ("Where does it run?", True)]       # one, the one it cannot do without
    host.command("ideas.cause_answer", {"idea": slug, "yes": True, "answers": [{"id": f"p-{parties['tech']}-runs_on", "pick": 0}]})
    assert [(f["key"], f["by"]) for f in project_facts.of(host.ideas.state_dir, parties["tech"])] == [("runs_on", "person")]


def test_the_diagnosis_is_taken_strictly(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    got = clean_diagnosis({"cause": "  it   is here ", "where": ["src/a.py", "./src/a.py", ".env", str(tmp_path / "src" / "a.py"), "/etc/passwd", 7],
                           "questions": [card(f"q{n}") for n in range(5)]}, "tech", "architect", tmp_path, False, set())
    assert got["cause"] == "it is here" and got["where"] == ["src/a.py"] and [c["id"] for c, _b, _k in got["cards"]] == ["case-1", "case-2", "case-3"]
    assert clean_diagnosis({"cause": "x", "questions": [card("q")]}, "tech", "architect", tmp_path, False, set(), again=True)["cards"] == []
    assert clean_diagnosis({"questions": []}, "tech", "architect", tmp_path, False, set()) is None and clean_diagnosis(None, "t", "a", tmp_path, False, set()) is None
    assert touched(tmp_path, "crash in src/a.py:12 and .env and v1.2 and /etc/passwd", 4) == ["src/a.py"]


def test_a_long_bug_with_a_failure_in_it_that_the_person_made_the_long_way_is_a_normal_talk(host, parties, model):
    _round_one(model, parties)
    slug = host.command("ideas.add", {"text": "Saving crashes, tests/test_save.py::test_it FAILED"})["slug"]
    host.command("ideas.talk", {"idea": slug})                                                                          # *The long way*: short is off
    _wait(host, slug)
    assert [c["step"] for c in model.calls] == ["talk_round"] and _row(host, slug, "talk") is not None and _row(host, slug, "cause") is None
