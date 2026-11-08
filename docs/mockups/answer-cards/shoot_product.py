"""The product's lifted question as it is (spec 158 F), no mockup layer: the camera of shoot.py pointed at the page itself, at 1440 x 900, with the ways' lines the test host writes.

    MOCK_OUT=docs/mockups/answer-cards/shots PYTHONPATH=. uv run --extra dev --extra browser --extra gui \
        pytest -q -p tests.conftest -p no:xdist docs/mockups/answer-cards/shoot_product.py"""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import pytest  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401
from tests.test_answer_cards_browser import WaysHost  # noqa: E402

OUT = Path(os.environ["MOCK_OUT"])


def test_shots(gui):
    server, browser = gui
    h = WaysHost()
    pg = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.route_web_socket("**/ws*", h.on_socket)
    pg.goto(server.url)
    pg.locator(".hand-card").first.wait_for(state="attached", timeout=WAIT_MS)
    pg.wait_for_timeout(2500)
    OUT.mkdir(parents=True, exist_ok=True)
    pg.locator('.hand .hand-card[data-kind="asks"][data-goal="phones"]').first.click(position={"x": 10, "y": 20})
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    pg.mouse.move(5, 5)
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "product-question.png"))
