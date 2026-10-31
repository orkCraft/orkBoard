"""Spec 117 part H, the loop as a rondel (docs/specs/117-each-lens-a-games-shape.md §7, decisions §195), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with a mouse),
against the maps' stub host (`MapsHost`, Game design's loop) with its currencies and steps changed where a test needs it.

The ring closes: a chevron after the last step of each ring too, as many chevrons as steps (the closing one marked, and not under the ring's tag). A step's card carries what it gives (*+ Coins*) and takes (*− Coins*) as
orkUI chips under its line, a title *Gives Coins* / *Takes Coins*, a name cut at 12 characters, three at most and then *+n*; a currency the loop does not name is left out; at the narrow width, where the loops lie as lists, the tokens
too; the heat and the reach of the kit (part E) still paint a step and a currency. No sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import LOOP, MapsHost, go, step  # noqa: E402
from tests.test_table_desktop_browser import shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

LONG = "Tournament tickets"                                                       # 18 characters: cut at 12


def loop_with(**by_step):
    """The stub's loop, with some steps' `gives` / `takes` changed (`step id = (gives, takes)`) and three more currencies."""
    lp = json.loads(json.dumps(LOOP))
    lp["currencies"] += [{"id": "tickets", "name": LONG, "kind": "hard", "line": ""}, {"id": "xp", "name": "XP", "kind": "progress", "line": ""}, {"id": "wood", "name": "Wood", "kind": "soft", "line": ""}]
    for loop in lp["loops"]:
        for s in loop["steps"]:
            if s["id"] in by_step:
                s["gives"], s["takes"] = (list(x) for x in by_step[s["id"]])
    return lp


@pytest.fixture(params=narrow.WIDTHS)
def rondel(gui, request):
    """The window at one of the two widths against a MapsHost: `(page, host, width, open)`, `open()` goes to Game design; the page's errors are asserted at the end."""
    errors: list[str] = []
    server, browser = gui
    host = MapsHost()
    pg = narrow.page(browser, request.param)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)

    def open_():
        pg.goto(server.url)
        pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
        go(pg, "game")
        pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)

    yield pg, host, request.param, open_
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def card(pg, sid):
    return pg.locator(f'.mp-st[data-id="{sid}"]')


def tokens(pg, sid):
    """A step's tokens: `[(text, title)]`."""
    return card(pg, sid).locator(".rd-tok").evaluate_all("els => els.map((e) => [e.innerText.trim(), e.title])")


def test_the_ring_closes_a_chevron_after_the_last_step_of_each_ring_and_not_under_its_tag(rondel):
    pg, host, w, open_ = rondel
    open_()
    if not wide(w):
        assert pg.locator(".mp-ring__chev").count() == 0 and pg.locator(".mp-ll").count() == 3                      # the lists have no ring to close
        return
    assert pg.locator(".mp-ring__chev").count() == 9 and pg.locator(".mp-ring__chev[data-close]").count() == 3     # one after each step, the last of each ring closing it
    for span in ("core", "session", "meta"):
        ring = pg.locator(f'.mp-ring[data-span="{span}"]')
        closing = ring.locator(".mp-ring__chev[data-close]").bounding_box()
        assert ring.locator(".mp-ring__chev").count() == 3
        box = ring.locator(".mp-ring__tag").bounding_box()
        assert closing["x"] >= box["x"] + box["width"] - 1 or closing["x"] + closing["width"] <= box["x"] + 1 or closing["y"] + closing["height"] <= box["y"] + 1 or closing["y"] >= box["y"] + box["height"] - 1, span   # clear of the tag
        steps = [b for b in (ring.locator(".mp-st").nth(i).bounding_box() for i in range(3))]
        for b in steps:                                                                                            # and clear of every card
            assert closing["x"] + closing["width"] <= b["x"] + 1 or b["x"] + b["width"] <= closing["x"] + 1 or closing["y"] + closing["height"] <= b["y"] + 1 or b["y"] + b["height"] <= closing["y"] + 1, span
    shot(pg, "rondel-ring-wide.png")


def test_a_ring_of_one_loop_and_of_one_step_closes_too(rondel):
    pg, host, w, open_ = rondel
    host.loop["loops"] = [{**host.loop["loops"][0], "steps": host.loop["loops"][0]["steps"][:1]}]
    open_()
    if wide(w):
        assert pg.locator(".mp-ring__chev").count() == 1 and pg.locator(".mp-ring__chev[data-close]").count() == 1
    else:
        assert pg.locator(".mp-ring__chev").count() == 0 and pg.locator(".mp-st").count() == 1


def test_a_step_shows_what_it_gives_and_takes_as_tokens_with_their_titles(rondel):
    pg, host, w, open_ = rondel
    host.loop = loop_with(**{"hold-the-tower": (["coins"], ["gems"]), "pick-a-hero": ([], ["coins"])})
    open_()
    assert tokens(pg, "hold-the-tower") == [["+ Coins", "Gives Coins"], ["− Gems", "Takes Gems"]]
    assert tokens(pg, "pick-a-hero") == [["− Coins", "Takes Coins"]]
    assert tokens(pg, "join-a-match") == [] and card(pg, "join-a-match").locator(".rd-toks").count() == 0            # nothing given or taken: no row
    assert card(pg, "hold-the-tower").locator(".ork-chip.rd-tok").count() == 2 and card(pg, "hold-the-tower").locator(".rd-tok").first.evaluate("e => e.classList.contains('ork-chip')")
    assert card(pg, "score-the-round").locator(".rd-tok").all_inner_texts() == ["+ Coins"]                            # the stub's own gives
    assert card(pg, "climb-the-ladder").locator(".rd-tok").all_inner_texts() == ["+ Gems"]
    if wide(w):
        assert pg.locator(".mp-rings .rd-tok").count() == 6
    else:
        assert pg.locator(".mp-ll .rd-tok").count() == 6                                                           # in the lists too, under the step's line
        assert "Coins" in card(pg, "score-the-round").inner_text() and card(pg, "score-the-round").locator(".rd-toks").evaluate("e => e.previousElementSibling.classList.contains('mp-card__foot')")
    shot(pg, f"rondel-tokens-{w}.png")


def test_a_name_is_cut_at_twelve_characters_three_tokens_at_most_and_then_plus_n(rondel):
    pg, host, w, open_ = rondel
    host.loop = loop_with(**{"hold-the-tower": (["tickets"], []), "rematch": (["coins", "gems", "xp"], ["wood", "tickets"]), "show-off": (["coins", "gems", "nowhere"], [])})
    open_()
    (text, title), = tokens(pg, "hold-the-tower")
    assert len(text) <= 14 and text == "+ Tournament …" and title == f"Gives {LONG}"                                # "+ " then the name cut at 12 characters
    got = tokens(pg, "rematch")
    assert [t for t, _ in got] == ["+ Coins", "+ Gems", "+ XP", "+2"] and got[3][1] == f"Takes Wood, Takes {LONG}"        # three, then the two left
    assert [t for t, _ in tokens(pg, "show-off")] == ["+ Coins", "+ Gems"]                                           # a currency the loop does not name is left out
    for sid in ("hold-the-tower", "rematch"):                                                                       # the chips stay inside the card
        c = card(pg, sid).bounding_box()
        for b in card(pg, sid).locator(".rd-tok").evaluate_all("els => els.map((e) => { const r = e.getBoundingClientRect(); return { x: r.x, w: r.width }; })"):
            assert b["x"] >= c["x"] - 1 and b["x"] + b["w"] <= c["x"] + c["width"] + 1, sid
    shot(pg, f"rondel-many-{w}.png")


def test_the_tokens_are_ink_chips_and_a_take_is_dashed(rondel):
    pg, host, w, open_ = rondel
    host.loop = loop_with(**{"rematch": (["coins"], ["gems"])})
    open_()
    give, take = (card(pg, "rematch").locator(f'.rd-tok[data-token="{k}"]') for k in ("gives", "takes"))
    style = lambda loc: loc.evaluate("e => { const s = getComputedStyle(e); return [s.color, s.borderTopStyle, s.borderTopColor]; }")
    assert style(give)[1] == "solid" and style(take)[1] == "dashed" and style(give)[0] == style(take)[0]               # the same ink, a take told by its dashes
    assert give.bounding_box()["height"] <= 20


def test_heat_and_reach_still_paint_a_step_and_the_economy_stays(rondel):
    pg, host, w, open_ = rondel
    host.loop = loop_with(**{"hold-the-tower": (["coins"], [])})
    open_()
    pg.evaluate("""() => { const c = document.querySelector('.mp-st[data-id="hold-the-tower"]'); c.setAttribute('data-heat', 'no_source'); c.insertAdjacentHTML('beforeend', '<i class="rc-edge" data-near="0"></i>'); }""")
    c = card(pg, "hold-the-tower")
    box, edge = c.bounding_box(), c.locator("i.rc-edge").bounding_box()
    assert abs(edge["x"] - box["x"]) <= 3 and abs(edge["width"] - box["width"]) <= 4 and abs(edge["height"] - box["height"]) <= 4          # the edge still wraps the card, the tokens inside it
    assert c.locator(".rd-tok").count() == 1 and pg.locator(".mp-eco").count() == 1 and pg.locator('.mp-eco__row[data-currency="coins"] .mp-cur').count() == 1   # the economy as built


def test_a_press_on_a_token_lifts_its_step(rondel):
    pg, host, w, open_ = rondel
    host.loop = loop_with(**{"hold-the-tower": (["coins"], [])})
    open_()
    card(pg, "hold-the-tower").locator(".rd-tok").first.click()
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    assert "Hold the tower" in pg.locator(".table-back").inner_text() and "Coins" in pg.locator(".table-back").inner_text()
