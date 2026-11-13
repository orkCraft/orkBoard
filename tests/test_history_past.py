"""Spec 162 G (decisions §277): this repository's own past, read fresh. A Board over a copy of this repository's pages, specs and decisions log, in one commit, read as a first open does
(`phase_moved`, then `chronicle.read`): every done page but a release goal is in the whole project's past and none in the discard, Product's past holds goal 116 with §194, a second read changes nothing."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import chronicle, event_log, idea_flag, ideas, journals, releases

HERE = Path(__file__).resolve().parents[1]
IDEAS = "llm-wiki/general/pages/ideas"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture(scope="module")
def past(tmp_path_factory):
    """A fresh Board over a copy of this repository's pages, specs and decisions, its work branch holding them as an AI tool's commit."""
    tmp = tmp_path_factory.mktemp("past")
    repo = tmp / "project"
    repo.mkdir()
    (repo / "README.md").write_text("# Copy\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".orkcraft/\n", encoding="utf-8")
    for cmd in (["init", "-q"], ["config", "user.email", "t@x"], ["config", "user.name", "T"], ["add", "-A"], ["commit", "-qm", "start"]):
        git(repo, *cmd)
    host = Orkboard(repo)
    slug = ideas.add_idea(host.ideas.root(), "a dark mode", state_dir=host.ideas.state_dir, queue="hold")
    host.ideas.tree_note(slug, "added")
    host.ideas.tree_flush(force=True)
    work = tmp / "tool"
    git(repo, "worktree", "add", "-q", "--detach", str(work), "dev")
    shutil.copytree(HERE / "llm-wiki", work / "llm-wiki", ignore=shutil.ignore_patterns("AGENTS.md", "CLAUDE.md", "*.png", "*.jpg", "*.gif", "*.webp"), dirs_exist_ok=True)
    shutil.copytree(HERE / "docs/specs", work / "docs/specs", ignore=shutil.ignore_patterns("*.png", "*.jpg", "*.gif", "*.webp"), dirs_exist_ok=True)
    shutil.copy(HERE / "docs/decisions.md", work / "docs/decisions.md")
    git(work, "add", "-A")
    git(work, "-c", "user.name=Claude Code", "-c", "user.email=t@x", "commit", "-qm", "tool: laid goals")
    git(repo, "update-ref", "refs/heads/dev", git(work, "rev-parse", "HEAD"))
    (repo / "docs").mkdir(exist_ok=True)
    shutil.copy(work / "docs/decisions.md", repo / "docs/decisions.md")                           # the working copy, as the host reads the log
    host.ideas._phase_at = 0.0
    return host


def _keeper_fails(host):
    def fail(*a, **k):
        raise AssertionError("the keeper is not called")
    for name in ("fold", "ask", "decide", "talk_answer"):
        setattr(host.ideas.keeper, name, fail)


def _moved(host):
    tree = host.ideas._board_tree
    with tree.git.lock:
        tree.follow()
    host.ideas.phase_moved(tree)


def _snapshot(host):
    sd = host.ideas.state_dir
    done = [p.stem for p in Path(host.ideas.root()).rglob("*.md") if "phase: done" in p.read_text(encoding="utf-8")]
    return {s: (idea_flag.flag_of(sd, s), ideas.state(sd, s).get("seen_at")) for s in sorted(done)}


def _read(host, party=""):
    return chronicle.read(*host.ideas._chronicle_args(), party=party)                             # as the window reads it: the host's own arguments


@pytest.fixture(scope="module")
def first(past):
    sd = past.ideas.state_dir
    _keeper_fails(past)
    before = [e.get("text") for e in journals.read(sd, journals.PROJECT)]
    _moved(past)
    return {"before": before, "after": _snapshot(past)}


def test_every_done_page_but_a_release_goal_is_in_the_whole_projects_past_and_none_in_the_discard(past, first):
    sd = past.ideas.state_dir
    done = first["after"]
    assert len(done) > 100
    past_slugs = {g["idea"] for c in _read(past)["chapters"] for g in c["goals"]}
    for slug, (flag, seen) in done.items():
        if releases.read(sd, slug) is not None:                                                  # a release goal is a craft of its own
            continue
        assert flag and flag["by"] == "done", slug
        assert seen, f"{slug} would stand in the discard"
        assert slug in past_slugs, slug
    assert [e.get("text") for e in journals.read(sd, journals.PROJECT)] == first["before"]        # no journal line; the keeper fails on any call
    assert "idea_flagged" not in [r["event"] for r in event_log.read(Path(past.repo_root))]


def test_products_past_holds_goal_116_in_the_week_of_26_october_2026_with_decision_194_under_it(past, first):
    got = _read(past, "product")
    (chapter, goal) = next(((c, g) for c in got["chapters"] for g in c["goals"] if g["idea"].startswith("116-")), (None, None))
    assert goal is not None, "goal 116 is not in Product's past"
    assert chapter["kind"] == "week" and chapter["day"] == "2026-10-26"
    assert goal["decision"] == 194 and 194 in got["decisions"]


