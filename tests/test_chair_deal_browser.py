"""Spec 161 stage I (decisions §272, §274.1, §160.6; hand/chairdeal.js), in a real browser at 1280 x 800 against the stall's stub host: the new chair at the tabs' end, pressed, is lit and the Orkmaster's question rises
(*A new chair at the table · Which craft sits in it?*); the hand holds a 144 x 202 card for each craft not seated, with its race's head, its whole line and its price in words (one with no price says so), the Orkmaster's pick starred
and named in words; the rest of the hand sinks; *Put it back* sends nothing; a craft's card sends `ideas.goal_save` once and the backpack opens on its chair. The narrow page keeps the parties' place. Screenshots to $CHAIR_SHOTS when set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand, party  # noqa: E402
from tests.test_stall_browser import StallHost  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["CHAIR_SHOTS"]) if os.environ.get("CHAIR_SHOTS") else None
LIVEOPS = "Events, the numbers of play, what players say, small fixes."
MARKETING = "Pages, posts and search; the store page and the way people come."
RELEASE = "Ships what is done: the gate, the version, the notes."
ART = "The look of it: sprites, scenes, the pictures players see."


def preset(id, name, line, leader, stage, **more):
    return {"id": id, "name": name, "line": line, "group": "stage", "stage": stage, "craft": "engineering", "recipe": id, "whole": False, "leader": leader, "build": [], "check": [],
            "squad": [leader], "size": "lean", "locked": False, "routines": [], "ops": False, "blocked": "", "sizes": {}, **more}


class ChairHost(StallHost):
    """The stall's host with the chair's crafts unseated (Marketing with the Orkmaster's pick, Art, which has no price) and, as the host says them, LiveOps and Release as waiting (`waits`: decisions §283.29), which no chair offers; a `ideas.goal_save` seats the craft sent."""

    def __init__(self, pick=True, stage="live", **more):
        super().__init__(**more)
        self.stage = stage
        self.presets = [preset("liveops", "LiveOps", LIVEOPS, "event-imp", "live", waits=True), preset("marketing", "Marketing", MARKETING, "growth-hack-gnome", "idea", **({"recommended": True} if pick else {})),
                        preset("art", "Art", ART, "art-dryad", "live"), preset("release", "Release", RELEASE, "release-night-king", "being_made", waits=True)]
        self.saved = []

    def handle(self, name, a):
        if name == "ideas.party_presets":
            self.log.append((name, a))
            return {"kind": {"id": "game", "words": "a game", "how": ""}, "presets": self.presets}
        if name == "ideas.stage":
            self.log.append((name, a))
            return {"stage": self.stage, "read": self.stage, "kind": "game", "offered": {}}
        if name == "ideas.party_price":
            self.log.append((name, a))
            if a["leader"] == "art-dryad":
                return {"error": "No price"}
            return {"low": 4.0, "high": 5.0, "learned": True, "ideas": 3, "checks": [], "hints": []}
        if name == "ideas.goal_save":
            self.log.append((name, a))
            self.saved.append(a)
            slug = {"liveops": "run", "marketing": "marketing", "art": "art", "release": "release"}[a["preset"]]
            self.parties.append(party(slug, a["title"], "gnome", "marketing"))
            return self.bump({"slug": slug})
        return super().handle(name, a)


def size(loc):
    return loc.evaluate("e => [e.offsetWidth, e.offsetHeight]")


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def press_chair(pg):
    pg.locator(".table-chair").click()
    pg.locator(".hand-crafts .hand-craft").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => [...document.querySelectorAll('.hand-craft__price')].every((e) => e.textContent.trim())", timeout=WAIT_MS)
    pg.mouse.move(2, 2)
    pg.wait_for_timeout(500)






def test_put_it_back_and_esc_send_nothing_and_seat_nothing(gui):
    pg, host, log = open_hand(gui, host=ChairHost())
    try:
        press_chair(pg)
        pg.locator('.hand-crafts [data-act="put"]').click()
        pg.locator('[data-chair-deal="question"]').wait_for(state="detached", timeout=WAIT_MS)
        assert pg.locator(".hand-row.is-sunk").count() == 0 and pg.locator(".table-chair").get_attribute("aria-pressed") == "false"
        press_chair(pg)
        pg.keyboard.press("Escape")
        pg.locator('[data-chair-deal="crafts"]').wait_for(state="detached", timeout=WAIT_MS)
        assert host.saved == [] and not [n for n, _a in host.log if n in ("ideas.goal_save", "ideas.stall")], host.log
        assert not log, log
    finally:
        pg.close()


def test_a_crafts_card_seats_it_once_and_the_backpack_opens_on_its_chair(gui):
    """Spec 161 I: the card sends `ideas.goal_save` as the parties' place does (title, about, leader, team, size, preset), once, and the stall opens on the new party's chair."""
    pg, host, log = open_hand(gui, host=ChairHost())
    try:
        press_chair(pg)
        pg.locator('.hand-craft[data-craft="marketing"]').dblclick()
        pg.locator(".slots-table").wait_for(timeout=WAIT_MS)
        saved = _calls(pg, host, "ideas.goal_save")
        assert saved == [{"title": "Marketing", "about": MARKETING, "leader": "growth-hack-gnome", "team": ["growth-hack-gnome"], "every": [], "size": "lean", "preset": "marketing"}], saved
        assert pg.locator("[data-backpack]").get_attribute("aria-pressed") == "true"
        pg.wait_for_function("() => document.querySelector('.slots-table').dataset.stall === 'marketing'", timeout=WAIT_MS)
        assert pg.locator('.table-tab[data-tab="marketing"]').get_attribute("aria-selected") == "true", "its tab is the open one"
        assert pg.locator('[data-chair-deal]').count() == 0 and ("ideas.stall", {"chair": "marketing"}) in host.log
        assert not log, log
    finally:
        pg.close()


