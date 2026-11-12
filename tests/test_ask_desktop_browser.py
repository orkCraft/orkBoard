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


def test_a_head_pressed_opens_the_bubble_under_it_the_field_focused_the_tail_under_its_centre(asked):
    pg, host, w = asked
    assert bubble(pg).count() == 0, "nothing open until a head is pressed"
    opened(pg)
    f = field(pg)
    assert f.get_attribute("placeholder") == "Ask the Orkmaster…" and f.get_attribute("aria-label") == "Ask the Orkmaster" and f.get_attribute("maxlength") == "500" and "ork-field" in f.get_attribute("class")
    assert focused(pg) == f.get_attribute("class"), "the field has the focus from the press itself"
    b, h = bubble(pg).bounding_box(), head(pg).bounding_box()
    assert bubble(pg).get_attribute("role") == "dialog" and b["y"] >= h["y"] + h["height"] and b["width"] <= 440.5
    tail = pg.evaluate("() => parseFloat(document.querySelector('.table-ask__tail').style.left)")
    assert abs(b["x"] + tail + 8 - (h["x"] + h["width"] / 2)) <= 1, "its tail under the head's centre"
    assert bubble(pg).locator(".table-ask__name").inner_text().lower() == "the orkmaster" and "/races/peon-crown" in bubble(pg).locator("img.ork-race__head").get_attribute("src")
    assert bubble(pg).locator(".table-ask__seat").count() == 0, "the Orkmaster has no seat to change"
    shot(pg, f"{w}-bubble-ask.png")
    open_tab(pg, "tech")
    assert bubble(pg).count() == 0, "another tab: put away"
    opened(pg, "tech")
    assert field(pg).get_attribute("placeholder") == "Ask the Architect…" and field(pg).get_attribute("aria-label") == "Ask the Architect"       # its leader seat's name
    assert bubble(pg).locator(".table-ask__name").inner_text().lower() == "the architect" and "/races/peon-elder" in bubble(pg).locator("img.ork-race__head").get_attribute("src")
    open_tab(pg, "art")
    opened(pg, "art")
    assert field(pg).get_attribute("placeholder") == "Ask the Art…"


def test_the_bubble_is_kept_inside_the_window_its_tail_still_under_the_head(gui):
    pg, host, errors = start(gui, "wide")
    try:
        heads(pg, left=1228)
        opened(pg)
        b, h = bubble(pg).bounding_box(), head(pg).bounding_box()
        assert b["x"] >= 16 - 0.5 and b["x"] + b["width"] <= 1280 - 16 + 0.5
        tail = pg.evaluate("() => parseFloat(document.querySelector('.table-ask__tail').style.left)")
        assert abs(b["x"] + tail + 8 - (h["x"] + h["width"] / 2)) <= 1
        pg.set_viewport_size({"width": 800, "height": 700})
        heads(pg, left=740)
        pg.wait_for_timeout(100)
        settled(pg)
        b = bubble(pg).bounding_box()
        assert b["x"] + b["width"] <= 800 - 16 + 0.5 and b["x"] >= 15.5
        shot(pg, "wide-bubble-edge.png")
    finally:
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


def test_the_field_is_kept_when_the_bubble_is_closed(asked):
    pg, host, w = asked
    opened(pg)
    field(pg).fill("Why is the lobby slow")
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.ask") == [] and host.sent("ideas.ask_clear") == []
    opened(pg)
    assert field(pg).input_value() == "Why is the lobby slow"


def test_while_it_is_read_the_question_is_muted_and_a_line_says_who_reads(asked):
    pg, host, w = asked
    open_tab(pg, "tech")
    opened(pg, "tech")
    host.put(record("asking", "tech"))
    reading = pg.locator(".table-ask__reading")
    reading.wait_for(timeout=WAIT_MS)
    assert reading.inner_text() == "The Architect is reading the table" and "ork-think" in reading.get_attribute("class") and field(pg).count() == 0
    assert bubble(pg).locator(".table-ask__q").inner_text() == "Why does the timer run on the server?" and bubble(pg).get_attribute("data-state") == "reading"
    shot(pg, f"{w}-bubble-reading.png")
    host.put(record("asking", ""))                                                                                               # the Orkmaster is asked: this one is only off, and says who reads
    pg.wait_for_function("() => document.querySelector('.table-ask__bubble').dataset.state === 'asking'", timeout=WAIT_MS)
    assert field(pg).is_disabled() and reading.inner_text() == "The Orkmaster is reading the table"
    host.put(record("answered", "tech"))
    pg.locator(".table-ask__text").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-ask__reading").count() == 0


def test_the_answer_with_the_question_the_sources_make_it_a_goal_and_ask_more_on_its_tab_only(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    opened(pg)
    box = bubble(pg)
    assert box.get_attribute("data-state") == "answered" and field(pg).count() == 0, "opening it shows the answer"
    assert "/races/peon-crown" in box.locator("img.ork-race__head").get_attribute("src")                                           # the Orkmaster's crowned head
    assert box.locator(".table-ask__q").inner_text() == "Why does the timer run on the server?"
    text = box.locator(".table-ask__text")
    assert text.inner_text() == ANSWER and text.evaluate("e => getComputedStyle(e).whiteSpace") == "pre-wrap"                      # its line breaks kept
    faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.table-ask__text')).fontFamily, getComputedStyle(document.querySelector('.table-title__pt')).fontFamily]")
    # decisions §291.1: the pixel face is gone; the text and the headings are both Rubik (IBM Plex Mono only for code, paths and ids)
    assert faces[0].startswith("Rubik") and faces[1].startswith("Rubik"), faces
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


def test_a_failure_is_said_in_its_words(asked):
    pg, host, w = asked
    host.put(record("failed", "", error="No answer came: ask again"))
    opened(pg)
    assert pg.locator(".table-ask__err").inner_text() == "No answer came: ask again" and bubble(pg).get_attribute("data-state") == "failed"
    assert pg.locator(".table-ask__err").get_attribute("role") == "alert"
    bubble(pg).get_by_role("button", name="Ask again").click()
    field(pg).wait_for(timeout=WAIT_MS)
    narrow.no_sideways(pg)


def test_a_cross_on_an_answer_puts_it_away_on_the_field_it_only_closes(asked):
    pg, host, w = asked
    opened(pg)
    bubble(pg).get_by_role("button", name="Put away").click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [] and head(pg).evaluate("e => e === document.activeElement")
    host.put(record("answered", ""))
    opened(pg)
    bubble(pg).get_by_role("button", name="Put away").click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{}] and host.ask is None
    assert head(pg).evaluate("e => e === document.activeElement"), "the head keeps the focus"


def test_esc_and_a_press_outside_close_it_the_answer_stays_the_head_has_the_focus(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    opened(pg)
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert head(pg).evaluate("e => e === document.activeElement"), "Esc: the focus is back on the head"
    opened(pg)
    pg.mouse.click(300, 600)                                                                                                     # a press outside
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [] and host.ask is not None, "the answer stays until it is put away"
    pg.wait_for_function("() => document.activeElement === document.querySelector('[data-ask-head=orkmaster]')", timeout=WAIT_MS)
    opened(pg)
    assert bubble(pg).get_attribute("data-state") == "answered", "opening it again shows the answer"
    head(pg).click()                                                                                                             # the head again puts it away
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)


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


def test_a_goal_less_answer_has_no_button(asked):
    pg, host, w = asked
    host.put(record("answered", "", goal=""))
    opened(pg)
    assert pg.get_by_role("button", name="Make it a goal").count() == 0 and pg.get_by_role("button", name="Ask more").count() == 1


def test_the_foot_names_the_leaders_seat_and_change_opens_its_popover_esc_closing_that_first(asked):
    pg, host, w = asked
    open_tab(pg, "tech")
    opened(pg, "tech")
    seat = bubble(pg).locator(".table-ask__seat")
    assert " ".join(seat.inner_text().split()) == "Its seat: Claude · Veteran Change" and "harness-claude-ink" in seat.locator(".ork-mark").get_attribute("src")
    seat.get_by_role("button", name="Change").click()
    pop = pg.locator(".table-seatpop")
    pop.wait_for(timeout=WAIT_MS)
    assert pop.get_attribute("data-seat") == "architect" and pg.locator(".table-ask__pop .table-seatpop").count() == 1
    assert pop.bounding_box()["y"] >= bubble(pg).bounding_box()["y"] + bubble(pg).bounding_box()["height"] - 1, "under the bubble"
    shot(pg, f"{w}-bubble-seat.png")
    pg.keyboard.press("Escape")
    pop.wait_for(state="detached", timeout=WAIT_MS)
    assert bubble(pg).count() == 1, "the first Esc closes the popover only"
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)


def test_none_over_an_open_page(asked):
    pg, host, w = asked
    host.put(record("answered", ""))
    opened(pg)
    pg.locator(".hand-die__play").click()                                                                                              # Play, the die in the hand, opens over the pane
    pg.locator(".table-over").wait_for(timeout=WAIT_MS)
    assert bubble(pg).count() == 0
    pg.get_by_role("button", name="Back").click()
    pg.wait_for_selector(".table-over", state="detached", timeout=WAIT_MS)
    assert bubble(pg).count() == 0, "put away: it does not come back by itself"
    opened(pg)
    assert pg.locator(".table-ask__text").count() == 1, "the answer is there again"


def test_a_letter_typed_in_the_field_does_not_open_the_new_goals_field(asked):
    pg, host, w = asked
    opened(pg)
    pg.keyboard.type("hello")
    assert field(pg).input_value() == "hello" and pg.locator(".hand-field").count() == 0


def test_the_evening_line_opens_the_bubble_once_a_day_for_a_party_and_is_drawn_at_its_top(asked):
    pg, host, w = asked
    host.since = SINCE
    heads(pg, "tech")                                                                                                            # the head is there when the tab opens, as it is the tab's own
    open_tab(pg, "tech")
    bubble(pg).wait_for(timeout=WAIT_MS)
    settled(pg)
    line = bubble(pg).locator(".cn-since")
    assert line.get_attribute("data-way") == "away" and "Since your last look:" in line.inner_text() and SINCE["line"] in line.inner_text()
    assert bubble(pg).locator(".table-ask__who + .cn-since").count() == 1 and field(pg).count() == 1, "at the top, over the field"
    shot(pg, f"{w}-bubble-evening.png")
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    open_tab(pg, "orkmaster")
    open_tab(pg, "tech")
    pg.wait_for_timeout(400)
    assert bubble(pg).count() == 0, "seen today: it does not open by itself again"
    opened(pg, "tech")
    assert bubble(pg).locator(".cn-since").count() == 1, "but it is drawn while the day lasts"
    keys = pg.evaluate("() => Object.keys(localStorage).filter((k) => k.startsWith('orkboard.ask.evening.'))")
    assert len(keys) == 1 and keys[0].startswith("orkboard.ask.evening.tech.")


def test_the_evening_line_without_local_storage_opens_once_while_the_page_lasts(gui):
    host = AskHost()
    host.since = SINCE
    pg, host, errors = start(gui, "wide", host, init="Object.defineProperty(window, 'localStorage', { get() { throw new Error('no storage'); } });")
    try:
        heads(pg, "tech")
        open_tab(pg, "tech")
        bubble(pg).wait_for(timeout=WAIT_MS)
        settled(pg)
        pg.keyboard.press("Escape")
        bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
        open_tab(pg, "orkmaster")
        open_tab(pg, "tech")
        pg.wait_for_timeout(400)
        assert bubble(pg).count() == 0
    finally:
        pg.context.close()
    assert not [e for e in errors if "no storage" in e or "pageerror" in e], "\n".join(errors)


def test_a_party_with_no_evening_line_does_not_open_by_itself(asked):
    pg, host, w = asked
    open_tab(pg, "tech")
    pg.wait_for_timeout(500)
    assert bubble(pg).count() == 0


def test_under_760_px_no_head_opens_a_bubble(gui):
    pg, host, errors = start(gui, "narrow")
    try:
        heads(pg)
        host.put(record("answered", ""))
        pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.openAsk('orkmaster'))")
        pg.wait_for_timeout(300)
        assert bubble(pg).count() == 0
        assert pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.askOpen.value)") is None, "put away at once"
        narrow.no_sideways(pg)
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_touch_screen_at_the_wide_width_opens_none_either(gui):
    server, browser = gui
    errors: list[str] = []
    host = AskHost()
    pg = browser.new_context(viewport={"width": 1000, "height": 700}, has_touch=True).new_page()
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    try:
        pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.openAsk('orkmaster'))")
        pg.wait_for_timeout(300)
        assert bubble(pg).count() == 0
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_add_to_the_goal_is_offered_on_an_answer_about_a_goal_in_analysis_and_sends_the_words_as_written(asked):
    """Spec 132 A (decisions §234.5): the answer's `goal_in_analysis` makes **Add to the goal** (`ideas.add_to_goal {idea, text, via: "bubble"}`: the question's words), the record is put away; a goal-less answer has none."""
    pg, host, w = asked
    host.put(record("answered", "", goal_in_analysis="timer"))
    opened(pg)
    button = pg.get_by_role("button", name="Add to the goal")
    assert button.count() == 1 and "primary" in button.get_attribute("class").split() and "Make it a goal" in bubble(pg).inner_text()
    shot(pg, f"{w}-bubble-add.png")
    button.click()
    pg.wait_for_function("() => !document.querySelector('.table-ask__bubble')", timeout=WAIT_MS)
    assert host.sent("ideas.add_to_goal") == [{"idea": "timer", "text": "Why does the timer run on the server?", "via": "bubble"}]
    pg.wait_for_function("() => document.body.innerText.includes('Added to the goal')", timeout=WAIT_MS)
    assert host.sent("ideas.ask_clear") == [{}]


def test_add_to_the_goal_says_the_decision_is_worded_again_and_its_cost(asked):
    pg, host, w = asked
    host.reworded = True
    host.put(record("answered", "", goal_in_analysis="timer"))
    opened(pg)
    pg.get_by_role("button", name="Add to the goal").click()
    pg.wait_for_function("() => document.body.innerText.includes('words its decision again')", timeout=WAIT_MS)
    assert "of Claude" in pg.locator("body").inner_text() or "at API prices" in pg.locator("body").inner_text()


def test_an_answer_about_no_goal_in_analysis_has_no_add_to_the_goal(asked):
    pg, host, w = asked
    host.put(record("answered", "", goal_in_analysis=""))
    opened(pg)
    assert pg.get_by_role("button", name="Add to the goal").count() == 0
