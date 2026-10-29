"""*Go on paid?* on the window (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §3, part C), in a real browser against a stub host answering the Orkmaster's goal-free row `paid` and the
command `ideas.paid`, at the two widths of `tests/narrow.py`: the card's face (the alert sign, the Orkmaster's head, *Go on paid?*, the price as its gem, *Holds until the next reset*, under the first lane),
lifted its words (with the reset, the tool and its cost, or *its cost is not known yet*) and its two answers, **Go on, paid** and **Wait for Thu 18:00**, each sent as `ideas.paid {yes}`. Screenshots to $PAID_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PAID_SHOTS"]) if os.environ.get("PAID_SHOTS") else None
THURSDAY = "2026-10-22T18:00"             # a Thursday, not today: the card says the day


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def paid_row(usd_task=0.4, until=THURSDAY):
    return need("paid", "", "", "Go on paid?", "Go on paid?", tool="claude", name="Claude Code", until=until, usd_task=usd_task, blocks=True, priority="high")


class PaidHost(HandHost):
    """A project of four parties with nothing to ask but the Orkmaster's row `paid`."""

    def __init__(self, **more):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = [paid_row(**more)]

    def handle(self, name, a):
        if name == "ideas.paid":
            self.log.append((name, a))
            self.needs = []
            return self.bump({"ok": True, "tool": "claude", "name": "Claude Code", "until": THURSDAY})
        return super().handle(name, a)


def open_paid(gui, width="wide", **more):
    pg, host, log = open_hand(gui, host=PaidHost(**more), width=width)
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg):
    return pg.locator('.hand-card[data-kind="paid"]')


def lifted(pg):
    return pg.locator(".hand-lifted")


BODY = "Every subscription is out until Thu 18:00. Go on with Claude Code paid by its API, about $0.40 a task, or wait."


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_card_is_the_orkmasters_go_on_paid_with_its_price_under_the_first_lane(gui, width):
    pg, host, log = open_paid(gui, width)
    try:
        c = front(pg)
        assert c.count() == 1 and c.get_attribute("data-top") == "1"
        assert c.locator(".hand-card__name").text_content().strip() == "Go on paid?"
        assert c.locator(".hand-card__window .ork-sign.alert").count() == 1 and c.locator(".hand-card__asker .ork-race__head").count() == 1, "the alert sign (orkUI has no coins sign) and the Orkmaster's head"
        assert c.locator(".hand-card__gem .ork-gem").text_content().strip() == "$0.40" and c.locator(".ork-gem.share").count() == 0, "its price in dollars, never a share of a window"
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Holds until the next reset"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-stack="paid@0"]').count() == 1, "the whole project's: under the first lane"
        shot(pg, f"{width}-paid-face")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_it_says_the_reset_the_tool_and_its_cost_and_has_two_answers(gui, width):
    pg, host, log = open_paid(gui, width)
    try:
        front(pg).click(position={"x": 10, "y": 24})
        lifted(pg).wait_for(timeout=WAIT_MS)
        card = lifted(pg)
        assert "Go on paid?" in card.locator(".hand-lifted__title").inner_text()
        assert card.locator(".hand-way__words").inner_text().strip() == BODY
        assert [b.inner_text().strip() for b in card.locator(".hand-answers .ork-btn").all()] == ["Go on, paid", "Wait for Thu 18:00"]
        assert card.locator(".hand-answers .ork-btn.primary").count() == 1
        assert all(not e.is_visible() for e in card.locator(".hand-spend").all()), "the price is in the words, not said again"
        shot(pg, f"{width}-paid-lifted")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_go_on_paid_sends_a_yes_and_the_card_goes(gui, width):
    pg, host, log = open_paid(gui, width)
    try:
        front(pg).click(position={"x": 10, "y": 24})
        lifted(pg).get_by_role("button", name="Go on, paid").click()
        assert _calls(pg, host, "ideas.paid") == [{"yes": True}]
        pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"paid\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_wait_sends_a_no_and_the_card_goes(gui, width):
    pg, host, log = open_paid(gui, width)
    try:
        front(pg).click(position={"x": 10, "y": 24})
        lifted(pg).get_by_role("button", name="Wait for Thu 18:00").click()
        assert _calls(pg, host, "ideas.paid") == [{"yes": False}]
        pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"paid\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_cost_not_known_has_no_gem_and_says_so(gui):
    pg, host, log = open_paid(gui, usd_task=None)
    try:
        assert front(pg).locator(".ork-gem").count() == 0
        front(pg).click(position={"x": 10, "y": 24})
        lifted(pg).wait_for(timeout=WAIT_MS)
        assert lifted(pg).locator(".hand-way__words").inner_text().strip() == "Every subscription is out until Thu 18:00. Go on with Claude Code paid by its API, its cost is not known yet, or wait."
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_reset_known_says_no_time_and_waits_plainly(gui):
    pg, host, log = open_paid(gui, until=None)
    try:
        front(pg).click(position={"x": 10, "y": 24})
        lifted(pg).wait_for(timeout=WAIT_MS)
        assert lifted(pg).locator(".hand-way__words").inner_text().strip().startswith("Every subscription is out. Go on with Claude Code")
        assert [b.inner_text().strip() for b in lifted(pg).locator(".hand-answers .ork-btn").all()] == ["Go on, paid", "Wait"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_row_is_the_first_lanes_and_a_reset_of_today_is_said_by_its_hour(gui):
    pg, host, log = open_paid(gui)
    try:
        got = pg.evaluate("""async () => {
          const { laneOf } = await import('/static/js/hand/data.js'), { untilWords } = await import('/static/js/arena/arenawords.js'), parties = ['tech', 'design'].map((slug) => ({ slug }));
          const now = new Date(2026, 9, 29, 12, 0), pad = (n) => String(n).padStart(2, '0');
          return [laneOf({ kind: 'paid', row: {} }, parties), untilWords('2026-10-29T18:00', now), untilWords('2026-10-30T18:00', now), untilWords('', now)];
        }""")
        assert got == [0, "18:00", "Fri 18:00", ""]
    finally:
        pg.close()
    assert not log, "\n".join(log)
