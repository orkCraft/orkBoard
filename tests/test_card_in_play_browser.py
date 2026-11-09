"""The card in play (docs/specs/168 D1, decisions §283.19, §286), in a real browser at 1366 x 768 against the hand's stub host: a question, a failure or a card of the Orkmaster's lifted rises at the table's foot at its left, 144 x 202, over
the hand; its goal is picked and its asker's tab opened (the Orkmaster's for what it plays); its ways are the hand's row from the same left edge, cut by the hand's rim and each rising whole when hovered; *Your own words…* lays a field
as large as the hand in the ways' place (Enter sends, Shift+Enter a new line, Esc closes it); a goal of several questions asks them one after another; and no element of the page is 404 x 566. Screenshots to $PLAY_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_answer_cards_browser import LINES, WaysHost, lift  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, need, node, open_hand, sig  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PLAY_SHOTS"]) if os.environ.get("PLAY_SHOTS") else None
VIEW = {"width": 1366, "height": 768}


def at_1366(gui, host=None, **more):
    pg, host, log = open_hand(gui, host=host or WaysHost(), **more)
    pg.set_viewport_size(VIEW)
    pg.wait_for_timeout(300)
    return pg, host, log


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def box(loc):
    b = loc.bounding_box()
    return {**b, "width": round(b["width"]), "height": round(b["height"])}                  # a card is 144 x 201.6 (5 : 7): the page's own size is the rounded one


def no_opened_card(pg):
    """No element is 404 x 566 (the opened card's size), whichever of its sides is wide."""
    got = pg.evaluate("() => [...document.querySelectorAll('body *')].filter((e) => { const r = e.getBoundingClientRect(); return Math.round(r.width) === 404 && Math.round(r.height) === 566; }).map((e) => e.className)")
    assert not got, got


def test_a_question_rises_at_the_tables_foot_at_its_left_and_its_goal_and_askers_tab_are_open(gui):
    pg, host, log = at_1366(gui)
    try:
        card = lift(pg, "asks", "phones")
        c, hand, pane = box(card), box(pg.locator(".hand")), box(pg.locator(".frame-table"))
        assert [c["width"], c["height"]] == [144, 202]
        assert c["y"] + c["height"] <= hand["y"] + 1 and hand["y"] - (c["y"] + c["height"]) <= 24, "standing on the hand: room left over its top"
        assert pane["x"] <= c["x"] <= pane["x"] + 60, "at the table's foot, at its left"
        first = box(pg.locator(".hand-ways-row .hand-ans").first)
        assert abs(first["x"] - c["x"]) <= 2, "the ways' row begins where the card stands"
        assert sig(pg, "frame/state.js", "tab") == "design", "the asking leader's tab is open"
        assert sig(pg, "frame/state.js", "picked") == "phones", "its goal is picked"
        no_opened_card(pg)
        shot(pg, "question")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_what_the_orkmaster_plays_opens_the_orkmasters_tab_and_a_failure_its_leaders(gui):
    pg, host, log = at_1366(gui, host=HandHost(extra=True))
    try:
        pg.evaluate("() => import('/static/js/frame/state.js').then((x) => x.openTab('tech'))")
        card = lift(pg, "route", "fresh")
        assert [box(card)["width"], box(card)["height"]] == [144, 202], "a card of any kind is the same card"
        assert sig(pg, "frame/state.js", "tab") == "orkmaster" and sig(pg, "frame/state.js", "picked") == "fresh"
        body, hand = box(pg.locator(".hand-body")), box(pg.locator(".hand"))
        assert abs(body["height"] - hand["height"]) <= 4 and body["y"] <= hand["y"] + 4, "its words and answers lie in the hand's place, as tall as the hand"
        no_opened_card(pg)
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        pg.evaluate("() => import('/static/js/frame/state.js').then((x) => x.openTab('design'))")
        lift(pg, "failed")
        assert sig(pg, "frame/state.js", "tab") == "tech", "a failure of Tech's opens Tech's tab"
        no_opened_card(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_ways_are_cut_by_the_rim_and_rise_whole_when_hovered(gui):
    pg, host, log = at_1366(gui)
    try:
        lift(pg, "asks", "phones")
        hand, ways = box(pg.locator(".hand")), pg.locator(".hand-ways-row .hand-ans")
        for i in range(3):
            w = box(ways.nth(i))
            assert [w["width"], w["height"]] == [144, 202]
            assert hand["y"] < w["y"] < hand["y"] + 30, "the top of a way shows under the hand's top edge"
            assert w["y"] + w["height"] > VIEW["height"] + 40, "the rest is under the rim"
        assert ways.nth(0).locator(".hand-ans__name").is_visible()
        ways.nth(1).hover()
        pg.wait_for_timeout(600)
        up = box(ways.nth(1))
        assert up["y"] + up["height"] <= VIEW["height"] + 2 and up["y"] < hand["y"], "hovered it rises whole over the hand"
        assert box(ways.nth(0))["y"] > hand["y"], "the others stay"
        pg.mouse.move(700, 300)
        pg.wait_for_timeout(600)
        assert box(ways.nth(1))["y"] + 202 > VIEW["height"] + 40, "it goes back"
        shot(pg, "question-hover")
        acts = pg.locator(".hand-ways-acts")
        assert box(acts)["y"] > hand["y"] and box(acts)["y"] + box(acts)["height"] <= VIEW["height"], "Open… and Put it back stay in the strip the rim leaves"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_way_carries_the_kind_the_leader_gave_it_for_the_pictures_to_come(gui):
    host = WaysHost()
    for n in host.nodes:
        if n["slug"] == "phones":
            n["asked"][0]["kinds"] = ["keep", "other"]
    for row in host.needs:
        if row.get("idea") == "phones":
            row["asked"] = next(n for n in host.nodes if n["slug"] == "phones")["asked"]
    pg, host, log = at_1366(gui, host=host)
    try:
        lift(pg, "asks", "phones")
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert ways.nth(0).get_attribute("data-way-kind") == "keep" and ways.nth(1).get_attribute("data-way-kind") == "other"
        assert ways.nth(2).get_attribute("data-way-kind") is None, "*<Leader> decides* is no way of the leader's"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_your_own_words_lays_a_field_as_large_as_the_hand_in_the_ways_place(gui):
    pg, host, log = at_1366(gui)
    try:
        card = lift(pg, "asks", "phones")
        pg.locator(".hand-ways-row .hand-ans--pen").click()
        field = pg.locator(".hand-pen")
        field.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        f, hand, c = box(field), box(pg.locator(".hand")), box(card)
        assert abs(f["y"] - hand["y"]) <= 4 and abs((f["y"] + f["height"]) - (hand["y"] + hand["height"])) <= 4, "as tall as the hand, in its place"
        assert abs(f["x"] - c["x"]) <= 2 and f["x"] + f["width"] < VIEW["width"] - 150, "from the card's left edge to the strip the sunk hand keeps"
        assert pg.locator(".hand-pen textarea").evaluate("e => e === document.activeElement"), "focused at once"
        assert pg.locator(".hand-ways-row .hand-ways-cards").evaluate("e => getComputedStyle(e).visibility") == "hidden", "the ways give way to it"
        shot(pg, "own-words")
        pg.keyboard.type("Phones count alone")
        pg.keyboard.press("Shift+Enter")
        pg.keyboard.type("and check back.")
        assert pg.locator(".hand-pen textarea").input_value() == "Phones count alone\nand check back."
        pg.keyboard.press("Enter")
        got = _calls(pg, host, "ideas.answer")
        assert got and got[0]["answers"] == ["Phones count alone\nand check back."] and got[0]["from"] == "hand", got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_of_several_questions_asks_them_one_after_another_each_its_own_card(gui):
    host = HandHost()
    more = [{"ask": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock: every phone agrees.", "by": None, "look": False},
            {"ask": "How big is the clock?", "choices": ["Large", "Small"], "pick": 1, "why": "", "by": None, "look": False}]
    for n in host.nodes:
        if n["slug"] == "phones":
            n["asked"] = more
    for row in host.needs:
        if row.get("idea") == "phones":
            row["asked"] = more
    pg, host, log = at_1366(gui, host=host)
    try:
        card = lift(pg, "asks", "phones")
        assert box(card)["width"] == 144 and card.get_attribute("data-step") == "0"
        assert "1/2" in card.locator(".hand-card__foot").inner_text() and "Where does the timer run?" in card.locator(".hand-card__foot").inner_text()
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert ways.nth(0).locator(".hand-ans__name").inner_text().strip() == "Server counts, phones show it"
        ways.nth(0).click()
        pg.wait_for_function("() => document.querySelector('.hand-lifted').dataset.step === '1'", timeout=WAIT_MS)
        assert not _calls(pg, host, "ideas.answer", at_least=0), "nothing is sent before the last"
        assert "2/2" in card.locator(".hand-card__foot").inner_text() and "How big is the clock?" in card.locator(".hand-card__foot").inner_text()
        assert pg.locator(".hand-ways-row .hand-ans").nth(0).locator(".hand-ans__name").inner_text().strip() == "Large"
        pg.locator(".hand-ways-row .hand-ans").nth(1).click()
        got = _calls(pg, host, "ideas.answer")
        assert got and got[0]["slug"] == "phones" and got[0]["answers"] == ["Server counts, phones show it", "Small"] and got[0]["from"] == "hand", got
        no_opened_card(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_conflict_lifted_is_two_small_cards_and_no_card_of_404_x_566(gui):
    """Spec 168 D1: the conflict's two cards are 144 x 202 each, side by side at the table's foot; the earlier one holds *Open in the past*."""
    from tests.test_conflict_browser import ConflictHost, lift as lift_conflict  # noqa: PLC0415
    pg, host, log = at_1366(gui, host=ConflictHost())
    try:
        card = lift_conflict(pg)
        earlier = pg.locator(".hand-earlier")
        earlier.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-earlier').classList.contains('is-out')", timeout=WAIT_MS)
        a, b = box(card), box(earlier)
        assert [a["width"], a["height"]] == [144, 202] and [b["width"], b["height"]] == [144, 202]
        assert b["x"] > a["x"] + a["width"] and abs(b["y"] - a["y"]) <= 3, "side by side"
        assert earlier.get_by_role("button", name="Open in the past").count() == 1
        no_opened_card(pg)
        shot(pg, "conflict")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_leaders_risk_lifted_is_the_card_in_play_its_ways_the_hand_and_its_tab_and_goal_are_open(gui):
    """Spec 168 D1, C4: a risk (or a conflict, a better, the fork) pressed on the leader's table rises at the table's foot as a 144 x 202 card, its ways the hand cut by the rim; *Leave it* sends C4's command."""
    from tests.test_leader_tables_browser import start  # noqa: PLC0415
    pg, host, errors = start(gui, "talk")
    try:
        pg.locator('.say-card[data-say="n2"]').click()
        card = pg.locator('.hand-lifted[data-kind="say"]')
        card.wait_for(timeout=WAIT_MS)
        pg.mouse.move(2, 2)
        pg.wait_for_timeout(500)
        c, hand, ways = box(card), box(pg.locator(".hand")), pg.locator(".hand-ways-row .hand-ans")
        assert [c["width"], c["height"]] == [144, 202] and c["y"] + c["height"] <= hand["y"] + 1
        assert ways.count() == 2 and box(ways.nth(0))["y"] > hand["y"] and box(ways.nth(0))["y"] + 202 > 768 + 40, "its ways are the hand, cut by the rim"
        assert abs(box(ways.nth(0))["x"] - c["x"]) <= 2
        assert sig(pg, "frame/state.js", "tab") == "tech" and sig(pg, "frame/state.js", "picked") == "seat"
        assert pg.locator(".q-choose").count() == 0 and pg.locator(".table-over").count() == 0, "nothing opens over the pane"
        no_opened_card(pg)
        shot(pg, "risk")
        pg.get_by_role("button", name="Leave it").click()
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        assert ("ideas.leave_say", {"idea": "seat", "id": "n2"}) in host.log
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)
