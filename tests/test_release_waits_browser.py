"""Spec 168 F4 (decisions §283.29, which changes §261.7 and §273.2): Release and Live wait. In a real browser at the wide width against the road's stub host: a Release already seated keeps its page
(the Board still has the party) but has no tab, and no pane of its checks; the new chair offers neither Release nor LiveOps (a host that says `waits`), and with only those left there is no chair."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_chair_deal_browser import ChairHost, press_chair  # noqa: E402
from tests.test_hand_desktop_browser import RoadHost, open_hand  # noqa: E402

pytestmark = pytest.mark.browser


class SeatedRelease(ChairHost, RoadHost):
    """The road's host (Release and Live seated) whose chair still has LiveOps and Release (waiting) and Art to offer."""


def test_a_seated_release_has_no_tab_and_no_checks_pane_and_the_chair_offers_neither_release_nor_liveops(gui):
    pg, host, log = open_hand(gui, host=SeatedRelease(pick=False))
    try:
        pg.locator('.table-tab[data-tab="tech"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.table-tab[data-tab="release"]').count() == 0, "a Release seated keeps its page and has no tab"
        assert any(p["slug"] == "release" for p in host.parties), "the party is still on the Board"
        assert pg.locator("[data-checks], .table-checks").count() == 0, "its checks are off"
        press_chair(pg)
        assert [c.get_attribute("data-craft") for c in pg.locator(".hand-crafts .hand-craft").all()] == ["marketing", "art"]
        assert not log, log
    finally:
        pg.close()


def test_with_only_waiting_crafts_left_there_is_no_chair(gui):
    host = SeatedRelease()
    host.presets = [p for p in host.presets if p["id"] in ("liveops", "release")]
    pg, host, log = open_hand(gui, host=host)
    try:
        pg.locator('.table-tab[data-tab="tech"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert pg.locator(".table-chair").count() == 0, "nothing to offer, no chair"
        assert not log, log
    finally:
        pg.close()
