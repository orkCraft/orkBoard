"""Spec 168 D3 (decisions §283.20): the quick question as the ? card, in a real browser against a stubbed host. An answered question (`town.ask`, with `party` who answered, `tab` where it was asked and
`ways`) is a card in the hand, its leader's head as its asker, no goal and no place on the Board; lifted it lays the answer and its three ways, **Make it a goal** (`make_it_a_goal`, opens the new
goal's field with the line the answer suggests), **Ask more** (`ask_more`, puts the answer away and opens the bubble on the tab it was asked on) and **Got it** (`take`, `ideas.ask_clear {got_it}`).
A hop keeps the answer with the leader that answered; a question still being answered is no card. The bubble's answer says the same three ways."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import ANSWER, AskHost, GOAL, bubble, head, opened, record, start  # noqa: E402

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


def test_an_answered_question_is_a_card_in_the_hand_and_a_question_being_answered_is_none(card):
    pg, host = card
    assert pg.locator(CARD).count() == 0
    host.put(record("asking", "tech", tab="tech"))
    pg.wait_for_timeout(300)
    assert pg.locator(CARD).count() == 0, "being answered: no card yet"
    answered(host)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    assert pg.locator(CARD).count() == 1
    host.put(None)
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"ask\"]')", timeout=WAIT_MS)


def test_lifted_it_has_the_answer_and_three_ways_by_their_kinds(card):
    pg, host = card
    answered(host)
    box = lifted(pg)
    assert box.locator('[data-part="question"]').inner_text() == "Why does the timer run on the server?"
    assert "Tech decided the timer runs on the server" in box.locator('[data-part="answer"]').inner_text() and ANSWER.split("\n")[1] in box.locator('[data-part="answer"]').inner_text()
    ways = box.locator("button[data-way-kind]")
    assert [(ways.nth(i).get_attribute("data-way-kind"), ways.nth(i).inner_text()) for i in range(ways.count())] == WAYS


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


def test_ask_more_puts_the_answer_away_and_opens_the_bubble_on_the_tab_it_was_asked_on(card):
    pg, host = card
    answered(host, party="tech", tab="")                                         # asked on the Orkmaster's tab, passed on to Tech's leader
    lifted(pg).locator('button[data-way-kind="ask_more"]').click()
    bubble(pg).wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{}] and bubble(pg).get_attribute("data-ask") == "orkmaster" and bubble(pg).get_attribute("data-state") == "asking"


def test_the_bubble_says_the_answer_on_the_tab_it_was_asked_on_with_got_it_too(card):
    pg, host = card
    answered(host, party="tech", tab="")                                         # a hop: Tech answered a question asked on the Orkmaster's tab
    opened(pg)
    assert bubble(pg).get_attribute("data-state") == "answered"
    ways = bubble(pg).locator("button[data-way-kind]")
    assert [ways.nth(i).get_attribute("data-way-kind") for i in range(ways.count())] == ["make_it_a_goal", "ask_more", "take"]
    bubble(pg).locator('button[data-way-kind="take"]').click()
    pg.wait_for_function("() => !document.querySelector('.table-ask__bubble')", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{"got_it": True}]
