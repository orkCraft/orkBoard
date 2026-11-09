"""Spec 150 E2.1, the conflict's card (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.1, decisions §254.6; mockup docs/mockups/table-edge/ section 4), in a real browser at the wide width against a stub host whose
`ideas.board` holds a goal's decision with an open conflict (`conflicted`) and the conflict's row before it, and whose `ideas.conflict` answers as gui/ideas_conflict.py does: the card lies under the first lane with the conflict sign, the Orkmaster's
head and *Goes against §212* at its foot, before the decision in the goal's stack; the decision lifted shows no *Confirm and start* while the conflict is open; the conflict lifted is two L cards side by side over the pane, the new goal's side (its title,
its why, *Goes against §212: <point>*, the three choices) and the earlier decision come out of the portal (its title and its why, *Open in the past*); each choice sends `ideas.conflict` (*Other…* with the person's words); answered, the card leaves the hand
and *Confirm and start* shows. Under reduced motion the earlier card does not fly. Screenshots to $CONFLICT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, node, need, open_hand, sig  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["CONFLICT_SHOTS"]) if os.environ.get("CONFLICT_SHOTS") else None
WHY = "Why: Players on a slow line see the timer jump; a timer on the client ticks smoothly and the server checks the end.\n\n1. The client counts the round down.\n2. The server checks the end."
POINT = "the server owns every clock of a round"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class ConflictHost(HandHost):
    """A project of four parties, a goal `timer` of Design's whose decision §240 goes against §212 (one conflict open); `ideas.conflict` answers it and the decision's row loses `conflicted`."""

    def __init__(self):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"] + [node("timer", "design", "Round timer on the client", "hand", state="decided", element="meadow")]
        self.decision = need("decision", "design", "timer", "Round timer on the client", WHY, number=240, confirmed=False, error="", conflicted=True, at="2026-10-20T09:01:00")
        self.conflict = need("conflict", "design", "timer", "Round timer on the client", POINT, number=212, point=POINT, title_then="The server owns every clock",
                             why_then="A clock on the client was cheated in the first playtest.", at="2026-10-20T09:00:00")
        self.needs = [self.conflict, self.decision]

    def handle(self, name, a):
        if name == "ideas.conflict":
            self.log.append((name, a))
            self.needs = [{**self.decision, "conflicted": False}]
            return self.bump({"ok": True, "idea": a["idea"], "number": a["number"], "choice": a["choice"], "reworded": a["choice"] != "replace", "left": 0,
                              **({"cost": {"calls": 1, "usd_high": 0.4}} if a["choice"] != "replace" else {})})
        return super().handle(name, a)


def open_conflict(gui, reduced=False):
    pg, host, log = open_hand(gui, host=ConflictHost())
    if reduced:
        pg.emulate_media(reduced_motion="reduce")
    pg.locator('.hand-card[data-kind="conflict"]').wait_for(timeout=WAIT_MS)
    return pg, host, log


def face(pg):
    return pg.locator('.hand-card--face[data-kind="conflict"]')


def lift(pg):
    face(pg).click(position={"x": 10, "y": 24})
    pg.locator('.hand-lifted[data-kind="conflict"]').wait_for(timeout=WAIT_MS)
    return pg.locator('.hand-lifted[data-kind="conflict"]')


def test_the_conflict_is_a_card_under_the_first_lane_before_the_decision_and_the_decision_cannot_be_confirmed(gui):
    pg, host, log = open_conflict(gui)
    try:
        c = face(pg)
        assert c.get_attribute("data-top") == "1", "the conflict is the goal's top card, before its decision"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="timer"]').count() == 1, "the whole goal's: under the first lane"
        assert c.locator(".hand-card__foot").text_content().strip() == "Goes against §212"
        assert c.locator(".corner--top .ork-sign.conflict").count() == 1 and c.locator(".corner--foot .ork-race__head").count() == 1, "the conflict sign, the Orkmaster's head"
        assert "asks" in c.get_attribute("class"), "the alert's edge: it asks you"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_lifted_it_is_two_cards_side_by_side_its_ways_the_hand_and_the_earlier_out_of_the_portal(gui):
    """Spec 168 D1 (before: spec 150 E2.1, two cards of 288 wide): the new goal's side is the 144 x 202 card in play at the table's foot, its three choices the hand's ways (*Other…* the Pen), the earlier decision a second 144 x 202 card beside it."""
    pg, host, log = open_conflict(gui)
    try:
        card = lift(pg)
        assert card.locator(".hand-card__name").inner_text().strip() == "Round timer on the client"
        assert card.locator(".hand-card__foot").inner_text().strip() == "Goes against §212"
        ways = pg.locator(".hand-ways-row .hand-ans")
        assert [w.locator(".hand-ans__name").inner_text().strip() for w in ways.all()] == ["The new one replaces §212", "Keep §212", "Other…"]
        earlier = pg.locator('.hand-earlier[data-earlier="212"]')
        earlier.wait_for(timeout=WAIT_MS)
        assert "is-out" in earlier.get_attribute("class"), "it comes out of the portal, once"
        pg.wait_for_function("() => !document.querySelector('.hand-earlier').classList.contains('is-out')", timeout=WAIT_MS)
        assert earlier.locator(".hand-card__name").inner_text().strip() == "The server owns every clock"
        assert "cheated in the first playtest" in earlier.locator(".hand-card__foot").inner_text()
        assert earlier.get_by_role("button", name="Open in the past").count() == 1
        a, b = card.bounding_box(), earlier.bounding_box()
        assert [round(a["width"]), round(a["height"]), round(b["width"]), round(b["height"])] == [144, 202, 144, 202], "two cards of the one size"
        assert b["x"] >= a["x"] + a["width"] - 4 and abs((b["y"] + b["height"]) - (a["y"] + a["height"])) < 24, "side by side, their feet on one line"
        shot(pg, "conflict-lifted")
        ways.first.click(position={"x": 20, "y": 30})
        got = _calls(pg, host, "ideas.conflict")
        assert got == [{"idea": "timer", "number": 212, "choice": "replace"}], got
        pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"conflict\"]') && !document.querySelector('.hand-earlier')", timeout=WAIT_MS)
        pg.locator('.hand-card--face[data-kind="decision"]').click(position={"x": 10, "y": 24})
        pg.locator('.hand-lifted[data-kind="decision"]').get_by_role("button", name="Confirm and start").wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_while_the_conflict_is_open_the_decision_says_so_and_has_no_confirm(gui):
    pg, host, log = open_conflict(gui)
    try:
        host.needs = [host.decision]                                                     # the decision alone in the hand, still conflicted (as a stale read would have it)
        host.bump({})
        pg.locator('.hand-card--face[data-kind="decision"]').wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card--face[data-kind="decision"]').click(position={"x": 10, "y": 24})
        card = pg.locator('.hand-lifted[data-kind="decision"]')
        card.wait_for(timeout=WAIT_MS)
        assert card.get_by_role("button", name="Confirm and start").count() == 0 and card.locator('[data-note="conflicted"]').count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("choice", ["keep", "other"])
def test_keep_and_other_send_their_choice_other_with_the_persons_words_and_under_reduced_motion_nothing_flies(gui, choice):
    pg, host, log = open_conflict(gui, reduced=True)
    try:
        card = lift(pg)
        earlier = pg.locator(".hand-earlier")
        earlier.wait_for(timeout=WAIT_MS)
        assert "is-out" not in earlier.get_attribute("class"), "reduced motion: it lies in its place"
        if choice == "keep":
            pg.locator(".hand-ways-row [data-way=keep]").click(position={"x": 20, "y": 30})
            want = {"idea": "timer", "number": 212, "choice": "keep"}
        else:
            pg.locator(".hand-ways-row .hand-ans--pen").click(position={"x": 20, "y": 30})
            pg.get_by_role("textbox", name="Your words to the Orkmaster").fill("The client counts, the server owns the end only")
            pg.keyboard.press("Enter")
            want = {"idea": "timer", "number": 212, "choice": "other", "text": "The client counts, the server owns the end only"}
        got = _calls(pg, host, "ideas.conflict")
        assert got == [want], got
        pg.locator(".ork-toast, [role=status]").filter(has_text="The Orkmaster words the decision again").first.wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_open_in_the_past_opens_the_earlier_decisions_entry_over_the_pane(gui):
    pg, host, log = open_conflict(gui)
    try:
        lift(pg)
        pg.locator(".hand-earlier").get_by_role("button", name="Open in the past").click()
        pg.locator('.table-over[data-kind="chronicle"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-earlier").count() == 0, "the lifted card is put down, the earlier one with it"
        assert pg.locator(".table-over__chronicle").get_attribute("data-view") == "decision" and sig(pg, "frame/state.js", "over")["props"] == {"decision": 212}, "the decision's entry (spec 156 D.5: the past itself lies in Release's lane)"
    finally:
        pg.close()
    assert not log, "\n".join(log)
