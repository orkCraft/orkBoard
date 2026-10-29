"""Spec 59 part C, the phone (docs/specs/59-mixed-parties.md §7, §8 "C"), in the sheet of spec 91 §7: Chromium at 390 × 844 against the scene of tests/test_pwa_arena_browser.py. New party's presets in one column
(*By stage of the project*, *By craft*, *Your own party*; this host reads a project of code: its parties by craft, Product, Design, Tech, Release, Run and Marketing, under the stage that offers them
(decisions §122.5, §151.5, spec 99 §1), the Taskmaster alone, and the Game, the Mobile app and the Website as crafts of their own, as the stub offers them): a pick fills the seats and sends `preset`, a seat
changed clears it; the Game's five builders' seats and two checkers' (a party's squad, decisions §151.1, §169.2) and *Concept* / *Build* / *Playtest*; a party made before shown over its seats; the stage switch's four heads (66 px) and its words whole at 390, a Game party's words and today's for another; an older host with no `stages` or `presets` (the crafts' parties as before); the service worker's version."""
from __future__ import annotations

import re
import copy
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.realm import library, party_presets
from tests.test_pwa_arena_browser import ELF, OWN, SCENE, _scene, member  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _band, _called, _new_goal, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

GAME = {"lead": {"word": "Concept"}, "build": {"word": "Build", "seats": 4}, "check": {"word": "Playtest", "seats": 1}}


def legacy(pid):
    """The library's mixed party `pid` (the Game, the Mobile app, the Website) as a craft's preset row: this stub offers them so that their leaders can be picked (spec 91 §7 has the stages of a kind instead)."""
    p = next(p for p in library.presets() if p["id"] == pid)
    return {"id": pid, "name": p["name"], "line": p["line"], "group": "craft", "stage": "", "craft": p["craft"], "recipe": "", "whole": False, "leader": p["lead"], "build": p["build"], "check": p["check"], "sizes": {}}


def hosted(monkeypatch, *, newer=True):
    """The host of spec 59 A answers `presets` and `stages` with the roles (`newer`), or an older one does not; and `ideas.party_presets` (a project of code, and the library's Game, Mobile app and Website)."""
    real = Stub.commands

    def commands(self):
        got = real(self)
        roles = got["ideas.roles"]

        def serve(a):
            out = roles(a)
            return {**out, "presets": library.presets(), "stages": library.stages()} if newer else out

        def presets_(a):
            self.calls.append(("ideas.party_presets", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return {"kind": {"id": "code", "words": "code"}, "presets": [*party_presets.listed("code"), legacy("game"), legacy("mobile-app"), legacy("website")]}
        older = {"ideas.party_presets": lambda a: {"error": "Unknown command"}}          # the real host answers the command, so an older one is told so: the page reads the roles' crafts instead
        return {**got, "ideas.roles": serve, **({"ideas.party_presets": presets_} if newer else older)}
    monkeypatch.setattr(Stub, "commands", commands)


async def _sheet(page):
    await _new_goal(page)
    sheet = page.get_by_role("dialog", name="New party")
    await sheet.wait_for(timeout=WAIT_MS)
    await sheet.locator(".pseat[data-seat]").first.wait_for(timeout=WAIT_MS)
    return sheet


async def _seats(sheet, band):
    return [await s.get_attribute("data-seat") for s in await sheet.locator(f'.pband[data-band="{band}"] .pseat[data-seat]').all()]


@pytest.mark.asyncio
async def test_the_library_gives_the_stages_then_the_crafts_then_the_taskmaster_alone_in_one_column(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        tiles = sheet.locator(".preset-tile")
        assert [await t.get_attribute("data-preset") for t in await tiles.all()] == ["product", "design", "tech", "release", "run", "marketing", "game", "mobile-app", "website", "mixed"]        # the crafts of a project of code (decisions §122.5, §151.5), not the stages of before
        assert [await g.get_attribute("aria-label") for g in await sheet.locator(".preset-group").all()] == ["By stage of the project", "By craft", "Your own party"]
        stages = sheet.locator('.preset-group.is-stage .preset-tile')
        xs = {round((await t.bounding_box())["x"]) for t in await stages.all()}
        assert len(xs) == 1                                                                     # one column
        for t in await tiles.all():
            assert (await t.bounding_box())["height"] >= 44
        game = sheet.locator('.preset-tile[data-preset="game"]')
        await game.click()
        assert (await _seats(sheet, "lead"), await _seats(sheet, "build"), await _seats(sheet, "check")) == (
            ["game-designer"], ["grunt", "artist", "level-designer", "sound-designer"], ["playtester"])         # its leader, its builders, its checker: a squad of up to five who do and two who check (decisions §151.1, §169.2)
        await sheet.get_by_label("What it is for").fill("A tower game.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game.", "craft": "design", "leader": "game-designer", "priority": "normal", "preset": "game",
                                                       "team": ["grunt", "artist", "level-designer", "sound-designer", "playtester"], "every": []})
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_seat_changed_clears_the_preset_and_the_game_has_one_builders_seat(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        await sheet.locator('.preset-tile[data-preset="game"]').click()
        builds = sheet.get_by_role("region", name="Does")
        assert await builds.get_attribute("data-stage") == "Build"
        assert await builds.locator(".team-seat").count() == 1 and await builds.locator(".pseat[data-seat]").count() == 4 and await builds.locator("[data-free]").count() == 1      # five seats (decisions §151.1, §169.2): four taken, one free
        assert "4 of 5 seats" in await builds.inner_text()
        assert await sheet.get_by_role("region", name="Leads").get_attribute("data-stage") == "Concept"
        assert await sheet.get_by_role("region", name="Checks").get_attribute("data-stage") == "Playtest"
        await sheet.get_by_role("button", name="Remove Grunt from the party").click()
        await sheet.locator('[data-free="build"]').first.click()                                 # two free seats: one taken again by another
        await page.get_by_role("dialog", name="Add a member").locator('[data-agent="animator"]').click()
        await sheet.get_by_label("What it is for").fill("A tower game, quiet.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game, quiet.", "craft": "design", "leader": "game-designer", "priority": "normal",
                                                       "team": ["artist", "level-designer", "sound-designer", "playtester", "animator"], "every": []})
        sent = [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]
        assert "preset" not in sent


@pytest.mark.asyncio
async def test_a_party_made_before_with_more_than_a_seat_a_stage_says_so_and_is_saved_as_it_was(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        team = ["grunt", "tester", "reviewer", "security-reviewer", "accessibility-reviewer"]          # three who check: a squad has two seats to check (decisions §151.1, §169.2; it had one a stage before)
        stub.own = [{"id": "p-1a2b3c4d", "name": "Wide web", "craft": "engineering", "leader": "architect", "team": team, "every": [],
                     "own": [], "goals": 3, "projects": 2, "met": 2, "saved": "2026-10-20T10:00:00"}]
        sheet = await _sheet(page)
        chip = sheet.locator("[data-party=p-1a2b3c4d]")
        await chip.wait_for(timeout=WAIT_MS)
        await chip.get_by_role("button", name="Pick your party “Wide web”").click()
        await sheet.get_by_label("What it is for").fill("A wide one.")
        save = sheet.get_by_role("button", name="Save party")
        assert await save.is_enabled()                                                             # a party the person made before keeps its team
        checks = sheet.get_by_role("region", name="Checks")
        assert await checks.locator(".party-over").inner_text() == "Checking has 2 seats with Architect: take one out first."
        assert await checks.locator(".pseat__head.is-over").count() == 1 and "3 of 2 seats" in await checks.inner_text()
        assert await sheet.get_by_role("region", name="Does").locator(".party-over").count() == 0
        assert await save.is_enabled()
        await save.click()
        assert await _called(stub, "ideas.goal_save", {"about": "A wide one.", "craft": "engineering", "leader": "architect", "priority": "normal", "party": "p-1a2b3c4d",
                                                       "team": team, "every": []})


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
        await _new_goal(page)
        sheet = page.get_by_role("dialog", name="New party")
        await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
        ids = [await t.get_attribute("data-preset") for t in await sheet.locator(".preset-tile").all()]
        assert [i for i in ids if i in ("engineering", "design", "data", "marketing", "product")] == ["engineering", "design", "data", "marketing", "product"]       # the crafts' parties stay
        await sheet.locator('.preset-tile[data-preset="design"]').click()
        await sheet.get_by_label("What it is for").fill("A design party.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert "preset" not in [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]


def test_the_service_worker_is_one_version_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 86
