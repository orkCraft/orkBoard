"""Spec 157 C (docs/specs/157-the-inventory-a-merchants-stall.md): the stall's host, on the Board's host of tests/test_board_35.py: `ideas.stall`, `stall_take`, `stall_back`,
`hero_table`, and the hero in the snapshot."""
from __future__ import annotations


import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError
from orkboard.realm import goal_team, heroes, ideas, look_wait, party_recipes
from tests.test_board_35 import host, model, runner  # noqa: F401  (fixtures)


def _party(host, craft="tech", title=None):
    root = host.ideas.root()
    slug = ideas.add_track(root, title or f"{craft} party")
    recipe = party_recipes.CRAFTS[craft]
    goal_team.set_recipe(root, slug, craft)
    goal_team.set_team(root, slug, party_recipes.squad_of(recipe), leader=recipe["leader"])
    return slug


def stall(host, chair=""):
    return host.command("ideas.stall", {"chair": chair})


def shelf(got, slot):
    return next(s for s in got["shelves"] if s["slot"] == slot)


def ware(got, slot, wid):
    return next(w for w in shelf(got, slot)["wares"] if w["id"] == wid)


def card(got, slot):
    return next(c for c in got["hand"] if c["slot"] == slot)




def test_the_orkmasters_chair_has_its_six_slots_and_carries_what_is_set(host):
    """Spec 168 H2 (decisions §283.31): the slots are How deep, The build starts, The night, Lands in dev by itself, Push, Goals at once."""
    got = stall(host)
    assert got["chair"] == "" and got["whose"] == "The Orkmaster" and got["say"]
    assert [s["slot"] for s in got["shelves"]] == ["target", "build_start", "night", "review", "push", "max_parallel"]
    assert all(s["kind"] == "small" for s in got["shelves"])
    assert [w["id"] for w in shelf(got, "target")["wares"]] == ["thrift", "balance", "quality"]
    assert [w["id"] for w in shelf(got, "build_start")["wares"]] == ["now", "30m", "2h", "tonight", "hand"]
    assert [w["id"] for w in shelf(got, "night")["wares"]] == ["off", "ideas", "builds", "proposals"]
    assert [w["id"] for w in shelf(got, "push")["wares"]] == ["no", "main", "both"]
    assert [w["id"] for w in shelf(got, "max_parallel")["wares"]] == ["1", "3", "8"]
    assert {c["slot"]: c["yours"] for c in got["hand"]} == {"target": "balance", "build_start": look_wait.build_start(True, host.ideas.settings_now().get("look_wait")), "night": "off", "review": "on", "push": "no", "max_parallel": "1"}
    assert all(c["fixed"] is False and c["word"] for c in got["hand"])
    assert ware(got, "target", "balance")["price"] == {"mine": True}
    assert ware(got, "target", "thrift")["price"] == {"word": "lighter"} and ware(got, "target", "quality")["price"] == {"word": "heavier"}
    assert ware(got, "push", "both")["price"] == {"word": "same cost"}
    assert shelf(got, "target")["at"] == 1 and shelf(got, "target")["cheaper"] is True and shelf(got, "push")["cheaper"] is False
    assert ware(got, "target", "balance")["default"] is True and ware(got, "target", "balance")["star"] is True        # the default, and the Orkmaster's pick
    assert ware(got, "night", "ideas")["star"] is True and "star" not in ware(got, "night", "off")




def test_a_take_writes_the_setting_publishes_and_undoes(host):
    got = host.command("ideas.stall_take", {"chair": "", "slot": "target", "value": "quality"})
    assert host.command("ideas.board")["target"] == "quality"
    assert got["undo"] == {"slot": "target", "value": "balance"}
    assert card(got["stall"], "target")["yours"] == "quality" and ware(got["stall"], "target", "balance")["before"] is True
    assert ware(got["stall"], "target", "quality")["before"] is False
    back = host.command("ideas.stall_take", {"chair": "", **got["undo"]})
    assert host.command("ideas.board")["target"] == "balance" and back["undo"]["value"] == "quality"




def test_the_other_settings_go_through_their_own_writers(host):
    host.command("ideas.stall_take", {"chair": "", "slot": "build_start", "value": "now"})
    host.command("ideas.stall_take", {"chair": "", "slot": "night", "value": "builds"})
    host.command("ideas.stall_take", {"chair": "", "slot": "review", "value": "off"})
    host.command("ideas.stall_take", {"chair": "", "slot": "max_parallel", "value": "3"})
    got = host.command("ideas.stall_take", {"chair": "", "slot": "push", "value": "main"})["stall"]
    b, mine = host.command("ideas.board"), host.ideas.settings_now()
    assert (b["look_wait"], b["autostart"], b["work_at_night"], b["night_rung"], b["build_start"]) == ("none", True, True, "builds", "now")
    assert mine["push"] == "main" and mine["review"] is True and mine["max_parallel"] == 3
    assert {c["slot"]: c["yours"] for c in got["hand"]} == {"target": "balance", "build_start": "now", "night": "builds", "review": "off", "push": "main", "max_parallel": "3"}
    host.command("ideas.stall_take", {"chair": "", "slot": "build_start", "value": "hand"})
    b = host.command("ideas.board")
    assert (b["autostart"], b["look_wait"], b["build_start"]) == (False, "none", "hand")      # by hand turns the start off and leaves the look as it was




def test_stall_back_writes_the_defaults(host):
    for slot, value in (("target", "thrift"), ("build_start", "30m"), ("night", "builds"), ("review", "off"), ("push", "both"), ("max_parallel", "8")):
        host.command("ideas.stall_take", {"chair": "", "slot": slot, "value": value})
    for slot in ("target", "build_start", "night", "review", "push", "max_parallel"):
        got = host.command("ideas.stall_back", {"chair": "", "slot": slot})
    b, mine = host.command("ideas.board"), host.ideas.settings_now()
    assert (b["target"], b["look_wait"], b["autostart"], b["work_at_night"]) == (settings.IDEAS["target"], settings.IDEAS["look_wait"], True, False)
    assert mine["push"] is False and mine["review"] is False and mine["max_parallel"] == 1
    assert card(got["stall"], "push")["yours"] == "no"


def test_a_tech_partys_chair_has_its_heroes_its_tool_its_tier_its_size_and_how_it_answers(host):
    party = _party(host)
    got = stall(host, party)
    assert got["chair"] == party and [s["slot"] for s in got["shelves"]] == ["hero", "tool", "tier", "size", "answers"]
    assert shelf(got, "hero")["kind"] == "heroes" and shelf(got, "tool")["kind"] == "small"
    assert [w["id"] for w in shelf(got, "hero")["wares"]] == ["sh-c4", "sh-xp", "sh-scene"]
    xp = ware(got, "hero", "sh-xp")
    assert xp["word"] == "Spike Shaman" and xp["stats"] == {"school": "Extreme programming", "flow": "test → code → refactor", "size": "standard", "decides": 3, "says_no": 2}
    assert xp["head"]["tier"] == "elder" and xp["head"]["race"] and xp["price"] == {"word": "one pass"}
    assert "Sh.man" in got["say"] and "C4 and hotspots" in got["say"]
    assert ware(got, "hero", "sh-c4")["price"] == {"mine": True}
    assert card(got, "hero")["yours"] == "sh-c4" and card(got, "hero")["head"] == ware(got, "hero", "sh-c4")["head"]
    assert [w["id"] for w in shelf(got, "tier")["wares"]] == ["", "laborer", "warrior", "elder"]        # *Default* (it follows *How deep*) is a way among them
    assert [w["id"] for w in shelf(got, "size")["wares"]] == ["lean", "standard", "full"] and [w["id"] for w in shelf(got, "answers")["wares"]] == ["pen", "choice", "fork", "silent"]
    assert [shelf(got, x)["label"] for x in ("tier", "size", "answers")] == ["Its tier", "Its party's size", "How it answers"]
    assert card(got, "tier")["yours"] == "" and card(got, "size")["yours"] == "standard" and card(got, "answers")["yours"] == "choice"       # a party that said nothing
    assert ware(got, "answers", "choice")["default"] is True and ware(got, "size", "standard")["default"] is True and ware(got, "tier", "")["default"] is True
    assert card(got, "tool")["yours"] == "" and ware(got, "tool", "")["price"] == {"mine": True}


def test_a_tool_signed_in_is_a_ware_and_a_tool_not_signed_in_is_refused(host, monkeypatch):
    party = _party(host)
    monkeypatch.setattr(host.ideas, "tools", lambda a: {"main": "claude", "tools": [{"id": "claude", "name": "Claude Code", "ready": True}, {"id": "codex", "name": "Codex", "ready": False}]})
    assert [w["id"] for w in shelf(stall(host, party), "tool")["wares"]] == ["", "claude"]
    got = host.command("ideas.stall_take", {"chair": party, "slot": "tool", "value": "claude"})
    assert goal_team.tool_of(host.ideas.root(), party) == "claude" and got["undo"] == {"slot": "tool", "value": ""}
    with pytest.raises(CommandError):
        host.command("ideas.stall_take", {"chair": party, "slot": "tool", "value": "codex"})
    host.command("ideas.stall_back", {"chair": party, "slot": "tool"})
    assert goal_team.tool_of(host.ideas.root(), party) == ""


def test_a_hero_is_taken_undone_and_put_back(host):
    party, root = _party(host), host.ideas.root()
    got = host.command("ideas.stall_take", {"chair": party, "slot": "hero", "value": "sh-xp"})
    assert goal_team.hero_of(root, party).id == "sh-xp" and got["undo"] == {"slot": "hero", "value": "sh-c4"}
    assert card(got["stall"], "hero")["yours"] == "sh-xp" and ware(got["stall"], "hero", "sh-c4")["before"] is True
    assert "Red" in got["stall"]["say"]
    host.command("ideas.stall_take", {"chair": party, **got["undo"]})
    assert goal_team.hero_of(root, party).id == "sh-c4"
    host.command("ideas.stall_take", {"chair": party, "slot": "hero", "value": "sh-xp"})
    host.command("ideas.stall_back", {"chair": party, "slot": "hero"})
    assert goal_team.hero_of(root, party).id == "sh-c4" and "hero" not in dict(ideas.track_page(root, party).meta)




def test_a_leaders_tier_is_taken_for_its_own_calls_and_put_back_to_default(host):
    party, root = _party(host), host.ideas.root()
    team = goal_team.team_of(root, party)
    seats = dict(goal_team.tiers_of(root, party))
    got = host.command("ideas.stall_take", {"chair": party, "slot": "tier", "value": "laborer"})
    assert goal_team.lead_tier_of(root, party) == "laborer" and card(got["stall"], "tier")["yours"] == "laborer" and card(got["stall"], "tier")["word"] == "Laborer"
    assert goal_team.tiers_of(root, party) == seats                                                       # its seats' tiers are not its own
    assert got["undo"] == {"slot": "tier", "value": ""}
    assert ware(got["stall"], "tier", "laborer")["price"] == {"mine": True}
    assert ware(got["stall"], "tier", "elder")["price"] == {"word": "heavier"} and ware(got["stall"], "tier", "")["price"] == {"word": "heavier"}      # Default: balance's Talk tier, warrior
    assert got["stall"]["shelves"][2]["wares"][0]["price"] == {"word": "heavier"}
    host.command("ideas.stall_back", {"chair": party, "slot": "tier"})
    assert goal_team.lead_tier_of(root, party) == "" and team


def test_a_partys_size_is_taken_with_its_seats_tiers_and_no_target_and_how_it_answers_is_taken(host):
    party, root = _party(host), host.ideas.root()
    got = host.command("ideas.stall_take", {"chair": party, "slot": "size", "value": "full"})
    assert goal_team.size_of(root, party) == "full" and card(got["stall"], "size")["yours"] == "full" and got["undo"] == {"slot": "size", "value": "standard"}
    team = goal_team.team_of(root, party)
    recipe = party_recipes.tiers_for(goal_team.leader_of(root, party), team, "full")
    assert {s: t for s, t in goal_team.tiers_of(root, party).items() if s in team} == {s: t for s, t in recipe.items() if s in team}
    assert host.command("ideas.board")["target"] == "balance"                                            # a size is no Target: How deep is as it was
    assert ware(got["stall"], "size", "lean")["price"] == {"word": "lighter"} and ware(got["stall"], "size", "standard")["price"] == {"word": "lighter"}
    host.command("ideas.stall_back", {"chair": party, "slot": "size"})
    assert goal_team.size_of(root, party) == "standard"
    got = host.command("ideas.stall_take", {"chair": party, "slot": "answers", "value": "fork"})
    assert goal_team.answers_of(root, party) == "fork" and card(got["stall"], "answers")["word"] == "Fork" and got["undo"] == {"slot": "answers", "value": "choice"}
    fork_price = ware(got["stall"], "answers", "fork")["price"]
    assert fork_price == {"mine": True} and all(ware(got["stall"], "answers", w)["price"] == {"word": "lighter"} for w in ("pen", "choice", "silent"))
    back = host.command("ideas.stall_take", {"chair": party, "slot": "answers", "value": "choice"})
    money = ware(back["stall"], "answers", "fork")["price"]["money"]
    assert money.startswith("+$") and "a question" in money and ware(back["stall"], "answers", "silent")["price"] == {"word": "same cost"}
    host.command("ideas.stall_take", {"chair": party, "slot": "answers", "value": "silent"})
    assert goal_team.answers_of(root, party) == "silent"
    host.command("ideas.stall_back", {"chair": party, "slot": "answers"})
    assert goal_team.answers_of(root, party) == "choice"
    with pytest.raises(Exception, match="not a ware"):
        host.command("ideas.stall_take", {"chair": party, "slot": "answers", "value": "shout"})


def test_release_has_its_chair_locked(host):
    (host.repo_root / "orkcraft.toml").write_text("[gate]\nalways = [\"tests/test_architecture.py\", \"tests/test_updates.py\"]\n")
    party = _party(host, "release")
    got = stall(host, party)
    assert [s["slot"] for s in got["shelves"]] == ["gate"]          # one hero offered: its hand card alone, no shelf
    assert card(got, "hero")["yours"] == "release" and card(got, "hero")["fixed"]
    gate = shelf(got, "gate")["wares"][0]
    assert gate["price"]["locked"] and "tests/test_architecture.py" in gate["line"]
    assert all(c["fixed"] for c in got["hand"])
    for slot in ("hero", "gate"):
        for cmd in ("ideas.stall_take", "ideas.stall_back"):
            with pytest.raises(CommandError, match="fixed|orkcraft.toml"):
                host.command(cmd, {"chair": party, "slot": slot, "value": "release"})
    assert goal_team.hero_of(host.ideas.root(), party).id == "release"






















# -- spec 164 E and F: offered, locked or starred by the project's kind; a cut hero said once --------------------------------------------------


def _kind(host, kind):
    from orkboard.realm import project_kind
    project_kind.keep(host.ideas.state_dir, kind)


def test_products_shelf_is_in_order_with_no_pivot_knight_and_pillar_knight_lays_four_places(host):
    _kind(host, "web")
    party = _party(host, "product")
    got = stall(host, party)
    ids = [w["id"] for w in shelf(got, "hero")["wares"]]
    assert "uni-lean" not in ids and "uni-pillar" in ids
    assert ids == [h.id for h in heroes.of("product")]
    assert ware(got, "hero", "uni-pillar")["price"] == {"word": "one pass"}
    taken = host.command("ideas.stall_take", {"chair": party, "slot": "hero", "value": "uni-pillar"})
    assert "4 places" in taken["stall"]["say"] and goal_team.hero_of(host.ideas.root(), party).id == "uni-pillar"




def test_scene_shaman_is_locked_and_refused_in_a_web_app_and_starred_in_a_game(host):
    _kind(host, "web")
    party = _party(host)
    got = stall(host, party)
    assert ware(got, "hero", "sh-scene")["price"] == {"locked": "Scene Shaman reads an engine's scenes: this project is not a game"}
    with pytest.raises(CommandError, match="not a game"):
        host.command("ideas.stall_take", {"chair": party, "slot": "hero", "value": "sh-scene"})
    assert "hero" not in dict(ideas.track_page(host.ideas.root(), party).meta)
    _kind(host, "game")
    got = stall(host, party)
    assert ware(got, "hero", "sh-scene").get("star") is True and ware(got, "hero", "sh-scene")["price"] == {"word": "one pass"}
    assert not any(w.get("star") for w in shelf(got, "hero")["wares"] if w["id"] != "sh-scene")






