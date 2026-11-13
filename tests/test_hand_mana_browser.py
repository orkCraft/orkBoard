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
from tests.test_hand_desktop_browser import HandHost, open_hand, sig  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["MANA_SHOTS"]) if os.environ.get("MANA_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def tool(provider, name, left, window="week"):
    return {"provider": provider, "name": name, "left": left, "rows": [{"window": window, "left": left, "reset": ""}] if left is not None else []}


TWO = [tool("claude", "Claude Code", 0.62), tool("codex", "Codex", 0.18)]


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










# -- the default's frame (docs/specs/105 §4.1–§4.2, decisions §177.1) ---------------------------------------------------------------------------

def mana_of(main="claude", now="", paid=None, moved=None, until=None):
    return {"main": main, "now": main if now == "" else now, "until": until, "moved": moved, "paid": paid}






def box(loc):
    return loc.bounding_box()






def settle(pg, host):
    host.bump({})
    pg.wait_for_timeout(100)


















# -- who drinks from a potion (spec 111 §3.4, decisions §189.2) ---------------------------------------------------------------------------------


def lit(pg):
    return sorted(pg.locator(".table-tab.is-lit").evaluate_all("els => els.map((e) => e.dataset.tab)"))
