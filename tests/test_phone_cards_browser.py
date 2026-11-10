"""The phone's cards (docs/specs/147-one-card-four-corners.md part F.2–F.3, decisions §251.5–§251.6), in a real browser against the phone's stub host, with touch at 390 × 844: the hand's row laid by leader (a 22 px separator with the leader's head before each
group), its card 80 × 112 cut at 62, a card pressed rising by what is cut to show the rest; the opened card 5 : 7 at the screen's width; and, while the keyboard is up (a stand-in `visualViewport` clearly shorter than the window), the opened card giving up 5 : 7 for
its top corners, its title in two lines and the field, as tall as the screen leaves, taking 5 : 7 back when the keyboard goes. (The crown's piles: tests/test_phone_menu_browser.py.) Screenshots to $UPRIGHT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_context_narrow_browser import SIGN_IN_Q, box, cards, open_up  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None

# the keyboard's visual viewport, as a browser reports it: shorter than the window by the keyboard's height; `__keyboard(px)` raises it, `__keyboard(0)` takes it away
KEYBOARD = """(() => {
  const t = new EventTarget(); let key = 0;
  const vv = { get height() { return window.innerHeight - key; }, offsetTop: 0, scale: 1, addEventListener: (...a) => t.addEventListener(...a), removeEventListener: (...a) => t.removeEventListener(...a) };
  Object.defineProperty(window, "visualViewport", { value: vv, configurable: true });
  window.__keyboard = (px) => { key = px; t.dispatchEvent(new Event("resize")); };
})();"""


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def card(pg):
    return pg.locator(".hand-up .hand-lifted")


def test_the_hand_is_laid_by_leader_a_head_before_each_group_and_each_group_is_its_leaders_cards(gui):
    pg, host, log = open_up(gui, "ready")
    try:
        row = pg.locator(".up-cards")
        kids = row.evaluate("(e) => [...e.children].map((c) => c.classList.contains('up-sep') ? 'sep' : c.dataset.key)")
        assert kids[0] == "sep" and kids.count("sep") >= 2 and kids[1] != "sep", "a separator opens the row and every group, its first card follows it"
        groups, cur = [], None
        for k in kids:
            if k == "sep":
                cur = []
                groups.append(cur)
            else:
                cur.append(k)
        assert all(groups), "no head without cards"
        assert sorted(k for g in groups for k in g) == sorted(c.get_attribute("data-key") for c in cards(pg).all()), "every card is in one group"
        assert groups[-1] == ["ready:music", "ready:codes"], "the goals ready for main last, under the lich's head"
        seps = pg.locator(".up-sep")
        lanes = [s.get_attribute("data-lane") for s in seps.all()]
        assert lanes == sorted(lanes, key=lambda x: float(x)) or "Infinity" in lanes, "in the lanes' order"
        for s in seps.all():
            head = s.locator("img.ork-race__head")
            assert head.count() == 1 and head.get_attribute("src").startswith("/ds/orkui/races/") and round(box(s)["width"]) == 22 and round(box(head)["height"]) == 16, "a 22 px separator with the leader's head, 16 px"
        shot(pg, "phone-row-leaders")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_row_cuts_a_card_at_62_and_a_card_pressed_rises_by_what_is_cut_and_shows_the_rest_tapped_it_opens(gui):
    pg, host, log = open_up(gui)
    try:
        row, second = pg.locator(".up-row"), cards(pg).nth(1)
        r, c = box(row), box(second)
        assert round(c["width"]) == 80 and round(c["height"]) == 112
        cut = pg.locator(".up-cards").evaluate("(e) => e.getBoundingClientRect().bottom")
        assert cut - c["y"] == pytest.approx(62, abs=1.5), "80 x 112 cut at 62 by the row's foot"
        assert second.locator(".up-card__why").evaluate("(e) => e.getBoundingClientRect().top") >= cut - 4, "the why lies under the cut"
        x, y = c["x"] + c["width"] / 2, c["y"] + 30
        pg.mouse.move(x, y)
        pg.mouse.down()
        pg.wait_for_timeout(450)
        risen = box(second)
        assert c["y"] - risen["y"] == pytest.approx(50, abs=2), "pressed, it rises by 50 px"
        assert second.locator(".corner--foot").evaluate("(e, cut) => e.getBoundingClientRect().bottom <= cut + 1", cut), "who asks and what it costs are in view"
        shot(pg, "phone-row-pressed")
        pg.mouse.up()
        pg.wait_for_function("() => document.querySelector('.up-card[aria-pressed=true]')?.dataset.key === 'goal:phones'", timeout=WAIT_MS)
        assert card(pg).count() == 1 and pg.locator(".up-look").get_attribute("data-goal") == "phones" and second.get_attribute("aria-pressed") == "true", "tapped, it opens in the middle"
        assert r["y"] + r["height"] == pytest.approx(pg.viewport_size["height"], abs=1)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_opened_card_is_5_to_7_at_the_screens_width_with_its_corners_and_its_body_scrolling(gui):
    pg, host, log = open_up(gui, first=True)
    try:
        b, vw = box(card(pg)), pg.viewport_size["width"]
        assert b["width"] == pytest.approx(vw - 16, abs=3) and b["height"] / b["width"] == pytest.approx(7 / 5, abs=0.02), "5 : 7 at the screen's width"
        assert card(pg).locator(".corner--top.corner--large .ork-elem").count() == 1 and card(pg).locator(".corner--foot.corner--large").count() == 1
        assert card(pg).locator(".hand-lifted__body").evaluate("(e) => getComputedStyle(e).overflowY") == "auto"
        assert card(pg).locator(".hand-card__head, .hand-card__window, .hand-card__label").count() == 0, "the former anatomy is gone"
        pg.locator(".hand-up .hand-lifted .hand-lifted__text, .hand-up .hand-lifted .q-choose").first.evaluate("(e) => { e.style.minHeight = '900px'; }")
        assert box(card(pg))["height"] == pytest.approx(b["height"], abs=1), "never taller: a long body scrolls inside"
        assert card(pg).locator(".hand-lifted__body").evaluate("(e) => e.scrollHeight > e.clientHeight"), "and does scroll"
        shot(pg, "phone-opened")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_while_the_keyboard_is_up_the_opened_card_keeps_its_top_corners_and_a_title_in_two_lines_then_the_field_and_5_to_7_returns(gui):
    pg, host, log = open_up(gui, init=KEYBOARD, first=True)
    try:
        assert name_is(pg, SIGN_IN_Q)
        before = box(card(pg))
        pg.locator(".hand-up .hand-lifted .q-card--blank").click()
        area = pg.locator(".hand-up .hand-lifted textarea")
        area.wait_for(timeout=WAIT_MS)
        pg.evaluate("() => window.__keyboard(330)")                                  # the keyboard: the visual viewport is 330 px shorter than the window
        pg.wait_for_function("() => document.querySelector('.hand-up .hand-lifted')?.classList.contains('is-typing')", timeout=WAIT_MS)
        pg.wait_for_timeout(200)
        h = pg.viewport_size["height"] - 330
        t = box(card(pg))
        assert t["height"] / t["width"] < 1.3, "it gave up 5 : 7"
        assert t["y"] + t["height"] <= h + 1 and t["y"] + t["height"] >= h - 24 and t["y"] >= 60, "as tall as the screen leaves: from under the top row to the keyboard"
        top = card(pg).locator(".corner--top")
        assert top.is_visible() and box(top)["y"] < box(card(pg).locator(".hand-lifted__title"))["y"], "its top corners, then its title"
        title = card(pg).locator(".hand-lifted__title")
        assert title.evaluate("(e) => getComputedStyle(e).webkitLineClamp") == "2" and box(title)["height"] <= 2 * 22 + 2, "the title in two lines"
        assert not card(pg).locator(".corner--foot").is_visible() and not pg.locator(".up-row").is_visible(), "the foot and the hand's row give way"
        a = box(area)
        assert a["y"] > box(title)["y"] and a["y"] + a["height"] <= h + 1 and a["height"] >= 80, "then the field, above the keyboard"
        shot(pg, "phone-typing")
        pg.evaluate("() => window.__keyboard(0)")
        pg.wait_for_function("() => !document.querySelector('.hand-up .hand-lifted')?.classList.contains('is-typing')", timeout=WAIT_MS)
        pg.wait_for_timeout(200)
        after = box(card(pg))
        assert after["height"] / after["width"] == pytest.approx(7 / 5, abs=0.02) and after["height"] == pytest.approx(before["height"], abs=2), "5 : 7 again when the keyboard goes"
        assert pg.locator(".up-row").is_visible()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_viewport_only_a_little_shorter_is_not_a_keyboard(gui):
    pg, host, log = open_up(gui, init=KEYBOARD, first=True)
    try:
        pg.evaluate("() => window.__keyboard(60)")                                   # a browser's bar, not a keyboard
        pg.wait_for_timeout(250)
        assert not card(pg).evaluate("(e) => e.classList.contains('is-typing')") and box(card(pg))["height"] / box(card(pg))["width"] == pytest.approx(7 / 5, abs=0.02)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def name_is(pg, text):
    return pg.locator(".hand-lifted .hand-card__name").inner_text().strip() == text
