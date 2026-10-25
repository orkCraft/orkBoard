"""Spec 74 part B, the phone (docs/specs/74-moments-of-magic.md §1, §2, §4, §5, §8; decisions §89): Chromium at 390 × 844 against the scene of tests/test_pwa_arena_browser.py. A merged result's
stack leaves with its goal's element stamped (`.big`, its colour) where the ✓ was, a dropped one keeps its ✗, a result sent back (its task in the field again) goes down with no flash, none of it
under reduced motion; the Board with no party has its stars (`aria-hidden`, no pointer, twinkling ones still at 0.6 under reduced motion) and the one line of words, Loading and an error have
neither, a Board with a party has no stars; `sw.js` v85."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import BACKEND, SCENE, SCREENS, _scene, node, task  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _phone  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

LINE = "Make a party, then write it a goal in plain words, like a spell. Its orks do the work; you look at it before it goes in."
# What the page does is recorded as it happens (a leave lasts 0.3 s): each stack that leaves, with what it holds and what it plays.
RECORD = """
(() => {
  window.__seen = [];
  const note = (e) => {
    if (!e.classList || !e.classList.contains("is-leaving") || !e.dataset.ghost) return;
    const flash = e.querySelector(".deck__flash"), mark = flash && flash.firstElementChild;
    window.__seen.push({ key: e.dataset.ghost, sign: e.dataset.sign, anim: getComputedStyle(e).animationName, ms: getComputedStyle(e).animationDuration, flash: Boolean(flash),
      mark: mark ? mark.className : "", markAnim: mark ? getComputedStyle(mark).animationName : "", markMs: mark ? getComputedStyle(mark).animationDuration : "",
      markSteps: mark ? getComputedStyle(mark).animationTimingFunction : "", size: mark ? [mark.offsetWidth, mark.offsetHeight] : [], flashAnim: flash ? getComputedStyle(flash).animationName : "" });
  };
  document.addEventListener("DOMContentLoaded", () => new MutationObserver((ms) => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1) { note(n); n.querySelectorAll && n.querySelectorAll(".is-leaving").forEach(note); } })
    .observe(document.body, { childList: true, subtree: true }));
})();
"""
SEEN = "() => window.__seen"
BACKEND_COLUMN = '.stack[data-column="backend"]'


def extra(element="ice"):
    """A goal of its own with one result waiting at Review, in Backend's first row."""
    n = node("x1", "A goal to look at", "working", "implementation", element=element, tasks=[task("r1", "A result", "review", BACKEND, 1)])
    SCENE["map"]["nodes"].append(n)
    return n


async def _ready(page):
    await page.locator(f"{BACKEND_COLUMN} .deck").first.wait_for(timeout=WAIT_MS)
    await page.wait_for_timeout(2300)                                                                  # the first read of a goal is not a change


async def _leave(page, stub, change):
    change()
    stub.bump({})
    await page.wait_for_function("() => window.__seen.some((s) => s.key === 'x1|now')", timeout=WAIT_MS * 2)
    return next(s for s in await page.evaluate(SEEN) if s["key"] == "x1|now")


@pytest.mark.asyncio
async def test_a_merged_result_leaves_with_its_goals_element_stamped_in_its_colour(fake_repo, monkeypatch):
    extra("ice")
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await _ready(page)
        seen = await _leave(page, stub, lambda: SCENE["map"]["nodes"][-1]["tasks"][0].update(state="merged"))
        assert seen["sign"] == "check" and seen["anim"] == "leave" and seen["ms"] == "0.3s"                 # the card fades as it did, as long
        assert "ork-elem" in seen["mark"] and "ice" in seen["mark"].split() and "big" in seen["mark"].split() and "dim" not in seen["mark"].split()      # the goal's element, 28 px, not the ✓
        assert seen["size"] == [28, 28] and "ork-sign" not in seen["mark"]
        assert seen["markAnim"] == "stamp" and seen["markMs"] == "0.1s" and seen["markSteps"] == "steps(3)"   # three steps over the first third
        assert seen["flashAnim"] == "none"                                                                 # held, not blinked away
        await page.wait_for_function("() => document.querySelectorAll('.deck.is-leaving').length === 0", timeout=WAIT_MS)
        assert len([s for s in await page.evaluate(SEEN) if s["key"] == "x1|now"]) == 1                    # once


@pytest.mark.asyncio
async def test_the_stamp_goes_from_double_size_and_faint_to_full(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _ready(page)
        frames = await page.evaluate("""() => { const d = document.createElement('div'); d.className = 'deck is-leaving'; d.dataset.sign = 'check'; d.innerHTML = '<span class="deck__flash"><span class="ork-elem lava big"></span></span>';
          document.body.append(d); const a = d.querySelector('.ork-elem').getAnimations()[0]; const k = a.effect.getKeyframes(); d.remove(); return k.map((f) => [f.transform, f.opacity]); }""")
        assert frames == [["scale(2)", "0.4"], ["scale(1)", "1"]]


@pytest.mark.asyncio
async def test_a_dropped_result_keeps_its_cross_and_a_goal_with_no_element_its_check(fake_repo, monkeypatch):
    extra("ice")
    SCENE["map"]["nodes"].append(node("x2", "A goal with no element", "working", "implementation", element="", tasks=[task("r2", "Another result", "review", BACKEND, 1)]))
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await _ready(page)
        seen = await _leave(page, stub, lambda: SCENE["map"]["nodes"][-2]["tasks"][0].update(state="dropped"))
        assert seen["sign"] == "cross" and "ork-sign" in seen["mark"] and "cross" in seen["mark"].split() and "ork-elem" not in seen["mark"]
        SCENE["map"]["nodes"][-1]["tasks"][0]["state"] = "merged"
        stub.bump({})
        await page.wait_for_function("() => window.__seen.some((s) => s.key === 'x2|now')", timeout=WAIT_MS * 2)
        none = next(s for s in await page.evaluate(SEEN) if s["key"] == "x2|now")
        assert none["sign"] == "check" and "ork-sign" in none["mark"] and "check" in none["mark"].split()   # nothing to stamp: the sign it had


@pytest.mark.asyncio
async def test_a_result_sent_back_goes_down_with_no_flash(fake_repo, monkeypatch):
    extra("ice")

    def back():
        t = SCENE["map"]["nodes"][-1]["tasks"][0]
        t.update(state="ready", by=SCREENS)                                                                # in the field again, at another member's column
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await _ready(page)
        seen = await _leave(page, stub, back)
        assert seen["sign"] == "back" and seen["flash"] is False and seen["anim"] == "back" and seen["ms"] == "0.3s"
        await page.wait_for_function("() => document.querySelectorAll('.deck.is-leaving').length === 0", timeout=WAIT_MS)
        assert len([s for s in await page.evaluate(SEEN) if s["key"] == "x1|now"]) == 1


@pytest.mark.asyncio
async def test_the_back_leave_moves_24_px_down_while_it_fades_in_three_steps(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _ready(page)
        got = await page.evaluate("""() => { const d = document.createElement('div'); d.className = 'deck is-leaving'; d.dataset.sign = 'back'; document.body.append(d);
          const a = d.getAnimations()[0], k = a.effect.getKeyframes(), t = a.effect.getTiming(), e = getComputedStyle(d).animationTimingFunction; d.remove(); return [k[k.length - 1].transform, k[k.length - 1].opacity, t.duration, e]; }""")
        assert got == ["translateY(24px)", "0", 300, "steps(3)"]


@pytest.mark.asyncio
async def test_nothing_of_it_plays_under_reduced_motion_and_the_card_is_not_flashed(fake_repo, monkeypatch):
    extra("ice")
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await page.emulate_media(reduced_motion="reduce")
        await _ready(page)
        SCENE["map"]["nodes"][-1]["tasks"][0]["state"] = "merged"
        stub.bump({})
        await page.locator(f'{BACKEND_COLUMN} .deck[data-key="x1|now"]').wait_for(state="detached", timeout=WAIT_MS * 2)
        assert await page.evaluate(SEEN) == []                                                             # nothing moves
        names = await page.evaluate("""() => { const out = []; for (const sign of ['check', 'cross', 'back']) { const d = document.createElement('div'); d.className = 'deck is-leaving'; d.dataset.sign = sign;
          d.innerHTML = '<span class="deck__flash"><span class="ork-elem ice big"></span></span>'; document.body.append(d);
          out.push([getComputedStyle(d).animationName, getComputedStyle(d.firstChild).animationName, getComputedStyle(d.querySelector('.ork-elem')).animationName]); d.remove(); } return out; }""")
        assert names == [["none", "none", "none"]] * 3


async def _empty(page):
    await page.locator(".arena-empty.has-void").wait_for(timeout=WAIT_MS)
    return page.locator(".arena-empty.has-void")


@pytest.mark.asyncio
async def test_the_board_with_no_party_has_its_stars_and_its_line(fake_repo, monkeypatch):
    SCENE["map"].update(goals=[], nodes=[], edges=[])
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        empty = await _empty(page)
        await empty.get_by_text("No parties yet.").wait_for(timeout=WAIT_MS)
        line = empty.locator(".arena-empty__say")
        assert (await line.inner_text()).strip() == LINE and "muted" in (await line.get_attribute("class")).split()
        assert await page.evaluate("document.querySelector('.arena-empty__say').previousElementSibling.textContent") == "No parties yet."      # under the heading line, before the buttons
        stars = empty.locator(".void-stars")
        assert await stars.get_attribute("aria-hidden") == "true" and await stars.evaluate("(e) => getComputedStyle(e).pointerEvents") == "none"
        assert await stars.evaluate("(e) => Number(getComputedStyle(e).zIndex) < 0 && getComputedStyle(e).position") == "absolute"            # behind the words and the buttons
        assert await stars.evaluate("(e) => getComputedStyle(e, '::before').boxShadow.match(/rgb/g).length") > 40                               # sparse 2 × 2 squares
        assert await stars.evaluate("(e) => [getComputedStyle(e, '::before').width, getComputedStyle(e, '::before').height]") == ["2px", "2px"]
        twinkle = await stars.evaluate("""(e) => [...e.querySelectorAll('b')].map((b) => { const s = getComputedStyle(b); return [s.animationName, s.animationDuration, s.animationTimingFunction, s.animationDelay, s.width, s.height, s.backgroundColor]; })""")
        ink = await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--ork-ink').trim()")
        assert 5 <= len(twinkle) <= 12 and {t[:3][0] for t in twinkle} == {"twinkle"} and {t[1] for t in twinkle} == {"4s"} and {t[2] for t in twinkle} == {"steps(4)"}
        assert len({t[3] for t in twinkle}) == len(twinkle) and {(t[4], t[5]) for t in twinkle} == {("2px", "2px")}                              # each its own delay
        assert await page.evaluate("(c) => { const e = document.createElement('i'); e.style.color = c; document.body.append(e); const v = getComputedStyle(e).color; e.remove(); return v; }", ink) == twinkle[0][6]
        assert await page.locator(".void-stars").count() == 1
        for box in await empty.locator("p, button").all():                                                  # the stars take no pointer: the buttons are pressed
            assert await box.evaluate("(e) => document.elementFromPoint(e.getBoundingClientRect().x + 2, e.getBoundingClientRect().y + 2)?.closest('.void-stars') === null")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_twinkling_stars_are_still_at_point_six_under_reduced_motion(fake_repo, monkeypatch):
    SCENE["map"].update(goals=[], nodes=[], edges=[])
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.emulate_media(reduced_motion="reduce")
        empty = await _empty(page)
        got = await empty.locator(".void-stars b").evaluate_all("(bs) => bs.map((b) => [getComputedStyle(b).animationName, getComputedStyle(b).opacity])")
        assert got and set(map(tuple, got)) == {("none", "0.6")}


@pytest.mark.asyncio
async def test_a_board_with_a_party_and_the_screens_that_reuse_the_empty_look_have_no_stars(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await _ready(page)
        assert await page.locator(".void-stars, .arena-empty__say").count() == 0
    real = Stub.commands

    def commands(self):
        got = real(self)
        return {**got, "ideas.map": lambda a: {"error": "The Board is not there"}}
    monkeypatch.setattr(Stub, "commands", commands)
    async with _phone(fake_repo, monkeypatch) as (stub, page):                                               # an error says so, in the void's absence
        await page.locator(".arena > p.arena-empty").first.wait_for(timeout=WAIT_MS)
        assert await page.locator(".void-stars, .arena-empty__say, .has-void").count() == 0


@pytest.mark.asyncio
async def test_sw_is_one_up(fake_repo):
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v85";' in sw
