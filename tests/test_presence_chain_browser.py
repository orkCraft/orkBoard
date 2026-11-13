"""Spec 161 G (the lamp's chain, decisions §271; before it the door of spec 139 C.2 and C.4, decisions §246.4–§246.5): the person's presence, in a real browser against the hand's stub host that says `presence` in its snapshot.

On the desktop (1280 x 800) the discard column's head holds the backpack (left) and the lamp's chain (right) over *Discard*: *Here · until 23:00*, or pulled (`.is-pulled`) *Away · until 19:00* (the word muted), *· held* when the
press holds; `aria-pressed` is *here*; a pull sends one `presence.set` with the other state, and the snapshot that follows turns the chain and puts the pane `.is-out` (the felt flat, the signals as they were); with no `presence`
(an older host) there is no chain; under 760 px the small chain with no words (`aria-label` and `title` keep them), at the tabs' end. The phone's top row (390 x 844) holds the small chain, no words, and the small backpack beside it, on the felt of the open party (stage K)."""
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
    """The hand's host with the presence: `presence` in the snapshot (none as an older host), and `presence.set` turning it as the real host does (the press holds the other state)."""

    def __init__(self, presence=HERE, **kw):
        super().__init__(**kw)
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


def chain(pg):
    return pg.locator(".presence-chain")


def signals(pg):
    return pg.evaluate("() => [...document.querySelectorAll('.corner__kind')].map((e) => e.className + getComputedStyle(e).color)")


def paint(pg, token):
    return pg.evaluate("t => { const e = document.createElement('i'); e.style.color = `var(${t})`; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)








def test_a_pull_sends_presence_set_once_and_the_snapshot_turns_the_chain_and_puts_the_pane_out(gui):
    host = DoorHost(HERE)
    pg, errors = start(gui, "wide", host)
    try:
        chain(pg).wait_for(timeout=WAIT_MS)
        before = signals(pg)
        chain(pg).click()
        assert _calls(pg, host, "presence.set") == [{"here": False}]
        pg.wait_for_function("() => document.querySelector('.presence-chain__word').textContent === 'Away'", timeout=WAIT_MS)
        assert chain(pg).locator(".presence-chain__line").text_content() == "until 19:00 · held"
        pg.wait_for_function("() => document.querySelector('.table-pane').classList.contains('is-out')", timeout=WAIT_MS)
        assert "is-pulled" in chain(pg).locator(".ork-chain").get_attribute("class")
        assert signals(pg) == before, "the signal rings are as they were"
        chain(pg).click()
        pg.wait_for_function("() => document.querySelector('.presence-chain__word').textContent === 'Here'", timeout=WAIT_MS)
        assert _calls(pg, host, "presence.set", at_least=2)[1] == {"here": True}
        assert not pg.locator(".table-pane").evaluate("e => e.classList.contains('is-out')")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)














