"""Spec 171 F in a real browser, on the `gui` fixture's Board, `?table=cards` and no `?mock=1`: the page fetches nothing under js/mock/ or static/mock/, Product's Jobs to be done lays its zones
empty with who fills each (the host's `fills`), and no word on the page ends in « · example»."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser


def open_cards(gui):
    from orkboard.realm import ideas
    server, browser = gui
    root = server.host.ideas.root()
    if not ideas.track_page(root, "product"):
        ideas.add_track(root, "Product")
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    seen: list[str] = []
    pg.on("request", lambda r: seen.append(r.url))
    pg.goto(server.url + "&table=cards" if "?" in server.url else server.url + "?table=cards")
    pg.wait_for_selector(".cards-lane", timeout=WAIT_MS)
    return pg, seen


def test_nothing_under_the_mock_is_fetched_and_no_word_says_example(gui):
    pg, seen = open_cards(gui)
    pg.wait_for_timeout(500)
    assert not [u for u in seen if "/mock/" in u], [u for u in seen if "/mock/" in u]
    assert "· example" not in pg.inner_text("body")
    pg.close()


def test_products_jobs_lie_empty_each_saying_who_fills_it(gui):
    pg, _seen = open_cards(gui)
    pg.locator('.cards-lane[data-party="product"] [data-value="jtbd"]').click(timeout=WAIT_MS)
    pg.wait_for_selector('.tb[data-framework="jtbd"]', timeout=WAIT_MS)
    zones = pg.locator(".tb-empty")
    assert {z.get_attribute("data-empty") for z in zones.all()} >= {"personas", "job", "jobs"}
    words = " ".join(zones.all_inner_texts())
    assert "Product lays its jobs" in words and "Product asks the person who the people are" in words
    assert pg.locator(".tb-card").count() == 0
    assert "· example" not in pg.inner_text("body")
    pg.close()
