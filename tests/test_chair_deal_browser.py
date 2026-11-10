"""Spec 161 stage I (decisions §272, §274.1, §160.6; hand/chairdeal.js), in a real browser at 1280 x 800 against the stall's stub host: the new chair at the tabs' end, pressed, is lit and the Orkmaster's question rises
(*A new chair at the table · Which craft sits in it?*); the hand holds a 144 x 202 card for each craft not seated, with its race's head, its whole line and its price in words (one with no price says so), the Orkmaster's pick starred
and named in words; the rest of the hand sinks; *Put it back* sends nothing; a craft's card sends `ideas.goal_save` once and the backpack opens on its chair. The narrow page keeps the parties' place. Screenshots to $CHAIR_SHOTS when set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
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


def test_the_chair_deals_a_card_for_each_craft_not_seated_with_head_line_price_and_the_pick_starred_and_named(gui):
    """Spec 161 I: the question rises, each unseated craft is a 144 x 202 card, its pick starred and named, the rest of the hand sunk."""
    pg, host, log = open_hand(gui, host=ChairHost())
    try:
        chair = pg.locator(".table-chair")
        chair.wait_for(timeout=WAIT_MS)
        press_chair(pg)
        assert chair.get_attribute("aria-pressed") == "true" and pg.locator(".table-chair .ork-chair.is-lit").count() == 1, "the chair is lit"
        q = pg.locator('[data-chair-deal="question"]')
        assert size(q) == [144, 202] and "asks" in q.get_attribute("class").split()
        assert q.locator(".hand-card__name").inner_text().strip() == "A new chair at the table" and q.locator(".hand-card__foot").inner_text().strip() == "Which craft sits in it?"
        assert q.locator("img.ork-race__head").get_attribute("src").endswith("peon-crown.png"), "the Orkmaster's head"
        cards = pg.locator(".hand-crafts .hand-craft")
        assert [c.get_attribute("data-craft") for c in cards.all()] == ["marketing", "art"], "no Release nor LiveOps chair (decisions §283.29)"
        for c in cards.all():
            assert size(c) == [144, 202]
            assert c.locator(".corner--top img.ork-race__head").count() == 1, "its race's head as its sign"
        mk, rel = cards.nth(0), cards.nth(1)
        assert "/gnome-" in mk.locator(".corner--top img.ork-race__head").get_attribute("src")
        assert mk.locator(".hand-ans__name").inner_text().strip() == "Marketing" and mk.locator(".hand-ans__line").inner_text().strip() == MARKETING, "the whole line"
        assert mk.locator(".hand-ans__line").evaluate("e => e.scrollHeight <= e.clientHeight + 1"), "not cut"
        assert "of Claude's week" in mk.locator(".hand-craft__price").inner_text() and mk.locator(".corner--foot .ork-gem").count() == 1, "its price, said plainly, in its corner"
        live = rel
        assert rel.locator(".hand-craft__price").inner_text().strip() == "no price yet" and rel.locator(".ork-gem").count() == 0, "no price: it says so, none invented"
        assert mk.get_attribute("data-pick") == "1" and mk.locator("[data-star]").inner_text() == "★" and mk.locator("[data-pick-words]").inner_text() == "the Orkmaster's pick"
        assert live.get_attribute("data-pick") is None and not live.locator("[data-star]").count() and not rel.locator("[data-star]").count(), "only the pick is starred"
        assert pg.locator(".hand-row.is-sunk").count() == 1 and pg.locator(".hand-row").get_attribute("inert") is not None, "the rest of the hand sinks"
        assert [n for n, _a in host.log if n == "ideas.goal_save"] == []
        shot(pg, "product-chair")
        assert not log, log
    finally:
        pg.close()


def test_with_no_pick_in_the_presets_the_first_reached_unseated_craft_is_the_orkmasters_pick(gui):
    """Spec 161 I: no preset says a pick, so the Orkmaster's is the first unseated craft whose stage is reached, in the presets' order."""
    pg, host, log = open_hand(gui, host=ChairHost(pick=False))
    try:
        press_chair(pg)
        assert pg.locator(".hand-craft").count() == 2 and pg.locator("[data-star]").count() == 1
        pick = pg.locator('.hand-craft[data-pick="1"]')
        assert pick.count() == 1 and pick.get_attribute("data-craft") == "marketing" and pick.locator("[data-pick-words]").inner_text() == "the Orkmaster's pick"
        assert not log, log
    finally:
        pg.close()


def test_the_first_pick_skips_a_craft_whose_stage_is_not_reached(gui):
    pg, host, log = open_hand(gui, host=ChairHost(pick=False, stage="being_made"))
    try:
        press_chair(pg)
        assert pg.locator(".hand-craft").count() == 1 and pg.locator('.hand-craft[data-pick="1"]').get_attribute("data-craft") == "marketing"
        assert pg.locator("[data-star]").count() == 1
    finally:
        pg.close()


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
        pg.locator(".stall-rug").wait_for(timeout=WAIT_MS)
        saved = _calls(pg, host, "ideas.goal_save")
        assert saved == [{"title": "Marketing", "about": MARKETING, "leader": "growth-hack-gnome", "team": ["growth-hack-gnome"], "every": [], "size": "lean", "preset": "marketing"}], saved
        assert pg.locator("[data-backpack]").get_attribute("aria-pressed") == "true"
        pg.wait_for_function("() => document.querySelector('.stall').dataset.stall === 'marketing'", timeout=WAIT_MS)
        assert pg.locator('.table-tab[data-tab="marketing"]').get_attribute("aria-selected") == "true", "its tab is the open one"
        assert pg.locator('[data-chair-deal]').count() == 0 and ("ideas.stall", {"chair": "marketing"}) in host.log
        assert not log, log
    finally:
        pg.close()


def test_the_narrow_page_keeps_the_parties_place(gui):
    server, browser = gui
    host = ChairHost()
    pg = narrow.page(browser, "narrow")
    pg.route_web_socket("**/ws*", host.on_socket)
    try:
        pg.goto(server.url)
        pg.locator(".table-chair").wait_for(timeout=WAIT_MS)
        pg.locator(".table-chair").click()
        pg.wait_for_timeout(300)
        assert pg.locator("[data-chair-deal]").count() == 0 and pg.locator(".parties-wrap").count() == 1
    finally:
        pg.close()
