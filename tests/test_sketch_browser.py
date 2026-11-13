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




def pick_args(pg, host, at_least=1):
    return _calls(pg, host, "ideas.pick", at_least)


# -- the card's face -------------------------------------------------------------------------------------------------------------------------


# -- the desktop: side by side over the pane --------------------------------------------------------------------------------------------------




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






# -- the phone: one variant at a time at the screen's width ---------------------------------------------------------------------------------------

def phone(gui, **kw):
    pg, host, log = window(gui, "phone", **kw)
    pg.locator(".hand-up .up-card").first.click()                     # goal 169 F: the middle is the feed until a card of the row is pressed
    pg.locator(".hand-lifted--up .hand-way--sketch").wait_for(timeout=WAIT_MS)
    return pg, host, log










# -- a picture is drawn as Pick one draws it ------------------------------------------------------------------------------------------------------------

