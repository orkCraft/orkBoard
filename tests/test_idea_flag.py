"""A goal's flag (docs/specs/50-parties-and-goals.md §2.2): its tally and `flag.json` (realm/idea_flag.py), `idea_gate.all_in`, and the
two ways the host raises it (gui/ideas_gate.py) on a fixture repository with dev and main: at the gate, and when a goal is done."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, idea_flag, idea_spend, ideas
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_in(path: Path, name: str, text: str) -> str:
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-m", f"edit {name}")
    return git(path, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """main holds `a.txt` and `old.txt`; dev is cut from it. Nothing else is checked out but main."""
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "orkcraft.toml").write_text("[gate]\nrun = \"true\"\n")          # a gate with tests: a project with none is refused its way to main (decisions §274.3)
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "start")
    commit_in(r, "old.txt", "older work\n")
    git(r, "branch", "dev")
    return r


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def land(repo: Path, slug: str, task: str, name: str, text: str = "x\n") -> str:
    """A task's work landed in dev the way the runner does: its commit is dev's new head."""
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, task, "dev")
    commit_in(path, name, text)
    commit, _subjects, _note = g.land(path, branch, "dev", push=False)
    g.remove(path)
    return commit


def goal(host, text: str, state: str = "done") -> str:
    """A goal under the first party (never General), in `state`; its plan comes with `plan`."""
    root = host.ideas.root()
    party = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First party")
    slug = host.command("ideas.add", {"text": text, "track": party, "hold": True})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state=state)
    return slug


def plan(host, slug: str, **commits: str) -> None:
    """The goal's plan: a merged task per `id=commit` (a commit of "" is a check that landed nothing)."""
    tasks = [{"id": tid, "title": f"Task {tid}", "state": "merged", "commit": c, "after": [], "round": 1} for tid, c in commits.items()]
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": tasks})


def events(host, name: str = "idea_flagged") -> list[dict]:
    return [r for r in event_log.read(Path(host.repo_root)) if r["event"] == name]


def go_done(host, slug: str) -> None:
    """What the runner does when its last task is merged: the state moves to `done` and the bus says so (the host sees the move)."""
    host.ideas.changed(slug)                                           # the host has seen it at work first (a restart sees no move)
    ideas.save_state(host.ideas.state_dir, slug, state="done")
    host.ideas.changed(slug)


# -- the tally and the file ---------------------------------------------------------------------------------------

def talk_from(host, slug: str, at: str) -> None:
    folder = ideas.state_folder(host.ideas.state_dir, slug)
    (folder / "talk.jsonl").write_text(json.dumps({"who": "you", "text": "x", "section": "", "at": at}) + "\n")


def test_the_tally_counts_merged_tasks_the_first_time_dollars_and_days(host):
    state = host.ideas.state_dir
    slug = goal(host, "Cache the table", "done")
    tasks = [{"id": "k1", "state": "merged", "round": 1}, {"id": "k2", "state": "merged", "round": 2},
             {"id": "ck", "state": "merged", "round": 1, "kind": "check"}, {"id": "k3", "state": "failed", "round": 1},
             {"id": "k4", "state": "review", "round": 1}]
    ideas.save_plan(state, slug, {"idea": slug, "tasks": tasks})
    talk_from(host, slug, "2026-10-10T08:00:00")
    now = dt.datetime(2026, 10, 14, 12, 0).astimezone()
    got = idea_flag.tally(host.ideas.root(), state, slug, now=now)
    assert got == {"tasks": 3, "first_time": 2, "usd": None, "days": 4}          # code and checks; unpriced is None, never 0
    ledger = ideas.state_folder(state, slug) / idea_spend.FILE
    ledger.write_text(json.dumps({"at": "2026-10-09T08:00:00", "step": "task", "task": "k1", "round": 1, "role": "grunt", "cost": 1.234}) + "\n")
    got = idea_flag.tally(host.ideas.root(), state, slug, now=now)
    assert got["usd"] == 1.23 and got["days"] == 5                                # the ledger's first line is the older start
    assert idea_flag.tally(host.ideas.root(), state, slug, now=dt.datetime(2026, 10, 9, 9, 0).astimezone())["days"] == 1   # at least one
    json.dumps(got)


def test_a_flag_by_done_takes_the_day_the_host_gives_and_keeps_it(host):
    state, root = host.ideas.state_dir, host.ideas.root()
    slug = goal(host, "Old goal", "done")
    first = idea_flag.raise_flag(root, state, slug, "done", "", at="2026-10-26")
    assert (first["by"], first["at"]) == ("done", "2026-10-26T00:00:00")
    assert idea_flag.raise_flag(root, state, slug, "done", "e" * 40, at="2026-11-02") == first            # once-only: at and by never rewritten
    assert idea_flag.raise_flag(root, state, slug, "gate", "f" * 40) == idea_flag.flag_of(state, slug) == first
    other = goal(host, "Other old goal", "done")
    assert idea_flag.raise_flag(root, state, other, "done", at=dt.date(2026, 10, 27))["at"] == "2026-10-27T00:00:00"
    with pytest.raises(ValueError):
        idea_flag.raise_flag(root, state, goal(host, "Third", "done"), "gate", at="2026-10-26")        # a day is for done only
    with pytest.raises(ValueError):
        idea_flag.raise_flag(root, state, goal(host, "Fourth", "done"), "done", at="last week")


# -- the gate's path ----------------------------------------------------------------------------------------------

def seen(host) -> list[str]:
    got: list[str] = []
    host.ideas.host.bus.subscribe(idea_keeper.CHANGED, lambda e: got.append(e.data.get("slug")))
    return got


def test_the_gate_raises_the_flag_of_each_done_goal_it_took_into_main(host, repo):
    done, working, other = goal(host, "Sync the queue", "done"), goal(host, "Retry on failure", "working"), goal(host, "Cache", "done")
    c1, c2 = land(repo, done, "k1", "q.txt"), land(repo, done, "k2", "r.txt")
    plan(host, done, k1=c1, k2=c2)
    plan(host, working, k1=land(repo, working, "k1", "w.txt"))                                       # in dev too, but not done
    plan(host, other, k1="", k2=git(repo, "rev-parse", "main"))                                      # done and in main before: no backfill
    heard = seen(host)
    got = host.command("ideas.gate_merge", {"sealed": True})
    flag = idea_flag.flag_of(host.ideas.state_dir, done)
    assert flag and flag["by"] == "gate" and flag["commit"] == got["commit"] and flag["tasks"] == 2 and flag["first_time"] == 2
    assert idea_flag.flag_of(host.ideas.state_dir, working) is None                                 # not done: it waits
    assert idea_flag.flag_of(host.ideas.state_dir, other) is None                                   # its work was in main before this spec
    (e,) = events(host)
    assert (e["idea"], e["goal"], e["by"], e["tasks"], e["first_time"], e["usd"], e["days"]) == (done, "first-party", "gate", 2, 2, None, e["days"])
    assert isinstance(e["days"], int) and e["days"] >= 1
    assert done in heard and heard.index(done) < len(heard) - 1 and heard[-1] == ""                  # ideas.changed with its slug, then the press's own
    assert len(events(host, "gate_merged")) == 1
    row = next(r for r in host.command("ideas.today")["events"] if r["mark"] == "⚑")                # today's strip, the recap and the flags say it
    assert (row["words"], row["title"], row["goal"], row["idea"], row["open"]) == ("is in main", "Sync the queue", "first-party", done, {"kind": "idea", "slug": done})
    recap = host.command("ideas.recap", {"since": (dt.datetime.now() - dt.timedelta(hours=1)).timestamp() * 1000})
    assert [(f["idea"], f["goal"], f["met"], f["by"]) for f in recap["flags"]] == [(done, "first-party", True, "gate")]
    assert [g["slug"] for g in host.command("ideas.flags")["goals"]] == [done]


def test_a_goal_that_is_not_done_never_gets_a_flag_and_a_failed_one_neither(host, repo):
    slug = goal(host, "Sync the queue", "working")
    plan(host, slug, k1=git(repo, "rev-parse", "main"))
    host.ideas.changed(slug)
    ideas.save_state(host.ideas.state_dir, slug, state="failed", error="x")
    host.ideas.changed(slug)
    assert idea_flag.flag_of(host.ideas.state_dir, slug) is None and events(host) == []

