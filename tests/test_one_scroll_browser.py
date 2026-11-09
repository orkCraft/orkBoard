"""Spec 150 C.5 (decisions §254.2): only the table scrolls. At the wide width, at 1280 x 800 and 1366 x 768, with a full board (the column's host, long titles among
its goals), nothing in `.frame-column` or `.frame-hand` has a box that scrolls vertically (`overflow-y` `auto` or `scroll` and a `scrollHeight` over its `clientHeight`),
an opened card's body excepted; and the page itself does not scroll."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, back  # noqa: E402
from tests.test_hand_desktop_browser import node  # noqa: E402

pytestmark = pytest.mark.browser

SIZES = ((1280, 800), (1366, 768))
LONG = "Let the host of a lobby hand it over to the player who has waited longest, with a sound, a toast and a line in the log"

SCROLLS = """() => {
  const out = [];
  for (const root of document.querySelectorAll(".frame-column, .frame-hand")) {
    for (const el of [root, ...root.querySelectorAll("*")]) {
      if (el.closest(".hand-lifted__body")) continue;                                   // an opened card's body may scroll
      const s = getComputedStyle(el);
      if ((s.overflowY === "auto" || s.overflowY === "scroll") && el.scrollHeight > el.clientHeight + 1) {
        out.push(`${el.tagName.toLowerCase()}.${String(el.className).split(" ").join(".")}: ${el.scrollHeight} > ${el.clientHeight}`);
      }
    }
  }
  return out;
}"""


class FullHost(ColumnHost):
    def __init__(self):
        super().__init__()
        self.nodes += [node("long1", "tech", LONG, "deck", state="raw", element="ice"),
                       node("long2", "design", LONG, "table", state="talk", element="lava", back=back()),
                       node("long3", "tech", LONG, "table", state="ready", agreed=True, element="dust", back=back())]


def open_at(gui, size):
    server, browser = gui
    host = FullHost()
    pg = browser.new_context(viewport={"width": size[0], "height": size[1]}).new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
    pg.locator(".frame-column").wait_for(timeout=WAIT_MS)
    return pg, log


@pytest.mark.parametrize("size", SIZES)
def test_nothing_outside_the_table_scrolls(gui, size):
    pg, log = open_at(gui, size)
    try:
        assert pg.evaluate(SCROLLS) == [], "the column and the hand never scroll"
        assert pg.evaluate("() => document.documentElement.scrollHeight - document.documentElement.clientHeight") <= 0, "the page does not scroll"
        for sel in (".frame-column .col-card", ".frame-hand .hand-card"):         # a card lifted: its body alone may scroll
            if pg.locator(sel).count():
                pg.locator(sel).first.dispatch_event("click")                       # the first back of a fan has the next one over its middle: pressed where the page hears it
                pg.wait_for_timeout(400)
                assert pg.evaluate(SCROLLS) == [], f"after a press on {sel}"
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(200)
    finally:
        pg.close()
    assert not log, "\n".join(log)
