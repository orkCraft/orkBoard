"""**The table's look on the desktop** (docs/specs/160-the-tables-look-and-the-rooms-things.md E, decisions §268, §269, §275), in a real browser at 1280 x 800: the pane wears the open party's felt (`data-party` from the open tab, the Orkmaster's the wood; the
computed background uses orkUI's felt tokens), the open tab has a pennant `.is-open` and each closed one a plain pennant, every closed tab's name is the light ink (its party's colour is only the rule under it, the pennant and the glow), the column's and
the discard's headings are bronze plaques, and an empty lane says whose it is on a flat plate in the party's plate colour. Screenshots to $TABLE_LOOK_SHOTS when it is set."""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost  # noqa: E402
from tests.test_window_desktop_browser import WindowHost  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["TABLE_LOOK_SHOTS"]) if os.environ.get("TABLE_LOOK_SHOTS") else None
# a token's colour as the browser computes it, read from a probe laid in the page
TOKEN = """(name) => { const e = document.createElement("i"); e.style.color = `var(${name})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }"""
BG = """(name) => { const e = document.createElement("i"); e.style.backgroundColor = `var(${name})`; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }"""


def open_window(gui):
    server, browser = gui
    host = WindowHost()
    rich = TableHost(rich=True, line=3)
    host.nodes = rich.nodes + [n for n in host.nodes if n["slug"] == "music"]
    pg = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".col-plab__t").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(1500)
    return pg


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def test_on_techs_tab_the_table_wears_techs_felt_and_the_open_tab_its_pennant(gui):
    pg = open_window(gui)
    pg.locator('.table-tab[data-tab="tech"]').click()
    pg.wait_for_timeout(800)
    pane = pg.locator("#table-pane")
    assert pane.get_attribute("data-party") == "ork"
    image = pane.evaluate("(e) => getComputedStyle(e).backgroundImage")
    for step in range(1, 6):                                                    # the five steps of the light, orkUI's tokens
        assert pg.evaluate(BG, f"--ork-felt-ork-{step}") in image, step
    open_cells = pg.locator(".table-tabcell.is-open")
    assert open_cells.count() == 1
    assert open_cells.locator(".ork-pennant.is-open").count() == 1
    closed = pg.locator(".table-tabcell:not(.is-open)")
    assert closed.count() >= 3
    for i in range(closed.count()):
        assert closed.nth(i).locator(".ork-pennant:not(.is-open)").count() == 1
    top = pg.locator(".table-tabcell.is-open .ork-pennant").bounding_box()["y"]
    assert top >= 4                                                             # clear of the window's top edge
    shot(pg, "tech")


def test_the_orkmasters_tab_is_the_wood_and_a_closed_tabs_name_is_the_light_ink(gui):
    pg = open_window(gui)
    pane = pg.locator("#table-pane")
    assert pane.get_attribute("data-party") == "orkmaster"
    image = pane.evaluate("(e) => getComputedStyle(e).backgroundImage")
    assert pg.evaluate(BG, "--ork-felt-orkmaster-1") in image
    ink = pg.evaluate(TOKEN, "--ork-ink")
    names = pg.locator(".table-tab:not(.is-off) .table-tab__main")
    assert names.count() >= 3
    for i in range(names.count()):
        assert names.nth(i).evaluate("(e) => getComputedStyle(e).color") == ink, names.nth(i).inner_text()
    pg.locator('.table-tab[data-tab="tech"]').click()
    pg.wait_for_timeout(800)
    assert pg.locator(".col-head__nm").evaluate("(e) => getComputedStyle(e).color") == ink          # the Orkmaster's name, closed
    assert pg.locator(".col-head > .ork-pennant:not(.is-open)").count() == 1
    shot(pg, "orkmaster-closed")


def test_the_headings_are_plaques_and_an_empty_lane_says_whose_it_is_on_a_plate(gui):
    pg = open_window(gui)
    heads = pg.locator(".col-plab__t")
    assert heads.count() >= 1
    for i in range(heads.count()):
        assert "ork-plaque" in (heads.nth(i).get_attribute("class") or ""), heads.nth(i).inner_text()
    assert pg.locator(".release-lane__label.ork-plaque").inner_text().strip().lower() == "discard"
    free = pg.locator(".table-lane__free.ork-plate")
    assert free.count() >= 1
    plate = pg.evaluate(BG, "--ork-plate-orkmaster")
    for i in range(free.count()):
        text = free.nth(i).inner_text().strip()
        name = re.fullmatch(r"(.+) is free · throw a goal here or @(.+)", text)
        assert name and name.group(1) == name.group(2), text
        assert free.nth(i).evaluate("(e) => getComputedStyle(e).backgroundColor") == plate
    lane = pg.locator(".table-lane[data-free], .table-lane:has(.table-lane__free)").first
    assert lane.get_attribute("data-race") in {"ork", "knight", "elf", "undead", "goblin", "gnome"}
    shot(pg, "orkmaster")
