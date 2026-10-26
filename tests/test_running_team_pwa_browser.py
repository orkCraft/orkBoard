"""Spec 92 on the phone (docs/specs/92-running-and-the-team.md, decisions §108): Chromium at 390 × 844 against the stub of test_pwa_shell_browser.py with fake `ops.*` commands (test_pwa_ops38_browser.py)
and `ideas.party_presets` (the real presets of a mobile app, from realm/party_presets.py). The parties' sheet has an *Operations* row, with the line *Make it a Team party*, only while no Team party exists
anywhere; the line opens New party on Team; a Team party made takes the row away and its field is today's Operations list; Team is greyed with *Team is in <project>* once the person has one elsewhere; a
project's running (Run, Upkeep) offers its recurring goals, ticked, and Save sends the ones kept; a recurring goal says how often it comes back. Targets 44 px, no sideways scroll."""
from __future__ import annotations

import copy

import pytest

from orkboard.gui.board_host import BoardPhone
from orkboard.realm import party_presets
from tests.test_pwa_arena_browser import SCENE, _scene  # noqa: F401  (the scene fixture is autouse)
from tests.test_pwa_new_party_91_browser import MAKING, new_party, with_presets  # noqa: F401
from tests.test_pwa_ops38_browser import _ops  # noqa: F401  (the fake Operations are autouse)
from tests.test_pwa_party_tool_browser import TOOLS, with_tools  # noqa: F401
from tests.test_pwa_project_browser import calls  # noqa: F401
from tests.test_pwa_route_browser import norm  # noqa: F401
from tests.test_pwa_shell_browser import FAB, NO_SCROLL, WAIT_MS, Stub, _phone, _where  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

TEAM: dict = {"now": None}                                  # the snapshot's `ops_team`: None while there is no Team party


def with_team(monkeypatch, kind="mobile", team=None):
    """The phone's host with Operations, the presets of `kind` (Team greyed where `team` says it is) and a Team party saved here that makes the snapshot's `ops_team`."""
    TEAM["now"] = copy.deepcopy(team)
    with_presets(monkeypatch, kind=kind)
    snap = BoardPhone.phone_snapshot
    monkeypatch.setattr(BoardPhone, "phone_snapshot", staticmethod(lambda host: {**snap(host), "ops_team": copy.deepcopy(TEAM["now"])}))
    real = Stub.commands

    def commands(self):
        got = real(self)

        def presets_(a):
            self.calls.append(("ideas.party_presets", {k: v for k, v in a.items() if k not in ("link", "device")}))
            at = "" if TEAM["now"] is None else "here" if TEAM["now"]["here"] else TEAM["now"]["name"]
            return {"kind": {"id": kind, "words": "a mobile app"}, "presets": party_presets.listed(kind, at)}

        def goal_save(a):
            if a.get("proposal") != "team":
                return got["ideas.goal_save"](a)
            self.calls.append(("ideas.goal_save", {k: v for k, v in a.items() if k not in ("link", "device")}))
            leader = Stub.leader(a.get("leader"))
            SCENE["map"]["goals"].append({**copy.deepcopy(SCENE["map"]["goals"][0]), "slug": "team", "title": "Team", "short": "Team", "ops": True, "leader": leader, "party": [], "team": [],
                                          "ideas": 0, "done": 0})
            TEAM["now"] = {"name": "project", "party": "team", "here": True}
            return self.bump({"slug": "team"})
        return {**got, "ideas.party_presets": presets_, "ideas.goal_save": goal_save}
    monkeypatch.setattr(Stub, "commands", commands)


def rows(sheet):
    return sheet.locator(".where-row[data-goal]")


@pytest.mark.asyncio
async def test_operations_are_among_the_parties_with_a_line_while_there_is_no_team_party_and_the_line_opens_new_party_on_team(fake_repo, monkeypatch):
    with_team(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await sheet.locator('.where-row[data-goal="ops"]').wait_for(timeout=WAIT_MS)
        assert (await rows(sheet).all_inner_texts())[-1].split("\n")[0] == "Operations"
        line = sheet.get_by_role("button", name="Make it a Team party")
        assert await line.count() == 1 and (await line.bounding_box())["height"] >= 44
        await line.click()
        new = page.get_by_role("dialog", name="New party")
        await new.wait_for(timeout=WAIT_MS)
        await new.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
        assert await new.locator('.preset-tile[aria-pressed="true"]').get_attribute("data-preset") == "team"               # New party opens on Team
        crafts = new.get_by_role("region", name="By craft").locator(".preset-tile")
        assert [await c.get_attribute("data-preset") for c in await crafts.all()][-1] == "team"                           # the last of By craft
        note = new.locator(".teamnote")
        assert await note.is_visible() and "Team holds your Operations" in await note.inner_text() and "stay yours" in await note.inner_text()
        assert await new.locator(".pteam").is_hidden() or await new.locator(".pband:visible").count() == 0
        assert await new.locator(".routines:visible").count() == 0
        assert norm(await new.locator('[data-foot="agents"]').inner_text()) == "Your Operations stay yours: Team only shows them here"
        assert await new.get_by_label("Name", exact=True).get_attribute("placeholder") == "Team"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_team_party_made_takes_the_operations_row_away_and_its_field_is_the_operations_list(fake_repo, monkeypatch):
    with_team(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await sheet.get_by_role("button", name="Make it a Team party").click()
        new = page.get_by_role("dialog", name="New party")
        await new.locator(".teamnote").wait_for(timeout=WAIT_MS)
        await new.get_by_role("button", name="Save party").click()
        await new.wait_for(state="hidden", timeout=WAIT_MS)
        saved = [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]
        assert saved["proposal"] == "team" and saved["leader"] == "product-manager" and saved["team"] == [] and "routines" not in saved
        for _ in range(40):                                              # the Board and the snapshot are read a moment apart: the sheet is drawn as it opens
            sheet = await _where(page)
            await sheet.locator('.where-row[data-goal="team"]').wait_for(timeout=WAIT_MS)
            if not await sheet.locator('.where-row[data-goal="ops"]').count():
                break
            await page.keyboard.press("Escape")
            await sheet.wait_for(state="hidden", timeout=WAIT_MS)
            await page.wait_for_timeout(250)
        assert await sheet.locator('.where-row[data-goal="ops"]').count() == 0 and await sheet.get_by_role("button", name="Make it a Team party").count() == 0
        team = sheet.locator('.where-row[data-goal="team"]')
        assert "Your Operations" in await team.inner_text()                                                                # in place of k/n done
        await team.click()
        await page.locator(".ops-view[data-team=true]").wait_for(timeout=WAIT_MS)                                           # today's Operations list in the Team party's field
        await page.get_by_role("button", name="New…").wait_for(timeout=WAIT_MS)
        assert await page.get_by_role("button", name="Operations settings").count() == 1
        assert await page.locator(FAB).count() == 0 or not await page.locator(FAB).is_visible()                            # it holds no goals: nothing to add
        await page.get_by_role("button", name="About Team").click()                                                         # what it is, and Remove party: nothing of a party's seats and goals
        about = page.get_by_role("dialog", name="About this party")
        await about.wait_for(timeout=WAIT_MS)
        assert "Team holds your Operations" in await about.inner_text() and await about.get_by_role("button", name="Remove party").count() == 1
        assert await about.get_by_text("Checks on every goal").count() == 0
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_with_a_team_party_in_another_project_there_is_no_operations_row_and_team_is_greyed_with_where(fake_repo, monkeypatch):
    with_team(monkeypatch, team={"name": "harbor", "party": "team", "here": False})
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await rows(sheet).first.wait_for(timeout=WAIT_MS)
        assert await sheet.locator('.where-row[data-goal="ops"]').count() == 0 and await sheet.get_by_role("button", name="Make it a Team party").count() == 0
        assert await sheet.locator('.where-row[data-goal="team"]').count() == 0                                            # it is in harbor, not here
        await page.keyboard.press("Escape")
        new = await new_party(page)
        off = new.locator('.preset-tile[data-preset="team"]')
        assert await off.is_disabled() and await off.get_attribute("title") == "Team is in harbor"
        assert norm(await off.locator("small").inner_text()) == "Team is in harbor"
        await off.click(force=True)
        assert await new.locator('.preset-tile[aria-pressed="true"]').get_attribute("data-preset") == "mobile-build"       # a press on it picks nothing


@pytest.mark.asyncio
async def test_a_run_party_offers_its_recurring_goals_ticked_and_save_sends_the_ones_kept(fake_repo, monkeypatch):
    with_team(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        new = await new_party(page)
        stage = new.get_by_role("region", name="By stage of the project").locator(".preset-tile")
        last = stage.last
        assert (await last.get_attribute("data-preset"), norm(await last.locator("b").text_content())) == ("mobile-liveops", "Run")
        assert await new.locator(".routines:visible").count() == 0                                                         # Build proposes none
        await last.click()
        assert await new.get_by_label("Name", exact=True).get_attribute("placeholder") == "Run"
        box = new.get_by_role("region", name="Recurring goals")
        boxes = box.locator("input[type=checkbox]")
        assert [await b.get_attribute("data-routine") for b in await boxes.all()] == ["deps", "reviews", "crashes"]
        assert [norm(await li.inner_text()) for li in await box.locator("label").all()] == ["Weekly dependency check every week", "Read the new reviews every week", "Look at the crashes every week"]
        assert all([await b.is_checked() for b in await boxes.all()])
        for label in await box.locator("label").all():
            assert (await label.bounding_box())["height"] >= 44
        await boxes.nth(2).uncheck()
        await new.get_by_label("What it is for", exact=True).fill("Keep the app running")
        await new.get_by_role("button", name="Save party").click()
        await new.wait_for(state="hidden", timeout=WAIT_MS)
        saved = [c[1] for c in stub.calls if c[0] == "ideas.goal_save"][-1]
        assert saved["routines"] == ["deps", "reviews"] and saved["proposal"] == "mobile-liveops" and saved["leader"] == "product-manager"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_wikis_party_is_upkeep_with_its_recurring_goals_and_another_press_ticks_afresh(fake_repo, monkeypatch):
    with_team(monkeypatch, kind="wiki")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        new = await new_party(page)
        last = new.get_by_role("region", name="By stage of the project").locator(".preset-tile").last
        assert (await last.get_attribute("data-preset"), norm(await last.locator("b").text_content())) == ("wiki-liveops", "Upkeep")
        await last.click()
        box = new.get_by_role("region", name="Recurring goals")
        assert [await b.get_attribute("data-routine") for b in await box.locator("input").all()] == ["stale", "links", "sources"]
        await box.locator("input").first.uncheck()
        await new.locator('.preset-tile[data-preset="wiki-build"]').click()
        assert await new.locator(".routines:visible").count() == 0
        await last.click()
        assert all([await b.is_checked() for b in await new.get_by_role("region", name="Recurring goals").locator("input").all()])        # pressed again: all ticked
