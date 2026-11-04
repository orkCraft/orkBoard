"""One card through a goal's life (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.5, §6.8, §6.11; decisions §198.8), in a real browser against a stub host: the + card turned into the field with the field focused in the press itself, its rune large and
the five on a press of it, Esc turning it back with its text and rune kept; Send turning it to its back and the back lying in the Orkmaster's column (spec 128 B.3: face down and sideways, its rune lit, no name, never the + card's green); a held goal's decision card in the hand;
at the narrow width the goal talked over a token with its rune glowing, and on a phone the field and the menu's row. What lay in the Orkmaster's lane at the wide width (the back's face, the route's heads, the wait as the seal's ring, the turn up and the flight to the lane) is the column's
now: tests/test_column_browser.py. Screenshots to $LIFE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
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
        if name in ("ideas.ripe_hold", "ideas.confirm", "ideas.route_set"):
            self.log.append((name, a))
            return self.bump({"ok": True, "route": a.get("route")}) if name != "ideas.route_set" else {"route": [STEP[p] for p in a["route"]], "cost": {"calls": 2}, "short": False, "offer": []}
        return super().handle(name, a)


def open_life(gui, width="wide", host=None):
    pg, host, log = open_hand(gui, host=host or LifeHost(), width=width)
    pg.locator(".hand .hand-plus").wait_for(timeout=WAIT_MS)
    return pg, host, log


def back_of(pg, slug):
    """A goal's card face down in the Orkmaster's column (spec 128 B.3: the card of In analysis, sideways, with no name)."""
    return pg.locator(f'.frame-column .col-card--down[data-goal="{slug}"]')


# -- the + card turned into the card of the text (§6.1) ---------------------------------------------------------------------------------------

def test_the_plus_card_turns_over_into_a_card_with_the_field_focused_in_the_press_its_rune_large_and_the_five_on_a_press_of_it(gui):
    pg, host, log = open_life(gui)
    try:
        pg.evaluate("""() => { window.__atClick = []; document.addEventListener('click', () => window.__atClick.push(document.activeElement && document.activeElement.tagName), false); }""")
        pg.locator(".hand .hand-plus").click(position={"x": 8, "y": 60})
        assert pg.evaluate("() => window.__atClick[0]") in ("TEXTAREA", "INPUT"), "the focus was given inside the press itself (on iOS a keyboard rises only for that)"
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('hand-field__text')", timeout=WAIT_MS)
        assert pg.locator(".hand-field__proxy").count() == 0, "the field the press focused is gone when the real one has the focus"
        pg.wait_for_function("() => document.querySelector('.hand-field').getAnimations().length === 0", timeout=WAIT_MS)
        box = field.bounding_box()
        assert abs(box["width"] / box["height"] - 5 / 7) < 0.02, f"a card, 5 : 7: {box}"
        rune = field.locator(".hand-field__rune")
        top = field.locator(".hand-field__top").bounding_box()
        assert rune.count() == 1 and abs(rune.bounding_box()["x"] - box["x"]) <= 12 and abs(rune.bounding_box()["y"] - top["y"]) <= 2, "its rune large at its top left, where a card's element stands"
        assert rune.locator(".ork-elem.big").count() == 1 and rune.get_attribute("aria-expanded") == "false"
        assert rune.get_attribute("aria-label").startswith("Its rune: ") or rune.get_attribute("aria-label") == "Its rune: none yet, choose one"
        assert field.locator(".hand-field__runes").count() == 0, "the five stand in a row only when the rune is pressed"
        assert field.get_by_role("button", name="Send").count() == 1 and field.get_by_role("textbox", name="Write a goal").count() == 1
        assert field.evaluate("e => getComputedStyle(e.querySelector('textarea')).fontFamily").lower().find("pixel") < 0, "the person's words are never in the pixel face"
        shot(pg, "field-card")
        rune.click()
        group = field.get_by_role("radiogroup", name="Its rune")
        group.wait_for(timeout=WAIT_MS)
        assert rune.get_attribute("aria-expanded") == "true" and group.get_by_role("radio").count() == 5
        assert group.get_by_role("radio").first.bounding_box()["width"] >= 39, "40 px each"
        group.get_by_role("radio", name="Rune 4").click()
        assert field.locator(".hand-field__runes").count() == 0, "a rune chosen closes the row"
        assert rune.get_attribute("aria-label") == "Its rune: Rune 4, change it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_esc_or_a_press_away_turns_the_card_back_into_the_plus_card_keeping_its_text_and_rune(gui):
    pg, host, log = open_life(gui)
    try:
        plus = pg.locator(".hand .hand-plus")
        plus.click(position={"x": 8, "y": 60})
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        field.get_by_role("textbox", name="Write a goal").fill("Players see who answered first")
        field.locator(".hand-field__rune").click()
        field.get_by_role("radio", name="Rune 5").click()
        pg.keyboard.press("Escape")                                              # the focus is on the rune button, not in the text: Esc is the card's
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        assert pg.locator(".hand-ghost").count() >= 0                            # the copy that turns back may be in the air a moment
        pg.wait_for_function("() => !document.querySelector('.hand-ghost') && getComputedStyle(document.querySelector('.hand .hand-plus')).visibility === 'visible'", timeout=WAIT_MS)
        plus.click(position={"x": 8, "y": 60})
        field.wait_for(timeout=WAIT_MS)
        assert field.get_by_role("textbox", name="Write a goal").input_value() == "Players see who answered first"
        assert field.locator(".hand-field__rune").get_attribute("aria-label") == "Its rune: Rune 5, change it", "its rune kept"
        pg.mouse.click(640, 120)                                                 # a press away
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        assert not host.added, "nothing was sent"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_card_is_there_with_no_turn_and_no_growth_and_no_copy_in_the_air(gui):
    pg, host, log = open_life(gui)
    try:
        pg.emulate_media(reduced_motion="reduce")
        pg.locator(".hand .hand-plus").click(position={"x": 8, "y": 60})
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

def test_sent_the_card_turns_to_its_back_and_the_back_lies_in_the_orkmasters_column_its_rune_lit_and_no_name_never_green(gui):
    """Spec 128 B.3: the goal sent lies face down and sideways in the column's In analysis, its rune lit at the seal's top, glowing while it is talked over, with no name (the name is on its other side)."""
    pg, host, log = open_life(gui)
    try:
        pg.locator(".hand .hand-plus").click(position={"x": 8, "y": 60})
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        field.get_by_role("textbox", name="Write a goal").fill("Players see who answered first, with a small crown over their name")
        field.get_by_role("textbox", name="Write a goal").press("Enter")
        assert _sent(pg, host, ("ideas.add", {"match": True, "text": "Players see who answered first, with a small crown over their name"}))
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        card = pg.locator('.frame-column .col-card--down[data-goal="new-goal"]')
        card.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-ghost')", timeout=WAIT_MS)
        assert card.locator(".ork-sigil__seal .ork-elem.ice.is-glowing").count() == 1, "its own rune lit at the seal's top, glowing while it is talked over"
        assert card.inner_text().strip() == "" and pg.locator(".table-back-nm").count() == 0, "no name on the face-down card"
        assert card.locator(".ork-plus, .ork-icon").count() == 0, "no +: the + card alone keeps that"
        colours = card.evaluate("e => { const c = getComputedStyle(e); const action = getComputedStyle(document.documentElement).getPropertyValue('--ork-action').trim(); const probe = document.createElement('i'); probe.style.color = action; document.body.appendChild(probe); const a = getComputedStyle(probe).color; probe.remove(); return [c.borderTopColor, c.color, c.backgroundColor, a]; }")
        assert colours[3] not in colours[:3], f"never the + card's green: {colours}"
        assert pg.locator('.frame-column .col-sec[data-pile="analysis"] .col-card').count() == 1 and pg.locator(".frame-table .table-card--back").count() == 0, "in the column, not the Orkmaster's lane"
        assert pg.locator(".hand .hand-plus").count() == 1, "a new + card lies at the lane's end"
        shot(pg, "send-landed")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- talked over, face down (§6.3) ---------------------------------------------------------------------------------------------------------

def _talking(host, **more):
    host.put("dark", "Players see who answered first", "talk", "dust", back=back(**more))


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


@pytest.mark.parametrize("width", ["narrow"])
def test_at_the_narrow_width_a_goal_talked_over_is_one_token_its_rune_glowing(gui, width):
    pg, host, log = open_life(gui, width=width)
    try:
        _talking(host)
        pg.locator('.frame-table .table-token[data-goal="dark"] .ork-elem.dust.is-glowing').wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_the_plus_card_turns_into_a_field_the_screens_width_less_its_gutters_with_the_focus_given_in_the_press(gui):
    pg, host, log = open_life(gui, width="phone")
    try:
        pg.locator(".up-plus .hand-plus").wait_for(timeout=WAIT_MS)
        pg.evaluate("""() => { window.__atClick = []; document.addEventListener('click', () => window.__atClick.push(document.activeElement && document.activeElement.tagName), false); }""")
        pg.locator(".up-plus .hand-plus").click()
        assert pg.evaluate("() => window.__atClick[0]") in ("TEXTAREA", "INPUT"), "the phone's keyboard rises for a focus given inside the press"
        field = pg.locator(".up-field .hand-field")
        field.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('hand-field__text')", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.hand-field').getAnimations().length === 0", timeout=WAIT_MS)
        box = field.bounding_box()
        assert abs(box["width"] - (pg.viewport_size["width"] - 16)) <= 2, f"the screen's width less the gutters: {box}"
        assert field.locator(".hand-field__rune").count() == 1 and field.locator(".hand-field__runes").count() == 0
        narrow.no_sideways(pg)
        shot(pg, "phone-field")
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_the_menus_row_of_a_goal_talked_over_shows_its_rune_glowing_and_a_goal_that_waits_does_not(gui):
    pg, host, log = open_life(gui, width="phone")
    try:
        pg.locator(".up-crown").wait_for(timeout=WAIT_MS)
        _talking(host)
        host.put("timer", "Round timer shows on every phone", "decided", "ice", back=back(heard=["design", "tech"], ripe=ripe(60, 240)))
        pg.locator(".up-crown").click()
        menu = pg.locator(".up-menu")
        menu.wait_for(timeout=WAIT_MS)
        assert menu.locator('.up-grow[data-goal="dark"] .ork-elem.dust.is-glowing').count() == 1, "the back's rune glowing in the menu's row"
        assert menu.locator('.up-grow[data-goal="timer"] .ork-elem.ice').count() == 1 and menu.locator('.up-grow[data-goal="timer"] .ork-elem.is-glowing').count() == 0
        shot(pg, "phone-menu-glowing")
    finally:
        pg.close()
    assert not log, "\n".join(log)
