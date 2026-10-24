"""Spec 74 part C, the desktop (docs/specs/74-moments-of-magic.md §6, §8; decisions §89), in a real browser at 1 440 × 900 against the route test's stub host (Passkey with its goals at work, Ideation with its
pitches, Release): a goal's moon is its tasks merged of its tasks in quarters (new, crescent, half, gibbous, full; 1 of 3 a crescent, 2 of 3 a gibbous), in its row of the left column 12 × 12 between its
title and its state's sign, and in its screen's head 28 × 28 (`.big`) before its state's words (*working 3/6*); a raw goal, a goal with no task, a pitch and a release have none; the moon is
`aria-hidden`, plays nothing and takes the frame's and the ink's colours; orkUI's `moons/` files are served (HTTP 200) beside orkUI's sheet."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import pip  # noqa: E402
from tests.test_route_desktop_browser import RouteHost, _goal  # noqa: E402
from tests.test_shell_browser import _open, _show_goal  # noqa: E402

pytestmark = pytest.mark.browser

PHASES = [(0, 4, "new"), (1, 4, "crescent"), (2, 4, "half"), (3, 4, "gibbous"), (4, 4, "full"), (1, 3, "crescent"), (2, 3, "gibbous"), (1, 8, "crescent"), (5, 8, "gibbous")]
MOONS = ("disk", "crescent", "half", "gibbous")
PROBE = "(v) => { const s = document.createElement('span'); s.style.color = `var(${v})`; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }"


class MoonHost(RouteHost):
    """The route test's world; a goal's screen has its node's tasks as its plan."""

    def page(self, slug):
        got = super().page(slug)
        tasks = next((n["tasks"] for n in self.nodes if n["slug"] == slug), [])
        if "error" not in got and tasks and got.get("plan") is None and not got.get("pitch"):
            got["plan"] = {"tasks": copy.deepcopy(tasks), "estimate": None}
        return got

    def merged(self, slug, merged, total):
        """The goal's tasks: `merged` of `total` merged, the rest waiting; the page is told."""
        self.node_of(slug)["tasks"] = [pip(f"m{i}", f"Task {i}", "merged" if i < merged else "waiting") for i in range(total)]
        self.bump({})


@pytest.fixture
def moons(gui):
    pg, host, errors = _open(gui, host=MoonHost(), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "passkey")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _row(pg, slug):
    return pg.locator(f'.arena-goal[data-slug="{slug}"]')


def _phase(row):
    """The phase class of a row's moon, or None when it has no moon."""
    moon = row.locator(".ork-moon")
    assert moon.count() <= 1
    return None if not moon.count() else [c for c in moon.get_attribute("class").split() if c not in ("ork-moon", "big")]


@pytest.mark.parametrize("merged,total,phase", PHASES)
def test_a_goals_moon_is_its_tasks_merged_of_its_tasks_rounded_to_quarters(moons, merged, total, phase):
    pg, host = moons
    host.merged("register", merged, total)
    pg.wait_for_function("(p) => document.querySelector('.arena-goal[data-slug=register] .ork-moon')?.classList.contains(p)", arg=phase, timeout=WAIT_MS)
    assert _phase(_row(pg, "register")) == [phase]


def test_the_moon_follows_a_merge_as_the_tasks_do_with_no_motion_of_its_own(moons):
    pg, host = moons
    host.merged("register", 1, 4)
    pg.wait_for_function("() => document.querySelector('.arena-goal[data-slug=register] .ork-moon.crescent')", timeout=WAIT_MS)
    host.merged("register", 2, 4)
    pg.wait_for_function("() => document.querySelector('.arena-goal[data-slug=register] .ork-moon.half')", timeout=WAIT_MS)
    anim = pg.locator('.arena-goal[data-slug="register"] .ork-moon').evaluate(
        "e => [getComputedStyle(e).animationName, getComputedStyle(e, '::after').animationName, getComputedStyle(e).transitionDuration, getComputedStyle(e, '::after').transitionDuration]")
    assert anim == ["none", "none", "0s", "0s"]


def test_a_raw_goal_and_one_with_no_task_have_none_and_a_plan_with_all_its_tasks_waiting_has_the_new_moon(moons):
    pg, host = moons
    assert _row(pg, "second").count() == 1 and _phase(_row(pg, "second")) is None                                       # asks: no task yet
    assert _phase(_row(pg, "recovery")) == ["new"]                                                                      # a plan: its tasks, none merged
    assert _phase(_row(pg, "signin")) == ["half"]                                                                       # 2 of 4
    pg.locator('.arena-pbody .arena-frow[data-fold="new"] .arena-frow__main').click()
    assert _row(pg, "magic").count() == 1 and _phase(_row(pg, "magic")) is None                                         # raw: none
    assert pg.locator(".arena-pbody .arena-goal .ork-moon").count() == len([s for s in ("register", "signin", "cookie", "recovery") if _row(pg, s).locator(".ork-moon").count()])


def test_a_release_at_work_a_pitch_and_the_rest_have_none(gui):
    class Lab(MoonHost):
        def __init__(self):
            super().__init__()
            r14 = self.node_of("r14")                                                                                   # a release goal with every task merged
            r14.update(state="working", stage="implementation", tasks=[pip("e1", "Notes", "merged"), pip("e2", "Build", "merged")])
            r14["flag"] = None
    pg, host, errors = _open(gui, host=Lab(), ready=".arena[data-goal=passkey]")
    _show_goal(pg, "release")
    assert _row(pg, "r14").count() == 1 and _phase(_row(pg, "r14")) is None
    _show_goal(pg, "ideas")
    pg.locator(".arena-sent .arena-frow__main").click()
    assert pg.locator(".arena-pitchrow").count() >= 1 and pg.locator(".arena-pitchrow .ork-moon").count() == 0
    got = pg.evaluate("async () => { const m = await import('/static/js/arena/goalwords.js'); return [m.moonOf({ state: 'working', tasks: [{ state: 'merged' }], release: { version: '1.4' } }), "
                      "m.moonOf({ state: 'working', tasks: [{ state: 'merged' }], type: { id: 'release' } }), m.moonOf({ state: 'sent', tasks: [{ state: 'merged' }], pitch: { state: 'sent' } }), "
                      "m.moonOf({ state: 'raw', tasks: [{ state: 'merged' }] }), m.moonOf({ state: 'working', tasks: [] }), m.moonOf({ state: 'working' }), "
                      "m.moonOf({ state: 'working', tasks: [{ state: 'merged' }, { state: 'dropped' }] }), m.moonOf({ state: 'done', tasks: [{ state: 'merged' }, { state: 'merged' }] })]; }")
    assert got == [None, None, None, None, None, None, "full", "full"]                                                 # a dropped task is not counted
    pg.close()
    assert not errors, "\n".join(errors)


def test_the_moon_is_12_px_after_the_title_before_the_state_sign_aria_hidden(moons):
    pg, host = moons
    row = _row(pg, "signin")
    title, moon, mark, main = [row.locator(s).bounding_box() for s in (".arena-goal__title", ".ork-moon", ".arena-goal__mark", ".arena-goal__main")]
    assert (round(moon["width"]), round(moon["height"])) == (12, 12) and moon["x"] >= title["x"] + title["width"] - 1 and moon["x"] + moon["width"] <= mark["x"] + 1       # between the two
    assert abs((moon["y"] + 6) - (main["y"] + main["height"] / 2)) <= 1                                                  # on the row's middle
    assert row.bounding_box()["height"] == 28 and row.locator(".ork-moon").get_attribute("aria-hidden") == "true" and row.locator(".ork-moon").inner_text() == ""
    assert row.locator(".ork-moon").evaluate("e => { const a = getComputedStyle(e, '::after'); return [a.width, a.height, a.position]; }") == ["12px", "12px", "absolute"]       # the lit part follows the box
    assert "moon" not in row.locator(".arena-goal__main").get_attribute("title")                                        # shown, never named
    assert row.locator(".arena-goal__main").evaluate("e => [...e.children].map((c) => c.className.split(' ')[0])")[-3:] == ["arena-goal__title", "ork-moon", "arena-goal__mark"]
    assert row.locator(".arena-goal__main").evaluate("e => e.scrollWidth <= e.clientWidth + 1")


def test_the_moon_takes_the_frame_and_the_ink_no_colour_of_its_own_and_its_files_are_served(moons):
    pg, host = moons
    host.merged("register", 4, 4)
    pg.wait_for_function("() => document.querySelector('.arena-goal[data-slug=register] .ork-moon.full')", timeout=WAIT_MS)
    dark, lit, full = (pg.evaluate(PROBE, v) for v in ("--ork-frame", "--ork-ink-muted", "--ork-ink"))
    half = _row(pg, "signin").locator(".ork-moon")
    got = half.evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e, '::after').backgroundColor, getComputedStyle(e).webkitMaskImage, getComputedStyle(e, '::after').webkitMaskImage]")
    assert got[0] == dark and got[1] == lit and "moons/disk.svg" in got[2] and "moons/half.svg" in got[3]
    got = _row(pg, "register").locator(".ork-moon").evaluate("e => [getComputedStyle(e, '::after').backgroundColor, getComputedStyle(e, '::after').webkitMaskImage]")
    assert got[0] == full and "moons/disk.svg" in got[1]                                                                 # the full moon's lit part is the ink
    for name in MOONS:                                                                                                   # served beside orkUI's sheet: `url(moons/…)` resolves there
        status = pg.evaluate("async (n) => { const r = await fetch(`/ds/orkui/moons/${n}.svg`); return [r.status, r.headers.get('content-type')]; }", name)
        assert status[0] == 200 and status[1].startswith("image/svg+xml"), name
    assert pg.evaluate("async () => (await fetch('/ds/orkui/components.css')).text()").count("url(moons/") >= 4


def test_a_goals_screen_has_its_moon_in_its_head_28_px_before_its_words(moons):
    pg, host = moons
    host.merged("register", 3, 4)
    _goal(pg, "register")
    bar = pg.locator(".board-ideaview .board-bar")
    moon, words = bar.locator(".ork-moon").bounding_box(), bar.locator(".board-state").bounding_box()
    assert (round(moon["width"]), round(moon["height"])) == (28, 28) and moon["x"] + moon["width"] <= words["x"] + 1
    cls = bar.locator(".ork-moon").get_attribute("class").split()
    assert "gibbous" in cls and "big" in cls and bar.locator(".ork-moon").get_attribute("aria-hidden") == "true"
    assert bar.locator(".board-state").inner_text().strip() == "working 3/4"                                             # its *k of n* words, the moon beside them
    assert bar.locator(".ork-moon").evaluate("e => getComputedStyle(e, '::after').width") == "28px"


def test_a_goal_with_no_task_has_no_moon_in_its_screen(moons):
    pg, host = moons
    _goal(pg, "second")
    assert pg.locator(".board-ideaview .board-bar .board-state").count() == 1 and pg.locator(".board-ideaview .board-bar .ork-moon").count() == 0
