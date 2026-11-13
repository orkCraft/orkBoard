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

from tests import mock_kit, narrow  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(p, page_url):
    b = launch(p)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(page_url + "?mock=1")
    pg.locator(".cards-m[data-mat='table']").first.wait_for(timeout=15000)
    return b, pg




# -- goal 171 stage J: the closed mats' slots and the three kinds of card (js/cards/slots.js, kind.js; decisions §299.5, §300.1, §300.4) ----------













# -- goal 171 stage H: the frame every mat lies in (js/cards/matframe.js, matframe.css; decisions §300.15) ---------------------------------

THREE = "163-products-tree-on-the-board"
CHRONICLE = "134-release-keeps-the-chronicle"       # done, no reviewer applies: every check of its gate can be green
RED = """async (slug) => { const link = await import("/static/js/link.js"), sp = await import("/static/js/cards/spreads/open.js");
  const names = ["Critical tests", "Tests of what it touched"];
  link.town.value = { ...link.town.value, main_checks: { [slug]: names.map((name, i) => ({ name, state: i ? "failed" : "passed", words: i ? "2 tests fail" : "312 passed" })) } };
  sp.openSpread({ kind: "gate", slug, from: document.querySelector(".cards-m, .cards-s") }); }"""






def test_tab_goes_through_the_mat_only_and_esc_gives_the_focus_back_to_the_card_that_opened_it(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m").first.focus()
        pg.evaluate(RED, THREE)
        pg.locator(".sp-veil[data-spread='gate']").wait_for(timeout=5000)
        seen = []
        for _ in range(8):
            pg.keyboard.press("Tab")
            seen.append(pg.evaluate("() => !!document.activeElement.closest('.sp-veil, .mathand')"))
        assert all(seen), seen
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        assert pg.evaluate("() => !document.querySelector('[inert]')")
        assert pg.evaluate("() => document.activeElement.matches('.cards-m, .cards-s')")
        b.close()




# -- goal 171 stage I: a mat's address, and on the phone the whole screen (js/cards/address.js; decisions §299.3, §300.3) -------------------------

def at_phone(p, page_url, hash_=""):
    b = launch(p)
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.goto(page_url + "?mock=1" + hash_)
    return b, pg


def test_a_mat_opened_has_its_address_and_a_reload_opens_it_again_on_the_phone(page_url):
    with sync_playwright() as p:
        b, pg = at_phone(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.wait_for(timeout=15000)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=5000)
        assert pg.evaluate("location.hash").startswith("#mat=table:") and ":architecture" in pg.evaluate("location.hash")
        assert pg.locator(".sp-shut").inner_text().strip() == "Back"
        narrow.no_sideways(pg)
        pg.reload()                                                                                         # the address opens it again
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=15000)
        assert pg.locator(".sp-shut").inner_text().strip() == "Back"
        pg.go_back()                                                                                        # the phone's Back puts it away
        pg.locator(".tb").wait_for(state="detached", timeout=5000)
        assert pg.evaluate("location.hash") == ""
        b.close()


def test_a_spread_has_its_address_esc_takes_it_off_and_the_card_opened_shows_one_line_not_a_row_of_mats(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        card = pg.locator(".cards-dealer .cards-row .cards-s[data-goal]").first
        card.wait_for(timeout=15000)
        slug = card.get_attribute("data-goal")
        card.click()
        assert pg.locator(".cards-l__acts button[data-lies]").count() == 1 and pg.locator(".cards-l__acts button", has_text="At the gate").count() <= 1       # one line, no row of mats
        assert pg.locator(".cards-l__lies").inner_text().startswith("Lies now at")
        pg.locator(".cards-l__lies button").click()
        pg.locator("[data-spread=track], [data-spread=gate]").wait_for(timeout=5000)
        assert pg.evaluate("location.hash").startswith("#mat=") and pg.evaluate("location.hash").endswith(":" + slug)
        pg.reload()
        pg.locator("[data-spread=track], [data-spread=gate]").wait_for(timeout=15000)
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        pg.wait_for_function("location.hash === ''")
        b.close()


def test_an_address_of_a_goal_the_board_does_not_have_opens_nothing(page_url):
    with sync_playwright() as p:
        b, pg = at_phone(p, page_url, "#mat=gate:no-such-goal")
        pg.locator(".cards-m").first.wait_for(timeout=15000)
        pg.wait_for_function("location.hash === ''")
        assert pg.locator(".sp-veil").count() == 0
        b.close()


@pytest.fixture(scope="module")
def turned_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/?mock=1"
    s.shutdown()






GREEN = RED.replace('state: i ? "failed" : "passed", words: i ? "2 tests fail" : "312 passed"', 'state: "passed", words: "312 passed"')
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => [x.name, x.args]))"


def test_the_gate_mat_opened_from_the_goals_card_seals_merge_into_main_with_from_mat(page_url):
    """Goal 113 B (H7): the seal sends `ideas.to_main {idea, sealed: true, from: "mat"}`; opened by its hand card it would send "hand" (`opened`)."""
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.evaluate(GREEN, CHRONICLE)
        seal = pg.locator(".mf-foot .mf-seal")
        seal.wait_for(timeout=5000)
        assert seal.get_attribute("aria-disabled") != "true", seal.inner_text()
        seal.click()
        pg.wait_for_function("() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.some((x) => x.name === 'ideas.to_main'))", timeout=15000)
        sent = [a for n, a in pg.evaluate(SENT) if n == "ideas.to_main"]
        assert sent == [{"idea": CHRONICLE, "sealed": True, "from": "mat"}], sent
        b.close()
