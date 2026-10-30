"""The Orkmaster's line when the work moved to another AI tool (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §4.3, decisions §177.2), in a real browser against a stub host, at the two widths of `tests/narrow.py`: a strip
on the table under the pane's title with the Orkmaster's crowned head and the line in the body face (not a toast); a press on its close button puts it away (kept for the project on this device), a newer move shows again, a day after
`at` it is gone; with no `localStorage` the page works and the line stays away for the run. Screenshots to $MANA_SHOTS when it is set."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_hand_mana_browser import TWO, mana_of  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["MANA_SHOTS"]) if os.environ.get("MANA_SHOTS") else None
LINE = "Claude Code is out until Thu 18:00: the work goes on with Codex."
BACK = "Claude Code is back: the work goes on with it."


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def ago(**delta) -> str:
    return (dt.datetime.now() - dt.timedelta(**delta)).isoformat(timespec="seconds")


def moved(at, line=LINE, to="codex"):
    return {"from": "claude", "to": to, "until": "2026-10-29T18:00", "at": at, "line": line}


def open_notice(gui, move, width="wide"):
    host = HandHost()
    host.limits, host.mana = TWO, mana_of("claude", "codex", moved=move)
    return open_hand(gui, host, width)


def say(pg, host, move):
    host.mana = mana_of("claude", "codex" if move and move["to"] else "claude", moved=move)
    host.bump({})
    pg.wait_for_timeout(150)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_line_is_a_strip_under_the_panes_title_with_the_crowned_head_in_the_body_face(gui, width):
    pg, host, log = open_notice(gui, moved(ago(minutes=5)), width)
    try:
        strip = pg.locator(".table-notice")
        strip.wait_for(timeout=WAIT_MS)
        assert strip.locator(".table-notice__line").inner_text() == LINE and strip.get_attribute("role") == "status"
        head = strip.locator("img.ork-race__head")
        assert "/races/peon-crown" in head.get_attribute("src")                                                                  # the Orkmaster's crowned head
        title, body, bar = pg.locator(".table-title").bounding_box(), pg.locator(".table-body").bounding_box(), strip.bounding_box()
        assert title["y"] + title["height"] <= bar["y"] + 1 and bar["y"] + bar["height"] <= body["y"] + 1                          # under the title, over the map
        assert head.bounding_box()["x"] < strip.locator(".table-notice__line").bounding_box()["x"]
        faces = pg.evaluate("() => [getComputedStyle(document.querySelector('.table-notice__line')).fontFamily, getComputedStyle(document.querySelector('.table-title__pt')).fontFamily]")
        assert faces[0] != faces[1]                                                                                              # the body face, never the pixel face
        assert pg.locator(".ork-toast, .toast").count() == 0                                                                     # not a toast
        close = strip.get_by_role("button", name="Dismiss")
        assert close.count() == 1
        if width == "narrow":
            assert close.bounding_box()["width"] >= 44 and close.bounding_box()["height"] >= 44
            assert bar["x"] >= 0 and bar["x"] + bar["width"] <= pg.viewport_size["width"] + 1
        narrow.no_sideways(pg)
        shot(pg, f"{width}-notice")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_press_on_the_close_button_puts_it_away_and_a_newer_move_shows_again(gui):
    pg, host, log = open_notice(gui, moved(ago(minutes=5)))
    try:
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)
        pg.locator(".table-notice").get_by_role("button", name="Dismiss").click()
        pg.wait_for_selector(".table-notice", state="detached", timeout=WAIT_MS)
        host.bump({})                                                                                                            # the same move, said again by a new snapshot: still put away
        pg.wait_for_timeout(200)
        assert pg.locator(".table-notice").count() == 0
        pg.reload()
        pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-notice").count() == 0                                                                          # kept on this device
        say(pg, host, moved(ago(minutes=1), BACK, to="claude"))                                                                  # a newer move
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-notice__line").inner_text() == BACK
        shot(pg, "wide-notice-newer")
        pg.locator(".table-notice").get_by_role("button", name="Dismiss").click()
        pg.wait_for_selector(".table-notice", state="detached", timeout=WAIT_MS)
        say(pg, host, moved(ago(minutes=10)))                                                                                    # an older one than what was put away stays away
        assert pg.locator(".table-notice").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_day_after_the_move_the_line_is_gone(gui):
    pg, host, log = open_notice(gui, moved(ago(hours=25)))
    try:
        pg.wait_for_selector(".hand-mana", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-notice").count() == 0                                                                          # a day and an hour: gone
        say(pg, host, moved(ago(hours=23, minutes=50)))
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)                                                                    # not yet a day
        say(pg, host, moved(ago(hours=24, minutes=1)))
        pg.wait_for_selector(".table-notice", state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_it_goes_by_itself_when_the_day_runs_out_while_the_page_is_open(gui):
    server, browser = gui
    host = HandHost()
    host.limits, host.mana = TWO, mana_of("claude", "codex", moved=moved(ago(hours=23, minutes=59, seconds=50)))
    pg = narrow.context(browser, "wide").new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)
        pg.wait_for_selector(".table-notice", state="detached", timeout=WAIT_MS + 20000)                                         # ten seconds left: its own timer takes it away
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_line_no_strip_and_no_move_no_strip(gui):
    pg, host, log = open_notice(gui, moved(ago(minutes=5), line="", to=None))
    try:
        pg.wait_for_selector(".hand-mana", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-notice").count() == 0                                                                          # every tool out: the card asks instead, the line has no words
        host.mana = mana_of("claude", "claude")
        host.bump({})
        pg.wait_for_timeout(200)
        assert pg.locator(".table-notice").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_line_is_the_tables_and_stays_while_another_tab_is_open(gui):
    pg, host, log = open_notice(gui, moved(ago(minutes=5)))
    try:
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)
        pg.locator('[data-tab="tech"]').click()
        pg.wait_for_timeout(200)
        assert pg.locator(".table-notice").count() == 1                                                                          # the Orkmaster speaks on every tab
        pg.locator(".hand-die").click()
        pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-notice").count() == 0                                                                          # not over what is opened over the pane
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_without_local_storage_the_line_shows_and_a_press_puts_it_away_for_the_run(gui):
    server, browser = gui
    host = HandHost()
    host.limits, host.mana = TWO, mana_of("claude", "codex", moved=moved(ago(minutes=5)))
    pg = narrow.context(browser, "wide").new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.locator(".table-notice").wait_for(timeout=WAIT_MS)
        pg.locator(".table-notice").get_by_role("button", name="Dismiss").click()
        pg.wait_for_selector(".table-notice", state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)
