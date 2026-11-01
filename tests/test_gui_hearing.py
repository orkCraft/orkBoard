"""Spec 120 D (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4.3–§4.5, §7) on the host: `ideas.hearing`, `ideas.throw` and `ideas.ripe_hold`; one row a goal; each throw doing what
it says (go and the person's words confirm the decision once it is worded, smaller words the goal, later waits on a goal, drop drops it); a fork thrown by its side; a late throw
refused in plain words; the seam of the wait. The model call is stubbed (`keeper.call`) as Talk's tests do."""
from __future__ import annotations

import sys
import time
import types

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError
from orkboard.realm import event_log, idea_questions, ideas, spec_sections
from tests.test_idea_decide import git  # noqa: F401
from tests.test_idea_talk import DECIDED, TECH_NO, _noes, _objections, _row, _state, _talk, _until_state, host, model, parties  # noqa: F401  (the fixtures)

COMMANDS = {"ideas.hearing", "ideas.throw", "ideas.ripe_hold"}


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


def test_the_commands_are_the_hosts_and_a_phones(host):
    assert COMMANDS <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in COMMANDS)


def test_a_goal_with_a_no_has_one_hearing_row_and_ideas_hearing_gives_it_with_its_goal(host, parties, model):
    slug = _no_goal(host, parties, model, tech=TECH_NO, product={"verdict": "no", "why": "Not worth it", "instead": "Only the setting"})
    rows = [n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug]
    assert [r["kind"] for r in rows] == ["hearing"] and rows[0]["moment"] == "talk"
    got = host.command("ideas.hearing", {"idea": slug})
    assert got["idea"] == slug and got["moment"] == "talk" and got["title"] == rows[0]["heading"] and got["sides"] == rows[0]["sides"]
    assert [(s["dir"], s["kind"]) for s in got["sides"]] == [("right", "go"), ("up", "smaller")]
    node = next(n for n in host.command("ideas.map")["nodes"] if n["slug"] == slug)
    assert node["needs_you"] == "hearing"


def test_a_goal_with_no_hearing_gives_null_and_a_throw_of_it_is_refused(host, parties, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    assert host.command("ideas.hearing", {"idea": slug}) is None
    with pytest.raises(CommandError, match="This was decided already"):
        _throw(host, slug, dir="right")
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.hearing", {"idea": "nobody"})


def test_the_arguments_are_checked_in_plain_words(host, parties, model):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    for args, why in (({"moment": "talk"}, "Throw it to a side"), ({"moment": "chat", "dir": "right"}, "moment is talk or fork"), ({"dir": "right"}, "moment is talk or fork"),
                      ({"moment": "talk", "dir": "down"}, "dir is right, left or up"), ({"moment": "talk", "dir": 3}, "dir and text are text"),
                      ({"moment": "talk", "text": 3}, "dir and text are text")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.throw", {"idea": slug, **args})
    with pytest.raises(CommandError, match="Throw it to a side"):
        _throw(host, slug, dir="left")                                                                            # a side that is not there (only go and the smaller one stand)
    assert len(_objections(host, slug)) == 1


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


def test_go_on_anyway_when_no_leader_said_go_is_the_right_side_too(host, parties, model, sections):
    slug = _no_goal(host, parties, model, product={"verdict": "no", "why": "No"}, design={"verdict": "no", "why": "No"}, tech=TECH_NO)
    got = host.command("ideas.hearing", {"idea": slug})
    assert got["sides"][0]["outcome"] == "Go on anyway" and got["sides"][0]["leaders"] == []
    assert _throw(host, slug, dir="right")["outcome"] == "Go on anyway"
    _until_sections(host, slug)
    assert sections == [slug]


def test_smaller_words_the_goal_as_the_instead_then_confirms_and_the_other_noes_are_overruled(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO, product={"verdict": "no", "why": "Not worth it before the lobby"})
    got = host.command("ideas.hearing", {"idea": slug})
    assert [(s["dir"], s["kind"]) for s in got["sides"]] == [("right", "go"), ("left", "drop"), ("up", "smaller")]
    done = _throw(host, slug, dir="up")
    assert done["kind"] == "smaller" and done["outcome"] == "Do the smaller one: Only the setting, no new caller"
    _until_sections(host, slug)
    page = ideas.idea_page(host.ideas.root(), slug)
    assert page.section("Gist") == "Only the setting, no new caller" and page.title == "Only the setting, no new caller"
    prompt = model.steps("decide")[0]["prompt"]
    assert "Only the setting, no new caller" in prompt and "Against" in prompt and "Not worth it before the lobby" in prompt    # Tech's no is answered; Product's was overruled and is told
    assert "It adds a third caller" not in prompt.split("overruled")[-1]
    assert len(model.steps("talk_round")) == 3                                                                         # Talk is not run again


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


def test_later_that_would_close_a_cycle_is_refused_and_the_hearing_stays(host, parties, model):
    first = host.command("ideas.add", {"text": "add a lobby for the party game", "track": parties["product"], "hold": True})["slug"]
    slug = _no_goal(host, parties, model, product={"verdict": "no", "why": "The lobby comes first", "after": first})
    from orkboard.realm import collide
    collide.add_dependency(host.ideas.root(), first, slug, "the other goal")
    with pytest.raises(CommandError, match="waits for this one"):
        _throw(host, slug, dir="left")
    assert len(_objections(host, slug)) == 1


def test_drop_drops_the_goal(host, parties, model):
    slug = _no_goal(host, parties, model, tech={"verdict": "no", "why": "No way"})
    assert _throw(host, slug, dir="left")["outcome"] == "Drop it"
    assert ideas.idea_page(host.ideas.root(), slug) is None and not any(n["idea"] == slug for n in host.command("ideas.board")["needs_you"])


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


def test_a_late_throw_is_refused_in_plain_words_and_changes_nothing(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    _throw(host, slug, dir="right")
    for args in ({"dir": "right"}, {"dir": "left"}, {"text": "my words"}):
        with pytest.raises(CommandError, match="This was decided already"):
            _throw(host, slug, **args)
    _until_sections(host, slug)
    with pytest.raises(CommandError, match="This was decided already"):
        _throw(host, slug, dir="right")
    with pytest.raises(CommandError, match="This was decided already"):
        host.command("ideas.throw", {"idea": slug, "moment": "fork", "dir": "right"})
    assert len(model.steps("decide")) == 1 and sections == [slug]


def test_a_hearing_another_face_answered_with_the_old_command_is_a_late_throw(host, parties, model):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    host.command("ideas.objection", {"idea": slug, "party": parties["tech"], "answer": "go"})
    with pytest.raises(CommandError, match="This was decided already"):
        _throw(host, slug, dir="right")


def test_a_doubt_only_hearing_is_open_when_the_weigher_says_so(host, parties, model, sections):
    _noes(model, parties, per=1, design={"verdict": "doubt", "why": "The contrast is low", "instead": "Keep the old look"})
    model.said[("decide", "")] = DECIDED
    slug = _talk(host, parties, ["design", "tech"])                                                                     # a question waits, so the goal is at Talk
    assert host.command("ideas.hearing", {"idea": slug}) is None and _objections(host, slug) == []                      # a doubt alone holds nothing today
    with ideas.LOCK:
        rec = idea_questions.record(host.ideas.state_dir, slug)
        rec["hearing"] = True                                                                                           # the seam of part C: `outcome` says a hearing
        idea_questions.save_record(host.ideas.state_dir, slug, rec)
    got = host.command("ideas.hearing", {"idea": slug})
    assert [(s["dir"], s["kind"]) for s in got["sides"]] == [("right", "go"), ("up", "smaller")] and got["title"].endswith("has a doubt")
    _throw(host, slug, dir="up")
    host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    _until_sections(host, slug)
    assert ideas.idea_page(host.ideas.root(), slug).section("Gist") == "Keep the old look"


def test_a_throw_is_logged_without_a_word_of_anyones(host, parties, model, sections):
    slug = _no_goal(host, parties, model, tech=TECH_NO)
    host.ideas.keeper.events = True
    _throw(host, slug, dir="right")
    _until_sections(host, slug)
    lines = [e for e in event_log.read(host.repo_root) if e["event"] == event_log.HEARING_THROWN]
    assert len(lines) == 1 and lines[0]["idea"] == slug and lines[0]["kind"] == "go" and lines[0]["dir"] == "right" and lines[0]["moment"] == "talk"
    assert "It adds a third caller" not in str(lines[0]) and event_log.HEARING_THROWN in event_log.EVENTS


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


def test_a_fork_thrown_again_after_it_was_answered_is_refused(host, parties, model):
    slug = _forked(host, parties)
    host.ideas.keeper.fork_answer = lambda s, side="", text="": None
    way = spec_sections.record(host.ideas.state_dir, slug)
    way["forks"][1]["status"] = "answered"
    spec_sections.save_record(host.ideas.state_dir, slug, way)
    assert host.command("ideas.hearing", {"idea": slug}) is None
    with pytest.raises(CommandError, match="This was decided already"):
        host.command("ideas.throw", {"idea": slug, "moment": "fork", "dir": "right"})
    with pytest.raises(CommandError, match="This was decided already"):
        host.command("ideas.throw", {"idea": slug, "moment": "talk", "dir": "right"})                              # a fork's goal has no Talk to throw


# -- the wait's seam ----------------------------------------------------------------------------------------------------------------------------

def test_hold_calls_the_keeper_or_the_ripe_module_and_says_so_plainly_when_neither_is_there(host, parties, model, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    monkeypatch.setitem(sys.modules, "orkboard.realm.idea_ripe", types.ModuleType("orkboard.realm.idea_ripe"))        # a module that has no `hold` yet
    with pytest.raises(CommandError, match="Nothing waits to start by itself"):
        host.command("ideas.ripe_hold", {"idea": slug})
    held = []
    sys.modules["orkboard.realm.idea_ripe"].hold = lambda state_dir, s: held.append(("module", s))
    assert host.command("ideas.ripe_hold", {"idea": slug}) == {"ok": True} and held == [("module", slug)]
    host.ideas.keeper.ripe_hold = lambda s: held.append(("keeper", s))
    host.command("ideas.ripe_hold", {"idea": slug})
    assert held[-1] == ("keeper", slug)
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.ripe_hold", {"idea": "nobody"})

