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
from tests.test_hand_desktop_browser import HandHost, call, node, need, open_hand  # noqa: E402
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


def kept(q, state, answer="", how="pick", pick=0, **more):
    return {"id": q["id"], "q": q["q"], "choices": q["choices"], "pick": pick, "why": q["why"], "project": q["project"], "state": state,
            **({"answer": answer, "round": 1} if state != "waiting" else {}), **({"how": how} if state == "answered" else {}), **more}


# the Talk as the host kept it (`ideas.talk_read`): Design's first question answered by the person, its second left to its pick, Tech's still waiting
KEPT = {"idea": "chat", "mode": "talk", "round": 1, "done": False, "cause": None, "stances": [
    {**STANCES[0], "questions": [kept(C1, "answered", "Server counts, phones show it"), kept(card("r1-0", "design", "Design lead", "Dark or light first?", ["Dark", "Light"], 0, "The lobby is dark."), "closed", "Dark")]},
    {**STANCES[1], "questions": [kept(C2, "waiting", pick=1)]}]}


class TalkHost(HandHost):
    """A project of four parties (Tech, Design, Product, Release), a goal at Talk with three questions of three leaders and two stances, `bug`: a bug with a case question and Tech's guess of its cause, `project`: the project's two
    questions of Product's."""

    def __init__(self, bug=False, project=False, past=False):
        super().__init__(bare=True)
        self.refuse = False
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = []
        chat = node("chat", "design", "Chat in the lobby", "hand", state="working" if past else "talk", element="ice")      # `past`: the goal has gone by its Talk, no row waits
        self.nodes.append(chat)
        if not past:
            self.needs.append(need("talk", "design", "chat", chat["title"], C1["q"], round=1, stances=STANCES, questions=[C1, C2, C3]))
        if bug:
            lag = node("lag", "tech", "The lobby lags after a reconnect", "hand", state="talk", element="dust")
            self.nodes.append(lag)
            self.needs.append(need("cause", "tech", "lag", lag["title"], "the lobby timer is not reset on reconnect: server/lobby.ts",
                                   cause="the lobby timer is not reset on reconnect: server/lobby.ts", where=["server/lobby.ts", "server/timer.ts"], q=[CAUSE_Q]))
        if project:
            self.needs.append({"kind": "project_q", "party": "product", "leader": "Product lead", "questions": PQ, "text": PQ[0]["q"], "blocks": False, "priority": "normal", "at": "2026-10-20T10:00:00"})

    def handle(self, name, a):
        if name == "ideas.talk_read":
            self.log.append((name, a))
            return KEPT
        if name in ("ideas.talk_answer", "ideas.cause_answer", "ideas.project_answer"):
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The goal is gone"}
            kind = {"ideas.talk_answer": "talk", "ideas.cause_answer": "cause", "ideas.project_answer": "project_q"}[name]
            self.needs = [n for n in self.needs if n["kind"] != kind]
            return self.bump({"ok": True})
        return super().handle(name, a)


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


def answers_sent(pg, host, name, at_least=1):
    return _calls(pg, host, name, at_least)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_talk_of_a_goal_past_it_is_opened_from_its_mark_in_the_title_and_read_as_kept(gui, width):
    pg, host, log = open_hand(gui, host=TalkHost(past=True), width=width)
    try:
        call(pg, "frame/state.js", "pick", "chat")
        pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
        assert pg.locator('.table-phase[data-phase="work"]').get_attribute("aria-current") == "step"
        pg.locator('.table-phase[data-phase="work"]').wait_for(timeout=WAIT_MS)
        assert pg.locator("button[data-phase]").count() == 0 and pg.locator(".table-over").count() == 0
        pg.locator('[data-earlier="talk"]').click()                                                                # the Orkmaster's Earlier: the Talk as kept, in place (spec 156 C.3)
        page = pg.locator('.phase-earlier__body[data-earlier-body="talk"] .talk-page')
        page.locator(".talk-stance").first.wait_for(timeout=WAIT_MS)
        assert [s.locator(".talk-stance__nm").text_content().strip() for s in page.locator(".talk-stance").all()] == ["Design", "Tech"]
        assert page.get_by_role("button", name="All the questions").count() == 0, "nothing waits: the Talk is read, not answered"
        page.locator(".talk-stance").first.get_by_role("button", name="More").click()
        assert "You said: Server counts" in page.locator(".talk-stance__asks").inner_text()
        shot(pg, f"{width}-past-talk")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_question_with_no_choices_says_say_it_in_a_line_and_its_one_place_is_the_open_field(gui, width):
    """Spec 149 I.3: no *Other...* to press first, no Cancel; the answer goes as the person's words."""
    host = TalkHost(project=True)
    bare = [card("project-for_whom", "product", "Product lead", "Whom is it for?", [], None, "", project=True)]
    host.needs = [n for n in host.needs if n["kind"] == "project_q"]
    host.needs[0]["questions"], host.needs[0]["text"] = bare, bare[0]["q"]
    pg, host, log = open_hand(gui, host=host, width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="project_q"][data-top="1"]').click(position={"x": 10, "y": 24})
        choose(pg).wait_for(timeout=WAIT_MS)
        assert pg.locator(".q-choose__hint").inner_text().strip() == "Say it in a line: the leader keeps it for the project"
        field = pg.locator(".q-card__field")
        field.wait_for(timeout=WAIT_MS)
        assert pg.locator('.q-card[data-choice="other"]').count() == 1 and pg.locator("button.q-card").count() == 0, "the field is open at once"
        assert pg.locator('.q-card[data-choice="other"] .ork-btn', has_text="Cancel").count() == 0
        narrow.no_sideways(pg)
        field.fill("Friends who play at a table")
        field.press("Enter")
        got = answers_sent(pg, host, "ideas.project_answer")
        assert got == [{"answers": [{"id": "project-for_whom", "text": "Friends who play at a table"}]}], got
    finally:
        pg.close()
    assert not log, "\n".join(log)
