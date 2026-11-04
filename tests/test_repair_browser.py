"""Spec 119 part D (docs/specs/119-the-hammer-and-the-bug.md §1, §4, §6; decisions §197), Chromium against the table's stub host (tests/test_table_desktop_browser.py `TableHost`) whose snapshot carries the `repair` of §3.2.

The bug's panel (spec 139 A.5, decisions §246.6: the bug left the tabs' row; it opens from *Report a problem…* in the Orkmaster's … and in the phone's crown menu, and from the *Report* of a crash the page shows; while a fix runs the Orkmaster's line says *Fixing Orkboard: ...*), by `repair.state`: idle (the line, *Fix it* when `repair.can` with its one line under it, *Save logs*; Save logs alone, as before, on a host that cannot or knows nothing of it), working (where to follow it, since when, *Stop the fix*),
ready (the newest subject, *and n more*, *Update and restart* in the signal), updating (nothing to press), failed (the error, *Try again* with the line last sent, *Save logs*); its title and `aria-label` by state; the commands each press sends
(`repair.start {said, page}`, `repair.stop`, `repair.update`); the pictures (the one map `PICTURES`: the bug and orkUI's hammer, striking while Claude works, standing raised under reduced motion; the squashed bug when the fix is in); why Fix it is not offered. The paired phone's row *Fix Orkboard* above Notifications, only when `repair.can`, its panel in the menu without Save logs.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_phone_menu_browser import PHONE, crown, menu  # noqa: E402
from tests.test_table_desktop_browser import TableHost, watch  # noqa: E402

pytestmark = pytest.mark.browser

WIDE = {"width": 1280, "height": 800}
CAN = {"can": True, "why": "", "state": "idle", "started_at": None, "landed": [], "error": ""}
CANNOT = {"can": False, "why": "Orkboard was not installed from git", "state": "idle", "started_at": None, "landed": [], "error": ""}
WORKING = {**CAN, "state": "working", "started_at": 1_761_900_000.0}
READY = {**CAN, "state": "ready", "started_at": 1_761_900_000.0, "landed": [{"sha": "b" * 40, "subject": "Keep the seat when the socket drops"}, {"sha": "a" * 40, "subject": "Older"}, {"sha": "9" * 40, "subject": "Oldest"}]}
UPDATING = {**READY, "state": "updating"}
FAILED = {**CAN, "state": "failed", "error": "claude exited at once\nRun `claude remote-control` once in ~/.orkcraft/repair/worktree to answer its questions, then Try again"}
TITLES = {"idle": "Save the logs or fix Orkboard", "working": "Claude is fixing Orkboard", "ready": "The fix is in: update and restart", "failed": "The fix did not come in"}


class RepairHost(TableHost):
    """The table's stub project whose snapshot says `repair` (None: a host that knows nothing of it) and which records `repair.*` and `logs.save`; the three commands answer the next state as the host would."""

    def __init__(self, repair=CAN, **kw):
        super().__init__(**kw)
        self.repair = repair

    def snapshot(self):
        snap = super().snapshot()
        if self.repair is not None:
            snap["state"]["repair"] = dict(self.repair)
        return snap

    def say(self, **repair):
        """The host's state changes (the snapshot is sent again; the Board stays as it was)."""
        self.repair = {**(self.repair or CAN), **repair}
        self.ws.send(json.dumps(self.snapshot()))

    def handle(self, name, a):
        if name == "repair.start":
            self.log.append((name, a))
            self.repair = {**self.repair, "state": "working", "started_at": 1_761_900_000.0, "error": ""}
            return dict(self.repair)
        if name == "repair.stop":
            self.log.append((name, a))
            self.repair = {**self.repair, "state": "idle", "started_at": None}
            return dict(self.repair)
        if name == "repair.update":
            self.log.append((name, a))
            self.repair = {**self.repair, "state": "updating"}
            return dict(self.repair)
        if name == "logs.save":
            self.log.append((name, a))
            return {"path": "/tmp/logs.zip"}
        return super().handle(name, a)


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(Path(d) / name))


def window(gui, host, width=WIDE, **ctx):
    """The desktop (a viewport dict) or a table width of tests/narrow.py against `host`: `(page, errors)`."""
    server, browser = gui
    errors: list[str] = []
    context = browser.new_context(viewport=width, **ctx) if isinstance(width, dict) else narrow.context(browser, width)
    pg = context.new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="The Orkmaster's menu").wait_for(timeout=WAIT_MS)
    return pg, errors


def panel(pg):
    return pg.locator(".table-logs__panel")


def menu_button(pg):
    return pg.get_by_role("button", name="The Orkmaster's menu")


def opened(pg):
    """The bug's panel, opened as a person does: the Orkmaster's …, then *Report a problem…* (spec 139 A.5)."""
    menu_button(pg).click()
    pg.get_by_role("menuitem", name="Report a problem…").click()
    panel(pg).wait_for(timeout=WAIT_MS)
    return panel(pg)


def head(pg):
    """The panel's head: its title by state, next to its picture."""
    return words(panel(pg).locator(".table-logs__head"))


def state_is(pg, state):
    pg.wait_for_function("(s) => document.querySelector('.table-logs__panel')?.dataset.repairState === s", arg=state, timeout=WAIT_MS)


def words(loc):
    return " ".join(loc.inner_text().split())


def buttons(loc):
    return [words(b) for b in loc.locator("button").all()]


def calls(pg, host, name, at_least=1):
    for _ in range(WAIT_MS // 50):
        got = [a for n, a in host.log if n == name]
        if len(got) >= at_least:
            return got
        pg.wait_for_timeout(50)
    return [a for n, a in host.log if n == name]


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def pic(pg):
    """What the panel's head draws: the sign under, and what lies over it (an icon's name, a sign's name, or '')."""
    return pg.evaluate("""() => { const b = document.querySelector('.table-logs__panel .table-logs__pic'), signs = [...b.querySelectorAll('.ork-sign')].map((e) => e.className.replace('ork-sign', '').replace('big', '').trim()),
      icon = b.querySelector('svg.ork-icon use'); return { signs, icon: icon ? icon.getAttribute('href').split('#')[1] : '' }; }""")


def color(loc):
    return loc.evaluate("e => getComputedStyle(e).color")


def alert_colour(pg):
    return pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-alert)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")


def fixing_line(pg):
    return pg.locator(".table-notice[data-fixing] .table-notice__line")


# -- the way in: the Orkmaster's … and a crash (spec 139 A.5) ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_top_row_has_no_bug_and_the_orkmasters_menu_has_report_a_problem_after_files(gui, width):
    pg, errors = window(gui, RepairHost(CAN), width)
    assert pg.locator(".table-tabs .table-logs, .table-tabs [data-repair-state]").count() == 0, "the bug left the top row"
    menu_button(pg).click()
    items = [words(i) for i in pg.get_by_role("menuitem").all()]
    assert items[-3:] == ["Settings", "Files", "Report a problem…"] or items[-2:] == ["Files", "Report a problem…"], items
    assert items.index("Report a problem…") == items.index("Files") + 1
    assert pg.get_by_role("menuitem", name="Report a problem…").locator(".ork-sign.bug").count() == 1, "orkUI's bug"
    pg.get_by_role("menuitem", name="Report a problem…").click()
    assert panel(pg).get_attribute("aria-label") == "Report a problem" and "What went wrong? (optional)" in panel(pg).inner_text()
    shot(pg, f"s139-report-{width}.png")
    finish(pg, errors)


def test_a_crash_the_page_shows_has_report_that_opens_the_panel_with_the_crashs_text_in_its_line(gui):
    host = RepairHost(CAN)
    pg, errors = window(gui, host)
    pg.evaluate("() => setTimeout(() => { throw new Error('The map of System did not draw'); }, 0)")
    card = pg.locator(".table-crash")
    card.wait_for(timeout=WAIT_MS)
    assert "Something broke: Error: The map of System did not draw" in words(card) and buttons(card) == ["Report", "Close"]
    assert calls(pg, host, "crash.window")[0]["message"] == "Error: The map of System did not draw", "the crash is still reported as before"
    shot(pg, "s139-crash.png")
    card.get_by_role("button", name="Report").click()
    p = panel(pg)
    p.wait_for(timeout=WAIT_MS)
    assert p.locator("input").input_value() == "Error: The map of System did not draw" and card.count() == 0
    assert buttons(p) == ["Fix it", "Save logs"]
    p.get_by_role("button", name="Fix it").click()
    assert calls(pg, host, "repair.start")[0]["said"] == "Error: The map of System did not draw"
    errors.clear()                                                                                                      # the thrown error is this test's own
    finish(pg, errors)


def test_a_crashs_close_puts_it_away(gui):
    pg, errors = window(gui, RepairHost(CAN))
    pg.evaluate("() => setTimeout(() => { throw new Error('Boom'); }, 0)")
    pg.locator(".table-crash").wait_for(timeout=WAIT_MS)
    pg.locator(".table-crash").get_by_role("button", name="Close").click()
    assert pg.locator(".table-crash").count() == 0 and panel(pg).count() == 0
    errors.clear()
    finish(pg, errors)


# -- idle ---------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_idle_and_can_the_panel_has_the_line_fix_it_with_its_one_line_under_it_and_save_logs(gui, width):
    pg, errors = window(gui, RepairHost(CAN), width)
    p = opened(pg)
    assert head(pg) == TITLES["idle"] == "Save the logs or fix Orkboard"
    assert pic(pg) == {"signs": ["bug"], "icon": "hammer"} and not p.evaluate("e => /is-(working|ready|failed)/.test(e.className)")
    assert p.get_attribute("aria-label") == "Report a problem"
    assert "What went wrong? (optional)" in p.inner_text() and p.locator("input").evaluate("e => e === document.activeElement") and p.locator("input").input_value() == ""
    assert buttons(p) == ["Fix it", "Save logs"]
    assert p.get_by_role("button", name="Fix it").get_attribute("class").split()[-1] == "primary" and "quiet" in p.get_by_role("button", name="Save logs").get_attribute("class")
    assert "Starts Claude Code on Orkboard's own code with this and the logs; you say go in the Claude app." in words(p)
    fix, hint, save = (p.locator(s).bounding_box() for s in ("[data-repair=fix]", "p.table-logs__label", "[data-repair=save]"))
    assert fix["y"] < hint["y"] < save["y"], "the one line is under Fix it, Save logs under it"
    box, size = p.bounding_box(), pg.viewport_size
    assert box["x"] >= 0 and box["x"] + box["width"] <= size["width"] + 1 and box["y"] + box["height"] <= size["height"], "inside the window"
    shot(pg, f"d119-idle-{width}.png")
    finish(pg, errors)


def test_fix_it_sends_the_line_and_the_pages_state_closes_the_panel_and_the_orkmaster_says_it_is_fixing(gui):
    host = RepairHost(CAN)
    pg, errors = window(gui, host)
    assert fixing_line(pg).count() == 0, "nothing is fixed: the Orkmaster says nothing"
    p = opened(pg)
    p.locator("input").fill("The timer froze")
    p.get_by_role("button", name="Fix it").click()
    got = calls(pg, host, "repair.start")
    assert len(got) == 1 and got[0]["said"] == "The timer froze" and set(got[0]["page"]) >= {"w", "h", "tab", "errors"}, got
    assert panel(pg).count() == 0
    fixing_line(pg).wait_for(timeout=WAIT_MS)                                                                           # the reply (and the next snapshot) says it
    assert words(fixing_line(pg)) == "Fixing Orkboard: The timer froze"
    assert pg.locator(".table-notice[data-fixing]").locator(".ork-race__head").count() == 1, "the Orkmaster's crowned head says it"
    assert not [n for n, _a in host.log if n == "logs.save"], "Fix it saves nothing by itself"
    shot(pg, "s139-fixing-line.png")
    host.say(state="idle", started_at=None)                                                                             # the fix is stopped: the line goes
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-fixing]')", timeout=WAIT_MS)
    finish(pg, errors)


def test_the_orkmasters_line_while_a_fix_runs_with_no_line_of_the_persons_says_where(gui):
    host = RepairHost(WORKING)
    pg, errors = window(gui, host)
    fixing_line(pg).wait_for(timeout=WAIT_MS)
    assert words(fixing_line(pg)) == "Fixing Orkboard: Claude is on it in the Claude app"
    host.say(**UPDATING)
    pg.wait_for_function("() => document.querySelector('.table-notice[data-fixing] .table-notice__line')?.textContent === 'Fixing Orkboard: updating with the fix'", timeout=WAIT_MS)
    host.say(**READY)
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-fixing]')", timeout=WAIT_MS)
    finish(pg, errors)


def test_a_fix_that_is_in_has_the_orkmasters_line_restart_to_take_it_until_it_is_put_away(gui):
    """Spec 139 A.5: the host sends no card for a fix that is in, so the Orkmaster's line says *Orkboard was fixed: restart to take it*, until the viewer puts it away (a newer fix shows again)."""
    host = RepairHost(WORKING)
    pg, errors = window(gui, host)
    solved = pg.locator(".table-notice[data-solved]")
    assert solved.count() == 0, "a fix that runs says it is being fixed, not that it was"
    host.say(**READY)
    solved.wait_for(timeout=WAIT_MS)
    assert words(solved.locator(".table-notice__line")) == "Orkboard was fixed: restart to take it" and solved.get_attribute("role") == "status"
    assert solved.locator(".ork-race__head").count() == 1 and pg.locator(".table-notice[data-fixing]").count() == 0
    shot(pg, "s139-fixed-line.png")
    host.say(**UPDATING)                                                                                                    # the restart is on its way: the line of the fix running says so, this one is not asked
    pg.wait_for_function("() => document.querySelector('.table-notice[data-fixing]')", timeout=WAIT_MS)
    host.say(**READY)
    solved.wait_for(timeout=WAIT_MS)
    solved.get_by_role("button", name="Dismiss").click()
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-solved]')", timeout=WAIT_MS)
    host.say(**READY)                                                                                                      # the same fix again: still put away
    pg.wait_for_timeout(200)
    assert solved.count() == 0
    host.say(started_at=1_761_999_999.0)                                                                                   # a newer fix shows again
    solved.wait_for(timeout=WAIT_MS)
    host.say(state="idle", started_at=None)
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-solved]')", timeout=WAIT_MS)
    finish(pg, errors)


def test_enter_in_the_line_presses_fix_it_and_with_no_fix_it_save_logs(gui):
    host = RepairHost(CAN)
    pg, errors = window(gui, host)
    opened(pg).locator("input").fill("It hung")
    pg.keyboard.press("Enter")
    assert calls(pg, host, "repair.start")[0]["said"] == "It hung" and panel(pg).count() == 0
    finish(pg, errors)
    host = RepairHost(CANNOT)
    pg, errors = window(gui, host)
    opened(pg).locator("input").fill("It hung too")
    pg.keyboard.press("Enter")
    assert calls(pg, host, "logs.save")[0]["said"] == "It hung too" and not [n for n, _a in host.log if n == "repair.start"]
    finish(pg, errors)


@pytest.mark.parametrize("repair", [CANNOT, None], ids=["not-git", "old-host"])
def test_a_host_that_cannot_or_knows_nothing_of_it_shows_save_logs_alone_as_before(gui, repair):
    host = RepairHost(repair)
    pg, errors = window(gui, host)
    p = opened(pg)
    assert head(pg) == "Save the logs"
    assert pic(pg) == {"signs": ["bug"], "icon": "hammer"}
    assert buttons(p) == ["Save logs"] and "Claude" not in p.inner_text()
    why = p.locator("[data-repair=why]")                                # the host says why Fix it is not offered; an old host says nothing
    assert (why.inner_text() == "Fix it is not here: Orkboard was not installed from git.") if repair else why.count() == 0
    assert "primary" in p.get_by_role("button", name="Save logs").get_attribute("class").split()
    p.locator("input").fill("Not git")
    p.get_by_role("button", name="Save logs").click()
    assert calls(pg, host, "logs.save")[0]["said"] == "Not git" and panel(pg).count() == 0
    finish(pg, errors)


# -- working ------------------------------------------------------------------------------------------------------------------------------------

def test_working_says_where_to_follow_it_and_since_when_and_stop_the_fix_stops_it(gui):
    host = RepairHost(WORKING)
    pg, errors = window(gui, host)
    p = opened(pg)
    assert head(pg) == TITLES["working"]
    assert "is-working" in p.get_attribute("class").split() and pic(pg) == {"signs": ["bug"], "icon": "hammer"}
    assert "Claude is fixing it in the Claude app, session Fix Orkboard." in words(p) and p.locator("strong").inner_text() == "Fix Orkboard"
    started = pg.evaluate("() => new Date(1761900000 * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })")
    assert f"Started {started}." in words(p)
    assert buttons(p) == ["Stop the fix"] and p.locator("input").count() == 0
    shot(pg, "d119-working.png")
    p.get_by_role("button", name="Stop the fix").click()
    assert calls(pg, host, "repair.stop") == [{}]
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-fixing]')", timeout=WAIT_MS)
    finish(pg, errors)


def test_the_hammer_strikes_while_claude_works_and_stands_raised_under_reduced_motion(gui):
    pg, errors = window(gui, RepairHost(WORKING))
    opened(pg)
    hammer = pg.locator(".table-logs__panel svg.ork-icon.is-striking")
    assert hammer.evaluate("e => getComputedStyle(e).animationName") == "ork-strike"
    finish(pg, errors)
    pg, errors = window(gui, RepairHost(WORKING), reduced_motion="reduce")
    opened(pg)
    hammer = pg.locator(".table-logs__panel svg.ork-icon.is-striking")
    assert hammer.evaluate("e => getComputedStyle(e).animationName") == "none" and hammer.evaluate("e => getComputedStyle(e).transform") != "none"
    finish(pg, errors)
    pg, errors = window(gui, RepairHost(CAN))
    opened(pg)
    assert pg.locator(".table-logs__panel svg.ork-icon").evaluate("e => getComputedStyle(e).animationName") == "none", "an idle bug does not move"
    finish(pg, errors)


# -- ready --------------------------------------------------------------------------------------------------------------------------------------

def test_ready_is_the_one_state_in_the_signal_names_the_newest_commit_and_update_and_restart_sends_repair_update(gui):
    host = RepairHost(WORKING)
    pg, errors = window(gui, host)
    p = opened(pg)
    ink = color(p.locator(".table-logs__head"))
    host.say(**READY)                                                   # main moved while the panel was open: it turns by itself
    state_is(pg, "ready")
    assert head(pg) == TITLES["ready"]
    assert "is-ready" in p.get_attribute("class").split() and pic(pg) == {"signs": ["bug-squashed"], "icon": "hammer"}
    alert = alert_colour(pg)
    assert color(p.locator(".table-logs__head")) == alert != ink and color(p.locator(".ork-sign").first) == alert == color(p.locator("svg.ork-icon")), "the signal the update's own notice wears"
    assert "The fix is in: Keep the seat when the socket drops" in words(p) and "and 2 more" in words(p)
    assert "What runs now stops, and the tasks cut off start again by themselves. The phone comes back by itself." in words(p)
    assert buttons(p)[0] == "Update and restart" and "primary" in p.get_by_role("button", name="Update and restart").get_attribute("class").split()
    shot(pg, "d119-ready.png")
    p.get_by_role("button", name="Update and restart").click()
    assert calls(pg, host, "repair.update") == [{}]
    finish(pg, errors)


def test_ready_with_one_commit_says_no_more(gui):
    pg, errors = window(gui, RepairHost({**READY, "landed": READY["landed"][:1]}))
    p = opened(pg)
    assert "The fix is in: Keep the seat when the socket drops" in words(p) and "more" not in words(p)
    finish(pg, errors)


def test_updating_says_so_and_has_nothing_to_press(gui):
    pg, errors = window(gui, RepairHost(UPDATING))
    p = opened(pg)
    assert words(p.locator("[role=status]")) == "Updating…" and p.locator("button, input").count() == 0
    assert "is-working" in p.get_attribute("class").split()
    finish(pg, errors)


# -- failed -------------------------------------------------------------------------------------------------------------------------------------

def test_failed_says_the_error_as_it_is_try_again_sends_the_line_last_sent_and_save_logs_saves(gui):
    host = RepairHost(CAN)
    pg, errors = window(gui, host)
    opened(pg).locator("input").fill("The seat is lost")
    panel(pg).get_by_role("button", name="Fix it").click()
    calls(pg, host, "repair.start")
    host.say(**FAILED)
    pg.wait_for_function("() => !document.querySelector('.table-notice[data-fixing]')", timeout=WAIT_MS)
    p = opened(pg)
    state_is(pg, "failed")
    assert head(pg) == TITLES["failed"]
    assert "is-failed" in p.get_attribute("class").split() and pic(pg) == {"signs": ["bug", "cross"], "icon": ""}
    assert p.locator("pre").inner_text() == FAILED["error"], "the error as it is"
    assert buttons(p) == ["Try again", "Save logs"]
    shot(pg, "d119-failed.png")
    p.get_by_role("button", name="Try again").click()
    again = calls(pg, host, "repair.start", 2)
    assert len(again) == 2 and again[1]["said"] == "The seat is lost" and "page" in again[1]
    host.say(**FAILED)
    opened(pg).get_by_role("button", name="Save logs").click()
    assert len(calls(pg, host, "logs.save")) == 1
    finish(pg, errors)


def test_the_panel_follows_the_state_while_it_is_open_and_esc_and_a_press_away_close_it(gui):
    host = RepairHost(WORKING)
    pg, errors = window(gui, host)
    p = opened(pg)
    assert buttons(p) == ["Stop the fix"]
    host.say(**READY)
    pg.get_by_role("button", name="Update and restart", exact=True).wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".table-logs__panel", state="detached", timeout=WAIT_MS)
    opened(pg)
    pg.mouse.click(300, 600)
    pg.wait_for_selector(".table-logs__panel", state="detached", timeout=WAIT_MS)
    finish(pg, errors)


# -- the phone ----------------------------------------------------------------------------------------------------------------------------------

def phone_page(gui, host, paired=True):
    server, browser = gui
    errors: list[str] = []
    ctx = narrow.context(browser, "phone")
    if paired:
        ctx.add_init_script(PHONE)
    pg = ctx.new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".up-crown", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    crown(pg).click()
    menu(pg).wait_for(timeout=WAIT_MS)
    return pg, errors


def test_the_paired_phones_menu_has_fix_orkboard_above_notifications_only_when_the_computer_can(gui):
    pg, errors = phone_page(gui, RepairHost(CAN))
    rows = pg.locator(".up-phone .up-phone__row")
    assert [words(r) for r in rows.all()] == ["Fix Orkboard", "Notifications Off", "Unpair this phone"]
    fix = menu(pg).get_by_role("button", name="Fix Orkboard", exact=True)
    assert fix.get_attribute("aria-expanded") == "false" and TITLES["idle"] in words(menu(pg).locator(".up-phone"))
    finish(pg, errors)
    for repair in (CANNOT, None):
        pg, errors = phone_page(gui, RepairHost(repair))
        assert menu(pg).get_by_role("button", name="Fix Orkboard").count() == 0 and menu(pg).get_by_role("switch", name="Notifications").count() == 1
        finish(pg, errors)
    pg, errors = phone_page(gui, RepairHost(CAN), paired=False)
    assert menu(pg).get_by_role("button", name="Fix Orkboard").count() == 0, "the page from the link has no rows"
    finish(pg, errors)


def test_the_phones_fix_row_opens_the_panels_content_in_the_menu_without_save_logs_and_fix_it_sends_the_line(gui):
    host = RepairHost(CAN)
    pg, errors = phone_page(gui, host)
    menu(pg).get_by_role("button", name="Fix Orkboard", exact=True).click()
    fixes = menu(pg).locator(".up-phone__fix")
    fixes.wait_for(timeout=WAIT_MS)
    assert "What went wrong? (optional)" in fixes.inner_text() and buttons(fixes) == ["Fix it"] and "Save logs" not in menu(pg).inner_text()
    assert "Starts Claude Code on Orkboard's own code with this and the logs; you say go in the Claude app." in words(fixes)
    shot(pg, "d119-phone-idle.png")
    fixes.locator("input").fill("From work")
    pg.keyboard.press("Enter")
    got = calls(pg, host, "repair.start")
    assert len(got) == 1 and got[0]["said"] == "From work" and "page" in got[0]
    pg.wait_for_function("() => document.querySelector('.up-phone__row').dataset.repairState === 'working'", timeout=WAIT_MS)
    assert menu(pg).locator(".up-phone__fix").count() == 0 and "Claude is fixing Orkboard" in words(menu(pg).locator(".up-phone"))
    finish(pg, errors)


def open_fix(row):
    """The row's content open in the menu (a press opens it, a second shuts it)."""
    if row.get_attribute("aria-expanded") != "true":
        row.click()
    return row.page.locator(".up-menu .up-phone__fix")


def test_the_phones_fix_row_in_each_state_stop_update_and_try_again(gui):
    host = RepairHost(WORKING)
    pg, errors = phone_page(gui, host)
    row = menu(pg).get_by_role("button", name="Fix Orkboard", exact=True)
    fixes = open_fix(row)
    assert "Claude is fixing it in the Claude app, session Fix Orkboard." in words(fixes) and buttons(fixes) == ["Stop the fix"]
    fixes.get_by_role("button", name="Stop the fix").click()
    assert calls(pg, host, "repair.stop") == [{}]
    host.say(**READY)
    pg.wait_for_function("() => document.querySelector('.up-phone__row').dataset.repairState === 'ready'", timeout=WAIT_MS)
    assert "is-ready" in row.get_attribute("class").split() and color(row) == pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-alert)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")
    fixes = open_fix(row)
    assert "The fix is in: Keep the seat when the socket drops" in words(fixes) and "and 2 more" in words(fixes)
    shot(pg, "d119-phone-ready.png")
    fixes.get_by_role("button", name="Update and restart").click()
    assert calls(pg, host, "repair.update") == [{}]
    host.say(**FAILED)
    pg.wait_for_function("() => document.querySelector('.up-phone__row').dataset.repairState === 'failed'", timeout=WAIT_MS)
    fixes = open_fix(row)
    assert fixes.locator("pre").inner_text() == FAILED["error"] and buttons(fixes) == ["Try again"]
    fixes.get_by_role("button", name="Try again").click()
    assert len(calls(pg, host, "repair.start")) == 1
    finish(pg, errors)


def test_the_phones_crown_menu_has_report_a_problem_that_opens_the_panel(gui):
    host = RepairHost(CAN)
    pg, errors = phone_page(gui, host, paired=False)
    item = menu(pg).get_by_role("button", name="Report a problem…")
    assert item.count() == 1 and item.locator(".ork-sign.bug").count() == 1
    item.click()
    p = panel(pg)
    p.wait_for(timeout=WAIT_MS)
    assert menu(pg).count() == 0 and "What went wrong? (optional)" in p.inner_text() and buttons(p) == ["Fix it", "Save logs"]
    box, size = p.bounding_box(), pg.viewport_size
    assert box["x"] >= 0 and box["x"] + box["width"] <= size["width"] + 1, "inside the phone's window"
    p.locator("input").fill("From the sofa")
    p.get_by_role("button", name="Fix it").click()
    assert calls(pg, host, "repair.start")[0]["said"] == "From the sofa"
    finish(pg, errors)
