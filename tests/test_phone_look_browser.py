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
from tests.test_hand_context_narrow_browser import UprightHost  # noqa: E402
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










