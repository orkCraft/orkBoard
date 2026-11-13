"""(Release and Live wait, decisions §283.29: Release, seated, keeps its page and has no tab, no lane and no table of checks; Live is the road's one tab. Its tests below say so.)
The road after the work (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, decisions §188; docs/specs/156-one-pick-and-the-release-column.md D.2, D.4, decisions §261.7–§261.8), in a real browser against a stub host, at the two widths
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
from tests.test_hand_desktop_browser import RoadHost, node, task  # noqa: E402
from tests.test_portal_browser import PortalHost, woken  # noqa: E402
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






def test_release_has_no_tab_whatever_its_tasks_do(gui):
    host = RoadHost(bare=True)
    pg, log = open_page(gui, host)
    try:
        assert tab(pg, "release").count() == 0
        host.nodes.append(node("cut", "release", "Cut the release", "table", state="working", stage="implementation", tasks=[task("r1", "Tag it", "running")]))
        host.bump(None)
        pg.wait_for_timeout(500)
        assert tab(pg, "release").count() == 0, "a task that runs wakes no tab: Release has none"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the hand ------------------------------------------------------------------------------------------------------------------------------------


# -- no gate, no ring (spec 113 §4, decisions §191.2) ---------------------------------------------------------------------------------------------------

GATE = {"into": "dev", "main": "main", "same": False, "commits": 0, "files": 0, "ideas": []}






# -- the checks, on Release's table ----------------------------------------------------------------------------------------------------------------

def test_to_main_runs_its_checks_without_release_s_skeletons_and_waits_for_the_last(gui):
    host = RoadPortalHost()
    host.step("music", "passed", "running", "waiting")
    pg, log = open_page(gui, host)
    try:
        card(pg, "music").wait_for(timeout=WAIT_MS)
        choose(pg, "music")
        pg.wait_for_function("() => document.querySelector('[data-tomain]')?.dataset.portal === 'check'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main_checks", 1) == [{"idea": "music"}]
        assert pg.locator(".table-checks").count() == 0 and tab(pg, "release").count() == 0, "Release's table of checks is off (decisions §283.29): the gate's checks run all the same"
        assert pg.locator("[data-tomain]").get_attribute("data-portal") == "check" and pg.locator(".table-tomain__line").text_content() == "Checking the way into main"
        shot(pg, "checking")
        to_main(pg).click(force=True)                                                        # a press while a check runs waits for it: nothing goes to main yet
        settle(pg, 500)
        assert [a for n, a in host.log if n == "ideas.to_main"] == []
        host.step("music", "passed", "passed", "passed")
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"})), "all passed: the goal goes"
    finally:
        pg.close()
    assert not log, "\n".join(log)




# -- the rite ------------------------------------------------------------------------------------------------------------------------------------

