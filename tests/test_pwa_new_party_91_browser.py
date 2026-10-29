"""Spec 91 part E on the phone (docs/specs/91-the-owners-list.md §7, decisions §107.5): Chromium at 390 × 844 against the proposals test's stub host with `ideas.party_presets` (the real presets of a mobile
app, from realm/party_presets.py) and `ideas.tools` with `makes`. New party is one sheet, the two halves of the desktop's dialog one step under the other: the presets first (*By stage of the project*,
*Your own party*: one party a craft, offered by its stage, since spec 99 §1), then the name, the size and the team by seats (*Leads*, *Does*, *Checks*). A preset pressed fills the bands; a size changes the seats and their tiers at once; a seat is taken out
and another put in from the band's sheet; a seat's AI tool is picked from groups that say what the role needs and why a tool cannot; Save party sends `tools`. Targets 44 px, no sideways scroll,
the service worker's version."""
from __future__ import annotations

import copy
import re

import pytest

from orkboard.realm import party_presets
from tests.test_pwa_arena_browser import SCENE, _about, _scene, _shot_to  # noqa: F401  (the scene fixture is autouse)
from tests.test_pwa_party_tool_browser import TOOLS, with_tools  # noqa: F401
from tests.test_pwa_project_browser import calls  # noqa: F401
from tests.test_pwa_route_browser import norm  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _new_goal, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

MAKING = copy.deepcopy(TOOLS)                     # Antigravity installed and ready, and the only tool that makes pictures
for row in MAKING["tools"]:
    row["makes"] = ["pictures"] if row["id"] == "agy" else []
    if row["id"] == "agy":
        row.update(ready=True, installed=True, signed_in=True)
MAKING["tools"].sort(key=lambda r: 0 if r["ready"] else 1)


def with_presets(monkeypatch, kind="mobile", **more):
    """The host of the phone's tool test plus `ideas.party_presets` (`kind`: what the project is) and tools that say what they make."""
    with_tools(monkeypatch, tools=MAKING, **more)
    real = Stub.commands

    def commands(self):
        got = real(self)

        def presets_(a):
            self.calls.append(("ideas.party_presets", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return {"kind": {"id": kind, "words": {"mobile": "a mobile app", "game": "a game"}.get(kind, "code")}, "presets": party_presets.listed(kind)}
        def goal_save(a):                                   # the seats' tools are kept with the party, as the host keeps them (spec 91 §6)
            r = got["ideas.goal_save"](a)
            for g in SCENE["map"]["goals"]:
                if g["slug"] == a.get("slug") and "tools" in a:
                    g["tools"] = dict(a["tools"])
            return r
        return {**got, "ideas.party_presets": presets_, "ideas.goal_save": goal_save}
    monkeypatch.setattr(Stub, "commands", commands)


async def new_party(page):
    await _new_goal(page)
    sheet = page.get_by_role("dialog", name="New party")
    await sheet.wait_for(timeout=WAIT_MS)
    await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
    await sheet.locator(".pseat[data-seat]").first.wait_for(timeout=WAIT_MS)
    return sheet


async def seats(sheet, band):
    return [await s.get_attribute("data-seat") for s in await sheet.locator(f'.pband[data-band="{band}"] .pseat[data-seat]').all()]


async def tier(sheet, role):
    src = await sheet.locator(f'.pseat[data-seat="{role}"] img.ork-race__head').get_attribute("src")
    return re.search(r"-(\w+?)(@2x)?\.png$", src).group(1)


async def size(sheet, word):
    await sheet.get_by_role("radiogroup", name="Size").get_by_role("radio", name=word).click()


async def press(sheet, preset):
    await sheet.locator(f'.preset-tile[data-preset="{preset}"]').click()


# -- one sheet, the presets first --------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_party_is_the_presets_first_and_then_the_team_by_seats_in_one_sheet(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        assert calls(stub, "ideas.party_presets") == [{}] and not calls(stub, "ideas.goal_save")
        nav = sheet.get_by_role("navigation", name="Presets")
        assert [await h.text_content() for h in await nav.locator("h4").all()] == ["By stage of the project", "Your own party"]                  # no *By craft*: the crafts are the stages' parties (spec 99 §1, decisions §122.5, §151.5)
        assert norm(await nav.locator(".presets__kind").inner_text()) == "For a mobile app: the Orkmaster knows what this project is"
        stages = nav.get_by_role("region", name="By stage of the project").locator(".preset-tile")
        assert [await c.get_attribute("data-preset") for c in await stages.all()] == ["product", "design", "tech", "release", "run", "marketing"]
        assert [norm(await c.locator("b").text_content()) for c in await stages.all()] == ["Product", "Design", "Tech", "Release", "Run", "Marketing"]
        own = nav.get_by_role("region", name="Your own party").locator(".preset-tile")
        assert norm(await own.locator("b").text_content()) == "Your own party" and norm(await own.locator("small").text_content()) == "Start from the Taskmaster and add who you need"
        assert [await c.get_attribute("data-preset") for c in await sheet.locator('.preset-tile[aria-pressed="true"]').all()] == ["tech"]       # the stage *Being made*'s party, Tech, is where it opens
        assert await sheet.get_by_label("Name", exact=True).input_value() == "" and await sheet.get_by_label("Name", exact=True).get_attribute("placeholder") == "Tech"
        group = sheet.get_by_role("radiogroup", name="Size")
        assert [norm(await b.inner_text()) for b in await group.get_by_role("radio").all()] == ["Lean", "Standard", "Full"]
        assert await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
        assert norm(await sheet.locator(".size-says").inner_text()).startswith("3 agents: the leader Veteran, the rest Seasoned")
        assert [await sheet.locator(f'[data-seats="{b}"]').inner_text() for b in ("lead", "build", "check")] == ["1 of 1 seats", "2 of 5 seats", "0 of 2 seats"]        # a squad of up to seven (spec 99 §1.3, decisions §151.1)
        assert [await sheet.get_by_role("region", name=b).locator("h3").text_content() for b in ("Leads", "Does", "Checks")] == ["Leads", "Does", "Checks"]
        assert (await seats(sheet, "lead"), await seats(sheet, "build"), await seats(sheet, "check")) == (["architect"], ["grunt", "tester"], [])
        assert norm(await sheet.locator('[data-free="check"]').first.inner_text()).endswith("Add a checker")
        assert norm(await sheet.locator('[data-foot="agents"]').inner_text()) == "3 agents · a task goes to the one who does its kind of work, the Grunt fills in"
        assert await sheet.get_by_role("button", name="Save party").is_enabled()
        for locator in (sheet.locator(".preset-tile").first, sheet.locator(".pseat__x").first, sheet.locator('[data-seat-tool="grunt"]'), sheet.locator('[data-free="check"]').first,
                        group.get_by_role("radio", name="Lean"), sheet.get_by_role("button", name="Save party")):
            box = await locator.bounding_box()
            assert box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= 390, await locator.inner_html()
        # the presets come first: the team is under them
        assert (await nav.bounding_box())["y"] < (await sheet.locator(".pteam").bounding_box())["y"]
        await _shot_to(page, "phone-new-party-91")
        assert await page.evaluate(NO_SCROLL) and await sheet.evaluate("(d) => d.scrollWidth <= d.clientWidth")


@pytest.mark.asyncio
async def test_a_stage_preset_fills_the_bands_a_size_changes_seats_and_tiers_at_once_and_a_seat_is_swapped_from_the_bands_sheet(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        await press(sheet, "design")
        assert await sheet.locator('.preset-tile[aria-pressed="true"]').get_attribute("data-preset") == "design"
        assert (await seats(sheet, "lead"), await seats(sheet, "build")) == (["product-designer"], ["ui-kit", "artist", "copywriter"]) and await sheet.get_by_label("Name", exact=True).get_attribute("placeholder") == "Design"
        await sheet.get_by_label("Name", exact=True).fill("Our first look")
        await press(sheet, "product")
        assert await seats(sheet, "lead") == ["product-manager"] and await sheet.get_by_label("Name", exact=True).input_value() == "Our first look"       # a name the person typed stays
        await press(sheet, "tech")
        await size(sheet, "Full")
        assert (await seats(sheet, "build"), await seats(sheet, "check")) == (["grunt", "tester"], ["reviewer", "security-reviewer"])
        assert (await tier(sheet, "architect"), await tier(sheet, "grunt"), await tier(sheet, "reviewer")) == ("elder", "warrior", "elder")
        assert norm(await sheet.locator(".size-says").inner_text()).startswith("5 agents, Seasoned and up") and norm(await sheet.locator('[data-foot="agents"]').inner_text()).startswith("5 agents ·")
        await size(sheet, "Lean")
        assert (await seats(sheet, "build"), await seats(sheet, "check")) == ([], []) and await tier(sheet, "architect") == "warrior"
        assert norm(await sheet.locator(".size-says").inner_text()).startswith("One agent, Seasoned")
        await size(sheet, "Standard")
        assert await seats(sheet, "build") == ["grunt", "tester"] and await tier(sheet, "architect") == "elder" and await tier(sheet, "grunt") == "warrior"
        # take Grunt out, put another in from the band's sheet
        await sheet.get_by_role("button", name="Remove Grunt from the party").click()
        assert await seats(sheet, "build") == ["tester"] and await sheet.locator(".preset-tile[aria-pressed=true]").count() == 0
        await sheet.locator('[data-free="build"]').first.click()
        roles_sheet = page.get_by_role("dialog", name="Add a member")
        await roles_sheet.wait_for(timeout=WAIT_MS)
        rows = roles_sheet.locator(".team-row")
        assert 1 <= await rows.count() <= 6 and await roles_sheet.get_by_role("button", name="More roles").count() == 1
        assert [await r.get_attribute("data-agent") for r in (await rows.all())[:1]] == ["grunt"]                                # the preset's candidates first
        assert await roles_sheet.locator('[data-agent="architect"]').count() == 0 and await roles_sheet.locator('[data-agent="tester"]').count() == 0     # the leader and the seated are not offered
        assert norm(await roles_sheet.locator('[data-agent="artist"] .pseat__needs').inner_text()) == "needs pictures"
        await roles_sheet.locator('[data-agent="artist"]').click()
        assert await seats(sheet, "build") == ["tester", "artist"] and await sheet.locator('[data-free="build"]').count() == 3        # of five seats
        assert norm(await sheet.locator('.pseat[data-seat="artist"] .pseat__needs').inner_text()) == "needs pictures"
        await sheet.locator('[data-free="check"]').first.click()
        checks_sheet = page.get_by_role("dialog", name="Add a checker")
        await checks_sheet.locator('[data-agent="accessibility-reviewer"]').click()
        assert await seats(sheet, "check") == ["accessibility-reviewer"]
        await size(sheet, "Lean")
        await size(sheet, "Full")
        assert (await seats(sheet, "build"), await seats(sheet, "check")) == (["tester", "artist"], ["accessibility-reviewer"])         # the seats the person chose come back with the size
        await sheet.get_by_role("button", name="Remove Architect from the party").click()
        assert await seats(sheet, "lead") == ["taskmaster"]
        await press(sheet, "mixed")
        assert (await seats(sheet, "lead"), await seats(sheet, "build"), await seats(sheet, "check")) == (["taskmaster"], [], []) and await sheet.locator('[data-free="lead"]').count() == 1


# -- a seat's AI tool --------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_artists_tool_is_antigravity_the_picker_groups_the_reasons_and_the_payload_carries_tools(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        await sheet.get_by_role("button", name="Remove Grunt from the party").click()
        await sheet.get_by_role("button", name="Remove Tester from the party").click()                                          # the Artist is the first who does: Seasoned, as a size gives it
        await sheet.locator('[data-free="build"]').first.click()
        await page.get_by_role("dialog", name="Add a member").locator('[data-agent="artist"]').click()
        btn = sheet.locator('[data-seat-tool="artist"]')
        assert norm(await btn.inner_text()) == "Party's tool · Claude Code" and await btn.get_attribute("aria-label") == "Its AI tool for Artist: Party's tool · Claude Code"
        assert (await btn.bounding_box())["height"] >= 44
        await btn.click()
        picker = page.get_by_role("dialog", name="Its AI tool for Artist")
        await picker.wait_for(timeout=WAIT_MS)
        rows = picker.locator(".tool-row")
        assert norm(await rows.first.inner_text()) == "The party's tool (Claude Code)" and await rows.first.get_attribute("aria-pressed") == "true"
        can = picker.locator('[data-group="can"]')
        assert await can.locator("h4").text_content() == "Can do what Artist needs"
        assert [await r.get_attribute("data-tool") for r in await can.locator(".tool-row").all()] == ["agy"]
        assert "Pictures, code and text" in norm(await can.inner_text()) and norm(await can.locator("[data-experimental]").inner_text()) == "experimental"
        cannot = picker.locator('[data-group="cannot"]')
        assert await cannot.locator("h4").text_content() == "Cannot make pictures"
        got = {await r.get_attribute("data-tool"): norm(await r.inner_text()) for r in await cannot.locator(".tool-row").all()}
        assert set(got) == {"claude", "codex", "pi", "cursor", "hermes"} and "draws no pictures" in got["claude"] and "its Seasoned model" in got["claude"] and "runs its own model" in got["pi"]
        assert norm(await picker.locator(".tool-foot").inner_text()) == "The tier comes from the party's size. Each tool runs its own model for it."
        assert await cannot.locator('[data-tool="hermes"]').is_disabled()                                                       # not installed: shown, not taken
        for r in await picker.locator(".tool-row:not([disabled])").all():
            assert (await r.bounding_box())["height"] >= 44
        await can.locator('[data-tool="agy"]').click()
        assert norm(await btn.inner_text()) == "Antigravity"
        await sheet.get_by_label("What it is for").fill("Pictures for the store.")
        await sheet.get_by_role("button", name="Save party").click()
        await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["leader"] == "architect" and sent["team"] == ["artist"] and sent["size"] == "standard" and sent["tools"] == {"artist": "agy"} and "tool" not in sent


async def _called(stub, name, n=1):
    import asyncio
    for _ in range(200):
        if len(calls(stub, name)) >= n:
            return
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_a_role_that_needs_sound_has_no_tool_that_can_and_every_tool_may_still_be_picked(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        await sheet.get_by_role("button", name="Remove Grunt from the party").click()
        await sheet.locator('[data-free="build"]').first.click()
        roles_sheet = page.get_by_role("dialog", name="Add a member")
        await roles_sheet.get_by_role("button", name="More roles").click()
        await roles_sheet.locator('[data-agent="sound-designer"]').click()
        await sheet.locator('[data-seat-tool="sound-designer"]').click()
        picker = page.get_by_role("dialog", name="Its AI tool for Sound designer")
        await picker.wait_for(timeout=WAIT_MS)
        assert norm(await picker.locator("[data-none]").inner_text()) == "No AI tool here makes sound: this seat writes it as code or a brief"
        assert await picker.locator('[data-group="can"] .tool-row').count() == 0
        cannot = picker.locator('[data-group="cannot"]')
        assert await cannot.locator("h4").text_content() == "Cannot make sound" and await cannot.locator(".tool-row").count() == 6
        assert "makes no sound" in norm(await cannot.locator('[data-tool="agy"]').inner_text())
        await cannot.locator('[data-tool="codex"]').click()                                                                     # the person decides
        assert norm(await sheet.locator('[data-seat-tool="sound-designer"]').inner_text()) == "Codex"
        await sheet.get_by_label("What it is for").fill("Sounds.")
        await sheet.get_by_role("button", name="Save party").click()
        await _called(stub, "ideas.goal_save")
        assert calls(stub, "ideas.goal_save")[-1]["tools"] == {"sound-designer": "codex"}


@pytest.mark.asyncio
async def test_save_party_sends_the_leader_the_team_the_size_the_partys_tool_and_the_recipe(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        await press(sheet, "design")
        await size(sheet, "Full")
        await sheet.locator('[data-sec="tool"] select').select_option("codex")
        await sheet.locator('[data-seat-tool="ui-kit"]').click()
        picker = page.get_by_role("dialog", name="Its AI tool for Design system designer")
        assert norm(await picker.locator(".tool-row").first.inner_text()) == "The party's tool (Codex)"
        await picker.locator('[data-tool="codex"]').click()                                                                      # the party's tool by name is still the party's
        await sheet.get_by_label("What it is for").fill("Draw the app before it is built.")
        await sheet.get_by_role("button", name="Save party").click()
        await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert "title" not in sent and sent["about"] == "Draw the app before it is built." and sent["leader"] == "product-designer" and sent["team"] == ["ui-kit", "artist", "copywriter", "accessibility-reviewer"]
        assert sent["size"] == "full" and sent["tool"] == "codex" and sent["proposal"] == "design" and "tools" not in sent and sent["priority"] == "normal"


@pytest.mark.asyncio
async def test_about_this_party_has_each_members_ai_tool_and_a_pick_saves_the_seats_tools_at_once(fake_repo, monkeypatch):
    with_presets(monkeypatch)
    SCENE["map"]["goals"][0]["tool"] = "codex"
    SCENE["map"]["goals"][0]["tools"] = {"backend": "claude"}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        sec = about.locator('[data-sec="The party"]')
        backend = sec.locator('[data-seat-tool="backend"]')
        await backend.wait_for(timeout=WAIT_MS)
        assert norm(await backend.inner_text()) == "Claude Code" and (await backend.bounding_box())["height"] >= 44
        assert await sec.locator('[data-seat-tool="taskmaster"]').count() == 0
        screens = sec.locator('[data-seat-tool="screens"]')
        assert norm(await screens.inner_text()) == "Party's tool · Codex"
        await screens.click()
        picker = page.get_by_role("dialog", name="Its AI tool for Screens")
        await picker.wait_for(timeout=WAIT_MS)
        assert norm(await picker.locator(".tool-row").first.inner_text()) == "The party's tool (Codex)"
        await picker.locator('[data-group="can"] [data-tool="pi"]').click()
        await _called(stub, "ideas.goal_save")
        assert calls(stub, "ideas.goal_save")[-1] == {"slug": "passkey", "tools": {"backend": "claude", "screens": "pi"}}
        await page.wait_for_function("() => document.querySelector('dialog[aria-label=\"About this party\"] [data-seat-tool=\"screens\"]')?.textContent.includes('pi')")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_preset_pressed_and_nothing_typed_is_saved_under_the_presets_name_and_a_line_alone_leaves_the_name_to_the_taskmaster(fake_repo, monkeypatch):
    with_presets(monkeypatch, refuse="held by the test")                                       # a save is recorded and refused: the stub makes no slug of a party with no words
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await new_party(page)
        await press(sheet, "design")
        save = sheet.get_by_role("button", name="Save party")
        assert await save.is_enabled()                                                          # a preset is a name already
        await save.click()
        await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["title"] == "Design" and sent["about"] == "" and sent["leader"] == "product-designer" and sent["proposal"] == "design"
        await sheet.get_by_label("What it is for").fill("Screens first.")
        await save.click()
        await _called(stub, "ideas.goal_save", 2)
        assert "title" not in calls(stub, "ideas.goal_save")[-1]                                # the Taskmaster names a party that has only what it is for


@pytest.mark.asyncio
async def test_a_host_without_the_command_has_the_librarys_stages_and_crafts(fake_repo, monkeypatch):
    with_tools(monkeypatch, tools=MAKING)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _new_goal(page)
        sheet = page.get_by_role("dialog", name="New party")
        await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
        assert len(await sheet.locator(".preset-tile").all()) >= 5
        assert await sheet.locator(".presets__kind").count() == 1                                                               # the kind is the Map's


def test_the_service_workers_version_and_its_files():
    from orkboard.gui import pwa
    sw = (pwa.ROOT / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v103"' in sw
    for name in ("shell-party-new.js", "shell-party-presets.js", "shell-party-seats.js", "shell-party-model.js", "shell-seat-tool.js", "party.css"):
        assert f'"{name}"' in sw and (pwa.ROOT / name).is_file()
    assert '<link rel="stylesheet" href="party.css">' in (pwa.ROOT / "index.html").read_text(encoding="utf-8")
