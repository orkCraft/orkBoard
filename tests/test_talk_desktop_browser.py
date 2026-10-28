"""Talk's questions on the window (docs/specs/100-a-goals-way-as-cards.md §2, part B; docs/specs/99-a-goals-way.md §5, §8), in a real browser against a stub host answering the rows `talk`, `cause` and `project_q` and their commands
(`ideas.talk_answer`, `ideas.cause_answer`, `ideas.project_answer`), at the two widths of `tests/narrow.py`: a question is a card (the sign `question`, its leader's head, the question at its foot, the stack's edges and no count), lifted
its choices are dealt over the pane (*Choose a card*: the banner, the leader's pick raised with its why, *Other…* a blank card with + and the pick's words, *Let <leader> decide*, *Put it back*), a press answers at once and the next of
the stack comes on top, the answers go together after the last, the questions together over the pane, the stances on the pane, the bug's cause (*Yes*, *No, it's elsewhere*, *Other…*, a part lit on System), the project's questions (a stack
under their leader's party's lane, its one line once). Screenshots to $TALK_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, node, need, open_hand, sig  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["TALK_SHOTS"]) if os.environ.get("TALK_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def card(cid, by, leader, q, choices, pick, why="", project=False):
    return {"id": cid, "by": by, "leader": leader, "q": q, "choices": choices, "pick": pick, "why": why, "project": project}


C1 = card("r1-1", "design", "Design lead", "Where does the timer run?", ["Server counts, phones show it", "Each phone counts down alone"], 0, "One clock: every phone agrees.")
C2 = card("r1-2", "tech", "Tech lead", "Which store first?", ["App Store", "Google Play", "Both at once"], 1, "Most of its players are on Android.", project=True)
C3 = card("r1-3", "product", "Product lead", "Who is it for?", ["Friends at a table", "Families"], 0, "The README says friends.")
STANCES = [{"party": "design", "leader": "Design lead", "stance": "Show one clock on every phone", "for": "Nobody argues about the time", "against": "A phone offline shows a stale time"},
           {"party": "tech", "leader": "Tech lead", "stance": "The server owns the clock", "for": "One place to reset", "against": "Every round trip adds delay"}]
CAUSE_Q = card("c-1", "tech", "Tech lead", "Where does it happen?", ["In the lobby", "In a round", "On the results screen"], 0, "The report says lobby.")
PQ = [card("project-for_whom", "product", "Product lead", "Whom is it for?", ["Friends at a table", "Families", "Streamers"], 0, "The README says friends.", project=True),
      card("project-hurts", "product", "Product lead", "What hurts them?", ["Waiting for a slow host", "Arguing about the rules"], 1, "The README lists the rules.", project=True)]


class TalkHost(HandHost):
    """A project of four parties (Tech, Design, Product, Release), a goal at Talk with three questions of three leaders and two stances, `bug`: a bug with a case question and Tech's guess of its cause, `project`: the project's two
    questions of Product's."""

    def __init__(self, bug=False, project=False):
        super().__init__(bare=True)
        self.refuse = False
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = []
        chat = node("chat", "design", "Chat in the lobby", "hand", state="talk", element="ice")
        self.nodes.append(chat)
        self.needs.append(need("talk", "design", "chat", chat["title"], C1["q"], round=1, stances=STANCES, questions=[C1, C2, C3]))
        if bug:
            lag = node("lag", "tech", "The lobby lags after a reconnect", "hand", state="talk", element="dust")
            self.nodes.append(lag)
            self.needs.append(need("cause", "tech", "lag", lag["title"], "the lobby timer is not reset on reconnect: server/lobby.ts",
                                   cause="the lobby timer is not reset on reconnect: server/lobby.ts", where=["server/lobby.ts", "server/timer.ts"], q=[CAUSE_Q]))
        if project:
            self.needs.append({"kind": "project_q", "party": "product", "leader": "Product lead", "questions": PQ, "text": PQ[0]["q"], "blocks": False, "priority": "normal", "at": "2026-10-20T10:00:00"})

    def handle(self, name, a):
        if name in ("ideas.talk_answer", "ideas.cause_answer", "ideas.project_answer"):
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The goal is gone"}
            kind = {"ideas.talk_answer": "talk", "ideas.cause_answer": "cause", "ideas.project_answer": "project_q"}[name]
            self.needs = [n for n in self.needs if n["kind"] != kind]
            return self.bump({"ok": True})
        return super().handle(name, a)


def open_talk(gui, width="wide", **more):
    pg, host, log = open_hand(gui, host=TalkHost(**more), width=width)
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg, goal):
    return pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')


def press(pg, goal):
    """A press on the left edge of a goal's front card (a stack that lies behind another shows only that, and rises under the pointer)."""
    front(pg, goal).click(position={"x": 10, "y": 24})


def choose(pg):
    return pg.locator('.table-over[data-kind="choose"]')


def banner(pg):
    return pg.locator(".q-choose__q").inner_text().strip()


def pick(pg, name):
    pg.locator(".q-card", has_text=name).first.click()


def wait_banner(pg, text):
    pg.wait_for_function("(t) => document.querySelector('.q-choose__q')?.textContent.trim() === t", arg=text, timeout=WAIT_MS)


def answers_sent(pg, host, name, at_least=1):
    return _calls(pg, host, name, at_least)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_question_is_a_card_with_its_sign_its_leaders_head_and_the_question_at_its_foot(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        c = front(pg, "chat")
        assert c.get_attribute("data-kind") == "talk" and c.get_attribute("data-key") == "talk/talk/chat/r1-1"
        assert c.locator(".hand-card__name").inner_text().strip() == "Chat in the lobby" and c.locator(".hand-card__head .ork-elem.ice").count() == 1       # the goal's element and name in its header
        assert c.locator(".hand-card__window .ork-sign.question").count() == 1 and c.locator(".hand-card__asker .ork-race__head").count() == 1             # the sign `question`, its leader's head over it
        assert c.locator(".hand-card__foot").text_content().strip() == "Where does the timer run?"                                                        # the question at its foot
        assert c.locator(".ork-gem").count() == 0                                                                                                           # a question costs nothing
        stack = pg.locator('.hand-stack[data-goal="chat"]')
        assert stack.get_attribute("data-n") == "2" and stack.locator(".ork-card-back.edge").count() == 2, "the edges hint how many are left"
        assert "/" not in pg.locator('.hand-slot:has(.hand-card[data-goal="chat"])').inner_text(), "never a count"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="chat"]').count() == 1, "the goal's Talk lies under the first lane (laneOf: the whole goal's)"
        shot(pg, f"{width}-question-card")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_its_choices_are_dealt_over_the_pane_a_press_answers_and_the_next_comes_on_top_the_answers_go_together_after_the_last(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-lifted").count() == 0, "the card's choices are the pane's, not an aside"
        assert banner(pg) == "Where does the timer run?"
        cards = pg.locator(".q-choose__row .q-card")
        assert cards.count() == 3 and [cards.nth(i).locator(".q-card__name").inner_text().strip() for i in range(3)] == ["Server counts, phones show it", "Each phone counts down alone", "Other…"]
        first = cards.first
        assert first.get_attribute("data-pick") == "1" and "is-pick" in first.get_attribute("class") and cards.nth(1).get_attribute("data-pick") is None, "the leader's pick, raised"
        assert first.locator(".q-card__foot").inner_text().strip() == "One clock: every phone agrees.", "with its why at its foot"
        assert cards.nth(1).locator(".q-card__foot").inner_text().strip() == ""
        assert first.locator(".hand-card__head, .q-card__head .ork-elem.ice").count() == 1, "the goal's element at the left of its header"
        assert cards.nth(2).get_attribute("class").count("q-card--blank") == 1 and cards.nth(2).locator(".ork-icon").count() == 1, "Other… is a blank card with +"
        assert pg.locator(".q-choose__hint").inner_text().strip() == "Pick an answer: the leader writes it into the spec", "the one line, under the first card"
        buttons = [b.inner_text().strip() for b in pg.locator(".q-choose__acts .ork-btn").all()]
        assert buttons == ["Let Design lead decide", "All the questions", "Put it back"]
        shot(pg, f"{width}-choose-words")
        narrow.no_sideways(pg)
        pick(pg, "Each phone counts down alone")                                                   # a press answers at once
        wait_banner(pg, "Which store first?")                                                       # the next of the stack is on top
        assert pg.locator(".q-choose__hint").count() == 0, "the line once, under the first card"
        assert pg.locator(".q-card.is-pick .q-card__name").inner_text().strip() == "Google Play"
        assert [n for n, _a in host.log if n == "ideas.talk_answer"] == [], "nothing is sent before the last"
        assert front(pg, "chat").locator(".hand-card__foot").text_content().strip() == "Which store first?" and pg.locator('.hand-stack[data-goal="chat"]').get_attribute("data-n") == "1"
        pick(pg, "Both at once")
        wait_banner(pg, "Who is it for?")
        pick(pg, "Families")
        got = answers_sent(pg, host, "ideas.talk_answer")
        assert len(got) == 1 and got[0] == {"idea": "chat", "answers": [{"id": "r1-1", "pick": 1}, {"id": "r1-2", "pick": 2}, {"id": "r1-3", "pick": 1}]}, got
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"chat\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_other_opens_a_field_with_the_picks_words_and_answers_with_what_is_written(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        pg.locator('.q-card[data-choice="other"]').click()
        field = pg.locator(".q-card__field")
        field.wait_for(timeout=WAIT_MS)
        assert field.input_value() == "Server counts, phones show it", "the field opens with the pick's words"
        assert pg.locator('.q-card[data-choice="other"] .ork-btn.primary').is_enabled()
        shot(pg, f"{width}-choose-other")
        narrow.no_sideways(pg)
        field.fill("The host's phone counts, the rest follow")
        field.press("Enter")
        wait_banner(pg, "Which store first?")
        pick(pg, "App Store")
        wait_banner(pg, "Who is it for?")
        pg.locator('.q-card[data-choice="other"]').click()
        pg.locator(".q-card__field").fill("")
        assert pg.locator('.q-card[data-choice="other"] .ork-btn.primary').is_disabled(), "an empty field answers nothing"
        pg.locator(".q-card__field").fill("Families with teenagers")
        pg.locator('.q-card[data-choice="other"] .ork-btn.primary').click()
        got = answers_sent(pg, host, "ideas.talk_answer")
        assert got[0]["answers"] == [{"id": "r1-1", "text": "The host's phone counts, the rest follow"}, {"id": "r1-2", "pick": 0}, {"id": "r1-3", "text": "Families with teenagers"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_let_the_leader_decide_answers_the_rest_with_the_picks_and_put_it_back_keeps_the_stack(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        pick(pg, "Each phone counts down alone")
        wait_banner(pg, "Which store first?")
        pg.get_by_role("button", name="Put it back").click()                                       # back to the map: the stack is as it was, one card answered
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        assert [n for n, _a in host.log if n == "ideas.talk_answer"] == []
        assert front(pg, "chat").locator(".hand-card__foot").text_content().strip() == "Which store first?", "its next question is on top"
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator(".q-choose__hint").count() == 0, "an answer is already given: the line is not said again"
        pg.get_by_role("button", name="Let Tech lead decide").click()
        got = answers_sent(pg, host, "ideas.talk_answer")
        assert got == [{"idea": "chat", "answers": [{"id": "r1-1", "pick": 1}], "decide": True}], got
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_questions_together_open_over_the_pane_and_go_in_one_command(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        pg.get_by_role("button", name="All the questions").click()
        page = pg.locator('.table-over[data-kind="talk"]')
        page.wait_for(timeout=WAIT_MS)
        form = page.locator(".talk-together")
        assert form.locator(".talk-ask").count() == 3 and form.locator(".talk-ask legend").first.inner_text().strip() == "Where does the timer run?"
        assert form.locator(".talk-ask").first.locator(".ork-btn.primary").inner_text().strip() == "● Server counts, phones show it", "the picks are on"
        shot(pg, f"{width}-questions-together")
        narrow.no_sideways(pg)
        form.locator(".talk-ask").nth(1).get_by_role("button", name="App Store").click()
        form.locator(".talk-ask").nth(2).locator("input").fill("Streamers")
        form.get_by_role("button", name="Send the answers").click()
        got = answers_sent(pg, host, "ideas.talk_answer")
        assert got == [{"idea": "chat", "answers": [{"id": "r1-1", "pick": 0}, {"id": "r1-2", "pick": 0}, {"id": "r1-3", "text": "Streamers"}]}], got
        pg.wait_for_function("() => !document.querySelector('.table-over')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_stances_are_on_the_pane_a_row_of_the_leaders_with_more_unfolding_in_place(gui, width):
    pg, host, log = open_talk(gui, width)
    try:
        call(pg, "frame/state.js", "openOver", "talk", {"idea": "chat"}, {"title": "Board", "key": ""}, "Chat in the lobby")
        page = pg.locator('.table-over[data-kind="talk"]')
        page.wait_for(timeout=WAIT_MS)
        stances = page.locator(".talk-stance")
        assert stances.count() == 2 and [s.locator(".talk-stance__nm").text_content().strip() for s in stances.all()] == ["Design", "Tech"]      # the party's name, never the leader's role
        assert all(s.locator(".ork-race__head").count() == 1 for s in stances.all())
        first = stances.first
        assert first.locator(".talk-stance__line").inner_text().strip() == "Show one clock on every phone"
        assert "Nobody argues about the time" in first.inner_text() and "A phone offline shows a stale time" in first.inner_text()
        assert [b.text_content() for b in first.locator(".ork-label").all()] == ["For", "Against"]
        assert first.locator(".talk-stance__asks").count() == 0
        first.get_by_role("button", name="More").click()
        assert "Where does the timer run?" in first.locator(".talk-stance__asks").inner_text(), "its questions unfold in place"
        shot(pg, f"{width}-stances")
        narrow.no_sideways(pg)
        if width == "wide":
            boxes = [s.bounding_box() for s in stances.all()]
            assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 2, "in a row"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_bugs_cause_is_a_card_after_its_case_questions_and_is_answered_yes_no_or_other(gui, width):
    pg, host, log = open_talk(gui, width, bug=True)
    try:
        c = front(pg, "lag")
        assert c.get_attribute("data-kind") == "cause" and c.locator(".hand-card__foot").text_content().strip() == "Where does it happen?"      # the case question comes first
        stack = pg.locator('.hand-stack[data-goal="lag"]')
        assert stack.get_attribute("data-n") == "1", "the guess lies under it"
        assert stack.locator(".ork-card-back.edge").count() == 1
        assert pg.locator(".hand-lane").nth(1).locator('.hand-stack[data-goal="lag"]').count() == 1, "under Tech's lane"
        press(pg, "lag")
        choose(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator(".q-choose__hint").count() == 0
        pick(pg, "In a round")
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        assert [n for n, _a in host.log if n == "ideas.cause_answer"] == [], "the case question's answer goes with the cause's"
        c = front(pg, "lag")
        assert c.get_attribute("data-kind") == "cause" and c.locator(".hand-card__name").inner_text().strip() == "The cause" and c.locator(".ork-sign.question").count() == 1
        assert c.locator(".hand-card__foot").text_content().strip() == "I think the lobby timer is not reset on reconnect: server/lobby.ts"
        assert c.locator(".hand-card__asker .ork-race__head").count() == 1
        press(pg, "lag")
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        assert "I think the lobby timer is not reset on reconnect" in lifted.inner_text()
        assert [p.inner_text() for p in lifted.locator(".q-cause__part").all()] == ["server/lobby.ts", "server/timer.ts"]
        assert [b.inner_text().strip() for b in lifted.locator(".hand-answers .ork-btn").all()] == ["Yes", "No, it's elsewhere", "Other…"]
        shot(pg, f"{width}-cause")
        narrow.no_sideways(pg)
        lifted.get_by_role("button", name="No, it's elsewhere").click()                              # one line for where
        line = lifted.locator("input.ork-field")
        assert line.get_attribute("placeholder") == "Where is it? One line"
        line.fill("In the timer service")
        line.press("Enter")
        got = answers_sent(pg, host, "ideas.cause_answer")
        assert got == [{"idea": "lag", "yes": False, "text": "In the timer service", "answers": [{"id": "c-1", "pick": 1}]}], got
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"lag\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_cause_yes_and_other_and_a_part_lit_on_system(gui):
    pg, host, log = open_talk(gui, bug=True)
    try:
        press(pg, "lag")
        choose(pg).wait_for(timeout=WAIT_MS)
        pg.get_by_role("button", name="Let Tech lead decide").click()                                 # a bug's guess is still the person's: the case question takes its pick
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        assert [n for n, _a in host.log if n == "ideas.cause_answer"] == []
        assert front(pg, "lag").get_attribute("data-kind") == "cause" and front(pg, "lag").locator(".hand-card__name").inner_text().strip() == "The cause"
        press(pg, "lag")
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        lifted.locator(".q-cause__part", has_text="server/timer.ts").click()                         # lights it on Tech's System
        assert sig(pg, "frame/state.js", "tab") == "tech" and sig(pg, "table/card.js", "litKey") == "t:part:tech:server/timer.ts"
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        lifted.get_by_role("button", name="Other…").click()
        lifted.locator("input.ork-field").fill("A race between two timers")
        lifted.get_by_role("button", name="Send").click()
        got = answers_sent(pg, host, "ideas.cause_answer")
        assert got == [{"idea": "lag", "yes": True, "text": "A race between two timers", "answers": [{"id": "c-1", "pick": 0}]}], got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_yes_sends_the_cause_with_no_text(gui):
    pg, host, log = open_talk(gui, bug=True)
    try:
        press(pg, "lag")
        choose(pg).wait_for(timeout=WAIT_MS)
        pick(pg, "In the lobby")
        pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"choose\"]')", timeout=WAIT_MS)
        press(pg, "lag")
        pg.locator(".hand-lifted").get_by_role("button", name="Yes").click()
        got = answers_sent(pg, host, "ideas.cause_answer")
        assert got == [{"idea": "lag", "yes": True, "answers": [{"id": "c-1", "pick": 0}]}], got
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_projects_questions_are_a_stack_under_their_leaders_party_with_the_one_line_once(gui, width):
    pg, host, log = open_talk(gui, width, project=True)
    try:
        stack = pg.locator('.hand-lane[data-lane="3"] .hand-stack[data-stack="party:product@3"]')           # Product's lane: the third party
        assert stack.count() == 1 and stack.get_attribute("data-n") == "1", "a stack of no goal's under its leader's party's lane"
        top = stack.locator('.hand-card[data-top="1"]')
        assert top.get_attribute("data-kind") == "project_q" and top.locator(".hand-card__foot").text_content().strip() == "Whom is it for?"
        assert top.locator(".hand-card__window .ork-sign.question").count() == 1 and top.locator(".hand-card__asker .ork-race__head").count() == 1, "its leader's head on its face"
        assert top.locator(".hand-card__party").text_content() == "Product"
        shot(pg, f"{width}-project-stack")
        top.click(position={"x": 10, "y": 24})
        choose(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator(".q-choose__hint").inner_text().strip() == "Pick an answer: the leader keeps it for the project"
        assert [b.inner_text().strip() for b in pg.locator(".q-choose__acts .ork-btn").all()] == ["Let Product lead decide", "Put it back"], "no questions together for the project's"
        shot(pg, f"{width}-choose-project")
        narrow.no_sideways(pg)
        pick(pg, "Streamers")
        wait_banner(pg, "What hurts them?")
        assert pg.locator(".q-choose__hint").count() == 0, "once"
        pick(pg, "Waiting for a slow host")
        got = answers_sent(pg, host, "ideas.project_answer")
        assert got == [{"answers": [{"id": "project-for_whom", "pick": 2}, {"id": "project-hurts", "pick": 0}]}], got
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-stack^=\"party:product\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_projects_questions_let_the_leader_decide_and_lie_after_the_others(gui):
    pg, host, log = open_talk(gui, project=True)
    try:
        stops = pg.evaluate("""async () => { const m = await import('/static/js/hand/data.js'); return m.stopsOfProject().map((s) => s.kind); }""")
        assert stops == ["talk", "talk", "talk", "project_q", "project_q"], stops             # they hold nothing back: after the others
        pg.locator('.hand-stack[data-stack="party:product@3"] .hand-card').first.click(position={"x": 10, "y": 24})
        choose(pg).wait_for(timeout=WAIT_MS)
        pg.mouse.move(640, 300)                                                                      # off the hand's card, which rises under the pointer over the pane's foot
        pg.get_by_role("button", name="Let Product lead decide").click()
        assert answers_sent(pg, host, "ideas.project_answer") == [{"answers": [], "decide": True}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_refused_answer_deals_the_cards_again(gui):
    pg, host, log = open_talk(gui)
    try:
        host.refuse = True
        press(pg, "chat")
        choose(pg).wait_for(timeout=WAIT_MS)
        for name in ("Server counts, phones show it", "Google Play", "Families"):
            pick(pg, name)
            pg.wait_for_timeout(150)
        assert len(answers_sent(pg, host, "ideas.talk_answer")) == 1
        pg.wait_for_function("() => document.querySelectorAll('.hand-stack[data-goal=\"chat\"]').length === 1", timeout=WAIT_MS)
        assert front(pg, "chat").locator(".hand-card__foot").text_content().strip() == "Where does the timer run?", "the host refused: the stack is dealt again from its first card"
    finally:
        pg.close()


def test_choose_is_reusable_previews_a_gem_a_head_and_its_props(gui):
    """Spec 100 C deals a fork's sides with the same component: a choice's preview in the window, its gem, its head; no *Other…* without `onOther`; a press answers with the id."""
    pg, host, log = open_talk(gui)
    try:
        pg.evaluate("""async () => {
          const [{ render, h }, { Choose }] = await Promise.all([import('preact'), import('/static/js/hand/choose.js')]);
          const px = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
          let box = document.getElementById('test-choose');
          if (!box) { box = document.createElement('div'); box.id = 'test-choose'; box.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:240px;overflow:auto;background:var(--ork-table);padding:16px;z-index:1'; document.body.appendChild(box); }
          window.__chosen = [];
          render(h(Choose, { question: 'Which look for the lobby?', pick: 'b', by: 'Art', element: 'ice', head: { race: 'elf', tier: 'elder' }, onChoose: (id) => window.__chosen.push(id),
            choices: [{ id: 'a', name: 'Quiet felt', preview: px }, { id: 'b', name: 'Loud neon', why: 'It reads from across a room.', preview: px, gem: '3%' }, { id: 'c', name: 'Plain', head: { race: 'peon', tier: 'laborer' } }] }), box);
        }""")
        row = pg.locator("#test-choose .q-choose__row")
        row.wait_for(timeout=WAIT_MS)
        cards = row.locator(".q-card")
        assert cards.count() == 3, "no Other… with no onOther"
        assert cards.nth(0).locator("img.q-card__preview").count() == 1 and cards.nth(1).locator("img.q-card__preview").count() == 1, "a choice of a look shows its preview in the window"
        assert cards.nth(1).get_attribute("data-pick") == "1" and cards.nth(1).locator(".q-card__foot").inner_text().strip() == "It reads from across a room."
        assert cards.nth(1).locator(".ork-gem").inner_text() == "3%" and cards.nth(0).locator(".ork-gem").count() == 0, "a gem on the one that costs more"
        assert cards.nth(2).locator(".q-card__window .ork-race__head").count() == 1, "a head in the window"
        assert pg.locator("#test-choose .q-choose__acts .ork-btn").count() == 0
        shot(pg, "wide-choose-previews")
        cards.nth(2).click()
        assert pg.evaluate("() => window.__chosen") == ["c"]
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_choose_previews_at_the_narrow_width_no_sideways_scroll(gui):
    pg, host, log = open_talk(gui, "narrow")
    try:
        pg.evaluate("""async () => {
          const [{ render, h }, { Choose }] = await Promise.all([import('preact'), import('/static/js/hand/choose.js')]);
          const px = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
          const box = document.createElement('div'); box.id = 'test-choose'; box.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:120px;overflow:auto;background:var(--ork-table);padding:16px;z-index:1'; document.body.appendChild(box);
          render(h(Choose, { question: 'Which look for the lobby?', pick: 'b', by: 'Art', element: 'ice', onChoose() {}, onOther() {}, decide: { label: 'Let Art decide', onDecide() {} },
            choices: [{ id: 'a', name: 'Quiet felt', preview: px }, { id: 'b', name: 'Loud neon', why: 'It reads from across a room.', preview: px, gem: '3%' }, { id: 'c', name: 'Plain paper with a very long name that wraps' }] }), box);
        }""")
        pg.locator("#test-choose .q-card").first.wait_for(timeout=WAIT_MS)
        shot(pg, "narrow-choose-previews")
        narrow.no_sideways(pg)
        assert pg.locator("#test-choose .q-card").count() == 4
        assert pg.evaluate("() => document.querySelector('#test-choose .q-choose').scrollWidth <= document.querySelector('#test-choose').clientWidth")
    finally:
        pg.close()
    assert not log, "\n".join(log)
