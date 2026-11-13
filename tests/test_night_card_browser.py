"""The night (docs/specs/121-the-day-the-morning-and-the-night.md §7.3, §9; docs/specs/128 part C.3, decisions §199.4, §206.9), in a real browser against a stub host.

There is no morning's card any more (§199.5 goes): when `ideas.night` returns a record, the goals done in the night lie in the discard each with a small moon on its card until its result is seen (and a moon on its row over the pane), on the first look after the night
they are dealt into the discard one by one (once for a night, kept on this device; none under reduced motion), the host is told once (`ideas.night {opened: true}`), and a night's failure is a failed task, a card of the hand like any other (tests/test_thrown_browser.py).
A host with no record, or without the command, draws nothing and no error. **Work at night** in Settings with the host's words; a plan held for the night says *Later, tonight 01:00* and **Build it now** (`ideas.start_now`). Screenshots to $NIGHT_SHOTS when it is set."""
from __future__ import annotations

import base64
import copy
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["NIGHT_SHOTS"]) if os.environ.get("NIGHT_SHOTS") else None
PAGE = base64.b64encode(b"<!doctype html><title>Game</title><body style='background:#123'><h1>dev's build</h1>").decode()
PLAYING = {"state": "playing", "url": f"data:text/html;base64,{PAGE}", "commit": "a" * 40, "short": "aaaaaaa", "dev": "a" * 40, "logo": ""}
SINCE = "2026-11-01T01:00:00+01:00"
NIGHT = {"since": SINCE, "hours": 8, "into": "dev", "empty": False, "play": None,
         "goals": [{"slug": "music", "short": "Lobby music loop", "title": "Lobby music loop", "goal": "tech", "done": True,
                    "screens": [{"screen": "lobby", "name": "Lobby", "path": "/lobby"}, {"screen": "room", "name": "Room", "path": "/rooms/:id"}]},
                   {"slug": "codes", "short": "Room codes", "title": "Room codes are four letters, no look-alikes", "goal": "design", "done": True,
                    "screens": [{"screen": "results", "name": "Results", "path": "/results"}]},
                   {"slug": "kick", "short": "Kick a player", "title": "Kick a player from the room", "goal": "tech", "done": False, "screens": []}],
         "failed": [{"slug": "timer", "short": "Timer reset", "title": "The timer doesn't reset after a reconnect", "task": "Reset the clock", "why": "The reset test failed: the seat is freed after 5 s"}],
         "reverts": [{"sha": "abc1234", "subject": 'Revert "Emoji reactions"', "at": "2026-11-01T03:10:00+01:00"}],
         "checks": [{"slug": "export", "short": "Export scores", "title": "Export the round scores", "task": "Check the file", "check": "npm test -- export"}]}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


class NightHost(HandHost):
    """The hand's host that answers `ideas.night` with `night` (None: the night did nothing; `older`: a host that does not know the command) and Play with `play`: `stopped` until a start, then `playing`; `peek` says what it is."""

    def __init__(self, night=NIGHT, older=False, playing=False, **kw):
        super().__init__(**kw)
        self.night, self.older, self.playing = copy.deepcopy(night), older, playing
        self.work_at_night = False
        self.night_words = None

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            if self.older and m["name"] == "ideas.night":                                                    # a host that does not know the command refuses it in words
                self.log.append((m["name"], m["args"]))
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": "Unknown command: ideas.night"}))
            else:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
        ws.on_message(on_message)

    def handle(self, name, a):
        if name == "ideas.night":
            self.log.append((name, a))
            return copy.deepcopy(self.night)
        if name == "ideas.play":
            self.log.append((name, a))
            if a.get("peek"):
                return dict(PLAYING) if self.playing else {"state": "stopped"}
            self.playing = True
            return dict(PLAYING)
        if name == "ideas.play_stop":
            self.log.append((name, a))
            self.playing = False
            return {"ok": True, "stopped": True}
        if name == "ideas.board":
            got = super().handle(name, a)
            got["work_at_night"] = self.work_at_night
            if self.night_words:
                got["night_words"] = self.night_words
            return got
        return super().handle(name, a)


def window(gui, width="narrow", reduced=False, init=None, prep=None, **kw):
    """The page against a NightHost (at the narrow width by default: the pile is there; Release's lane holds the same cards whole at the wide one); `reduced`: under reduced motion from the first frame, `init`: a script run before the page's own (it watches the discard)."""
    server, browser = gui
    host = NightHost(**kw)
    if prep:
        prep(host)
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    if reduced:
        pg.emulate_media(reduced_motion="reduce")
    if init:
        pg.add_init_script(init)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".up-card" if width == "phone" else ".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log




def nights(host):
    return [a for n, a in host.log if n == "ideas.night"]


def pile(pg):
    return pg.locator(":is(.release-lane, .table-end) .table-discard")


def top(pg):
    return pg.locator(":is(.release-lane, .table-end) .table-discard .hand-done")


# -- no morning's card; the moon in the discard -------------------------------------------------------------------------------------------------



def test_a_goal_done_in_the_night_lies_in_the_discard_under_a_small_moon_until_its_result_is_seen(gui):
    pg, host, log = window(gui, reduced=True)                                                              # (reduced motion: no deal to wait for)
    try:
        top(pg).wait_for(timeout=WAIT_MS)
        pg.locator(':is(.release-lane, .table-end) .hand-done[data-moon="1"]').wait_for(timeout=WAIT_MS)
        assert top(pg).get_attribute("data-slug") == "music" and top(pg).locator(".hand-done__moon .ork-sign.moon").count() == 1, "the newest done goal is the pile's top, a moon on it"
        assert top(pg).locator(".corner__kind.is-success .ork-sign.check").count() == 1, "still the card of a goal done (its done sign in the top row: spec 147 A.3)"
        shot(pg, "wide-night-moon")
        top(pg).click()
        pg.locator(".hand-discardview").wait_for(timeout=WAIT_MS)
        rows = pg.locator(".hand-drow")
        assert rows.count() == 2 and [rows.nth(i).locator(".hand-drow__moon").count() for i in range(2)] == [1, 1], "a moon on each of the night's goals in the list"
        assert pg.locator(".hand-drow__moon .ork-sign.moon").count() == 2
        rows.nth(0).click()                                                                                  # its result is seen: it leaves the discard, so does its moon
        pg.wait_for_function("() => document.querySelector(':is(.release-lane, .table-end) .hand-done')?.dataset.slug === 'codes'", timeout=WAIT_MS)
        assert host.seen_log == ["music"] and top(pg).get_attribute("data-moon") == "1" and pile(pg).get_attribute("data-n") == "0", "it is gone from the pile and the next one keeps its moon"
    finally:
        pg.close()
    assert not log, "\n".join(log)




# -- the first look: dealt one by one ----------------------------------------------------------------------------------------------------------







# -- Work at night, and a plan held for it -------------------------------------------------------------------------------------------------------

def open_settings(pg):
    pg.evaluate("() => import('/static/js/frame/place.js').then((m) => m.openPlace('settings', {}, 'Settings'))")
    pg.locator('.place[aria-label="Settings"]').wait_for(timeout=WAIT_MS)


def test_work_at_night_is_a_setting_in_the_hosts_words_and_a_press_sets_it(gui):
    pg, host, log = window(gui, night=None)
    try:
        open_settings(pg)
        box = pg.locator('[data-settings="work-at-night"]')
        assert box.inner_text().strip().endswith("Work at night") and not box.locator("input").is_checked()
        assert pg.locator('[data-settings="work-at-night-hint"]').inner_text().strip() == ("What you decide by day is built in the night's window (01:00–07:00). Talk, hearings and sketches still run by day. "
                                                                                            "A bug's short way, and anything you start with a press, starts at once.")
        box.locator("i").click()
        assert _calls(pg, host, "ideas.board_set")[0] == {"work_at_night": True}
        shot(pg, "wide-night-setting")
    finally:
        pg.close()
    assert not log, "\n".join(log)






@pytest.mark.parametrize("width", ("wide", "phone"))
def test_a_plan_that_starts_tonight_says_so_and_build_it_now_starts_it_at_once(gui, width):
    host = NightHost(night=None)
    export = next(n for n in host.nodes if n["slug"] == "export")
    export["start_at"] = "night"
    pg, host, log = open_hand(gui, host=host, width=width)
    try:
        pg.locator(".up-card" if width == "phone" else ".hand-stack").first.wait_for(timeout=WAIT_MS)
        if width == "phone":
            pg.locator('.up-card[data-key^="goal:export"], .up-card[data-key="goal:export"]').first.click()
        else:
            pg.locator('.hand-card[data-kind="plan"]').first.click(position={"x": 10, "y": 24})
        pg.locator('.hand-lifted [data-night="waits"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.hand-lifted [data-night="waits"]').text_content().strip() == "Later, tonight 01:00"
        now = pg.locator('.hand-lifted [data-answer="build-now"]')
        assert now.text_content().strip() == "Build it now" and "primary" in now.get_attribute("class")
        assert pg.get_by_role("button", name="Start the work").count() == 0
        assert pg.locator(".hand-lifted .hand-spend").count() == 1, "its cost is said under it"
        now.click()
        assert _calls(pg, host, "ideas.start_now")[0] == {"slug": "export", "via": "hand"}
        narrow.no_sideways(pg)
        shot(pg, f"{width}-held-plan")
    finally:
        pg.close()
    assert not log, "\n".join(log)
