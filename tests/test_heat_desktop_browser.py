"""Spec 165 part H, heat's squares on every map (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.1, §183.5), in a real browser at 1280 x 800, the host faked.

`ideas.heat {party}` answers `{party, map, heat: [{on, kind}]}`: on Tech's System and on Design's screens each part with hints wears at most three hollow squares (the first three kinds in the hints' order),
each `role="img"` saying its kind in words in its label and title, beside a concern's mark and not over it; a press on a square falls through to the card; the page asks again when the Board's rev moves."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import INDEX, LOBBY, ROOMS, ConcernHost  # noqa: E402
from tests.test_screens_desktop_browser import ScreensHost  # noqa: E402
from tests.test_table_desktop_browser import tab, watch  # noqa: E402

pytestmark = pytest.mark.browser

SYS_HEAT = [{"on": LOBBY, "kind": "fan_in"}, {"on": LOBBY, "kind": "unstable"}, {"on": LOBBY, "kind": "fan_in"}, {"on": LOBBY, "kind": "hotspot"}, {"on": LOBBY, "kind": "big"},
            {"on": ROOMS, "kind": "untested_churn"}, {"on": "", "kind": "cycle"}]
SCR_HEAT = [{"on": "join", "kind": "no_picture"}, {"on": "host", "kind": "no_states"}, {"on": "host", "kind": "a11y"}]


class HeatMixin:
    def heat_setup(self, heat):
        self.heat = heat
        self.heat_asked = 0

    def handle(self, name, a):
        if name == "ideas.heat":
            self.log.append((name, a))
            self.heat_asked += 1
            return {"party": a["party"], "map": "", "heat": [dict(h) for h in self.heat.get(a["party"], [])]}
        return super().handle(name, a)


class TechHost(HeatMixin, ConcernHost):
    def __init__(self):
        super().__init__()
        self.heat_setup({"tech": SYS_HEAT})


class DesignHost(HeatMixin, ScreensHost):
    def __init__(self):
        super().__init__()
        self.heat_setup({"design": SCR_HEAT})


def open_tab(gui, host, slug, wait):
    server, browser = gui
    errors: list[str] = []
    pg = browser.new_context(**narrow.WIDE).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    tab(pg, slug).click()
    pg.locator(wait).wait_for(timeout=WAIT_MS)
    return pg, errors


def squares(pg, pid):
    return pg.locator(f'.ht-slot[data-ht-for="{pid}"] .ht-sq')


def test_system_parts_wear_at_most_three_squares_each_saying_its_kind_in_words(gui):
    host = TechHost()
    pg, errors = open_tab(gui, host, "tech", ".table-sys .sys[data-state=shown]")
    sq = squares(pg, LOBBY)
    sq.first.wait_for(timeout=WAIT_MS)
    assert sq.count() == 3                                                         # four kinds, one twice: the first three kinds, in the hints' order
    assert [s.get_attribute("data-kind") for s in sq.all()] == ["fan_in", "unstable", "hotspot"]
    for s in sq.all():
        assert s.get_attribute("role") == "img"
        assert s.get_attribute("aria-label") == s.get_attribute("title") and s.get_attribute("aria-label") not in ("", s.get_attribute("data-kind"))
    assert sq.first.get_attribute("aria-label") == "used by many parts"
    assert squares(pg, ROOMS).count() == 1
    assert squares(pg, INDEX).count() == 0                                         # a part with no hint: no slot
    # the squares are beside the concern's mark, not over it
    pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"] .cn-mark').wait_for(timeout=WAIT_MS)
    a, b = pg.locator(f'.ht-slot[data-ht-for="{LOBBY}"]').bounding_box(), pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"]').bounding_box()
    assert a["x"] + a["width"] <= b["x"] + 0.5
    assert pg.locator(f'.ht-slot[data-ht-for="{LOBBY}"]').evaluate("e => getComputedStyle(e).pointerEvents") == "none"
    for pid in (LOBBY, ROOMS):                                                       # clear of the card's name (spec 165 K)
        slot = pg.locator(f'.ht-slot[data-ht-for="{pid}"]').bounding_box()
        name = pg.locator(f'[data-pick-id="{pid}"] .sys-part__name').first.bounding_box()
        assert slot["x"] >= name["x"] + name["width"] or slot["y"] >= name["y"] + name["height"] or slot["y"] + slot["height"] <= name["y"], (pid, slot, name)
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_a_screen_wears_its_squares_and_asks_again_when_the_board_moves(gui):
    host = DesignHost()
    pg, errors = open_tab(gui, host, "design", ".scr-map[data-state='read']")
    squares(pg, "host").first.wait_for(timeout=WAIT_MS)
    assert squares(pg, "host").count() == 2 and squares(pg, "join").count() == 1
    asked = host.heat_asked
    host.heat = {"design": [{"on": "round", "kind": "dead_end"}]}
    host.push()
    pg.wait_for_function("() => document.querySelectorAll('.ht-slot[data-ht-for=\"round\"]').length === 1", timeout=WAIT_MS)
    assert host.heat_asked > asked and squares(pg, "host").count() == 0
    assert not errors, "\n".join(errors)
    pg.context.close()


def test_a_host_without_heat_leaves_the_map_bare(gui):
    host = TechHost()
    host.heat = {}
    pg, errors = open_tab(gui, host, "tech", ".table-sys .sys[data-state=shown]")
    pg.wait_for_timeout(300)
    assert pg.locator(".ht-sq").count() == 0
    assert not errors, "\n".join(errors)
    pg.context.close()
