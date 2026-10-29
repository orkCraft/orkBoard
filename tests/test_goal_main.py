"""Spec 105 §5 (docs/specs/105-the-default-tool-moving-on-and-the-portal.md): a goal to main on its own (realm/goal_main.py,
`ideas.to_main_plan` and `ideas.to_main` in gui/ideas_gate.py) on a real git repository: dev holds the goals' tasks landed one after
the other, main holds the start; a goal goes to main by its commits cherry-picked, so main holds them under new shas."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import event_log, goal_main, idea_flag, idea_gate, ideas
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_in(path: Path, name: str, text: str, message: str = "") -> str:
    (path / name).parent.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", message or f"edit {name}")
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
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "start")
    commit_in(r, "old.txt", "older work\n")
    git(r, "branch", "dev")
    return r


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def goal(host, text: str, state: str = "done") -> str:
    root = host.ideas.root()
    party = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First party")
    slug = host.command("ideas.add", {"text": text, "track": party, "hold": True})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state=state)
    return slug


def task(host, repo: Path, slug: str, tid: str, files: dict[str, str]) -> list[str]:
    """A task as the runner runs it: a worktree off dev, a commit per file, landed into dev; its plan keeps `commit` and `subjects`.
    The commits it brought, oldest first."""
    state = host.ideas.state_dir
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, tid, "dev")
    for name, text in files.items():
        commit_in(path, name, text)
    sha, subjects, _note = g.land(path, branch, "dev", push=False)
    g.remove(path)
    plan = ideas.plan(state, slug) or {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": []}
    plan["tasks"].append({"id": tid, "title": f"Task {tid}", "state": "merged", "commit": sha, "subjects": subjects, "after": [], "round": 1})
    ideas.save_plan(state, slug, plan)
    return git(repo, "log", "--reverse", f"-n{len(subjects)}", "--format=%H", sha).split()


def unfinished(host, slug: str) -> None:
    """The goal has one more task, at Review."""
    plan = ideas.plan(host.ideas.state_dir, slug)
    plan["tasks"].append({"id": "rv", "title": "Waiting", "state": "review", "commit": "", "after": [], "round": 1})
    ideas.save_plan(host.ideas.state_dir, slug, plan)
    ideas.save_state(host.ideas.state_dir, slug, state="running")


def depends(host, slug: str, *on: str) -> None:
    ideas.set_meta(host.ideas.root(), slug, depends_on=json.dumps(list(on)))


def short(host, slug: str) -> str:
    return next(i["short"] for i in ideas.ideas(host.ideas.root()) if i["slug"] == slug)


def plan_of(host, repo: Path, slug: str) -> dict:
    return goal_main.plan(repo, host.ideas.state_dir, slug, root=host.ideas.root(), into="dev", main="main")


def worktrees(repo: Path) -> list[str]:
    """The worktrees of the gate (a leftover of a pick would be one)."""
    return [ln for ln in git(repo, "worktree", "list", "--porcelain").splitlines() if ln.startswith("worktree ") and "gate-main" in ln]


def events(host, name: str) -> list[dict]:
    return [r for r in event_log.read(Path(host.repo_root)) if r["event"] == name]


@pytest.fixture
def work(host, repo):
    """dev: Lobby's first task (two commits), Chat's task, the person's own commit, Lobby's second task. Lobby, Chat done."""
    lobby, chat = goal(host, "Lobby\nwhere players meet"), goal(host, "Chat rooms")
    l1 = task(host, repo, lobby, "k1", {"lobby/room.ts": "room\n", "lobby/player.ts": "player\n"})
    c1 = task(host, repo, chat, "k1", {"chat/room.ts": "chat\n"})
    git(repo, "checkout", "-q", "dev")
    own = commit_in(repo, "own.txt", "the person's own commit\n")
    git(repo, "checkout", "-q", "main")
    l2 = task(host, repo, lobby, "k2", {"lobby/join.ts": "join\n"})
    return lobby, chat, l1, c1, own, l2


# -- the plan -----------------------------------------------------------------------------------------------------

def test_a_goals_commits_are_its_tasks_ranges_in_the_order_they_landed(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    got = plan_of(host, repo, lobby)
    assert got["goals"] == [lobby] and got["commits"] == [*l1, *l2] and got["sealed"] is None       # not Chat's, not the person's own
    assert got["files"] == 3 and got["titles"] == {lobby: short(host, lobby)}
    assert plan_of(host, repo, chat)["commits"] == c1 and own not in got["commits"]
    assert worktrees(repo) == []                                         # the trial's worktree is gone


def test_the_goals_it_stands_on_come_with_it_in_the_order_dev_holds_them(host, repo, work):
    lobby, chat, l1, c1, _own, l2 = work
    depends(host, lobby, chat)
    got = plan_of(host, repo, lobby)
    assert got["goals"] == [lobby, chat] and got["commits"] == [*l1, *c1, *l2] and got["sealed"] is None
    assert got["titles"] == {lobby: short(host, lobby), chat: short(host, chat)}
    depends(host, chat, "no-such-goal")                                                    # a goal the Board lost is nothing to stand on
    assert plan_of(host, repo, chat)["goals"] == [chat]


def test_a_goal_main_has_already_is_not_stood_on(host, repo, work):
    lobby, chat, _l1, _c1, _own, _l2 = work
    depends(host, lobby, chat)
    goal_main.merge(repo, host.ideas.state_dir, chat, root=host.ideas.root())
    got = plan_of(host, repo, lobby)
    assert got["goals"] == [lobby] and got["sealed"] is None                               # main holds Chat, under new shas


def test_a_goal_that_changed_the_same_files_earlier_comes_with_it(host, repo):
    first, second, third = goal(host, "Lobby"), goal(host, "Reconnect"), goal(host, "Scores")
    a = task(host, repo, first, "k1", {"shared/player.ts": "one\n"})
    b = task(host, repo, third, "k1", {"scores.ts": "scores\n"})                          # touches nothing the others do
    c = task(host, repo, second, "k1", {"shared/player.ts": "one\ntwo\n"})                 # on Lobby's file, later
    got = plan_of(host, repo, second)
    assert got["goals"] == [second, first] and got["commits"] == [*a, *c] and got["sealed"] is None and b[0] not in got["commits"]
    assert plan_of(host, repo, first)["goals"] == [first]                                  # the earlier goal stands on nothing
    assert plan_of(host, repo, third)["goals"] == [third]


# -- by patch id --------------------------------------------------------------------------------------------------

def test_a_pick_is_in_main_by_its_patch_id_and_the_gate_does_not_count_it_again(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    before = host.command("ideas.gate")
    assert before["commits"] == 5 and [i["slug"] for i in before["ideas"]] == [lobby, chat] and before["files"] == 5
    got = host.command("ideas.to_main", {"idea": lobby})
    assert got["ok"] is True and got["goals"] == [lobby] and got["note"] == ""
    assert git(repo, "rev-parse", "main") == got["commit"] and set(git(repo, "rev-list", "main..dev").split()) >= {*l1, *l2}   # by sha: still ahead
    after = host.command("ideas.gate")
    assert after["commits"] == 2 and after["files"] == 2 and [i["slug"] for i in after["ideas"]] == [chat]
    pending, equal = idea_gate.cherry(IdeaGit(repo), "dev", "main")
    assert pending == [*c1, own] and equal == {*l1, *l2}
    git_ = IdeaGit(repo)
    assert goal_main.in_main(git_, [*l1, *l2], "dev", "main") is True and goal_main.in_main(git_, [*l1, *c1], "dev", "main") is False
    assert goal_main.in_main(git_, [], "dev", "main") is False and goal_main.in_main(git_, [git(repo, "rev-parse", "main")], "dev", "main") is True


def test_dev_whole_still_goes_after_a_goal_went_alone(host, repo, work):
    lobby, chat, *_ = work
    host.command("ideas.to_main", {"idea": lobby})
    got = host.command("ideas.gate_merge")
    assert got["ok"] is True and git(repo, "merge-base", "--is-ancestor", "dev", "main") == ""
    assert host.command("ideas.gate")["commits"] == 0 and (repo / "chat" / "room.ts").exists() and (repo / "own.txt").exists()
    (e,) = events(host, "gate_merged")
    assert e["commits"] == 2                                                             # Chat's and the person's: not Lobby's again
    assert idea_flag.flag_of(host.ideas.state_dir, chat)["by"] == "gate"


# -- sealed -------------------------------------------------------------------------------------------------------

def test_a_goal_with_a_task_not_landed_is_sealed_in_words(host, repo, work):
    lobby, *_ = work
    unfinished(host, lobby)
    got = plan_of(host, repo, lobby)
    assert got["sealed"] == f"{short(host, lobby)} is not done yet"
    with pytest.raises(CommandError, match="is not done yet"):
        host.command("ideas.to_main", {"idea": lobby})
    assert git(repo, "log", "-1", "--format=%s", "main") == "edit old.txt"


def test_a_goal_it_stands_on_that_is_not_done_seals_it(host, repo, work):
    lobby, chat, *_ = work
    depends(host, lobby, chat)
    unfinished(host, chat)
    assert plan_of(host, repo, lobby)["sealed"] == f"{short(host, chat)} is not done yet"
    assert host.command("ideas.to_main_plan", {"idea": lobby})["sealed"] == f"{short(host, chat)} is not done yet"
    third = goal(host, "Never started", state="raw")                                       # no plan at all
    depends(host, lobby, third)
    assert plan_of(host, repo, lobby)["sealed"] in (f"{short(host, chat)} is not done yet", f"{short(host, third)} is not done yet")


def test_a_pick_that_would_conflict_seals_it_with_the_files_and_leaves_nothing_behind(host, repo):
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"a.txt": "dev's a\n"})
    commit_in(repo, "a.txt", "main's own a\n")                                              # main moved on the same file
    before = git(repo, "rev-parse", "main")
    got = plan_of(host, repo, lobby)
    assert got["sealed"] == f"{short(host, lobby)} does not apply to main cleanly: a.txt" and len(got["commits"]) == 1
    with pytest.raises(CommandError, match="does not apply to main cleanly: a.txt"):
        host.command("ideas.to_main", {"idea": lobby})
    assert git(repo, "rev-parse", "main") == before and worktrees(repo) == []
    assert git(repo, "status", "--porcelain") == "" and events(host, "goal_to_main") == []
    assert idea_flag.flag_of(host.ideas.state_dir, lobby) is None


def test_a_goal_in_main_already_and_a_goal_without_commits_have_nothing_to_send(host, repo, work):
    lobby, chat, *_ = work
    host.command("ideas.to_main", {"idea": lobby})
    assert plan_of(host, repo, lobby)["sealed"] == f"{short(host, lobby)} is in main already"
    with pytest.raises(CommandError, match="is in main already"):
        host.command("ideas.to_main", {"idea": lobby})
    check = goal(host, "A check only")
    ideas.save_plan(host.ideas.state_dir, check, {"idea": check, "tasks": [{"id": "c1", "state": "merged", "commit": "", "after": []}]})
    assert plan_of(host, repo, check)["sealed"] == f"{short(host, check)} has nothing to send to main"


def test_main_behind_its_origin_seals_it(host, repo, tmp_path):
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "main")
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"lobby.ts": "l\n"})
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(remote), str(other))
    git(other, "config", "user.email", "o@x")
    git(other, "config", "user.name", "O")
    commit_in(other, "elsewhere.txt", "pushed from elsewhere\n")
    git(other, "push", "-q", "origin", "main")
    git(repo, "fetch", "-q", "origin")
    assert plan_of(host, repo, lobby)["sealed"] == "main is behind origin/main: pull it first"


def test_without_a_gate_there_is_nothing_to_send(host, repo):
    lobby = goal(host, "Lobby")
    got = goal_main.plan(repo, host.ideas.state_dir, lobby, root=host.ideas.root(), into="main", main="main")
    assert got["sealed"] == "Results merge into main itself: there is no gate" and got["commits"] == []


# -- the merge ----------------------------------------------------------------------------------------------------

def test_the_merge_picks_the_commits_in_order_onto_main_and_the_checkout_follows(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    depends(host, lobby, chat)
    rev = host.snapshot()["ideas_rev"]
    got = host.command("ideas.to_main", {"idea": lobby})
    assert got["ok"] is True and got["goals"] == [lobby, chat] and got["note"] == ""
    assert git(repo, "rev-parse", "main") == got["commit"]
    assert git(repo, "log", "--format=%s", "-4", "main").split("\n")[::-1] == [
        "edit lobby/room.ts", "edit lobby/player.ts", "edit chat/room.ts", "edit lobby/join.ts"]
    assert not (repo / "own.txt").exists()                                                  # the person's own commit stays in dev
    assert all((repo / n).exists() for n in ("lobby/room.ts", "lobby/player.ts", "lobby/join.ts", "chat/room.ts"))   # main is checked out
    assert git(repo, "status", "--porcelain") == "" and worktrees(repo) == []
    assert git(repo, "rev-parse", "dev") == l2[-1] and own in git(repo, "rev-list", "dev").split()   # dev is not moved
    (e,) = events(host, "goal_to_main")
    assert (e["idea"], e["goals"], e["commits"], e["files"], e["pushed"], e["device"]) == (lobby, [lobby, chat], 4, 4, False, "desktop")
    assert (e["into"], e["main"]) == ("dev", "main") and host.snapshot()["ideas_rev"] > rev
    assert git(repo, "log", "-1", "--format=%an", "main") == "T"                           # the author stays


def test_dev_is_not_moved_and_a_main_not_checked_out_moves_by_update_ref(host, repo, work):
    lobby, *_ = work
    dev = git(repo, "rev-parse", "dev")
    git(repo, "checkout", "-q", "-b", "mine")
    host.command("ideas.to_main", {"idea": lobby, "device": "phone"})
    assert git(repo, "rev-parse", "dev") == dev and not (repo / "lobby").exists()
    assert git(repo, "show", "main:lobby/join.ts") == "join" and git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "mine"
    assert events(host, "goal_to_main")[0]["device"] == "phone"


def test_the_flags_of_the_goals_it_took_are_raised_and_a_goal_left_behind_has_none(host, repo, work):
    lobby, chat, *_ = work
    other = goal(host, "Other")
    task(host, repo, other, "k1", {"other.txt": "o\n"})
    depends(host, lobby, chat)
    got = host.command("ideas.to_main", {"idea": lobby})
    for slug in (lobby, chat):
        flag = idea_flag.flag_of(host.ideas.state_dir, slug)
        assert flag and flag["by"] == "gate" and flag["commit"] == got["commit"]
    assert idea_flag.flag_of(host.ideas.state_dir, other) is None
    assert sorted(e["idea"] for e in events(host, "idea_flagged")) == sorted([lobby, chat])


def test_a_goal_not_done_gets_no_flag_and_a_goal_stood_on_waits_for_nothing_it_lacks(host, repo):
    lobby = goal(host, "Lobby", state="done")
    task(host, repo, lobby, "k1", {"lobby.ts": "l\n"})
    host.command("ideas.to_main", {"idea": lobby})
    assert idea_flag.flag_of(host.ideas.state_dir, lobby)["by"] == "gate"
    assert host.command("ideas.gate")["commits"] == 0


def test_it_pushes_when_the_project_pushes_after_merging(host, repo, tmp_path):
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "main")
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"lobby.ts": "l\n"})
    host.ideas.save_settings({**host.ideas.settings_now(), "push": True})
    got = host.command("ideas.to_main", {"idea": lobby})
    assert got["note"] == "" and git(remote, "rev-parse", "main") == git(repo, "rev-parse", "main") == got["commit"]
    assert events(host, "goal_to_main")[0]["pushed"] is True
    second = goal(host, "Second")
    task(host, repo, second, "k1", {"second.ts": "s\n"})
    host.ideas.save_settings({**host.ideas.settings_now(), "push": False})
    host.command("ideas.to_main", {"idea": second})
    assert git(remote, "rev-parse", "main") != git(repo, "rev-parse", "main")


# -- the commands -------------------------------------------------------------------------------------------------

def test_the_commands_round_trip_and_the_phone_may_send_them(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    assert BoardPhone.allowed(host, "ideas.to_main_plan", {}) and BoardPhone.allowed(host, "ideas.to_main", {})
    depends(host, lobby, chat)
    seen = host.command("ideas.to_main_plan", {"idea": lobby})
    assert seen == {"idea": lobby, "goals": [lobby, chat], "commits": [*l1, *c1, *l2], "sealed": None, "files": 4,
                    "titles": {lobby: short(host, lobby), chat: short(host, chat)}, "into": "dev", "main": "main"}
    assert not (repo / "lobby").exists() and git(repo, "log", "-1", "--format=%s", "main") == "edit old.txt"      # a plan moves nothing
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.to_main_plan", {})
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.to_main", {})
    done = host.command("ideas.to_main", {"idea": lobby})
    assert done["ok"] is True and done["goals"] == [lobby, chat]
    assert host.command("ideas.to_main_plan", {"idea": chat})["sealed"] == f"{short(host, chat)} is in main already"
