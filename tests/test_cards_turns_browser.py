"""**A card's turns in the hand and the Dropped pile** (goal 170, decisions §298.7, §298.8), on mocks (`?mock=1`): a goal's idea rated and its spec rated
come to the hand as S cards with their craft tokens; pressed, their ways lie in the hand as cards; a risk that blocks holds *Play it* and says whose it is; *Drop* sends
`ideas.drop` and the goal lies in the discard's Dropped pile, face down, which spreads face up with *Take back*. The proposed commands are logged by the mock, never sent."""
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
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => [x.name, x.args]))"
HAND = ".frame-hand button.hand-card"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(f"{HAND}[data-kind=turn]").first.wait_for(timeout=15000)


def turn(pg, name):
    return pg.locator(f"{HAND}[data-kind=turn]", has_text=name)


def turns_are(pg, n, text=""):
    """The turn cards in the hand come to `n` (a card that leaves crumbles for a moment first)."""
    pg.wait_for_function("([sel, n, text]) => [...document.querySelectorAll(sel)].filter((e) => !e.classList.contains('is-gone') && e.textContent.includes(text)).length === n", arg=[f"{HAND}[data-kind=turn]", n, text], timeout=5000)


def sent(pg, name):
    return [a for n, a in pg.evaluate(SENT) if n == name]


def test_a_rated_card_comes_to_the_hand_ringed_red_with_its_tokens_and_its_four_ways(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        card = pg.locator(f"{HAND}[data-kind=turn][aria-label*='blocked']")
        assert card.count() == 1                                                          # a risk that blocks rings it and says so where its time is
        assert card.locator(".hands-toks .cards-ct").count() >= 2 and card.locator(".cards-sq[data-kind=b]").count() == 1
        assert "blocked" in card.inner_text() and card.evaluate("(el) => getComputedStyle(el).borderTopColor") != pg.locator(f"{HAND}[data-kind=turn]:not([aria-label*='blocked'])").first.evaluate("(el) => getComputedStyle(el).borderTopColor")
        card.click()
        assert pg.locator(".hand-ways-row [data-way]").count() == 4
        text = pg.locator(".hand-ways-row").inner_text()
        for way in ("Play it", "Change it", "Put off", "Drop"):
            assert way in text
        play = pg.locator("[data-way=play]")
        assert play.is_disabled() and "risk blocks it until" in play.inner_text()          # the leader whose risk it is
        play.click(force=True)
        assert sent(pg, "ideas.turn_play") == []
        b.close()


def test_drop_sends_ideas_drop_and_the_goal_lies_face_down_in_the_dropped_pile_where_take_back_brings_it_back(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pile = pg.locator("[data-pile=dropped]")
        assert pile.locator(".cards-dropped__pile").is_visible() and pile.locator(".cards-s").count() == 0      # face down: no card face, no number
        assert pile.locator("[data-plate=dropped]").inner_text().strip() == "Dropped"
        before = pg.locator(f"{HAND}[data-kind=turn]").count()
        card = pg.locator(f"{HAND}[data-kind=turn][aria-label*='blocked']")
        slug = card.get_attribute("data-goal")
        card.click()
        pg.locator("[data-way=drop]").click()
        assert sent(pg, "ideas.drop") == [{"slug": slug}]
        turns_are(pg, before - 1)                                                            # it leaves the hand
        pg.locator("[data-plate=dropped]").click()                                          # the pile spreads, its cards face up with their last tokens
        spread = pg.locator("[data-pile=dropped] .cards-dropped__one")
        assert spread.count() == 3 and pg.locator(f"[data-dropped='{slug}'] .cards-ct").count() >= 2
        pg.locator(f"[data-dropped='{slug}'] [data-act=take_back]").click()
        assert sent(pg, "ideas.take_back") == [{"slug": slug}]
        assert pg.locator("[data-pile=dropped] .cards-dropped__one").count() == 2
        turns_are(pg, before)                                                               # its turn is back in the hand
        b.close()


def test_the_mocks_two_dropped_goals_spread_and_a_spec_rated_card_starts_with_its_cost(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(".cards-dropped__pile").click()
        assert pg.locator(".cards-dropped__one").count() == 2 and pg.locator(".cards-dropped__one .cards-s").count() == 2
        spec = pg.locator(f"{HAND}[data-kind=turn]", has_text="The timer stops")
        assert spec.count() == 1
        spec.click()
        text = pg.locator(".hand-ways-row").inner_text()
        assert pg.locator(".hand-ways-row [data-way]").count() == 3 and "Change the spec" in text and "Drop" in text and "Put off" not in text
        start = pg.locator("[data-way=play]")
        assert start.inner_text().startswith("Start") and "about 25% of Codex" in start.inner_text()
        start.click()

        assert len(sent(pg, "ideas.turn_play")) == 1
        turns_are(pg, 0, "The timer stops")
        b.close()


def test_change_it_writes_the_change_in_a_field_and_sends_it_with_the_goal(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        turn(pg, "The timer stops").click()
        pg.locator("[data-way=own]").click()
        pg.locator(".hand-pen textarea").fill("Make it two coins")
        pg.keyboard.press("Enter")
        got = sent(pg, "ideas.turn_change")
        assert len(got) == 1 and got[0]["text"] == "Make it two coins" and got[0]["slug"].endswith("-example-1")
        b.close()
