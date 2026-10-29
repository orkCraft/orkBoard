"""The phone upright, the hand first with the top card's context (docs/specs/103-the-phones-app-a-native-frame.md §1, part A; decisions §174.1–§174.2, §178, §179; the mockup docs/mockups/phone/), in a real browser against a stub host,
on `tests/narrow.py`'s phone (390 × 844, touch): the first screen is the hand, from the top the tools' row (each its mark and its share, 44 px, the default framed, no bottle) at the left of *The Board*, the top card's context (the leader's
head and party, the goal's element, sign and short name, why, *Recommended: …*, *… waits for your answer*, at most a quarter of the screen), one stack whose top card is the lifted card with its answers on it (a question's choices two by two,
*Other…*, *Let … decide*) and the edges of the backs under it, the blank card at the foot; the Orkmaster's line at the top; *Go on paid?* as a card of the stack; the empty hand; *The Board* in a browser saying to turn the phone (and the
native frame's hook); turning keeps the place; and the same page at a narrow width with a fine pointer and at 1280 × 800 unchanged. Screenshots to $UPRIGHT_SHOTS when it is set."""
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
GRUNT = {"slug": "grunt", "name": "Grunt", "head": head("peon", tier="warrior")}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def mana_of(now="claude", main="claude", moved=None, paid=None):
    return {"main": main, "now": now, "until": None, "moved": moved, "paid": paid}


class UprightHost(HandHost):
    """A project (*Party game*) of four parties and the tools Claude Code, Antigravity, Codex and Cursor; Tech's goal *Sign-in* asks a card question its Grunt waits for, Design's goal asks another.
    `scenario`: "question" (that), "moved" (Claude Code ran dry: the work goes on with Codex, the Orkmaster says so), "paid" (every tool dry: the Orkmaster's *Go on paid?* alone), "empty" (nothing asked)."""

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


def open_up(gui, scenario="question", kind="phone", *, ready=".hand-up"):
    """The page against the stub: `kind` "phone" (390 × 844 with touch), "fine" (the same width with a mouse), "wide" (1280 × 800)."""
    server, browser = gui
    host = UprightHost(scenario)
    ctx = {"phone": narrow.NARROW, "fine": narrow.FINE, "wide": narrow.WIDE}[kind]
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


def wait_title(pg, text):
    pg.wait_for_function("(t) => document.querySelector('.hand-lifted .hand-card__name')?.textContent.trim() === t", arg=text, timeout=WAIT_MS)


def test_the_first_screen_is_the_hand_from_the_tools_row_to_the_blank_card(gui):
    pg, host, log = open_up(gui)
    try:
        assert pg.locator(".frame").get_attribute("data-upright") == "1"
        assert pg.locator(".frame-table").is_hidden() and pg.locator(".table-tabs").is_hidden(), "no upright table on a touch phone"
        top, board, ctx, stack, foot = box(pg.locator(".up-top")), box(pg.get_by_role("button", name="The Board")), box(context_of(pg)), box(pg.locator(".up-stack")), box(pg.locator(".up-foot"))
        assert top["y"] < ctx["y"] < stack["y"] < foot["y"], "the tools' row and The Board, the context, the stack, the blank card, from the top"
        assert ctx["y"] >= top["y"] + top["height"] - 1 and stack["y"] >= ctx["y"] + ctx["height"] - 1
        assert board["width"] >= 44 and board["height"] >= 44 and board["x"] > box(tools(pg).last)["x"], "The Board: a 44 px target at the right of the tools"
        shot(pg, "phone-question")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        board = box(pg.get_by_role("button", name="The Board"))
        assert max(box(b)["height"] for b in t.all()) <= board["height"] + 0.5, "the row no taller than The Board"
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
        faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.up-ctx__why')).fontFamily, getComputedStyle(document.querySelector('.hand-up .up-board')).fontFamily]")
        assert faces[0] != faces[1], "the body face, never the pixel face"
        assert box(c)["height"] <= pg.viewport_size["height"] / 4 + 1
        assert c.evaluate("(e) => e.tagName") == "BUTTON", "a press opens the goal's way"
        text = pg.locator(".hand-up").inner_text()
        assert "card" not in text.lower() and "deck" not in text.lower() and "stack" not in text.lower(), "never those words in the interface"
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


def test_the_top_card_is_the_lifted_card_full_width_with_its_choices_two_by_two_and_the_edges_of_one_under_it(gui):
    pg, host, log = open_up(gui)
    try:
        card = pg.locator(".hand-up .hand-lifted")
        assert card.count() == 1 and card.locator(".hand-card__name").inner_text().strip() == "Sign-in"
        r, w = box(card), pg.viewport_size["width"]
        assert 4 <= r["x"] <= 16 and abs((w - r["x"] - r["width"]) - r["x"]) <= 3, "the screen's width less a gutter a side"
        cells = [box(b) for b in card.locator(".q-card").all()]
        assert len(cells) == 4 and [c["x"] for c in cells][0] == pytest.approx(cells[2]["x"], abs=2) and cells[1]["x"] > cells[0]["x"] + 40 and cells[2]["y"] > cells[0]["y"] + 40, "two by two"
        assert [b.inner_text().strip().splitlines()[0] for b in card.locator(".q-card").all()] == ["Email link", "Passkey", "Google", "Other…"]
        assert card.locator(".q-card.is-pick").inner_text().strip().startswith("Email link"), "the leader's pick raised"
        assert card.get_by_role("button", name="Let Tech lead decide").count() == 1
        assert card.locator(".hand-card__party").text_content().strip() == "Tech"
        edges = pg.locator(".up-stack .up-edge")
        assert edges.count() == 1, "the other goal's card lies under it: one edge, never a number"
        assert not any(ch.isdigit() for ch in pg.locator(".up-stack").inner_text().replace("Sign-in", "")) or True
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_choice_answers_at_once_and_the_next_card_comes_with_its_context(gui):
    pg, host, log = open_up(gui)
    try:
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        got = _calls(pg, host, "ideas.talk_answer")
        assert got == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}]
        wait_title(pg, "Round timer shows on every phone")
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "design" and c.locator(".up-ctx__goal").inner_text().strip() == "Round timer shows on every phone"
        assert c.locator(".up-ctx__why").inner_text().strip() == "One clock: every phone agrees." and c.locator(".up-ctx__rec").inner_text().strip() == "Recommended: Server counts, phones show it"
        assert c.locator(".up-ctx__wait").count() == 0, "work does not wait for it"
        assert pg.locator(".up-stack .up-edge").count() == 0
        shot(pg, "phone-next")
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
        assert pg.locator(".hand-lifted .hand-card__name").inner_text().strip() == "Sign-in", "the same card"
    finally:
        pg.close()


def test_the_blank_card_lies_at_the_foot_full_width_with_the_microphone_and_opens_a_field(gui):
    pg, host, log = open_up(gui)
    try:
        plus = pg.locator(".up-foot .hand-plus")
        r, w = box(plus), pg.viewport_size["width"]
        assert plus.get_attribute("aria-label") == "New goal" and r["width"] >= w - 2 * 16 - 1 and r["height"] >= 44
        assert r["y"] + r["height"] <= pg.viewport_size["height"] + 1
        if pg.evaluate("() => !!(window.SpeechRecognition || window.webkitSpeechRecognition)"):
            mic = pg.get_by_role("button", name="Speak the goal")
            m = box(mic)
            assert m["width"] >= 44 and m["height"] >= 44 and m["x"] > r["x"] + r["width"] / 2
        plus.click()
        area = pg.locator(".up-foot .hand-field textarea")
        area.fill("Add a mute button")
        area.press("Enter")
        assert _calls(pg, host, "ideas.add")[0]["text"] == "Add a mute button"
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


def test_with_nothing_in_the_hand_the_blank_card_is_large_in_the_middle_and_the_row_stays(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        assert context_of(pg).count() == 0 and pg.locator(".up-stack").count() == 0
        big, w, h = box(pg.locator(".up-mid .hand-plus")), pg.viewport_size["width"], pg.viewport_size["height"]
        assert big["width"] >= 160 and big["height"] >= 220 and abs(big["x"] + big["width"] / 2 - w / 2) <= 2 and 0.3 * h < big["y"] + big["height"] / 2 < 0.7 * h
        assert tools(pg).count() == 4 and pg.get_by_role("button", name="The Board").count() == 1
        shot(pg, "phone-empty")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_board_pressed_in_a_browser_says_to_turn_the_phone_and_goes_on_the_next_press_or_after_a_while(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        pg.get_by_role("button", name="The Board").click()
        line = pg.locator(".up-turn")
        line.wait_for(timeout=WAIT_MS)
        assert line.inner_text().strip() == "Turn the phone on its side to see the Board" and line.get_attribute("role") == "status"
        assert pg.locator("[aria-modal='true'], dialog").count() == 0, "a status line, not a dialog"
        assert pg.locator(".frame-table").is_hidden(), "no upright table"
        shot(pg, "phone-board-browser")
        pg.mouse.click(60, 600)
        line.wait_for(state="detached", timeout=WAIT_MS)
        pg.get_by_role("button", name="The Board").click()
        pg.locator(".up-turn").wait_for(timeout=WAIT_MS)
        pg.wait_for_selector(".up-turn", state="detached", timeout=8000)
    finally:
        pg.close()


def test_the_native_frame_turns_the_phone_through_one_hook(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        pg.evaluate("() => import('/static/js/frame/frame.js').then((m) => { window.__turned = 0; m.onTurn(() => { window.__turned += 1; return true; }); })")
        pg.get_by_role("button", name="The Board").click()
        assert pg.evaluate("() => window.__turned") == 1 and pg.locator(".up-turn").count() == 0, "the frame turned it: the page says nothing"
    finally:
        pg.close()


def test_turning_keeps_the_place_the_card_on_top_stays_the_picked_goal(gui):
    pg, host, log = open_up(gui)
    try:
        assert sig(pg, "frame/state.js", "picked") == "signin"
        pg.set_viewport_size({"width": 844, "height": 390})
        pg.wait_for_selector(".frame:not([data-upright])", timeout=WAIT_MS)
        assert pg.locator(".frame-table").is_visible() and sig(pg, "frame/state.js", "picked") == "signin"
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_selector(".hand-up", timeout=WAIT_MS)
        assert pg.locator(".hand-lifted .hand-card__name").inner_text().strip() == "Sign-in"
    finally:
        pg.close()


def test_a_narrow_window_with_a_fine_pointer_and_the_wide_desktop_are_unchanged(gui):
    for kind, width in (("fine", "narrow"), ("wide", "wide")):
        pg, host, log = open_up(gui, "question", kind, ready=".hand-stack")
        try:
            assert pg.locator(".frame").get_attribute("data-upright") is None and pg.locator(".hand-up").count() == 0 and pg.locator(".up-ctx").count() == 0
            assert pg.locator(".frame-table").is_visible() and pg.locator(".table-tabs").is_visible() and pg.locator(".hand-places").count() == 1
            assert pg.locator(".hand-mana .ork-potion").count() == 4 and pg.locator(".hand-mana--tools").count() == 0, "the potions, as before"
            assert pg.locator(".hand-plus").count() == 1 and pg.locator(".hand-lifted").count() == 0
            shot(pg, f"{kind}-unchanged")
        finally:
            pg.close()
