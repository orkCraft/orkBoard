"""Spec 147 part E and the laying flight of D.2 (docs/specs/147-one-card-four-corners.md, decisions §251.3, §251.7, §70), in a real browser against a stub host: a goal that passes from To review to At work between two snapshots turns its back face up
(orkUI's `.ork-turn`, `data-fly="start"`) and stands at At work, then a card of it flies to the strip of each party doing it and folds into it (`data-fly="deal"`), one motion that travels and ends with no copy in the air; none under reduced motion; two starts
in one snapshot deal the first and lay the rest (one flight). A goal that asks the person has its card come to the hand from its back in To review (`data-fly="hand"`: the back turns up on its way). A goal laid from the + card turns face down, its rune lights in the
middle of its back and it flies small into the Orkmaster's fan (`data-fly="lay"`), where the fan ends with one more back; nothing flies under reduced motion."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_card_life_browser import LifeHost, open_life  # noqa: E402
from tests.test_column_browser import ColumnHost, back, open_column, ripe  # noqa: E402
from tests.test_hand_desktop_browser import need, node, open_hand, task  # noqa: E402

pytestmark = pytest.mark.browser

# every copy that flies is `[data-fly]` on the body: this keeps a record of the ones that came, and of the ones that were put on their face
WATCH = """() => {
  window.__fly = [];
  new MutationObserver((ms) => {
    for (const m of ms) {
      for (const n of m.addedNodes) if (n.dataset && n.dataset.fly) window.__fly.push({ fly: n.dataset.fly, turn: n.classList.contains('ork-turn'), up: n.classList.contains('is-up'), ups: n.classList.contains('is-up') ? 1 : 0, el: n });
      const r = m.type === 'attributes' && m.target.dataset && m.target.dataset.fly ? window.__fly.find((x) => x.el === m.target) : null;
      if (r) { const up = m.target.classList.contains('is-up'); if (up && !r.up) r.ups++; r.up = up; }
    }
  }).observe(document.body, { childList: true, attributes: true, attributeFilter: ['class'], subtree: true });
}"""
KINDS = "() => window.__fly.map((x) => x.fly)"
IN_AIR = "() => document.querySelectorAll('.table-flyer, .hand-ghost').length"


def node_of(host, slug):
    return next(n for n in host.nodes if n["slug"] == slug)


def start(host, slug, *tasks):
    """The goal's wait is over: its first task runs, it is at work."""
    node_of(host, slug).update(state="working", stage="implementation", back=back(ripe=ripe(0, by="leaders")), tasks=list(tasks))


def settled(pg):
    pg.wait_for_function(f"({IN_AIR})() === 0", timeout=WAIT_MS * 2)


def test_a_start_turns_the_back_up_and_flies_one_card_per_strip_then_nothing_is_in_the_air(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="timer"][data-pile="review"]', timeout=WAIT_MS)
        pg.evaluate(WATCH)
        start(host, "timer", task("t1", "Draw the bar", "running"))
        host.bump({})
        pg.wait_for_function("() => window.__fly.some((x) => x.fly === 'deal')", timeout=WAIT_MS * 2)
        kinds = pg.evaluate(KINDS)
        strips = pg.locator('.table-board .table-goal[data-goal="timer"] .table-gstrip').count()
        assert strips >= 1 and kinds.count("start") == 1, kinds
        assert kinds.count("deal") == strips, ("a card flies to the strip of each party doing it", kinds, strips)
        turned = pg.evaluate("() => window.__fly.filter((x) => x.fly === 'start').map((x) => [x.turn, x.ups])")
        assert turned == [[True, 1]], "its back is orkUI's .ork-turn and is put on its face once"
        settled(pg)
        assert pg.locator('.col-card[data-goal="timer"]').evaluate("e => [e.dataset.pile, getComputedStyle(e).visibility, e.classList.contains('col-card--up')]") == ["work", "visible", True], "it stands at At work"
        assert pg.evaluate(KINDS).count("start") == 1 and pg.evaluate(KINDS).count("deal") == strips, "one motion, played once"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_start_flies_nothing_under_reduced_motion_and_the_card_stands_at_once(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="timer"][data-pile="review"]', timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        pg.evaluate(WATCH)
        start(host, "timer", task("t1", "Draw the bar", "running"))
        host.bump({})
        pg.wait_for_selector('.col-sec[data-pile="work"] .col-card[data-goal="timer"]', timeout=WAIT_MS)
        pg.wait_for_selector('.table-board .table-goal[data-goal="timer"] .table-gstrip', timeout=WAIT_MS)
        pg.wait_for_timeout(1200)
        assert pg.evaluate(KINDS) == [] and pg.evaluate(IN_AIR) == 0, "none under reduced motion"
        assert pg.locator('.col-card[data-goal="timer"]').evaluate("e => getComputedStyle(e).visibility") == "visible"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_two_starts_in_one_snapshot_deal_the_first_and_lay_the_rest(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="scoring"][data-pile="review"]', timeout=WAIT_MS)
        pg.evaluate(WATCH)
        start(host, "timer", task("t1", "Draw the bar", "running"))
        start(host, "scoring", task("s1", "Tidy it", "running"))
        host.bump({})
        pg.wait_for_function("() => window.__fly.some((x) => x.fly === 'deal')", timeout=WAIT_MS * 2)
        settled(pg)
        kinds = pg.evaluate(KINDS)
        assert kinds.count("start") == 1, ("one back is turned", kinds)
        assert kinds.count("deal") == pg.locator('.table-board .table-goal[data-goal="timer"] .table-gstrip').count(), ("the cards of one goal fly", kinds)
        pg.wait_for_selector('.col-sec[data-pile="work"] .col-card[data-goal="scoring"]', timeout=WAIT_MS)
        assert pg.locator('.col-card[data-goal="scoring"]').evaluate("e => [e.dataset.pile, getComputedStyle(e).visibility]") == ["work", "visible"], "the other is laid where it lies"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_start_into_a_lane_under_the_pointer_flies_no_card_to_it(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="timer"][data-pile="review"]', timeout=WAIT_MS)
        pg.evaluate(WATCH)
        start(host, "timer", task("t1", "Draw the bar", "running"))
        host.bump({})
        pg.wait_for_selector('.table-board .table-goal[data-goal="timer"] .table-gstrip', timeout=WAIT_MS)
        box = pg.locator('.table-board .table-lane[data-party="tech"]').bounding_box()
        pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] - 4)
        pg.wait_for_function("() => window.__fly.some((x) => x.fly === 'start')", timeout=WAIT_MS * 2)
        settled(pg)
        assert "deal" not in pg.evaluate(KINDS), "the lane under the pointer takes no card"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def asking_review(host, slug="ask1", title="Round timer on phones", party="tech"):
    """A goal whose spec is made, waiting in To review, that asks the person: its question is in the hand."""
    host.nodes = [n for n in host.nodes if n["slug"] != slug]
    asked = [{"ask": f"Which way for {title}?", "choices": ["This", "That"], "pick": None, "why": "", "by": None, "look": False}]
    host.nodes.append(node(slug, party, title, "table", state="ready", agreed=True, asks_you=True, element="ice", asked=asked, back=back(ripe=None)))
    host.needs.append(need("asks", party, slug, title, asked[0]["ask"], at="2026-10-20T09:30:00", asked=asked))


def test_a_goal_that_asks_you_has_its_card_come_to_the_hand_from_its_back_in_to_review(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="timer"][data-pile="review"]', timeout=WAIT_MS)
        pg.evaluate(WATCH)
        asking_review(host)
        host.bump({})
        pg.wait_for_selector('.col-card--deck[data-goal="ask1"].asks', timeout=WAIT_MS)
        pg.wait_for_function("() => window.__fly.some((x) => x.fly === 'hand' && x.ups === 1)", timeout=WAIT_MS)
        flown = pg.evaluate("() => window.__fly.filter((x) => x.fly === 'hand').map((x) => [x.turn, x.ups])")
        assert flown == [[True, 1]], "its back lifts and turns up on its way (orkUI's .ork-turn)"
        card = pg.locator('.hand-stack[data-goal="ask1"] .hand-card')
        card.first.wait_for(state="attached", timeout=WAIT_MS)
        assert card.first.evaluate("e => [e.style.visibility, e.classList.contains('ork-deal')]") == ["hidden", False], "hidden while the copy flies, not the old deal"
        settled(pg)
        assert card.first.evaluate("e => getComputedStyle(e).visibility") == "visible", "it lands in the hand, under the asking leader's lane"
        assert pg.locator('.col-card--deck[data-goal="ask1"]').count() == 1, "its back stays in the deck"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_that_asks_flies_no_card_under_reduced_motion(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="timer"][data-pile="review"]', timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        pg.evaluate(WATCH)
        asking_review(host)
        host.bump({})
        pg.locator('.hand-stack[data-goal="ask1"] .hand-card').first.wait_for(state="attached", timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert pg.evaluate(KINDS) == [] and pg.locator('.hand-stack[data-goal="ask1"] .hand-card').first.evaluate("e => getComputedStyle(e).visibility") == "visible"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def lay(pg, host, words="Players see who answered first"):
    pg.locator(".hand .hand-plus").click(position={"x": 8, "y": 60})
    field = pg.locator(".hand-field")
    field.wait_for(timeout=WAIT_MS)
    field.get_by_role("textbox", name="Write a goal").fill(words)
    field.get_by_role("textbox", name="Write a goal").press("Enter")


def test_a_goal_laid_turns_face_down_lights_its_rune_and_flies_small_into_the_fan_which_ends_with_one_more_back(gui):
    pg, host, log = open_life(gui)
    try:
        pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
        pg.evaluate(WATCH)
        before = pg.locator(".col-card--fan").count()
        lay(pg, host)
        pg.wait_for_function("() => window.__fly.some((x) => x.fly === 'lay')", timeout=WAIT_MS)
        assert pg.locator('body > .table-turned[data-fly="lay"] .table-turned__seal .ork-sigil.small').count() == 1, "the small seal of the hand's backs in the middle of its back"
        assert pg.locator('body > .table-turned[data-fly="lay"] .table-turned__seal .ork-elem').count() == 1, "its rune in the middle"
        pg.wait_for_selector('.frame-column .col-card--fan[data-goal="new-goal"]', timeout=WAIT_MS)
        settled(pg)
        assert pg.evaluate(KINDS).count("lay") == 1 and pg.locator(".col-card--fan").count() == before + 1, "one more back in the fan"
        assert pg.locator('.col-card--fan[data-goal="new-goal"]').evaluate("e => getComputedStyle(e).visibility") == "visible", "the back lies in the fan when the copy has landed"
        last = pg.evaluate("() => { const f = [...document.querySelectorAll('.col-card--fan')]; return f[f.length - 1].dataset.goal; }")
        assert last == "new-goal", "at the fan's end"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_laid_flies_nothing_under_reduced_motion_and_its_back_is_in_the_fan_at_once(gui):
    pg, host, log = open_life(gui)
    try:
        pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        pg.evaluate(WATCH)
        before = pg.locator(".col-card--fan").count()
        lay(pg, host)
        pg.wait_for_selector('.frame-column .col-card--fan[data-goal="new-goal"]', timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        assert pg.evaluate(KINDS) == [] and pg.evaluate(IN_AIR) == 0 and pg.locator(".col-card--fan").count() == before + 1
        assert pg.locator('.col-card--fan[data-goal="new-goal"]').evaluate("e => getComputedStyle(e).visibility") == "visible"
    finally:
        pg.close()
    assert not log, "\n".join(log)
