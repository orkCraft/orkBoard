"""Spec 157 E (docs/specs/157-the-inventory-a-merchants-stall.md; decisions §267.2), in a real browser against a stub host: a party whose leader's hero is not its craft's default draws the hero's table
(`ideas.hero_table {party}`): a lane a place with its question under its name, a kept card in its lane with its goal's element and its state as the border, an empty place saying its question and nothing
else, the one line over the table while nothing is kept or the kept frame is stale (its goal a press that picks the goal), a row a place for the `rows` layout; a default hero shows today's map.
The screenshot goes to the file `HERO_SHOT` names when it is set."""
from __future__ import annotations

import copy
import os

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, node, open_hand  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

XP = [("Red", "Which test fails, written before its code?"), ("Green", "What is the least code that passes it?"),
      ("Refactor", "What can be cleaner with the tests green?"), ("Released small", "What went out in a small step?")]
ATOM = [("Tokens", "Which values are named once?"), ("Atoms", "Which parts stand alone?"), ("Molecules", "Which atoms work as one?")]


def table(hero, layout, places, kept, laid="2026-11-07", stale=False, elements=None):
    return {"hero": hero, "layout": layout, "laid": laid, "stale": stale, "elements": elements or {},
            "places": [{"name": n, "ask": a, "cards": copy.deepcopy(kept.get(n, []))} for n, a in places]}


class HeroHost(HandHost):
    def __init__(self, doc=None, laying=True):
        super().__init__(bare=True)
        self.doc = doc
        for p in self.parties:
            if p["slug"] == "tech":
                p["leader"] = {**p["leader"], "hero": {"id": "sh-xp", "name": "Spike Shaman", "school": "Extreme programming", "default": False, "head": {"race": "orc", "tier": "elder"}}}
            if p["slug"] == "design":
                p["leader"] = {**p["leader"], "hero": {"id": "dry-heur", "name": "Pixel-Perfect Dryad", "school": "Nielsen's heuristics", "default": True, "head": {"race": "elf", "tier": "elder"}}}
        if laying:
            self.nodes.append(node("laying", "tech", "Lay the tables", "table", state="ready", element="void"))

    def handle(self, name, a):
        if name == "ideas.hero_table":
            self.log.append((name, a))
            return copy.deepcopy(self.doc)
        return super().handle(name, a)


KEPT = {"Red": [{"title": "Reconnect keeps the seat", "line": "fails on the second socket", "goal": "timer", "state": "bad"}],
        "Green": [{"title": "Keep a seat table", "line": "one map by room code", "goal": "timer", "state": "hot"},
                  {"title": "Free the seat", "line": "after thirty seconds", "goal": "", "state": "ghost"}],
        "Refactor": [{"title": "Name the seat", "line": "", "goal": "nogoal", "state": "good"}]}


def open_table(gui, host, slug="tech"):
    pg, host, log = open_hand(gui, host=host)
    open_tab(pg, slug)
    return pg, host, log


def test_a_kept_table_lays_a_lane_a_place_with_its_cards_element_and_state(gui):
    pg, host, log = open_table(gui, HeroHost(table("sh-xp", "lanes", XP, KEPT, elements={"timer": "dust"})))
    try:
        pg.locator(".hm").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hm").get_attribute("data-layout") == "lanes"
        assert [t.lower() for t in pg.locator(".hm-place__nm").all_inner_texts()] == ["red", "green", "refactor", "released small"]
        assert pg.locator('[data-place="Red"] .hm-place__ask').inner_text() == "Which test fails, written before its code?"
        assert ("ideas.hero_table", {"party": "tech"}) in host.log
        red = pg.locator('[data-place="Red"] .hm-card')
        assert red.count() == 1 and "Reconnect keeps the seat" in red.inner_text() and "fails on the second socket" in red.inner_text()
        assert red.locator(".ork-elem.dust").count() == 1 and red.get_attribute("data-state") == "bad"
        green = pg.locator('[data-place="Green"] .hm-card')
        assert green.count() == 2 and green.nth(0).get_attribute("data-state") == "hot" and green.nth(1).get_attribute("data-state") == "ghost"
        assert green.nth(1).locator(".ork-elem").count() == 0                                    # no goal: no element
        assert pg.locator('[data-place="Refactor"] .hm-card .ork-elem').count() == 0              # a goal whose element is not known: none
        border = lambda loc: loc.evaluate("e => getComputedStyle(e).borderTopColor")             # noqa: E731
        assert len({border(red), border(green.nth(0)), border(pg.locator('[data-place="Refactor"] .hm-card'))}) == 3
        assert green.nth(1).evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"
        assert pg.locator(".hm-laying").count() == 0                                             # laid and not stale: no line
        pg.screenshot(path=os.environ.get("HERO_SHOT", "/tmp/hero-table-lanes.png"))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_empty_place_says_only_its_question(gui):
    pg, host, log = open_table(gui, HeroHost(table("sh-xp", "lanes", XP, KEPT)))
    try:
        place = pg.locator('[data-place="Released small"]')
        place.wait_for(timeout=WAIT_MS)
        assert place.locator(".hm-card").count() == 0
        assert place.locator(".hm-place__ask").inner_text() == "What went out in a small step?"
        assert [t.strip() for t in place.inner_text().split("\n") if t.strip()][1:] == ["What went out in a small step?"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_nothing_kept_says_who_lays_the_table_and_the_goal_is_a_press_that_picks_it(gui):
    pg, host, log = open_table(gui, HeroHost(table("sh-xp", "lanes", XP, {}, laid="")))
    try:
        line = pg.locator(".hm-laying")
        line.wait_for(timeout=WAIT_MS)
        assert line.inner_text() == "Spike Shaman lays this table with the goal Lay the tables"
        assert pg.locator(".hm-place").count() == 4 and pg.locator(".hm-card").count() == 0
        line.get_by_role("button", name="Lay the tables").click()
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.picked.value === 'laying')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_stale_table_says_lay_the_partys_table_and_without_the_goal_it_is_plain_text(gui):
    pg, host, log = open_table(gui, HeroHost(table("sh-xp", "lanes", XP, KEPT, stale=True), laying=False))
    try:
        line = pg.locator(".hm-laying")
        line.wait_for(timeout=WAIT_MS)
        assert line.inner_text() == "Spike Shaman lays this table with the goal Lay Tech's table"
        assert line.get_by_role("button").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_rows_layout_is_a_row_a_place(gui):
    pg, host, log = open_table(gui, HeroHost(table("sh-xp", "rows", ATOM, {"Atoms": [{"title": "Button", "line": "one press", "goal": "", "state": ""}]})))
    try:
        pg.locator(".hm.is-rows").wait_for(timeout=WAIT_MS)
        boxes = [pg.locator(f'[data-place="{n}"]').bounding_box() for n, _ in ATOM]
        assert boxes[0]["y"] < boxes[1]["y"] < boxes[2]["y"] and boxes[0]["x"] == boxes[1]["x"]
        assert pg.locator('[data-place="Atoms"] .hm-place__nm').bounding_box()["x"] < pg.locator('[data-place="Atoms"] .hm-card').bounding_box()["x"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_default_hero_shows_todays_map_not_the_heros(gui):
    pg, host, log = open_table(gui, HeroHost(table("x", "lanes", XP, {})), "design")
    try:
        pg.wait_for_timeout(300)
        assert pg.locator(".hm").count() == 0 and not [c for c in host.log if c[0] == "ideas.hero_table"]
        same = pg.evaluate("""() => import('/static/js/table/maps.js').then((m) => m.mapOf({ party_craft: 'release', leader: { hero: { default: true } } }) === m.mapOf({ party_craft: 'release' })
            && m.mapOf({ party_craft: 'release', leader: { hero: { default: false } } }) !== m.mapOf({ party_craft: 'release' }))""")
        assert same
    finally:
        pg.close()
    assert not log, "\n".join(log)
