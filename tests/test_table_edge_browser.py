"""The Release column (docs/specs/156-one-pick-and-the-release-column.md D, decisions §261.7–§261.10; before it the table's edge, spec 150 D), in a real browser: at 760 px and up there is no edge column (no `.frame-edge`); Live's and Release's are
tabs at the row's end (Live, then Release last, their heads asleep or awake by the corners' old rules), and the discard is Release's lane under Release's tab, beside the pane, flush with the window's right edge, on every tab, its label *Discard* or
*<party>'s discard*; the die and the potions stand at the hand's right end, as they do under 760 px; a project without a Release party has a headless *Discard* lane; in a 1366 x 768 window the ready card and the first goal not yet seen are in view;
under 760 px the narrow page is as it was (the table's end, the hand's end). Screenshots to $TABLE_EDGE_SHOTS when it is set."""
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
SIZES = {"1280x800": {"viewport": {"width": 1280, "height": 800}}, "1366x768": {"viewport": {"width": 1366, "height": 768}}}


class LaneHost(RoadHost):
    """RoadHost with one goal ready for main (Lobby music loop, Tech's) and another done and not yet seen (Room codes, Design's)."""

    def __init__(self, **more):
        super().__init__(**more)
        if self.gate_doc.get("ideas"):
            self.gate_doc["ideas"] = [g for g in self.gate_doc["ideas"] if g["slug"] == "music"]


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


def test_there_is_no_edge_the_table_spans_to_the_windows_right_and_the_lane_is_its_last_column(gui):
    pg, log = open_at(gui, LaneHost())
    try:
        assert pg.locator(".frame-edge").count() == 0 and pg.evaluate("() => document.querySelector('.frame').dataset.edge") is None, "no edge"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.frame')).gridTemplateColumns.split(' ').length") == 2, "the Orkmaster's column and the table"
        table, lane, pane = box(pg, ".frame-table"), box(pg, ".table-under > .release-lane"), box(pg, ".table-under > .table-pane")
        assert round(table["x"] + table["width"]) == 1280 and round(lane["x"] + lane["width"]) == 1280, "the table and its lane reach the window's right edge"
        assert round(pane["x"] + pane["width"]) == round(lane["x"]), "the pane ends where the lane begins"
        assert pg.locator(".table-end").count() == 0, "no end at the foot of the lanes"
        assert pg.locator(".frame-hand .hand-end .hand-die").count() == 1 and pg.locator(".frame-hand .hand-end .hand-mana").count() == 1, "the die and the potions at the hand's right end"
        shot(pg, "column-1280x800")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_live_and_release_are_tabs_at_the_rows_end_release_last_and_its_lane_stands_under_its_tab(gui):
    pg, log = open_at(gui, LaneHost())
    try:
        tabs = pg.evaluate("() => [...document.querySelectorAll('.table-tab[data-tab]')].map((e) => e.dataset.tab)")
        assert tabs == ["tech", "design", "product", "live", "release"], "Live before Release, Release last"
        live, release, lane = box(pg, '[data-cell="live"]'), box(pg, '[data-cell="release"]'), box(pg, ".release-lane")
        assert release["x"] > live["x"] and round(release["x"]) == round(lane["x"]), "Release's tab stands over the lane"
        assert round(release["x"] + release["width"]) <= 1280 - 7, "the gutter at the right"
        assert pg.locator(".ork-portal-ring__before, .ork-portal-ring__after, .portal__past, .pyramid").count() == 0, "their heads have left the ring; no past line, no pyramid"
        assert round(box(pg, '.table-board [data-live]')["x"]) == round(live["x"]), "Live's lane under Live's tab"
        pg.locator('.table-tab[data-tab="release"]').click()
        pg.locator('.table-tab[data-tab="release"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_road_tabs_heads_wake_by_the_old_corners_rules(gui):
    pg, log = open_at(gui, LaneHost(bare=True))                                          # nothing ready, nothing at work
    try:
        for slug in ("release", "live"):
            assert "is-asleep" in pg.locator(f'.table-tab[data-tab="{slug}"]').get_attribute("class"), f"{slug} asleep while it has nothing to do"
    finally:
        pg.close()
    pg, log = open_at(gui, LaneHost())                                                    # a goal is ready for main: Release wakes, Live stays asleep
    try:
        assert "is-asleep" not in pg.locator('.table-tab[data-tab="release"]').get_attribute("class")
        assert "is-asleep" in pg.locator('.table-tab[data-tab="live"]').get_attribute("class")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("tab,label", [("orkmaster", "Discard"), ("tech", "Tech's discard"), ("design", "Design's discard"), ("live", "Live's discard"), ("release", "Release's discard")])
def test_the_discard_lane_is_on_every_tab_through_its_eyes(gui, tab, label):
    pg, log = open_at(gui, LaneHost())
    try:
        if tab != "orkmaster":
            pg.locator(f'.table-tab[data-tab="{tab}"]').click()
            pg.locator(f'.table-tab[data-tab="{tab}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".release-lane__label").text_content() == label and pg.locator(".release-lane").get_attribute("aria-label") == label
        slugs = pg.evaluate("() => [...document.querySelectorAll('.release-lane [data-slug], .release-lane [data-portal-card]')].map((e) => e.dataset.slug || e.dataset.portalCard)")
        want = {"orkmaster": ["music", "codes"], "tech": ["music"], "design": ["codes"], "live": ["music", "codes"], "release": ["music", "codes"]}[tab]
        assert slugs == want, f"on {tab}'s tab: {slugs}"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_project_without_a_release_party_has_a_headless_discard_lane(gui):
    pg, log = open_at(gui, HandHost())                                                    # no party of the release craft
    try:
        lane = pg.locator(".release-lane")
        assert "is-headless" in lane.get_attribute("class") and pg.locator(".release-lane__label").text_content() == "Discard"
        assert pg.locator('.table-tab[data-tab="release"]').count() == 1
        pg.locator('.table-tab[data-tab="tech"]').click()
        pg.locator('.table-tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".release-lane__label").text_content() == "Discard", "the word stays on every tab"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_in_a_1366_by_768_window_the_ready_card_and_the_first_not_seen_are_in_view_and_nothing_scrolls_the_page(gui):
    pg, log = open_at(gui, LaneHost(), "1366x768")
    try:
        scroll = box(pg, ".release-lane__scroll")
        ready, seen = box(pg, '[data-portal-card="music"]'), box(pg, '.release-lane__done [data-slug="codes"]')
        for b in (ready, seen):
            assert b["y"] >= scroll["y"] - 1 and b["y"] + b["height"] <= scroll["y"] + scroll["height"] + 1, f"in view: {b} in {scroll}"
        assert ready["y"] < seen["y"], "the ready card on top"
        assert round(ready["width"]) == 144 and round(ready["height"]) == 202, "whole cards at the hand's size"
        assert pg.evaluate("() => document.documentElement.scrollHeight - innerHeight") <= 0, "the page itself does not scroll"
        shot(pg, "lane-1366x768")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_760_px_there_is_no_lane_and_the_end_and_the_hands_end_are_as_they_were(gui):
    pg, log = open_at(gui, HandHost(), "narrow")
    try:
        assert pg.locator(".release-lane, .frame-edge").count() == 0
        assert pg.locator(".table-end").count() == 1 and pg.locator(".hand-end").count() == 1, "the discard's end on the table and the die and the potions in the hand's end, as today"
        assert pg.locator(".hand-end .hand-die").count() == 1 and pg.locator(".hand-end .hand-mana").count() == 1 and pg.locator(".table-end .table-discard").count() == 1
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
