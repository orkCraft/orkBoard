"""Spec 168 C1 and C2 (docs/specs/168-the-window-played-as-a-card-games-table.md §C; decisions §283.23–§283.25) on the keeper: a leader's say beside its verdict (`needs`, `better`) parsed
and limited; an old reply (questions only) read as before, its questions among the needs; the prompt holding the pile's look-alikes and the goals in line; a `better` taken written into the
Gist by one call of the Orkmaster with its *Added:* lines kept and undone by a press; two that contradict as one fork; the leaders judged again, twice at most, then the hearing. The model
call is stubbed (`keeper.call`), as in tests/test_idea_talk.py."""
from __future__ import annotations

import time

import pytest

from pathlib import Path

from orkboard.realm import event_log, goal_refine, idea_say, idea_target, ideas
from orkboard.realm.idea_talk_parse import clean_better, clean_needs, clean_round
from tests.test_idea_talk import Model, _round_one, _talk, _wait, card, host, model, parties  # noqa: F401  (the fixtures and the helpers of Talk's tests)

GOAL = "add a dark mode option to the settings screen"


# -- parsed strictly and limited ---------------------------------------------------------------------------------------------------------

def test_a_reply_with_needs_and_better_is_parsed_and_limited():
    long = "word " * 80
    said = {"stance": "s", "needs": [
        {"kind": "risk", "line": long, "rests_on": "§283.23", "ways": [{"name": f"way {n}", "line": f"does {n}"} for n in range(5)]},
        {"kind": "conflict", "line": "clashes", "rests_on": "dark-mode", "ways": []},
        {"kind": "doom", "line": "unknown kind is dropped"},
        {"kind": "question", "line": "", "ways": []},
        {"kind": "question", "line": "where does it live?", "rests_on": "not a root!", "ways": [{"name": "a"}, {"name": "A", "line": "same name"}, {"line": "no name"}, "x"]},
        {"kind": "risk", "line": "a fourth is past the bound"},
    ], "better": [
        {"line": "say it in one sentence", "weight": "lighter"}, {"line": "drop the option", "weight": "HEAVIER"}, {"line": "x", "weight": "huge"}, {"line": "", "weight": "same"},
        {"line": long, "weight": "same"}, {"line": "past the bound", "weight": "same"}]}
    got = clean_round(said, "tech", "architect", 1, False, set())
    needs, better = got["needs"], got["better"]
    assert [n["id"] for n in needs] == ["n-tech-1", "n-tech-2", "n-tech-3"] and [n["kind"] for n in needs] == ["risk", "conflict", "question"]       # an unknown kind and an empty line are dropped; three at most
    assert len(needs[0]["line"]) <= 200 and needs[0]["line"].endswith("…") and needs[0]["rests_on"] == "§283.23" and needs[1]["rests_on"] == "dark-mode"
    assert [w["name"] for w in needs[0]["ways"]] == ["way 0", "way 1", "way 2"] and needs[0]["ways"][1] == {"name": "way 1", "line": "does 1", "way_kind": "other"}      # three ways at most
    assert needs[2]["rests_on"] == "" and needs[2]["ways"] == [{"name": "a", "line": "", "way_kind": "other"}]                     # a root that is none reads empty; the same name once; no name, no way
    assert [(b["id"], b["weight"]) for b in better] == [("b-tech-1", "lighter"), ("b-tech-2", "heavier"), ("b-tech-3", "same")] and len(better[2]["line"]) <= 200      # an unknown weight is dropped
    assert clean_needs("nonsense") == [] and clean_better({"line": "x"}) == [] and clean_needs([None, 3, "x"]) == []


# -- the prompt: what code knows -----------------------------------------------------------------------------------------------------------

def _say_round(model, parties, per=1, **per_party):
    _round_one(model, parties, per)
    for who, more in per_party.items():
        model.said[("talk_round", parties[who])] = {**model.said[("talk_round", parties[who])], **more}


# -- the rows the faces read ------------------------------------------------------------------------------------------------------------------

def test_a_leaders_say_is_kept_and_the_old_questions_read_as_needs_of_the_kind_question(host, parties, model):
    _say_round(model, parties, tech={"verdict": "doubt", "why": "it breaks the theme", "needs": [{"kind": "risk", "line": "the theme file is shared", "rests_on": "§283.1", "ways": [{"name": "Fork it", "line": "a copy"}]}],
                                     "better": [{"line": "name the option plainly", "weight": "lighter"}]})
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    say = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert [r["party"] for r in say["leaders"]] == [parties["design"], parties["tech"]]
    tech = next(r for r in say["leaders"] if r["party"] == parties["tech"])
    assert tech["verdict"] == "doubt" and tech["why"] == "it breaks the theme"
    own = [n for n in tech["needs"] if not n["legacy"]]
    assert own[0]["id"] == "n-" + parties["tech"] + "-1" and own[0]["state"] == "open" and own[0]["ways"] == [{"name": "Fork it", "line": "a copy", "way_kind": "other"}]
    questions = [n for n in tech["needs"] if n["legacy"]]
    assert questions and all(q["kind"] == "question" and q["state"] == "open" and q["ways"] and q["rests_on"] == "" for q in questions)       # today's cards, read as needs
    assert [b["state"] for b in tech["better"]] == ["open"] and tech["better"][0]["weight"] == "lighter"
    design = next(r for r in say["leaders"] if r["party"] == parties["design"])
    assert design["verdict"] == "go" and [n for n in design["needs"] if not n["legacy"]] == [] and design["better"] == [] and design["needs"]       # an old reply: its questions only
    assert say["judged"] == 0 and say["judge_left"] == 2 and say["rewrite"] is None and say["fork"] is None and say["answered"] is False


# -- a better taken is written into the Gist by one cheap call of the Orkmaster ---------------------------------------------------------------------

def _spoken(host, parties, model, **per_party):
    """A goal at Talk whose Gist holds the person's words and two *Added:* lines, its leaders having spoken."""
    _say_round(model, parties, **per_party)
    slug = _talk(host, parties, ["design", "tech"], GOAL)
    host.ideas.add_words(slug, "and keep the choice per device", "", "")
    host.ideas.add_words(slug, "and remember it\nacross restarts", "", "")
    return slug


def _settle(host, slug):
    """Every run of the goal ended, the ones that follow another (a rewrite, then the judging again) too."""
    quiet = 0
    for _ in range(2000):
        quiet = 0 if host.ideas.keeper.busy(slug) else quiet + 1
        if quiet >= 8:
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _gist(host, slug):
    return ideas.idea_page(host.ideas.root(), slug).section("Gist")


def _id(host, slug, party, kind, n=1):
    return f"{kind}-{party}-{n}"


def test_a_better_taken_rewrites_the_gist_keeps_the_added_lines_and_is_undone_by_a_press(host, parties, model):
    tech = parties["tech"]
    slug = _spoken(host, parties, model, tech={"better": [{"line": "say it plainly: a dark theme switch", "weight": "lighter"}]})
    before = _gist(host, slug)
    base, tail = goal_refine.split(before)
    assert tail.startswith("Added: and keep the choice per device") and "Added: and remember it\nacross restarts" in tail and base == GOAL
    model.said[("rewrite", "")] = {"gist": "Add a dark theme switch to the settings screen."}
    out = host.command("ideas.take_better", {"idea": slug, "id": _id(host, slug, tech, "b")})
    _wait(host, slug)
    assert out["ok"] is True and out["rewriting"] is True
    calls = model.steps("rewrite")
    assert len(calls) == 1 and calls[0]["tools"] is False and (calls[0]["tier"], calls[0]["effort"]) == idea_target.pick("rewrite", "balance") == ("warrior", "low")        # one cheap call, no tools
    assert "say it plainly: a dark theme switch" in calls[0]["prompt"] and "(lighter)" in calls[0]["prompt"] and "Added:" not in calls[0]["prompt"] and "Read no file" in calls[0]["prompt"]
    after = _gist(host, slug)
    assert after != before and after.startswith("Add a dark theme switch to the settings screen.")
    assert goal_refine.split(after)[1] == tail                                                  # the Added lines, byte for byte
    node = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert node["rewrite"]["before"] == before and node["rewrite"]["after"] == after and node["rewrite"]["undoable"] is True and node["waiting"] == []
    assert next(b for r in node["leaders"] if r["party"] == tech for b in r["better"])["state"] == "taken"
    assert ideas.state(host.ideas.state_dir, slug)["error"] == ""
    host.command("ideas.undo_rewrite", {"idea": slug})
    assert _gist(host, slug) == before                                                           # exactly
    node = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert node["rewrite"] is None and next(b for r in node["leaders"] if r["party"] == tech for b in r["better"])["state"] == "open"
    with pytest.raises(Exception, match="Nothing was rewritten"):
        host.command("ideas.undo_rewrite", {"idea": slug})


# -- taken ones that contradict come back as one fork ----------------------------------------------------------------------------------------------

def test_two_that_contradict_come_back_as_one_fork_and_the_choice_writes_them(host, parties, model):
    design, tech = parties["design"], parties["tech"]
    slug = _spoken(host, parties, model, design={"better": [{"line": "follow the system's theme only", "weight": "lighter"}]},
                   tech={"better": [{"line": "let the person pick a theme in the settings", "weight": "heavier"}]})
    before = _gist(host, slug)
    a, b = _id(host, slug, design, "b"), _id(host, slug, tech, "b")
    model.said[("rewrite", "")] = {"fork": {"ask": "Which theme rule?", "choices": ["Follow the system", "Let the person pick"], "lines": ["no setting", "a setting"], "between": [a, b]}}
    host.command("ideas.take_better", {"idea": slug, "id": a})
    _wait(host, slug)
    # the first one alone is no contradiction in the stub's mind: it forks all the same, then the second joins the pending ones
    node = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert node["fork"]["card"]["choices"] == ["Follow the system", "Let the person pick"] and set(node["fork"]["ids"]) == {a} and _gist(host, slug) == before
    assert node["rewrite"] is None and node["waiting"] == []                                      # nothing is written while the person has not chosen
    out = host.command("ideas.take_better", {"idea": slug, "id": b})
    assert out["rewriting"] is False                                                              # a fork waits: no second call
    assert len(model.steps("rewrite")) == 1
    model.said[("rewrite", "")] = {"gist": "Add a dark mode the person picks in the settings."}
    host.command("ideas.say_fork", {"idea": slug, "pick": 1})
    _wait(host, slug)
    calls = model.steps("rewrite")
    assert len(calls) == 2 and "Let the person pick — a setting" in calls[1]["prompt"] and "never ask again" in calls[1]["prompt"]
    node = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert node["fork"] is None and set(node["rewrite"]["ids"]) == {a, b} and _gist(host, slug).startswith("Add a dark mode the person picks in the settings.")
    host.command("ideas.undo_rewrite", {"idea": slug})                                            # the fork's items are open again
    assert _gist(host, slug) == before
    assert {i["state"] for r in idea_say.leaders(host.ideas.state_dir, slug) for i in r["better"]} == {"open"}


# -- judging again ----------------------------------------------------------------------------------------------------------------------------

def _verdicts(model, parties, **by):
    """The `talk_verdict` answer of each party named (a dict, or a callable of the call)."""
    for who, said in by.items():
        model.said[("talk_verdict", parties[who])] = said


def _spoken_three(host, parties, model, per=1, **more):
    _say_round(model, parties, per, product={"verdict": "doubt", "why": "not now"}, design={"better": [{"line": "d", "weight": "same"}]}, tech={"better": [{"line": "t", "weight": "same"}]}, **more)
    return _talk(host, parties, ["product", "design", "tech"], GOAL)


def test_all_answered_judges_again_by_itself_and_the_second_round_is_the_last(host, parties, model):
    product, design, tech = parties["product"], parties["design"], parties["tech"]
    slug = _spoken_three(host, parties, model, per=0)
    _verdicts(model, parties, product={"verdict": "doubt", "why": "still not now"}, design={"verdict": "go"}, tech={"verdict": "go"})
    model.said[("rewrite", "")] = {"gist": "Rewritten."}
    host.command("ideas.leave_say", {"idea": slug, "id": _id(host, slug, design, "b")})
    assert model.steps("talk_verdict") == []                                                      # Tech's is still open: not yet
    host.command("ideas.take_better", {"idea": slug, "id": _id(host, slug, tech, "b")})
    _settle(host, slug)                                                                            # the rewrite, then (all answered) the judging again
    judged = model.steps("talk_verdict")
    assert sorted(c["party"] for c in judged) == sorted([product, design, tech]) and all(c["tools"] is False for c in judged)
    told = {c["party"]: c["prompt"] for c in judged}
    assert "Taken, and now written into the goal's words:" in told[tech] and "(yours)" in told[tech] and "Turned down:" in told[design]
    assert "What the person took and turned down" in told[product] and "(yours)" not in told[product]
    say = idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)
    assert say["judged"] == 1 and say["judge_left"] == 1 and say["to_judge"] == [product]            # Product still doubts; the others' marks are cleared
    n = len(judged)
    out = host.command("ideas.judge_again", {"idea": slug})                                         # Judge again now: the second and last time
    _settle(host, slug)
    assert out["parties"] == [product] and [c["party"] for c in model.steps("talk_verdict")[n:]] == [product]
    assert idea_say.node(host.ideas.root(), host.ideas.state_dir, slug)["judge_left"] == 0
    with pytest.raises(Exception, match="judged it twice"):
        host.command("ideas.judge_again", {"idea": slug})
    assert len(model.steps("talk_verdict")) == n + 1
    assert [e["parties"] for e in _events(host, event_log.JUDGED_AGAIN)] == [[product, design, tech], [product]]


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def test_a_taken_one_waiting_is_written_before_the_leaders_judge(host, parties, model):
    tech = parties["tech"]
    slug = _spoken(host, parties, model, tech={"better": [{"line": "t", "weight": "same"}]})
    model.said[("rewrite", "")] = {"fork": {"ask": "?", "choices": ["x", "y"], "between": []}}
    host.command("ideas.take_better", {"idea": slug, "id": _id(host, slug, tech, "b")})
    _settle(host, slug)
    with pytest.raises(Exception, match="choose first"):
        host.command("ideas.judge_again", {"idea": slug})                                            # a fork waits: the person's choice comes first

