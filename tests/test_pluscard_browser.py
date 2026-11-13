"""The new goal's card in a public repository with the yes (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md F.4; decisions §255.10): the line **Keep off the repository** on the field the + card grows into,
a toggle offered only where the host's snapshot says `keep_off_offered` (a public or unreadable repository with `in_code` true), its choice sent as `keep_off` of `ideas.add` and put back when the goal is sent.
Real browser against a stub host, at the two widths of `tests/narrow.py`. Screenshots to $INCODE_SHOTS when it is set."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, _field, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["INCODE_SHOTS"]) if os.environ.get("INCODE_SHOTS") else None
LINE = "Keep off the repository"


class OfferHost(HandHost):
    """The snapshot says whether the field offers the line (`keep_off_offered`, gui/ideas.py)."""

    def __init__(self, offered=True):
        super().__init__()
        self.offered = offered

    def snapshot(self):
        doc = super().snapshot()
        doc["state"] = copy.deepcopy(doc["state"])
        doc["state"]["keep_off_offered"] = self.offered
        return doc


def open_field(gui, width="wide", offered=True):
    pg, host, log = open_hand(gui, host=OfferHost(offered), width=width)
    pg.locator(".hand :is(.hand-plus, [data-blank-deck])").click()
    return pg, host, log






def test_a_goal_sent_with_the_toggle_on_carries_keep_off_and_the_toggle_is_put_back(gui):
    pg, host, log = open_field(gui)
    try:
        field, area = _field(pg)
        field.locator("[data-keep-off]").click()
        area.fill("Rotate the signing key")
        area.press("Enter")
        sent = _calls(pg, host, "ideas.add")
        assert sent[-1].get("keep_off") is True and sent[-1]["text"] == "Rotate the signing key"
        pg.locator(".hand :is(.hand-plus, [data-blank-deck])").wait_for(timeout=WAIT_MS)
        pg.locator(".hand :is(.hand-plus, [data-blank-deck])").click()
        field, _area = _field(pg)
        assert field.locator("[data-keep-off]").get_attribute("aria-checked") == "false"
    finally:
        pg.close()
    assert not log, "\n".join(log)


