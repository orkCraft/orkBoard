"""Spec 91 E (docs/specs/91-the-owners-list.md §7, decisions §107.5), the host's part: New party's presets. The stages of each kind of project (Ideation, Concept, Build, Release, LiveOps; Concept,
Build and LiveOps are `party_recipes.STAGE_RECIPES`, made of the library's agents and fitted to the kind), the crafts and the person's own, each with its leader, its builders and checkers and its three
sizes; `ideas.party_presets` (no model, nothing written); a stage kept with the party as its recipe, so a Lean party grows back. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, idea_target, ideas, library, party_presets, party_recipes, party_resize, project_kind


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.root = h.ideas.root()
    yield h


STAGE_ROWS = [(k, r) for k, rows in party_recipes.STAGE_RECIPES.items() for r in rows]


def test_every_kind_has_a_concept_a_build_and_a_liveops_made_of_the_librarys_agents_that_fit_the_seats():
    assert set(party_recipes.STAGE_RECIPES) == set(project_kind.KINDS) - {"empty"}                   # an empty folder has code's
    for kind, rows in party_recipes.STAGE_RECIPES.items():
        assert [r["id"] for r in rows] == [f"{kind}-concept", f"{kind}-build", f"{kind}-liveops"]
        assert [r["name"] for r in rows] == ["Concept", "Build", "LiveOps"]


@pytest.mark.parametrize("kind,recipe", STAGE_ROWS, ids=[r["id"] for _k, r in STAGE_ROWS])
def test_a_stage_recipe_names_only_the_librarys_agents_and_fits_its_leaders_seats_in_every_size(kind, recipe):
    for slug in [recipe["leader"], *recipe["build"], *recipe["check"]]:
        assert library.get(slug) is not None, slug
    assert library.get(recipe["leader"]).band == "lead" and not library.get(recipe["leader"]).pitch
    assert all(library.get(s).band == "build" and not library.get(s).pitch for s in recipe["build"])
    assert all(library.get(s).band == "check" and not library.get(s).pitch for s in recipe["check"])
    assert recipe["build"] and recipe["check"] and recipe["name"] and recipe["line"] and recipe["because"]
    assert len(recipe["build"]) + len(recipe["check"]) <= goal_team.SEATS + 3                       # candidates, a size seats one a stage
    for size in idea_target.SIZES:
        got = party_recipes.sized(recipe, size)
        assert goal_team.seats(got["team"], got["leader"]) == "", (recipe["id"], size)
        assert len(got["team"]) <= goal_team.SEATS
    assert party_recipes.sized(recipe, "lean")["team"] == [] and party_recipes.sized(recipe, "standard")["team"] == recipe["build"][:1]
    assert party_recipes.sized(recipe, "full")["team"] == [recipe["build"][0], recipe["check"][0]]


def test_the_stage_recipes_are_proposed_to_no_one_but_are_found_by_id_and_kind():
    proposed = {r["id"] for rows in party_recipes.RECIPES.values() for r in rows}
    assert not proposed & {r["id"] for _k, r in STAGE_ROWS}
    assert all(party_recipes.for_kind(k) and not any(r["id"].endswith(("-concept", "-liveops")) for r in party_recipes.for_kind(k)) for k in project_kind.KINDS)
    assert party_recipes.get("game-build")["leader"] == "game-designer" and party_recipes.get("web-liveops")["leader"] == "growth"
    assert party_recipes.kind_of("game-build") == "game" and party_recipes.kind_of("game-build", "mobile") == "game" and party_recipes.kind_of("mobile-concept", "mobile") == "mobile"
    assert party_recipes.get("nothing") is None


def test_the_stages_of_a_game_are_the_game_designers_concept_build_and_liveops():
    game = {r["id"]: r for r in party_recipes.STAGE_RECIPES["game"]}
    assert (game["game-concept"]["leader"], game["game-concept"]["build"], game["game-concept"]["check"]) == ("game-designer", ["level-designer", "artist"], ["playtester"])
    assert (game["game-build"]["leader"], game["game-build"]["build"], game["game-build"]["check"]) == ("game-designer", ["grunt", "artist", "sound-designer"], ["playtester", "reviewer"])
    assert (game["game-liveops"]["leader"], game["game-liveops"]["build"], game["game-liveops"]["check"]) == ("analyst", ["data-engineer", "grunt", "copywriter"], ["data-reviewer"])


def test_the_stages_of_a_kind_are_ideation_concept_build_release_liveops_and_an_empty_folder_has_codes():
    for kind in project_kind.KINDS:
        rows = party_recipes.stages_of(kind)
        assert [r["name"] for r in rows] == ["Ideation", "Concept", "Build", "Release", "LiveOps"], kind
        assert rows[0]["id"] == "ideation" and rows[3]["id"] == "release" and rows[0]["whole"] and rows[3]["whole"]
    assert [r["id"] for r in party_recipes.stages_of("empty")] == ["ideation", "code-concept", "code-build", "release", "code-liveops"]
    assert [r["id"] for r in party_recipes.stages_of("mobile")][1:4] == ["mobile-concept", "mobile-build", "release"]
    assert party_recipes.stages_of("nowhere")[2]["id"] == "code-build"


def test_a_concept_is_led_by_the_designer_the_kind_has_and_a_liveops_by_the_one_who_reads_the_numbers():
    lead = {k: [r["leader"] for r in party_recipes.stages_of(k)] for k in project_kind.KINDS}
    assert lead["game"] == ["investor", "game-designer", "game-designer", "release-manager", "analyst"]
    assert lead["mobile"][1] == "product-designer" and lead["web"][1] == "product-designer" and lead["backend"][1] == "architect"
    assert lead["web"][4] == "growth" and lead["data"][1:5] == ["analyst", "analyst", "release-manager", "analyst"] and lead["wiki"][1] == "product-manager"


# -- the list the dialog reads ------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", project_kind.KINDS)
def test_the_presets_of_a_kind_are_the_stages_the_crafts_and_the_persons_own_each_with_its_three_sizes(kind):
    rows = party_presets.listed(kind)
    assert [r["group"] for r in rows] == ["stage"] * 5 + ["craft"] * 6 + ["own"]
    assert [r["name"] for r in rows[5:]] == ["Tech", "Design", "Data", "Marketing", "Product", "Art and sound", "Your own party"]
    assert [r["id"] for r in rows[5:]] == ["engineering", "design", "data", "marketing", "product", "art", "mixed"]
    assert [r["stage"] for r in rows[:5]] == ["ideation", "concept", "build", "release", "liveops"] and all(r["line"] for r in rows)
    assert len({r["id"] for r in rows}) == len(rows)
    for r in rows:
        assert library.get(r["leader"]) is not None and set(r["sizes"]) == set(idea_target.SIZES)
        for size, got in r["sizes"].items():
            assert got == party_recipes.sized({"leader": r["leader"], "build": r["build"], "check": r["check"]}, size)
            assert goal_team.seats(got["team"], got["leader"]) == "", (kind, r["id"], size)


def test_the_craft_presets_are_the_librarys_parties_of_one_craft_and_art_and_sound_and_the_own_party_is_the_taskmaster_alone():
    rows = {r["id"]: r for r in party_presets.listed("game")}
    assert rows["engineering"]["name"] == "Tech" and (rows["engineering"]["leader"], rows["engineering"]["build"], rows["engineering"]["check"]) == ("architect", ["grunt", "tester"], ["reviewer"])
    assert (rows["art"]["name"], rows["art"]["leader"], rows["art"]["build"][:2]) == ("Art and sound", "art-director", ["artist", "sound-designer"])
    own = rows["mixed"]
    assert (own["name"], own["line"], own["leader"], own["build"], own["check"]) == ("Your own party", "Start from the Taskmaster and add who you need", "taskmaster", [], [])
    assert own["sizes"]["full"]["team"] == [] and own["sizes"]["lean"]["tiers"] == {}                                   # the Taskmaster is no seat
    assert rows["ideation"]["whole"] and rows["release"]["whole"] and not rows["game-build"]["whole"]
    assert rows["ideation"]["sizes"]["full"]["team"] == ["product-view", "skeptic"]
    assert rows["game-build"]["sizes"]["standard"] == {"leader": "game-designer", "team": ["grunt"], "tiers": {"game-designer": "elder", "grunt": "warrior"}, "size": "standard"}
    assert rows["game-build"]["sizes"]["full"]["tiers"] == {"game-designer": "elder", "grunt": "warrior", "playtester": "elder"}
    assert rows["game-build"]["sizes"]["lean"]["tiers"] == {"game-designer": "warrior"}


# -- the command ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_ideas_party_presets_answers_for_the_projects_kind_and_writes_nothing(host):
    got = host.command("ideas.party_presets", {})
    assert got["kind"] == {"id": "code", "words": "code"} and got["presets"] == party_presets.listed("code")
    assert [r["id"] for r in got["presets"][:5]] == ["ideation", "code-concept", "code-build", "release", "code-liveops"]
    assert ideas.tracks(host.root, make=False) == [] or all(t["slug"] == "general" for t in ideas.tracks(host.root, make=False))


def test_ideas_party_presets_follows_what_the_folder_is(fake_repo):
    (fake_repo / "project.godot").write_text("", encoding="utf-8")
    got = Orkboard(fake_repo).command("ideas.party_presets", {})
    assert got["kind"]["id"] == "game" and [r["id"] for r in got["presets"][:5]] == ["ideation", "game-concept", "game-build", "release", "game-liveops"]


def test_a_party_made_from_a_stage_keeps_it_as_its_recipe_and_a_lean_one_grows_back(host):
    build = party_presets.listed("code")[2]
    slug = host.command("ideas.goal_save", {"title": "Build", "about": "Code and tests.", "leader": build["leader"], "team": [], "every": [], "size": "lean", "proposal": build["id"]})["slug"]
    assert goal_team.recipe_of(host.root, slug) == "code-build" and goal_team.team_of(host.root, slug) == []
    grown = party_resize.resized(host.root, slug, "full")
    assert grown["recipe"] == "code-build" and grown["team"] == ["grunt", "reviewer"] and grown["joins"] == ["grunt", "reviewer"]
    host.command("ideas.goal_save", {"slug": slug, "size": "full"})
    assert goal_team.team_of(host.root, slug) == ["grunt", "reviewer"] and goal_team.tiers_of(host.root, slug) == {"architect": "elder", "grunt": "warrior", "reviewer": "elder"}


def test_a_party_made_from_a_preset_saves_the_seats_tools_beside_the_size(host):
    build = party_presets.listed("game")[2]
    full = build["sizes"]["full"]
    slug = host.command("ideas.goal_save", {"title": "Build", "about": "A game.", "leader": full["leader"], "team": full["team"], "every": [], "size": "full", "proposal": build["id"],
                                            "tools": {"grunt": "claude"}})["slug"]
    assert goal_team.team_of(host.root, slug) == ["grunt", "playtester"] and goal_team.tools_of(host.root, slug) == {"grunt": "claude"}
