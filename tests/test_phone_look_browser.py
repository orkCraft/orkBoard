"""The phone's middle (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5, part D; decisions §195.2; the mockup docs/mockups/phone/sidebar.html A1 and A3), in a real browser against a stub host, with touch at 390 × 844: what is looked at is the goal picked, else the
party the person picked in the menu, else the goal of the hand's first card (its card on it, answered with one tap), else nothing (*Nothing waits for you.*). A goal: its header, its phases (a press opens its page), its route by its leaders' heads (done, at work,
next), why and *<Party>'s tasks*; a goal in line: its phases, the moon and its hour. A party: its leader's header, its squad (a head opens its popover as a sheet), the tools of its sword and shield in words, its goals at work and its concerns. Screenshots to
$UPRIGHT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_context_narrow_browser import SIGN_IN_Q, TIMER_Q, WHY, UprightHost, box, cards, context_of, css_colour, name_of, open_up, pots, wait_title  # noqa: E402
from tests.test_hand_desktop_browser import head, node, sig, task  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None
SEAT_WHY = "A player who loses signal comes back to the seat they had."
SEAT = "Keep the seat when a socket reconnects"
CONCERN = {"id": "c1", "level": "alert", "what": "Lobbies live in memory: a restart drops every game.", "why": "", "fix": "", "on": "server/lobby.ts", "aspect": "hotspots"}
NOTE = {"id": "c2", "level": "note", "what": "The email link has no rate limit.", "why": "", "fix": "", "on": "auth/link.ts", "aspect": "security"}
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

    def handle(self, name, a):
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
    """Opens the menu and presses a goal's row (`kind` "goal") or a party's (`kind` "party") by its name."""
    crown(pg).click()
    pg.locator(".up-menu .up-prow").first.wait_for(timeout=WAIT_MS)
    pg.locator(".up-menu .up-grow" if kind == "goal" else ".up-menu .up-prow", has_text=name).first.click()
    pg.locator(".up-menu").wait_for(state="detached", timeout=WAIT_MS)


def look(pg):
    return pg.locator(".hand-up .up-look")


def raised(pg):
    return pg.locator('.hand-up .up-card[aria-pressed="true"]')


def test_with_a_hand_the_first_entrys_goal_is_looked_at_its_way_under_its_card_answered_with_one_tap(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        assert look(pg).get_attribute("data-look") == "goal" and look(pg).get_attribute("data-goal") == "signin" and look(pg).get_attribute("data-entry") == "goal:signin", "the goal of the hand's first card"
        head_ = pg.locator(".up-gh")
        assert head_.locator(".up-gh__name").inner_text().strip() == "Sign-in" and head_.locator(".ork-elem.dust.big").count() == 1 and head_.locator(".ork-sign.feature").count() == 1
        assert head_.locator(".up-gh__type").inner_text().strip() == "Feature · Talk"
        assert pg.locator(".up-gh__name").evaluate("(e) => [getComputedStyle(e).fontSize, getComputedStyle(e).fontWeight]") == ["20px", "600"], "its short name in the body face at 20 px"
        c = context_of(pg)
        assert c.locator(".up-ctx__who").inner_text().strip().lower() == "tech" and c.locator(".up-ctx__why").inner_text().strip() == WHY and c.locator(".up-ctx__rec").inner_text().strip() == "Recommended: Email link"
        assert c.locator(".up-ctx__wait").inner_text().strip() == "Grunt waits for your answer" and c.locator(".up-ctx__goal").count() == 0
        assert name_of(pg) == SIGN_IN_Q and raised(pg).get_attribute("data-key") == "goal:signin", "its card, with its answers, and the same card raised in the row"
        ys = [box(pg.locator(s).first)["y"] for s in (".up-gh", ".up-ctx", ".hand-up .hand-lifted", ".up-phases", ".up-route", ".up-why")]
        assert ys == sorted(ys) and len(set(ys)) == 6, "the header, the context, the card, the phases, the route, why"
        assert pg.locator(".up-why").inner_text().strip() == "About signin."
        shot(pg, "phone-look-goal")
        pg.locator(".hand-up .hand-lifted .q-card", has_text="Passkey").click()
        assert _calls(pg, host, "ideas.talk_answer") == [{"idea": "signin", "answers": [{"id": "q1", "pick": 1}]}], "one tap answers"
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'phones'", timeout=WAIT_MS)
        assert pg.locator(".hand-up .hand-lifted").count() == 1 and raised(pg).get_attribute("data-key") == "goal:phones", "the next card is on the screen"
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


def test_a_goal_picked_from_the_menu_with_no_card_shows_its_way_alone_route_why_and_the_tasks_of_the_step_at_work(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "goal", SEAT)
        assert look(pg).get_attribute("data-goal") == "seat" and look(pg).get_attribute("data-entry") is None
        assert pg.locator(".hand-up .hand-lifted").count() == 0 and raised(pg).count() == 0, "no card on it, no card raised"
        assert cards(pg).count() == 2, "the hand's cards stay in the row"
        assert sig(pg, "frame/state.js", "picked") == "seat"
        assert pg.locator(".up-gh__name").inner_text().strip() == SEAT and pg.locator(".up-gh__type").inner_text().strip() == "Feature · at work in Tech"
        steps = pg.locator(".up-route .up-step")
        assert [s.inner_text().strip() for s in steps.all()] == ["Design", "Tech", "Product"] and [s.get_attribute("class") for s in steps.all()] == ["up-step is-done", "up-step is-now", "up-step is-next"], "the parties in the route's order"
        assert all("/races/" in s.locator("img").get_attribute("src") for s in steps.all()) and steps.nth(0).locator(".ork-sign.check").count() == 1 and steps.nth(1).locator(".ork-sign.work").count() == 1
        assert steps.nth(1).evaluate("(e) => getComputedStyle(e).rotate") not in ("none", "0deg"), "the one at work turned"
        assert float(steps.nth(2).evaluate("(e) => getComputedStyle(e).opacity")) < 1, "the next faint"
        assert pg.locator(".up-route .ork-icon").count() == 2
        assert pg.locator(".up-why").inner_text().strip() == SEAT_WHY
        assert pg.locator(".up-why").evaluate("(e) => getComputedStyle(e).webkitLineClamp") == "4"
        tasks = pg.locator(".up-tasks .up-task")
        assert pg.locator(".up-sec .up-lab").text_content().strip() == "Tech's tasks"
        assert [t.locator(".up-task__name").inner_text().strip() for t in tasks.all()] == ["Check the seat", "Keep the seat"], "the front first (cascadeOf)"
        assert [t.locator(".up-task__stage").inner_text().strip() for t in tasks.all()] == ["Checking", "Doing"]
        assert all(t.locator("img").count() == 1 for t in tasks.all()), "each its doer's head"
        alert = css_colour(pg, "--ork-alert")
        assert [t.evaluate("(e) => getComputedStyle(e).borderTopColor") == alert for t in tasks.all()] == [False, False], "nothing asks, nothing failed"
        shot(pg, "phone-look-way")
        narrow = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert narrow <= 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_that_asks_or_failed_is_in_the_alerts_frame_and_the_goals_card_is_on_its_way(gui):
    pg, host, log = open_up(gui, host=LookHost(calm=False))
    try:
        assert look(pg).get_attribute("data-goal") == "seat" and raised(pg).get_attribute("data-key") == "goal:seat", "a failed task is a card: the goal of the hand's first card"
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


def test_a_goal_in_line_shows_its_phases_and_why_and_the_moon_with_its_hour_no_route_no_tasks(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "goal", "Chat in the lobby")
        assert look(pg).get_attribute("data-goal") == "chat" and pg.locator(".up-gh__type").inner_text().strip() == "Feature · In line"
        assert [p.get_attribute("class") for p in pg.locator(".up-phase").all()] == ["up-phase"] * 4, "none past, none its own"
        wait = pg.locator(".up-wait")
        assert wait.locator(".ork-sign.moon").count() == 1 and wait.inner_text().strip() == "Waits for the reset, from 21:40", "the moon and its hour"
        assert pg.locator(".up-route, .up-tasks").count() == 0 and pg.locator(".up-why").inner_text().strip() == "About chat."
        shot(pg, "phone-look-line")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_party_picked_shows_its_header_squad_tools_goals_at_work_and_concerns(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "party", "Tech")
        assert look(pg).get_attribute("data-look") == "party" and sig(pg, "frame/state.js", "tab") == "tech" and sig(pg, "frame/state.js", "picked") == ""
        assert raised(pg).count() == 0 and pg.locator(".hand-up .hand-lifted").count() == 0, "no card raised, no card in the middle"
        h = pg.locator(".up-ph")
        hd = box(h.locator("img").first)
        assert "/races/shaman-elder" in h.locator("img").first.get_attribute("src") and round(hd["width"]) == 48 and round(hd["height"]) == 44, "its leader's head, 48 x 44"
        assert h.locator(".up-ph__name").text_content().strip() == "Tech" and h.locator(".up-ph__brief").inner_text().strip() == "How it is built, and what it costs to change." and h.locator(".up-ph__size").inner_text().strip() == "Standard"
        faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.up-ph__name')).fontFamily, getComputedStyle(document.querySelector('.up-ph__brief')).fontFamily]")
        assert faces[0] != faces[1], "its name in the heading face"
        cols = pg.locator(".up-squad__col")
        assert [c.locator(".up-lab").inner_text().strip().lower() for c in cols.all()] == ["leads", "does", "checks"], "Leads, Does (the Grunt of its tasks), Checks"
        seats = pg.locator(".up-squad .table-seat")
        assert seats.count() >= 2 and all(box(s)["width"] >= 44 and box(s)["height"] >= 44 for s in seats.all()), "the heads only, each a 44 px target"
        assert pg.locator(".up-squad").inner_text().count("Tester") == 0, "heads only: no names"
        tools = pg.locator(".up-tools .up-tool")
        assert [t.inner_text().strip() for t in tools.all()] == ["Does on the default (now Claude Code)", "Checks on Codex, set for this party"]
        assert tools.nth(0).locator(".ork-sign.sword").count() == 1 and tools.nth(1).locator(".ork-sign.shield").count() == 1 and tools.nth(0).locator("img.ork-mark").count() == 1
        work = pg.locator(".up-party .up-grow")
        assert [w.inner_text().replace("\n", " ").strip() for w in work.all()] == [f"{SEAT} Checks"], "its goals at work as the menu's rows (the front task checks)"
        concerns = pg.locator(".up-concerns .up-concern")
        assert [c.locator(".up-concern__what").inner_text().strip() for c in concerns.all()] == [CONCERN["what"], NOTE["what"]], "the alerts first; one made into a goal is not a concern now"
        assert concerns.nth(0).locator(".ork-sign.alert").count() == 1 and concerns.nth(0).locator(".up-concern__on").inner_text().strip() == "server/lobby.ts" and concerns.nth(1).locator(".ork-sign.alert").count() == 0
        assert pg.eval_on_selector_all(".up-party .up-sec .up-lab", "(els) => els.map((e) => e.textContent.trim())") == ["At work", "Concerns"]
        assert _calls(pg, host, "ideas.concerns")[0] == {"party": "tech"}
        shot(pg, "phone-look-party")
        work.first.click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'seat'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "tab") == "orkmaster", "a press on its goal picks the goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_head_of_the_squad_opens_its_popover_as_a_sheet_at_the_foot(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "party", "Tech")
        pg.locator(".up-squad .table-seat").first.click()
        pop = pg.locator(".table-seatpop")
        pop.wait_for(timeout=WAIT_MS)
        r, h = box(pop), pg.viewport_size["height"]
        assert r["y"] + r["height"] == pytest.approx(h, abs=2) and r["x"] <= 1 and r["width"] >= pg.viewport_size["width"] - 2, "a sheet at the foot of the screen"
        pg.keyboard.press("Escape")
        pop.wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_party_with_no_concerns_and_no_goal_at_work_has_neither_section(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "party", "Release")
        assert look(pg).get_attribute("data-look") == "party" and pg.locator(".up-ph__name").text_content().strip() == "Release"
        pg.wait_for_timeout(300)
        assert pg.locator(".up-concerns, .up-party .up-sec").count() == 0, "none when it has none"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_press_on_a_card_of_the_row_lets_the_party_go_and_a_party_is_not_kept_across_a_start(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        pick_from_menu(pg, "party", "Tech")
        assert look(pg).get_attribute("data-look") == "party"
        cards(pg).nth(1).click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'phones'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "tab") == "orkmaster" and raised(pg).get_attribute("data-key") == "goal:phones"
        pick_from_menu(pg, "party", "Design")
        assert look(pg).get_attribute("data-look") == "party"
        pg.reload()
        pg.wait_for_selector(".hand-up .up-look", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.look === 'goal'", timeout=WAIT_MS)
        assert look(pg).get_attribute("data-goal") == "signin", "a phone starts on the hand's goal, whatever party the tabs kept on this device"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_answering_the_last_card_of_the_picked_goal_picks_the_next_entry(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        cards(pg).nth(1).click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'phones'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "phones"
        pg.locator(".hand-up .hand-lifted button", has_text="Server counts, phones show it").first.click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'signin'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "" and raised(pg).get_attribute("data-key") == "goal:signin" and cards(pg).count() == 1, "the next entry is looked at, its card raised"
        assert name_of(pg) == SIGN_IN_Q
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_picked_from_the_menu_that_has_a_card_shows_its_card_and_raises_it(gui):
    pg, host, log = open_up(gui, host=LookHost())
    try:
        cards(pg).nth(1).click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'phones'", timeout=WAIT_MS)
        pick_from_menu(pg, "goal", "Sign-in")
        assert look(pg).get_attribute("data-goal") == "signin" and look(pg).get_attribute("data-entry") == "goal:signin" and name_of(pg) == SIGN_IN_Q and raised(pg).get_attribute("data-key") == "goal:signin"
        pick_from_menu(pg, "goal", "Daily quests")
        assert look(pg).get_attribute("data-goal") == "daily" and pg.locator(".hand-up .hand-lifted").count() == 0 and raised(pg).count() == 0, "a goal in Talk with no card: its way alone"
        assert [p.get_attribute("class") for p in pg.locator(".up-phase").all()] == ["up-phase is-now", "up-phase", "up-phase", "up-phase"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_with_nothing_picked_and_nothing_in_the_hand_the_line_and_the_crown_and_the_plus_card_are_the_ways_on(gui):
    pg, host, log = open_up(gui, "empty")
    try:
        assert pg.locator(".up-look").count() == 0 and pg.get_by_text("Nothing waits for you.", exact=True).count() == 1
        assert crown(pg).count() == 1 and pg.locator(".up-plus .hand-plus").count() == 1 and pots(pg).count() == 4
        pick_from_menu(pg, "party", "Tech")
        assert look(pg).get_attribute("data-look") == "party", "a party can be looked at with an empty hand"
        assert pg.get_by_text("Nothing waits for you.", exact=True).count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_of_no_goal_is_its_context_and_its_card_and_the_ready_goal_has_its_way_under_the_portal(gui):
    pg, host, log = open_up(gui, "paid")
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
