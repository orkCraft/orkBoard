"""A lifted card stays a hand card and its ways are the hand (docs/specs/158 part F, decisions §270), in a real browser at 1280 x 800 against the hand's stub host: a card with one open question, or a failure, is lifted
as the 144 x 202 hand card it was, in its signal's ring, its goal's card in the Orkmaster's column ringed the same; each way is a 144 x 202 card in the hand's row with its name and its whole line at rest, the leader's pick
marked by its head and by its words, a priced way's cost in its corner; *<Leader> decides*, *Open…* and *Put it back* at the row's end; the rest of the hand sinks, grey and inert; pressing a way answers at once, from the hand.
The narrow page keeps the inline card. Screenshots to $LIFT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["LIFT_SHOTS"]) if os.environ.get("LIFT_SHOTS") else None
LINES = ["One clock on the server; every phone draws the same second.", "No server time; phones may drift a second apart."]


class WaysHost(HandHost):
    """The hand's host whose open question has a line for each way (the leader writes them to fit) and a price on the second."""

    def __init__(self):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "phones":
                n["asked"][0].update(lines=LINES, costs=[None, {"usd_low": 0.5, "usd_high": 1.0}])
        for row in self.needs:
            if row.get("idea") == "phones":
                row["asked"] = next(n for n in self.nodes if n["slug"] == "phones")["asked"]
        asked = [{"ask": "Which colour is the clock?", "choices": ["Green", "Amber"], "pick": 1, "why": "Amber reads on every screen.", "by": None, "look": False}]
        clock = node("clock", "design", "The clock's face on the host's screen", "table", state="working", element="ice", asks_you=True, asked=asked)
        self.nodes.append(clock)                                                  # a goal at work in the column, asking: its card there is ringed
        self.needs.append(need("asks", "design", "clock", clock["title"], "Which colour is the clock?", at="2026-10-20T09:35:00", asked=asked))


def lift(pg, kind, goal=None):
    pick = f'.hand-card[data-kind="{kind}"]' + (f'[data-goal="{goal}"]' if goal else "")
    pg.locator(pick).first.click(position={"x": 10, "y": 20})
    card = pg.locator(".hand-lifted")
    card.wait_for(timeout=WAIT_MS)
    pg.mouse.move(2, 2)
    pg.wait_for_timeout(500)
    return card


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def size(loc):
    return loc.evaluate("e => [e.offsetWidth, e.offsetHeight]")


def test_a_lifted_question_stays_a_hand_card_in_its_ring_and_its_ways_are_cards_with_their_whole_line(gui):
    """Spec 158 F, decisions §270.1–§270.3: the question is 144 x 202 in its signal's ring, its goal's card in the column ringed, each way a 144 x 202 card with its line whole at rest, its pick marked in words."""
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        card = lift(pg, "asks", "phones")
        assert card.get_attribute("data-kind") == "asks" and "asks" in card.get_attribute("class").split(), "in its signal's ring"
        assert card.get_attribute("aria-label").startswith("Lifted: ")
        assert size(card) == [144, 202], size(card)
        assert not pg.locator(".hand-lifted--card").count(), "no opened card"
        assert card.locator(".hand-card__name").inner_text().strip() == "Round timer shows on every phone"
        assert card.evaluate("e => getComputedStyle(e).boxShadow") not in ("", "none"), "ringed"
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert ways.count() == 4, "two ways, the leader's and the Pen"
        for i in range(3):
            assert size(ways.nth(i)) == [144, 202]
        first, second, decide = ways.nth(0), ways.nth(1), ways.nth(2)
        assert first.locator(".hand-ans__name").inner_text().strip() == "Server counts, phones show it"
        for w, line in ((first, LINES[0]), (second, LINES[1])):
            el = w.locator(".hand-ans__line")
            assert el.inner_text().strip() == line and el.is_visible(), "its line at rest, no hover"
            assert el.evaluate("e => e.scrollHeight <= e.clientHeight + 1"), "the whole line, cut nowhere"
            assert w.evaluate("e => e.scrollHeight <= e.clientHeight + 1")
        pick = first.locator(".corner--foot")
        assert first.get_attribute("data-pick") == "1" and pick.inner_text().strip().lower() == "its pick" and pick.locator(".ork-race__head").count() == 1, "the leader's pick by its head and in words"
        assert second.get_attribute("data-pick") is None and "its pick" not in second.inner_text()
        assert second.locator(".corner__much .ork-gem").count() == 1, "a priced way's cost in its corner"
        assert decide.locator(".hand-ans__name").inner_text().strip().endswith("decides") and decide.locator(".corner--top .ork-race__head").count() == 1
        acts = pg.locator(".hand-ways-acts")
        assert acts.get_by_role("button", name="Open…").is_visible() and acts.get_by_role("button", name="Put it back").is_visible()
        row = pg.locator(".hand-row")
        assert row.evaluate("e => e.inert") and "is-sunk" in row.get_attribute("class").split(), "the rest of the hand sinks and is inert"
        assert row.evaluate("e => getComputedStyle(e).filter") == "grayscale(1)", "grey"
        top, hand = card.bounding_box(), pg.locator(".hand").bounding_box()
        assert top["y"] + top["height"] < pg.locator(".hand-ways-row").bounding_box()["y"] + 1, "the question stands on the table's foot over its ways"
        assert top["y"] >= 0 and hand["y"] > 0
        narrow.no_sideways(pg)
        shot(pg, "question")
        pg.get_by_role("button", name="Put it back").click()
        assert pg.locator(".hand-lifted, .hand-ways-row").count() == 0 and not pg.locator(".hand-row").evaluate("e => e.inert")
        assert pg.locator('.col-card[data-ringed]').count() == 0, "the ring goes with the card"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_goals_card_in_the_column_is_ringed_in_the_questions_signal(gui):
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        lift(pg, "asks", "clock")
        ring = pg.locator('.frame-column .col-card[data-goal="clock"]')
        assert ring.count() == 1 and ring.first.get_attribute("data-ringed") == "asks"
        assert ring.first.evaluate("e => getComputedStyle(e).outlineStyle") == "solid" and ring.first.evaluate("e => getComputedStyle(e).outlineWidth") == "2px"
        assert pg.locator('.frame-column .col-card[data-ringed]').count() == 1, "only its goal's card"
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        assert pg.locator('.col-card[data-ringed]').count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pressing_a_way_answers_at_once_from_the_hand_and_the_leader_decides_the_same_way(gui):
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        lift(pg, "asks", "phones")
        pg.locator(".hand-ways-row .hand-ans").nth(1).click()
        got = _calls(pg, host, "ideas.answer")
        assert got and got[0]["slug"] == "phones" and got[0]["answers"] == ["Each phone counts down alone"] and got[0]["from"] == "hand", got
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        lift(pg, "asks", "words")
        pg.locator(".hand-ways-row .hand-ans:not(.hand-ans--pen)").last.click()
        got = _calls(pg, host, "ideas.answer", at_least=2)
        assert got[-1]["slug"] == "words" and got[-1]["decide"] is True and got[-1]["from"] == "hand", got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_open_opens_todays_form_and_keeps_the_picks(gui):
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        lift(pg, "asks", "phones")
        pg.get_by_role("button", name="Open…").click()
        pg.wait_for_selector(".hand-stopface", timeout=WAIT_MS)
        assert pg.locator(".hand-stopface").get_by_text("Where does the timer run?").count() >= 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_failure_stays_a_hand_card_in_its_ring_and_start_again_is_a_priced_way(gui):
    pg, host, log = open_hand(gui)
    try:
        card = lift(pg, "failed")
        assert "fails" in card.get_attribute("class").split() and size(card) == [144, 202]
        ring = pg.locator('.frame-column .col-card[data-goal="timer"]')
        assert ring.count() == 1 and ring.first.get_attribute("data-ringed") == "fails" and ring.first.evaluate("e => getComputedStyle(e).outlineColor") != "rgba(0, 0, 0, 0)", "its goal's card in the column is ringed the same"
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert ways.count() == 1 and size(ways.first) == [144, 202]
        assert ways.first.locator(".hand-ans__name").inner_text().strip() == "Start again" and ways.first.locator(".hand-ans__line").inner_text().strip()
        assert ways.first.locator(".corner__much .ork-gem").count() == 1, "its cost in its corner"
        assert pg.locator(".hand-row").evaluate("e => e.inert")
        shot(pg, "failure")
        ways.first.click()
        got = _calls(pg, host, "ideas.start")
        assert got and got[0]["slug"] == "timer" and got[0]["via"] == "hand", got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_page_keeps_the_inline_card(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        card = lift(pg, "asks", "phones")
        assert card.evaluate("e => e.classList.contains('hand-lifted--card')") and pg.locator(".hand-ways-row").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_reduced_motion_rises_at_once(gui):
    server, browser = gui
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        pg.emulate_media(reduced_motion="reduce")
        lift(pg, "asks", "phones")
        assert pg.locator(".hand-lifted--asked").evaluate("e => getComputedStyle(e).animationName") == "none"
        assert pg.locator(".hand-ways-row").evaluate("e => getComputedStyle(e).animationName") == "none"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def focused(pg):
    return pg.evaluate("() => { const e = document.activeElement; return e ? [e.getAttribute('data-way') || e.getAttribute('data-act') || e.getAttribute('data-kind') || e.tagName, getComputedStyle(e).boxShadow] : null }")


def test_tab_runs_the_ways_then_the_leader_the_pen_open_and_put_it_back_each_in_a_ring(gui):
    """Spec 158 G: Tab keeps to the card; the sunk hand is not reached; Escape and *Put it back* give the focus back to the hand card."""
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        lift(pg, "asks", "phones")
        assert pg.evaluate("() => document.activeElement.classList.contains('hand-lifted')")
        seen = []
        for _ in range(6):
            pg.keyboard.press("Tab")
            who, ring = focused(pg)
            seen.append(who)
            assert "2px" in ring and ring != "none", (who, ring)
        assert seen == ["way-0", "way-1", "decide", "own", "open", "put"], seen
        pg.get_by_role("button", name="Put it back").focus()
        pg.keyboard.press("Enter")
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        pg.wait_for_timeout(100)
        assert pg.evaluate("() => document.activeElement.classList.contains('hand-card') && document.activeElement.dataset.goal") == "phones"
        lift(pg, "asks", "phones")
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        pg.wait_for_timeout(100)
        assert pg.evaluate("() => document.activeElement.classList.contains('hand-card') && document.activeElement.dataset.goal") == "phones"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_your_own_words_opens_a_focused_field_beside_the_question_and_sends_the_words_from_the_hand(gui):
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        card = lift(pg, "asks", "phones")
        own = pg.locator(".hand-ways-row .hand-ans--pen")
        assert own.locator(".hand-ans__name").inner_text().strip() == "Your own words…"
        assert own.evaluate("e => getComputedStyle(e).borderStyle") == "dashed", "dashed until pressed"
        assert pg.locator(".hand-pen").count() == 0
        own.click()
        field = pg.locator(".hand-pen textarea")
        field.wait_for(timeout=WAIT_MS)
        assert field.evaluate("e => e === document.activeElement"), "focused"
        assert own.evaluate("e => getComputedStyle(e).borderStyle") == "solid"
        box, q = pg.locator(".hand-pen").bounding_box(), card.bounding_box()
        assert abs(box["y"] + box["height"] - (q["y"] + q["height"])) <= 2 and box["x"] >= q["x"] + q["width"], (box, q)
        send = pg.get_by_role("button", name="Send to ")
        assert send.inner_text().strip().startswith("Send to ")
        shot(pg, "pen")
        send.click()
        pg.wait_for_timeout(200)
        assert not _calls(pg, host, "ideas.answer", at_least=0), "an empty field sends nothing"
        field.fill("  Phones count alone and check back.  ")
        pg.keyboard.press("Escape")
        assert pg.locator(".hand-pen").count() == 0 and pg.locator(".hand-lifted").count() == 1, "Escape closes the field first"
        assert pg.evaluate("() => document.activeElement.dataset.way") == "own"
        own.click()
        pg.locator(".hand-pen textarea").fill("  Phones count alone and check back.  ")
        pg.get_by_role("button", name="Send to ").click()
        got = _calls(pg, host, "ideas.answer")
        assert got and got[0]["slug"] == "phones" and got[0]["answers"] == ["Phones count alone and check back."] and got[0]["from"] == "hand", got
    finally:
        pg.close()
    assert not log, "\n".join(log)
