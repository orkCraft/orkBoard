"""**A battle** (goal 170, decisions §298.6), on mocks (`?mock=1`): the battle's card in the hand has the battle emblem for its picture, *vs <what>* under its name, *battle* in its corner
and its act *Settle it*; pressed, the Orkmaster's spread opens (the new card, the old ones, one row for each craft, the cost to undo under an old card, the four ways); a way sends
`ideas.battle_settle`; Esc closes it and the focus goes back. On a phone width the field stacks."""
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
CARD = ".frame-hand button.hand-card[data-kind=battle]"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(CARD).wait_for(timeout=15000)


def test_the_battle_card_in_the_hand_has_its_emblem_its_vs_line_its_corner_and_its_act(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        card = pg.locator(CARD)
        emblem = card.locator(".cards-emblem")
        assert emblem.count() == 1 and emblem.get_attribute("aria-hidden") == "true" and emblem.locator("i").count() == 3      # a card upright, two backs crossed behind it
        assert card.locator(".ork-race__head").count() == 0                                   # no leader's head: the emblem is its picture
        text = card.inner_text()
        assert "vs §240 and " in text and "battle" in text and "Settle it" in text
        assert card.evaluate("(el) => getComputedStyle(el.querySelector('.cards-emblem i.is-f')).borderTopWidth") == "1px"
        b.close()


def test_settle_it_opens_the_spread_with_the_new_card_the_old_ones_three_axes_and_the_cost_to_undo(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(CARD).click()
        sp = pg.locator("[data-spread=battle]")
        sp.wait_for()
        assert "A new card against two" in sp.inner_text() and "Read each axis" in sp.inner_text() and "It goes against a decision and a goal" in sp.inner_text()
        assert sp.locator(".bt-new .sp-card").count() == 1 and sp.locator(".bt-olds .bt-one").count() == 2
        assert sp.locator(".bt-decision .bt-sect").inner_text() == "§" and "§240" in sp.locator(".bt-decision").inner_text()
        rows = sp.locator(".bt-row[data-axis]")
        assert rows.count() == 3 and [r.locator("b").text_content() for r in rows.all()] == ["Value", "Experience", "Risk"]
        assert "Product's axis" in rows.first.inner_text() and rows.first.locator(".cards-ct").count() == 3     # the new card's token and the two old cards'
        assert "No total" in sp.inner_text()
        undo = sp.locator(".bt-undo").all_inner_texts()
        assert len(undo) == 2 and undo[0].startswith("to undo: ≈20% Claude · 2 modules, 6 tests change")
        assert sp.locator(".sp-cards [data-way]").all_inner_texts() == ["New wins\nthe old goal reopens as a change; the old decision is replaced by a new one, never edited", "Old wins\nthe new card is dropped, or changed to fit", "Merge\nthe leaders write one card of both", "Not a battle\nthe Orkmaster read it wrong"]
        b.close()


def test_a_way_sends_battle_settle_and_the_card_leaves_the_hand_and_esc_gives_the_focus_back(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator(CARD).click()
        pg.locator("[data-spread=battle]").wait_for()
        pg.keyboard.press("Escape")                                                           # Esc closes it, the focus is back on the card that opened it
        assert pg.locator(".sp-veil").count() == 0
        assert pg.evaluate("() => document.activeElement?.dataset?.kind") == "battle"
        pg.locator(CARD).click()
        pg.locator("[data-way=merge]").click()
        sent = [a for n, a in pg.evaluate(SENT) if n == "ideas.battle_settle"]
        assert len(sent) == 1 and sent[0]["way"] == "merge" and sent[0]["slug"].startswith("163-")
        assert pg.locator(".sp-veil").count() == 0
        pg.wait_for_function("(sel) => ![...document.querySelectorAll(sel)].some((e) => !e.classList.contains('is-gone'))", arg=CARD, timeout=5000)
        b.close()


def test_on_a_phone_width_the_battle_stacks_the_new_card_the_axes_the_old_cards_and_the_ways(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        pg.goto(page_url + "?mock=1")
        pg.locator(".mock-plate__b").wait_for(timeout=15000)
        pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => import('/static/js/link.js').then((l) => m.openSpread({ kind: 'battle', slug: l.proposed('turns').find((t) => t.kind === 'battle').goal })))")
        sp = pg.locator("[data-spread=battle]")
        sp.wait_for()
        box = lambda sel: sp.locator(sel).first.bounding_box()  # noqa: E731
        new, axes, old, way, field = box(".bt-new"), box(".bt-axes"), box(".bt-olds"), box(".sp-cards [data-way]"), box(".sp-field")
        assert new["y"] + new["height"] <= axes["y"] + 1 and axes["y"] + axes["height"] <= old["y"] + 1                  # one under the other
        assert way["y"] >= field["y"] + field["height"] - 1 and old["y"] > 0                                         # the ways under the field that holds the old cards
        assert pg.evaluate("() => document.documentElement.scrollWidth") <= 390 and sp.locator(".bt-row[data-axis]").count() == 3
        b.close()
