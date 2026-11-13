"""Spec 120 D (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4.3–§4.5, §7) on the host: `ideas.hearing`, `ideas.throw` and `ideas.unthrow`; one row a goal; each throw doing what
it says (go and the person's words confirm the decision once it is worded, smaller words the goal, later waits on a goal, drop drops it); a fork thrown by its side; a late throw
refused in plain words. The model call is stubbed (`keeper.call`) as Talk's tests do."""
from __future__ import annotations

import time

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError
from orkboard.realm import event_log, idea_questions, ideas, spec_sections
from tests.test_idea_decide import git  # noqa: F401
from tests.test_idea_talk import DECIDED, TECH_NO, _noes, _objections, _row, _state, _talk, _until_state, host, model, parties  # noqa: F401  (the fixtures)

COMMANDS = {"ideas.hearing", "ideas.throw", "ideas.unthrow"}


def _throw(host, slug, **args):
    return host.command("ideas.throw", {"idea": slug, "moment": "talk", **args})


def _until_sections(host, slug):
    """The sections were asked for (the stub saw the goal), not only its state `sections`: the state is saved just before they are."""
    for _ in range(1000):
        if slug in host.ideas.keeper.sections.seen and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"the sections were never asked for: {_state(host, slug)['state']} {_state(host, slug)['error']}")


@pytest.fixture
def sections(host):
    """The sections stubbed: the goal only reaches `sections`, as Confirm and start leaves it."""
    seen = []
    host.ideas.keeper.sections = lambda s: seen.append(s)
    host.ideas.keeper.sections.seen = seen
    return seen


def _no_goal(host, parties, model, text="add a dark mode option", **noes):
    """A goal at Talk whose leaders said `noes`, with no question (the hearing is open, the decision waits)."""
    _noes(model, parties, per=0, **noes)
    model.said[("decide", "")] = DECIDED
    return _talk(host, parties, ["product", "design", "tech"], text)


def test_a_goal_with_a_no_has_one_hearing_row_and_ideas_hearing_gives_it_with_its_goal(host, parties, model):
    slug = _no_goal(host, parties, model, tech=TECH_NO, product={"verdict": "no", "why": "Not worth it", "instead": "Only the setting"})
    rows = [n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug]
    assert [r["kind"] for r in rows] == ["hearing"] and rows[0]["moment"] == "talk"
    got = host.command("ideas.hearing", {"idea": slug})
    assert got["idea"] == slug and got["moment"] == "talk" and got["title"] == rows[0]["heading"] and got["sides"] == rows[0]["sides"]
    assert [(s["dir"], s["kind"]) for s in got["sides"]] == [("right", "go"), ("up", "smaller")]
    node = next(n for n in host.command("ideas.map")["nodes"] if n["slug"] == slug)
    assert node["needs_you"] == "hearing"


def test_go_confirms_the_decision_once_it_is_worded_names_the_overruled_and_the_sections_follow(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO, design={"verdict": "doubt", "why": "The contrast is low"})
    got = _throw(host, slug, dir="right")
    assert got["ok"] is True and got["kind"] == "go" and got["dir"] == "right" and got["outcome"] == "Do it" and got["moment"] == "talk" and got["to"] == [host.ideas.keeper._name("product-manager")]
    _until_sections(host, slug)
    line = f"Against {host.ideas.keeper._name('architect')}: It adds a third caller to server/ws"
    assert line in model.steps("decide")[0]["prompt"] and "Doubt from" in model.steps("decide")[0]["prompt"]          # the leader overruled and the doubt are told to the decision
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert "## 1. Dark mode (" in entry and ", the person and Orkboard)" in entry and line in entry                      # confirmed as the person would, nothing pressed
    assert sections == [slug] and _row(host, slug, "decision") is None and _objections(host, slug) == []
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is True
    assert "thrown" not in idea_questions.record(host.ideas.state_dir, slug)
    said = ideas.talk(host.ideas.state_dir, slug)
    assert any(t["who"] == "you" and t["text"].startswith("Thrown to ") and "Do it" in t["text"] for t in said)


def test_later_waits_on_the_goal_named_and_goes_back_to_the_deck_held(host, parties, model):
    first = host.command("ideas.add", {"text": "add a lobby for the party game", "track": parties["product"], "hold": True})["slug"]
    slug = _no_goal(host, parties, model, text="add a dark mode option", product={"verdict": "no", "why": "The lobby comes first", "after": first})
    got = host.command("ideas.hearing", {"idea": slug})
    assert [(s["dir"], s["kind"]) for s in got["sides"]] == [("right", "go"), ("left", "later")]
    done = _throw(host, slug, dir="left")
    assert done["kind"] == "later" and done["outcome"] == "After add a lobby for the party game"
    node = next(n for n in host.command("ideas.map")["nodes"] if n["slug"] == slug)
    assert node["waits_on"] == [first] and node["depends_on"] == [first] and node["place"] == "deck" and node["state"] == "raw" and node["queue"] == "hold"
    assert _objections(host, slug) == [] and idea_questions.record(host.ideas.state_dir, slug) == {} and len(model.steps("decide")) == 0
    assert host.command("ideas.hearing", {"idea": slug}) is None


def test_the_persons_own_words_are_confirmed_as_written_and_win_over_a_side(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    words = "## 9. Light and dark (28 October, the person and Orkboard)\nWhy: mine.\n\n1. Only dark."
    done = _throw(host, slug, dir="left", text=words)
    assert done["kind"] == "own" and done["dir"] == "" and done["to"] == []
    _until_sections(host, slug)
    entry = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert "## 1. Light and dark (" in entry and "Why: mine." in entry and "1. Only dark." in entry
    assert sections == [slug] and spec_sections.record(host.ideas.state_dir, slug)["decision"]["confirmed"] is True


def test_a_throw_when_the_questions_still_wait_goes_on_when_they_are_answered(host, parties, model, sections):
    _noes(model, parties, per=1, tech=TECH_NO)
    model.said[("decide", "")] = DECIDED
    slug = _talk(host, parties, ["tech"])
    _throw(host, slug, dir="right")
    assert model.steps("decide") == [] and _row(host, slug, "talk") is not None                                         # the person's questions still wait for them
    host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    _until_sections(host, slug)
    assert sections == [slug] and len(model.steps("decide")) == 1


# -- a fork -------------------------------------------------------------------------------------------------------------------------------------

def _forked(host, parties, n=3):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state="sections")
    sides = [{"party": parties[w], "leader": lead, "says": f"{w} way", "why": f"because {w}"} for w, lead in (("product", "product-manager"), ("design", "product-designer"), ("tech", "architect"))][:n]
    spec_sections.save_record(host.ideas.state_dir, slug, {"forks": [{"id": "f1", "about": "Done", "sides": sides, "status": "answered"},
                                                                     {"id": "f2", "about": "Waves", "sides": sides, "status": "open"}]})
    return slug


def test_a_fork_is_a_hearing_by_its_first_open_fork_and_its_row_stays_a_fork(host, parties, model):
    slug = _forked(host, parties)
    got = host.command("ideas.hearing", {"idea": slug})
    assert got["moment"] == "fork" and got["id"] == "f2" and got["about"] == "Waves" and got["own"] is True
    assert [(s["dir"], s["party"], s["outcome"]) for s in got["sides"]] == [("right", parties["product"], "product way"), ("left", parties["design"], "design way"), ("up", parties["tech"], "tech way")]
    assert got["title"].endswith(" disagree")
    (row,) = [n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug]
    assert row["kind"] == "fork" and row["hearing"]["sides"] == got["sides"]


def test_a_fork_thrown_to_a_side_answers_it_by_that_party_and_by_words_with_the_persons_own(host, parties, model):
    slug = _forked(host, parties)
    answers = []
    host.ideas.keeper.fork_answer = lambda s, side="", text="": answers.append((s, side, text))
    done = host.command("ideas.throw", {"idea": slug, "moment": "fork", "dir": "left"})
    assert done["ok"] is True and done["moment"] == "fork" and done["kind"] == "side" and done["outcome"] == "design way"
    host.command("ideas.throw", {"idea": slug, "moment": "fork", "text": "  Six waves, no more  "})
    assert answers == [(slug, parties["design"], ""), (slug, "", "Six waves, no more")]
    with pytest.raises(CommandError, match="That side is not on this hearing"):
        host.command("ideas.throw", {"idea": _forked(host, parties, 2), "moment": "fork", "dir": "up"})             # a fork of two has no top side


# -- Undo of a throw (spec 120 §6.7, `ideas.unthrow`) -----------------------------------------------------------------------------------------------

def _unthrow(host, slug, **args):
    return host.command("ideas.unthrow", {"idea": slug, "moment": "talk", **args})


def test_a_drop_taken_back_returns_the_goal_with_its_state_its_ledger_and_its_hearing(host, parties, model):
    slug = _no_goal(host, parties, model, tech={"verdict": "no", "why": "No way"})
    state_dir, root = host.ideas.state_dir, host.ideas.root()
    spend = state_dir / "ideas" / slug / "spend.jsonl"
    spend.write_text('{"at": "2026-10-20T10:00:00", "usd": 0.5, "calls": 1}\n', encoding="utf-8")
    was = (ideas.idea_page(root, slug).title, idea_questions.record(state_dir, slug), spend.read_text(encoding="utf-8"))
    gone = state_dir / "ideas" / "spend-gone.jsonl"
    _throw(host, slug, dir="left")
    assert ideas.idea_page(root, slug) is None and not (state_dir / "ideas" / slug).exists() and slug in gone.read_text(encoding="utf-8")
    assert _unthrow(host, slug) == {"ok": True, "kind": "drop", "moment": "talk"}
    assert (ideas.idea_page(root, slug).title, idea_questions.record(state_dir, slug), spend.read_text(encoding="utf-8")) == was
    assert not gone.exists() or slug not in gone.read_text(encoding="utf-8"), "the ledger lines the drop moved are taken out again"
    assert len(_objections(host, slug)) == 1 and host.command("ideas.hearing", {"idea": slug})["moment"] == "talk"
    assert slug in [i["slug"] for i in ideas.ideas(root)], "the pages' index has it again"
    with pytest.raises(CommandError, match="It went on already"):
        _unthrow(host, slug)                                                                                          # taken back once


def test_a_go_that_began_the_decision_cannot_be_taken_back_and_changes_nothing(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    _throw(host, slug, dir="right")
    _until_sections(host, slug)
    with pytest.raises(CommandError, match="It went on already"):
        _unthrow(host, slug)
    assert sections == [slug] and len(model.steps("decide")) == 1

