"""The phone's menu of the leaders (docs/specs/117-the-phone-a-menu-of-the-leaders.md §4, part C; decisions §195.1; the mockup docs/mockups/phone/sidebar.html A2), in a real browser against the table's stub host (four parties, goals at work, three goals in line,
Talk and Spec added), with touch at 390 × 844: the crown opens a sheet from the left (312 px) over the scrim, which the scrim, Esc and the phone's back close (one history entry while it is open), the focus going in and back; its head (the project with its
switcher, *Settings*, *Stop all*); the Orkmaster's goals (Talk, Spec, then in line with the moon); each party with its sword and shield and its goals at work (*Work* or *Checks*); no count and no alert anywhere; the picked row; a press on a goal or a party
picks it and closes the menu; the desktop has no crown. Screenshots to $UPRIGHT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import sig  # noqa: E402
from tests.test_table_desktop_browser import TableHost, node, watch  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None
MENU = "The leaders and their goals"
TALK, SPEC, REVIEWED = "Daily quests: who plays them?", "Leaderboard", "Players see who answered first"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class MenuHost(TableHost):
    """The table's stub project (*shop*) with a goal in Talk and one in Spec of Game design's, nothing asked of the person."""

    def __init__(self):
        super().__init__(rich=True, line=3)
        self.nodes += [node("daily", "game", TALK, "talk", element="ice", sign="feature"), node("board", "game", SPEC, "decided", element="lava", sign="chart"),
                       node("first", "game", REVIEWED, "ready", element="void", sign="feature", back={"ripe": {"left_s": 120, "seconds": 300, "by": None, "held": False}})]      # a spec made, its work to start by itself in 2 min: To review


def start(gui, kind="phone", errors=None):
    """The page at the phone's size (touch) or at `kind` "wide" / "fine" against a MenuHost: `(page, host, errors)`."""
    server, browser = gui
    errors = [] if errors is None else errors
    host = MenuHost()
    pg = narrow.context(browser, {"phone": "phone", "wide": "wide", "fine": "narrow"}[kind]).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".up-crown" if kind == "phone" else ".table-tab", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    return pg, host, errors


def crown(pg):
    return pg.get_by_role("button", name=MENU, exact=True)


def menu(pg):
    return pg.locator(".up-menu")


def opened(pg):
    crown(pg).click()
    menu(pg).wait_for(timeout=WAIT_MS)
    pg.locator(".up-prow").first.wait_for(timeout=WAIT_MS)
    return menu(pg)


def box(loc):
    return loc.bounding_box()


def rows(pg):
    return pg.locator(".up-menu .up-grow, .up-menu .up-prow")


def texts(loc):
    return [" ".join(t.split()) for t in loc.all_inner_texts()]


def css_colour(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def bg_of(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.background = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }", token)


def test_the_crown_opens_a_sheet_from_the_left_over_the_scrim_and_focus_goes_in(gui):
    pg, host, errors = start(gui)
    try:
        assert menu(pg).count() == 0 and crown(pg).get_attribute("aria-expanded") == "false" and pg.locator(".up-scrim").count() == 0
        m = opened(pg)
        assert m.get_attribute("role") == "dialog" and m.get_attribute("aria-modal") == "true" and m.get_attribute("aria-label") == MENU
        assert crown(pg).get_attribute("aria-expanded") == "true"
        assert pg.evaluate("() => !!document.activeElement.closest('.up-menu')"), "the focus goes into the sheet"
        assert pg.evaluate("() => history.state && history.state.orkboardMenu") == 1, "one history entry while it is open"
        narrow.no_sideways(pg)
        shot(pg, "phone-menu")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)




















def test_a_goal_pressed_is_picked_and_the_menu_closes_the_picked_row_has_the_inks_bar(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        assert pg.locator(".up-menu .is-on").count() == 0, "nothing chosen: the feed is looked at, no row picked (goal 169 F)"
        pg.locator(".up-grow", has_text="Tidy the lobby code").click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "calm" and sig(pg, "frame/state.js", "tab") == "orkmaster", "the goal is picked, no party"
        assert pg.evaluate("() => document.activeElement.classList.contains('up-crown')")
        opened(pg)
        on = pg.locator(".up-menu .is-on")
        assert on.count() == 1 and on.get_attribute("data-goal") == "calm" and on.get_attribute("aria-current") == "true"
        shot(pg, "phone-menu-picked")
        pg.locator(f'.up-piles .col-card--fan[aria-label^="{TALK}"]').click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "daily"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)








def test_stop_all_sends_halt_and_closes_the_menu(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        pg.get_by_role("button", name="Stop all", exact=True).click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        for _ in range(40):
            if any(n == "halt" for n, _a in host.log):
                break
            pg.wait_for_timeout(50)
        assert any(n == "halt" for n, _a in host.log)
    finally:
        pg.close()
    assert not errors, "\n".join(errors)




PHONE = """globalThis.__calls = []; let on = false;
globalThis.orkboardPhone = Object.freeze({ paired: () => true, unpair() { __calls.push("unpair"); },
  push: Object.freeze({ async state() { return { supported: true, why: "", permission: on ? "granted" : "default", on, quiet: "" }; },
    async on() { __calls.push("on"); on = true; return { ok: true }; }, async off() { __calls.push("off"); on = false; return { ok: true }; }, async setQuiet() { return { ok: true }; } }) });"""


