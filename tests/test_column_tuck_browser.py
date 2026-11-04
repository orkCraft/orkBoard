"""Spec 130 E.1–E.2 (decisions §236), in a real browser against a stub host: the Orkmaster's column has a width of its own; a face-down card lies tucked under the window's left edge with its seal whole in what shows, slides out whole on
hover and on focus and goes back; the three piles share one right edge; a face-up card keeps its width; the hand's lanes stand under the table's at 1280 and 1920. The numbers are read from `--column-tuck`, so the owner's pick (45 or 30) is one line."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, open_column  # noqa: E402

pytestmark = pytest.mark.browser
DOWN = '.col-sec[data-pile="analysis"] .col-card--down'


def px(pg, name):
    return float(pg.evaluate(f"() => parseFloat(getComputedStyle(document.querySelector('.frame')).getPropertyValue('{name}'))"))


def rest(pg):
    """The pointer away, and no card keeps focus: every card lies at rest."""
    pg.mouse.move(700, 300)
    pg.evaluate("() => document.activeElement?.blur()")


def settled(pg, sel):
    pg.wait_for_function("(s) => { const e = document.querySelector(s); return e && e.getAnimations().every((a) => a.playState !== 'running'); }", arg=sel, timeout=WAIT_MS)
    return pg.locator(sel).first.bounding_box()


def test_the_column_has_a_width_of_its_own_and_the_table_gains_what_it_gives_up(gui):
    pg, host, log = open_column(gui)
    try:
        tuck = px(pg, "--column-tuck")
        assert tuck == 45, "built with §236.1's own number until the owner's pick"
        c, t = pg.locator(".frame-column").bounding_box(), pg.locator(".frame-table").bounding_box()
        assert abs(c["width"] - (max(112, 157 - tuck) + 16)) <= 1, c
        assert c["x"] == 0 and abs(t["x"] - c["width"]) <= 1, "the table begins where the column ends"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_face_down_card_is_cut_by_the_windows_edge_and_its_seal_is_whole_in_what_shows(gui):
    pg, host, log = open_column(gui)
    try:
        rest(pg)
        tuck = px(pg, "--column-tuck")
        box = settled(pg, DOWN)
        assert abs(box["x"] + tuck) <= 1 and abs(box["width"] - 157) <= 1 and abs(box["height"] - 112) <= 1, box
        shown = box["x"] + box["width"]
        assert abs(shown - (157 - tuck)) <= 1, "what shows of it"
        seal = pg.locator(f"{DOWN} .col-sigil").first.bounding_box()
        assert abs(seal["x"] + seal["width"] / 2 - shown / 2) <= 1.5, (seal, shown)
        assert seal["x"] >= 0 and seal["x"] + seal["width"] <= shown, "the ring is inside the window, under no edge"
        edges = pg.evaluate("() => { const s = document.querySelector('.col-scroll'); return [getComputedStyle(s).overflowX, s.getBoundingClientRect().left]; }")
        assert edges == ["hidden", 0], "the cut is the column's own box at the window's edge: no margin"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_face_down_card_slides_out_whole_on_hover_and_on_focus_and_goes_back(gui):
    pg, host, log = open_column(gui)
    try:
        rest(pg)
        tuck = px(pg, "--column-tuck")
        pg.hover(DOWN, position={"x": 60, "y": 50})
        out = settled(pg, DOWN)
        assert abs(out["x"]) <= 1, out
        seen = pg.evaluate("""(sel) => { const c = document.querySelector(sel).getBoundingClientRect(); const hit = document.elementFromPoint(c.right - 4, c.top + c.height / 2); return hit?.closest?.('.col-card--down') != null; }""", DOWN)
        assert seen, "its right end lies over the table, not clipped by the pile's box"
        rest(pg)
        assert abs(settled(pg, DOWN)["x"] + tuck) <= 1, "back when left"
        pg.keyboard.press("Tab")
        pg.locator(DOWN).first.focus()
        pg.evaluate("(s) => { const e = document.querySelector(s); e.blur(); }", DOWN)
        pg.locator('.col-head__switch').focus()
        pg.keyboard.press("Tab")
        assert pg.evaluate("(s) => document.activeElement === document.querySelector(s)", DOWN), "the front card takes the keyboard next"
        out = settled(pg, DOWN)
        assert abs(out["x"]) <= 1, out
        ring = pg.evaluate("(s) => getComputedStyle(document.querySelector(s)).boxShadow", DOWN)
        assert "inset" in ring, "the focus ring is drawn inside what shows"
        rest(pg)
        assert abs(settled(pg, DOWN)["x"] + tuck) <= 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_nothing_animates_and_the_card_is_whole_at_once(gui):
    pg, host, log = open_column(gui)
    try:
        pg.emulate_media(reduced_motion="reduce")
        rest(pg)
        assert pg.evaluate("(s) => getComputedStyle(document.querySelector(s)).transitionDuration", DOWN) == "0s"
        pg.hover(DOWN, position={"x": 60, "y": 50})
        box = pg.locator(DOWN).first.bounding_box()
        assert abs(box["x"]) <= 1, "at once"
        assert pg.evaluate("(s) => document.querySelector(s).getAnimations().length", DOWN) == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_three_piles_share_one_right_edge_and_a_face_up_card_keeps_its_width(gui):
    pg, host, log = open_column(gui)
    try:
        rest(pg)
        ends = {}
        for pile, sel in (("analysis", ".col-card--down"), ("review", ".col-card--up"), ("work", ".col-card--up")):
            box = settled(pg, f'.col-sec[data-pile="{pile}"] {sel}')
            ends[pile] = box["x"] + box["width"]
            if sel.endswith("up"):
                assert abs(box["width"] - 112) <= 1, box
        assert max(ends.values()) - min(ends.values()) <= 1, ends
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", [1280, 1920])
def test_the_hands_lanes_stand_under_the_tables_lanes(gui, width):
    pg, host, log = open_column(gui, host=ColumnHost())
    try:
        pg.set_viewport_size({"width": width, "height": 900})
        pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
        for slug in pg.eval_on_selector_all(".table-board .table-lane[data-party]", "els => els.map((e) => e.dataset.party)"):
            lane = pg.locator(f'.table-lane[data-party="{slug}"]').bounding_box()
            hand = pg.locator(f'.hand-lane[data-lane="{slug}"]')
            if hand.count():
                got = hand.bounding_box()
                assert abs(got["x"] - lane["x"]) <= 2 and abs(got["width"] - lane["width"]) <= 2, (slug, got, lane)
        plus = pg.locator(".hand .hand-plus").evaluate("e => [e.offsetWidth, e.offsetHeight]")
        assert plus == [144, 202], ("the + card keeps its 5 : 7", plus)
        assert pg.locator(".hand .hand-plus").bounding_box()["x"] >= -1, "its turned corners stay in the window"
        first = pg.locator('.hand-lane[data-lane="0"]').bounding_box()
        col = pg.locator(".frame-column").bounding_box()
        assert first["x"] + first["width"] <= col["width"] + 17, "the first lane lies under the column"
    finally:
        pg.close()
    assert not log, "\n".join(log)
