"""**The hand as whole cards** (goal 170, stage M): on mocks (`?mock=1`) the hand's cards are S cards, upright 2.5:3.5, each wholly
inside the hand (no half-hidden rise), the card that asks lifted and ringed with its "!"; pressing a question card opens its ways
(the hand's own answer UI). The cards of the hand as it was (cut by the hand's rim) are not drawn on the table of cards."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
BOXES = """() => { const h = document.querySelector('.frame-hand').getBoundingClientRect();
  return { hand: [h.top, h.bottom], old: !!document.querySelector('.hand-card--face'),
    cards: [...document.querySelectorAll('.frame-hand button.hand-card--stop')].map((c) => { const r = c.getBoundingClientRect();
    return { w: r.width, h: r.height, top: r.top, bottom: r.bottom, asks: c.classList.contains('is-asks'), bang: !!c.querySelector('.hands-asks'), goal: c.dataset.goal }; }) }; }"""
ALERT = """() => { const d = document.createElement('i'); d.style.color = 'var(--ork-alert)'; document.body.append(d);
  const c = getComputedStyle(d).color; d.remove(); return c; }"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def test_the_hands_cards_are_whole_s_cards_and_the_asking_one_is_ringed(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        pg.locator(".frame-hand button.hand-card--stop").first.wait_for(timeout=15000)
        pg.wait_for_timeout(800)
        got = pg.evaluate(BOXES)
        assert len(got["cards"]) >= 3 and not got["old"]
        assert got["hand"][1] - got["hand"][0] < 230                      # a row for whole cards, not the whole window
        for c in got["cards"]:
            assert abs(c["w"] / c["h"] - 2.5 / 3.5) < 0.03, c
            assert 100 <= c["w"] <= 140, c
            assert c["top"] >= got["hand"][0] - 12 and c["bottom"] <= got["hand"][1] + 1, (c, got["hand"])      # wholly in the hand's row (a lifted one by a few px)
        asking = [c for c in got["cards"] if c["asks"]]
        assert asking and all(c["bang"] for c in asking)
        ring = pg.locator(".frame-hand button.hand-card--stop.is-asks").first.evaluate("(e) => getComputedStyle(e).borderTopColor")
        assert ring == pg.evaluate(ALERT)
        b.close()


def test_pressing_a_question_card_opens_no_l_and_its_ways_are_cards(page_url):
    """Decisions §296.2: no L over the table for a question; its ways are cards (a talk question's lie by its question today, q-choose)."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        card = pg.locator(".frame-hand button.hand-card--stop.is-asks").first
        card.wait_for(timeout=15000)
        card.click()
        pg.locator(".q-choose__row").first.wait_for(timeout=5000)
        assert pg.locator(".cards-l").count() == 0
        b.close()
