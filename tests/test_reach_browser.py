"""Spec 117 part E, the kit (docs/specs/117-each-lens-a-games-shape.md §4, decisions §195; mockup docs/mockups/tech-reach/), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with a mouse),
against the concerns' stub host (`ConcernHost`: Game design with its loop, Tech led by the Architect with its System, Art, Release, Marketing) that also answers part A's commands as the contract says —
`ideas.heat {party}` → `{map, parts: {part id: [{kind, aspect, words}]}}`, `ideas.reach {party, slug}` → `{map, slug, element, state, near: {id: 0 | 1 | 2}, guard?, links?}` — and has goals' cards in the hand.

Heat: a hollow square for each kind of hint on a part's card, in the concern's slot before its mark (the title the hints' words, a line each), `data-heat` on the card, the slot gone with the heat. Reach: the hand's card of a goal under the
pointer (or focused) lights the open map's cards — the touched card a solid edge in the goal's element with its rune, what it reaches a dashed edge, then a dotted one, the others dimmed — and leaving clears them; a picked goal does the same
and stays; the edge is a child of the card, inset (the notch would clip an outline); System's reached parts say whether a test checks them; the strip's line in each state (*changes 1 part · reaches 2 through what uses them · 1 with no test ·
through the hotspot …*, *what it reaches is known once its spec says what will change*, *changes nothing on System*); the answer kept per goal and revision; the edges come in nearest first, none under reduced motion; a host without the
commands draws nothing and throws nothing; no sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import ConcernHost, go, loop, start, system  # noqa: E402
from tests.test_hand_desktop_browser import need  # noqa: E402
from tests.test_picking_desktop_browser import part  # noqa: E402
from tests.test_table_desktop_browser import shot, wide  # noqa: E402

pytestmark = pytest.mark.browser

INDEX, LOBBY, ROOMS, NET = "server/index.ts", "server/lobby.ts", "server/rooms.ts", "client/net.ts"
SEAT, RESULTS, TIMER = "seat", "results", "timer"                       # Tech's goals (ice, dust) and Game design's (meadow): the cards of the hand

HEAT = {"tech": {LOBBY: [{"kind": "hotspot", "aspect": "hotspots", "words": "Changed 14 times in 30 days, holds lobby.ts of 610 lines"},
                         {"kind": "untested_churn", "aspect": "testability", "words": "Changed 9 times in 30 days, no test"}],
                 INDEX: [{"kind": "hotspot", "aspect": "hotspots", "words": "Changed 11 times in 30 days"}],
                 NET: [{"kind": "big", "aspect": "modularity", "words": "Holds a file of 800 lines or more"}]},
        "game": {"hold-the-tower": [{"kind": "no_source", "aspect": "economy", "words": "Nothing in the loop pays for it"}],
                 "cur:gems": [{"kind": "pile_up", "aspect": "economy", "words": "Gems is only earned"}, {"kind": "no_sink", "aspect": "economy", "words": "Nothing takes Gems"}]}}
REACH = {("tech", SEAT): {"map": "system", "element": "ice", "state": "ok", "near": {LOBBY: 0, INDEX: 1, NET: 2}, "guard": {INDEX: True, NET: False}, "links": [["client", "server"]]},
         ("tech", RESULTS): {"map": "system", "element": "dust", "state": "no_will", "near": {}, "guard": {}, "links": []},
         ("tech", TIMER): {"map": "system", "element": "meadow", "state": "none", "near": {}, "guard": {}, "links": []},
         ("game", SEAT): {"map": "game-design", "element": "ice", "state": "ok", "near": {"hold-the-tower": 0, "score-the-round": 1, "cur:coins": 1, "spend-the-coins": 2}}}


class ReachHost(ConcernHost):
    """The concerns' host with goals' cards in the hand (a failure of each of three goals) that answers the heat and the reach; `bare`: a host that does not know the two commands."""

    def __init__(self, bare=False):
        super().__init__()
        self.bare = bare
        self.heat = copy.deepcopy(HEAT)
        self.reach = copy.deepcopy(REACH)
        self.needs = [need("failed", "tech", SEAT, "Keep the seat when a socket reconnects", "It failed", at="2026-10-20T08:00:00"),
                      need("failed", "tech", RESULTS, "Results screen with the round's best answer", "It failed", at="2026-10-20T08:10:00"),
                      need("failed", "game", TIMER, "Round timer shows on every phone", "It failed", at="2026-10-20T08:20:00")]

    def handle(self, name, a):
        if name in ("ideas.heat", "ideas.reach") and not self.bare:
            self.log.append((name, a))
            if name == "ideas.heat":
                return {"map": {"tech": "system", "game": "game-design"}.get(a["party"], ""), "parts": copy.deepcopy(self.heat.get(a["party"], {}))}
            slug = a["slug"]
            return copy.deepcopy(self.reach.get((a["party"], slug)) or {"map": "game-design", "element": "dust", "state": "none", "near": {}}) | {"slug": slug}
        return super().handle(name, a)

    def asked(self, name):
        return [a for n, a in self.log if n == name]


@pytest.fixture(params=narrow.WIDTHS)
def desk(gui, request):
    """The window at one of the two widths against a ReachHost: `(page, host, width)`; the page's errors are asserted at the end."""
    pg, host, errors = start(gui, request.param, ReachHost())
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def card(pg, goal):
    """The goal's card in the hand."""
    return pg.locator(f'.hand-card[data-goal="{goal}"]')


def aim(pg, goal, w):
    """The pointer on the goal's card in the hand (at the narrow width the card is pointed at all the same: a mouse)."""
    c = card(pg, goal)
    c.wait_for(timeout=WAIT_MS)
    c.scroll_into_view_if_needed()
    c.hover(position={"x": 8, "y": 24})                                                                     # a card that lies behind another shows its left edge


def leave(pg):
    pg.mouse.move(3, 3)


def edges(pg):
    """`{part id: near}` of the edges drawn now."""
    return pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.rc-edge')].map((e) => [e.parentElement.closest('[data-pick-id]')?.dataset.pickId || e.parentElement.dataset.pickId || e.parentElement.parentElement.dataset.pickId, Number(e.dataset.near)]))")


def lit(pg, n):
    """Waits for `n` edges."""
    pg.wait_for_function("(n) => document.querySelectorAll('.rc-edge').length === n", arg=n, timeout=WAIT_MS)


def line(pg):
    return " ".join(pg.locator(".rc-line").inner_text().split())


def css(el, prop):
    return el.evaluate("(e, p) => getComputedStyle(e)[p]", prop)


# -- heat ----------------------------------------------------------------------------------------------------------------------------------------

def test_heat_is_a_hollow_square_for_each_kind_of_hint_on_a_part_in_the_concerns_slot_before_its_mark(desk):
    pg, host, w = desk
    system(pg)
    pg.locator(".cn-heat").first.wait_for(timeout=WAIT_MS)
    assert host.asked("ideas.heat")[0] == {"party": "tech"}
    lobby = part(pg, LOBBY)
    assert lobby.get_attribute("data-heat") == "hotspot untested_churn" and part(pg, ROOMS).get_attribute("data-heat") is None
    squares = pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"] .cn-heat')
    assert squares.locator(".cn-hint").count() == 2 and squares.get_attribute("title") == "Changed 14 times in 30 days, holds lobby.ts of 610 lines\nChanged 9 times in 30 days, no test"
    assert squares.locator(".cn-hint").first.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [6, 6], "concerns.css's hollow square, 6 × 6 (the System's scaled box draws it smaller)"
    assert squares.locator(".cn-hint").first.evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
    order = pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"]').evaluate("e => [...e.children].map((c) => c.className)")
    assert order == ["cn-heat", "cn-slot__m"], "the squares before the concern's mark"
    assert pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"] .cn-mark[data-level="alert"]').count() == 1, "the leader's alert is still there"
    only = pg.locator(f'.cn-slot[data-cn-for="{INDEX}"]')
    assert only.locator(".cn-heat .cn-hint").count() == 1 and only.locator(".cn-slot__m").count() == 0 and part(pg, INDEX).get_attribute("data-heat") == "hotspot", "the slot is made for the heat alone"
    assert pg.locator(".cn-slot button, button .cn-slot").count() == 0, "a button holds no button"
    shot(pg, f"reach-heat-system-{w}.png")
    host.heat["tech"] = {ROOMS: [{"kind": "big", "aspect": "modularity", "words": "Holds a file of 800 lines or more"}]}              # the hints changed: the Board moves, the page reads again
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_function("() => !document.querySelector('.cn-slot[data-cn-for=\"server/index.ts\"]')", timeout=WAIT_MS)
    assert part(pg, ROOMS).get_attribute("data-heat") == "big" and part(pg, INDEX).get_attribute("data-heat") is None and part(pg, LOBBY).get_attribute("data-heat") is None
    assert pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"] .cn-heat').count() == 0 and pg.locator(f'.cn-slot[data-cn-for="{LOBBY}"] .cn-mark').count() == 1, "the mark stays when the heat goes"
    assert len(host.asked("ideas.heat")) >= 2


def test_a_step_of_the_loop_and_a_currency_take_heat_too(desk):
    pg, host, w = desk
    loop(pg)
    hold, gems = pg.locator('.mp-card[data-id="hold-the-tower"]'), pg.locator('.mp-card[data-id="cur:gems"]')
    gems.locator(".cn-heat").wait_for(timeout=WAIT_MS)
    assert host.asked("ideas.heat")[0] == {"party": "game"}
    assert hold.get_attribute("data-heat") == "no_source" and gems.get_attribute("data-heat") == "pile_up no_sink"
    assert gems.locator(".cn-heat .cn-hint").count() == 2 and hold.locator(".cn-heat .cn-hint").count() == 1
    assert hold.locator(".cn-heat + .cn-slot__m .cn-mark").count() == 1, "beside the alert on the step"
    shot(pg, f"reach-heat-loop-{w}.png")


def test_a_host_without_the_commands_draws_no_heat_and_no_reach_and_throws_nothing(gui):
    pg, host, errors = start(gui, "wide", ReachHost(bare=True))
    system(pg)
    pg.locator(".cn-mark").first.wait_for(timeout=WAIT_MS)
    card(pg, SEAT).hover(force=True)
    pg.wait_for_timeout(300)
    assert pg.locator(".cn-heat, .rc-edge, .rc-line, [data-reach-dim], [data-heat]").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- reach: the hand's card under the pointer --------------------------------------------------------------------------------------------------

def test_a_goals_card_under_the_pointer_lights_the_cards_it_reaches_solid_dashed_dotted_and_dims_the_others_and_leaving_clears_them(desk):
    pg, host, w = desk
    system(pg)
    pg.locator(".cn-heat").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".rc-edge").count() == 0
    aim(pg, SEAT, w)
    lit(pg, 3)
    assert host.asked("ideas.reach") == [{"party": "tech", "slug": SEAT}]
    assert edges(pg) == {LOBBY: 0, INDEX: 1, NET: 2}
    edge = lambda p, n: part(pg, p).locator(f'.rc-edge[data-near="{n}"]')  # noqa: E731
    assert [css(edge(LOBBY, 0), "borderTopStyle"), css(edge(INDEX, 1), "borderTopStyle"), css(edge(NET, 2), "borderTopStyle")] == ["solid", "dashed", "dotted"]
    ice = pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-elem-ice)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")
    assert all(css(edge(p, n), "borderTopColor") == ice for p, n in ((LOBBY, 0), (INDEX, 1), (NET, 2))), "the goal's element, ice"
    assert all(css(edge(p, n), "borderTopWidth") == "2px" for p, n in ((LOBBY, 0), (INDEX, 1), (NET, 2)))
    assert part(pg, LOBBY).locator(".rc-edge > .ork-elem.ice").count() == 1 and part(pg, INDEX).locator(".rc-edge > .ork-elem").count() == 0, "the rune on the touched card only"
    assert edge(LOBBY, 0).evaluate("e => [e.offsetWidth, e.offsetHeight]") == part(pg, LOBBY).evaluate("e => [e.offsetWidth, e.offsetHeight]"), "inset: the card's own size, not round it"
    assert edge(LOBBY, 0).evaluate("e => e.parentElement.matches('.sys-part')"), "a child of the card"
    assert part(pg, ROOMS).get_attribute("data-reach-dim") == "" and css(part(pg, ROOMS), "opacity") == "0.38"
    assert all(part(pg, p).get_attribute("data-reach-dim") is None for p in (LOBBY, INDEX, NET))
    assert pg.locator("[data-reach-dim]").count() == 1
    shot(pg, f"reach-system-{w}.png")
    leave(pg)
    lit(pg, 0)
    pg.wait_for_function("() => document.querySelectorAll('[data-reach-dim]').length === 0", timeout=WAIT_MS)
    assert pg.locator(".rc-line").count() == 0


def test_the_guard_on_a_reached_part_of_the_system_the_shield_or_no_test(desk):
    pg, host, w = desk
    system(pg)
    aim(pg, SEAT, w)
    lit(pg, 3)
    shield = part(pg, INDEX).locator(".rc-guard")
    assert shield.get_attribute("title") == "A test checks it" and shield.locator(".ork-sign.shield").count() == 1 and shield.get_attribute("aria-label") == "A test checks it"
    none = part(pg, NET).locator(".rc-guard")
    assert none.inner_text() == "no test" and none.get_attribute("class") == "rc-guard is-none"
    assert part(pg, LOBBY).locator(".rc-guard").count() == 0, "the touched part has its rune, not a guard"
    box, c = shield.bounding_box(), part(pg, INDEX).bounding_box()
    assert box["x"] - c["x"] <= 12 and box["y"] - c["y"] <= 12, "at the card's top left"
    leave(pg)
    lit(pg, 0)


def test_the_same_goal_again_is_kept_and_a_new_revision_asks_again(desk):
    pg, host, w = desk
    system(pg)
    for _ in range(2):
        aim(pg, SEAT, w)
        lit(pg, 3)
        leave(pg)
        lit(pg, 0)
    assert len(host.asked("ideas.reach")) == 1, "kept per party, goal and revision of the Board"
    host.reach[("tech", SEAT)]["near"] = {LOBBY: 0}
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_timeout(200)
    aim(pg, SEAT, w)
    lit(pg, 1)
    assert len(host.asked("ideas.reach")) == 2 and edges(pg) == {LOBBY: 0}
    leave(pg)


def test_the_cards_of_another_map_light_the_same_way_with_no_guard(desk):
    pg, host, w = desk
    loop(pg)
    aim(pg, SEAT, w)
    lit(pg, 4)
    assert host.asked("ideas.reach") == [{"party": "game", "slug": SEAT}]
    cards = lambda n: pg.locator(f'.mp-card:has(> .rc-edge[data-near="{n}"])')  # noqa: E731
    assert cards(0).get_attribute("data-id") == "hold-the-tower" and cards(1).count() == 2 and cards(2).get_attribute("data-id") == "spend-the-coins"
    assert pg.locator(".rc-guard").count() == 0 and pg.locator(".mp-card .rc-edge > .ork-elem.ice").count() == 1
    assert css(cards(1).first.locator("> .rc-edge"), "borderTopStyle") == "dashed" and css(cards(2).locator("> .rc-edge"), "borderTopStyle") == "dotted"
    assert pg.locator(".mp-card[data-reach-dim]").count() == pg.locator(".mp-card").count() - 4
    assert cards(0).locator("> .rc-edge").evaluate("e => [e.offsetWidth, e.offsetHeight]") == cards(0).evaluate("e => [e.offsetWidth, e.offsetHeight]"), "inset in the card"
    shot(pg, f"reach-loop-{w}.png")
    leave(pg)
    lit(pg, 0)


def test_the_focus_on_a_goals_card_lights_the_reach_and_the_blur_clears_it(desk):
    pg, host, w = desk
    system(pg)
    card(pg, SEAT).wait_for(timeout=WAIT_MS)
    card(pg, SEAT).focus()
    lit(pg, 3)
    pg.evaluate("() => document.activeElement.blur()")
    lit(pg, 0)


def test_a_picked_goal_does_the_same_and_stays_when_the_pointer_leaves(desk):
    pg, host, w = desk
    system(pg)
    card(pg, SEAT).wait_for(timeout=WAIT_MS)
    card(pg, SEAT).scroll_into_view_if_needed()
    card(pg, SEAT).click(position={"x": 8, "y": 24})                                                        # a press on a goal's card picks the goal
    lit(pg, 3)
    leave(pg)
    pg.evaluate("() => document.activeElement.blur()")
    pg.wait_for_timeout(250)
    assert edges(pg) == {LOBBY: 0, INDEX: 1, NET: 2}, "the picked goal's reach stays"
    assert line(pg).startswith("Keep the seat when a socket reconnects changes 1 part")
    go(pg, "game")                                                                                          # another tab: the picked goal's reach on its map
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    lit(pg, 4)
    assert host.asked("ideas.reach")[-1] == {"party": "game", "slug": SEAT}


# -- the strip's line --------------------------------------------------------------------------------------------------------------------------

def test_the_strips_line_in_each_state(desk):
    pg, host, w = desk
    system(pg)
    pg.locator(".cn-heat").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".rc-line").count() == 0, "nothing while no goal is shown"
    aim(pg, SEAT, w)
    pg.locator(".rc-line").wait_for(timeout=WAIT_MS)
    assert line(pg) == "Keep the seat when a socket reconnects changes 1 part · reaches 2 through what uses them · 1 with no test · through the hotspot server/index.ts"
    assert pg.locator(".rc-line > .ork-elem.ice").count() == 1 and pg.locator(".rc-line > :first-child").get_attribute("class").startswith("ork-elem ice"), "its element's rune first"
    assert pg.locator(".rc-line").evaluate("e => e.parentElement.classList.contains('cn-strip')"), "in the strip, under the aspects"
    shot(pg, f"reach-line-{w}.png")
    leave(pg)
    pg.locator(".rc-line").wait_for(state="detached", timeout=WAIT_MS)
    aim(pg, RESULTS, w)
    pg.locator('.rc-line[data-state="no_will"]').wait_for(timeout=WAIT_MS)
    assert line(pg) == "Results screen with the round's best answer: what it reaches is known once its spec says what will change"
    assert pg.locator(".rc-edge").count() == 0 and pg.locator("[data-reach-dim]").count() == 0, "a goal that reaches nothing dims nothing"
    leave(pg)
    pg.locator(".rc-line").wait_for(state="detached", timeout=WAIT_MS)
    aim(pg, TIMER, w)
    pg.locator('.rc-line[data-state="none"]').wait_for(timeout=WAIT_MS)
    assert line(pg) == "Round timer shows on every phone changes nothing on System"
    leave(pg)
    pg.locator(".rc-line").wait_for(state="detached", timeout=WAIT_MS)
    host.reach[("tech", SEAT)]["near"] = {LOBBY: 0, INDEX: 0}                                              # two parts changed, none reached
    host.reach[("tech", SEAT)]["guard"] = {}
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_timeout(200)
    aim(pg, SEAT, w)
    pg.locator(".rc-line").wait_for(timeout=WAIT_MS)
    assert line(pg) == "Keep the seat when a socket reconnects changes 2 parts"
    leave(pg)


def test_the_loops_line_says_what_its_relation_goes_through(desk):
    pg, host, w = desk
    loop(pg)
    aim(pg, SEAT, w)
    pg.locator(".rc-line").wait_for(timeout=WAIT_MS)
    assert line(pg) == "Keep the seat when a socket reconnects changes 1 part · reaches 3 through what their currencies feed"
    leave(pg)


# -- motion ------------------------------------------------------------------------------------------------------------------------------------

def test_the_edges_come_in_nearest_first_and_none_under_reduced_motion(gui):
    pg, host, errors = start(gui, "wide", ReachHost())
    system(pg)
    aim(pg, SEAT, "wide")
    lit(pg, 3)
    seen = pg.evaluate("() => [...document.querySelectorAll('.rc-edge')].map((e) => [Number(e.dataset.near), getComputedStyle(e).animationName, getComputedStyle(e).animationDelay, getComputedStyle(e).animationDuration])")
    assert sorted(seen) == [[0, "rc-in", "0s", "0.18s"], [1, "rc-in", "0.12s", "0.18s"], [2, "rc-in", "0.24s", "0.18s"]], "orkUI's motion tokens, 120 ms apart"
    pg.context.close()
    assert not errors, "\n".join(errors)
    pg, host, errors = start(gui, "wide", ReachHost(), reduced_motion="reduce")
    system(pg)
    aim(pg, SEAT, "wide")
    lit(pg, 3)
    assert {s for s in pg.evaluate("() => [...document.querySelectorAll('.rc-edge')].map((e) => getComputedStyle(e).animationName)")} == {"none"}
    pg.context.close()
    assert not errors, "\n".join(errors)
