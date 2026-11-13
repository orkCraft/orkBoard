"""Spec 135 part B, the backlog's groups in the hand (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §B.2; decisions §242.5), at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch),
against a `HandHost` with the row `groups`: one card in the hand, *These look like one goal*, with the page sign and the Orkmaster as its asker; lifted, each group a block of its goals' titles with their heads, its
why and **Join** / **Keep apart**, and **Not now** at its foot; the answers go as `ideas.groups_answer` / `ideas.groups_now`, a lifted card tells the host (`ideas.groups_open`), the cost of a worded decision is said
as a share, and nothing counts what waits. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

HEAD = {"race": "peon", "tier": "elder"}
ROW = {"kind": "groups", "id": "2026-11-04T09:00:00", "idea": "", "goal": "", "title": "", "text": "", "blocks": False, "priority": "normal", "at": "2026-11-04T09:01:00", "cost": None,
       "groups": [{"id": "g-1", "why": "Both change how dark mode is switched", "adds": [],
                   "goals": [{"idea": "dark-a", "title": "Add a dark mode option", "party": "tech", "head": HEAD}, {"idea": "dark-b", "title": "Dark mode needs a timer", "party": "tech", "head": HEAD}]},
                  {"id": "g-2", "why": "The same footer", "adds": ["design"],
                   "goals": [{"idea": "foot-a", "title": "Tidy the footer", "party": "tech", "head": HEAD}, {"idea": "foot-b", "title": "Footer links in a row", "party": "design", "head": HEAD}]}]}


class GroupsHost(HandHost):
    """Four parties and nothing waiting but the row `groups`."""

    def __init__(self, row=None):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = [dict(row or ROW)]
        self.refuse = False

    def handle(self, name, a):
        if name == "ideas.groups_open":
            self.log.append((name, a))
            return {"ok": True}
        if name in ("ideas.groups_answer", "ideas.groups_now"):
            self.log.append((name, a))
            if self.refuse:
                return {"error": "No goals wait to be joined"}
            self.needs = []
            return self.bump({"ok": True})
        return super().handle(name, a)


@pytest.fixture(params=narrow.WIDTHS)
def groups(gui, request):
    pg, host, log = open_hand(gui, host=GroupsHost(), width=request.param)
    pg.locator('.hand-card[data-kind="groups"]').first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    pg.close()
    assert not log, "\n".join(log)


def front(pg):
    return pg.locator('.hand-card[data-kind="groups"]').first


def lifted(pg):
    front(pg).click(position={"x": 10, "y": 24})
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    return pg.locator(".hand-lifted")






def test_every_group_is_answered_then_the_answer_goes_and_the_card_leaves(groups):
    pg, host, w = groups
    card_ = lifted(pg)
    blocks = card_.locator(".hand-group")
    blocks.nth(0).get_by_role("button", name="Join").click()
    pg.wait_for_timeout(300)
    assert _calls(pg, host, "ideas.groups_answer", ms=200) == [], "one group is not every group"
    assert blocks.nth(0).get_by_role("button", name="Join").get_attribute("aria-pressed") == "true"
    blocks.nth(1).get_by_role("button", name="Keep apart").click()
    assert _calls(pg, host, "ideas.groups_answer") == [{"id": ROW["id"], "join": ["g-1"], "apart": ["g-2"]}]
    pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"groups\"]')", timeout=WAIT_MS)


def test_not_now_sends_it_and_the_card_leaves(groups):
    pg, host, w = groups
    card_ = lifted(pg)
    card_.get_by_role("button", name="Not now").click()
    assert _calls(pg, host, "ideas.groups_now") == [{"id": ROW["id"]}]
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"groups\"]')", timeout=WAIT_MS)




