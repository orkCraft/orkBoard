"""Spec 125 B (docs/specs/125-the-journals.md §B; decisions §203): the writers of the journals and the host's commands. Each row of the spec's table writes its one entry, with its scope, its kind, its goal and its
parts, in the product's words (the second person in a leader's journal, the third in the project's); `came_back` and `went_through` once a goal; a journal that cannot be written fails nothing; `ideas.journal`
and `ideas.journal_strike` and their refusals. The hosts are composed as Talk's, the concerns' and the project questions' tests compose them; the model call is stubbed (`keeper.call`).
"""
from __future__ import annotations

import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.gui.ideas_journal import JournalMixin, journal_commands
from orkboard.realm import concerns as store, goal_team, hypotheses, idea_questions, ideas, journal_notes, journals, lexicon, library, pitches, project_facts, project_questions
from tests import test_concerns as C, test_idea_project_q as PQ, test_idea_talk as T
from tests.test_gui_hearing import _no_goal, _throw, _until_sections, sections  # noqa: F401  (the fixture `sections`)
from tests.test_idea_talk import DECIDED, TECH_NO, _noes, _talk, parties  # noqa: F401  (the fixture `parties`)
from tests.test_idea_project_q import product  # noqa: F401  (the fixture)

PROJECT = journals.PROJECT


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.root()                                                    # the Board's tree stands: a decision is committed to dev
    assert isinstance(h.ideas, JournalMixin) and set(journal_commands(h.ideas)) <= set(h.commands)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def model(host):
    return T.Model(host)


@pytest.fixture
def pq_model(host):
    return PQ.Model(host)


@pytest.fixture
def app_host(fake_repo) -> Orkboard:
    """The concerns' host: a small React app on dev, so that Design has a map."""
    C.run(fake_repo, "checkout", "-q", "-b", "dev")
    for name, text in C.APP.items():
        (fake_repo / name).parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / name).write_text(text)
    C.run(fake_repo, "add", "-A")
    C.run(fake_repo, "commit", "-q", "-m", "an app")
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def state_of(host):
    return host.ideas.state_dir


def entries(host, scope=PROJECT, kind=None):
    return [e for e in journals.read(state_of(host), scope) if kind is None or e["kind"] == kind]


def one(host, scope, kind):
    got = entries(host, scope, kind)
    assert len(got) == 1, (scope, kind, got)
    return got[0]


def title_of(host, slug):
    return " ".join(ideas.idea_page(host.ideas.root(), slug).title.split())


def a_goal(host, text="Dark mode for the night"):
    return ideas.add_idea(host.ideas.root(), text, "general", state_of(host))


# -- the word -----------------------------------------------------------------------------------------------------------------------------------

def test_the_word_journal_is_in_the_glossary():
    assert next(t for t in lexicon.TERMS if t.key == "journal") == lexicon.Term("journal", "journal", "journals")


# -- a leader's stance in Talk's first round ----------------------------------------------------------------------------------------------------

def test_each_leader_keeps_what_it_said_in_the_first_round_in_its_own_journal(host, parties, model):
    _noes(model, parties, per=0, tech=TECH_NO, design={"verdict": "doubt", "why": "The contrast is low"})
    model.said[("decide", "")] = DECIDED
    slug = _talk(host, parties, ["product", "design", "tech"])
    title = title_of(host, slug)
    tech = one(host, parties["tech"], "stance")
    assert tech["text"] == f"On “{title}” you said no: It adds a third caller to server/ws" and tech["idea"] == slug and tech["on"] == []
    assert one(host, parties["design"], "stance")["text"] == f"On “{title}” you said doubt: The contrast is low"
    assert one(host, parties["product"], "stance")["text"] == f"On “{title}” you said go: product stance"          # a go has no why: the stance is its words
    assert entries(host, PROJECT) == []                                                                       # a leader's stance is no one else's


def test_a_stance_on_a_goal_with_marks_keeps_their_ids(host, parties, model):
    _noes(model, parties, per=0)
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    ideas.save_state(state_of(host), slug, marks=[{"map": "system", "id": "ws", "name": "ws"}, {"map": "system", "group": "g", "name": "g"}])
    host.command("ideas.route_set", {"idea": slug, "route": [parties["tech"]]})
    host.command("ideas.talk", {"idea": slug})
    T._wait(host, slug)
    assert one(host, parties["tech"], "stance")["on"] == ["ws"]


# -- a decision confirmed -----------------------------------------------------------------------------------------------------------------------

def test_a_decision_confirmed_is_the_projects_and_says_the_leaders_the_person_overruled(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO, design={"verdict": "doubt", "why": "The contrast is low"})
    _throw(host, slug, dir="right")
    _until_sections(host, slug)
    architect = host.ideas.keeper._name("architect")
    got = one(host, PROJECT, "decision")
    assert got["text"] == f"Decision 1: Dark mode (against {architect}: It adds a third caller to server/ws)" and got["idea"] == slug and got["ref"] == "1"
    over = one(host, parties["tech"], "overruled")
    assert over["text"] == f"The person went on with “{title_of(host, slug)}” against your no: It adds a third caller to server/ws" and over["idea"] == slug
    assert entries(host, parties["design"], "overruled") == []                                                 # a doubt is not a no


def test_a_decision_nobody_objected_to_is_the_projects_alone_with_its_number(host, parties, model, sections):
    slug = _no_goal(host, parties, model, design={"verdict": "doubt", "why": "The contrast is low"})
    _throw(host, slug, dir="right")
    _until_sections(host, slug)
    assert [e["text"] for e in entries(host, PROJECT, "decision")] == ["Decision 1: Dark mode"]
    assert entries(host, parties["design"], "overruled") == [] and entries(host, parties["tech"], "overruled") == []


# -- an objection answered ----------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("answer, kind, tail", [("drop", "heeded", "the person dropped it"), ("smaller", "heeded", "the person made it smaller"), ("go", "overruled", None)])
def test_an_answer_to_a_no_is_heeded_or_overruled_in_that_partys_journal(host, parties, model, answer, kind, tail):
    _noes(model, parties, per=0, tech=TECH_NO)
    host.ideas.keeper.decide = lambda s: None
    slug = _talk(host, parties, ["tech"])
    title = title_of(host, slug)                                                                              # a dropped goal's page is gone after
    host.command("ideas.objection", {"idea": slug, "party": parties["tech"], "answer": answer})
    got = one(host, parties["tech"], kind)
    assert got["idea"] == slug
    assert got["text"] == (f"Your no to “{title}” was heeded: {tail}" if tail else f"The person went on with “{title}” against your no: It adds a third caller to server/ws")
    assert entries(host, parties["tech"], "overruled" if kind == "heeded" else "heeded") == []


def test_a_no_put_later_is_heeded(host, parties, model):
    first = host.command("ideas.add", {"text": "add a lobby for the party game", "track": parties["product"], "hold": True})["slug"]
    slug = _no_goal(host, parties, model, product={"verdict": "no", "why": "The lobby comes first", "after": first})
    _throw(host, slug, dir="left")
    assert one(host, parties["product"], "heeded")["text"] == f"Your no to “{title_of(host, slug)}” was heeded: the person put it later"


def test_a_throw_writes_for_the_leaders_of_the_side_and_overrules_the_others_unless_the_goal_is_gone(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO, product={"verdict": "no", "why": "Not worth it before the lobby"})
    title = title_of(host, slug)
    _throw(host, slug, dir="up")                                                                              # Tech's smaller one: Product's no is overruled
    assert one(host, parties["tech"], "heeded")["text"] == f"Your no to “{title}” was heeded: the person made it smaller"
    assert one(host, parties["product"], "overruled")["text"] == f"The person went on with “{title}” against your no: Not worth it before the lobby"
    other = _no_goal(host, parties, model, text="add a light mode option", tech=TECH_NO, product={"verdict": "no", "why": "Not worth it before the lobby"})
    _throw(host, other, dir="left")                                                                           # Product's side drops the goal: Tech's no is none overruled
    assert [e["idea"] for e in entries(host, parties["product"], "heeded")] == [other]
    assert [e["idea"] for e in entries(host, parties["tech"]) if e["kind"] in ("heeded", "overruled")] == [slug]


# -- a hypothesis judged ------------------------------------------------------------------------------------------------------------------------

def test_a_hypothesis_judged_held_or_refuted_is_the_projects_and_an_unsure_one_is_not(host):
    held = host.command("ideas.hypothesis_set", {"text": "People want a sketch first", "signal": "most ask for one"})["item"]["id"]
    wrong = host.command("ideas.hypothesis_set", {"text": "People read the manual", "signal": "most open it"})["item"]["id"]
    host.command("ideas.hypothesis_judge", {"id": held, "state": "unsure", "why": "Two of five"})
    assert entries(host) == []
    host.command("ideas.hypothesis_judge", {"id": held, "state": "held", "why": "Clear enough to build on"})
    host.command("ideas.hypothesis_judge", {"id": wrong, "state": "refuted"})
    first, second = entries(host, PROJECT, "hypothesis")
    assert first["text"] == "“People want a sketch first” held: Clear enough to build on" and first["ref"] == "1" and first["idea"] == ""
    assert second["text"] == "“People read the manual” was refuted" and second["ref"] == "2"
    assert hypotheses.read(state_of(host))["items"][0]["verdict"]["decision"] == 1


# -- a goal reaches main, a goal dropped, a pitch passed ----------------------------------------------------------------------------------------

def test_a_goal_that_reaches_main_is_the_projects_once(host):
    slug = a_goal(host)
    ideas.save_state(state_of(host), slug, state="done")
    assert host.ideas._raise_flag(slug, "done") is True
    assert one(host, PROJECT, "done")["text"] == f"“{title_of(host, slug)}” is in main" and one(host, PROJECT, "done")["idea"] == slug
    assert host.ideas._raise_flag(slug, "gate") is False
    journal_notes.done(state_of(host), host.ideas.root(), slug)                                              # nor another way of the same goal
    assert len(entries(host, PROJECT, "done")) == 1


def test_a_goal_the_person_dropped_is_the_projects_with_its_why_when_the_command_carried_one(host):
    one_, two = a_goal(host, "Dark mode for the night"), a_goal(host, "Light mode for the day")
    title = title_of(host, one_)
    host.command("ideas.drop", {"slug": one_})
    host.command("ideas.drop", {"slug": two, "why": "Not before the lobby"})
    assert ideas.idea_page(host.ideas.root(), one_) is None
    plain, said = entries(host, PROJECT, "dropped")
    assert plain["text"] == f"“{title}” was dropped" and plain["idea"] == one_
    assert said["text"] == "“Light mode for the day” was dropped: Not before the lobby"


def test_a_pitch_passed_keeps_its_why_in_the_projects_journal(host):
    ideation = T._party(host, "Ideas", "investor", [], "product")
    slug = ideas.add_idea(host.ideas.root(), "A night mode pitch", ideation, state_of(host))
    ideas.save_state(state_of(host), slug, state="judged")
    assert pitches.is_pitch(host.ideas.root(), slug)
    host.command("ideas.pitch_pass", {"slug": slug, "why": "Not now,   not ever."})
    got = one(host, PROJECT, "pitch_passed")
    assert got["text"] == f"Pitch “{title_of(host, slug)}” passed: Not now, not ever." and got["idea"] == slug


# -- the brief ----------------------------------------------------------------------------------------------------------------------------------

def test_a_line_of_the_brief_the_person_answered_is_the_projects_and_one_left_to_the_leader_is_not(host, product, pq_model):
    PQ._ask(host, product)
    host.command("ideas.project_answer", {"answers": [{"id": "project-for_whom", "pick": 1}, {"id": "project-hurts", "text": "Waiting for the slowest player"}], "decide": True})
    assert [e["text"] for e in entries(host, PROJECT, "brief")] == ["Whom it is for: Players online", "What hurts them: Waiting for the slowest player"]   # leaves_out was read


def test_a_line_of_the_brief_set_or_dropped_by_hand_is_the_projects_and_a_fact_that_is_no_part_of_it_is_not(host, product):
    host.command("ideas.project_fact_set", {"party": product, "key": "why_us", "text": "One TV, no table"})
    host.command("ideas.project_fact_set", {"party": product, "key": "stack", "text": "Python"})
    host.command("ideas.project_fact_set", {"party": product, "key": "why_us", "text": ""})
    host.command("ideas.project_fact_set", {"party": product, "key": "why_us", "text": ""})                  # nothing left to drop: nothing kept
    assert [e["text"] for e in entries(host, PROJECT, "brief")] == ["Why this, not what they use now: One TV, no table", "Why this, not what they use now: dropped"]
    assert project_facts.of(state_of(host), product)[0]["key"] == "stack"


# -- a result decided at Review -----------------------------------------------------------------------------------------------------------------

class FakeRunner:
    def __init__(self, refuse=False):
        self.refuse = refuse

    def _go(self):
        if self.refuse:
            raise type("RunnerError", (Exception,), {})("Its tests are red: send it back")

    def merge(self, slug, tid, device="", dear=False):
        self._go()
        return "abc123"

    def back(self, slug, tid, why, device="", suggested=False):
        self._go()

    def drop_task(self, slug, tid, device=""):
        self._go()


def at_review(host, parties, stances=None, state="review"):
    """A goal with one task in `state` whose Talk left `stances` (Tech said no, Design doubted, Product went on)."""
    slug = a_goal(host, "A review idea")
    ideas.save_plan(state_of(host), slug, {"idea": slug, "made_at": "2026-10-17T09:00:00", "passed_at": None, "estimate": {"tasks": 1, "usd_low": 0.15, "usd_high": 0.45}, "todos": [],
                                           "tasks": [{"id": "k1", "title": "Do it", "brief": "b", "tier": "warrior", "after": [], "state": state, "branch": "", "commit": "", "session": "",
                                                      "cost": None, "tokens": None, "started": "", "finished": "", "error": "", "note": ""}]})
    idea_questions.save_record(state_of(host), slug, {"stances": stances if stances is not None else [
        {"party": parties["tech"], "verdict": "no", "why": "A third caller"}, {"party": parties["design"], "verdict": "doubt", "why": "Low contrast"},
        {"party": parties["product"], "verdict": "go", "why": ""}]})
    host.ideas._runner = FakeRunner()
    return slug


def test_a_merge_is_a_first_time_through_for_the_leaders_who_doubted_or_said_no_once_a_goal(host, parties):
    slug = at_review(host, parties)
    host.command("ideas.merge", {"slug": slug, "task": "k1"})
    title = "A review idea"
    assert one(host, parties["tech"], "went_through")["text"] == f"“{title}”, which you said no to, went through at Review the first time"
    assert one(host, parties["design"], "went_through")["text"] == f"“{title}”, which you doubted, went through at Review the first time"
    assert entries(host, parties["product"]) == []                                                           # it said go
    host.command("ideas.merge", {"slug": slug, "task": "k1"})
    assert len(entries(host, parties["tech"], "went_through")) == 1


def test_a_send_back_is_a_came_back_once_a_goal_and_a_merge_after_it_is_no_first_time(host, parties):
    slug = at_review(host, parties)
    host.command("ideas.back", {"slug": slug, "task": "k1", "why": "Rename it"})
    assert one(host, parties["tech"], "came_back")["text"] == "“A review idea”, which you said no to, came back at Review: Rename it"
    assert one(host, parties["design"], "came_back")["text"] == "“A review idea”, which you doubted, came back at Review: Rename it"
    host.command("ideas.back", {"slug": slug, "task": "k1", "why": "And again"})
    host.command("ideas.merge", {"slug": slug, "task": "k1"})
    assert len(entries(host, parties["tech"], "came_back")) == 1 and entries(host, parties["tech"], "went_through") == []


def test_a_result_dropped_at_review_came_back_and_one_dropped_elsewhere_did_not(host, parties):
    slug = at_review(host, parties)
    host.command("ideas.drop_task", {"slug": slug, "task": "k1"})
    assert one(host, parties["tech"], "came_back")["text"] == "“A review idea”, which you said no to, came back at Review: it was dropped"
    other = at_review(host, parties, state="ready")
    host.command("ideas.drop_task", {"slug": other, "task": "k1"})
    assert [e["idea"] for e in entries(host, parties["tech"], "came_back")] == [slug]


def test_a_goal_no_leader_doubted_and_an_answer_the_runner_refused_keep_nothing(host, parties):
    calm = at_review(host, parties, stances=[{"party": parties["tech"], "verdict": "go", "why": ""}])
    host.command("ideas.merge", {"slug": calm, "task": "k1"})
    slug = at_review(host, parties)
    host.ideas._runner = FakeRunner(refuse=True)
    with pytest.raises(CommandError, match="tests are red"):
        host.command("ideas.merge", {"slug": slug, "task": "k1"})
    with pytest.raises(CommandError, match="tests are red"):
        host.command("ideas.back", {"slug": slug, "task": "k1", "why": "Fix them"})
    assert entries(host, parties["tech"]) == [] and entries(host, parties["design"]) == []


# -- a leader's concerns and its evening line ---------------------------------------------------------------------------------------------------

def test_a_concern_made_a_goal_or_called_not_a_problem_is_that_partys(app_host):
    design = C._party(app_host, "Design", "product-designer")
    model = C.Model(app_host, {"concerns": [C.concern("cart", "alert", "Nothing leads here"), C.concern("home", "note", "Not looked at")]})
    C._look(app_host, design)
    got = app_host.command("ideas.concerns", {"party": design})
    assert len(got["concerns"]) == 2
    first, second = got["concerns"]
    made = app_host.command("ideas.concern_goal", {"party": design, "id": first["id"]})
    app_host.command("ideas.concern_dismiss", {"party": design, "id": second["id"]})
    goal = entries(app_host, design, "concern_goal")[0]
    assert goal["text"] == f"Your concern on {first['name']} became the goal “{title_of(app_host, made['idea'])}”" and goal["idea"] == made["idea"] and goal["on"] == [first["on"]]
    gone = entries(app_host, design, "concern_dismissed")[0]
    assert gone["text"] == f"The person said your concern on {second['name']} is not a problem: {second['what']}" and gone["on"] == [second["on"]]
    assert model.looks and entries(app_host, PROJECT) == []


@pytest.mark.parametrize("way, text", [("toward", "Since your last look the screens map went toward what you keep: Help is a step nearer"),
                                       ("away", "Since your last look the screens map went away from what you keep: Help is a step nearer"),
                                       ("sideways", "Since your last look the screens map changed; it is unclear which way: Help is a step nearer")])
def test_the_evening_line_a_leader_keeps_is_its_own_and_the_first_look_has_none(app_host, way, text):
    design = C._party(app_host, "Design", "product-designer")
    model = C.Model(app_host)
    C._look(app_host, design)
    assert entries(app_host, design) == []                                                                   # nothing to compare yet
    C._change_map(app_host)
    C._a_day_ago(app_host, design)
    model.answer = {"concerns": [], "since": {"way": way, "line": "Help is a step nearer"}}
    C._look(app_host, design)
    assert [e["text"] for e in entries(app_host, design, "since")] == [text] and entries(app_host, PROJECT) == []


# -- a journal that cannot be written fails nothing ---------------------------------------------------------------------------------------------

def test_a_journal_that_cannot_be_written_fails_nothing(host, product, monkeypatch):
    (state_of(host) / "journals").write_text("not a folder")                                                 # the disk refuses every entry
    slug = a_goal(host)
    assert host.command("ideas.drop", {"slug": slug, "why": "Not now"}) == {"ok": True}
    host.command("ideas.project_fact_set", {"party": product, "key": "why_us", "text": "One TV"})
    assert project_facts.of(state_of(host), product)[0]["text"] == "One TV"
    (state_of(host) / "journals").unlink()

    def boom(*a, **k):
        raise RuntimeError("the journal is broken")

    monkeypatch.setattr(journals, "add", boom)
    other = a_goal(host, "Light mode for the day")
    assert host.command("ideas.drop", {"slug": other}) == {"ok": True} and ideas.idea_page(host.ideas.root(), other) is None
    assert journal_notes.note(state_of(host), PROJECT, "dropped", "x") is None
    journal_notes.stances(state_of(host), host.ideas.root(), "nowhere", [{"party": "BAD SCOPE!", "verdict": "no", "why": "x"}, "not a stance"])      # a scope that is none, nothing raised


# -- the host's commands ------------------------------------------------------------------------------------------------------------------------

def test_the_journal_commands_are_the_hosts_and_a_phones(host):
    assert {"ideas.journal", "ideas.journal_strike"} <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in ("ideas.journal", "ideas.journal_strike"))


def test_ideas_journal_gives_the_projects_journal_or_a_partys_with_the_struck_marked_and_the_digest(host, parties):
    assert host.command("ideas.journal") == {"entries": [], "digest": {}}
    mine = journals.add(state_of(host), PROJECT, "decision", "Decision 1: No accounts", idea="lobby", ref="1")
    tech = journals.add(state_of(host), parties["tech"], "stance", "On “Lobby” you said no: it adds a caller", idea="lobby")
    journals.save_digest(state_of(host), parties["tech"], "It guards the cache.", tech["id"])
    got = host.command("ideas.journal", {})
    assert got["entries"] == [mine] and got["digest"] == {}
    got = host.command("ideas.journal", {"party": parties["tech"]})
    assert got["entries"] == [tech] and got["digest"]["text"] == "It guards the cache." and got["digest"]["upto"] == tech["id"]
    struck = host.command("ideas.journal_strike", {"party": parties["tech"], "id": tech["id"], "why": "Not so"})
    assert struck["ok"] is True and struck["entry"]["id"] == tech["id"] and struck["entry"]["struck"]["why"] == "Not so"
    again = host.command("ideas.journal", {"party": parties["tech"]})
    assert again["entries"][0]["struck"]["why"] == "Not so" and again["entries"][0]["text"] == tech["text"]
    assert journals.read(state_of(host), parties["tech"]) == [] and journals.text(state_of(host), parties["tech"], idea="lobby") != ""            # struck: never read into a call again
    host.command("ideas.journal_strike", {"id": mine["id"]})
    assert journals.read(state_of(host), PROJECT) == []


def test_the_journal_commands_refuse_in_plain_words(host, parties):
    mine = journals.add(state_of(host), PROJECT, "decision", "Decision 1: No accounts")
    with pytest.raises(CommandError, match="No such party"):
        host.command("ideas.journal", {"party": "nobody"})
    with pytest.raises(CommandError, match="No such party"):
        host.command("ideas.journal_strike", {"party": "nobody", "id": mine["id"]})
    with pytest.raises(CommandError, match="No such party"):
        host.command("ideas.journal", {"party": "general"})
    with pytest.raises(CommandError, match="No such entry"):
        host.command("ideas.journal_strike", {"id": "abc123"})
    with pytest.raises(CommandError, match="No such entry"):
        host.command("ideas.journal_strike", {"party": parties["tech"], "id": mine["id"]})                    # an entry of the project's is none of a party's
    with pytest.raises(CommandError, match="id is missing"):
        host.command("ideas.journal_strike", {})
    with pytest.raises(CommandError, match="party is not text"):
        host.command("ideas.journal", {"party": 3})
    with pytest.raises(CommandError, match="why is not text"):
        host.command("ideas.journal_strike", {"id": mine["id"], "why": 3})
    assert journals.read(state_of(host), PROJECT) == [mine]
