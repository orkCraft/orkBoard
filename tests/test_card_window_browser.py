"""Spec 148 part A (docs/specs/148-a-window-on-every-card.md, decisions §252), in a real browser: `windowOf` of table/cardwindow.js chooses what a card's window shows in one order (what the work made, else the goal's picture,
else its words, else nothing), and `CardWindow` draws it in the lanes' window frame: an `<img>` (lazy, `object-fit: contain`, the goal's name as its alt) for a picture, real text clamped to the lines that fit for words, the made
window's drawing for what was made, nothing for none. `CardWindow` is drawn into a box of the test's own, against the hand's stub host."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402

pytestmark = pytest.mark.browser

PIC = "/media/_photo/dark-mode/1.jpg?s=abc"
DOT = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"       # a picture that loads, so the page logs no 404
MADE = {"kind": "hypothesis", "text": "Hosts who can skip a round stay longer", "state": "open"}
LONG = "The login screen is cut off on the phone when the keyboard is up and the person cannot reach the button below it. " * 4

DRAW = """async ({ of, h }) => {
  const [{ render, h: el }, { CardWindow }] = await Promise.all([import('preact'), import('/static/js/table/cardwindow.js')]);
  let box = document.getElementById('card-window');
  if (!box) { box = document.createElement('div'); box.id = 'card-window'; box.style.cssText = 'position:fixed;left:0;top:0;width:157px;background:var(--ork-panel);padding:8px;z-index:5'; document.body.appendChild(box); }
  render(null, box);
  render(el(CardWindow, { of, h }), box);
}"""


def draw(pg, of, h=None):
    pg.evaluate(DRAW, {"of": of, "h": h})
    return pg.locator("#card-window")


def test_the_window_chooses_made_then_picture_then_words_then_none(gui):
    pg, host, log = open_hand(gui)
    try:
        got = pg.evaluate("""({ made, pic }) => import('/static/js/table/cardwindow.js').then((m) => [
          m.windowOf({ made, picture: pic, words: 'w' }),
          m.windowOf({ made: null, picture: pic, words: 'w' }),
          m.windowOf({ made: { kind: 'diff', files: [] }, picture: pic, words: 'w' }),
          m.windowOf({ picture: '', words: '  Shows   the\\nwords ' }),
          m.windowOf({ picture: '   ', words: '' }),
          m.windowOf({}), m.windowOf(),
          m.linesOf(70), m.linesOf(100), m.linesOf(0)])""", {"made": MADE, "pic": PIC})
        made, picture, empty_made, words, none, bare, nothing, l70, l100, l0 = got
        assert made["kind"] == "made" and made["made"]["text"] == MADE["text"], "what the work made wins"
        assert picture == {"kind": "picture", "url": PIC}, "no made: the picture"
        assert empty_made["kind"] == "picture", "a made kind with nothing to draw is no made"
        assert words == {"kind": "words", "text": "Shows the words"}, "no picture: the words, whitespace made plain"
        assert none == bare == nothing == {"kind": "none"}
        assert (l70, l100, l0) == (3, 5, 1), "the lines a height holds, one at least"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_picture_is_a_lazy_img_contained_on_the_ground_with_the_goals_name_as_its_alt(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, {"picture": DOT, "words": "never shown", "name": "Dark mode"}, 90)
        win = box.locator(".card-win")
        win.wait_for(timeout=WAIT_MS)
        img = win.locator("img")
        assert img.count() == 1 and win.get_attribute("data-window") == "card-picture" and "never shown" not in box.inner_text()
        assert img.get_attribute("src") == DOT and img.get_attribute("alt") == "Dark mode" and img.get_attribute("loading") == "lazy"
        assert img.evaluate("e => getComputedStyle(e).objectFit") == "contain"
        assert abs(win.bounding_box()["height"] - 90) <= 0.5, "the place's height"
        assert "is-window" in win.get_attribute("class").split(), "the lanes' frame"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_words_are_real_text_clamped_to_the_lines_the_height_holds(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, {"words": LONG, "name": "Dark mode"}, 70)
        text = box.locator(".card-win__words")
        text.wait_for(timeout=WAIT_MS)
        assert box.locator("img").count() == 0 and text.inner_text().startswith("The login screen"), "real, selectable text"
        assert text.evaluate("e => getComputedStyle(e).webkitLineClamp") == "3"
        assert text.evaluate("e => e.scrollHeight > e.clientHeight"), "the rest is cut"
        assert text.bounding_box()["height"] <= 3 * 15 + 1
        box = draw(pg, {"words": "Short."}, 100)
        assert box.locator(".card-win__words").inner_text() == "Short."
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_what_the_work_made_is_drawn_by_the_made_window_and_none_draws_nothing(gui):
    pg, host, log = open_hand(gui)
    try:
        box = draw(pg, {"made": MADE, "picture": PIC}, 92)
        box.locator(".made-hyp").wait_for(timeout=WAIT_MS)
        assert box.locator("img").count() == 0 and box.locator(".card-win").get_attribute("data-window") == "made"
        assert MADE["text"] in box.locator(".made-hyp__text").inner_text() and box.locator(".made-hyp__chip").inner_text() == "Open"
        box = draw(pg, {"made": None, "picture": "", "words": ""}, 70)
        assert box.locator(".card-win").count() == 0 and box.inner_text().strip() == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)
