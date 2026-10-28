"""Spec 100 F (docs/specs/100-a-goals-way-as-cards.md §5b) on the host: `ideas.project_facts` and `ideas.project_fact_set` (the facts kept for a party's calls, read and changed),
`ideas.project_kind_set` (the person's correction of what the project is), `ideas.talk_read` (a goal's Talk as kept). Keys and data, never words but a refusal's. The model call is
stubbed (`keeper.call`).

These tests compose the mixin onto the host the way the lead's wiring does (the `host` fixture): they pass without that wiring in `gui/ideas.py`.
"""
from __future__ import annotations

import json
import sys
import time

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.gui.ideas_facts import FactsMixin, facts_commands
from orkboard.realm import goal_team, idea_questions, ideas, library, project_facts, project_kind, project_stage

COMMANDS = {"ideas.project_facts", "ideas.project_fact_set", "ideas.project_kind_set", "ideas.talk_read"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas, FactsMixin):                                  # wired by the lead: the host's bases and its table
        h.ideas.__class__ = type("IdeasWithFacts", (FactsMixin, type(h.ideas)), {})
        h.commands.update(facts_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def model(host):
    seen: list[dict] = []

    def call(tier, prompt, effort="", budget=None):
        step = host.ideas.keeper.measure()["step"]
        seen.append({"step": step, "prompt": prompt})
        if step == "talk_round":
            out = {"stance": "For it", "for": "Players want it", "against": "It costs", "questions": [
                {"ask": "Which first?", "choices": ["Web", "Phone"], "pick": 1, "why": "most players are on phones", "blocks": True},
                {"ask": "Dark too?", "choices": ["Yes", "No"], "pick": 0, "why": "cheap", "blocks": False}]}
        else:
            out = {"title": "A goal", "questions": []}
        return json.dumps(out), 0.01, 10, ""

    host.ideas.keeper.call = call
    return seen


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


def _wait(host, slug):
    for _ in range(1000):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


# -- the commands are the host's and a phone's ------------------------------------------------------------------------------------------

def test_the_commands_are_the_hosts_and_a_phones(host):
    assert COMMANDS == set(facts_commands(host.ideas)) and COMMANDS <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in COMMANDS)


# -- the facts of a party -----------------------------------------------------------------------------------------------------------------

def test_the_facts_kept_for_a_party_are_keys_texts_and_who_gave_them_in_the_order_kept(host, tech):
    assert host.command("ideas.project_facts", {"party": tech}) == {"facts": []}
    project_facts.keep(host.ideas.state_dir, tech, "stack", "Plain Python", "read")
    project_facts.keep(host.ideas.state_dir, tech, "runs_on", "Node 20", "person")
    project_facts.keep(host.ideas.state_dir, "orkmaster", "for_whom", "Friends at one TV", "person")
    assert host.command("ideas.project_facts", {"party": tech}) == {"facts": [{"key": "stack", "text": "Plain Python", "by": "read"},
                                                                              {"key": "runs_on", "text": "Node 20", "by": "person"}]}
    assert host.command("ideas.project_facts", {"party": "orkmaster"}) == {"facts": [{"key": "for_whom", "text": "Friends at one TV", "by": "person"}]}


def test_a_fact_set_is_the_persons_and_read_into_the_partys_calls_an_empty_text_drops_it(host, tech):
    got = host.command("ideas.project_fact_set", {"party": tech, "key": "stack", "text": "  Plain   Python,\nno framework "})
    assert got == {"ok": True, "facts": [{"key": "stack", "text": "Plain Python, no framework", "by": "person"}]}
    assert "- Plain Python, no framework" in project_facts.for_call(host.ideas.state_dir, tech)
    project_facts.keep(host.ideas.state_dir, tech, "stack", "Rust", "read")                             # a reading never takes the person's word
    assert host.command("ideas.project_facts", {"party": tech})["facts"][0]["text"] == "Plain Python, no framework"
    host.command("ideas.project_fact_set", {"party": tech, "key": "stack", "text": "Go"})                  # the person's own again replaces
    assert host.command("ideas.project_facts", {"party": tech})["facts"] == [{"key": "stack", "text": "Go", "by": "person"}]
    dropped = host.command("ideas.project_fact_set", {"party": tech, "key": "stack", "text": "   "})
    assert dropped == {"ok": True, "dropped": True, "facts": []} and project_facts.for_call(host.ideas.state_dir, tech) == ""
    assert host.command("ideas.project_fact_set", {"party": tech, "key": "stack", "text": ""}) == {"ok": True, "facts": []}      # nothing to drop is not a refusal


def test_a_common_fact_set_is_the_common_core_and_dropped_leaves_it(host, tech):
    host.command("ideas.project_fact_set", {"party": tech, "key": "for_whom", "text": "Friends at one TV"})
    assert project_facts.common(host.ideas.state_dir) == "Whom it is for: Friends at one TV" and "for_whom" in project_facts.answered(host.ideas.state_dir)
    host.command("ideas.project_fact_set", {"party": tech, "key": "for_whom", "text": ""})
    assert project_facts.common(host.ideas.state_dir) == "" and "for_whom" not in project_facts.answered(host.ideas.state_dir)


def test_the_facts_commands_check_their_arguments_in_plain_words(host, tech):
    for name in ("ideas.project_facts", "ideas.project_fact_set"):
        with pytest.raises(CommandError, match="party is missing"):
            host.command(name, {})
        with pytest.raises(CommandError, match="No such party"):
            host.command(name, {"party": "nobody", "key": "stack", "text": "x"})
    with pytest.raises(CommandError, match="party is not text"):
        host.command("ideas.project_facts", {"party": 3})
    with pytest.raises(CommandError, match="key is missing"):
        host.command("ideas.project_fact_set", {"party": tech, "text": "x"})
    with pytest.raises(CommandError, match="Not a fact's key: 'Bad Key'"):
        host.command("ideas.project_fact_set", {"party": tech, "key": "Bad Key", "text": "x"})
    with pytest.raises(CommandError, match="text is not text"):
        host.command("ideas.project_fact_set", {"party": tech, "key": "stack", "text": 3})
    assert project_facts.of(host.ideas.state_dir, tech) == []


# -- the kind ---------------------------------------------------------------------------------------------------------------------------------

def test_the_persons_kind_is_kept_in_project_json_beside_the_stage_and_read_before_the_files(host):
    repo = host.ideas.keeper.repo_root
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    assert host.command("ideas.proposals", {})["kind"]["id"] == "code" and project_kind.kept(host.ideas.state_dir) == ""      # read from the files
    project_stage.keep(host.ideas.state_dir, "live")
    got = host.command("ideas.project_kind_set", {"kind": "game"})
    assert got == {"ok": True, "kind": {"id": "game", "words": "a game", "signs": [], "kept": True}}
    assert json.loads((host.ideas.state_dir / "project.json").read_text()) == {"stage": "live", "kind": "game"}         # the stage kept
    shown = host.command("ideas.proposals", {})                                                         # the proposals are the kept kind's
    assert shown["kind"]["id"] == "game" and shown["kind"]["words"] == "a game" and shown["proposals"]
    assert host.command("ideas.party_presets", {})["kind"]["id"] == "game"
    assert host.command("ideas.stage", {})["kind"] == "game"
    assert project_stage.read(repo) == "being_made"                                                      # the stage's read still counts the code


def test_a_kind_that_is_none_is_refused_in_plain_words_and_nothing_is_kept(host):
    for bad in ({}, {"kind": ""}, {"kind": "castle"}, {"kind": "Game"}):
        with pytest.raises(CommandError, match="kind is missing" if bad.get("kind", None) in (None, "") else "A kind is one of empty, mobile, game, web, backend, data, wiki, design, texts, code"):
            host.command("ideas.project_kind_set", bad)
    with pytest.raises(CommandError, match="kind is not text"):
        host.command("ideas.project_kind_set", {"kind": 3})
    assert project_kind.kept(host.ideas.state_dir) == ""


# -- Talk read ------------------------------------------------------------------------------------------------------------------------------

def test_a_goal_not_talked_has_an_empty_talk_and_a_goal_that_is_gone_is_refused(host, tech):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    assert host.command("ideas.talk_read", {"idea": slug}) == {"idea": slug, "mode": "", "round": 1, "done": False, "stances": [], "cause": None}
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.talk_read", {"idea": "nobody"})
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.talk_read", {})


def test_the_talk_as_kept_has_each_leaders_stance_for_against_and_its_questions_waiting_then_answered(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _wait(host, slug)
    got = host.command("ideas.talk_read", {"idea": slug})
    json.dumps(got)                                                                                       # all data
    assert (got["mode"], got["round"], got["done"], got["cause"]) == ("talk", 1, False, None)
    (stance,) = got["stances"]
    assert (stance["party"], stance["leader"], stance["stance"], stance["for"], stance["against"]) == (tech, "architect", "For it", "Players want it", "It costs")
    assert [(q["q"], q["state"]) for q in stance["questions"]] == [("Which first?", "waiting"), ("Dark too?", "waiting")]
    card, other = stance["questions"]
    assert card["choices"] == ["Web", "Phone"] and card["pick"] == 1 and card["why"] == "most players are on phones" and card["project"] is False
    assert "answer" not in card and set(card) == {"id", "q", "choices", "pick", "why", "project", "state"}
    host.ideas.keeper.decide = lambda s: None                                                              # part E's seam
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": card["id"], "text": "Both, phone first"}], "decide": True})
    after = {q["id"]: q for q in host.command("ideas.talk_read", {"idea": slug})["stances"][0]["questions"]}
    assert (after[card["id"]]["state"], after[card["id"]]["answer"], after[card["id"]]["how"], after[card["id"]]["round"]) == ("answered", "Both, phone first", "text", 1)
    assert (after[other["id"]]["state"], after[other["id"]]["answer"], after[other["id"]]["how"]) == ("answered", "Yes", "decide")      # left to the leader's pick
    assert not [q for q in after.values() if q["state"] == "waiting"]


def test_the_talk_read_groups_the_questions_by_their_party_and_reads_a_bugs_cause(host, tech):
    slug = host.command("ideas.add", {"text": "Saving crashes when the file is empty", "track": tech})["slug"]
    card = {"id": "c1", "by": "tech", "leader": "architect", "q": "Where does it happen?", "choices": ["Lobby", "Game"], "pick": 0, "why": "the report", "project": False}
    rec = {"mode": "bug", "round": 2, "stances": [{"party": "design", "leader": "product-designer", "stance": "Careful", "for": "a", "against": "b"}],
           "waiting": [card], "answers": [{**card, "id": "c0", "answer": "Lobby", "how": "pick", "round": 1}],
           "defaults": [{"id": "c2", "by": "design", "leader": "product-designer", "q": "Dark?", "answer": "Yes", "why": "", "project": True, "round": 1}],
           "cause": {"text": "the timer is not reset", "where": ["src/app.py"], "by": "leader", "pending": True, "guesses": 1, "confirmed": False}, "done": True}
    idea_questions.save_record(host.ideas.state_dir, slug, rec)
    got = host.command("ideas.talk_read", {"idea": slug})
    assert (got["mode"], got["round"], got["done"]) == ("bug", 2, True)
    assert got["cause"] == {"text": "the timer is not reset", "where": ["src/app.py"], "by": "leader", "pending": True, "confirmed": False}
    by = {s["party"]: s for s in got["stances"]}
    assert list(by) == ["design", "tech"]                                                                  # a party with questions and no stance has one of its own, with no words
    assert (by["tech"]["stance"], by["tech"]["for"], by["tech"]["leader"]) == ("", "", "")
    assert [(q["id"], q["state"]) for q in by["tech"]["questions"]] == [("c0", "answered"), ("c1", "waiting")]
    (closed,) = by["design"]["questions"]
    assert (closed["state"], closed["answer"], closed["project"], closed["choices"], closed["pick"]) == ("closed", "Yes", True, [], None) and "how" not in closed
