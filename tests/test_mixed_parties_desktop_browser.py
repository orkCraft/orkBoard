"""Spec 59 B on the desktop (docs/specs/59-mixed-parties.md §6, Tests → B), in the dialog of spec 91 §7: New party's presets (a host that reads no project has the library's: Ideation and Release, the crafts, the
Taskmaster alone; a pick fills the seats and sends `preset`, a seat changed clears it), the seats and the stage words by the leader (a Game designer's Concept, Build, Playtest; a seat a stage, so no second member:
no free seat; a party made before is shown over its seats in the alert colour), and the board's stage words from the party's `stages` (today's from an older host that sends none)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import party_presets  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost, solo_lead  # noqa: E402
from tests.test_shell_browser import StubHost, _calls, _new_party, _open, _show_goal  # noqa: E402

pytestmark = pytest.mark.browser

GAME_STAGES = {"lead": {"word": "Concept"}, "build": {"word": "Build", "seats": 1}, "check": {"word": "Playtest", "seats": 1}}


class GameHost(StubHost):
    """The stub of a game's project: `ideas.party_presets` answers a game's stages (the Game designer's Concept, Build and LiveOps)."""

    def handle(self, name, a):
        if name == "ideas.party_presets":
            self.log.append((name, a))
            return {"kind": {"id": "game", "words": "a game"}, "presets": party_presets.listed("game")}
        return super().handle(name, a)


@pytest.fixture
def party(gui):
    pg, host, errors = _open(gui, host=StubHost())
    _show_goal(pg)
    _new_party(pg)
    yield pg, host, pg.get_by_role("dialog", name="New party")
    pg.close()
    assert not errors, "\n".join(errors)


def _in(dlg, band):
    return [e.get_attribute("data-seat") for e in dlg.locator(f'.shell-band[data-band="{band}"] .shell-seat[data-seat]').all()]


def test_the_library_lists_the_stages_then_the_crafts_then_the_taskmaster_alone(party):
    pg, host, dlg = party
    assert [h.text_content() for h in dlg.locator(".shell-presets h3").all()] == ["By stage of the project", "By craft", "Your own party"]
    assert [t.get_attribute("data-craft") for t in dlg.locator(".shell-craft-tile").all()] == ["ideation", "release", "engineering", "design", "data", "marketing", "product", "art", "mixed"]
    ideation = dlg.locator('.shell-craft-tile[data-craft="ideation"]')
    assert "Ideation" in ideation.text_content() and "Small pitches: invest, reshape or pass, and why" in ideation.inner_text()
    assert ideation.locator(".ork-race__head").count() == 1                                                     # the leader's head
    assert dlg.locator('.shell-craft-tile[data-craft="engineering"]').get_attribute("aria-pressed") == "true"        # the party it starts from


def test_a_pick_fills_the_seats_and_is_sent_as_the_preset_until_a_seat_changes(party):
    pg, host, dlg = party
    dlg.locator('.shell-craft-tile[data-craft="release"]').click()
    assert dlg.locator('.shell-craft-tile[data-craft="release"]').get_attribute("aria-pressed") == "true"
    assert (_in(dlg, "lead"), _in(dlg, "build"), _in(dlg, "check")) == (["release-manager"], ["release-engineer"], ["release-checker"])
    dlg.get_by_label("Name", exact=True).fill("Our versions")
    dlg.get_by_role("button", name="Save party").click()
    got = _calls(pg, host, "ideas.goal_save")[0]
    assert got["preset"] == "release" and got["leader"] == "release-manager" and got["team"] == ["release-engineer", "release-checker"]


def test_a_seat_changed_afterwards_clears_the_preset(party):
    pg, host, dlg = party
    dlg.locator('.shell-craft-tile[data-craft="design"]').click()
    dlg.get_by_role("button", name="Remove Design system designer from the party").click()
    assert all(t.get_attribute("aria-pressed") == "false" for t in dlg.locator(".shell-craft-tile").all())
    dlg.get_by_label("Name", exact=True).fill("Pages")
    dlg.get_by_role("button", name="Save party").click()
    assert "preset" not in _calls(pg, host, "ideas.goal_save")[0]


def test_a_game_has_one_builder_seat_and_the_stage_words_of_its_leader(gui):
    pg, host, errors = _open(gui, host=GameHost())
    _show_goal(pg)
    _new_party(pg)
    dlg = pg.get_by_role("dialog", name="New party")
    dlg.locator('.shell-craft-tile[data-craft="game-build"]').click()
    leads, builds, checks = (dlg.get_by_role("region", name=n) for n in ("Leads", "Does", "Checks"))
    assert [b.get_attribute("data-stage") for b in (leads, builds, checks)] == ["Concept", "Build", "Playtest"]            # the leader's stages, their words
    assert "1 of 1 seats" in builds.inner_text() and "1 of 1 seats" in checks.inner_text()
    assert builds.locator(".shell-team-seat").count() == 1 and checks.locator(".shell-team-seat").count() == 1
    assert dlg.locator('[data-free="build"]').count() == 0 and dlg.locator('[data-free="check"]').count() == 0          # a seat a stage: a second member has no seat
    dlg.locator('.shell-craft-tile[data-craft="engineering"]').click()                            # another leader: today's words and seats
    assert [b.get_attribute("data-stage") for b in (leads, builds, checks)] == ["Planning", "Implementation", "Checking"]
    assert builds.locator(".shell-team-seat").count() == 1 and checks.locator(".shell-team-seat").count() == 1                 # a seat a stage with every leader (spec 87 §5)
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_party_made_before_with_more_than_a_seat_a_stage_shows_the_extra_members_in_the_alert_colour_and_is_still_saved(gui):
    pg, host, errors = _open(gui, host=StubHost())
    _show_goal(pg)
    host.goals["ship-sync"].update(about="Sync between devices.", craft="engineering", leader=host.leader("architect"), team=["grunt", "tester", "reviewer"], every=[])      # made when a party had three builders
    host.bump({})
    pg.locator(".arena-phead__leads", has_text="Architect").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    builds = dlg.get_by_role("region", name="Does")
    builds.wait_for(timeout=WAIT_MS)
    assert builds.get_by_role("alert").inner_text() == "Implementation has 1 seat with Architect: take one out first."
    assert builds.locator(".shell-team-seat.is-over").count() == 1 and builds.locator(".shell-team-seat").count() == 2          # (two builders, one seat; the Reviewer is a checker)
    assert builds.locator(".shell-team-seat.is-over").first.evaluate("e => getComputedStyle(e).borderTopColor") != builds.locator(".shell-team-seat:not(.is-over)").first.evaluate("e => getComputedStyle(e).borderTopColor")
    assert "2 of 1 seats" in builds.inner_text() and builds.locator("[data-free]").count() == 0
    save = dlg.get_by_role("button", name="Save party")
    assert save.is_enabled()                                                                      # a party made before keeps its team: Edit the party saves it as it is
    dlg.get_by_label("What it is for").fill("Sync, kept.")
    save.click()
    pg.wait_for_function("() => document.querySelectorAll('[role=dialog]').length === 0", timeout=WAIT_MS)
    got = _calls(pg, host, "ideas.goal_save")[-1]
    assert got["slug"] == "ship-sync" and got.get("team", ["grunt", "tester", "reviewer"]) == ["grunt", "tester", "reviewer"]
    pg.close()
    assert not errors, "\n".join(errors)


def test_new_party_takes_the_first_builder_and_the_first_checker_of_a_preset_and_one_seat_is_not_overfull(party):
    pg, host, dlg = party
    dlg.locator('.shell-craft-tile[data-craft="release"]').click()
    assert _in(dlg, "build") == ["release-engineer"] and _in(dlg, "check") == ["release-checker"]
    dlg.locator('.shell-craft-tile[data-craft="ideation"]').click()
    assert len(_in(dlg, "build")) == 4 and len(_in(dlg, "check")) == 1                             # Ideation is its four views and the Skeptic whole
    assert dlg.get_by_role("region", name="Does").get_by_role("alert").count() == 0 and dlg.locator(".shell-team-seat.is-over").count() == 0
    dlg.get_by_label("Name", exact=True).fill("Pitches")
    assert dlg.get_by_role("button", name="Save party").is_enabled()


class StagesHost(ArenaHost):
    """The map of a host that sends `stages` for the party shown (a Game designer's) and none for the other."""

    def map_doc(self):
        got = super().map_doc()
        for g in got["goals"]:
            if g["slug"] == "passkey":
                g["stages"] = GAME_STAGES
        return got


def _labels(pg):
    return [h.text_content() for h in pg.locator(".arena-cols__head .arena-lbl:not(.is-blank)").all()]


def test_the_board_says_the_stage_words_of_the_party_and_todays_without_stages(gui):
    pg, host, errors = _open(gui, host=StagesHost(), ready=".arena-phead")
    try:
        pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
        assert _labels(pg) == ["Build", "Playtest"]                                               # over the first builder, the first checker
        assert pg.locator(".arena-cols__head .arena-lbl", has_text="Build").get_attribute("title") == "1 seat"
        solo_lead(pg)                                                                             # the leader alone: its stage
        pg.locator(".arena-solo-wrap").wait_for(timeout=WAIT_MS)
        assert "Planning" not in pg.locator(".arena-solo-wrap").inner_text()
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
    pg, host, errors = _open(gui, host=ArenaHost(), ready=".arena-phead")                          # an older host: no `stages`
    try:
        pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
        assert _labels(pg) == ["Implementation", "Checking"]
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
