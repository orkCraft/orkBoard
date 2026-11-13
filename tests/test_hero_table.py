"""Spec 157 A.4: a hero's kept table, `<wiki>/pages/tables/<party>.md` (realm/hero_table.py)."""
from __future__ import annotations

import pytest

from orkboard.realm import goal_team, hero_table, heroes, ideas


@pytest.fixture
def party(tmp_path):
    root = tmp_path / "wiki"
    slug = ideas.add_track(root, "Engineering")
    goal_team.set_recipe(root, slug, "tech")
    goal_team.set_hero(root, slug, "sh-xp")
    return root, slug


def test_no_file_gives_every_place_empty(party):
    root, slug = party
    got = hero_table.read(root, slug)
    xp = heroes.get("sh-xp")
    assert got["hero"] == "sh-xp" and got["laid"] == "" and got["stale"] is False
    assert got["places"] == [{"name": n, "ask": a, "cards": []} for n, a in xp.places] and [p["name"] for p in got["places"]] == ["Red", "Green", "Refactor", "Released small"]


def test_a_table_round_trips_with_goal_and_state(party):
    root, slug = party
    hero_table.write(root, slug, "sh-xp", {"Red": [{"title": "Login test", "line": "fails on an empty name", "goal": "fix-login", "state": "bad"}, {"title": "Plain", "line": ""}],
                                          "Green": [{"title": "Cart", "line": "passes", "state": "good"}]})
    text = (root / "pages" / "tables" / f"{slug}.md").read_text(encoding="utf-8")
    assert text.startswith("---\nowner: board\nkind: table\nparty: " + slug + "\nhero: sh-xp\nlaid: ") and "schema: 1" in text
    assert "## Red\n- Login test — fails on an empty name {goal: fix-login, state: bad}\n- Plain\n" in text
    got = hero_table.read(root, slug)
    assert got["laid"] and got["stale"] is False
    by = {p["name"]: p["cards"] for p in got["places"]}
    assert by["Red"] == [{"title": "Login test", "line": "fails on an empty name", "goal": "fix-login", "state": "bad"}, {"title": "Plain", "line": "", "goal": "", "state": ""}]
    assert by["Green"] == [{"title": "Cart", "line": "passes", "goal": "", "state": "good"}] and by["Refactor"] == [] and by["Released small"] == []


def test_a_table_of_another_hero_is_stale(party):
    root, slug = party
    hero_table.write(root, slug, "sh-xp", {"Red": [{"title": "A", "line": "b"}]})
    goal_team.set_hero(root, slug, "sh-c4")
    got = hero_table.read(root, slug)
    assert got["stale"] is True and got["hero"] == "sh-c4" and got["places"] == []
    assert all(p["cards"] == [] for p in got["places"])                      # none of the old places is the new hero's here


def test_a_default_hero_has_no_places_and_a_bad_name_is_refused(party):
    root, slug = party
    hero_table.write(root, slug, "sh-c4", {"Red": [{"title": "x"}]})
    assert "## " not in (root / "pages" / "tables" / f"{slug}.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        hero_table.write(root, slug, "nowhere", {})
    with pytest.raises(ValueError):
        hero_table.write(root, "../up", "sh-xp", {})
    assert hero_table.read(root, "../up")["laid"] == ""
