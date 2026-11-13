"""Spec 99 A (docs/specs/99-a-goals-way.md §1, Tests → A; decisions §122, §137.1, §151, §158): one craft a party; the recipes of each kind by craft, no mixed recipe
offered and the ones of before still found; the squad and the size apart (a size sets the tiers and how a task goes, never the squad); a party the project has;
the craft of a party made before. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.realm import goal_team, idea_target, library, party_recipes, party_recipes_before, project_kind

ALL = [(k, r) for k, rows in party_recipes.RECIPES.items() for r in rows]
GAME = ["game-design", "tech", "art", "release", "liveops", "marketing"]
APP = ["product", "design", "tech", "release", "run", "marketing"]


def test_a_game_has_game_design_tech_art_release_liveops_and_marketing_and_every_other_kind_product_design_tech_release_run_and_marketing():
    got = {k: [r["id"] for r in party_recipes.for_kind(k)] for k in project_kind.KINDS}
    assert got == {k: GAME if k == "game" else APP for k in project_kind.KINDS}
    assert [r["id"] for r in party_recipes.for_kind("nonsense")] == APP                      # an unknown kind: code's
    names = {r["id"]: r["name"] for _k, r in ALL}
    assert names == {"product": "Product", "design": "Design", "tech": "Tech", "release": "Release", "run": "Run", "marketing": "Marketing",
                     "game-design": "Game design", "art": "Art", "liveops": "LiveOps"}
    lead = {r["id"]: r["leader"] for _k, r in ALL}
    assert lead == {"product": "product-manager", "design": "product-designer", "tech": "architect", "release": "release-manager", "run": "analyst",
                    "marketing": "growth", "game-design": "game-designer", "art": "art-director", "liveops": "analyst"}


def test_ideation_and_the_mixed_recipes_are_not_offered_but_a_party_made_from_one_is_found_by_its_recipe():
    offered = {r["id"] for _k, r in ALL}
    for gone in ("ideation", "game", "mobile-features", "web-pages", "mobile-architecture", "backend", "backend-data", "data-work", "wiki", "design-screens", "texts",
                 "engineering-code", "game-build", "mobile-liveops"):
        assert gone not in offered and party_recipes.get(gone) is not None, gone         # not offered, but its recipe is found
    assert party_recipes.get("ideation")["leader"] == "investor"
    assert party_recipes.get("mobile-features")["leader"] == "product-manager" and party_recipes.get("game-build")["leader"] == "game-designer"
    assert party_recipes.get("nope") is None and party_recipes.get("tech") is party_recipes.CRAFTS["tech"] and party_recipes.get("release")["leader"] == "release-manager"
    assert party_recipes_before.BEFORE["mobile"][0]["id"] == "mobile-features"
    assert party_recipes.kind_of("mobile-features") == "mobile" and party_recipes.kind_of("game-liveops") == "game"
    assert party_recipes.kind_of("release", "web") == "web" and party_recipes.kind_of("release", "game") == "game" and party_recipes.kind_of("nope") == ""
    assert party_recipes.kind_of("art", "web") == "game" and party_recipes.kind_of("product", "game") == "empty"        # the first kind that has it, else the project's own


@pytest.mark.parametrize("kind,recipe", ALL, ids=[f"{k}:{r['id']}" for k, r in ALL])
def test_a_recipe_names_only_the_librarys_agents_and_its_squad_fits_the_seats_in_every_size(kind, recipe):
    for slug in [recipe["leader"], *recipe["build"], *recipe["check"]]:
        assert library.get(slug) is not None, slug
    assert library.get(recipe["leader"]).band == "lead"
    assert all(library.get(s).band == "build" for s in recipe["build"]) and all(library.get(s).band == "check" for s in recipe["check"])
    assert recipe["name"] and recipe["line"] and recipe["because"] and recipe["craft"] == recipe["id"]
    assert set(recipe["squad"]) <= {*recipe["build"], *recipe["check"]} and party_recipes.squad_of(recipe) == recipe["squad"]
    for size in idea_target.SIZES:
        got = party_recipes.sized(recipe, size)
        assert got["leader"] == recipe["leader"] and got["size"] == size
        assert goal_team.seats(got["team"], got["leader"]) == "", (recipe["id"], size)
        assert len(got["team"]) + 1 <= goal_team.SEATS


def test_each_size_gives_its_seats_their_tiers_lean_seasoned_standard_the_leader_veteran_full_the_leader_and_the_checker_veteran():
    tech = party_recipes.get("tech")
    lean, std, full = (party_recipes.sized(tech, s) for s in idea_target.SIZES)
    assert lean["tiers"] == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}          # the leader's tier is its own at every size (spec 152 A.1)
    assert std["tiers"] == {"architect": "elder", "grunt": "warrior"}
    assert full["tiers"] == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    for r in (party_recipes.get(i) for i in ("product", "design", "marketing", "run", "game-design")):
        got = [party_recipes.sized(r, s) for s in idea_target.SIZES]
        assert "laborer" not in got[2]["tiers"].values() and "laborer" not in got[0]["tiers"].values()


def test_a_party_the_project_has_is_of_the_recipe_kept_on_its_page_else_the_same_leader_with_the_squad_inside_its_team():
    tech = party_recipes.get("tech")
    mine = {"leader": "architect", "team": [*party_recipes.squad_of(tech), "security-reviewer"], "recipe": "tech"}
    assert party_recipes.has(tech, [mine]) and party_recipes.has(tech, [{"leader": "architect", "team": [], "recipe": "tech"}])
    made_before = {"leader": "architect", "team": ["grunt", "tester", "reviewer"], "recipe": "mobile-architecture"}
    assert party_recipes.has(tech, [made_before]) and party_recipes.has(tech, [{**made_before, "recipe": ""}])        # a party of before is its leader's craft
    assert not party_recipes.has(tech, [{"leader": "architect", "team": ["grunt"], "recipe": ""}]) and not party_recipes.has(tech, [])
    assert not party_recipes.has(tech, [{"leader": "architect", "team": ["grunt", "tester", "reviewer"], "recipe": "run"}])       # another craft's party
    assert not party_recipes.has(party_recipes.get("product"), [made_before])
    release = party_recipes.get("release")
    assert party_recipes.has(release, [{"leader": "release-manager", "team": ["release-engineer", "release-checker"], "recipe": "release"}])
    assert party_recipes.has(release, [{"leader": "release-manager", "team": [], "recipe": ""}]) and not party_recipes.has(release, [{"leader": "architect", "team": []}])


def test_a_running_party_proposes_the_recurring_goals_of_its_kind_and_a_games_liveops_those_of_a_game():
    assert party_recipes.routines_of("run", "web") == "web-liveops" and party_recipes.routines_of("run", "backend") == "backend-liveops"
    assert party_recipes.routines_of("liveops", "game") == "game-liveops" and party_recipes.routines_of("tech", "web") == "tech"
