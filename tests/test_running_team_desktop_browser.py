"""Spec 92 on the desktop, the recurring goals (docs/specs/92-running-and-the-team.md §2, decisions §108), in a real browser at 1 440 × 900 against New party's stub host (tests/test_new_party_91_desktop_browser.py): a project's running (LiveOps · Run · Upkeep) offers its recurring goals, ticked, and Save sends the ones kept. Its Team parts went with Operations off the desktop (spec 98 §1)."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_new_party_91_desktop_browser import PresetHost  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open, _parties  # noqa: E402

pytestmark = pytest.mark.browser



class TeamHost(PresetHost):
    """New party's host with Operations (`ops_rev`) and the person's Team party: `team` is the snapshot's `ops_team` (None: there is none), and a Team party saved here makes it."""

    def __init__(self, kind_id="mobile", team=None):
        super().__init__(kind_id=kind_id)
        self.ops = True
        self.team = team

    def snapshot(self):
        snap = super().snapshot()
        snap["state"]["ops_team"] = copy.deepcopy(self.team)
        return snap

    def map_doc(self):
        doc = super().map_doc()
        for g in doc["goals"]:
            g["ops"] = bool(self.team and self.team.get("here") and g["slug"] == self.team["party"])
        return doc

    def handle(self, name, a):
        if name == "ideas.party_presets":
            got = super().handle(name, a)
            if self.team:
                for r in got["presets"]:
                    if r["id"] == "team":
                        r["blocked"] = "Team is in this project" if self.team["here"] else f"Team is in {self.team['name']}"
            return got
        if name == "ideas.goal_save" and a.get("proposal") == "team":
            self.log.append((name, a))
            self.goals["team"] = self.goal("team", "Team", "normal", "ready", about="", leader=self.leader(a.get("leader")), team=[], every=[], craft="product")
            self.team = {"name": "shop", "party": "team", "here": True}
            return self.bump({"slug": "team"})
        if name == "ops.list":
            self.log.append((name, a))
            return {"templates": [], "runs": [], "settings": {}, "standing": [], "servers_needed": {}}
        return super().handle(name, a)


def _open_team(gui, **more):
    pg, host, errors = _open(gui, host=TeamHost(**more), ready=".arena[data-goal=passkey]")
    pg.set_default_timeout(WAIT_MS)
    return pg, host, errors


def _dialog(pg):
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator(".shell-preset").first.wait_for(timeout=WAIT_MS)
    return dlg


def test_a_mobile_projects_run_party_offers_its_recurring_goals_ticked_and_save_sends_the_ones_kept(gui):
    pg, host, errors = _open_team(gui)
    _new_party(pg)
    dlg = _dialog(pg)
    stage = dlg.get_by_role("region", name="By stage of the project").locator(".shell-preset")
    assert [(c.get_attribute("data-craft"), c.locator("b").text_content()) for c in stage.all()][-1] == ("mobile-liveops", "Run")
    assert dlg.locator(".shell-routines").count() == 0                                                                       # Build proposes none
    dlg.locator('.shell-preset[data-craft="mobile-liveops"]').click()
    assert dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Run"
    assert [s.get_attribute("data-seat") for s in dlg.locator('.shell-band[data-band="lead"] .shell-seat[data-seat]').all()] == ["product-manager"]
    box = dlg.get_by_role("region", name="Recurring goals")
    boxes = box.locator("input[type=checkbox]")
    assert [b.get_attribute("data-routine") for b in boxes.all()] == ["deps", "reviews", "crashes"]
    assert [" ".join(li.inner_text().split()) for li in box.locator("li").all()] == ["Weekly dependency check every week", "Read the new reviews every week", "Look at the crashes every week"]
    assert all(b.is_checked() for b in boxes.all())
    boxes.nth(2).uncheck()
    dlg.get_by_label("What it is for", exact=True).fill("Keep the app running")
    dlg.get_by_role("button", name="Save party").click()
    pg.wait_for_function("() => document.querySelectorAll('[role=dialog]').length === 0", timeout=WAIT_MS)
    saved = _calls(pg, host, "ideas.goal_save")[-1]
    assert saved["routines"] == ["deps", "reviews"] and saved["proposal"] == "mobile-liveops" and saved["leader"] == "product-manager"
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_wikis_party_is_upkeep_and_a_games_is_liveops_each_with_its_recurring_goals_and_another_press_ticks_afresh(gui):
    pg, host, errors = _open_team(gui, kind_id="wiki")
    _new_party(pg)
    dlg = _dialog(pg)
    last = dlg.get_by_role("region", name="By stage of the project").locator(".shell-preset").last
    assert (last.get_attribute("data-craft"), last.locator("b").text_content()) == ("wiki-liveops", "Upkeep")
    last.click()
    box = dlg.get_by_role("region", name="Recurring goals")
    assert [b.get_attribute("data-routine") for b in box.locator("input").all()] == ["stale", "links", "sources"]
    box.locator("input").first.uncheck()
    dlg.locator('.shell-preset[data-craft="wiki-build"]').click()
    assert dlg.locator(".shell-routines").count() == 0
    last.click()
    assert all(b.is_checked() for b in dlg.get_by_role("region", name="Recurring goals").locator("input").all())             # pressed again: all ticked
    pg.close()
    assert not errors, "\n".join(errors)
    gpg, ghost, gerrors = _open_team(gui, kind_id="game")
    _new_party(gpg)
    gdlg = _dialog(gpg)
    gdlg.get_by_role("region", name="By stage of the project").locator(".shell-preset").last.click()
    assert gdlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "LiveOps"
    assert [b.get_attribute("data-routine") for b in gdlg.get_by_role("region", name="Recurring goals").locator("input").all()] == ["numbers", "players", "crashes", "events"]
    gpg.close()
    assert not gerrors, "\n".join(gerrors)
