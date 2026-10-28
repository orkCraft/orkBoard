"""Spec 99 E (docs/specs/99-a-goals-way.md §6, §7) on the host: `ideas.confirm` (*Confirm and start*) and `ideas.fork_answer` answer the rows `decision` and `fork`; their arguments are
checked, a phone may send them, the commit is an event, and a goal that had a fork is never started by itself. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, goal_team, ideas, library, spec_sections

DECIDE_COMMANDS = {"ideas.confirm", "ideas.fork_answer"}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.command("ideas.board_set", {"autostart": False})          # a plan made is not started: no runner here
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def tech(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, ["architect", "grunt", "tester"])
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    goal_team.set_team(root, slug, ["grunt", "tester"], leader="architect")
    return slug


@pytest.fixture
def model(host):
    seen: list[dict] = []

    def call(tier, prompt, effort="", budget=None):
        step = host.ideas.keeper.measure()["step"]
        seen.append({"step": step, "prompt": prompt})
        out = {"talk_round": {"stance": "For it", "for": "f", "against": "a", "questions": []},
               "decide": {"title": "Dark mode ships", "why": "People read at night.", "points": ["Tech adds it.", "Off by default."]},
               "section_first": {"why": "Because.", "done_when": ["It works"], "will_be": ["changed src"], "risk": "low"},
               "plan": {"tasks": [{"id": "k1", "title": "Do it", "brief": "Do the thing.", "kind": "code", "tier": "warrior", "after": []}], "todos": []}}.get(step, {})
        return json.dumps(out), 0.01, 10, ""

    host.ideas.keeper.call = call
    return seen


def _until(host, slug, state):
    for _ in range(1500):
        if ideas.state(host.ideas.state_dir, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"never {state}: {ideas.state(host.ideas.state_dir, slug)}")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def test_the_commands_are_the_hosts_and_a_phones(host):
    assert DECIDE_COMMANDS <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in DECIDE_COMMANDS)


def test_the_arguments_are_checked_in_plain_words(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.confirm", {})
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.confirm", {"idea": "nobody"})
    with pytest.raises(CommandError, match="text is not text"):
        host.command("ideas.confirm", {"idea": slug, "text": 3})
    with pytest.raises(CommandError, match="no decision to confirm now"):
        host.command("ideas.confirm", {"idea": slug})                                                # a goal not decided
    with pytest.raises(CommandError, match="side and text are text"):
        host.command("ideas.fork_answer", {"idea": slug, "side": 1})
    with pytest.raises(CommandError, match="no fork to settle now"):
        host.command("ideas.fork_answer", {"idea": slug, "side": "tech"})
    assert model == []


def test_a_goal_from_the_press_of_talk_to_its_plan_by_one_confirm_and_the_commit_is_an_event(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "decided")
    row = _row(host, slug, "decision")
    assert row["title"] == "Dark mode ships" and row["number"] == 1 and row["confirmed"] is False and _row(host, slug, "talk") is None
    got = host.command("ideas.confirm", {"idea": slug, "text": "Why: my words.\n\n1. Only this."})
    assert got["ok"] is True and got["number"] == 1 and got["commit"] and got["path"] == "docs/decisions.md"
    assert subprocess.run(["git", "show", "dev:docs/decisions.md"], cwd=host.repo_root, capture_output=True, text=True).stdout.count("Why: my words.") == 1
    _until(host, slug, "plan")
    assert _row(host, slug, "decision") is None and _row(host, slug, "plan") is not None
    ev = [e for e in event_log.read(Path(host.repo_root)) if e["event"] == event_log.BOARD_COMMITTED and e.get("what") == "decision"]
    assert ev and ev[-1]["commit"] == got["commit"] and ev[-1]["pages"] >= 2
    ideas_page = ideas.idea_page(host.ideas.root(), slug)
    assert ideas_page.parts("Tech")["Why"] == "Because." and ideas_page.section("Asked") == "add a dark mode option"


def test_a_goal_that_had_a_fork_is_never_started_by_itself_but_one_that_had_none_is_left_to_the_risk(host, tech, model):
    host.command("ideas.board_set", {"autostart": True})
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech})["slug"]
    assert host.ideas.autostart(slug) == ""                                                                  # BoardMixin's: no plan, nothing to decide
    spec_sections.save_record(host.ideas.state_dir, slug, {"wait": True})
    assert host.ideas.autostart(slug) == "wait"                                                              # after a fork the plan waits for the person's Start
    spec_sections.save_record(host.ideas.state_dir, slug, {"wait": False})
    assert host.ideas.autostart(slug) == ""
