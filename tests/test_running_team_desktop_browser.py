"""Spec 92 on the desktop (docs/specs/92-running-and-the-team.md, decisions §108), in a real browser at 1 440 × 900 against New party's stub host (tests/test_new_party_91_desktop_browser.py): the left
column has an *Operations* row, with the line *Make it a Team party*, only while no Team party exists anywhere; a Team party made in a project takes the row away and its Board is today's Operations
list; Team is the last of *By craft* on every kind, greyed with *Team is in <project>* once the person has one; a project's running (LiveOps · Run · Upkeep) offers its recurring goals, ticked, and
Save sends the ones kept."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_new_party_91_desktop_browser import PresetHost  # noqa: E402
from tests.test_shell_browser import _calls, _new_party, _open, _parties  # noqa: E402

pytestmark = pytest.mark.browser

OPS_ROW = '.arena-phead[data-goal="@operations"]'


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


def test_operations_are_in_the_column_with_a_line_while_there_is_no_team_party_and_the_line_opens_new_party_on_team(gui):
    pg, host, errors = _open_team(gui)
    col = _parties(pg)
    assert col.locator(OPS_ROW).count() == 1 and col.locator(OPS_ROW).inner_text().strip() == "Operations"
    line = col.get_by_role("button", name="Make it a Team party")
    assert line.count() == 1
    line.click()
    dlg = _dialog(pg)
    assert dlg.locator(".shell-preset[aria-pressed=true]").get_attribute("data-craft") == "team"                           # New party opens on Team
    team = dlg.locator('.shell-preset[data-craft="team"]')
    assert team.locator("b").text_content() == "Team" and "your work with people" in team.get_attribute("title").lower() and team.is_enabled()
    crafts = dlg.get_by_role("region", name="By craft").locator(".shell-preset")
    assert [c.get_attribute("data-craft") for c in crafts.all()][-1] == "team"                                              # the last of By craft
    note = dlg.locator("[data-team=true]")
    assert "Team holds your Operations" in note.inner_text() and "stay yours" in note.inner_text()
    assert dlg.get_by_role("radiogroup", name="Size").count() == 0 and dlg.locator(".shell-seat").count() == 0 and dlg.locator(".shell-routines").count() == 0       # no seats to fill, nothing recurring
    assert dlg.locator('[data-foot="agents"]').inner_text() == "Your Operations stay yours: Team only shows them here"
    assert dlg.get_by_label("Name", exact=True).get_attribute("placeholder") == "Team"
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_team_party_made_here_takes_the_operations_row_away_and_its_board_is_the_operations_list(gui):
    pg, host, errors = _open_team(gui)
    _parties(pg).get_by_role("button", name="Make it a Team party").click()
    dlg = _dialog(pg)
    dlg.get_by_role("button", name="Save party").click()
    pg.wait_for_function("() => document.querySelectorAll('[role=dialog]').length === 0", timeout=WAIT_MS)
    saved = _calls(pg, host, "ideas.goal_save")[-1]
    assert saved["proposal"] == "team" and saved["leader"] == "product-manager" and saved["team"] == [] and "routines" not in saved
    col = _parties(pg)
    col.locator('.arena-phead[data-goal="team"]').wait_for(timeout=WAIT_MS)
    assert col.locator(OPS_ROW).count() == 0 and col.get_by_role("button", name="Make it a Team party").count() == 0       # no Operations row, no line
    pg.locator(".arena[data-team=true] .board-ops").wait_for(timeout=WAIT_MS)                                               # the Team party opens today's Operations list
    assert pg.locator(".arena[data-team=true] .board-ops h3").first.text_content().strip().startswith("Operations")
    head = col.locator('.arena-phead[data-goal="team"]')
    assert head.get_attribute("aria-current") == "true" and "leads" in head.inner_text() and head.locator(".arena-phead__count").count() == 0       # a party with no goals to count
    assert pg.locator(".arena-pbody, .arena-deck").count() == 0
    _new_party(pg)
    off = _dialog(pg).locator('.shell-preset[data-craft="team"]')                                                           # one Team party: its card is greyed
    assert off.is_disabled() and off.locator("[data-blocked]").inner_text() == "Team is in this project"
    pg.close()
    assert not errors, "\n".join(errors)


def test_with_a_team_party_in_another_project_there_is_no_operations_row_and_team_is_offered_greyed_with_where(gui):
    pg, host, errors = _open_team(gui, team={"name": "harbor", "party": "team", "here": False})
    col = _parties(pg)
    col.locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    assert col.locator(OPS_ROW).count() == 0 and col.get_by_role("button", name="Make it a Team party").count() == 0
    assert col.locator('.arena-phead[data-goal="team"]').count() == 0                                                       # it is in harbor, not here
    _new_party(pg)
    off = _dialog(pg).locator('.shell-preset[data-craft="team"]')
    assert off.is_disabled() and off.get_attribute("title") == "Team is in harbor" and off.locator("[data-blocked]").inner_text() == "Team is in harbor"
    off.click(force=True)
    assert _dialog(pg).locator(".shell-preset[aria-pressed=true]").get_attribute("data-craft") == "mobile-build"           # a press on it picks nothing
    pg.close()
    assert not errors, "\n".join(errors)


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
