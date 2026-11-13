"""Spec 42 B (docs/specs/42-coming-back.md §2.1, Tests → B): a goal's tally and the project's flags on a fixture board, and
`ideas.flags` on the host and the phone. Code, no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, goal_flags, goal_verdict, idea_spend, ideas


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def _goal(root, title):
    return ideas.save_goal(root, None, title, "About " + title, None, "normal")[0]


def _idea(root, state, goal, text, status="done", tasks=()):
    slug = ideas.add_idea(root, text, goal, state)
    ideas.save_state(state, slug, state=status)
    if tasks:
        folder = state / "ideas" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "plan.json").write_text(json.dumps({"idea": slug, "tasks": [{"id": f"k{n}", "title": f"T{n}", "state": s, "round": r}
                                                                           for n, (s, r) in enumerate(tasks, 1)]}))
    return slug


def _ledger(path: Path, at: str, cost=0.5):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": at, "step": "task", "task": "k1", "round": 1, "role": "grunt", "cost": cost}) + "\n")


def _event(project: Path, event: str, at: str, **fields):
    row = {"at": at, "event": event, **fields}
    target = event_log.path(project)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _verdict(state, goal, met, at, by="Product manager"):
    got = goal_verdict.save(state, goal, {"met": met, "verdict": "x"}, by=by)
    folder = ideas.goal_folder(state, goal)
    (folder / "verdict.json").write_text(json.dumps({**got, "at": at}))


def test_days_run_from_the_oldest_start_to_the_verdict_and_usd_is_null_when_unpriced(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    project = Path(host.ideas.host.repo_root)
    goal = _goal(root, "Offline mode")
    a = _idea(root, state, goal, "Cache the table", "done", [("merged", 1)])
    _verdict(state, goal, True, "2026-10-18T12:00:00")
    _ledger(ideas.goal_folder(state, goal) / idea_spend.FILE, "2026-10-14T12:00:00", 1.25)
    assert goal_flags.tally(root, state, goal)["days"] == 4 and goal_flags.tally(root, state, goal)["usd"] == 1.25
    _ledger(state / "ideas" / a / idea_spend.FILE, "2026-10-10T08:00:00", None)           # an idea's first line is older
    assert goal_flags.tally(root, state, goal)["days"] == 8
    _event(project, "goal_saved", "2026-10-01T09:00:00+00:00", goal=goal, new=False)      # an edit is not a start
    _event(project, "goal_saved", "2026-10-09T09:00:00+00:00", goal=goal, new=True)
    assert goal_flags.tally(root, state, goal)["days"] == 9
    _verdict(state, goal, True, "2026-10-09T10:00:00")
    assert goal_flags.tally(root, state, goal)["days"] == 1                                # at least one
    only = _goal(root, "Unpriced")
    _idea(root, state, only, "Alone", "done")
    _ledger(state / "ideas" / "alone" / idea_spend.FILE, "2026-10-01T08:00:00", None)
    assert goal_flags.tally(root, state, only)["usd"] is None


def test_flags_are_the_met_goals_newest_first_and_general_never(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    old, new, no, quiet = _goal(root, "Old goal"), _goal(root, "New goal"), _goal(root, "Not met"), _goal(root, "No verdict")
    _verdict(state, old, True, "2026-10-01T10:00:00")
    _verdict(state, new, True, "2026-10-18T10:00:00", by="Growth")
    _verdict(state, no, False, "2026-10-19T10:00:00")
    _verdict(state, ideas.GENERAL, True, "2026-10-20T10:00:00")
    got = goal_flags.flags(root, state)
    assert [f["goal"] for f in got] == [new, old] and got[0]["by"] == "Growth" and got[0]["at"] == "2026-10-18T10:00:00"
    assert set(got[0]) == {"goal", "title", "short", "by", "at", "tally"} and got[0]["title"] == "New goal"


def test_ideas_flags_is_the_hosts_and_a_phones_and_needs_a_project(host):
    assert BoardPhone.allowed(Orkboard(), "ideas.flags", {})
    with pytest.raises(CommandError, match="Open a folder first"):
        Orkboard().command("ideas.flags", {})
    assert host.command("ideas.flags", {}) == {"flags": [], "goals": []}                  # spec 50 §2.4: `goals` beside the old `flags`
    root, state = host.ideas.root(), host.ideas.state_dir
    goal = _goal(root, "Offline mode")
    _verdict(state, goal, True, "2026-10-18T10:00:00")
    got = host.command("ideas.flags", {})
    (flag,) = got["flags"]
    json.dumps(flag)
    assert flag["goal"] == goal and flag["tally"]["ideas"] == 0 and got["goals"] == []

