"""Spec 157 C (docs/specs/157-the-inventory-a-merchants-stall.md): the stall's host, on the Board's host of tests/test_board_35.py: `ideas.stall`, `stall_take`, `stall_back`,
`hero_table`, and the hero in the snapshot."""
from __future__ import annotations

import json
import sys
import types

import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError
from orkboard.realm import goal_team, hero_table, heroes, ideas, party_recipes
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


def prices(got):
    return [w["price"] for s in got["shelves"] for w in s["wares"]]


def test_the_orkmasters_chair_has_its_five_shelves_and_carries_what_is_set(host):
    got = stall(host)
    assert got["chair"] == "" and got["whose"] == "The Orkmaster" and got["say"]
    assert [s["slot"] for s in got["shelves"]] == ["target", "look_wait", "autostart", "work_at_night", "push"]
    assert all(s["kind"] == "small" for s in got["shelves"])
    assert [w["id"] for w in shelf(got, "target")["wares"]] == ["thrift", "balance", "quality"]
    assert [w["id"] for w in shelf(got, "look_wait")["wares"]] == ["30m", "2h", "tonight", "none"]
    assert {c["slot"]: c["yours"] for c in got["hand"]} == {"target": "balance", "look_wait": settings.IDEAS["look_wait"], "autostart": "on", "work_at_night": "off", "push": "off"}
    assert all(c["fixed"] is False and c["word"] for c in got["hand"])
    assert ware(got, "target", "balance")["price"] == {"mine": True}
    assert ware(got, "target", "thrift")["price"] == {"word": "lighter"} and ware(got, "target", "quality")["price"] == {"word": "heavier"}
    assert ware(got, "autostart", "off")["price"] == {"word": "same cost"}


def test_no_price_is_a_number_the_host_did_not_estimate(host):
    party = _party(host)
    for chair in ("", party):
        for p in prices(stall(host, chair)):
            assert set(p) <= {"mine", "locked", "word"}
            assert "word" not in p or p["word"] in ("lighter", "heavier", "one pass", "same cost")


def test_a_take_writes_the_setting_publishes_and_undoes(host):
    got = host.command("ideas.stall_take", {"chair": "", "slot": "target", "value": "quality"})
    assert host.command("ideas.board")["target"] == "quality"
    assert got["undo"] == {"slot": "target", "value": "balance"}
    assert card(got["stall"], "target")["yours"] == "quality" and ware(got["stall"], "target", "balance")["before"] is True
    assert ware(got["stall"], "target", "quality")["before"] is False
    back = host.command("ideas.stall_take", {"chair": "", **got["undo"]})
    assert host.command("ideas.board")["target"] == "balance" and back["undo"]["value"] == "quality"


def test_a_take_publishes_changed(host):
    seen = []
    real = host.ideas.changed
    host.ideas.changed = lambda slug: (seen.append(slug), real(slug))
    host.command("ideas.stall_take", {"chair": "", "slot": "push", "value": "on"})
    assert "" in seen


def test_the_other_settings_go_through_their_own_writers(host):
    host.command("ideas.stall_take", {"chair": "", "slot": "look_wait", "value": "none"})
    host.command("ideas.stall_take", {"chair": "", "slot": "autostart", "value": "off"})
    host.command("ideas.stall_take", {"chair": "", "slot": "work_at_night", "value": "on"})
    got = host.command("ideas.stall_take", {"chair": "", "slot": "push", "value": "on"})["stall"]
    b = host.command("ideas.board")
    assert (b["look_wait"], b["autostart"], b["work_at_night"]) == ("none", False, True) and host.ideas.settings_now()["push"] is True
    assert {c["slot"]: c["yours"] for c in got["hand"]} == {"target": "balance", "look_wait": "none", "autostart": "off", "work_at_night": "on", "push": "on"}


def test_stall_back_writes_the_defaults(host):
    for slot, value in (("target", "thrift"), ("look_wait", "30m"), ("autostart", "off"), ("work_at_night", "on"), ("push", "on")):
        host.command("ideas.stall_take", {"chair": "", "slot": slot, "value": value})
    for slot in ("target", "look_wait", "autostart", "work_at_night", "push"):
        got = host.command("ideas.stall_back", {"chair": "", "slot": slot})
    b = host.command("ideas.board")
    assert (b["target"], b["look_wait"], b["autostart"], b["work_at_night"]) == (settings.IDEAS["target"], settings.IDEAS["look_wait"], True, False)
    assert host.ideas.settings_now()["push"] is False
    assert card(got["stall"], "push")["yours"] == "off"


def test_a_tech_partys_chair_has_its_heroes_its_tool_and_its_tiers(host):
    party = _party(host)
    got = stall(host, party)
    assert got["chair"] == party and [s["slot"] for s in got["shelves"]] == ["hero", "tool", "tier"]
    assert shelf(got, "hero")["kind"] == "heroes" and shelf(got, "tool")["kind"] == "small"
    assert [w["id"] for w in shelf(got, "hero")["wares"]] == ["sh-c4", "sh-xp", "sh-scene"]
    xp = ware(got, "hero", "sh-xp")
    assert xp["word"] == "Spike Shaman" and xp["stats"] == {"school": "Extreme programming", "flow": "test → code → refactor", "size": "standard", "decides": 3, "says_no": 2}
    assert xp["head"]["tier"] == "elder" and xp["head"]["race"] and xp["price"] == {"word": "one pass"}
    assert "Sh.man" in got["say"] and "C4 and hotspots" in got["say"]
    assert ware(got, "hero", "sh-c4")["price"] == {"mine": True}
    assert card(got, "hero")["yours"] == "sh-c4" and card(got, "hero")["head"] == ware(got, "hero", "sh-c4")["head"]
    assert [w["id"] for w in shelf(got, "tier")["wares"]] == ["laborer", "warrior", "elder"]
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


def test_taking_a_hero_calls_the_lay_hook_when_it_exists_and_only_for_a_hero_that_is_not_the_default(host, monkeypatch):
    laid = []
    fake = types.SimpleNamespace(lay_party=lambda root, state_dir, party: laid.append(party))
    monkeypatch.setitem(sys.modules, "orkboard.realm.lay_tables", fake)
    import orkboard.realm as realm
    monkeypatch.setattr(realm, "lay_tables", fake, raising=False)
    party = _party(host)
    host.command("ideas.stall_take", {"chair": party, "slot": "hero", "value": "sh-xp"})
    host.command("ideas.stall_back", {"chair": party, "slot": "hero"})
    assert laid == [party]


def test_a_tier_is_taken_for_every_seat_and_put_back_to_the_recipes(host):
    party, root = _party(host), host.ideas.root()
    team = goal_team.team_of(root, party)
    assert team
    start = card(stall(host, party), "tier")["yours"]
    got = host.command("ideas.stall_take", {"chair": party, "slot": "tier", "value": "laborer"})
    assert {goal_team.tiers_of(root, party)[s] for s in team} == {"laborer"} and card(got["stall"], "tier")["yours"] == "laborer"
    assert got["undo"] == {"slot": "tier", "value": start}
    assert ware(got["stall"], "tier", "laborer")["price"] == {"mine": True}
    assert set(ware(got["stall"], "tier", "elder")["price"]) == {"word"}
    host.command("ideas.stall_back", {"chair": party, "slot": "tier"})
    recipe = party_recipes.tiers_for(goal_team.leader_of(root, party), team, goal_team.size_of(root, party) or "standard")
    assert {s: t for s, t in goal_team.tiers_of(root, party).items() if s in team} == {s: t for s, t in recipe.items() if s in team}


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


def test_what_cannot_be_taken_is_refused_in_plain_words(host):
    party = _party(host)
    for args, match in (({"chair": "", "slot": "target", "value": "lavish"}, "not a ware"),
                        ({"chair": "", "slot": "hero", "value": "sh-xp"}, "no hero to take"),
                        ({"chair": "", "slot": "target"}, "value is missing"),
                        ({"chair": "nowhere", "slot": "target", "value": "thrift"}, "That party is gone"),
                        ({"chair": party, "slot": "hero", "value": "dry-sprint"}, "not a ware"),
                        ({"chair": party, "slot": "hero", "value": "release"}, "not a ware"),
                        ({"chair": party, "slot": "tier", "value": "king"}, "not a ware"),
                        ({"chair": party, "slot": "target", "value": "thrift"}, "no target to take")):
        with pytest.raises(CommandError, match=match):
            host.command("ideas.stall_take", args)
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.stall", {"chair": "nowhere"})
    with pytest.raises(CommandError):
        host.command("ideas.stall_back", {"chair": "", "slot": "hero"})
    assert host.command("ideas.board")["target"] == "balance"


def _leader(host, party):
    return next(g for g in host.command("ideas.map", {})["goals"] if g["slug"] == party)["leader"]


def test_the_snapshot_gives_a_partys_leader_its_hero(host):
    party, root = _party(host), host.ideas.root()
    hero = _leader(host, party)["hero"]
    assert hero["id"] == "sh-c4" and hero["name"] == "Sh.man" and hero["school"] == "C4 and hotspots" and hero["default"] is True
    assert hero["head"] == {"race": "shaman", "tier": "elder"}
    goal_team.set_hero(root, party, "sh-xp")
    hero = _leader(host, party)["hero"]
    assert hero["id"] == "sh-xp" and hero["default"] is False and hero["name"] == "Spike Shaman" and hero["head"]["tier"] == "elder"


def test_the_hero_table_reads_the_kept_cards_with_the_layout_and_the_elements(host):
    party, root = _party(host), host.ideas.root()
    goal_team.set_hero(root, party, "sh-xp")
    got = host.command("ideas.hero_table", {"party": party})
    assert got["hero"] == "sh-xp" and got["layout"] == "lanes" and got["party"] == party and got["elements"] == {}
    assert [p["name"] for p in got["places"]] == ["Red", "Green", "Refactor", "Released small"] and all(p["cards"] == [] for p in got["places"])
    hero_table.write(root, party, "sh-xp", {"Red": [{"title": "A test", "line": "fails first", "goal": "some-goal", "state": "hot"}]})
    got = host.command("ideas.hero_table", {"party": party})
    assert got["places"][0]["cards"][0]["goal"] == "some-goal" and set(got["elements"]) == {"some-goal"}
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.hero_table", {"party": "nowhere"})


def test_the_new_commands_are_in_the_hosts_table_and_the_projects(host):
    from orkboard.gui.board_projects import _board_commands
    for name in ("ideas.stall", "ideas.stall_take", "ideas.stall_back", "ideas.hero_table"):
        assert name in host.commands and name in _board_commands()
    json.dumps(stall(host))


def test_only_arts_chair_lays_its_makers_after_the_ai_tool_and_tier(host, monkeypatch):
    from orkboard.realm import craft_tools

    monkeypatch.setattr(craft_tools, "key", lambda _: None)
    art = _party(host, "art")
    got = stall(host, art)
    assert [s["slot"] for s in got["shelves"]] == ["tool", "tier", "craft_tools"]
    makers = shelf(got, "craft_tools")
    assert makers["label"] == "Its makers"
    assert makers["sub"] == "Run in Orkboard on your key"
    assert [w["word"] for w in makers["wares"]] == ["Picture maker", "Sound maker"]
    for w in makers["wares"]:
        assert w["line"] == craft_tools.get(w["id"]).title
        assert w["leaves"] == craft_tools.get(w["id"]).leaves
        assert not w["here"] and w["why"] == "no key on this computer"
        assert w["cap"] is None and w["price"] == {"word": "Set a cap"}
    for chair in ("", _party(host, "tech")):
        assert not any(s["slot"] == "craft_tools" for s in stall(host, chair)["shelves"])


def test_maker_plates_say_the_agreed_cap_in_money_and_about_an_estimate(host):
    from orkboard.realm import craft_tools

    art = _party(host, "art")
    craft_tools.set_taken(host.ideas.root(), art, {
        tid: {"cap": {"amount": "1.25", "currency": "USD"}} for tid in craft_tools.REGISTRY
    })
    got = stall(host, art)
    assert ware(got, "craft_tools", "openai-images")["price"] == {"money": "1.25 USD cap"}
    assert ware(got, "craft_tools", "elevenlabs-sound")["price"] == {"money": "about 1.25 USD cap"}


def test_maker_host_strings_shown_on_the_rug_never_say_harness(host, monkeypatch):
    from dataclasses import replace
    from orkboard.realm import craft_tools

    monkeypatch.setattr(craft_tools, "key", lambda _: None)
    art = _party(host, "art")
    tool = craft_tools.get("openai-images")
    reasons = []
    for changed in (tool, replace(tool, needs=("unavailable-making",)), replace(tool, official_api=False)):
        monkeypatch.setitem(craft_tools.REGISTRY, tool.id, changed)
        got = stall(host, art)
        reasons.append(ware(got, "craft_tools", tool.id)["why"])
        assert "harness" not in json.dumps(got).lower()
    assert reasons == ["no key on this computer", "its AI tool cannot make it", "no official API"]


def test_a_maker_take_needs_an_explicit_valid_cap_and_preserves_other_makers(host, monkeypatch):
    from orkboard.realm import craft_tools

    monkeypatch.setattr(craft_tools, "key", lambda _: "fake-maker-key")
    art = _party(host, "art")
    args = {"chair": art, "slot": "craft_tools", "value": "openai-images"}
    path = host.ideas.root() / ideas.TRACKS / f"{art}.md"
    before = path.read_text()
    for cap in (None, {}, {"amount": "0", "currency": "USD"}, {"amount": "-1", "currency": "USD"},
                {"amount": "NaN", "currency": "USD"}, {"amount": "2", "currency": "EUR"},
                {"amount": "no money", "currency": "USD"}):
        with pytest.raises(CommandError, match="maker.*cap"):
            host.command("ideas.stall_take", {**args, "cap": cap})
        assert path.read_text() == before
    cap = {"amount": "1.25", "currency": "USD"}
    got = host.command("ideas.stall_take", {**args, "cap": cap})
    assert ware(got["stall"], "craft_tools", "openai-images")["price"] == {"money": "1.25 USD cap"}
    host.command("ideas.stall_take", {**args, "value": "elevenlabs-sound", "cap": cap})
    assert set(craft_tools.taken(host.ideas.root(), art)) == {"openai-images", "elevenlabs-sound"}
    host.command("ideas.stall_take", {**args, "cap": {"amount": "2", "currency": "USD"}})
    assert craft_tools.taken(host.ideas.root(), art)["elevenlabs-sound"]["cap"] == cap


def test_a_maker_take_refuses_the_wrong_chair_and_a_missing_key(host, monkeypatch):
    from orkboard.realm import craft_tools

    monkeypatch.setattr(craft_tools, "key", lambda _: None)
    art, tech = _party(host, "art"), _party(host)
    args = {"slot": "craft_tools", "value": "openai-images", "cap": {"amount": "1", "currency": "USD"}}
    for chair in ("", tech):
        with pytest.raises(CommandError, match="not for this party"):
            host.command("ideas.stall_take", {**args, "chair": chair})
    with pytest.raises(CommandError, match="not here: no key"):
        host.command("ideas.stall_take", {**args, "chair": art})
    assert craft_tools.taken(host.ideas.root(), art) == {}


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


def test_a_web_apps_design_shelf_stars_the_orkmasters_pick_and_the_hand_never(host):
    _kind(host, "web")
    got = stall(host, _party(host, "design"))
    wares = shelf(got, "hero")["wares"]
    assert [w["id"] for w in wares] == [h.id for h in heroes.of("design")]
    assert [w["id"] for w in wares if w.get("star")] == ["dry-heur"]
    assert "star" not in card(got, "hero")


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


def test_a_games_art_has_no_shelf_and_liveops_has_no_card(host):
    _kind(host, "game")
    art = stall(host, _party(host, "art"))
    assert not any(s["slot"] == "hero" for s in art["shelves"]) and card(art, "hero")["yours"] == "dry-sprite"
    live = _party(host, "liveops")
    got = stall(host, live)
    assert not any(s["slot"] == "hero" for s in got["shelves"] + got["hand"])
    with pytest.raises(CommandError, match="This party has no hero"):
        host.command("ideas.stall_back", {"chair": live, "slot": "hero"})


@pytest.mark.parametrize("cut", sorted(heroes.CUT))
def test_a_cut_hero_is_said_once_and_the_page_and_table_stay(host, cut):
    root = host.ideas.root()
    craft = {"uni": "product", "dry": "design", "sh": "tech", "imp": "run"}[cut.split("-")[0]]
    party = _party(host, craft)
    page = root / ideas.TRACKS / f"{party}.md"
    page.write_text(page.read_text().replace("\n---\n", f"\nhero: {cut}\n---\n", 1), encoding="utf-8")
    table = root / "pages" / "tables" / f"{party}.md"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(f"---\nowner: board\nkind: table\nparty: {party}\nhero: {cut}\nlaid: 2026-01-01\nschema: 1\n---\n\n## Anywhere\n- A card — kept as laid\n", encoding="utf-8")
    before, table_before = page.read_bytes(), table.read_bytes()
    name, why = heroes.CUT[cut]
    first = stall(host, party)["say"]
    assert first.startswith(f"{name} was cut: {why}.") and "its craft's default, leads now." in first
    assert page.read_bytes() == before and table.read_bytes() == table_before
    got = stall(host, party)
    assert name not in got["say"] and table.read_bytes() == table_before
    assert goal_team.hero_of(root, party).id == heroes.default(craft).id
    assert [c["yours"] for c in got["hand"] if c["slot"] == "hero"] in ([heroes.default(craft).id], [] if craft != "product" else None)  # no hero card where no hero is offered
    host.ideas.__dict__.pop("_stall_before", None)
    got = stall(host, party)
    assert name not in got["say"] and page.read_bytes() == before and table.read_bytes() == table_before
    assert goal_team.hero_of(root, party).id == heroes.default(craft).id
    assert [c["yours"] for c in got["hand"] if c["slot"] == "hero"] in ([heroes.default(craft).id], [] if craft != "product" else None)  # no hero card where no hero is offered
