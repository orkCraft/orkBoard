"""Spec 59 part C, the phone (docs/specs/59-mixed-parties.md §7, §8 "C"): Chromium at 390 × 844 against the scene of tests/test_pwa_arena_browser.py. New party's library in one column, the mixed
first (*Mixed*, *One craft*, *Taskmaster alone*): a pick fills the seats and sends `preset`, a seat changed clears it; the Game's four builders' seats and *Concept* / *Build* / *Playtest*; a leader with
fewer seats (the alert line, *Save party* off); the stage switch's four heads (66 px) and its words whole at 390, a Game party's words and today's for another; an older host with no `stages` or
`presets` (the row of crafts as before); the service worker's version."""
from __future__ import annotations

import re
import copy
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.realm import library
from tests.test_pwa_arena_browser import ELF, OWN, SCENE, _scene, member  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _band, _called, _new_goal, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

GAME = {"lead": {"word": "Concept"}, "build": {"word": "Build", "seats": 4}, "check": {"word": "Playtest", "seats": 1}}


def hosted(monkeypatch, *, newer=True):
    """The host of spec 59 A answers `presets` and `stages` with the roles (`newer`), or an older one does not."""
    real = Stub.commands

    def commands(self):
        got = real(self)
        roles = got["ideas.roles"]

        def serve(a):
            out = roles(a)
            return {**out, "presets": library.presets(), "stages": library.stages()} if newer else out
        return {**got, "ideas.roles": serve}
    monkeypatch.setattr(Stub, "commands", commands)


async def _sheet(page):
    await _new_goal(page)
    sheet = page.get_by_role("dialog", name="New party")
    await sheet.wait_for(timeout=WAIT_MS)
    return sheet


@pytest.mark.asyncio
async def test_the_library_gives_the_mixed_parties_first_in_one_column(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        tiles = sheet.locator(".preset-tile")
        await tiles.first.wait_for(timeout=WAIT_MS)
        assert [await t.get_attribute("data-preset") for t in await tiles.all()] == ["game", "mobile-app", "website", "ideation", "release", "art", "engineering", "design", "data", "marketing", "product", "mixed"]
        assert [await g.get_attribute("aria-label") for g in await sheet.locator(".preset-group").all()] == ["Mixed", "One craft", "Taskmaster alone"]
        xs = {round((await t.bounding_box())["x"]) for t in await tiles.all()}
        assert len(xs) == 1                                                                     # one column
        for t in await tiles.all():
            assert (await t.bounding_box())["height"] >= 44
        game = sheet.locator('.preset-tile[data-preset="game"]')
        assert "Rules, levels, art and sound, played through" in await game.inner_text() and await game.locator("img").count() == 3          # its leader, its first builder, its first checker (spec 87 §5)
        await game.click()
        assert await sheet.locator(".party-line").first.inner_text() == \
            "Leads: Game designer · Builds: Grunt · Checks: Playtester"
        await sheet.get_by_label("What it is for").fill("A tower game.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game.", "craft": "design", "leader": "game-designer", "priority": "normal", "preset": "game",
                                                       "team": ["grunt", "playtester"], "every": []})
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_seat_changed_clears_the_preset_and_the_game_has_one_builders_seat(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        await sheet.locator('.preset-tile[data-preset="game"]').click()
        await sheet.locator('.party [data-change="team"]').click()
        builds = sheet.get_by_role("region", name="Builds")
        await builds.get_by_role("button").first.click()
        assert await builds.get_attribute("data-stage") == "Build"
        assert await builds.locator(".team-seat").count() == 1 and await builds.locator(".team-seat:not(.is-empty)").count() == 1
        assert "1 of 1" in await builds.inner_text() and "Build · 1 seat" in await builds.inner_text()
        assert await sheet.get_by_role("region", name="Leads").get_attribute("data-stage") == "Concept"
        assert await sheet.get_by_role("region", name="Checks").get_attribute("data-stage") == "Playtest"
        await sheet.get_by_role("button", name="Take out: Grunt").click()
        await sheet.get_by_role("button", name="Take in: Artist").click()                          # the one seat taken again by another
        await builds.get_by_role("button", name="Done").click()
        await sheet.get_by_label("What it is for").fill("A tower game, quiet.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game, quiet.", "craft": "design", "leader": "game-designer", "priority": "normal",
                                                       "team": ["playtester", "artist"], "every": []})
        sent = [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]
        assert "preset" not in sent


@pytest.mark.asyncio
async def test_a_party_made_before_with_more_than_a_seat_a_stage_says_so_and_is_saved_as_it_was(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        stub.own = [{"id": "p-1a2b3c4d", "name": "Wide web", "craft": "engineering", "leader": "architect", "team": ["grunt", "tester", "reviewer"], "every": [],
                     "own": [], "goals": 3, "projects": 2, "met": 2, "saved": "2026-10-20T10:00:00"}]
        sheet = await _sheet(page)
        chip = sheet.locator("[data-party=p-1a2b3c4d]")
        await chip.wait_for(timeout=WAIT_MS)
        await chip.get_by_role("button", name="Pick your party “Wide web”").click()
        await sheet.get_by_label("What it is for").fill("A wide one.")
        save = sheet.get_by_role("button", name="Save party")
        assert await save.is_enabled()                                                             # a party the person made before keeps its team
        await sheet.locator('.party [data-change="team"]').click()
        builds = sheet.get_by_role("region", name="Builds")
        await builds.get_by_role("button").first.click()
        assert await builds.locator(".party-over").inner_text() == "Implementation has 1 seat with Architect: take one out first."
        assert await save.is_enabled()
        await builds.get_by_role("button", name="Done").click()
        await save.click()
        assert await _called(stub, "ideas.goal_save", {"about": "A wide one.", "craft": "engineering", "leader": "architect", "priority": "normal", "party": "p-1a2b3c4d",
                                                       "team": ["grunt", "tester", "reviewer"], "every": []})


@pytest.mark.asyncio
async def test_the_stage_switch_shows_four_heads_in_66_px_and_the_party_s_words(fake_repo, monkeypatch):
    hosted(monkeypatch)
    goal = SCENE["map"]["goals"][0]
    goal["stages"] = copy.deepcopy(GAME)
    goal["party"] += [member({"slug": "levels", "name": "Levels"}, "build", ELF), member({"slug": "sound", "name": "Sound"}, "build", OWN)]
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        names = [await page.locator(f'.band[data-band="{k}"] .band__name').inner_text() for k in ("lead", "build", "check")]
        assert [n.lower() for n in names] == ["concept", "build", "playtest"]
        await _band(page, "build")
        faces = page.locator('.band[data-band="build"] .band__face')
        assert await faces.count() == 4
        boxes = [await f.locator(".ork-race__head").bounding_box() for f in await faces.all()]
        assert round(boxes[-1]["x"] + boxes[-1]["width"] - boxes[0]["x"]) == 66
        assert [round(b["x"] - boxes[0]["x"]) for b in boxes] == [0, 14, 28, 42]
        for key in ("lead", "build", "check"):                                               # the words whole, none cut
            word = page.locator(f'.band[data-band="{key}"] .band__name')
            assert await word.evaluate("e => e.scrollWidth <= e.clientWidth + 1 && e.getBoundingClientRect().right <= 390")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_an_older_host_says_today_s_words_and_keeps_the_row_of_crafts(fake_repo, monkeypatch):
    hosted(monkeypatch, newer=False)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        names = [await page.locator(f'.band[data-band="{k}"] .band__name').inner_text() for k in ("lead", "build", "check")]
        assert [n.lower() for n in names] == ["planning", "implementation", "checking"]
        sheet = await _sheet(page)
        assert await sheet.locator(".craft-tile").count() == 6 and await sheet.locator(".preset-tile").count() == 0
        await sheet.locator('.craft-tile[data-craft="design"]').click()
        await sheet.get_by_label("What it is for").fill("A design party.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert "preset" not in [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]


def test_the_service_worker_is_one_version_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 86
