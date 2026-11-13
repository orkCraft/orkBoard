"""The project's feed on the phone (goal 169 F, decisions §291.5–§291.9; the mockup docs/mockups/phone/feed.html v3, screens 1, 2, 3 and 6), in a real browser against a stub host that feeds `ideas.feed`, with touch at 390 × 844: with no goal picked the phone's
middle is the feed (hand/upfeed.js), asked with this phone's own last look (js/linkpaired.js `looked`), drawn in the reader's order: the heads row on top, what waits first, then the news newest first, one leader's posts in a row one block, the goals at work as
sideways cards with a button each way, the one seen line that spreads; the hand's row at the foot unchanged, no card raised, no tab. A head pressed narrows the feed to it and says so; pressed again the whole feed. A goal's screen (goal 169 G, screen 4) is the
same reader cut to the goal's route (`ideas.feed` with `route`): its heads the route's leaders, its blocks in the reader's order, the goal's question still in the hand, raised. Pictures for Design to $FEED_SHOTS when it is set (at 390 × 844, three device
pixels a pixel)."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_context_narrow_browser import open_up  # noqa: E402
from tests.test_hand_desktop_browser import node, sig, task  # noqa: E402
from tests.test_phone_look_browser import SEAT, LookHost, pick_from_menu  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["FEED_SHOTS"]) if os.environ.get("FEED_SHOTS") else None
PROJECT = "/p/party-game"
LEADERBOARD = "Leaderboard is ready to start"
LOBBY = "Lobby takes the game's colours"


def iso(t: dt.datetime) -> str:
    return t.astimezone().isoformat(timespec="seconds")


def post(leader, at, text, kind="news", goal=""):
    return {"leader": leader, "at": iso(at), "kind": kind, "goal": goal, "text": text, "event": "idea.added", "acts": []}


class FeedHost(LookHost):
    """LookHost's project (Tech's *Keep the seat…* at work, Tech's concerns), two goals ready for main, a plan of Tech's that starts by itself, Design's lobby at work too, and the reader's answer as realm/board_feed.py gives it: the heads (the Orkmaster, Tech with news
    and asking, Design with news, Product and Release with none), what waits (the plan's clock, Lobby waiting for main), the posts since the look (Tech's three in a row, then Design's concern, then the Orkmaster's) and what came before it."""

    def __init__(self, scenario="ready"):
        super().__init__(scenario)
        self.nodes += [node("leader", "tech", LEADERBOARD, "table", state="plan", element="void", type={"sign": "tune", "name": "Tune"}),
                       node("lobby", "design", LOBBY, "table", state="working", element="ice", stage="implementation", type={"sign": "screen", "name": "Screen"}, tasks=[task("l1", "Paint the lobby", "running")])]
        self.now = dt.datetime.now().astimezone().replace(microsecond=0)

    def feed(self, a):
        if a.get("route"):
            return {**self.goal_feed(a), "since": iso(dt.datetime.fromtimestamp(a["since"] / 1000)) if a.get("since") else ""}
        now, since_ms = self.now, a.get("since")
        since = dt.datetime.fromtimestamp(since_ms / 1000).astimezone() if since_ms else None
        mins = lambda m: now - dt.timedelta(minutes=m)              # noqa: E731
        starts = (now + dt.timedelta(minutes=53)).replace(second=0)
        tech = [post("tech", mins(5), "Keep the seat: Keep the seat is in dev", goal="seat"), post("tech", mins(9), "Accepted step 1 of Keep the seat", goal="seat"), post("tech", mins(14), "Keep the seat's plan changed", "change", goal="seat")]
        posts = [{"leader": "tech", "post": tech[0], "more": tech[1:]},
                 {"leader": "design", "post": post("design", mins(30), "Doubts Round timer shows on every phone", "concern", goal="phones"), "more": []},
                 {"leader": "orkmaster", "post": post("orkmaster", mins(42), "Chat in the lobby was added", goal="chat"), "more": []}]
        seen = None
        if since is not None:
            old = [post("product", since - dt.timedelta(hours=2), "Pick the theme of the first week was added"), post("design", since - dt.timedelta(hours=3), "Accepted step 2 of Daily quests", goal="daily")]
            seen = {"since": iso(since), "leaders": ["product", "design"], "posts": old}
        return {"since": iso(since) if since else "",
                "heads": [{"leader": "orkmaster", "news": True, "asks": False}, {"leader": "tech", "news": True, "asks": True}, {"leader": "design", "news": True, "asks": False},
                          {"leader": "product", "news": False, "asks": False}, {"leader": "release", "news": False, "asks": False}],
                "waits": [{"kind": "starts", "goal": "leader", "short": LEADERBOARD, "title": LEADERBOARD, "party": "tech", "leader": "orkmaster", "at": iso(starts),
                           "acts": [{"act": "change_spec", "command": "ideas.spec_change", "args": {"idea": "leader"}}, {"act": "start_now", "command": "ideas.start_now", "args": {"slug": "leader"}}]},
                          {"kind": "main", "goal": "music", "short": "Lobby", "title": "Lobby music loop", "party": "tech", "leader": "release", "at": "", "main_ready": True, "main_reason": "",
                           "acts": [{"act": "to_main", "command": "ideas.to_main", "args": {"idea": "music"}}]}],
                "posts": posts, "seen": seen}

    def handle(self, name, a):
        if name == "ideas.feed":
            self.log.append((name, a))
            return self.feed(a)
        if name in ("ideas.start_now", "ideas.spec_change"):
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)




def at_look(minutes_ago=60):
    return int((dt.datetime.now() - dt.timedelta(minutes=minutes_ago)).timestamp() * 1000)


def open_feed(gui, since=None, host=None, scenario="ready"):
    """The phone against a FeedHost, this phone's last look at the project `since` (ms) when given."""
    init = f"localStorage.setItem('orkcraft.looked', JSON.stringify({{ '{PROJECT}': {since} }}));" if since else None
    pg, host, log = open_up(gui, host=host or FeedHost(scenario), init=init)
    pg.locator(".up-feed .post-card").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def feed(pg):
    return pg.locator(".hand-up .up-feed")


def heads(pg):
    return pg.locator(".up-fh .up-fh__head")




def blocks(pg):
    """The feed's blocks in the page's order: `[(kind, its leader or goal)]`."""
    return pg.eval_on_selector_all(".up-feed > .post-card, .up-feed > .up-fd__lab, .up-feed > .up-fd__seen",
                                   "(els) => els.map((e) => e.classList.contains('up-fd__lab') ? ['label', e.textContent.trim()] : e.classList.contains('up-fd__seen') ? ['seen', ''] : [e.dataset.wait ? 'wait' : e.classList.contains('post-card--work') ? 'work' : 'post', e.dataset.wait ? e.dataset.goal : e.dataset.leader])")


def looked(pg):
    return pg.evaluate(f"() => (JSON.parse(localStorage.getItem('orkcraft.looked')) || {{}})['{PROJECT}'] ?? null")










def test_a_wait_carries_only_its_own_acts_each_the_command_the_reader_names(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        plan, main = pg.locator('.post-card[data-wait="starts"]'), pg.locator('.post-card[data-wait="main"]')
        assert [b.get_attribute("data-act") for b in plan.locator(".post-card__acts button").all()] == ["change_spec", "start_now"]
        assert [b.get_attribute("data-act") for b in main.locator(".post-card__acts button").all()] == ["to_main"] and main.locator('[data-act="to_main"]').inner_text().strip() == "To main"
        plan.locator('[data-act="start_now"]').click()
        assert _calls(pg, host, "ideas.start_now") == [{"slug": "leader"}]
        plan.locator('[data-act="change_spec"]').click()
        plan.locator("textarea").fill("Show the top ten, not three")
        plan.locator('[data-act="send"]').click()
        assert _calls(pg, host, "ideas.spec_change") == [{"idea": "leader", "text": "Show the top ten, not three"}], "the words go with the command the reader names"
        main.locator('[data-act="to_main"]').click()
        assert _calls(pg, host, "ideas.to_main") == [{"idea": "music"}]
        plan.locator(".post-card__goal").click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'leader'", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)




def goal_blocks(pg):
    """A goal's feed's blocks in the page's order, as `blocks` reads the project's."""
    return pg.eval_on_selector_all(".up-gfeed > .post-card, .up-gfeed > .up-fd__lab, .up-gfeed > .up-fd__seen",
                                   "(els) => els.map((e) => e.classList.contains('up-fd__lab') ? ['label', e.textContent.trim()] : e.classList.contains('up-fd__seen') ? ['seen', ''] : [e.dataset.wait ? 'wait' : 'post', e.dataset.wait ? e.dataset.goal : e.dataset.leader])")


def goal_heads(pg):
    return pg.locator(".up-gfeed .up-fh__head")




def test_a_head_pressed_in_a_goals_feed_narrows_it_and_the_goal_stays_picked(gui):
    pg, host, log = open_feed(gui, at_look())
    try:
        pick_from_menu(pg, "goal", SEAT)
        pg.locator(".up-gfeed .post-card").first.wait_for(timeout=WAIT_MS)
        tech = pg.locator('.up-gfeed .up-fh__head[data-leader="tech"]')
        tech.click()
        pg.locator(".up-gfeed .up-fd__only").wait_for(timeout=WAIT_MS)
        assert tech.get_attribute("aria-pressed") == "true" and pg.locator(".up-gfeed .up-fd__only").inner_text().strip() == "The feed shows only Tech"
        assert [b for b in goal_blocks(pg) if b[0] == "post"] == [["post", "tech"]], "narrowed to its posts"
        assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "orkmaster", "the goal stays picked, no party picked"
        tech.click()
        pg.locator(".up-gfeed .up-fd__only").wait_for(state="detached", timeout=WAIT_MS)
        assert tech.get_attribute("aria-pressed") == "false" and [b for b in goal_blocks(pg) if b[0] == "post"] == [["post", "tech"], ["post", "design"]], "pressed again, the goal's whole feed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))




# -- the folding header, the round button and the chain (goal 169 H, decisions §292; feed.html v3 screens 7 and 8) ------------------------------------------

PLAY_UP, ROUND = "Play it on the computer", "Play, Inventory, History"






def top(pg):
    return pg.locator(".hand-up .up-top")


def middle(pg):
    return pg.locator(".hand-up .up-look")






def options(pg):
    return pg.locator(".up-sel .up-sel__opt")


def focused(pg):
    return pg.evaluate("() => document.activeElement?.className || ''")










