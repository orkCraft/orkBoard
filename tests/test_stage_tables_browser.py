"""Spec 168 part C3 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.16.1, .3, .5, .7; mockup docs/mockups/table-template/), in a real browser at 1366 x 768 against a stub host: the Orkmaster's tab shows a table for each stage of the
goal picked: **the project** (a lane a leader, its goals in Talk as small cards over the cascade), **an idea** (the route and its price on a plate with *Judge again now*, a small card with its verdict's sign under each leader), **a spec** (a big card under
each leader, face up once its section is written, a back before), **the implementation** (the plan's tasks in their leaders' lanes, a later leader's step a placeholder). The cards are of the two sizes only (144 x 202 and 56 x 78), *Judge again now*
sends `ideas.judge_again`, and a card pressed picks its goal and opens its leader's tab. Pictures to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import sig  # noqa: E402
from tests.test_table_desktop_browser import SPEC_PAGE, WayHost, pick, shot, task, watch  # noqa: E402

pytestmark = pytest.mark.browser

ROUTE = [{"step": "party", "party": "game", "goal": "seat", "state": "working", "done": 0, "total": 0}, {"step": "party", "party": "tech", "goal": "seat", "state": "working", "done": 0, "total": 2},
         {"step": "party", "party": "art", "goal": "seat", "state": "working", "done": 0, "total": 0}]
SAY = {"leaders": [{"party": "game", "leader": "Game design lead", "craft": "product", "weigher": False, "verdict": "go", "why": "The seat is a promise to the player", "needs": [], "better": []},
                   {"party": "tech", "leader": "Architect", "craft": "engineering", "weigher": False, "verdict": "doubt", "why": "One clock on the server",
                    "needs": [{"id": "n1", "kind": "risk", "line": "A rejoin may reset the clock", "rests_on": "", "ways": [], "state": "open"}, {"id": "n2", "kind": "question", "line": "Where does the timer run?", "rests_on": "", "ways": [], "state": "open"}],
                    "better": []}],
       "rewrite": None, "fork": None, "judged": 0, "judge_left": 2, "answered": [], "waiting": [], "to_judge": []}
SIZES = {(56, 78), (144, 202)}


class StageHost(WayHost):
    """The table's host with the goal `seat` routed through Game design, Tech and Art: what the leaders said (Game design go, Tech doubt with two to answer, Art not yet), its price, and the sections of its spec written so far."""

    def __init__(self, state, written=("Game design", "Tech"), tasks=None):
        super().__init__(state=state)
        seat = next(n for n in self.nodes if n["slug"] == "seat")
        seat.update(route=copy.deepcopy(ROUTE), say=copy.deepcopy(SAY) if state in ("talk", "routed") else None, estimate={"usd_low": 0.2, "usd_high": 0.6}, place="table")
        seat["tasks"] = tasks if tasks is not None else []                       # a goal in Talk or in its spec has no task at work (one that has is the implementation's)
        self.written = written

    def handle(self, name, a):
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": "Keep the seat when a socket reconnects", "state": "sections", "track": "tech", "sections": [s for s in SPEC_PAGE if s["name"] in ("Gist", "Route", *self.written)]}
        if name == "ideas.judge_again":
            self.log.append((name, a))
            return {"ok": True, "idea": a["idea"], "parties": ["tech"]}
        return super().handle(name, a)


def stage(gui, state, errors, **kw):
    """The window at 1366 x 768 against a StageHost: `(page, host)`."""
    server, browser = gui
    host = StageHost(state, **kw)
    pg = browser.new_context(viewport={"width": 1366, "height": 768}).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-board").first.wait_for(timeout=WAIT_MS)
    return pg, host


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def sizes(pg, selector):
    return {(round(b["width"]), round(b["height"])) for b in (e.bounding_box() for e in pg.locator(selector).all()) if b}


def test_the_project_lays_a_leaders_goals_in_talk_as_small_cards_over_its_cascade(gui):
    errors: list[str] = []
    pg, host = stage(gui, "talk", errors)
    row = pg.locator('.table-lane[data-party="tech"] .sb-row[data-row="ideas"]')
    row.wait_for(timeout=WAIT_MS)
    assert row.locator('[data-goal="seat"][data-verdict="doubt"]').count() == 1 and row.locator(".verdict.is-doubt").count() == 1, "Tech has said: its card is face up with its sign"
    assert pg.locator('.table-lane[data-party="game"] [data-goal="seat"][data-verdict="go"] .verdict.is-go').count() == 1
    assert pg.locator('.table-lane[data-party="art"] [data-goal="seat"][data-assessing]').count() == 1, "Art has not said: a back"
    assert sizes(pg, ".sb-row .ork-card") == {(56, 78)}
    assert pg.locator(".sb-plate, .table-board--plan").count() == 0, "nothing is picked: the lanes of the project"
    assert pg.locator('.table-lane[data-party="game"] .sb-rows ~ .table-goal .table-casc').count() > 0, "the cascade stays under the rows"
    shot(pg, "c3-project.png")
    row.locator('[data-goal="seat"]').click()
    assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "tech"
    finish(pg, errors)


def test_an_idea_in_talk_is_its_route_and_price_on_a_plate_and_a_small_card_under_each_leader(gui):
    errors: list[str] = []
    pg, host = stage(gui, "talk", errors)
    pick(pg, "seat")
    plate = pg.locator('.sb-plate[data-view="route"]')
    plate.wait_for(timeout=WAIT_MS)
    assert [e.get_attribute("data-party") for e in plate.locator(".phase-route__step").all()] == ["game", "tech", "art"]
    assert "Game design, then Tech, then Art" in plate.locator(".phase-route__words").inner_text() and "$0.20" in plate.inner_text()
    lanes = {lane.get_attribute("data-party"): lane for lane in pg.locator(".sb--idea .table-lane[data-party]").all()}
    assert lanes["game"].locator(".verdict.is-go").count() == 1 and lanes["tech"].locator(".verdict.is-doubt").count() == 1
    assert lanes["tech"].locator('.ork-card.sm[data-signal="alert"]').count() == 1, "two questions wait: the alert frame"
    assert lanes["art"].locator(".sb-back").count() == 1 and "Assessing" in lanes["art"].inner_text()
    assert "Doubt · 2 to answer" in lanes["tech"].inner_text()
    assert sizes(pg, ".sb--idea .ork-card") == {(56, 78)}, "the two sizes only: here the small one"
    shot(pg, "c3-idea.png")
    finish(pg, errors)


def test_judge_again_now_sends_the_command_and_a_card_pressed_picks_its_goal_and_opens_its_leaders_tab(gui):
    errors: list[str] = []
    pg, host = stage(gui, "talk", errors)
    pick(pg, "seat")
    pg.locator('.sb-plate [data-judge]').click()
    pg.wait_for_function("() => true")
    assert ("ideas.judge_again", {"idea": "seat"}) in host.log
    pg.locator('.sb--idea .table-lane[data-party="game"] .ork-card.sm').click()
    assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "game"
    finish(pg, errors)


def test_a_spec_is_a_big_card_under_each_leader_face_up_once_its_section_is_written(gui):
    errors: list[str] = []
    pg, host = stage(gui, "sections", errors, written=("Game design",))
    pick(pg, "seat")
    pg.locator('.sb--spec [data-spec-card="game"][data-state="written"]').wait_for(timeout=WAIT_MS)
    assert pg.locator('.sb--spec [data-spec-card="tech"][data-state="writing"]').count() == 1 and pg.locator('.sb--spec [data-spec-card="art"][data-state="writing"]').count() == 1
    assert "The timer shows" in pg.locator('[data-spec-card="game"]').inner_text()
    assert sizes(pg, ".sb--spec [data-spec-card]") == {(144, 202)}
    shot(pg, "c3-spec.png")
    pg.locator('[data-spec-card="tech"]').click()
    assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "tech"
    finish(pg, errors)


def test_the_implementation_is_the_tasks_top_down_in_their_leaders_lanes_and_a_later_step_a_placeholder(gui):
    errors: list[str] = []
    tasks = [task("s1", "Keep the seat when a socket reconnects", "running", party="tech"), task("s2", "Reset the round timer when a player rejoins", "waiting", party="tech", after=["s1"])]
    pg, host = stage(gui, "working", errors, tasks=tasks)
    pick(pg, "seat")
    pg.locator('.table-board--plan[data-plan="seat"]').wait_for(timeout=WAIT_MS)
    pg.locator('.table-board--plan [data-plan-task="s2"]').wait_for(timeout=WAIT_MS)
    assert pg.locator('.table-lane[data-party="game"] .sb-later').count() == 1 and pg.locator('.table-lane[data-party="art"] .sb-later').count() == 1, "a later leader's step is a placeholder"
    assert "when the step before it is accepted" in pg.locator('.sb-later').first.inner_text()
    assert pg.locator(".plan-arrow").count() == 1
    assert sizes(pg, ".table-board--plan .plan-slot .ork-card") == {(144, 202)}
    shot(pg, "c3-implementation.png")
    finish(pg, errors)
