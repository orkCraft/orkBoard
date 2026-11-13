"""Spec 128 E (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md; decisions §206.5) in a real browser against the table's stub host: the open leader's bubble says what it is about (the picked goal's rune and name, or
*The whole project*) and carries a part of a goal's change as a chip with × (`openAsk(tab, part)`); under an answer *Make it a change* stands only for a goal that is agreed or at work on a leader's tab (never the Orkmaster's), *Make it a goal* only for
nothing picked or a goal done; pressed, it sends `ideas.change {idea, party, part?, text}` and puts the answer away. The decision in the hand (hand/changecard.js): lifted, *Now* and *Proposed* side by side, the cost, **Accept**, **Talk more** (the bubble
again with the part and the words kept) and **Keep the spec**; Design's three looks as choices and *Let Design decide*."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import AskHost, bubble, field, head, opened, record, settled, start  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

GOAL_TITLE = "Keep the seat when a socket reconnects"      # the stub host's goal `seat`: tech, working
RESULTS_TITLE = "Results screen with the round's best answer"         # `results`: tech, planning (no failure of its own: its card is the top of its stack)


class ChangeHost(AskHost):
    """The ask host that also answers the change commands (`ideas.change`, `ideas.change_take`, `ideas.change_keep`) and keeps the Needs you rows the test puts."""

    def handle(self, name, a):
        if name in ("ideas.change", "ideas.change_take", "ideas.change_keep"):
            self.log.append((name, a))
            if name != "ideas.change":
                self.needs = [n for n in self.needs if n.get("id") != a["id"]]
                self.push()
            return {"ok": True, "id": "c1", "added": 1, "changed": 1, "dropped": 0, "left": []}
        return super().handle(name, a)


def pick(pg, slug):
    pg.evaluate(f"() => import('/static/js/frame/state.js').then((m) => {{ m.picked.value = {slug!r}; }})")


def row(shape="plan", **more):
    base = {"kind": "leader_change", "idea": "results", "id": "c1", "task": "c1", "goal": "tech", "party": "tech", "part": "server/lobby.ts", "said": "Keep the seat for a minute after a drop", "shape": shape, "status": "ready",
            "text": "The seat is kept for 60 s", "why": "The seat is kept for 60 s after a drop.", "blocks": False, "title": RESULTS_TITLE, "priority": "normal", "at": "2026-11-02T09:00:00",
            "before": {"tasks": [{"id": "s1", "title": "Keep the seat", "short": "Keep seat", "op": "change"}, {"id": "s3", "title": "Drop the old timer", "short": "Old timer", "op": "drop"}], "lines": ["changed Rounds — no wait"]},
            "after": {"tasks": [{"id": "s1", "title": "Keep the seat for 60 s", "short": "Seat 60 s", "op": "change"}, {"id": "", "title": "Timer test", "short": "Timer test", "op": "add"}], "lines": ["changed Rounds — keeps the seat 60 s", "new Seats — a map of seats"]},
            "looks": [], "usd_low": 0.2, "usd_high": 0.6, "error": ""}
    return {**base, **more}


@pytest.fixture
def asked(gui):
    server, browser = gui
    pg, host, errors = start(gui, "wide", ChangeHost())
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def about(pg):
    return [" ".join(c.inner_text().split()) for c in bubble(pg).locator(".table-ask__chip").all()]


def test_the_bubble_says_what_it_is_about_the_whole_project_or_the_picked_goal(asked):
    pg, host = asked
    open_tab(pg, "tech")
    host.put(record("answered", "tech"))
    opened(pg, "tech")
    assert about(pg) == ["The whole project"]
    assert bubble(pg).locator(".table-ask__chip[data-about=project] .ork-elem").count() == 0
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    pick(pg, "seat")
    opened(pg, "tech")
    assert about(pg) == [GOAL_TITLE] and bubble(pg).locator(".table-ask__chip[data-about=goal] .ork-elem").count() == 1


def test_make_it_a_change_stands_only_for_a_goal_agreed_or_at_work_on_a_leaders_tab_and_make_it_a_goal_for_nothing_or_a_goal_done(asked):
    pg, host = asked
    open_tab(pg, "tech")
    host.put(record("answered", "tech"))
    change, goal = lambda: bubble(pg).get_by_role("button", name="Make it a change"), lambda: bubble(pg).get_by_role("button", name="Make it a goal")      # noqa: E731
    opened(pg, "tech")                                                                                            # nothing picked
    assert change().count() == 0 and goal().count() == 1
    head(pg, "tech").click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    pick(pg, "seat")                                                                                               # a goal at work, on a leader's tab
    opened(pg, "tech")
    assert change().count() == 1 and goal().count() == 0 and "primary" in change().get_attribute("class").split()
    head(pg, "tech").click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    open_tab(pg, "orkmaster")                                                                                      # the same goal, the Orkmaster's tab: neither
    host.put(record("answered", ""))
    opened(pg)
    assert change().count() == 0 and goal().count() == 0
    head(pg).click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    next(n for n in host.nodes if n["slug"] == "seat")["state"] = "done"                                           # a goal done, on a leader's tab
    host.push()
    open_tab(pg, "tech")
    host.put(record("answered", "tech"))
    opened(pg, "tech")
    assert change().count() == 0 and goal().count() == 1
    for state in ("decided", "sections", "plan"):                                                                  # agreed, whatever step it is at
        head(pg, "tech").click()
        bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
        next(n for n in host.nodes if n["slug"] == "seat")["state"] = state
        host.push()
        opened(pg, "tech")
        assert change().count() == 1, state


def test_a_part_comes_as_a_chip_with_a_cross_that_takes_it_off_and_it_goes_with_the_bubble(asked):
    pg, host = asked
    open_tab(pg, "tech")
    pick(pg, "seat")
    pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.openAsk('tech', { id: 'server/lobby.ts', name: 'lobby.ts' }))")
    bubble(pg).wait_for(timeout=WAIT_MS)
    settled(pg)
    assert about(pg) == [GOAL_TITLE, "lobby.ts"] and field(pg).get_attribute("placeholder") == "What about lobby.ts?"
    bubble(pg).get_by_role("button", name="Take the part off").click()
    assert about(pg) == [GOAL_TITLE] and field(pg).get_attribute("placeholder") == f"What about {GOAL_TITLE}?"
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.openAsk('tech', 'Rounds'))")
    bubble(pg).wait_for(timeout=WAIT_MS)
    assert about(pg) == [GOAL_TITLE, "Rounds"]
    pg.keyboard.press("Escape")
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    opened(pg, "tech")
    assert about(pg) == [GOAL_TITLE], "a part is for the opening that carried it"


def test_make_it_a_change_sends_the_words_with_the_goal_the_party_and_the_part_and_puts_the_answer_away(asked):
    pg, host = asked
    open_tab(pg, "tech")
    pick(pg, "seat")
    host.put(record("answered", "tech"))
    pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.openAsk('tech', 'server/lobby.ts'))")
    bubble(pg).wait_for(timeout=WAIT_MS)
    bubble(pg).get_by_role("button", name="Make it a change").click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.change") == [{"idea": "seat", "party": "tech", "part": "server/lobby.ts", "text": "Why does the timer run on the server?"}]
    assert host.sent("ideas.ask_clear") == [{}] and host.ask is None, "the answer is put away: the change is the card now"


def test_keep_the_spec_drops_it_and_talk_more_opens_the_bubble_again_with_the_part_and_the_words_kept(asked):
    pg, host = asked
    host.needs = [row()]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    lifted.get_by_role("button", name="Keep the spec").click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"leader_change\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.change_keep") == [{"idea": "results", "id": "c1", "via": "hand"}] and host.sent("ideas.change_take") == []
    host.needs = [row()]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').click(position={"x": 10, "y": 20})
    pg.locator(".hand-lifted").get_by_role("button", name="Talk more").click()
    bubble(pg).wait_for(timeout=WAIT_MS)
    settled(pg)
    assert bubble(pg).get_attribute("data-ask") == "tech" and field(pg).input_value() == "Keep the seat for a minute after a drop"
    assert about(pg) == [RESULTS_TITLE, "server/lobby.ts"] and len(host.sent("ideas.change_keep")) == 2


def test_a_design_change_is_three_looks_to_choose_from_and_let_design_decide(asked):
    pg, host = asked
    looks = [{"key": str(n), "name": name, "why": f"Why {name}", "lines": [f"changed Results — {name} for the winner"]} for n, name in ((1, "Banner"), (2, "Crown"), (3, "Podium"))]
    host.needs = [row("looks", goal="art", party="art", looks=looks, before={"tasks": [], "lines": []}, after={"tasks": [], "lines": []}, usd_low=None, usd_high=None)]
    host.push()
    card = pg.locator('.hand-card[data-kind="leader_change"]')
    card.wait_for(timeout=WAIT_MS)
    assert card.locator(".ork-gem").count() == 0, "looks cost nothing of their own"
    card.click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    assert [b.get_attribute("data-look") for b in lifted.locator(".hand-change__look").all()] == ["1", "2", "3"] and lifted.locator('[data-side="now"]').count() == 0
    assert "Podium for the winner" in lifted.locator('[data-look="3"]').inner_text() and lifted.get_by_role("button", name="Accept").count() == 0
    lifted.locator('[data-look="3"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"leader_change\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.change_take") == [{"idea": "results", "id": "c1", "via": "hand", "look": "3"}]
    host.needs = [row("looks", goal="art", party="art", looks=looks, usd_low=None, usd_high=None)]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').click(position={"x": 10, "y": 20})
    pg.locator(".hand-lifted").get_by_role("button", name="Let Art decide").click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"leader_change\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.change_take")[-1] == {"idea": "results", "id": "c1", "via": "hand", "decide": True}
