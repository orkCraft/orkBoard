"""A log one reads (docs/specs/107-what-the-owners-day-said.md §3), in a real browser against the hand's stub host: a failed task's stop opened over the pane shows its log as sections, a round's (the prompt a session
got) folded under its heading, the gate's output open and the log scrolled to its foot, the escape codes of a terminal gone, Copy beside the caption, the line of what happened above it; and the log stays at its foot
while its text grows."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, _press, open_hand, pane  # noqa: E402

pytestmark = pytest.mark.browser

PROMPT = "\n".join(f"prompt line {i}: what the session was told" for i in range(60))
GATE = "\n".join(f"\x1b[32mtests/test_clock.py::test_case_{i} PASSED\x1b[0m" for i in range(120))
LOG = (f"== round 1 · 2026-10-29T18:40:05 · sonnet\nallowed: git, npm\n{PROMPT}\n== the session answered\nI changed the clock.\n"
       f"== the gate, try 1\n{GATE}\n\x1b[31mFAILED\x1b[0m tests/test_clock.py::test_reset\nthe last line of the gate\n")


class LogHost(HandHost):
    """The failing task has no error of its own (its tests said what happened) and a log of three sections."""

    def __init__(self):
        super().__init__()
        next(t for n in self.nodes if n["slug"] == "timer" for t in n["tasks"]).update(error="")

    def handle(self, name, a):
        got = super().handle(name, a)
        if name == "ideas.task":
            return got | {"log": LOG, "tests": {"passed": 120, "failed": 1, "green": False, "failing": ["tests/test_clock.py::test_reset"], "tail": ""}}
        return got


def test_a_failed_tasks_log_is_sections_with_the_round_folded_and_the_gate_open_at_its_foot(gui):
    pg, host, log = open_hand(gui, host=LogHost())
    try:
        _press(pg, "timer")
        pg.locator(".hand-lifted").get_by_role("button", name="Open…").click()
        box = pane(pg)
        view = box.locator(".shell-logview")
        view.wait_for(timeout=WAIT_MS)
        rounds, answered, gate = (view.locator("details").nth(i) for i in range(3))
        assert view.locator("details").count() == 3
        assert rounds.get_attribute("open") is None and answered.get_attribute("open") is not None and gate.get_attribute("open") is not None     # the round folded, the others open
        assert "== round 1" in rounds.locator("summary").inner_text() and not rounds.locator("pre").is_visible()                                    # its heading only: the prompt is not drawn
        assert "prompt line 3" not in view.inner_text() and "the last line of the gate" in view.inner_text()
        assert "\x1b" not in view.inner_text() and "FAILED tests/test_clock.py::test_reset" in view.inner_text()                                   # the terminal's codes are gone
        body = view.locator(".shell-logview__body")
        at = body.evaluate("e => ({top: e.scrollTop, room: e.scrollHeight - e.clientHeight, height: e.clientHeight, window: innerHeight})")
        assert at["room"] > 0 and abs(at["top"] - at["room"]) <= 2 and at["height"] <= max(0.6 * at["window"], 1) + 2 and at["height"] <= 642        # a long log, opened at its end, bounded
        assert box.get_by_text("The tests failed: tests/test_clock.py::test_reset").count() == 1 and view.get_by_role("button", name="Copy").count() == 1     # the line of what happened, Copy
        rounds.locator("summary").click()                                                                                                           # a round's prompt is there to read when it is asked for
        assert rounds.locator("pre").is_visible() and "prompt line 3" in rounds.inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


GROW = """async () => {
  const [{ render, h }, { LogView }] = await Promise.all([import('preact'), import('/static/js/shell/logview.js')]);
  const box = document.createElement('div'); box.id = 'grow'; box.style.cssText = 'position:fixed;left:0;top:0;width:600px;z-index:5;background:var(--ork-canvas)'; document.body.appendChild(box);
  const lines = (n) => Array.from({ length: n }, (_, i) => `line ${i}`).join('\\n');
  window.__grow = (n) => render(h(LogView, { text: `== the gate, try 1\\n${lines(n)}\\n== at Review · now\\nend ${n}\\n`, label: 'Log' }), box);
  window.__grow(100);
}"""


def test_the_log_stays_at_its_foot_while_its_text_grows_unless_the_person_scrolled_up(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.evaluate(GROW)
        body = pg.locator("#grow .shell-logview__body")
        body.wait_for(timeout=WAIT_MS)
        foot = "e => Math.abs(e.scrollTop - (e.scrollHeight - e.clientHeight)) <= 2"
        assert body.evaluate(foot)
        pg.evaluate("window.__grow(200)")
        pg.wait_for_function("() => document.querySelector('#grow .shell-logview__body').textContent.includes('end 200')", timeout=WAIT_MS)
        pg.wait_for_function("() => { const e = document.querySelector('#grow .shell-logview__body'); return Math.abs(e.scrollTop - (e.scrollHeight - e.clientHeight)) <= 2; }", timeout=WAIT_MS)      # it grew and the end came with it
        body.evaluate("e => { e.scrollTop = 0; }")
        pg.evaluate("window.__grow(300)")
        pg.wait_for_function("() => document.querySelector('#grow .shell-logview__body').textContent.includes('end 300')", timeout=WAIT_MS)
        assert body.evaluate("e => e.scrollTop") == 0                                                                                               # one who scrolled up is not pulled down
    finally:
        pg.close()
    assert not log, "\n".join(log)
