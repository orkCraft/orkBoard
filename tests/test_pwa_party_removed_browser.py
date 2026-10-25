"""Spec 80 part C, the phone: a party removed (docs/specs/80-a-party-removed.md §0, §3, §5, §6): Chromium at 390 × 844 against the world of tests/test_pwa_route_browser.py (Passkey, Ideation, Website) with a General party.
*Remove party* stands at the foot of the party's sheet (About this party), never in General's; it opens a sheet with 44 px choices (*Move its k goals to General and remove* first, *Remove the party and its k goals*
in the danger colour, *Cancel*; a party with no goal says *It has no goals* and asks *Remove* / *Cancel*); *move* and *drop* send `ideas.track_drop` and the toast says what happened; the host's refusal is said in the
question, which stays; the removed party that was shown falls back to General; no sideways scroll; the service worker's version."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import OWN, SCENE, _about, _scene, node  # noqa: F401
from tests.test_pwa_route_browser import a_party, world  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _called, _phone, _pick_goal

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

HOST: dict = {}


def removable(monkeypatch, refuse=""):
    """The route tests' world with a General party; `ideas.track_drop` answers as the host does (the party and its goals gone, or its goals in General), or refuses with `refuse`."""
    world(monkeypatch, release=False)
    SCENE["map"]["goals"].append(a_party("general", "General", {"slug": "gen-lead", "name": "Gen lead"}, [({"slug": "gen-lead", "name": "Gen lead"}, "lead", OWN)], types=[]))
    HOST.clear()
    HOST["refuse"] = refuse
    real = Stub.commands

    def commands(self):
        def drop(a):
            a = {k: v for k, v in a.items() if k not in ("link", "device")}
            self.calls.append(("ideas.track_drop", dict(a)))
            if HOST["refuse"]:
                return {"error": HOST["refuse"]}
            slug, mine = a["slug"], [n for n in SCENE["map"]["nodes"] if n["goal"] == a["slug"]]
            title = next(g["title"] for g in SCENE["map"]["goals"] if g["slug"] == slug)
            SCENE["map"]["goals"] = [g for g in SCENE["map"]["goals"] if g["slug"] != slug]
            if a.get("goals") == "drop":
                SCENE["map"]["nodes"] = [n for n in SCENE["map"]["nodes"] if n["goal"] != slug]
            else:
                for n in mine:
                    n["goal"] = "general"
            self.bump({})
            return {"ok": True, "moved": len(mine) if a.get("goals") != "drop" else 0, "dropped": len(mine) if a.get("goals") == "drop" else 0, "title": title}
        return {**real(self), "ideas.track_drop": drop}
    monkeypatch.setattr(Stub, "commands", commands)


def goals_of(slug):
    return len([n for n in SCENE["map"]["nodes"] if n["goal"] == slug])


async def _ask(page, slug):
    """The party shown, its sheet, *Remove party*, and the question it opens."""
    if slug != "passkey":
        await _pick_goal(page, slug)
    about = await _about(page)
    await about.get_by_role("button", name="Remove party").click()
    ask = page.locator("dialog.remove[open]")
    await ask.wait_for(timeout=WAIT_MS)
    return ask


@pytest.mark.asyncio
async def test_remove_party_is_at_the_foot_of_the_sheet_and_general_has_none(fake_repo, monkeypatch):
    removable(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        remove = about.get_by_role("button", name="Remove party")
        assert await remove.count() == 1 and "danger" in await remove.get_attribute("class")
        assert (await remove.bounding_box())["height"] >= 44
        last = await about.locator(".sheet-in > .party-about > *").last.get_attribute("class")
        assert "party-about__remove" in last                                                                              # at the foot
        await page.keyboard.press("Escape")
        await _pick_goal(page, "general")
        about = await _about(page)
        assert await about.get_by_role("button", name="Edit the party").count() == 1
        assert await about.get_by_role("button", name="Remove party").count() == 0                                       # General stays


@pytest.mark.asyncio
async def test_the_question_has_44px_choices_and_move_is_first_and_default(fake_repo, monkeypatch):
    removable(monkeypatch)
    k = goals_of("passkey")
    assert k > 1
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        ask = await _ask(page, "passkey")
        assert await ask.get_attribute("aria-label") == "Remove Sign in with a passkey?" or await ask.get_attribute("aria-label") == f"Remove {SCENE['map']['goals'][0]['title']}?"
        buttons = ask.locator(".remove-ask .ork-btn")
        assert [(await b.inner_text()).strip() for b in await buttons.all()] == [f"Move its {k} goals to General and remove", f"Remove the party and its {k} goals", "Cancel"]
        assert [await b.get_attribute("data-act") for b in await buttons.all()] == ["remove-move", "remove-drop", "remove-cancel"]
        assert "primary" in await buttons.nth(0).get_attribute("class") and "danger" in await buttons.nth(1).get_attribute("class")
        for b in await buttons.all():
            assert (await b.bounding_box())["height"] >= 44
        assert await page.evaluate(NO_SCROLL)
        await buttons.nth(2).click()                                                                                       # Cancel: nothing is sent
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        assert not [c for c in stub.calls if c[0] == "ideas.track_drop"] and goals_of("passkey") == k


@pytest.mark.asyncio
async def test_move_sends_the_command_says_the_toast_and_the_shown_party_falls_back_to_general(fake_repo, monkeypatch):
    removable(monkeypatch)
    k = goals_of("passkey")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        title = await page.locator(".partydeck").first.get_attribute("aria-label")
        assert "Parties:" in title
        ask = await _ask(page, "passkey")
        await ask.locator('[data-act="remove-move"]').click()
        assert await _called(stub, "ideas.track_drop", {"slug": "passkey", "goals": "move"})
        await page.locator(".flash", has_text=f"removed · {k} goals moved to General").first.wait_for(timeout=WAIT_MS)
        await page.locator('.partydeck[data-goal="general"]').wait_for(timeout=WAIT_MS)                                    # General is shown now
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        sheet = page.get_by_role("dialog", name="Parties")
        await page.locator(".partydeck").first.click()
        await sheet.wait_for(timeout=WAIT_MS)
        assert await sheet.locator('.where-row[data-goal="passkey"]').count() == 0 and await sheet.locator('.where-row[data-goal="general"]').count() == 1
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_drop_sends_the_command_and_the_toast_says_the_goals_removed(fake_repo, monkeypatch):
    removable(monkeypatch)
    k = goals_of("passkey")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        ask = await _ask(page, "passkey")
        await ask.locator('[data-act="remove-drop"]').click()
        assert await _called(stub, "ideas.track_drop", {"slug": "passkey", "goals": "drop"})
        await page.locator(".flash", has_text=f"removed · {k} goals removed").first.wait_for(timeout=WAIT_MS)
        await page.locator('.partydeck[data-goal="general"]').wait_for(timeout=WAIT_MS)
        assert goals_of("passkey") == 0


@pytest.mark.asyncio
async def test_a_refusal_is_said_in_the_question_which_stays(fake_repo, monkeypatch):
    removable(monkeypatch, refuse="2 goals at work: stop them first")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        ask = await _ask(page, "passkey")
        await ask.locator('[data-act="remove-move"]').click()
        said = ask.locator('[data-said="refused"]')
        await said.wait_for(timeout=WAIT_MS)
        assert (await said.inner_text()).strip() == "2 goals at work: stop them first" and await said.get_attribute("role") == "alert"
        assert await ask.locator('[data-act="remove-move"]').is_enabled() and await ask.get_attribute("open") is not None   # still asking
        assert await page.locator(".flash", has_text="removed").count() == 0 and await page.evaluate(NO_SCROLL)
        await ask.locator('[data-act="remove-cancel"]').click()
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        await page.locator('.partydeck[data-goal="passkey"]').wait_for(timeout=WAIT_MS)                                    # the party is still shown


@pytest.mark.asyncio
async def test_a_party_with_no_goals_says_so_and_asks_remove_or_cancel(fake_repo, monkeypatch):
    removable(monkeypatch)
    assert goals_of("website") == 0
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        ask = await _ask(page, "website")
        assert (await ask.locator('[data-sec="no-goals"]').inner_text()).strip() == "It has no goals"
        buttons = ask.locator(".remove-ask .ork-btn")
        assert [(await b.inner_text()).strip() for b in await buttons.all()] == ["Remove", "Cancel"]
        assert "danger" in await buttons.nth(0).get_attribute("class")
        for b in await buttons.all():
            assert (await b.bounding_box())["height"] >= 44
        await buttons.nth(0).click()
        assert await _called(stub, "ideas.track_drop", {"slug": "website", "goals": "move"})
        await page.locator(".flash", has_text="Website removed").first.wait_for(timeout=WAIT_MS)
        assert await page.locator(".flash", has_text="goals").count() == 0                                                  # no goals to say
        await page.locator('.partydeck[data-goal="general"]').wait_for(timeout=WAIT_MS)                                    # Website was shown: General now
        assert await page.evaluate(NO_SCROLL)


def test_the_service_worker_is_one_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 90 and re.search(r'"shell-party-remove\.js"', sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))])
