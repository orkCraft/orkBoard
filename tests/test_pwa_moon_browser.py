"""Spec 74 part C, the phone (docs/specs/74-moments-of-magic.md §6, §8; decisions §89): Chromium at 390 × 844 against the scene of tests/test_pwa_arena_browser.py. A goal's moon is its tasks
merged of its tasks in quarters (new, crescent, half, gibbous, full; 1 of 3 a crescent, 2 of 3 a gibbous), in its row of the Goals sheet 14 × 14 between its title and its state's sign and in its
screen's head 28 × 28 (`.big`) beside its words; a raw goal, a goal with no task, a pitch and a release have none; the moon is `aria-hidden`, plays nothing and takes the frame's and the ink's colours;
orkUI's `moons/` files are served by the app (and kept by the service worker); `sw.js` v85."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import BACKEND, SCENE, _scene, node, task  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

PHASES = [(0, 4, "new"), (1, 4, "crescent"), (2, 4, "half"), (3, 4, "gibbous"), (4, 4, "full"), (1, 3, "crescent"), (2, 3, "gibbous"), (1, 8, "crescent"), (5, 8, "gibbous")]
MOONS = ("disk", "crescent", "half", "gibbous")
PROBE = "(v) => { const s = document.createElement('span'); s.style.color = `var(${v})`; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }"


def _of(slug):
    return next(n for n in SCENE["map"]["nodes"] if n["slug"] == slug)


def _merged(slug, merged, total):
    """The goal's tasks: `merged` of `total` merged, the rest waiting."""
    _of(slug)["tasks"] = [task(f"m{i}", f"Task {i}", "merged" if i < merged else "waiting", BACKEND) for i in range(total)]


def _pages(monkeypatch):
    """A goal's screen from its node of the Map: its state, its tasks as its plan."""
    real = Stub.commands

    def commands(self):
        def page(a):
            n = _of(a["slug"])
            self.calls.append(("ideas.page", {"slug": a["slug"]}))
            return {"slug": n["slug"], "title": n["title"], "track": n["goal"], "state": n["state"], "size": "M", "talk": [], "busy": False, "checks": [], "lens": [], "state_error": "", "route": [],
                    "plan": {"tasks": copy.deepcopy(n["tasks"]), "estimate": None} if n["tasks"] else None, "pitch": copy.deepcopy(n.get("pitch")),
                    "sections": [{"name": "Gist", "thesis": n["title"], "text": f"{n['title']}: in the person's words."}]}
        return {**real(self), "ideas.page": page}
    monkeypatch.setattr(Stub, "commands", commands)


async def _sheet(page):
    await page.locator(".gbar__head", has_text="2 of 9 goals done").wait_for(timeout=WAIT_MS)
    await page.locator(".gbar__head").click()
    sheet = page.get_by_role("dialog", name="Goals")
    await sheet.wait_for(timeout=WAIT_MS)
    return sheet


async def _phase(row):
    """The phase class of a row's moon, or None when it has no moon."""
    moon = row.locator(".ork-moon")
    assert await moon.count() <= 1
    if not await moon.count():
        return None
    return [c for c in (await moon.get_attribute("class")).split() if c not in ("ork-moon", "big")]


@pytest.mark.asyncio
@pytest.mark.parametrize("merged,total,phase", PHASES)
async def test_a_goals_moon_is_its_tasks_merged_of_its_tasks_rounded_to_quarters(fake_repo, monkeypatch, merged, total, phase):
    _merged("register", merged, total)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        assert await _phase(sheet.locator('.dk[data-idea="register"]')) == [phase]


@pytest.mark.asyncio
async def test_a_raw_goal_and_one_with_no_task_have_no_moon_and_a_goal_with_tasks_all_waiting_has_the_new_moon(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        assert await sheet.locator('.dk[data-idea="second"]').count() == 1 and await _phase(sheet.locator('.dk[data-idea="second"]')) is None            # asks: no task yet
        assert await _phase(sheet.locator('.dk[data-idea="recovery"]')) == ["new"]                                                                       # a plan: its tasks, none merged
        assert await _phase(sheet.locator('.dk[data-idea="signin"]')) == ["half"]                                                                        # 3 of 5: 2.4 quarters
        await sheet.locator('[data-fold="new"] .gfold__head').click()
        raw = sheet.locator('.dk[data-idea="magic"]')
        assert await raw.count() == 1 and await _phase(raw) is None
        assert await sheet.locator(".dk .ork-moon").count() == 4                                                                                        # register, signin, cookie and recovery: the rest have no task


@pytest.mark.asyncio
async def test_a_pitch_and_a_release_have_none(fake_repo, monkeypatch):
    _merged("register", 2, 4)
    _of("register")["release"] = {"version": "1.4", "goals": ["button"], "out": ""}                                    # a release goal carries its file
    _of("signin")["pitch"] = {"state": "judged"}                                                                       # a pitch carries its views
    _of("cookie")["type"] = {"id": "release", "name": "A release", "sign": "release"}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        for slug in ("register", "cookie"):
            assert await sheet.locator(f'.dk[data-idea="{slug}"]').count() == 1 and await _phase(sheet.locator(f'.dk[data-idea="{slug}"]')) is None
        words = await page.evaluate("async () => { const m = await import('./shell-goals-words.js'); return [m.moonOf({ state: 'working', tasks: [{ state: 'merged' }], release: { version: '1.4' } }), "
                                    "m.moonOf({ state: 'sent', tasks: [{ state: 'merged' }], pitch: { state: 'sent' } }), m.moonOf({ state: 'raw', tasks: [{ state: 'merged' }] }), m.moonOf({ state: 'working', tasks: [] }), "
                                    "m.moonOf({ state: 'working', tasks: [{ state: 'merged' }, { state: 'dropped' }] }), m.moonOf({ state: 'done', tasks: [{ state: 'merged' }, { state: 'merged' }] })]; }")
        assert words == [None, None, None, None, "full", "full"]                                                       # a dropped task is not counted


@pytest.mark.asyncio
async def test_the_moon_is_14_px_after_the_title_before_the_state_sign_aria_hidden_and_still(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        row = sheet.locator('.dk[data-idea="signin"]')
        title, moon, mark, main = [await row.locator(s).bounding_box() for s in (".dk__title", ".ork-moon", ".dk__mark", ".dk__main")]
        assert (round(moon["width"]), round(moon["height"])) == (14, 14) and moon["x"] >= title["x"] + title["width"] - 1 and moon["x"] + moon["width"] <= mark["x"] + 1       # between the two
        assert abs((moon["y"] + 7) - (main["y"] + main["height"] / 2)) <= 1                                           # on the row's middle
        el = row.locator(".ork-moon")
        assert await el.get_attribute("aria-hidden") == "true" and await el.inner_text() == ""
        after = await el.evaluate("e => { const a = getComputedStyle(e, '::after'); return [a.width, a.height, a.position, a.animationName, getComputedStyle(e).animationName, getComputedStyle(e).transitionDuration]; }")
        assert after == ["14px", "14px", "absolute", "none", "none", "0s"]                                              # the lit part is the box's size; no motion of its own
        assert "moon" not in await row.locator(".dk__main").get_attribute("aria-label")                           # shown, never named
        order = await row.locator(".dk__main").evaluate("e => [...e.children].map((c) => c.className.split(' ')[0])")
        assert order.index("dk__title") < order.index("ork-moon") < order.index("dk__mark")


@pytest.mark.asyncio
async def test_the_moon_takes_the_frame_and_the_ink_no_colour_of_its_own_and_its_files_are_served(fake_repo, monkeypatch):
    _merged("register", 4, 4)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        dark, lit, full = await page.evaluate(PROBE, "--ork-frame"), await page.evaluate(PROBE, "--ork-ink-muted"), await page.evaluate(PROBE, "--ork-ink")
        half = sheet.locator('.dk[data-idea="signin"] .ork-moon')
        got = await half.evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e, '::after').backgroundColor, getComputedStyle(e).webkitMaskImage, getComputedStyle(e, '::after').webkitMaskImage]")
        assert got[0] == dark and got[1] == lit and "moons/disk.svg" in got[2] and "moons/half.svg" in got[3]
        fullmoon = sheet.locator('.dk[data-idea="register"] .ork-moon')
        got = await fullmoon.evaluate("e => [getComputedStyle(e, '::after').backgroundColor, getComputedStyle(e, '::after').webkitMaskImage]")
        assert got[0] == full and "moons/disk.svg" in got[1]                                                            # the full moon's lit part is the ink
        for name in MOONS:                                                                                              # the masks are served beside the sheets, once and not found nowhere
            status = await page.evaluate("async (n) => { const r = await fetch(`moons/${n}.svg`); return [r.status, r.headers.get('content-type')]; }", name)
            assert status[0] == 200 and status[1].startswith("image/svg+xml"), name


@pytest.mark.asyncio
async def test_a_goals_screen_has_its_moon_in_its_head_28_px_beside_its_words(fake_repo, monkeypatch):
    _merged("register", 3, 4)
    _pages(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        await sheet.locator('.dk[data-idea="register"] .dk__open').click()
        head = page.locator(".screen .goal-state")
        await head.wait_for(timeout=WAIT_MS)
        moon, words = await head.locator(".ork-moon").bounding_box(), await head.locator("p").bounding_box()
        assert (round(moon["width"]), round(moon["height"])) == (28, 28) and moon["x"] + moon["width"] <= words["x"] + 1
        assert "gibbous" in (await head.locator(".ork-moon").get_attribute("class")).split() and "big" in (await head.locator(".ork-moon").get_attribute("class")).split()
        assert "working" in await head.locator("p").inner_text()
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_goal_that_is_not_read_has_no_moon_in_its_screen(fake_repo, monkeypatch):
    _pages(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        await sheet.locator('.dk[data-idea="second"] .dk__open').click()
        await page.locator(".screen .goal-state").wait_for(timeout=WAIT_MS)
        assert await page.locator(".screen .goal-state .ork-moon").count() == 0


def test_the_app_serves_the_moons_and_its_worker_keeps_them_in_the_new_version():
    served = pwa.files()
    assert {f"moons/{n}.svg" for n in MOONS} <= set(served) and all(served[f"moons/{n}.svg"].is_file() for n in MOONS)
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    shell = sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
    assert 'const CACHE = "orkcraft-app-v85";' in sw and all(f'"moons/{n}.svg"' in shell for n in MOONS)
