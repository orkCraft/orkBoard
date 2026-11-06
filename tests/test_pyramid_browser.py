"""Spec 150 E2.3, the pyramid in the portal (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.3, decisions §254.7; mockup docs/mockups/table-edge/ section 5, *Or out of the portal itself*, the pyramid), in a real browser at
1280 x 800 against the road's stub host with `ideas.chronicle_last` answered as gui/ideas_chronicle.py does: the open tab's last three decisions stand in the ring's eye as three small cards, the newest in front and whole, each older one smaller
(0.74, 0.54), darker (0.62, 0.42) and higher; a decision newer than the party's last look (localStorage `orkboard.past.seen.<party>`) is marked with its edge in the ink until the past is opened; never looked at, nothing is marked; a step hovered rises
whole under the ring with its title, its why and its version, and pressed opens the past with that card lit; while a goal is ready for main the pyramid is not drawn. Screenshots to $PYRAMID_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, call  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PYRAMID_SHOTS"]) if os.environ.get("PYRAMID_SHOTS") else None
LAST = {"design": [{"number": 231, "title": "Camp is tested in marketing", "element": "lava", "kind": "decision", "parties": ["design", "product"], "version": "", "at": "2026-11-04T10:00:00"},
                   {"number": 226, "title": "The dark look, pushed", "element": "void", "kind": "decision", "parties": ["design"], "version": "v0.3", "at": "2026-10-27T10:00:00"},
                   {"number": 209, "title": "The lobby holds eight", "element": "meadow", "kind": "decision", "parties": ["design", "product"], "version": "v0.3", "at": "2026-10-20T10:00:00"}],
        "": [{"number": 232, "title": "The server owns every clock", "element": "dust", "kind": "decision", "parties": ["tech"], "version": "", "at": "2026-11-05T10:00:00"}]}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class PyramidHost(RoadHost):
    def __init__(self, ready=False):
        super().__init__(bare=not ready)

    def handle(self, name, a):
        if name == "ideas.chronicle_last":
            self.log.append((name, a))
            return {"decisions": LAST.get(a.get("party", ""), [])}
        if name == "ideas.chronicle_decision":
            self.log.append((name, a))
            d = next(x for x in LAST["design"] if x["number"] == a["number"])
            return {"number": d["number"], "title": d["title"], "day": "2026-10-27", "changes": [], "changed_by": [], "goal": "", "entry": f"## {d['number']}. {d['title']}\n\nWhy: brighter ink, nothing under 14 px."}
        if name == "ideas.chronicle":
            self.log.append((name, a))
            return {"kind": "tag", "earlier": None, "chapters": [], "unreleased": {"goals": [], "decisions": []}}
        return super().handle(name, a)


def open_ring(gui, host=None, seen=None, tab="design"):
    """The window against the stub; `seen`: what this browser kept of Design's last look (None: never looked)."""
    server, browser = gui
    host = host or PyramidHost()
    pg = narrow.page(browser, "wide")
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text}"))
    if seen is not None:
        pg.add_init_script(f"try {{ localStorage.setItem('orkboard.past.seen.design', '{seen}'); }} catch (e) {{}}")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".ork-portal-ring__before").wait_for(timeout=WAIT_MS)
    call(pg, "frame/state.js", "openTab", tab)
    return pg, host, log


def steps(pg):
    return pg.locator(".pyramid .pyramid__step")


def stored(pg):
    return pg.evaluate("() => localStorage.getItem('orkboard.past.seen.design')")


def test_three_steps_the_newest_in_front_and_whole_each_older_smaller_darker_and_higher(gui):
    pg, host, log = open_ring(gui, seen=231)
    try:
        pg.wait_for_function("() => document.querySelectorAll('.pyramid .pyramid__step').length === 3", timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        by_age = sorted(steps(pg).all(), key=lambda s: int(s.get_attribute("data-age")))
        assert [s.get_attribute("data-decision") for s in by_age] == ["231", "226", "209"], "the newest in front"
        boxes = [s.bounding_box() for s in by_age]
        assert [round(b["width"] / 56, 2) for b in boxes] == [1.0, 0.74, 0.54] and round(boxes[0]["height"]) == 78
        assert [s.evaluate("e => getComputedStyle(e).filter") for s in by_age] == ["brightness(1)", "brightness(0.62)", "brightness(0.42)"]
        assert boxes[0]["y"] > boxes[1]["y"] > boxes[2]["y"], "each older one higher, into the swirl"
        assert [int(s.evaluate("e => getComputedStyle(e).zIndex")) for s in by_age] == [4, 3, 2], "the front one over the others"
        ring = pg.locator(".ork-portal-ring").bounding_box()
        mid = ring["x"] + ring["width"] / 2
        assert all(abs(b["x"] + b["width"] / 2 - mid) < 2 for b in boxes), "in the portal's eye"
        assert pg.locator(".pyramid__step.is-new").count() == 0, "nothing newer than the last look: it lies still"
        assert [a for n, a in host.log if n == "ideas.chronicle_last"][-1] == {"party": "design", "n": 3}
        shot(pg, "pyramid-at-rest")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_new_one_is_marked_until_the_past_is_opened(gui):
    pg, host, log = open_ring(gui, seen=226)
    try:
        new = pg.locator('.pyramid__step.is-new[data-decision="231"]')
        new.wait_for(timeout=WAIT_MS)
        assert new.get_attribute("data-age") == "0" and pg.locator(".pyramid__step.is-new").count() == 1
        pg.wait_for_timeout(600)
        shot(pg, "pyramid-a-new-one")
        pg.locator(".ork-portal-ring__before").click()                                     # the past opened: the newest is seen
        pg.locator('.table-over[data-kind="chronicle"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.pyramid__step.is-new')", timeout=WAIT_MS)
        assert stored(pg) == "231"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_never_looked_at_nothing_is_marked_and_the_newest_is_taken_as_seen(gui):
    pg, host, log = open_ring(gui)
    try:
        pg.wait_for_function("() => document.querySelectorAll('.pyramid .pyramid__step').length === 3", timeout=WAIT_MS)
        assert pg.locator(".pyramid__step.is-new").count() == 0 and stored(pg) == "231"
        call(pg, "frame/state.js", "openTab", "orkmaster")                                  # the Orkmaster's tab: the whole project's last decisions
        pg.wait_for_function("() => document.querySelector('.pyramid')?.dataset.party === 'orkmaster' && document.querySelectorAll('.pyramid__step').length === 1", timeout=WAIT_MS)
        assert [a for n, a in host.log if n == "ideas.chronicle_last"][-1] == {"n": 3}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_step_hovered_rises_whole_under_the_ring_and_pressed_opens_the_past_with_it_lit(gui):
    pg, host, log = open_ring(gui, seen=231)
    try:
        pg.wait_for_function("() => document.querySelectorAll('.pyramid .pyramid__step').length === 3", timeout=WAIT_MS)
        step = pg.locator('.pyramid__step[data-decision="226"]')
        step.focus()
        rise = pg.locator('.pyramid__rise[data-rise="226"]')
        rise.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.pyramid__rise .pyramid__why')", timeout=WAIT_MS)
        b, ring = rise.bounding_box(), pg.locator(".ork-portal-ring").bounding_box()
        assert round(b["width"]) == 144 and round(b["height"]) == 202 and b["y"] > ring["y"] + ring["height"], "whole, under the ring"
        assert "The dark look, pushed" in rise.inner_text() and "brighter ink, nothing under 14 px." in rise.inner_text() and rise.locator('[data-much="version"]').inner_text() == "v0.3"
        shot(pg, "pyramid-hovered")
        step.click()
        pg.locator('.table-over[data-kind="chronicle"] .chr[data-lit="226"]').wait_for(timeout=WAIT_MS)
        assert [a for n, a in host.log if n == "ideas.chronicle"][-1] == {"party": "design"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_while_a_goal_is_ready_for_main_the_pyramid_is_not_drawn(gui):
    pg, host, log = open_ring(gui, host=PyramidHost(ready=True), seen=231)
    try:
        pg.locator(".portal-host .ork-portal").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(800)
        assert pg.locator(".pyramid").count() == 0, "the ring is the gate's"
        assert pg.locator(".portal__past").inner_text() == "Design's past ›", "the lich still opens the past"
        shot(pg, "pyramid-ready-for-main")
    finally:
        pg.close()
    assert not log, "\n".join(log)
