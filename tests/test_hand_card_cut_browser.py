"""The hand's card, cut under its title (docs/specs/147-one-card-four-corners.md part C, decisions §251.5), in a real browser against the hand's stub host: the card is 144 x 202 with its corners' top row (the goal's rune at the left, the kind's
sign at the right, no head there) and its title whole in three lines; the rim of the hand cuts it at 100 px (62 px at the narrow width) between two lines; the hand is as tall as the cut and its padding unless the die and the potions need more, and
then the cards keep their top and show more, the cut kept between two lines; hovered or focused the card rises by what is hidden and shows its foot row (who asks, how much), at once under reduced motion; the narrow hand is laid by leader, a head before
each leader's group (the Orkmaster's crown before the first lane's). The words of the face are the glossary's (tests/test_hand_desktop_browser.py has the rest)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, lane, open_hand  # noqa: E402

pytestmark = pytest.mark.browser

SHOWN = {"wide": 100, "narrow": 62}
TOP = 8                                                    # the hand's own room above its cards (`--hc-top`)

# every line box of a card's title and why, as [top, bottom] in the page
LINES = """(card) => [...card.querySelectorAll('.hand-card__name, .hand-card__foot')].flatMap((e) => {
  const out = [], walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) { const r = document.createRange(); r.selectNodeContents(t); for (const b of r.getClientRects()) out.push([b.top, b.bottom]); }
  return out; })"""


def settle(pg):
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(900)


def edge(pg, selector):
    """The bottom of the first element that matches, or 0."""
    return pg.evaluate("(s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().bottom : 0; }", selector)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_rim_cuts_the_card_after_its_title_and_the_hand_is_as_tall_as_the_cut_unless_the_die_and_the_potions_need_more(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        settle(pg)
        card = pg.locator('.hand-card[data-goal="timer"]')
        box, hand = card.bounding_box(), pg.locator(".hand").bounding_box()
        shown, bottom = SHOWN[width], hand["y"] + hand["height"]
        visible = bottom - box["y"]
        needs = max(edge(pg, ".hand-die"), edge(pg, ".hand-mana")) - box["y"]                   # what the die and the potions reach down to, from the cards' top
        assert needs > 0 and card.evaluate("e => [e.offsetWidth, e.offsetHeight]") == ([144, 202] if width == "wide" else [80, 112]), (box, needs)
        assert visible >= max(shown, needs) - 1, f"the hand holds the cut and the die and the potions: {visible} for {shown} and {needs}"
        lines = pg.evaluate(LINES, card.element_handle())
        cut = box["y"] + visible
        assert lines and all(b <= cut + 0.5 or t >= cut - 0.5 for t, b in lines), f"the cut lies between two lines, not through one: {lines} at {cut}"
        if needs <= shown:
            assert abs(visible - shown) <= 1
        else:
            card_h = box["height"]
            assert visible <= max(needs, card_h) + 18, "the cards show more by a line or two, no more than the die and the potions need"
        assert hand["height"] == pytest.approx(visible + TOP + 3, abs=1.5), "the hand's own height: its room above, its rim and what shows"
        # nothing needs more: the hand is the cut plus its paddings, the card's title and its rune row whole above it
        pg.evaluate("() => document.querySelector('.hand').style.setProperty('--hc-ends', '0px')")
        pg.wait_for_timeout(300)
        hand2, box2 = pg.locator(".hand").bounding_box(), card.bounding_box()
        assert (hand2["y"] + hand2["height"]) - box2["y"] == pytest.approx(shown, abs=1), "the visible height is the cut"
        assert hand2["height"] == pytest.approx(shown + TOP + 3, abs=1.5)
        name = pg.locator('.hand-card[data-goal="timer"] .hand-card__name').bounding_box()
        assert name["y"] + name["height"] <= box2["y"] + shown, "the title shows whole above the cut"
        assert pg.locator('.hand-card[data-goal="timer"] .corner--top').bounding_box()["y"] + 20 <= name["y"] + 1
        assert pg.evaluate(LINES, card.element_handle()) and all(b <= box2["y"] + shown + 0.5 or t >= box2["y"] + shown - 0.5 for t, b in pg.evaluate(LINES, card.element_handle()))
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_card_hovered_rises_by_what_the_rim_hides_and_shows_its_foot_row(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        settle(pg)
        pg.evaluate("() => document.querySelector('.hand').style.setProperty('--hc-ends', '0px')")           # the cut alone: the card rises by 202 - 100 (112 - 62)
        pg.wait_for_timeout(300)
        card = pg.locator('.hand-card[data-goal="theme"]')
        slot = pg.locator('.hand-slot:has(.hand-card[data-goal="theme"])')
        foot, why = card.locator(".corner--foot"), card.locator(".hand-card__foot")
        h = pg.viewport_size["height"]
        rest, rest_slot = card.bounding_box(), slot.bounding_box()
        assert foot.bounding_box()["y"] >= h, "at rest the foot row lies under the rim"
        card.hover(position={"x": 12, "y": 12}, force=True)                                                     # on its left edge: at the narrow width the die lies over the last card's middle
        pg.wait_for_timeout(600)
        up, up_slot = card.bounding_box(), slot.bounding_box()
        assert foot.bounding_box()["y"] + foot.bounding_box()["height"] <= h + 1 and foot.locator(".ork-race__head").count() == 1, "risen, the foot row shows: who asks and how much"
        if width == "wide":
            assert rest_slot["y"] - up_slot["y"] == pytest.approx(202 - 100, abs=1) and up["y"] + up["height"] == pytest.approx(h, abs=3), "it rises by what the cut hid"
            assert why.bounding_box()["y"] + why.bounding_box()["height"] <= foot.bounding_box()["y"] + 1, "its why lies over the foot row"
        else:
            assert up["y"] < rest["y"] and up["y"] + up["height"] <= h + 7
        pg.mouse.move(pg.viewport_size["width"] / 2, 120)
        pg.wait_for_timeout(600)
        assert foot.bounding_box()["y"] >= h, "lowered, the foot row lies under the rim again"
        card.focus()                                                                                           # keyboard focus raises it too
        pg.wait_for_timeout(600)
        assert foot.bounding_box()["y"] + foot.bounding_box()["height"] <= h + 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_hovered_shows_whole_at_once_under_reduced_motion(gui):
    server, browser = gui
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    host = HandHost()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        settle(pg)
        card = pg.locator('.hand-card[data-goal="theme"]')
        assert pg.locator('.hand-slot:has(.hand-card[data-goal="theme"])').evaluate("e => getComputedStyle(e).transitionDuration") in ("0s", "0s, 0s")
        card.hover(position={"x": 12, "y": 12})
        pg.wait_for_timeout(60)
        foot = card.locator(".corner--foot").bounding_box()
        assert foot["y"] + foot["height"] <= 801, "whole at once, with no spring"
    finally:
        ctx.close()


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_hands_cards_are_the_goals_rune_and_kind_over_a_whole_title_with_no_head_on_top(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(extra=True), width=width)
    try:
        settle(pg)
        cards = pg.locator(".hand .hand-card--face")
        assert cards.count() >= 6
        for c in cards.all():
            top = c.locator(".corner--top")
            assert top.count() == 1 and c.locator(".corner--foot").count() == 1, "one top row and one foot row"
            assert top.locator(".corner__rune .ork-elem").count() == 1 and top.locator(".ork-race__head").count() == 0, "the rune at the top and no head there"
            assert top.evaluate("e => e.firstElementChild.classList.contains('corner__rune') && e.lastElementChild.classList.contains('corner__kind')"), "the rune first, the kind last"
            assert c.locator(".hand-card__party, .hand-card__label, .hand-card__gem, .hand-card__asker").count() == 0, "no party label, no gem and no asker's head on the face"
            name = c.locator(".hand-card__name")
            assert name.evaluate("""e => { const r = e.getBoundingClientRect(), w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), lines = [];
              for (let t = w.nextNode(); t; t = w.nextNode()) { const g = document.createRange(); g.selectNodeContents(t); for (const b of g.getClientRects()) lines.push(b); }
              return lines.length > 0 && lines.every((b) => b.top >= r.bottom - 0.5 || b.bottom <= r.bottom + 0.5); }"""), "the title is not clipped: no line of it is cut through (a longer one ends with its last whole line)"
            assert name.evaluate("e => e.getBoundingClientRect().height") == (60 if width == "wide" else 36), "three (two) whole lines"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_hand_is_laid_by_leader_a_head_before_each_leaders_group(gui):
    """At 700 px (still the narrow layout, under 760): room for the heads. At 390 px with the die and the potions the row has none to spare: the separators give way to a hairline (the cards tighten first), never a sideways scroll."""
    server, browser = gui
    pg = browser.new_context(viewport={"width": 700, "height": 844}).new_page()
    host, log = HandHost(extra=True), []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    try:
        settle(pg)
        seps = pg.locator(".hand-sep")
        groups = [i for i in range(5) if lane(pg, i).locator(".hand-stack").count()]
        assert groups == [0, 1, 2, 3] and seps.count() == len(groups), "a separator before each lane that holds cards: the project's, Tech's, Design's, Product's"
        races = [seps.nth(k).locator(".ork-race__head").get_attribute("src") for k in range(len(groups))]
        assert ["peon-crown" in races[0], "shaman" in races[1], "dryad" in races[2], "unicorn" in races[3]] == [True] * 4, races
        xs = []
        for k, i in enumerate(groups):
            sep = seps.nth(k).bounding_box()
            first = lane(pg, i).locator(".hand-slot:not(.is-plus)").first.bounding_box()
            assert 21.5 <= sep["width"] <= 22.5 and abs(seps.nth(k).locator(".ork-race__head").bounding_box()["height"] - 16) <= 0.5, "a 22 px separator with the leader's 16 px head"
            assert sep["x"] + sep["width"] <= first["x"] + 1, "the head is before its group's cards"
            xs.append(sep["x"])
        assert xs == sorted(xs), "in the lanes' order"
        narrow.no_sideways(pg)
    finally:
        pg.context.close()
    assert not log, "\n".join(log)


def test_a_crowded_narrow_hand_gives_its_separators_way_before_it_scrolls_sideways(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        settle(pg)
        narrow.no_sideways(pg)
        assert pg.locator(".hand-row").evaluate("e => e.scrollWidth <= e.clientWidth + 1")
        assert pg.locator(".hand-sep").count() == 3 and all(s["width"] >= 1 for s in (e.bounding_box() for e in pg.locator(".hand-sep").all()))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_wide_hand_has_no_separator_the_lane_says_who(gui):
    pg, host, log = open_hand(gui, host=HandHost(extra=True), width="wide")
    try:
        settle(pg)
        assert pg.locator(".hand-sep").count() > 0 and all(not e.is_visible() for e in pg.locator(".hand-sep").all())
    finally:
        pg.close()
    assert not log, "\n".join(log)
