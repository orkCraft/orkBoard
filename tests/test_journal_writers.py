"""Spec 125 B (docs/specs/125-the-journals.md §B; decisions §203): the writers of the journals and the host's commands. Each row of the spec's table writes its one entry, with its scope, its kind, its goal and its
parts, in the product's words (the second person in a leader's journal, the third in the project's); `came_back` and `went_through` once a goal; a journal that cannot be written fails nothing; `ideas.journal`
and `ideas.journal_strike` and their refusals. The hosts are composed as Talk's, the concerns' and the project questions' tests compose them; the model call is stubbed (`keeper.call`).
"""
from __future__ import annotations

import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_journal import JournalMixin, journal_commands
from orkboard.realm import idea_questions, ideas, journal_notes, journals
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


# -- the brief ----------------------------------------------------------------------------------------------------------------------------------

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


# -- a leader's concerns and its evening line ---------------------------------------------------------------------------------------------------

# -- a journal that cannot be written fails nothing ---------------------------------------------------------------------------------------------

# -- the host's commands ------------------------------------------------------------------------------------------------------------------------

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
