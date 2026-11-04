"""Spec 132 A on the host (docs/specs/132-four-levels-the-way-down-and-findings.md §A; decisions §234.5, §237.3): `ideas.add_to_goal` (words kept as written, the decision worded again
when it was worded), `ideas.decision_change` (the entry kept as written, or worded again by the Orkmaster), `keeper.reword`, and the quick question's `goal_in_analysis`. The model call
is stubbed (`keeper.call`); the commit test is a real git repository."""
from __future__ import annotations

import json
import subprocess
import sys
import time

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.gui.ideas_refine import refine_commands
from orkboard.realm import board_ask, event_log, goal_refine, goal_team, idea_ripe, ideas, library, spec_sections

DECISION = {"title": "Dark mode ships", "why": "People read at night.", "points": ["Tech adds it.", "Off by default."]}
AGAIN = {"title": "Dark mode ships with a timer", "why": "People read at night, and set a time.", "points": ["Tech adds it with a timer.", "Off by default."]}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    h.command("ideas.board_set", {"autostart": False})
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def tech(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, ["architect", "grunt", "tester"])
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    goal_team.set_team(root, slug, ["grunt", "tester"], leader="architect")
    return slug


class Seen(list):
    """The calls the stub saw; `answers` what the `decide` step answers."""

    answers: dict


@pytest.fixture
def model(host):
    """`seen` every call; `answers["decide"]` the JSON the next `decide` calls get (a list is taken in turn, the last kept)."""
    seen = Seen()
    answers: dict = {"decide": [DECISION]}

    def call(tier, prompt, effort="", budget=None):
        step = host.ideas.keeper.measure()["step"]
        seen.append({"step": step, "prompt": prompt})
        if step == "decide":
            got = answers["decide"]
            got = (got.pop(0) if len(got) > 1 else got[0]) if isinstance(got, list) else got
            return (got if isinstance(got, str) else json.dumps(got)), 0.01, 10, ""
        out = {"talk_round": {"stance": "For it", "for": "f", "against": "a", "questions": []},
               "section_first": {"why": "Because.", "done_when": ["It works"], "will_be": ["changed src"], "risk": "low"},
               "plan": {"tasks": [{"id": "k1", "title": "Do it", "brief": "Do the thing.", "kind": "code", "tier": "warrior", "after": []}], "todos": []}}.get(step, {})
        return json.dumps(out), 0.01, 10, ""

    host.ideas.keeper.call = call
    seen.answers = answers
    return seen


def _idle(host, slug):
    for _ in range(1500):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _until(host, slug, state):
    for _ in range(1500):
        if ideas.state(host.ideas.state_dir, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"never {state}: {ideas.state(host.ideas.state_dir, slug)}")


def _decided(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "decided")
    model.clear()
    return slug


def _decision(host, slug):
    return spec_sections.record(host.ideas.state_dir, slug)["decision"]


def _decides(model):
    return [c for c in model if c["step"] == "decide"]


def _events(host, name):
    from pathlib import Path
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def test_the_commands_are_the_hosts_and_a_phones(host):
    names = {"ideas.add_to_goal", "ideas.decision_change"}
    assert set(refine_commands(host.ideas)) == names <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in names)
    assert {event_log.GOAL_ADDED_TO, event_log.DECISION_CHANGED} <= set(event_log.EVENTS)


def test_words_added_to_a_goal_not_yet_decided_are_kept_as_written_and_no_call_is_made(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech, "hold": True})["slug"]
    got = host.command("ideas.add_to_goal", {"idea": slug, "text": "  Also a timer, as the person wrote it.  "})
    assert got["ok"] is True and got["reworded"] is False and "cost" not in got and model == []
    gist = ideas.idea_page(host.ideas.root(), slug).section("Gist")
    assert gist == "add a dark mode option\n\nAdded: Also a timer, as the person wrote it."
    assert goal_refine.words(ideas.idea_page(host.ideas.root(), slug)) == gist
    (added,) = _events(host, event_log.GOAL_ADDED_TO)
    assert added["idea"] == slug and added["reworded"] is False and added["chars"] == len("Also a timer, as the person wrote it.")


def test_a_goal_whose_decision_is_worded_has_it_worded_again_with_the_old_wording_and_the_new_words(host, tech, model):
    slug = _decided(host, tech, model)
    assert _decision(host, slug)["title"] == "Dark mode ships"
    model.answers["decide"] = [AGAIN]
    got = host.command("ideas.add_to_goal", {"idea": slug, "text": "Also a timer."})
    assert got["reworded"] is True and got["cost"]["calls"] == 1 and got["cost"]["usd_high"]
    _idle(host, slug)
    (call,) = _decides(model)
    assert "The decision as it is worded now" in call["prompt"] and "Dark mode ships" in call["prompt"] and "Added: Also a timer." in call["prompt"]
    d = _decision(host, slug)
    assert d["title"] == "Dark mode ships with a timer" and d["confirmed"] is False and d["by"] == "orkmaster" and "timer" in d["text"]
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "decided" and ideas.state(host.ideas.state_dir, slug)["error"] == ""


def test_a_decision_that_cannot_be_worded_again_keeps_its_old_wording_and_says_so(host, tech, model):
    slug = _decided(host, tech, model)
    model.answers["decide"] = "not a decision"
    host.command("ideas.add_to_goal", {"idea": slug, "text": "Also a timer."})
    _idle(host, slug)
    assert _decision(host, slug)["title"] == "Dark mode ships"
    assert "old words stay" in ideas.state(host.ideas.state_dir, slug)["error"]
    assert "Added: Also a timer." in ideas.idea_page(host.ideas.root(), slug).section("Gist")          # the words are kept whatever the call did


def test_add_to_the_goal_is_refused_in_words(host, tech, model):
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.add_to_goal", {"text": "x"})
    with pytest.raises(CommandError, match="text is missing"):
        host.command("ideas.add_to_goal", {"idea": "nobody", "text": "  "})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.add_to_goal", {"idea": "nobody", "text": "x"})
    slug = _decided(host, tech, model)
    with pytest.raises(CommandError, match="too long"):
        host.command("ideas.add_to_goal", {"idea": slug, "text": "x" * ideas.SECTION_CHARS})
    host.ideas.keeper._busy[slug] = "talking"
    with pytest.raises(CommandError, match="keeper is busy with this goal"):
        host.command("ideas.add_to_goal", {"idea": slug, "text": "x"})
    host.ideas.keeper._busy.pop(slug)
    host.command("ideas.confirm", {"idea": slug})
    with pytest.raises(CommandError, match="This goal is agreed: ask its leader for a change"):
        host.command("ideas.add_to_goal", {"idea": slug, "text": "x"})
    assert "Added:" not in ideas.idea_page(host.ideas.root(), slug).section("Gist") and not _decides(model)


def test_the_change_kept_as_written_is_the_decisions_entry_and_no_call_is_made(host, tech, model):
    slug = _decided(host, tech, model)
    ideas.save_state(host.ideas.state_dir, slug, error="")
    got = host.command("ideas.decision_change", {"idea": slug, "text": "## 9. My title (3 November 2026, the person and Orkboard)\n\nWhy: my words.\n\n1. Only this."})
    assert got["ok"] is True and got["kept"] is True and got["reworded"] is False and model == []
    d = _decision(host, slug)
    assert d["title"] == "My title" and d["text"] == "Why: my words.\n\n1. Only this." and d["by"] == "person" and d["confirmed"] is False
    assert idea_ripe.of(host.ideas.state_dir, slug) is None                              # the person's own entry: the leaders' wait is over
    done = host.command("ideas.confirm", {"idea": slug})
    assert done["title"] == "My title"
    shown = subprocess.run(["git", "show", "dev:docs/decisions.md"], cwd=host.repo_root, capture_output=True, text=True).stdout
    assert shown.count("Why: my words.") == 1 and "My title" in shown
    (ev,) = _events(host, event_log.DECISION_CHANGED)
    assert ev["kept"] is True and ev["said"] is False


def test_the_change_said_in_words_is_worded_again_by_one_call_given_the_old_entry_and_the_words(host, tech, model):
    slug = _decided(host, tech, model)
    model.answers["decide"] = [AGAIN]
    got = host.command("ideas.decision_change", {"idea": slug, "say": "Add a timer to it"})
    assert got["reworded"] is True and got["kept"] is False and got["cost"]["calls"] == 1
    _idle(host, slug)
    (call,) = _decides(model)
    assert "People read at night." in call["prompt"] and "Add a timer to it" in call["prompt"] and "What the person says to change in it" in call["prompt"]
    assert _decision(host, slug)["title"] == "Dark mode ships with a timer"
    (ev,) = _events(host, event_log.DECISION_CHANGED)
    assert ev["said"] is True and ev["kept"] is False


def test_the_text_and_the_words_together_the_text_first_then_the_words_on_it(host, tech, model):
    slug = _decided(host, tech, model)
    model.answers["decide"] = [AGAIN]
    got = host.command("ideas.decision_change", {"idea": slug, "text": "Why: written.\n\n1. By hand.", "say": "and a timer"})
    assert got["kept"] is True and got["reworded"] is True
    _idle(host, slug)
    (call,) = _decides(model)
    assert "Why: written." in call["prompt"] and "and a timer" in call["prompt"]


def test_the_change_is_refused_in_words(host, tech, model):
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.decision_change", {"idea": "nobody", "say": "x"})
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech, "hold": True})["slug"]
    with pytest.raises(CommandError, match="no decision to change now"):
        host.command("ideas.decision_change", {"idea": slug, "say": "x"})                # in analysis, but nothing worded yet
    slug = _decided(host, tech, model)
    with pytest.raises(CommandError, match="Write the decision, or say what to change"):
        host.command("ideas.decision_change", {"idea": slug})
    with pytest.raises(CommandError, match="text is not text"):
        host.command("ideas.decision_change", {"idea": slug, "text": 3})
    host.ideas.keeper._busy[slug] = "talking"
    with pytest.raises(CommandError, match="keeper is busy with this goal"):
        host.command("ideas.decision_change", {"idea": slug, "say": "x"})
    host.ideas.keeper._busy.pop(slug)
    host.command("ideas.confirm", {"idea": slug})
    with pytest.raises(CommandError, match="This goal is agreed: ask its leader for a change"):
        host.command("ideas.decision_change", {"idea": slug, "text": "Why: late."})
    assert not _decides(model)


def test_goal_in_analysis_by_code(host, tech, model):
    slug = _decided(host, tech, model)
    title = ideas.idea_page(host.ideas.root(), slug).title
    root, state = host.ideas.root(), host.ideas.state_dir
    assert goal_refine.in_analysis(state, slug) and goal_refine.in_answer(root, state, ["§12", title.upper()]) == slug and goal_refine.in_answer(root, state, ["§12"]) == ""
    host.command("ideas.confirm", {"idea": slug})
    _until(host, slug, "plan")
    assert not goal_refine.in_analysis(state, slug) and goal_refine.in_answer(root, state, [title]) == ""


def test_a_quick_questions_answer_carries_the_goal_in_analysis_it_is_about(host, tech, model):
    slug = _decided(host, tech, model)
    title = ideas.idea_page(host.ideas.root(), slug).title
    answer = {"answer": "It is being decided.", "sources": [title], "goal": ""}
    base = host.ideas.keeper.call

    def call(tier, prompt, effort="", budget=None):
        return (json.dumps(answer), 0.01, 10, "") if host.ideas.keeper.measure()["step"] == "ask" else base(tier, prompt, effort, budget)

    host.ideas.keeper.call = call
    host.command("ideas.ask", {"party": "", "q": "Where is the dark mode?"})
    _idle(host, "ask")
    rec = board_ask.record(host.ideas.state_dir)
    assert rec["status"] == "answered" and rec["goal_in_analysis"] == slug
    answer["sources"] = ["§12"]
    host.command("ideas.ask", {"party": "", "q": "Where is it?"})
    _idle(host, "ask")
    assert board_ask.record(host.ideas.state_dir)["goal_in_analysis"] == ""
