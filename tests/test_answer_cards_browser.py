"""A lifted card stays a hand card and its ways are the hand (docs/specs/158 part F, decisions §270), in a real browser at 1280 x 800 against the hand's stub host: a card with one open question, or a failure, is lifted
as the 144 x 202 hand card it was, in its signal's ring, its goal's card in the Orkmaster's column ringed the same; each way is a 144 x 202 card in the hand's row with its name and its whole line at rest, the leader's pick
marked by its head and by its words, a priced way's cost in its corner; *<Leader> decides*, *Open…* and *Put it back* at the row's end; the rest of the hand sinks, grey and inert; pressing a way answers at once, from the hand.
The narrow page keeps the inline card. Screenshots to $LIFT_SHOTS when it is set."""
from __future__ import annotations

import copy
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
        wr = pg.locator(".hand-ways-row").bounding_box()
        assert abs(top["x"] + top["width"] - (wr["x"] + wr["width"])) <= 2, "at the right end of the ways row, over its acts"
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
        assert abs(box["y"] + box["height"] - (q["y"] + q["height"])) <= 2 and box["x"] + box["width"] <= q["x"], (box, q)      # left of the question: the right of it is the table's empty foot and the discard
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


TALK = {"idea": "phones", "mode": "talk", "round": 1, "done": False, "heard": ["tech", "design"], "cause": None, "stances": [
    {"party": "tech", "leader": "Architect", "weigher": False, "verdict": "go", "stance": "The server owns the clock", "for": "One place to reset", "against": "Every round trip adds delay", "questions": []},
    {"party": "design", "leader": "Designer", "weigher": False, "verdict": "doubt", "stance": "Phones must agree on the second", "for": "Nobody argues about the time", "against": "A phone offline shows a stale time",
     "questions": [{"id": "q1", "q": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock: every phone agrees.", "project": False, "state": "waiting"}]}]}


class TalkHost(WaysHost):
    """The goal `phones` is still in Talk: its leaders' Talk as the host kept it, two stances and Design's open question."""

    def __init__(self):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "phones":
                n["state"] = "talk"

    def handle(self, name, a):
        if name == "ideas.talk_read":
            self.log.append((name, a))
            return copy.deepcopy(TALK)
        return super().handle(name, a)


def test_a_goal_in_talk_lifted_lays_its_leaders_talk_and_its_question_on_the_table(gui):
    """Spec 158 H, decisions §270.4: lifted at 1280 x 800, the table of a goal still in Talk shows in each leader's lane its verdict and its lines, and in the asking leader's lane the question with its ways."""
    pg, host, log = open_hand(gui, host=TalkHost())
    try:
        lift(pg, "asks", "phones")
        board = pg.locator(".table-board--plan")
        board.wait_for(timeout=WAIT_MS)
        pg.locator(".plan-talk").first.wait_for(timeout=WAIT_MS)
        tech, design = board.locator('.table-lane[data-party="tech"] .plan-talk'), board.locator('.table-lane[data-party="design"] .plan-talk')
        assert tech.count() == 1 and design.count() == 1
        assert tech.locator(".plan-talk__verdict").inner_text().strip().lower() == "go" and design.locator(".plan-talk__verdict").inner_text().strip().lower() == "doubt"
        text = tech.inner_text()
        assert "The server owns the clock" in text and "One place to reset" in text and "Every round trip adds delay" in text
        assert "Phones must agree on the second" in design.inner_text() and "A phone offline shows a stale time" in design.inner_text()
        assert tech.locator(".plan-talk__ask").count() == 0, "the question lies in its asker's lane only"
        ask = design.locator(".plan-talk__ask")
        assert ask.count() == 1 and ask.locator(".plan-talk__q").inner_text().strip() == "Where does the timer run?"
        assert ask.locator(".plan-talk__ways li").all_inner_texts() == ["\u25cf Server counts, phones show it", "Each phone counts down alone"]
        assert pg.locator(".plan-wait").count() == 0, "something was said: not the empty line"
        assert board.locator(".plan-talk button, .plan-talk input").count() == 0, "read-only: nothing to press"
        shot(pg, "talk-table")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_risen_question_covers_no_lanes_talk_and_the_sunk_hand_can_be_seen(gui):
    """Spec 158 H, Design's Done when 5: at 1280 x 800 the risen question stands right of the ways, over no lane's Talk or question; the sunk hand shows beside the ways row, grey and inert."""
    pg, host, log = open_hand(gui, host=TalkHost())
    try:
        card = lift(pg, "asks", "phones")
        pg.locator(".plan-talk").first.wait_for(timeout=WAIT_MS)
        q = card.bounding_box()
        for lane in pg.locator(".plan-talk").all():
            for part in lane.locator(":scope > *, .plan-talk__ask > *").all():
                b = part.bounding_box()
                if not b or not b["width"]:
                    continue
                apart = q["x"] >= b["x"] + b["width"] or q["x"] + q["width"] <= b["x"] or q["y"] >= b["y"] + b["height"] or q["y"] + q["height"] <= b["y"]
                assert apart, ("the question covers Talk", q, b)
        row, ways = pg.locator(".hand-row.is-sunk"), pg.locator(".hand-ways-row").bounding_box()
        assert row.evaluate("e => e.inert") and row.evaluate("e => getComputedStyle(e).filter") == "grayscale(1)"
        r = row.bounding_box()
        assert r["x"] >= ways["x"] + ways["width"] - 2 and r["width"] > 100, ("the sunk hand beside the ways, not under them", r, ways)
        assert row.locator(".hand-card, .hand-slot").count() > 0
        shot(pg, "product-talk")
    finally:
        pg.close()
    assert not log, "\n".join(log)


LONG = ["Counts on the server, so every phone draws the very same second as the host does", "Counts on each phone alone, so no server is needed and a second may drift apart."]


class LongHost(WaysHost):
    """The same host whose ways' lines are the 80 characters a leader may write."""

    def __init__(self):
        super().__init__()
        assert all(len(x) == 80 for x in LONG), [len(x) for x in LONG]
        for n in self.nodes:
            if n["slug"] == "phones":
                n["asked"][0]["lines"] = LONG
        for row in self.needs:
            if row.get("idea") == "phones":
                row["asked"] = next(n for n in self.nodes if n["slug"] == "phones")["asked"]


def test_a_way_of_eighty_characters_shows_it_whole_and_its_accessible_name_reads_name_pick_line_question(gui):
    """Spec 159 D: each way card shows its leader's line whole (80 characters, no cut, never "Answers with this."); its aria-label is the name, "its pick" on the pick, the line, then the question."""
    pg, host, log = open_hand(gui, host=LongHost())
    try:
        lift(pg, "asks", "phones")
        ways = pg.locator(".hand-ways-row .hand-ans")
        ask = "Round timer shows on every phone"
        for i, line in enumerate(LONG):
            w = ways.nth(i)
            el = w.locator(".hand-ans__line")
            assert el.inner_text().strip() == line and el.is_visible()
            assert el.evaluate("e => e.scrollHeight <= e.clientHeight + 1"), "cut nowhere"
            assert w.evaluate("e => e.scrollHeight <= e.clientHeight + 1")
            assert "Answers with this." not in w.inner_text()
            name = w.locator(".hand-ans__name").inner_text().strip()
            label = w.get_attribute("aria-label")
            want = f"{name}{', its pick' if i == 0 else ''}, {line}"
            assert label.startswith(want) and ask in label[len(want):], label
        shot(pg, "question-lines")
        ways.nth(1).click()
        got = _calls(pg, host, "ideas.answer")
        assert got and got[0]["slug"] == "phones" and got[0]["from"] == "hand", got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_question_without_lines_reads_as_before(gui):
    """Spec 159 D: no lines, the pick shows the question's why, the rest "Answers with this.", the accessible name without a line."""
    pg, host, log = open_hand(gui, host=WaysHost())
    try:
        lift(pg, "asks", "clock")
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert ways.nth(0).locator(".hand-ans__line").inner_text().strip() == "Answers with this."
        assert ways.nth(1).locator(".hand-ans__line").inner_text().strip() == "Amber reads on every screen."
        for i in range(2):
            label = ways.nth(i).get_attribute("aria-label")
            assert "Amber reads on every screen" not in label and "Answers with this" not in label, label
        assert ways.nth(1).get_attribute("aria-label").startswith("Amber, its pick: ")
    finally:
        pg.close()
    assert not log, "\n".join(log)
