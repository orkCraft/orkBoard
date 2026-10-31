"""Spec 117 part G, Design's screens as rooms (docs/specs/117-each-lens-a-games-shape.md §6, decisions §195), in a real browser at both widths (`tests/narrow.py`) against the screens' stub host with a flow of its own.

A screen's card has a door in its left side for each screen that leads to it and one in its right for each it leads to (a link back, or within a step, counts; a link to itself and a screen twice do not): a gap in the card's frame, 10 px tall,
at most three a side, the others *and n more* in the side's title (*Leads here: …*, *Leads to: …*); a side with none is a wall, 3 px of ink: a screen nothing leads to (on its left), a dead end and the flow's end (on its right); the entry's
left side has a door from outside with a small chevron (*Where people come in*). All of it lies inside the card's box, under the reach edge the kit paints; the walls agree with `dead_end` and `loose` (realm/map_signals.py). The arrows and
the narrow width's chips are as they were; no sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_screens_desktop_browser import ScreensHost, shot, start  # noqa: E402
from tests.test_table_desktop_browser import watch  # noqa: E402,F401

pytestmark = pytest.mark.browser

NAMES = {"home": "Welcome", "hub": "Hub", "a": "Alpha", "b": "Bravo", "c": "Charlie", "d": "Delta", "dead": "Dead", "end": "Finish", "stray": "Stray"}
SCREENS = [{"id": i, "name": n, "path": f"/{i}", "file": f"src/{i}.tsx"} for i, n in NAMES.items()]
LINKS = [("home", "hub"), ("hub", "a"), ("hub", "b"), ("hub", "c"), ("hub", "d"), ("hub", "dead"), ("a", "hub"), ("b", "hub"), ("c", "hub"), ("d", "hub"), ("a", "end"), ("a", "home"), ("a", "a"), ("b", "hub")]
STEPS = [["home"], ["hub"], ["a", "b", "c", "d", "dead"], ["end"], ["stray"]]


class RoomsHost(ScreensHost):
    """The screens' stub with a flow that has a hub (five screens each way), a back link to the entry, a dead end, the end of the flow and a screen nothing leads to."""

    def handle(self, name, a):
        if name == "ideas.screens":
            self.log.append((name, a))
            return {"head": "a" * 40, "source": "react-router", "entry": "home", "more": 0, "loose": ["stray"], "screens": [dict(s) for s in SCREENS],
                    "links": [{"from": f, "to": t} for f, t in LINKS], "steps": [list(r) for r in STEPS], "segments": []}
        return super().handle(name, a)


@pytest.fixture(params=narrow.WIDTHS)
def rooms(gui, request, monkeypatch):
    import tests.test_screens_desktop_browser as base
    monkeypatch.setattr(base, "ScreensHost", RoomsHost)
    errors: list[str] = []
    pg, host = start(gui, request.param, errors)
    pg.locator(".scr-map[data-state='read']").wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def side(pg, sid, which):
    return pg.locator(f'.scr-card[data-screen="{sid}"] .scr-side[data-side="{which}"]')


def doors(pg, sid, which):
    return side(pg, sid, which).locator(".scr-door").count()


def walled(pg, sid, which):
    return side(pg, sid, which).get_attribute("class").split().count("is-wall") == 1


def test_a_door_for_each_screen_that_leads_to_a_card_on_its_left_and_one_for_each_it_leads_to_on_its_right(rooms):
    pg, host, w = rooms
    assert [doors(pg, s, "in") for s in ("hub", "a", "b", "dead", "end")] == [3, 1, 1, 1, 1]
    assert [doors(pg, s, "out") for s in ("home", "hub", "a", "b", "c")] == [1, 3, 3, 1, 1]                               # a link back counts; a link to itself and a link twice do not (Bravo to Hub is listed twice)
    assert side(pg, "a", "in").get_attribute("title") == "Leads here: Hub"
    assert side(pg, "a", "out").get_attribute("title") == "Leads to: Welcome, Hub, Finish"    # the flow's order: Welcome is step one
    assert side(pg, "home", "out").get_attribute("title") == "Leads to: Hub"
    shot(pg, f"rooms-{w}.png")


def test_more_than_three_doors_a_side_say_and_n_more_in_the_sides_title(rooms):
    pg, host, w = rooms
    assert side(pg, "hub", "in").get_attribute("title") == "Leads here: Welcome, Alpha, Bravo and 2 more" and side(pg, "hub", "in").get_attribute("data-more") == "2"
    assert side(pg, "hub", "out").get_attribute("title") == "Leads to: Alpha, Bravo, Charlie and 2 more" and side(pg, "hub", "out").get_attribute("data-more") == "2"
    assert side(pg, "a", "out").get_attribute("data-more") == "0" and "more" not in side(pg, "a", "out").get_attribute("title")


def test_a_side_with_no_door_is_a_wall_of_three_pixels_of_ink(rooms):
    pg, host, w = rooms
    assert walled(pg, "stray", "in") and walled(pg, "stray", "out")                                                         # nothing leads to it, it leads nowhere
    assert walled(pg, "dead", "out") and not walled(pg, "dead", "in")                                                       # a dead end: no door out, not where the flow ends
    assert walled(pg, "end", "out") and not walled(pg, "end", "in")                                                         # the flow's end
    assert not any(walled(pg, s, "in") for s in ("home", "hub", "a", "b", "c", "d")) and not any(walled(pg, s, "out") for s in ("home", "hub", "a", "b", "c", "d"))
    assert doors(pg, "stray", "in") == 0 and doors(pg, "dead", "out") == 0
    wall = side(pg, "dead", "out").locator(".scr-frame")
    assert wall.count() == 1 and wall.evaluate("e => getComputedStyle(e).width") == "3px"
    ink = pg.evaluate("() => { const d = document.createElement('i'); d.style.background = 'var(--ork-ink)'; document.body.appendChild(d); const c = getComputedStyle(d).backgroundColor; d.remove(); return c; }")
    assert wall.evaluate("e => getComputedStyle(e).backgroundColor") == ink
    frame = side(pg, "hub", "out").locator(".scr-frame").first
    assert frame.evaluate("e => getComputedStyle(e).backgroundColor") != ink                                                # a side with doors is the frame, not a wall
    shot(pg, f"rooms-walls-{w}.png")


def test_the_walls_agree_with_the_hints_dead_end_and_loose(rooms):
    pg, host, w = rooms
    room = {s: (pg.locator(f'.scr-card[data-screen="{s}"]').get_attribute("data-room") or "").split() for s in NAMES}
    assert [s for s, t in room.items() if "dead_end" in t] == ["dead"] and [s for s, t in room.items() if "loose" in t] == ["stray"]
    assert [s for s, t in room.items() if "end" in t] == ["end"] and [s for s, t in room.items() if "entry" in t] == ["home"]   # the last step that is not loose: Stray's is
    for s, t in room.items():
        assert walled(pg, s, "out") == ("dead_end" in t or ("end" in t and s == "end") or "loose" in t)
        assert walled(pg, s, "in") == ("loose" in t)


def test_the_entrys_left_side_has_a_door_from_outside_with_a_chevron(rooms):
    pg, host, w = rooms
    assert doors(pg, "home", "in") == 2                                                                                    # from outside, and the link back from Alpha
    entry = side(pg, "home", "in").locator(".scr-door--in")
    assert entry.count() == 1 and entry.get_attribute("title") == "Where people come in" and entry.locator(".ork-chev.right").count() == 1
    assert side(pg, "home", "in").get_attribute("title") == "Leads here: Alpha"
    assert pg.locator(".scr-door--in").count() == 1 and pg.locator(".scr-door .ork-chev").count() == 1                      # no other screen has one
    assert not walled(pg, "home", "in")
    assert pg.locator('.scr-card[data-screen="hub"]').get_attribute("data-room") is None


def test_a_door_is_a_gap_ten_pixels_tall_inside_the_cards_box(rooms):
    pg, host, w = rooms
    card = pg.locator('.scr-card[data-screen="hub"]').bounding_box()
    for which in ("in", "out"):
        for door in side(pg, "hub", which).locator(".scr-door").all():
            box = door.bounding_box()
            assert abs(box["height"] - 10) < 0.5
            assert card["x"] - 1.5 <= box["x"] and box["x"] + box["width"] <= card["x"] + card["width"] + 1.5
            assert card["y"] <= box["y"] and box["y"] + box["height"] <= card["y"] + card["height"] + 0.5


def test_the_reach_edge_stays_over_the_doors(rooms):
    pg, host, w = rooms
    if w != "wide":
        pytest.skip("the same card, the same edge")
    pg.evaluate("""() => { const i = document.createElement('i'); i.className = 'rc-edge'; i.dataset.near = '0'; i.dataset.elem = 'ice'; document.querySelector('.scr-card[data-screen="hub"]').appendChild(i); }""")
    edge = pg.locator('.scr-card[data-screen="hub"] > .rc-edge')
    z = lambda el: int(el.evaluate("e => getComputedStyle(e).zIndex") or 0)                                                # the edge takes no pointer: it is over by its place in the stack
    assert z(edge) > z(side(pg, "hub", "in")) and z(edge) > z(side(pg, "hub", "out"))
    door, box = side(pg, "hub", "in").locator(".scr-door").first.bounding_box(), edge.bounding_box()
    assert box["x"] - 1 <= door["x"] < box["x"] + 3 and box["y"] - 1 <= door["y"] and door["y"] + door["height"] <= box["y"] + box["height"] + 1      # (a card leans a little under the pointer)   # it lies along the door's side
    shot(pg, "rooms-reach-wide.png")


def test_the_arrows_and_the_narrow_widths_chips_are_as_they_were(rooms):
    pg, host, w = rooms
    if w == "wide":
        assert pg.locator(".scr-lines path").count() == 7                                                                  # the forward links: home>hub, hub>a b c d dead, a>end, and none back
        assert pg.locator(".scr-arrow").count() == 7
    else:
        assert pg.locator(".scr-links").count() >= 2 and pg.locator(".scr-arrow").count() == 0
