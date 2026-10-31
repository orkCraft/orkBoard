"""Spec 117 part F, System as a network (docs/specs/117-each-lens-a-games-shape.md §5, decisions §195), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with a mouse), against the reach kit's stub host
(`ReachHost`, tests/test_reach_browser.py) with a System of three containers in a row (`system_of`, tests/test_owners_day_desktop_browser.py: c0 → c1 → c2, wider than the pane, so the fit scales it).

A link whose pair of containers is in the reach's `links` (a goal under the pointer in the hand, on System) draws its arrow and its name in the goal's element (`is-reach`); a reach that does not cross a link leaves it as it was (ink,
no class), one on another map or with no links lights none, and leaving the goal puts everything back; the fit's scale keeps the arrows' ends on the columns' tops and the names on their lanes. Screenshots to the directory
ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import system  # noqa: E402
from tests.test_owners_day_desktop_browser import system_of  # noqa: E402
from tests.test_reach_browser import RESULTS, SEAT, TIMER, ReachHost, aim, leave, start  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser

A, B, C = "c0/p0.ts", "c1/p0.ts", "c2/p0.ts"


class NetHost(ReachHost):
    """The reach host with a System of three containers, and three goals reaching it as each case needs: SEAT (ice) crosses c0 → c1, RESULTS (dust) c1 → c2, TIMER (meadow) says its links on another map."""

    def __init__(self):
        super().__init__()
        self.reach[("tech", SEAT)] = {"map": "system", "element": "ice", "state": "ok", "near": {A: 0, B: 1}, "guard": {B: True}, "links": [["c0", "c1"]]}
        self.reach[("tech", RESULTS)] = {"map": "system", "element": "dust", "state": "ok", "near": {B: 0, C: 1}, "guard": {C: False}, "links": [["c1", "c2"]]}
        self.reach[("tech", TIMER)] = {"map": "game-design", "element": "meadow", "state": "ok", "near": {A: 0}, "links": [["c0", "c1"]]}

    def handle(self, name, a):
        if name == "ideas.system":
            self.log.append((name, a))
            return copy.deepcopy(system_of(3))
        return super().handle(name, a)


@pytest.fixture(params=narrow.WIDTHS)
def net(gui, request):
    """The window at one of the two widths on Tech's System: `(page, host, width)`; the page's errors are asserted at the end."""
    pg, host, errors = start(gui, request.param, NetHost())
    system(pg)
    pg.wait_for_function("() => document.querySelectorAll('.arch-link').length === 2", timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def paint(pg, token, prop="color"):
    """What a token computes to as a `prop` (the elements' colours are orkUI's tokens)."""
    return pg.evaluate("([t, p]) => { const e = document.createElement('i'); e.style[p] = `var(${t})`; document.body.append(e); const c = getComputedStyle(e)[p]; e.remove(); return c; }", [token, prop])


def css(el, prop):
    return el.evaluate("(e, p) => getComputedStyle(e)[p]", prop)


def arrow(pg, key):
    return pg.locator(f'.arena-arrow[data-edge="{key}"]')


def name(pg, key):
    return pg.locator(f'.arch-link[data-link="{key}"]')


def lit_keys(pg):
    """`[arrow keys, name keys]` carrying `is-reach` now."""
    return pg.evaluate("() => [[...document.querySelectorAll('.arena-arrow.is-reach')].map((e) => e.dataset.edge), [...document.querySelectorAll('.arch-link.is-reach')].map((e) => e.dataset.link)]")


def lit(pg, key):
    pg.wait_for_function("(k) => !!document.querySelector(`.arena-arrow.is-reach[data-edge='${k}']`) && !!document.querySelector(`.arch-link.is-reach[data-link='${k}']`)", arg=key, timeout=WAIT_MS)


def test_a_reach_crossing_a_link_draws_its_arrow_and_its_name_in_the_goals_element_and_leaving_puts_them_back(net):
    pg, host, w = net
    ink = paint(pg, "--ork-ink")
    assert lit_keys(pg) == [[], []] and css(arrow(pg, "c0>c1").locator("polyline"), "stroke") == ink
    aim(pg, SEAT, w)
    lit(pg, "c0>c1")
    assert host.asked("ideas.reach") == [{"party": "tech", "slug": SEAT}]
    assert lit_keys(pg) == [["c0>c1"], ["c0>c1"]], "only the link the reach crosses"
    ice = paint(pg, "--ork-elem-ice")
    line, head = arrow(pg, "c0>c1").locator("polyline"), arrow(pg, "c0>c1").locator("polygon")
    assert css(line, "stroke") == ice and css(head, "fill") == ice, "the arrow in the goal's element, ice"
    assert css(name(pg, "c0>c1"), "color") == ice and css(name(pg, "c0>c1"), "borderTopColor") == ice, "and its name"
    assert name(pg, "c0>c1").get_attribute("aria-pressed") == "false" and name(pg, "c0>c1").inner_text().startswith("HTTP: 1 route"), "still the link's own button, its words unchanged"
    other = name(pg, "c1>c2")
    assert css(arrow(pg, "c1>c2").locator("polyline"), "stroke") == ink and css(other, "color") == ink and css(other, "borderTopColor") != ice, "the others as they were"
    assert float(css(line, "strokeWidth").removesuffix("px")) > float(css(arrow(pg, "c1>c2").locator("polyline"), "strokeWidth").removesuffix("px")), "a little heavier than the rest"
    shot(pg, f"reach-system-link-{w}.png")
    leave(pg)
    pg.wait_for_function("() => document.querySelectorAll('.is-reach').length === 0", timeout=WAIT_MS)
    assert css(arrow(pg, "c0>c1").locator("polyline"), "stroke") == ink and css(name(pg, "c0>c1"), "color") == ink


def test_a_reach_that_crosses_another_link_lights_that_one_and_one_that_crosses_none_or_is_on_another_map_leaves_them_all(net):
    pg, host, w = net
    aim(pg, RESULTS, w)
    lit(pg, "c1>c2")
    assert lit_keys(pg) == [["c1>c2"], ["c1>c2"]]
    assert css(arrow(pg, "c1>c2").locator("polyline"), "stroke") == paint(pg, "--ork-elem-dust"), "dust, this goal's element"
    leave(pg)
    pg.wait_for_function("() => document.querySelectorAll('.is-reach').length === 0", timeout=WAIT_MS)
    aim(pg, TIMER, w)                                                                                       # its answer is for another map: the links are not System's
    pg.wait_for_function("() => document.querySelectorAll('.rc-line').length === 1", timeout=WAIT_MS)
    assert pg.locator(".rc-line").get_attribute("data-goal") == TIMER and lit_keys(pg) == [[], []]
    leave(pg)
    host.reach[("tech", SEAT)]["links"] = []                                                                # a reach that crosses nothing
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    aim(pg, SEAT, w)
    pg.wait_for_function("() => document.querySelectorAll('.rc-edge').length === 2", timeout=WAIT_MS)
    assert lit_keys(pg) == [[], []] and pg.locator(".arch-link").count() == 2, "the parts are lit, the links left as they are"
    shot(pg, f"reach-system-nolink-{w}.png")


def test_the_fits_scale_keeps_the_lit_arrows_ends_on_the_columns_and_its_name_on_its_lane(net):
    pg, host, w = net
    f = float(pg.locator(".arch").get_attribute("data-scale"))
    assert 0.5 <= f < 1, f"three columns of three cards are wider than the pane, so the fit scales them ({f})"
    aim(pg, SEAT, w)
    lit(pg, "c0>c1")
    pg.wait_for_timeout(300)                                                                                # the arrows are drawn in four steps (arena.css `arena-draw`): measured when they are done
    for key in ("c0>c1", "c1>c2"):                                                                          # the lit one and the other: ends where the fit had them
        head = arrow(pg, key).locator("polygon").bounding_box()
        xs, lane = pg.evaluate("""([k, f]) => { const p = document.querySelector(`.arena-arrow[data-edge='${k}'] polyline`).getAttribute('points').split(' ').map((s) => s.split(',').map(Number)), o = document.querySelector('.arch').getBoundingClientRect();
          return [[o.left + p[1][0] * f, o.left + p[2][0] * f], o.top + p[1][1] * f]; }""", [key, f])                    # the lane's ends and its height, from the arrow's own points (a stroke widens a box)
        col = pg.locator(f'.arch-col[data-container="{key.split(">")[1]}"]').bounding_box()
        assert col["x"] - 1 <= head["x"] + head["width"] / 2 <= col["x"] + col["width"] + 1, (key, head, col)
        assert abs((head["y"] + head["height"]) - col["y"]) <= 4, (key, head, col)
        btn = name(pg, key).bounding_box()
        assert abs((btn["x"] + btn["width"] / 2) - sum(xs) / 2) <= 1.5, ("the name in the middle of its lane", key, btn, xs)
        assert abs((btn["y"] + btn["height"] / 2) - lane) <= 1.5, (key, btn, lane)
    pg.locator('.arch-zoom [data-fit="full"]').click()                                                      # at 100 % the same holds
    pg.wait_for_function("() => document.querySelector('.arch').dataset.scale === '1.000'", timeout=WAIT_MS)
    aim(pg, SEAT, w)
    lit(pg, "c0>c1")
    pg.wait_for_timeout(300)
    head, col = arrow(pg, "c0>c1").locator("polygon").bounding_box(), pg.locator('.arch-col[data-container="c1"]').bounding_box()
    assert abs((head["y"] + head["height"]) - col["y"]) <= 4 and col["x"] - 1 <= head["x"] + head["width"] / 2 <= col["x"] + col["width"] + 1
