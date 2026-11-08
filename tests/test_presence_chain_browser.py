"""Spec 160 G (the lamp's chain, decisions §271; before it the door of spec 139 C.2 and C.4, decisions §246.4–§246.5): the person's presence, in a real browser against the hand's stub host that says `presence` in its snapshot.

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


def chain(pg):
    return pg.locator(".presence-chain")


def signals(pg):
    return pg.evaluate("() => [...document.querySelectorAll('.corner__kind')].map((e) => e.className + getComputedStyle(e).color)")


def paint(pg, token):
    return pg.evaluate("t => { const e = document.createElement('i'); e.style.color = `var(${t})`; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def test_the_head_holds_the_backpack_and_the_chain_over_discard_on_both_tabs(gui):
    pg, errors = start(gui, "wide", DoorHost(HERE))
    try:
        for tab in ("", "tech"):
            if tab:
                pg.locator(f'.table-tab[data-tab="{tab}"]').click()
            head = pg.locator('.release-lane__head[data-room-things="discard"]')
            head.locator(".presence-chain").wait_for(timeout=WAIT_MS)
            a, b, label = head.locator("[data-backpack]").bounding_box(), head.locator(".presence-chain").bounding_box(), pg.locator(".release-lane__label").bounding_box()
            assert a["x"] < b["x"] and a["x"] > pg.viewport_size["width"] * 0.8, "the backpack at the left, the chain at the right of the column's head"
            assert max(a["y"] + a["height"], b["y"] + b["height"]) <= label["y"] + 8
            assert pg.locator(".table-tabs__end .presence-chain, .table-tabs__end .stall-pack").count() == 0
            assert "Discard" in pg.locator(".release-lane__label").text_content()
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_lit_chain_says_here_and_its_line(gui):
    pg, errors = start(gui, "wide", DoorHost(HERE))
    try:
        d = chain(pg)
        d.wait_for(timeout=WAIT_MS)
        assert d.get_attribute("aria-pressed") == "true" and "is-pulled" not in d.locator(".ork-chain").get_attribute("class")
        assert d.locator(".presence-chain__word").text_content() == "Here" and d.locator(".presence-chain__line").text_content() == "until 23:00"
        assert d.get_attribute("title") == "You are here: questions come as they arise. Press to be away. (until 23:00)"
        assert d.locator(".ork-chain").evaluate("e => e.offsetWidth") == 12, "the chain at its own size, 12 wide"
        assert d.locator(".presence-chain__word").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink")
        assert not pg.locator(".table-pane").evaluate("e => e.classList.contains('is-out')")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_pulled_chain_says_away_muted_and_the_pane_is_out(gui):
    pg, errors = start(gui, "wide", DoorHost(AWAY))
    try:
        d = chain(pg)
        d.wait_for(timeout=WAIT_MS)
        assert d.get_attribute("aria-pressed") == "false" and "is-pulled" in d.locator(".ork-chain").get_attribute("class")
        assert d.locator(".presence-chain__word").text_content() == "Away" and d.locator(".presence-chain__line").text_content() == "until 19:00"
        assert d.locator(".presence-chain__word").evaluate("e => getComputedStyle(e).color") == paint(pg, "--ork-ink-muted")
        assert d.get_attribute("title").startswith("You are away: steps that ask wait for your hours. Press to be here.")
        assert pg.locator(".table-pane").evaluate("e => e.classList.contains('is-out')")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_pull_sends_presence_set_once_and_the_snapshot_turns_the_chain_and_puts_the_pane_out(gui):
    host = DoorHost(HERE)
    pg, errors = start(gui, "wide", host)
    try:
        chain(pg).wait_for(timeout=WAIT_MS)
        before = signals(pg)
        felt = pg.locator(".table-pane").evaluate("e => getComputedStyle(e).backgroundColor")
        chain(pg).click()
        assert _calls(pg, host, "presence.set") == [{"here": False}]
        pg.wait_for_function("() => document.querySelector('.presence-chain__word').textContent === 'Away'", timeout=WAIT_MS)
        assert chain(pg).locator(".presence-chain__line").text_content() == "until 19:00 · held"
        pg.wait_for_function("() => document.querySelector('.table-pane').classList.contains('is-out')", timeout=WAIT_MS)
        assert "is-pulled" in chain(pg).locator(".ork-chain").get_attribute("class")
        assert signals(pg) == before, "the signal rings are as they were"
        assert pg.locator(".table-pane").evaluate("e => getComputedStyle(e).backgroundColor") != felt, "the felt is flat and darker"
        chain(pg).click()
        pg.wait_for_function("() => document.querySelector('.presence-chain__word').textContent === 'Here'", timeout=WAIT_MS)
        assert _calls(pg, host, "presence.set", at_least=2)[1] == {"here": True}
        assert not pg.locator(".table-pane").evaluate("e => e.classList.contains('is-out')")
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_chain_tugs_once_on_a_pull_and_not_under_reduced_motion(gui):
    server, browser = gui
    for motion in ("no-preference", "reduce"):
        host = DoorHost(HERE)
        pg = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion=motion).new_page()
        pg.route_web_socket("**/ws*", host.on_socket)
        pg.goto(server.url)
        try:
            chain(pg).wait_for(timeout=WAIT_MS)
            pg.evaluate("() => { window.__tug = 0; new MutationObserver(() => { if (document.querySelector('.ork-chain.is-tugging')) window.__tug++; }).observe(document.body, { attributes: true, subtree: true, attributeFilter: ['class'] }); }")
            chain(pg).click()
            pg.wait_for_function("() => document.querySelector('.presence-chain__word').textContent === 'Away'", timeout=WAIT_MS)
            pg.wait_for_timeout(800)
            assert (pg.evaluate("() => window.__tug") > 0) == (motion == "no-preference"), motion
            assert pg.locator(".ork-chain.is-tugging").count() == 0, "the beat is taken off when it is over"
        finally:
            pg.context.close()


def test_a_host_that_does_not_say_presence_has_no_chain(gui):
    pg, errors = start(gui, "wide", DoorHost(None))
    try:
        pg.wait_for_timeout(500)
        assert chain(pg).count() == 0 and pg.locator(".presence-door").count() == 0
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_under_760_the_small_chain_has_no_words_and_the_label_keeps_them(gui):
    pg, errors = start(gui, "narrow", DoorHost(HERE))
    try:
        d = chain(pg)
        d.wait_for(timeout=WAIT_MS)
        assert d.locator(".ork-chain.small").evaluate("e => e.offsetWidth") == 6 and d.locator(".presence-chain__words").count() == 0
        assert "until 23:00" in d.get_attribute("title") and d.get_attribute("aria-label") == "Here, until 23:00"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_phones_top_row_has_the_small_chain_where_the_door_stood(gui):
    host = DoorHost(AWAY)
    pg, errors = start(gui, "phone", host)
    try:
        d = pg.locator(".up-top .presence-chain")
        d.wait_for(timeout=WAIT_MS)
        assert pg.locator(".presence-door, .ork-door").count() == 0, "the door is gone"
        assert d.locator(".ork-chain.small.is-pulled").count() == 1 and d.locator(".presence-chain__words").count() == 0, "small, pulled while away, no words"
        assert not d.evaluate("e => /Here|Away/.test(e.innerText)"), "no visible words"
        assert d.get_attribute("aria-label") == "Away, until 19:00" and "until 19:00" in d.get_attribute("title")
        pack = pg.locator(".up-top .stall-pack")
        assert pack.count() == 1 and pack.locator(".ork-pack.small").count() == 1 and pack.get_attribute("aria-label") and pack.get_attribute("title"), "the backpack beside the chain"
        assert pack.evaluate("e => getComputedStyle(e.querySelector('.stall-pack__word')).display") == "none", "the backpack's word is in aria-label and title only"
        kids = pg.evaluate("() => [...document.querySelectorAll('.up-top > *')].map((e) => e.className.split(' ')[0])")
        assert kids.index("stall-pack") + 1 == kids.index("presence-chain") and kids.index("presence-chain") < kids.index("up-die"), kids
        d.click()
        assert _calls(pg, host, "presence.set") == [{"here": True}], "one press, one presence.set"
        pg.wait_for_function("() => document.querySelector('.up-top .presence-chain').dataset.here === 'true'", timeout=WAIT_MS)
        assert d.locator(".ork-chain.is-pulled").count() == 0 and d.get_attribute("aria-label").startswith("Here")
        for el in (d, pack):
            box = el.bounding_box()
            assert box["x"] >= 0 and box["x"] + box["width"] <= 390 and box["width"] >= 44 and box["height"] >= 44, box
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_phones_table_wears_the_felt_and_away_puts_it_out(gui):
    host = DoorHost(HERE)
    pg, errors = start(gui, "phone", host)
    try:
        hand = pg.locator(".hand-up")
        hand.wait_for(timeout=WAIT_MS)
        cls = hand.get_attribute("class")
        assert "ork-table" in cls and "is-out" not in cls and hand.get_attribute("data-party") == "orkmaster"
        assert "radial-gradient" in hand.evaluate("e => getComputedStyle(e).backgroundImage"), "the felt's light is orkUI's steps"
        pg.locator(".up-top .presence-chain").click()
        pg.wait_for_function("() => document.querySelector('.hand-up').classList.contains('is-out')", timeout=WAIT_MS)
        flat = pg.evaluate("() => { const e = document.createElement('i'); e.style.backgroundColor = 'var(--ork-felt-orkmaster-out)'; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }")
        assert hand.evaluate("e => getComputedStyle(e).backgroundImage") == "none" and hand.evaluate("e => getComputedStyle(e).backgroundColor") == flat, "away: the felt flat and darker"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_phones_backpack_opens_the_stall_over_the_hand_and_the_way_back_closes_it(gui):
    """Spec 160 K: on the phone the backpack shows the inventory's stall over the hand; ← closes it."""
    host = DoorHost(HERE)
    pg, errors = start(gui, "phone", host)
    try:
        pack = pg.locator(".up-top .stall-pack")
        assert pg.locator(".stall-merchant").count() == 0
        pack.click()
        pg.locator(".stall-merchant").wait_for(state="visible", timeout=WAIT_MS)
        assert pg.locator(".stall-rug").is_visible() and pg.locator(".frame[data-over]").count() == 1
        assert pg.locator(".stall-pack").first.get_attribute("aria-pressed") == "true" and pg.locator(".up-top .stall-pack .ork-pack.is-open").count() == 1
        pg.locator("[data-stall-back]").click()
        pg.locator(".up-top").wait_for(state="visible", timeout=WAIT_MS)
        assert pg.locator(".stall-merchant").count() == 0 and pg.locator(".frame[data-over]").count() == 0
        assert pg.locator(".up-top .stall-pack .ork-pack.is-open").count() == 0
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)
