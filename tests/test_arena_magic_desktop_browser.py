"""Moments of magic on the desktop (docs/specs/74-moments-of-magic.md §1–§5, decisions §89), in a real browser at 1 440 × 900 against the one window's stub host
(tests/test_arena_decks_desktop_browser.py): a result answered leaves the hand as a stop does (spec 90 §2.3: Waits for your look and its seal are gone), a sent-back one's task in the field,
the empty Board's stars and its line of words, and a Board
with a party that has no stars."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost, arena  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import _open  # noqa: E402

pytestmark = pytest.mark.browser

LINE = "Make a party, then write it a goal in plain words, like a spell. Its orks do the work; you look at it before it goes in."

# Records each result's card that starts to leave the hand, at the frame it gets `is-leaving` (it lasts 0.3 s: a poll could miss it).
WATCH = """() => { window.__left = []; new MutationObserver((ms) => { for (const m of ms) { const e = m.target; if (m.type !== 'attributes' || !e.classList?.contains('is-leaving') || e.dataset.kind !== 'result') continue;
  const cs = getComputedStyle(e);
  window.__left.push({ key: e.dataset.key, name: cs.animationName, dur: cs.animationDuration, fn: cs.animationTimingFunction }); } }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] }); }"""

KEY = "result/register/k1"


# -- a result answered (§1, §2; a card of the hand since docs/specs/90-what-the-first-look-said.md §2.3) -----------------------------------------------

def test_a_result_answered_leaves_the_hand_where_it_stands_as_a_stop_does(arena):
    pg, host = arena
    pg.evaluate(WATCH)
    pg.mouse.move(5, 5)
    pg.locator(f'.arena-hc[data-key="{KEY}"]').wait_for(timeout=WAIT_MS)
    host.leave("ideas.merge", {"slug": "register", "task": "k1"})
    pg.wait_for_function("(k) => window.__left.some((x) => x.key === k)", arg=KEY, timeout=WAIT_MS)
    left = next(x for x in pg.evaluate("() => window.__left") if x["key"] == KEY)
    assert [left["name"], left["dur"], left["fn"]] == ["arena-leave", "0.3s", "steps(4)"]                        # it fades where it stands, in steps
    pg.locator(f'.arena-hc[data-key="{KEY}"]').wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator(".arena-stack .arena-task[data-task=k1]").count() == 0                                    # merged: not in the field


def test_a_sent_back_results_task_is_in_the_field_again(arena):
    pg, host = arena
    pg.mouse.move(5, 5)
    host.leave("ideas.back", {"slug": "register", "task": "k1"})                                                # its task is running again
    pg.locator(f'.arena-hc[data-key="{KEY}"]').wait_for(state="detached", timeout=WAIT_MS)
    pg.locator(".arena-stack .arena-task[data-task=k1]").wait_for(timeout=WAIT_MS)


def test_nothing_plays_under_reduced_motion_a_result_just_goes(arena):
    pg, host = arena
    pg.emulate_media(reduced_motion="reduce")
    pg.evaluate(WATCH)
    pg.mouse.move(5, 5)
    host.leave("ideas.merge", {"slug": "register", "task": "k1"})
    pg.locator(f'.arena-hc[data-key="{KEY}"]').wait_for(state="detached", timeout=WAIT_MS)
    assert all(x["name"] == "none" for x in pg.evaluate("() => window.__left"))


# -- the empty Board in the void (§4, §5) -----------------------------------------------------------------------------------------------------

def _no_party(pg, host):
    for slug in list(host.goals):
        host.goals.pop(slug)
    host.nodes = []
    host.bump({})
    pg.get_by_text("No parties yet").wait_for(timeout=WAIT_MS)


def _token(pg, name, prop="color"):
    return pg.evaluate("([n, p]) => { const i = document.createElement('i'); i.style[p] = `var(${n})`; document.body.append(i); const c = getComputedStyle(i)[p]; i.remove(); return c; }", [name, prop])


def test_the_empty_board_has_its_stars_behind_its_words_and_the_line_of_a_spell_and_a_board_with_a_party_has_none(gui):
    pg, host, errors = _open(gui, host=ArenaHost(), ready=".arena-phead")
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-stars").count() == 0                                                              # a Board with a party: no stars
    _no_party(pg, host)
    stars = pg.locator(".arena-stars")
    assert stars.count() == 1 and stars.get_attribute("aria-hidden") == "true"
    assert stars.evaluate("e => getComputedStyle(e).pointerEvents") == "none" and stars.evaluate("e => getComputedStyle(e).position") == "absolute"
    layers = stars.locator("i")
    assert layers.count() == 5 and stars.locator("i.is-ink").count() == 3
    colours = layers.evaluate_all("els => els.map((e) => getComputedStyle(e).backgroundColor)")
    assert colours == [_token(pg, "--ork-frame", "backgroundColor"), _token(pg, "--ork-ink-faint", "backgroundColor"), *[_token(pg, "--ork-ink", "backgroundColor")] * 3]      # tokens only
    assert layers.nth(2).evaluate("e => getComputedStyle(e).animationName") == "arena-twinkle" and layers.nth(0).evaluate("e => getComputedStyle(e).animationName") == "none"
    assert layers.nth(2).evaluate("e => getComputedStyle(e).animationDuration") == "4s" and layers.nth(2).evaluate("e => getComputedStyle(e).animationTimingFunction") == "steps(4)"
    assert pg.evaluate("() => { const r = document.querySelector('.arena-stars').getBoundingClientRect(); return r.width * r.height; }") > 400_000       # the Board's free area, not a strip
    assert pg.evaluate("""() => { const b = document.querySelector('.arena-note .ork-btn').getBoundingClientRect();
      return document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2).closest('.arena-stars') === null; }""")                       # the buttons are above the stars
    line = pg.locator(".arena-note p.arena-cap")
    assert line.inner_text() == LINE and line.evaluate("e => e.previousElementSibling.innerText") == "No parties yet"                         # under *No parties yet*
    assert line.evaluate("e => getComputedStyle(e).color") == _token(pg, "--ork-ink-muted")
    assert [b.inner_text() for b in pg.locator(".arena-note .ork-btn").all()] == ["New party", "New goal"]                                    # the buttons keep their words
    pg.close()
    assert not errors, "\n".join(errors)


def test_the_twinkling_stars_stand_still_at_sixty_percent_under_reduced_motion(gui):
    pg, host, errors = _open(gui, host=ArenaHost(), ready=".arena-phead")
    pg.emulate_media(reduced_motion="reduce")
    _no_party(pg, host)
    ink = pg.locator(".arena-stars i.is-ink")
    assert ink.evaluate_all("els => els.map((e) => [getComputedStyle(e).animationName, getComputedStyle(e).opacity])") == [["none", "0.6"]] * 3
    pg.close()
    assert not errors, "\n".join(errors)
