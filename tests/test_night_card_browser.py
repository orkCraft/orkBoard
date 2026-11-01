"""Spec 121 part F (docs/specs/121-the-day-the-morning-and-the-night.md §7.2, §7.3, §9; decisions §199.4–§199.5; mockup docs/mockups/hearing/ §5), in a real browser against a stub host.

The morning's card: when `ideas.night` returns a record, the Orkmaster's card is the first of the hand (the moon sign, the crowned head, *The night: 3 goals in dev*, *Since 01:00*); lifted it has a row a goal (its rune, its short name, its screens) with
**Play it** (`ideas.play {path, idea}` of the first screen, the die thrown as today), *Failed: <goal>* with its reason, *Reverted*, *Checks red: <check>* and **Done**, and tells the host it was opened (`ideas.night {opened: true}`) once; **Done** sends
it away until the next night. On the phone the rows stay and **Play it** is *Play it on the computer*. A host with no record, or without the command, draws no card and no error. **Work at night** in Settings with the host's words; a plan held for the
night says *Waits for the night (01:00)* and **Build it now** (`ideas.start_now`). Screenshots to $NIGHT_SHOTS when it is set."""
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
from tests.test_hand_desktop_browser import HandHost, call, open_hand, sig  # noqa: E402
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


def window(gui, width="wide", **kw):
    pg, host, log = open_hand(gui, host=NightHost(**kw), width=width)
    pg.locator(".up-card" if width == "phone" else ".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def card(pg):
    return pg.locator('.hand-card[data-kind="night"]')


def lift(pg):
    card(pg).first.click(position={"x": 10, "y": 24})
    pg.locator('.hand-lifted .hand-way--night').wait_for(timeout=WAIT_MS)


def rows(pg):
    return pg.locator(".hand-way--night .nt-row")


def nights(host):
    return [a for n, a in host.log if n == "ideas.night"]


# -- the card -----------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_morning_is_the_orkmasters_first_card_with_the_moon_the_crowned_head_and_the_count_of_what_was_done(gui, width):
    pg, host, log = window(gui, width)
    try:
        c = card(pg)
        c.wait_for(timeout=WAIT_MS)
        assert c.count() == 1 and c.get_attribute("data-top") == "1" and c.locator(".hand-card__name").text_content().strip() == "The night: 3 goals in dev"
        assert c.locator(".hand-card__window .ork-sign.moon").count() == 1 and c.locator(".hand-card__asker img.ork-race__head").get_attribute("src").endswith("peon-crown.png"), "the moon and the Orkmaster's crown"
        assert pg.locator(".hand-lane").nth(0).locator(".hand-stack").evaluate_all("els => els.map((e) => e.dataset.stack)")[-1].startswith("night/"), "in the first lane, in front"
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Since 01:00"
        assert c.locator(".ork-gem").count() == 0, "a count of what was done, never a price"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-night-card")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_card_is_the_first_of_the_orkmasters_lane_in_front_of_its_other_cards(gui):
    host = NightHost()
    host.needs.append({"kind": "paid", "goal": "", "idea": "", "title": "Go on paid?", "text": "Go on paid?", "at": "2026-10-20T09:00:00", "priority": "high", "blocks": True,
                       "tool": "claude", "name": "Claude Code", "until": "2026-10-22T18:00", "usd_task": 0.4})
    pg, host, log = open_hand(gui, host=host)
    try:
        card(pg).wait_for(timeout=WAIT_MS)
        lane = pg.locator('.hand-lane[data-lane="0"] .hand-stack')
        assert lane.count() == 2 and lane.nth(0).get_attribute("data-stack").startswith("night/") and lane.nth(1).get_attribute("data-stack").startswith("paid"), "the morning's card in front, the question behind it"
        z = lambda i: int(lane.nth(i).evaluate("e => getComputedStyle(e.closest('.hand-slot')).getPropertyValue('--z')"))        # noqa: E731
        assert z(0) > z(1)
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- lifted: the rows --------------------------------------------------------------------------------------------------------------------------

def test_lifted_a_row_a_goal_with_its_screens_and_play_it_then_what_failed_was_reverted_or_went_red(gui):
    pg, host, log = window(gui)
    try:
        lift(pg)
        assert rows(pg).count() == 6
        goal = rows(pg).nth(0)
        assert goal.locator(".ork-elem").count() == 1 and goal.locator(".nt-t b").text_content() == "Lobby music loop" and goal.locator(".nt-t span").text_content() == "Lobby · Room"
        assert goal.get_by_role("button", name="Play it: Lobby music loop").count() == 1 and rows(pg).nth(1).locator(".nt-t span").text_content() == "Results"
        assert rows(pg).nth(2).locator(".nt-t span").count() == 0 and rows(pg).nth(2).locator('[data-act="play"]').count() == 1, "a goal with no screen of its own is played at the preview's first page"
        bad = [(r.get_attribute("data-row"), r.locator(".nt-t b").text_content(), (r.locator(".nt-t span").text_content() if r.locator(".nt-t span").count() else "")) for r in rows(pg).all()[3:]]
        assert bad == [("failed", "Failed: Timer reset", "The reset test failed: the seat is freed after 5 s"), ("reverted", "Reverted", 'Revert "Emoji reactions" · abc1234'),
                       ("checks", "Checks red: npm test -- export", "Export scores · Check the file")]
        assert pg.locator('.hand-way--night [data-answer="done"]').text_content().strip() == "Done" and pg.locator(".nt-phone").count() == 0
        assert nights(host).count({"opened": True}) == 1, "the host is told it was opened"
        narrow.no_sideways(pg)
        shot(pg, "wide-night-lifted")
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".hand-lifted", state="detached", timeout=WAIT_MS)
        lift(pg)
        assert nights(host).count({"opened": True}) == 1, "once a night"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_open_on_a_failed_row_picks_its_goal(gui):
    pg, host, log = window(gui)
    try:
        lift(pg)
        rows(pg).nth(3).get_by_role("button", name="Open").click()
        assert sig(pg, "frame/state.js", "picked") == "timer"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_done_sends_it_away_until_the_next_night(gui):
    pg, host, log = window(gui)
    try:
        lift(pg)
        pg.locator('[data-answer="done"]').click()
        pg.wait_for_selector('.hand-card[data-kind="night"]', state="detached", timeout=WAIT_MS)
        host.bump(None)                                                                                      # the Board moves on: the same night's card does not come back
        pg.wait_for_timeout(700)
        assert card(pg).count() == 0
        assert pg.evaluate("() => localStorage.getItem('orkboard.night.done')").count(SINCE) == 1
        pg.reload()
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        assert card(pg).count() == 0, "kept on this device"
    finally:
        pg.close()


def test_a_night_with_nothing_or_a_host_without_the_command_has_no_card_and_no_error(gui):
    pg, host, log = window(gui, night=None)
    try:
        pg.wait_for_timeout(900)
        assert card(pg).count() == 0 and _calls(pg, host, "ideas.night")
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = window(gui, older=True)
    try:
        pg.wait_for_timeout(900)
        assert card(pg).count() == 0 and pg.locator(".hand-stack").count() >= 1
    finally:
        pg.close()
    assert not [l for l in log if l.startswith("pageerror")], "\n".join(log)


# -- Play it ------------------------------------------------------------------------------------------------------------------------------------

def test_play_it_opens_play_at_the_first_screens_path_and_the_die_is_thrown(gui):
    pg, host, log = window(gui)
    try:
        lift(pg)
        rows(pg).nth(1).get_by_role("button", name="Play it: Room codes").click()
        pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
        asked = _calls(pg, host, "ideas.play", 2)
        assert asked[0] == {"peek": True} and asked[1] == {"path": "/results", "idea": "codes"}, asked
        pg.locator(".play-throw").first.wait_for(timeout=WAIT_MS)                                             # thrown as the die throws it
        pg.locator("iframe.play-frame").wait_for(timeout=WAIT_MS)
        assert pg.locator("iframe.play-frame").get_attribute("src") == PLAYING["url"]
        assert pg.locator(".hand-lifted").count() == 0, "the card is put back"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_play_it_on_a_goal_with_no_screen_asks_no_path_and_a_play_already_playing_is_asked_at_the_path(gui):
    pg, host, log = window(gui)
    try:
        lift(pg)
        rows(pg).nth(2).get_by_role("button", name="Play it: Kick a player").click()
        pg.locator("iframe.play-frame").wait_for(timeout=WAIT_MS)
        assert _calls(pg, host, "ideas.play", 2)[1] == {"idea": "kick"}
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = window(gui, playing=True)
    try:
        lift(pg)
        rows(pg).nth(0).get_by_role("button", name="Play it: Lobby music loop").click()
        pg.locator('.table-over[data-kind="play"]').wait_for(timeout=WAIT_MS)
        asked = _calls(pg, host, "ideas.play", 2)
        assert asked[0] == {"peek": True} and asked[1] == {"path": "/lobby", "idea": "music"}, "no second start: the page at the path"
        pg.locator("iframe.play-frame").wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the phone: the rows stay, Play is the computer's -------------------------------------------------------------------------------------------

def test_on_the_phone_the_rows_stay_and_play_it_is_play_it_on_the_computer(gui):
    pg, host, log = window(gui, "phone")
    try:
        pg.locator(".hand-lifted--up .hand-way--night").wait_for(timeout=WAIT_MS)
        assert rows(pg).count() == 6 and pg.locator('.hand-way--night [data-act="play"]').count() == 0 and pg.locator(".hand-way--night").get_by_role("button", name="Play it").count() == 0
        assert pg.locator(".nt-phone").text_content().strip() == "Play it on the computer"
        assert pg.locator('[data-answer="done"]').bounding_box()["height"] >= 43
        assert nights(host).count({"opened": True}) == 1
        rows(pg).nth(3).get_by_role("button", name="Open").click()
        assert sig(pg, "frame/state.js", "picked") == "timer"
        narrow.no_sideways(pg)
        shot(pg, "phone-night")
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        assert pg.locator('.hand-lifted [data-night="waits"]').text_content().strip() == "Waits for the night (01:00)"
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
