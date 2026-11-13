"""Spec 121 part F (docs/specs/121-the-day-the-morning-and-the-night.md §7.1, §9; decisions §199.3; mockup docs/mockups/hearing/ §4), in a real browser against a stub host: a leader's sketch, a pick of the task `sketch` whose variants are `text/html`
pages (media `page`), before the spec.

The card's face says who sketched it. Lifted on the desktop (1280 and the narrow window with a mouse) it opens the variants side by side over the pane, each page in an `iframe` with `sandbox="allow-scripts"` and no `allow-same-origin` (its page runs
and cannot read the Board's page), `title` *Sketch A by <Leader>*, each at about a phone's width, each with **Pick this one**; the note, **Sketch again** (a field, *What to change*) and **No sketch: go on** under all; with *Work at night* on, **Pick and
build now** beside **Pick this one**, quieter. On a phone-sized page (touch, upright) the card is the middle: one variant at a time at the screen's width, **A · B · C** as buttons, the variant's line, then the answers. The answers are `ideas.pick`
(`key`, `note`, `now`; `key: null` with `note` for new ones; `key: null` with `skip: true` for none). A picture sketch is drawn as Pick one draws it. Screenshots to $SKETCH_SHOTS when it is set."""
from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, PNG, head, need, node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["SKETCH_SHOTS"]) if os.environ.get("SKETCH_SHOTS") else None
LEADER = "Pixel-Perfect Dryad"

PAGE = ("<!doctype html><meta name=viewport content='width=device-width'><body style='margin:0;font:16px sans-serif;background:#223;color:#eee'><p id=name>{name}</p><p id=sandbox>?</p><button id=b onclick=\"this.textContent='pressed'\">Next</button>"
        "<script>try { document.getElementById('sandbox').textContent = 'reached ' + parent.document.title; } catch (e) { document.getElementById('sandbox').textContent = 'blocked'; }</script>")


def page_url(name: str) -> str:
    return "data:text/html;base64," + base64.b64encode(PAGE.replace("{name}", name).encode()).decode()


def variants():
    return [{"key": k, "name": name, "why": why, "url": page_url(name), "mime": "text/html", "w": None, "h": None, "seconds": None}
            for k, name, why in (("A", "the crown", "A small crown over the first player's name."), ("B", "the gold frame", "The first row framed in gold."), ("C", "the moment", "A banner as the answers close."))]


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class SketchHost(HandHost):
    """A project with one goal at its sketch: the pick row of the task `sketch` (Design's leader made three pages), and `ideas.pick` answering it. `work_at_night`: the Board's setting."""

    def __init__(self, media="page", round_=1, work_at_night=False):
        super().__init__(bare=True)
        self.work_at_night = work_at_night
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.nodes.append(node("party", "design", "Party quiz results", "table", state="working", element="ice", asks_you=True))
        vs = variants()
        if media != "page":
            vs = [{"key": "A", "name": "Crown", "why": "", "url": "data:image/png;base64," + base64.b64encode(PNG).decode(), "mime": "image/png", "w": 3, "h": 2, "seconds": None},
                  {"key": "B", "name": "Frame", "why": "", "url": "data:image/png;base64," + base64.b64encode(PNG).decode(), "mime": "image/png", "w": 3, "h": 2, "seconds": None}]
        self.needs = [need("pick", "design", "party", "Party quiz results", "Which look?", slug="party", task="sketch", round=round_, media=media, variants=vs, n=len(vs), ask="Which look for the results?",
                           short="Party quiz", idea_title="Party quiz results", by={"slug": "design-lead", "name": LEADER, "head": head("dryad", "design")}, blocks=True)]

    def handle(self, name, a):
        if name == "ideas.board":
            got = super().handle(name, a)
            got["work_at_night"] = self.work_at_night
            return got
        if name == "ideas.pick":
            self.log.append((name, a))
            self.needs = []
            return self.bump({"ok": True})
        return super().handle(name, a)


def window(gui, width="wide", **kw):
    pg, host, log = open_hand(gui, host=SketchHost(**kw), width=width)
    pg.locator(".up-card" if width == "phone" else ".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def lift(pg):
    pg.locator('.hand-card[data-kind="pick"]').first.click(position={"x": 10, "y": 24})


def open_pane(pg):
    lift(pg)
    pg.locator('.table-over[data-kind="choose"] .sk-pane').wait_for(timeout=WAIT_MS)
    pg.locator(".sk-pane iframe.sk-frame").nth(2).wait_for(timeout=WAIT_MS)


def pane_frame(pg, key):
    return pg.frame_locator(f'.sk-pane iframe[title="Sketch {key} by {LEADER}"]')


def pick_args(pg, host, at_least=1):
    return _calls(pg, host, "ideas.pick", at_least)


# -- the card's face -------------------------------------------------------------------------------------------------------------------------


# -- the desktop: side by side over the pane --------------------------------------------------------------------------------------------------


def test_a_sketchs_page_runs_in_its_frame_and_cannot_reach_the_boards_page(gui):
    pg, host, log = window(gui)
    try:
        open_pane(pg)
        a = pane_frame(pg, "A")
        a.locator("#name").wait_for(timeout=WAIT_MS)
        assert a.locator("#name").text_content() == "the crown"
        assert a.locator("#sandbox").text_content() == "blocked", "its script ran and could not read parent.document"
        a.locator("#b").click()
        assert a.locator("#b").text_content() == "pressed", "pressed as the real thing would be"
        assert pane_frame(pg, "B").locator("#name").text_content() == "the gold frame"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pick_this_one_under_a_variant_sends_its_letter_and_the_note_and_the_pane_goes_with_the_card(gui):
    pg, host, log = window(gui)
    try:
        open_pane(pg)
        pg.get_by_role("textbox", name="A note (optional)").fill("Love the gold")
        pg.locator('.sk-one[data-variant="B"] [data-answer="pick"]').click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": "B", "note": "Love the gold", "via": "hand"}
        pg.locator(".sk-pane").wait_for(state="detached", timeout=WAIT_MS)
        pg.wait_for_selector('.hand-card[data-kind="pick"]', state="detached", timeout=WAIT_MS)            # the card crumbles where it lay, then it is gone
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pick_and_build_now_only_with_work_at_night_on_and_it_sends_now(gui):
    off, host, log = window(gui)
    try:
        open_pane(off)
        assert off.locator('[data-answer="pick-now"]').count() == 0 and off.get_by_role("button", name="Pick and build now").count() == 0
    finally:
        off.close()
    assert not log
    pg, host, log = window(gui, work_at_night=True)
    try:
        open_pane(pg)
        now = pg.locator('.sk-one[data-variant="C"] [data-answer="pick-now"]')
        assert now.text_content().strip() == "Pick and build now" and "primary" not in now.get_attribute("class") and "primary" in pg.locator('.sk-one[data-variant="C"] [data-answer="pick"]').get_attribute("class"), "quieter than Pick this one"
        assert pg.locator('.sk-one[data-variant="C"] [data-answer="pick"]').bounding_box()["x"] < now.bounding_box()["x"], "beside it"
        now.click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": "C", "note": "", "via": "hand", "now": True}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_sketch_again_asks_what_to_change_and_sends_new_ones_with_the_note(gui):
    pg, host, log = window(gui)
    try:
        open_pane(pg)
        pg.locator('[data-answer="again-open"]').click()
        field = pg.get_by_role("textbox", name="What to change")
        go = pg.locator('[data-answer="again"]')
        assert go.text_content().strip() == "Sketch again" and go.is_disabled(), "nothing to send yet"
        field.fill("Bigger crown, no gold")
        go.click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": None, "note": "Bigger crown, no gold", "via": "hand"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_sketch_go_on_sends_none_and_skip(gui):
    pg, host, log = window(gui)
    try:
        open_pane(pg)
        pg.get_by_role("button", name="No sketch: go on").click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": None, "skip": True, "via": "hand"}
        pg.locator(".sk-pane").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_after_three_rounds_it_says_so_and_offers_no_fourth(gui):
    pg, host, log = window(gui, round_=3)
    try:
        open_pane(pg)
        assert pg.locator('[data-part="rounds"]').text_content().strip() == "Three rounds: pick one or go on"
        assert pg.locator('[data-answer="again-open"]').count() == 0 and pg.get_by_role("button", name="No sketch: go on").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the phone: one variant at a time at the screen's width ---------------------------------------------------------------------------------------

def phone(gui, **kw):
    pg, host, log = window(gui, "phone", **kw)
    pg.locator(".hand-up .up-card").first.click()                     # goal 169 F: the middle is the feed until a card of the row is pressed
    pg.locator(".hand-lifted--up .hand-way--sketch").wait_for(timeout=WAIT_MS)
    return pg, host, log


def test_on_the_phone_one_variant_shows_at_the_screens_width_and_a_b_c_are_buttons_that_change_it(gui):
    pg, host, log = phone(gui)
    try:
        assert pg.locator(".sk-pane").count() == 0 and pg.locator("iframe.sk-frame").count() == 1, "one at a time"
        f = pg.locator("iframe.sk-frame")
        assert f.get_attribute("title") == f"Sketch A by {LEADER}" and f.get_attribute("sandbox") == "allow-scripts"
        card = pg.locator(".hand-lifted--up").bounding_box()
        box = f.bounding_box()
        assert box["width"] >= card["width"] - 40 and box["width"] <= 390 and box["x"] >= 0 and box["x"] + box["width"] <= 391, (box, card)
        abc = pg.locator(".sk-abc button")
        assert [b.text_content().strip() for b in abc.all()] == ["A", "B", "C"] and abc.nth(0).get_attribute("aria-pressed") == "true"
        assert all(b.bounding_box()["height"] >= 43 for b in abc.all()), "a target of 44 px"
        assert pg.locator(".sk-line").text_content().strip().startswith("A · the crown")
        pg.frame_locator("iframe.sk-frame").locator("#name").wait_for(timeout=WAIT_MS)
        assert pg.frame_locator("iframe.sk-frame").locator("#sandbox").text_content() == "blocked"
        abc.nth(2).click()
        assert abc.nth(2).get_attribute("aria-pressed") == "true" and abc.nth(0).get_attribute("aria-pressed") == "false"
        assert pg.locator("iframe.sk-frame").count() == 1 and pg.locator("iframe.sk-frame").get_attribute("title") == f"Sketch C by {LEADER}"
        pg.frame_locator("iframe.sk-frame").locator("#name").wait_for(timeout=WAIT_MS)
        assert pg.frame_locator("iframe.sk-frame").locator("#name").text_content() == "the moment"
        assert pg.locator(".sk-line").text_content().strip().startswith("C · the moment")
        narrow.no_sideways(pg)
        shot(pg, "phone-sketch")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_phone_pick_this_one_sends_the_variant_shown_with_the_note(gui):
    pg, host, log = phone(gui)
    try:
        pg.locator('.sk-abc [data-variant="B"]').click()
        pg.get_by_role("textbox", name="A note (optional)").fill("Gold, but thinner")
        pg.locator('[data-answer="pick"]').click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": "B", "note": "Gold, but thinner", "via": "hand"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_phone_pick_and_build_now_sits_under_pick_this_one_with_work_at_night_on(gui):
    pg, host, log = phone(gui, work_at_night=True)
    try:
        pick, now = pg.locator('[data-answer="pick"]'), pg.locator('[data-answer="pick-now"]')
        assert now.text_content().strip() == "Pick and build now" and "primary" not in now.get_attribute("class")
        assert pick.bounding_box()["y"] < now.bounding_box()["y"] and pick.bounding_box()["height"] >= 43 and now.bounding_box()["height"] >= 43
        now.click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": "A", "note": "", "via": "hand", "now": True}
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_phone_sketch_again_and_no_sketch_are_answers_too(gui):
    pg, host, log = phone(gui)
    try:
        pg.locator('[data-answer="again-open"]').click()
        pg.get_by_role("textbox", name="What to change").fill("Less green")
        pg.locator('[data-answer="again"]').click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": None, "note": "Less green", "via": "hand"}
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = phone(gui)
    try:
        pg.get_by_role("button", name="No sketch: go on").click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": None, "skip": True, "via": "hand"}
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- a picture is drawn as Pick one draws it ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", ("wide", "phone"))
def test_a_picture_sketch_is_pick_ones_tiles_with_the_sketchs_answers(gui, width):
    pg, host, log = window(gui, width, media="image")
    try:
        if width == "wide":
            lift(pg)
        else:
            pg.locator(".hand-up .up-card").first.click()                 # goal 169 F: the middle is the feed until a card of the row is pressed
        pg.locator(".hand-way--sketch .pick-tiles").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-way--sketch .pick-tile").count() == 2 and pg.locator("iframe").count() == 0 and pg.locator(".sk-pane").count() == 0
        assert pg.locator('[data-answer="pick"]').is_disabled(), "nothing picked yet"
        pg.locator('.pick-tile__label[data-variant="B"]').click()
        pg.locator('[data-answer="pick"]').click()
        assert pick_args(pg, host)[0] == {"slug": "party", "task": "sketch", "key": "B", "note": "", "via": "hand"}
    finally:
        pg.close()
    assert not log, "\n".join(log)
