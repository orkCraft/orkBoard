"""Spec 75 A (docs/specs/75-parties-fitted-to-the-project.md §2, Tests → A): the recipes name only the library's agents and fit their leaders' seats;
the three sizes of a recipe (spec 87 §5; lean: no team; standard: the first builder; full: the first builder and the first checker; Ideation and Release the same);
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


def test_lean_is_the_leader_alone_standard_its_first_builder_full_the_first_builder_and_the_first_checker():
    feat = party_recipes.get("mobile-features")
    assert party_recipes.sized(feat, "lean") == {"leader": "product-manager", "team": [], "tiers": {"product-manager": "warrior"}, "size": "lean"}
    assert party_recipes.sized(feat, "standard")["team"] == ["grunt"]
    assert party_recipes.sized(feat, "full")["team"] == ["grunt", "reviewer"]                 # (the other builders and checkers stay listed, with no seat)
    web = party_recipes.get("web-pages")
    assert party_recipes.sized(web, "standard")["team"] == ["grunt"] and party_recipes.sized(web, "full")["team"] == ["grunt", "reviewer"]
    game = party_recipes.get("game")
    assert library.seats_of("game-designer") == {"lead": 1, "build": 1, "check": 1}
    assert party_recipes.sized(game, "full")["team"] == ["grunt", "playtester"]
    assert party_recipes.sized(game, "standard")["team"] == ["grunt"]
    wiki = party_recipes.get("wiki")
    assert party_recipes.sized(wiki, "standard")["team"] == ["copywriter"] and party_recipes.sized(wiki, "full")["team"] == ["copywriter", "editor"]
    assert party_recipes.sized(wiki, "lean")["team"] == []
    arch = party_recipes.get("backend-data")
    assert party_recipes.sized(arch, "full")["team"] == ["data-engineer", "data-reviewer"]


def test_ideation_and_release_are_sized_too_lean_the_leader_alone_standard_the_first_builder_full_with_the_first_checker():
    for pid in ("ideation", "release"):
        r = party_recipes.get(pid)
        lean, standard, full = [party_recipes.sized(r, s)["team"] for s in idea_target.SIZES]
        assert lean == [] and standard == r["build"][:1] and full == [*r["build"][:1], *r["check"][:1]]
    assert party_recipes.sized(party_recipes.get("ideation"), "standard")["team"] == ["product-view"]
    assert party_recipes.sized(party_recipes.get("ideation"), "full")["team"] == ["product-view", "skeptic"]
    assert party_recipes.sized(party_recipes.get("release"), "full")["team"] == ["release-engineer", "release-checker"]


def test_a_size_that_is_none_is_refused_and_each_size_has_its_target():
    with pytest.raises(ValueError, match="lean, standard or full"):
        party_recipes.sized(party_recipes.get("wiki"), "huge")
    assert party_recipes.TARGET == {"lean": "thrift", "standard": "balance", "full": "quality"} == idea_target.SIZE_TARGET


def test_a_party_the_project_has_is_the_same_leader_with_the_standard_team_inside_its_team():
    feat = party_recipes.get("mobile-features")
    standard = party_recipes.sized(feat, "standard")["team"]
    mine = {"leader": "product-manager", "team": [*standard, "aso"]}
    assert party_recipes.has(feat, [mine]) and party_recipes.has(feat, [{"leader": "product-manager", "team": standard}])
    assert not party_recipes.has(feat, [{"leader": "product-manager", "team": ["artist"]}])        # the standard team is not inside it
    assert not party_recipes.has(feat, [{"leader": "architect", "team": standard}]) and not party_recipes.has(feat, [])
    assert not party_recipes.has(party_recipes.get("wiki"), [mine])                                # another recipe of the same leader
    ideation = party_recipes.get("ideation")
    assert party_recipes.has(ideation, [{"leader": "investor", "team": [*library.VIEWS, library.SKEPTIC]}])


def test_the_kind_a_recipe_is_proposed_to_prefers_the_projects_own():
    assert party_recipes.kind_of("release", "web") == "web" and party_recipes.kind_of("release", "wiki") == "mobile"
    assert party_recipes.kind_of("ideation", "design") == "design" and party_recipes.kind_of("nope") == ""


def test_each_size_gives_its_seats_their_tiers_lean_seasoned_standard_the_leader_veteran_full_the_leader_and_the_checker_veteran():
    feat = party_recipes.get("mobile-features")
    lean, std, full = (party_recipes.sized(feat, s) for s in idea_target.SIZES)
    assert lean["tiers"] == {"product-manager": "warrior"}
    assert std["tiers"] == {"product-manager": "elder", "grunt": "warrior"}
    assert full["tiers"] == {"product-manager": "elder", "grunt": "warrior", "reviewer": "elder"}
    for r in (party_recipes.get(i) for i in ("ideation", "release", "game", "wiki", "engineering-code")):
        got = [party_recipes.sized(r, s) for s in idea_target.SIZES]
        assert got[0]["team"] == [] and len(got[1]["team"]) == 1 and len(got[2]["team"]) == 2
        assert "laborer" not in got[2]["tiers"].values() and "laborer" not in got[0]["tiers"].values()


def test_tiers_for_any_team_follows_the_sizes_and_a_party_made_before_keeps_its_team():
    team = ["grunt", "tester", "reviewer", "security-reviewer"]
    assert party_recipes.tiers_for("architect", team, "lean") == {s: "warrior" for s in ["architect", *team]}
    assert party_recipes.tiers_for("architect", team, "standard") == {"architect": "elder", "grunt": "warrior"}
    assert party_recipes.tiers_for("architect", team, "full") == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder", "security-reviewer": "elder"}
    assert party_recipes.tiers_for("taskmaster", ["grunt"], "standard") == {"grunt": "warrior"}          # the Taskmaster is no seat
    assert party_recipes.sized(party_recipes.get("backend"), "standard")["team"] == ["grunt"]
