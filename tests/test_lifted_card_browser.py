"""A lifted card is a card (docs/specs/104 §5, decisions §176.4), in a real browser against the hand's stub host at the two widths of `tests/narrow.py`: the hand card's frame and anatomy at twice its width (the screen's width
less a gutter a side at the narrow one), turned a degree or two, its foot on the hand's line, its body between the window and the foot holding the answers, the cost's words and *Put it back*, scrolling inside at the card's
most height and never growing wider; the focus on it, Esc lowering it. Screenshots to $LIFT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["LIFT_SHOTS"]) if os.environ.get("LIFT_SHOTS") else None
LONG = " ".join(["The timer does not reset after a reconnect, so every phone that joins late shows the old round and the host has to restart the room by hand."] * 6)

MEASURE = """e => { const body = e.querySelector('.hand-lifted__body'), hand = e.parentElement.getBoundingClientRect(), foot = e.querySelector('.hand-card__foot').getBoundingClientRect(),
  card = document.querySelector('.hand-card:not(.hand-lifted)');
  return { width: e.offsetWidth, height: e.offsetHeight, card: card.offsetWidth, scrolls: body.scrollHeight > body.clientHeight + 1, sideways: e.scrollWidth > e.clientWidth + 1, bodyTop: body.getBoundingClientRect().top,
    windowBottom: e.querySelector('.hand-card__window').getBoundingClientRect().bottom, footTop: foot.top, handTop: hand.top, footBottom: foot.bottom, rotate: getComputedStyle(e).rotate,
    focused: document.activeElement === e, maxHeight: parseFloat(getComputedStyle(e).maxHeight), vh: innerHeight, vw: innerWidth } }"""


class LongHost(HandHost):
    """The hand's host with a failed task whose error is far longer than a card."""

    def __init__(self):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "timer":
                n["tasks"][0]["error"] = LONG


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def lift(pg, kind):
    pg.locator(f'.hand-card[data-kind="{kind}"]').first.click(position={"x": 10, "y": 20})
    card = pg.locator(".hand-lifted")
    card.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(250)
    return card


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_lifted_card_is_a_card_of_the_hand_cards_anatomy_twice_as_wide_turned_a_little_with_its_foot_on_the_hands_line(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        card = lift(pg, "plan")
        classes = card.get_attribute("class").split()
        assert {"ork-card", "hand-card", "hand-card--stop", "hand-card--big", "hand-lifted"} <= set(classes)
        assert card.get_attribute("role") == "dialog" and card.get_attribute("data-kind") == "plan" and card.get_attribute("data-key") == "plan/export/"
        assert card.get_attribute("aria-label").startswith("Lifted: ")
        children = card.evaluate("e => [...e.children].map((c) => c.className.split(' ')[0])")
        assert children == ["hand-card__head", "hand-card__window", "hand-card__label", "hand-lifted__body", "hand-card__foot"], children
        assert card.locator(".hand-card__window .ork-sign").count() == 1 and card.locator(".hand-card__asker .ork-race__head").count() == 1
        assert card.locator(".hand-card__label .hand-card__party").text_content().strip() == "Tech" and card.locator(".hand-card__label .ork-gem").count() == 1
        assert card.locator(".hand-card__foot").inner_text().strip() == "Plan ready", "its foot says what the card is"
        assert card.locator(".hand-card__name").inner_text().strip() == "Export the round scores"
        body = card.locator(".hand-lifted__body")
        assert body.get_by_role("button", name="Start the work").count() == 1 and body.get_by_role("button", name="Put it back").count() == 1 and body.locator(".hand-spend").count() == 1
        m = card.evaluate(MEASURE)
        if width == "wide":
            assert m["width"] == 2 * m["card"], "twice a hand card's width"
            assert m["height"] >= m["width"] * 7 / 5 - 1, "its proportions at the least"
        else:
            assert abs(m["width"] - (m["vw"] - 16)) <= 1, "the screen's width less a gutter a side"
        assert 1 <= abs(float(m["rotate"].removesuffix("deg"))) <= 2, m["rotate"]
        assert abs(m["footBottom"] - m["handTop"]) <= 8, "its foot stands on the hand's line"
        assert m["bodyTop"] >= m["windowBottom"] and m["footTop"] >= m["bodyTop"], "the body lies between the window and the foot"
        assert m["focused"] and not m["sideways"]
        box = card.bounding_box()
        assert box["x"] >= -1 and box["x"] + box["width"] <= m["vw"] + 1 and box["y"] >= 0
        assert card.evaluate("e => getComputedStyle(e).zIndex") == "60"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-lifted-short")
        pg.keyboard.press("Escape")
        assert pg.locator(".hand-lifted").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_long_body_scrolls_inside_the_card_which_stops_at_its_most_height_and_never_grows_wider(gui, width):
    pg, host, log = open_hand(gui, host=LongHost(), width=width)
    try:
        card = lift(pg, "failed")
        m = card.evaluate(MEASURE)
        assert m["height"] <= m["maxHeight"] + 1 and m["maxHeight"] < m["vh"], "the card stops at its most height"
        if width == "wide":
            assert m["scrolls"] and m["width"] == 2 * m["card"], "the body scrolls inside, the width is twice the hand card's"
            card.locator(".hand-lifted__body").evaluate("e => { e.scrollTop = e.scrollHeight; }")
            assert card.get_by_role("button", name="Put it back").is_visible()
        assert not m["sideways"] and card.locator(".hand-card__foot").is_visible() and card.locator(".hand-card__head").is_visible()
        box = card.bounding_box()
        assert box["y"] >= 0 and box["x"] >= -1 and box["x"] + box["width"] <= m["vw"] + 1
        shot(pg, f"{width}-lifted-long")
        pg.locator(".hand-lifted").get_by_role("button", name="Put it back").click()
        assert pg.locator(".hand-lifted").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)
