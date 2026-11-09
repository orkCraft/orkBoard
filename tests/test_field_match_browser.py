"""Spec 135 A.5 (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §A.5; decisions §242.1–§242.2) in a real browser against the hand's stub host: the new-goal field sends `ideas.add` with `match: true`; when the
host answers `{slug: "", match: {...}}` nothing was added, the field stays open with its words, its rune and its files kept, and says under the text *Looks like part of: <title>* with **Add to it** (its cost under it when the goal's
decision is worded again: *about <n>% of …*) and **Keep apart**. *Keep apart* sends the goal again with `apart` and the goal it was offered (`with`); *Add to it* sends `ideas.add_to_goal {idea, text, element, via: "match"}` and closes the
field; changing the words puts the line away and sending again looks again. No toast, no count, no card. The phone's field (updeck.js) is the same one. Screenshots to $MATCH_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_context_narrow_browser import UprightHost, open_up, plus  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, _calls, _field, _plus, open_hand  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["MATCH_SHOTS"]) if os.environ.get("MATCH_SHOTS") else None
WORDS = "Show the round timer bigger"
TITLE = "Show the round timer on the host's screen"
LINE = "Looks like part of: " + TITLE


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


def match(reworded=False):
    return {"idea": "timer", "title": TITLE, "party": "tech", "state": "decided" if reworded else "talk", "score": 0.42, "why": ["words", "route"], "shared": ["round", "timer"], "adds": [],
            "reworded": reworded, "cost": {"calls": 1, "usd_high": 0.08} if reworded else None}


class MatchMixin:
    """`ideas.add` answers a match for words that say *timer* until `apart` is sent; `ideas.add_to_goal` keeps what it got."""
    reworded = False

    def handle(self, name, a):
        if name == "ideas.add" and a.get("match") is True and a.get("apart") is not True and "timer" in a.get("text", "").lower():
            self.log.append((name, a))
            return {"slug": "", "match": match(self.reworded)}
        if name == "ideas.add_to_goal":
            self.log.append((name, a))
            return {"ok": True, "idea": a["idea"], "reworded": self.reworded}
        return super().handle(name, a)


class Desk(MatchMixin, HandHost):
    pass


class Phone(MatchMixin, UprightHost):
    pass


def written(pg, text=WORDS):
    field, area = _field(pg)
    area.fill(text)
    return field, area


def line(pg):
    return pg.locator(".hand-field__match")


def test_a_match_keeps_the_field_open_with_its_words_and_says_one_line_with_two_buttons(gui):
    pg, host, log = open_hand(gui, host=Desk())
    try:
        _plus(pg).click()
        field, area = written(pg)
        area.press("Enter")
        line(pg).wait_for(timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.add")[-1] == {"text": WORDS, "match": True, "now": True}
        assert " ".join(line(pg).locator("[data-part=looks]").inner_text().split()) == LINE
        assert [b.inner_text() for b in line(pg).get_by_role("button").all()] == ["Add to it", "Keep apart"]
        assert field.is_visible() and area.input_value() == WORDS, "it closes nothing: the words stay"
        assert line(pg).locator("[data-part=cost]").count() == 0, "its goal has no decision worded: no cost"
        assert pg.locator(".ork-toast, .shell-toasts .ork-toast").count() == 0, "no toast"
        shot(pg, "field-match.png")
        send = field.locator("[data-corner=go]").bounding_box()
        assert send["y"] + send["height"] <= pg.viewport_size["height"], "Now (the card's last corner) stays above the window's edge"
        area.fill(WORDS + " and the round number")
        assert line(pg).count() == 0, "changed words: the line was of the old ones"
        area.press("Enter")
        line(pg).wait_for(timeout=WAIT_MS)
        assert len(_calls(pg, host, "ideas.add", 2)) == 2, "sending again looks again"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_keep_apart_sends_it_again_with_apart_and_the_goal_it_was_offered_and_closes_the_field(gui):
    pg, host, log = open_hand(gui, host=Desk())
    try:
        _plus(pg).click()
        written(pg)[1].press("Enter")
        line(pg).wait_for(timeout=WAIT_MS)
        line(pg).get_by_role("button", name="Keep apart").click()
        pg.locator(".hand-field").wait_for(state="detached", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.add", 2)[-1] == {"text": WORDS, "match": True, "apart": True, "with": "timer"}
        assert not [1 for n, _a in host.log if n == "ideas.add_to_goal"], "kept apart: nothing joined"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_add_to_it_sends_the_words_with_the_rune_and_via_match_closes_the_field_and_adds_no_goal(gui):
    host = Desk()
    host.reworded = True
    pg, host, log = open_hand(gui, host=host)
    try:
        _plus(pg).click()
        field, area = written(pg)
        area.press("Enter")
        line(pg).wait_for(timeout=WAIT_MS)
        cost = line(pg).locator("[data-part=cost]")
        assert cost.count() == 1 and cost.inner_text().startswith("about "), "the cost of wording its decision again"
        shot(pg, "field-match-cost.png")
        line(pg).get_by_role("button", name="Add to it").click()
        pg.locator(".hand-field").wait_for(state="detached", timeout=WAIT_MS)
        got = _calls(pg, host, "ideas.add_to_goal")[-1]
        assert got["idea"] == "timer" and got["text"] == WORDS and got["via"] == "match" and got.get("element", "") in ("", "meadow", "ice", "dust", "void", "lava")
        assert len(_calls(pg, host, "ideas.add")) == 1, "the goal was never added"
        _plus(pg).click()
        assert _field(pg)[1].input_value() == "", "the words went with it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_match_adds_as_it_did_and_the_phones_field_says_the_same_line(gui):
    pg, host, log = open_hand(gui, host=Desk())
    try:
        _plus(pg).click()
        written(pg, "Reset the clock after a reconnect")[1].press("Enter")
        pg.locator(".hand-field").wait_for(state="detached", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.add")[-1]["text"] == "Reset the clock after a reconnect" and line(pg).count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = open_up(gui, host=Phone("question"))
    try:
        plus(pg).click()
        area = pg.locator(".up-field textarea")
        area.wait_for(timeout=WAIT_MS)
        area.fill(WORDS)
        area.press("Enter")
        line(pg).wait_for(timeout=WAIT_MS)
        assert " ".join(line(pg).locator("[data-part=looks]").inner_text().split()) == LINE and pg.locator(".up-field").is_visible()
        buttons = line(pg).get_by_role("button")
        assert [b.inner_text() for b in buttons.all()] == ["Add to it", "Keep apart"]
        assert all(b.bounding_box()["height"] >= 40 for b in buttons.all()), "a thumb's size"
        shot(pg, "field-match-phone.png")
        narrow.no_sideways(pg)
        line(pg).get_by_role("button", name="Add to it").click()
        pg.locator(".up-field").wait_for(state="detached", timeout=WAIT_MS)
        assert [a for n, a in host.log if n == "ideas.add_to_goal"][-1]["via"] == "match"
    finally:
        pg.close()
    assert not log, "\n".join(log)
