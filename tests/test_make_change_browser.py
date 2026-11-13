"""Spec 128 E (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md; decisions §206.5) in a real browser against the table's stub host: the open leader's bubble says what it is about (the picked goal's rune and name, or
*The whole project*) and carries a part of a goal's change as a chip with × (`openAsk(tab, part)`); under an answer *Make it a change* stands only for a goal that is agreed or at work on a leader's tab (never the Orkmaster's), *Make it a goal* only for
nothing picked or a goal done; pressed, it sends `ideas.change {idea, party, part?, text}` and puts the answer away. The decision in the hand (hand/changecard.js): lifted, *Now* and *Proposed* side by side, the cost, **Accept**, **Talk more** (the bubble
again with the part and the words kept) and **Keep the spec**; Design's three looks as choices and *Let Design decide*."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import AskHost, bubble, record, start  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

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




