"""The product's window at 1280 x 800 on the Orkmaster's tab and on Tech's (spec 160 E): a camera, not a test.

    PRODUCT_OUT=docs/mockups/table-look/shots PYTHONPATH=. uv run --extra dev --extra browser --extra gui pytest -q -p tests.conftest -p no:xdist docs/mockups/table-look/shoot_product.py
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from tests.browser_kit import WAIT_MS, gui  # noqa: F401
from tests.test_window_desktop_browser import WindowHost
from tests.test_table_desktop_browser import TableHost

OUT = Path(os.environ.get("PRODUCT_OUT", "docs/mockups/table-look/shots"))


def host():
    h = WindowHost()
    rich = TableHost(rich=True, line=3)
    h.nodes = rich.nodes + [n for n in h.nodes if n["slug"] == "music"]
    return h


def test_shots(gui):
    server, browser = gui
    pg = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
    pg.route_web_socket("**/ws*", host().on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(2500)
    OUT.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(OUT / "product-orkmaster.png"))
    pg.locator('.table-tab[data-tab="tech"]').click()
    pg.wait_for_timeout(1800)
    pg.mouse.move(640, 790)
    pg.screenshot(path=str(OUT / "product-tech.png"))
