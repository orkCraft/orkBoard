"""Spec 157 F (docs/specs/157-the-inventory-a-merchants-stall.md; decisions §267.3-4): the goals that lay the tables. No model; nothing starts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_board_35 import host, model, runner  # noqa: F401  (fixtures)

from orkboard.realm import goal_phase, goal_team, ideas, lay_tables, party_recipes


def _party(root: Path, craft: str, title: str) -> str:
    slug = ideas.add_track(root, title)
    recipe = party_recipes.CRAFTS[craft]
    goal_team.set_recipe(root, slug, craft)
    goal_team.set_team(root, slug, party_recipes.squad_of(recipe), leader=recipe["leader"])
    return slug


@pytest.fixture
def board(tmp_path):
    root, state = tmp_path / "wiki", tmp_path / "state"
    state.mkdir()
    tech, design = _party(root, "tech", "Tech"), _party(root, "design", "Design")
    return root, state, tech, design


def _goal(root, slug):
    return next(g for g in ideas.ideas(root) if g["slug"] == slug)


def test_lay_first_lays_the_goal_once_with_its_route_and_gist_and_starts_nothing(board):
    root, state, tech, design = board
    goal_team.set_hero(root, tech, "sh-xp")
    slug = lay_tables.lay_first(root, state)
    assert slug
    g = _goal(root, slug)
    assert g["title"] == "Lay the tables" and g["priority"] == "low"
    st = ideas.state(state, slug)
    assert [r["party"] for r in st["route"]] == [tech] and st["state"] == "raw"      # Design's hero is its craft's default: its map is read from the code
    assert goal_phase.of(st["state"]) == "new"
    gist = ideas.idea_page(root, slug).section("Gist")
    assert "Spike Shaman (Extreme programming), its places: Red, Green, Refactor, Released small." in gist
    assert "Pixel-Perfect Dryad" not in gist
    assert "pages/tables/<party>.md" in gist and "nothing starts by itself" in gist and "no number it did not read" in gist
    assert json.loads((state / "project.json").read_text())["tables_laid"] is True
    assert lay_tables.lay_first(root, state) == ""
    assert len([x for x in ideas.ideas(root) if x["title"] == "Lay the tables"]) == 1


def test_every_hero_its_crafts_default_lays_nothing_and_is_not_asked_again(board):
    root, state, tech, _design = board
    assert lay_tables.lay_first(root, state) == ""
    assert json.loads((state / "project.json").read_text())["tables_laid"] is True
    goal_team.set_hero(root, tech, "sh-xp")
    assert lay_tables.lay_first(root, state) == ""                   # a hero taken later lays its own goal
    assert lay_tables.lay_party(root, state, tech)
    assert not [g for g in ideas.ideas(root) if g["title"] == "Lay the tables"]


def test_lay_party_lays_its_goal_not_twice_while_one_waits_and_again_once_it_is_done(board):
    root, state, tech, _design = board
    goal_team.set_hero(root, tech, "sh-xp")
    slug = lay_tables.lay_party(root, state, tech)
    g = _goal(root, slug)
    assert g["title"] == "Lay Tech's table" and g["priority"] == "low"
    st = ideas.state(state, slug)
    assert [r["party"] for r in st["route"]] == [tech] and st["state"] == "raw"
    assert "Spike Shaman" in ideas.idea_page(root, slug).section("Gist")
    assert lay_tables.lay_party(root, state, tech) == ""
    ideas.save_state(state, slug, state="done")
    assert lay_tables.lay_party(root, state, tech) not in ("", slug)
    assert lay_tables.lay_party(root, state, "no-such-party") == ""

