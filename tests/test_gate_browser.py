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
ENV_TEXT = "The tests could not run: `vitest` is not installed."
COULD_NOT_RUN = {"ran": True, "command": "npm test", "passed": None, "failed": None, "failing": [], "tail": "sh: vitest: command not found", "green": False, "exit": 127,
                 "env": ENV_TEXT, "install": [{"dir": "prototypes/ar", "command": "npm ci"}]}            # spec 107 §1: a gate that tested nothing
OLD = {"passed": 3, "failed": 0, "failing": [], "tail": "3 passed", "green": True}               # a task from before: no `ran`
RESULTS = [("Nothing ran", NOT_RAN), ("Exit zero", EXIT_0), ("Exit one", EXIT_1), ("Pytest counts", PYTEST), ("Before the gate", OLD), ("Could not run", COULD_NOT_RUN)]
LINES = {"Nothing ran": "no tests ran", "Exit zero": "✓ passed (exit 0)", "Exit one": "✗ failed (exit 1)",
         "Pytest counts": "✓ 7 / 7 passed", "Before the gate": "✓ 3 / 3 passed", "Could not run": "could not run"}


def tasks():
    return [task(f"r{i}", title, "review", tests=tests, diff=DIFF) for i, (title, tests) in enumerate(RESULTS)]


def shot(page, name: str) -> None:
    folder = os.environ.get("GATE_SHOTS")
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(folder) / f"{name}.png"))
