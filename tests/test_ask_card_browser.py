"""Spec 168 D3 (decisions §283.20): the quick question as the ? card, in a real browser against a stubbed host. An answered question (`town.ask`, with `party` who answered, `tab` where it was asked and
`ways`) is a card in the hand, its leader's head as its asker, no goal and no place on the Board; lifted it lays the answer and its three ways, **Make it a goal** (`make_it_a_goal`, opens the new
goal's field with the line the answer suggests), **Ask more** (`ask_more`, puts the answer away and opens the bubble on the tab it was asked on) and **Got it** (`take`, `ideas.ask_clear {got_it}`).
A hop keeps the answer with the leader that answered; a question still being answered is no card. The bubble's answer says the same three ways."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import GOAL, record, start  # noqa: E402

pytestmark = pytest.mark.browser

CARD = '.hand-card[data-kind="ask"]'
WAYS = [("make_it_a_goal", "Make it a goal"), ("ask_more", "Ask more"), ("take", "Got it")]


@pytest.fixture
def card(gui):
    pg, host, errors = start(gui, "wide")
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def answered(host, party="tech", tab="tech", **more):
    host.put(record("answered", party, tab=tab, hop=party != tab, ways=[k for k, _n in WAYS], **more))


def lifted(pg):
    pg.locator(CARD).first.dispatch_event("click")                                  # the hand's cards overlap: pressed as a key would
    box = pg.locator(".hand-lifted")
    box.wait_for(timeout=WAIT_MS)
    return box






def test_got_it_puts_the_card_away_and_is_told_to_the_host(card):
    pg, host = card
    answered(host)
    lifted(pg).locator('button[data-way-kind="take"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"ask\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{"got_it": True}] and host.ask is None


def test_make_it_a_goal_opens_the_field_with_the_line_the_answer_suggests(card):
    pg, host = card
    answered(host)
    lifted(pg).locator('button[data-way-kind="make_it_a_goal"]').click()
    area = pg.locator(".hand-field textarea")
    area.wait_for(timeout=WAIT_MS)
    assert area.input_value() == GOAL and host.sent("ideas.ask_goal") == [{}]




