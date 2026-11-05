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
from orkboard.realm.idea_git import BOARD_EMAIL, BOARD_NAME, IdeaGit


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


# -- ready for main (spec 143 F.3, F.4) ---------------------------------------------------------------------------

def test_a_goal_with_a_task_failed_or_still_to_do_is_not_ready_for_main(host, repo, work):
    lobby, chat, *_ = work
    assert [i["slug"] for i in host.command("ideas.gate")["ideas"]] == [lobby, chat]
    for state in ("failed", "waiting", "ready", "running", "review"):
        plan = ideas.plan(host.ideas.state_dir, lobby)
        plan["tasks"] = [t for t in plan["tasks"] if t["id"] != "later"] + [{"id": "later", "title": "Later", "state": state, "commit": "", "after": [], "round": 1}]
        ideas.save_plan(host.ideas.state_dir, lobby, plan)
        got = host.command("ideas.gate")
        assert [i["slug"] for i in got["ideas"]] == [chat], f"a task {state}: Lobby is not ready for main"
        assert got["commits"] == 2 and got["files"] == 2, "its commits are left out of the count: Chat's and the person's own are what is ready (spec 149 G.3)"
    plan = ideas.plan(host.ideas.state_dir, lobby)
    plan["tasks"][-1]["state"] = "dropped"
    ideas.save_plan(host.ideas.state_dir, lobby, plan)
    assert [i["slug"] for i in host.command("ideas.gate")["ideas"]] == [lobby, chat], "a dropped task holds nothing back"


def test_the_boards_own_commits_are_no_pile_but_a_code_commit_of_no_goal_is(host, repo):
    git(repo, "checkout", "-q", "dev")
    commit_in(repo, "wiki/pages/tracks/tech.md", "# Tech\n", "The Board lays the table")
    commit_in(repo, "wiki/pages/ideas/first.md", "# First\n", "The Board writes a goal")
    git(repo, "checkout", "-q", "main")
    got = host.command("ideas.gate")
    assert got["commits"] == 0 and got["files"] == 0 and got["ideas"] == [], "a laid table with no work has no pile"
    git(repo, "checkout", "-q", "dev")
    commit_in(repo, "own.txt", "the person's own commit\n")
    git(repo, "checkout", "-q", "main")
    got = host.command("ideas.gate")
    assert got["commits"] == 1 and got["files"] == 1, "a commit of code that belongs to no goal still counts, the Board's two do not"
    host.command("ideas.gate_merge")
    assert (repo / "wiki" / "pages" / "tracks" / "tech.md").exists(), "they go into main with the next merge"


# -- one pile, half a goal refused, the Board's own (spec 149 G.2, G.3, G.4) --------------------------------------

def test_dev_whole_is_refused_in_words_while_a_goal_with_commits_in_dev_is_not_ready(host, repo, work):
    lobby, chat, *_ = work
    unfinished(host, lobby)
    with pytest.raises(CommandError) as e:
        host.command("ideas.gate_merge")
    assert str(e.value) == f"{short(host, lobby)} is at 2 of 3: it would reach main half made.", "the words say the goal, how far it is and why"
    assert git(repo, "rev-parse", "main") != git(repo, "rev-parse", "dev") and events(host, "gate_merged") == [], "main is as it was"
    plan = ideas.plan(host.ideas.state_dir, lobby)
    plan["tasks"] = [t for t in plan["tasks"] if t["id"] != "rv"]
    ideas.save_plan(host.ideas.state_dir, lobby, plan)
    assert host.command("ideas.gate_merge")["ok"] is True, "ready again: the press goes"
    assert idea_flag.flag_of(host.ideas.state_dir, chat) is not None


def test_commits_that_belong_to_no_goal_still_go_with_dev_whole_while_a_goal_is_ready_or_has_no_commits_there(host, repo):
    git(repo, "checkout", "-q", "dev")
    commit_in(repo, "own.txt", "the person's own commit\n")
    git(repo, "checkout", "-q", "main")
    assert host.command("ideas.gate")["commits"] == 1 and host.command("ideas.gate_merge")["ok"] is True
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "dev")


def test_the_pile_counts_only_the_commits_of_goals_ready_and_of_no_goal(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    got = host.command("ideas.gate")
    assert got["commits"] == 5 and got["files"] == 5 and [i["slug"] for i in got["ideas"]] == [lobby, chat]
    unfinished(host, lobby)
    got = host.command("ideas.gate")
    assert got["commits"] == 2 and got["files"] == 2 and [i["slug"] for i in got["ideas"]] == [chat], "Lobby's three commits and three files are left out"
    unfinished(host, chat)
    got = host.command("ideas.gate")
    assert got["commits"] == 1 and got["files"] == 1 and got["ideas"] == [], "only the person's own commit, which belongs to no goal"


def test_a_goal_sent_alone_when_ready_leaves_a_pile_that_says_nothing_after_the_board_folds(host, repo, work):
    lobby, chat, *_ = work
    host.command("ideas.to_main", {"idea": lobby})
    host.command("ideas.to_main", {"idea": chat})
    host.command("ideas.gate_merge")                                                         # the person's own commit goes with dev whole: nothing else is left
    git(repo, "checkout", "-q", "dev")
    (repo / "llm-wiki" / "wiki" / "specs").mkdir(parents=True)
    (repo / "llm-wiki" / "wiki" / "specs" / "lobby.md").write_text("# Lobby\n")
    git(repo, "add", "-A")
    git(repo, "-c", f"user.name={BOARD_NAME}", "-c", f"user.email={BOARD_EMAIL}", "commit", "-q", "-m", "board: the fold", "--author", f"{BOARD_NAME} <{BOARD_EMAIL}>")
    git(repo, "checkout", "-q", "main")
    got = host.command("ideas.gate")
    assert got["commits"] == 0 and got["files"] == 0 and got["ideas"] == [], "the fold's commit is the Board's: no pile"


def test_without_board_pages_leaves_out_a_commit_authored_by_the_board_and_keeps_a_persons(repo):
    git(repo, "checkout", "-q", "dev")
    (repo / "llm-wiki" / "wiki" / "specs").mkdir(parents=True)
    (repo / "llm-wiki" / "wiki" / "specs" / "lobby.md").write_text("# Lobby\n")
    git(repo, "add", "-A")
    git(repo, "-c", f"user.name={BOARD_NAME}", "-c", f"user.email={BOARD_EMAIL}", "commit", "-q", "-m", "board: the fold", "--author", f"{BOARD_NAME} <{BOARD_EMAIL}>")
    fold = git(repo, "rev-parse", "HEAD")
    mine = commit_in(repo, "llm-wiki/wiki/specs/other.md", "# Other\n", "a person edits a spec")
    git(repo, "checkout", "-q", "main")
    g = IdeaGit(repo)
    shas, files = idea_gate.waiting(g, "dev", "main")
    assert fold in shas and mine in shas
    assert idea_gate.without_board_pages(g, shas, files) == ([mine], 1)


def test_a_commit_by_the_board_under_either_name_is_no_pile(tmp_path):
    """The Board's commits said *Orkline board* before spec 149 F.3 and say *<the product> board* since: both are the Board's (§253.8)."""
    import subprocess
    from orkboard import brand
    from orkboard.realm import idea_gate
    from orkboard.realm.idea_git import BOARD_NAME, IdeaGit
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, text=True).stdout.strip()
    run("init", "-q", "-b", "main")
    shas = []
    for i, (who, email) in enumerate([(BOARD_NAME, "board@orkline.local"), brand.board_author(), ("Someone", "someone@example.com")]):
        (tmp_path / f"llm-wiki/specs/s{i}.md").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f"llm-wiki/specs/s{i}.md").write_text(f"{i}\n")
        run("add", "-A")
        run("-c", f"user.name={who}", "-c", f"user.email={email}", "commit", "-q", "-m", f"c{i}")
        shas.append(run("rev-parse", "HEAD"))
    kept, files = idea_gate.without_board_pages(IdeaGit(tmp_path), shas, 3)
    assert kept == shas[2:] and files == 1
