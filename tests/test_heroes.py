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


def test_the_catalog_is_the_specs_seventeen_in_order():
    assert list(heroes.HEROES) == ["uni-ost", "uni-jtbd", "uni-lean", "uni-shape", "dry-heur", "dry-diamond", "dry-atom", "dry-sprint", "sh-c4", "sh-ddd", "sh-xp", "sh-fit",
                                   "imp-slo", "imp-obs", "fairy-aarrr", "fairy-aso", "release"]
    assert len(heroes.HEROES) == 17 and all(k == h.id for k, h in heroes.HEROES.items())
    assert [h.id for h in heroes.of("tech")] == ["sh-c4", "sh-ddd", "sh-xp", "sh-fit"] and heroes.of("nowhere") == []
    assert heroes.get("sh-xp").name == "Spike Shaman" and heroes.get("nowhere") is None and heroes.get("") is None


def test_one_default_a_craft_and_places_only_on_the_others():
    crafts = {h.craft for h in heroes.HEROES.values()}
    assert crafts == {"product", "design", "tech", "run", "marketing", "release"} and crafts <= set(lens_rubrics.RUBRICS)
    for craft in crafts:
        assert [h.default for h in heroes.of(craft)].count(True) == 1 and heroes.default(craft).craft == craft
    assert heroes.default("liveops") is None
    assert {h.id for h in heroes.HEROES.values() if h.default} == {"uni-ost", "dry-heur", "sh-c4", "imp-slo", "fairy-aarrr", "release"}
    for h in heroes.HEROES.values():
        assert h.size in heroes.SIZES and h.layout in heroes.LAYOUTS and 1 <= h.decides <= 3 and 1 <= h.says_no <= 3
        assert h.name and h.school and h.flow
        if h.default:
            assert h.places == ()
        else:
            assert 3 <= len(h.places) <= 5 and all(n and a.endswith("?") for n, a in h.places)
            assert len({n for n, _a in h.places}) == len(h.places)
            assert h.framework and h.short and 4 <= len(h.aspects) <= 6
            ids = [a["id"] for a in h.aspects]
            assert len(set(ids)) == len(ids)
            for a in h.aspects:
                assert re.fullmatch(r"[a-z][a-z_]*", a["id"]) and a["name"] and a["ask"].endswith("?") and "signals" not in a
    assert heroes.get("sh-xp").places[0] == ("Red", "Which test fails, written before its code?") and heroes.get("dry-atom").layout == "rows"


def test_a_default_heros_frame_is_its_crafts_rubric_read_at_call_time(monkeypatch):
    for h in (x for x in heroes.HEROES.values() if x.default):
        r = lens_rubrics.RUBRICS[h.craft]
        assert (h.framework, h.short, h.aspects) == (r["framework"], r["short"], r["aspects"]) and h.aspects is r["aspects"]
    monkeypatch.setitem(lens_rubrics.RUBRICS, "tech", {**lens_rubrics.RUBRICS["tech"], "short": "changed"})
    assert heroes.get("sh-c4").short == "changed"


def test_the_crafts_of_the_catalog_are_the_ones_a_party_has():
    assert set(map_parts.MAPS) <= set(lens_rubrics.RUBRICS) and set(party_recipes.CRAFTS) <= set(lens_rubrics.RUBRICS)
    for craft in ("product", "design", "tech", "run", "marketing", "release"):
        assert party_recipes.craft_of(craft, "") == craft and map_parts.craft_of.__name__           # a recipe's craft is a RUBRICS key as it stands


def test_a_party_has_its_crafts_default_hero_until_one_is_taken(root):
    slug = _party(root, "tech")
    assert ideas.track_page(root, slug).get("hero") == "" and goal_team.hero_of(root, slug).id == "sh-c4"
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["hero"] == ""
    goal_team.set_hero(root, slug, "sh-xp")
    assert goal_team.hero_of(root, slug).id == "sh-xp" and ideas.track_page(root, slug).get("hero") == "sh-xp"
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["hero"] == "sh-xp"
    goal_team.set_hero(root, slug, "sh-c4")                                 # the craft's default writes the key away
    assert "hero" not in [k for k, _v in ideas.track_page(root, slug).meta] and goal_team.hero_of(root, slug).id == "sh-c4"


def test_taking_a_hero_keeps_every_other_key(root):
    slug = _party(root, "design")
    goal_team.set_team(root, slug, ["artist"], leader="product-designer")
    goal_team.set_tool(root, slug, "")
    before = ideas.track_page(root, slug)
    meta = dict(before.meta)
    goal_team.set_hero(root, slug, "dry-sprint")
    after = ideas.track_page(root, slug)
    assert dict(after.meta) == {**meta, "hero": "dry-sprint"} and after.title == before.title and after.sections == before.sections


def test_set_hero_refuses_a_hero_of_another_craft_an_unknown_one_and_releases(root):
    tech, release = _party(root, "tech"), _party(root, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "dry-atom")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, tech, "nowhere")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, release, "release")
    with pytest.raises(ValueError):
        goal_team.set_hero(root, "no-such-party", "sh-xp")
    assert goal_team.hero_of(root, tech).id == "sh-c4" and goal_team.hero_of(root, release).id == "release"


def test_a_kept_hero_of_another_craft_reads_as_the_default(root):
    slug = _party(root, "tech")
    page = ideas.track_page(root, slug)
    page.set("hero", "dry-atom")
    ideas._write(root / ideas.TRACKS / f"{slug}.md", page.text())
    assert goal_team.hero_of(root, slug).id == "sh-c4"
    page.set("hero", "gone")
    ideas._write(root / ideas.TRACKS / f"{slug}.md", page.text())
    assert goal_team.hero_of(root, slug).id == "sh-c4"


def test_a_party_with_no_craft_has_no_hero(root):
    assert goal_team.hero_of(root, ideas.add_track(root, "General")) is None


def test_the_rubric_follows_the_hero_and_today_s_callers_are_unchanged():
    xp = heroes.get("sh-xp")
    r = lens_rubrics.rubric("tech", xp)
    assert r["framework"] == xp.framework and r["short"] == xp.short and [a["id"] for a in r["aspects"]] == [a["id"] for a in xp.aspects]
    assert all(a["signals"] == () for a in r["aspects"]) and lens_rubrics.rubric("tech", "sh-xp") == r
    for same in (None, heroes.get("sh-c4"), "sh-c4", heroes.get("dry-atom"), "nowhere"):             # none, the default, another craft's, unknown: today's
        assert lens_rubrics.rubric("tech", same) is lens_rubrics.RUBRICS["tech"]
    assert lens_rubrics.rubric("tech") is lens_rubrics.RUBRICS["tech"] and lens_rubrics.rubric("", xp) is None
    assert lens_rubrics.prompt_lines("tech") == lens_rubrics.prompt_lines("tech", heroes.get("sh-c4"))


def test_the_prompt_and_the_scorecard_take_the_hero():
    lines = lens_rubrics.prompt_lines("tech", "sh-xp").split("\n")
    assert lines[0] == f"How a senior of tech reviews this map: {heroes.get('sh-xp').framework}." and lines[1].startswith("- test_first: Test first. ")
    assert len(lines) == 1 + len(heroes.get("sh-xp").aspects)
    card = lens_rubrics.scorecard("tech", {"at": "2026-01-01", "concerns": [{"aspect": "simple", "level": "alert"}]}, "sh-xp")
    assert [c["id"] for c in card] == [a["id"] for a in heroes.get("sh-xp").aspects]
    assert next(c for c in card if c["id"] == "simple")["state"] == "alert" and next(c for c in card if c["id"] == "refactor")["state"] == "clear"
    assert [c["id"] for c in lens_rubrics.scorecard("tech", {})] == ["modularity", "coupling", "hotspots", "testability", "safety"]


def test_the_words_are_in_the_glossary():
    assert [lexicon.term(k) for k in ("inventory", "hero.yours", "hero.yours_before", "hero.back_to_default", "hero.in_your_hand", "hero.what_leaves", "hero.lay_tables")] == [
        "Inventory", "Yours", "Yours before", "Back to default", "in your hand", "What leaves this computer", "Lay the tables"]
    assert lexicon.term("hero", many=True) == "heroes" and lexicon.term("hero.frame") == "frame"
