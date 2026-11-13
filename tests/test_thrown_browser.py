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


# -- a failure ----------------------------------------------------------------------------------------------------------------------------------


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


def looking(host):
    host.nodes = [n for n in host.nodes if n["slug"] != "look"]
    host.nodes.append(node("look", "design", "The look of the first screen", "table", state="working", stage="implementation", element="ice", asks_you=False,
                           tasks=[task("p1", "Draw the screen", "running"), task("p2", "Pick the words", "running")]))
