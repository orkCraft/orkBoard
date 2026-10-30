"""Spec 111 part C (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, decisions §188, §187.4), in a real browser against a stub host, at the two widths of `tests/narrow.py`: Release and Live are no tabs and
have no lanes at the wide width, and wait in the portal ring's corners, asleep (their leader's head, grey and still) or awake (in colour, with their members, stepping while a task runs, an alert on the leader) on the signals the tabs
use; a press on a corner opens that party's view with no tab lit; the narrow width keeps them in the row of heads. A goal chosen for main has its checks asked (`ideas.to_main_checks`) and followed in the snapshot's `main_checks`
(scripted here as the host's `main.check` moves it): each check a skeleton in the gate in front of the portal (the portal `is-sealed is-guarded`, the line *Checking the way into main*), passed ones in Release's corner with a tick,
a red one staying with its words (*Sealed: Tests is red: 2 tests fail*), the portal open when all passed; a seal no check owns keeps its X; `ideas.to_main` is not asked while a skeleton stands; the ring plays the rite as the goal
goes in. A road party's cards lie in the hand's last lane, at its right end. Screenshots to $ROAD_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, need, node, sig, task  # noqa: E402
from tests.test_portal_browser import PortalHost, SEALED, card, portal, woken  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["ROAD_SHOTS"]) if os.environ.get("ROAD_SHOTS") else None
SK = "/ds/orkui/races/skeleton-"


class RoadPortalHost(PortalHost, RoadHost):
    """The portal's project (Lobby, Reconnect, Menu ready for main) with the road's parties and the scripted checks."""


def shot(pg, name, still=True):
    if SHOTS:
        if still:
            woken(pg)                                                                # the ring's first waking is over
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
    return pg, log


def open_view(gui, host, width="wide", reduced=False):
    """The window with the discard's view open (the pile pressed)."""
    pg, log = open_page(gui, host, width, reduced)
    pile = pg.locator(".table-end .hand-done")
    pile.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    pile.click()
    pg.locator(".portal-cards").wait_for(timeout=WAIT_MS)
    return pg, log


def release(pg):
    return pg.locator(".ork-portal-ring__before")


def live(pg):
    return pg.locator(".ork-portal-ring__after")


def gate(pg):
    return pg.locator(".ork-portal-ring__gate > .ork-portal-ring__guard")


def srcs(loc):
    """The heads' files, without their size and extension: `lich-elder`, `skeleton-warrior`."""
    return loc.locator(".ork-race__head").evaluate_all("els => els.map((e) => e.getAttribute('src').split('/').pop().replace(/(@2x)?\\.png$/, ''))")


def tabs(pg):
    return pg.locator(".table-tab[data-tab]").evaluate_all("els => els.map((e) => e.dataset.tab)")


def settle(pg, ms=300):
    pg.wait_for_timeout(ms)


# -- the tabs and the lanes ---------------------------------------------------------------------------------------------------------------------

def test_at_the_wide_width_release_and_live_are_no_tabs_and_have_no_lanes_and_at_the_narrow_width_they_are_kept(gui):
    pg, log = open_page(gui, RoadHost(bare=True))
    try:
        assert tabs(pg) == ["orkmaster", "tech", "design", "product"]
        assert pg.evaluate("() => document.querySelector('.frame').style.getPropertyValue('--lanes')") == "4", "the project's lane and three parties'"
        assert pg.locator(".hand-lane").count() == 4 and pg.locator(".table-lane[data-party]").count() == 3
        assert pg.locator('.table-lane[data-party="release"], .table-lane[data-party="live"]').count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, log = open_page(gui, RoadHost(bare=True), "narrow")
    try:
        assert tabs(pg) == ["orkmaster", "tech", "design", "product", "release", "live"], "the narrow width keeps them in the row of heads"
        assert pg.locator(".ork-portal-ring").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_asleep_each_corner_is_its_leaders_head_alone_grey_and_a_press_opens_the_party_with_no_tab_lit(gui):
    pg, log = open_page(gui, RoadHost(bare=True))
    try:
        pg.locator(".ork-portal-ring").wait_for(timeout=WAIT_MS)
        ring = pg.locator(".ork-portal-ring").bounding_box()
        for corner, words, race in ((release(pg), "Release: open its view", "lich-elder"), (live(pg), "Live: open its view", "imp-elder")):
            assert corner.evaluate("e => e.tagName") == "BUTTON" and corner.get_attribute("title") == words and corner.get_attribute("aria-label") == words
            assert "is-asleep" in corner.get_attribute("class") and "is-working" not in corner.get_attribute("class") and corner.get_attribute("data-awake") == "false"
            assert srcs(corner) == [race], "its leader's head alone"
            assert corner.locator(".ork-race__head").evaluate("e => getComputedStyle(e).filter") == "grayscale(1)"
        assert pg.locator(".ork-portal-ring").get_attribute("aria-hidden") is None, "a ring that holds buttons is not hidden"
        r, l = release(pg).bounding_box(), live(pg).bounding_box()
        assert r["x"] < ring["x"] + 20 and r["y"] > ring["y"] + ring["height"] - 60, "Release at the ring's lower left"
        assert l["x"] + l["width"] > ring["x"] + ring["width"] - 20 and l["y"] < ring["y"] + 20, "Live at its upper right"
        shot(pg, "asleep")
        release(pg).click()
        assert sig(pg, "frame/state.js", "tab") == "release"
        pg.wait_for_function("() => document.querySelector('.table-title__pt')?.textContent.toLowerCase().includes('through release')", timeout=WAIT_MS)    # the pane shows Release
        assert pg.locator('.table-tab[aria-selected="true"]').count() == 0, "no tab is lit"
        live(pg).click()
        assert sig(pg, "frame/state.js", "tab") == "live" and pg.locator('.table-tab[aria-selected="true"]').count() == 0
        pg.wait_for_function("() => document.querySelector('.table-title__pt')?.textContent.toLowerCase().includes('through live')", timeout=WAIT_MS)
        shot(pg, "live-view")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_corner_wakes_on_the_signals_the_tabs_use_and_steps_while_a_task_runs(gui):
    host = RoadHost()
    pg, log = open_page(gui, host)
    try:
        pg.locator(".ork-portal-ring__before").wait_for(timeout=WAIT_MS)
        assert "is-asleep" not in release(pg).get_attribute("class"), "goals are ready for main: Release is awake"
        assert srcs(release(pg)) == ["lich-elder", "lich-warrior", "lich-laborer"], "its leader and two of its members"
        assert "is-working" not in release(pg).get_attribute("class")
        assert "is-asleep" in live(pg).get_attribute("class") and len(srcs(live(pg))) == 1
        host.nodes.append(node("hotfix", "live", "Ship the hotfix", "table", state="working", stage="implementation", tasks=[task("h1", "Patch the server", "running")]))
        host.bump(None)
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring__after').classList.contains('is-asleep')", timeout=WAIT_MS)
        assert "is-working" in live(pg).get_attribute("class") and srcs(live(pg)) == ["imp-elder", "goblin-warrior", "peon-warrior"], "Live's leader and two members (the one at work among them)"
        assert live(pg).locator(".ork-portal-ring__alert").count() == 0
        assert live(pg).locator(".ork-race__head").first.evaluate("e => getComputedStyle(e).animationName") != "none", "the leader steps while a task runs"
        host.nodes = [n for n in host.nodes if n["slug"] != "hotfix"]
        next(p for p in host.parties if p["slug"] == "live")["concerns"] = {"alerts": 1}
        host.bump(None)
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__after .ork-portal-ring__alert').length === 1", timeout=WAIT_MS)
        assert "is-asleep" not in live(pg).get_attribute("class") and "is-working" not in live(pg).get_attribute("class"), "awake with an alert on its leader, not stepping"
        assert live(pg).locator(".ork-portal-ring__guard").first.locator(".ork-portal-ring__alert").count() == 1
        shot(pg, "live-awake")
        next(p for p in host.parties if p["slug"] == "live")["concerns"] = {"alerts": 0}
        host.needs.append(need("asks", "live", "ask", "Which region first?", "Where does it run?", asked=[{"ask": "Where does it run?", "choices": ["EU", "US"], "pick": None, "why": "", "by": None, "look": False}]))
        host.nodes.append(node("ask", "live", "Which region first?", "hand", state="asks", asks_you=True))
        host.bump(None)
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring__after').classList.contains('is-asleep')", timeout=WAIT_MS)      # it asks: a card of its lies in the hand
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_release_wakes_for_a_task_that_runs_and_sleeps_with_nothing_to_do(gui):
    host = RoadHost(bare=True)
    pg, log = open_page(gui, host)
    try:
        pg.locator(".ork-portal-ring__before").wait_for(timeout=WAIT_MS)
        assert "is-asleep" in release(pg).get_attribute("class")
        host.nodes.append(node("cut", "release", "Cut the release", "table", state="working", stage="implementation", tasks=[task("r1", "Tag it", "running")]))
        host.bump(None)
        pg.wait_for_function("() => document.querySelector('.ork-portal-ring__before').classList.contains('is-working')", timeout=WAIT_MS)
        assert "is-asleep" not in release(pg).get_attribute("class")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the hand ------------------------------------------------------------------------------------------------------------------------------------

def test_a_road_partys_cards_lie_in_the_last_lane_at_its_right_end_before_the_potions(gui):
    host = RoadHost()
    host.needs.append(need("asks", "release", "gate", "Hold the release?", "Hold it for the weekend?", at="2026-10-20T10:30:00",
                           asked=[{"ask": "Hold it for the weekend?", "choices": ["Yes", "No"], "pick": None, "why": "", "by": None, "look": False}]))
    host.nodes.append(node("gate", "release", "Hold the release?", "hand", state="asks", asks_you=True, asked=host.needs[-1]["asked"]))
    pg, log = open_page(gui, host)
    try:
        pg.locator('.hand-stack[data-goal="gate"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.hand-lane[data-lane="3"] .hand-stack[data-goal="gate"]').count() == 1, "in the last lane, where the lanes end (Release has none of its own)"
        assert pg.locator('.hand-lane[data-lane="3"] .hand-stack[data-goal="theme"]').count() == 1
        road, own = pg.locator('.hand-stack[data-goal="gate"]').bounding_box(), pg.locator('.hand-stack[data-goal="theme"]').bounding_box()
        assert road["x"] > own["x"], "at the lane's right end, in front"
        potions = pg.locator(".hand .ork-potion").first.bounding_box() if pg.locator(".hand .ork-potion").count() else None
        assert potions is None or road["x"] + road["width"] <= potions["x"] + 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the gate ------------------------------------------------------------------------------------------------------------------------------------

def choose(pg, slug):
    card(pg, slug).click()
    portal(pg).wait_for(timeout=WAIT_MS)


def test_the_skeletons_stand_in_the_gate_while_their_checks_run_and_step_aside_with_a_tick_as_each_passes(gui):
    host = RoadPortalHost()
    host.step("music", "passed", "running", "waiting")
    pg, log = open_view(gui, host)
    try:
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard').length === 2", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main_checks", 1) == [{"idea": "music"}]
        door = portal(pg)
        assert "is-sealed" in door.get_attribute("class") and "is-guarded" in door.get_attribute("class") and "is-sealed" in pg.locator(".ork-portal-ring").get_attribute("class")
        assert pg.locator(".portal__line").text_content() == "Checking the way into main" and pg.locator(".portal__sealed").text_content() == ""
        assert srcs(gate(pg)) == ["skeleton-warrior", "skeleton-elder"], "the merge has passed: Tests and Looks stand"
        assert [g.get_attribute("aria-label") for g in gate(pg).all()] == ["Tests: checking", "Looks: checking"]
        assert "is-working" in gate(pg).nth(0).get_attribute("class") and "is-working" not in gate(pg).nth(1).get_attribute("class"), "the one running steps"
        assert gate(pg).first.locator(".ork-race__head").evaluate("e => e.className.includes('big') && (e.width === 48 || e.getBoundingClientRect().width === 48)")
        assert srcs(release(pg)) == ["lich-elder", "skeleton-laborer"] and release(pg).locator(".ork-portal-ring__tick").count() == 1, "the passed skeleton beside the lich, with a tick"
        assert "is-asleep" not in release(pg).get_attribute("class") and "is-working" in release(pg).get_attribute("class"), "Release is awake and working while its checks run"
        gate_box, ring = pg.locator(".ork-portal-ring__gate").bounding_box(), pg.locator(".ork-portal-ring").bounding_box()
        assert ring["y"] + 90 < gate_box["y"] < ring["y"] + 125, "in front of the portal's lower part"
        shot(pg, "checking")
        pg.locator(".ork-portal-ring__gate").click()                                  # the gate lies over the portal: a press on it is a press on the portal
        settle(pg)
        assert [a for n, a in host.log if n == "ideas.to_main"] == [], "nothing goes to main while a skeleton stands"
        host.step("music", "passed", "passed", "running")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard').length === 1", timeout=WAIT_MS)
        assert [g.get_attribute("aria-label") for g in gate(pg).all()] == ["Looks: checking"] and len(srcs(release(pg))) == 3
        host.step("music", "passed", "passed", "passed")
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring__gate')", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'open'", timeout=WAIT_MS)
        assert "is-sealed" not in portal(pg).get_attribute("class") and "is-guarded" not in portal(pg).get_attribute("class") and "is-open" in pg.locator(".ork-portal-ring").get_attribute("class")
        assert pg.locator(".portal__line").text_content() == "Into main: Lobby, and Reconnect it stands on"
        assert srcs(release(pg)) == ["lich-elder", "skeleton-laborer", "skeleton-warrior", "skeleton-elder"] and release(pg).locator(".ork-portal-ring__tick").count() == 3
        shot(pg, "passed")
        portal(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"})), "all passed: the goal goes"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_red_check_stays_in_front_with_its_words_and_blocks_the_portal(gui):
    host = RoadPortalHost()
    host.step("codes", "passed", "failed", words={1: "2 tests fail"})
    pg, log = open_view(gui, host)
    try:
        choose(pg, "codes")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard.is-red').length === 1", timeout=WAIT_MS)
        assert gate(pg).count() == 1 and gate(pg).first.get_attribute("aria-label") == "Tests: 2 tests fail" and gate(pg).first.locator(".ork-portal-ring__alert").count() == 1
        assert pg.locator(".portal__line").text_content() == "Sealed: Tests is red: 2 tests fail" and pg.locator(".portal__sealed").text_content() == "", "the line over the portal says it"
        assert pg.locator(".portal__line").evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-danger)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }")
        assert pg.locator(".portal__line").count() == 1, "the sealed words stand in place of the line"
        assert "is-guarded" in portal(pg).get_attribute("class") and portal(pg).get_attribute("aria-label") == "Sealed: Tests is red: 2 tests fail"
        assert srcs(release(pg)) == ["lich-elder", "skeleton-laborer"] and release(pg).locator(".ork-portal-ring__tick").count() == 1, "the one that passed is in the corner"
        assert "is-working" not in gate(pg).first.get_attribute("class") and pg.locator(".portal-host").get_attribute("data-portal") == "sealed"
        shot(pg, "red")
        pg.locator(".ork-portal-ring__gate").click()
        settle(pg)
        assert [a for n, a in host.log if n == "ideas.to_main"] == []
        host.step("codes", "passed", "passed")                                     # fixed
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring__gate') && document.querySelector('.portal-host').dataset.portal === 'open'", timeout=WAIT_MS)
        assert pg.locator(".portal__line").text_content() == "Into main: Reconnect"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_dropped_on_the_portal_while_its_checks_run_is_not_lost_in_silence_and_goes_nowhere(gui):
    host = RoadPortalHost()
    host.step("codes", "passed", "running")
    pg, log = open_view(gui, host)
    try:
        woken(pg)
        src = card(pg, "codes").bounding_box()
        pg.mouse.move(src["x"] + 40, src["y"] + 60)
        pg.mouse.down()
        pg.mouse.move(src["x"] + 60, src["y"] + 70, steps=4)
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard').length === 1", timeout=WAIT_MS)
        door = pg.locator(".ork-portal-ring__gate").bounding_box()
        pg.mouse.move(door["x"] + door["width"] / 2, door["y"] + door["height"] / 2, steps=12)                           # over the skeleton standing in front of the portal
        pg.wait_for_function("() => document.querySelector('.ork-portal')?.classList.contains('is-taking')", timeout=WAIT_MS)
        pg.mouse.up()
        pg.locator(".gui-toasts").get_by_text("Checking the way into main").wait_for(timeout=WAIT_MS)                  # said in a toast, not dropped in silence
        assert [a for n, a in host.log if n == "ideas.to_main"] == [], "nothing goes to main while a skeleton stands"
        assert "is-taking" not in portal(pg).get_attribute("class")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_fourth_check_is_folded_into_the_third_skeletons_words(gui):
    host = RoadPortalHost()
    host.step("codes", "passed", "passed", "passed", "running")
    pg, log = open_view(gui, host)
    try:
        choose(pg, "codes")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard').length === 1", timeout=WAIT_MS)
        assert gate(pg).first.get_attribute("aria-label") == "Looks and 1 more: checking" and srcs(gate(pg))[0] == "skeleton-elder"
        assert len(srcs(release(pg))) == 3 and release(pg).locator(".ork-portal-ring__tick").count() == 2, "the first two have passed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_seal_no_check_owns_keeps_its_x_and_asks_for_no_checks_and_a_conflict_is_the_merges(gui):
    host = RoadPortalHost()
    host.plans["menu"]["conflict"] = False
    pg, log = open_view(gui, host)
    try:
        choose(pg, "menu")
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'sealed'", timeout=WAIT_MS)
        assert "is-sealed" in portal(pg).get_attribute("class") and "is-guarded" not in portal(pg).get_attribute("class"), "the sealed portal with its X"
        assert pg.locator(".ork-portal-ring__gate").count() == 0 and pg.locator(".portal__sealed").text_content() == f"Sealed: {SEALED}"
        assert [n for n, _ in host.log if n == "ideas.to_main_checks"] == [], "no check owns this seal"
        host.plans["menu"]["conflict"] = True                                      # the host's trial pick did not apply: the merge's reason
        host.step("menu", "failed", "waiting", words={0: SEALED})
        card(pg, "music").click()
        settle(pg)
        card(pg, "menu").click()
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard.is-red').length === 1", timeout=WAIT_MS)
        assert "is-guarded" in portal(pg).get_attribute("class") and pg.locator(".portal__line").text_content() == f"Sealed: The merge is red: {SEALED}"
        assert gate(pg).count() == 2 and gate(pg).nth(1).get_attribute("aria-label") == "Tests: checking" and srcs(release(pg)) == ["lich-elder"], "the merge is red: no skeleton has passed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_red_goal_chosen_again_asks_the_host_to_check_it_again(gui):
    host = RoadPortalHost()
    host.script["codes"] = (("passed", "failed"), {1: "2 tests fail"})
    pg, log = open_view(gui, host)
    try:
        choose(pg, "codes")
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'sealed'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main_checks", 1) == [{"idea": "codes"}]
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.portal__line') && !document.querySelector('.ork-portal-ring__gate')", timeout=WAIT_MS)
        host.script["codes"] = (("passed", "passed"), {})                          # fixed since
        choose(pg, "codes")
        assert _calls(pg, host, "ideas.to_main_checks", 2) == [{"idea": "codes"}, {"idea": "codes", "again": True}]
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'open'", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_the_narrow_width_no_check_is_asked_and_the_portal_is_as_it_was(gui):
    host = RoadPortalHost()
    pg, log = open_view(gui, host, "narrow")
    try:
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('.portal-host')?.dataset.portal === 'open'", timeout=WAIT_MS)
        assert pg.locator(".ork-portal-ring").count() == 0 and [n for n, _ in host.log if n == "ideas.to_main_checks"] == []
        portal(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the rite ------------------------------------------------------------------------------------------------------------------------------------

def test_the_ring_plays_the_rite_in_the_goals_colour_as_it_goes_in_once_and_never_under_reduced_motion(gui):
    host = RoadPortalHost()
    host.step("music", "passed", "passed")
    pg, log = open_view(gui, host)
    try:
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'open'", timeout=WAIT_MS)
        assert "is-sending" not in pg.locator(".ork-portal-ring").get_attribute("class")
        portal(pg).click()
        pg.wait_for_function("() => document.querySelector('.ork-portal-ring').classList.contains('is-sending')", timeout=WAIT_MS)
        cls = pg.locator(".ork-portal-ring").get_attribute("class")
        assert "rite-void" in cls and "is-open" in cls, "Lobby's rune is void"
        shot(pg, "rite", still=False)
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring').classList.contains('is-sending')", timeout=4000)
        assert "rite-" not in pg.locator(".ork-portal-ring").get_attribute("class")
    finally:
        pg.close()
    assert not log, "\n".join(log)
    host = RoadPortalHost()
    host.step("music", "passed", "passed")
    pg, log = open_view(gui, host, reduced=True)
    try:
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('.portal-host').dataset.portal === 'open'", timeout=WAIT_MS)
        portal(pg).click()
        assert _sent(pg, host, ("ideas.to_main", {"idea": "music"}))
        seen = pg.evaluate("() => new Promise((done) => { let on = false; const end = Date.now() + 1500; const tick = () => { if (document.querySelector('.ork-portal-ring')?.classList.contains('is-sending')) on = true; if (Date.now() > end) done(on); else requestAnimationFrame(tick); }; tick(); })")
        assert seen is False, "nothing plays under reduced motion"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the room ------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", ["wide", "small"])
def test_the_road_fits_over_the_hand_at_1280_and_1024_wide_in_every_state(gui, width):
    host = RoadPortalHost()
    host.step("codes", "passed", "failed", words={1: "2 tests fail"})
    pg, log = open_view(gui, host, width)
    try:
        def clear(state):
            hand = pg.locator(".hand").bounding_box()
            for sel in (".ork-portal-ring", ".ork-portal-ring__before .ork-race__head", ".ork-portal-ring__after .ork-race__head", ".ork-portal-ring__gate", ".portal__sealed", ".portal__line"):    # the corners' own boxes reach 6 px past the ring
                for el in pg.locator(sel).all():
                    box = el.bounding_box()
                    if box and box["height"]:
                        assert box["y"] + box["height"] <= hand["y"] + 1, f"{state}: {sel} overlaps the hand"
                        assert box["x"] >= 0 and box["x"] + box["width"] <= pg.viewport_size["width"] + 1, f"{state}: {sel} leaves the window"
            narrow.no_sideways(pg)
            corners = [b for b in (el.bounding_box() for el in pg.locator(".ork-portal-ring__before, .ork-portal-ring__after").all()) if b]
            for sel in (".portal__hint", ".portal__sealed", ".portal__line", ".portal__label", ".table-end__label"):
                for el in pg.locator(sel).all():
                    box = el.bounding_box()
                    if box and box["height"] and el.inner_text().strip():
                        for c in corners:
                            apart = box["x"] + box["width"] <= c["x"] or c["x"] + c["width"] <= box["x"] or box["y"] + box["height"] <= c["y"] or c["y"] + c["height"] <= box["y"]
                            assert apart, f"{state}: {sel} overlaps a corner of the ring"
        clear("asleep or open")
        shot(pg, f"{width}-rest")
        choose(pg, "codes")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard.is-red').length === 1", timeout=WAIT_MS)
        clear("red")
        shot(pg, f"{width}-red")
        host.step("codes", "passed", "running", "waiting")
        pg.wait_for_function("() => document.querySelectorAll('.ork-portal-ring__gate > .ork-portal-ring__guard').length === 2", timeout=WAIT_MS)
        clear("checking")
        shot(pg, f"{width}-checking")
        host.step("codes", "passed", "passed", "passed")
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring__gate')", timeout=WAIT_MS)
        clear("passed")
        shot(pg, f"{width}-passed")
    finally:
        pg.close()
    assert not log, "\n".join(log)
