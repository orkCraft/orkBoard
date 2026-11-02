"""Spec 128 part F.1 (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.4; mockup docs/mockups/goal-card/), in a real browser against a stub host: the Orkmaster's tab with a goal picked draws that goal's plan alone, its tasks in
their leaders' lanes (planned ones faint, done ones grey, the one at work glowing), an SVG arrow from each task to the tasks that wait for it (dashed from a task done), and a goal with no plan yet says its tasks are dealt to the leaders when it is agreed.
Nothing picked: the Board as it was; Esc and the title's cross pick nothing."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_goal_view_browser import open_goals, pick_music  # noqa: E402
from tests.test_hand_desktop_browser import sig  # noqa: E402

pytestmark = pytest.mark.browser

ARROWS = {("m1", "m2"), ("m1", "m3"), ("m2", "m3"), ("m3", "m4")}


def arrows(pg):
    return pg.eval_on_selector_all(".plan-arrow", "els => els.map((e) => [e.dataset.from, e.dataset.to, e.classList.contains('is-done')])")


def test_with_nothing_picked_the_board_is_as_it_was_and_a_goal_picked_draws_its_plan_alone_in_its_leaders_lanes(gui):
    pg, host, log = open_goals(gui)
    try:
        pg.wait_for_selector(".table-board", timeout=WAIT_MS)
        assert pg.locator(".table-board--plan, .plan-arrows").count() == 0
        assert pg.locator('.table-card[data-goal="timer"]').count() == 1, "nothing picked: every goal's tasks are on the Board"
        pick_music(pg)
        board = pg.locator('.table-board--plan[data-plan="music"]')
        board.wait_for(timeout=WAIT_MS)
        placed = {t.get_attribute("data-plan-task"): t.evaluate("(e) => e.closest('.table-lane').dataset.party") for t in board.locator("[data-plan-task]").all()}
        assert placed == {"m1": "tech", "m2": "design", "m3": "tech", "m4": "product"}, "each task stands in the lane of the leader whose work it is"
        assert pg.locator('.table-card[data-goal="timer"]').count() == 0, "another goal's tasks are not drawn"
        assert pg.locator(".table-lane--first").count() == 0 and pg.locator(".table-goal").count() == 0, "its tasks, no strips of other goals"
        assert [p for p in pg.locator('.table-lane[data-party="release"]').all_inner_texts()] == ["Nothing for Release"]
        order = pg.eval_on_selector_all('.table-lane[data-party="tech"] [data-plan-task]', "els => els.map((e) => e.dataset.planTask)")
        assert order == ["m1", "m3"], "the order the plan runs them"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_planned_tasks_are_faint_done_ones_grey_and_the_one_at_work_glows(gui):
    pg, host, log = open_goals(gui)
    try:
        pick_music(pg)
        pg.wait_for_selector('.plan-slot[data-plan-task="m1"]', timeout=WAIT_MS)
        phase = {s.get_attribute("data-plan-task"): s.get_attribute("data-phase") for s in pg.locator(".plan-slot").all()}
        assert phase == {"m1": "done", "m2": "work", "m3": "planned", "m4": "planned"}
        opacity = lambda t: float(pg.evaluate(f"() => getComputedStyle(document.querySelector('.plan-slot[data-plan-task=\"{t}\"]')).opacity"))  # noqa: E731
        assert opacity("m2") == 1 and 0.5 < opacity("m3") < 0.7 and opacity("m1") < 0.5, "the planned faint, the done fainter, the one at work whole"
        assert "grayscale" in pg.evaluate("() => getComputedStyle(document.querySelector('.plan-slot[data-plan-task=\"m1\"]')).filter"), "done: grey"
        assert pg.locator('.plan-slot[data-plan-task="m2"] .table-stage .ork-elem.is-glowing').count() == 1, "at work: the goal's rune glowing, as on the Board"
        assert pg.locator('.plan-slot[data-plan-task="m3"] .ork-elem.is-glowing').count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_arrow_runs_from_each_task_to_the_tasks_that_wait_for_it_and_one_from_a_task_done_is_dashed(gui):
    pg, host, log = open_goals(gui)
    try:
        pick_music(pg)
        pg.wait_for_selector(".plan-arrow", state="attached", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelectorAll('.plan-arrow').length === 4", timeout=WAIT_MS)
        got = arrows(pg)
        assert {(a, b) for a, b, _d in got} == ARROWS and len(got) == 4
        assert {(a, b) for a, b, done in got if done} == {("m1", "m2"), ("m1", "m3")}, "from a task done: dashed"
        dash = pg.evaluate("() => [...document.querySelectorAll('.plan-arrow')].map((p) => [p.dataset.from, getComputedStyle(p).strokeDasharray])")
        assert all((d != "none") == (f == "m1") for f, d in dash), dash
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.plan-arrows')).pointerEvents") == "none", "an arrow takes no press"
        assert pg.locator(".plan-arrows[aria-hidden='true']").count() == 1
        # each arrow ends at the card that waits: its last point lies on the card's edge
        ends = pg.evaluate("""() => {
          const svg = document.querySelector('.plan-arrows'), s = svg.getBoundingClientRect();
          return [...svg.querySelectorAll('.plan-arrow')].map((p) => {
            const a = p.getPointAtLength(0), b = p.getPointAtLength(p.getTotalLength());
            const box = (id) => { const r = document.querySelector('.plan-slot[data-plan-task=\"' + id + '\"]').getBoundingClientRect(); return { l: r.left - s.left, t: r.top - s.top, r: r.right - s.left, b: r.bottom - s.top }; };
            const near = (pt, c) => pt.x >= c.l - 5 && pt.x <= c.r + 5 && pt.y >= c.t - 5 && pt.y <= c.b + 5;
            return [p.dataset.from + '>' + p.dataset.to, near(a, box(p.dataset.from)), near(b, box(p.dataset.to))];
          });
        }""")
        assert all(start and end for _k, start, end in ends), ends
        # a lane to the right is reached along the row, a task below in the same lane from the card's foot
        d = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.plan-arrow')].map((p) => [p.dataset.from + '>' + p.dataset.to, p.getAttribute('d')]))")
        assert d["m1>m2"].startswith("M") and "C" in d["m1>m2"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_pressed_on_the_plan_is_lifted_and_the_arrows_follow_a_plan_that_changes(gui):
    pg, host, log = open_goals(gui)
    try:
        pick_music(pg)
        pg.wait_for_function("() => document.querySelectorAll('.plan-arrow').length === 4", timeout=WAIT_MS)
        pg.locator('.plan-slot[data-plan-task="m2"] .table-card').click()
        pg.wait_for_selector(".table-back", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "lifted") == "t:task:music/m2"
        pg.keyboard.press("Escape")
        # m3 waits for nothing now: its two arrows go
        for n in host.nodes:
            if n["slug"] == "music":
                for t in n["tasks"]:
                    if t["id"] == "m3":
                        t["after"] = []
        host.bump(None)
        pg.wait_for_function("() => document.querySelectorAll('.plan-arrow').length === 2", timeout=WAIT_MS)
        assert {(a, b) for a, b, _d in arrows(pg)} == {("m1", "m2"), ("m3", "m4")}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_with_no_plan_yet_says_its_tasks_are_dealt_to_the_leaders_when_it_is_agreed(gui):
    pg, host, log = open_goals(gui)
    try:
        pg.locator('.col-card[data-goal="fresh"]').click()
        pg.wait_for_selector(".plan-wait", timeout=WAIT_MS)
        assert pg.locator(".plan-wait").inner_text() == "Its tasks are dealt to the leaders when it is agreed"
        assert pg.locator("[data-plan-task], .plan-arrow").count() == 0 and pg.locator(".table-board--plan").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_esc_and_the_titles_cross_pick_nothing_and_the_board_is_as_it_was(gui):
    pg, host, log = open_goals(gui)
    try:
        pick_music(pg)
        pg.wait_for_selector(".plan-arrow", state="attached", timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".table-board:not(.table-board--plan)", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "" and pg.locator('.table-card[data-goal="timer"]').count() == 1
        pick_music(pg)
        pg.wait_for_selector(".plan-arrow", state="attached", timeout=WAIT_MS)
        assert pg.locator(".table-title__unpick").get_attribute("aria-label") == "Look at the whole project"
        pg.locator(".table-title__unpick").click()
        pg.wait_for_selector(".table-board:not(.table-board--plan)", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)
