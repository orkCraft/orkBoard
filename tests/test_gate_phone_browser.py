"""Spec 37 C on the phone's results (390 × 844; each a stop along the bottom, spec 49 §6): the same lines as the desktop's (test_gate_browser.py). Screenshot to the
folder named by GATE_SHOTS when it is set."""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

from tests.test_gate_browser import ENV_TEXT, LINES, tasks  # noqa: E402
from tests.browser_kit import WAIT_MS  # noqa: E402
from tests.test_pwa_shell_browser import _called, _phone, _pop  # noqa: E402
from tests.test_pwa_shell_browser import task  # noqa: E402


def plain(line):
    """The desktop's line starts with a typed ✓ or ✗; the phone draws orkUI's sign there (spec 50 §0): the words after it are the same."""
    return re.sub(r"^[✓✗] ", "", line)


@pytest.mark.asyncio
async def test_phone_review_card_reads_ran_then_the_exit_code_then_the_counts(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        stub.plan["tasks"] = tasks()
        stub.bump(None)
        await page.locator('.hc[aria-label*="Pytest counts"]').wait_for(timeout=WAIT_MS)
        for title, line in LINES.items():                                                              # a result stop says its tests' line, then its changes
            raised = await _pop(page, f"To look at: {title}")
            assert plain(line) in " ".join((await raised.locator(".raised__text").inner_text()).split()), title
            if title == "Exit one":
                assert await raised.get_by_role("button", name="Fix", exact=True).is_visible()
                assert await raised.get_by_role("button", name="Merge into dev").is_disabled()
            if title == "Could not run":                                                                # spec 107 §1.3: not red; install and test again comes first
                assert await raised.get_by_role("button", name="Install and test again").is_visible()
                assert await raised.get_by_role("button", name="Merge into dev").is_disabled()
                assert await raised.locator("[data-env]").inner_text() == ENV_TEXT and "Its tests are red" not in await raised.inner_text()
                assert await raised.locator("[data-no-install]").inner_text() == "Sending it back would not help: the task cannot install anything."
            if title == "Nothing ran":
                assert await raised.get_by_role("button", name="Merge into dev").is_enabled()
            await raised.get_by_role("button", name="Put it back").click()
            await raised.wait_for(state="hidden", timeout=WAIT_MS)
        raised = await _pop(page, "To look at: Pytest counts")                                         # its own screen has the facts, the same line
        await raised.get_by_role("button", name="Open it on its own screen").click()
        facts = page.locator(".screen .facts dd").first
        await facts.wait_for(timeout=WAIT_MS)
        assert " ".join((await facts.inner_text()).split()) == plain(LINES["Pytest counts"])
        await page.get_by_role("button", name="Back", exact=True).click()
        folder = os.environ.get("GATE_SHOTS")
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(Path(folder) / "review-phone-390x844.png"))


@pytest.mark.asyncio
async def test_install_and_test_again_asks_the_host_and_fix_opens_empty_for_a_result_that_could_not_run(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        stub.plan["tasks"] = tasks()
        stub.bump(None)
        raised = await _pop(page, "To look at: Could not run")
        install = raised.get_by_role("button", name="Install and test again")
        assert await install.get_attribute("title") == "Runs `npm ci` in prototypes/ar in your project, then the tests again"
        await raised.get_by_role("button", name="Fix", exact=True).click()
        assert await raised.get_by_label("What to fix, in one line").input_value() == ""              # nothing the code can mend is suggested
        await install.click()
        assert await _called(stub, "ideas.regate", {"slug": "sync", "task": "r5", "install": True})


@pytest.mark.asyncio
async def test_the_same_failure_again_is_said_and_a_line_the_face_wrote_is_told_suggested(fake_repo, monkeypatch):
    red = {"ran": True, "command": "pytest", "passed": 3, "failed": 1, "failing": ["tests/test_queue.py::test_empty"], "tail": "1 failed", "green": False}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        stub.plan["tasks"] = [task("s1", "Same again", "review", tests={**red, "same": True}, diff={"files": 1, "added": 1, "removed": 0}, round=2),
                              task("s2", "First time", "review", tests=red, diff={"files": 1, "added": 1, "removed": 0})]
        stub.bump(None)
        raised = await _pop(page, "To look at: Same again")
        assert await raised.locator("[data-same]").inner_text() == "The last fix changed nothing: the tests failed the same way."
        await raised.get_by_role("button", name="Fix", exact=True).click()
        assert await raised.get_by_label("What to fix, in one line").input_value() == ""
        await raised.get_by_role("button", name="Put it back").click()
        raised = await _pop(page, "To look at: First time")
        assert await raised.locator("[data-same]").count() == 0
        await raised.get_by_role("button", name="Fix", exact=True).click()
        line = raised.get_by_label("What to fix, in one line")
        assert await line.input_value() == "Fix the failing tests: tests/test_queue.py::test_empty"
        await line.press("Enter")
        assert await _called(stub, "ideas.back", {"slug": "sync", "task": "s2", "why": "Fix the failing tests: tests/test_queue.py::test_empty", "suggested": True})
