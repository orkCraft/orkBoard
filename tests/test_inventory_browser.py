"""Spec 117 part I, Art as an inventory (docs/specs/117-each-lens-a-games-shape.md §8, decisions §195), at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844), against the maps' stub host (`MapsHost`) that answers
`ideas.art_map` with each asset's `weight`, each kind's `bytes` and the map's `budget`, and `ideas.heat` with `unused` on two assets.

A lane is a grid of cells and a card spans one cell when its asset is light, two normal, three heavy (a one-cell card its picture and its name in a line); a lane's foot says its size in files; with a budget a line over the lanes
says how much of it Art takes, past it in the alert colour; an asset no code names (`data-heat~="unused"`) lies faint, its frame dashed, its title saying so; the reach's edge on such a card stays whole. No sideways scroll.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import COMMIT, MapsHost, asset, card, go, picture, wide  # noqa: E402
from tests.test_table_desktop_browser import shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

MB = 1048576
GLOW, TILE, LOGO, HERO, BANNER = "sprites/glow.png", "sprites/tile.png", "sprites/coin.png", "sprites/hero-idle.png", "sprites/banner.png"
UNUSED = "Nothing in the code names it"


def weighed(a, weight, size):
    return {**a, "weight": weight, "bytes": size}


class InventoryHost(MapsHost):
    """The maps' host whose Art answers with weights, kinds' bytes and a budget (`budget`: `{bytes, of}` or None); `unused` the assets the heat says nothing names."""

    def __init__(self, budget=None, unused=(TILE, HERO)):
        super().__init__()
        self.budget = budget
        self.unused = unused
        art = [weighed(asset(HERO, "art", w=16, h=16, url=picture("#c9a227")), "normal", 600 * 1024),
               weighed(asset(TILE, "art", w=16, h=16, url=picture("#556")), "light", 4 * 1024),
               weighed(asset(LOGO, "art", w=16, h=16, url=picture("#d4af37")), "light", 12 * 1024),
               weighed(asset(BANNER, "art", w=16, h=16, url=picture("#668")), "heavy", 3 * MB),
               weighed(asset(GLOW, "art", w=16, h=16, url=picture("#865")), "normal", 300 * 1024)]
        self.assets = [{"kind": "art", "own": True, "n": 5, "bytes": sum(a["bytes"] for a in art), "folders": [{"folder": "sprites/", "n": 5}], "assets": art},
                       {"kind": "sound", "own": True, "n": 1, "bytes": 90 * 1024, "folders": [{"folder": "sounds/", "n": 1}],
                        "assets": [weighed(asset("sounds/hit.wav", "sound", seconds=0.4), "light", 90 * 1024)]},
                       {"kind": "music", "own": True, "n": 2, "bytes": 5 * MB, "folders": [{"folder": "music/", "n": 2}],
                        "assets": [weighed(asset("music/loop.ogg", "music", seconds=72), "normal", 5 * MB)]},
                       {"kind": "clip", "own": True, "n": 0, "bytes": 0, "folders": [], "assets": []}]

    def handle(self, name, a):
        if name == "ideas.art_map":
            return {**copy.deepcopy(super().handle(name, a)), "budget": self.budget}
        if name == "ideas.heat":
            self.log.append((name, a))
            return {"map": "art", "parts": {u: [{"kind": "unused", "aspect": "dead_code", "words": "No file names it"}] for u in self.unused}}
        return super().handle(name, a)


def open_art(gui, width, host):
    server, browser = gui
    errors: list[str] = []
    pg = narrow.page(browser, width)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    go(pg, "art")
    pg.locator(".mp-lane .mp-card").first.wait_for(timeout=WAIT_MS)
    return pg, errors


@pytest.fixture(params=narrow.WIDTHS)
def inv(gui, request):
    """The window at one of the two widths on Art, the host without a budget: `(page, host, width)`; the page's errors are asserted at the end."""
    host = InventoryHost()
    pg, errors = open_art(gui, request.param, host)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def box(pg, cid):
    return card(pg, cid).bounding_box()


def test_a_card_spans_one_two_or_three_cells_by_its_assets_weight_its_picture_filling_it(inv):
    pg, host, w = inv
    cell, gap = 72, 8
    spans = {TILE: 1, LOGO: 1, HERO: 2, GLOW: 2, BANNER: 3}
    for cid, n in spans.items():
        c = card(pg, cid)
        if not c.count():
            continue                                                                                                       # four are shown at 390, the rest are behind *and n more*
        b = c.bounding_box()
        assert abs(b["width"] - (n * cell + (n - 1) * gap)) <= 1.5 and abs(b["height"] - b["width"]) <= 1.5, (cid, b)       # n cells each way
    one, two = card(pg, TILE), card(pg, HERO)
    assert one.get_attribute("class").count("is-s1") == 1 and two.get_attribute("class").count("is-s2") == 1
    pic, win = two.locator(".mp-win").bounding_box(), two.locator(".mp-win img").bounding_box()
    assert abs(pic["width"] - win["width"]) <= 2 * 4 + 2 and win["height"] >= pic["height"] - 12                           # the picture fills its window (less its padding)
    small = one.locator(".mp-win").bounding_box()
    assert small["height"] >= 30 and one.locator(".mp-card__nm").is_visible() and one.locator(".mp-win img").is_visible()   # a one-cell card: its picture and its name
    nm = one.locator(".mp-card__nm").bounding_box()
    assert nm["height"] <= 18 and nm["y"] > small["y"]                                                                     # the name in one line, under the picture
    shot(pg, f"inventory-{w}.png")


def test_a_lane_has_its_foot_and_no_budget_line_without_a_budget(inv):
    pg, host, w = inv
    foot = lambda kind: pg.locator(f'.mp-lane[data-kind="{kind}"] .iv-foot')
    assert foot("art").inner_text() == "3.9 MB in 5 files" and foot("sound").inner_text() == "90 KB in 1 file" and foot("music").inner_text() == "5 MB in 2 files"
    assert foot("clip").count() == 0                                                                                       # a lane with no file has no foot
    assert pg.locator(".iv-budget").count() == 0
    assert pg.locator('.mp-lane[data-kind="art"] .mp-cap').first.inner_text() == "sprites/: 5 pictures"                       # the lane's caption as built


@pytest.mark.parametrize("budget,words,over", [({"bytes": 5 * MB, "of": 10 * MB}, "Art: 5 MB of the budget's 10 MB", False),
                                              ({"bytes": 12 * MB + MB // 2, "of": 10 * MB}, "Art: 12.5 MB, over the budget's 10 MB", True)])
def test_the_budget_line_over_the_lanes_says_how_much_art_takes_and_past_it_turns_to_the_alert_colour(gui, budget, words, over):
    for width in narrow.WIDTHS:
        pg, errors = open_art(gui, width, InventoryHost(budget=budget))
        line = pg.locator(".iv-budget")
        assert line.inner_text() == words and (line.get_attribute("data-over") is not None) is over
        assert line.bounding_box()["y"] < pg.locator(".mp-lanes").bounding_box()["y"]                                         # over the lanes
        color = pg.evaluate("() => [getComputedStyle(document.querySelector('.iv-budget')).color, getComputedStyle(document.documentElement).getPropertyValue('--ork-alert')]")
        if over:
            pg.evaluate("() => { const e = document.createElement('i'); e.id = 'probe'; e.style.color = 'var(--ork-alert)'; document.body.appendChild(e); }")
            assert color[0] == pg.evaluate("() => getComputedStyle(document.getElementById('probe')).color")
        else:
            assert color[0] != pg.evaluate("() => (document.body.insertAdjacentHTML('beforeend', '<i id=probe style=\"color:var(--ork-alert)\"></i>'), getComputedStyle(document.getElementById('probe')).color)")
        shot(pg, f"inventory-budget-{'over' if over else 'under'}-{width}.png")
        narrow.no_sideways(pg)
        pg.context.close()
        assert not errors, "\n".join(errors)


def test_an_asset_nothing_names_lies_faint_its_frame_dashed_and_its_title_says_so(inv):
    pg, host, w = inv
    pg.locator(f'.mp-card[data-id="{TILE}"][data-heat~="unused"]').wait_for(timeout=WAIT_MS)
    tile, hero, logo = card(pg, TILE), card(pg, HERO), card(pg, LOGO)
    assert "unused" in hero.get_attribute("data-heat") and logo.get_attribute("data-heat") is None
    assert tile.evaluate("el => getComputedStyle(el).borderTopStyle") == "dashed" and logo.evaluate("el => getComputedStyle(el).borderTopStyle") == "solid"
    assert float(tile.locator(".mp-win").evaluate("el => getComputedStyle(el).opacity")) < 1 and float(logo.locator(".mp-win").evaluate("el => getComputedStyle(el).opacity")) == 1
    assert tile.get_attribute("title") == f"tile.png\n{UNUSED}" and tile.locator(".mp-card__nm").get_attribute("title") == f"tile.png\n{UNUSED}"
    assert logo.get_attribute("title") is None and logo.locator(".mp-card__nm").get_attribute("title") == "coin.png"
    shot(pg, f"inventory-unused-{w}.png")


def test_the_reach_edge_of_a_faint_card_stays_whole(inv):
    pg, host, w = inv
    pg.locator(f'.mp-card[data-id="{TILE}"][data-heat~="unused"]').wait_for(timeout=WAIT_MS)
    pg.evaluate("""(id) => { const c = document.querySelector(`.mp-card[data-id="${id}"]`), e = document.createElement('i'); e.className = 'rc-edge'; e.dataset.near = '0'; e.dataset.elem = 'ice'; c.prepend(e); }""", TILE)
    edge = card(pg, TILE).locator(":scope > .rc-edge")
    pg.wait_for_timeout(500)                                                                                               # the edge has come in
    assert edge.is_visible() and float(edge.evaluate("el => getComputedStyle(el).opacity")) == 1 and edge.evaluate("el => getComputedStyle(el.parentElement).opacity") == "1"
    assert abs(edge.bounding_box()["width"] - box(pg, TILE)["width"]) <= 2                                                 # it lies over the card's own box


def test_the_lanes_stay_as_built_and_a_heavy_card_never_spans_past_its_lane(inv):
    pg, host, w = inv
    lane = pg.locator('.mp-lane[data-kind="art"]')
    assert lane.locator(".mp-card").count() == (5 if wide(w) else 4)                                                      # six shown (four at 390), the rest behind *and n more*
    if not wide(w):
        lane.get_by_role("button", name="and 1 more").click()
    banner = box(pg, BANNER)
    laneb = lane.bounding_box()
    assert banner["x"] + banner["width"] <= laneb["x"] + laneb["width"] + 1                                               # inside its lane
    assert [h.text_content().strip() for h in pg.locator(".mp-lane__head .ork-label").all()] == ["Art and icons", "Sound", "Music", "Clips"]
