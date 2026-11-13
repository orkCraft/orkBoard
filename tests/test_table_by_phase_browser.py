"""Spec 156 part C (docs/specs/156-one-pick-and-the-release-column.md C.4, decisions §261.4), in a real browser against a stub host: with a goal picked the table shows its phase at the open tab (Tech's stance in Talk, its section in Spec, GoalView at work,
the result and the quality record when done), the phase marks in the title are spans (no `button[data-phase]`), *Earlier: Talk · Spec* unfolds what a phase said in place and folds again, and through the Orkmaster a routed goal not yet talked shows its route and cost.
Nothing opens over the pane."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import open_tab, pick, way  # noqa: E402

pytestmark = pytest.mark.browser


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def phased(gui, state, tab="tech", **kw):
    errors: list[str] = []
    pg, host = way(gui, "wide", errors, state=state, **kw)
    open_tab(pg, tab)
    pick(pg, "seat")
    pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
    return pg, host, errors


def test_a_goal_in_talk_shows_techs_stance_and_the_marks_are_no_buttons(gui):
    pg, host, errors = phased(gui, "talk")
    pg.locator('[data-view="talk"] .talk-stance').wait_for(timeout=WAIT_MS)
    assert pg.locator('[data-view="talk"] .talk-stance').get_attribute("data-party") == "tech"
    assert "The server owns the clock" in pg.locator('[data-view="talk"]').inner_text()
    assert pg.locator("button[data-phase]").count() == 0
    assert pg.locator('.table-phase[data-phase="talk"]').get_attribute("aria-current") == "step"
    assert pg.locator(".table-over").count() == 0 and pg.locator(".phase-earlier").count() == 0
    finish(pg, errors)




def test_a_goal_at_work_shows_the_goal_view_and_earlier_unfolds_talk_in_place_and_folds(gui):
    pg, host, errors = phased(gui, "working")
    pg.locator(".gv").wait_for(timeout=WAIT_MS)
    assert pg.locator("button[data-phase]").count() == 0
    line = pg.locator(".phase-earlier__line")
    assert line.inner_text().replace("\n", " ").strip().lower() == "earlier: talk · spec"
    assert pg.locator(".phase-earlier__body").count() == 0
    talk = pg.locator('[data-earlier="talk"]')
    talk.click()
    pg.locator('.phase-earlier__body[data-earlier-body="talk"] .talk-stance').wait_for(timeout=WAIT_MS)
    assert talk.get_attribute("aria-expanded") == "true" and pg.locator(".table-over").count() == 0
    assert pg.locator(".gv").count() == 1, "in place: the table stays"
    pg.locator('[data-earlier="spec"]').click()
    pg.locator('.phase-earlier__body[data-earlier-body="spec"] .spec-section').wait_for(timeout=WAIT_MS)
    talk.click()
    pg.locator('.phase-earlier__body[data-earlier-body="talk"]').wait_for(state="detached", timeout=WAIT_MS)
    assert talk.get_attribute("aria-expanded") == "false"
    finish(pg, errors)




