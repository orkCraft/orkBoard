"""**A leader's question, from its lane to the hand, answered in an L** (goal 170; decisions §145: the hand is what the person
decides): on mocks a leader's post that asks the person is an M card with *Answer in hand*; pressed, the question's card of the
hand opens as an L over the table (js/cards/ask.js, the mockup docs/mockups/table-cards/ ?open=ask): the question, its ways
numbered 1–4 with the leader's pick marked, *Your own words…* last, and what the old face had beyond the ways as buttons. A way
sends what the hand's own face sends (kept by the mock, never sent); keys 1–4 play a way; Esc and Close put it away and the focus
goes back to the card it came from. The mock's example lays the question both in the lane and in the hand
(js/mock/parts/examples.js)."""
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
SENT = """() => import("/static/js/mock/mocklink.js").then((m) => m.sent.value.map((x) => ({ name: x.name, args: x.args })))"""
CARD = ".frame-hand button.hand-card[data-kind='talk']"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def _page(p, page_url):
    b = launch(p)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(page_url + "?mock=1")
    pg.locator(".cards-m.is-asks").first.wait_for(timeout=15000)
    return b, pg


def _example_card(pg):
    """The hand's card of the example question (the one the lane's M asks too)."""
    return pg.locator(CARD, has_text="Which way does the table open first").first


def test_answer_in_hand_opens_the_question_as_an_l_with_its_ways(page_url):
    with sync_playwright() as p:
        b, pg = _page(p, page_url)
        pg.locator(".cards-m.is-asks").first.get_by_role("button", name="Answer in hand").click()
        l = pg.locator(".cards-ask")
        l.wait_for(timeout=5000)
        assert pg.locator("button.q-card").count() == 0, "the old face over the pane is not opened"
        assert "Which way does the table open first" in l.inner_text()
        assert l.get_by_text("Why the tokens").count() in (0, 1)
        assert [k.inner_text() for k in l.locator(".cards-way__k").all()] == ["1", "2", "3", "4"]
        ways = l.locator(".cards-way")
        assert ways.nth(0).get_attribute("data-pick") == "1" and "pick" in ways.nth(0).inner_text()
        assert "Your own words" in ways.nth(3).inner_text()
        assert pg.evaluate("document.activeElement.matches('.cards-way.is-pick')")
        for name in ("Close", "Put it back"):
            assert l.get_by_role("button", name=name).is_visible()
        assert l.get_by_role("button", name="Let ", exact=False).first.is_visible()      # what the old face had: the leader decides
        # Esc puts it away and the focus is on the hand's card it came from
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(200)
        assert pg.locator(".cards-ask").count() == 0
        assert pg.evaluate("document.activeElement.matches('.frame-hand button.hand-card')")
        # Close does the same
        _example_card(pg).click()
        l.wait_for(timeout=5000)
        l.get_by_role("button", name="Close").click()
        pg.wait_for_timeout(200)
        assert pg.locator(".cards-ask").count() == 0
        assert pg.evaluate("document.activeElement.matches('.frame-hand button.hand-card')")
        b.close()


def test_key_2_sends_the_second_way_as_the_hands_face_sends_it(page_url):
    with sync_playwright() as p:
        b, pg = _page(p, page_url)
        _example_card(pg).focus()
        pg.keyboard.press("Enter")
        l = pg.locator(".cards-ask")
        l.wait_for(timeout=5000)
        assert "dealer" in l.locator(".cards-way").nth(1).inner_text().lower()
        first = l.locator(".cards-ask__q").inner_text()
        pg.keyboard.press("2")
        pg.wait_for_timeout(300)
        calls = lambda: [x for x in pg.evaluate(SENT) if x["name"] in ("ideas.talk_answer", "ideas.answer")]
        for _ in range(6):                               # a goal's questions come one after another: the answers go together after the last
            if not pg.locator(".cards-ask").count():
                break
            assert calls() == [] and l.locator(".cards-ask__q").inner_text() != first
            pg.keyboard.press("1")
            pg.wait_for_timeout(300)
        assert pg.locator(".cards-ask").count() == 0
        sent = calls()
        assert len(sent) == 1, sent
        args = sent[0]["args"]
        assert sent[0]["name"] == "ideas.talk_answer" and args["idea"] and args["answers"][0] == {"id": "page-example", "pick": 1}, args       # questioncard.js sendRow, as the hand's face sends it
        b.close()


def test_the_leaders_pick_is_one_press_and_own_words_go_as_text(page_url):
    with sync_playwright() as p:
        b, pg = _page(p, page_url)
        _example_card(pg).click()
        l = pg.locator(".cards-ask")
        l.wait_for(timeout=5000)
        l.get_by_role("button", name="Your own words").click()
        pg.locator(".cards-ask__field").fill("Both, the lanes narrower")
        pg.keyboard.press("Escape")                      # the field closes first, the L stays
        assert pg.locator(".cards-ask").count() == 1 and pg.locator(".cards-ask__field").count() == 0
        pg.keyboard.press("4")                           # key 4 is *Your own words…*
        pg.locator(".cards-ask__field").fill("Both, the lanes narrower")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(400)
        for _ in range(6):                               # the goal's other questions: its leader's pick each
            if not pg.locator(".cards-ask").count():
                break
            pg.keyboard.press("1")
            pg.wait_for_timeout(300)
        sent = [x for x in pg.evaluate(SENT) if x["name"] == "ideas.talk_answer"]
        assert len(sent) == 1 and sent[0]["args"]["answers"][0] == {"id": "page-example", "text": "Both, the lanes narrower"}, sent
        b.close()
