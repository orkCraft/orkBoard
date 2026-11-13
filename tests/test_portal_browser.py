"""The portal to main (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §6, decisions §177.4), in a real browser at the two widths of `tests/narrow.py`, against a stub whose `ideas.gate` lists goals ready for main and whose
`ideas.to_main_plan` and `ideas.to_main` answer as the host's do (gui/ideas_gate.py): each goal ready for main is a card in the discard's view; pressing one (or beginning to drag it) opens the portal above the pile with the line the plan
says; a press on the portal, a drop on it or Enter sends the goal alone with `ideas.to_main`; a sealed portal says its reason and plays nothing; the first time it says how; Esc or a press away closes it.
At the wide width the portal's place is the always laid ring (docs/specs/110-runes-on-the-table.md §3.2, decisions §185.2, §186.3): the open portal lies in it while goals are ready, pressed with no goal chosen it opens the discard's view, a goal chosen puts its element
in the ring's seal (faint while the portal is sealed) and closing the view, Esc or a press away drop the choice and leave the ring open; at the narrow width the portal opens when a goal is chosen and closes with the choice, as before.
Screenshots to $PORTAL_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, RoadHost, node, open_hand, sig  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PORTAL_SHOTS"]) if os.environ.get("PORTAL_SHOTS") else None
SEALED = "Menu does not apply to main cleanly: player.ts"
FIRST_WIDE, FIRST_NARROW = "Drag a goal done into the portal to send it to main", "Tap the portal to send it to main"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class PortalHost(HandHost):
    """The hand's project with three goals ready for main: Lobby (which stands on Reconnect), Reconnect, and Menu (the gate holds it: it does not apply to main cleanly)."""

    def __init__(self):
        super().__init__()
        menu = node("menu", "tech", "Menu screen", "discard", state="done", element="ice", updated="2026-10-18T12:00:00")
        self.nodes.append(menu)
        self.gate_doc["ideas"].append({"slug": "menu", "title": menu["title"], "goal": "tech", "tasks": 1})
        self.gate_doc["commits"] = 6
        self.plans = {
            "music": {"goals": ["music", "codes"], "commits": ["a1", "a2"], "sealed": None, "titles": {"music": "Lobby", "codes": "Reconnect"}, "files": 3},
            "codes": {"goals": ["codes"], "commits": ["a2"], "sealed": None, "titles": {"codes": "Reconnect"}, "files": 1},
            "menu": {"goals": ["menu"], "commits": ["m1"], "sealed": SEALED, "titles": {"menu": "Menu"}, "files": 1}}
        self.refuse = ""

    def handle(self, name, a):
        if name == "ideas.to_main_checks" and not isinstance(self, RoadHost):                # the checks on the way into main (spec 111 §4.2), all passed at once: the portal is open as the test means it
            self.log.append((name, a))
            return {"idea": a["idea"], "running": False, "checks": [{"name": "The merge", "state": "passed", "words": ""}, {"name": "Tests", "state": "passed", "words": ""}]}
        if name == "ideas.to_main_plan":
            self.log.append((name, a))
            return {"idea": a["idea"], "into": "dev", "main": "main", **self.plans[a["idea"]]}
        if name == "ideas.to_main":
            self.log.append((name, a))
            if self.refuse:
                return {"error": self.refuse}
            gone = set(self.plans[a["idea"]]["goals"])
            self.gate_doc["ideas"] = [i for i in self.gate_doc["ideas"] if i["slug"] not in gone]
            self.gate_doc["commits"] -= len(self.plans[a["idea"]]["commits"])
            return self.bump({"commit": "abc", "goals": sorted(gone), "commits": 1, "files": 1, "note": "", "pushed": False})
        return super().handle(name, a)


def open_view(gui, width="narrow"):
    """The window against the portal's stub with the discard's view open (the pile pressed)."""
    pg, host, log = open_hand(gui, host=PortalHost(), width=width)
    pile = pg.locator(".table-end .hand-done")
    pile.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    pile.click()
    pg.locator(".portal-cards").wait_for(timeout=WAIT_MS)
    return pg, host, log


def card(pg, slug):
    return pg.locator(f'[data-portal-card="{slug}"]')


def portal(pg):
    return pg.locator(".portal-host .ork-portal")


def unchosen(pg):
    """Waits for no goal to be chosen: no line over the portal (at the narrow width there is no portal then; at the wide one the ring stays, open or asleep)."""
    pg.wait_for_function("() => !document.querySelector('.portal__line')", timeout=WAIT_MS)


def woken(pg):
    """Waits for the ring's waking to end (its eye opens after the runes, about a second): until then the portal is not there to be hit."""
    pg.wait_for_function("() => document.getAnimations().every((a) => !a.effect?.target?.closest?.('.ork-portal-ring') || a.playState !== 'running' || a.effect.getComputedTiming().iterations === Infinity)", timeout=WAIT_MS)


def seal(pg):
    return pg.locator(".ork-portal-ring__seal > .ork-elem")


def open_portal(pg, slug="music"):
    card(pg, slug).click()
    portal(pg).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => !['wait', 'ready', 'asleep', undefined].includes(document.querySelector('.portal-host')?.dataset.portal)", timeout=WAIT_MS)


@pytest.mark.parametrize("width", ["narrow"])
def test_a_goal_ready_for_main_is_a_card_and_pressing_it_opens_the_portal_above_the_pile(gui, width):
    pg, host, log = open_view(gui, width)
    try:
        assert pg.locator(".portal-cards [data-portal-card]").count() == 3
        assert portal(pg).count() == (1 if width == "wide" else 0), "the ring's portal lies there at the wide width; at the narrow one none until a goal is chosen"
        assert pg.locator(".portal__line").count() == 0 and (width == "narrow" or seal(pg).count() == 0), "no goal chosen: no line, nothing in the seal"
        assert pg.get_by_role("region", name="Ready for main").get_by_role("button", name="To main", exact=True).count() == 1, "To main stays, and takes the portal's way (spec 149 G.1)"
        assert pg.locator("#table-pane .hand-discardview").get_by_role("region", name="Done, not yet seen").count() == 1, "Done, not yet seen stays"
        assert "Lobby music loop" in card(pg, "music").inner_text() and card(pg, "music").locator(".ork-sign.check").count() == 1 and card(pg, "music").locator(".ork-elem.void").count() == 1
        open_portal(pg)
        if width == "wide":
            ring = pg.locator(".portal-host > .ork-portal-ring")
            assert ring.count() == 1 and portal(pg).evaluate("e => e.parentElement.classList.contains('ork-portal-ring')"), "the portal lies in the ring"
            assert "is-open" in ring.get_attribute("class") and "is-sealed" not in ring.get_attribute("class")
            assert seal(pg).count() == 1 and "void" in seal(pg).get_attribute("class"), "the chosen goal's element lies in the ring's seal"
        else:
            assert pg.locator(".ork-portal-ring").count() == 0, "no ring at the narrow width"
        assert pg.locator(".portal__label").text_content() == "Main"
        assert pg.locator(".portal__line").text_content() == "Into main: Lobby, and Reconnect it stands on"
        assert portal(pg).get_attribute("aria-label") == "Send Lobby and Reconnect to main" and portal(pg).evaluate("e => e.tagName") == "BUTTON"
        assert ("small" in portal(pg).get_attribute("class")) == (width == "narrow")
        assert card(pg, "music").get_attribute("aria-pressed") == "true" and "ork-picked" in card(pg, "music").get_attribute("class")
        assert pg.evaluate("() => document.activeElement?.classList.contains('ork-portal')"), "the focus is on the portal"
        pg.wait_for_timeout(300)
        assert len(_calls(pg, host, "ideas.to_main_plan", 1)) == 1, "the plan is asked once, not on every render"
        narrow.no_sideways(pg)
        card(pg, "codes").click()                                                                                      # another goal chosen: its own line
        pg.wait_for_function("() => document.querySelector('.portal__line')?.textContent === 'Into main: Reconnect'", timeout=WAIT_MS)
        assert portal(pg).get_attribute("aria-label") == "Send Reconnect to main" and card(pg, "music").get_attribute("aria-pressed") == "false"
        assert _calls(pg, host, "ideas.to_main_plan", 2) == [{"idea": "music"}, {"idea": "codes"}]
        if width == "wide":
            assert "dust" in seal(pg).get_attribute("class") and seal(pg).count() == 1, "the seal holds the goal chosen now"
    finally:
        pg.close()
    assert not log, "\n".join(log)




@pytest.mark.parametrize("width", ["narrow"])
def test_pressing_the_portal_sends_the_goal_alone_with_what_it_stands_on_and_the_cards_leave(gui, width):
    pg, host, log = open_view(gui, width)
    try:
        open_portal(pg)
        shot(pg, f"{width}-open")
        portal(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"})) and [a for n, a in host.log if n == "ideas.to_main"] == [{"idea": "music", "sealed": True}]
        pg.wait_for_function("() => document.querySelectorAll('[data-portal-card]').length === 1", timeout=WAIT_MS)             # Lobby and Reconnect left the ready goals
        assert card(pg, "menu").count() == 1 and card(pg, "music").count() == 0 and card(pg, "codes").count() == 0
        unchosen(pg)
        assert sig(pg, "frame/state.js", "over")["kind"] == "discard", "the view stays open"
        assert "1 goal ready for main" in pg.locator(".table-end .hand-done").get_attribute("aria-label")
        assert portal(pg).count() == (1 if width == "wide" else 0), "the ring stays open for Menu; at the narrow width the portal is gone"
        if width == "wide":
            assert seal(pg).count() == 0 and pg.locator(".portal-host").get_attribute("data-portal") == "ready"
    finally:
        pg.close()
    assert not log, "\n".join(log)






@pytest.mark.parametrize("width", ["narrow"])
def test_a_sealed_portal_says_its_reason_again_when_pressed_and_plays_nothing(gui, width):
    pg, host, log = open_view(gui, width)
    try:
        open_portal(pg, "menu")
        assert "is-sealed" in portal(pg).get_attribute("class")
        assert portal(pg).get_attribute("aria-label") == f"Sealed: {SEALED}"
        line = pg.locator(".portal__sealed")
        assert line.get_attribute("aria-live") == "polite" and line.text_content() == f"Sealed: {SEALED}"
        assert pg.locator(".portal__hint").count() == 0, "no first-time line over a sealed portal"
        shot(pg, f"{width}-sealed")
        pg.locator(".portal__sealed span").evaluate("e => e.setAttribute('data-before', '1')")
        portal(pg).click()
        pg.wait_for_function("() => document.querySelector('.portal__sealed span') && !document.querySelector('.portal__sealed span').hasAttribute('data-before')", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert [n for n, _ in host.log if n == "ideas.to_main"] == [] and line.text_content() == f"Sealed: {SEALED}", "the reason said again, nothing played"
        assert card(pg, "menu").count() == 1 and portal(pg).count() == 1 and "is-sealed" in portal(pg).get_attribute("class")
    finally:
        pg.close()
    assert not log, "\n".join(log)










def test_an_error_from_the_host_is_shown_as_a_failed_act_and_the_goal_stays(gui):
    pg, host, log = open_view(gui)
    try:
        host.refuse = "main moved while it was merging: look again"
        open_portal(pg)
        portal(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"}))
        pg.get_by_text("main moved while it was merging: look again").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator("[data-portal-card]").count() == 3 and portal(pg).count() == 1, "nothing left, the portal is open for another try"
        assert card(pg, "music").evaluate("e => !e.classList.contains('is-going')")
    finally:
        pg.close()
    assert not log or all("main moved" in m for m in log), "\n".join(log)




# -- the wide width: the ready card picked in Release's lane (spec 156 D.4) ------------------------------------------------------------------------------


def open_lane(gui, host=None):
    """The window at the wide width against the portal's stub, the lane laid with its ready cards."""
    pg, host, log = open_hand(gui, host=host or PortalHost(), width="wide")
    pg.locator('.release-lane [data-portal-card="music"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    return pg, host, log


def lane_card(pg, slug):
    return pg.locator(f'.release-lane [data-portal-card="{slug}"]')


def picked_is(pg, slug):
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)


def tomain(pg):
    return pg.locator("[data-tomain]")










