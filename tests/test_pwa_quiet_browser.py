"""Spec 87 C, the phone (docs/specs/87-quieter-work-longer-names.md §4.2, §4.3, §6): Chromium at 390 × 844 against the stub of test_pwa_shell_browser.py. A to-do lies last in the hand; each other
open project in the projects' sheet says one mark and no number (the alert sign when something waits for you, else the hourglass while a task is at work, else none); the goal's plan shows
*Before <task>: <to-do>* under its tasks until the to-do is done or its task is merged; the service worker's version. No sideways scroll."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _phone, _pop, _shot  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

ROOT = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "pwa"
ROWS = [{"path": "/work/alpha", "name": "alpha", "working": 2, "needs_you": 1, "review": 0},
        {"path": "/work/beta", "name": "beta", "working": 1, "needs_you": 2, "review": 4},
        {"path": "/work/gamma", "name": "gamma", "working": 3, "needs_you": 0, "review": 1},
        {"path": "/work/delta", "name": "delta", "working": 0, "needs_you": 0, "review": 5}]


@pytest.fixture(autouse=True)
def _projects(monkeypatch):
    state = {"current": "/work/alpha"}
    real = Stub.commands

    def commands(self):
        def use(a):
            state["current"] = a["path"]
            return self.bump({"ok": True})

        def lst(a):
            return {"current": state["current"], "open": ROWS, "recent": []}
        return {**real(self), "projects.list": lst, "projects.use": use}
    monkeypatch.setattr(Stub, "commands", commands)


async def _sheet(page):
    await page.locator(".board-bar .projbtn").click()
    sheet = page.get_by_role("dialog", name="Projects")
    await sheet.get_by_role("button", name=re.compile("^delta")).wait_for(timeout=WAIT_MS)
    return sheet


async def _open_plan(page):
    raised = await _pop(page, "Plan ready: Dark mode")
    await raised.get_by_role("button", name="Open it on its own screen").click()
    screen = page.locator(".screen")
    await screen.get_by_text("The plan", exact=True).wait_for(timeout=WAIT_MS)
    return screen


@pytest.mark.asyncio
async def test_a_project_in_the_switcher_says_one_mark_and_no_number(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        sheet = await _sheet(page)
        row = lambda name: sheet.locator(f'.project-row[data-project="{name}"]')
        assert await row("beta").locator(".project-mark.alert .ork-sign.alert").count() == 1 and await row("beta").locator(".ork-busy").count() == 0      # something waits for you: the alert sign, though a task is at work too
        assert await row("gamma").locator(".project-mark.busy .ork-busy").count() == 1 and await row("gamma").locator(".ork-sign").count() == 0         # a task at work: the hourglass
        assert await row("delta").locator(".project-mark").count() == 0 and await row("delta").locator(".ork-busy, .ork-sign").count() == 0                # nothing waits: no mark
        assert await row("alpha").locator(".project-mark").count() == 0                                                                                    # this one says "this one"
        text = " ".join((await sheet.locator(".project-list").inner_text()).split())
        assert text == "beta gamma delta" and not re.search(r"\d|working|review|nothing waits", text)                                                       # no number, no count in words
        assert await row("beta").locator(".project-mark").get_attribute("aria-label") == "needs you"                                                      # a screen reader still hears it
        assert await row("gamma").locator(".project-mark").get_attribute("aria-label") == "at work"
        assert await row("beta").locator(".ork-sign.alert").evaluate("e => getComputedStyle(e).color") != await row("beta").evaluate("e => getComputedStyle(e).color")   # the signal is the alert's colour
        assert (await row("delta").bounding_box())["height"] >= 56
        await _shot(page, "phone-projects-marks-390x844")
        assert await page.evaluate(NO_SCROLL)
        await row("gamma").click()
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_a_todo_lies_last_in_the_hand_after_the_plan_and_the_results(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        hand = page.locator(".hc")
        await hand.first.wait_for(timeout=WAIT_MS)
        assert [await b.get_attribute("data-kind") for b in await hand.all()] == ["plan", "look", "look", "todo"]
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_plan_says_before_which_task_a_todo_is_needed_until_it_is_done(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        screen = await _open_plan(page)
        lines = screen.locator(".before-lines .before-line")
        await lines.first.wait_for(timeout=WAIT_MS)
        assert [await l.inner_text() for l in await lines.all()] == ["Before Add the queue: API_KEY", "Before Retry on a lost signal: API_KEY"]         # the plan's order
        assert await screen.locator(".plan .tasks").evaluate("e => e.nextElementSibling.className") == "before-lines"                                      # under the tasks
        assert await page.evaluate(NO_SCROLL)
        await _shot(page, "phone-plan-before-390x844")
        await page.get_by_role("button", name="Back", exact=True).click()
        await screen.wait_for(state="hidden", timeout=WAIT_MS)
        stub.plan["tasks"][1]["state"] = "merged"                                                                                                         # a task already made is not waited for
        stub.bump({})
        screen = await _open_plan(page)
        await screen.locator(".before-lines .before-line").first.wait_for(timeout=WAIT_MS)
        assert [await l.inner_text() for l in await screen.locator(".before-lines .before-line").all()] == ["Before Retry on a lost signal: API_KEY"]
        await page.get_by_role("button", name="Back", exact=True).click()
        await screen.wait_for(state="hidden", timeout=WAIT_MS)
        stub.plan["todos"][0]["done"] = True                                                                                                              # a to-do done is not said
        stub.bump({})
        screen = await _open_plan(page)
        await screen.locator(".plan .tasks").wait_for(timeout=WAIT_MS)
        assert await screen.locator(".before-lines").count() == 0


def test_the_service_worker_is_v94_and_the_new_marks_have_no_colour_of_their_own():
    assert 'const CACHE = "orkcraft-app-v95"' in (ROOT / "sw.js").read_text(encoding="utf-8")
    css = (ROOT / "app.css").read_text(encoding="utf-8")
    rules = [ln for ln in css.splitlines() if ln.startswith((".project-mark", ".before-line", ".plan .before-lines", ".project-list .project-row"))]
    assert len(rules) == 5 and not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|border-radius", "\n".join(rules))
