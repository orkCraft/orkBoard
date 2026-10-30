"""The quick question on the page (docs/specs/106-a-quick-question.md §3, decisions §181), in a real browser against the table's stub host, at the two widths of `tests/narrow.py`: one line at the top of the pane, *Ask the
Orkmaster…* on the Orkmaster's tab and *Ask the <its leader's role>…* on a party's; Enter sends `ideas.ask` with the tab's party and empties the field, an empty field sends nothing; while it is read the field is off and a line says who reads;
the answer lies on its tab only, with the asker's head, the question, the answer in the body face, its sources and ×, which sends `ideas.ask_clear`; *Make it a goal* tells the host and opens the new goal's field with the line written; none
over an open page; a letter typed in the field does not open the new goal's field. Screenshots to $ASK_SHOTS when it is set."""
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


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


def record(status="answered", party="", **more):
    return {"status": status, "party": party, "q": "Why does the timer run on the server?", "answer": ANSWER if status == "answered" else "", "sources": ["§142", "Round timer shows on every phone"] if status == "answered" else [],
            "goal": GOAL if status == "answered" else "", "at": "2026-10-29T10:00:00", "error": "", **more}


class AskHost(TableHost):
    """The table's host that keeps one question as the real host does: `ask` is in the snapshot, `ideas.ask` makes it *asking* (answered by the test when it wants), `ideas.ask_clear` removes it."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ask = None

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
        return super().handle(name, a)

    def sent(self, name):
        return [a for n, a in self.log if n == name]


@pytest.fixture(params=narrow.WIDTHS)
def asked(gui, request):
    """The window at one of the two widths against an AskHost: `(page, host, width)`; the page's errors are asserted at the end."""
    errors: list[str] = []
    server, browser = gui
    host = AskHost()
    pg = narrow.page(browser, request.param)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-ask__field").wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def field(pg):
    return pg.locator(".table-ask__field")


def test_the_line_is_at_the_top_of_the_pane_with_the_orkmasters_words_and_a_partys_leaders(asked):
    pg, host, w = asked
    f = field(pg)
    assert f.get_attribute("placeholder") == "Ask the Orkmaster…" and f.get_attribute("aria-label") == "Ask the Orkmaster" and f.get_attribute("maxlength") == "500"
    assert pg.locator("form.table-ask").count() == 0 and pg.locator("form.table-ask__form").count() == 1 and "ork-field" in f.get_attribute("class")
    title, line, body = pg.locator(".table-title").bounding_box(), pg.locator(".table-ask").bounding_box(), pg.locator(".table-body").bounding_box()
    assert title["y"] + title["height"] <= line["y"] + 1 and line["y"] <= body["y"] + body["height"] / 2                       # under the title, at the top of the pane
    assert pg.get_by_role("button").filter(has_text="Ask").count() == 0                                                         # no button besides Enter
    open_tab(pg, "tech")
    assert field(pg).get_attribute("placeholder") == "Ask the Architect…" and field(pg).get_attribute("aria-label") == "Ask the Architect"       # its leader seat's name
    open_tab(pg, "art")
    assert field(pg).get_attribute("placeholder") == "Ask the Art…"
    narrow.no_sideways(pg)
    shot(pg, f"{w}-line.png")


def test_enter_sends_the_question_with_the_tabs_party_and_empties_the_field_an_empty_line_sends_nothing(asked):
    pg, host, w = asked
    field(pg).focus()
    pg.keyboard.press("Enter")
    pg.keyboard.type("   ")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(200)
    assert host.sent("ideas.ask") == []
    field(pg).fill("Where is the lobby goal?")
    pg.keyboard.press("Enter")
    pg.wait_for_function("() => document.querySelector('.table-ask__reading')", timeout=WAIT_MS)
    assert host.sent("ideas.ask") == [{"party": "", "q": "Where is the lobby goal?"}]
    host.put(None)
    pg.wait_for_function("() => !document.querySelector('.table-ask__reading')", timeout=WAIT_MS)
    assert field(pg).input_value() == ""                                                                                         # emptied once it was sent
    open_tab(pg, "tech")
    field(pg).fill("Why this way?")
    pg.keyboard.press("Enter")
    pg.wait_for_function("() => document.querySelector('.table-ask__reading')", timeout=WAIT_MS)
    assert host.sent("ideas.ask")[-1] == {"party": "tech", "q": "Why this way?"}


def test_while_it_is_read_the_field_is_off_and_a_line_says_who_reads(asked):
    pg, host, w = asked
    host.put(record("asking", ""))
    reading = pg.locator(".table-ask__reading")
    reading.wait_for(timeout=WAIT_MS)
    assert reading.inner_text() == "The Orkmaster is reading…" and reading.locator(".ork-busy").count() == 1 and field(pg).is_disabled()
    host.put(record("asking", "tech"))
    pg.wait_for_function("() => document.querySelector('.table-ask__reading').textContent.includes('Architect')", timeout=WAIT_MS)
    assert reading.inner_text() == "The Architect is reading…"
    open_tab(pg, "tech")
    assert field(pg).is_disabled() and pg.locator(".table-ask__answer").count() == 0
    shot(pg, f"{w}-reading.png")
    host.put(record("answered", "tech"))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    assert field(pg).is_enabled() and pg.locator(".table-ask__reading").count() == 0


def test_the_answer_lies_on_its_tab_only_with_the_head_the_question_the_sources_and_a_cross(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    box = pg.locator(".table-ask__answer")
    box.wait_for(timeout=WAIT_MS)
    assert "ork-panel" in box.get_attribute("class") and "/races/peon-crown" in box.locator("img.ork-race__head").get_attribute("src")        # the Orkmaster's crowned head
    assert box.locator(".table-ask__q").inner_text() == "Why does the timer run on the server?"
    text = box.locator(".table-ask__text")
    assert text.inner_text() == ANSWER and text.evaluate("e => getComputedStyle(e).whiteSpace") == "pre-wrap"                              # its line breaks kept
    faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.table-ask__text')).fontFamily, getComputedStyle(document.querySelector('.table-title__pt')).fontFamily]")
    assert faces[0] != faces[1]                                                                                                          # the body face, never the pixel face
    assert [s.inner_text() for s in box.locator(".table-ask__src").all()] == ["§142", "Round timer shows on every phone"]
    open_tab(pg, "tech")
    assert pg.locator(".table-ask__answer").count() == 0                                                                                 # asked on the Orkmaster's tab: not on a party's
    host.put(record("answered", "tech"))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    assert "/races/peon-elder" in pg.locator(".table-ask__answer img.ork-race__head").get_attribute("src")                               # the party's leader's head
    open_tab(pg, "orkmaster")
    assert pg.locator(".table-ask__answer").count() == 0
    host.put(record("failed", "", error="No answer came: ask again"))
    pg.locator(".table-ask__answer .table-ask__err").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-ask__err").inner_text() == "No answer came: ask again"
    narrow.no_sideways(pg)
    host.put(record("answered", ""))
    pg.locator(".table-ask__text").wait_for(timeout=WAIT_MS)
    shot(pg, f"{w}-answer.png")


def test_a_cross_puts_the_answer_away(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Put away").click()
    pg.wait_for_selector(".table-ask__answer", state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{}] and host.ask is None


def test_make_it_a_goal_tells_the_host_and_opens_the_new_goals_field_with_the_line_written_the_record_stays(asked):
    pg, host, w = asked
    open_tab(pg, "tech")
    host.put(record("answered", "tech"))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Make it a goal").click()
    area = pg.locator(".hand-field textarea")
    area.wait_for(timeout=WAIT_MS)
    assert area.input_value() == GOAL and host.sent("ideas.ask_goal") == [{}]
    assert "Tech" in pg.locator(".hand-field__chips").inner_text()                                                                       # addressed to the open tab's party, as the field always is
    assert pg.locator(".table-ask__answer").count() == 1                                                                                 # the record stays until ×
    shot(pg, f"{w}-goal.png")


def test_a_goal_less_answer_has_no_button(asked):
    pg, host, w = asked
    host.put(record("answered", "", goal=""))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Make it a goal").count() == 0


def test_none_over_an_open_page(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)
    pg.locator(".hand-die").click()                                                                                                          # Play, the die in the hand, opens over the pane
    pg.locator(".table-over").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-ask").count() == 0
    pg.get_by_role("button", name="Back").click()
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    pg.locator(".table-ask__answer").wait_for(timeout=WAIT_MS)                                                                           # back: the line and the answer are there again


def test_a_letter_typed_in_the_line_does_not_open_the_new_goals_field(asked):
    pg, host, w = asked
    field(pg).focus()
    pg.keyboard.type("hello")
    assert field(pg).input_value() == "hello" and pg.locator(".hand-field").count() == 0
    if w == "wide":                                                                                                                      # the control: with nothing focused the same key opens it
        field(pg).fill("")
        pg.evaluate("() => document.activeElement.blur()")
        pg.keyboard.press("q")
        pg.locator(".hand-field").wait_for(timeout=WAIT_MS)
        assert field(pg).input_value() == ""
