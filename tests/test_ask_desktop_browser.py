"""The quick question as the open leader's bubble (docs/specs/123-the-leaders-at-the-table.md §6, which changes docs/specs/106-a-quick-question.md §3, decisions §181, §201), in a real browser against the table's stub host.
The head that opens it is the tabs' (spec 123 F; the open tab's head is a button carrying `data-ask-head="<tab>"`); the tests press it. The bubble stands under the head,
its tail under the head's centre, at most 440 px wide, kept inside the window; asking: the field focused in the press, Enter sends `ideas.ask` with the tab's party and empties it, an empty field sends nothing, the field is kept when it is closed;
reading: the question muted and *The <Leader> is reading the map*; answered: the answer in the body face with its line breaks, its sources, **Make it a goal** (tells the host, opens the new goal's field with the line written) and *Ask more*;
failed: its error; × on an answer sends `ideas.ask_clear`, Esc, × on the field and a press outside only close it, the focus back to the head; the foot (*Its seat: Claude · Veteran*, **Change** opens the seat's popover, Esc closes that first);
the evening line (`since` of the party's record) opens it once a day for a party and is drawn at its top; none over an open page, none under 760 px. Screenshots to $ASK_SHOTS when it is set."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, open_tab  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["ASK_SHOTS"]) if os.environ.get("ASK_SHOTS") else None
GOAL = "Show the round timer on the host's screen"
ANSWER = "Tech decided the timer runs on the server (§142).\nThe phones only show it."
BUBBLE = ".table-ask__bubble"
FIELD = ".table-ask__field"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


def record(status="answered", party="", **more):
    return {"status": status, "party": party, "q": "Why does the timer run on the server?", "answer": ANSWER if status == "answered" else "", "sources": ["§142", "Round timer shows on every phone"] if status == "answered" else [],
            "goal": GOAL if status == "answered" else "", "at": "2026-10-29T10:00:00", "error": "", **more}


SINCE = {"line": "Two goals went toward clean edges; one broke the lobby.", "way": "away", "at": "2026-10-29T07:00:00"}


class AskHost(TableHost):
    """The table's host that keeps one question as the real host does: `ask` is in the snapshot, `ideas.ask` makes it *asking* (answered by the test when it wants), `ideas.ask_clear` removes it; `since`: the evening line the party
    Tech's record carries (`ideas.concerns`)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ask = None
        self.since = None
        self.reworded = False

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["ask"] = self.ask
        return doc

    def put(self, ask):
        self.ask = ask
        self.ws.send(json.dumps(self.snapshot()))

    def handle(self, name, a):
        if name == "ideas.ask":
            self.log.append((name, a))
            self.ask = record("asking", a["party"], q=a["q"])
            self.ws.send(json.dumps(self.snapshot()))
            return {"ok": True}
        if name == "ideas.ask_clear":
            self.log.append((name, a))
            self.ask = None
            self.ws.send(json.dumps(self.snapshot()))
            return {"ok": True}
        if name == "ideas.ask_goal":
            self.log.append((name, a))
            return {"ok": True}
        if name == "ideas.add_to_goal":
            self.log.append((name, a))
            return {"ok": True, "idea": a["idea"], "reworded": self.reworded, **({"cost": {"calls": 1, "usd_high": 0.4}} if self.reworded else {})}
        if name == "ideas.concerns" and a.get("party") == "tech" and self.since:
            self.log.append((name, a))
            return {"at": "2026-10-29T08:00:00", "map_hash": "h1", "by": "architect", "status": "ready", "error": "", "measure": None, "concerns": [], "dismissed": [], "rubric": None, "since": self.since}
        return super().handle(name, a)

    def sent(self, name):
        return [a for n, a in self.log if n == name]


def start(gui, width, host=None, init=""):
    errors: list[str] = []
    server, browser = gui
    host = host or AskHost()
    pg = narrow.page(browser, width)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    if init:
        pg.add_init_script(init)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, errors


def heads(pg, tab="orkmaster", left=920, top=4):
    """The tabs' open head is the real head now (spec 123 F: a button carrying `data-ask-head="<tab>"` in the open tab's cell): nothing to stand in for it. Kept for the tests that name it."""


def head(pg, tab="orkmaster"):
    return pg.locator(f'[data-ask-head="{tab}"]')


def bubble(pg):
    return pg.locator(BUBBLE)


def field(pg):
    return pg.locator(FIELD)


def opened(pg, tab="orkmaster"):
    if head(pg, tab).count() == 0:
        heads(pg, tab)
    head(pg, tab).click()
    bubble(pg).wait_for(timeout=WAIT_MS)
    settled(pg)


def settled(pg):
    """The bubble has stopped popping up (its box is where it stays)."""
    pg.wait_for_function("() => { const b = document.querySelector('.table-ask__bubble'); return !b || b.getAnimations().length === 0; }", timeout=WAIT_MS)


def focused(pg):
    return pg.evaluate("() => document.activeElement && (document.activeElement.className || document.activeElement.tagName)")


@pytest.fixture
def asked(gui):
    """The window at the wide width against an AskHost: `(page, host, "wide")`; the page's errors are asserted at the end."""
    pg, host, errors = start(gui, "wide")
    heads(pg)
    yield pg, host, "wide"
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)






def test_enter_sends_the_question_with_the_tabs_party_and_empties_the_field_an_empty_line_sends_nothing(asked):
    pg, host, w = asked
    opened(pg)
    pg.keyboard.press("Enter")
    pg.keyboard.type("   ")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(200)
    assert host.sent("ideas.ask") == []
    field(pg).fill("Where is the lobby goal?")
    pg.keyboard.press("Enter")
    pg.locator(".table-ask__reading").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.ask") == [{"party": "", "q": "Where is the lobby goal?"}]
    host.put(None)
    pg.wait_for_function("() => !document.querySelector('.table-ask__reading')", timeout=WAIT_MS)
    assert field(pg).input_value() == ""                                                                                         # emptied once it was sent
    open_tab(pg, "tech")
    opened(pg, "tech")
    field(pg).fill("Why this way?")
    pg.keyboard.press("Enter")
    pg.locator(".table-ask__reading").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.ask")[-1] == {"party": "tech", "q": "Why this way?"}






def test_the_answer_with_the_question_the_sources_make_it_a_goal_and_ask_more_on_its_tab_only(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    opened(pg)
    box = bubble(pg)
    assert box.get_attribute("data-state") == "answered" and field(pg).count() == 0, "opening it shows the answer"
    assert "/races/peon-crown" in box.locator("img.ork-race__head").get_attribute("src")                                           # the Orkmaster's crowned head
    assert box.locator(".table-ask__q").inner_text() == "Why does the timer run on the server?"
    text = box.locator(".table-ask__text")
    assert text.inner_text() == ANSWER
    assert [s.inner_text() for s in box.locator(".table-ask__src").all()] == ["§142", "Round timer shows on every phone"]
    assert "primary" in box.get_by_role("button", name="Make it a goal").get_attribute("class").split()
    shot(pg, f"{w}-bubble-answer.png")
    box.get_by_role("button", name="Ask more").click()
    field(pg).wait_for(timeout=WAIT_MS)
    assert focused(pg) == field(pg).get_attribute("class") and box.locator(".table-ask__text").count() == 0 and host.sent("ideas.ask_clear") == []
    open_tab(pg, "tech")
    opened(pg, "tech")
    assert pg.locator(".table-ask__text").count() == 0 and field(pg).count() == 1, "asked on the Orkmaster's tab: not on a party's"
    host.put(record("answered", "tech"))
    pg.locator(".table-ask__text").wait_for(timeout=WAIT_MS)
    assert "/races/peon-elder" in bubble(pg).locator("img.ork-race__head").get_attribute("src")                                    # the party's leader's head
    open_tab(pg, "orkmaster")
    opened(pg)
    assert pg.locator(".table-ask__text").count() == 0








def test_make_it_a_goal_tells_the_host_and_opens_the_new_goals_field_with_the_line_written_the_record_stays(asked):
    pg, host, w = asked
    open_tab(pg, "tech")
    host.put(record("answered", "tech"))
    opened(pg, "tech")
    pg.get_by_role("button", name="Make it a goal").click()
    area = pg.locator(".hand-field textarea")
    area.wait_for(timeout=WAIT_MS)
    assert area.input_value() == GOAL and host.sent("ideas.ask_goal") == [{}]
    assert "Tech" in pg.locator(".hand-field__chips").inner_text()                                                               # addressed to the open tab's party, as the field always is
    assert bubble(pg).count() == 0 and host.ask is not None, "the bubble gives way; the record stays until it is put away"
    shot(pg, f"{w}-bubble-goal.png")
























