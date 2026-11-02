"""Questions and failures as flights (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part C, decisions §206.6–§206.7), in a real browser against a stub host.

A failure: the failed task's card turns red where it lies, after a beat the hand takes it as a card dealt from that card (orkUI's `.ork-deal`, which turns a little as it flies) and the lane keeps a dashed place (`.ork-card-place`) saying *Back here on Try again*
while the failure lies in the hand; tried again, the failure card flies back to the place (`.ork-play`) and the lane's card returns. A failure there when the page is drawn is in the hand at once with its place in the lane; under reduced motion everything appears
in place at once. A question for the person: the card of the task that asks stays where it is and the question card is dealt from it (not from the first card of its goal), and answered it flies back into it. Screenshots to $THROWN_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node, task  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["THROWN_SHOTS"]) if os.environ.get("THROWN_SHOTS") else None
BEAT = 700                                                                                                  # flight.js BEAT_MS


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def open_page(gui, host, width="wide", reduced=False):
    """The page against `host`; `reduced`: under reduced motion from the first frame."""
    server, browser = gui
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    if reduced:
        pg.emulate_media(reduced_motion="reduce")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".hand-stack, .up-card").first.wait_for(timeout=WAIT_MS)
    return pg, log


def working(host, slug="work", title="Build the lobby", party="tech", state="running", extra=()):
    """A goal at work (the table's lane) whose task `w1` is `state`; `extra` more tasks."""
    host.nodes = [n for n in host.nodes if n["slug"] != slug]
    host.nodes.append(node(slug, party, title, "table", state="working", stage="implementation", element="ice", tasks=[task("w1", "Write the lobby", state), *extra]))


def fail(host, slug="work", tid="w1", error="Its checks went red twice"):
    mine = next(n for n in host.nodes if n["slug"] == slug)
    next(t for t in mine["tasks"] if t["id"] == tid).update(state="failed", error=error)
    host.needs.append(need("failed", mine["goal"], slug, mine["title"], "It failed", at="2026-10-20T11:00:00"))
    host.bump(None)


def cleared(host, slug="work", tid="w1"):
    mine = next(n for n in host.nodes if n["slug"] == slug)
    next(t for t in mine["tasks"] if t["id"] == tid).update(state="running", error="")
    host.needs = [n for n in host.needs if not (n["kind"] == "failed" and n["idea"] == slug)]
    host.bump(None)


def lane_card(pg, slug="work", tid="w1"):
    return pg.locator(f'.frame-table [data-goal="{slug}"][data-task="{tid}"]')


def hand_failure(pg, slug="work", tid="w1"):
    return pg.locator(f'.hand-card[data-key="failed/{slug}/{tid}"]')


def center(box):
    return (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


# -- a failure ----------------------------------------------------------------------------------------------------------------------------------

def test_a_failure_turns_its_card_red_then_is_thrown_to_the_hand_and_leaves_a_place_in_its_lane(gui):
    host = HandHost()
    working(host)
    pg, log = open_page(gui, host)
    try:
        card = lane_card(pg)
        card.wait_for(timeout=WAIT_MS)
        assert card.get_attribute("data-lkey") == "t:task:work/w1" and "table-card" in card.get_attribute("class") and "fails" not in card.get_attribute("class")
        assert hand_failure(pg).count() == 0
        pg.wait_for_timeout(300)                                                                              # (the first draw is over: the hand's lanes are settled)
        fail(host)
        pg.locator('[data-lkey="t:task:work/w1"].fails').wait_for(timeout=WAIT_MS)                            # it turns red where it lies ...
        assert hand_failure(pg).count() == 0 and pg.locator('.table-thrown[data-task="w1"]').count() == 0, "... and stays there a beat"
        shot(pg, "thrown-red")
        hand_failure(pg).wait_for(timeout=WAIT_MS)                                                            # ... then it is in the hand
        place = pg.locator('.table-thrown[data-goal="work"][data-task="w1"]')
        place.wait_for(timeout=WAIT_MS)
        assert "ork-card-place" in place.get_attribute("class") and place.inner_text().strip() == "Back here on Start again", "a dashed place in its lane, saying where it comes back"
        assert pg.locator('[data-lkey="t:task:work/w1"]').count() == 0, "the card is in the hand, not in the lane"
        assert place.evaluate("(e) => e.closest('.table-lane') !== null"), "the place lies in the lane the card lay in"
        assert place.bounding_box()["width"] > 100 and place.bounding_box()["height"] > 60, "as large as the card was"
        shot(pg, "thrown-place")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_failure_card_is_dealt_from_its_lanes_card_turning_a_little(gui):
    host = HandHost()
    working(host)
    pg, log = open_page(gui, host)
    try:
        lane_card(pg).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        origin = lane_card(pg).bounding_box()                                                                 # where the card lies (the place keeps the box)
        pg.evaluate("""() => { window.__deal = []; new MutationObserver(() => { for (const e of document.querySelectorAll('.hand-card[data-kind="failed"].ork-deal')) {
            if (!window.__deal.length && e.style.getPropertyValue('--ork-deal-x')) window.__deal.push([e.dataset.key, e.style.getPropertyValue('--ork-deal-x'), e.style.getPropertyValue('--ork-deal-y'),
              getComputedStyle(e).animationName]); } }).observe(document.body, { subtree: true, attributes: true, childList: true }); }""")
        fail(host)
        pg.wait_for_function("() => window.__deal.length > 0", timeout=WAIT_MS)
        key, x, y, name = pg.evaluate("() => window.__deal[0]")
        assert key == "failed/work/w1" and name == "ork-deal", "orkUI's deal: it turns a little (its keyframes rotate the card by the lean token)"
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        card = hand_failure(pg).bounding_box()
        want = (center(origin)[0] - center(card)[0], center(origin)[1] - center(card)[1])
        assert abs(float(x.removesuffix("px")) - want[0]) <= 4 and abs(float(y.removesuffix("px")) - want[1]) <= 4, f"it comes from the card's box: {(x, y)} vs {want}"
        assert hand_failure(pg).get_attribute("data-from"), "it says who handed it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_tried_again_the_failure_flies_back_to_its_place_and_the_card_returns(gui):
    host = HandHost()
    working(host)
    pg, log = open_page(gui, host)
    try:
        lane_card(pg).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        fail(host)
        hand_failure(pg).wait_for(timeout=WAIT_MS)
        place = pg.locator('.table-thrown[data-task="w1"]')
        place.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        pg.evaluate("""() => { window.__back = []; new MutationObserver(() => { for (const e of document.querySelectorAll('.hand-card.is-gone.ork-play')) {
            if (!window.__back.length) window.__back.push([e.style.getPropertyValue('--ork-play-x'), e.style.getPropertyValue('--ork-play-y')]); } }).observe(document.body, { subtree: true, attributes: true, childList: true }); }""")
        at = center(hand_failure(pg).bounding_box())
        to = center(place.bounding_box())
        cleared(host)                                                                                          # Try again: the task runs, the failure leaves the hand
        pg.wait_for_function("() => window.__back.length > 0", timeout=WAIT_MS)
        x, y = pg.evaluate("() => window.__back[0]")
        assert abs(float(x.removesuffix("px")) - (to[0] - at[0])) <= 4 and abs(float(y.removesuffix("px")) - (to[1] - at[1])) <= 4, f"it flies back to the place: {(x, y)} vs {(to[0] - at[0], to[1] - at[1])}"
        pg.locator('[data-lkey="t:task:work/w1"]').wait_for(timeout=WAIT_MS)                                  # the card is back in its lane
        pg.wait_for_function("() => !document.querySelector('.table-thrown[data-task=\"w1\"]')", timeout=WAIT_MS)
        assert hand_failure(pg).count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_failure_there_when_the_page_is_drawn_is_in_the_hand_with_its_place_in_the_lane_and_nothing_flies(gui):
    host = HandHost()
    working(host, state="failed")
    next(n for n in host.nodes if n["slug"] == "work")["tasks"][0].update(error="Its checks went red twice")
    host.needs.append(need("failed", "tech", "work", "Build the lobby", "It failed", at="2026-10-20T11:00:00"))
    pg, log = open_page(gui, host)
    try:
        pg.locator('.table-thrown[data-task="w1"]').wait_for(timeout=WAIT_MS)
        assert hand_failure(pg).count() == 1 and pg.locator(".hand-card.ork-deal").count() == 0 and pg.locator('[data-lkey="t:task:work/w1"]').count() == 0
        assert pg.locator('.table-thrown[data-task="w1"]').inner_text().strip() == "Back here on Start again"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_failure_is_in_the_hand_and_its_place_in_the_lane_at_once(gui):
    host = HandHost()
    working(host)
    pg, log = open_page(gui, host, reduced=True)
    try:
        lane_card(pg).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        fail(host)
        pg.locator('.table-thrown[data-task="w1"]').wait_for(timeout=BEAT - 300)                              # no beat to wait for
        hand_failure(pg).wait_for(timeout=BEAT - 300)
        assert pg.locator(".hand-card.ork-deal").count() == 0 and pg.locator(".hand-card[data-handing]").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_a_failure_has_no_lane_to_leave_and_comes_at_once(gui):
    host = HandHost()
    working(host)
    pg, log = open_page(gui, host, width="phone")
    try:
        pg.wait_for_timeout(300)
        fail(host)
        pg.wait_for_function("() => document.querySelector('.up-card.fails[data-key=\"goal:work\"]')", timeout=BEAT - 300)
        assert pg.locator(".table-thrown").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- a question ---------------------------------------------------------------------------------------------------------------------------------

def asks_pick(host, slug="look", tid="p2"):
    """The goal's second task asks the person to pick (a pick card in the hand)."""
    mine = next(n for n in host.nodes if n["slug"] == slug)
    next(t for t in mine["tasks"] if t["id"] == tid).update(state="picking")
    variants = [{"key": "A", "name": "Calm", "text": "Welcome back.", "why": ""}, {"key": "B", "name": "Loud", "text": "WELCOME BACK!", "why": ""}]
    host.needs.append(need("pick", mine["goal"], "", mine["title"], "Which words?", slug=slug, task=tid, round=1, media="text", variants=variants, n=2, ask="Which words?", short="Pick the words",
                           by={"slug": "elf", "name": "Elf", "head": {"craft": "design", "race": "elf", "tier": "elder"}}))
    host.bump(None)


def looking(host):
    host.nodes = [n for n in host.nodes if n["slug"] != "look"]
    host.nodes.append(node("look", "design", "The look of the first screen", "table", state="working", stage="implementation", element="ice", asks_you=False,
                           tasks=[task("p1", "Draw the screen", "running"), task("p2", "Pick the words", "running")]))


def test_a_question_is_dealt_from_the_card_of_the_task_that_asks_and_flies_back_into_it_when_answered(gui):
    host = HandHost()
    looking(host)
    pg, log = open_page(gui, host)
    try:
        pg.locator('.frame-table [data-goal="look"][data-task="p2"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        got = pg.evaluate("""() => import('/static/js/hand/motion.js').then((m) => [m.fromWhere({ goal: 'look', party: 'design' }), m.fromWhere({ goal: 'look', party: 'design', task: 'p2' })]
          .map((w) => w && [w.at, w.el.dataset.task]))""")
        assert got[0][0] == "goal" and got[1] == ["goal", "p2"], f"the asking task's own card is the origin, not the goal's first: {got}"
        pg.evaluate("""() => { window.__deal = []; new MutationObserver(() => { for (const e of document.querySelectorAll('.hand-card[data-kind="pick"].ork-deal')) {
            if (!window.__deal.length && e.style.getPropertyValue('--ork-deal-x')) window.__deal.push([e.style.getPropertyValue('--ork-deal-x'), e.style.getPropertyValue('--ork-deal-y')]); } }).observe(document.body, { subtree: true, attributes: true, childList: true }); }""")
        origin = pg.locator('.frame-table [data-goal="look"][data-task="p2"]')
        asks_pick(host)
        pg.wait_for_function("() => window.__deal.length > 0", timeout=WAIT_MS)
        x, y = pg.evaluate("() => window.__deal[0]")
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        card = pg.locator('.hand-card[data-kind="pick"]').first.bounding_box()
        box = origin.bounding_box()                                                                            # (its goal moved up its lane when it asked: the card's box is read where it lies now)
        want = (center(box)[0] - center(card)[0], center(box)[1] - center(card)[1])
        assert abs(float(x.removesuffix("px")) - want[0]) <= 4 and abs(float(y.removesuffix("px")) - want[1]) <= 4, f"the question card comes out of the asking task's card: {(x, y)} vs {want}"
        assert "asks" in origin.get_attribute("class"), "its card stays where it is, its line the alert's (yellow)"
        shot(pg, "asked")
        pg.evaluate("""() => { window.__back = []; new MutationObserver(() => { for (const e of document.querySelectorAll('.hand-card.is-gone.ork-play')) {
            if (!window.__back.length) window.__back.push([e.style.getPropertyValue('--ork-play-x'), e.style.getPropertyValue('--ork-play-y')]); } }).observe(document.body, { subtree: true, attributes: true, childList: true }); }""")
        at = center(pg.locator('.hand-card[data-kind="pick"]').first.bounding_box())
        next(t for n in host.nodes if n["slug"] == "look" for t in n["tasks"] if t["id"] == "p2").update(state="running")
        host.needs = [n for n in host.needs if n["kind"] != "pick"]
        host.bump(None)                                                                                        # answered
        pg.wait_for_function("() => window.__back.length > 0", timeout=WAIT_MS)
        bx, by = pg.evaluate("() => window.__back[0]")
        to = center(origin.bounding_box())                                                                     # (its goal moved down its lane again: it flies to the card where it lies now)
        assert abs(float(bx.removesuffix("px")) - (to[0] - at[0])) <= 4 and abs(float(by.removesuffix("px")) - (to[1] - at[1])) <= 4, f"answered, it flies back into the task's card: {(bx, by)} vs {(to[0] - at[0], to[1] - at[1])}"
        pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"pick\"]')", timeout=WAIT_MS)
        assert "asks" not in origin.get_attribute("class"), "none left: the yellow goes"
    finally:
        pg.close()
    assert not log, "\n".join(log)
