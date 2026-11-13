"""Spec 157 E (docs/specs/157-the-inventory-a-merchants-stall.md; decisions §267.2), in a real browser against a stub host: a party whose leader's hero is not its craft's default draws the hero's table
(`ideas.hero_table {party}`): a lane a place with its question under its name, a kept card in its lane with its goal's element and its state as the border, an empty place saying its question and nothing
else, the one line over the table while nothing is kept or the kept frame is stale (its goal a press that picks the goal), a row a place for the `rows` layout; a default hero shows today's map.
The screenshot goes to the file `HERO_SHOT` names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, node, open_hand  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

XP = [("Red", "Which test fails, written before its code?"), ("Green", "What is the least code that passes it?"),
      ("Refactor", "What can be cleaner with the tests green?"), ("Released small", "What went out in a small step?")]


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












