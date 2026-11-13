"""**The desktop reads well** (docs/specs/169, decisions §291), in a real browser at 1366 x 768 on the first lane: the page's
headings, buttons and card texts are set in Rubik, no visible text is under 12 px, and a card has orkUI's 10 px corners."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost  # noqa: E402
from tests.test_window_desktop_browser import WindowHost  # noqa: E402

pytestmark = pytest.mark.browser

FAMILY = "(e) => getComputedStyle(e).fontFamily"


def open_window(gui):
    server, browser = gui
    host = WindowHost()
    rich = TableHost(rich=True, line=3)
    host.nodes = rich.nodes + [n for n in host.nodes if n["slug"] == "music"]
    pg = browser.new_context(viewport={"width": 1366, "height": 768}).new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(1500)
    return pg


def rubik(pg, selector):
    loc = pg.locator(selector)
    assert loc.count() >= 1, selector
    return loc.first.evaluate(FAMILY).strip("\"' ").startswith("Rubik")






