"""The phone's hand (docs/specs/103-the-phones-app-a-native-frame.md §1, part A; decisions §174.1, §178, §179, §180; the mockups docs/mockups/phone/hand.html and portal.html), in a real browser against a stub host, with touch (390 × 844
upright, 844 × 390 on its side): the one screen is the hand, no Board; from the top the tools' row and **…** (Stop all, the project and its switcher, Settings), the top card's context between the arrows to the previous and next goal
(their leader's head and element) with *Spec* under it, ONE goal's cards (the first on top, 68% of the screen wide, named by the question itself, the goal's other cards only edges under it, a swipe or an arrow to the next goal), the
green deck *New goal* under the thumb and the field it opens over the keyboard; a goal ready for main as Release's card with the portal on it; the Orkmaster's line; *Go on paid?*; the empty hand; and the same page at a narrow
width with a fine pointer and at 1280 × 800 unchanged. Screenshots to $UPRIGHT_SHOTS when it is set."""
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
        asked = [{"ask": "Which sign-in first?", "choices": SIGN_IN["choices"], "pick": 0, "why": WHY, "by": GRUNT, "look": False}]
        signin = node("signin", "tech", "Sign-in", "hand", state="talk", element="dust", asked=asked, type={"sign": "feature", "name": "Feature"})
        phones = node("phones", "design", "Round timer shows on every phone", "hand", state="asks", element="meadow", type={"sign": "screen", "name": "Screen"},
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
    """The page against the stub: `kind` "phone" (390 × 844 with touch), "fine" (the same width with a mouse), "wide" (1280 × 800)."""
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


def tools(pg):
    return pg.locator(".hand-up .hand-mana--tools .hand-pot")


def context_of(pg):
    return pg.locator(".hand-up .up-ctx")


def more(pg):
    return pg.get_by_role("button", name="More", exact=True)


def name_of(pg):
    return pg.locator(".hand-lifted .hand-card__name").inner_text().strip()


def wait_title(pg, text):
    pg.wait_for_function("(t) => document.querySelector('.hand-lifted .hand-card__name')?.textContent.trim() === t", arg=text, timeout=WAIT_MS)


def swipe(pg, dx, x=195, y=500):
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x + dx / 2, y, steps=4)
    pg.mouse.move(x + dx, y, steps=4)
    pg.mouse.up()


def test_the_tools_are_their_marks_and_shares_no_bottle_each_44_px_the_default_framed(gui):
    pg, host, log = open_up(gui)
    try:
        t = tools(pg)
        assert [b.get_attribute("data-provider") for b in t.all()] == ["claude", "agy", "codex", "cursor"]
        assert [b.get_attribute("aria-label") for b in t.all()] == ["Claude Code: 62% of the week left, the default", "Antigravity: 80% of the week left", "Codex: 41% of the week left", "Cursor: 18% of the week left"]
        assert [b.get_attribute("title") for b in t.all()] == [b.get_attribute("aria-label") for b in t.all()], "the potions' words"
        assert [b.locator(".hand-pot__share").inner_text() for b in t.all()] == ["62%", "80%", "41%", "18%"]
        assert pg.locator(".hand-up .ork-potion").count() == 0, "no bottle"
        mark = t.nth(0).locator("img.ork-mark")
        assert mark.get_attribute("src").endswith("/marks/harness-claude.png") and mark.bounding_box()["y"] < t.nth(0).locator(".hand-pot__share").bounding_box()["y"], "the mark in its own colour, the share under it"
        for b in t.all():
            r = box(b)
            assert r["width"] >= 44 and r["height"] >= 44
        board = box(more(pg))
        assert max(box(b)["height"] for b in t.all()) <= board["height"] + 0.5, "the row no taller than the …"
        assert [b.get_attribute("data-level") for b in t.all()] == ["ok", "ok", "ok", "warn"] or t.nth(3).get_attribute("data-level") != t.nth(0).get_attribute("data-level")
        colours = pg.evaluate("() => [...document.querySelectorAll('.hand-up .hand-pot--tool .hand-pot__share')].map((e) => getComputedStyle(e).color)")
        assert colours[3] != colours[0], "the share is in the warning's colour as it runs low"
        framed = pg.locator(".hand-up .hand-pot--tool[data-default='1']")
        assert framed.count() == 1 and framed.get_attribute("data-provider") == "claude"
        f, c = box(pg.locator(".hand-up .hand-mana__frame")), box(framed)
        assert abs(f["x"] - c["x"]) <= 1 and abs(f["y"] - c["y"]) <= 1 and abs(f["width"] - c["width"]) <= 1
        t.nth(2).click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "limits", "a press opens what used it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_context_says_who_which_goal_why_the_pick_and_who_waits_in_a_quarter_of_the_screen(gui):
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
        assert box(c)["height"] <= pg.viewport_size["height"] / 4 + 1
        assert c.evaluate("(e) => e.tagName") == "BUTTON", "a press opens the goal's way"
        text = pg.locator(".hand-up").inner_text()
        assert "deck" not in text.lower() and "stack" not in text.lower(), "never those words in the interface"
        shot(pg, "phone-context")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_context_scrolls_inside_past_a_quarter_of_the_screen(gui):
    pg, host, log = open_up(gui)
    try:
        pg.evaluate("() => { const w = document.querySelector('.up-ctx__why'); w.textContent = Array(40).fill('A long reason that goes on and on.').join(' '); }")
        c = context_of(pg)
        assert box(c)["height"] <= pg.viewport_size["height"] / 4 + 1
        assert c.evaluate("(e) => e.scrollHeight > e.clientHeight && getComputedStyle(e).overflowY") in ("auto", "scroll", True) or c.evaluate("(e) => e.scrollHeight > e.clientHeight")
        s = box(pg.locator(".up-stack"))
        c.evaluate("(e) => { e.scrollTop = 40; }")
        assert box(pg.locator(".up-stack")) == s, "the stack never moves"
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
        wait_title(pg, "Round timer shows on every phone")
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
        assert pg.locator(".hand-lifted .hand-card__name").inner_text().strip() == "Which sign-in first?", "the same card"
    finally:
        pg.close()


def test_the_work_moved_on_the_line_over_the_tools_and_the_frame_on_the_tool_now(gui):
    pg, host, log = open_up(gui, "moved")
    try:
        strip = pg.locator(".hand-up .table-notice")
        assert strip.inner_text().strip() == LINE and "/races/peon-crown" in strip.locator("img").get_attribute("src")
        assert box(strip)["y"] + box(strip)["height"] <= box(pg.locator(".up-top"))["y"] + 1, "at the very top, over the tools' row"
        framed = pg.locator(".hand-up .hand-pot--tool[data-default='1']")
        assert framed.get_attribute("data-provider") == "codex" and framed.get_attribute("aria-label").endswith(", the default")
        dry = tools(pg).nth(0)
        assert dry.locator(".hand-pot__share").inner_text() == "0%" and dry.get_attribute("data-level") == "danger"
        x = box(strip.get_by_role("button", name="Dismiss"))
        assert x["width"] >= 44 and x["height"] >= 44
        shot(pg, "phone-moved")
        strip.get_by_role("button", name="Dismiss").click()
        assert pg.locator(".hand-up .table-notice").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_go_on_paid_is_a_card_of_the_stack_with_the_orkmasters_context_and_its_two_buttons(gui):
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
        framed = pg.locator(".hand-up .hand-pot--tool[data-default='1']")
        assert framed.count() == 1 and tools(pg).nth(2).locator(".hand-pot__share").inner_text() == "2%"
        shot(pg, "phone-paid")
        yes.click()
        assert _calls(pg, host, "ideas.paid") == [{"yes": True}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_first_screen_is_the_hand_from_the_tools_row_to_the_card_with_no_board_and_no_blank_card(gui):
    pg, host, log = open_up(gui)
    try:
        assert pg.locator(".frame").get_attribute("data-upright") == "1"
        assert pg.locator(".frame-table").is_hidden() and pg.locator(".table-tabs").is_hidden(), "no Board on a phone"
        assert pg.get_by_role("button", name="The Board").count() == 0 and "Turn the phone" not in pg.locator("body").inner_text()
        top, m, nav, ctx, stack = box(pg.locator(".up-top")), box(more(pg)), box(pg.locator(".up-navrow")), box(context_of(pg)), box(pg.locator(".up-stack"))
        assert top["y"] < nav["y"] < stack["y"], "the tools' row and the …, the context between the arrows, the card"
        assert ctx["y"] >= top["y"] + top["height"] - 1 and stack["y"] >= nav["y"] + nav["height"] - 1
        assert m["width"] >= 44 and m["height"] >= 44 and m["x"] > box(tools(pg).last)["x"] and m["x"] + m["width"] > pg.viewport_size["width"] - 24, "the …: a 44 px target at the top right"
        assert pg.locator(".hand-up .hand-plus").count() == 0 and pg.locator(".up-foot").count() == 0, "no full-width blank card"
        shot(pg, "phone-question")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_more_menu_holds_stop_all_the_project_and_its_switcher_and_settings_each_44_px(gui):
    pg, host, log = open_up(gui)
    try:
        assert more(pg).get_attribute("aria-expanded") == "false"
        more(pg).click()
        menu = pg.get_by_role("menu", name="More")
        menu.wait_for(timeout=WAIT_MS)
        assert more(pg).get_attribute("aria-expanded") == "true"
        assert menu.get_by_role("menuitem").all_inner_texts() == ["Stop all", "Switch project", "Settings"]
        assert menu.locator("[data-project]").inner_text().strip() == "Party game"
        for b in menu.get_by_role("menuitem").all():
            assert box(b)["height"] >= 44
        r, w = box(menu), pg.viewport_size["width"]
        assert r["x"] >= 0 and r["x"] + r["width"] <= w + 1
        shot(pg, "phone-menu")
        pg.keyboard.press("Escape")
        menu.wait_for(state="detached", timeout=WAIT_MS)
        more(pg).click()
        menu.wait_for(timeout=WAIT_MS)
        pg.mouse.click(40, 700)
        menu.wait_for(state="detached", timeout=WAIT_MS)
        more(pg).click()
        menu.get_by_role("menuitem", name="Settings").click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "settings" and pg.locator(".hand-up").is_hidden()
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        more(pg).click()
        menu.get_by_role("menuitem", name="Switch project").click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "projects"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_stop_all_in_the_menu_sends_the_halt_command(gui):
    pg, host, log = open_up(gui)
    try:
        more(pg).click()
        pg.get_by_role("menu", name="More").get_by_role("menuitem", name="Stop all").click()
        pg.wait_for_timeout(300)
        assert any("halt" in str(c[0]) for c in host.log) or any("halt" in str(c) for c in host.log)
    finally:
        pg.close()


def test_the_top_card_is_68_percent_of_the_screen_turned_a_degree_named_by_the_question_with_its_choices_two_by_two(gui):
    pg, host, log = open_up(gui)
    try:
        card = pg.locator(".hand-up .hand-lifted")
        assert card.count() == 1 and name_of(pg) == "Which sign-in first?", "the question itself is the card's name"
        assert "Sign-in" in context_of(pg).inner_text(), "the goal's name is in the context above"
        ow, vw = card.evaluate("(e) => e.offsetWidth"), pg.viewport_size["width"]
        assert abs(ow / vw - 0.68) < 0.015 and 262 <= round(ow) <= 268, f"about 264 of 390 px: {ow}"
        b = box(card)
        assert abs((b["x"] + b["width"] / 2) - vw / 2) <= 3, "centred"
        assert card.evaluate("(e) => getComputedStyle(e).rotate") not in ("none", "0deg"), "turned a degree"
        cells = [box(c) for c in card.locator(".q-card").all()]
        assert len(cells) == 4 and cells[0]["x"] == pytest.approx(cells[2]["x"], abs=2) and cells[1]["x"] > cells[0]["x"] + 40 and cells[2]["y"] > cells[0]["y"] + 40, "two by two"
        assert [c.inner_text().strip().splitlines()[0] for c in card.locator(".q-card").all()] == ["Email link", "Passkey", "Google", "Other…"]
        assert card.locator(".q-card.is-pick").inner_text().strip().startswith("Email link"), "the leader's pick raised"
        assert card.get_by_role("button", name="Let Tech lead decide").count() == 1
        assert card.locator(".hand-card__party").text_content().strip() == "Tech"
        assert pg.locator(".up-stack .up-edge").count() == 0, "one goal at a time: no edge, no fan of the other goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_goals_other_cards_are_edges_under_the_top_card(gui):
    pg, host, log = open_up(gui, "deep")
    try:
        assert pg.locator(".up-stack .up-edge").count() == 1 and name_of(pg) == "Which sign-in first?"
        shot(pg, "phone-deep")
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        wait_title(pg, "Keep passwords?")
        assert pg.locator(".up-stack .up-edge").count() == 0 and _calls(pg, host, "ideas.talk_answer") == [], "the answers go together after the last"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_choice_answers_at_once_and_the_next_goal_comes_with_its_context(gui):
    pg, host, log = open_up(gui)
    try:
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}]
        wait_title(pg, "Round timer shows on every phone")
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "design" and c.locator(".up-ctx__goal").inner_text().strip() == "Round timer shows on every phone"
        assert c.locator(".up-ctx__why").inner_text().strip() == "One clock: every phone agrees." and c.locator(".up-ctx__rec").inner_text().strip() == "Recommended: Server counts, phones show it"
        assert c.locator(".up-ctx__wait").count() == 0, "work does not wait for it"
        assert pg.locator(".up-stack .up-edge").count() == 0
        assert pg.locator(".up-nav:not([disabled])").count() == 0, "the last goal: no arrow beyond it"
        shot(pg, "phone-next")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def arrows(pg):
    return pg.locator(".up-nav")


def test_the_arrows_and_a_swipe_go_along_the_goals_with_the_neighbours_head_and_element(gui):
    pg, host, log = open_up(gui)
    try:
        prev, nxt = arrows(pg).nth(0), arrows(pg).nth(1)
        assert prev.is_disabled() and not nxt.is_disabled(), "nothing beyond the first: disabled"
        assert nxt.get_attribute("aria-label") == "Next goal: Round timer shows on every phone"
        r = box(nxt)
        assert r["width"] >= 44 and r["height"] >= 44
        who = nxt.locator(".up-nav__who")
        assert "/races/" in who.locator("img").get_attribute("src")
        hb = box(who.locator("img"))
        assert round(hb["width"]) == 24 and round(hb["height"]) == 22, "the head at 24 x 22"
        assert who.locator(".ork-elem.meadow").count() == 1, "the neighbour goal's element"
        assert nxt.locator(".ork-sign").count() == 0 and not any(ch.isdigit() for ch in nxt.inner_text()), "no alert sign, no number"
        shot(pg, "phone-arrows")
        nxt.click()
        wait_title(pg, "Round timer shows on every phone")
        assert context_of(pg).locator(".up-ctx__goal").inner_text().strip() == "Round timer shows on every phone" and sig(pg, "frame/state.js", "picked") == "phones"
        assert arrows(pg).nth(1).is_disabled() and arrows(pg).nth(0).get_attribute("aria-label") == "Previous goal: Sign-in"
        swipe(pg, 140)
        wait_title(pg, "Which sign-in first?")
        swipe(pg, -140)
        wait_title(pg, "Round timer shows on every phone")
        swipe(pg, 140, x=8)
        pg.wait_for_timeout(200)
        assert name_of(pg) == "Round timer shows on every phone", "a swipe from the screen's edge is not ours"
        swipe(pg, 30)
        pg.wait_for_timeout(200)
        assert name_of(pg) == "Round timer shows on every phone", "a short move is not a swipe"
        pg.mouse.move(195, 500)
        pg.mouse.down()
        pg.mouse.move(215, 640, steps=6)
        pg.mouse.up()
        assert name_of(pg) == "Round timer shows on every phone", "a vertical move is a scroll"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_spec_under_the_context_opens_the_spec_page_or_talk_while_it_is_not_written(gui):
    pg, host, log = open_up(gui)
    try:
        spec = pg.locator(".up-spec")
        assert spec.inner_text().strip() == "The spec is written after your answers" and box(spec)["height"] >= 44 and spec.get_attribute("data-page") == "talk"
        spec.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "talk"
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        pg.evaluate("""async () => { const s = await import('/static/js/shell/store.js'); const m = s.mapData.value; m.nodes.find((n) => n.slug === 'phones').state = 'decided'; s.mapData.value = { ...m, nodes: [...m.nodes] }; }""")
        arrows(pg).nth(1).click()
        wait_title(pg, "Round timer shows on every phone")
        spec = pg.locator(".up-spec")
        assert spec.inner_text().strip() == "Spec" and spec.get_attribute("data-page") == "spec"
        spec.click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "spec"
    finally:
        pg.close()


def test_a_card_of_no_goal_has_no_spec_button(gui):
    pg, host, log = open_up(gui, "paid")
    try:
        assert pg.locator(".up-spec").count() == 0 and arrows(pg).count() == 2 and pg.locator(".up-nav:not([disabled])").count() == 0
    finally:
        pg.close()


def css_colour(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = `var(${t})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def test_new_goal_is_the_green_deck_under_the_thumb_and_opens_the_field_over_the_keyboard_with_the_microphone(gui):
    pg, host, log = open_up(gui)
    try:
        deck = pg.get_by_role("button", name="New goal")
        r, w, h = box(deck), pg.viewport_size["width"], pg.viewport_size["height"]
        assert deck.count() == 1 and 52 <= r["width"] <= 64 and 72 <= r["height"] <= 84, "about 56 x 76"
        assert r["x"] + r["width"] >= w - 20 and r["y"] + r["height"] >= h - 20, "bottom right"
        assert deck.evaluate("(e) => getComputedStyle(e).position") == "fixed" and deck.locator("svg.ork-icon").count() == 1
        assert pg.locator(".up-deck__back").evaluate("(e) => getComputedStyle(e).color") == css_colour(pg, "--ork-action")
        shot(pg, "phone-deck")
        deck.click()
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


def test_with_nothing_in_the_hand_the_line_and_the_deck_and_the_row_stay(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        assert context_of(pg).count() == 0 and pg.locator(".up-stack").count() == 0 and arrows(pg).count() == 0
        line, w, h = box(pg.get_by_text("Nothing waits for you.", exact=True)), pg.viewport_size["width"], pg.viewport_size["height"]
        assert abs(line["x"] + line["width"] / 2 - w / 2) <= 3 and 0.3 * h < line["y"] + line["height"] / 2 < 0.7 * h, "in the middle"
        assert tools(pg).count() == 4 and more(pg).count() == 1 and pg.get_by_role("button", name="New goal").count() == 1
        shot(pg, "phone-empty")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_its_side_a_phone_shows_the_hand_not_the_table_and_the_goal_stays_picked(gui):
    pg, host, log = open_up(gui, kind="side")
    try:
        assert pg.locator(".frame").get_attribute("data-upright") == "1" and pg.locator(".frame-table").is_hidden() and pg.locator(".hand-up").is_visible()
        assert name_of(pg) == "Which sign-in first?" and more(pg).count() == 1 and pg.get_by_role("button", name="New goal").count() == 1
        assert sig(pg, "frame/state.js", "picked") == "signin"
        shot(pg, "side-question")
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_selector(".hand-up", timeout=WAIT_MS)
        assert name_of(pg) == "Which sign-in first?"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def ready_card(pg):
    return pg.locator(".hand-up .hand-ready")


def to_ready(pg):
    for _ in range(4):
        if ready_card(pg).count():
            break
        arrows(pg).nth(1).click()
        pg.wait_for_timeout(150)
    ready_card(pg).wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('.hand-ready')?.dataset.portal !== 'wait'", timeout=WAIT_MS)


def ready_name(pg):
    c = ready_card(pg)
    return c.locator(".hand-card__name").inner_text().strip() if c.count() else ""


def test_a_goal_ready_for_main_is_releases_card_after_the_questions_with_the_portal_on_it(gui):
    pg, host, log = open_up(gui, "ready")
    try:
        to_ready(pg)
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
        assert arrows(pg).nth(1).is_enabled() and arrows(pg).nth(1).get_attribute("aria-label") == "Next goal: Reconnect", "the other ready goal lies beyond it"
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
        to_ready(pg)
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.wait_for_function("() => document.querySelector('.hand-ready .hand-card__name')?.textContent.trim() === 'Reconnect is ready for main'", timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.to_main") == [] and [g["slug"] for g in host.gate_doc["ideas"]] == ["music", "codes"], "the goal stays ready in the discard"
        ready_card(pg).get_by_role("button", name="Later").click()
        pg.get_by_text("Nothing waits for you.", exact=True).wait_for(timeout=WAIT_MS)
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
            assert pg.locator(".hand-mana .ork-potion").count() == 4 and pg.locator(".hand-mana--tools").count() == 0, "the potions, as before"
            assert pg.locator(".hand-plus").count() == 1 and pg.locator(".hand-lifted").count() == 0 and pg.locator(".up-deck").count() == 0 and pg.locator(".hand-ready").count() == 0
            shot(pg, f"{kind}-unchanged")
        finally:
            pg.close()
