"""Spec 102 C §3.2 (docs/specs/102-the-other-maps-and-picking-on-them.md, decisions §137.3): Release's map, dev against main. A card is a goal with a task landed in
dev whose commit main lacks (its element, its name, its newest such commit), ticked; what is out since the last version; the gate's counts as `ideas.gate` has them; its text.
Real git repositories (tests/test_commit_goal.py's: main at the start, dev ahead), no model."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_maps import MapsMixin, maps_commands
from orkboard.realm import goal_team, ideas, idea_element, library, release_map
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


def goal(pages: Path, repo: Path, title: str, element: str = "") -> str:
    slug = ideas.add_idea(pages, title, "general", state(repo))
    if element:
        ideas.save_state(state(repo), slug, element=element)
    return slug


def release_party(pages: Path) -> str:
    slug, _new = ideas.save_goal(pages, None, "Release", "About release.", craft="product")
    goal_team.set_team(pages, slug, [], leader=library.RELEASE_MANAGER)
    return slug


# -- read ---------------------------------------------------------------------------------------------------------------------------

def test_the_goals_in_dev_and_not_in_main_newest_landing_first_ticked_with_their_element_title_and_commit(repo, pages):
    one, two = goal(pages, repo, "Dark mode", "ice"), goal(pages, repo, "Faster pages")
    a, _ = land(repo, one, "k1", {"x.css": "x\n"})
    b, _ = land(repo, two, "k1", {"y.css": "y\n"})
    c, _ = land(repo, one, "k2", {"z.css": "z\n"})
    commit(repo, "mine.txt", "my own\n")                                             # the person's own commit: no goal's
    got = release_map.read(state(repo), repo, pages)
    ats = [g.pop("at") for g in got["goals"]]
    assert all(isinstance(t, int) and t > 0 for t in ats)
    assert got == {"into": "dev", "main": "main", "same": False, "commits": 4, "files": 4, "since": None,
                   "goals": [{"idea": one, "title": "Dark mode", "element": "ice", "hue": "ice", "commit": c, "ticked": True},
                             {"idea": two, "title": "Faster pages", "element": "", "hue": "", "commit": b, "ticked": True}]}
    assert a != c


# -- the text -----------------------------------------------------------------------------------------------------------------------

def test_the_text_names_the_goals_waiting_and_the_last_version(repo, pages):
    one = goal(pages, repo, "Dark mode")
    sha, _ = land(repo, one, "k1", {"x.css": "x\n"})
    text = release_map.text(state(repo), repo, "", pages)
    assert text == release_map.text(state(repo), repo, "", pages) == release_map.text(state(repo), repo, "abc", pages)
    assert text == "\n".join(["The map of Release: dev against main", "", "Waiting for main (1 goal; 1 commit, 1 file changed):",
                              f'- goal {one} "Dark mode" (commit {sha[:7]})', "", "No version is out yet."])
    (repo / "CHANGELOG.md").write_text("## [1.3] - 2026-10-20\n- c\n", encoding="utf-8")
    assert release_map.text(state(repo), repo, "", pages).endswith("\n\nLast version out: 1.3, 2026-10-20.")


# -- ideas.release_map --------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    git(fake_repo, "branch", "-M", "main")
    git(fake_repo, "branch", "dev")
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas, MapsMixin):                                       # wired by the lead: the host's bases and its table
        h.ideas.__class__ = type("IdeasWithMaps", (MapsMixin, type(h.ideas)), {})
        h.commands.update(maps_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_command_answers_what_the_gate_would_merge(host, fake_repo):
    root = host.ideas.root()
    slug = ideas.add_idea(root, "Dark mode", "general", host.ideas.state_dir)
    git(fake_repo, "checkout", "-q", "dev")
    sha, _ = land(fake_repo, slug, "k1", {"x.css": "x\n"})
    got = host.command("ideas.release_map", {})
    gate = host.command("ideas.gate", {})
    assert (got["into"], got["main"], got["commits"], got["files"]) == (gate["into"], gate["main"], gate["commits"], gate["files"])
    assert got["goals"] == [{"idea": slug, "title": "Dark mode", "element": idea_element.of(host.ideas.state_dir, slug), "hue": idea_element.hue_of(host.ideas.state_dir, slug), "commit": sha, "ticked": True, "at": got["goals"][0]["at"]}]
    assert [g["slug"] for g in gate["ideas"]] == [slug]

