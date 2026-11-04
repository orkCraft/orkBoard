"""Spec 144 B (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md; decisions §224.3, §225.1), in a real browser against a stub host: the setting *Give me time to look* in Settings (four
choices and the line under them, 2 h at first), and To review's card for a spec made: a node with `look_until` in the future says *Starts by itself at 13:40* and the pile *next at 13:40*, a clock time and
never minutes; *Start now* passes its plan (`ideas.start_now`); a card with no `look_until` reads as before."""
from __future__ import annotations

import datetime as dt
import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, back, open_column, ripe  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, need, node, open_hand, shot  # noqa: E402
from tests.test_night_card_browser import open_settings  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser


def at(seconds_ahead: float) -> tuple[float, str]:
    """`look_until` (epoch seconds) and its local clock time as the page says it."""
    when = time.time() + seconds_ahead
    day = dt.datetime.fromtimestamp(when)
    return when, day.strftime("%H:%M") if day.date() == dt.date.today() else day.strftime("%a %H:%M")      # the weekday is said when it is not today


class LookHost(HandHost):
    def __init__(self, look="2h"):
        super().__init__(bare=True)
        self.look = look

    def handle(self, name, a):
        if name == "ideas.board_set" and "look_wait" in a:
            self.log.append((name, a))
            self.look = a["look_wait"]
            return self.bump({"look_wait": self.look})
        got = super().handle(name, a)
        if name == "ideas.board" and isinstance(got, dict):
            got["look_wait"] = self.look
        return got


def line(pg):
    return pg.locator('[data-settings="look-wait-line"]').inner_text().strip()


def test_the_setting_has_four_choices_and_the_line_under_it_says_what_follows(gui):
    pg, host, log = open_hand(gui, host=LookHost())
    try:
        pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
        open_settings(pg)
        box = pg.locator('[data-settings="look-wait"]')
        box.wait_for(timeout=WAIT_MS)
        assert "give me time to look" in box.inner_text().lower()
        assert [t.strip() for t in box.get_by_role("radio").all_inner_texts()] == ["30 min", "2 h", "until tonight", "do not wait"]
        assert box.locator('[role=radio][aria-checked=true]').inner_text().strip() == "2 h"
        assert line(pg) == "If you do not look, it starts: you give every spec 2 hours"
        box.get_by_role("radio", name="until tonight").click()
        assert _sent(pg, host, ("ideas.board_set", {"look_wait": "tonight"}))
        pg.wait_for_function("() => document.querySelector('[data-settings=\"look-wait-line\"]').innerText.includes('until tonight')", timeout=WAIT_MS)
        assert line(pg) == "If you do not look, it starts: you give every spec until tonight"
        box.get_by_role("radio", name="do not wait").click()
        pg.wait_for_function("() => document.querySelector('[data-settings=\"look-wait-line\"]').innerText.includes('as soon as')", timeout=WAIT_MS)
        assert line(pg) == "A spec starts as soon as it is made"
        shot(pg, "wide-look-wait-setting")
    finally:
        pg.close()
    assert not log, "\n".join(log)


class WaitingHost(ColumnHost):
    """To review holds a spec made that waits for its look (13:40-ish), one whose look has gone by, and a decision's wait as before."""

    def __init__(self):
        super().__init__()
        until, self.clock = at(3 * 3600)
        self.nodes = [n for n in self.nodes if n["slug"] not in ("timer", "scoring")]      # …so that the card of a look is the front one
        self.nodes += [node("looking", "tech", "Rename a room after it is made", "table", state="plan", agreed=True, element="lava", look_until=until,
                            start_at=dt.datetime.fromtimestamp(until).strftime("%Y-%m-%dT%H:%M:%S"), back=back()),
                       node("later", "design", "Lobby in Polish again", "table", state="plan", agreed=True, element="ice", look_until=time.time() - 60, back=back())]


    def handle(self, name, a):
        if name == "ideas.start_now":
            self.log.append((name, a))
            return self.bump({"ok": True})
        return super().handle(name, a)


def test_a_spec_waiting_for_its_look_says_the_clock_time_and_never_minutes(gui):
    pg, host, log = open_column(gui, host=WaitingHost())
    try:
        card = pg.locator('.col-card[data-goal="looking"]')
        card.wait_for(timeout=WAIT_MS)
        assert card.get_attribute("data-pile") == "review"
        assert f"Starts by itself at {host.clock}" in card.get_attribute("aria-label")
        under = pg.locator('[data-under="review"]').inner_text().strip()
        assert under == f"next at {host.clock}" or under.startswith("next at "), under
        for words in (card.get_attribute("aria-label"), under):
            assert " min" not in words and "in 4" not in words
        assert pg.locator('.col-card[data-goal="looking"] .col-count, .col-card[data-goal="looking"] .col-wbar:not(.is-quiet)').count() == 0, "its bar is quiet and has no number"
        later = pg.locator('.col-card[data-goal="later"]')
        assert "Starts by itself" not in later.get_attribute("aria-label"), "a look gone by reads as a card with no look"
        shot(pg, "wide-look-wait-column")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_start_now_on_a_spec_waiting_for_its_look_passes_its_plan(gui):
    pg, host, log = open_column(gui, host=WaitingHost())
    try:
        pg.locator('.col-card[data-goal="looking"]').click()
        acts = pg.locator('.col-lift[data-lift="acts"]')
        acts.wait_for(timeout=WAIT_MS)
        assert f"Starts by itself at {host.clock}" in acts.inner_text() and acts.get_by_role("button", name="Hold").count() == 0
        acts.get_by_role("button", name="Start now").click()
        assert _sent(pg, host, ("ideas.start_now", {"slug": "looking"}))
    finally:
        pg.close()
