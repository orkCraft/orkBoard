"""Spec 157 A (docs/specs/157-the-inventory-a-merchants-stall.md): the heroes' catalog, a party's hero, and the lens following the hero."""
from __future__ import annotations

import re

import pytest

from orkboard.realm import goal_team, heroes, ideas, lens_rubrics, lexicon, map_parts, party_recipes


@pytest.fixture
def root(tmp_path):
    return tmp_path / "wiki"


def _party(root, craft):
    slug = ideas.add_track(root, f"{craft} party")
    goal_team.set_recipe(root, slug, craft)
    return slug


def test_a_default_heros_frame_is_its_crafts_rubric_read_at_call_time(monkeypatch):
    for h in (x for x in heroes.HEROES.values() if x.default):
        r = lens_rubrics.RUBRICS[h.craft]
        assert (h.framework, h.short, h.aspects) == (r["framework"], r["short"], r["aspects"]) and h.aspects is r["aspects"]
    monkeypatch.setitem(lens_rubrics.RUBRICS, "tech", {**lens_rubrics.RUBRICS["tech"], "short": "changed"})
    assert heroes.get("sh-c4").short == "changed"


def test_a_party_has_its_crafts_default_hero_until_one_is_taken(root):
    slug = _party(root, "tech")
    assert ideas.track_page(root, slug).get("hero") == "" and goal_team.hero_of(root, slug).id == "sh-c4"
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["hero"] == ""
    goal_team.set_hero(root, slug, "sh-xp")
    assert goal_team.hero_of(root, slug).id == "sh-xp" and ideas.track_page(root, slug).get("hero") == "sh-xp"
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["hero"] == "sh-xp"
    goal_team.set_hero(root, slug, "sh-c4")                                 # the craft's default writes the key away
    assert "hero" not in [k for k, _v in ideas.track_page(root, slug).meta] and goal_team.hero_of(root, slug).id == "sh-c4"


def test_set_hero_refuses_a_hero_of_another_craft_an_unknown_one_and_releases(root):
    tech, release = _party(root, "tech"), _party(root, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "dry-sprint")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "nowhere")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, release, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, "no-such-party", "sh-xp")
    assert goal_team.hero_of(root, tech).id == "sh-c4" and goal_team.hero_of(root, release).id == "release"


def test_every_hero_a_kind_offers_has_its_head_in_orkuis_copy_spec_164_h():
    from orkboard.design import orkui
    from orkboard.realm import roles
    wanted = {h.id for h in heroes.HEROES.values() if not h.default} | {"uni-mda", "dry-sprite"}
    missing = sorted(i for i in wanted if not (roles.RACE_FILES / f"hero-{i}-elder.png").is_file())
    assert not missing, f"no hero-<id>-elder.png in orkUI's copy for {missing}"
    stamped = orkui.stamp()["files"]
    assert all(f"races/hero-{i}-elder.png" in stamped for i in wanted)
    assert "signs/pick.svg" in stamped and not orkui.problems()

