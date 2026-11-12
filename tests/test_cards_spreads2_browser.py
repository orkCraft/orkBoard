"""**The other spreads** (goal 170, docs/mockups/spreads/): what each card costs, which of two matters more,
the new goals sorted, and the Orkmaster's deal, drawn over the table of cards on mocks (`?mock=1`). Each opens from its act (a goal's L or the
deck's), shows its parts, has its acts as buttons with their words, plays by its keys, says what it sends (the mock keeps it) and closes with
Esc. The proposed commands (`ideas.order`, `ideas.sort`, `ideas.way`, `ideas.tool_for`) are logged by the mock, never sent."""
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
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => x.name))"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, lambda d: (mock_kit.lay_standard(d), mock_kit.lay_limits(d)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal]").first.wait_for(timeout=15000)


def spread_of(pg, name):
    s = pg.locator(f"[data-spread={name}]")
    s.wait_for()
    return s


def closes_with_esc(pg):
    pg.keyboard.press("Escape")
    assert pg.locator(".sp-veil").count() == 0


def test_a_concern_with_no_mat_opens_as_an_l_of_words_and_the_retired_who_says_what_is_gone(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator("article.cards-m .post-card__text", has_text="Doubts Product").first.click()       # a concern: decisions §298 retires its mat
        pg.locator(".cards-l").wait_for(timeout=5000)
        assert pg.locator(".sp-veil").count() == 0
        pg.keyboard.press("Escape")
        pg.locator(".cards-wait .cards-s").first.click()
        assert pg.get_by_role("button", name="Who says what").count() == 0
        b.close()


def test_the_cost_opens_from_the_deck_with_the_tools_left_and_each_card_saying_its_cost_is_not_known_yet(page_url):
    """Was: potions, costs and a card the tools cannot pay (*18% left*, *play it on Claude*, *Wait for 04:00*), all laid by the mock's `proposed.costs`. The host
    prices no goal before it is played (spec 171 F): the shares lie empty, saying who fills them; the potions are the host's own limits (laid here in the
    snapshot). The unpaid card and its two ways out wait for the costs' mat (its own goal); `ideas.route_later` is the host's, held by tests/test_gui_route.py."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="What each card costs").click()
        sp = spread_of(pg, "cost")
        assert sp.locator(".sp-pots .ork-potion").count() == 2 and "62%" in sp.inner_text() and "18%" in sp.inner_text()          # the tools' left today, the host's limits
        assert sp.locator(".sp-card .sp-cost").count() == 0                                       # no share is laid
        assert sp.locator(".sp-costw", has_text="Its cost is not known yet").count() >= 3 and sp.locator(".sp-card.is-muted").count() == 0
        play = sp.get_by_role("button", name="Play", exact=False).first
        assert play.is_visible()
        play.click()
        assert pg.locator(".sp-veil").count() == 0 and "ideas.start" in pg.evaluate(SENT)
        b.close()


def test_the_duel_sets_goals_into_the_order_by_pairs_and_sends_it_when_kept(page_url):
    """The order so far starts with the first goal alone (the host keeps no order of goals); the pairs build it."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="Weigh two at a time").click()
        sp = spread_of(pg, "duel")
        assert sp.locator(".sp-dispute, .sp-card.is-xl").count() == 2 and sp.locator(".sp-thick").count() == 1 and sp.locator(".sp-ladder .sp-rung").count() >= 2
        assert "still to weigh" in sp.inner_text() and not any(ch.isdigit() for ch in sp.locator(".sp-deckl").inner_text())       # a pile's thickness, no number
        rungs = sp.locator(".sp-ladder .sp-rung:not(.is-gap)").count()
        assert rungs == 1
        pg.keyboard.press("ArrowLeft")
        pg.keyboard.press("ArrowRight")
        pg.keyboard.press("ArrowLeft")
        assert sp.locator(".sp-ladder .sp-rung:not(.is-gap)").count() > rungs        # the goals asked about are set in the order
        sp.get_by_role("button", name="Skip").is_visible()
        sp.get_by_role("button", name="Done: keep this order").click()
        assert pg.locator(".sp-veil").count() == 0 and "ideas.order" in pg.evaluate(SENT)
        b.close()


def test_the_duel_skips_a_pair_with_the_down_key_and_has_its_buttons_with_words(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="Weigh two at a time").click()
        sp = spread_of(pg, "duel")
        before = sp.locator(".sp-card.is-xl .sp-card__name").first.inner_text()
        pg.keyboard.press("ArrowDown")
        assert sp.locator(".sp-card.is-xl .sp-card__name").first.inner_text() != before
        assert sp.get_by_role("button", name="This one").count() == 2
        closes_with_esc(pg)
        b.close()


def test_the_sort_puts_new_goals_on_three_piles_by_keys_takes_one_back_and_sends(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="Sort the new goals").click()
        sp = spread_of(pg, "sort")
        assert sp.locator(".sp-bin").count() == 3 and sp.locator(".sp-thick").count() == 1 and sp.locator(".sp-col .sp-card.is-xl").count() == 1
        first = sp.locator(".sp-card__name").first.inner_text()
        assert sp.get_by_role("button", name="To work").is_visible() and sp.get_by_role("button", name="Later").is_visible() and sp.get_by_role("button", name="Drop").is_visible()
        pg.keyboard.press("1")
        assert sp.locator(".sp-card__name").first.inner_text() != first and sp.locator(".sp-bin.is-work.is-full").count() == 1
        pg.keyboard.press("2")
        sp.get_by_role("button", name="Back one").click()
        assert sp.locator(".sp-bin.is-later.is-full").count() == 0
        sp.get_by_role("button", name="Drop", exact=False).first.click()
        sp.get_by_role("button", name="Done: send this sorting").click()
        assert pg.locator(".sp-veil").count() == 0 and "ideas.sort" in pg.evaluate(SENT)
        b.close()


def test_the_deal_opens_from_a_goal_in_talks_l_and_the_deck_and_deals_the_route_on_its_chairs(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(".cards-wait .cards-s").first.click()
        pg.locator(".cards-l").get_by_role("button", name="The deal").click()
        sp = spread_of(pg, "deal")
        assert sp.locator(".sp-chair").count() >= 3 and sp.locator(".sp-chair[data-dealt='1']").count() == 2 and sp.locator(".sp-chair[data-dealt='0']").count() >= 1
        assert "not dealt" in sp.inner_text() and sp.locator(".sp-chair__ch").first.get_attribute("src").startswith("/ds/orkui/chair/chair-leader-")
        assert sp.locator(".sp-chair:disabled").count() == sp.locator(".sp-chair").count()      # nothing moves before *Change the deal*
        sp.get_by_role("button", name="Change the deal").click()
        sp.locator(".sp-chair[data-dealt='0']:not(:disabled)").first.click()
        assert sp.locator(".sp-chair[data-dealt='1']").count() == 3
        sp.get_by_role("button", name="Deal it").click()
        sent = pg.evaluate(SENT)
        assert pg.locator(".sp-veil").count() == 0 and "ideas.route_set" in sent and "ideas.route_start" in sent
        pg.get_by_role("button", name="The deal", exact=True).first.click()      # the deck's act
        spread_of(pg, "deal")
        closes_with_esc(pg)
        b.close()


def test_the_new_spreads_wear_orkuis_tokens_and_the_page_without_cards_has_none_of_them(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_timeout(1500)
        assert pg.locator(".sp-veil, .cards-deckacts, .cards-s").count() == 0
        b.close()
