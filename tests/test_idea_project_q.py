"""Spec 99 G (docs/specs/99-a-goals-way.md §8, decisions §153.1–§153.4, §157.1): the project's questions at the first start. Product's leader (in a game Game design's) is called once,
cheaper tier, no tools, given the project's files by code, and asks two or three cards each only where the files do not say it (where they do, its reading is the card's pick); with
neither party the Orkmaster's one card. The row `project_q` lies after the other stacks and holds nothing back; `ideas.project_answer` keeps the answers (`project_facts.keep`),
Product's whom and hurts as a segment, and they are read into every leader's calls. The model call is stubbed (`keeper.call`).

These tests compose the mixins onto the keeper and the host the way the lead's wiring does (the `host` fixture): they pass without that wiring in `core/idea_keeper.py` and `gui/ideas.py`.
"""
from __future__ import annotations

import json
import sys
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_project_q import ProjectQMixin as KeeperProjectQ
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_project_q import ProjectQMixin as GuiProjectQ, project_q_commands
from orkboard.realm import board_map, board_rows, goal_team, idea_lens, idea_questions, idea_spend, idea_target, ideas, library, orkmaster, project_facts, project_questions


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    keeper, ideas_ = h.ideas.keeper, h.ideas
    keeper.__class__ = type("WiredKeeper", (KeeperProjectQ, type(keeper)), {})                 # the lead's wiring: the keeper's bases …
    ideas_.__class__ = type("WiredIdeas", (GuiProjectQ, type(ideas_)), {})                      # … and the host's, with its commands
    h.commands.update(project_q_commands(ideas_))
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


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


def card(key, pick=0, said=False, choices=("A", "B"), **more):
    return {"key": key, "ask": f"Question {key}?", "choices": list(choices), "pick": pick, "why": "because", "said": said, **more}


THREE = {"questions": [card("for_whom", said=True, choices=("Friends at one TV", "Players online")), card("hurts", choices=("Slow rounds", "Lost scores")),
                       card("leaves_out", choices=("Accounts", "Matchmaking", "Ads"))]}


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=THREE):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", ""), "tool": k.tool_now()})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"goal:{party}"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _ask(host, party=None):
    asked = host.command("ideas.project_ask", {})
    if party:
        _wait(host, party)
    return asked


def _row(host):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "project_q"), None)


def _readme(host, text):
    (host.ideas.keeper.repo_root / "README.md").write_text(text, encoding="utf-8")


# -- the call: Product's leader, the cheaper tier, no tools, the files by code --------------------------------------------------------------

def test_the_first_start_is_one_call_of_products_leader_on_the_cheaper_tier_with_no_tools_given_the_files_chosen_by_code(host, product, tech, model):
    _readme(host, "# Party Pad\n\nA party game for friends who share one TV.\n")
    (host.ideas.keeper.repo_root / "docs" / "decisions.md").write_text("## 1. SECRET DECISION TEXT\n", encoding="utf-8")
    assert _ask(host, product) == {"ok": True, "asked": True}
    (call,) = model.calls
    assert call["step"] == "project_q" and call["tools"] is False and call["key"] == f"goal:{product}"
    assert (call["tier"], call["effort"]) == idea_target.pick("project_q", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("project_q", "balance")
    p = call["prompt"]
    assert p.startswith("You are Product manager, the leader of this goal's party")                                  # its leader's voice
    assert "Party Pad" in p and "share one TV" in p and "docs/notes.md" in p and "first note" in p                  # the README and docs/'s top level, by their paths
    assert "SECRET DECISION TEXT" not in p                                                                         # the decisions file is never one of them
    assert "Read no file" in p                                                                                     # the files are here: it reads none
    for k in ("for_whom", "hurts", "leaves_out"):
        assert f'"{k}"' in p
    assert len(model.calls) == 1                                                                                   # one call, not one a card


def test_in_a_game_game_designs_leader_asks_and_product_before_it_when_both_are_there(host, model):
    game = _party(host, "Game design", "game-designer", ["level-designer"], "product")
    assert goal_team.craft_of(host.ideas.root(), game) == "game-design" and project_questions.party_of(host.ideas.root()) == game
    _ask(host, game)
    assert model.calls[0]["key"] == f"goal:{game}"
    both = _party(host, "Product", "product-manager", ["copywriter"], "product")
    assert project_questions.party_of(host.ideas.root()) == both


def test_the_call_runs_as_its_partys_step_in_the_specs_stage_of_its_partys_ledger(host, product, model):
    _ask(host, product)
    spent = idea_spend.of_goal(host.ideas.state_dir, product)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01                                           # the party's ledger, the specs stage
    assert idea_spend.STEP_STAGE["project_q"] == "spec" and "project_q" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("project_q", target) == idea_target.pick("talk_round", target)                     # the matrix of Talk's round
    assert idea_target.READS["project_q"] == 0 and idea_target.CONTEXT["project_q"] >= project_facts.START_CHARS * 3 and idea_target.CAPS["project_q"] <= 0.15


# -- the cards ------------------------------------------------------------------------------------------------------------------------

def test_the_row_is_the_leaders_stack_of_two_or_three_cards_where_the_files_say_it_the_reading_is_the_pick(host, product, model):
    _ask(host, product)
    rec = project_questions.record(host.ideas.state_dir)
    assert rec["status"] == "waiting" and rec["party"] == product and rec["leader"] == "product-manager" and rec["read"] == ["project-for_whom"]
    row = _row(host)
    assert row["kind"] == "project_q" and row["party"] == product and row["leader"] == "product-manager" and len(row["questions"]) == 3
    c = row["questions"][0]
    assert c == {"id": "project-for_whom", "by": product, "leader": "product-manager", "q": "Question for_whom?", "choices": ["Friends at one TV", "Players online"], "pick": 0,
                 "why": "because", "project": True}
    assert [q["id"] for q in row["questions"]] == ["project-for_whom", "project-hurts", "project-leaves_out"] and all(2 <= len(q["choices"]) <= 4 for q in row["questions"])
    assert row["blocks"] is False and "idea" not in row and row["text"] == "Question for_whom?"


def test_a_card_is_taken_strictly_a_key_once_a_key_answered_never_and_at_most_three(host, product):
    model = Model(host, {"questions": [card("hurts"), card("hurts", pick=1), card("for_whom", choices=("only",)), card("stack"), {"key": "leaves_out", "ask": "x"},
                                       card("leaves_out", pick=7), card("leaves_out", pick="B"), "no", card("for_whom", choices=("one", "two"))]})
    project_facts.keep(host.ideas.state_dir, product, "for_whom", "Players", "person")                           # answered already: never asked again
    _ask(host, product)
    assert "for_whom" not in model.calls[0]["prompt"].split("The questions")[1].split("Rules")[0]
    cards = project_questions.record(host.ideas.state_dir)["questions"]
    assert [c["id"] for c in cards] == ["project-hurts", "project-leaves_out"] and cards[0]["pick"] == 0 and cards[1]["pick"] == 1       # the first of a key; a pick by its words
    assert project_questions.clean({"questions": [card(k) for k in ("for_whom", "hurts", "leaves_out")]}, "p", "l", set())[2][1] == "leaves_out"
    assert project_questions.clean("no", "p", "l", set()) == [] and project_questions.clean({"questions": "no"}, "p", "l", set()) == []


def test_a_call_that_does_not_answer_is_tried_once_more_and_then_asks_nothing_and_may_be_asked_again(host, product):
    model = Model(host, "not json at all")
    _ask(host, product)
    assert len(model.calls) == 2                                                                                  # one more try
    rec = project_questions.record(host.ideas.state_dir)
    assert rec["status"] == "failed" and "did not answer" in rec["error"] and rec["questions"] == [] and _row(host) is None
    model.answer = THREE
    assert _ask(host, product)["asked"] is True and project_questions.record(host.ideas.state_dir)["status"] == "waiting" and _row(host) is not None


def test_a_project_is_asked_once_at_its_first_start(host, product, model):
    assert _ask(host, product)["asked"] is True
    assert _ask(host, product)["asked"] is False and len(model.calls) == 1                                        # asked, waiting
    host.command("ideas.project_answer", {"answers": [], "decide": True})
    assert _ask(host, product)["asked"] is False and len(model.calls) == 1 and _row(host) is None                 # answered or let go: never again


def test_with_all_three_facts_answered_nothing_is_asked(host, product, model):
    for k in project_questions.KEYS:
        project_facts.keep(host.ideas.state_dir, product, k, "kept", "person")
    assert _ask(host)["asked"] is False and not model.calls and project_questions.record(host.ideas.state_dir) == {}


def test_no_call_is_made_where_the_keeper_may_not_run_and_the_save_is_not_refused(host, product, model, monkeypatch):
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    assert _ask(host) == {"ok": True, "asked": False, "why": "Today's spend limit is reached: the keeper waits"}
    assert not model.calls and project_questions.record(host.ideas.state_dir) == {}                                 # nothing begun: asked at the next first start


# -- with neither party: the Orkmaster's one card -------------------------------------------------------------------------------------

def test_with_neither_party_there_is_no_call_and_the_orkmasters_one_card_what_is_this_project_for(host, tech, model):
    assert project_questions.party_of(host.ideas.root()) == ""
    assert _ask(host) == {"ok": True, "asked": True} and not model.calls
    row = _row(host)
    assert row["kind"] == "project_q" and row["party"] == "" and row["leader"] == orkmaster.ROLE == project_questions.ORKMASTER and len(row["questions"]) == 1
    c = row["questions"][0]
    assert c["q"] == "What is this project for?" and c["choices"] == [] and c["pick"] is None and c["project"] is True and c["by"] == "orkmaster"
    assert _ask(host)["asked"] is False
    got = host.command("ideas.project_answer", {"answers": [{"id": c["id"], "text": "  a mobile app for\n tennis clubs "}]})
    assert got == {"ok": True, "kept": [{"key": "for_whom", "by": "person"}]} and _row(host) is None
    assert project_facts.common(host.ideas.state_dir) == "Whom it is for: a mobile app for tennis clubs"            # the common core every leader's call is given


def test_the_orkmasters_card_let_go_keeps_nothing_and_leaves_the_hand(host, model):
    _ask(host)
    assert host.command("ideas.project_answer", {"decide": True}) == {"ok": True, "kept": []} and _row(host) is None and project_facts.answered(host.ideas.state_dir) == set()
    with pytest.raises(CommandError, match="The project asks nothing now"):
        host.command("ideas.project_answer", {"decide": True})


# -- the row among the stacks ---------------------------------------------------------------------------------------------------------

def test_the_row_lies_after_the_other_stacks_in_the_board_and_the_map_and_holds_nothing_back(host, product, model):
    root, state = host.ideas.root(), host.ideas.state_dir
    slug = host.command("ideas.add", {"text": "add a score board", "track": product})["slug"]
    ideas.save_state(state, slug, state="failed", error="it broke")                                                  # a stop that blocks
    _ask(host, product)
    needs = host.command("ideas.board")["needs_you"]
    assert needs[-1]["kind"] == "project_q" and any(n["kind"] == "failed" for n in needs[:-1])                      # after the others
    built = board_map.build(root, state, {}, [], 0.0)
    assert built["rows"] == board_rows.rows(state) == board_rows.project_q(state) and built["rows"][0]["kind"] == "project_q"
    assert host.command("ideas.map", {})["rows"][0]["questions"] == needs[-1]["questions"]
    host.command("ideas.project_answer", {"answers": [], "decide": True})
    assert board_map.build(root, state, {}, [], 0.0)["rows"] == [] and _row(host) is None                            # answered or let go, it leaves the hand
    assert board_rows.rows(state) == []


def test_the_row_is_a_pure_read_of_the_record_and_only_while_it_waits(tmp_path):
    sd = tmp_path / "s"
    assert board_rows.rows(sd) == []
    project_questions.save_record(sd, {"status": "asking", "party": "p", "leader": "l", "questions": [{"q": "x"}]})
    assert board_rows.rows(sd) == []
    project_questions.save_record(sd, {"status": "waiting", "party": "p", "leader": "l", "questions": []})
    assert board_rows.rows(sd) == []
    project_questions.save_record(sd, {"status": "waiting", "party": "p", "leader": "l", "questions": [{"q": "x?"}, "no"]})
    (row,) = board_rows.rows(sd)
    assert row["kind"] == "project_q" and row["questions"] == [{"q": "x?"}] and row["blocks"] is False


# -- the answers ----------------------------------------------------------------------------------------------------------------------

def test_the_answers_are_kept_as_the_projects_by_the_person_and_a_pick_left_to_the_leader_by_read(host, product, model):
    _ask(host, product)
    got = host.command("ideas.project_answer", {"answers": [{"id": "project-for_whom", "pick": 1}, {"id": "project-hurts", "text": "Waiting for the slowest player"}], "decide": True})
    assert got == {"ok": True, "kept": [{"key": "for_whom", "by": "person"}, {"key": "hurts", "by": "person"}, {"key": "leaves_out", "by": "read"}]}
    kept = {f["key"]: (f["text"], f["by"]) for f in project_facts.of(host.ideas.state_dir, product)}
    assert kept == {"for_whom": ("Players online", "person"), "hurts": ("Waiting for the slowest player", "person"), "leaves_out": ("Accounts", "read")}
    assert project_facts.common(host.ideas.state_dir).splitlines() == ["Whom it is for: Players online", "What hurts them: Waiting for the slowest player", "What it leaves out: Accounts"]
    assert project_questions.record(host.ideas.state_dir)["status"] == "done" and _row(host) is None
    assert project_facts.answered(host.ideas.state_dir) == set(project_questions.KEYS)


def test_the_answers_are_checked_every_card_answered_or_left_to_the_leader_and_only_cards_that_are_asked(host, product, model):
    _ask(host, product)
    with pytest.raises(CommandError, match="Answer every question, or let the leader decide"):
        host.command("ideas.project_answer", {"answers": [{"id": "project-hurts", "pick": 0}]})
    with pytest.raises(CommandError, match="That question is not asked now"):
        host.command("ideas.project_answer", {"answers": [{"id": "project-stack", "pick": 0}], "decide": True})
    with pytest.raises(CommandError, match="answers are a list"):
        host.command("ideas.project_answer", {"answers": [{"pick": 0}]})
    with pytest.raises(CommandError, match="answers are a list"):
        host.command("ideas.project_answer", {"answers": "all"})
    assert project_facts.answered(host.ideas.state_dir) == set() and _row(host) is not None                              # nothing kept, still asked
    host.command("ideas.project_answer", {"answers": [{"id": c["id"], "pick": 1} for c in _row(host)["questions"]]})
    assert [f["text"] for f in project_facts.of(host.ideas.state_dir, product)] == ["Players online", "Lost scores", "Matchmaking"]
    with pytest.raises(CommandError, match="The project asks nothing now"):
        host.command("ideas.project_answer", {"answers": []})


def test_a_pick_left_to_the_leader_never_replaces_a_persons_earlier_answer(host, product, model):
    _ask(host, product)
    project_facts.keep(host.ideas.state_dir, product, "leaves_out", "What I wrote myself", "person")                 # answered elsewhere while the stack waited
    got = host.command("ideas.project_answer", {"answers": [], "decide": True})
    assert got["kept"][-1] == {"key": "leaves_out", "by": "read"}
    kept = {f["key"]: f["text"] for f in project_facts.of(host.ideas.state_dir, product)}
    assert kept["leaves_out"] == "What I wrote myself" and project_facts.common(host.ideas.state_dir).splitlines()[-1] == "What it leaves out: What I wrote myself"


def test_products_whom_and_hurts_are_also_kept_as_a_segment_with_its_pain_for_products_map(host, product, model):
    state = host.ideas.state_dir
    _ask(host, product)
    host.command("ideas.project_answer", {"answers": [{"id": "project-for_whom", "text": "Friends at one TV"}, {"id": "project-hurts", "text": "Slow rounds"},
                                                      {"id": "project-leaves_out", "pick": 0}]})
    assert idea_lens.segments(state) == [{"segment": "Friends at one TV", "pains": ["Slow rounds"]}]


def test_a_segment_is_kept_only_for_products_party_and_a_later_answer_adds_to_it(host, tech):
    state = host.ideas.state_dir
    game = _party(host, "Game design", "game-designer", ["level-designer"], "product")
    model = Model(host)
    _ask(host, game)
    host.command("ideas.project_answer", {"answers": [], "decide": True})
    assert idea_lens.segments(state) == [] and project_facts.of(state, game)                                          # Game design keeps the facts, no segment
    host2 = host.ideas
    product = _party(host, "Product", "product-manager", ["copywriter"], "product")
    host2._segment(product, {"for_whom"})
    assert idea_lens.segments(state) == []                                                                              # nothing of Product's yet
    project_facts.keep(state, product, "for_whom", "Teams", "person")
    host2._segment(product, {"for_whom"})
    project_facts.keep(state, product, "hurts", "Meetings", "person")
    host2._segment(product, {"hurts"})
    assert idea_lens.segments(state) == [{"segment": "Teams", "pains": ["Meetings"]}]


def test_what_is_answered_is_read_into_every_leaders_calls_and_never_asked_again(host, product, tech, model):
    _ask(host, product)
    host.command("ideas.project_answer", {"answers": [{"id": "project-for_whom", "text": "Friends at one TV"}, {"id": "project-hurts", "text": "Slow rounds"},
                                                      {"id": "project-leaves_out", "text": "Accounts"}]})
    state = host.ideas.state_dir
    for party in (product, tech):                                                                                      # the common core to every leader, not only the asker
        text = project_facts.for_call(state, party, [{"party": product}, {"party": tech}])
        assert "Whom it is for: Friends at one TV" in text and "What hurts them: Slow rounds" in text and "What it leaves out: Accounts" in text
    assert project_facts.for_call(state, tech, [{"party": tech}], member=True) == ""                                    # a member is given none
    assert project_facts.answered(state) >= set(project_questions.KEYS)
    entry = {"party": tech, "leader": "architect"}                                                                       # Talk's round for Tech's leader reads them
    prompt = host.ideas.keeper.round_prompt(_goal(host, product), entry, [entry], 1, "", True, project_facts.answered(state))
    assert "Whom it is for: Friends at one TV" in prompt and "What it leaves out: Accounts" in prompt


def _goal(host, party):
    return host.command("ideas.add", {"text": "add a score board", "track": party})["slug"]


def _design(host, model):
    """A party the person saves with *Save party* (its goal is read by the keeper at once: that call is no question of the project's)."""
    slug = host.command("ideas.goal_save", {"about": "Docs.", "craft": "design", "leader": "product-designer", "team": ["accessibility-reviewer"]})["slug"]
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"goal:{slug}"):
            break
        time.sleep(0.01)
    return slug


# -- the trigger and the commands -----------------------------------------------------------------------------------------------------

def test_party_save_with_first_true_asks_the_project_and_without_it_does_not(host, product, model):
    goal = _design(host, model)
    host.command("ideas.party_save", {"goal": goal, "name": "Design alone"})
    assert not model.steps("project_q") and project_questions.record(host.ideas.state_dir) == {}
    got = host.command("ideas.party_save", {"goal": goal, "name": "Design alone", "replace": True, "first": True})
    assert set(got) == {"id"}                                                                                           # the save answers as it did
    _wait(host, product)
    assert len(model.steps("project_q")) == 1 and _row(host)["kind"] == "project_q"
    host.command("ideas.party_save", {"goal": goal, "name": "Design alone", "replace": True, "first": True})
    assert len(model.steps("project_q")) == 1                                                                           # asked once


def test_party_save_with_first_true_is_not_refused_where_the_questions_cannot_be_asked(host, product, model, monkeypatch):
    goal = _design(host, model)
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    assert set(host.command("ideas.party_save", {"goal": goal, "name": "Design alone", "first": True})) == {"id"} and not model.steps("project_q")


def test_party_save_with_first_true_is_not_refused_on_a_host_without_the_wiring(fake_repo):
    h = Orkboard(fake_repo)
    assert not hasattr(h.ideas, "project_start") and not hasattr(h.ideas.keeper, "project_ask")                       # the lead's wiring is not in yet
    goal = h.command("ideas.goal_save", {"about": "Docs.", "craft": "design", "leader": "product-designer", "team": ["accessibility-reviewer"]})["slug"]
    assert set(h.command("ideas.party_save", {"goal": goal, "name": "Design alone", "first": True})) == {"id"}


def test_the_commands_are_two(host):
    table = project_q_commands(host.ideas)
    assert set(table) == {"ideas.project_ask", "ideas.project_answer"} and all(callable(f) for f in table.values())


def test_the_host_returns_keys_and_data_never_interface_words_but_the_cards_it_is_given(host, product, model):
    _ask(host, product)
    row = _row(host)
    assert set(row) == {"kind", "party", "leader", "questions", "text", "blocks", "priority", "at"}
    assert json.dumps(host.command("ideas.project_answer", {"answers": [], "decide": True})).count("Let") == 0


def test_the_architecture_keeps_orkboards_rule(host):
    """The mixin is a keeper's: `realm/` has no face and core/ no gui import."""
    import orkboard.core.idea_project_q as core
    import orkboard.realm.board_rows as rows
    import orkboard.realm.project_questions as q
    for module in (core, rows, q):
        assert "orkboard.gui" not in open(module.__file__, encoding="utf-8").read().replace("`gui/", "")
    assert idea_keeper.KeeperError and idea_questions.CHOICES == (2, 4)
