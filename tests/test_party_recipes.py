"""Spec 99 A (docs/specs/99-a-goals-way.md §1, Tests → A; decisions §122, §137.1, §151, §158): one craft a party; the recipes of each kind by craft, no mixed recipe
offered and the ones of before still found; the squad and the size apart (a size sets the tiers and how a task goes, never the squad); a party the project has;
the craft of a party made before. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.realm import goal_team, idea_target, library, party_recipes, party_recipes_before, project_kind, roles

ALL = [(k, r) for k, rows in party_recipes.RECIPES.items() for r in rows]
GAME = ["game-design", "tech", "art", "release", "liveops", "marketing"]
APP = ["product", "design", "tech", "release", "run", "marketing"]


def test_every_kind_has_recipes_and_only_the_known_kinds():
    assert set(party_recipes.RECIPES) == set(project_kind.KINDS)
    assert all(rows for rows in party_recipes.RECIPES.values())


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


def test_ideation_team_and_the_mixed_recipes_are_not_offered_but_a_party_made_from_one_is_found_by_its_recipe():
    offered = {r["id"] for _k, r in ALL}
    for gone in ("ideation", "team", "game", "mobile-features", "web-pages", "mobile-architecture", "backend", "backend-data", "data-work", "wiki", "design-screens", "texts",
                 "engineering-code", "game-build", "mobile-liveops"):
        assert gone not in offered and party_recipes.get(gone) is not None, gone         # not offered, but its recipe is found
    assert party_recipes.get("ideation")["leader"] == "investor" and party_recipes.get("team") is party_recipes.TEAM
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


def test_the_ids_are_each_one_and_the_craft_ids_are_the_roles_party_races_keys():
    ids = [r["id"] for _k, r in ALL if r["id"] in party_recipes.CRAFTS]
    assert len(set(ids)) == len(party_recipes.CRAFTS) == 9
    assert set(party_recipes.CRAFTS) == set(roles.PARTY_RACES)


def test_the_art_party_is_the_librarys_preset_seats_and_the_roles_of_a_craft_are_most_needed_first():
    art = party_recipes.get("art")
    preset = next(p for p in library.PRESETS if p[0] == "art")
    assert (art["leader"], art["build"], art["check"]) == (preset[4], list(preset[5]), list(preset[6]))
    assert party_recipes.get("tech")["build"] == ["grunt", "tester"] and party_recipes.get("tech")["check"] == ["reviewer", "security-reviewer"]
    assert party_recipes.get("tech")["line"] == "How it is built: its parts, its tests and the build" and party_recipes.get("tech")["name"] == "Tech"
    assert party_recipes.get("marketing")["check"] == ["editor"] and {"copywriter", "seo", "aso", "community"} == set(party_recipes.get("marketing")["build"])
    assert party_recipes.get("release")["build"] == ["release-engineer", "release-notes", "aso"] and party_recipes.get("release")["check"] == ["release-checker"]


def test_the_squad_is_the_same_in_every_size_and_release_is_its_leader_alone():
    for _k, r in ALL:
        teams = [party_recipes.sized(r, s)["team"] for s in idea_target.SIZES]
        assert teams[0] == teams[1] == teams[2] == party_recipes.squad_of(r), r["id"]
    tech = party_recipes.get("tech")
    assert party_recipes.squad_of(tech) == ["grunt", "tester", "reviewer"]                      # the first two who do and the first who checks
    assert party_recipes.sized(tech, "lean")["team"] == ["grunt", "tester", "reviewer"]        # a size never changes the squad
    release = party_recipes.get("release")
    assert party_recipes.squad_of(release) == [] and [party_recipes.sized(release, s)["team"] for s in idea_target.SIZES] == [[], [], []]
    assert party_recipes.sized(tech, "standard")["basis"] == ["grunt", "reviewer"] and party_recipes.sized(tech, "lean")["basis"] == ["grunt"]


def test_a_size_that_is_none_is_refused_and_each_size_has_its_target():
    with pytest.raises(ValueError, match="lean, standard or full"):
        party_recipes.sized(party_recipes.get("tech"), "huge")
    assert party_recipes.TARGET == {"lean": "thrift", "standard": "balance", "full": "quality"} == idea_target.SIZE_TARGET


def test_each_size_gives_its_seats_their_tiers_lean_seasoned_standard_the_leader_veteran_full_the_leader_and_the_checker_veteran():
    tech = party_recipes.get("tech")
    lean, std, full = (party_recipes.sized(tech, s) for s in idea_target.SIZES)
    assert lean["tiers"] == {"architect": "warrior", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}
    assert std["tiers"] == {"architect": "elder", "grunt": "warrior"}
    assert full["tiers"] == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    for r in (party_recipes.get(i) for i in ("product", "design", "marketing", "run", "game-design")):
        got = [party_recipes.sized(r, s) for s in idea_target.SIZES]
        assert "laborer" not in got[2]["tiers"].values() and "laborer" not in got[0]["tiers"].values()


def test_releases_leader_alone_is_seasoned_at_every_size_the_cheaper_tier():
    release = party_recipes.get("release")
    assert [party_recipes.sized(release, s)["tiers"] for s in idea_target.SIZES] == [{"release-manager": "warrior"}] * 3
    with_notes = party_recipes.tiers_for("release-manager", ["release-notes"], "standard")      # a seat added: as any party's
    assert with_notes == {"release-manager": "elder", "release-notes": "warrior"}


def test_tiers_for_any_team_follows_the_sizes_and_a_party_made_before_keeps_its_team():
    team = ["grunt", "tester", "reviewer", "security-reviewer"]
    assert party_recipes.tiers_for("architect", team, "lean") == {s: "warrior" for s in ["architect", *team]}
    assert party_recipes.tiers_for("architect", team, "standard") == {"architect": "elder", "grunt": "warrior"}
    assert party_recipes.tiers_for("architect", team, "full") == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder", "security-reviewer": "elder"}
    assert party_recipes.tiers_for("taskmaster", ["grunt"], "standard") == {"grunt": "warrior"}          # the Taskmaster is no seat


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


def test_the_craft_of_a_party_is_its_recipes_else_its_leaders_and_none_for_the_taskmasters_ideations_and_teams():
    assert party_recipes.craft_of("tech", "architect") == "tech" and party_recipes.craft_of("run", "") == "run"
    assert party_recipes.craft_of("mobile-features", "product-manager") == "product" and party_recipes.craft_of("", "product-designer") == "design"
    assert party_recipes.craft_of("", "game-designer") == "game-design" and party_recipes.craft_of("", "art-director") == "art" and party_recipes.craft_of("", "analyst") == "run"
    assert party_recipes.craft_of("", "growth") == "marketing" and party_recipes.craft_of("", "release-manager") == "release"
    assert party_recipes.craft_of("", "taskmaster") == "" and party_recipes.craft_of("", "investor") == "" and party_recipes.craft_of("team", "product-manager") == ""
    assert party_recipes.is_release({"recipe": "release", "leader": ""}) and party_recipes.is_release({"recipe": "", "leader": "release-manager"})
    assert not party_recipes.is_release({"recipe": "tech", "leader": "architect"})


def test_a_running_party_proposes_the_recurring_goals_of_its_kind_and_a_games_liveops_those_of_a_game():
    assert party_recipes.routines_of("run", "web") == "web-liveops" and party_recipes.routines_of("run", "backend") == "backend-liveops"
    assert party_recipes.routines_of("liveops", "game") == "game-liveops" and party_recipes.routines_of("tech", "web") == "tech"
