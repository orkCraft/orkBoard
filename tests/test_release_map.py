"""Spec 102 C §3.2 (docs/specs/102-the-other-maps-and-picking-on-them.md, decisions §137.3): Release's map, dev against main. A card is a goal with a task landed in
dev whose commit main lacks (its element, its name, its newest such commit), ticked; what is out since the last version; the gate's counts as `ideas.gate` has them; its text.
Real git repositories (tests/test_commit_goal.py's: main at the start, dev ahead), no model."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_maps import MapsMixin, maps_commands
from orkboard.realm import goal_team, ideas, idea_element, library, map_text, release_map, releases
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
    assert got == {"into": "dev", "main": "main", "same": False, "commits": 4, "files": 4, "since": None,
                   "goals": [{"idea": one, "title": "Dark mode", "element": "ice", "commit": c, "ticked": True},
                             {"idea": two, "title": "Faster pages", "element": "", "commit": b, "ticked": True}]}
    assert a != c


def test_a_goal_all_of_whose_commits_main_has_waits_for_nothing_and_a_dropped_goal_is_not_listed(repo, pages):
    one, two = goal(pages, repo, "Dark mode"), goal(pages, repo, "Faster pages")
    land(repo, one, "k1", {"x.css": "x\n"})
    git(repo, "branch", "-f", "main", "dev")                                          # main caught up: one's commit is in it
    land(repo, two, "k1", {"y.css": "y\n"})
    assert [g["idea"] for g in release_map.read(state(repo), repo, pages)["goals"]] == [two]
    (pages / ideas.IDEAS / f"{two}.md").unlink()                                          # dropped from the Board
    got = release_map.read(state(repo), repo, pages)
    assert got["goals"] == [] and got["commits"] == 1
    assert [g["idea"] for g in release_map.read(state(repo), repo)["goals"]] == [two]    # no pages: every plan's goal, its slug for a title
    assert release_map.read(state(repo), repo)["goals"][0]["title"] == two


def test_main_caught_up_waits_for_nothing_and_dev_as_main_is_no_gate(repo, pages):
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    git(repo, "branch", "-f", "main", "dev")
    got = release_map.read(state(repo), repo, pages)
    assert (got["same"], got["commits"], got["goals"]) == (False, 0, [])
    only = release_map.read(state(repo), repo, pages, "main")
    assert (only["same"], only["goals"]) == (True, [])


def test_since_is_the_release_partys_last_version_that_is_out(repo, pages):
    party = release_party(pages)
    assert release_map.read(state(repo), repo, pages)["since"] is None
    for version, out, at in (("1.2", "2026-10-10T09:00:00", "2026-10-09T09:00:00"), ("1.3", "2026-10-20T09:00:00", "2026-10-19T09:00:00"), ("1.4", "", "2026-10-25T09:00:00")):
        slug = ideas.add_idea(pages, f"Release {version}", party, state(repo))
        ideas.save_state(state(repo), slug, type="release")
        ideas._write_json(releases._path(state(repo), slug), {"version": version, "goals": [], "out": out, "at": at})
    assert release_map.read(state(repo), repo, pages)["since"] == {"version": "1.3", "out": "2026-10-20T09:00:00"}
    assert release_map.read(state(repo), repo)["since"] is None                         # no pages, no party to ask


# -- the text -----------------------------------------------------------------------------------------------------------------------

def test_the_text_names_the_goals_waiting_and_the_last_version(repo, pages):
    one = goal(pages, repo, "Dark mode")
    sha, _ = land(repo, one, "k1", {"x.css": "x\n"})
    text = release_map.text(state(repo), repo, "", pages)
    assert text == release_map.text(state(repo), repo, "", pages) == release_map.text(state(repo), repo, "abc", pages)
    assert text == "\n".join(["The map of Release: dev against main", "", "Waiting for main (1 goal; 1 commit, 1 file changed):",
                              f'- goal {one} "Dark mode" (commit {sha[:7]})', "", "No version is out yet."])
    party = release_party(pages)
    slug = ideas.add_idea(pages, "Release 1.3", party, state(repo))
    ideas._write_json(releases._path(state(repo), slug), {"version": "1.3", "goals": [], "out": "2026-10-20T09:00:00", "at": "2026-10-19T09:00:00"})
    assert release_map.text(state(repo), repo, "", pages).endswith("\n\nLast version out: 1.3, 2026-10-20.")


def test_the_text_for_no_gate_nothing_waiting_the_persons_own_commits_and_no_dev(repo, pages):
    assert release_map.text(state(repo), repo, "", pages).splitlines()[2] == "Nothing in dev waits for main."
    commit(repo, "mine.txt", "my own\n")
    lines = release_map.text(state(repo), repo, "", pages).splitlines()
    assert lines[2] == "Waiting for main (0 goals; 1 commit, 1 file changed):" and lines[3] == "- the commits are the person's own, no goal's."
    assert release_map.text(state(repo), repo, "", pages, "main").splitlines()[2] == "main and main are one branch here: there is no gate, nothing waits for main."
    assert release_map.text(state(repo), repo, "", pages, "no-such") is None


def test_the_text_is_bounded_and_says_how_many_goals_it_left_out(repo, pages):
    for n in range(50):
        land(repo, goal(pages, repo, f"A goal with a rather long title number {n:03d} to fill the text"), "k1", {f"f{n}.txt": "x\n"})
    text = release_map.text(state(repo), repo, "", pages)
    assert len(text) <= map_text.LIMIT and "\n- and " in text and " more goals\n" in text


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
    assert got["goals"] == [{"idea": slug, "title": "Dark mode", "element": idea_element.of(host.ideas.state_dir, slug), "commit": sha, "ticked": True}]
    assert [g["slug"] for g in gate["ideas"]] == [slug]
