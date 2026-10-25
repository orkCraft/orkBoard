"""Spec 83 part C, the phone (docs/specs/83-one-field-and-the-night-asked.md §2, §3, §4): Chromium at 390 × 844 against the arena's scene (Passkey, High) with a Board that has not been asked
about the night (`night_low` null). New goal has one field and no *Keep for tonight*: the line under Priority says *runs tonight* or *runs after the other priorities*; the first Low goal
asks *Low work may run at night?* in a sheet (*Yes, at night* / *No, by day*, 44 px) and sends `ideas.night_allow`, once; closing the form with words sends `hold`, never `night`; the
drawer has the switch (unset: off, *not asked yet*); *Tonight* on a pitch and on a held goal asks first and makes it Low, and is not drawn after *No, by day*; no sideways scroll; the
service worker's version."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import SCENE, _scene  # noqa: F401
from tests.test_pwa_goal_types_browser import _form, typed
from tests.test_pwa_ideation_browser import _ideation, hosted
from tests.test_pwa_shell_browser import FAB, NO_SCROLL, WAIT_MS, Stub, _called, _menu, _phone

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

HOST: dict = {}
LINE = "Low goals then run between 01:00 and 07:00, on what is left of the window; you can change it in Settings"


def unasked(monkeypatch, value=None):
    """The Board's word about the night is `value` (null: not asked yet); `ideas.night_allow` changes it as the host does."""
    HOST["night_low"] = value
    real = Stub.commands

    def commands(self):
        got = real(self)

        def board(a):
            return {**got["ideas.board"](a), "night_low": HOST["night_low"]}

        def allow(a):
            out = got["ideas.night_allow"](a)
            HOST["night_low"] = a["allow"]
            self.bump({})
            return out
        return {**got, "ideas.board": board, "ideas.night_allow": allow}
    monkeypatch.setattr(Stub, "commands", commands)


def question(page):
    return page.locator("dialog.night[open]")


async def _low(page, text, party_priority="low"):
    form = await _form(page)
    await form.get_by_label("The goal", exact=True).fill(text)
    await form.get_by_role("radio", name="Low" if party_priority == "low" else "Normal").click()
    return form


@pytest.mark.asyncio
async def test_the_first_low_goal_asks_once_in_a_sheet_and_the_answer_is_sent(fake_repo, monkeypatch):
    typed(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        form = await _low(page, "Someday")
        line = form.locator('[data-night="priority"]')
        assert (await line.inner_text()).strip() == "Low: runs after the other priorities." and await form.get_by_role("button", name="Keep for tonight").count() == 0
        assert await form.get_by_role("button", name="Add the goal").is_visible()
        await form.get_by_role("button", name="Add the goal").click()
        assert await _called(stub, "ideas.add", {"text": "Someday", "track": "passkey", "priority": "low"})                    # the goal is added either way
        ask = question(page)
        await ask.wait_for(timeout=WAIT_MS)
        assert await ask.get_attribute("aria-label") == "Low work may run at night?" and (await ask.locator('[data-sec="night-line"]').inner_text()).strip() == LINE
        names = [(await b.inner_text()).strip() for b in await ask.locator(".night-ask button.ork-btn").all()]
        assert names == ["Yes, at night", "No, by day"]
        for b in await ask.locator(".night-ask button.ork-btn").all():
            assert (await b.bounding_box())["height"] >= 44
        assert "primary" in await ask.get_by_role("button", name="Yes, at night").get_attribute("class")
        assert await page.evaluate(NO_SCROLL)
        await ask.get_by_role("button", name="Yes, at night").click()
        assert await _called(stub, "ideas.night_allow", {"allow": True})
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        form = await _low(page, "Another")                                                                                   # never asked again
        assert (await form.locator('[data-night="priority"]').inner_text()).strip() == "Low: runs tonight."
        await form.get_by_role("button", name="Add the goal").click()
        await form.wait_for(state="hidden", timeout=WAIT_MS)
        await page.wait_for_timeout(400)
        assert await question(page).count() == 0 and len([c for c in stub.calls if c[0] == "ideas.night_allow"]) == 1


@pytest.mark.asyncio
async def test_no_by_day_is_sent_and_a_normal_goal_or_a_closed_form_asks_nothing(fake_repo, monkeypatch):
    typed(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        form = await _form(page)                                                                                          # the party's priority is High: no question
        await form.get_by_label("The goal", exact=True).fill("Now please")
        await form.get_by_role("button", name="Add the goal").click()
        await form.wait_for(state="hidden", timeout=WAIT_MS)
        await page.wait_for_timeout(400)
        assert await question(page).count() == 0
        form = await _low(page, "Put back")                                                                                # closed with words: kept, not started, no question
        await form.get_by_role("button", name="Put it back").click()
        assert await _called(stub, "ideas.add", {"text": "Put back", "track": "passkey", "priority": "low", "hold": True})
        await form.wait_for(state="hidden", timeout=WAIT_MS)
        await page.wait_for_timeout(400)
        assert await question(page).count() == 0 and not [c for c in stub.calls if c[0] == "ideas.night_allow"]
        form = await _low(page, "Someday")
        await form.get_by_role("button", name="Add the goal").click()
        ask = question(page)
        await ask.wait_for(timeout=WAIT_MS)
        await ask.get_by_role("button", name="No, by day").click()
        assert await _called(stub, "ideas.night_allow", {"allow": False})
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        form = await _low(page, "Later")
        assert (await form.locator('[data-night="priority"]').inner_text()).strip() == "Low: runs after the other priorities."


@pytest.mark.asyncio
async def test_esc_on_the_question_answers_nothing_and_it_is_asked_the_next_time(fake_repo, monkeypatch):
    typed(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        form = await _low(page, "Someday")
        await form.get_by_role("button", name="Add the goal").click()
        ask = question(page)
        await ask.wait_for(timeout=WAIT_MS)
        await page.keyboard.press("Escape")
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        assert not [c for c in stub.calls if c[0] == "ideas.night_allow"]
        form = await _low(page, "Again")
        await form.get_by_role("button", name="Add the goal").click()
        await question(page).wait_for(timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_the_drawer_has_the_switch_unset_is_off_and_not_asked_yet(fake_repo, monkeypatch):
    typed(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        drawer = await _menu(page)
        box_ = drawer.get_by_label("Low work may run at night")
        assert not await box_.is_checked()
        hint = drawer.locator("[data-settings=night-low-hint]")
        assert (await hint.inner_text()).strip() == "and the leaders re-read goals and propose new ones then · not asked yet"
        await box_.check()
        assert await _called(stub, "ideas.night_allow", {"allow": True})
        await page.wait_for_function("() => !document.querySelector('[data-settings=night-low-hint]').textContent.includes('not asked yet')", timeout=WAIT_MS)
        assert await box_.is_checked()
        await box_.uncheck()
        assert await _called(stub, "ideas.night_allow", {"allow": False})
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_tonight_on_a_pitch_asks_first_and_makes_it_low(fake_repo, monkeypatch):
    hosted(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _ideation(page)
        await page.locator(FAB).click()
        form = page.locator("dialog.newgoal[open]")
        await form.wait_for(timeout=WAIT_MS)
        await form.get_by_label("What is the pitch?").fill("Undo a merge")
        await form.get_by_role("button", name="Tonight").click()
        ask = question(page)
        await ask.wait_for(timeout=WAIT_MS)
        assert not [c for c in stub.calls if c[0] == "ideas.add" and c[1].get("night")]                                    # asked first
        await ask.get_by_role("button", name="Yes, at night").click()
        assert await _called(stub, "ideas.add", {"text": "Undo a merge", "track": "ideation", "priority": "low", "night": True})
        await form.wait_for(state="hidden", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_no_by_day_on_a_pitch_keeps_the_form_without_tonight(fake_repo, monkeypatch):
    hosted(monkeypatch)
    unasked(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _ideation(page)
        await page.locator(FAB).click()
        form = page.locator("dialog.newgoal[open]")
        await form.wait_for(timeout=WAIT_MS)
        await form.get_by_label("What is the pitch?").fill("Share by link")
        await form.get_by_role("button", name="Tonight").click()
        ask = question(page)
        await ask.wait_for(timeout=WAIT_MS)
        await ask.get_by_role("button", name="No, by day").click()
        assert await _called(stub, "ideas.night_allow", {"allow": False})
        await ask.wait_for(state="hidden", timeout=WAIT_MS)
        await form.get_by_role("button", name="Tonight").wait_for(state="hidden", timeout=WAIT_MS)
        assert await form.is_visible()                       # the form stays, Tonight is not drawn
        assert await form.get_by_role("button", name="Hold", exact=True).is_visible() and await form.get_by_role("button", name="Judge now").is_visible()


@pytest.mark.asyncio
async def test_the_service_worker_names_the_new_file_and_a_newer_version():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 91
    assert '"shell-night-ask.js"' in sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
