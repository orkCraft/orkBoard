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


def window(gui, width="wide", reduced=False, init=None, **kw):
    """The page against a NightHost; `reduced`: under reduced motion from the first frame, `init`: a script run before the page's own (it watches the discard)."""
    server, browser = gui
    host = NightHost(**kw)
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


# What the discard looked like, each time it changed: `place` (nothing in it), else `<slug of the card on top>/<how many lie under it>/<the slug dealt just now>`.
WATCH = """() => { const seen = window.__pile = [];
  const look = () => { const d = document.querySelector('.table-discard'), top = d?.querySelector('.hand-done');
    const now = !d ? (document.querySelector('.table-end .table-place') ? 'place' : 'none') : `${top?.dataset.slug || 'back'}/${d.dataset.n}/${top?.dataset.dealt || ''}`;
    if (seen[seen.length - 1] !== now) seen.push(now); };
  new MutationObserver(look).observe(document, { subtree: true, childList: true, attributes: true }); }"""
INIT = "document.addEventListener('DOMContentLoaded', (" + WATCH + "));"


def nights(host):
    return [a for n, a in host.log if n == "ideas.night"]


def pile(pg):
    return pg.locator(".table-end .table-discard")


def top(pg):
    return pg.locator(".table-end .table-discard .hand-done")


# -- no morning's card; the moon in the discard -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.PHONE_WIDTHS)
def test_there_is_no_morning_card_in_the_hand_though_the_night_did_something(gui, width):
    pg, host, log = window(gui, width)
    try:
        _calls(pg, host, "ideas.night")
        pg.wait_for_timeout(900)
        assert pg.locator('[data-kind="night"], [data-key^="night/"], [data-stack^="night/"], .hand-way--night').count() == 0, "the morning's card is not dealt"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_done_in_the_night_lies_in_the_discard_under_a_small_moon_until_its_result_is_seen(gui):
    pg, host, log = window(gui, reduced=True)                                                              # (reduced motion: no deal to wait for)
    try:
        top(pg).wait_for(timeout=WAIT_MS)
        pg.locator('.table-end .hand-done[data-moon="1"]').wait_for(timeout=WAIT_MS)
        assert top(pg).get_attribute("data-slug") == "music" and top(pg).locator(".hand-done__moon .ork-sign.moon").count() == 1, "the newest done goal is the pile's top, a moon on it"
        moon, kind = top(pg).locator(".hand-done__moon").bounding_box(), top(pg).locator(".corner__kind").bounding_box()
        assert moon["x"] + moon["width"] <= kind["x"] + 1 and abs((moon["y"] + moon["height"] / 2) - (kind["y"] + kind["height"] / 2)) <= 3, "in the top row, left of the kind's sign (spec 147 A.3: the card has no window now)"
        assert top(pg).locator(".corner__kind.is-success .ork-sign.check").count() == 1, "still the card of a goal done (its done sign in the top row: spec 147 A.3)"
        shot(pg, "wide-night-moon")
        top(pg).click()
        pg.locator(".hand-discardview").wait_for(timeout=WAIT_MS)
        rows = pg.locator(".hand-drow")
        assert rows.count() == 2 and [rows.nth(i).locator(".hand-drow__moon").count() for i in range(2)] == [1, 1], "a moon on each of the night's goals in the list"
        assert pg.locator(".hand-drow__moon .ork-sign.moon").count() == 2
        rows.nth(0).click()                                                                                  # its result is seen: it leaves the discard, so does its moon
        pg.wait_for_function("() => document.querySelector('.table-end .hand-done')?.dataset.slug === 'codes'", timeout=WAIT_MS)
        assert host.seen_log == ["music"] and top(pg).get_attribute("data-moon") == "1" and pile(pg).get_attribute("data-n") == "0", "it is gone from the pile and the next one keeps its moon"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_the_night_did_not_finish_wears_no_moon(gui):
    night = copy.deepcopy(NIGHT)
    night["goals"] = [g | {"done": False} if g["slug"] == "codes" else g for g in night["goals"]]
    pg, host, log = window(gui, reduced=True, night=night)
    try:
        top(pg).wait_for(timeout=WAIT_MS)
        pg.locator('.table-end .hand-done[data-moon="1"]').wait_for(timeout=WAIT_MS)
        top(pg).click()
        pg.locator(".hand-discardview").wait_for(timeout=WAIT_MS)
        moons = pg.locator(".hand-drow").evaluate_all("els => els.map((e) => [e.dataset.slug, !!e.querySelector('.hand-drow__moon')])")
        assert moons == [["music", True], ["codes", False]], moons
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the first look: dealt one by one ----------------------------------------------------------------------------------------------------------

def test_on_the_first_look_after_the_night_its_goals_are_dealt_into_the_discard_one_by_one_once(gui):
    pg, host, log = window(gui, init=INIT)
    try:
        pg.wait_for_function("() => window.__pile.includes('codes/0/codes') && window.__pile.some((s) => s.startsWith('music/1/music'))", timeout=WAIT_MS)
        seen = pg.evaluate("() => window.__pile")
        order = [s for s in seen if s.endswith("/codes") or s.endswith("/music")]
        assert order == ["codes/0/codes", "music/1/music"], f"one by one, the oldest first: {order}"
        assert seen[seen.index("codes/0/codes") - 1] in ("place", "back/1/", "back/0/"), f"the goals lay out of the pile until their turn: {seen}"
        pg.wait_for_function("() => !document.querySelector('.table-discard .ork-deal')", timeout=WAIT_MS)
        assert top(pg).get_attribute("data-slug") == "music" and pile(pg).get_attribute("data-n") == "1" and top(pg).get_attribute("data-moon") == "1"
        assert nights(host).count({"opened": True}) == 1, "the host is told once"
        assert pg.evaluate("() => Object.values(JSON.parse(localStorage.getItem('orkboard.night.dealt')))") == [SINCE], "kept on this device"
        shot(pg, "wide-night-dealt")
        pg.reload()                                                                                          # the same night is not dealt again
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(1200)
        assert pg.evaluate("() => document.querySelectorAll('.table-discard .ork-deal').length") == 0 and top(pg).get_attribute("data-slug") == "music"
        assert nights(host).count({"opened": True}) == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_nights_goals_lie_in_the_discard_at_once(gui):
    pg, host, log = window(gui, reduced=True, init=INIT)
    try:
        pg.wait_for_function("() => window.__pile.some((s) => s.startsWith('music/1'))", timeout=WAIT_MS)
        pg.wait_for_timeout(1000)
        seen = pg.evaluate("() => window.__pile")
        assert not [s for s in seen if s.endswith("/codes") or s.endswith("/music")] and not [s for s in seen[seen.index("music/1/"):] if s.startswith("back")], f"no deal, no hold: {seen}"
        assert nights(host).count({"opened": True}) == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_night_with_nothing_or_a_host_without_the_command_has_no_moon_and_no_error(gui):
    pg, host, log = window(gui, night=None)
    try:
        pg.wait_for_timeout(900)
        assert _calls(pg, host, "ideas.night") and pg.locator(".hand-done__moon").count() == 0 and top(pg).count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = window(gui, older=True)
    try:
        pg.wait_for_timeout(900)
        assert pg.locator(".hand-done__moon").count() == 0 and pg.locator(".hand-stack").count() >= 1
    finally:
        pg.close()
    assert not [l for l in log if l.startswith("pageerror")], "\n".join(log)


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


def test_when_i_am_at_the_computer_is_a_setting_of_rows_added_edited_and_removed_and_each_whole_row_is_sent(gui):
    """Spec 138 B.1: the Settings section with no hours says that nothing waits; *Add hours* offers weekday evenings and sends them; a day and a time are edited; *Remove* sends none."""
    pg, host, log = window(gui, night=None)
    try:
        open_settings(pg)
        box = pg.locator('[data-settings="hours"]')
        assert "when i am at the computer" in box.inner_text().lower() and box.locator("[data-hours]").count() == 0
        assert "nothing waits for you" in pg.locator('[data-settings="hours-hint"]').inner_text()
        box.locator("[data-hours-add]").click()
        pg.wait_for_function("() => document.querySelectorAll('[data-hours]').length === 1")
        assert _calls(pg, host, "ideas.board_set")[-1] == {"hours": [{"days": [0, 1, 2, 3, 4], "from": "19:00", "to": "23:00"}]}
        assert "waits for the first reset inside these hours" in pg.locator('[data-settings="hours-hint"]').inner_text()
        box.locator('[data-hours="0"] .shell-seg__one', has_text="Sat").click()
        assert _calls(pg, host, "ideas.board_set")[-1]["hours"][0]["days"] == [0, 1, 2, 3, 4, 5]
        box.locator('[data-hours-to="0"]').fill("22:30")
        assert _calls(pg, host, "ideas.board_set")[-1]["hours"][0]["to"] == "22:30"
        box.locator('[data-hours-remove="0"]').click()
        assert _calls(pg, host, "ideas.board_set")[-1] == {"hours": []} and box.locator("[data-hours]").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_hosts_own_words_are_what_the_setting_says(gui):
    pg, host, log = open_hand(gui, host=NightHost(night=None))
    host.night_words = {"label": "Work at night", "hint": "The host's own line.", "waits": "Waits", "now": "Now", "now_sketch": "Now, sketch"}
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        host.bump(None)
        pg.wait_for_function("() => document.querySelector('.hand') !== null")
        pg.wait_for_timeout(300)
        open_settings(pg)
        pg.wait_for_function("() => document.querySelector('[data-settings=\"work-at-night-hint\"]')?.innerText.trim() === \"The host's own line.\"", timeout=WAIT_MS)
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
