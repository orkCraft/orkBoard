"""A card's face and the hand's fan (docs/specs/160 stage F, decisions §269.6 and §269.7, §276), in a real browser at 1280 x 800: a card's frame is its element's token with a gilt line inside it, its face in hard-stopped bands (no blur
on it); a failure's card has the danger ring and a faint second over the frame, a done card no ring (§276.2); the hand's front cards are turned two degrees, one way and the other by lane, and straight under reduced motion."""
from __future__ import annotations

import re

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_discard_table_browser import open_maps  # noqa: E402
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_table_desktop_browser import start  # noqa: E402

TOKEN = "(name) => { const d = document.createElement('i'); d.style.color = `var(${name})`; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }"
FRAME = "(e) => getComputedStyle(e, '::after').boxShadow"


def token(pg, name):
    return pg.evaluate(TOKEN, name)


def lines(shadow):
    """A computed inset-shadow list as `[(colour, spread)]`, the outermost first (the first of the list is painted on top)."""
    parts = re.split(r", (?=(?:rgba?|color)\()", shadow)
    return [(p.split(" 0px 0px 0px ")[0], int(re.search(r"(\d+)px inset", p).group(1))) for p in parts]


@pytest.fixture
def table(gui):
    errors: list[str] = []
    pg, host = start(gui, "wide", errors)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.mark.browser
def test_a_cards_frame_is_its_elements_token_with_a_gilt_line_and_its_face_is_in_hard_bands(table):
    pg, host = table
    meadow, ice = pg.locator('[data-lkey="t:task:rules/r1"]'), pg.locator('[data-lkey="t:task:seat/s2"]')
    for card, name in ((meadow, "--ork-elem-meadow"), (ice, "--ork-elem-ice")):
        assert card.evaluate("(e) => getComputedStyle(e).getPropertyValue('--ork-el')").strip() == pg.evaluate("(n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim()", name), "the frame is the element's token"
        face = card.evaluate("(e) => getComputedStyle(e).backgroundImage")
        assert face.startswith("linear-gradient(") and "radial" not in face
        assert len(re.findall(r"\d+(?:\.\d+)?%", face)) >= 6, "the element in stepped bands, a hard stop at each edge"
    r = lines(meadow.evaluate(FRAME))
    assert [w for _, w in r] == [3, 4, 5], "a thick frame, a gilt line inside it, a dark line inside that"
    assert r[0][0] != lines(ice.evaluate(FRAME))[0][0], "the frame is the element's colour: two elements, two frames"
    assert token(pg, "--ork-elem-meadow") != token(pg, "--ork-elem-ice")
    window = pg.locator('[data-lkey="t:task:rules/r1"] .table-card__win').evaluate("(e) => getComputedStyle(e).boxShadow")
    assert "inset" in window and window.count("0px 0px") >= 2 and "px 0px 0px" in window.replace("0px 0px 0px", ""), window
    for card in (meadow, ice):
        everything = card.evaluate("(e) => getComputedStyle(e).boxShadow + ' ' + getComputedStyle(e, '::after').boxShadow")
        blurs = [re.findall(r"-?[\d.]+px", part)[2] for part in re.split(r", (?=(?:rgba?|color)\()", everything.replace("none ", "")) if "px" in part]
        assert blurs and set(blurs) == {"0px"}, "no blurred shadow on a card"


@pytest.mark.browser
def test_a_failed_card_wears_one_ring_and_a_faint_second_over_its_frame(table):
    pg, host = table
    card = pg.locator('[data-lkey="t:task:seat/s2"]')
    assert card.evaluate("e => e.classList.contains('fails')")
    got = lines(card.evaluate(FRAME))
    assert [w for _, w in got] == [2, 4, 5, 6], "the ring, the faint second, then the frame and its gilt line"
    assert got[0][0] == token(pg, "--ork-danger"), "the danger ring, outermost: the element's frame cannot hide it"
    assert got[1][0] != got[0][0]
    pg.screenshot(path="/tmp/claude-0/-home-user/bff42dbb-2f8d-589b-a39c-92fba3b77fd3/scratchpad/lane-1280.png")


@pytest.mark.browser
def test_a_done_card_has_the_frame_and_no_ring(gui):
    pg, host, log = open_maps(gui, "wide")
    try:
        card = pg.locator(".hand-done.hand-card").first
        card.wait_for(timeout=WAIT_MS)
        got = lines(card.evaluate(FRAME))
        assert [w for _, w in got] == [3, 4, 5], "the frame alone"
        for ring in ("--ork-danger", "--ork-alert", "--ork-success"):
            assert token(pg, ring) not in [c for c, _ in got], f"success is no ring and nothing else rings it ({ring})"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.browser
def test_the_hands_front_cards_are_turned_two_degrees_and_not_under_reduced_motion(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-slot .hand-card--face").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        fronts = ".hand-slot:not(.is-behind):not(.is-plus) .hand-stack > .hand-card--face:not(.hand-lifted)"
        turned = pg.evaluate("(q) => [...document.querySelectorAll(q)].map((e) => getComputedStyle(e).rotate)", fronts)
        assert turned and set(turned) <= {"-2deg", "2deg"}, turned
        pg.screenshot(path="/tmp/claude-0/-home-user/bff42dbb-2f8d-589b-a39c-92fba3b77fd3/scratchpad/hand-1280.png")
        pg.emulate_media(reduced_motion="reduce")
        pg.wait_for_timeout(300)
        still = pg.evaluate("() => [...document.querySelectorAll('.hand-slot .hand-stack > .hand-card--face')].map((e) => getComputedStyle(e).rotate)")
        assert still and set(still) <= {"none", "0deg"}, still
    finally:
        pg.close()
    assert not log, "\n".join(log)
