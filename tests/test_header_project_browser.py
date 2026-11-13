"""The project in the Orkmaster's header (docs/specs/161-the-tables-look-and-the-rooms-things.md stage J, decisions §272.5), in a real browser at 1280 x 800 against the hand's stub host: the header's first line is the project's name
and its second the kind and stage in the caption face (*Game · Being made*); *The Orkmaster* is in the `aria-label` and the `title`, not in the visible words; the stage or the kind pressed deals its choices to the hand as 144 x 202 cards,
the present one marked, each with its one line; a card pressed sends `ideas.stage_set` or `ideas.project_kind_set` once; *Put it back* and Esc send nothing. The narrow page keeps its head. Screenshots to $HEADER_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["HEADER_SHOTS"]) if os.environ.get("HEADER_SHOTS") else None
CARD = lambda name, craft, frm: {"id": craft, "name": name, "line": "", "craft": craft, "leader": craft, "from": frm, "locked": False}  # noqa: E731
OFFERED = {"idea": [CARD("Game design", "game-design", "idea"), CARD("Art", "art", "idea"), CARD("Release", "release", "idea")],
           "being_made": [CARD("Game design", "game-design", "idea"), CARD("Art", "art", "idea"), CARD("Tech", "tech", "being_made"), CARD("Release", "release", "idea")],
           "live": [CARD("Game design", "game-design", "idea"), CARD("Tech", "tech", "being_made"), CARD("LiveOps", "liveops", "live"), CARD("Marketing", "marketing", "live"), CARD("Release", "release", "idea")]}


class ProjectHost(HandHost):
    """The hand's host that also says the project's stage and kind (`ideas.stage`) and keeps what is set."""

    def __init__(self):
        super().__init__()
        self.stage, self.kind = "being_made", "game"

    def stage_doc(self):
        return {"stage": self.stage, "read": "idea", "kept": True, "kind": self.kind, "offered": OFFERED}

    def handle(self, name, a):
        if name == "ideas.stage":
            self.log.append((name, a))
            return self.stage_doc()
        if name == "ideas.stage_set":
            self.log.append((name, a))
            self.stage = a["stage"]
            return self.stage_doc()
        if name == "ideas.project_kind_set":
            self.log.append((name, a))
            self.kind = a["kind"]
            return {"kind": {"id": self.kind, "words": self.kind}}
        return super().handle(name, a)


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def opened(gui, width="wide"):
    pg, host, log = open_hand(gui, host=ProjectHost(), width=width)
    if width == "wide":
        pg.locator(".col-head__sub").wait_for(timeout=WAIT_MS)
    return pg, host, log


def sent(host, name):
    return [a for n, a in host.log if n == name]


def test_the_header_says_the_projects_name_then_its_kind_and_stage_and_the_orkmaster_only_in_its_label(gui):
    pg, host, log = opened(gui)
    try:
        head = pg.locator(".col-head")
        tab = head.locator(".col-head__tab")
        name = tab.locator(".col-head__nm")
        sub = head.locator(".col-head__sub")
        assert sub.text_content().strip() == "Game · Being made"
        assert name.inner_text().strip() and "orkmaster" not in head.inner_text().lower(), "The Orkmaster leaves the visible header"
        assert tab.get_attribute("aria-label").startswith("The Orkmaster · ") and tab.get_attribute("title").startswith("The Orkmaster: "), "its label and title still name it"
        assert head.get_attribute("aria-label") == "The Orkmaster"
        assert head.locator(".ork-pennant").count() == 1 and tab.locator(".ork-race__head").count() == 1, "its head and pennant stay"
        a, b = name.bounding_box(), sub.bounding_box()
        assert b["y"] > a["y"] + a["height"] - 2, "the kind and stage on the second line"
        assert abs(a["x"] - b["x"]) <= 2, "under the name"
        assert sub.evaluate("e => getComputedStyle(e).fontSize") in ("12px", "13px", "11px", "14px")
        box = head.bounding_box()
        assert b["y"] + b["height"] <= box["y"] + box["height"], "inside the head"
        shot(pg, "header")
    finally:
        pg.close()
    assert not log, "\n".join(log)


LONG = "The long-running party game for twelve friends who all play across three time zones every Friday"


class LongHost(ProjectHost):
    """The project has a very long name (spec 168 B3)."""

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["projects"] = {"current": "/p/long", "open": [{"path": "/p/long", "name": LONG, "needs_you": 0, "working": 0}], "recent": []}
        return doc


def test_a_long_projects_name_takes_two_lines_then_is_cut_whole_in_its_title_and_the_kind_and_stage_stay_on_one_line(gui):
    """Spec 168 B3 (decisions §283.13): the column keeps its 160 px; the name in its head takes two lines, then is cut with an ellipsis, whole in its `title`; *Game · Being made* is one line, cut."""
    pg, host, log = open_hand(gui, host=LongHost(), width="wide")
    try:
        pg.locator(".col-head__sub").wait_for(timeout=WAIT_MS)
        name, sub, head = pg.locator(".col-head__nm"), pg.locator(".col-head__sub"), pg.locator(".col-head")
        assert name.get_attribute("title") == LONG, "whole in its title (and so on hover)"
        lines = name.evaluate("e => { const s = getComputedStyle(e); return [Math.round(e.getBoundingClientRect().height / parseFloat(s.lineHeight)), s.webkitLineClamp || s.lineClamp, e.scrollHeight > e.clientHeight + 1]; }")
        assert lines[0] == 2 and str(lines[1]) == "2" and lines[2] is True, f"two lines, then cut ({lines})"
        assert pg.locator(".frame-column").bounding_box()["width"] == 160, "the column keeps its 160 px"
        a, b, box = name.bounding_box(), sub.bounding_box(), head.bounding_box()
        assert b["y"] >= a["y"] + a["height"] - 2 and b["y"] + b["height"] <= box["y"] + box["height"], "the kind and stage under the two lines, inside the head"
        assert sub.evaluate("e => [getComputedStyle(e).whiteSpace, getComputedStyle(e).overflowX, Math.round(e.getBoundingClientRect().height)]")[:2] == ["nowrap", "hidden"] and b["height"] <= 16, "one line, cut"
        shot(pg, "header-long")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_stage_pressed_deals_three_cards_the_present_marked_and_a_card_sends_stage_set_once(gui):
    pg, host, log = opened(gui)
    try:
        pg.locator('.col-head__pick[data-deal="stage"]').click()
        ways = pg.locator(".hand-ways-row .hand-ans")
        ways.first.wait_for(timeout=WAIT_MS)
        assert ways.count() == 3 and [w.locator(".hand-ans__name").inner_text().strip() for w in ways.all()] == ["Idea", "Being made", "Live"]
        for w in ways.all():
            assert w.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [120, 168]
        marked = pg.locator(".hand-ways-row .hand-ans[data-pick='1']")
        assert marked.count() == 1 and marked.locator(".hand-ans__name").inner_text().strip() == "Being made"
        assert ways.nth(2).locator(".hand-ans__line").inner_text().strip() == "LiveOps and Marketing join the chair's crafts"
        assert ways.nth(1).locator(".hand-ans__line").inner_text().strip() == "Tech joins the chair's crafts"
        assert pg.locator(".hand-row").evaluate("e => e.inert"), "the rest of the hand sinks"
        assert pg.locator(".hand-lifted--asked").get_attribute("aria-label").startswith("The Orkmaster asks")
        shot(pg, "stage-dealt")
        ways.nth(2).click()
        got = _calls(pg, host, "ideas.stage_set")
        assert got == [{"stage": "live"}], got
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        assert pg.locator(".col-head__sub").text_content().strip() == "Game · Live"
        assert not pg.locator(".hand-row").evaluate("e => e.inert")
        assert len(sent(host, "ideas.stage_set")) == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_put_it_back_and_the_present_card_and_esc_send_nothing_for_the_stage(gui):
    pg, host, log = opened(gui)
    try:
        press = pg.locator('.col-head__pick[data-deal="stage"]')
        press.click()
        pg.get_by_role("button", name="Put it back").click()
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        press.click()
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        press.click()
        pg.locator(".hand-ways-row .hand-ans[data-pick='1']").click()
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert sent(host, "ideas.stage_set") == [] and sent(host, "ideas.project_kind_set") == []
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_kind_pressed_deals_the_kinds_the_present_marked_and_a_card_sends_the_kind_once(gui):
    pg, host, log = opened(gui)
    try:
        pg.locator('.col-head__pick[data-deal="kind"]').click()
        ways = pg.locator(".hand-ways-row .hand-ans")
        ways.first.wait_for(timeout=WAIT_MS)
        names = [w.locator(".hand-ans__name").inner_text().strip() for w in ways.all()]
        assert names[0] == "Empty folder" and "Game" in names and "Web app" in names and len(names) == 10, names
        marked = pg.locator(".hand-ways-row .hand-ans[data-pick='1']")
        assert marked.count() == 1 and marked.locator(".hand-ans__name").inner_text().strip() == "Game"
        assert all(w.locator(".hand-ans__line").inner_text().strip() for w in ways.all()), "each with its line"
        shot(pg, "kind-dealt")
        pg.locator('.hand-ways-row .hand-ans[data-way="web"]').scroll_into_view_if_needed()
        pg.locator('.hand-ways-row .hand-ans[data-way="web"]').click()
        got = _calls(pg, host, "ideas.project_kind_set")
        assert got == [{"kind": "web"}], got
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        assert pg.locator(".col-head__sub").text_content().strip() == "Web app · Being made"
        assert len(sent(host, "ideas.project_kind_set")) == 1
        pg.locator('.col-head__pick[data-deal="kind"]').click()
        pg.get_by_role("button", name="Put it back").click()
        pg.wait_for_selector(".hand-ways-row", state="detached", timeout=WAIT_MS)
        assert len(sent(host, "ideas.project_kind_set")) == 1, "Put it back sends nothing"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_page_keeps_its_head(gui):
    pg, host, log = opened(gui, width="narrow")
    try:
        assert pg.locator(".col-head__sub:visible").count() == 0 and pg.locator(".col-head__pick:visible").count() == 0
        assert pg.locator('.table-tab[data-tab="orkmaster"]').count() == 1
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
