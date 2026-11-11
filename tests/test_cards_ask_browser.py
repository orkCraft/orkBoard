"""**A leader's question, from its lane to the hand** (goal 170; decisions §145: the hand is what the person decides): on mocks a
leader's post that asks the person is an M card with *Answer in hand*; pressed, the question's card in the hand opens with its
ways, the focus on the leader's pick; a way played sends `ideas.answer` (kept by the mock, never sent). The mock's example lays
the question both in the lane and in the hand (js/mock/parts/examples.js)."""
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


def test_answer_in_hand_opens_the_questions_card_and_a_way_sends_the_answer(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        ask = pg.locator(".cards-m.is-asks").first
        ask.wait_for(timeout=15000)
        btn = ask.get_by_role("button", name="Answer in hand")
        assert btn.is_visible()
        btn.click()
        pick = pg.locator("button.q-card[data-pick='1']")
        pick.wait_for(timeout=5000)
        assert pg.evaluate("document.activeElement.matches('button.q-card[data-pick=\"1\"]')")
        assert pg.get_by_text("Which way does the table open first", exact=False).first.is_visible()
        # the L of the same post says it too, and leads to the same card
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
        b.close()
