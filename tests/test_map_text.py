"""Spec 99 B §2.1 (docs/specs/99-a-goals-way.md, decisions §156.1–§156.2): a leader's map as text, Tech's *System*. Read by code from dev's
snapshot with no model: the containers whole, their links named, the parts a line each with Uses and Used by; bounded to about 3,000
characters, the parts keeping only their names past it; the same bytes for the same snapshot and for two heads of dev that changed no part;
*Changed since your last call* with each change's goal (and *by you*); the parts in detail, bounded; a project with no dev has no map. Real git
repositories (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.realm import ideas, map_text
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)
from tests.test_system_overview import GAME, write


@pytest.fixture
def game(repo: Path) -> Path:
    """The owner's party game (tests/test_system_overview.py's) on dev."""
    write(repo, GAME)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the game")
    return repo


def body(text: str) -> str:
    """The map's text without its first line (the head's short commit)."""
    return text.split("\n", 1)[1]


def many(repo: Path, folders: int) -> None:
    """A Python project of `folders` parts, each importing the next."""
    for n in range(folders):
        nxt = f"from pkg.part{n + 1:04d} import mod\n" if n + 1 < folders else ""
        (repo / "pkg" / f"part{n:04d}").mkdir(parents=True, exist_ok=True)
        (repo / "pkg" / f"part{n:04d}" / "mod.py").write_text(nxt + "VALUE = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "many parts")


# -- §2.1 the text ---------------------------------------------------------------------------------------------------------------------

def test_the_map_names_the_containers_whole_their_links_and_the_shared_part_then_the_parts_a_line_each(game):
    text = map_text.system(state(game), game)
    assert text.startswith(f"The map of System at dev {git(game, 'rev-parse', 'dev')[:7]}\n")
    assert "- Root (.): stack concurrently; ways in: script dev" in text
    assert "- client (client): stack React, socket.io-client, Vite and 1 others; ways in: page client/index.html, script dev, script build" in text
    assert "- server (server): stack Express, Socket.IO and 1 others; ways in: main server/src/index.ts, script dev, script start, listen server/src/index.ts" in text
    assert "- client to server: 3 routes (GET /api/health, POST /api/rooms, GET /api/rooms/:code) · 3 events (answer, join, state)" in text
    assert "- config: used by client, server" in text
    assert "- client/src/views: layer 2, face; Uses: net, config; Used by: client/src" in text      # a part by its name, a name two share by its path
    assert "- server/src/routes: layer 2, doors; Uses: server/src, db; Used by: server/src" in text
    assert "|" not in text and map_text.NAMED_ONLY not in text and len(text) <= map_text.LIMIT
    assert text.index("Containers:") < text.index("Links:") < text.index("Shared by") < text.index("Parts (")


def test_past_the_bound_the_parts_keep_only_their_names_and_the_text_says_so(repo):
    many(repo, 60)
    text = map_text.system(state(repo), repo)
    assert len(text) <= map_text.LIMIT and map_text.NAMED_ONLY in text
    assert "- pkg/part0000\n" in text and "Uses:" not in text.split("Parts (", 1)[1]
    assert map_text.system(state(repo), repo) == text


def test_a_project_with_no_dev_has_no_map_and_another_party_is_given_none(tmp_path):
    r = tmp_path / "plain"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    commit(r, "a.py", "X = 1\n")
    assert map_text.system(r / ".orkcraft", r) is None and map_text.detail(r / ".orkcraft", r, ["."]) == ""


def test_each_craft_has_its_map_as_text(game):
    from orkboard.realm import art_map, loop, release_map, way_map
    assert map_text.of("tech", state(game), game) == map_text.system(state(game), game)
    assert map_text.of("game-design", state(game), game) == loop.text(state(game), game)                  # spec 102 §4: each craft's own
    assert map_text.of("art", state(game), game) == art_map.text(state(game), game)
    assert map_text.of("release", state(game), game) == release_map.text(state(game), game)
    assert map_text.of("marketing", state(game), game) == way_map.text(state(game), game)
    from orkboard.realm import screen_map
    from orkboard.realm import opportunity_tree
    assert map_text.of("design", state(game), game) == screen_map.text(state(game), game)
    assert map_text.of("product", state(game), game) == opportunity_tree.text(state(game), game)          # decisions §172
    assert map_text.of("nobody", state(game), game) is None


# -- §2.1 changed since the party's last call ------------------------------------------------------------------------------------------

def test_changed_since_the_last_call_names_each_change_with_its_goal_and_the_persons_own(game):
    pages = game / "board"
    (pages / ideas.IDEAS).mkdir(parents=True)
    (pages / ideas.IDEAS / "dark-mode.md").write_text("---\nowner: board\n---\n# Dark mode for the lobby\n")
    seen = git(game, "rev-parse", "dev")
    map_text.system(state(game), game)
    land(game, "dark-mode", "k1", {"client/src/theme/dark.ts": "export const dark = true;\n"})
    commit(game, "server/src/db/store.ts", "export const save = (x) => [x];\n", "my own change")
    text = map_text.system(state(game), game, seen, pages)
    assert text.startswith(map_text.system(state(game), game) + "\n\nChanged since your last call:\n")
    assert '- new part client/src/theme (goal dark-mode "Dark mode for the lobby")' in text
    assert "- changed part server/src/db (by you)" in text
    assert text.index("new part") < text.index("changed part") and len(text) < map_text.LIMIT + map_text.CHANGED


# -- §2.1 the parts in detail ------------------------------------------------------------------------------------------------------------

def test_detail_gives_the_named_parts_in_full_a_file_naming_its_part_and_an_unknown_path_none(game):
    got = map_text.detail(state(game), game, ["server/src/routes", "client/src/views/TvView.tsx", "nowhere", "server/src/routes"])
    assert got.splitlines()[0] == f"Parts in detail at dev {git(game, 'rev-parse', 'dev')[:7]}:"
    assert "- server/src/routes (1 file)\n  Files: rooms.ts\n  Uses: server/src, server/src/db\n  Used by: server/src" in got
    assert "- client/src/views (3 files)\n  Files: JudgeView.tsx, PlayerView.tsx, TvView.tsx" in got
    assert got.count("- server/src/routes") == 1 and "nowhere" not in got
    assert map_text.detail(state(game), game, ["nowhere"]) == "" and map_text.detail(state(game), game, []) == ""


# -- §7.4 who decided a change ------------------------------------------------------------------------------------------------------------

def test_a_change_says_who_decided_it_from_the_goals_sections_the_leader_the_person_by_a_fork_or_a_member_alone(game):
    pages = game / "board"
    (pages / ideas.IDEAS).mkdir(parents=True)
    tech = "### Why\nx\n\n### Done when\n- y\n\n### Will be\n- new client/src/theme — the dark theme"
    (pages / ideas.IDEAS / "dark-mode.md").write_text(f"---\nowner: board\n---\n# Dark mode\n\n## Gist\ng\n\n## Tech\n{tech}\n")
    (pages / ideas.IDEAS / "waves.md").write_text(f"---\nowner: board\n---\n# Waves\n\n## Decisions\n- 2026-10-28: Fork — waves: six [sections: Tech]\n\n## Tech\n{tech.replace('client/src/theme', 'server/src/db')}\n")
    (pages / ideas.IDEAS / "old.md").write_text("---\nowner: board\n---\n# Old\n\n## Gist\ng\n\n## Why\nw\n")
    seen = git(game, "rev-parse", "dev")
    map_text.system(state(game), game)
    land(game, "dark-mode", "k1", {"client/src/theme/dark.ts": "export const dark = true;\n"})
    land(game, "waves", "k1", {"server/src/db/store.ts": "export const save = (x) => [x];\n"})
    land(game, "old", "k1", {"client/src/net/api.ts": "export const x = 1;\n"})
    land(game, "dark-mode", "k2", {"client/src/views/extra.ts": "export const e = 1;\n"})          # a part nobody promised: a member alone
    text = map_text.system(state(game), game, seen, pages)
    assert '- new part client/src/theme (goal dark-mode "Dark mode", decided by the leader)' in text
    assert '- changed part server/src/db (goal waves "Waves", decided by the person)' in text
    assert '- changed part client/src/net (goal old "Old")' in text                                   # a page of before has no Will be: nothing said
    assert '(goal dark-mode "Dark mode", decided by a member alone)' in text
