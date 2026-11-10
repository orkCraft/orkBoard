"""Spec 168 part G2 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.16.10, §283.16.11), in a real browser at 1366 x 768 against a stub host: a goal done and picked shows its result.

Through the Orkmaster: a lane a leader of the goal, in it a big card (144 x 202) that says what its section planned against what was built and, under it, its problems lit (a small card, 56 x 78, for each kind: a *Done when* line not met or not checked, a failed
task, a red test, a finding, a task sent back) and a line for each. Through a leader: the parts of the goal as cards of the one size, the leader's map with the planned parts outlined and the built filled, the work before and after (Tech's System by commit,
Design's pictures of a screen) and every error of the goal's work as a line. The cards are of the two sizes only. Pictures to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_goal_view_browser import RESULT, GoalHost  # noqa: E402
from tests.test_hand_desktop_browser import sig  # noqa: E402
from tests.test_table_desktop_browser import pick, shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

SIZES = {(56, 78), (144, 202)}
PIXEL = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='120'><rect width='160' height='120' fill='%23233'/><rect x='12' y='14' width='136' height='22' fill='%2380b060'/><rect x='12' y='48' width='90' height='12' fill='%23789'/><rect x='12' y='70' width='60' height='30' fill='%23a86'/></svg>"
PIC = {"goal": "codes", "task": "c1", "id": "c1-shot-r1", "file": "shot.png", "w": 800, "h": 600, "at": "2026-10-20T10:00:00", "url": PIXEL}
RESULTS = copy.deepcopy(RESULT)
RESULTS["parties"][0]["done_when"] = [{"text": "Rounds keep their score", "state": "ok"}, {"text": "The lobby opens", "state": "unchecked", "word": "not checked"}]
RESULTS["parties"].append({"party": "design", "title": "Design", "parts": [{"id": "results", "kind": "changed", "verdict": "ok", "line": "the winner first", "note": ""},
                                                                         {"id": "podium", "kind": "new", "verdict": "missing", "line": "nothing of it landed", "note": ""}],
                           "done_when": [{"text": "The winner shows first", "state": "unmet", "word": "not met"}]})
RESULTS["errors"] = [{"party": "tech", "kind": "failed", "task": "c2", "title": "Keep the rounds", "line": "npm test: 2 failed"},
                     {"party": "tech", "kind": "test", "task": "c1", "title": "Make the codes", "line": "tests/test_score.py::test_round"},
                     {"party": "tech", "kind": "finding", "task": "c3", "title": "Review", "line": "src/score: leaks a timer"},
                     {"party": "design", "kind": "sent_back", "task": "c4", "title": "Draw the winner", "line": "sent back 2 times"}]
RESULTS["before_after"] = {
    "tech": {"kind": "parts", "before": {"commit": "a" * 40, "short": "aaaaaaa", "at": ""}, "after": {"commit": "b" * 40, "short": "bbbbbbb", "at": ""}, "none": "",
             "parts": [{"path": "src/lobby", "name": "lobby", "before": None, "after": {"count": 2, "uses": ["src/net"]}, "change": "new", "uses_new": ["src/net"], "uses_gone": []},
                       {"path": "src/old", "name": "old", "before": {"count": 1, "uses": []}, "after": None, "change": "gone", "uses_new": [], "uses_gone": []},
                       {"path": "src/score", "name": "score", "before": {"count": 3, "uses": []}, "after": {"count": 5, "uses": ["src/net"]}, "change": "changed", "uses_new": ["src/net"], "uses_gone": []}]},
    "design": {"kind": "screens", "screens": [{"screen": "results", "name": "Results", "path": "/results", "before": PIC, "after": {**PIC, "id": "c2-shot-r1"}},
                                              {"screen": "podium", "name": "Podium", "path": "/podium", "before": None, "after": {**PIC, "id": "c3-shot-r1"}}]}}


def open_result(gui, errors, result=None):
    """The window at 1366 x 768 against the goal host, the goal `codes` (done) not picked yet: `(page, host)`."""
    server, browser = gui
    host = GoalHost()
    host.result = result or RESULTS
    next(n for n in host.nodes if n["slug"] == "codes")["route"] = [{"party": "tech", "leader": "tech-lead", "head": {"race": "orc", "tier": "elder"}},
                                                                  {"party": "design", "leader": "design-lead", "head": {"race": "dryad", "tier": "elder"}}]
    pg = browser.new_context(viewport={"width": 1366, "height": 768}).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".col-card", timeout=WAIT_MS)
    return pg, host


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def sizes(pg, selector):
    return {(round(b["width"]), round(b["height"])) for b in (e.bounding_box() for e in pg.locator(selector).all()) if b}


def texts(pg, selector):
    return [" ".join(t.split()) for t in pg.locator(selector).all_text_contents()]


def test_through_the_orkmaster_a_goal_done_is_a_lane_a_leader_with_planned_against_built_and_its_problems_lit(gui):
    errors: list[str] = []
    pg, host = open_result(gui, errors)
    assert sig(pg, "frame/state.js", "tab") == "orkmaster"
    pick(pg, "codes")
    pg.locator('.sb--result [data-result-card="tech"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-board--plan").count() == 0, "a goal done is its result, not its plan"
    tech, design = pg.locator('.sb--result .table-lane[data-party="tech"]'), pg.locator('.sb--result .table-lane[data-party="design"]')
    assert tech.locator("[data-result-card]").count() == 1 and design.locator("[data-result-card]").count() == 1, "a lane a leader of the goal"
    assert pg.locator('.sb--result .table-lane[data-party="product"] [data-result-card]').count() == 0
    card = tech.locator("[data-result-card]")
    assert texts(pg, '[data-result-card="tech"] [data-line]') == ["Planned 3 · built 1", "✓ 1 · ≠ 1 · ✗ 1 · + 1", "Done when: 1 met · 1 not checked"], "planned against built, in the honest words"
    assert texts(pg, '[data-result-card="design"] [data-line]') == ["Planned 2 · built 1", "✓ 1 · ✗ 1", "Done when: 1 not met"]
    assert card.get_attribute("data-signal") == "danger" and design.locator("[data-result-card]").get_attribute("data-signal") == "danger", "a failed task, a line not met: the danger frame"
    kinds = lambda lane: [e.get_attribute("data-problem") for e in lane.locator(".rb-smalls .ork-card").all()]  # noqa: E731
    assert kinds(tech) == ["failed", "test", "not_checked", "finding"] and kinds(design) == ["not_met", "sent_back"], "a small card for each kind of problem, the worst first"
    assert tech.locator('.rb-smalls [data-problem="failed"]').get_attribute("data-signal") == "danger" and tech.locator('.rb-smalls [data-problem="finding"]').get_attribute("data-signal") == "alert"
    assert texts(pg, '.table-lane[data-party="tech"] .rb-lines li') == [
        "Not checked The lobby opens", "Failed Keep the rounds: npm test: 2 failed", "Red test tests/test_score.py::test_round · Make the codes", "Finding src/score: leaks a timer"]
    assert texts(pg, '.table-lane[data-party="design"] .rb-lines li') == ["Not met The winner shows first", "Sent back Draw the winner: sent back 2 times"]
    assert "4 to look at" not in pg.locator(".rb-plate").inner_text() and "6 to look at" in pg.locator(".rb-plate").inner_text()
    assert sizes(pg, ".sb--result .ork-card") == SIZES, "the two sizes only"
    assert sizes(pg, ".sb--result [data-result-card]") == {(144, 202)} and sizes(pg, ".sb--result .rb-smalls .ork-card") == {(56, 78)}
    shot(pg, "g2-orkmaster.png")
    card.click()
    assert sig(pg, "frame/state.js", "picked") == "codes" and sig(pg, "frame/state.js", "tab") == "tech", "a card pressed opens its leader's tab"
    finish(pg, errors)


def test_a_leader_with_no_problem_is_not_lit_and_the_goal_not_read_says_so(gui):
    errors: list[str] = []
    clean = copy.deepcopy(RESULTS)
    clean["errors"] = [e for e in clean["errors"] if e["party"] != "tech"]
    clean["parties"][0]["done_when"] = [{"text": "Rounds keep their score", "state": "ok"}]
    pg, host = open_result(gui, errors, clean)
    pick(pg, "codes")
    pg.locator('.sb--result [data-result-card="tech"]').wait_for(timeout=WAIT_MS)
    assert pg.locator('[data-result-card="tech"]').get_attribute("data-signal") is None and pg.locator('.table-lane[data-party="tech"] .rb-smalls .ork-card').count() == 0
    assert pg.locator('.table-lane[data-party="tech"] .rb-lines').count() == 0, "nothing lit where nothing is wrong"
    finish(pg, errors)


def test_through_tech_a_goal_done_is_planned_against_built_on_its_map_before_and_after_by_commit_and_every_error(gui):
    errors: list[str] = []
    pg, host = open_result(gui, errors)
    pg.locator('.table-tab[data-tab="tech"]').click()
    pick(pg, "codes")
    view = pg.locator('.gv[data-view="changed"][data-party="tech"]')
    view.wait_for(timeout=WAIT_MS)
    pg.wait_for_selector(".rb-scheme .rb-chip", timeout=WAIT_MS)
    assert sizes(pg, ".gv-card") == {(144, 202)}, "the parts of the goal as cards of the one size"
    chips = {c.get_attribute("data-id"): c for c in view.locator(".rb-chip").all()}
    assert {"src/score", "src/net", "src/other", "src/old", "src/lobby"} <= set(chips), "the whole map, a part a goal made beside it"
    assert chips["src/score"].get_attribute("data-verdict") == "ok" and chips["src/score"].get_attribute("data-planned") == "1"
    assert chips["src/lobby"].get_attribute("data-verdict") == "differs" and chips["src/old"].get_attribute("data-verdict") == "missing"
    assert chips["src/net"].get_attribute("data-verdict") is None and chips["src/net"].get_attribute("data-planned") is None, "a part nothing planned nor changed is neither"
    assert "planned" in view.locator(".rb-scheme__key").inner_text() and "built" in view.locator(".rb-scheme__key").inner_text()
    ba = view.locator(".rb-ba")
    assert "aaaaaaa" in ba.locator(".rb-sys__hd").text_content() and "bbbbbbb" in ba.locator(".rb-sys__hd").text_content(), "the System at the commit before and at the last"
    rows = {r.get_attribute("data-part"): r for r in ba.locator(".rb-sys__row").all()}
    assert [rows[p].get_attribute("data-change") for p in ("src/lobby", "src/old", "src/score")] == ["new", "gone", "changed"]
    assert "not there" in rows["src/lobby"].locator('[data-side="before"]').inner_text() and "2 files" in rows["src/lobby"].locator('[data-side="after"]').inner_text()
    assert "3 files" in rows["src/score"].locator('[data-side="before"]').inner_text() and "5 files" in rows["src/score"].locator('[data-side="after"]').inner_text()
    assert "+ uses net" in rows["src/score"].inner_text() and "gone" in rows["src/old"].locator('[data-side="after"]').inner_text()
    assert texts(pg, ".rb-errors .rb-lines li") == ["Failed Keep the rounds: npm test: 2 failed", "Red test tests/test_score.py::test_round · Make the codes", "Finding src/score: leaks a timer"], "every error of its work, none of Design's"
    assert sizes(pg, ".gv .ork-card") == {(144, 202)}
    shot(pg, "g2-tech.png")
    view.locator(".gv-main").evaluate("e => { e.scrollTop = e.scrollHeight; }")
    shot(pg, "g2-tech-below.png")
    finish(pg, errors)


def test_tech_with_no_system_kept_from_before_the_goal_compares_nothing_and_says_so(gui):
    errors: list[str] = []
    partial = copy.deepcopy(RESULTS)
    partial["before_after"]["tech"] = {**partial["before_after"]["tech"], "before": None, "none": "the System was not kept from before this goal",
                                       "parts": [{"path": "src/score", "name": "score", "before": None, "after": {"count": 5, "uses": []}, "change": "new", "uses_new": [], "uses_gone": []}]}
    pg, host = open_result(gui, errors, partial)
    pg.locator('.table-tab[data-tab="tech"]').click()
    pick(pg, "codes")
    pg.locator(".rb-ba .rb-sys__row").wait_for(timeout=WAIT_MS)
    assert "The System was not kept from before this goal: nothing is compared." in pg.locator(".rb-ba").inner_text()
    assert "not there" in pg.locator(".rb-ba .rb-sys__row").inner_text()
    finish(pg, errors)


def test_through_design_a_goal_done_has_the_picture_of_each_screen_before_and_after_and_the_errors_of_its_work(gui):
    errors: list[str] = []
    pg, host = open_result(gui, errors)
    pick(pg, "codes")
    pg.locator('.sb--result').wait_for(timeout=WAIT_MS)
    pg.locator('.table-tab[data-tab="design"]').click()
    view = pg.locator('.gv[data-view="changed"][data-party="design"]')
    view.wait_for(timeout=WAIT_MS)
    pg.wait_for_selector(".rb-shots__row", timeout=WAIT_MS)
    row = lambda s: view.locator(f'.rb-shots__row[data-screen="{s}"]')  # noqa: E731
    assert row("results").locator(".rb-shot img").count() == 2 and [e.get_attribute("data-side") for e in row("results").locator(".rb-shot").all()] == ["before", "after"]
    assert row("podium").locator('.rb-shot.is-none[data-side="before"]').count() == 1 and row("podium").locator('.rb-shot[data-side="after"] img').count() == 1, "none kept before: none is made up"
    assert "no picture kept" in row("podium").locator(".is-none figcaption").inner_text()
    assert sizes(pg, ".rb-shot") == {(144, 202)} and sizes(pg, ".gv .ork-card") == {(144, 202)}
    assert texts(pg, ".rb-errors .rb-lines li") == ["Sent back Draw the winner: sent back 2 times"]
    chips = {c.get_attribute("data-id"): c.get_attribute("data-verdict") for c in view.locator(".rb-chip").all()}
    assert chips["results"] == "ok" and chips["podium"] == "missing"
    shot(pg, "g2-design.png")
    view.locator(".gv-main").evaluate("e => { e.scrollTop = e.scrollHeight; }")
    shot(pg, "g2-design-below.png")
    finish(pg, errors)
