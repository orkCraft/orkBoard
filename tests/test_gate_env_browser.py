"""Spec 107 §1.3, §1.4 on the desktop, in a real browser: a result whose gate could not run says so (*could not run*, why, no *Its tests are red*), offers
**Install and test again** (or **Test again**) first and Merge stays off; a send back that changed nothing says so and Fix opens empty; a Fix line the face wrote
and sent unchanged is told to the host as suggested. `ResultActions` is drawn into a box of the test's own, against the hand's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser

ENV = "The tests could not run: `vitest` is not installed."
ROWS = [{"dir": "prototypes/ar", "command": "npm ci"}, {"dir": "server", "command": "npm ci"}]
DIFF = {"files": 2, "added": 5, "removed": 1}
BASE = {"idea": "sync", "task": "k1", "title": "Add the queue", "round": 1, "conflict": "", "look": "", "cost": 0.4, "over": False, "diff": DIFF}
COULD_NOT = {"passed": None, "failed": None, "failing": [], "tail": "sh: vitest: command not found", "green": False, "ran": True, "command": "npm test", "exit": 127,
             "env": ENV, "install": ROWS[:1]}
RED = {"passed": 3, "failed": 1, "failing": ["tests/test_queue.py::test_empty"], "tail": "1 failed, 3 passed", "green": False, "ran": True, "command": "pytest"}

DRAW = """async (r) => {
  const [{ render, h }, { ResultActions }] = await Promise.all([import('preact'), import('/static/js/shell/review.js')]);
  let box = document.getElementById('test-result');
  if (!box) { box = document.createElement('div'); box.id = 'test-result'; box.style.cssText = 'position:fixed;left:0;top:0;width:560px;background:var(--ork-panel);padding:16px;z-index:5'; document.body.appendChild(box); }
  render(null, box);
  render(h(ResultActions, { r }), box);
}"""


def draw(pg, tests, **more):
    pg.evaluate(DRAW, {**BASE, "tests": tests, **more})
    return pg.locator("#test-result")


def test_a_result_that_could_not_run_says_why_offers_install_and_test_again_first_and_merge_stays_off(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, COULD_NOT)
        install = box.get_by_role("button", name="Install and test again")
        install.wait_for(timeout=WAIT_MS)
        assert "primary" in install.get_attribute("class").split()
        assert install.get_attribute("title") == "Runs `npm ci` in prototypes/ar in your project, then the tests again"
        assert box.locator("[data-env]").inner_text() == ENV and "Its tests are red" not in box.inner_text()
        assert box.locator("[data-no-install]").inner_text() == "Sending it back would not help: the task cannot install anything."
        merge = box.get_by_role("button", name="Merge into dev")
        assert merge.is_disabled() and "primary" not in merge.get_attribute("class").split()
        fix = box.get_by_role("button", name="Fix", exact=True)
        assert fix.is_visible() and "primary" not in fix.get_attribute("class").split() and box.get_by_role("button", name="Drop…").is_visible()
        buttons = [b.inner_text() for b in box.locator(".shell-actions__main button").all()]
        assert buttons[0] == "Install and test again", buttons
        fix.click()
        assert box.get_by_label("What to fix, in one line").input_value() == ""                 # nothing the code can mend is suggested
        install.click()
        assert _sent(pg, host, ("ideas.regate", {"slug": "sync", "task": "k1", "install": True}))
        words = pg.evaluate("([r]) => import('/static/js/shell/review.js').then((m) => m.testsWords(r))", [{**BASE, "tests": COULD_NOT}])
        assert words == {"mark": "", "text": "could not run", "names": [], "tone": "alert"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_nothing_to_install_it_is_test_again_and_several_folders_are_joined_by_then(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, {**COULD_NOT, "install": []})
        again = box.get_by_role("button", name="Test again", exact=True)
        again.wait_for(timeout=WAIT_MS)
        assert again.get_attribute("title") == "Runs the tests again: install what they need in your project first"
        again.click()
        assert _sent(pg, host, ("ideas.regate", {"slug": "sync", "task": "k1", "install": False}))
        box = draw(pg, {**COULD_NOT, "install": ROWS})
        assert box.get_by_role("button", name="Install and test again").get_attribute("title") == \
            "Runs `npm ci` in prototypes/ar, then `npm ci` in server in your project, then the tests again"
        box = draw(pg, {**COULD_NOT, "env": "The install failed: npm ERR! network is down"})
        assert box.locator("[data-env]").inner_text() == "The install failed: npm ERR! network is down"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_red_result_is_still_red_with_fix_suggesting_its_line_and_the_line_sent_unchanged_is_told_suggested(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, RED)
        box.get_by_role("button", name="Merge into dev").wait_for(timeout=WAIT_MS)
        assert "Its tests are red" in box.locator(".shell-actions__why").first.inner_text()
        assert box.get_by_role("button", name="Install and test again").count() == 0 and box.locator("[data-same], [data-no-install]").count() == 0
        box.get_by_role("button", name="Fix", exact=True).click()
        field = box.get_by_label("What to fix, in one line")
        assert field.input_value() == "Fix the failing tests: tests/test_queue.py::test_empty"
        field.press("Enter")
        assert _sent(pg, host, ("ideas.back", {"slug": "sync", "task": "k1", "why": "Fix the failing tests: tests/test_queue.py::test_empty", "suggested": True}))
        box = draw(pg, RED, task="k2")
        box.get_by_role("button", name="Fix", exact=True).click()
        box.get_by_label("What to fix, in one line").fill("Cover the empty queue")
        box.get_by_label("What to fix, in one line").press("Enter")
        assert _sent(pg, host, ("ideas.back", {"slug": "sync", "task": "k2", "why": "Cover the empty queue"}))      # typed: no `suggested`
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_same_failure_again_is_said_and_fix_opens_empty(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, {**RED, "same": True}, round=2)
        box.get_by_role("button", name="Fix", exact=True).wait_for(timeout=WAIT_MS)
        assert box.locator("[data-same]").inner_text() == "The last fix changed nothing: the tests failed the same way."
        assert "Its tests are red" in box.locator(".shell-actions__why").first.inner_text()
        box.get_by_role("button", name="Fix", exact=True).click()
        assert box.get_by_label("What to fix, in one line").input_value() == ""
        assert box.get_by_role("button", name="Merge into dev").is_disabled()
    finally:
        pg.close()
    assert not log, "\n".join(log)
