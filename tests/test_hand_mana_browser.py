"""The potions (docs/specs/168 A4, decisions §285.1: at 760 px and up a row of three bottles at most in the right column's head, their tops on one line, the 5 hours' share under each, the week's under a bottle smaller than the large; hovered or focused every tool lies in a list under it, the empty slot at its end; the drum went).
Before it, the mana in the hand (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §3, §7; decisions §175.2, §176.1–§176.2), in a real browser against a stub host, at the two widths of `tests/narrow.py`: the AI tools' limits
as potions at the hand's right end, flush against the window's edge: one potion a tool in the chips' order, one row of up to three at the default size and two rows of two small ones for four and of three for five or six, the first five and a
*+n* for more, each tool's mark in its own colour above it and its share under it, the chip's words on the button, a press opening what used the tool over the pane, a tool not read its mark alone, *Limits not read*, a card lifted
that spends hatching its share off its tool's potion; the tabs' end holds no chip. Spec 111 B (decisions §189.2): a potion hovered or focused outlines its tool's marks on the tabs and its words say how many parties do and check
on it. Screenshots to $MANA_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, _press, _stack, node, open_hand, sig, task  # noqa: E402

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


class ToolsHost(HandHost):
    """The real host's `tools` in the snapshot (spec 130 B): the tools in the hand in the person's order; with room, the empty slot ends the row."""

    def __init__(self, tools=("claude", "codex"), full=False):
        super().__init__()
        self.hand, self.order, self.full = list(tools), list(tools), full

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["tools"] = {"hand": [{"id": t, "title": t.title()} for t in self.order], "order": list(self.order), "full": self.full}
        return doc

    def handle(self, name, a):
        if name == "tools.order":
            self.log.append((name, a))
            self.order = list(a["order"])
            self.bump({})
            return {}
        return super().handle(name, a)


def open_mana(gui, limits, width="wide"):
    host = HandHost()
    host.limits = limits
    return open_hand(gui, host, width)


def unroll(pg):
    """At the wide width every tool lies in the list only while the row is hovered or focused (spec 168 A4): the pointer goes onto the row. Under 760 px they always lie in their rows."""
    if pg.viewport_size["width"] >= 760:
        pg.locator(".pots__row").wait_for(timeout=WAIT_MS)
        b = pg.locator(".pots__row").bounding_box()
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)


def pots(pg):
    unroll(pg)
    pg.locator(":is(.hand-mana, .pots__all) .hand-pot").first.wait_for(timeout=WAIT_MS)
    return pg.locator(":is(.hand-mana, .pots__all) .hand-pot")


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_two_tools_are_two_potions_in_one_row_in_the_chips_order_flush_against_the_right_edge(gui, width):
    pg, host, log = open_mana(gui, TWO, width)
    try:
        p = pots(pg)
        pg.wait_for_timeout(500)
        assert [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex"]                                      # one potion a tool, in the chips' order
        assert [b.get_attribute("aria-label") for b in p.all()] == [f"Claude Code: 62% of the week left{', the default' if width == 'narrow' else ''}", "Codex: 18% of the week left"]      # the default's frame is the narrow page's: at the wide width the front is the row's first
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
        if width == "narrow":
            m = pg.locator(".hand-mana").bounding_box()
            assert m["x"] + m["width"] == pytest.approx(pg.viewport_size["width"], abs=1)                                      # flush against the window's edge at the narrow width
            assert pg.locator(".hand-mana").evaluate("e => e.closest('.hand') !== null")                                       # in the hand
        else:
            lane, m = pg.locator(".release-lane").bounding_box(), pg.locator(".pots__all").bounding_box()
            assert pg.locator(".pots").evaluate("e => e.closest('.release-lane__head') !== null") and pg.locator(".hand .hand-mana, .hand .pots").count() == 0      # at the right column's head, not in the hand
            assert m["x"] >= 0 and m["x"] + m["width"] <= lane["x"] + lane["width"] + 1                                       # the list unrolled is anchored at the column's right edge, inside the window
        assert pg.locator(".table-tabs__end .table-chip, .table-tabs .limit-chip").count() == 0                                # none at the tabs' end
        narrow.no_sideways(pg)
        shot(pg, f"{width}-two")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_tabs_end_keeps_the_backpack_and_the_empty_chair_no_door_no_bug_and_no_chip(gui):
    """Decisions §267.1: the backpack stood at the tabs' end before the empty chair; spec 161 H, §272.1: it stood at the left of the discard column's head; spec 168 A4/A5, decisions §285.3: it stands at the hand's right end, the tabs' end keeps the empty chair."""
    pg, host, log = open_mana(gui, TWO)
    try:
        pots(pg)
        end = pg.locator(".table-tabs__end")
        assert end.get_by_role("button", name="New party").count() == 1 and end.get_by_role("button", name="Stop all").count() == 0
        assert end.locator("button:not(.stall-pack)").count() == 1 and end.locator(".stall-pack").count() == 0 and pg.locator('.hand-end .stall-pack').count() == 1 and end.locator(".table-logs").count() == 0 and pg.locator(".table-chip").count() == 0          # the empty chair alone: Stop all is the die's front face, the bug is in the Orkmaster's … (spec 139 A.4-A.5)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_four_tools_are_two_rows_of_two_small_potions(gui):
    pg, host, log = open_mana(gui, SIX[:4], "narrow")
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


def test_five_or_six_tools_are_two_rows_of_three_small_potions_at_the_narrow_width(gui):
    pg, host, log = open_mana(gui, SIX, "narrow")
    try:
        p = pots(pg)
        pg.wait_for_timeout(500)
        assert p.count() == 6 and [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex", "agy", "cursor", "hermes", "pi"]
        boxes = [b.bounding_box() for b in p.all()]
        assert boxes[0]["y"] == boxes[1]["y"] == boxes[2]["y"] and boxes[3]["y"] == boxes[4]["y"] == boxes[5]["y"] and boxes[3]["y"] > boxes[0]["y"] + 40      # two rows of three
        assert boxes[0]["x"] < boxes[1]["x"] < boxes[2]["x"] and boxes[0]["x"] == pytest.approx(boxes[3]["x"], abs=1)
        assert all("small" in b.locator(".ork-potion").get_attribute("class").split() for b in p.all())                         # small
        assert "is-warn" in p.nth(1).locator(".ork-potion").get_attribute("class")
        assert "is-danger" in p.nth(4).locator(".ork-potion").get_attribute("class")                                            # 4 % is the danger's level
        assert [b.locator(".hand-pot__share").inner_text() for b in p.all()] == ["62%", "18%", "85%", "45%", "4%", "30%"]
        assert p.nth(2).get_attribute("aria-label") == "Antigravity: 85% of the week left"
        hand, mana = pg.locator(".hand").bounding_box(), pg.locator(".hand-mana").bounding_box()
        assert mana["y"] + mana["height"] <= hand["y"] + hand["height"] + 1                                                    # the hand holds them: it grows by what they need and no more
        assert hand["height"] <= 240, hand
        shot(pg, "narrow-six")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def visible_potions(pg):
    """The bottles of the row at rest, in the row's order (provider ids)."""
    return pg.locator(".pots__row .pot-s").evaluate_all("els => els.map((e) => e.dataset.provider)")


def front_of(pg):
    """The tool the work goes to: the row's bottle with its share in the ink (`is-front`); "paid" for the paid tool's slot."""
    return pg.locator(".pots__row .pot-s.is-front").evaluate("e => (e.dataset.paid ? 'paid' : e.dataset.provider)")


HEALTHY = [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", 0.55), tool("agy", "Antigravity", 0.85), tool("cursor", "Cursor", 0.45), tool("hermes", "Hermes", 0.7), tool("pi", "Pi", 0.5), tool("aider", "Aider", 0.5), tool("goose", "Goose", 0.7)]


@pytest.mark.parametrize("count", [2, 4, 6, 8])
def test_three_bottles_at_most_stand_in_the_row_tops_on_one_line_and_hovered_every_tool_lies_in_a_list(gui, count):
    limits = HEALTHY[:count]
    host = HandHost()
    host.limits = limits
    host.parties[0]["tool"] = limits[1 if count == 2 else 2]["provider"] if count > 2 else "codex"                    # Tech's tab: the tool its party works on stands in front
    pg, host, log = open_hand(gui, host)
    try:
        pg.locator('[data-tab="tech"]').click()
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)
        pg.wait_for_timeout(500)
        tools = [t["provider"] for t in limits]
        assert pg.locator(".pots[data-open]").count() == 0 and pg.locator(".pots__all").is_hidden(), "no list at rest"
        seen = visible_potions(pg)
        front = front_of(pg)
        assert seen[0] == front and len(seen) == min(3, count), (front, seen)                                                # the tool the work goes to first, three at most
        assert seen[1:] == [t for t in tools if t != front][: len(seen) - 1], "then the person's order (none is at the warn or the danger level)"
        tops = pg.locator(".pots__row .ork-potion").evaluate_all("els => els.map((e) => e.getBoundingClientRect().top)")
        assert len(set(tops)) == 1, tops                                                                                       # their tops are on one line
        bottles = pg.locator(".pots__row .pot-s").all()
        assert all(b.locator(".pot-s__cork .ork-mark, .pot-s__cork .hand-pot__initial").count() == 1 for b in bottles), "each bottle wears its tool's mark as its cork"
        corks = pg.locator(".pots__row .pot-s__cork").evaluate_all("els => els.map((e) => e.getBoundingClientRect().top)")
        assert len(set(corks)) == 1, corks                                                                                     # the corks on one line, as the tops
        assert pg.locator(".pots__row .ork-potion").evaluate_all("els => els.every((e) => e.offsetWidth <= 28 && e.offsetHeight <= 36)")      # orkUI's .small: 2 px a cell, 28 × 36 at most
        assert pg.locator(".pots").evaluate("e => e.closest('.release-lane__head') !== null")
        b = pg.locator(".pots__row").bounding_box()
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)                                                      # hover: every tool in a list
        pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)
        row = pg.locator(".pots__all .hand-pot:not(.hand-pot--empty)")
        assert [e.get_attribute("data-provider") for e in row.all()] == tools, "every tool, in the person's order"
        assert all(e.locator(".ork-mark, .hand-pot__initial").count() == 1 and e.locator(".hand-pot__share").count() == 1 for e in row.all()), "each with its mark and shares"
        assert all(e.is_visible() for e in row.all())
        shot(pg, f"wide-unrolled-{count}")
        pg.keyboard.press("Escape")
        pg.locator(".pots[data-open]").wait_for(state="detached", timeout=WAIT_MS)                                            # Esc folds it
        assert pg.locator(".pots__all").is_hidden()
        pg.mouse.move(640, 300)
        b = pg.locator(".pots__row").bounding_box()
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)
        pg.locator(".pots[data-open]").wait_for(state="detached", timeout=WAIT_MS)                                            # the pointer leaving folds it
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_unrolled_row_ends_with_the_empty_slot_and_lights_it_while_the_orkmaster_asks_for_a_tool(gui):
    host = ToolsHost()
    host.limits = TWO
    pg, host, log = open_hand(gui, host)
    try:
        pots(pg)
        slot = pg.locator(".pots__all .hand-pot--empty")
        assert slot.count() == 1 and slot.is_visible() and slot.get_attribute("aria-label") == "Add an AI tool"
        order = pg.locator(".pots__all > .hand-pot").evaluate_all("els => els.map((e) => e.dataset.provider || 'slot')")
        assert order == ["claude", "codex", "slot"], "the empty slot at the row's end"
        assert "is-lit" not in slot.get_attribute("class")
        slot.click()
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.lifted.value).then((v) => /add/i.test(v))", timeout=WAIT_MS)       # its press lifts the adding card
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_potion_pressed_in_the_row_lifts_its_tools_card_and_a_drag_in_the_row_changes_the_order(gui):
    host = ToolsHost(full=True)
    host.limits = TWO
    pg, host, log = open_hand(gui, host)
    try:
        p = pots(pg)
        assert p.nth(0).get_attribute("draggable") == "true" and pg.locator(":is(.hand-mana, .pots__all) .hand-pot--empty").count() == 0, "six tools or full: no empty slot"
        p.nth(1).drag_to(p.nth(0))
        pg.wait_for_function("() => document.querySelector('.pots__all > .hand-pot')?.dataset.provider === 'codex'", timeout=WAIT_MS)
        p = pots(pg)
        p.nth(1).click()
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.lifted.value).then((v) => /claude/.test(v))", timeout=WAIT_MS)       # the tool's card
        assert ("tools.order", {"order": ["codex", "claude"]}) in host.log
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_in_danger_takes_the_second_place_and_says_its_share_in_the_dangers_colour_under_its_bottle(gui):
    limits = [tool("claude", "Claude Code", 0.62), tool("agy", "Antigravity", 0.85), tool("codex", "Codex", 0.04), tool("cursor", "Cursor", 0.45)]
    pg, host, log = open_mana(gui, limits)
    try:
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)
        pg.wait_for_timeout(500)
        assert front_of(pg) == "claude"
        assert visible_potions(pg) == ["claude", "codex", "agy"], "the tool the work goes to, then the one at the danger's level, then the person's order"
        danger = pg.locator('.pots__row .pot-s[data-provider="codex"]')
        assert "is-danger" in danger.locator(".ork-potion").get_attribute("class") and danger.get_attribute("data-level") == "danger"
        five = danger.locator(".pot-s__five")
        assert five.inner_text() == "4%" and five.evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const i = document.createElement('i'); i.style.color = 'var(--ork-danger)'; document.body.append(i); const v = getComputedStyle(i).color; i.remove(); return v; }")
        assert pg.locator('.pots__row .pot-s.is-front[data-provider="claude"] .pot-s__five').inner_text() == "62%"
        assert pg.locator('.pots__row .pot-s.is-front[data-provider="claude"] .pot-s__five').evaluate("e => getComputedStyle(e).fontWeight") == "600", "the tool the work goes to has its share in the ink, bold"
        shot(pg, "wide-row-danger")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tool_at_the_warn_level_stands_in_the_row_too_one_that_is_dry_says_out_and_the_list_says_when_it_is_back(gui):
    soon = {"provider": "codex", "name": "Codex", "left": 0.0, "rows": [{"window": "5h", "left": 0.0, "reset": "2026-10-20T14:00:00"}, {"window": "week", "left": 0.5, "reset": "2026-10-24T09:00:00"}]}
    limits = [tool("claude", "Claude Code", 0.62), tool("agy", "Antigravity", 0.85), soon, tool("cursor", "Cursor", 0.18)]
    pg, host, log = open_mana(gui, limits)
    try:
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        assert visible_potions(pg) == ["claude", "codex", "cursor"], "the alerts before the person's order"
        dry = pg.locator('.pots__row .pot-s[data-provider="codex"]')
        assert dry.locator(".pot-s__five").inner_text() == "out" and "is-danger" in dry.get_attribute("class")
        assert pg.locator('.pots__row .pot-s[data-provider="cursor"]').get_attribute("data-level") == "warn"
        assert pg.locator('.pots__row .pot-s[data-provider="cursor"] .pot-s__five').evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const i = document.createElement('i'); i.style.color = 'var(--ork-alert)'; document.body.append(i); const v = getComputedStyle(i).color; i.remove(); return v; }")
        unroll(pg)
        back = pg.locator('.pots__all .hand-pot[data-provider="codex"]').inner_text()
        assert "back" in back, back                                                                                            # the list says when it is back
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_front_is_the_open_tabs_tool_and_the_picked_goal_at_works_tool_and_nothing_the_person_does_reorders_the_row(gui):
    host = HandHost()
    host.limits = SIX[:4]
    host.mana = {"main": "claude", "now": "claude", "until": None, "moved": None, "paid": None}
    next(p for p in host.parties if p["slug"] == "design")["tool"] = "agy"
    host.nodes.append(node("sail", "design", "A goal at work", "table", state="working", element="ice", tool="cursor", tasks=[task("w1", "Do it", "running")]))
    pg, host, log = open_hand(gui, host)
    try:
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        assert front_of(pg) == "claude"                                                                                          # the project's tab: the tool now
        pg.locator('[data-tab="design"]').click()
        pg.wait_for_function("() => document.querySelector('.pots__row .pot-s')?.dataset.provider === 'agy'", timeout=WAIT_MS)
        assert front_of(pg) == "agy"                                                                                             # the open tab's tool
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => { m.picked.value = 'sail'; })")
        pg.wait_for_function("() => document.querySelector('.pots__row .pot-s')?.dataset.provider === 'cursor'", timeout=WAIT_MS)
        assert front_of(pg) == "cursor"                                                                                          # the picked goal at work: its tool
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => { m.picked.value = ''; })")
        pg.wait_for_function("() => document.querySelector('.pots__row .pot-s')?.dataset.provider === 'agy'", timeout=WAIT_MS)
        before = visible_potions(pg)
        p = pots(pg)                                                                                                             # hover, press: the row is not reordered
        p.nth(0).click()
        pg.mouse.move(640, 300)
        pg.wait_for_timeout(300)
        assert visible_potions(pg) == before and front_of(pg) == "agy"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_smaller_bottle_says_the_week_under_its_share_and_the_large_one_does_not(gui):
    limits = [tool("claude", "Claude Code", 0.9), {"provider": "codex", "name": "Codex", "left": 0.05, "rows": [{"window": "5h", "left": 0.05, "reset": ""}, {"window": "week", "left": 0.35, "reset": ""}]},
              {"provider": "agy", "name": "Antigravity", "left": 0.8, "rows": [{"window": "5h", "left": 0.8, "reset": ""}, {"window": "week", "left": 0.2, "reset": ""}]}]
    pg, host, log = open_mana(gui, limits)
    try:
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        large, codex, agy = (pg.locator(f'.pots__row .pot-s[data-provider="{t}"]') for t in ("claude", "codex", "agy"))
        assert large.get_attribute("data-size") == "large" and large.locator(".pot-s__week").count() == 0, "the large bottle says the 5 hours alone"
        assert codex.get_attribute("data-size") == "medium" and codex.locator(".pot-s__week").all_inner_texts() == ["week", "35%"]      # a smaller bottle: the week, and its share
        assert agy.get_attribute("data-size") == "small" and agy.locator(".pot-s__week").all_inner_texts() == ["week", "20%"] and agy.locator(".pot-s__five").inner_text() == "80%"
        assert "size-medium" in codex.locator(".ork-potion").get_attribute("class") and "size-small" in agy.locator(".ork-potion").get_attribute("class")
        tops = pg.locator(".pots__row .ork-potion").evaluate_all("els => els.map((e) => e.getBoundingClientRect().top)")
        assert len(set(tops)) == 1, "their tops on one line"
        head = pg.locator(".release-lane__head").bounding_box()
        for loc in (large, codex, agy):
            b = loc.bounding_box()
            assert head["y"] <= b["y"] and b["y"] + b["height"] <= head["y"] + head["height"] + 1, (b, head)                     # all within the head
        shot(pg, "wide-row-weeks")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_more_than_six_tools_are_five_potions_and_a_plus_n_that_opens_all_of_them_at_the_narrow_width(gui):
    pg, host, log = open_mana(gui, EIGHT, "narrow")
    try:
        p = pots(pg)
        assert [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex", "agy", "cursor", "hermes", None]
        more = pg.locator(".hand-pot--more")
        assert more.inner_text().strip() == "+3" and more.get_attribute("aria-label") == "3 more tools: what is left of them"
        assert pg.locator(".hand-mana .ork-potion").count() == 5
        shot(pg, "narrow-eight")
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


def test_a_tool_whose_limits_were_not_read_is_its_mark_alone_and_its_words_say_so(gui):
    pg, host, log = open_mana(gui, [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", None)])
    try:
        p = pots(pg)
        codex = p.nth(1)
        assert codex.locator(".hand-pot__share").inner_text() == "" and codex.get_attribute("aria-label") == "Codex: Limits not read"
        assert codex.locator(".ork-potion").count() == 0                                                           # no bottle (spec 140 C1)
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


def test_no_limits_no_mana(gui):
    pg, host, log = open_mana(gui, [])
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-mana").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_no_goal_at_all_the_potions_still_lie_in_the_right_columns_head(gui):
    host = HandHost(empty=True)
    host.limits = TWO
    pg, host, log = open_hand(gui, host)
    try:
        p = pots(pg)
        pg.locator(".hand-plus.is-large").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        box = pg.locator(".pots__row").bounding_box()
        assert p.count() == 2 and box["x"] + box["width"] <= pg.viewport_size["width"] + 1 and box["y"] + box["height"] <= pg.viewport_size["height"] + 1, "the potions lie in the right column's head, inside the window"
        shot(pg, "wide-empty")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the default's frame (docs/specs/105 §4.1–§4.2, decisions §177.1) ---------------------------------------------------------------------------

def mana_of(main="claude", now="", paid=None, moved=None, until=None):
    return {"main": main, "now": main if now == "" else now, "until": until, "moved": moved, "paid": paid}


PAID = {"tool": "agy", "name": "Antigravity", "until": "2026-10-29T18:00", "usd_task": 0.4}


def open_default(gui, limits, mana, width="wide", pinned=None):
    host = HandHost()
    host.limits, host.mana = limits, mana
    for slug, provider in (pinned or {}).items():
        next(p for p in host.parties if p["slug"] == slug)["tool"] = provider
    return open_hand(gui, host, width)


def box(loc):
    return loc.bounding_box()


def same_box(a, b, tol=1):
    return all(abs(a[k] - b[k]) <= tol for k in ("x", "y", "width", "height"))


def framed_on(pg):
    """The tool the default lies on. Under 760 px: the provider (or "paid") the frame lies on, the one place whose box the frame's box is and the one `data-default` says. At the wide width there is no frame: the tool the work goes to (the row's first) is the default (decisions §261.13)."""
    pg.wait_for_timeout(450)                                                                                                    # the slide or the turn is over
    if pg.viewport_size["width"] >= 760:
        return front_of(pg)
    frame = pg.locator(".hand-mana__frame")
    assert not frame.evaluate("e => e.hidden")
    on = pg.locator('.hand-mana [data-default="1"]')
    assert on.count() == 1
    assert same_box(box(frame), box(on)), (box(frame), box(on))
    return "paid" if on.get_attribute("data-paid") else on.get_attribute("data-provider")


def settle(pg, host):
    host.bump({})
    pg.wait_for_timeout(100)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_frame_is_on_the_tool_now_on_the_projects_tab_with_its_words(gui, width):
    pg, host, log = open_default(gui, TWO, mana_of("claude", "codex", until="2026-10-29T18:00"), width)
    try:
        p = pots(pg)
        assert framed_on(pg) == "codex"
        if width == "wide":
            assert pg.locator(".hand-mana__frame").count() == 0 and pg.locator('.hand-mana [data-default="1"]').count() == 0, "no frame at the wide width: the front is the default"
            assert p.nth(1).get_attribute("aria-label") == "Codex: 18% of the week left" and p.nth(0).get_attribute("aria-label") == "Claude Code: 62% of the week left"
            assert pg.locator(".pots__row .pot-s.is-front").get_attribute("aria-label") == "Codex: 18% of the week left" and visible_potions(pg)[0] == "codex"
        else:
            assert p.nth(1).get_attribute("aria-label") == "Codex: 18% of the week left, the default" and p.nth(1).get_attribute("title") == p.nth(1).get_attribute("aria-label")
            assert p.nth(0).get_attribute("aria-label") == "Claude Code: 62% of the week left" and p.nth(0).get_attribute("data-default") is None
            assert pg.locator('.hand-mana [data-default="1"]').count() == 1                                                          # one place is framed
            assert pg.locator(".hand-mana__frame").evaluate("e => getComputedStyle(e).clipPath") != "none"                           # orkUI's notch
            assert pg.locator(".hand-mana__frame").evaluate("e => getComputedStyle(e).borderTopWidth") == "2px"
        shot(pg, f"{width}-default-moved")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_frame_is_on_the_main_tool_with_nothing_said_and_on_the_first_with_no_mana_at_all(gui):
    pg, host, log = open_default(gui, TWO, mana_of("codex"))
    try:
        pots(pg)
        assert framed_on(pg) == "codex"                                                                                          # now = main: the Main tool
        host.mana = {**mana_of("claude"), "now": None}                                                                           # every tool is out: the Main tool keeps the frame
        settle(pg, host)
        assert framed_on(pg) == "claude"
        host.mana = None
        settle(pg, host)
        assert framed_on(pg) == "claude"                                                                                         # the host says nothing: the first
        host.mana = mana_of("", None)
        settle(pg, host)
        assert framed_on(pg) == "claude"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_partys_tab_frames_its_own_tool_and_the_tool_now_when_it_has_none(gui):
    pg, host, log = open_default(gui, SIX, mana_of("claude", "agy"), pinned={"design": "codex"})
    try:
        pots(pg)
        assert framed_on(pg) == "agy"                                                                                            # the project's tab: the tool now
        pg.locator('[data-tab="design"]').click()
        assert framed_on(pg) == "codex"                                                                                          # a party set to Codex on purpose
        shot(pg, "wide-default-pinned")
        pg.locator('[data-tab="tech"]').click()
        assert framed_on(pg) == "agy"                                                                                            # a party that follows: the tool now
        pg.locator('[data-tab="orkmaster"]').click()
        assert framed_on(pg) == "agy"
        host.mana = mana_of("claude", "claude")                                                                                  # the Main tool is back: every following tab goes with it
        settle(pg, host)
        assert framed_on(pg) == "claude"
        pg.locator('[data-tab="design"]').click()
        assert framed_on(pg) == "codex"                                                                                          # a pinned tool is never moved
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_row_follows_the_active_tool_by_itself_and_nothing_shifts(gui):
    pg, host, log = open_default(gui, SIX, mana_of("claude", "claude"))
    try:
        pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)
        assert framed_on(pg) == "claude"
        before = pg.locator(".pots__row").bounding_box(), pg.locator(".release-lane__head").bounding_box()
        host.mana = mana_of("claude", "agy")
        settle(pg, host)
        assert framed_on(pg) == "agy" and visible_potions(pg)[0] == "agy"
        assert (pg.locator(".pots__row").bounding_box(), pg.locator(".release-lane__head").bounding_box()) == before            # the row and the head do not move or change size
        shot(pg, "wide-row-turned")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_frame_slides_between_places_and_nothing_shifts(gui):
    pg, host, log = open_default(gui, SIX, mana_of("claude", "claude"), "narrow")
    try:
        p = pots(pg)
        assert framed_on(pg) == "claude"
        before = [box(b) for b in p.all()]
        borders = p.evaluate_all("els => els.map(e => { const s = getComputedStyle(e); return [s.borderTopWidth, s.borderTopColor, s.borderTopStyle]; })")
        assert all(b[0] == "2px" and b[1] == "rgba(0, 0, 0, 0)" and b[2] == "solid" for b in borders), borders               # every potion keeps a transparent border of the frame's width
        frame = pg.locator(".hand-mana__frame")
        assert frame.evaluate("e => getComputedStyle(e).transitionProperty") == "transform" and frame.evaluate("e => getComputedStyle(e).transitionDuration") == "0.18s"      # --ork-motion-base
        host.mana = mana_of("claude", "agy")
        settle(pg, host)
        assert frame.evaluate("e => getComputedStyle(e).transform").startswith("matrix")
        assert framed_on(pg) == "agy"
        assert [box(b) for b in p.all()] == before                                                                               # no potion moved
        assert same_box(box(frame), box(p.nth(2)))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_lifted_card_keeps_the_frame_and_says_the_default_before_what_it_spends(gui):
    pg, host, log = open_default(gui, TWO, mana_of("claude", "claude"))
    try:
        p = pots(pg)
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        _press(pg, "export")
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert p.nth(0).get_attribute("aria-label") == "Claude Code: 62% of the week left. This card takes about 4% of it"          # the default is said by the row's first at the wide width, no more in the label
        assert framed_on(pg) == "claude"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_while_going_on_paid_holds_the_paid_tool_is_a_slot_after_the_potions_and_the_front_of_the_drum(gui, width):
    limits = [tool("claude", "Claude Code", 0.0), tool("codex", "Codex", 0.0), tool("cursor", "Cursor", 0.0), tool("hermes", "Hermes", 0.0)]
    pg, host, log = open_default(gui, limits, mana_of("claude", "agy", paid=PAID), width)
    try:
        p = pots(pg)
        pg.wait_for_timeout(300)
        assert [b.get_attribute("data-provider") for b in p.all()] == ["claude", "codex", "cursor", "hermes", "agy"]            # the paid tool after the potions
        slot = pg.locator(".hand-pot--paid")
        assert slot.count() == 1 and slot.get_attribute("data-paid") == "1"
        assert slot.locator("use").get_attribute("href").endswith("/icons/icons.svg#coins")                                      # orkUI's coins
        assert slot.locator(".ork-potion").count() == 0 and slot.locator(".hand-pot__share").inner_text() == "API"
        assert slot.locator(".hand-pot__sub").inner_text() == "≈$0.40"
        words = slot.get_attribute("aria-label")
        assert words.startswith("Antigravity paid by its API: no limit, about $0.40 a task, going on until ") and words.endswith(", the default" if width == "narrow" else "") and slot.get_attribute("title") == words
        assert framed_on(pg) == "paid"
        if width == "narrow":
            assert pg.locator('.hand-mana [data-default="1"]').count() == 1 and p.nth(0).get_attribute("data-default") is None       # the frame is on it, no potion has it
        else:
            assert pg.locator('.pots__row .pot-s.is-paid.is-front[data-provider="agy"]').count() == 1       # the front is its place: the tool's mark where the bottle stands, API under it
            assert pg.locator('.pots__row .pot-s.is-front .pot-s__five').inner_text() == "API"
        shot(pg, f"{width}-default-paid")
        boxes = [box(b) for b in p.all()]
        mana, hand = (pg.locator(".hand-mana").bounding_box() if width == "narrow" else None), pg.locator(".hand").bounding_box()
        if width == "narrow":
            assert boxes[4]["y"] > boxes[0]["y"] + 40 and boxes[4]["x"] >= boxes[3]["x"] - 1                                         # five places: two rows of three, the slot in the second
            assert mana["y"] + mana["height"] <= hand["y"] + hand["height"] + 1 and mana["x"] + mana["width"] == pytest.approx(pg.viewport_size["width"], abs=1)
        else:
            assert boxes[4]["y"] >= boxes[3]["y"] and all(b["x"] >= 0 and b["x"] + b["width"] <= pg.viewport_size["width"] for b in boxes)       # the unrolled list: the paid slot after the potions, inside the window
        narrow.no_sideways(pg)
        slot.click()
        pg.locator('.table-over[data-kind="limits"]').wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["props"] == {"provider": "agy"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_paid_slot_with_no_known_cost_says_so_and_has_no_price(gui):
    pg, host, log = open_default(gui, TWO, mana_of("claude", "agy", paid={**PAID, "usd_task": None, "until": None}))
    try:
        pots(pg)
        slot = pg.locator(".hand-pot--paid")
        assert slot.count() == 1 and slot.locator(".hand-pot__sub").count() == 0
        assert slot.get_attribute("aria-label") == "Antigravity paid by its API: no limit, its cost is not known yet"
        assert framed_on(pg) == "paid"
        host.mana = mana_of("claude", "claude")                                                                                  # the yes ended with the reset: the slot goes, the front goes back
        settle(pg, host)
        pg.wait_for_function("() => !document.querySelector('.hand-pot--paid')")
        assert framed_on(pg) == "claude"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- who drinks from a potion (spec 111 §3.4, decisions §189.2) ---------------------------------------------------------------------------------


def lit(pg):
    return sorted(pg.locator(".table-tab.is-lit").evaluate_all("els => els.map((e) => e.dataset.tab)"))
