"""A card's four corners (docs/specs/147-one-card-four-corners.md part A, decisions §251.2), in a real browser: a lane's card and the discard's card have one top row (the goal's rune first, the kind's sign last) and one foot row (who, how much);
a sign is 14 px and a head 16 on every card; a lane's card is 5 : 7 at the frame's card width. The bottom right's one figure (`muchOf`) and the words of the corners (realm/lexicon.py `corner_*`) are kept here too."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_discard_table_browser import open_maps  # noqa: E402
from tests.test_table_desktop_browser import node, start, task  # noqa: E402

CORNERS_JS = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "js" / "table" / "corners.js"


def rows_of(card):
    """The card's corner rows, in the order they lie: the top row first."""
    return card.evaluate("e => [...e.querySelectorAll('.corner')].map((r) => r.className.replace('corner ', ''))")


def corners_ok(card):
    """One top row and one foot row; the rune first and the kind last in the top; the sign 14 px, the head 16."""
    assert rows_of(card) == ["corner--top", "corner--foot"]
    top = card.locator(".corner--top")
    assert top.evaluate("e => e.firstElementChild.classList.contains('corner__rune') && e.lastElementChild.classList.contains('corner__kind')"), "the rune first, the kind last"
    assert top.locator(".corner__rune .ork-elem").count() == 1 and top.locator(".corner__kind .ork-sign").count() == 1
    sign, rune = top.locator(".corner__kind .ork-sign").bounding_box(), top.locator(".corner__rune .ork-elem").bounding_box()
    assert abs(sign["width"] - 14) <= 0.5 and abs(sign["height"] - 14) <= 0.5 and abs(rune["width"] - 14) <= 0.5, "a sign and a rune are 14 px"
    assert rune["x"] < sign["x"], "the rune lies left of the kind"
    for head in card.locator(".corner--foot .ork-race__head").all():
        assert abs(head.bounding_box()["height"] - 16) <= 0.5, "a head is 16 px high"
    foot = card.locator(".corner--foot").bounding_box()
    assert top.bounding_box()["height"] <= 20.5 and foot["height"] <= 20.5, "rows 20 px tall"


@pytest.fixture
def table(gui):
    errors: list[str] = []
    pg, host = start(gui, "wide", errors)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.mark.browser
def test_a_lane_card_has_a_top_row_and_a_foot_row_and_is_5_by_7(table):
    pg, host = table
    cards = pg.locator(".table-lane[data-party] .table-card--task")
    assert cards.count() >= 4
    for card in cards.all():
        box = card.bounding_box()
        assert abs(box["width"] - 144) <= 1 and abs(box["width"] / box["height"] - 5 / 7) <= 0.012, box          # 144 x 202, 5 : 7
        corners_ok(card)
    working = pg.locator('[data-lkey="t:task:rules/r1"]')
    assert working.locator(".corner--foot .ork-race__head").count() == 1, "who works: the seat's head in the foot"
    window = working.locator(".table-card__win").bounding_box()
    assert 80 <= window["height"] <= 92, "the window onto the work lies between the title and the foot"
    assert working.locator(".table-card__head").bounding_box()["y"] >= working.locator(".corner--top").bounding_box()["y"] + 18
    assert working.locator(".table-card__win").bounding_box()["y"] + window["height"] <= working.locator(".corner--foot").bounding_box()["y"] + 1


@pytest.mark.browser
def test_the_figure_at_the_foots_right_is_the_one_the_state_gives(table):
    pg, host = table
    failed = pg.locator('[data-lkey="t:task:seat/s2"]')
    assert failed.locator(".corner--foot .corner__much .ork-gem").inner_text().strip() == "$1", "a retry spends: its cost"
    working = pg.locator('[data-lkey="t:task:rules/r1"]')
    much = working.locator(".corner--foot .corner__much")
    assert much.count() == 0, "at work with steps, the time worked is in the card's words, not on its foot (spec 129 H2.1): nothing known draws nothing"
    got = pg.evaluate("""async () => { const c = await import('/static/js/table/corners.js');
      return [c.muchOf({ asks: true, cost: '$1' }), c.muchOf({ done: true, took: 1080 }), c.muchOf({ left: 240 }), c.muchOf({ left: 240, worked: 30 }), c.muchOf({ worked: 30 }), c.muchOf({ cost: '$2' }), c.muchOf({}), c.muchOf({ done: true })]; }""")
    assert got[0] == {"kind": "ask", "text": "asks you"} and got[1] == {"kind": "time", "text": "took 18 min"} and got[2] == {"kind": "time", "text": "4 min left"}
    assert got[3] == got[2], "the time left before the time worked"
    assert got[4]["text"] == "worked 30 s" and got[5] == {"kind": "gem", "text": "$2"} and got[6] is None and got[7] is None, "nothing known draws nothing"


@pytest.mark.browser
def test_the_discards_card_has_a_top_row_and_a_foot_row(gui):
    server, browser = gui
    pg, host, log = open_maps(gui, "wide", done=False)
    try:
        done = lambda tid, who: task(tid, f"Task {tid}", "merged", who=who, started="2026-10-20T10:00:00", finished="2026-10-20T10:18:00")      # noqa: E731
        host.nodes.append(node("music", "tech", "Lobby music loop with a very long name that goes on and on for more than four lines of the card", "done", element="void", place="discard", updated="2026-10-20T12:00:00",
                               tasks=[done("m1", "grunt"), done("m2", "artist")]))
        host.push()
        card = pg.locator(":is(.frame-edge, .table-end) .hand-done.hand-card")
        card.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        box = card.bounding_box()
        assert (round(box["width"]), round(box["height"])) == (144, 202)
        corners_ok(card)
        assert card.locator(".corner--top .corner__kind .ork-sign.check").count() == 1, "the done sign"
        ok = pg.evaluate("() => { const d = document.createElement('i'); d.style.color = 'var(--ork-success)'; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }")
        assert card.locator(".corner__kind").evaluate("e => getComputedStyle(e).color") == ok, "in the success colour"
        name = card.locator(".hand-done__name")
        assert name.evaluate("e => getComputedStyle(e).webkitLineClamp") == "3" and name.bounding_box()["height"] <= 61, "the name in three lines at most (spec 150 C.4)"
        assert card.locator(".corner--foot .ork-race__head").count() == 2, "the heads that did it"
        assert card.locator(".corner--foot .corner__much").inner_text().strip() == "took 18 min", "the time it took"
        assert card.locator(".hand-done__line").count() == 0, "no line of main: the snapshot has no time for it"
        host.nodes[-1]["in_main"] = "2026-10-20T11:40:00"
        host.push()
        card.locator(".hand-done__line").wait_for(timeout=WAIT_MS)
        assert card.locator(".hand-done__line").inner_text().strip() == "2 tasks, in main since 11:40"
        assert card.bounding_box()["height"] == box["height"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.browser
def test_the_pages_corner_words_are_the_glossarys():
    js = CORNERS_JS.read_text(encoding="utf-8")
    got = dict(re.findall(r'(\w+) = "([^"]+)"', re.search(r"export const (ASKS = .*?);", js).group(1).replace(", ", ";\n")))
    assert got == {"ASKS": lexicon.term("corner_asks"), "LEFT": lexicon.term("corner_left"), "TOOK": lexicon.term("corner_took"), "WORKED": lexicon.term("corner_worked"), "IN_MAIN": lexicon.term("corner_in_main")}
