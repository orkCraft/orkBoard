"""The mana in the hand (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §3, §7; decisions §175.2, §176.1–§176.2), in a real browser against a stub host, at the two widths of `tests/narrow.py`: the AI tools' limits
as potions at the hand's right end, flush against the window's edge: one potion a tool in the chips' order, one row of up to three at the default size and two rows of two small ones for four and of three for five or six, the first five and a
*+n* for more, each tool's mark in its own colour above it and its share under it, the chip's words on the button, a press opening what used the tool over the pane, a tool not read an empty potion with *?*, a card lifted
that spends hatching its share off its tool's potion; the tabs' end holds no chip. Screenshots to $MANA_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, _press, _stack, open_hand, sig  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["MANA_SHOTS"]) if os.environ.get("MANA_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def tool(provider, name, left, window="week"):
    return {"provider": provider, "name": name, "left": left, "rows": [{"window": window, "left": left, "reset": ""}] if left is not None else []}


TWO = [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", 0.18)]
SIX = [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", 0.18), tool("agy", "Antigravity", 0.85), tool("cursor", "Cursor", 0.45), tool("hermes", "Hermes", 0.04), tool("pi", "Pi", 0.30)]
EIGHT = [*SIX, tool("aider", "Aider", 0.5), tool("goose", "Goose", 0.7)]


def open_mana(gui, limits, width="wide"):
    host = HandHost()
    host.limits = limits
    return open_hand(gui, host, width)


def pots(pg):
    pg.locator(".hand-mana .hand-pot").first.wait_for(timeout=WAIT_MS)
    return pg.locator(".hand-mana .hand-pot")


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_two_tools_are_two_potions_in_one_row_in_the_chips_order_flush_against_the_right_edge(gui, width):
    pg, host, log = open_mana(gui, TWO, width)
    try:
        p = pots(pg)
        pg.wait_for_timeout(500)
        assert [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex"]                                      # one potion a tool, in the chips' order
        assert [b.get_attribute("aria-label") for b in p.all()] == ["Claude Code: 62% of the week left", "Codex: 18% of the week left"]
        assert [b.get_attribute("title") for b in p.all()] == [b.get_attribute("aria-label") for b in p.all()]                  # the chip's words, as title and for a screen reader
        assert [b.locator(".hand-pot__share").inner_text() for b in p.all()] == ["62%", "18%"]
        small = width == "narrow"
        assert [("small" in (b.locator(".ork-potion").get_attribute("class") or "").split()) for b in p.all()] == [small, small]      # the default size on the desktop, small on the phone
        assert p.nth(0).locator(".ork-potion").get_attribute("aria-hidden") == "true"
        assert "--ork-potion-left:0.62" in p.nth(0).locator(".ork-potion").get_attribute("style").replace(" ", "")
        assert "is-warn" in p.nth(1).locator(".ork-potion").get_attribute("class") and "is-warn" not in p.nth(0).locator(".ork-potion").get_attribute("class")
        ys = [b.bounding_box()["y"] for b in p.all()]
        assert ys[0] == ys[1]                                                                                                  # one row
        mark = p.nth(0).locator("img.ork-mark")
        assert mark.get_attribute("src").endswith("/marks/harness-claude.png") and "-ink" not in mark.get_attribute("src")        # the mark in its own colour
        assert mark.get_attribute("srcset").endswith("harness-claude@2x.png 2x")
        assert mark.bounding_box()["y"] < p.nth(0).locator(".ork-potion").bounding_box()["y"] < p.nth(0).locator(".hand-pot__share").bounding_box()["y"]       # the mark above, the share under
        assert pg.locator(".hand-mana").bounding_box()["x"] + pg.locator(".hand-mana").bounding_box()["width"] == pytest.approx(pg.viewport_size["width"], abs=1)        # flush against the window's edge
        assert pg.locator(".hand-mana").evaluate("e => e.closest('.hand') !== null") and pg.locator(".table-tabs__end .table-chip, .table-tabs .limit-chip").count() == 0    # in the hand, none at the tabs' end
        narrow.no_sideways(pg)
        shot(pg, f"{width}-two")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_tabs_end_keeps_plus_and_stop_all_and_no_chip(gui):
    pg, host, log = open_mana(gui, TWO)
    try:
        pots(pg)
        end = pg.locator(".table-tabs__end")
        assert end.get_by_role("button", name="New party").count() == 1 and end.get_by_role("button", name="Stop all").count() == 1
        assert end.locator("button").count() == 2 and pg.locator(".table-chip").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_four_tools_are_two_rows_of_two_small_potions(gui, width):
    pg, host, log = open_mana(gui, SIX[:4], width)
    try:
        p = pots(pg)
        pg.wait_for_timeout(500)
        assert p.count() == 4
        boxes = [b.bounding_box() for b in p.all()]
        assert boxes[0]["y"] == boxes[1]["y"] and boxes[2]["y"] == boxes[3]["y"] and boxes[2]["y"] > boxes[0]["y"] + 40           # two rows of two (decisions §177.8)
        assert boxes[0]["x"] < boxes[1]["x"] and boxes[0]["x"] == pytest.approx(boxes[2]["x"], abs=1) and boxes[1]["x"] == pytest.approx(boxes[3]["x"], abs=1)
        assert all("small" in b.locator(".ork-potion").get_attribute("class").split() for b in p.all())
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_five_or_six_tools_are_two_rows_of_three_small_potions(gui, width):
    pg, host, log = open_mana(gui, SIX, width)
    try:
        p = pots(pg)
        pg.wait_for_timeout(500)
        assert p.count() == 6 and [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex", "agy", "cursor", "hermes", "pi"]
        boxes = [b.bounding_box() for b in p.all()]
        assert boxes[0]["y"] == boxes[1]["y"] == boxes[2]["y"] and boxes[3]["y"] == boxes[4]["y"] == boxes[5]["y"] and boxes[3]["y"] > boxes[0]["y"] + 40      # two rows of three
        assert boxes[0]["x"] < boxes[1]["x"] < boxes[2]["x"] and boxes[0]["x"] == pytest.approx(boxes[3]["x"], abs=1)
        assert all("small" in b.locator(".ork-potion").get_attribute("class").split() for b in p.all())                         # small
        assert [b.locator(".ork-potion").get_attribute("class").split()[-1] for b in p.all()][:2] == ["small", "is-warn"] or "is-warn" in p.nth(1).locator(".ork-potion").get_attribute("class")
        assert "is-danger" in p.nth(4).locator(".ork-potion").get_attribute("class")                                            # 4 % is the danger's level
        assert [b.locator(".hand-pot__share").inner_text() for b in p.all()] == ["62%", "18%", "85%", "45%", "4%", "30%"]
        assert p.nth(2).get_attribute("aria-label") == "Antigravity: 85% of the week left"
        hand, mana = pg.locator(".hand").bounding_box(), pg.locator(".hand-mana").bounding_box()
        assert mana["y"] + mana["height"] <= hand["y"] + hand["height"] + 1                                                    # the hand holds them: it grows by what they need and no more
        assert hand["height"] <= 240, hand
        shot(pg, f"{width}-six")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_more_than_six_tools_are_five_potions_and_a_plus_n_that_opens_all_of_them(gui):
    pg, host, log = open_mana(gui, EIGHT)
    try:
        p = pots(pg)
        assert [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex", "agy", "cursor", "hermes", None]
        more = pg.locator(".hand-pot--more")
        assert more.inner_text().strip() == "+3" and more.get_attribute("aria-label") == "3 more tools: what is left of them"
        assert pg.locator(".hand-mana .ork-potion").count() == 5
        shot(pg, "wide-eight")
        more.click()
        pg.locator('.table-over[data-kind="limits"]').wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["props"] == {}                                                                  # all of them, no provider
        assert pg.locator(".arena-limits .arena-limit").count() == 8
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_press_opens_what_used_the_tool_over_the_pane(gui, width):
    pg, host, log = open_mana(gui, TWO, width)
    try:
        pots(pg).nth(1).click()
        pg.locator('.table-over[data-kind="limits"] .arena-usage').wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["props"] == {"provider": "codex"}
        assert ("ideas.usage", {"provider": "codex", "scope": "project"}) in host.log
        assert pg.locator("[data-title]").inner_text().lower().endswith("codex: what used it")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_whose_limits_were_not_read_is_an_empty_potion_and_a_question_mark(gui):
    pg, host, log = open_mana(gui, [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", None)])
    try:
        p = pots(pg)
        codex = p.nth(1)
        assert codex.locator(".hand-pot__share").inner_text() == "?" and codex.get_attribute("aria-label") == "Codex: limits not read yet"
        assert "--ork-potion-left:0" in codex.locator(".ork-potion").get_attribute("style").replace(" ", "") and "is-warn" not in codex.locator(".ork-potion").get_attribute("class")
        assert p.nth(0).locator(".hand-pot__share").inner_text() == "62%"
        shot(pg, "wide-unread")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_without_a_mark_shows_its_initial_in_the_body_face(gui):
    pg, host, log = open_mana(gui, [tool("claude", "Claude Code", 0.62), tool("aider", "Aider", 0.5)])
    try:
        p = pots(pg)
        assert p.nth(1).locator("img").count() == 0 and p.nth(1).locator(".hand-pot__initial").inner_text() == "A"
        assert p.nth(0).locator(".hand-pot__initial").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_lifted_card_that_spends_hatches_its_share_off_its_tools_potion(gui, width):
    pg, host, log = open_mana(gui, TWO, width)
    try:
        p = pots(pg)
        assert p.locator(".hand-pot__took").count() == 0 and "--ork-potion-spend" not in p.nth(0).locator(".ork-potion").get_attribute("style")
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        _press(pg, "export")                                                                                                     # a plan: about 2–4% of Claude's week
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        claude = p.nth(0)
        assert "--ork-potion-spend:0.04" in claude.locator(".ork-potion").get_attribute("style").replace(" ", "")
        assert claude.locator(".hand-pot__share").inner_text().replace("\n", " ") == "62% −4%"
        assert "This card takes about 4%" in claude.get_attribute("aria-label")
        assert "--ork-potion-spend" not in p.nth(1).locator(".ork-potion").get_attribute("style")                                # the other tool's potion is as it was
        shot(pg, f"{width}-spend")
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
        assert p.locator(".hand-pot__took").count() == 0 and "--ork-potion-spend" not in claude.locator(".ork-potion").get_attribute("style")
        _press(pg, "theme")                                                                                                      # a question spends nothing
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        assert p.locator(".hand-pot__took").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_limits_no_mana(gui):
    pg, host, log = open_mana(gui, [])
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-mana").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_no_goal_at_all_the_potions_still_lie_at_the_hands_right_end(gui):
    host = HandHost(empty=True)
    host.limits = TWO
    pg, host, log = open_hand(gui, host)
    try:
        p = pots(pg)
        pg.locator(".hand-plus.is-large").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        box = pg.locator(".hand-mana").bounding_box()
        assert p.count() == 2 and box["x"] + box["width"] == pytest.approx(pg.viewport_size["width"], abs=1) and box["y"] + box["height"] <= pg.viewport_size["height"] + 1
        shot(pg, "wide-empty")
    finally:
        pg.close()
    assert not log, "\n".join(log)
