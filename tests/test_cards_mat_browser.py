"""**A leader's mat** (goal 170; decisions §297): on mocks (`?mock=1`) a leader's M that is a change in its framework or a spread of it
shows its spread's shape and one line at its foot, and opens as that table or spread, the leader's words at its head; a word with
neither opens as an L of words. The closed list: a change in a framework → its table at the part; a change → *What changed*; a concern,
a question or views that differ → *Who says what*."""
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


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(p, page_url):
    b = launch(p)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(page_url + "?mock=1")
    pg.locator(".cards-m[data-mat='table']").first.wait_for(timeout=15000)
    return b, pg


def test_a_mat_shows_its_shape_and_one_line_never_a_picture_of_its_spread(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        mats = pg.evaluate("[...document.querySelectorAll('.cards-m[data-mat]')].map(m => [m.dataset.mat, m.querySelector('.cards-mat__shape').dataset.shape, m.querySelector('.cards-mat').innerText.trim()])")
        kinds = {m[0] for m in mats}
        assert {"table", "diff", "dispute"} <= kinds, mats
        assert ["table", "table", "Architecture: gui/"] in mats and ["diff", "diff", "What changed"] in mats
        assert pg.locator(".cards-m .tb-card, .cards-m .sp-card").count() == 0      # no table drawn in a mat
        b.close()


def test_a_framework_mat_lays_its_table_at_its_part_with_the_leaders_words_at_its_head(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        tb = pg.locator(".tb[data-framework='architecture']")
        tb.wait_for(timeout=5000)
        assert tb.get_attribute("data-at") == "gui/"
        assert "is-at" in tb.locator(".tb-card[data-card='gui/']").get_attribute("class")
        assert "gui/ is past its line" in tb.locator(".cards-said").inner_text()
        tb.locator(".tb-switch button", has_text="Feed").click()
        pg.locator(".cards-lanes").wait_for(timeout=5000)
        pg.locator(".tb-switch button", has_text="Architecture").first.click()       # laid by its switch: no words at its head
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=5000)
        assert pg.locator(".tb .cards-said").count() == 0 and pg.locator(".tb-card.is-at").count() == 0
        b.close()


def test_a_change_opens_what_changed_and_a_concern_who_says_what_no_l_of_words(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='diff']").first.click(position={"x": 30, "y": 20})
        pg.locator(".sp-veil[data-spread='diff']").wait_for(timeout=5000)
        assert pg.locator(".cards-l").count() == 0
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        pg.locator(".cards-m[data-mat='dispute']").first.focus()
        pg.keyboard.press("Enter")
        pg.locator(".sp-veil[data-spread='dispute']").wait_for(timeout=5000)
        assert pg.locator(".cards-l").count() == 0
        b.close()
