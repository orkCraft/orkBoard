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
    (r / "orkcraft.toml").write_text("[gate]\nrun = \"true\"\n")          # a gate with tests (the `true` command), as the checks need one (spec 158 B)
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


def to_main(host, slug: str, **more) -> dict:
    """What the page does (stage A, decisions §274): the checks on the way into main asked and waited for, then the goal sent."""
    import time
    host.command("ideas.to_main_checks", {"idea": slug})
    for _ in range(1000):
        got = host.ideas._main_checks.get(slug)
        if got and not got["running"]:
            break
        time.sleep(0.02)
    return host.command("ideas.to_main", {"sealed": True, "idea": slug, **more})


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



def test_the_goals_it_stands_on_come_with_it_in_the_order_dev_holds_them(host, repo, work):
    lobby, chat, l1, c1, _own, l2 = work
    depends(host, lobby, chat)
    got = plan_of(host, repo, lobby)
    assert got["goals"] == [lobby, chat] and got["commits"] == [*l1, *c1, *l2] and got["sealed"] is None
    assert got["titles"] == {lobby: short(host, lobby), chat: short(host, chat)}
    depends(host, chat, "no-such-goal")                                                    # a goal the Board lost is nothing to stand on
    assert plan_of(host, repo, chat)["goals"] == [chat]


# -- by patch id --------------------------------------------------------------------------------------------------

def test_a_pick_is_in_main_by_its_patch_id_and_the_gate_does_not_count_it_again(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    before = host.command("ideas.gate")
    assert before["commits"] == 5 and [i["slug"] for i in before["ideas"]] == [lobby, chat] and before["files"] == 5
    got = to_main(host, lobby)
    assert got["ok"] is True and got["goals"] == [lobby] and got["note"] == ""
    assert git(repo, "rev-parse", "main") == got["commit"] and set(git(repo, "rev-list", "main..dev").split()) >= {*l1, *l2}   # by sha: still ahead
    after = host.command("ideas.gate")
    assert after["commits"] == 2 and after["files"] == 2 and [i["slug"] for i in after["ideas"]] == [chat]
    pending, equal = idea_gate.cherry(IdeaGit(repo), "dev", "main")
    assert pending == [*c1, own] and equal == {*l1, *l2}
    git_ = IdeaGit(repo)
    assert goal_main.in_main(git_, [*l1, *l2], "dev", "main") is True and goal_main.in_main(git_, [*l1, *c1], "dev", "main") is False
    assert goal_main.in_main(git_, [], "dev", "main") is False and goal_main.in_main(git_, [git(repo, "rev-parse", "main")], "dev", "main") is True


# -- sealed -------------------------------------------------------------------------------------------------------

def test_a_goal_with_a_task_not_landed_is_sealed_in_words(host, repo, work):
    lobby, *_ = work
    unfinished(host, lobby)
    got = plan_of(host, repo, lobby)
    assert got["sealed"] == f"{short(host, lobby)} is not done yet"
    with pytest.raises(CommandError, match="is not done yet"):
        host.command("ideas.to_main", {"sealed": True, "idea": lobby})
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
        to_main(host, lobby)
    assert git(repo, "rev-parse", "main") == before and worktrees(repo) == []
    assert git(repo, "status", "--porcelain") == "" and events(host, "goal_to_main") == []
    assert idea_flag.flag_of(host.ideas.state_dir, lobby) is None


# -- the merge ----------------------------------------------------------------------------------------------------

def test_the_merge_picks_the_commits_in_order_onto_main_and_the_checkout_follows(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    depends(host, lobby, chat)
    rev = host.snapshot()["ideas_rev"]
    got = to_main(host, lobby)
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


def test_the_flags_of_the_goals_it_took_are_raised_and_a_goal_left_behind_has_none(host, repo, work):
    lobby, chat, *_ = work
    other = goal(host, "Other")
    task(host, repo, other, "k1", {"other.txt": "o\n"})
    depends(host, lobby, chat)
    got = to_main(host, lobby)
    for slug in (lobby, chat):
        flag = idea_flag.flag_of(host.ideas.state_dir, slug)
        assert flag and flag["by"] == "gate" and flag["commit"] == got["commit"]
    assert idea_flag.flag_of(host.ideas.state_dir, other) is None
    assert sorted(e["idea"] for e in events(host, "idea_flagged")) == sorted([lobby, chat])


# -- the commands -------------------------------------------------------------------------------------------------

def test_the_commands_round_trip_and_the_phone_may_send_them(host, repo, work):
    lobby, chat, l1, c1, own, l2 = work
    assert BoardPhone.allowed(host, "ideas.to_main_plan", {}) and BoardPhone.allowed(host, "ideas.to_main", {"sealed": True, "sealed": True})
    depends(host, lobby, chat)
    seen = host.command("ideas.to_main_plan", {"idea": lobby})
    assert seen == {"idea": lobby, "goals": [lobby, chat], "commits": [*l1, *c1, *l2], "sealed": None, "files": 4,
                    "titles": {lobby: short(host, lobby), chat: short(host, chat)}, "into": "dev", "main": "main"}
    assert not (repo / "lobby").exists() and git(repo, "log", "-1", "--format=%s", "main") == "edit old.txt"      # a plan moves nothing
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.to_main_plan", {})
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.to_main", {"sealed": True, "sealed": True})
    done = to_main(host, lobby)
    assert done["ok"] is True and done["goals"] == [lobby, chat]
    assert host.command("ideas.to_main_plan", {"idea": chat})["sealed"] == f"{short(host, chat)} is in main already"


# -- ready for main (spec 143 F.3, F.4) ---------------------------------------------------------------------------



# -- one pile, half a goal refused, the Board's own (spec 149 G.2, G.3, G.4) --------------------------------------

def test_dev_whole_is_refused_in_words_while_a_goal_with_commits_in_dev_is_not_ready(host, repo, work):
    lobby, chat, *_ = work
    unfinished(host, lobby)
    with pytest.raises(CommandError) as e:
        host.command("ideas.gate_merge", {"sealed": True})
    assert str(e.value) == f"{short(host, lobby)} is at 2 of 3: it would reach main half made.", "the words say the goal, how far it is and why"
    assert git(repo, "rev-parse", "main") != git(repo, "rev-parse", "dev") and events(host, "gate_merged") == [], "main is as it was"
    plan = ideas.plan(host.ideas.state_dir, lobby)
    plan["tasks"] = [t for t in plan["tasks"] if t["id"] != "rv"]
    ideas.save_plan(host.ideas.state_dir, lobby, plan)
    assert host.command("ideas.gate_merge", {"sealed": True})["ok"] is True, "ready again: the press goes"
    assert idea_flag.flag_of(host.ideas.state_dir, chat) is not None


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


def test_a_goal_in_dev_reaches_main_after_the_checks_with_no_release_party(host, repo):
    """Release is a craft as any (decisions §274.1): no Release party, and the goal still goes to main by `ideas.to_main`."""
    from orkboard.realm import goal_types
    slug = goal(host, "No Release seated")
    task(host, repo, slug, "t1", {"new.txt": "new\n"})
    assert goal_types.release_party(host.ideas.root()) == ""
    got = to_main(host, slug)
    assert got.get("ok", True) is not False
    assert "new.txt" in git(repo, "ls-tree", "--name-only", "-r", "main")


# -- the one named skip (spec 158 B, decisions §274.3) -------------------------------------------------------------



def test_untested_true_sends_without_asking_the_checks_and_logs_skipped(host, repo, work):
    lobby, *_ = work
    got = host.command("ideas.to_main", {"sealed": True, "idea": lobby, "untested": True})
    assert got["ok"] is True and git(repo, "rev-parse", "main") == got["commit"]
    (e,) = events(host, "goal_to_main")
    assert e["tests"] == "skipped" and "checks_s" not in e


def test_a_project_with_no_tests_is_refused_in_words_and_only_the_skip_sends_it(host, repo, work, monkeypatch):
    from orkboard.realm import gate_config
    lobby, *_ = work
    monkeypatch.setattr(gate_config, "read", lambda root: gate_config.Gate(always=(), none=True, derived=True))
    before = git(repo, "rev-parse", "main")
    with pytest.raises(CommandError, match="has no tests.*To main without the tests"):
        to_main(host, lobby)
    assert git(repo, "rev-parse", "main") == before and events(host, "goal_to_main") == []
    got = host.command("ideas.to_main", {"sealed": True, "idea": lobby, "untested": True})
    assert got["ok"] is True and events(host, "goal_to_main")[0]["tests"] == "skipped"
