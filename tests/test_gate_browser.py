"""Spec 37 C on the Review card, in a real browser: the tests' line reads `ran` first, then `null` counts as the exit code,
then the counts as today — desktop at 1 440 × 900 (a stub host's results; the phone's is in test_gate_phone_browser.py). Screenshots go to the folder
named by GATE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_pwa_shell_browser import task  # noqa: E402
from tests.test_shell_browser import StubHost, _open  # noqa: E402

pytestmark = pytest.mark.browser

DIFF = {"files": 2, "added": 5, "removed": 1}
NOT_RAN = {"ran": False, "command": "", "passed": 0, "failed": 0, "failing": [], "tail": "no tests ran", "green": True}
EXIT_0 = {"ran": True, "command": "npm test", "passed": None, "failed": None, "failing": [], "tail": "ok", "green": True, "exit": 0}
EXIT_1 = {"ran": True, "command": "npm test", "passed": None, "failed": None, "failing": [], "tail": "boom", "green": False, "exit": 1}
PYTEST = {"ran": True, "command": "python -m pytest -q", "passed": 7, "failed": 0, "failing": [], "tail": "7 passed", "green": True}
OLD = {"passed": 3, "failed": 0, "failing": [], "tail": "3 passed", "green": True}               # a task from before: no `ran`
RESULTS = [("Nothing ran", NOT_RAN), ("Exit zero", EXIT_0), ("Exit one", EXIT_1), ("Pytest counts", PYTEST), ("Before the gate", OLD)]
LINES = {"Nothing ran": "no tests ran", "Exit zero": "✓ passed (exit 0)", "Exit one": "✗ failed (exit 1)",
         "Pytest counts": "✓ 7 / 7 passed", "Before the gate": "✓ 3 / 3 passed"}


def tasks():
    return [task(f"r{i}", title, "review", tests=tests, diff=DIFF) for i, (title, tests) in enumerate(RESULTS)]


def shot(page, name: str) -> None:
    folder = os.environ.get("GATE_SHOTS")
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(folder) / f"{name}.png"))


def test_desktop_review_card_reads_ran_then_the_exit_code_then_the_counts(gui):
    pg, host, errors = _open(gui, host=StubHost())
    host.plan["tasks"] = tasks()
    host.bump(None)
    card = lambda title: pg.locator(f'.arena-hc[data-kind=result]:has(.arena-hc__open[aria-label="To look at: {title}"])')      # noqa: E731  (a result: the hand's card, spec 90 §2.3)
    card("Pytest counts").wait_for(timeout=WAIT_MS)                                                     # the hand holds every result waiting
    for title, line in LINES.items():                                                                   # each opened in the right column: its tests' line
        card(title).locator(".arena-hc__open").focus()
        pg.keyboard.press("Enter")
        pg.wait_for_function("(t) => document.querySelector('.shell-drawer .shell-ptab.is-on')?.textContent.includes(t)", arg=title, timeout=WAIT_MS)
        facts = pg.locator(".shell-drawer .shell-facts dd").first
        facts.wait_for(timeout=WAIT_MS)
        sign = {"✓": "check", "✗": "cross"}.get(line[0])                                                  # the desktop draws the mark as orkUI's sign, the phone still types it
        assert " ".join(facts.inner_text().split()) == (line[2:] if sign else line), title
        assert facts.locator(f".ork-sign.{sign}").count() == (1 if sign else 0), title
    pg.get_by_role("button", name="Close the right column").click()
    exit_one = card("Exit one")
    exit_one.locator(".arena-hc__open").focus()
    assert exit_one.get_by_role("button", name="Fix", exact=True).is_visible()
    assert exit_one.get_by_role("button", name="Merge into dev").is_disabled()
    nothing = card("Nothing ran")
    nothing.locator(".arena-hc__open").focus()
    assert nothing.get_by_role("button", name="Merge into dev").is_enabled()
    shot(pg, "review-desktop-1440x900")
    pg.close()
    assert not errors, "\n".join(errors)
