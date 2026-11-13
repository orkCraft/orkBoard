"""Spec 168 F2 and F3 (decisions §283.26–§283.28): the discard's two piles, in a real browser at 1366 x 768 against the hand's stub with goals done on their own branch. The lower pile (done on its branch, waiting for dev) is drawn only while
*Lands in dev by itself* is off, under its plate *dev*; the upper (in dev, waiting for main) under *main*. A plate pressed deals the branches to the hand (`ideas.branch_set`: never `orkboard/*`, `goal/*`, `idea/*`; a card warns first when goals are
at work; the lower plate also a new branch from dev); a card of the lower pile played has *To dev* and, in its menu, *To dev without the tests*; a goal blocked before dev is a card in the hand of its party's stack whatever the setting says, with
*Try again* and, when no test ran, *To dev without the tests*. To main lights the goals the card takes along, has *To main without the tests* in its menu, and the cards dissolve into the ring (none under reduced motion).
Pictures to $ORKCRAFT_SHOTS_DIR (or /tmp) when `DISCARD_PILES_SHOTS` is set.

Goal 170 B (decisions §293.4): every card of the lane is a post drawn by table/post.js (`.post-card`; a goal ready for main carries `data-portal-card`, a goal of the lower pile sits in `[data-pile="lower"]`), its goal's name a button that picks it (or plays it, in the lower
pile), the ready one ringed by the portal (`data-portal`) with the act *To main*. Cases changed for the posts: the card's 144 x 202 size (hand cards) is now the post's own width, one column of the lane, in test_both_piles_lie_in_the_column_...; a card pressed is the post's goal name
pressed (`post(pg, slug)`); the cards that dissolve into the ring are posts with `data-melting` (was `.is-dissolving`), checked in test_the_cards_dissolve_into_the_ring_...; **To main on the post** is new in test_to_main_on_the_post_sends_the_goal_the_way_it_went_before
(the pane's To main, tomain.js, is still held by test_to_main_lights_the_goals_...). No case was dropped here."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import node, task  # noqa: E402
from tests.test_portal_browser import PortalHost  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["DISCARD_PILES_SHOTS"]) if os.environ.get("DISCARD_PILES_SHOTS") else None
BIG = {"viewport": {"width": 1366, "height": 768}}
NO_TESTS = "This project has no tests, so nothing can show the goal is safe for dev: send it with To dev without the tests"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"f2-{name}.png"))


class DevHost(PortalHost):
    """The portal's project (Lobby and Reconnect and Menu ready for main) with three goals done on their own branch: Dark mode (Tech) and Score board (Design) waiting for dev, and Chat rooms (Tech) blocked because no test ran."""

    def __init__(self, review=True, at_work=0, blocked=True):
        super().__init__()
        self.review, self.at_work = review, at_work
        self.now = {"dev": "dev", "main": "main"}
        self.rows = []
        for slug, goal, title, element, at in (("dusk", "tech", "Dark mode", "lava", "2026-10-21T12:00:00"), ("scores", "design", "Score board", "meadow", "2026-10-21T11:00:00"), ("chat", "tech", "Chat rooms", "ice", "2026-10-21T10:00:00")):
            if slug == "chat" and not blocked:
                continue
            self.nodes.append(node(slug, goal, title, "discard", state="done", element=element, updated=at, tasks=[task(f"{slug}1", "Make it", "merged", made="Add it", cost=0.5)]))
            self.rows.append({"slug": slug, "goal_branch": f"goal/{slug}", "waits_for_dev": True, "dev_why": "", "dev_blocked": False, "dev_kind": ""})
        if blocked:
            chat = next(r for r in self.rows if r["slug"] == "chat")
            chat.update(dev_why=NO_TESTS, dev_blocked=True, dev_kind="no_tests")
        for slug in ("dusk", "scores", "chat"):
            self.plans[slug] = {"goals": [slug], "commits": [f"{slug}1"], "sealed": None, "titles": {slug: slug}, "files": 1}
        self.stuck = blocked                               # the host refuses Chat rooms without `untested`, as the gate does for a project with no tests

    def handle(self, name, a):
        if name == "ideas.board":
            doc = super().handle(name, a)
            doc["ideas"] = [{**r, "dev_why": r["dev_why"] or ("Lands in dev by itself is off: it waits for you" if self.review and r["waits_for_dev"] else "")} for r in self.rows]
            doc["review"] = self.review
            return doc
        if name == "ideas.branch_set":
            self.log.append((name, a))
            which = a["which"]
            if "branch" in a or "new" in a:
                self.now[which] = a.get("branch") or a["new"]
                self.gate_doc["into" if which == "dev" else "main"] = self.now[which]
                return self.bump({"ok": True, "which": which, "branch": self.now[which]})
            branches = ["dev", "main", "next", "release"] if which == "dev" else ["main", "dev"]
            return {"which": which, "now": self.now[which], "branches": [self.now[which], *[b for b in branches if b != self.now[which]]], "from": self.now["dev"], "at_work": self.at_work}
        if name == "ideas.goal_to_dev":
            self.log.append((name, a))
            row = next(r for r in self.rows if r["slug"] == a["idea"])
            if row["dev_blocked"] and not a.get("untested"):
                return {"refuse": NO_TESTS}
            self.rows = [r for r in self.rows if r is not row]
            self.gate_doc["ideas"].append({"slug": row["slug"], "title": next(n["title"] for n in self.nodes if n["slug"] == row["slug"]), "goal": "tech", "tasks": 1})
            self.gate_doc["commits"] += 1
            return self.bump({"ok": True, "commit": "abc", "branch": row["goal_branch"], "note": "", "subjects": []})
        return super().handle(name, a)


def _refusing(host):
    """The stub's socket answering a refusal as the host does (`ok: false`, the words): a command that returns `{"refuse": words}` is refused."""
    import json

    def on_socket(ws):
        host.ws = ws
        ws.send(json.dumps(host.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            got = host.handle(m["name"], m["args"])
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": got["refuse"]} if isinstance(got, dict) and "refuse" in got else {"t": "reply", "id": m["id"], "ok": True, "result": got}))
        ws.on_message(on_message)
    return on_socket


def open_piles(gui, host=None, **more):
    server, browser = gui
    host = host or DevHost(**more)
    ctx = browser.new_context(**BIG)
    pg = ctx.new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", _refusing(host))
    pg.goto(server.url)
    pg.locator('.release-lane [data-portal-card="music"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(400)
    return pg, host, log


def post(pg, slug):
    """The goal's name on its post in the lane, the button that picks the goal."""
    return pg.locator(f'.release-lane .post-card[data-slug="{slug}"] .post-card__goal')


def close(pg, log, allowed=()):
    pg.context.close()
    assert not [m for m in log if not any(a in m for a in allowed)], "\n".join(log)


def test_a_plate_deals_its_branches_to_the_hand_and_never_the_boards_or_the_works(gui):
    pg, host, log = open_piles(gui)
    try:
        pg.locator('[data-plate="dev"]').click()
        row = pg.locator(".hand-ways-cards [data-way]")
        row.first.wait_for(timeout=WAIT_MS)
        names = [row.nth(i).get_attribute("data-way") for i in range(row.count())]
        assert names == ["branch:dev", "branch:main", "branch:next", "branch:release", "own"], "any branch, the one now first, and a new one from dev"
        assert not [n for n in names if n.startswith(("branch:orkboard/", "branch:goal/", "branch:idea/"))]
        assert row.first.get_attribute("data-way-kind") == "keep" and row.nth(2).get_attribute("data-way-kind") == "take"
        assert pg.locator('.hand-lifted[data-kind="plate"] .hand-card__name').inner_text() == "Which branch do goals land in?"
        shot(pg, "plate-dealt")
        pg.locator('[data-way="branch:next"]').click()
        assert _sent(pg, host, ("ideas.branch_set", {"which": "dev", "branch": "next"}))
        pg.wait_for_function("() => document.querySelector('[data-plate=\"dev\"]')?.textContent === 'next'", timeout=WAIT_MS)
        assert pg.locator(".hand-lifted").count() == 0, "answered: the card goes back"
        pg.locator('[data-plate="main"]').click()
        pg.locator('.hand-ways-cards [data-way="branch:dev"]').wait_for(timeout=WAIT_MS)
        assert [pg.locator(".hand-ways-cards [data-way]").nth(i).get_attribute("data-way") for i in range(pg.locator(".hand-ways-cards [data-way]").count())] == ["branch:main", "branch:dev"], "the upper pile: main or dev"
        pg.locator('[data-way="branch:dev"]').click()
        assert _sent(pg, host, ("ideas.branch_set", {"which": "main", "branch": "dev"}))
    finally:
        close(pg, log)


def test_the_lower_plate_makes_a_new_branch_from_dev_in_a_field_of_its_own(gui):
    pg, host, log = open_piles(gui)
    try:
        pg.locator('[data-plate="dev"]').click()
        pg.locator('[data-way="own"]').click()
        field = pg.locator(".hand-pen__text")
        field.wait_for(timeout=WAIT_MS)
        assert "A new branch from dev" in pg.locator('[data-way="own"]').text_content()
        field.fill("spring")
        pg.locator('[data-act="send-words"]').click()
        assert _sent(pg, host, ("ideas.branch_set", {"which": "dev", "new": "spring"}))
        pg.wait_for_function("() => document.querySelector('[data-plate=\"dev\"]')?.textContent === 'spring'", timeout=WAIT_MS)
    finally:
        close(pg, log)


def test_a_card_warns_first_when_goals_are_at_work_and_a_branch_is_dealt_after_it(gui):
    pg, host, log = open_piles(gui, at_work=2)
    try:
        pg.locator('[data-plate="dev"]').click()
        warn = pg.locator('.hand-lifted[data-kind="plate"]')
        warn.wait_for(timeout=WAIT_MS)
        assert warn.locator(".hand-card__name").inner_text() == "Goals are at work"
        assert pg.locator(".hand-ways-cards [data-way]").count() == 1 and not [c for c in _calls(pg, host, "ideas.branch_set") if "branch" in c]
        shot(pg, "warning")
        pg.locator('[data-way="warn_go"]').click()
        pg.locator('[data-way="branch:next"]').wait_for(timeout=WAIT_MS)
        assert not [c for c in host.log if c[0] == "ideas.branch_set" and "branch" in c[1]], "nothing is set by the warning"
    finally:
        close(pg, log)


# -- F3: To main ------------------------------------------------------------------------------------------------------
