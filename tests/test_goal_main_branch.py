"""Spec 168 F3 (decisions §283.26, §283.28): a goal that came into dev through its own branch goes to main as any goal does. Dev was merged into its branch as a step started, so its
commits in dev have merge commits among them that belong to no goal: `commit_goal.index` and `goal_main.plan` must name the goal's own commits only, in the order dev holds them."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import commit_goal, goal_branch, goal_main, idea_gate, ideas
from orkboard.realm.idea_git import IdeaGit

from tests.test_goal_main import commit_in, git, goal


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "orkcraft.toml").write_text("[gate]\nrun = \"true\"\n")
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "start")
    git(r, "branch", "dev")
    return r


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def land(host, repo: Path, slug: str, tid: str, onto: str, files: dict[str, str]) -> list[str]:
    """A task as the runner runs it, landed on `onto` (a goal's branch, or dev); its plan keeps `commit` and `subjects`. The commits it brought, oldest first."""
    state = host.ideas.state_dir
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, tid, onto)
    for name, text in files.items():
        commit_in(path, name, text)
    sha, subjects, _note = g.land(path, branch, onto, push=False)
    g.remove(path)
    plan = ideas.plan(state, slug) or {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "tasks": []}
    plan["tasks"].append({"id": tid, "title": f"Task {tid}", "state": "merged", "commit": sha, "subjects": subjects, "after": [], "round": 1})
    ideas.save_plan(state, slug, plan)
    return git(repo, "log", "--reverse", f"-n{len(subjects)}", "--format=%H", sha).split()


def plan_of(host, repo: Path, slug: str) -> dict:
    return goal_main.plan(repo, host.ideas.state_dir, slug, root=host.ideas.root(), into="dev", main="main")


@pytest.fixture
def through_branch(host, repo):
    """Lobby begins on its branch (task k1); Chat lands in dev beside it, and the person commits there; Lobby's second step starts (dev merged into its branch: a merge commit), its task
    k2 lands on the branch; the goal goes into dev once, by fast-forward. Returns the slugs, the commits of each and the merge commit."""
    state, g = host.ideas.state_dir, IdeaGit(repo)
    lobby, chat = goal(host, "Lobby\nwhere players meet"), goal(host, "Chat rooms")
    branch = goal_branch.begin(g, state, lobby, {"tasks": []}, "dev", 1)
    l1 = land(host, repo, lobby, "k1", branch, {"lobby/room.ts": "room\n", "lobby/player.ts": "player\n"})
    c1 = land(host, repo, chat, "k1", "dev", {"chat/room.ts": "chat\n"})
    git(repo, "checkout", "-q", "dev")
    own = commit_in(repo, "own.txt", "the person's own commit\n")
    git(repo, "checkout", "-q", "main")
    goal_branch.step_started(g, state, lobby, 2, "dev")
    merge = git(repo, "rev-parse", branch)
    assert len(git(repo, "rev-list", "--parents", "-n1", merge).split()) == 3, "dev was merged into the goal's branch: a merge commit"
    l2 = land(host, repo, lobby, "k2", branch, {"lobby/join.ts": "join\n"})
    goal_branch.ready(state, lobby)
    got = goal_branch.to_dev(g, state, lobby, "dev", untested=True)
    assert git(repo, "rev-parse", "dev") == got["commit"] == l2[-1]                      # fast-forward: dev holds the branch's own commits and its merge commit
    return lobby, chat, l1, c1, own, l2, merge


def test_the_index_names_a_goals_own_commits_and_not_the_merge_commit_between_them(host, repo, through_branch):
    lobby, chat, l1, c1, own, l2, merge = through_branch
    owner = commit_goal.index(host.ideas.state_dir, repo, "dev")
    assert [s for s in (*l1, *l2) if owner.get(s, {}).get("goal") == lobby] == [*l1, *l2], "every commit of Lobby's tasks is Lobby's"
    assert [owner[s]["task"] for s in (*l1, *l2)] == ["k1", "k1", "k2"]
    assert owner[c1[0]]["goal"] == chat
    assert merge not in owner and own not in owner, "a merge commit of dev into the goal, and the person's own commit, belong to no goal"


def test_to_main_takes_the_goals_commits_in_dev_order_and_not_the_merge_commit(host, repo, through_branch):
    lobby, chat, l1, c1, own, l2, merge = through_branch
    plan = plan_of(host, repo, lobby)
    assert plan["sealed"] is None and plan["goals"] == [lobby]
    assert plan["commits"] == [*l1, *l2], "the goal's own commits, oldest first"
    assert merge not in plan["commits"]
    other = plan_of(host, repo, chat)
    assert other["sealed"] is None and other["commits"] == c1 and other["goals"] == [chat]


def test_the_merge_picks_the_goal_onto_main_and_a_goal_beside_it_is_still_waiting(host, repo, through_branch):
    lobby, chat, l1, c1, own, l2, merge = through_branch
    got = goal_main.merge(repo, host.ideas.state_dir, lobby, False, root=host.ideas.root(), into="dev", main="main")
    assert got["goals"] == [lobby] and len(got["commits"]) == 3
    tree = git(repo, "ls-tree", "-r", "--name-only", "main").split()
    assert {"lobby/room.ts", "lobby/player.ts", "lobby/join.ts"} <= set(tree) and "chat/room.ts" not in tree and "own.txt" not in tree
    assert goal_main.in_main(IdeaGit(repo), [*l1, *l2], "dev", "main"), "by patch id, never by sha: the picks are new commits"
    after = plan_of(host, repo, chat)
    assert after["commits"] == c1 and after["sealed"] is None, "Chat did not go with Lobby, and goes after it"
    pending, _same = idea_gate.cherry(IdeaGit(repo), "dev", "main")
    assert l1[0] not in pending and c1[0] in pending


def test_dev_merged_into_the_goal_a_second_time_at_the_end_is_no_goals_either(host, repo):
    """Dev moves while the goal's last step runs: the merge into dev merges dev into the branch once more, the merge commit is the branch's tip, and the goal still goes alone."""
    state, g = host.ideas.state_dir, IdeaGit(repo)
    lobby, chat = goal(host, "Lobby\nwhere players meet"), goal(host, "Chat rooms")
    branch = goal_branch.begin(g, state, lobby, {"tasks": []}, "dev", 1)
    l1 = land(host, repo, lobby, "k1", branch, {"lobby/room.ts": "room\n"})
    c1 = land(host, repo, chat, "k1", "dev", {"chat/room.ts": "chat\n"})
    goal_branch.ready(state, lobby)
    got = goal_branch.to_dev(g, state, lobby, "dev", untested=True)
    tip = got["commit"]
    assert len(git(repo, "rev-list", "--parents", "-n1", tip).split()) == 3, "the branch's tip is the merge of dev"
    owner = commit_goal.index(state, repo, "dev")
    assert owner[l1[0]]["goal"] == lobby and owner[c1[0]]["goal"] == chat and tip not in owner
    assert plan_of(host, repo, lobby)["commits"] == l1 and plan_of(host, repo, chat)["commits"] == c1
    done = goal_main.merge(repo, state, chat, False, root=host.ideas.root(), into="dev", main="main")
    assert done["goals"] == [chat] and "lobby/room.ts" not in git(repo, "ls-tree", "-r", "--name-only", "main").split()
