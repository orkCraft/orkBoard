"""One card through a goal's life (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.5, §6.8, §6.11; decisions §198.8), in a real browser against a stub host: the + card turned into the field with the field focused in the press itself, its rune large and
the five on a press of it, Esc turning it back with its text and rune kept; Send turning it to its back and the back lying in the Orkmaster's column (spec 128 B.3: face down and sideways, its rune lit, no name, never the + card's green); a held goal's decision card in the hand;
at the narrow width the goal talked over a token with its rune glowing, and on a phone the field and the menu's row. What lay in the Orkmaster's lane at the wide width (the back's face, the route's heads, the wait as the seal's ring, the turn up and the flight to the lane) is the column's
now: tests/test_column_browser.py. Screenshots to $LIFE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, head, need, node, open_hand, task  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["LIFE_SHOTS"]) if os.environ.get("LIFE_SHOTS") else None
STEP = {"design": {"party": "design", "leader": "design-lead", "head": head("dryad", "design")}, "tech": {"party": "tech", "leader": "tech-lead", "head": head("shaman")},
        "product": {"party": "product", "leader": "product-lead", "head": head("unicorn", "product")}}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def ripe(left, seconds=240, held=False, by=""):
    return {"left_s": left, "seconds": seconds, "risk": "low", "priority": "high", "held": held, "by": by or ("person" if held else ""), "why": ""}


def back(route=("design", "tech"), heard=(), stances=(), ripe=None):
    return {"route": [STEP[p] for p in route], "cost": {"calls": 3, "usd_low": 0.1, "usd_high": 0.2}, "offer": ["product"], "short": False, "heard": list(heard),
            "stances": [{"party": p, "leader": STEP[p]["leader"], "stance": s} for p, s in stances], "round": 1, "ripe": ripe}


class LifeHost(HandHost):
    """A project of four parties with one goal done long ago and goals of our own at the Orkmaster: each is `talk` (its leaders talk it over), `decided` with a wait, or `sections`; `ideas.add` makes the goal that was written, in Talk, at once."""

    def __init__(self):
        super().__init__(bare=True)
        self.nodes = [node("old", "tech", "An old goal", "history", state="done", seen="2026-10-18T10:00:00")]
        self.needs = []

    def put(self, slug, title, state="talk", element="dust", party="design", **more):
        self.nodes = [n for n in self.nodes if n["slug"] != slug]
        self.nodes.append(node(slug, party, title, "table", state=state, element=element, **more))
        return self.bump({})

    def mine(self, slug):
        return next(n for n in self.nodes if n["slug"] == slug)

    def change(self, slug, **more):
        self.mine(slug).update(more)
        return self.bump({})

    def handle(self, name, a):
        if name == "ideas.add":
            self.log.append((name, a))
            self.added.append(a)
            element = a.get("element") or "ice"
            self.nodes.append(node("new-goal", a.get("party") or "design", a["text"][:40], "table", state="talk", element=element, back=back()))
            return self.bump({"slug": "new-goal", "queue": "now", "element": element, "route": ["design", "tech"]})
        if name in ("ideas.confirm", "ideas.route_set"):
            self.log.append((name, a))
            return self.bump({"ok": True, "route": a.get("route")}) if name != "ideas.route_set" else {"route": [STEP[p] for p in a["route"]], "cost": {"calls": 2}, "short": False, "offer": []}
        return super().handle(name, a)


def open_life(gui, width="wide", host=None):
    pg, host, log = open_hand(gui, host=host or LifeHost(), width=width)
    pg.locator(".hand :is(.hand-plus, [data-blank-deck])").wait_for(timeout=WAIT_MS)
    return pg, host, log


# -- the + card turned into the card of the text (§6.1) ---------------------------------------------------------------------------------------

def test_the_plus_card_turns_over_into_a_card_with_the_field_focused_in_the_press_its_rune_large_and_the_five_on_a_press_of_it(gui):
    pg, host, log = open_life(gui)
    try:
        pg.evaluate("""() => { window.__atClick = []; document.addEventListener('click', () => window.__atClick.push(document.activeElement && document.activeElement.tagName), false); }""")
        pg.locator(".hand :is(.hand-plus, [data-blank-deck])").click(position={"x": 8, "y": 60})
        assert pg.evaluate("() => window.__atClick[0]") in ("TEXTAREA", "INPUT"), "the focus was given inside the press itself (on iOS a keyboard rises only for that)"
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('hand-field__text')", timeout=WAIT_MS)
        assert pg.locator(".hand-field__proxy").count() == 0, "the field the press focused is gone when the real one has the focus"
        pg.wait_for_function("() => document.querySelector('.hand-field__card').getAnimations().every((a) => a.playState === 'finished')", timeout=WAIT_MS)
        box = pg.locator(".hand-field__card").bounding_box()
        assert abs(box["width"] / box["height"] - 5 / 7) < 0.02, f"a card, 5 : 7: {box}"
        rune = field.locator(".hand-field__rune")
        top = field.locator(".corner--top").bounding_box()
        assert rune.count() == 1 and abs(rune.bounding_box()["x"] - box["x"]) <= 16 and abs(rune.bounding_box()["y"] - top["y"]) <= 8, "its rune is the card's top left corner, a button (spec 150 F.1)"
        assert rune.locator(".ork-elem").count() == 1 and rune.get_attribute("aria-expanded") == "false"
        assert rune.get_attribute("aria-label").startswith("Its rune: ") or rune.get_attribute("aria-label") == "Its rune: none yet, choose one"
        assert field.locator(".hand-field__runes").count() == 0, "the five stand in a row only when the rune is pressed"
        assert field.locator("[data-corner=go]").count() == 1 and field.get_by_role("textbox", name="Write a goal").count() == 1      # *Now or Later* is a corner (spec 168 D2)
        assert field.evaluate("e => getComputedStyle(e.querySelector('textarea')).fontFamily").lower().find("pixel") < 0, "the person's words are never in the pixel face"
        shot(pg, "field-card")
        rune.click()
        group = pg.locator(".hand-dealt[data-open=rune]")
        group.wait_for(timeout=WAIT_MS)
        assert rune.get_attribute("aria-expanded") == "true" and group.get_by_role("menuitemradio").count() == 5, "the five dealt to the hand (spec 168 D2)"
        group.get_by_role("menuitemradio", name="Rune 4").click(position={"x": 20, "y": 30})
        assert pg.locator(".hand-dealt").count() == 0, "a rune chosen puts the row back"
        assert rune.get_attribute("aria-label") == "Its rune: Rune 4, change it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_card_is_there_with_no_turn_and_no_growth_and_no_copy_in_the_air(gui):
    pg, host, log = open_life(gui)
    try:
        pg.emulate_media(reduced_motion="reduce")
        pg.locator(".hand :is(.hand-plus, [data-blank-deck])").click(position={"x": 8, "y": 60})
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        assert field.evaluate("e => e.getAnimations().length") == 0, "no growth"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        assert pg.locator(".hand-ghost").count() == 0, "no turn back"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- sent: it turns back and goes face down to the Orkmaster (§6.2) --------------------------------------------------------------------------


# -- talked over, face down (§6.3) ---------------------------------------------------------------------------------------------------------


def test_a_held_goals_decision_card_in_the_hand_says_start_and_a_decision_with_no_wait_says_confirm_and_start(gui):
    pg, host, log = open_life(gui)
    try:
        host.put("timer", "Round timer shows on every phone", "decided", "ice", back=back(heard=["design", "tech"], ripe=ripe(0, 240, held=True)))
        row = need("decision", "design", "timer", "Round timer shows on every phone", "Why: One clock.\n\n1. Tech counts.", number=201, confirmed=False, error="")
        host.needs = [row]
        host.bump({})
        pg.locator('.hand-card[data-kind="decision"]').wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="decision"]').click(position={"x": 10, "y": 20})
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        assert lifted.get_by_role("button", name="Start", exact=True).count() == 1 and lifted.get_by_role("button", name="Confirm and start").count() == 0
        lifted.get_by_role("button", name="Start", exact=True).click()
        assert _sent(pg, host, ("ideas.confirm", {"idea": "timer"}))
        pg.keyboard.press("Escape")
        host.put("timer", "Round timer shows on every phone", "decided", "ice")                    # no wait: the card as it always was
        host.needs = [row]
        host.bump({})
        pg.locator('.hand-card[data-kind="decision"]').click(position={"x": 10, "y": 20})
        assert pg.locator(".hand-lifted").get_by_role("button", name="Confirm and start").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)
