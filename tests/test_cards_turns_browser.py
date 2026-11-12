"""**A card's turns in the hand and the Dropped pile** (goal 170, decisions §298.7, §298.8; goal 171 G), on mocks (`?mock=1`): the host answers `ideas.turns` (the moves that wait,
read from the Board's pages: gui/ideas_mats.py) and the recording holds that answer, but the hand deals no turn card from it until goal 171's stage K, so none is drawn and none is an
example. The Dropped pile holds this page's own drops only (the host keeps no list of them): a goal dropped lies face down, spreads face up with *Take back*, which sends `ideas.take_back`
and puts it out of the pile. The cases that pressed a turn card (a rated card ringed red with its tokens and four ways, *Drop* sending `ideas.drop`, a spec rated starting with its cost,
*Change it* sending the words, the two dropped goals the mock laid) laid cards only the mock's `proposed.turns` held; they come back in stage K, which deals them from `ideas.turns`."""
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
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => [x.name, x.args]))"
HAND = ".frame-hand button.hand-card"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal]").first.wait_for(timeout=15000)


def sent(pg, name):
    return [a for n, a in pg.evaluate(SENT) if n == name]


def test_the_host_answers_ideas_turns_from_the_recording_and_the_hand_deals_no_turn_card_yet(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        got = pg.evaluate("() => import('/static/js/link.js').then((l) => l.command('ideas.turns', {}))")
        assert got and got["turns"] and all({"goal", "kind", "at"} <= set(t) for t in got["turns"])         # the host's own answer, recorded
        assert pg.locator(f"{HAND}[data-kind=turn]").count() == 0 and pg.locator(f"{HAND}[data-kind=battle]").count() == 0
        assert "ideas.turns" not in [n for n, _ in pg.evaluate(SENT)]                                      # answered, never "not sent"
        b.close()


def test_a_goal_dropped_lies_face_down_in_the_dropped_pile_where_take_back_puts_it_out(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pile = pg.locator("[data-pile=dropped]")
        assert pile.count() == 0                                                                           # nothing dropped, no pile
        slug = pg.locator(".cards-lanes .cards-s[data-goal]").first.get_attribute("data-goal")
        pg.evaluate("(slug) => import('/static/js/cards/dropped.js').then((m) => m.dropGoal(slug))", slug)
        pile.wait_for()
        assert pile.locator(".cards-dropped__pile").is_visible() and pile.locator(".cards-s").count() == 0      # face down: no card face, no number
        assert pile.locator("[data-plate=dropped]").inner_text().strip() == "Dropped"
        pg.locator("[data-plate=dropped]").click()                                                         # the pile spreads, its cards face up with their last tokens
        assert pg.locator("[data-pile=dropped] .cards-dropped__one").count() == 1
        pg.locator(f"[data-dropped='{slug}'] [data-act=take_back]").click()
        assert sent(pg, "ideas.take_back") == [{"slug": slug}]
        pg.wait_for_function("() => !document.querySelector('[data-pile=dropped] .cards-dropped__one')", timeout=5000)
        b.close()
