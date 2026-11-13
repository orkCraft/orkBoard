"""The phone's middle (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5, part D; decisions §195.2; the mockup docs/mockups/phone/sidebar.html A1 and A3), in a real browser against a stub host, with touch at 390 × 844: what is looked at is the goal picked, else the
party the person picked in the menu, else the goal of the hand's first card (its card on it, answered with one tap), else nothing (*Nothing waits for you.*). A goal: its header, its phases (a press opens its page), its route by its leaders' heads (done, at work,
next), why and *<Party>'s tasks*; a goal in line: its phases, the moon and its hour. A party: its leader's header, its squad (a head opens its popover as a sheet), the tools of its sword and shield in words, its goals at work and its concerns. Screenshots to
$UPRIGHT_SHOTS when it is set. Since goal 169 F a party picked is the project's feed narrowed to it and nothing picked is the whole feed: tests/test_phone_feed_browser.py. Since goal 169 G a goal's route is its feed's heads row (the reader cut to
its route, `ideas.feed` with `route`) in place of its route's legs; its feed's blocks: tests/test_phone_feed_browser.py."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_context_narrow_browser import TIMER_Q, UprightHost, box, context_of, css_colour, open_up, wait_title  # noqa: E402
from tests.test_hand_desktop_browser import head, node, task  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None
SEAT_WHY = "A player who loses signal comes back to the seat they had."
SEAT = "Keep the seat when a socket reconnects"
CONCERN = {"id": "c1", "level": "alert", "what": "Lobbies live in memory: a restart drops every game.", "why": "", "fix": "", "on": "server/lobby.ts", "aspect": "hotspots"}
NOTE = {"id": "c2", "level": "note", "what": "The email link has no rate limit.", "why": "", "fix": "", "on": "auth/link.ts", "aspect": "security"}
ROUTES = {"seat": ["design", "tech", "product"], "signin": ["tech"], "phones": ["design"], "daily": ["design"], "music": ["tech"]}       # each goal's route, as the reader cuts the feed to it (goal 169 G)
MADE = {"id": "c3", "level": "alert", "what": "Already a goal.", "why": "", "fix": "", "on": "server/rooms.ts", "aspect": "hotspots", "idea": "seat"}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class LookHost(UprightHost):
    """The phone's stub project, and Tech's goal *Keep the seat…* at work on a route of three parties (Design done, Tech at work, Product next), a goal in Talk of Design's, a goal in line that waits for the reset, Tech's size, brief, tools and squad, its leader's
    concerns and a spec that says why. `calm`: the seat's tasks run and check, nothing asks or failed (so the goal has no card in the hand); not calm, one failed and one asks the person to pick (it has a card, the hand's first)."""

    def __init__(self, scenario="question", calm=True):
        super().__init__(scenario)
        tasks = [task("s1", "Keep the seat", "running"), task("s2", "Check the seat", "testing", band="check")] if calm else \
            [task("s1", "Keep the seat", "running"), task("s2", "Reset the round timer", "failed", error="3 checks failed"), task("s3", "Pick the wording", "picking")]
        route = [{"step": "party", "party": "design", "goal": "seat", "state": "done", "done": 1, "total": 1, "n": 1, "of": 3},
                 {"step": "party", "party": "tech", "goal": "seat", "state": "working", "done": 0, "total": 3, "n": 2, "of": 3},
                 {"step": "party", "party": "product", "goal": "seat", "state": "waiting", "done": 0, "total": 0, "n": 3, "of": 3}]
        self.nodes += [
            node("seat", "tech", SEAT, "table", state="working", element="ice", stage="implementation", type={"sign": "feature", "name": "Feature"}, route=route,
                 tasks=tasks),
            node("daily", "design", "Daily quests: who plays them?", "table", state="talk", element="void", type={"sign": "feature", "name": "Feature"}),
            node("chat", "tech", "Chat in the lobby", "deck", state="raw", element="dust", type={"sign": "feature", "name": "Feature"}, waits_as="reset", held_until="2026-10-20T21:40:00")]
        tech = next(p for p in self.parties if p["slug"] == "tech")
        tech.update(brief="How it is built, and what it costs to change.", size="standard", does_tool="claude", does_default=True, does_mixed=False, checks_tool="codex", checks_default=False, checks_mixed=False, lean=False,
                    party=[{**tech["leader"], "band": "lead", "state": "free", "why": ""}, {"slug": "tester", "name": "Tester", "head": head("peon", tier="laborer"), "band": "check", "state": "free", "why": ""}])

    def goal_feed(self, a):
        """The reader's feed cut to a goal's route (realm/board_feed.py `route`): the Orkmaster's head, then the route's leaders in route order; Tech asks on Sign-in, Design has news on the seat; the seat's posts, Tech's then Design's."""
        slug, at = a["route"], dt.datetime.now().astimezone().replace(microsecond=0)
        heads = [{"leader": "orkmaster", "news": False, "asks": False}] + [{"leader": p, "news": slug == "seat" and p in ("tech", "design"), "asks": slug == "signin" and p == "tech"} for p in ROUTES.get(slug, [])]
        post = lambda leader, m, text, kind="news": {"leader": leader, "at": (at - dt.timedelta(minutes=m)).isoformat(timespec="seconds"), "kind": kind, "goal": slug, "text": text, "event": "idea.added", "acts": []}  # noqa: E731
        posts = [{"leader": "tech", "post": post("tech", 6, "Accepted step 1 of Keep the seat"), "more": [post("tech", 11, "Keep the seat's plan changed", "change")]},
                 {"leader": "design", "post": post("design", 25, "Keep the seat's screen is drawn"), "more": []}] if slug == "seat" else []
        return {"since": "", "heads": heads, "waits": [], "posts": posts, "seen": None}

    def handle(self, name, a):
        if name == "ideas.feed" and a.get("route"):
            self.log.append((name, a))
            return self.goal_feed(a)
        if name == "ideas.concerns":
            self.log.append((name, a))
            return {"status": "done", "error": "", "concerns": [CONCERN, NOTE, MADE] if a.get("party") == "tech" else [], "dismissed": []}
        if name == "ideas.page":
            self.log.append((name, a))
            return {"title": a["slug"], "sections": [{"name": "Why", "text": SEAT_WHY if a["slug"] == "seat" else f"About {a['slug']}."}]}
        return super().handle(name, a)


def crown(pg):
    return pg.get_by_role("button", name="The leaders and their goals", exact=True)


def pick_from_menu(pg, kind, name):
    """Opens the menu and presses a goal (`kind` "goal": its card in the Orkmaster's piles or its row under its party, whichever comes first) or a party's row (`kind` "party") by its name."""
    crown(pg).click()
    pg.locator(".up-menu .up-prow").first.wait_for(timeout=WAIT_MS)
    (pg.locator(f'.up-menu button[data-goal][aria-label^="{name}"]') if kind == "goal" else pg.locator(".up-menu .up-prow", has_text=name)).first.click()
    pg.locator(".up-menu").wait_for(state="detached", timeout=WAIT_MS)


def look(pg):
    return pg.locator(".hand-up .up-look")


def raised(pg):
    return pg.locator('.hand-up .up-card[aria-pressed="true"]')


def test_the_phases_the_past_ones_muted_its_own_in_the_ink_and_a_press_opens_the_goals_page(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "goal", SEAT)
        ph = pg.locator(".up-phases")
        assert [p.inner_text().strip() for p in ph.locator(".up-phase").all()] == ["Talk", "Spec", "Work", "Done"] and box(ph)["height"] >= 44
        assert [p.get_attribute("class") for p in ph.locator(".up-phase").all()] == ["up-phase is-past", "up-phase is-past", "up-phase is-now", "up-phase"]
        colours = ph.evaluate("(e) => [...e.children].map((c) => getComputedStyle(c).borderTopColor)")
        assert colours[0] == colours[1] != colours[2] and colours[2] == css_colour(pg, "--ork-ink") and colours[3] != colours[2], "the past ones muted, its own in the ink"
        ph.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "spec" and pg.locator(".hand-up").is_hidden(), "the goal's page of the phase it is in"
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        assert look(pg).get_attribute("data-goal") == "seat", "the same goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_that_asks_or_failed_is_in_the_alerts_frame_and_the_goals_card_is_on_its_way(gui):
    pg, host, log = open_up(gui, host=LookHost(calm=False))
    try:
        pg.locator('.hand-up .up-card[data-key="goal:seat"]').click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'seat'", timeout=WAIT_MS)
        assert raised(pg).get_attribute("data-key") == "goal:seat", "a failed task is a card: its goal's card pressed in the row"
        assert pg.locator(".hand-up .hand-lifted").count() == 1 and pg.locator(".up-tasks").count() == 1
        tasks = pg.locator(".up-tasks .up-task")
        assert [t.locator(".up-task__name").inner_text().strip() for t in tasks.all()] == ["Reset the round timer", "Keep the seat", "Pick the wording"]
        assert [t.locator(".up-task__stage").inner_text().strip() for t in tasks.all()] == ["Doing, failed", "Doing", "Planning, asks you to pick"]
        alert = css_colour(pg, "--ork-alert")
        assert [t.evaluate("(e) => getComputedStyle(e).borderTopColor") == alert for t in tasks.all()] == [True, False, True], "a task that asks or failed in the alert's frame"
        shot(pg, "phone-look-tasks")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_in_line_shows_its_phases_and_why_and_the_moon_with_its_hour_no_feed_no_tasks(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "goal", "Chat in the lobby")
        assert look(pg).get_attribute("data-goal") == "chat" and pg.locator(".up-gh__type").inner_text().strip() == "Feature · In line"
        assert [p.get_attribute("class") for p in pg.locator(".up-phase").all()] == ["up-phase"] * 4, "none past, none its own"
        wait = pg.locator(".up-wait")
        assert wait.locator(".ork-sign.moon").count() == 1 and wait.inner_text().strip() == "Waits for the reset, from 21:40", "the moon and its hour"
        assert pg.locator(".up-gfeed, .up-tasks").count() == 0 and pg.locator(".up-why").inner_text().strip() == "About chat."
        assert not [a for n, a in host.log if n == "ideas.feed" and a.get("route")], "a goal in line asks no feed of its route (goal 169 G)"
        shot(pg, "phone-look-line")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_of_no_goal_is_its_context_and_its_card_and_the_ready_goal_has_its_way_under_the_portal(gui):
    pg, host, log = open_up(gui, "paid", first=True)
    try:
        assert look(pg).get_attribute("data-look") == "card" and context_of(pg).count() == 1 and pg.locator(".hand-up .hand-lifted").count() == 1 and pg.locator(".up-gh, .up-phases").count() == 0
    finally:
        pg.close()
    pg, host, log = open_up(gui, "ready")
    try:
        pg.locator('.up-card[data-kind="ready"]').first.click()
        pg.locator(".hand-ready").wait_for(timeout=WAIT_MS)
        assert look(pg).get_attribute("data-goal") == "music" and pg.locator(".up-gh__name").inner_text().strip() == "Lobby"
        assert [p.get_attribute("class") for p in pg.locator(".up-phase").all()] == ["up-phase is-past", "up-phase is-past", "up-phase is-past", "up-phase is-now"], "a goal done: its last phase its own"
        assert pg.locator(".up-tasks").count() == 0
        shot(pg, "phone-look-ready")
    finally:
        pg.close()


READABLE = """() => {
  const rgb = (s) => { const m = s.match(/rgba?\\(([^)]+)\\)/); const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = ({ r, g, b }) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.a > 0.5) return c; if (e.classList.contains("ork-btn")) { const q = rgb(getComputedStyle(e, "::before").backgroundColor); if (q.a > 0.5) return q; } } return { r: 0, g: 0, b: 0, a: 1 }; };
  const sizes = [], low = [], small = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement, cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (!r.width || !r.height || cs.visibility === "hidden" || cs.display === "none" || +cs.opacity === 0 || el.closest("script,style,noscript,[hidden]")) continue;
    const size = parseFloat(cs.fontSize); sizes.push(size); if (size < 14) small.push(`${el.tagName}.${el.className} ${size}px ${n.textContent.trim().slice(0, 20)}`);
    const f = rgb(cs.color), b = bgOf(el), a = f.a;
    const mix = { r: f.r * a + b.r * (1 - a), g: f.g * a + b.g * (1 - a), b: f.b * a + b.b * (1 - a) };
    const l1 = lum(mix), l2 = lum(b), ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    if (ratio < 4.5) low.push(`${el.tagName}.${el.className} ${n.textContent.trim().slice(0, 30)} ${ratio.toFixed(2)} fg=${cs.color} bg=${JSON.stringify(b)} dis=${el.disabled}`);
  }
  return { body: getComputedStyle(document.body).fontSize, min: Math.min(...sizes), count: sizes.length, low, small };
}"""
