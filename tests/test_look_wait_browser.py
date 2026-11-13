"""Spec 144 B (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md; decisions §224.3, §225.1), in a real browser against a stub host: the setting *Give me time to look* in Settings (four
choices and the line under them, 2 h at first)."""
from __future__ import annotations

import datetime as dt
import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, open_hand, shot  # noqa: E402
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
        pg.wait_for_selector(".hand :is(.hand-plus, [data-blank-deck])", timeout=WAIT_MS)
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
