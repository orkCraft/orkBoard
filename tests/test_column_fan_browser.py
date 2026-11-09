"""Spec 147 B (docs/specs/147-one-card-four-corners.md, decisions §251.3–§251.4; mockup docs/mockups/card-ratio/), in a real browser against a stub host: the Orkmaster's hand is a near-straight fan of 56 x 78 backs no wider than 144 px whatever it holds, the goal being read lifted; the column never
scrolls at 650, 790 and 940 px of window and *At work · later* gives way (a foot, an edge, then the pile sinks under the hand's rim); To review is a deck of backs whose ring fills by the share of the wait, a goal that asks the person has the ring and the frame in the alert and is never the next to start,
and the next to start is named under the title; `giveWay` (table/giveway.js) and the words of the piles (realm/lexicon.py `column_reading`, `next_in`, `next_at`)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, back, open_column, ripe  # noqa: E402
from tests.test_hand_desktop_browser import call, node, task  # noqa: E402

pytestmark = pytest.mark.browser
PILES_JS = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "js" / "table" / "stages.js"


class FanHost(ColumnHost):
    """Eight goals in analysis, two of To review (one asks the person), four at work."""

    def __init__(self, analysis=8, work=4):
        super().__init__()
        self.nodes = [node(f"a{i}", "tech", f"Goal in analysis {i}", "deck", state="reading" if i == 0 else "raw", element=("ice", "lava", "dust", "void", "meadow")[i % 5]) for i in range(analysis)]
        self.nodes += [
            node("asking", "tech", "Which clock to keep", "table", state="ready", agreed=True, element="void", asks_you=True, back=back(ripe=None)),
            node("soon", "tech", "Round timer on phones", "table", state="ready", agreed=True, element="ice", back=back(ripe=ripe(120, seconds=240))),
        ]
        self.nodes += [node(f"w{i}", "design", f"Goal at work {i}", "table", state="working", element="meadow", stage="implementation", tasks=[task(f"t{i}", "Do it", "running")]) for i in range(work)]


def at(pg, height):
    pg.set_viewport_size({"width": 1280, "height": height})
    pg.mouse.move(700, 300)
    pg.wait_for_timeout(300)                                                               # the observer measures, the page lays the pile again


def test_the_fan_of_eight_is_no_wider_than_144_px_each_back_a_step_apart_and_the_one_read_lifted(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        cards = pg.locator(".col-card--fan")
        assert cards.count() == 8
        left = cards.evaluate_all("els => els.map((e) => e.offsetLeft)")
        assert [b - a for a, b in zip(left, left[1:])] == [12] * 7, f"floor(88 / 7) = 12 px apart ({left}): 12 to 16, tighter after seven"
        assert max(x + 56 for x in left) <= 144 and pg.locator(".col-fan").evaluate("e => e.offsetWidth") <= 144, "never wider than 144 px"
        assert cards.evaluate_all("els => els.map((e) => [e.offsetWidth, e.offsetHeight])") == [[56, 78]] * 8
        assert cards.evaluate_all("els => els.map((e) => e.style.getPropertyValue('--r'))") == ["-14deg", "-10deg", "-6deg", "-2deg", "2deg", "6deg", "10deg", "14deg"], "4 degrees a card past seven, about the middle"
        sink = cards.evaluate_all("els => els.map((e) => parseFloat(e.style.getPropertyValue('--sink')))")
        assert sink[:4] == sorted(sink[:4], reverse=True) and sink[4:] == sorted(sink[4:]) and sink[0] == sink[7] > sink[3] == sink[4], f"an arc: the ends lie lower than the middle ({sink})"
        z = cards.evaluate_all("els => els.map((e) => Number(getComputedStyle(e).zIndex))")
        assert z[1:] == sorted(z[1:]) and z[1] < z[2], "the later back over the earlier"
        lifted = pg.evaluate("() => [...document.querySelectorAll('.col-card--fan')].map((e) => Math.round(new DOMMatrix(getComputedStyle(e).transform).f - parseFloat(e.style.getPropertyValue('--sink'))))")
        assert lifted == [-12] + [0] * 7, "the goal being read stands 12 px out of the fan"
        under = pg.locator('[data-under="analysis"]')
        assert under.inner_text() == "reading: Goal in analysis 0" and under.bounding_box()["y"] < pg.locator(".col-fan").bounding_box()["y"], "named under the title, over the hand"
        assert pg.locator(".col-fan").bounding_box()["height"] == 92, "the fan is about 90 px tall whatever it holds"
        pg.locator(".col-card--fan").nth(6).hover(position={"x": 5, "y": 50})                 # its left 12 px: the next back lies over the rest
        pg.wait_for_timeout(100)
        assert pg.evaluate("() => { const e = document.querySelectorAll('.col-card--fan')[6]; return Math.round(new DOMMatrix(getComputedStyle(e).transform).f - parseFloat(e.style.getPropertyValue('--sink'))); }") == -10, "a back hovered rises 10 px"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_step_and_the_turn_of_a_fan_by_how_many_it_holds(gui):
    pg, host, log = open_column(gui, host=FanHost(analysis=1, work=1))
    try:
        got = [call(pg, "table/fan.js", "stepOf", n) for n in (0, 1, 2, 3, 4, 6, 7, 8, 9, 12, 30)]
        assert got == [0, 0, 16, 16, 16, 16, 14, 12, 11, 8, 6], "16 while few, 14 at seven (seven within the column's 160 px), 88 / (n - 1) as they grow, never under 6, never a count"
        assert all(56 + (n - 1) * call(pg, "table/fan.js", "stepOf", n) <= 144 for n in range(2, 8)), "up to seven within 144 px"
        assert [call(pg, "table/fan.js", "turnStep", n) for n in (2, 4, 5, 7, 8, 12)] == [6, 6, 5, 5, 4, 4], "4 to 6 degrees a card"
        assert [call(pg, "table/fan.js", "turnOf", i, 4) for i in range(4)] == [-9, -3, 3, 9] and call(pg, "table/fan.js", "turnOf", 1, 3) == 0
        assert [call(pg, "table/fan.js", "stepOf", n, True) for n in (2, 3, 4, 9)] == [44, 44, 29, 11] and call(pg, "table/fan.js", "turnOf", 0, 3, True) == -1.5, "the phone's menu keeps the fan it had"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("height", [650, 790, 940])
def test_the_column_never_scrolls_at_any_of_the_three_heights(gui, height):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        at(pg, height)
        got = pg.evaluate("""() => { const s = document.querySelector('.col-scroll'), r = document.querySelector('.col-room'), c = document.querySelector('.col'); return {
          scroll: [s.scrollHeight, s.clientHeight, getComputedStyle(s).overflowY], col: [c.scrollHeight, c.clientHeight, c.scrollWidth, c.clientWidth], all: [...document.querySelectorAll('.col *')].some((e) => ['auto', 'scroll'].includes(getComputedStyle(e).overflowY) && e.scrollHeight > e.clientHeight + 1 && !e.closest('.col-lift')) }; }""")
        assert got["scroll"][0] <= got["scroll"][1] and got["scroll"][2] == "hidden", got
        assert got["col"][0] <= got["col"][1] and not got["all"], got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def room_and_cards(pg):
    return pg.evaluate("""() => { const r = document.querySelector('.col-room').getBoundingClientRect();
      return {room: {top: r.top, bottom: r.bottom, height: r.height}, sunk: document.querySelector('.col-pile.is-up').classList.contains('is-sunk'),
        cards: [...document.querySelectorAll('.col-sec[data-pile=work] .col-card')].map((e) => { const b = e.getBoundingClientRect(), f = e.querySelector('.corner--foot').getBoundingClientRect(), u = e.querySelector('.corner--top').getBoundingClientRect();
          const mid = document.elementFromPoint(f.left + 8, f.top + f.height / 2);
          return {top: b.top, left: b.left, bottom: b.bottom, rune: u.top + 20, footTop: f.top, footBottom: f.bottom, footSeen: !!mid && mid.closest('.col-card') === e && f.bottom <= r.bottom + 0.5}; }) }; }""")


def test_at_650_the_front_card_shows_its_rune_row_and_the_cards_behind_are_slivers(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        at(pg, 650)
        got = room_and_cards(pg)
        front = got["cards"][0]
        assert got["sunk"], "the pile sank under the hand's rim"
        assert got["room"]["height"] >= 32 and front["top"] >= got["room"]["top"] - 1 and front["rune"] <= got["room"]["bottom"] + 0.5, f"the front card's rune row (its top 32 px) shows ({got})"
        shown = got["room"]["bottom"] - front["top"]
        assert shown >= 32 and ((shown - 32) % 20 < 0.6 or (shown - 32) % 20 > 19.4), f"the rim falls between two lines of the front card (its top 32 px, then 20 px a line): {shown}"
        assert all(not c["footSeen"] for c in got["cards"]), "no foot shows in so little room"
        assert [round(c["left"] - front["left"]) for c in got["cards"]] == [0, 3, 6, 9, 12][: len(got["cards"])] and len({round(c["top"]) for c in got["cards"]}) == 1, "the cards behind lie 3 px to the right each: slivers"
        assert pg.locator(".col-card--up .corner__rune .ork-elem").first.is_visible()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_790_the_cards_behind_give_up_their_feet_for_edges_the_furthest_first_or_the_pile_sinks(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        at(pg, 790)
        got = room_and_cards(pg)
        top = [round(c["top"] - got["cards"][0]["top"]) for c in got["cards"]]
        steps = [b - a for a, b in zip(top, top[1:])]
        if not got["sunk"]:
            assert set(steps) <= {26, 3} and steps == sorted(steps, reverse=True), f"a foot while it fits, then edges, the furthest first: {steps}"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_940_every_card_behind_shows_its_foot(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        at(pg, 940)
        got = room_and_cards(pg)
        assert not got["sunk"] and len(got["cards"]) == 4
        assert [round(b["top"] - a["top"]) for a, b in zip(got["cards"], got["cards"][1:])] == [26, 26, 26], "the foot of each, 26 px"
        assert all(c["footSeen"] for c in got["cards"]), f"every foot (who, how much) is seen, whole and uncovered ({got})"
        assert got["cards"][-1]["bottom"] <= got["room"]["bottom"] + 0.5
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_window_made_taller_lays_the_pile_again_without_a_reload(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        at(pg, 650)
        assert room_and_cards(pg)["sunk"]
        at(pg, 940)
        assert not room_and_cards(pg)["sunk"], "the observer measured again"
        at(pg, 650)
        assert room_and_cards(pg)["sunk"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_to_review_names_the_next_to_start_under_its_title_and_a_goal_that_asks_is_never_the_next(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        under = pg.locator('[data-under="review"]')
        assert under.inner_text() == "next in 2 min: Round timer on phones", "its time and its name"
        assert under.locator("b").inner_text() == "Round timer on phones" and under.bounding_box()["y"] < pg.locator(".col-card--spec").first.bounding_box()["y"], "named under the title, over the deck"
        assert [c.get_attribute("data-goal") for c in pg.locator(".col-card--spec").all()] == ["soon", "asking"], "the one that starts first in front"
        by = {n["slug"]: n for n in host.nodes}
        by["soon"].update(asks_you=True, back=back(ripe=None))                                  # now the timer asks the person ...
        by["asking"].update(asks_you=False, back=back(ripe=ripe(30, seconds=240)))              # ... and the other one's wait runs
        host.bump({})
        pg.wait_for_function("() => document.querySelector('[data-under=review]').textContent === 'next in 30 s: Which clock to keep'", timeout=WAIT_MS)
        by["asking"].update(asks_you=True, back=back(ripe=None))
        host.bump({})
        pg.wait_for_function("() => document.querySelector('[data-under=review]').textContent === ''", timeout=WAIT_MS)       # none starts by itself: nothing is named
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_back_of_the_deck_fills_its_ring_by_the_share_of_the_wait_and_a_goal_that_asks_has_the_ring_and_the_frame_in_the_alert(gui):
    pg, host, log = open_column(gui, host=FanHost())
    try:
        pg.wait_for_selector(".col-card--spec", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        soon, asking = pg.locator('.col-card--spec[data-goal="soon"]'), pg.locator('.col-card--spec[data-goal="asking"]')
        ring = soon.locator(".ork-sigil.is-waiting")
        assert ring.count() == 1 and float(ring.get_attribute("data-share")) == pytest.approx(0.5), "120 of 240 s left: half of the ring"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--spec[data-goal=soon] .ork-sigil'), '::after').getPropertyValue('--_arc')").strip() == "180deg", "four places of eight"
        assert soon.locator(".col-spec__rune .ork-elem").count() == 1 and soon.locator(".corner").count() == 0, "its ring holds the rune: no corners"
        ice, alert = pg.evaluate("() => [getComputedStyle(document.documentElement).getPropertyValue('--ork-elem-ice').trim(), getComputedStyle(document.documentElement).getPropertyValue('--ork-alert').trim()]")
        paint = lambda c: pg.evaluate("(c) => { const s = document.createElement('i'); s.style.color = c; document.body.append(s); const v = getComputedStyle(s).color; s.remove(); return v; }", c)  # noqa: E731
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--spec[data-goal=soon] .ork-sigil'), '::after').color") == paint(ice), "its ring in the goal's colour"
        assert "asks" in asking.get_attribute("class").split() and asking.locator(".ork-sigil.col-stopped").count() == 1
        assert float(asking.locator(".ork-sigil").get_attribute("data-share")) == 1 and asking.locator(".ork-sigil").evaluate("e => e.classList.contains('col-busy')") is False, "the ring full and still"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--spec[data-goal=asking] .ork-sigil'), '::after').color") == paint(alert), "in the alert"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--spec[data-goal=asking]')).borderTopColor") == paint(alert), "and its frame"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--spec[data-goal=soon]')).borderTopColor") != paint(alert)
        asking.click(position={"x": 40, "y": 54})                                               # its 4 px under the front back
        assert pg.evaluate("() => import('/static/js/frame/state.js').then((x) => x.picked.value)") == "asking", "a back pressed picks its goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_giveway_feet_then_edges_the_furthest_first_then_the_pile_sinks_to_a_line(gui):
    pg, host, log = open_column(gui, host=FanHost(analysis=1, work=1))
    try:
        way = lambda room, behind, front=202: call(pg, "table/giveway.js", "giveWay", {"room": room, "front": front, "behind": behind})  # noqa: E731
        assert way(400, 3) == {"steps": [26, 26, 26], "sunk": 0, "push": 0}, "it fits: every card behind a foot"
        assert way(202, 0) == {"steps": [], "sunk": 0, "push": 0} and way(400, 0)["sunk"] == 0, "nothing behind, nothing to give"
        assert way(202 + 26 * 2 + 3, 3)["steps"] == [26, 26, 3], "the furthest card's foot gives way first"
        assert way(202 + 26 + 3 + 3, 3)["steps"] == [26, 3, 3]
        assert way(202 + 9, 3) == {"steps": [3, 3, 3], "sunk": 0, "push": 0}, "all edges, and it fits"
        # sunk: the front card shows `room`, the rim falls between two lines (its top 32 px, then 20 px a line)
        got = way(150, 3)
        assert got["sunk"] == 202 - 132 and got["push"] == 150 - 132, "150 shows 32 + 5 lines would be 132: the pile moves 18 px further under"
        assert 202 - got["sunk"] == 132 and (132 - 32) % 20 == 0
        assert way(132, 3)["push"] == 0 and way(132, 3)["sunk"] == 70, "a rim already between two lines stays"
        assert way(45, 5)["sunk"] == 202 - 32 and way(45, 5)["push"] == 13, "the rune row alone shows"
        assert way(20, 2)["sunk"] == 202 and way(20, 2)["push"] == 20, "less than the rune row: it is under the rim"
        assert way(300, 3, front=202)["sunk"] == 0 and way(-5, 1)["sunk"] == 202
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.browser
def test_the_pages_column_words_are_the_glossarys():
    js = PILES_JS.read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (READING = .*?);", js).group(1).replace(", ", ";\n")))
    assert got == {"READING": lexicon.term("column_reading"), "WRITING": lexicon.term("column_writing"), "AT_WORK": lexicon.term("column_at_work"), "NEXT_IN": lexicon.term("next_in"), "NEXT_AT": lexicon.term("next_at")}
    titles = re.search(r"export const PILES = (\[.*?\]);", js).group(1)
    assert re.findall(r'"([^"]+)"\]', titles) == [lexicon.term("pile_ideas"), lexicon.term("pile_specs"), lexicon.term("pile_implementation")]


def test_seven_backs_lie_within_the_columns_160_px_and_a_picked_back_rises_with_its_ring(gui):
    """Spec 168 B2 (decisions §283.13): seven backs 14 px apart, 5 degrees a card, within 160 px, never a count; the picked back risen, its back `.is-ringed`."""
    pg, host, log = open_column(gui, host=FanHost(analysis=7))
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        cards = pg.locator(".col-card--fan")
        assert cards.count() == 7
        left = cards.evaluate_all("els => els.map((e) => e.offsetLeft)")
        assert [b - a for a, b in zip(left, left[1:])] == [14] * 6 and max(x + 56 for x in left) <= 144 <= 160, left
        assert cards.evaluate_all("els => els.map((e) => e.style.getPropertyValue('--r'))") == ["-15deg", "-10deg", "-5deg", "0deg", "5deg", "10deg", "15deg"]
        assert not any(ch.isdigit() for ch in pg.locator(".col-sec[data-pile=analysis] .col-plab").inner_text()), "never a count"
        assert pg.locator(".col-fan .is-ringed").count() == 0
        cards.nth(3).click(position={"x": 8, "y": 50})
        pg.wait_for_selector(".col-card--fan.ork-picked", timeout=WAIT_MS)
        picked = pg.locator(".col-card--fan.ork-picked")
        assert picked.get_attribute("data-goal") == "a3" and picked.locator(".ork-card-back.is-ringed").count() == 1, "the picked back wears the ring"
        assert pg.evaluate("() => { const e = document.querySelector('.col-card--fan.ork-picked'); return Math.round(new DOMMatrix(getComputedStyle(e).transform).f - parseFloat(e.style.getPropertyValue('--sink'))); }") == -10, "and rises"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--fan.ork-picked .ork-card-back')).clipPath") == "none", "orkUI 0.37.0: the ringed back loses the notch's clip"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_column_never_scrolls_at_1366_by_768_with_the_new_piles(gui):
    """Spec 168 B2: Ideas' fan, Specs' small deck and Implementation's cascade fit the table's height at the common laptop screen; only Implementation gives way."""
    pg, host, log = open_column(gui, host=FanHost())
    try:
        pg.set_viewport_size({"width": 1366, "height": 768})
        pg.mouse.move(700, 300)
        pg.wait_for_timeout(300)
        got = pg.evaluate("""() => { const s = document.querySelector('.col-scroll'), c = document.querySelector('.col'); return {scroll: [s.scrollHeight, s.clientHeight, getComputedStyle(s).overflowY], col: [c.scrollHeight, c.clientHeight]}; }""")
        assert got["scroll"][0] <= got["scroll"][1] and got["scroll"][2] == "hidden" and got["col"][0] <= got["col"][1], got
        assert pg.locator(".col-sec[data-pile=review] .col-card--spec").first.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [78, 56], "Specs' cards lie on their side, 78 x 56"
    finally:
        pg.close()
    assert not log, "\n".join(log)
