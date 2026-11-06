"""Spec 156 part C (docs/specs/156-one-pick-and-the-release-column.md C.4, decisions §261.4), in a real browser against a stub host: with a goal picked the table shows its phase at the open tab (Tech's stance in Talk, its section in Spec, GoalView at work,
the result and the quality record when done), the phase marks in the title are spans (no `button[data-phase]`), *Earlier: Talk · Spec* unfolds what a phase said in place and folds again, and through the Orkmaster a routed goal not yet talked shows its route and cost.
Nothing opens over the pane."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_quality_browser import QualityHost, start  # noqa: E402
from tests.test_table_desktop_browser import ROUTE_ROW, open_tab, pick, way  # noqa: E402

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


def test_a_goal_in_spec_shows_techs_section_and_earlier_talk(gui):
    pg, host, errors = phased(gui, "sections")
    pg.locator('[data-view="spec"] .spec-section').wait_for(timeout=WAIT_MS)
    assert pg.locator('[data-view="spec"] .spec-section').get_attribute("data-party") == "tech"
    assert "The seat is kept" in pg.locator('[data-view="spec"]').inner_text()
    assert pg.locator(".phase-earlier__line").inner_text().replace("\n", " ").strip().lower() == "earlier: talk"
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


def test_a_goal_done_shows_the_result_and_under_it_the_quality_record(gui):
    host = QualityHost([])
    pg, errors = start(gui, "wide", host)
    open_tab(pg, "tech")
    pick(pg, "seat")
    pg.locator(".gv").wait_for(timeout=WAIT_MS)
    pg.locator('.phase-quality .quality-page[data-kind="quality"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".gv").get_attribute("data-view") == "changed"
    assert pg.locator(".table-over").count() == 0 and pg.locator("button[data-phase]").count() == 0
    assert pg.locator('.table-phase[data-phase="done"]').get_attribute("aria-current") == "step"
    assert pg.locator('[data-earlier="talk"]').count() == 1
    finish(pg, errors)


def test_through_the_orkmaster_a_routed_goal_not_talked_shows_its_route_and_cost(gui):
    errors: list[str] = []
    pg, host = way(gui, "wide", errors, state="routed", needs=[ROUTE_ROW])
    pick(pg, "seat")
    view = pg.locator('[data-view="route"]')
    view.wait_for(timeout=WAIT_MS)
    assert [e.get_attribute("data-party") for e in view.locator(".phase-route__step").all()] == ["game", "tech"]
    assert "then" in view.locator(".phase-route__words").inner_text()
    assert view.locator(".hand-way__cost").count() == 1 and "6 calls" in view.inner_text()
    assert pg.locator(".phase-earlier").count() == 0 and pg.locator("button[data-phase]").count() == 0
    finish(pg, errors)
