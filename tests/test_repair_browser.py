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
from tests.test_table_desktop_browser import TableHost, watch  # noqa: E402

pytestmark = pytest.mark.browser

WIDE = {"width": 1280, "height": 800}
CAN = {"can": True, "why": "", "state": "idle", "started_at": None, "landed": [], "error": ""}
READY = {**CAN, "state": "ready", "started_at": 1_761_900_000.0, "landed": [{"sha": "b" * 40, "subject": "Keep the seat when the socket drops"}, {"sha": "a" * 40, "subject": "Older"}, {"sha": "9" * 40, "subject": "Oldest"}]}
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




def fixing_line(pg):
    return pg.locator(".table-balloon[data-balloon=fixing] .table-balloon__line")


# -- the way in: the Orkmaster's … and a crash (spec 139 A.5) ---------------------------------------------------------------------------------------



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




# -- idle ---------------------------------------------------------------------------------------------------------------------------------------



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
    assert pg.locator(".table-balloon[data-balloon=fixing]").count() == 1 and pg.locator(".table-notice").count() == 0, "the Orkmaster says it in the balloon, none in the pane"
    assert not [n for n, _a in host.log if n == "logs.save"], "Fix it saves nothing by itself"
    shot(pg, "s139-fixing-line.png")
    host.say(state="idle", started_at=None)                                                                             # the fix is stopped: the line goes
    pg.wait_for_function("() => !document.querySelector('.table-balloon[data-balloon=fixing]')", timeout=WAIT_MS)
    finish(pg, errors)










# -- working ------------------------------------------------------------------------------------------------------------------------------------





# -- ready --------------------------------------------------------------------------------------------------------------------------------------







# -- failed -------------------------------------------------------------------------------------------------------------------------------------

def test_failed_says_the_error_as_it_is_try_again_sends_the_line_last_sent_and_save_logs_saves(gui):
    host = RepairHost(CAN)
    pg, errors = window(gui, host)
    opened(pg).locator("input").fill("The seat is lost")
    panel(pg).get_by_role("button", name="Fix it").click()
    calls(pg, host, "repair.start")
    host.say(**FAILED)
    pg.wait_for_function("() => !document.querySelector('.table-balloon[data-balloon=fixing]')", timeout=WAIT_MS)
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




# -- the phone ----------------------------------------------------------------------------------------------------------------------------------











