"""Spec 43 D on the desktop (docs/specs/43-party-measured.md §4, Tests → D): Needs you's party row with *Take it out* and *Keep it*, never
counted. (A checker's muted line and the dialog's *Its check* line were on *Agents*, which left the desktop: spec 98 A.)"""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import StubHost, _calls, _open, _sent, _show_goal, _stop  # noqa: E402

pytestmark = pytest.mark.browser

ROW = {"idea": "", "goal": "ship-sync", "kind": "party", "by": "reviewer", "title": "Take Reviewer out of Ship sync's party?",
       "text": "It found nothing in the last 8 goals; a check costs about $0.35.", "priority": "normal", "blocks": False, "at": "2026-10-20T03:00:00"}


@pytest.fixture
def shell(gui):
    host = StubHost()
    host.party_rows = [dict(ROW)]
    pg, host, errors = _open(gui, host=host)
    _show_goal(pg)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _needs(pg):
    pg.locator(".arena-hc").first.wait_for(timeout=WAIT_MS)
    return _stop(pg, "party")


def test_the_party_row_is_a_proposal_s_with_take_it_out_and_keep_it_and_is_never_counted(shell):
    pg, host = shell
    row = _needs(pg)
    assert "Take Reviewer out of Ship sync's party?" in row.inner_text() and "It found nothing in the last 8 goals; a check costs about $0.35." in row.inner_text()
    assert "proposed" in row.inner_text().lower()
    assert row.get_by_role("button", name="Take it out: Take Reviewer out of Ship sync's party?").is_visible()
    rows = [k for k in pg.locator(".arena-hc").evaluate_all("els => els.map(e => e.dataset.kind)") if k not in ("result", "gate")]       # the stops: the results and the gate's batch are cards of their own
    assert rows[-1] == "todo"                                                                           # a to-do lies last of all (spec 87 §4.3)
    rows = rows[:-1]
    assert rows[-1] == "party" or rows[-2:] == ["proposal", "party"]                                    # then the party's, with the proposals
    row.get_by_role("button", name="Keep it: Take Reviewer out of Ship sync's party?").click()
    why = row.get_by_label("Why not: Take Reviewer out of Ship sync's party?")
    assert why.get_attribute("placeholder") == "Why not? (optional, one line)"
    why.fill("the public page needs it")
    row.get_by_role("button", name="Keep: Take Reviewer out of Ship sync's party?").click()
    assert _sent(pg, host, ("ideas.party_answer", {"goal": "ship-sync", "take": False, "reason": "the public page needs it"}))
    pg.wait_for_function("() => document.querySelectorAll('.arena-hc[data-kind=party]').length === 0", timeout=WAIT_MS)


def test_take_it_out_answers_at_once_and_a_keep_with_no_reason_sends_none(shell):
    pg, host = shell
    _needs(pg).get_by_role("button", name="Take it out: Take Reviewer out of Ship sync's party?").click()
    assert _sent(pg, host, ("ideas.party_answer", {"goal": "ship-sync", "take": True}))
    pg.mouse.move(5, 5)                                                                                 # nothing shifts under the pointer: it is away
    host.party_rows = [dict(ROW)]
    host.bump({})
    pg.locator(".arena-hc[data-kind=party]").wait_for(timeout=WAIT_MS)
    _stop(pg, "party").get_by_role("button", name="Keep it: Take Reviewer out of Ship sync's party?").click()
    pg.get_by_role("button", name="Keep: Take Reviewer out of Ship sync's party?").click()
    assert _calls(pg, host, "ideas.party_answer", 2)[-1] == {"goal": "ship-sync", "take": False}


def test_the_row_is_one_of_the_party_s_stops_along_the_bottom(shell):
    pg, host = shell
    host.party_rows = [dict(ROW)]
    host.bump({})
    pg.locator(".arena-hc[data-kind=party]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-hand .arena-hc[data-kind=party]").count() == 1                             # the stops along the bottom (their count), the row among them
    assert pg.locator('.arena-phead[aria-current=true]').get_attribute("data-goal") == "ship-sync" and pg.locator('.arena-phead[aria-current=true] .arena-phead__stop').count() == 0      # the shown party's stops are not counted on its heading (spec 52 §4.5)
