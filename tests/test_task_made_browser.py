"""Spec 142 part D (docs/specs/142-a-cards-window-where-it-has-something-to-show.md, decisions §249.3), in a real browser against a stub host whose tasks carry `craft_made` as the snapshot serves it: a card's window
for a task being checked draws what it made by its craft (92 px high, the same as the other windows): Tech's three files with six bars each, Art's image at a whole-number scale, pixelated, Design's thumbnail with its
before faint, Release's ticks, Product's quoted hypothesis and its state chip; and a task with none keeps its type's sign. The pure functions of made.js are checked in the page's own module."""
from __future__ import annotations

import base64
import struct
import zlib

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, node, open_hand, task  # noqa: E402
from tests.test_task_steps_browser import card, css, token  # noqa: E402

pytestmark = pytest.mark.browser


def png_uri(w, h):
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    raw = b"".join(b"\x00" + b"\x86\xc0\x62\xff" * w for _ in range(h))
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    return "data:image/png;base64," + base64.b64encode(data).decode()


MADE = {
    "tech": {"kind": "diff", "files": [{"path": "src/join_with_a_very_long_name_indeed.py", "added": 40, "removed": 10}, {"path": "tests/test_join.py", "added": 12, "removed": 0}, {"path": "README.md", "added": 0, "removed": 2}]},
    "art": {"kind": "asset", "url": png_uri(16, 16), "w": 16, "h": 16, "name": "hero.png"},
    "design": {"kind": "screen", "before": png_uri(20, 36), "after": png_uri(20, 36)},
    "rel": {"kind": "checks", "items": [{"name": "The merge", "state": "passed"}, {"name": "Tests", "state": "failed"}, {"name": "Notes", "state": "waiting"}]},
    "prod": {"kind": "hypothesis", "text": "Hosts who can skip a round stay longer in the room", "state": "open"},
}


class MadeHost(HandHost):
    """One goal for each craft's kind, its front task being checked and carrying `craft_made`; and a Tech one with none."""

    def __init__(self):
        super().__init__(bare=True)
        elems = ["meadow", "ice", "dust", "void", "lava", "meadow"]
        self.nodes = [node(slug, party, slug, "table", state="working", stage="implementation", element=elems[i], tasks=[task("m1", f"Made {slug}", "testing", band="check", **({"craft_made": MADE[slug]} if slug in MADE else {}))])
                      for i, (slug, party) in enumerate([("tech", "tech"), ("art", "design"), ("design", "design"), ("rel", "tech"), ("prod", "design"), ("bare", "tech")])]


def open_made(gui):
    pg, host, log = open_hand(gui, host=MadeHost(), width="wide")
    pg.wait_for_selector(".table-card", timeout=WAIT_MS)
    return pg, host, log


def win(pg, goal):
    return card(pg, goal, "m1").locator(".table-card__win")


def test_a_tech_task_checked_draws_its_three_files_with_six_bars_each(gui):
    pg, host, log = open_made(gui)
    try:
        w = win(pg, "tech")
        assert w.get_attribute("data-window") == "made" and 80 <= round(w.bounding_box()["height"]) <= 92      # what the 5 : 7 card leaves between its title and its foot (spec 147 A.2)
        rows = w.locator(".made-diff__row")
        assert rows.count() == 3 and all(rows.nth(i).locator(".made-diff__bars > i").count() == 6 for i in range(3))
        first = w.locator(".made-diff__file").first
        assert first.inner_text() == "join_with_a_very_long_name_indeed.py" and css(first, "textOverflow") == "ellipsis" and first.evaluate("e => e.scrollWidth > e.clientWidth"), "the name is cut with an ellipsis"
        top = rows.nth(0).locator("i")
        assert [top.nth(k).get_attribute("class") for k in range(6)] == ["is-a", "is-a", "is-a", "is-a", "is-a", "is-x"], "the largest file fills its row"
        assert rows.nth(1).locator("i.is-a").count() >= 1 and rows.nth(1).locator("i.is-o").count() >= 1, "a smaller one fills part of it"
        assert css(rows.nth(0).locator("i.is-a").first, "backgroundColor") == token(pg, "--ork-success")
        assert css(rows.nth(0).locator("i.is-x").first, "backgroundColor") == token(pg, "--ork-danger")
        assert css(rows.nth(2).locator("i.is-o").first, "backgroundColor") == token(pg, "--ork-frame")
        box = rows.nth(0).locator("i").first.bounding_box()
        assert (round(box["width"]), round(box["height"])) == (4, 6)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_art_task_draws_its_image_at_a_whole_number_scale_pixelated_on_a_checker(gui):
    pg, host, log = open_made(gui)
    try:
        w = win(pg, "art")
        img = w.locator(".made-asset__img")
        img.wait_for(timeout=WAIT_MS)
        assert css(img, "imageRendering") in ("pixelated", "crisp-edges") and img.get_attribute("data-scale") == "4"
        box = img.bounding_box()
        assert (round(box["width"]), round(box["height"])) == (64, 64), "16 px at a scale of 4"
        assert "hero.png" in w.inner_text() and "16 × 16" in w.inner_text()
        assert "repeating-conic-gradient" in css(w.locator(".made-asset"), "backgroundImage"), "on a checker"
        assert w.bounding_box()["height"] >= box["height"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_design_task_draws_its_screen_before_faint_and_after(gui):
    pg, host, log = open_made(gui)
    try:
        w = win(pg, "design")
        before, after = w.locator(".made-screen__img.is-before"), w.locator(".made-screen__img.is-after")
        assert before.count() == 1 and after.count() == 1 and w.locator(".made-screen__arrow").count() == 1
        assert float(css(before, "opacity")) < 0.5 and float(css(after, "opacity")) == 1
        assert after.bounding_box()["height"] <= 92
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_release_task_draws_its_checks_as_ticks(gui):
    pg, host, log = open_made(gui)
    try:
        w = win(pg, "rel")
        rows = w.locator(".made-checks__row")
        assert [r.inner_text().strip() for r in (rows.nth(i) for i in range(3))] == ["The merge", "Tests", "Notes"]
        assert rows.nth(0).locator(".ork-sign.check").count() == 1 and css(rows.nth(0).locator(".ork-sign.check"), "color") == token(pg, "--ork-success")
        assert rows.nth(1).locator(".ork-sign.cross").count() == 1 and rows.nth(2).locator(".made-checks__dot").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_product_task_draws_its_hypothesis_quoted_and_its_state_as_a_chip(gui):
    pg, host, log = open_made(gui)
    try:
        w = win(pg, "prod")
        assert w.locator("q.made-hyp__text").inner_text() == "Hosts who can skip a round stay longer in the room"
        chip = w.locator(".ork-chip")
        assert chip.inner_text().strip() == "Open" and "“" in css(w.locator("q"), "quotes")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_with_nothing_made_keeps_the_window_it_had_and_the_pure_parts_hold(gui):
    pg, host, log = open_made(gui)
    try:
        assert win(pg, "bare").get_attribute("data-window") != "made" and win(pg, "bare").locator(".made-diff").count() == 0
        got = pg.evaluate("""() => import('/static/js/table/made.js').then((m) => ({
          bars: m.barsOf({ added: 3, removed: 1 }, 4).join(""), tiny: m.barsOf({ added: 1, removed: 0 }, 100).join(""), none: m.barsOf({ added: 0, removed: 0 }, 5).join(""),
          scale: [m.scaleOf(16, 16), m.scaleOf(100, 10), m.scaleOf(0, 5)], odd: m.madeOf({ state: "merged", craft_made: { kind: "diff", files: [] } }), run: m.madeOf({ state: "merged", craft_made: { kind: "event" } }),
          running: m.madeOf({ state: "running", craft_made: { kind: "hypothesis", text: "x", state: "open" } }) }))""")
        assert got["bars"] == "aaaaax", "the file with most lines fills the row: 5 added, 1 taken"
        assert got["tiny"] == "a" + "ooooo" and got["none"] == "oooooo"
        assert got["scale"] == [4, 0, 0] and got["odd"] is None and got["run"] is None and got["running"] is None
    finally:
        pg.close()
    assert not log, "\n".join(log)
