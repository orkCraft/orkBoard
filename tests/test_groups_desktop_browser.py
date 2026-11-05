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
from tests.test_table_desktop_browser import shot  # noqa: E402

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


def test_the_groups_are_one_card_with_the_page_sign_the_first_groups_titles_and_the_orkmaster_as_asker(groups):
    pg, host, w = groups
    assert pg.locator('.hand-card[data-kind="groups"]').count() == 1
    c = front(pg)
    assert c.locator(".hand-card__name").text_content().strip() == "Add a dark mode option + Dark mode needs a timer"
    assert c.locator(".corner--top .ork-sign.page").count() == 1
    asker = c.locator(".corner--foot .ork-race__head")
    assert asker.count() == 1 and "crown" in asker.get_attribute("src"), "the Orkmaster asks"
    assert c.locator(".ork-gem").count() == 0, "no worded decision: no cost"
    if w == "wide":
        assert c.locator(".hand-card__foot").text_content().strip() == "These look like one goal"
    narrow.no_sideways(pg)


def test_lifted_each_group_lists_its_goals_with_their_heads_its_why_and_its_two_answers_and_not_now_is_at_the_foot(groups):
    pg, host, w = groups
    card_ = lifted(pg)
    assert card_.locator(".hand-way > .ork-label").first.inner_text().lower() == "these look like one goal"
    blocks = card_.locator(".hand-group")
    assert blocks.count() == 2
    first = blocks.nth(0)
    assert [" ".join(li.inner_text().split()) for li in first.locator("li").all()] == ["Add a dark mode option", "Dark mode needs a timer"]
    assert first.locator("li .ork-race__head").count() == 2 and first.locator('[data-part="why"]').inner_text() == "Both change how dark mode is switched"
    assert [b.inner_text().strip() for b in first.locator(".ork-btn").all()] == ["Join", "Keep apart"]
    assert blocks.nth(1).locator('[data-part="adds"]').inner_text().startswith("Brings in ") and blocks.nth(0).locator('[data-part="adds"]').count() == 0
    assert [b.inner_text().strip() for b in card_.locator(".hand-group__foot .ork-btn").all()] == ["Not now"]
    shot(pg, f"groups-hand-{w}.png")
    narrow.no_sideways(pg)


def test_lifting_tells_the_host_and_putting_it_back_lets_it_go(groups):
    pg, host, w = groups
    card_ = lifted(pg)
    assert _calls(pg, host, "ideas.groups_open") == [{"id": ROW["id"], "open": True}]
    card_.get_by_role("button", name="Put it back").click() if w == "wide" else pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    assert _calls(pg, host, "ideas.groups_open", at_least=2) == [{"id": ROW["id"], "open": True}, {"id": ROW["id"], "open": False}]


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


def test_a_refused_answer_keeps_the_card_lifted(groups):
    pg, host, w = groups
    host.refuse = True
    card_ = lifted(pg)
    card_.get_by_role("button", name="Not now").click()
    assert _calls(pg, host, "ideas.groups_now") == [{"id": ROW["id"]}]
    pg.wait_for_timeout(300)
    assert pg.locator(".hand-lifted").count() == 1 and pg.locator('.hand-card[data-kind="groups"]').count() >= 1


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_worded_decision_says_its_cost_as_a_share_under_the_buttons(gui, width):
    row = {**ROW, "groups": ROW["groups"][:1], "cost": {"calls": 1, "usd_high": 0.08}}
    pg, host, log = open_hand(gui, host=GroupsHost(row), width=width)
    pg.locator('.hand-card[data-kind="groups"]').first.wait_for(timeout=WAIT_MS)
    card_ = lifted(pg)
    words = card_.locator(".hand-spend").inner_text()
    assert "of Claude's" in words or "at API prices" in words
    assert card_.locator(".hand-group").count() == 1
    pg.close()
    assert not log, "\n".join(log)
