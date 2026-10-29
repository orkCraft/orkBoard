"""Spec 42 F on the desktop (docs/specs/42-coming-back.md §6, Tests → F), in the window as two parts (docs/specs/98-the-table-and-the-hand.md §7): the AI tools' limits (a potion of the hand's mana, spec 104 B) open what used the tool over the pane, and
*Spend today · This week's work* in it opens This week with its lines in order (the nights, the streak and the tonight line went, spec 98 A). The words of a week that waits (`waitsWords`) are read from the page's module. The cards
*While you were away* and *Last week* went with the old window (spec 98 E)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost  # noqa: E402

pytestmark = pytest.mark.browser

WEEK = {"usd": 46.1, "ops_usd": 3.2, "merged": 12, "first_time": 10, "usd_per_merged": 3.84, "nights": {"worked": 4, "idle": 2, "off": 1},
        "tonight": 0, "night_on": True, "into": "dev"}


class WeekHost(TableHost):
    def __init__(self):
        super().__init__()
        self.week = dict(WEEK)

    def handle(self, name, a):
        if name == "ideas.week_work":
            self.log.append((name, a))
            return dict(self.week)
        if name == "ideas.usage":
            self.log.append((name, a))
            return {"rows": [], "outside": 0, "window": "5h", "scopes": ["project"], "tokens_only": False}
        return super().handle(name, a)


def _open(gui, host=None):
    server, browser = gui
    host = host or WeekHost()
    pg = narrow.page(browser, "wide")
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, errors


def _spend(pg):
    """*Spend today*, in the place the limits' potion opens."""
    if not pg.locator(".table-over__limits").count():
        pg.locator(".hand-pot").first.click()
    return pg.get_by_role("button", name="Spend today: $2.40. This week's work")


def _lines(pg):
    return [" ".join(p.text_content().split()) for p in pg.locator('.place[aria-label="This week"] .week p').all()]


def _show(gui, host):
    pg, host, errors = _open(gui, host=host)
    _spend(pg).click()
    pg.locator('.place[aria-label="This week"] .week').wait_for(timeout=WAIT_MS)
    return pg, host, errors


def _logged(host, entry):
    return entry in host.log


def test_todays_spend_opens_this_week_over_the_pane_with_its_lines_in_order(gui):
    pg, host, errors = _show(gui, WeekHost())
    assert _lines(pg) == ["≈$46 of work at API prices in this project: not your bill",
                          "12 results in dev, 10 the first time · ≈$3.84 a result"]
    assert pg.locator("[aria-modal]").count() == 0                                                     # over the pane, never a dialog
    for _ in range(40):
        if _logged(host, ("ideas.log", {"event": "opened", "what": "week", "ref": "this", "device": "desktop"})):
            break
        pg.wait_for_timeout(50)
    assert _logged(host, ("ideas.log", {"event": "opened", "what": "week", "ref": "this", "device": "desktop"}))
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_null_part_and_a_missing_price_are_left_out(gui):
    host = WeekHost()
    host.week.update(ops_usd=None, usd_per_merged=None)
    pg, host, errors = _show(gui, host)
    assert _lines(pg) == ["≈$46 of work at API prices in this project: not your bill", "12 results in dev, 10 the first time"]
    pg.keyboard.press("Escape")
    host.week.update(usd=None, ops_usd=None, merged=0, first_time=0)
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    _spend(pg).click()
    pg.locator('.place[aria-label="This week"] .week').wait_for(timeout=WAIT_MS)
    assert _lines(pg) == ["No results in dev in the last 7 days"]
    pg.close()
    assert not errors, "\n".join(errors)


# -- spec 44 B: the week's pace ---------------------------------------------------------------------------------------

def test_the_week_line_says_when_low_work_waits_and_last_weeks_unused_share(gui):
    host = WeekHost()
    host.week.update(week={"left": 0.55, "rest": 2 / 7, "pace": "ahead", "reset": 0}, last_unused=0.3)
    pg, host, errors = _show(gui, host)
    assert _lines(pg)[-2:] == ["The week: 55 % left with 2 days to go", "Last week ended with 30 % unused"]
    for pace, words in (("even", ""), ("behind", ": Low work waits until the week comes back")):
        host.week.update(week={"left": 0.2, "rest": 1 / 7, "pace": pace, "reset": 0}, last_unused=None)
        pg.keyboard.press("Escape")
        pg.locator(".table-board").wait_for(timeout=WAIT_MS)
        _spend(pg).click()
        pg.locator('.place[aria-label="This week"] .week').wait_for(timeout=WAIT_MS)
        got = _lines(pg)
        assert f"The week: 20 % left with 1 day to go{words}" in got and not [x for x in got if x.startswith("Last week ended")]
    host.week.update(week=None)
    pg.keyboard.press("Escape")
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    _spend(pg).click()
    pg.locator('.place[aria-label="This week"] .week').wait_for(timeout=WAIT_MS)
    assert not [x for x in _lines(pg) if x.startswith("The week")]                                     # no week read: no line
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_week_wait_says_until_when_and_without_a_time_says_none(gui):
    pg, host, errors = _open(gui)
    got = pg.evaluate("""async () => {
      const m = await import('/static/js/arena/arenawords.js');
      return [m.waitsWords({ kind: "week", until: "2026-10-26T09:00" }), m.waitsWords({ kind: "week", until: "" })]; }""")
    assert got == ["waits: the week is behind · until Mon 09:00", "waits: the week is behind"]
    pg.close()
    assert not errors, "\n".join(errors)
