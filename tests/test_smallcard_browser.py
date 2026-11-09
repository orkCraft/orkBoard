"""Spec 168 A2 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.3, §283.4, §284.2), in a real browser against a stub host: the small face-up card (table/smallcard.js) measures 56 x 78 with its rune, a dot for each party of its route
(filled when done, hollow ahead) and its picture (a goal's own, else its kind's sign), a signal is its frame; the preview (table/preview.js) shows a card hovered or focused at 144 x 202 beside it after about 300 ms, one at a time, Esc puts it away, focus never moves,
no box changes size; the column's fan and deck backs have it in place of a native `title`, their words in `aria-label`."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import open_column  # noqa: E402

pytestmark = pytest.mark.browser

PIC = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

MOUNT = """async ([pic]) => {
  const [{ render, h }, { SmallCard }] = await Promise.all([import('preact'), import('/static/js/table/smallcard.js')]);
  let box = document.getElementById('sm-test');
  if (!box) { box = document.createElement('div'); box.id = 'sm-test'; box.style.cssText = 'position:fixed;left:400px;top:120px;display:flex;gap:30px;z-index:5'; document.body.appendChild(box); }
  const n = (slug, more) => ({ slug, title: 'Goal ' + slug, short: 'Goal ' + slug, element: 'ice', hue: 'ice', type: { sign: 'bug' }, ...more });
  const parties = [{ slug: 'tech' }, { slug: 'design' }, { slug: 'art' }];
  render(h('div', { style: 'display:contents' },
    h(SmallCard, { n: n('plain'), parties, done: ['tech'] }),
    h(SmallCard, { n: n('pic', { picture: pic }), parties, done: ['tech', 'design', 'art'], signal: 'alert' }),
    h(SmallCard, { n: n('bad'), parties: [{ slug: 'tech' }], signal: 'danger' })), box);
}"""


def mount(pg):
    pg.evaluate(MOUNT, [PIC])
    pg.wait_for_selector("#sm-test .sm", timeout=WAIT_MS)


def test_the_small_card_is_56_by_78_with_its_rune_its_dots_and_its_picture(gui):
    pg, host, log = open_column(gui)
    try:
        mount(pg)
        cards = pg.locator("#sm-test .sm")
        assert cards.count() == 3
        assert cards.evaluate_all("els => els.map((e) => [e.offsetWidth, e.offsetHeight])") == [[56, 78]] * 3
        plain, pic, bad = cards.nth(0), cards.nth(1), cards.nth(2)
        assert plain.inner_text().strip() == "", "no words on its face"
        assert plain.locator(".sm-tl .ork-elem.ice").count() == 1, "the goal's rune, top left"
        rune, box = plain.locator(".sm-tl").bounding_box(), plain.bounding_box()
        assert rune["x"] - box["x"] < 8 and rune["y"] - box["y"] < 8
        dots = plain.locator(".sm-dot")
        assert dots.count() == 3 and plain.locator(".sm-dot.is-done").count() == 1, "a dot a party, the one done filled, the others hollow"
        assert dots.evaluate_all("els => els.map((e) => getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)')") == [True, False, False]
        assert plain.locator(".sm-dots").bounding_box()["y"] > box["y"] + box["height"] / 2, "the dots at the foot"
        assert plain.locator(".sm-pic .ork-sign.big.bug").count() == 1 and plain.locator(".sm-pic img").count() == 0, "no picture attached: its kind's sign, big"
        assert pic.locator(".sm-pic img.sm-pic__img").count() == 1 and pic.locator(".sm-pic .ork-sign").count() == 0, "the goal's picture in its middle"
        assert pic.locator(".sm-dot.is-done").count() == 3
        assert pic.get_attribute("data-signal") == "alert" and bad.get_attribute("data-signal") == "danger"
        ring = cards.evaluate_all("els => els.map((e) => getComputedStyle(e).boxShadow)")
        assert ring[0] == "none" and ring[1] != "none" and ring[2] != "none" and ring[1] != ring[2], "the signal is the card's own frame"
        assert plain.get_attribute("title") is None and plain.get_attribute("aria-label") == "Goal plain"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_small_card_hovered_or_focused_is_shown_at_144_by_202_after_a_moment_and_esc_puts_it_away(gui):
    pg, host, log = open_column(gui)
    try:
        mount(pg)
        card = pg.locator("#sm-test .sm").nth(1)
        before = pg.evaluate("() => [...document.querySelectorAll('#sm-test .sm')].map((e) => [e.offsetWidth, e.offsetHeight])")
        card.hover()
        pg.wait_for_timeout(100)
        assert pg.locator("[data-preview]").count() == 0, "not at once"
        pg.wait_for_selector("[data-preview=face]", timeout=WAIT_MS)
        big, small = pg.locator("[data-preview=face]").bounding_box(), card.bounding_box()
        assert (big["width"], big["height"]) == (144, 202) and big["x"] >= small["x"] + small["width"], "beside it, to its right, 144 x 202"
        assert "Goal pic" in pg.locator("[data-preview=face]").inner_text() and pg.locator("[data-preview=face] img").count() == 1
        assert pg.evaluate("() => [...document.querySelectorAll('#sm-test .sm')].map((e) => [e.offsetWidth, e.offsetHeight])") == before, "no box changes size"
        pg.keyboard.press("Escape")
        assert pg.locator("[data-preview]").count() == 0, "Esc puts it away"
        pg.wait_for_timeout(500)
        assert pg.locator("[data-preview]").count() == 0, "and it stays away while the pointer rests"
        pg.mouse.move(5, 5)
        pg.locator("#sm-test .sm").nth(0).focus()
        pg.wait_for_selector("[data-preview=face]", timeout=WAIT_MS)
        assert pg.evaluate("() => document.activeElement.getAttribute('data-goal')") == "plain", "focus never moves"
        assert pg.locator("[data-preview=face]").inner_text().count("Goal plain") == 1
        pg.locator("#sm-test .sm").nth(2).hover()
        pg.wait_for_selector("[data-preview=face]:has-text('Goal bad')", timeout=WAIT_MS)
        assert pg.locator("[data-preview]").count() == 1, "one at a time"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_fan_and_the_deck_backs_are_previewed_with_their_goals_name_and_have_no_native_title(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        backs = pg.locator(".col-card--down")
        assert backs.count() >= 6
        assert backs.evaluate_all("els => els.map((e) => e.getAttribute('title'))") == [None] * backs.count(), "no native title on any back"
        fan = pg.locator(".col-card--fan")
        label = fan.nth(2).get_attribute("aria-label")
        assert label.startswith("Kick a player from the lobby"), label
        fan.nth(2).hover(position={"x": 18, "y": 50})
        pg.wait_for_selector("[data-preview=back]", timeout=WAIT_MS)
        said = pg.locator("[data-preview=back]")
        assert said.bounding_box()["width"] == 144 and said.bounding_box()["height"] == 202
        assert "Kick a player from the lobby" in said.inner_text() and "waits for the Orkmaster" in said.inner_text(), "the goal's name and its state's line"
        assert label == "Kick a player from the lobby: waits for the Orkmaster"
        pg.keyboard.press("Escape")
        assert pg.locator("[data-preview]").count() == 0
        pg.mouse.move(700, 600)
        pg.wait_for_timeout(200)
        fan.nth(3).focus()
        pg.wait_for_selector("[data-preview=back]", timeout=WAIT_MS)
        assert "Host can skip a round" in pg.locator("[data-preview=back]").inner_text()
        assert pg.evaluate("() => document.activeElement.getAttribute('data-goal')") == "raw2", "focus stays on the back"
        deck = pg.locator(".col-card--deck").first
        deck.focus()
        pg.wait_for_selector("[data-preview=back]:has-text('Round timer on phones')", timeout=WAIT_MS)
        assert pg.locator("[data-preview]").count() == 1
        pg.mouse.move(700, 600)
        pg.evaluate("() => document.activeElement.blur()")
        pg.wait_for_function("() => !document.querySelector('[data-preview]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)
