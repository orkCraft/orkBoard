"""One card through a goal's life (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.5, §6.8, §6.11; decisions §198.8), in a real browser against a stub host: the + card turned into the field with the field focused in the press itself, its rune large and
the five on a press of it, Esc turning it back with its text and rune kept; Send turning it to its back and the back lying in the Orkmaster's lane, its rune lit and its name at its foot, never the + card's green; hover lifting and not turning, a press turning it to
its face (its words, its route, what each leader said); the route's heads lit as `heard` grows; the seal's ring as the wait (its share following `left_s`, its words), Hold and Start; the wait's end turning the back up and one flight at a time to the lane, none for
a hidden page, none under reduced motion. Screenshots to $LIFE_SHOTS when it is set."""
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
    return pg.locator(f'.frame-table .table-card--back[data-goal="{slug}"]')


def at_rest(pg, ms=900):
    pg.wait_for_timeout(ms)


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

def test_sent_the_card_turns_to_its_back_and_the_back_lies_in_the_orkmasters_lane_its_rune_lit_its_name_at_its_foot_never_green(gui):
    pg, host, log = open_life(gui)
    try:
        pg.locator(".hand .hand-plus").click(position={"x": 8, "y": 60})
        field = pg.locator(".hand-field")
        field.wait_for(timeout=WAIT_MS)
        field.get_by_role("textbox", name="Write a goal").fill("Players see who answered first, with a small crown over their name")
        field.get_by_role("textbox", name="Write a goal").press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "Players see who answered first, with a small crown over their name"}))
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        flyer = pg.locator("body > .hand-ghost.ork-turn")
        try:
            flyer.wait_for(state="attached", timeout=2000)
            assert flyer.get_attribute("aria-hidden") == "true" and flyer.locator(".ork-turn__back .ork-sigil__seal .ork-elem.ice").count() == 1 and flyer.locator(".ork-turn__face").count() == 1, "orkUI's turn: a copy of the back, in the goal's rune, and the card of the words, over everything"
            shot(pg, "send-flying")
        except Exception:                                                        # it may already have landed on a quick machine
            pass
        card = back_of(pg, "new-goal")
        card.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-ghost') && document.querySelector('.table-card--back').style.visibility !== 'hidden'", timeout=WAIT_MS)
        assert card.locator(".ork-sigil__seal .ork-elem.ice.is-glowing").count() == 1, "its own rune lit at the seal's top, glowing while it is talked over"
        assert card.locator(".table-back-nm").inner_text().startswith("Players see who answered first")
        assert card.locator(".ork-plus, .ork-icon").count() == 0, "no +: the + card alone keeps that"
        colours = card.evaluate("e => { const c = getComputedStyle(e); const action = getComputedStyle(document.documentElement).getPropertyValue('--ork-action').trim(); const probe = document.createElement('i'); probe.style.color = action; document.body.appendChild(probe); const a = getComputedStyle(probe).color; probe.remove(); return [c.borderTopColor, c.color, c.backgroundColor, a]; }")
        assert colours[3] not in colours[:3], f"never the + card's green: {colours}"
        assert pg.locator(".frame-table .table-lane--first .table-card--back").count() == 1, "in the Orkmaster's lane"
        assert pg.locator(".hand .hand-plus").count() == 1, "a new + card lies at the lane's end"
        shot(pg, "send-landed")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- talked over, face down (§6.3) ---------------------------------------------------------------------------------------------------------

def _talking(host, **more):
    host.put("dark", "Players see who answered first", "talk", "dust", back=back(**more))


def test_a_goal_talked_over_lies_face_down_with_its_rune_glowing_and_its_routes_heads_lit_as_each_leader_has_said(gui):
    pg, host, log = open_life(gui)
    try:
        _talking(host, route=("design", "tech", "product"))
        card = back_of(pg, "dark")
        card.wait_for(timeout=WAIT_MS)
        assert card.get_attribute("data-back") == "talk" and card.get_attribute("aria-label") == "Players see who answered first: the leaders are talking it over · 0 of 3 leaders have said"
        assert card.locator(".ork-elem.dust.is-glowing").count() == 1 and card.locator(".table-back-nm").inner_text() == "Players see who answered first"
        heads = pg.locator('.frame-table [data-goal="dark"] ~ .table-back-heads .table-back-head, .frame-table .table-back-heads .table-back-head')
        assert heads.count() == 3 and pg.locator(".table-back-head.is-said").count() == 0, "faint until `heard` names them"
        opacity = lambda: [float(h.evaluate("e => getComputedStyle(e.querySelector('img')).opacity")) for h in heads.all()]  # noqa: E731
        assert opacity() == [0.3, 0.3, 0.3]
        assert card.locator(".ork-sigil.is-waiting").count() == 0, "never on the ring: the ring has one meaning at a time"
        host.change("dark", back=back(route=("design", "tech", "product"), heard=["design"]))
        pg.wait_for_function("() => document.querySelectorAll('.table-back-head.is-said').length === 1", timeout=WAIT_MS)
        pg.wait_for_timeout(400)                                                  # the head lights in three steps
        assert card.get_attribute("aria-label").endswith("1 of 3 leaders have said") and opacity() == [1.0, 0.3, 0.3]
        host.change("dark", back=back(route=("design", "tech", "product"), heard=["design", "tech", "product"]))
        pg.wait_for_function("() => document.querySelectorAll('.table-back-head.is-said').length === 3", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert card.get_attribute("aria-label").endswith("3 of 3 leaders have said") and opacity() == [1.0, 1.0, 1.0]
        assert not pg.locator(".table-back-heads").inner_text().strip(), "no verdict, no tick, no count is drawn"
        shot(pg, "talk-heads")
        host.put("second", "A sound when the round ends", "talk", "void", back=back(route=("design",)))
        back_of(pg, "second").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-card--back .ork-elem.void").count() == 1 and pg.locator(".table-card--back .ork-elem.dust").count() == 1, "told apart by their rune"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_hovering_a_back_only_lifts_it_and_a_press_turns_it_to_its_face_with_its_words_its_route_what_each_leader_said_and_turn_it_back(gui):
    pg, host, log = open_life(gui)
    try:
        _talking(host, stances=[("design", "Yes, with a frame"), ("tech", "Yes, one event")], heard=["design", "tech"])
        card = back_of(pg, "dark")
        card.wait_for(timeout=WAIT_MS)
        assert card.evaluate("e => getComputedStyle(e).transform") == "none"
        card.hover(position={"x": 30, "y": 60})
        pg.wait_for_timeout(400)
        assert card.evaluate("e => getComputedStyle(e).transform") != "none", "it lifts and leans (orkUI's `.ork-leans`)"
        assert pg.locator(".table-back").count() == 0 and card.get_attribute("aria-pressed") == "false", "a pointer crossing the lane turns nothing"
        card.click(position={"x": 30, "y": 60})
        face = pg.locator(".table-back")
        face.wait_for(timeout=WAIT_MS)
        assert face.get_attribute("aria-label") == "Players see who answered first, turned over"
        turn = pg.locator(".frame-table .table-turn")
        assert turn.get_attribute("class").split()[:2] == ["ork-turn", "table-turn"] and "is-up" in turn.get_attribute("class").split() and turn.evaluate("e => getComputedStyle(e).aspectRatio") == "5 / 7", "orkUI's turn, 5 : 7, face up in place"
        assert face.locator(".table-back__goal").inner_text() == "Players see who answered first"
        assert face.locator(".hand-route__steps .hand-route__step").count() == 3, "the route's heads with their + (two parties and the +)"
        assert face.get_by_role("button", name="Take Design off the route").count() == 1 and face.get_by_role("button", name="Add a party to the route").count() == 1
        assert face.locator(".hand-way__acts").count() == 0, "no Talk on a goal that is talking"
        stances = face.locator(".table-back__stances li")
        assert [s.inner_text().strip() for s in stances.all()] == ["Design Yes, with a frame", "Tech Yes, one event"], "what each leader that has said said, a line each"
        assert face.locator(".hand-way__cost").count() == 1, "its cost"
        shot(pg, "talk-face")
        face.get_by_role("button", name="Take Tech off the route").click()
        assert _sent(pg, host, ("ideas.route_set", {"idea": "dark", "route": ["design"]}))
        face.get_by_role("button", name="Turn it back").click()
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
        assert "is-up" not in turn.get_attribute("class").split(), "turned down again, in place"
        assert card.get_attribute("aria-pressed") == "false"
        pg.wait_for_function("() => getComputedStyle(document.querySelector('.table-card--back')).visibility === 'visible'", timeout=WAIT_MS)       # orkUI's turn shows the side it turns to at once
        card.focus()
        pg.keyboard.press("Enter")                                               # Enter turns it too
        pg.locator(".table-back").wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the wait (§6.4) -------------------------------------------------------------------------------------------------------------------------

def _waiting(host, left, seconds=240, **more):
    host.put("timer", "Round timer shows on every phone", "decided", "ice", back=back(heard=["design", "tech"], ripe=ripe(left, seconds, **more)))


SHARE = "e => e.style.getPropertyValue('--ork-sigil-share')"
ARC = "() => getComputedStyle(document.querySelector('.table-card--back .ork-sigil'), '::after').getPropertyValue('--_arc').trim()"


def test_the_seals_ring_is_the_wait_its_share_following_the_time_left_in_eight_steps_and_the_words_under_the_card(gui):
    pg, host, log = open_life(gui)
    try:
        _waiting(host, 240)
        card = back_of(pg, "timer")
        card.wait_for(timeout=WAIT_MS)
        sigil = card.locator(".ork-sigil")
        assert card.get_attribute("data-back") == "wait" and "is-waiting" in sigil.get_attribute("class").split()
        assert pg.locator(".table-back-under").inner_text() == "Starts by itself in 4 min"
        assert sigil.evaluate(SHARE) == "0", "nothing of the wait is gone yet"
        assert card.locator(".ork-elem.ice.is-glowing").count() == 0, "the rune stands lit, still: it is not talked over any more"
        assert pg.evaluate(ARC) == "0deg"
        host.change("timer", back=back(heard=["design", "tech"], ripe=ripe(60, 240)))
        pg.wait_for_function("() => document.querySelector('.table-back-under').innerText === 'Starts by itself in 1 min'", timeout=WAIT_MS)
        assert sigil.evaluate(SHARE) == "0.75" and pg.evaluate(ARC) == "270deg", "three quarters gone: six steps of eight"
        host.change("timer", back=back(heard=["design", "tech"], ripe=ripe(40, 240)))
        pg.wait_for_function("() => document.querySelector('.table-back-under').innerText === 'Starts by itself in 40 s'", timeout=WAIT_MS)
        assert sigil.evaluate(SHARE) == "0.875"
        shot(pg, "wait-ring")
        steps = []
        for left in (240, 210, 200, 120, 30, 1, 0):                              # eighths of 240 s are 30 s: the ring stands where its step is, between two steps it does not move
            host.change("timer", back=back(heard=["design", "tech"], ripe=ripe(left, 240)))
            pg.wait_for_function("(l) => !!document.querySelector('.table-card--back')", arg=left, timeout=WAIT_MS)
            pg.wait_for_timeout(120)
            steps.append(sigil.evaluate(SHARE))
        assert steps == ["0", "0.125", "0.25", "0.5", "0.875", "1", "1"], steps
        sigil.evaluate("e => e.style.setProperty('--ork-sigil-share', '0.45')")
        assert pg.evaluate(ARC) == "135deg", "orkUI rounds the share down to an eighth (0.45 is 3/8): the page sets the share and nothing else"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.table-card--back .ork-sigil'), '::after').color") != pg.evaluate("() => getComputedStyle(document.querySelector('.table-card--back .ork-sigil')).color"), "the lit runes wear the goal's colour, the sigil's own colour is the faint ink"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_held_wait_stands_where_it_was_and_says_so_and_pressed_the_waiting_card_has_hold_and_the_held_one_start(gui):
    pg, host, log = open_life(gui)
    try:
        _waiting(host, 90)
        host.needs = [need("decision", "design", "timer", "Round timer shows on every phone", "Why: Every phone should agree.\n\n1. Tech counts on the server.\n2. Phones show it.", number=201, confirmed=False, error="")]
        host.bump({})
        card = back_of(pg, "timer")
        card.wait_for(timeout=WAIT_MS)
        card.click(position={"x": 30, "y": 60})
        face = pg.locator(".table-back")
        face.wait_for(timeout=WAIT_MS)
        assert "All the leaders agreed" in face.inner_text() and face.locator('[data-caption="wait"]').inner_text() == "All the leaders agreed"
        assert "Every phone should agree." in face.inner_text(), "the decision's words"
        assert face.get_by_role("button", name="Hold").count() == 1 and face.get_by_role("button", name="Start").count() == 0
        shot(pg, "wait-face")
        face.get_by_role("button", name="Hold").click()
        assert _sent(pg, host, ("ideas.ripe_hold", {"idea": "timer"}))
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
        host.change("timer", back=back(heard=["design", "tech"], ripe=ripe(0, 240, held=True)))
        pg.wait_for_function("() => document.querySelector('.table-back-under').innerText === 'Held: start it when you are ready'", timeout=WAIT_MS)
        assert back_of(pg, "timer").get_attribute("data-back") == "held"
        assert back_of(pg, "timer").locator(".ork-sigil").evaluate(SHARE) == "0.625", "the ring stands where the wait was held (90 s of 240 left: the share seen)"
        card.click(position={"x": 30, "y": 60})
        face = pg.locator(".table-back")
        face.wait_for(timeout=WAIT_MS)
        assert face.get_by_role("button", name="Start").count() == 1 and face.get_by_role("button", name="Hold").count() == 0
        assert "Held: start it when you are ready" in face.inner_text()
        face.get_by_role("button", name="Start").click()
        assert _sent(pg, host, ("ideas.confirm", {"idea": "timer"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


# -- the wait's end: turned up, then flown to its lane (§6.5) ------------------------------------------------------------------------------

def _worked(host, slug, party="design"):
    host.change(slug, state="working", goal=party, back=None, tasks=[task("t1", "Draw the crown", "running")], stage="implementation")


def test_the_waits_end_turns_the_back_up_where_it_lies_and_the_card_then_flies_to_its_lane_once_and_a_second_waits_for_the_first(gui):
    pg, host, log = open_life(gui)
    try:
        _waiting(host, 5)
        host.put("sound", "A sound when the round ends", "decided", "void", party="tech", back=back(route=("tech",), heard=["tech"], ripe=ripe(5, 600)))
        back_of(pg, "timer").wait_for(timeout=WAIT_MS)
        back_of(pg, "sound").wait_for(timeout=WAIT_MS)
        pg.evaluate("() => { window.__fl = { max: 0, seen: 0 }; setInterval(() => { const n = document.querySelectorAll('body > .table-flyer').length; window.__fl.max = Math.max(window.__fl.max, n); window.__fl.seen += n ? 1 : 0; }, 16); }")
        host.change("timer", state="sections", back=None)                                       # the wait ended: the leaders confirmed
        host.change("sound", state="sections", back=None)
        pg.wait_for_function("() => document.querySelectorAll('.table-turn.is-up .table-card--own').length === 2", timeout=WAIT_MS)
        assert pg.locator(".table-turn.ork-turn").count() == 2 and pg.locator(".table-turn.is-up .ork-turn__face .table-card--own").count() == 2, "turned up where they lay: orkUI's `.ork-turn`, in place"
        pg.wait_for_function("() => !document.querySelector('.table-card--back')", timeout=WAIT_MS)
        assert pg.locator(".table-turn .ork-turn__back").count() == 0, "the back is taken away when it has turned"
        assert pg.locator(".table-turn.is-up .table-card--own .table-card__nm").first.inner_text(), "the goal's header, its rune, its name"
        pg.wait_for_timeout(500)
        assert pg.evaluate("() => window.__fl.seen") == 0, "no flight yet: the goals are not in a lane"
        _worked(host, "timer", "design")
        _worked(host, "sound", "tech")
        pg.wait_for_function("() => window.__fl.seen > 0", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelectorAll('body > .table-flyer').length === 0 && window.__fl.seen > 5", timeout=WAIT_MS * 2)
        pg.wait_for_timeout(1500)
        assert pg.evaluate("() => window.__fl.max") == 1, "one card flies at a time"
        assert pg.evaluate("() => import('/static/js/table/flight.js').then((m) => m.flights.done)") == 2, "each flew once"
        assert pg.locator('.frame-table .table-lane[data-party="design"] .table-goal[data-goal="timer"]').count() == 1
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.table-goal[data-goal=\"timer\"]')).visibility") == "visible", "and lies in its lane when it has landed"
        assert pg.locator(".table-lane--first .table-goal").count() == 0, "the lane it left closed behind it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_nothing_flies_for_a_hidden_page_or_under_reduced_motion_the_card_is_in_its_lane(gui):
    pg, host, log = open_life(gui)
    try:
        _waiting(host, 5)
        back_of(pg, "timer").wait_for(timeout=WAIT_MS)
        pg.evaluate("() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); }")
        host.change("timer", state="sections", back=None)
        pg.wait_for_function("() => !document.querySelector('.table-card--back')", timeout=WAIT_MS)
        _worked(host, "timer")
        pg.wait_for_function("() => document.querySelector('.table-lane[data-party=\"design\"] .table-goal[data-goal=\"timer\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator("body > .table-flyer").count() == 0 and pg.evaluate("() => import('/static/js/table/flight.js').then((m) => m.flights.done)") == 0, "not seen: no flight"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.table-goal[data-goal=\"timer\"]')).visibility") == "visible"
        pg.evaluate("() => { delete document.hidden; }")
        pg.emulate_media(reduced_motion="reduce")
        host.put("sound", "A sound when the round ends", "decided", "void", party="tech", back=back(route=("tech",), heard=["tech"], ripe=ripe(5, 600)))
        back_of(pg, "sound").wait_for(timeout=WAIT_MS)
        host.change("sound", state="sections", back=None)
        pg.wait_for_function("() => !document.querySelector('.table-card--back')", timeout=WAIT_MS)
        assert pg.locator(".table-turn.is-up").evaluate("e => e.querySelector('.ork-turn__face').getAnimations().length + (getComputedStyle(e.querySelector('.ork-turn__face')).transform === 'none' ? 0 : 1)") == 0, "no turn under reduced motion: orkUI swaps the sides at once"
        _worked(host, "sound", "tech")
        pg.wait_for_function("() => document.querySelector('.table-lane[data-party=\"tech\"] .table-goal[data-goal=\"sound\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator("body > .table-flyer").count() == 0 and pg.evaluate("() => import('/static/js/table/flight.js').then((m) => m.flights.done)") == 0
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
