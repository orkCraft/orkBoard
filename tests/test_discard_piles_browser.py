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


def lane_dev(pg, slug):
    return pg.locator(f'.release-lane [data-pile="lower"] .post-card[data-slug="{slug}"] .post-card__goal')


def post(pg, slug):
    """The goal's name on its post in the lane, the button that picks the goal."""
    return pg.locator(f'.release-lane .post-card[data-slug="{slug}"] .post-card__goal')


def close(pg, log, allowed=()):
    pg.context.close()
    assert not [m for m in log if not any(a in m for a in allowed)], "\n".join(log)


def test_both_piles_lie_in_the_column_each_under_its_plate_the_lower_only_while_lands_in_dev_by_itself_is_off(gui):
    pg, host, log = open_piles(gui)
    try:
        upper, lower = pg.locator('.release-lane [data-plate="main"]'), pg.locator('.release-lane [data-plate="dev"]')
        assert upper.text_content() == "main" and lower.text_content() == "dev"
        assert upper.evaluate("e => getComputedStyle(e).fontFamily") == lower.evaluate("e => getComputedStyle(e).fontFamily"), "both in the pixel face"
        order = pg.evaluate("""() => [...document.querySelectorAll('.release-lane__scroll [data-plate], .release-lane__scroll [data-portal-card], .release-lane__scroll [data-pile] .post-card')].map((e) => e.dataset.plate || e.dataset.portalCard || e.dataset.slug)""")
        assert order.index("main") < order.index("music") < order.index("dev") < order.index("dusk"), "the upper pile first, then the lower"
        assert [pg.locator('[data-pile="lower"] .post-card').nth(i).get_attribute("data-slug") for i in range(pg.locator('[data-pile="lower"] .post-card').count())] == ["dusk", "scores", "chat"]
        assert pg.locator('.release-lane .release-lane__done [data-slug="dusk"]').count() == 0, "a goal waiting for dev is not in the upper pile's done goals"
        lane_w = pg.evaluate("() => document.querySelector('.release-lane__scroll').clientWidth")
        size = pg.evaluate("() => { const e = document.querySelector('[data-pile=\"lower\"] .post-card'); return [e.offsetWidth, e.className]; }")
        assert "ork-card" in size[1] and lane_w - 40 <= size[0] <= lane_w, "a post of the lane's width (post.js), not a hand card"
        assert pg.locator('.release-lane .plate-count, .release-lane [data-plate] [data-count]').count() == 0 and not any(ch.isdigit() for ch in pg.locator('.release-lane [data-plate]').first.text_content()), "no count on a plate"
        assert pg.locator('.release-lane [data-pile="lower"] .discard-pile__words').text_content() == "done · waits for dev"
        shot(pg, "piles-upper")
        pg.locator('[data-plate="dev"]').evaluate("e => e.scrollIntoView({ block: 'center' })")                    # the column scrolls: the upper pile's last card above the lower plate and its cards
        pg.wait_for_timeout(200)
        shot(pg, "piles-both")
        host.review = True
        host.review = False
        host.bump(None)
        pg.wait_for_function("() => !document.querySelector('[data-pile=\"lower\"]')", timeout=WAIT_MS)
        assert pg.locator('.release-lane [data-plate="main"]').count() == 1 and pg.locator('[data-plate="dev"]').count() == 0, "the lower pile is drawn only while it is off"
    finally:
        close(pg, log)


def test_the_lower_pile_is_the_open_tabs_eyes_a_partys_tab_holds_its_goals_only(gui):
    pg, host, log = open_piles(gui)
    try:
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openTab('design'))")
        pg.wait_for_function("() => document.querySelectorAll('[data-pile=\"lower\"] .post-card').length === 1", timeout=WAIT_MS)
        assert lane_dev(pg, "scores").count() == 1 and lane_dev(pg, "dusk").count() == 0
    finally:
        close(pg, log)


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


def test_a_card_of_the_lower_pile_played_has_to_dev_and_in_its_menu_to_dev_without_the_tests(gui):
    pg, host, log = open_piles(gui)
    try:
        lane_dev(pg, "dusk").click()
        lifted = pg.locator('.hand-lifted[data-kind="lower"]')
        lifted.wait_for(timeout=WAIT_MS)
        assert lifted.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [144, 202]
        ways = pg.locator(".hand-ways-cards [data-way]")
        assert [ways.nth(i).inner_text().split("\n")[0] for i in range(ways.count())] == ["To dev"] and ways.first.get_attribute("data-way-kind") == "go_on"
        menu = pg.locator('.hand-ways-acts [data-act="to_dev_untested"]')
        assert menu.inner_text() == "To dev without the tests"
        shot(pg, "lower-played")
        ways.first.click()
        assert _sent(pg, host, ("ideas.goal_to_dev", {"sealed": True, "idea": "dusk"}))
        pg.wait_for_function("() => !document.querySelector('[data-pile=\"lower\"] .post-card[data-slug=\"dusk\"]')", timeout=WAIT_MS)
        assert [a for n, a in host.log if n == "ideas.goal_to_dev"] == [{"idea": "dusk", "sealed": True}], "no `untested` from the way"
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openTab('orkmaster'))")           # playing a card opened its leader's tab: the Orkmaster's sees every pile
        lane_dev(pg, "scores").click()
        pg.locator('.hand-ways-acts [data-act="to_dev_untested"]').click()
        assert _sent(pg, host, ("ideas.goal_to_dev", {"sealed": True, "idea": "scores", "untested": True}))
    finally:
        close(pg, log)


def test_a_goal_blocked_before_dev_is_a_card_in_the_hand_whatever_the_setting_says(gui):
    for review in (True, False):
        pg, host, log = open_piles(gui, review=review)
        try:
            card = pg.locator('.hand-card[data-key="dev/chat"]')
            card.wait_for(timeout=WAIT_MS)
            assert card.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [144, 202]
            assert "Chat rooms cannot go into dev" in card.inner_text() or "Chat rooms cannot go into dev" in (card.get_attribute("aria-label") or "")
            lane = pg.locator('.hand-lane:has(.hand-card[data-key="dev/chat"])').get_attribute("data-lane")
            assert lane not in (None, "0"), "in its party's lane"
            assert pg.locator('[data-pile="lower"]').count() == (1 if review else 0), "the lower pile follows the setting; the hand's card does not"
            if review:
                shot(pg, "blocked-card")
            card.dispatch_event("click")
            lifted = pg.locator('.hand-lifted[data-kind="dev_blocked"]')
            lifted.wait_for(timeout=WAIT_MS)
            assert NO_TESTS in lifted.inner_text()
            ways = pg.locator(".hand-ways-cards [data-way]")
            assert [ways.nth(i).get_attribute("data-way") for i in range(ways.count())] == ["try_again", "to_dev_untested"], "Try again and, no test having run, To dev without the tests"
            assert [ways.nth(i).get_attribute("data-way-kind") for i in range(ways.count())] == ["start_again", "accept_risk"]
            if review:
                shot(pg, "blocked-played")
            pg.locator('[data-way="try_again"]').click()
            assert _sent(pg, host, ("ideas.goal_to_dev", {"sealed": True, "idea": "chat"}))
            assert pg.locator('.hand-places .hand-card[data-key="dev/chat"]').count() == 1, "refused: the card stays"
            pg.locator('[data-way="to_dev_untested"]').click()
            assert _sent(pg, host, ("ideas.goal_to_dev", {"sealed": True, "idea": "chat", "untested": True}))
            pg.wait_for_function("() => !document.querySelector('.hand-places .hand-card[data-key=\"dev/chat\"]')", timeout=WAIT_MS)
        finally:
            close(pg, log, allowed=("no tests",))


def test_a_blocked_goal_whose_tests_ran_has_try_again_alone(gui):
    host = DevHost()
    next(r for r in host.rows if r["slug"] == "chat").update(dev_kind="red", dev_why="The tests are red on dev with the goal: test_x failed")
    pg, host, log = open_piles(gui, host=host)
    try:
        pg.locator('.hand-card[data-key="dev/chat"]').dispatch_event("click")
        pg.locator(".hand-ways-cards [data-way]").first.wait_for(timeout=WAIT_MS)
        ways = pg.locator(".hand-ways-cards [data-way]")
        assert [ways.nth(i).get_attribute("data-way") for i in range(ways.count())] == ["try_again"]
        assert "test_x failed" in pg.locator('.hand-lifted[data-kind="dev_blocked"]').inner_text()
    finally:
        close(pg, log)


# -- F3: To main ------------------------------------------------------------------------------------------------------

def test_to_main_lights_the_goals_it_takes_along_and_has_to_main_without_the_tests_in_its_menu(gui):
    pg, host, log = open_piles(gui)
    try:
        post(pg, "music").click()
        pg.locator("[data-tomain] [data-to-main]").wait_for(timeout=WAIT_MS)
        pg.locator('.release-lane [data-portal-card="codes"][data-along="1"]').wait_for(timeout=WAIT_MS)
        assert pg.locator("[data-along]").count() == 1, "only the goal Lobby stands on is lit"
        menu = pg.locator("[data-tomain] [data-to-main-untested]")
        assert menu.text_content() == "To main without the tests" and menu.is_visible()
        shot(pg, "to-main-along")
        pg.locator("[data-tomain] [data-to-main]").click()
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"}))
        assert [a for n, a in host.log if n == "ideas.to_main"] == [{"idea": "music", "sealed": True}], "tested: no `untested`"
    finally:
        close(pg, log)


def test_to_main_on_the_post_sends_the_goal_the_way_it_went_before(gui):
    """Goal 170 B: the ready post ringed by the portal has the act *To main* (a button with its word); it sends what the pane's To main sends: `ideas.to_main` for the goal, tested."""
    pg, host, log = open_piles(gui)
    try:
        top = pg.locator('.release-lane .post-card[data-portal-card="music"]')
        assert top.get_attribute("data-portal") == "1" and pg.locator(".release-lane .post-card[data-portal]").count() == 1, "the portal rings the top ready post alone"
        assert pg.locator('.release-lane .post-card[data-portal-card="codes"] [data-act="to_main"]').count() == 0, "the others wait for their turn: no act on them"
        button = top.locator('[data-act="to_main"]')
        assert button.inner_text().strip() == "To main"
        button.focus()
        pg.keyboard.press("Enter")
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"}))
        assert [a for n, a in host.log if n == "ideas.to_main"] == [{"idea": "music", "sealed": True}], "tested: no `untested`"
    finally:
        close(pg, log)


def test_the_cards_dissolve_into_the_ring_and_leave_and_under_reduced_motion_nothing_moves(gui):
    pg, host, log = open_piles(gui)
    try:
        post(pg, "music").click()
        pg.locator("[data-tomain] [data-to-main]").wait_for(timeout=WAIT_MS)
        pg.locator('[data-along="1"]').wait_for(timeout=WAIT_MS)
        pg.evaluate("""() => { window.__melt = new Set(); new MutationObserver(() => document.querySelectorAll('[data-melting]').forEach((e) => window.__melt.add(e.dataset.slug))).observe(document.body, { subtree: true, attributes: true, childList: true }); }""")
        pg.locator("[data-tomain] [data-to-main]").click()
        pg.wait_for_function("() => window.__melt.size === 2", timeout=WAIT_MS)
        assert sorted(pg.evaluate("() => [...window.__melt]")) == ["codes", "music"], "the goal and the one it stood on"
        pg.wait_for_function("() => !document.querySelector('[data-portal-card=\"music\"], [data-portal-card=\"codes\"]')", timeout=WAIT_MS)
    finally:
        close(pg, log)
    server, browser = gui
    ctx = browser.new_context(**BIG, reduced_motion="reduce")
    pg = ctx.new_page()
    host = DevHost()
    log = []
    pg.on("pageerror", lambda e: log.append(str(e)))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.locator('.release-lane [data-portal-card="music"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        post(pg, "music").click()
        pg.locator('[data-along="1"]').wait_for(timeout=WAIT_MS)
        pg.locator("[data-tomain] [data-to-main]").click()
        assert _sent(pg, host, ("ideas.to_main", {"sealed": True, "idea": "music"}))
        assert pg.locator("[data-melting]").count() == 0, "nothing moves under reduced motion"
    finally:
        ctx.close()
    assert not log, "\n".join(log)
