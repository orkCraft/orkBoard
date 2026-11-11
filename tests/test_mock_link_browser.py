"""**The page on mocks** (goal 170, stage M): `?mock=1` opens the real page with no host. js/link.js then opens no socket;
js/mock/mocklink.js gives the page the recorded snapshot (`static/mock/board.json`, tools/record_mock.py) and answers a
command from the recording; a command it does not hold is kept as what would have been sent, said once, never sent. A plate
says the page runs on mocks; pressed, it lists what would have gone. Without `?mock=1` the mock is never loaded."""
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
COUNT = """() => { window.__sockets = 0; const R = window.WebSocket;
  window.WebSocket = function (...a) { window.__sockets++; return new R(...a); }; window.WebSocket.prototype = R.prototype; }"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def test_the_page_on_mocks_draws_the_recorded_board_with_no_socket_and_sends_nothing(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.add_init_script(f"({COUNT})()")
        pg.goto(page_url + "?mock=1")
        plate = pg.locator(".mock-plate__b")
        plate.wait_for(timeout=15000)
        assert "Nothing is sent." in plate.inner_text()
        assert pg.evaluate("window.__sockets") == 0
        assert pg.get_by_text("Tech", exact=True).first.is_visible()
        # a change the recording does not hold is kept, never sent
        got = pg.evaluate("""() => import("/static/js/link.js").then((l) => l.command("ideas.answer", { slug: "x", n: 1, answer: "y" }))""")
        assert got is None
        plate.click()
        assert "ideas.answer" in pg.locator(".mock-plate__sent").inner_text()
        assert pg.get_by_text("Not sent: the page runs on mocks (ideas.answer)").count() == 1
        b.close()


def test_without_mock_the_page_never_loads_the_mock(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page()
        asked = []
        pg.on("request", lambda r: asked.append(r.url))
        pg.goto(page_url)
        pg.wait_for_timeout(1500)
        assert not [u for u in asked if "/mock/" in u and "plate.css" not in u]
        assert pg.locator(".mock-plate").count() == 0
        b.close()
