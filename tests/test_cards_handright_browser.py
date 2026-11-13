"""**The hand's right on the table of cards** (decisions §298.9, §298.6): two groups, *What you do* and *What you have*, and at the window's edge the
deck of blank cards, which opens the new goal's field by press and by the key N; no + card at the hand's left while goals exist; the Orkmaster's four
mats open their spreads."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests import mock_kit  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/?mock=1"
    s.shutdown()


def start(p, url):
    b = launch(p)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(url)
    pg.wait_for_selector(".cards-lane", timeout=15000)
    pg.wait_for_selector(".hr-group", timeout=15000)
    return b, pg




def test_the_deck_of_blank_cards_lies_at_the_edge_and_opens_the_field_by_press_and_by_n(page_url):
    with sync_playwright() as p:
        b, pg = start(p, page_url)
        assert pg.locator(".hand .hand-plus").count() == 0, "no + card at the hand's left while goals exist"
        deck = pg.locator("[data-blank-deck]")
        assert deck.get_attribute("aria-label") == "New goal" and "N" in deck.inner_text()
        top = pg.locator(".hr-blank__top").bounding_box()
        assert top["x"] + top["width"] > 1440, "its top card is half hidden past the edge"
        before = pg.locator(".hr-blank__top").evaluate("e => getComputedStyle(e).translate")
        deck.hover()
        pg.wait_for_timeout(400)
        assert pg.locator(".hr-blank__top").evaluate("e => getComputedStyle(e).translate") != before, "it rises when pointed at"
        deck.click()
        pg.wait_for_selector(".hand-field textarea, .hand-field__card textarea", timeout=5000)
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-field textarea", state="detached")
        pg.mouse.move(300, 300)
        pg.keyboard.press("n")
        pg.wait_for_selector(".hand-field textarea, .hand-field__card textarea", timeout=5000)
        assert pg.locator(".hand-field textarea").first.input_value() == "", "N opens the field and is not the goal's first letter"
        b.close()


def test_the_orkmasters_four_mats_open_their_spreads(page_url):
    with sync_playwright() as p:
        b, pg = start(p, page_url)
        lane = pg.get_by_role("group", name="The Orkmaster's mats")
        assert pg.locator(".cards-dealer .cards-lab", has_text="Its mats").count() == 1
        assert lane.locator(".cards-mat__shape").count() == 0                                           # no shape beside a mat's line
        for name in ("What each card costs", "Weigh two at a time", "Sort the new goals", "The deal"):
            btn = lane.get_by_role("button", name=name)
            btn.scroll_into_view_if_needed()
            btn.click()
            pg.wait_for_selector(".sp", timeout=5000)
            pg.keyboard.press("Escape")
            pg.wait_for_selector(".sp", state="detached", timeout=5000)
        b.close()
