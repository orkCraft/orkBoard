"""The phone's menu of the leaders (docs/specs/117-the-phone-a-menu-of-the-leaders.md §4, part C; decisions §195.1; the mockup docs/mockups/phone/sidebar.html A2), in a real browser against the table's stub host (four parties, goals at work, three goals in line,
Talk and Spec added), with touch at 390 × 844: the crown opens a sheet from the left (312 px) over the scrim, which the scrim, Esc and the phone's back close (one history entry while it is open), the focus going in and back; its head (the project with its
switcher, *Settings*, *Stop all*); the Orkmaster's goals (Talk, Spec, then in line with the moon); each party with its sword and shield and its goals at work (*Work* or *Checks*); no count and no alert anywhere; the picked row; a press on a goal or a party
picks it and closes the menu; the desktop has no crown. Screenshots to $UPRIGHT_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import sig  # noqa: E402
from tests.test_table_desktop_browser import TableHost, node, watch  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["UPRIGHT_SHOTS"]) if os.environ.get("UPRIGHT_SHOTS") else None
MENU = "The leaders and their goals"
TALK, SPEC = "Daily quests: who plays them?", "Leaderboard"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class MenuHost(TableHost):
    """The table's stub project (*shop*) with a goal in Talk and one in Spec of Game design's, nothing asked of the person."""

    def __init__(self):
        super().__init__(rich=True, line=3)
        self.nodes += [node("daily", "game", TALK, "talk", element="ice", sign="feature"), node("board", "game", SPEC, "decided", element="lava", sign="chart")]


def start(gui, kind="phone", errors=None):
    """The page at the phone's size (touch) or at `kind` "wide" / "fine" against a MenuHost: `(page, host, errors)`."""
    server, browser = gui
    errors = [] if errors is None else errors
    host = MenuHost()
    pg = narrow.context(browser, {"phone": "phone", "wide": "wide", "fine": "narrow"}[kind]).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".up-crown" if kind == "phone" else ".table-tab", timeout=WAIT_MS)
    pg.wait_for_timeout(500)
    return pg, host, errors


def crown(pg):
    return pg.get_by_role("button", name=MENU, exact=True)


def menu(pg):
    return pg.locator(".up-menu")


def opened(pg):
    crown(pg).click()
    menu(pg).wait_for(timeout=WAIT_MS)
    pg.locator(".up-prow").first.wait_for(timeout=WAIT_MS)
    return menu(pg)


def box(loc):
    return loc.bounding_box()


def rows(pg):
    return pg.locator(".up-menu .up-grow, .up-menu .up-prow")


def texts(loc):
    return [" ".join(t.split()) for t in loc.all_inner_texts()]


def css_colour(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.color = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }", token)


def bg_of(pg, token):
    return pg.evaluate("(t) => { const e = document.createElement('i'); e.style.background = 'var(' + t + ')'; document.body.append(e); const c = getComputedStyle(e).backgroundColor; e.remove(); return c; }", token)


def test_the_crown_opens_a_sheet_from_the_left_over_the_scrim_and_focus_goes_in(gui):
    pg, host, errors = start(gui)
    try:
        assert menu(pg).count() == 0 and crown(pg).get_attribute("aria-expanded") == "false" and pg.locator(".up-scrim").count() == 0
        m = opened(pg)
        r, w, h = box(m), pg.viewport_size["width"], pg.viewport_size["height"]
        assert r["x"] == 0 and r["y"] == 0 and r["height"] == pytest.approx(h, abs=1) and r["width"] <= 312.5 and r["width"] <= 0.8 * w + 0.5 and r["width"] >= 300, "312 px at most 80% of the width, from the left, the whole height"
        s = box(pg.locator(".up-scrim"))
        assert s["x"] == 0 and s["width"] == pytest.approx(w, abs=1) and s["height"] == pytest.approx(h, abs=1), "the scrim over the screen"
        assert pg.locator(".up-scrim").evaluate("(e) => getComputedStyle(e).backgroundColor") == css_colour(pg, "--ork-scrim")
        assert m.get_attribute("role") == "dialog" and m.get_attribute("aria-modal") == "true" and m.get_attribute("aria-label") == MENU
        assert crown(pg).get_attribute("aria-expanded") == "true"
        assert pg.evaluate("() => !!document.activeElement.closest('.up-menu')"), "the focus goes into the sheet"
        assert pg.evaluate("() => history.state && history.state.orkboardMenu") == 1, "one history entry while it is open"
        narrow.no_sideways(pg)
        shot(pg, "phone-menu")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_the_scrim_esc_and_the_phones_back_close_it_and_the_focus_returns_to_the_crown(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        pg.mouse.click(370, 400)                                      # the scrim, right of the sheet
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert pg.evaluate("() => document.activeElement.classList.contains('up-crown')"), "the focus is back on the crown"
        assert pg.evaluate("() => history.state && history.state.orkboardMenu") is None and pg.locator(".up-scrim").count() == 0, "its history entry is gone with it"
        opened(pg)
        pg.keyboard.press("Escape")
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert crown(pg).get_attribute("aria-expanded") == "false"
        opened(pg)
        pg.go_back()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert pg.locator(".hand-up").is_visible() and pg.url.startswith("http"), "the phone's back closed the sheet and left the page where it was"
        opened(pg)
        crown_after = pg.evaluate("() => history.length")
        pg.keyboard.press("Escape")
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert pg.evaluate("() => history.length") <= crown_after, "no entry piles up"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_the_menu_is_never_opened_by_a_swipe_from_the_left_edge(gui):
    pg, host, errors = start(gui)
    try:
        pg.mouse.move(2, 400)
        pg.mouse.down()
        pg.mouse.move(120, 405, steps=6)
        pg.mouse.move(260, 410, steps=6)
        pg.mouse.up()
        pg.wait_for_timeout(300)
        assert menu(pg).count() == 0, "the left edge is the system's back"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_its_head_is_the_crowned_head_the_project_with_its_switcher_settings_and_stop_all_each_44_px(gui):
    pg, host, errors = start(gui)
    try:
        m = opened(pg)
        head = m.locator(".up-menu__head")
        assert box(head)["height"] == pytest.approx(60, abs=1.5) and "/races/peon-crown" in head.locator("img").first.get_attribute("src")
        project, settings, stop = head.get_by_role("button", name="Switch project: shop"), head.get_by_role("button", name="Settings", exact=True), head.get_by_role("button", name="Stop all", exact=True)
        assert project.inner_text().strip() == "shop" and project.locator(".ork-icon").count() == 1, "the project's name with a chevron"
        for b in (project, settings, stop):
            r = box(b)
            assert r["width"] >= 44 and r["height"] >= 44
        assert stop.evaluate("(e) => getComputedStyle(e).color") == css_colour(pg, "--ork-danger"), "Stop all in the danger colour"
        assert box(project)["x"] < box(settings)["x"] < box(stop)["x"]
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_the_groups_the_orkmasters_goals_then_each_party_with_its_goals_at_work(gui):
    pg, host, errors = start(gui)
    try:
        m = opened(pg)
        groups = m.locator(".up-group")
        assert groups.count() == 5, "the Orkmaster's goals and the four parties, Release too"
        assert groups.first.locator(".up-group__label").inner_text().strip().lower() == "orkmaster · being talked about"
        talked = texts(groups.first.locator(".up-grow"))
        assert talked == [f"{TALK} Talk", f"{SPEC} Spec", "Chat in the lobby In line", "Round music that fades in In line", "A banner for the lobby In line"], "Talk and Spec in the Board's order, then those in line"
        assert [g.locator(".up-prow__name").inner_text().strip() for g in groups.all()[1:]] == ["Game design", "Tech", "Art", "Release"], "the tabs' order"
        by = {g.locator(".up-prow__name").inner_text().strip(): texts(g.locator(".up-grow")) for g in groups.all()[1:]}
        assert by["Game design"] == ["Write the timer's rules: seconds in each phase Work"]
        assert sorted(by["Tech"]) == sorted(["Tidy the lobby code Work", "Keep the seat when a socket reconnects Work", "Check that a rejoin keeps the round Checks"])
        assert by["Art"] == ["A timer bar that drains Checks"], "a goal whose front task is a check says Checks"
        assert by["Release"] == [] and groups.nth(4).locator("button").count() == 1, "a party with no goal at work is its row alone"
        for g in groups.all()[1:]:
            head = g.locator(".up-prow img.ork-race__head").first
            assert head.get_attribute("src").startswith("/ds/orkui/races/") and round(box(head)["width"]) == 24
        shot(pg, "phone-menu-groups")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_goals_row_is_its_element_the_types_sign_its_name_and_its_phase_the_moon_beside_one_that_waits_for_the_reset(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        talk = pg.locator(".up-grow", has_text=TALK)
        assert talk.locator(".ork-elem.ice").count() == 1 and talk.locator(".ork-sign.feature").count() == 1 and talk.locator(".up-grow__phase").inner_text().strip() == "Talk"
        assert pg.locator(".up-grow", has_text="Leaderboard").locator(".ork-sign.chart").count() == 1
        music = pg.locator(".up-grow", has_text="Round music that fades in")
        assert music.locator(".ork-sign.moon").count() == 1 and music.locator(".up-grow__phase").inner_text().strip() == "In line", "the moon beside the name of the one that waits for the reset"
        assert pg.locator(".up-grow", has_text="Chat in the lobby").locator(".ork-sign.moon").count() == 0
        assert pg.locator(".up-grow", has_text="Keep the seat").locator(".ork-elem.ice").count() == 1
        for r in pg.locator(".up-grow").all():
            assert box(r)["height"] >= 40
        x = [box(r.locator(".ork-elem"))["x"] for r in pg.locator(".up-grow").all()]
        assert max(x) - min(x) < 1 and min(x) >= 44, "indented to the heads' column"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_each_party_has_its_sword_and_shield_as_the_tabs_draw_them(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        row = lambda name: pg.locator(".up-prow", has_text=name)  # noqa: E731
        tech = row("Tech")
        assert tech.locator(".table-tab__marks .ork-sign.sword").count() == 1 and tech.locator(".table-tab__marks .ork-sign.shield").count() == 1
        assert [m.get_attribute("data-tool") for m in tech.locator(".table-tab__marks img.ork-mark").all()] == ["claude", "codex"], "Does on Claude, Checks on Codex"
        assert "-ink" in tech.locator("img.ork-mark").first.get_attribute("src"), "in ink: the open tab's alone is in colour"
        assert tech.get_attribute("aria-label") == "Tech · Does on Claude · Checks on Codex" and tech.get_attribute("title") == tech.get_attribute("aria-label")
        art = row("Art")
        assert art.locator(".table-tab__off .ork-sign.shield").count() == 1 and art.locator(".table-tab__marks img.ork-mark").count() == 1, "a Lean party: the shield faint, no mark"
        assert art.get_attribute("aria-label").endswith("no separate check")
        assert row("Release").locator(".table-tab__more").count() == 1, "a column on more than one tool: the dot"
        assert row("Game design").locator(".table-tab__marks img.ork-mark").count() == 2
        for r in pg.locator(".up-prow").all():
            assert box(r)["height"] >= 48
        shot(pg, "phone-menu-marks")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_no_count_no_alert_no_waits_for_you_anywhere_in_the_menu(gui):
    pg, host, errors = start(gui)
    try:
        m = opened(pg)
        assert m.locator(".ork-sign.alert, .ork-badge, .table-tab__dot, .table-tab__alert").count() == 0
        text = " ".join(m.inner_text().split())
        assert "waits for you" not in text.lower() and "alert" not in text.lower() and "!" not in text
        for r in rows(pg).all():
            name = r.locator(".up-grow__name, .up-prow__name").inner_text()
            rest = " ".join(r.inner_text().replace(name, "").split())
            assert not any(ch.isdigit() for ch in rest), f"a digit in {rest!r}"
        assert not any(ch.isdigit() for ch in m.locator(".up-menu__head").inner_text()) and "menu" not in text.lower(), "never called menu where a person reads it"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_goal_pressed_is_picked_and_the_menu_closes_the_picked_row_has_the_inks_bar(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        on = pg.locator(".up-menu .is-on")
        assert on.count() == 1 and on.get_attribute("data-goal") == "seat", "nothing chosen: the goal of the hand's first card is the picked one"
        pg.locator(".up-grow", has_text="Tidy the lobby code").click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "calm" and sig(pg, "frame/state.js", "tab") == "orkmaster", "the goal is picked, no party"
        assert pg.evaluate("() => document.activeElement.classList.contains('up-crown')")
        opened(pg)
        on = pg.locator(".up-menu .is-on")
        assert on.count() == 1 and on.get_attribute("data-goal") == "calm" and on.get_attribute("aria-current") == "true"
        assert on.evaluate("(e) => getComputedStyle(e).backgroundColor") == bg_of(pg, "--ork-panel")
        assert css_colour(pg, "--ork-ink").replace("rgb(", "").replace(")", "") in on.evaluate("(e) => getComputedStyle(e).boxShadow"), "the ink's bar at its left"
        shot(pg, "phone-menu-picked")
        pg.locator(".up-grow", has_text=TALK).click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "daily"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_goal_with_a_card_in_the_hand_is_picked_as_that_card(gui):
    pg, host, errors = start(gui)
    try:
        assert pg.locator('.up-card[aria-pressed="true"]').get_attribute("data-key") == "goal:seat"
        opened(pg)
        pg.locator(".up-grow", has_text="Check that a rejoin keeps the round").click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.up-card[aria-pressed=true]')?.dataset.key === 'goal:recheck'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "recheck" and sig(pg, "hand/entries.js", "at") == "goal:recheck", "its entry is the one on the screen"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_party_pressed_is_picked_with_no_goal_and_the_menu_closes(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        pg.locator(".up-prow", has_text="Art").click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "tab") == "art" and sig(pg, "frame/state.js", "picked") == "", "the party is picked, no goal"
        opened(pg)
        on = pg.locator(".up-menu .is-on")
        assert on.count() == 1 and on.get_attribute("data-party") == "art", "the picked party's row has the bar"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_the_head_opens_the_switcher_and_settings_over_the_pane_and_back_returns_to_the_hand(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        pg.get_by_role("button", name="Switch project: shop").click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "projects" and pg.locator(".hand-up").is_hidden() and menu(pg).count() == 0
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
        assert menu(pg).count() == 0, "← comes back to the hand, the menu closed"
        opened(pg)
        pg.get_by_role("button", name="Settings", exact=True).click()
        pg.wait_for_selector(".table-over", timeout=WAIT_MS)
        assert pg.locator(".table-over").get_attribute("data-kind") == "settings"
        pg.wait_for_timeout(300)
        assert pg.locator(".table-over").count() == 1, "the thing it opened stays open (the back that closed the menu did not close it)"
        pg.go_back()
        pg.wait_for_selector(".hand-up", state="visible", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_stop_all_sends_halt_and_closes_the_menu(gui):
    pg, host, errors = start(gui)
    try:
        opened(pg)
        pg.get_by_role("button", name="Stop all", exact=True).click()
        menu(pg).wait_for(state="detached", timeout=WAIT_MS)
        for _ in range(40):
            if any(n == "halt" for n, _a in host.log):
                break
            pg.wait_for_timeout(50)
        assert any(n == "halt" for n, _a in host.log)
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("kind", ["wide", "fine"])
def test_the_desktop_and_a_narrow_window_with_a_mouse_have_no_crown_and_no_menu(gui, kind):
    pg, host, errors = start(gui, kind)
    try:
        assert pg.locator(".up-crown, .up-menu, .up-scrim, .up-top").count() == 0 and pg.get_by_role("button", name=MENU).count() == 0
        assert pg.locator(".table-tab").count() >= 5 and pg.locator(".table-tabs").is_visible(), "the tabs, as before"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


PHONE = """globalThis.__calls = []; let on = false;
globalThis.orkboardPhone = Object.freeze({ paired: () => true, unpair() { __calls.push("unpair"); },
  push: Object.freeze({ async state() { return { supported: true, why: "", permission: on ? "granted" : "default", on, quiet: "" }; },
    async on() { __calls.push("on"); on = true; return { ok: true }; }, async off() { __calls.push("off"); on = false; return { ok: true }; }, async setQuiet() { return { ok: true }; } }) });"""


def test_this_phone_rows_only_in_the_paired_app(gui):
    """At the menu's foot, only in the app the frame pairs: *Notifications* turns them on and off; *Unpair this phone* asks a second press (spec 117 As built E)."""
    pg, _host, errors = start(gui)
    crown(pg).click()
    assert menu(pg).get_by_role("switch", name="Notifications").count() == 0          # the page from the link: no frame, no rows
    pg.context.close()
    server, browser = gui
    ctx = narrow.context(browser, "phone")
    ctx.add_init_script(PHONE)
    pg = ctx.new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", MenuHost().on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".up-crown", timeout=WAIT_MS)
    crown(pg).click()
    sw = menu(pg).get_by_role("switch", name="Notifications")
    assert sw.get_attribute("aria-checked") == "false"
    sw.click()
    pg.wait_for_function("document.querySelector('.up-phone__row[role=switch]').getAttribute('aria-checked') === 'true'", timeout=WAIT_MS)
    menu(pg).get_by_role("button", name="Unpair this phone").click()
    assert pg.evaluate("__calls") == ["on"]
    menu(pg).get_by_role("button", name="Press again to unpair").click()
    assert pg.evaluate("__calls") == ["on", "unpair"]
    shot(pg, "phone-menu-this-phone")
    assert not errors
