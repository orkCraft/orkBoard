"""Spec 92 on the phone (docs/specs/92-running-and-the-team.md, decisions §108): Chromium at 390 × 844 against the stub of test_pwa_shell_browser.py with fake `ops.*` commands (test_pwa_ops38_browser.py)
and `ideas.party_presets` (the real presets of a mobile app, from realm/party_presets.py). The parties' sheet has an *Operations* row while no Team party exists
anywhere; Team is no party to make or to be offered since decisions §122.2 (spec 99 §1), but a Team party the person already has takes the row away and its field is today's Operations list, and a Team party in
another project leaves no row here; a project's running (Run) offers its recurring goals, ticked, and Save sends the ones kept; a recurring goal says how often it comes back. Targets 44 px, no sideways scroll."""
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
    """The phone's host with Operations, the presets of `kind` and, where `team` says so, a Team party the person has already (it makes the snapshot's `ops_team`): none can be made since decisions §122.2."""
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

        return {**got, "ideas.party_presets": presets_}
    monkeypatch.setattr(Stub, "commands", commands)


def rows(sheet):
    return sheet.locator(".where-row[data-goal]")


def a_team_party_here():
    """A Team party made before decisions §122.2 and kept (spec 99 §1: a party of theirs the project has stays): the Board holds it and the snapshot says it is here."""
    SCENE["map"]["goals"].append({**copy.deepcopy(SCENE["map"]["goals"][0]), "slug": "team", "title": "Team", "short": "Team", "ops": True, "leader": Stub.leader("product-manager"), "party": [], "team": [],
                                  "ideas": 0, "done": 0})
    TEAM["now"] = {"name": "project", "party": "team", "here": True}


@pytest.mark.asyncio
async def test_operations_are_among_the_parties_while_there_is_no_team_party_and_team_is_no_party_to_make_nor_to_be_offered(fake_repo, monkeypatch):
    with_team(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await sheet.locator('.where-row[data-goal="ops"]').wait_for(timeout=WAIT_MS)
        assert (await rows(sheet).all_inner_texts())[-1].split("\n")[0] == "Operations"
        assert await sheet.get_by_role("button", name="Make it a Team party").count() == 0                                  # Team goes for now: Operations stay the person's own list (decisions §122.2)
        await page.keyboard.press("Escape")
        new = await new_party(page)
        assert await new.locator('.preset-tile[data-preset="team"]').count() == 0 and await new.get_by_role("region", name="By craft").count() == 0       # no Team tile, in no group (spec 99 §1)
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_team_party_the_project_has_takes_the_operations_row_away_and_its_field_is_the_operations_list(fake_repo, monkeypatch):
    with_team(monkeypatch)
    a_team_party_here()
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await sheet.locator('.where-row[data-goal="team"]').wait_for(timeout=WAIT_MS)
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
async def test_with_a_team_party_in_another_project_there_is_no_operations_row_and_no_team_tile(fake_repo, monkeypatch):
    with_team(monkeypatch, team={"name": "harbor", "party": "team", "here": False})
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await rows(sheet).first.wait_for(timeout=WAIT_MS)
        assert await sheet.locator('.where-row[data-goal="ops"]').count() == 0 and await sheet.get_by_role("button", name="Make it a Team party").count() == 0
        assert await sheet.locator('.where-row[data-goal="team"]').count() == 0                                            # it is in harbor, not here
        await page.keyboard.press("Escape")
        new = await new_party(page)
        assert await new.locator('.preset-tile[data-preset="team"]').count() == 0                                           # Team is offered nowhere now (decisions §122.2): not greyed, not there
        assert await new.locator('.preset-tile[aria-pressed="true"]').get_attribute("data-preset") == "tech"


@pytest.mark.asyncio
async def test_a_run_party_offers_its_recurring_goals_ticked_and_save_sends_the_ones_kept(fake_repo, monkeypatch):
    with_team(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        new = await new_party(page)
        run = new.get_by_role("region", name="By stage of the project").locator('.preset-tile[data-preset="run"]')
        assert norm(await run.locator("b").text_content()) == "Run"                                                        # Run is the Live stage's party (spec 99 §1)
        assert await new.locator(".routines:visible").count() == 0                                                         # Tech proposes none
        await run.click()
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
        assert saved["routines"] == ["deps", "reviews"] and saved["proposal"] == "run" and saved["leader"] == "analyst"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_wikis_run_party_has_its_kinds_recurring_goals_and_another_press_ticks_afresh(fake_repo, monkeypatch):
    with_team(monkeypatch, kind="wiki")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        new = await new_party(page)
        last = new.get_by_role("region", name="By stage of the project").locator('.preset-tile[data-preset="run"]')
        assert norm(await last.locator("b").text_content()) == "Run"                                                        # a craft is one party in every kind: Run, with the wiki's recurring goals (no Upkeep since spec 99 §1)
        await last.click()
        box = new.get_by_role("region", name="Recurring goals")
        assert [await b.get_attribute("data-routine") for b in await box.locator("input").all()] == ["stale", "links", "sources"]
        await box.locator("input").first.uncheck()
        await new.locator('.preset-tile[data-preset="tech"]').click()
        assert await new.locator(".routines:visible").count() == 0
        await last.click()
        assert all([await b.is_checked() for b in await new.get_by_role("region", name="Recurring goals").locator("input").all()])        # pressed again: all ticked
