"""A lifted card is a card (docs/specs/104 §5, decisions §176.4), in a real browser against the hand's stub host at the two widths of `tests/narrow.py`: the hand card's frame and anatomy at twice its width (the screen's width
less a gutter a side at the narrow one), turned a degree or two, its foot on the hand's line, its body between the window and the foot holding the answers, the cost's words and *Put it back*, scrolling inside at the card's
most height and never growing wider; the focus on it, Esc lowering it. Screenshots to $LIFT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["LIFT_SHOTS"]) if os.environ.get("LIFT_SHOTS") else None
LONG = " ".join(["The timer does not reset after a reconnect, so every phone that joins late shows the old round and the host has to restart the room by hand."] * 14)

MEASURE = """e => { const body = e.querySelector('.hand-lifted__body'), hand = e.parentElement.getBoundingClientRect(), foot = e.querySelector('.corner--foot').getBoundingClientRect(), top = e.querySelector('.corner--top').getBoundingClientRect(),
  acts = e.querySelector('.hand-lifted__acts'), card = document.querySelector('.hand-card:not(.hand-lifted)'), cs = getComputedStyle(body);
  return { width: e.offsetWidth, height: e.offsetHeight, card: card.offsetWidth, scrolls: body.scrollHeight > body.clientHeight + 1, sideways: e.scrollWidth > e.clientWidth + 1, bodyTop: body.getBoundingClientRect().top,
    bodyBottom: body.getBoundingClientRect().bottom, actsTop: acts ? acts.getBoundingClientRect().top : null, actsBottom: acts ? acts.getBoundingClientRect().bottom : null, topBottom: top.bottom, footTop: foot.top, handTop: hand.top, footBottom: foot.bottom,
    rotate: getComputedStyle(e).rotate, focused: document.activeElement === e, maxHeight: parseFloat(getComputedStyle(e).maxHeight), vh: innerHeight, vw: innerWidth, overflowY: cs.overflowY, mask: cs.maskImage || cs.webkitMaskImage } }"""


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
def test_the_opened_card_is_404_by_566_with_its_corners_large_its_body_between_them_and_its_answers_above_the_foot(gui, width):
    """Spec 147 D.1, decisions §251.6: the hand card opened is 5 : 7 (404 x 566 at the wide width, the screen's width less a gutter a side at the narrow one), turned a degree or two, its foot on the hand's line."""
    pg, host, log = open_hand(gui, width=width)
    try:
        card = lift(pg, "plan")
        classes = card.get_attribute("class").split()
        assert {"ork-card", "hand-card", "hand-card--stop", "hand-card--big", "hand-lifted", "hand-lifted--card"} <= set(classes)
        assert card.get_attribute("role") == "dialog" and card.get_attribute("data-kind") == "plan" and card.get_attribute("data-key") == "plan/export/"
        assert card.get_attribute("aria-label").startswith("Lifted: ")
        children = card.evaluate("e => [...e.children].map((c) => c.className.split(' ')[0])")
        assert children == ["corner", "hand-card__name", "hand-lifted__body", "hand-lifted__acts", "corner"], children
        top, foot = card.locator(".corner--top"), card.locator(".corner--foot")
        assert top.evaluate("e => e.classList.contains('corner--large')") and foot.evaluate("e => e.classList.contains('corner--large')"), "the corners are drawn large"
        assert top.locator(".corner__rune .ork-elem").count() == 1 and top.locator(".corner__name").inner_text().strip() == "Export the round scores", "the goal's rune and name at the top left"
        assert top.locator(".corner__kind .hand-lifted__kind").text_content().strip() == "Plan ready" and top.locator(".corner__kind .ork-sign").count() == 1, "the kind's word and sign at the top right"
        assert top.evaluate("e => e.firstElementChild.classList.contains('corner__rune') && e.lastElementChild.classList.contains('corner__kind')")
        assert foot.locator(".corner__who .ork-race__head").count() == 1 and foot.locator(".corner__who .corner__word").inner_text().strip() == "the Tech leader asks", "who asks at the foot's left"
        assert foot.locator(".corner__much .ork-gem").count() == 1, "the cost at its right"
        assert card.locator(".hand-card__window, .hand-card__label, .hand-card__party").count() == 0, "the former window, label row and foot are gone"
        assert card.locator(".hand-card__name").inner_text().strip() == "Export the round scores"
        acts = card.locator(".hand-lifted__acts")
        assert acts.get_by_role("button", name="Start the work").count() == 1 and acts.get_by_role("button", name="Put it back").count() == 1 and acts.locator(".hand-spend").count() == 1
        m = card.evaluate(MEASURE)
        if width == "wide":
            assert m["width"] == 404 and abs(m["height"] - 566) <= 1, (m["width"], m["height"])
            assert abs(m["width"] / m["height"] - 5 / 7) < 0.01, "5 : 7"
        else:
            assert abs(m["width"] - (m["vw"] - 16)) <= 1, "the screen's width less a gutter a side"
        assert 1 <= abs(float(m["rotate"].removesuffix("deg"))) <= 2, m["rotate"]
        assert abs(m["footBottom"] - m["handTop"]) <= 14, "its foot stands on the hand's line"
        assert m["bodyTop"] >= m["topBottom"] - 6 and m["actsTop"] >= m["bodyBottom"] - 6 and m["footTop"] >= m["actsBottom"] - 6, "the body lies between the corners, the answers above the foot"
        assert m["overflowY"] == "auto" and m["mask"] and m["mask"] != "none", "the body scrolls and fades at its foot"
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
        if card.get_by_role("button", name="More").count():                     # one sentence shows, the rest is behind its … (spec 140 A4): opened, the long body scrolls
            card.get_by_role("button", name="More").click()
        m = card.evaluate(MEASURE)
        assert m["height"] <= m["maxHeight"] + 1 and m["maxHeight"] < m["vh"], "the card stops at its most height"
        if width == "wide":
            assert m["scrolls"] and m["width"] == 404 and m["height"] <= 566 + 1, "the body scrolls inside, the card never grows past 404 x 566"
            card.locator(".hand-lifted__body").evaluate("e => { e.scrollTop = e.scrollHeight; }")
        assert card.get_by_role("button", name="Put it back").is_visible(), "the buttons stay above the foot whatever the body holds"
        assert not m["sideways"] and card.locator(".corner--foot").is_visible() and card.locator(".corner--top").is_visible() and card.locator(".hand-lifted__title").is_visible()
        box = card.bounding_box()
        assert box["y"] >= 0 and box["x"] >= -1 and box["x"] + box["width"] <= m["vw"] + 1
        shot(pg, f"{width}-lifted-long")
        pg.locator(".hand-lifted").get_by_role("button", name="Put it back").click()
        assert pg.locator(".hand-lifted").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


class SaidHost(HandHost):
    """The hand's host with a failed task whose error is `error`."""

    def __init__(self, error):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "timer":
                n["tasks"][0]["error"] = error


@pytest.mark.parametrize("kind,signal", [("failed", "fails"), ("asks", "asks")])
def test_a_lifted_card_keeps_its_signal(gui, kind, signal):
    """Decisions §53.5 (a signal is always seen): lifted, a failure is ringed in danger and a question in alert, as at rest."""
    pg, host, log = open_hand(gui, width="wide")
    try:
        card = lift(pg, kind)
        assert signal in card.get_attribute("class").split(), f"the lifted {kind} card keeps its signal's class"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_lifted_card_does_not_draw_a_line_that_repeats_its_title(gui):
    """Spec 140 A4, decisions §247.6: a line equal to the title is not drawn."""
    pg, host, log = open_hand(gui, host=SaidHost("Reset the clock."), width="wide")
    try:
        card = lift(pg, "failed")
        assert card.locator(".hand-lifted__title").inner_text().strip() == "Reset the clock"
        assert card.locator("[data-said]").count() == 0 and card.get_by_text("Reset the clock").count() == 1, "the line that repeats the title is not drawn"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_lifted_card_says_one_sentence_and_the_rest_behind_its_dots(gui):
    pg, host, log = open_hand(gui, host=SaidHost("The reset test failed. Run it again after the change. Then read the log."), width="wide")
    try:
        card = lift(pg, "failed")
        said = card.locator("[data-said]")
        assert said.count() == 1 and said.evaluate("e => e.firstChild.textContent.trim()") == "The reset test failed." and "Run it again" not in said.inner_text(), "one sentence"
        said.get_by_role("button", name="More").click()
        assert "Run it again after the change." in said.inner_text() and "Then read the log." in said.inner_text(), "the rest behind its …"
        said.get_by_role("button", name="Less").click()
        assert "Run it again" not in said.inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


class PricedHost(HandHost):
    """The hand's host with Design's question about the phones' timer answered by ways that have a price (`asked[].costs`)."""

    def __init__(self):
        super().__init__()
        costs = [{"usd_low": 1.0, "usd_high": 1.0}, {"usd_low": 3.0, "usd_high": 4.0}]
        for row in [*self.nodes, *self.needs]:
            if row.get("slug") == "phones" or row.get("idea") == "phones":
                for q in row["asked"]:
                    q["costs"] = costs


def test_picking_a_way_changes_the_cost_at_the_opened_cards_foot(gui):
    """Spec 147 D.1, decisions §251.6: the foot's bottom right is the cost of the way picked; it changes as another is picked, and Answer sends the way picked."""
    pg, host, log = open_hand(gui, host=PricedHost(), width="wide")
    try:
        pg.locator('.hand-card[data-key="asks/phones/"]').first.click(position={"x": 10, "y": 20})
        card = pg.locator(".hand-lifted")
        card.wait_for(timeout=WAIT_MS)
        ways = card.get_by_role("radio")
        assert ways.count() == 2 and ways.nth(0).get_attribute("aria-checked") == "true", "the way the asker recommends is picked"
        cost = card.locator(".corner--foot .corner__much .ork-gem")
        first, second = ways.nth(0).get_attribute("data-cost"), ways.nth(1).get_attribute("data-cost")
        assert first and second and first != second, (first, second)
        assert cost.get_attribute("data-cost") == first, "the foot shows the picked way's cost"
        ways.nth(1).click()
        assert ways.nth(1).get_attribute("aria-checked") == "true" and ways.nth(0).get_attribute("aria-checked") == "false"
        expect(cost).to_have_attribute("data-cost", second, timeout=WAIT_MS)   # another way picked: the foot's cost is its (it is drawn on the next frame)
        ways.nth(0).click()
        expect(cost).to_have_attribute("data-cost", first, timeout=WAIT_MS)
        ways.nth(1).click()
        shot(pg, "wide-lifted-priced")
        card.get_by_role("button", name="Answer", exact=True).click()
        sent = [a for n, a in host.log if n == "ideas.answer"]
        assert sent and sent[-1]["answers"] == ["Each phone counts down alone"] and sent[-1]["slug"] == "phones", sent
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_way_without_a_price_leaves_the_cards_own_cost_at_the_foot(gui):
    pg, host, log = open_hand(gui, width="wide")
    try:
        card = lift(pg, "plan")
        gem = card.locator(".corner--foot .corner__much .ork-gem")
        assert gem.get_attribute("data-cost") == card.locator(".hand-spend .ork-gem").get_attribute("data-cost"), "the card's own cost at its foot"
    finally:
        pg.close()
    assert not log, "\n".join(log)


DOT = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"       # a picture that loads, so the page logs no 404


class PictureHost(HandHost):
    """The hand's host with a picture on the failing goal and none on the plan's."""

    def __init__(self):
        super().__init__()
        for n in self.nodes:
            if n["slug"] == "timer":
                n["picture"] = DOT


def test_the_opened_card_has_its_window_at_the_top_of_its_body_160_px_high(gui):
    """Spec 148 B.5, decisions §252.3: the goal's picture, 160 px high, first in the body that scrolls; the card stays 404 x 566. Without a picture the body is its question."""
    pg, host, log = open_hand(gui, host=PictureHost(), width="wide")
    try:
        card = lift(pg, "failed")
        win = card.locator(".hand-lifted__body > .hand-lifted__win .card-win")
        assert win.count() == 1 and win.get_attribute("data-window") == "card-picture" and win.locator("img").get_attribute("src") == DOT
        assert win.evaluate("e => e.offsetHeight") == 160, "160 px high"
        assert card.evaluate("e => e.querySelector('.hand-lifted__body').firstElementChild.classList.contains('hand-lifted__win')"), "at the top of its body"
        m = card.evaluate(MEASURE)
        assert m["width"] == 404 and abs(m["height"] - 566) <= 1, "the card stays 404 x 566"
        shot(pg, "wide-lifted-window")
        card.get_by_role("button", name="Put it back").click()
        card = lift(pg, "plan")
        assert card.locator(".card-win").count() == 0, "no picture, no made: nothing extra, its question is its body"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_opened_cards_words_are_the_glossarys():
    import re
    from orkboard.realm import lexicon
    js = (Path(__file__).resolve().parents[1] / "orkboard/gui/static/js/hand/openwords.js").read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (SLOT_RUNE = .*?);\n", js).group(1)))
    assert got == {"SLOT_RUNE": lexicon.term("slot_rune"), "SLOT_WHO": lexicon.term("slot_who"), "SLOT_KIND": lexicon.term("slot_kind"), "NOW": lexicon.term("now"), "LATER": lexicon.term("later"), "SLOT_MUCH": lexicon.term("slot_much"), "ATTACH_HINT": lexicon.term("attach_hint"), "LEADER": lexicon.term("opened_leader"), "ASKS": lexicon.term("opened_asks")}
