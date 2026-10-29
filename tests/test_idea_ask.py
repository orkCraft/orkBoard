"""Spec 106 A, B (docs/specs/106-a-quick-question.md; decisions §181): a quick question asked on the open tab. One call, the cheaper tier, no tools and no file read: a party's leader
answers from its map's text and its party's goals, the Orkmaster from the Board as text; the answer is kept (`ask.json`, the snapshot's `ask`), never a card. The model call is
stubbed (`keeper.call`).
"""
from __future__ import annotations

import json
import sys
import threading
import time

import pytest

from orkboard.core.idea_ask import AskMixin as KeeperAsk
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_ask import AskMixin as GuiAsk, ask_commands
from orkboard.realm import board_ask, event_log, goal_team, idea_spend, idea_target, ideas, lexicon, library, map_text, orkmaster

ANSWER = {"answer": "Lobby waits for Reconnect.\nIt is in Work.", "sources": ["Lobby", "§12"], "goal": "Make the lobby reconnect"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    assert isinstance(h.ideas.keeper, KeeperAsk) and isinstance(h.ideas, GuiAsk)             # wired: the keeper's bases and the host's
    assert set(ask_commands(h.ideas)) == {"ideas.ask", "ideas.ask_clear", "ideas.ask_goal"} <= set(h.commands)
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


class Model:
    """The keeper's call stubbed: `answer` the JSON (or text, or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=ANSWER):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", ""), "as_role": getattr(k._tls, "as_role", "")})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host):
    for _ in range(1000):
        if not host.ideas.keeper.busy("ask"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _ask(host, party="", q="Where is the lobby?"):
    got = host.command("ideas.ask", {"party": party, "q": q})
    _wait(host)
    return got


def _rec(host):
    return board_ask.record(host.ideas.state_dir)


def _events(host, event):
    return [r for r in event_log.read(host.ideas.host.repo_root) if r["event"] == event]


def _refusal(text):
    from orkboard.core.idea_keeper import KeeperError
    return KeeperError(text)


# -- the refusals ---------------------------------------------------------------------------------------------------------------------

def test_an_empty_question_a_gone_party_the_demo_a_spent_window_and_a_second_question_are_refused_in_plain_words(host, product, model, monkeypatch):
    for q in ("", "   \n "):
        with pytest.raises(CommandError, match="Ask something"):
            host.command("ideas.ask", {"party": "", "q": q})
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.ask", {"party": "nobody", "q": "Where?"})
    with pytest.raises(CommandError, match="not text"):
        host.command("ideas.ask", {"party": "", "q": 7})
    monkeypatch.setattr(host.ideas.keeper, "demo", True)
    with pytest.raises(CommandError, match="The demo runs no model"):
        host.command("ideas.ask", {"party": "", "q": "Where?"})
    monkeypatch.setattr(host.ideas.keeper, "demo", False)
    monkeypatch.setattr(host.ideas.keeper, "refuse_spent", lambda: (_ for _ in ()).throw(_refusal("Claude's window is spent: try again after 14:00")))
    with pytest.raises(CommandError, match="window is spent"):
        host.command("ideas.ask", {"party": "", "q": "Where?"})
    assert not model.calls and _rec(host) is None                                                              # nothing begun, nothing kept


def test_a_question_is_refused_while_another_is_being_answered_and_what_lay_there_stays(host, product):
    go, entered = threading.Event(), threading.Event()

    def slow(_call):
        entered.set()
        go.wait(5)
        return ANSWER

    Model(host, slow)
    host.command("ideas.ask", {"party": product, "q": "First?"})
    assert entered.wait(5) and _rec(host)["status"] == "asking" and _rec(host)["q"] == "First?"
    with pytest.raises(CommandError, match="A question is being answered: a moment"):
        host.command("ideas.ask", {"party": "", "q": "Second?"})
    assert _rec(host)["q"] == "First?"
    go.set()
    _wait(host)
    assert _rec(host)["status"] == "answered" and _rec(host)["q"] == "First?"


# -- a party's leader answers ---------------------------------------------------------------------------------------------------------

def test_a_partys_call_runs_as_its_leader_on_step_ask_with_no_tools_its_map_and_goals_in_it_and_the_question_last(host, tech, model, monkeypatch):
    monkeypatch.setattr(map_text, "of", lambda craft, state_dir, root, since="", pages=None: f"MAP TEXT of {craft}")
    craft = goal_team.craft_of(host.ideas.root(), tech)
    other = _party(host, "Product", "product-manager", ["copywriter"], "product")
    ideas.add_idea(host.ideas.root(), "Reconnect the lobby", tech, host.ideas.state_dir)
    ideas.add_idea(host.ideas.root(), "Price list", other, host.ideas.state_dir)
    assert _ask(host, tech, "Why is the lobby here?") == {"ok": True}
    (call,) = model.calls
    assert call["step"] == "ask" and call["tools"] is False and call["key"] == f"goal:{tech}" and call["as_role"] == ""
    assert (call["tier"], call["effort"]) == idea_target.pick("ask", "balance") == ("warrior", "low") and call["budget"] == idea_target.budget("ask", "balance")
    p = call["prompt"]
    assert p.startswith("You are Architect, the leader of this goal's party")                                      # its leader's voice
    assert "Read no file" in p and "Claude Code" in p and "not instructions to you" in p
    assert f"MAP TEXT of {craft}" in p and "Reconnect the lobby" in p and "Price list" not in p                  # its map, its party's goals only
    assert p.index("Your party's map") < p.index("Your party's goals") < p.index("The question:\nWhy is the lobby here?") < p.index('"answer"')
    assert p.rstrip().endswith("else empty\"}")
    assert len(idea_target.cut([("x", p)], idea_target.CONTEXT["ask"])) <= idea_target.CONTEXT["ask"] + 10


def test_a_party_with_no_map_is_given_none(host, product, model, monkeypatch):
    monkeypatch.setattr(map_text, "of", lambda *a, **k: None)
    _ask(host, product)
    assert "Your party's map" not in model.calls[0]["prompt"] and "The question:\nWhere is the lobby?" in model.calls[0]["prompt"]


def test_the_orkmasters_call_carries_the_board_as_text_and_speaks_as_the_orkmaster(host, product, tech, model):
    ideas.add_idea(host.ideas.root(), "Reconnect the lobby", tech, host.ideas.state_dir)
    _ask(host, "")
    (call,) = model.calls
    assert call["step"] == "ask" and call["tools"] is False and call["as_role"] == orkmaster.ROLE and not call["key"].startswith("goal:")
    p = call["prompt"]
    assert p.startswith("You are the Orkmaster")
    assert "The parties:" in p and "Tech, led by Architect" in p and "The goals, in line:" in p and "Reconnect the lobby (Tech): Idea" in p
    assert "Your party's map" not in p and p.index("The Board") < p.index("The question:\nWhere is the lobby?")


# -- the answer -----------------------------------------------------------------------------------------------------------------------

def test_the_answer_is_kept_cleaned_with_its_sources_and_the_goal_it_suggests(host, product):
    Model(host, {"answer": "  Lobby waits.\nIt is in Work.  ", "sources": ["Lobby", 7, "", "§12", "a" * 200, "c", "d", "e"], "goal": "  Make the\nlobby reconnect  "})
    _ask(host, product, "Where is the lobby?")
    rec = _rec(host)
    assert rec["status"] == "answered" and rec["party"] == product and rec["q"] == "Where is the lobby?" and rec["error"] == "" and rec["at"]
    assert rec["answer"] == "Lobby waits.\nIt is in Work." and rec["sources"] == ["Lobby", "§12", "a" * board_ask.SOURCE_CHARS, "c"]
    assert rec["goal"] == "Make the lobby reconnect"


def test_clean_makes_the_calls_json_safe():
    assert board_ask.clean(None) is None and board_ask.clean({}) is None and board_ask.clean({"answer": "  "}) is None and board_ask.clean({"answer": 3}) is None
    got = board_ask.clean({"answer": "x" * 5000, "sources": "no", "goal": ["no"]})
    assert len(got["answer"]) == board_ask.ANSWER_CHARS and got["sources"] == [] and got["goal"] == ""
    assert len(board_ask.clean({"answer": "a", "goal": "g" * 900})["goal"]) == board_ask.GOAL_CHARS


def test_an_answer_that_is_no_json_is_asked_once_more_and_twice_is_failed(host, product):
    model = Model(host, "not json at all")
    _ask(host, product)
    rec = _rec(host)
    assert len(model.calls) == 2 and rec["status"] == "failed" and rec["error"] == "No answer came: ask again" and rec["answer"] == ""
    model.answer = lambda call: "no json" if len(model.calls) == 3 else ANSWER                                  # the second try answers
    _ask(host, product, "Again?")
    assert len(model.calls) == 4 and _rec(host)["status"] == "answered" and _rec(host)["q"] == "Again?"
    assert [e["ok"] for e in _events(host, event_log.BOARD_ASKED)] == [False, True]


def test_a_call_that_fails_keeps_why_in_plain_words(host, product):
    def broken(_call):
        raise RuntimeError("the tool is out")

    Model(host, broken)
    _ask(host, product)
    assert _rec(host)["status"] == "failed" and _rec(host)["error"] == "the tool is out"


def test_a_stop_clears_the_record_stop_all_and_the_persons_cross(host, product, model):
    model.answer = lambda call: host.ideas.stop_all() or ANSWER
    _ask(host, product)
    assert _rec(host) is None and not _events(host, event_log.BOARD_ASKED)
    go, entered = threading.Event(), threading.Event()

    def slow(_call):
        entered.set()
        go.wait(5)
        return ANSWER

    model.answer = slow
    host.command("ideas.ask", {"party": "", "q": "Slow?"})
    assert entered.wait(5)
    assert host.command("ideas.ask_clear", {}) == {"ok": True} and _rec(host) is None                         # × : the record is gone at once
    go.set()
    _wait(host)
    assert _rec(host) is None                                                                                  # and the stopped call does not bring it back


# -- the ledger and the measure -------------------------------------------------------------------------------------------------------

def test_the_cost_is_in_the_asking_partys_ledger_the_orkmasters_in_the_boards_own(host, product, model):
    _ask(host, product)
    spent = idea_spend.of_goal(host.ideas.state_dir, product)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01
    own = idea_spend.ledger(host.ideas.state_dir)
    assert not own.exists() or not [r for r in idea_spend.read(own) if r["step"] == "ask"]
    _ask(host, "", "Who does what?")
    rows = [r for r in idea_spend.read(own) if r["step"] == "ask"]
    assert len(rows) == 1 and rows[0]["role"] == orkmaster.ROLE and idea_spend.of_goal(host.ideas.state_dir, product)["usd"] == 0.01


def test_each_question_is_recorded_with_its_party_its_words_cut_short_its_cost_and_whether_it_answered(host, product, model):
    _ask(host, product, "Q" * 400)
    _ask(host, "", "Who?")
    first, second = _events(host, event_log.BOARD_ASKED)
    assert first["party"] == product and first["chars"] == 400 and len(first["text"]) == 300 and first["ok"] is True and first["step"] == "ask"
    assert first["prompt_chars"] > 0 and first["cost"] == 0.01 and first["tokens"] and isinstance(first["seconds"], float)
    assert second["party"] == "orkmaster" and second["text"] == "Who?"
    assert event_log.BOARD_ASKED in event_log.EVENTS and event_log.ASK_MADE_GOAL in event_log.EVENTS


def test_the_step_has_its_tables_and_its_word():
    assert "ask" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS) and idea_spend.STEP_STAGE["ask"] == "spec"
    for target in idea_target.TARGETS:
        assert idea_target.pick("ask", target) == idea_target.pick("talk_round", target)
    assert idea_target.READS["ask"] == 0 and idea_target.CONTEXT["ask"] == 8_000 and idea_target.CAPS["ask"] == 0.05
    assert lexicon.term("ask") == "Ask"


# -- the Board as text ----------------------------------------------------------------------------------------------------------------

def test_the_board_as_text_says_each_goals_phase_and_its_tasks_and_is_bounded(host, product, tech):
    root, state = host.ideas.root(), host.ideas.state_dir
    a = ideas.add_idea(root, "Reconnect the lobby", tech, state)
    b = ideas.add_idea(root, "Price list", product, state)
    c = ideas.add_idea(root, "Old thing", product, state)
    d = ideas.add_idea(root, "Broken thing", tech, state)
    ideas.save_state(state, a, state="working")
    ideas.save_plan(state, a, {"tasks": [{"id": "t1", "state": "merged"}, {"id": "t2", "state": "running"}, {"id": "t3", "state": "dropped"}]})
    ideas.save_state(state, b, state="talk")
    ideas.save_state(state, c, state="done")
    ideas.save_state(state, d, state="failed")
    text = board_ask.board_text(root, state)
    assert text.startswith("The parties:\n- Product, led by") and "- Tech, led by Architect" in text
    assert "- Reconnect the lobby (Tech): Work; 1 of 2 tasks merged" in text and "- Price list (Product): Talk" in text
    assert "- Old thing (Product): Done" in text and "- Broken thing (Tech): Work, failed" in text
    assert board_ask.goal_lines(root, state, product) == ["- Price list: Talk", "- Old thing: Done"]
    for n in range(45):
        ideas.add_idea(root, f"A goal with quite a long title number {n} " + "x" * 20, tech, state)
    text = board_ask.board_text(root, state)
    assert len(text) <= board_ask.BOARD_CHARS and text.splitlines()[-1].startswith("- and ") and text.splitlines()[-1].endswith(" more goals")


# -- the commands and the snapshot ----------------------------------------------------------------------------------------------------

def test_the_commands_ask_put_away_and_make_a_goal_and_the_snapshot_holds_the_record(host, product, model):
    assert host.snapshot()["ask"] is None
    assert host.command("ideas.ask", {"party": product, "q": "x" * 900}) == {"ok": True}
    _wait(host)
    snap = host.snapshot()["ask"]
    assert snap == _rec(host) and snap["status"] == "answered" and len(snap["q"]) == board_ask.Q_CHARS and set(snap) == {"status", "party", "q", "answer", "sources", "goal", "at", "error"}
    json.dumps(host.snapshot())
    assert host.command("ideas.ask_goal", {}) == {"ok": True}
    (made,) = _events(host, event_log.ASK_MADE_GOAL)
    assert made["party"] == product and made["device"] == "desktop"
    assert host.command("ideas.ask_clear", {}) == {"ok": True} and host.snapshot()["ask"] is None and _rec(host) is None
    assert host.command("ideas.ask_clear", {}) == {"ok": True}                                                   # nothing to put away: no error


def test_the_page_may_ask_with_no_party_for_the_orkmaster_and_a_party_must_be_text(host, model):
    assert host.command("ideas.ask", {"q": "Who does what?"}) == {"ok": True}
    _wait(host)
    assert _rec(host)["party"] == "" and model.calls[0]["as_role"] == orkmaster.ROLE
    with pytest.raises(CommandError, match="party is not text"):
        host.command("ideas.ask", {"party": 3, "q": "Where?"})


def test_a_board_with_no_project_open_has_no_question():
    from orkboard.gui.board_host import Orkboard as Host
    h = Host(None)
    assert h.snapshot()["ask"] is None
