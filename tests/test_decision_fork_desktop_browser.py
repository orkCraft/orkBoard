"""The decision and a fork on the window (docs/specs/100-a-goals-way-as-cards.md §3, part C; docs/specs/99-a-goals-way.md §6–§7), in a real browser against a stub host answering the rows `decision` and `fork`, `ideas.page` and
the commands `ideas.confirm` and `ideas.fork_answer`, at the two widths of `tests/narrow.py`: the decision's card (its face *Decision <n>*, the Orkmaster's head, no gem, under the first lane; lifted its *Why* and its numbered points, *Edit*
opening the entry as a field on the card and sent as `text`, one button **Confirm and start**), a fork (its face *<A> and <B> disagree*, a leader's head; lifted the two sides dealt as cards over the pane, each its leader's head, what
it says, its why, a press throwing the side, *Or say it in your own words* throwing the person's words: spec 120 §6.7, `tests/test_hearing_browser.py` draws the hearing itself) and the goal's Spec on the pane with the sections of the two sides lit.
Screenshots to $DECISION_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, node, need, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["DECISION_SHOTS"]) if os.environ.get("DECISION_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


DECISION_TEXT = ("Why: Players talk before a round starts, and one room each keeps the talk readable. Design asked for it, Tech agreed.\n\n"
                 "1. The lobby has one chat room for everyone in the room.\n2. Design words the messages' look; Tech keeps the last fifty.\n3. No private messages in this goal.")
SIDES = [{"party": "design", "leader": "Design lead", "says": "A room holds ten players", "why": "The game is no fun with six."},
         {"party": "tech", "leader": "Tech lead", "says": "The server holds six players in a room", "why": "One server process cannot carry more."}]
SIDES2 = [{"party": "design", "leader": "Design lead", "says": "Show the clock on every phone", "why": "Nobody argues about the time."},
          {"party": "tech", "leader": "Tech lead", "says": "Only the host's screen shows the clock", "why": "Phones drift."}]

PAGES = {
    "rooms": [
        {"name": "Asked", "text": "A room should hold as many players as want in."}, {"name": "Gist", "text": "How many players a room holds."}, {"name": "Route", "text": "Design, then Tech"},
        {"name": "Design", "text": "### Why\nThe game is no fun with six.\n\n### Done when\n- A room holds ten players\n- The lobby shows who joined\n\n### Will be\n- changed lobby-screen — ten seats\n- new seat-list"},
        {"name": "Tech", "text": "### Why\nOne server process.\n\n### Done when\n- The server holds six players in a room\n- A seventh player is refused\n\n### Will be\n- changed server/rooms.ts — the cap"},
    ],
    "chat": [{"name": "Gist", "text": "Chat in the lobby."}, {"name": "Why", "text": "Players talk first."}, {"name": "Done when", "text": "- Messages show in the lobby\n- The last fifty are kept"}],
}


class DecisionHost(HandHost):
    """A project of four parties (Tech, Design, Product, Release), a goal `chat` of Design's whose decision waits (`confirmed` set for the failed-sections case), a goal `rooms` of Tech's with a fork between Design and Tech (and a second fork
    behind it when `two`)."""

    def __init__(self, two=False, confirmed=False):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = []
        self.forks = [dict(about="How many players a room holds", sides=SIDES, id="f1")]
        if two:
            self.forks.append(dict(about="Who shows the clock", sides=SIDES2, id="f2"))
        self.nodes.append(node("chat", "design", "Chat in the lobby", "hand", state="decided", element="ice"))
        self.nodes.append(node("rooms", "tech", "Rooms hold more players", "hand", state="sections", element="dust", route=["design", "tech"]))
        self.decision = need("decision", "design", "chat", "Players chat in the lobby, one room each", DECISION_TEXT, number=118, confirmed=confirmed,
                             error="The sections could not be written: the limits are spent" if confirmed else "")
        self.needs = [self.decision, self.fork_row()]
        self.refuse = False

    def fork_row(self):
        f = self.forks[0]
        sides = [{"dir": d, "kind": "side", "party": s["party"], "leaders": [s["party"]], "names": [s["leader"]], "also": [], "line": s["why"], "outcome": s["says"]} for s, d in zip(f["sides"], ("right", "left", "up"))]
        hearing = {"moment": "fork", "id": f["id"], "about": f["about"], "title": " and ".join(s["leader"] for s in f["sides"]) + " disagree", "sides": sides, "left_out": [], "own": True}
        return need("fork", "tech", "rooms", "Rooms hold more players", f["about"], id=f["id"], about=f["about"], sides=f["sides"], hearing=hearing)

    def handle(self, name, a):
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": a["slug"], "sections": PAGES.get(a["slug"], []), "state": "sections", "track": "tech"}
        if name == "ideas.confirm":
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The keeper is busy with this goal: a moment"}
            self.needs = [n for n in self.needs if n["kind"] != "decision"]
            return self.bump({"ok": True, "number": 118, "title": "Players chat in the lobby, one room each"})
        if name == "ideas.decision_change":
            self.log.append((name, a))
            return {"ok": True, "idea": a["idea"], "kept": bool(a.get("text")), "reworded": bool(a.get("say")), **({"cost": {"calls": 1, "usd_high": 0.4}} if a.get("say") else {})}
        if name == "ideas.throw":
            self.log.append((name, a))
            self.forks.pop(0)
            self.needs = [n for n in self.needs if n["kind"] != "fork"] + ([self.fork_row()] if self.forks else [])
            return self.bump({"ok": True})
        if name == "ideas.fork_answer":
            self.log.append((name, a))
            self.forks.pop(0)
            self.needs = [n for n in self.needs if n["kind"] != "fork"] + ([self.fork_row()] if self.forks else [])
            return self.bump({"ok": True})
        return super().handle(name, a)


def open_decision(gui, width="wide", **more):
    pg, host, log = open_hand(gui, host=DecisionHost(**more), width=width)
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg, goal):
    return pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')


def press(pg, goal):
    front(pg, goal).click(position={"x": 10, "y": 24})


def lifted(pg):
    return pg.locator(".hand-lifted")


def box(loc):
    return loc.bounding_box()


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_decision_is_a_card_with_its_number_the_orkmasters_head_and_no_gem_under_the_first_lane(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        c = front(pg, "chat")
        assert c.get_attribute("data-kind") == "decision"
        assert c.locator(".hand-card__name").text_content().strip() == "Players chat in the lobby, one room each" and c.locator(".corner--top .ork-elem.ice").count() == 1       # the goal's element and the decision's title
        assert c.locator(".corner--top .ork-sign.page").count() == 1 and c.locator(".corner--foot .ork-race__head").count() == 1
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Decision 118", "its face says its number, not the decision's text"
        assert c.locator(".ork-gem").count() == 0, "it spends nothing new"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="chat"]').count() == 1, "the whole goal's: under the first lane"
        shot(pg, f"{width}-decision-face")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_the_decision_says_why_and_its_numbered_points_and_has_one_button_that_confirms(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        press(pg, "chat")
        lifted(pg).wait_for(timeout=WAIT_MS)
        card = lifted(pg)
        assert "Players chat in the lobby, one room each" in card.locator(".hand-card__name").inner_text()
        assert card.locator(".hand-way__why .body").inner_text().startswith("Players talk before a round starts")
        pts = card.locator(".hand-way__points li")
        assert pts.count() == 3 and pts.first.inner_text().startswith("The lobby has one chat room"), "the points numbered, the Orkmaster's words"
        assert card.locator(".hand-way__points").evaluate("e => e.tagName") == "OL"
        assert card.locator(".hand-spend").count() == 0, "no gem, no cost line"
        assert " ".join(card.locator(".hand-lifted__kind").text_content().split()) == "Decision 118" and " ".join(card.text_content().split()).count("Decision 118") == 1, "its number is said once, beside what the card is"
        primaries = card.locator(".hand-answers .ork-btn.primary")
        assert primaries.count() == 1 and primaries.inner_text().strip() == "Confirm and start", "one button"
        assert [b.inner_text().strip() for b in card.locator(".hand-answers .ork-btn").all()] == ["Confirm and start", "Change…"]
        shot(pg, f"{width}-decision-lifted")
        narrow.no_sideways(pg)
        primaries.click()
        got = _calls(pg, host, "ideas.confirm")
        assert got == [{"idea": "chat"}], got
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"chat\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_change_opens_the_entry_as_a_field_on_the_card_and_what_is_written_is_sent_as_text(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        press(pg, "chat")
        lifted(pg).get_by_role("button", name="Change…").click()
        field = lifted(pg).locator("textarea.hand-way__entry")
        field.wait_for(timeout=WAIT_MS)
        seed = field.input_value()
        assert seed.startswith("## 118. Players chat in the lobby, one room each\n\nWhy: Players talk") and "3. No private messages" in seed
        assert lifted(pg).get_by_role("button", name="Change…").count() == 0 and lifted(pg).get_by_role("button", name="Cancel").count() == 1
        shot(pg, f"{width}-decision-editing")
        narrow.no_sideways(pg)
        field.fill("## 118. Players chat, one room\n\nWhy: It is enough.\n\n1. One room.\n2. Nothing private.")
        lifted(pg).get_by_role("button", name="Confirm and start").click()
        got = _calls(pg, host, "ideas.confirm")
        assert got == [{"idea": "chat", "text": "## 118. Players chat, one room\n\nWhy: It is enough.\n\n1. One room.\n2. Nothing private."}], got
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_change_then_cancel_and_confirm_sends_no_text_and_a_refusal_keeps_the_card(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        host.refuse = True
        press(pg, "chat")
        lifted(pg).get_by_role("button", name="Change…").click()
        lifted(pg).locator("textarea").fill("changed my mind")
        lifted(pg).get_by_role("button", name="Cancel").click()
        assert lifted(pg).locator("textarea").count() == 0 and lifted(pg).locator(".hand-way__points li").count() == 3, "back to the decision as worded"
        lifted(pg).get_by_role("button", name="Confirm and start").click()
        assert _calls(pg, host, "ideas.confirm") == [{"idea": "chat"}]
        pg.wait_for_timeout(300)
        assert lifted(pg).count() == 1, "refused: the card stays lifted"
    finally:
        pg.close()
    assert not [m for m in log if "pageerror" in m], "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_decision_written_already_asks_the_sections_again_and_has_no_change(gui, width):
    pg, host, log = open_decision(gui, width, confirmed=True)
    try:
        press(pg, "chat")
        card = lifted(pg)
        card.wait_for(timeout=WAIT_MS)
        assert card.get_by_role("button", name="Change").count() == 0
        assert "written already" in card.locator('[data-note="written"]').inner_text() and "limits are spent" in card.locator('[data-note="written"]').inner_text()
        card.get_by_role("button", name="Confirm and start").click()
        assert _calls(pg, host, "ideas.confirm") == [{"idea": "chat"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_fork_is_a_card_saying_who_disagrees_with_a_leaders_head_under_the_first_lane(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        c = front(pg, "rooms")
        assert c.get_attribute("data-kind") == "fork" and c.get_attribute("aria-label").startswith("A fork: "), "what the card is, in plain words"
        assert c.locator(".corner--top .ork-sign.question").count() == 1 and c.locator(".corner--foot .ork-race__head").count() == 1
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Design and Tech disagree"
        assert c.locator(".ork-gem").count() == 0
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="rooms"]').count() == 1
        shot(pg, f"{width}-fork-face")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_a_fork_is_a_hearing_over_the_pane_with_the_spec_lit_under_it_and_a_press_throws_a_side(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        press(pg, "rooms")
        pane = pg.locator('.table-over[data-kind="choose"]')
        pane.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-lifted").count() == 0 or not pg.locator(".hand-lifted").first.is_visible(), "the sides are the pane's, not an aside"
        hr = pane.locator('.hr[data-moment="fork"]')
        hr.wait_for(timeout=WAIT_MS)
        assert hr.locator(".hr-title").text_content().strip() == "Design lead and Tech lead disagree"
        sides = hr.locator(".hr-side")
        assert sides.count() == 2
        a, b = hr.locator('.hr-side[data-dir="right"]'), hr.locator('.hr-side[data-dir="left"]')
        assert a.locator(".hr-out__words").text_content().strip() == "A room holds ten players" and b.locator(".hr-out__words").text_content().strip() == "The server holds six players in a room"
        assert a.locator(".hr-head .ork-race__head").count() == 1 and b.locator(".hr-head .ork-race__head").count() == 1, "each its leader's head"
        assert a.locator(".hr-says").text_content().strip() == "The game is no fun with six." and b.locator(".hr-says").text_content().strip() == "One server process cannot carry more."
        assert [a.locator(".hr-who__names").text_content().strip(), b.locator(".hr-who__names").text_content().strip()] == ["Design lead", "Tech lead"]
        assert hr.locator(".hr-own").text_content().strip() == "Or say it in your own words"
        # the Spec page under the sides, the two sections lit
        page = pane.locator('.spec-page[data-kind="spec"]')
        page.wait_for(timeout=WAIT_MS)
        page.locator(".spec-section").first.wait_for(timeout=WAIT_MS)
        assert [x.text_content().strip() for x in page.locator(".spec-common dt").all()] == ["Asked", "Gist", "Route"]
        secs = page.locator(".spec-section")
        assert secs.count() == 2 and secs.nth(0).get_attribute("data-party") == "design" and secs.nth(1).get_attribute("data-party") == "tech"
        assert all(s.get_attribute("data-lit") == "1" and s.locator(".ork-race__head").count() == 1 and s.locator(".spec-section__flag").text_content().strip() == "Disagrees" for s in secs.all())
        assert [x.inner_text().strip() for x in secs.nth(0).locator(".spec-line.is-lit").all()] == ["A room holds ten players"], "the line that says what the side says"
        assert [x.inner_text().strip() for x in secs.nth(1).locator(".spec-line.is-lit").all()] == ["The server holds six players in a room"]
        done, will = secs.nth(0).locator('.spec-col[data-part="done"]'), secs.nth(0).locator('.spec-col[data-part="will"]')
        assert done.locator(".ork-label").text_content().strip() == "Done when" and will.locator(".ork-label").first.text_content().strip() == "Will be"
        assert will.locator(".spec-will__id").first.inner_text().strip() == "lobby-screen" and will.locator('[data-will="new"] .spec-will__id').inner_text().strip() == "seat-list"
        d, w = box(done), box(will)
        if width == "wide":
            assert d["x"] < w["x"] and abs(d["y"] - w["y"]) < 4, "Done when at the left, Will be at the right"
        else:
            assert w["y"] > d["y"], "at the narrow width the one is under the other"
        shot(pg, f"{width}-fork-lifted-spec-lit")
        narrow.no_sideways(pg)
        b.locator(".hr-side__btn").click()                                                          # a press on a side throws it at once
        got = _calls(pg, host, "ideas.throw")
        assert got == [{"idea": "rooms", "moment": "fork", "dir": "left"}], got
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"rooms\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_persons_own_words_throw_a_fork_as_text_and_the_next_fork_takes_the_pane(gui, width):
    pg, host, log = open_decision(gui, width, two=True)
    try:
        press(pg, "rooms")
        pg.locator('.table-over[data-kind="choose"] .hr').wait_for(timeout=WAIT_MS)
        pg.get_by_role("button", name="Or say it in your own words").click()
        field = pg.locator(".hr-field__text")
        field.wait_for(timeout=WAIT_MS)
        shot(pg, f"{width}-fork-other")
        field.fill("Eight players, and the server is told")
        pg.locator(".hr-field .ork-btn.primary").click()
        got = _calls(pg, host, "ideas.throw")
        assert got == [{"idea": "rooms", "moment": "fork", "text": "Eight players, and the server is told"}], got
        pg.wait_for_function("() => document.querySelector('.hr-title')?.textContent.trim() === 'Design lead and Tech lead disagree' && document.querySelector('.hr-side[data-dir=\"right\"] .hr-out__words')?.textContent.trim() === 'Show the clock on every phone'", timeout=WAIT_MS)
        assert pg.locator(".hr-card").evaluate("(el) => !el.classList.contains('is-away')"), "the next fork's card is on the pane"
        pg.get_by_role("button", name="Put it back").click()
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        assert [n for n, _a in host.log if n == "ideas.throw"] == ["ideas.throw"], "put back throws nothing"
        assert front(pg, "rooms").count() == 1, "the fork is still in the hand"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_spec_page_alone_lights_nothing_and_reads_a_page_of_before_as_one_section_of_its_party(gui, width):
    pg, host, log = open_decision(gui, width)
    try:
        call(pg, "frame/state.js", "openOver", "spec", {"idea": "chat"}, {"title": "Board", "key": ""}, "Spec")
        page = pg.locator('.table-over[data-kind="spec"] .spec-page')
        page.wait_for(timeout=WAIT_MS)
        page.locator(".spec-section").first.wait_for(timeout=WAIT_MS)
        secs = page.locator(".spec-section")
        assert secs.count() == 1 and secs.first.get_attribute("data-party") == "design" and secs.first.get_attribute("data-lit") is None
        assert [x.inner_text().strip() for x in secs.first.locator(".spec-line").all()] == ["Messages show in the lobby", "The last fifty are kept"]
        assert secs.first.locator('.spec-col[data-part="will"]').count() == 0 and page.locator(".spec-line.is-lit").count() == 0
        shot(pg, f"{width}-spec-alone")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_one_change_keeps_the_field_as_written_and_words_the_line_again(gui, width):
    """Spec 132 A, decisions §237.3: under the field one line, *Or say what to change*; Change sends `ideas.decision_change` with the field as `text` and the line as `say`."""
    pg, host, log = open_decision(gui, width)
    try:
        press(pg, "chat")
        lifted(pg).get_by_role("button", name="Change…").click()
        field = lifted(pg).locator("textarea.hand-way__entry")
        field.wait_for(timeout=WAIT_MS)
        line = lifted(pg).get_by_label("Or say what to change")
        assert line.count() == 1 and "or say what to change" in lifted(pg).inner_text().lower()
        change = lifted(pg).get_by_role("button", name="Change", exact=True)
        assert change.is_disabled(), "nothing changed, nothing to send"
        line.fill("Make it three rooms")
        assert lifted(pg).get_by_role("button", name="Confirm and start").is_disabled(), "a line to be worded is sent by Change, not lost by Confirm"
        shot(pg, f"{width}-decision-change")
        narrow.no_sideways(pg)
        change.click()
        got = _calls(pg, host, "ideas.decision_change")
        assert got == [{"idea": "chat", "say": "Make it three rooms"}], got
        pg.wait_for_function("() => !document.querySelector('.hand-lifted textarea')", timeout=WAIT_MS)
        lifted(pg).get_by_role("button", name="Change…").click()
        lifted(pg).locator("textarea.hand-way__entry").fill("## 118. Chat\n\nWhy: x.\n\n1. One room.")
        lifted(pg).get_by_label("Or say what to change").fill("and quieter")
        lifted(pg).get_by_role("button", name="Change", exact=True).click()
        got = _calls(pg, host, "ideas.decision_change")
        assert got[-1] == {"idea": "chat", "text": "## 118. Chat\n\nWhy: x.\n\n1. One room.", "say": "and quieter"}, got
    finally:
        pg.close()
    assert not log, "\n".join(log)
