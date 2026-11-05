"""The table's edge (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md D, decisions §254.3–§254.4), in a real browser: at 760 px and up the window has a third column, 212 px wide, at the right of the table and the hand,
holding top to bottom the ring (the imp at twelve, the lich at six, always drawn from Start, asleep while nothing is ready), the discard, the die (its right face Resume, waiting there while Stop all is in front) and the potions; the table gains
the width (no `padding-right` for an end); in a 1366 x 768 window everything fits with no scroll; under 760 px the edge is not drawn and the table's end and the hand's end are as they were.
Screenshots to $TABLE_EDGE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, RoadHost  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["TABLE_EDGE_SHOTS"]) if os.environ.get("TABLE_EDGE_SHOTS") else None
EDGE_W = 212
SIZES = {"1280x800": {"viewport": {"width": 1280, "height": 800}}, "1366x768": {"viewport": {"width": 1366, "height": 768}}}


def open_at(gui, host, size="1280x800"):
    """The page against the stub at a window size (or at the narrow desktop width, `narrow`), waiting for the hand and the table's tabs."""
    server, browser = gui
    pg = narrow.page(browser, "narrow") if size == "narrow" else browser.new_context(**SIZES[size]).new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(700)
    return pg, log


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def box(pg, selector):
    b = pg.locator(selector).first.bounding_box()
    assert b, f"{selector} is not drawn"
    return b


def test_the_edge_lies_at_the_frames_right_with_the_ring_the_discard_the_die_and_the_potions_in_that_order(gui):
    pg, log = open_at(gui, RoadHost())
    try:
        edge = box(pg, ".frame > .frame-edge")
        assert round(edge["x"] + edge["width"]) == 1280 and round(edge["width"]) == EDGE_W and round(edge["y"]) == 0 and round(edge["height"]) == 800, "the frame's third column, as tall as the window"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.frame')).gridTemplateColumns.split(' ').length") == 3, "the Orkmaster's column, the table and the edge"
        kids = pg.evaluate("() => [...document.querySelector('.frame-edge').children].map((e) => e.classList[0])")
        assert kids == ["portal-host", "edge-discard", "hand-die", "hand-mana"], "top to bottom: the ring, the discard, the die, the potions"
        ys = [box(pg, f".frame-edge > .{k}")["y"] for k in kids]
        assert ys == sorted(ys), "in that order down the edge"
        assert pg.locator(".table-end, .hand-end, .hand-mana-only").count() == 0, "the table's end and the hand's end are gone at the wide width"
        assert pg.locator(".frame-hand .hand-die, .frame-hand .hand-mana, .frame-table .portal-host, .frame-table .table-discard").count() == 0, "none of them lies in the table or the hand now"
        hand = box(pg, ".frame-hand")
        assert round(hand["x"] + hand["width"]) == round(edge["x"]), "the hand ends where the edge begins"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_table_gains_the_width_and_its_right_edge_is_the_edges_left(gui):
    pg, log = open_at(gui, RoadHost())
    try:
        edge, table = box(pg, ".frame-edge"), box(pg, ".frame-table")
        assert round(table["x"] + table["width"]) == round(edge["x"]), "the table's right edge is the edge's left"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.table-body')).paddingRight") == "0px", "no room kept for an end"
        pg.locator('.table-tab[data-tab="tech"]').click()                              # a party's tab: the map takes the width, there is still no end
        pg.locator('.table-tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.table-body')).paddingRight") == "0px" and pg.locator(".table-end").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_ring_is_drawn_from_start_asleep_with_nothing_ready_the_imp_at_twelve_and_the_lich_at_six(gui):
    pg, log = open_at(gui, RoadHost(bare=True))                                          # a gate with nothing to merge: nothing ready, nothing done
    try:
        host = pg.locator(".frame-edge > .portal-host")
        assert "is-ring" in host.get_attribute("class") and "is-asleep" in host.get_attribute("class") and "is-bare" not in host.get_attribute("class"), "asleep, faint and still, and drawn"
        assert pg.locator(".ork-portal-ring.is-bare, .ork-portal-ring.is-open").count() == 0 and pg.locator(".portal__label").count() == 0, "no *Main* while nothing is ready"
        assert pg.locator(".frame-edge > .edge-discard").count() == 0, "nothing done: no pile"
        ring, imp, lich = box(pg, ".ork-portal-ring"), box(pg, ".ork-portal-ring__after"), box(pg, ".ork-portal-ring__before")
        cx, cy = ring["x"] + ring["width"] / 2, ring["y"] + ring["height"] / 2
        assert imp["y"] + imp["height"] <= cy - ring["height"] / 2 + 8 and lich["y"] >= cy + ring["height"] / 2 - 12, "the imp above the ring's centre (at twelve), the lich below it (at six)"
        for corner in (imp, lich):
            assert abs(corner["x"] + 18 - cx) <= 6, "the head stands on the ring's vertical axis"
        for sel in (".ork-portal-ring__after > .ork-portal-ring__guard > img", ".ork-portal-ring__before > .ork-portal-ring__guard > img"):
            head = box(pg, sel)
            assert (round(head["width"]), round(head["height"])) == (36, 33), "each head 36 x 33"
        assert pg.locator(".ork-portal-ring__after .portal__corner-word").text_content() == "Live" and pg.locator(".ork-portal-ring__before .portal__corner-word").text_content() == "Release", "their words beside them"
        for side in ("after", "before"):
            assert "is-asleep" in pg.locator(f".ork-portal-ring__{side}").get_attribute("class"), "asleep grey, as today"
        word, head = box(pg, ".ork-portal-ring__after .portal__corner-word"), box(pg, ".ork-portal-ring__after > .ork-portal-ring__guard")
        assert word["x"] >= head["x"] + head["width"] - 1, "the word beside the head"
        shot(pg, "edge-nothing-ready")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_ready_for_main_wakes_the_ring_with_its_word_main_and_the_imp_and_the_lich_stay(gui):
    pg, log = open_at(gui, RoadHost())                                                    # two goals ready for main
    try:
        host = pg.locator(".frame-edge > .portal-host")
        assert "is-asleep" not in host.get_attribute("class") and "is-open" in pg.locator(".ork-portal-ring").get_attribute("class")
        assert pg.locator(".portal__label").text_content() == "Main"
        assert pg.locator(".ork-portal-ring__after, .ork-portal-ring__before").count() == 2
        assert pg.locator(".frame-edge > .edge-discard .hand-done").count() == 1, "the discard lies under the ring"
        shot(pg, "edge-ready-for-main")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_die_wears_the_right_face_resume_while_stop_all_is_in_front(gui):
    pg, log = open_at(gui, RoadHost())
    try:
        die = pg.locator(".frame-edge > .hand-die .ork-die")
        classes = die.get_attribute("class").split()
        assert "front-stop" in classes and "right-resume" in classes, "Stop all in front, Resume waiting on its right face"
        assert pg.locator(".frame-edge > .hand-die .ork-die__face.is-right").count() == 1
        assert pg.locator(".frame-edge > .hand-die .hand-die__play, .frame-edge > .hand-die .hand-die__stop").count() == 2, "its two presses are laid over its faces as before"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("hosts", ["ready", "nothing"])
def test_everything_in_the_edge_fits_a_1366_by_768_window_with_no_scroll(gui, hosts):
    pg, log = open_at(gui, RoadHost() if hosts == "ready" else RoadHost(bare=True), "1366x768")
    try:
        sizes = pg.evaluate("() => { const e = document.querySelector('.frame-edge'); return { sh: e.scrollHeight, ch: e.clientHeight, sw: e.scrollWidth, cw: e.clientWidth, page: document.documentElement.scrollHeight - innerHeight }; }")
        assert sizes["sh"] <= sizes["ch"] and sizes["sw"] <= sizes["cw"] and sizes["page"] <= 0, f"nothing scrolls: {sizes}"
        edge = box(pg, ".frame-edge")
        for k in ("portal-host", "hand-die", "hand-mana"):
            b = box(pg, f".frame-edge > .{k}")
            assert b["y"] >= edge["y"] - 1 and b["y"] + b["height"] <= edge["y"] + edge["height"] + 1 and b["x"] >= edge["x"] - 1 and b["x"] + b["width"] <= edge["x"] + edge["width"] + 1, f"{k} lies inside the edge"
        if hosts == "ready":
            pile = box(pg, ".frame-edge > .edge-discard")
            die = box(pg, ".frame-edge > .hand-die")
            assert pile["y"] + pile["height"] <= die["y"] + 1, "the discard lies over the die"
            assert round(box(pg, ".frame-edge .table-discard")["height"]) == 202 and round(box(pg, ".frame-edge .table-discard")["width"]) == 144, "the discard 144 x 202"
        shot(pg, f"edge-1366x768-{hosts}")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_shorter_window_cuts_the_discard_from_its_foot_and_the_die_and_the_potions_keep_their_place(gui):
    server, browser = gui
    pg = browser.new_context(viewport={"width": 1280, "height": 640}).new_page()
    pg.route_web_socket("**/ws*", RoadHost().on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".frame-edge .hand-die", timeout=WAIT_MS)
    pg.wait_for_timeout(700)
    try:
        edge, die, pots = box(pg, ".frame-edge"), box(pg, ".frame-edge > .hand-die"), box(pg, ".frame-edge > .hand-mana")
        assert die["y"] + die["height"] <= pots["y"] + 1 and pots["y"] + pots["height"] <= edge["y"] + edge["height"] + 1, "the die and the potions at the foot, whole"
        assert pg.evaluate("() => { const e = document.querySelector('.frame-edge'); return e.scrollHeight <= e.clientHeight; }"), "the edge itself does not scroll"
        assert pg.locator(".frame-edge .table-discard .hand-done").count() == 1, "the top card is there"
    finally:
        pg.close()


@pytest.mark.parametrize("shot_size", ["1280x800", "1366x768"])
def test_screenshots(gui, shot_size):
    if not SHOTS:
        pytest.skip("screenshots only when $TABLE_EDGE_SHOTS is set")
    for name, host in (("nothing-ready", RoadHost(bare=True)), ("ready-for-main", RoadHost())):
        pg, log = open_at(gui, host, shot_size)
        try:
            shot(pg, f"edge-{shot_size}-{name}")
        finally:
            pg.close()
        assert not log, "\n".join(log)


def test_under_760_px_the_edge_is_not_drawn_and_the_end_and_the_hands_end_are_as_they_were(gui):
    pg, log = open_at(gui, HandHost(), "narrow")
    try:
        assert pg.locator(".frame-edge").count() == 0 and pg.evaluate("() => document.querySelector('.frame').dataset.edge") is None
        assert pg.locator(".table-end").count() == 1 and pg.locator(".hand-end").count() == 1, "the discard's end on the table and the die and the potions in the hand's end, as today"
        assert pg.locator(".hand-end .hand-die").count() == 1 and pg.locator(".hand-end .hand-mana").count() == 1 and pg.locator(".table-end .table-discard").count() == 1
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
