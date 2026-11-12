"""**The other five spreads** (goal 170, docs/mockups/spreads/): who says what on a goal, what each card costs, which of two matters more,
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

from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => x.name))"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
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


def test_the_dispute_opens_from_a_goals_l_with_the_leaders_views_and_their_ways_in_the_hand(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(".cards-wait .cards-s").first.click()
        pg.get_by_role("button", name="Who says what").click()
        sp = spread_of(pg, "dispute")
        assert sp.locator(".sp-voice").count() >= 2 and sp.locator(".sp-dispute > .sp-card.is-xl").count() == 1
        assert sp.locator(".sp-dispute .cards-tok").count() >= 2 * 2            # the goal's tokens and each view's own
        ways = sp.locator(".sp-cards button.cards-s")
        assert ways.count() == sp.locator(".sp-voice").count() + 1                # each leader's way, and *Your own words…*
        assert "Your own words" in ways.last.inner_text()
        pg.keyboard.press("Tab")
        assert pg.evaluate("document.activeElement.tagName") == "BUTTON"
        closes_with_esc(pg)
        b.close()


def test_a_way_played_is_only_kept_by_the_mock_and_key_1_plays_the_first(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(".cards-wait .cards-s").first.click()
        pg.get_by_role("button", name="Who says what").click()
        spread_of(pg, "dispute")
        pg.keyboard.press("1")
        assert pg.locator(".sp-veil").count() == 0
        assert "ideas.answer" in pg.evaluate(SENT)                                # the goal asks a question: the existing answer command
        b.close()


def test_your_own_words_open_a_field_and_send_them(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(".cards-wait .cards-s").first.click()
        pg.get_by_role("button", name="Who says what").click()
        sp = spread_of(pg, "dispute")
        sp.get_by_role("button", name="Your own words").click()
        sp.get_by_role("textbox", name="Your own words").fill("Both, in turn")
        sp.get_by_role("button", name="Send these words").click()
        assert pg.locator(".sp-veil").count() == 0 and "ideas.answer" in pg.evaluate(SENT)
        b.close()


def test_the_dispute_opens_from_a_leaders_post_about_a_goal_three_leaders_spoke_of(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator("article.cards-m .post-card__text", has_text="Doubts Product").first.click()       # a concern's mat (decisions §297.2)
        sp = spread_of(pg, "dispute")
        assert sp.locator(".sp-voice").count() == 3 and sp.locator(".sp-cards button.cards-s").count() == 4
        closes_with_esc(pg)
        b.close()


def test_the_cost_opens_from_the_deck_with_potions_costs_and_a_card_the_tools_cannot_pay(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="What each card costs").click()
        sp = spread_of(pg, "cost")
        assert sp.locator(".sp-pots .ork-potion").count() == 2 and "example" in sp.inner_text()          # the costs are the mock's, marked
        assert sp.locator(".sp-card .sp-cost").count() >= 3 and "about 12% of Claude" in sp.inner_text()
        assert sp.locator(".sp-card.is-muted").count() == 1 and "18% left" in sp.inner_text() and "play it on Claude" in sp.inner_text()
        assert sp.get_by_role("button", name="Play", exact=False).first.is_visible()
        sp.locator(".sp-card.is-muted").click()                                         # the card that cannot be paid: its two ways out in the hand
        assert sp.get_by_role("button", name="on Claude", exact=False).is_visible() and sp.get_by_role("button", name="Wait for 04:00").is_visible()
        sp.get_by_role("button", name="Wait for 04:00").click()
        assert pg.locator(".sp-veil").count() == 0 and "ideas.route_later" in pg.evaluate(SENT)
        b.close()


def test_the_duel_sets_goals_into_the_order_by_pairs_and_sends_it_when_kept(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.get_by_role("button", name="Weigh two at a time").click()
        sp = spread_of(pg, "duel")
        assert sp.locator(".sp-dispute, .sp-card.is-xl").count() == 2 and sp.locator(".sp-thick").count() == 1 and sp.locator(".sp-ladder .sp-rung").count() >= 3
        assert "still to weigh" in sp.inner_text() and not any(ch.isdigit() for ch in sp.locator(".sp-deckl").inner_text())       # a pile's thickness, no number
        rungs = sp.locator(".sp-ladder .sp-rung:not(.is-gap)").count()
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
