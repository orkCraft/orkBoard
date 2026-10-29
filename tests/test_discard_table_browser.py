"""The discard on the table (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §4, §7; decisions §176.3), in a real browser at the two widths of `tests/narrow.py`: the pile lies in the table's last column (right of the
lanes) at its foot, aligned right, the hand card's size, with the word *Discard* above it, on the project's tab and on a party's tab (where the party's map ends beside it and scrolls as it did), and not in the hand; none with nothing
done and nothing ready for main; its press opens the `discard` face over the pane and a second press closes it; at the narrow width it lies at the lanes' end (80 px wide) and a card lifted from the hand stands over it.
Screenshots to $DISCARD_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, open_hand, sig  # noqa: E402
from tests.test_maps_desktop_browser import MapsHost  # noqa: E402
from tests.test_table_desktop_browser import node  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["DISCARD_SHOTS"]) if os.environ.get("DISCARD_SHOTS") else None
CARD = {"wide": (144, 202), "narrow": (80, 112)}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def box(pg, selector):
    return pg.locator(selector).first.bounding_box()


def open_maps(gui, width, done=True):
    """The window against the maps' host (a party of each craft) with goals done, at `width`, on the Orkmaster's tab."""
    server, browser = gui
    host = MapsHost()
    if done:
        host.nodes.append(node("music", "tech", "Lobby music loop", "done", element="void", place="discard", updated="2026-10-20T12:00:00"))
        host.nodes.append(node("codes", "game", "Room codes are four letters", "done", element="dust", place="discard", updated="2026-10-19T12:00:00"))
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_discard_lies_at_the_foot_of_the_projects_last_column_not_in_the_hand(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        assert pg.locator(".hand .hand-done, .hand .table-discard, .hand .table-end").count() == 0, "none in the hand"
        assert pg.locator(".hand-end > :not(.hand-mana):not(.hand-logs)").count() == 0, "`.hand-end` holds the mana and the logs button alone (spec 107 §10)"
        pile, label = box(pg, ".table-discard"), box(pg, ".table-end__label")
        assert pg.locator(".table-end__label").text_content() == "Discard" and label["y"] + label["height"] <= pile["y"] + 1, "the word above the pile"
        assert (round(pile["width"]), round(pile["height"])) == CARD[width], "the hand card's size"
        hand_card = pg.locator(".hand .hand-card").first.bounding_box()
        assert round(hand_card["width"]) == round(pile["width"]), "the same width as a card of the hand"
        body, hand = box(pg, ".table-body"), box(pg, ".hand")
        assert pile["y"] + pile["height"] <= body["y"] + body["height"] and body["y"] + body["height"] - (pile["y"] + pile["height"]) <= 40, "at the column's foot, above the hand"
        assert pile["y"] + pile["height"] <= hand["y"] + 1
        last = box(pg, ".table-lane--free")
        assert pile["x"] >= last["x"] - 1 and pile["x"] + pile["width"] <= last["x"] + last["width"] + 1, "in the last column, right of the lanes"
        assert pile["x"] + pile["width"] >= last["x"] + last["width"] - 40, "aligned right"
        lanes = pg.locator(".table-board .table-lane:not(.table-lane--free)").evaluate_all("els => els.map((e) => e.getBoundingClientRect().right)")
        assert pile["x"] >= max(lanes) - 1, "none of the lanes lies under it"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-project")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_on_a_partys_tab_the_map_ends_beside_the_pile_and_still_scrolls(gui, width):
    pg, host, log = open_maps(gui, width)
    try:
        call(pg, "frame/state.js", "openTab", "art")
        pg.locator(".mp").first.wait_for(timeout=WAIT_MS)
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        pile, pane, head = box(pg, ".table-discard"), box(pg, ".table-body"), box(pg, ".table-head")
        mp = pg.locator(".mp").first
        m = mp.bounding_box()
        assert abs((head["x"] + head["width"]) - (pane["x"] + pane["width"])) <= 2, "the party's header keeps the pane's whole width"
        assert pile["y"] + pile["height"] <= pane["y"] + pane["height"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40, "the pile at the foot"
        if width == "wide":
            assert m["x"] + m["width"] <= pile["x"] + 1, "the map ends before the pile's column"
        else:
            assert m["y"] + m["height"] <= pile["y"] - 10, "the map ends above the pile"
        assert pg.locator(".mp-scroll").first.evaluate("e => getComputedStyle(e).overflowY") == "auto", "the map scrolls as it did"
        assert pg.locator(".table-end").count() == 1
        narrow.no_sideways(pg)
        shot(pg, f"{width}-party-map")
        call(pg, "frame/state.js", "openTab", "orkmaster")                                                                 # the project's tab again: the pile is still there
        pg.wait_for_selector(".table-board", timeout=WAIT_MS)
        assert pg.locator(".table-end .hand-done").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_system_map_of_tech_the_pile_lies_at_the_foot_too(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")
        pg.wait_for_selector(".table-head", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        pile, pane = box(pg, ".table-discard"), box(pg, ".table-body")
        assert pg.locator(".table-end .hand-done").count() == 1 and pile["x"] + pile["width"] <= pane["x"] + pane["width"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40
        shot(pg, "wide-tech")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_piles_press_opens_the_face_over_the_pane_and_a_second_press_closes_it(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert done.get_attribute("aria-expanded") == "false"
        done.click()
        pg.locator("#table-pane .hand-discardview").wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["kind"] == "discard" and "is-on" in done.get_attribute("class") and done.get_attribute("aria-expanded") == "true"
        assert pg.locator("#table-pane .hand-discardview").evaluate("e => e.closest('.table-body') !== null"), "the face lies over the pane"
        shot(pg, f"{width}-discard-open")
        done.click()
        assert sig(pg, "frame/state.js", "over") is None and pg.locator("#table-pane .hand-discardview").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_nothing_done_and_nothing_ready_for_main_is_no_pile_and_ready_alone_is_a_back(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True))
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".table-end, .table-discard, .table-end__label").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)
    host = HandHost()                                                                                                       # two goals ready for main, none done to see: that line alone on a back
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    pg, host, log = open_hand(gui, host=host)
    try:
        back = pg.locator(".table-end .hand-done.ork-card-back")
        back.wait_for(timeout=WAIT_MS)
        assert back.get_attribute("aria-label") == "Done. 2 goals ready for main" and pg.locator(".table-end__label").text_content() == "Discard"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_pile_leans_and_rises_on_hover_like_a_card(gui):
    pg, host, log = open_hand(gui)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert "ork-leans" in done.get_attribute("class")
        y0 = done.bounding_box()["y"]
        done.hover()
        pg.wait_for_timeout(500)
        assert done.bounding_box()["y"] < y0, "it rises under the pointer"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discard_is_seen_through_the_result_and_leaves_the_pile(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".table-end .hand-done").click()
        pane = pg.locator("#table-pane")
        pane.get_by_role("region", name="Done, not yet seen").locator('.hand-drow[data-slug="codes"]').click()
        assert sig(pg, "frame/state.js", "over")["kind"] == "result"
        assert host.seen_log == ["codes"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_card_lifted_from_the_hand_stands_over_the_pile(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="failed"]').first.click(position={"x": 10, "y": 20})
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        z = pg.evaluate("() => [getComputedStyle(document.querySelector('.hand')).zIndex, getComputedStyle(document.querySelector('.table-end')).zIndex].map(Number)")
        assert z[0] > z[1], "the hand's layer is above the pile's"
        l, p = lifted.bounding_box(), pg.locator(".table-discard").bounding_box()
        x0, x1 = max(l["x"], p["x"]), min(l["x"] + l["width"], p["x"] + p["width"])
        y0, y1 = max(l["y"], p["y"]), min(l["y"] + l["height"], p["y"] + p["height"])
        if x1 > x0 and y1 > y0:                                                                                              # where they meet, the card is on top
            assert pg.evaluate("([x, y]) => document.elementFromPoint(x, y)?.closest('.hand-lifted') !== null", [(x0 + x1) / 2, (y0 + y1) / 2])
        elif width == "narrow":
            pytest.fail("at the narrow width the lifted card spans the screen and meets the pile")
        shot(pg, f"{width}-lifted-over-the-pile")
    finally:
        pg.close()
    assert not log, "\n".join(log)
