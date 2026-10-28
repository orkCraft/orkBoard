"""Spec 99 A (docs/specs/99-a-goals-way.md §1, decisions §122.5, §151.5), the host's part: New party's presets. One row a craft of the project's kind (a game's Game design, Tech, Art, Release,
LiveOps and Marketing; the rest's Product, Design, Tech, Release, Run and Marketing), each under the stage that offers it, with its leader, the roles to tick from, the squad ticked by default and
its three sizes (the same team in each: the size sets the tiers); the person's own party; `ideas.party_presets` (no model, nothing written); a craft kept with the party as its recipe. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, idea_target, ideas, library, party_presets, party_recipes, party_resize, project_kind, project_stage


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.root = h.ideas.root()
    yield h


@pytest.mark.parametrize("kind", project_kind.KINDS)
def test_the_presets_of_a_kind_are_its_crafts_under_their_stages_and_the_persons_own_each_with_its_three_sizes(kind):
    rows = party_presets.listed(kind)
    crafts = ["game-design", "tech", "art", "release", "liveops", "marketing"] if kind == "game" else ["product", "design", "tech", "release", "run", "marketing"]
    assert [r["group"] for r in rows] == ["stage"] * 6 + ["own"] and [r["id"] for r in rows] == [*crafts, "mixed"]
    assert [r["recipe"] for r in rows[:6]] == crafts and rows[-1]["name"] == "Your own party"
    assert {r["id"]: r["stage"] for r in rows[:6]} == {c: project_stage.FROM[c] for c in crafts} and all(r["line"] for r in rows)
    assert "team" not in {r["id"] for r in rows} and "ideation" not in {r["id"] for r in rows}            # Team and Ideation are not offered (decisions §122)
    assert len({r["id"] for r in rows}) == len(rows)
    for r in rows:
        assert library.get(r["leader"]) is not None and set(r["sizes"]) == set(idea_target.SIZES)
        for size, got in r["sizes"].items():
            assert got == party_recipes.sized({"leader": r["leader"], "build": r["build"], "check": r["check"], "squad": r["squad"]}, size)
            assert got["team"] == r["squad"], (kind, r["id"], size)                                      # the squad and the size are apart
            assert goal_team.seats(got["team"], got["leader"]) == "", (kind, r["id"], size)
        assert r["ops"] is False and r["blocked"] == "" and r["whole"] is False


def test_a_row_says_its_stage_its_proposed_size_the_roles_to_tick_and_the_squad_ticked_and_release_is_locked_and_alone():
    rows = {r["id"]: r for r in party_presets.listed("web")}
    assert {c: (rows[c]["stage"], rows[c]["size"]) for c in ("product", "design", "tech", "release", "run", "marketing")} == {
        "product": ("idea", "lean"), "design": ("idea", "lean"), "tech": ("being_made", "standard"), "release": ("idea", "lean"), "run": ("live", "standard"),
        "marketing": ("live", "standard")}
    tech = rows["tech"]
    assert (tech["name"], tech["leader"], tech["build"], tech["check"], tech["squad"], tech["locked"]) == (
        "Tech", "architect", ["grunt", "tester"], ["reviewer", "security-reviewer"], ["grunt", "tester", "reviewer"], False)
    release = rows["release"]
    assert (release["leader"], release["squad"], release["locked"]) == ("release-manager", [], True)
    assert [release["sizes"][s]["tiers"] for s in idea_target.SIZES] == [{"release-manager": "warrior"}] * 3
    assert tech["sizes"]["lean"]["tiers"] == {"architect": "warrior", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}
    assert tech["sizes"]["standard"]["tiers"] == {"architect": "elder", "grunt": "warrior"}
    assert tech["sizes"]["full"]["tiers"] == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    game = {r["id"]: r for r in party_presets.listed("game")}
    assert (game["art"]["name"], game["art"]["leader"], game["art"]["build"][:2]) == ("Art", "art-director", ["artist", "sound-designer"])
    assert (game["game-design"]["name"], game["liveops"]["name"], game["liveops"]["leader"]) == ("Game design", "LiveOps", "analyst")


def test_the_own_party_is_the_taskmaster_alone():
    own = party_presets.listed("code")[-1]
    assert (own["id"], own["name"], own["line"], own["leader"], own["build"], own["check"]) == (
        "mixed", "Your own party", "Start from the Taskmaster and add who you need", "taskmaster", [], [])
    assert own["sizes"]["full"]["team"] == [] and own["sizes"]["lean"]["tiers"] == {}                                   # the Taskmaster is no seat


def test_a_running_party_carries_the_recurring_goals_of_its_kind_and_team_is_no_row():
    web = {r["id"]: r for r in party_presets.listed("web")}
    assert [x["id"] for x in web["run"]["routines"]] and web["run"]["routines"] == party_presets.recurring.listed("web-liveops")
    game = {r["id"]: r for r in party_presets.listed("game")}
    assert game["liveops"]["routines"] == party_presets.recurring.listed("game-liveops") and game["tech"]["routines"] == []
    assert party_presets.team_words("") == "" and party_presets.team_words("here") == "Team is in this project" and party_presets.team_words("Mars") == "Team is in Mars"
    assert party_presets.listed("web", team_at="Mars", ops=True) == party_presets.listed("web")                         # Team says nothing now


# -- the command ---------------------------------------------------------------------------------------------------------------------------------------------------

def test_ideas_party_presets_answers_for_the_projects_kind_and_writes_nothing(host):
    got = host.command("ideas.party_presets", {})
    assert got["kind"] == {"id": "code", "words": "code"} and got["presets"] == party_presets.listed("code")
    assert [r["id"] for r in got["presets"][:6]] == ["product", "design", "tech", "release", "run", "marketing"]
    assert ideas.tracks(host.root, make=False) == [] or all(t["slug"] == "general" for t in ideas.tracks(host.root, make=False))


def test_ideas_party_presets_follows_what_the_folder_is(fake_repo):
    (fake_repo / "project.godot").write_text("", encoding="utf-8")
    got = Orkboard(fake_repo).command("ideas.party_presets", {})
    assert got["kind"]["id"] == "game" and [r["id"] for r in got["presets"][:6]] == ["game-design", "tech", "art", "release", "liveops", "marketing"]


def test_a_party_made_from_a_craft_keeps_it_as_its_recipe_and_a_size_never_changes_its_squad(host):
    tech = next(r for r in party_presets.listed("code") if r["id"] == "tech")
    slug = host.command("ideas.goal_save", {"title": "Tech", "about": "Code and tests.", "leader": tech["leader"], "team": tech["squad"], "every": [], "size": "lean", "proposal": tech["id"]})["slug"]
    assert goal_team.recipe_of(host.root, slug) == "tech" and goal_team.team_of(host.root, slug) == ["grunt", "tester", "reviewer"]
    assert goal_team.craft_of(host.root, slug) == "tech"
    assert goal_team.tiers_of(host.root, slug) == tech["sizes"]["lean"]["tiers"]
    grown = party_resize.resized(host.root, slug, "full")
    assert grown["recipe"] == "tech" and grown["team"] == ["grunt", "tester", "reviewer"] and grown["joins"] == [] and grown["leaves"] == []
    assert grown["tiers"] == tech["sizes"]["full"]["tiers"]
    host.command("ideas.goal_save", {"slug": slug, "size": "full"})
    assert goal_team.team_of(host.root, slug) == ["grunt", "tester", "reviewer"] and goal_team.tiers_of(host.root, slug) == tech["sizes"]["full"]["tiers"]


def test_a_party_made_from_a_craft_without_a_size_still_keeps_its_recipe(host):
    row = next(r for r in party_presets.listed("code") if r["id"] == "design")
    slug = host.command("ideas.goal_save", {"title": "Design", "about": "Screens.", "leader": row["leader"], "team": row["squad"], "every": [], "proposal": "design"})["slug"]
    assert goal_team.recipe_of(host.root, slug) == "design" and goal_team.craft_of(host.root, slug) == "design" and goal_team.size_of(host.root, slug) == ""


def test_a_party_made_from_a_craft_saves_the_seats_tools_beside_the_size(host):
    row = next(r for r in party_presets.listed("game") if r["id"] == "tech")
    full = row["sizes"]["full"]
    slug = host.command("ideas.goal_save", {"title": "Tech", "about": "A game.", "leader": full["leader"], "team": full["team"], "every": [], "size": "full", "proposal": row["id"],
                                            "tools": {"grunt": "claude"}})["slug"]
    assert goal_team.team_of(host.root, slug) == ["grunt", "tester", "reviewer"] and goal_team.tools_of(host.root, slug) == {"grunt": "claude"}


def test_a_running_party_made_with_its_recurring_goals_asks_its_kinds_routines(host):
    run = next(r for r in party_presets.listed("code") if r["id"] == "run")
    pick = [run["routines"][0]["id"]]
    got = host.command("ideas.goal_save", {"title": "Run", "about": "Keep it running.", "leader": run["leader"], "team": run["squad"], "every": [], "proposal": "run", "routines": pick})
    assert goal_team.recipe_of(host.root, got["slug"]) == "run"
    assert len([i for i in ideas.ideas(host.root, got["slug"])]) == 1                                          # the recurring goal added
    with pytest.raises(Exception, match="No recurring goal"):
        host.command("ideas.goal_save", {"title": "Run again", "about": "x", "leader": run["leader"], "team": [], "proposal": "run", "routines": ["nope"]})
