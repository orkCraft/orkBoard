"""The phone's hand (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3, part B; docs/specs/103-the-phones-app-a-native-frame.md; decisions §174.1, §178–§180, §195; the mockup docs/mockups/phone/sidebar.html), in a real browser against a stub host, with touch
(390 × 844 upright, 844 × 390 on its side): the one screen is, from the top, the Orkmaster's line, **the top row** (the crown, the potions as bottles with the default framed, the die, which says *Play it on the computer*, the discard), **the middle**
(the picked entry's context and its card with its answers, one tap answers; *Spec* under it) and **the hand's row** (one card an entry, its upper part, the picked one raised, the + card at its right end opening the field); a goal ready for main as
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
from tests.test_hand_desktop_browser import HandHost, head, need, node, sig  # noqa: E402
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


def open_up(gui, scenario="question", kind="phone", *, ready=".hand-up", host=None):
    """The page against the stub: `kind` "phone" (390 × 844 with touch), "side" (844 × 390), "fine" (390 × 844 with a mouse), "wide" (1280 × 800)."""
    server, browser = gui
    host = host or UprightHost(scenario)
    ctx = {"phone": narrow.NARROW, "side": SIDE, "fine": narrow.FINE, "wide": narrow.WIDE}[kind]
    pg = browser.new_context(**ctx).new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(ready, state="attached", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    return pg, host, log


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


def picked_card(pg):
    return pg.locator('.hand-up .up-card[aria-pressed="true"]')


def plus(pg):
    return pg.locator(".hand-up .up-plus .hand-plus")


def name_of(pg):
    return pg.locator(".hand-lifted .hand-card__name").inner_text().strip()


def wait_title(pg, text):
    pg.wait_for_function("(t) => document.querySelector('.hand-lifted .hand-card__name')?.textContent.trim() === t", arg=text, timeout=WAIT_MS)


def css_colour(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def test_the_screen_is_the_notice_the_top_row_the_middle_and_the_hand_row_from_the_top_with_no_board_no_arrows_no_deck(gui):
    pg, host, log = open_up(gui)
    try:
        assert pg.locator(".frame").get_attribute("data-upright") == "1"
        assert pg.locator(".frame-table").is_hidden() and pg.locator(".table-tabs").is_hidden(), "no Board on a phone"
        top, look, row, w, h = box(pg.locator(".up-top")), box(pg.locator(".up-look")), box(pg.locator(".up-row")), pg.viewport_size["width"], pg.viewport_size["height"]
        assert top["y"] < look["y"] < row["y"], "the top row, the middle, the hand's row"
        assert round(top["height"]) == 61 or round(top["height"]) == 60, "the top row is 60 px (and its line)"
        assert round(row["height"]) in (112, 113) and abs(row["y"] + row["height"] - h) <= 1, "the hand's row of 112 px lies at the screen's foot"
        assert look["y"] >= top["y"] + top["height"] - 1 and look["y"] + look["height"] <= row["y"] + 1
        for gone in (".up-nav", ".up-edge", ".up-deck", ".up-stack", ".up-navrow"):
            assert pg.locator(gone).count() == 0, gone
        assert pg.get_by_role("button", name="The Board").count() == 0 and "Turn the phone" not in pg.locator("body").inner_text()
        text = pg.locator(".hand-up").inner_text().lower()
        assert "deck" not in text and "stack" not in text and "menu" not in text, "never those words in the interface"
        shot(pg, "phone-question")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_crown_is_a_44_px_button_at_the_left_of_the_top_row_and_opens_the_menu_of_the_leaders(gui):       # the menu itself: tests/test_phone_menu_browser.py
    pg, host, log = open_up(gui)
    try:
        c = crown(pg)
        r = box(c)
        assert r["width"] >= 44 and r["height"] >= 44 and r["x"] < 16 and "/races/peon-crown" in c.locator("img").get_attribute("src"), "the Orkmaster's crowned head at the left"
        assert c.get_attribute("aria-expanded") == "false" and box(pots(pg).first)["x"] > r["x"] + r["width"] - 1
        c.click()
        pg.locator(".up-menu").wait_for(timeout=WAIT_MS)
        assert c.get_attribute("aria-expanded") == "true" and pg.locator(".up-menu").get_attribute("aria-label") == "The leaders and their goals"
        pg.keyboard.press("Escape")
        pg.locator(".up-menu").wait_for(state="detached", timeout=WAIT_MS)
        assert pg.get_by_role("menu").count() == 0, "no **…** menu any more"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_potions_are_bottles_with_their_shares_the_default_framed_each_44_px_and_a_press_opens_what_used_it(gui):
    pg, host, log = open_up(gui)
    try:
        t = pots(pg)
        assert [b.get_attribute("data-provider") for b in t.all()] == ["claude", "agy", "codex", "cursor"]
        assert [b.get_attribute("aria-label") for b in t.all()] == ["Claude Code: 62% of the week left, the default", "Antigravity: 80% of the week left", "Codex: 41% of the week left", "Cursor: 18% of the week left"]
        assert [b.get_attribute("title") for b in t.all()] == [b.get_attribute("aria-label") for b in t.all()], "the potions' words"
        assert [b.locator(".up-pot__share").inner_text() for b in t.all()] == ["62%", "80%", "41%", "18%"]
        assert pg.locator(".hand-up .ork-potion.small").count() == 4, "a bottle each, at the small scale"
        assert [b.get_attribute("data-size") for b in t.all()] == [b.locator(".ork-potion").evaluate("(e) => [...e.classList].find((c) => c.startsWith('size-'))?.slice(5) || 'large'") for b in t.all()], "the bottle's size is the week's"
        mark = t.nth(0).locator("img.ork-mark")
        m, s = box(mark), box(t.nth(0).locator(".up-pot__share"))
        assert mark.get_attribute("src").endswith("/marks/harness-claude.png") and round(m["width"]) == 12 and m["y"] + m["height"] <= s["y"], "its mark small at the corner, in its own colour, over the share"
        for b in t.all():
            r = box(b)
            assert r["width"] >= 44 and r["height"] >= 44
        colours = pg.evaluate("() => [...document.querySelectorAll('.hand-up .up-pot__share')].map((e) => getComputedStyle(e).color)")
        assert colours[3] != colours[0] and colours[3] == css_colour(pg, "--ork-alert"), "the share is in the warning's colour as it runs low"
        framed = pg.locator(".hand-up .up-pot[data-default='1']")
        assert framed.count() == 1 and framed.get_attribute("data-provider") == "claude" and "is-default" in framed.get_attribute("class")
        assert framed.evaluate("(e) => getComputedStyle(e).borderTopColor") == css_colour(pg, "--ork-ink") and t.nth(1).evaluate("(e) => getComputedStyle(e).borderTopColor") != css_colour(pg, "--ork-ink"), "the default wears the ink's frame"
        assert pg.locator(".hand-up .hand-mana, .hand-up .hand-pot").count() == 0
        shot(pg, "phone-top")
        t.nth(2).click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "limits", "a press opens what used it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_more_than_four_tools_or_the_paid_slot_make_a_plus_n_place(gui):
    host = UprightHost("question")
    host.limits += [tool("hermes", "Hermes", 0.5), tool("pi", "Pi", 0.3)]
    pg, host, log = open_up(gui, host=host)
    try:
        assert pots(pg).count() == 4 and pots(pg).last.get_attribute("aria-label") == "3 more tools: what is left of them" and pots(pg).last.inner_text().strip() == "+3"
        pots(pg).last.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "limits"
    finally:
        pg.close()
    host = UprightHost("question")
    host.mana = mana_of("claude", "claude", paid={"tool": "claude", "name": "Claude Code", "until": "2026-10-22T18:00", "usd_task": 0.4})
    pg, host, log = open_up(gui, host=host)
    try:
        assert pots(pg).count() == 4 and pg.locator(".hand-up .up-pot--paid").count() == 1 and pg.locator(".hand-up .up-pot--paid .up-pot__share").inner_text() == "API"
    finally:
        pg.close()


def test_the_die_says_play_it_on_the_computer_and_throws_nothing(gui):
    pg, host, log = open_up(gui)
    try:
        die = pg.locator(".hand-up .up-die")
        r = box(die)
        assert die.count() == 1 and die.get_attribute("aria-label") == PLAY_UP and r["width"] >= 44 and r["height"] >= 44 and r["x"] > box(pots(pg).last)["x"], "at the right of the potions"
        assert die.locator(".ork-die").count() == 1 and die.locator(".ork-die").evaluate("(e) => e.offsetWidth") < 69, "orkUI's die, smaller than the desktop's"
        die.click()
        pg.get_by_text(PLAY_UP, exact=True).wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-over").count() == 0 and pg.locator(".play-throw, .playpane").count() == 0 and all("play" not in str(c[0]) for c in host.log), "nothing thrown, nothing asked"
        assert pg.locator(".hand-up").is_visible(), "still the hand"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discard_is_a_small_pile_that_opens_the_goals_done_and_ready_over_the_pane_none_with_nothing(gui):
    pg, host, log = open_up(gui, "question")
    try:
        assert pg.locator(".hand-up .up-pile").count() == 0, "none while nothing is done and nothing waits for main"
    finally:
        pg.close()
    pg, host, log = open_up(gui, "ready")
    try:
        pile = pg.locator(".hand-up .up-pile")
        r, top = box(pile), box(pile.locator(".up-pile__top"))
        assert pile.count() == 1 and r["width"] >= 44 and r["x"] + r["width"] > pg.viewport_size["width"] - 24 and box(pg.locator(".up-die"))["x"] < r["x"], "at the top row's right end, after the die"
        assert round(top["width"]) == 32 and round(top["height"]) == 44, "its top card 32 x 44"
        assert pile.get_attribute("aria-label").startswith("Done: Lobby music loop") and "2 goals ready for main" in pile.get_attribute("aria-label")
        shot(pg, "phone-pile")
        pile.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "discard" and pg.locator(".hand-up").is_hidden()
        assert "ready for main" in pg.locator(".hand-discardview").inner_text().lower()
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_context_says_who_which_goal_why_the_pick_and_who_waits_above_the_card(gui):
    pg, host, log = open_up(gui)
    try:
        c = context_of(pg)
        who = c.locator(".up-ctx__who")
        assert who.inner_text().strip().lower() == "tech" and "/races/shaman-elder" in who.locator("img").get_attribute("src")
        hb = box(who.locator("img"))
        assert round(hb["width"]) == 24 and round(hb["height"]) == 22, "the leader's head at 24 x 22"
        goal = c.locator(".up-ctx__goal")
        assert goal.inner_text().strip() == "Sign-in" and goal.locator(".ork-elem.dust").count() == 1 and goal.locator(".ork-sign.feature").count() == 1
        assert c.locator(".up-ctx__why").inner_text().strip() == WHY
        assert c.locator(".up-ctx__rec").inner_text().strip() == "Recommended: Email link"
        assert c.locator(".up-ctx__wait").inner_text().strip() == "Grunt waits for your answer"
        faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.up-ctx__why')).fontFamily, getComputedStyle(document.querySelector('.hand-up .up-spec')).fontFamily]")
        assert faces[0] != faces[1], "the body face, never the pixel face"
        assert box(c)["y"] + box(c)["height"] <= box(pg.locator(".hand-up .hand-lifted"))["y"] + 1, "above the card"
        assert c.evaluate("(e) => e.tagName") == "BUTTON", "a press opens the goal's way"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_middle_scrolls_as_a_whole_and_the_rows_stay(gui):
    pg, host, log = open_up(gui)
    try:
        pg.evaluate("() => { const w = document.querySelector('.up-ctx__why'); w.textContent = Array(60).fill('A long reason that goes on and on.').join(' '); }")
        look, row = pg.locator(".up-look"), box(pg.locator(".up-row"))
        assert look.evaluate("(e) => e.scrollHeight > e.clientHeight && ['auto', 'scroll'].includes(getComputedStyle(e).overflowY)")
        top = box(pg.locator(".up-top"))
        look.evaluate("(e) => { e.scrollTop = 200; }")
        assert box(pg.locator(".up-row")) == row and box(pg.locator(".up-top")) == top, "the top row and the hand's row never move"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_row_draws_every_entry_upper_part_the_first_picked_and_raised_with_no_count(gui):
    pg, host, log = open_up(gui, "ready")
    try:
        c = cards(pg)
        assert c.count() == 4, "Sign-in, the timer, and the two goals ready for main: one card an entry"
        assert [b.get_attribute("data-kind") for b in c.all()] == ["stops", "stops", "ready", "ready"]
        first = c.first
        assert first.get_attribute("aria-pressed") == "true" and sum(1 for b in c.all() if b.get_attribute("aria-pressed") == "true") == 1
        r0, r1 = box(first), box(c.nth(1))
        assert round(r0["width"]) == 88 and round(r1["width"]) == 88 and round(r0["height"]) == 124, "88 x 124"
        assert r1["y"] - r0["y"] == pytest.approx(6, abs=1.5), "the picked one raised by 6 px"
        assert first.evaluate("(e) => getComputedStyle(e).borderTopColor") == css_colour(pg, "--ork-ink"), "with the ink's frame"
        assert first.locator(".ork-elem.dust").count() == 1 and first.locator(".up-card__name").inner_text().strip() == SIGN_IN_Q, "its element and its name (the question itself)"
        assert first.locator(".up-card__asker img").count() == 1 and first.locator(".up-card__window .ork-sign.question").count() == 1, "its window: the action's sign and the asker's head"
        assert "/races/shaman-elder" in first.locator(".up-card__asker img").get_attribute("src") and round(box(first.locator(".up-card__asker img"))["width"]) == 16
        assert c.nth(1).get_attribute("class").count("asks") == 1 and c.nth(2).get_attribute("class").count("asks") == 0
        assert c.nth(2).locator(".up-card__name").inner_text().strip() == "Lobby is ready for main" and c.nth(2).locator(".ork-sign.check").count() == 1
        assert SIGN_IN_Q in c.first.get_attribute("aria-label") and not any(ch.isdigit() for ch in pg.locator(".up-cards").inner_text()), "its words for a screen reader; never a number"
        shot(pg, "phone-row")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_press_on_another_card_picks_it_and_its_card_and_context_come_to_the_middle(gui):
    pg, host, log = open_up(gui)
    try:
        assert name_of(pg) == SIGN_IN_Q
        cards(pg).nth(1).click()
        pg.wait_for_function("() => document.querySelector('.up-card[aria-pressed=true]')?.dataset.key === 'goal:phones'", timeout=WAIT_MS)
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "design" and c.locator(".up-ctx__goal").inner_text().strip() == TIMER_Q
        assert c.locator(".up-ctx__why").inner_text().strip() == "One clock: every phone agrees." and c.locator(".up-ctx__wait").count() == 0
        assert picked_card(pg).count() == 1 and picked_card(pg).get_attribute("data-key") == "goal:phones"
        assert sig(pg, "frame/state.js", "picked") == "phones", "the picked goal follows"
        assert pg.locator(".hand-up .hand-lifted button").count() >= 2, "its answers on its card"
        cards(pg).nth(0).click()
        wait_title(pg, SIGN_IN_Q)
        assert sig(pg, "frame/state.js", "picked") == "signin"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_card_in_the_middle_is_full_width_less_the_gutters_not_turned_its_choices_two_by_two(gui):
    pg, host, log = open_up(gui)
    try:
        card = pg.locator(".hand-up .hand-lifted")
        assert card.count() == 1 and name_of(pg) == SIGN_IN_Q, "the question itself is the card's name"
        b, vw = box(card), pg.viewport_size["width"]
        assert b["x"] == pytest.approx(8, abs=2) and b["x"] + b["width"] == pytest.approx(vw - 8, abs=2), "full width less a gutter a side"
        assert card.evaluate("(e) => getComputedStyle(e).rotate") in ("none", "0deg") and card.evaluate("(e) => getComputedStyle(e).position") == "relative", "not turned, in its place"
        cells = [box(c) for c in card.locator(".q-card").all()]
        assert len(cells) == 4 and cells[0]["x"] == pytest.approx(cells[2]["x"], abs=2) and cells[1]["x"] > cells[0]["x"] + 40 and cells[2]["y"] > cells[0]["y"] + 40, "two by two"
        assert [c.inner_text().strip().splitlines()[0] for c in card.locator(".q-card").all()] == ["Email link", "Passkey", "Google", "Other…"]
        assert card.locator(".q-card.is-pick").inner_text().strip().startswith("Email link"), "the leader's pick raised"
        assert card.get_by_role("button", name="Let Tech lead decide").count() == 1 and card.locator(".hand-card__party").text_content().strip() == "Tech"
        for c in card.locator(".q-card").all():
            assert box(c)["height"] >= 44
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_one_tap_on_a_choice_answers_at_once_and_the_next_entry_comes_to_the_middle(gui):
    pg, host, log = open_up(gui)
    try:
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}]
        pg.wait_for_function("() => document.querySelector('.up-card[aria-pressed=true]')?.dataset.key === 'goal:phones'", timeout=WAIT_MS)
        assert cards(pg).count() == 1, "the answered entry left the row"
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "design" and c.locator(".up-ctx__goal").inner_text().strip() == TIMER_Q
        assert c.locator(".up-ctx__rec").inner_text().strip() == "Recommended: Server counts, phones show it" and c.locator(".up-ctx__wait").count() == 0
        assert sig(pg, "frame/state.js", "picked") == "phones"
        shot(pg, "phone-next")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goals_other_cards_are_not_cards_of_the_row_no_edge_no_count(gui):
    pg, host, log = open_up(gui, "deep")
    try:
        assert cards(pg).count() == 2 and name_of(pg) == SIGN_IN_Q, "Sign-in asks two questions: one entry, one card in the row"
        assert pg.locator(".up-edge, .ork-card-back.edge").count() == 0
        assert not any(ch.isdigit() for ch in pg.locator(".up-cards").inner_text()), "no number"
        shot(pg, "phone-deep")
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        wait_title(pg, "Keep passwords?")
        assert cards(pg).count() == 2 and _calls(pg, host, "ideas.talk_answer") == [], "the answers go together after the last"
        assert picked_card(pg).get_attribute("data-key") == "goal:signin"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_other_and_let_the_leader_decide_answer_from_the_card(gui):
    pg, host, log = open_up(gui)
    try:
        pg.locator(".hand-up .hand-lifted .q-card--blank").click()
        pg.locator(".hand-up .hand-lifted textarea").fill("Magic link or SSO")
        pg.get_by_role("button", name="Send", exact=True).click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "text": "Magic link or SSO"}]}]
        wait_title(pg, TIMER_Q)
    finally:
        pg.close()
    pg, host, log = open_up(gui)
    try:
        pg.get_by_role("button", name="Let Tech lead decide").click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [], "decide": True}]
    finally:
        pg.close()


def test_a_press_on_the_context_opens_the_goals_way_over_the_pane_and_back_returns_to_the_same_card(gui):
    pg, host, log = open_up(gui)
    try:
        context_of(pg).click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "talk" and pg.locator(".frame-table").is_visible() and pg.locator(".hand-up").is_hidden()
        assert pg.locator(".table-tabs").is_hidden()
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        assert name_of(pg) == SIGN_IN_Q, "the same card"
    finally:
        pg.close()


def test_spec_under_the_card_opens_the_spec_page_or_talk_while_it_is_not_written(gui):
    pg, host, log = open_up(gui)
    try:
        spec = pg.locator(".up-spec")
        assert spec.inner_text().strip() == "The spec is written after your answers" and box(spec)["height"] >= 44 and spec.get_attribute("data-page") == "talk"
        assert box(spec)["y"] >= box(pg.locator(".hand-up .hand-lifted"))["y"] + box(pg.locator(".hand-up .hand-lifted"))["height"] - 1, "under the card"
        spec.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "talk"
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        pg.evaluate("""async () => { const s = await import('/static/js/shell/store.js'); const m = s.mapData.value; m.nodes.find((n) => n.slug === 'phones').state = 'decided'; s.mapData.value = { ...m, nodes: [...m.nodes] }; }""")
        cards(pg).nth(1).click()
        pg.wait_for_function("() => document.querySelector('.up-spec')?.dataset.page === 'spec'", timeout=WAIT_MS)
        spec = pg.locator(".up-spec")
        assert spec.inner_text().strip() == "Spec"
        spec.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "spec"
    finally:
        pg.close()


def test_a_card_of_no_goal_has_no_spec_button_and_its_card_is_in_the_row(gui):
    pg, host, log = open_up(gui, "paid")
    try:
        assert pg.locator(".up-spec").count() == 0 and cards(pg).count() == 1 and cards(pg).first.get_attribute("aria-pressed") == "true"
        assert cards(pg).first.locator(".up-card__name").inner_text().strip() == "Go on paid?"
    finally:
        pg.close()


def test_the_plus_card_lies_at_the_rows_right_end_the_cards_pass_under_it_and_it_opens_the_field_over_the_keyboard_with_the_microphone(gui):
    pg, host, log = open_up(gui, "ready")
    try:
        p, row, w, h = plus(pg), box(pg.locator(".up-row")), pg.viewport_size["width"], pg.viewport_size["height"]
        r = box(p)
        assert p.count() == 1 and 60 <= r["width"] <= 70 and 86 <= r["height"] <= 96, "about 64 x 90"
        assert r["x"] + r["width"] >= w - 20 and r["y"] >= row["y"], "at the row's right end"
        assert p.evaluate("(e) => getComputedStyle(e).borderTopColor") == css_colour(pg, "--ork-action") and p.get_attribute("aria-label") == "New goal"
        shot(pg, "phone-plus")
        scroller = pg.locator(".up-cards")
        assert scroller.evaluate("(e) => e.scrollWidth > e.clientWidth"), "four cards and the room under the + card: the row scrolls sideways"
        scroller.evaluate("(e) => { e.scrollLeft = e.scrollWidth; }")
        last = box(cards(pg).last)
        assert last["x"] + last["width"] <= r["x"] + 1, "the last card can be brought clear of the + card"
        p.click()
        area = pg.locator(".up-field textarea")
        area.wait_for(timeout=WAIT_MS)
        f = box(pg.locator(".up-field"))
        assert f["y"] + f["height"] >= h - 2 and pg.evaluate("() => document.activeElement === document.querySelector('.up-field textarea')"), "at the foot, focused"
        if pg.evaluate("() => !!(window.SpeechRecognition || window.webkitSpeechRecognition)"):
            m = box(pg.get_by_role("button", name="Speak the goal"))
            assert m["width"] >= 44 and m["height"] >= 44 and f["y"] <= m["y"] and m["y"] + m["height"] <= f["y"] + f["height"], "the microphone in the field"
        shot(pg, "phone-field")
        area.fill("Add a mute button")
        area.press("Enter")
        assert _calls(pg, host, "ideas.add")[0]["text"] == "Add a mute button"
        pg.locator(".up-field").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_nothing_in_the_hand_the_line_the_row_of_the_plus_card_alone_and_the_top_row_stay(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        assert context_of(pg).count() == 0 and cards(pg).count() == 0 and pg.locator(".up-look").count() == 0
        line, w, h = box(pg.get_by_text("Nothing waits for you.", exact=True)), pg.viewport_size["width"], pg.viewport_size["height"]
        assert abs(line["x"] + line["width"] / 2 - w / 2) <= 3 and 0.3 * h < line["y"] + line["height"] / 2 < 0.7 * h, "in the middle"
        assert pots(pg).count() == 4 and crown(pg).count() == 1 and pg.locator(".up-die").count() == 1 and plus(pg).count() == 1 and pg.locator(".up-pile").count() == 0
        shot(pg, "phone-empty")
        plus(pg).click()
        pg.locator(".up-field textarea").wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_work_moved_on_the_line_over_the_top_row_and_the_frame_on_the_tool_now(gui):
    pg, host, log = open_up(gui, "moved")
    try:
        strip = pg.locator(".hand-up .table-notice")
        assert strip.inner_text().strip() == LINE and "/races/peon-crown" in strip.locator("img").get_attribute("src")
        assert box(strip)["y"] + box(strip)["height"] <= box(pg.locator(".up-top"))["y"] + 1, "at the very top, over the top row"
        framed = pg.locator(".hand-up .up-pot[data-default='1']")
        assert framed.get_attribute("data-provider") == "codex" and framed.get_attribute("aria-label").endswith(", the default")
        dry = pots(pg).nth(0)
        assert dry.locator(".up-pot__share").inner_text() == "0%" and dry.get_attribute("data-level") == "danger"
        x = box(strip.get_by_role("button", name="Dismiss"))
        assert x["width"] >= 44 and x["height"] >= 44
        shot(pg, "phone-moved")
        strip.get_by_role("button", name="Dismiss").click()
        assert pg.locator(".hand-up .table-notice").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_go_on_paid_is_a_card_of_the_row_with_the_orkmasters_context_and_its_two_buttons(gui):
    pg, host, log = open_up(gui, "paid")
    try:
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "orkmaster · party game" and "/races/peon-crown" in c.locator("img").get_attribute("src")
        assert c.locator(".up-ctx__goal").count() == 0 and c.locator(".up-ctx__rec").count() == 0, "no goal, no pick"
        assert c.locator(".up-ctx__wait").inner_text().strip() == "The work waits for your answer"
        assert c.evaluate("(e) => e.tagName") == "DIV", "nothing to open: it has no goal"
        card = pg.locator(".hand-up .hand-lifted")
        assert card.locator(".hand-card__name").inner_text().strip() == "Go on paid?" and card.locator(".hand-card__gem .ork-gem").inner_text().strip() == "$0.40"
        yes, wait = card.get_by_role("button", name="Go on, paid"), card.get_by_role("button", name="Wait for Thu 18:00")
        assert yes.count() == 1 and wait.count() == 1 and box(yes)["height"] >= 44
        framed = pg.locator(".hand-up .up-pot[data-default='1']")
        assert framed.count() == 1 and pots(pg).nth(2).locator(".up-pot__share").inner_text() == "2%"
        shot(pg, "phone-paid")
        yes.click()
        assert _calls(pg, host, "ideas.paid") == [{"yes": True}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_its_side_a_phone_shows_the_hand_not_the_table_and_the_goal_stays_picked(gui):
    pg, host, log = open_up(gui, kind="side")
    try:
        assert pg.locator(".frame").get_attribute("data-upright") == "1" and pg.locator(".frame-table").is_hidden() and pg.locator(".hand-up").is_visible()
        assert name_of(pg) == SIGN_IN_Q and crown(pg).count() == 1 and plus(pg).count() == 1 and cards(pg).count() == 2
        assert sig(pg, "frame/state.js", "picked") == "signin"
        top, row = box(pg.locator(".up-top")), box(pg.locator(".up-row"))
        assert row["y"] + row["height"] <= pg.viewport_size["height"] + 1 and box(pg.locator(".up-look"))["height"] >= 120, "the middle keeps room on its side"
        shot(pg, "side-question")
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_selector(".hand-up", timeout=WAIT_MS)
        assert name_of(pg) == SIGN_IN_Q
    finally:
        pg.close()
    assert not log, "\n".join(log)


def ready_card(pg):
    return pg.locator(".hand-up .hand-ready")


def to_ready(pg):
    pg.locator('.up-card[data-kind="ready"]').first.click()
    ready_card(pg).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('.hand-ready')?.dataset.portal !== 'wait'", timeout=WAIT_MS)


def ready_name(pg):
    c = ready_card(pg)
    return c.locator(".hand-card__name").inner_text().strip() if c.count() else ""


def test_a_goal_ready_for_main_is_releases_card_after_the_questions_with_the_portal_on_it(gui):
    pg, host, log = open_up(gui, "ready")
    try:
        to_ready(pg)
        assert picked_card(pg).get_attribute("data-key") == "ready:music"
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "release" and "/races/lich" in c.locator("img").get_attribute("src")
        assert c.locator(".up-ctx__goal").inner_text().strip() == "Lobby" and c.locator(".ork-elem.void").count() == 1 and c.locator(".ork-sign.screen").count() == 1
        assert c.locator(".up-ctx__why").inner_text().strip() == "Lobby and Reconnect are done and their checks are green"
        card = ready_card(pg)
        assert ready_name(pg) == "Lobby is ready for main" and card.locator(".hand-card__party").inner_text().strip().lower() == "release"
        assert card.locator(".hand-ready__line").inner_text().strip() == "Into main: Lobby, and Reconnect it stands on"
        door = card.locator("button.ork-portal")
        assert door.get_attribute("aria-label") == "Send Lobby and Reconnect to main" and card.locator(".hand-ready__label").text_content().strip() == "Main"
        assert card.get_by_role("button", name="Later").count() == 1 and box(card.get_by_role("button", name="Later"))["height"] >= 44
        assert "is-new" in door.get_attribute("class") and card.locator(".hand-ready__hint").inner_text().strip() == "Tap the portal to send it to main", "the first time"
        pg.wait_for_timeout(300)
        assert len(_calls(pg, host, "ideas.to_main_plan")) == 1, "the plan is asked once"
        assert cards(pg).nth(3).get_attribute("data-key") == "ready:codes" and cards(pg).nth(3).locator(".up-card__name").inner_text().strip() == "Reconnect is ready for main", "the other ready goal lies beside it in the row"
        shot(pg, "phone-portal")
        assert _calls(pg, host, "ideas.to_main") == []
        door.click()
        assert _calls(pg, host, "ideas.to_main") == [{"idea": "music"}]
        pg.wait_for_function("() => !document.querySelector('.hand-ready') || document.querySelector('.hand-ready .hand-card__name').textContent.trim() !== 'Lobby is ready for main'", timeout=WAIT_MS)
        assert ready_name(pg) == "" or ready_name(pg) == "Reconnect is ready for main"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_sealed_goal_says_its_reason_in_danger_and_a_press_sends_nothing(gui):
    host = UprightHost("readyonly")
    host.plans["music"]["sealed"] = "Lobby does not apply to main cleanly: player.ts"
    pg, host, log = open_up(gui, host=host)
    try:
        to_ready(pg)
        door = ready_card(pg).locator("button.ork-portal")
        assert "is-sealed" in door.get_attribute("class") and door.get_attribute("aria-label").startswith("Sealed: ")
        reason = ready_card(pg).locator(".hand-ready__sealed")
        assert reason.inner_text().strip() == "Sealed: Lobby does not apply to main cleanly: player.ts"
        assert reason.evaluate("(e) => getComputedStyle(e).color") == css_colour(pg, "--ork-danger")
        assert ready_card(pg).locator(".hand-ready__hint").count() == 0, "no first-time line over a sealed portal"
        shot(pg, "phone-sealed")
        door.click()
        pg.wait_for_timeout(300)
        assert _calls(pg, host, "ideas.to_main") == [] and ready_card(pg).count() == 1
        assert reason.inner_text().strip().startswith("Sealed: ")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_later_puts_the_card_back_and_the_next_comes_while_the_goal_stays_ready(gui):
    pg, host, log = open_up(gui, "readyonly")
    try:
        assert cards(pg).count() == 2 and ready_card(pg).count() == 1, "with only goals ready for main the first is picked"
        to_ready(pg)
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.wait_for_function("() => document.querySelector('.hand-ready .hand-card__name')?.textContent.trim() === 'Reconnect is ready for main'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main") == [] and [g["slug"] for g in host.gate_doc["ideas"]] == ["music", "codes"], "the goal stays ready in the discard"
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.get_by_text("Nothing waits for you.", exact=True).wait_for(timeout=WAIT_MS)
        assert cards(pg).count() == 0
    finally:
        pg.close()


def test_the_first_time_line_is_not_said_again_once_seen(gui):
    pg, host, log = open_up(gui, "readyonly")
    try:
        pg.evaluate("() => localStorage.setItem('orkboard.portal.seen', '1')")
        pg.reload()
        pg.wait_for_selector(".hand-ready", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.hand-ready')?.dataset.portal !== 'wait'", timeout=WAIT_MS)
        assert ready_card(pg).locator(".hand-ready__hint").count() == 0 and "is-new" not in ready_card(pg).locator("button.ork-portal").get_attribute("class")
    finally:
        pg.close()


def test_a_narrow_window_with_a_fine_pointer_and_the_wide_desktop_are_unchanged(gui):
    for kind in ("fine", "wide"):
        pg, host, log = open_up(gui, "ready", kind, ready=".hand-stack")
        try:
            assert pg.locator(".frame").get_attribute("data-upright") is None and pg.locator(".hand-up").count() == 0 and pg.locator(".up-ctx").count() == 0
            assert pg.locator(".frame-table").is_visible() and pg.locator(".table-tabs").is_visible() and pg.locator(".hand-places").count() == 1
            assert pg.locator(".hand-mana .ork-potion").count() == 4 and pg.locator(".up-pot, .up-top, .up-row, .up-crown").count() == 0, "the potions, as before: no crown, no row"
            assert pg.locator(".hand-plus").count() == 1 and pg.locator(".hand-lifted").count() == 0 and pg.locator(".up-card, .up-plus").count() == 0 and pg.locator(".hand-ready").count() == 0
            assert pg.locator(".table-menu__btn").count() >= 1 and pg.get_by_role("button", name="The leaders and their goals").count() == 0, "no crown"
            shot(pg, f"{kind}-unchanged")
        finally:
            pg.close()
