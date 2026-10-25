"""Spec 75 A (docs/specs/75-parties-fitted-to-the-project.md §2, Tests → A): the recipes name only the library's agents and fit their leaders' seats;
the three sizes of a recipe (lean: no team; standard: two builders and a checker; full: within its seats; Ideation and Release whole in each);
the recipes of each kind as the spec writes them; a recipe's party the project has. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.realm import goal_team, idea_target, library, party_recipes, project_kind

ALL = [(k, r) for k, rows in party_recipes.RECIPES.items() for r in rows]


def test_every_kind_has_recipes_and_only_the_known_kinds():
    assert set(party_recipes.RECIPES) == set(project_kind.KINDS)
    assert all(rows for rows in party_recipes.RECIPES.values())


@pytest.mark.parametrize("kind,recipe", ALL, ids=[f"{k}:{r['id']}" for k, r in ALL])
def test_a_recipe_names_only_the_librarys_agents_and_fits_its_leaders_seats_in_every_size(kind, recipe):
    for slug in [recipe["leader"], *recipe["build"], *recipe["check"]]:
        assert library.get(slug) is not None, slug
    assert library.get(recipe["leader"]).band == "lead"
    assert all(library.get(s).band == "build" for s in recipe["build"]) and all(library.get(s).band == "check" for s in recipe["check"])
    assert recipe["name"] and recipe["line"] and recipe["because"]
    for size in idea_target.SIZES:
        got = party_recipes.sized(recipe, size)
        assert got["leader"] == recipe["leader"] and got["size"] == size
        assert goal_team.seats(got["team"], got["leader"]) == "", (recipe["id"], size)
        assert len(got["team"]) <= goal_team.SEATS
        assert set(got["team"]) <= {*recipe["build"], *recipe["check"]}


def test_the_ids_are_each_one_and_the_presets_are_built_on_their_seats():
    ids = [r["id"] for _k, r in ALL if r["id"] not in ("ideation", "release", "game")]
    assert len(ids) == len(set(ids))
    for pid in ("ideation", "release", "game"):
        preset = next(p for p in library.PRESETS if p[0] == pid)
        for _k, r in ALL:
            if r["id"] == pid:
                assert (r["leader"], r["build"], r["check"]) == (preset[4], list(preset[5]), list(preset[6]))


def test_the_recipes_of_each_kind_are_the_specs():
    ids = {k: [r["id"] for r in party_recipes.for_kind(k, {"sql": 1})] for k in project_kind.KINDS}
    assert ids == {"empty": ["ideation"], "mobile": ["mobile-features", "mobile-architecture", "release"], "web": ["web-pages", "release"],
                   "backend": ["backend", "backend-data"], "game": ["game", "release"], "data": ["data-work"], "wiki": ["wiki", "ideation"],
                   "design": ["design-screens", "ideation"], "texts": ["texts", "ideation"], "code": ["engineering-code"]}
    lead = {r["id"]: r["leader"] for _k, r in ALL}
    assert lead["mobile-features"] == "product-manager" and lead["mobile-architecture"] == "architect" and lead["web-pages"] == "product-designer"
    assert lead["data-work"] == "analyst" and lead["wiki"] == "product-manager" and lead["design-screens"] == "product-designer" and lead["texts"] == "growth"
    feat = party_recipes.get("mobile-features")
    assert feat["name"] == "Mobile app: features" and {"grunt", "artist", "aso", "ui-kit"} <= set(feat["build"]) and feat["check"] == ["reviewer", "accessibility-reviewer"]
    assert party_recipes.get("mobile-architecture")["check"] == ["reviewer", "security-reviewer"]
    assert party_recipes.get("data-work")["build"] == ["data-engineer", "sql", "experimenter"] and party_recipes.get("data-work")["check"] == ["data-reviewer"]
    assert party_recipes.get("engineering-code")["build"] == ["grunt", "tester"] and party_recipes.get("engineering-code")["check"] == ["reviewer"]
    assert party_recipes.get("web-pages")["build"][:3] == ["grunt", "ui-kit", "copywriter"]


def test_a_backend_is_offered_data_only_when_the_folder_has_sql():
    assert [r["id"] for r in party_recipes.for_kind("backend", {"sql": 0})] == ["backend"]
    assert [r["id"] for r in party_recipes.for_kind("backend", None)] == ["backend"]
    assert [r["id"] for r in party_recipes.for_kind("backend", {"sql": 4})] == ["backend", "backend-data"]
    assert [r["id"] for r in party_recipes.for_kind("nonsense")] == ["engineering-code"]


def test_lean_is_the_leader_alone_standard_two_builders_and_a_checker_full_every_seat():
    feat = party_recipes.get("mobile-features")
    assert party_recipes.sized(feat, "lean") == {"leader": "product-manager", "team": [], "size": "lean"}
    assert party_recipes.sized(feat, "standard")["team"] == ["grunt", "artist", "reviewer"]
    full = party_recipes.sized(feat, "full")["team"]
    assert full == ["grunt", "artist", "aso", "reviewer", "accessibility-reviewer"]          # (the fourth builder: no seat for it)
    web = party_recipes.get("web-pages")
    assert party_recipes.sized(web, "full")["team"] == ["grunt", "ui-kit", "copywriter", "reviewer", "accessibility-reviewer"]
    game = party_recipes.get("game")
    assert library.seats_of("game-designer") == {"lead": 1, "build": 4, "check": 1}
    assert party_recipes.sized(game, "full")["team"] == ["grunt", "artist", "level-designer", "sound-designer", "playtester"]
    assert party_recipes.sized(game, "standard")["team"] == ["grunt", "artist", "playtester"]
    wiki = party_recipes.get("wiki")                                                          # one builder: standard has just that one
    assert party_recipes.sized(wiki, "standard")["team"] == ["copywriter", "editor"] and party_recipes.sized(wiki, "lean")["team"] == []


def test_ideation_and_release_keep_their_whole_seats_in_every_size():
    for pid in ("ideation", "release"):
        r = party_recipes.get(pid)
        teams = [party_recipes.sized(r, s)["team"] for s in idea_target.SIZES]
        assert teams[0] == teams[1] == teams[2] == [*r["build"], *r["check"]] and teams[0]
    assert sorted(party_recipes.sized(party_recipes.get("ideation"), "lean")["team"]) == sorted([*library.VIEWS, library.SKEPTIC])


def test_a_size_that_is_none_is_refused_and_each_size_has_its_target():
    with pytest.raises(ValueError, match="lean, standard or full"):
        party_recipes.sized(party_recipes.get("wiki"), "huge")
    assert party_recipes.TARGET == {"lean": "thrift", "standard": "balance", "full": "quality"} == idea_target.SIZE_TARGET


def test_a_party_the_project_has_is_the_same_leader_with_the_standard_team_inside_its_team():
    feat = party_recipes.get("mobile-features")
    standard = party_recipes.sized(feat, "standard")["team"]
    mine = {"leader": "product-manager", "team": [*standard, "aso"]}
    assert party_recipes.has(feat, [mine]) and party_recipes.has(feat, [{"leader": "product-manager", "team": standard}])
    assert not party_recipes.has(feat, [{"leader": "product-manager", "team": ["grunt"]}])         # the standard team is not inside it
    assert not party_recipes.has(feat, [{"leader": "architect", "team": standard}]) and not party_recipes.has(feat, [])
    assert not party_recipes.has(party_recipes.get("wiki"), [mine])                                # another recipe of the same leader
    ideation = party_recipes.get("ideation")
    assert party_recipes.has(ideation, [{"leader": "investor", "team": [*library.VIEWS, library.SKEPTIC]}])


def test_the_kind_a_recipe_is_proposed_to_prefers_the_projects_own():
    assert party_recipes.kind_of("release", "web") == "web" and party_recipes.kind_of("release", "wiki") == "mobile"
    assert party_recipes.kind_of("ideation", "design") == "design" and party_recipes.kind_of("nope") == ""
