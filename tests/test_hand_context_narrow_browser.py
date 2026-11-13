"""The phone's hand (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3, part B; docs/specs/103-the-phones-app-a-native-frame.md; decisions §174.1, §178–§180, §195; the mockup docs/mockups/phone/sidebar.html), in a real browser against a stub host, with touch
(390 × 844 upright, 844 × 390 on its side): the one screen is, from the top, the Orkmaster's line, **the top row** (the crown, the potions as bottles with the default framed, the die, which says *Play it on the computer*, the discard), **the middle**
(the picked entry's goal with its way, its context and its card with its answers, one tap answers: tests/test_phone_look_browser.py reads the middle) and **the hand's row** (one card an entry, its upper part, the picked one raised, the + card at its right end opening the field); a goal ready for main as
Release's card with the portal on it; *Go on paid?*; the empty hand; and the same page at a narrow width with a fine pointer and at 1280 × 800 unchanged. Screenshots to $UPRIGHT_SHOTS when it is set."""
from __future__ import annotations

import copy
import datetime as dt
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, head, need, node  # noqa: E402
from tests.test_hand_mana_browser import tool  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None
WHY = "A new player meets it before the lobby, so it decides what the lobby needs from them."
SIGN_IN = {"id": "q1", "by": "tech", "leader": "Tech lead", "q": "Which sign-in first?", "choices": ["Email link", "Passkey", "Google"], "pick": 0, "why": WHY, "project": False}
LINE = "Claude Code is out until Thu 18:00: the work goes on with Codex."
SIDE = {"viewport": {"width": 844, "height": 390}, "has_touch": True, "is_mobile": True, "device_scale_factor": 2}        # a phone on its side
GRUNT = {"slug": "grunt", "name": "Grunt", "head": head("peon", tier="warrior")}
PLAY_UP = "Play it on the computer"
SIGN_IN_Q, TIMER_Q = "Which sign-in first?", "Round timer shows on every phone"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def mana_of(now="claude", main="claude", moved=None, paid=None):
    return {"main": main, "now": now, "until": None, "moved": moved, "paid": paid}


class UprightHost(HandHost):
    """A project (*Party game*) of four parties and the tools Claude Code, Antigravity, Codex and Cursor; Tech's goal *Sign-in* asks a card question its Grunt waits for, Design's goal asks another.
    `scenario`: "question" (that), "deep" (Sign-in asks two questions), "ready" (that, and two goals ready for main), "readyonly" (only those), "moved" (Claude Code ran dry: the work goes on with Codex, the Orkmaster says so), "paid" (every tool dry: the Orkmaster's *Go on paid?* alone), "empty" (nothing asked)."""

    def __init__(self, scenario="question"):
        super().__init__(bare=True)
        self.scenario = scenario
        self.limits = [tool("claude", "Claude Code", 0.62), tool("agy", "Antigravity", 0.80), tool("codex", "Codex", 0.41), tool("cursor", "Cursor", 0.18)]
        self.mana = mana_of()
        asked = [{"ask": SIGN_IN_Q, "choices": SIGN_IN["choices"], "pick": 0, "why": WHY, "by": GRUNT, "look": False}]
        signin = node("signin", "tech", "Sign-in", "hand", state="talk", element="dust", asked=asked, type={"sign": "feature", "name": "Feature"})
        phones = node("phones", "design", TIMER_Q, "hand", state="asks", element="meadow", type={"sign": "screen", "name": "Screen"},
                      asked=[{"ask": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock: every phone agrees.", "by": None, "look": False}])
        self.nodes = [n for n in self.nodes if n["place"] != "hand"] + [signin, phones]
        self.needs = [need("talk", "tech", "signin", signin["title"], SIGN_IN["q"], at="2026-10-20T09:30:00", round=1, stances=[], questions=[copy.deepcopy(SIGN_IN)], blocks=True),
                      need("asks", "design", "phones", phones["title"], "Where does the timer run?", at="2026-10-20T09:40:00", asked=phones["asked"])]
        if scenario == "deep":
            second = {"id": "q2", "by": "tech", "leader": "Tech lead", "q": "Keep passwords?", "choices": ["No", "Yes"], "pick": 0, "why": "Fewer things to leak.", "project": False}
            self.needs[0]["questions"].append(second)
        if scenario in ("ready", "readyonly"):
            music = node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00", short="Lobby", type={"sign": "screen", "name": "Screen"})
            codes = node("codes", "design", "Room codes are four letters", "discard", state="done", element="dust", updated="2026-10-19T12:00:00", short="Reconnect")
            self.nodes += [music, codes]
            self.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 5, "files": 9, "ideas": [{"slug": "music", "title": music["title"], "goal": "tech", "tasks": 1}, {"slug": "codes", "title": codes["title"], "goal": "design", "tasks": 2}]}
            self.plans = {"music": {"goals": ["music", "codes"], "commits": ["a1", "a2"], "sealed": None, "titles": {"music": "Lobby", "codes": "Reconnect"}, "files": 3},
                          "codes": {"goals": ["codes"], "commits": ["a2"], "sealed": None, "titles": {"codes": "Reconnect"}, "files": 1}}
            if scenario == "readyonly":
                self.nodes = [n for n in self.nodes if n["place"] != "hand"]
                self.needs = []
        if scenario == "moved":
            self.limits[0] = tool("claude", "Claude Code", 0.0)
            self.mana = mana_of("codex", "claude", moved={"from": "claude", "to": "codex", "until": "2026-10-29T18:00", "at": dt.datetime.now().isoformat(timespec="seconds"), "line": LINE})
        if scenario == "paid":
            self.limits = [tool("claude", "Claude Code", 0.0), tool("agy", "Antigravity", 0.0), tool("codex", "Codex", 0.02), tool("cursor", "Cursor", 0.0)]
            self.mana = mana_of(None, "claude")
            self.nodes = [n for n in self.nodes if n["place"] != "hand"]
            self.needs = [need("paid", "", "", "Go on paid?", "Go on paid?", tool="claude", name="Claude Code", until="2026-10-22T18:00", usd_task=0.4, blocks=True, priority="high")]
        if scenario == "empty":
            self.nodes = [n for n in self.nodes if n["place"] != "hand"]
            self.needs = []

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["projects"] = {"current": "/p/party-game", "open": [{"path": "/p/party-game", "name": "Party game", "needs_you": 0, "working": 0}], "recent": []}
        return doc

    def handle(self, name, a):
        if name == "ideas.to_main_plan":
            self.log.append((name, a))
            return {"idea": a["idea"], "into": "dev", "main": "main", **self.plans[a["idea"]]}
        if name == "ideas.to_main":
            self.log.append((name, a))
            gone = set(self.plans[a["idea"]]["goals"])
            self.gate_doc["ideas"] = [i for i in self.gate_doc["ideas"] if i["slug"] not in gone]
            return self.bump({"commit": "abc", "goals": sorted(gone), "commits": 1, "files": 1, "note": "", "pushed": False})
        if name == "ideas.talk_answer":
            self.log.append((name, a))
            self.needs = [n for n in self.needs if n["kind"] != "talk"]
            return self.bump({"ok": True})
        if name == "ideas.paid":
            self.log.append((name, a))
            self.needs = []
            self.mana = mana_of("claude", "claude", paid={"tool": "claude", "name": "Claude Code", "until": "2026-10-22T18:00", "usd_task": 0.4}) if a.get("yes") else self.mana
            return self.bump({"ok": True, "tool": "claude", "name": "Claude Code", "until": "2026-10-22T18:00"})
        return super().handle(name, a)


def open_up(gui, scenario="question", kind="phone", *, ready=".hand-up", host=None, init=None, first=False):
    """The page against the stub: `kind` "phone" (390 × 844 with touch), "side" (844 × 390), "fine" (390 × 844 with a mouse), "wide" (1280 × 800); `init`: a script run in every page before its own (a stand-in for the keyboard's visual viewport, tests/test_phone_cards_browser.py).
    `first`: the first card of the hand's row pressed, so the middle shows it (goal 169 F: with nothing pressed the middle is the project's feed, tests/test_phone_feed_browser.py)."""
    server, browser = gui
    host = host or UprightHost(scenario)
    ctx = {"phone": narrow.NARROW, "side": SIDE, "fine": narrow.FINE, "wide": narrow.WIDE}[kind]
    context = browser.new_context(**ctx)
    if init:
        context.add_init_script(init)
    pg = context.new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(ready, state="attached", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    if first:
        press_first(pg)
    return pg, host, log


def press_first(pg):
    """The first card of the hand's row pressed: its entry is the one the middle shows (goal 169 F)."""
    pg.locator(".hand-up .up-card").first.click()
    pg.wait_for_function("() => { const l = document.querySelector('.hand-up .up-look'); return !!l && l.dataset.look !== 'feed'; }", timeout=WAIT_MS)
    pg.evaluate("() => { document.activeElement?.blur(); const r = document.querySelector('.hand-up .up-cards'); if (r) r.scrollTop = 0; }")      # the press is over; the click's own scroll into view of the row put back
    pg.wait_for_timeout(200)


def box(loc):
    return loc.bounding_box()


def pots(pg):
    return pg.locator(".hand-up .up-pot")


def crown(pg):
    return pg.get_by_role("button", name="The leaders and their goals", exact=True)


def context_of(pg):
    return pg.locator(".hand-up .up-ctx")


def cards(pg):
    return pg.locator(".hand-up .up-card")


def plus(pg):
    return pg.locator(".hand-up .up-plus .hand-plus")


def name_of(pg):
    return pg.locator(".hand-lifted .hand-card__name").inner_text().strip()




def css_colour(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)






def test_the_die_says_play_it_on_the_computer_and_throws_nothing(gui):        # goal 169 H: the die is the round button's face at the foot's right, Play one of its three (was: a small die in the top row)
    pg, host, log = open_up(gui)
    try:
        die = pg.locator(".hand-up .up-round")
        assert die.count() == 1 and pg.locator(".up-top .up-die, .up-top .ork-die").count() == 0
        assert "/ds/orkui/die/die-" in die.locator("img").get_attribute("src"), "orkUI's cartoon die on its face"
        die.click()
        pg.get_by_role("button", name=PLAY_UP, exact=True).click()
        pg.get_by_text(PLAY_UP, exact=True).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-over").count() == 0 and pg.locator(".play-throw, .playpane").count() == 0 and all("play" not in str(c[0]) for c in host.log), "nothing thrown, nothing asked"
        assert pg.locator(".hand-up").is_visible(), "still the hand"
    finally:
        pg.close()
    assert not log, "\n".join(log)






def ready_card(pg):
    return pg.locator(".hand-up .hand-ready")


def to_ready(pg):
    pg.locator('.up-card[data-kind="ready"]').first.click()
    ready_card(pg).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('.hand-ready')?.dataset.portal !== 'wait'", timeout=WAIT_MS)




def test_later_puts_the_card_back_and_the_next_comes_while_the_goal_stays_ready(gui):
    pg, host, log = open_up(gui, "readyonly")
    try:
        assert cards(pg).count() == 2 and ready_card(pg).count() == 0, "with only goals ready for main: the feed until one is pressed (goal 169 F)"
        to_ready(pg)
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.wait_for_function("() => document.querySelector('.hand-ready .hand-card__name')?.textContent.trim() === 'Reconnect is ready for main'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main") == [] and [g["slug"] for g in host.gate_doc["ideas"]] == ["music", "codes"], "the goal stays ready in the discard"
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.get_by_text("Nothing waits for you.", exact=True).wait_for(timeout=WAIT_MS)
        assert cards(pg).count() == 0
    finally:
        pg.close()


