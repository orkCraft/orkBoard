"""**A card's moves in the hand and the Dropped pile** (goal 170, decisions §298.7, §298.8; goal 171 G and K), on mocks (`?mock=1`): the host answers `ideas.turns` (the moves that wait, read from the Board's
pages: gui/ideas_mats.py); the test lays it as a host would (tests/mock_kit.py `lay_turns`) and the hand deals one card a goal from it: a goal that asks lifts its ways, a goal whose Talk is said or whose
spec is written opens its mat, where a Drop lies in the hand with its Undo. The Dropped pile holds this page's own drops only (the host keeps no list of them): a goal dropped lies face down, spreads face up
with *Take back*, which sends `ideas.take_back` and puts it out of the pile, its card back in the hand. Of the cases stage G removed, these come back here: a card ringed with its tokens and its ways, *Drop*
sending `ideas.drop` with the pile spread. Not back: a spec rated *Start* with its cost and *Change it* sending the words (the host has no command that starts a goal or changes one in its turn, and prices none
before it is played), and the two dropped goals the mock laid (the host keeps no list of them)."""
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
ALERT = """() => { const d = document.createElement('i'); d.style.color = 'var(--ork-alert)'; document.body.append(d);
  const c = getComputedStyle(d).color; d.remove(); return c; }"""
ASKS, TALK = "172-example-1", "173-example-2"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal]").first.wait_for(timeout=15000)
    pg.locator(f"{HAND}[data-kind=turn]").first.wait_for(timeout=15000)


def sent(pg, name):
    return [a for n, a in pg.evaluate(SENT) if n == name]


def test_the_host_answers_ideas_turns_and_a_card_that_waits_is_ringed_with_its_tokens_and_lifts_its_ways(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        got = pg.evaluate("() => import('/static/js/link.js').then((l) => l.command('ideas.turns', {}))")
        assert got and got["turns"] and all({"goal", "kind", "at"} <= set(t) for t in got["turns"])         # the host's own answer
        assert "ideas.turns" not in [n for n, _ in pg.evaluate(SENT)]                                      # answered, never "not sent"
        card = pg.locator(f"{HAND}[data-kind=turn][data-goal='{ASKS}']")
        assert card.evaluate("(el) => getComputedStyle(el).borderTopColor") == pg.evaluate(ALERT)          # ringed as a card that asks is
        assert card.locator(".hands-toks .cards-ct").count() >= 1 and card.locator(".cards-sq").count() >= 1      # with its leaders' tokens
        assert pg.locator(f"{HAND}[data-kind=battle]").count() == 0                                        # the host lays no battle: none is drawn
        card.click()
        assert pg.locator(".hand-ways-row [data-way]").count() == 4                                        # its question's three ways and one of its own words
        text = pg.locator(".hand-ways-row").inner_text()
        assert "Keep it" in text and "In your own words" in text
        pg.locator("[data-way=own]").click()                                                               # its own words in a field, sent as the answer
        pg.locator(".hand-pen textarea").fill("Make it two coins")
        pg.keyboard.press("Enter")
        assert sent(pg, "ideas.answer_way") == [{"slug": ASKS, "answers": ["Make it two coins"], "from": "hand"}]
        b.close()


def test_drop_sends_ideas_drop_and_the_goal_lies_face_down_in_the_dropped_pile_where_take_back_brings_its_card_back(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{TALK}']").click()                                  # its mat opens: the hand is its ways
        pg.locator(".mathand [data-way=drop]").click()
        assert sent(pg, "ideas.drop") == [{"slug": TALK, "from": "hand"}]
        pile = pg.locator("[data-pile=dropped]")
        pile.wait_for()
        assert pile.locator(".cards-dropped__pile").is_visible() and pile.locator(".cards-s").count() == 0      # face down: no card face, no number
        assert pile.locator("[data-plate=dropped]").inner_text().strip() == "Dropped"
        assert pg.locator(f"{HAND}[data-goal='{TALK}']").count() == 0                                      # its card left the hand
        pg.locator("[data-plate=dropped]").click()                                                         # the pile spreads, its cards face up with their last tokens
        assert pg.locator("[data-pile=dropped] .cards-dropped__one").count() == 1 and pg.locator(f"[data-dropped='{TALK}'] .cards-ct").count() >= 2
        pg.locator(f"[data-dropped='{TALK}'] [data-act=take_back]").click()
        assert sent(pg, "ideas.take_back") == [{"slug": TALK}]
        pg.wait_for_function("() => !document.querySelector('[data-pile=dropped] .cards-dropped__one')", timeout=5000)
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{TALK}']").wait_for(timeout=5000)                   # its card is back in the hand
        b.close()
