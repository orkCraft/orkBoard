"""Spec 139 C.2 and C.4 (docs/specs/139-the-die-the-door-and-the-bug.md, decisions §246.4–§246.5): the door as the person, in a real browser against the hand's stub host that says `presence` in its snapshot.

Open with *Here* and its line (*until 23:00*), shut with *Away* (*until 19:00*, the word muted), *· held* when the press holds; `aria-pressed` is *here* and the title says what a press does; a press sends
`presence.set` with the other state and the snapshot that follows turns the door; with no `presence` (an older host) there is no door; under 760 px the small door with its word alone; the phone's top row has the small door."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

HERE = {"here": True, "until": "2026-11-04T23:00", "held": False}
AWAY = {"here": False, "until": "2026-11-05T19:00", "held": False}


class DoorHost(HandHost):
    """The hand's host with the door: `presence` in the snapshot (none as an older host), and `presence.set` turning it as the real host does (the press holds the other state)."""

    def __init__(self, presence=HERE):
        super().__init__()
        self.presence = copy.deepcopy(presence)

    def snapshot(self):
        doc = super().snapshot()
        if self.presence is not None:
            doc["state"]["presence"] = copy.deepcopy(self.presence)
        return doc

    def handle(self, name, a):
        if name == "presence.set":
            self.log.append((name, a))
            self.presence = {"here": a["here"], "until": "2026-11-04T19:00", "held": True}
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return self.presence
        return super().handle(name, a)


def start(gui, width, host):
    server, browser = gui
    pg = narrow.page(browser, width)
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".up-top" if width == "phone" else ".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    return pg, errors


def door(pg):
    return pg.locator(".presence-door")


def paint(pg, token):
    return pg.evaluate("t => { const e = document.createElement('i'); e.style.color = `var(${t})`; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def test_open_door_says_here_and_its_line(gui):
    pg, errors = start(gui, "wide", DoorHost(HERE))
    try:
        d = door(pg)
        d.wait_for(timeout=WAIT_MS)
        cls = d.locator(".ork-door").get_attribute("class")
        assert d.get_attribute("aria-pressed") == "true" and "is-open" in cls
        assert d.locator(".presence-door__word").text_content() == "Here" and d.locator(".presence-door__line").text_content() == "until 23:00"
        assert d.get_attribute("title") == "You are here: questions come as they arise. Press to be away. (until 23:00)"
        assert d.locator(".ork-door").evaluate("e => e.offsetWidth") == 28, "the door at its own size, 28 wide"
        assert d.locator(".presence-door__word").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink")
        assert d.bounding_box()["x"] > pg.viewport_size["width"] / 2, "at the top row's end"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_shut_door_says_away_muted(gui):
    pg, errors = start(gui, "wide", DoorHost(AWAY))
    try:
        d = door(pg)
        d.wait_for(timeout=WAIT_MS)
        assert d.get_attribute("aria-pressed") == "false" and "is-open" not in d.locator(".ork-door").get_attribute("class")
        assert d.locator(".presence-door__word").text_content() == "Away" and d.locator(".presence-door__line").text_content() == "until 19:00"
        assert d.locator(".presence-door__word").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink-muted")
        assert d.get_attribute("title").startswith("You are away: steps that ask wait for your hours. Press to be here.")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_press_sends_presence_set_with_the_other_state_and_the_snapshot_turns_the_door(gui):
    host = DoorHost(HERE)
    pg, errors = start(gui, "wide", host)
    try:
        door(pg).wait_for(timeout=WAIT_MS)
        door(pg).click()
        assert _calls(pg, host, "presence.set") == [{"here": False}]
        pg.wait_for_function("() => document.querySelector('.presence-door__word').textContent === 'Away'", timeout=WAIT_MS)
        assert door(pg).locator(".presence-door__line").text_content() == "until 19:00 · held"
        door(pg).click()
        pg.wait_for_function("() => document.querySelector('.presence-door__word').textContent === 'Here'", timeout=WAIT_MS)
        assert _calls(pg, host, "presence.set", at_least=2)[1] == {"here": True}
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_host_that_does_not_say_presence_has_no_door(gui):
    pg, errors = start(gui, "wide", DoorHost(None))
    try:
        pg.wait_for_timeout(500)
        assert door(pg).count() == 0
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_under_760_the_small_door_and_its_word_alone(gui):
    pg, errors = start(gui, "narrow", DoorHost(HERE))
    try:
        d = door(pg)
        d.wait_for(timeout=WAIT_MS)
        assert d.locator(".ork-door.small").evaluate("e => e.offsetWidth") == 14 and d.locator(".presence-door__word").text_content() == "Here"
        assert d.locator(".presence-door__line").count() == 0
        assert "until 23:00" in d.get_attribute("title")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_phones_top_row_has_the_small_door(gui):
    host = DoorHost(AWAY)
    pg, errors = start(gui, "phone", host)
    try:
        d = pg.locator(".up-top .presence-door")
        d.wait_for(timeout=WAIT_MS)
        assert d.locator(".ork-door.small").count() == 1 and d.locator(".presence-door__word").text_content() == "Away"
        d.click()
        assert _calls(pg, host, "presence.set") == [{"here": True}]
        pg.wait_for_function("() => document.querySelector('.up-top .presence-door__word').textContent === 'Here'", timeout=WAIT_MS)
        box = d.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= 390
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)
