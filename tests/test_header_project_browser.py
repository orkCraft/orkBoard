"""The project in the Orkmaster's header (docs/specs/161-the-tables-look-and-the-rooms-things.md stage J, decisions §272.5), in a real browser at 1280 x 800 against the hand's stub host: the header's first line is the project's name
and its second the kind and stage in the caption face (*Game · Being made*); *The Orkmaster* is in the `aria-label` and the `title`, not in the visible words; the stage or the kind pressed deals its choices to the hand as 144 x 202 cards,
the present one marked, each with its one line; a card pressed sends `ideas.stage_set` or `ideas.project_kind_set` once; *Put it back* and Esc send nothing. The narrow page keeps its head. Screenshots to $HEADER_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

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




LONG = "The long-running party game for twelve friends who all play across three time zones every Friday"


class LongHost(ProjectHost):
    """The project has a very long name (spec 168 B3)."""

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["projects"] = {"current": "/p/long", "open": [{"path": "/p/long", "name": LONG, "needs_you": 0, "working": 0}], "recent": []}
        return doc




def test_the_stage_pressed_deals_three_cards_the_present_marked_and_a_card_sends_stage_set_once(gui):
    pg, host, log = opened(gui)
    try:
        pg.locator('.col-head__pick[data-deal="stage"]').click()
        ways = pg.locator(".hand-ways-row .hand-ans")
        ways.first.wait_for(timeout=WAIT_MS)
        assert ways.count() == 3 and [w.locator(".hand-ans__name").inner_text().strip() for w in ways.all()] == ["Idea", "Being made", "Live"]
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


