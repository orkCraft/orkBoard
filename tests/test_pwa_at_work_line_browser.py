"""Spec 72 part C, the phone: a closed party says what it is at work on (docs/specs/72-at-work-under-a-closed-party.md §1, §3, §4 "C"): Chromium at 390 × 844 against the world of tests/test_pwa_route_browser.py with a
Website party that has five goals at work and a Mobile party with two. In the parties' sheet, under each party's row but the one shown, one quiet line: the work sign, then each goal's element and short name joined by *·*
(two goals, then *and k more*); a party with none at work has no line and neither has the party shown; a tap on a goal closes the sheet and shows that party with that goal alone picked into the filter, *and k more*
shows it with no pick; each is a 44 px button, the line's name says *At work: <goals>*, its ink is the muted one, no sideways scroll; the service worker's version."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import SCENE, _redrawn, _scene, _shot_to, node  # noqa: F401
from tests.test_pwa_route_browser import a_party, norm, world  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _phone, _where
from tests.test_pwa_route_browser import WORLD  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

FIVE = [("web1", "Cookie banner", "ice"), ("web2", "Pricing page", "dust"), ("web3", "Contact form", "void"), ("web4", "Footer links", "lava"), ("web5", "Sitemap", "meadow")]
TWO = [("app1", "Push permission", "meadow"), ("app2", "Offline cache", "ice")]


def at_work(monkeypatch):
    """The route tests' world (Passkey shown, Ideation, Website) with five goals at work in Website and a Mobile party with two; a sixth goal of Website is only planned."""
    world(monkeypatch, release=False)
    SCENE["map"]["goals"].append(a_party("mobile", "Mobile app", {"slug": "mob-lead", "name": "Mob lead"}, [({"slug": "mob-lead", "name": "Mob lead"}, "lead", SCENE["map"]["goals"][0]["leader"]["head"])], types=[]))
    for goal, rows in (("website", FIVE), ("mobile", TWO)):
        for slug, title, element in rows:
            SCENE["map"]["nodes"].append(node(slug, f"{title} in full", "working", "implementation", goal=goal, short=title, element=element, folded=False))
    SCENE["map"]["nodes"].append(node("web6", "Legal pages", "planning", "planning", goal="website", element="ice", folded=False))


def lines(sheet):
    return sheet.locator(".where-work")


@pytest.mark.asyncio
async def test_a_closed_party_has_a_quiet_line_of_its_goals_at_work_and_the_party_shown_has_none(fake_repo, monkeypatch):
    at_work(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await lines(sheet).first.wait_for(timeout=WAIT_MS)
        assert await sheet.locator(".where-row.is-on").get_attribute("data-goal") == "passkey"
        assert [await x.get_attribute("data-for") for x in await lines(sheet).all()] == ["website", "mobile"]            # not under Passkey (shown), nor Ideation (nothing at work)
        mobile = lines(sheet).nth(1)
        assert norm(await mobile.inner_text()) == "Push permission · Offline cache"
        assert [await b.get_attribute("aria-label") for b in await mobile.locator("button").all()] == ["Push permission in full", "Offline cache in full"]    # each its whole title
        assert await mobile.get_attribute("aria-label") == "At work: Push permission in full, Offline cache in full" == await mobile.get_attribute("title")
        assert await mobile.locator(".ork-sign.work").count() == 1 and "↻" not in await mobile.inner_text()               # orkUI's work sign
        assert [await e.get_attribute("class") for e in await mobile.locator(".ork-elem").all()] == ["ork-elem meadow", "ork-elem ice"]
        for b in await mobile.locator("button").all():
            assert (await b.bounding_box())["height"] >= 44
        assert await sheet.locator(".where-work button button, button .where-work").count() == 0                          # no nested buttons
        quiet = await mobile.evaluate("(e) => getComputedStyle(e).color")
        assert quiet == await sheet.locator(".where-row__body small").first.evaluate("(e) => getComputedStyle(e).color")   # the muted ink
        row = await sheet.locator('.where-row[data-goal="mobile"]').bounding_box()
        line = await mobile.bounding_box()
        assert line["y"] >= row["y"] + row["height"] - 1 and await page.evaluate(NO_SCROLL)                                # under its row


@pytest.mark.asyncio
async def test_five_at_work_end_with_and_k_more_and_a_tap_picks_the_goal_into_the_party(fake_repo, monkeypatch):
    at_work(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        web = sheet.locator('.where-work[data-for="website"]')
        await web.wait_for(timeout=WAIT_MS)
        assert norm(await web.inner_text()) == "Cookie banner · Pricing page and 3 more"
        assert await web.get_attribute("aria-label") == "At work: Cookie banner in full, Pricing page in full, Contact form in full, Footer links in full, Sitemap in full"
        assert (await web.locator(".where-work__more").bounding_box())["height"] >= 44
        assert (await web.bounding_box())["height"] <= 2 * 44 + 8                                                           # one row that wraps to two at most
        assert await page.evaluate(NO_SCROLL)
        await _shot_to(page, "phone-at-work")
        await web.locator('[data-idea="web2"]').click()
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)
        await page.locator('.partydeck[data-goal="website"]').wait_for(timeout=WAIT_MS)                                    # that party shown
        bar = page.locator(".gbar.is-on")
        await bar.wait_for(timeout=WAIT_MS)
        assert "Website" in await bar.inner_text() and "1 of" in await bar.locator(".gbar__words").inner_text()            # only that goal picked
        assert await bar.locator(".ork-elem").count() == 1 and "dust" in await bar.locator(".ork-elem").get_attribute("class")
        assert await page.evaluate(NO_SCROLL)
        sheet = await _where(page)                                                                                          # Website is now the one shown: no line; the closed Passkey and Mobile have theirs
        await sheet.locator(".where-work").first.wait_for(timeout=WAIT_MS)
        assert [await x.get_attribute("data-for") for x in await lines(sheet).all()] == ["passkey", "mobile"]
        await sheet.locator('.where-work[data-for="mobile"] [data-idea="app1"]').click()                                   # another party: its own pick
        await page.locator('.partydeck[data-goal="mobile"]').wait_for(timeout=WAIT_MS)
        await page.locator(".gbar.is-on").wait_for(timeout=WAIT_MS)
        assert "Mobile app" in await page.locator(".gbar.is-on").inner_text()


@pytest.mark.asyncio
async def test_and_k_more_shows_the_party_with_no_pick_even_after_a_goal_was_picked(fake_repo, monkeypatch):
    at_work(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        await sheet.locator('.where-work[data-for="website"] [data-idea="web1"]').click()
        await page.locator(".gbar.is-on").wait_for(timeout=WAIT_MS)
        sheet = await _where(page)
        await sheet.locator('.where-row[data-goal="passkey"]').click()                                                      # back to Passkey
        await page.locator('.partydeck[data-goal="passkey"]').wait_for(timeout=WAIT_MS)
        sheet = await _where(page)
        await sheet.locator('.where-work[data-for="website"] .where-work__more').click()
        await page.locator('.partydeck[data-goal="website"]').wait_for(timeout=WAIT_MS)
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        assert await page.locator(".gbar.is-on").count() == 0                                                               # shown whole
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_party_with_nothing_at_work_has_no_line_and_the_rows_keep_their_height(fake_repo, monkeypatch):
    world(monkeypatch, release=False)
    for n in SCENE["map"]["nodes"]:
        if n["state"] == "working":
            n["state"] = "planning"
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _where(page)
        assert await sheet.locator(".where-row[data-goal]").count() >= 3 and await lines(sheet).count() == 0
        assert await page.evaluate(NO_SCROLL)


def test_the_service_worker_is_one_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v84";' in sw and re.search(r'"shell-where\.js"', sw)
