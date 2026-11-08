"""The road after the work (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, decisions §188; docs/specs/156-one-pick-and-the-release-column.md D.2, D.4, decisions §261.7–§261.8), in a real browser against a stub host, at the two widths
of `tests/narrow.py`: Release and Live are tabs at the wide width too, **Live before Release, Release last**, Live's lane after the tabs' end and Release's lane the discard; their leaders' heads wear the corners' old waking rules on the tabs' faces (asleep:
grey and still; awake: in colour, stepping while a task runs, an alert sign on it); the narrow width keeps them in the row of heads in the Board's order. A goal chosen for main (the ready card picked in the lane) has its checks asked (`ideas.to_main_checks`)
and followed in the snapshot's `main_checks` (scripted here as the host's `main.check` moves it): Release's table shows each check, a skeleton with its name and its state and, for a red one, why; *To main* waits while they run and says the reason while one
is red; `ideas.to_main` is not asked while a check stands; the ring plays the rite as the goal goes in. A road party's cards lie in the hand's last lane, at its right end. With no gate (spec 113 §4: dev and main one branch) there is no ring and no
goal ready for main: the lane holds the goals done. Screenshots to $ROAD_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, need, node, sig, task  # noqa: E402
from tests.test_portal_browser import PortalHost, SEALED, woken  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["ROAD_SHOTS"]) if os.environ.get("ROAD_SHOTS") else None


class RoadPortalHost(PortalHost, RoadHost):
    """The portal's project (Lobby, Reconnect, Menu ready for main) with the road's parties and the scripted checks."""


def shot(pg, name, still=True):
    if SHOTS:
        if still:
            woken(pg)
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


SMALL = {"viewport": {"width": 1024, "height": 768}}


def open_page(gui, host, width="wide", reduced=False):
    server, browser = gui
    ctx = browser.new_context(**({"wide": narrow.WIDE, "narrow": narrow.FINE, "small": SMALL}[width]), **({"reduced_motion": "reduce"} if reduced else {}))
    pg = ctx.new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    return pg, log


def tab(pg, slug):
    return pg.locator(f'.table-tab[data-tab="{slug}"]')


def asleep(pg, slug):
    return "is-asleep" in tab(pg, slug).get_attribute("class")


def tabs(pg):
    return pg.locator(".col-head__tab[data-tab], .table-tab[data-tab]").evaluate_all("els => els.map((e) => e.dataset.tab)")


def card(pg, slug):
    return pg.locator(f'.release-lane [data-portal-card="{slug}"]')


def choose(pg, slug):
    """Picks the ready card: the goal is chosen for main (its plan, its checks)."""
    card(pg, slug).click()
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)


def settle(pg, ms=300):
    pg.wait_for_timeout(ms)


def to_main(pg):
    return pg.locator("[data-tomain] [data-to-main]")


def states(pg):
    return pg.locator(".table-checks .table-check__state").all_inner_texts()


# -- the tabs and the lanes ---------------------------------------------------------------------------------------------------------------------

def test_at_the_wide_width_release_stands_in_the_leaders_row_and_live_is_the_last_tab_and_at_the_narrow_width_they_are_kept_in_the_boards_order(gui):
    pg, log = open_page(gui, RoadHost(bare=True))
    try:
        assert tabs(pg) == ["orkmaster", "tech", "design", "product", "release", "live"], "Release in the leaders' row in the Board's order, Live last"
        assert pg.evaluate("() => document.querySelector('.frame').style.getPropertyValue('--lanes')") == "4", "four lanes before the tabs' end, Release's among them; Live's lane follows it and the discard is the window's column beside the table"
        assert pg.locator(".hand-lane").count() == 6 and pg.locator(".table-lane[data-party]").count() == 5
        assert pg.locator('.table-lane[data-party="release"]').count() == 1 and pg.locator('.table-lane[data-party="live"]').count() == 1, "Release has a lane as any party, Live has one after the end"
        assert pg.locator(".frame > .release-lane").count() == 1 and pg.locator(".frame-table .release-lane").count() == 0, "the discard is beside the table, outside it"
        assert pg.locator(".ork-portal-ring__before, .ork-portal-ring__after, .ork-portal-ring").count() == 0, "their heads have left the ring"
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, log = open_page(gui, RoadHost(bare=True), "narrow")
    try:
        assert tabs(pg) == ["orkmaster", "tech", "design", "product", "release", "live"], "the narrow width keeps them in the row of heads"
        assert pg.locator(".ork-portal-ring, .release-lane").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_asleep_each_road_tab_is_its_leaders_head_grey_and_still_and_a_press_opens_the_party(gui):
    pg, log = open_page(gui, RoadHost(bare=True))
    try:
        for slug, race in (("release", "lich-elder"), ("live", "imp-elder")):
            assert asleep(pg, slug) and "is-working" not in tab(pg, slug).get_attribute("class")
            src = tab(pg, slug).locator(".ork-race__head").get_attribute("src")
            assert race in src and "asleep" in src, f"{slug}: its leader's head, the asleep face"
        shot(pg, "asleep")
        tab(pg, "live").click()
        pg.locator('.table-tab[data-tab="live"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "tab") == "live"
        tab(pg, "release").click()
        pg.locator('.table-tab[data-tab="release"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".release-lane__label").text_content() == "Release's discard"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_road_tab_wakes_on_the_signals_the_corners_used_and_steps_while_a_task_runs(gui):
    host = RoadHost()
    pg, log = open_page(gui, host)
    try:
        assert not asleep(pg, "release"), "goals are ready for main: Release is awake"
        assert asleep(pg, "live")
        host.nodes.append(node("hotfix", "live", "Ship the hotfix", "table", state="working", stage="implementation", tasks=[task("h1", "Patch the server", "running")]))
        host.bump(None)
        pg.wait_for_function("() => !document.querySelector('.table-tab[data-tab=\"live\"]').classList.contains('is-asleep')", timeout=WAIT_MS)
        assert tab(pg, "live").get_attribute("data-working") is not None, "Live's leader is at work"
        host.nodes = [n for n in host.nodes if n["slug"] != "hotfix"]
        next(p for p in host.parties if p["slug"] == "live")["concerns"] = {"alerts": 1}
        host.bump(None)
        pg.wait_for_function("() => document.querySelectorAll('.table-tab[data-tab=\"live\"] .table-tab__alert').length === 1", timeout=WAIT_MS)
        assert not asleep(pg, "live") and tab(pg, "live").get_attribute("data-working") is None, "awake with an alert on its leader, not at work"
        shot(pg, "live-awake")
        next(p for p in host.parties if p["slug"] == "live")["concerns"] = {"alerts": 0}
        host.needs.append(need("asks", "live", "ask", "Which region first?", "Where does it run?", asked=[{"ask": "Where does it run?", "choices": ["EU", "US"], "pick": None, "why": "", "by": None, "look": False}]))
        host.nodes.append(node("ask", "live", "Which region first?", "hand", state="asks", asks_you=True))
        host.bump(None)
        pg.wait_for_function("() => !document.querySelector('.table-tab[data-tab=\"live\"]').classList.contains('is-asleep')", timeout=WAIT_MS)      # it asks: a card of its lies in the hand
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_release_wakes_for_a_task_that_runs_and_sleeps_with_nothing_to_do(gui):
    host = RoadHost(bare=True)
    pg, log = open_page(gui, host)
    try:
        assert asleep(pg, "release")
        host.nodes.append(node("cut", "release", "Cut the release", "table", state="working", stage="implementation", tasks=[task("r1", "Tag it", "running")]))
        host.bump(None)
        pg.wait_for_function("() => document.querySelector('.table-tab[data-tab=\"release\"]').dataset.working !== undefined", timeout=WAIT_MS)
        assert not asleep(pg, "release")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the hand ------------------------------------------------------------------------------------------------------------------------------------

def test_a_road_partys_cards_lie_in_its_lane_under_its_tab_before_the_potions(gui):
    host = RoadHost()
    host.needs.append(need("asks", "release", "gate", "Hold the release?", "Hold it for the weekend?", at="2026-10-20T10:30:00",
                           asked=[{"ask": "Hold it for the weekend?", "choices": ["Yes", "No"], "pick": None, "why": "", "by": None, "look": False}]))
    host.nodes.append(node("gate", "release", "Hold the release?", "hand", state="asks", asks_you=True, asked=host.needs[-1]["asked"]))
    pg, log = open_page(gui, host)
    try:
        pg.locator('.hand-stack[data-goal="gate"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.hand-lane[data-lane="4"] .hand-stack[data-goal="gate"]').count() == 1, "in Release's lane, as any party's (the discard is the column beside the table)"
        assert pg.locator('.hand-lane[data-lane="3"] .hand-stack[data-goal="theme"]').count() == 1
        road = pg.locator('.hand-stack[data-goal="gate"]').bounding_box()
        release = tab(pg, "release").bounding_box()
        assert road["x"] >= release["x"] - 60 and road["x"] + road["width"] <= pg.viewport_size["width"], "under Release's tab, in the leaders' lanes"
        assert pg.locator(".hand-end .hand-die").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- no gate, no ring (spec 113 §4, decisions §191.2) ---------------------------------------------------------------------------------------------------

NO_GATE = {"into": "dev", "main": "dev", "same": True, "commits": 0, "files": 0, "ideas": []}      # results merge into dev itself: the gate's own answer (`idea_gate.same`)
GATE = {"into": "dev", "main": "main", "same": False, "commits": 0, "files": 0, "ideas": []}


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_with_no_gate_there_is_no_ring_release_and_live_are_tabs_and_nothing_is_ready_for_main(gui, width):
    host = RoadHost(bare=True)
    host.gate_doc = dict(NO_GATE)
    pg, log = open_page(gui, host, width)
    try:
        pg.wait_for_timeout(400)
        assert tabs(pg) == ["orkmaster", "tech", "design", "product", "release", "live"]
        assert pg.locator(".ork-portal-ring, .portal-host, .ork-portal, [data-portal-card]").count() == 0
        assert pg.evaluate("() => document.querySelector('.frame').style.getPropertyValue('--lanes')") == ("4" if width == "wide" else "6")
        assert pg.locator(".hand-lane").count() == 6
        assert pg.locator(".table-end").count() == 0 and pg.locator(".release-lane .hand-done, .release-lane [data-portal-card]").count() == 0, "nothing done, nothing ready"
        shot(pg, f"c113-no-gate-{width}", still=False)
        tab(pg, "release").click()
        pg.locator('.table-tab[data-tab="release"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_no_gate_a_goal_done_lies_in_the_lane_with_no_ring_and_no_ready_for_main(gui):
    host = RoadHost()
    host.gate_doc = dict(NO_GATE)
    pg, log = open_page(gui, host)
    try:
        pile = pg.locator(".release-lane .hand-done")
        pile.first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".ork-portal-ring, .portal-host, [data-portal-card], [data-tomain]").count() == 0 and pg.locator(".release-lane__label").text_content() == "Discard"
        assert pile.count() == 2, "both goals done lie in the lane, whole"
        assert pg.locator(".release-lane").get_by_text("ready for main").count() == 0, "no *ready for main* in the lane"
        shot(pg, "c113-no-gate-lane", still=False)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_ring_comes_and_goes_with_the_gate_and_the_tabs_stay_where_they_are(gui):
    host = RoadHost(bare=True)
    host.gate_doc = dict(NO_GATE)
    pg, log = open_page(gui, host)
    try:
        assert pg.locator(".ork-portal-ring").count() == 0 and tabs(pg)[-2:] == ["release", "live"]
        host.nodes.append(node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00"))
        host.gate_doc = {**GATE, "commits": 2, "files": 1, "ideas": [{"slug": "music", "title": "Lobby music loop", "goal": "tech", "tasks": 1}]}      # a main branch appears, and a goal is ready for it
        host.bump({})
        pg.locator(".release-lane .ork-portal-ring").wait_for(timeout=WAIT_MS)
        assert tabs(pg)[-2:] == ["release", "live"] and card(pg, "music").count() == 1
        host.gate_doc = dict(NO_GATE)
        host.bump({})
        pg.locator(".release-lane .ork-portal-ring").wait_for(state="detached", timeout=WAIT_MS)
        assert tabs(pg)[-2:] == ["release", "live"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the checks, on Release's table ----------------------------------------------------------------------------------------------------------------

def test_release_shows_the_checks_a_skeleton_each_while_they_run_and_to_main_waits_for_the_last(gui):
    host = RoadPortalHost()
    host.step("music", "passed", "running", "waiting")
    pg, log = open_page(gui, host)
    try:
        card(pg, "music").wait_for(timeout=WAIT_MS)
        choose(pg, "music")
        tab(pg, "release").click()
        pg.locator(".table-checks .table-check").nth(2).wait_for(timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main_checks", 1) == [{"idea": "music"}]
        assert pg.locator(".table-checks .table-check__name").all_inner_texts() == ["The merge", "Tests", "Looks"] and states(pg) == ["passed", "checking", "waiting"]
        srcs = pg.locator(".table-checks .ork-race__head").evaluate_all("els => els.map((e) => e.getAttribute('src'))")
        assert ["skeleton-laborer" in srcs[0], "skeleton-warrior" in srcs[1], "skeleton-elder" in srcs[2]] == [True, True, True], "Release's members, one a check"
        assert "is-working" in pg.locator(".table-checks .table-check__head").nth(1).get_attribute("class") and not asleep(pg, "release"), "the one running steps; Release is awake"
        assert pg.locator("[data-tomain]").get_attribute("data-portal") == "check" and pg.locator(".table-tomain__line").text_content() == "Checking the way into main"
        shot(pg, "checking")
        to_main(pg).click(force=True)                                                        # a press while a check runs waits for it: nothing goes to main yet
        settle(pg, 500)
        assert [a for n, a in host.log if n == "ideas.to_main"] == []
        host.step("music", "passed", "passed", "passed")
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"})), "all passed: the goal goes"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_red_check_says_why_in_words_blocks_to_main_and_clears_when_fixed(gui):
    host = RoadPortalHost()
    host.step("codes", "passed", "failed", words={1: "2 tests fail"})
    pg, log = open_page(gui, host)
    try:
        card(pg, "codes").wait_for(timeout=WAIT_MS)
        choose(pg, "codes")
        tab(pg, "release").click()
        pg.locator(".table-checks .table-check.is-red").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-check.is-red .table-check__why").text_content() == "2 tests fail" and states(pg) == ["passed", "red"]
        assert pg.locator(".table-tomain__sealed").text_content() == "Sealed: Tests is red: 2 tests fail" and pg.locator("[data-tomain]").get_attribute("data-portal") == "sealed"
        assert pg.locator(".table-tomain__sealed").evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-danger)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }")
        shot(pg, "red")
        to_main(pg).click()
        settle(pg)
        assert [a for n, a in host.log if n == "ideas.to_main"] == [], "a red check blocks the way"
        host.step("codes", "passed", "passed")                                       # fixed
        pg.wait_for_function("() => document.querySelector('[data-tomain]').dataset.portal === 'open'", timeout=WAIT_MS)
        assert pg.locator(".table-tomain__line").text_content() == "Into main: Reconnect"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_fourth_check_is_shown_too_a_skeleton_each(gui):
    host = RoadPortalHost()
    host.step("codes", "passed", "passed", "passed", "running")
    pg, log = open_page(gui, host)
    try:
        card(pg, "codes").wait_for(timeout=WAIT_MS)
        choose(pg, "codes")
        tab(pg, "release").click()
        pg.locator(".table-checks .table-check").nth(3).wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-checks .table-check__name").all_inner_texts() == ["The merge", "Tests", "Looks", "Regression"] and states(pg)[-1] == "checking"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_seal_no_check_owns_says_its_reason_and_asks_for_no_checks_and_a_conflict_is_the_merges(gui):
    host = RoadPortalHost()
    host.plans["menu"]["conflict"] = False
    pg, log = open_page(gui, host)
    try:
        card(pg, "menu").wait_for(timeout=WAIT_MS)
        choose(pg, "menu")
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'sealed'", timeout=WAIT_MS)
        assert pg.locator(".table-tomain__sealed").text_content() == f"Sealed: {SEALED}" and pg.locator(".table-checks").count() == 0
        assert [n for n, _ in host.log if n == "ideas.to_main_checks"] == [], "no check owns this seal"
        host.plans["menu"]["conflict"] = True                                        # the host's trial pick did not apply: the merge's reason
        host.step("menu", "failed", "waiting", words={0: SEALED})
        card(pg, "music").click()
        settle(pg)
        card(pg, "menu").click()
        tab(pg, "release").click()
        pg.wait_for_function("() => document.querySelectorAll('.table-checks .table-check.is-red').length === 1", timeout=WAIT_MS)
        assert pg.locator(".table-tomain__sealed").text_content() == f"Sealed: The merge is red: {SEALED}"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_red_goal_chosen_again_asks_the_host_to_check_it_again(gui):
    host = RoadPortalHost()
    host.script["codes"] = (("passed", "failed"), {1: "2 tests fail"})
    pg, log = open_page(gui, host)
    try:
        card(pg, "codes").wait_for(timeout=WAIT_MS)
        choose(pg, "codes")
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'sealed'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main_checks", 1) == [{"idea": "codes"}]
        pg.keyboard.press("Escape")                                                  # put away: the choice is dropped
        pg.wait_for_function("() => !document.querySelector('[data-tomain]')", timeout=WAIT_MS)
        host.script["codes"] = (("passed", "passed"), {})                            # fixed since
        choose(pg, "codes")
        assert _calls(pg, host, "ideas.to_main_checks", 2) == [{"idea": "codes"}, {"idea": "codes", "again": True}]
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'open'", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_the_narrow_width_no_check_is_asked_and_the_portal_is_as_it_was(gui):
    host = RoadPortalHost()
    pg, log = open_page(gui, host, "narrow")
    try:
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        pg.locator(".table-end .hand-done").click()
        pg.locator(".portal-cards").wait_for(timeout=WAIT_MS)
        pg.locator('[data-portal-card="music"]').click()
        pg.wait_for_function("() => document.querySelector('.portal-host')?.dataset.portal === 'open'", timeout=WAIT_MS)
        assert pg.locator(".ork-portal-ring").count() == 0 and [n for n, _ in host.log if n == "ideas.to_main_checks"] == []
        pg.locator(".portal-host .ork-portal").click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the rite ------------------------------------------------------------------------------------------------------------------------------------

def test_the_ring_plays_the_rite_in_the_goals_colour_as_it_goes_in_once_and_never_under_reduced_motion(gui):
    host = RoadPortalHost()
    host.step("music", "passed", "passed")
    pg, log = open_page(gui, host)
    try:
        card(pg, "music").wait_for(timeout=WAIT_MS)
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'open'", timeout=WAIT_MS)
        assert "is-sending" not in pg.locator(".release-lane .ork-portal-ring").get_attribute("class")
        to_main(pg).click()
        pg.wait_for_function("() => document.querySelector('.release-lane .ork-portal-ring')?.classList.contains('is-sending')", timeout=WAIT_MS)
        cls = pg.locator(".release-lane .ork-portal-ring").get_attribute("class")
        assert "rite-void" in cls and "is-open" in cls, "Lobby's rune is void"
        shot(pg, "rite", still=False)
        pg.wait_for_function("() => !document.querySelector('.release-lane .ork-portal-ring')?.classList.contains('is-sending')", timeout=4000)
    finally:
        pg.close()
    assert not log, "\n".join(log)
    host = RoadPortalHost()
    host.step("music", "passed", "passed")
    pg, log = open_page(gui, host, reduced=True)
    try:
        card(pg, "music").wait_for(timeout=WAIT_MS)
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'open'", timeout=WAIT_MS)
        to_main(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
        seen = pg.evaluate("() => new Promise((done) => { let on = false; const end = Date.now() + 1500; const tick = () => { if (document.querySelector('.ork-portal-ring')?.classList.contains('is-sending')) on = true; if (Date.now() < end) requestAnimationFrame(tick); else done(on); }; tick(); })")
        assert seen is False, "nothing plays under reduced motion"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", ["wide", "small"])
def test_the_lane_and_the_table_fit_over_the_hand_at_1280_and_1024_wide_in_every_state(gui, width):
    host = RoadPortalHost()
    host.step("codes", "passed", "failed", words={1: "2 tests fail"})
    pg, log = open_page(gui, host, width)
    try:
        card(pg, "codes").wait_for(timeout=WAIT_MS)

        def clear(state):
            lane = pg.locator(".release-lane").bounding_box()
            hand = pg.locator(".hand").bounding_box()
            assert lane["y"] + lane["height"] <= hand["y"] + 1 and lane["x"] + lane["width"] <= pg.viewport_size["width"] + 1, f"{state}: the lane is over the hand and inside the window"
            narrow.no_sideways(pg)
            assert pg.evaluate("() => { const e = document.querySelector('.release-lane__scroll'); return e.scrollWidth <= e.clientWidth; }"), f"{state}: nothing of the lane scrolls sideways"
        clear("at rest")
        shot(pg, f"{width}-rest")
        choose(pg, "codes")
        tab(pg, "release").click()
        pg.wait_for_function("() => document.querySelectorAll('.table-checks .table-check.is-red').length === 1", timeout=WAIT_MS)
        clear("red")
        shot(pg, f"{width}-red")
        host.step("codes", "passed", "running", "waiting")
        pg.wait_for_function("() => document.querySelectorAll('.table-checks .table-check').length === 3", timeout=WAIT_MS)
        clear("checking")
        host.step("codes", "passed", "passed", "passed")
        pg.wait_for_function("() => document.querySelector('[data-tomain]').dataset.portal === 'open'", timeout=WAIT_MS)
        clear("passed")
        shot(pg, f"{width}-passed")
    finally:
        pg.close()
    assert not log, "\n".join(log)
