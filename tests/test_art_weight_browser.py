"""Spec 165 part O, Art's cards by weight (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.2, §280.4), in a real browser at 1280 x 800, the host faked.

`ideas.art_map` gives each asset its `weight` (`light`, `normal`, `heavy`), each kind its `bytes` and the map `budget_mb`: a card's width is its weight's (three widths of orkUI's spacing), a lane's foot says its size in MB and,
with a budget, *of <n> MB*; an asset no goal's reach lights lies faint (its frame and window, its name still 4.5:1). Cards, stamps and lift are as they were. A picture to ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import MapsHost, go  # noqa: E402
from tests.test_table_desktop_browser import shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

MB = 1048576
SIZES = {"sprites/coin.png": (4096, "light"), "sprites/hero-idle.png": (200 * 1024, "normal"), "sprites/tile-0.png": (900 * 1024, "heavy"), "sounds/hit-thud.wav": (40 * 1024, "light"),
         "sounds/win-jingle.wav": (600 * 1024, "normal"), "music/lobby-loop.ogg": (6 * MB, "heavy"), "clips/intro.mp4": (3 * MB, "normal")}


class WeightHost(MapsHost):
    budget = 50
    reach: dict = {}

    def handle(self, name, a):
        if name == "ideas.art_map":
            got = super().handle(name, a)
            for k in got["kinds"]:
                for x in k["assets"]:
                    size, weight = SIZES.get(x["id"], (2048, "light"))
                    x["bytes"], x["weight"] = size, weight
                k["bytes"] = sum(x["bytes"] for x in k["assets"])
            return {**got, "budget_mb": self.budget}
        if name == "ideas.reach":
            return {"party": a["party"], "map": "art", "goals": self.reach}
        return super().handle(name, a)


def opened(gui, host):
    server, browser = gui
    errors: list[str] = []
    pg = narrow.page(browser, narrow.WIDTHS[0])
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    go(pg, "art")
    pg.locator('.mp-lane[data-kind="art"] .mp-card').first.wait_for(timeout=WAIT_MS)
    return pg, errors


def width(pg, cid):
    return pg.locator(f'.mp-card[data-id="{cid}"]').evaluate("e => e.getBoundingClientRect().width")


def test_the_picture_of_art_by_weight(gui):
    pg, errors = opened(gui, WeightHost())
    shot(pg, os.environ.get("ART_SHOT", "art-by-weight.png"))
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_a_cards_width_is_its_weights_and_the_cards_are_as_they_were(gui):
    pg, errors = opened(gui, WeightHost())
    light, normal, heavy = width(pg, "sprites/coin.png"), width(pg, "sprites/hero-idle.png"), width(pg, "sprites/tile-0.png")
    assert light < normal < heavy, (light, normal, heavy)
    assert pg.locator('.mp-card[data-id="sprites/coin.png"]').get_attribute("data-lkey") == "t:map:art:sprites/coin.png"
    pg.locator('.mp-card[data-id="sprites/hero-idle.png"] .mp-card__nm').click()
    assert pg.locator(".table-back").get_attribute("data-lifted") == "t:map:art:sprites/hero-idle.png"
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_a_lanes_foot_is_its_size_and_with_a_budget_of_it(gui):
    pg, errors = opened(gui, WeightHost())
    assert pg.locator('.mp-lane__foot[data-foot="music"]').inner_text() == "6.0 MB of 50 MB"
    assert pg.locator('.mp-lane__foot[data-foot="sound"]').inner_text() == "0.6 MB of 50 MB"
    pg.context.close()
    host = WeightHost()
    host.budget = None
    pg, errors = opened(gui, host)
    assert pg.locator('.mp-lane__foot[data-foot="music"]').inner_text() == "6.0 MB"
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_an_asset_no_goal_reach_lights_lies_faint_and_its_name_stays_readable(gui):
    host = WeightHost()
    pg, errors = opened(gui, host)
    assert pg.locator(".mp-asset.is-faint").count() == 0, "with nothing kept no asset is faint"
    host.reach = {"timer": {"lit": ["sprites/coin.png"], "one": ["sprites/hero-idle.png"], "two": [], "no_test": []}}
    pg.evaluate("() => import('/static/js/table/reach.js').then((x) => { x.reachData.value = { timer: { lit: ['sprites/coin.png'], one: ['sprites/hero-idle.png'], two: [], no_test: [] } }; })")
    pg.wait_for_function("() => document.querySelector('.mp-asset.is-faint')", timeout=WAIT_MS)
    assert "is-faint" not in pg.locator('.mp-card[data-id="sprites/coin.png"]').get_attribute("class")
    assert "is-faint" not in pg.locator('.mp-card[data-id="sprites/hero-idle.png"]').get_attribute("class")
    assert "is-faint" in pg.locator('.mp-card[data-id="sprites/tile-0.png"]').get_attribute("class")
    card = pg.locator('.mp-card[data-id="sprites/tile-0.png"]')
    assert card.evaluate("e => getComputedStyle(e).opacity") == "1"                              # the card as a whole is not faded: only its window is, so the name keeps its ink
    assert card.locator(".mp-win").evaluate("e => Number(getComputedStyle(e).opacity)") < 1
    assert not errors, "\n".join(errors)
    pg.context.close()
