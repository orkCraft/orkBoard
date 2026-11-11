"""**The desktop reads well** (docs/specs/169, decisions §291), in a real browser at 1366 x 768 on the first lane: the page's
headings, buttons and card texts are set in Rubik, no visible text is under 12 px, and a card has orkUI's 10 px corners."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost  # noqa: E402
from tests.test_window_desktop_browser import WindowHost  # noqa: E402

pytestmark = pytest.mark.browser

SMALLEST = """() => {
  let min = 999, who = "";
  for (const e of document.body.querySelectorAll("*")) {
    if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    if (!r.width || !r.height || s.visibility === "hidden" || s.display === "none" || +s.opacity === 0) continue;
    const px = parseFloat(s.fontSize);
    if (px < min) { min = px; who = e.className + " :: " + e.textContent.trim().slice(0, 30); }
  }
  return [min, who];
}"""
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
    pg.locator(".col-plab__t").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(1500)
    return pg


def rubik(pg, selector):
    loc = pg.locator(selector)
    assert loc.count() >= 1, selector
    return loc.first.evaluate(FAMILY).strip("\"' ").startswith("Rubik")


def test_headings_buttons_and_card_text_are_rubik(gui):
    pg = open_window(gui)
    assert rubik(pg, ".col-plab__t")
    assert rubik(pg, "button")
    fams = pg.evaluate("""() => { for (const c of document.querySelectorAll(".ork-card")) for (const e of c.querySelectorAll("*"))
      if ([...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getBoundingClientRect().width) return getComputedStyle(e).fontFamily; return ""; }""")
    assert fams.strip("\"' ").startswith("Rubik"), fams


def test_no_visible_text_is_under_twelve_px(gui):
    pg = open_window(gui)
    smallest, who = pg.evaluate(SMALLEST)
    assert smallest >= 12, (smallest, who)


def test_a_card_has_ten_px_corners(gui):
    pg = open_window(gui)
    assert pg.locator(".ork-card").first.evaluate("(e) => getComputedStyle(e).borderTopLeftRadius") == "10px"
