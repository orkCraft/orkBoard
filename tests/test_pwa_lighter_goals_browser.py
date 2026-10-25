"""Spec 73 part C, the phone (docs/specs/73-a-lighter-column.md §5, §6 "C"): the Goals sheet drawn lighter, Chromium at 390 × 844 against the scene of tests/test_pwa_decks_browser.py.
A goal's row is one line of 44 px (its element, its type's sign, its title, its state's sign, then › that opens it; its old second line is its `aria-label` after the title; no pile, no second line);
*New · n* and *Flags · n* are folded rows of 44 px with *Process now* and *k wait for main* at their right; no sideways scroll; the service worker's version."""
from __future__ import annotations

import re
import os
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import SCENE, _scene  # noqa: F401
from tests.test_pwa_decks_browser import norm
from tests.test_type_top_right_browser import _typed
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, _called, _phone

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

SHOT = os.environ.get("LIGHTER_SHOT", "")                                  # a path: a screenshot of the sheet is kept there (a test of the look, kept by hand)


async def _sheet(page):
    await page.locator(".gbar__head", has_text="2 of 9 goals done").wait_for(timeout=WAIT_MS)                          # (the Map was read)
    await page.locator(".gbar__head").click()
    sheet = page.get_by_role("dialog", name="Goals")
    await sheet.wait_for(timeout=WAIT_MS)
    return sheet


@pytest.mark.asyncio
async def test_a_goal_is_one_line_of_44_px_with_its_old_line_in_its_label(fake_repo, monkeypatch):
    _typed()
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar__head").wait_for(timeout=WAIT_MS)
        sheet = await _sheet(page)
        rows = sheet.locator(".dk")
        assert await rows.count() == 7                                                                                  # the new goals are in the folded New row
        for r in await rows.all():
            main, opens = await r.locator(".dk__main").bounding_box(), await r.locator(".dk__open").bounding_box()
            assert round(main["height"]) == 44 and round(opens["height"]) == 44 and round(opens["width"]) == 44        # one line, 44 px; › is a 44 px target
            assert await r.locator(".pile, .dk__line, .dk__body").count() == 0                                          # no pile, no second line
            assert await r.locator(".dk__title").evaluate("e => getComputedStyle(e).whiteSpace") == "nowrap"            # the title: one line, cut with an ellipsis
            assert await r.locator(".dk__elem .ork-elem").count() == 1
        register = sheet.locator('.dk[data-idea="register"]')
        assert await register.locator(".dk__type .ork-sign").count() == 1                                               # its type's sign
        els, typ, title = [await register.locator(s).bounding_box() for s in (".dk__elem", ".dk__type", ".dk__title")]
        assert round(els["width"]) == 14 and round(typ["width"]) == 14 and els["x"] < typ["x"] < title["x"]            # the element, the type's sign, the title
        label = await register.locator(".dk__main").get_attribute("aria-label")
        assert label.startswith(f"{await register.locator('.dk__title').inner_text()} · ") and "in dev · implementation" in label     # the old second line goes after the title
        assert await register.locator(".dk__mark .ork-sign.work").count() == 1                                          # the state's sign
        plain = sheet.locator('.dk[data-idea="pagewords"]')                                                              # a goal with no type: the space kept
        assert await plain.locator(".dk__type").count() == 0 and (await plain.locator(".dk__title").bounding_box())["x"] == title["x"]
        await register.locator(".dk__open").click()                                                                      # › opens it
        await page.locator(".screen").wait_for(state="visible", timeout=WAIT_MS)
        assert await _called(stub, "ideas.log", {"event": "opened", "what": "idea", "ref": "register", "device": "phone", "via": "map"})


@pytest.mark.asyncio
async def test_new_and_flags_are_folded_rows_of_44_px_with_process_now_and_what_waits_for_main(fake_repo, monkeypatch):
    _typed()
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar__head").wait_for(timeout=WAIT_MS)
        sheet = await _sheet(page)
        new, flags = sheet.locator('[data-fold="new"]'), sheet.locator('[data-fold="flags"]')
        assert norm(await new.inner_text()).lower() == "new · 2 process now" and norm(await flags.inner_text()).lower() == "flags · 1 1 waits for main"      # (drawn in capitals)
        for fold in (new, flags):
            assert round((await fold.bounding_box())["height"]) == 44 and round((await fold.locator(".gfold__head").bounding_box())["height"]) == 44
            assert await fold.locator(".gfold__head .ork-chev.right").count() == 1 and await fold.locator(".gfold__head").get_attribute("aria-expanded") == "false"     # folded: orkUI's chevron
        assert (await new.locator("[data-act=process]").bounding_box())["height"] >= 44
        assert await sheet.locator(".goals__flag, .goals__line").count() == 0                                            # Flags is folded: nothing of it shown
        assert await sheet.locator('.dk[data-idea="magic"]').count() == 0                                                # New is folded
        await new.locator(".gfold__head").click()                                                                        # unfolded: its goals' rows below it
        assert await new.locator(".gfold__head .ork-chev:not(.right)").count() == 1
        assert [await r.get_attribute("data-idea") for r in await sheet.locator(".dk").all()][-2:] == ["magic", "log"]
        if SHOT:
            await page.wait_for_timeout(500)                                                                             # (the sheet has slid up)
            await page.screenshot(path=SHOT)
        await sheet.locator('[data-fold="flags"] .gfold__head').click()
        assert [norm(await w.inner_text()) for w in await sheet.locator(".goals__line").filter(has=page.locator(".ork-sign.check")).all()] == ["Where the credentials are kept · in dev"]
        assert len(await sheet.locator(".goals__flag").all()) == 1
        assert await page.evaluate(NO_SCROLL)
        assert await sheet.evaluate("e => e.scrollWidth <= e.clientWidth")                                               # nothing of the sheet runs out at its right
        await sheet.locator("[data-act=process]").click()                                                                # Process now: the next new goal is read now
        assert await _called(stub, "ideas.queue", {"slug": "magic", "queue": "now", "via": "party"})


def test_the_service_worker_has_the_new_version():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 86
