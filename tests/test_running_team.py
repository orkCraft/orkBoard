"""Spec 92 (docs/specs/92-running-and-the-team.md, decisions §108), the host's part: running the project is a stage party by the project's kind (LiveOps · Run · Upkeep) with recurring goals
it proposes when it is made, and working with people is one Team party, in one project of the person's choosing, whose Board is their Operations. Code, no model."""
from __future__ import annotations

import datetime as dt
import time

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, ideas, library, ops_team, party_presets, party_recipes, pitches, project_kind, recurring
from orkboard.realm import op_runs

RUNNING = [(k, party_recipes.get(f"{k}-liveops")) for k in project_kind.KINDS if k != "empty"]


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.root = h.ideas.root()
    yield h
    h.close()


def _team(host, **more):
    team = party_presets.listed("code")[-2]
    assert team["id"] == "team"
    return host.command("ideas.goal_save", {"title": "Team", "about": "", "leader": team["leader"], "team": [], "every": [], "size": "standard", "proposal": "team", **more})["slug"]


# -- the project's running, by the project's kind ------------------------------------------------------------------------------------------------------------------

def test_the_fifth_stage_is_liveops_for_a_game_upkeep_for_words_and_files_and_run_for_the_rest():
    assert {k: party_recipes.running_name(k) for k in project_kind.KINDS} == {"game": "LiveOps", "wiki": "Upkeep", "design": "Upkeep", "texts": "Upkeep", "mobile": "Run", "web": "Run",
                                                                              "backend": "Run", "code": "Run", "data": "Run", "empty": "Run"}
    for kind, recipe in RUNNING:
        assert recipe["id"] == f"{kind}-liveops" and recipe["name"] == party_recipes.running_name(kind)
        assert party_recipes.stages_of(kind)[4]["id"] == recipe["id"]
    assert party_recipes.stages_of("empty")[4]["name"] == "Run" and party_recipes.stages_of("nowhere")[4]["id"] == "code-liveops"


@pytest.mark.parametrize("kind,recipe", RUNNING, ids=[f"{k}-liveops" for k, _r in RUNNING])
def test_a_running_party_is_led_and_staffed_by_library_roles_and_proposes_two_to_four_recurring_goals(kind, recipe):
    assert library.get(recipe["leader"]).band == "lead"
    assert recipe["build"] and recipe["check"]
    if kind in ("mobile", "web", "backend", "code"):                                  # Run: monitoring, incidents, dependencies, the store's reviews; the Grunt and the Tester do, the Reviewer checks
        assert recipe["leader"] in ("architect", "product-manager") and {"grunt", "tester"} <= set(recipe["build"]) and "reviewer" in recipe["check"]
    if kind in ("wiki", "texts"):                                                      # Upkeep: the Copywriter does, the Editor checks
        assert "copywriter" in recipe["build"] and recipe["check"] == ["editor"]
    rows = recurring.listed(recipe["id"])
    assert 2 <= len(rows) <= 4, kind
    assert len({r["id"] for r in rows}) == len(rows)
    for r in rows:
        got = recurring.get(recipe["id"], r["id"])
        assert r["every"] in recurring.EVERY and r["words"] == recurring.WORDS[r["every"]] and r["title"] and len(got["text"]) > 40
        text = (r["title"] + got["text"]).lower()
        assert "orc " not in text and "orchestration" not in text                      # house wording
    assert set(recurring.ROUTINES) == {f"{k}-liveops" for k, _r in RUNNING}


def test_the_recurring_goals_the_brief_names_are_proposed_where_they_fit():
    titles = {k: [r["title"] for r in recurring.listed(f"{k}-liveops")] for k, _r in RUNNING}
    assert titles["mobile"][:2] == ["Weekly dependency check", "Read the new reviews"]
    assert titles["wiki"][:2] == ["Find stale pages", "Check the links"]
    assert titles["backend"][0] == titles["code"][0] == "Weekly dependency check"
    assert [r["every"] for r in recurring.listed("data-liveops")][0] == "day"          # a pipeline is checked every day


def test_the_presets_of_a_kind_carry_the_recurring_goals_of_its_running_stage_and_team_is_the_last_craft(host):
    rows = {r["id"]: r for r in party_presets.listed("wiki")}
    assert [r["id"] for r in rows["wiki-liveops"]["routines"]] == ["stale", "links", "sources"] and rows["wiki-liveops"]["name"] == "Upkeep"
    assert rows["wiki-build"]["routines"] == [] and rows["ideation"]["routines"] == [] and rows["engineering"]["routines"] == []
    team = rows["team"]
    assert (team["group"], team["name"], team["leader"], team["build"], team["check"], team["ops"], team["blocked"]) == ("craft", "Team", "product-manager", [], [], True, "")
    assert not any(r["ops"] for r in party_presets.listed("game") if r["id"] != "team")
    assert all(any(r["id"] == "team" for r in party_presets.listed(k)) for k in project_kind.KINDS)             # on every kind
    assert library.get(team["leader"]).craft == "product" and goal_team.seats([], team["leader"]) == ""


# -- the Team party: one, across the person's projects ------------------------------------------------------------------------------------------------------------------

def test_a_team_party_is_made_with_the_recipe_and_the_note_of_where_it_is_and_its_map_row_says_it_is_operations(host, fake_repo):
    assert host.snapshot()["ops_team"] is None
    slug = _team(host)
    assert goal_team.recipe_of(host.root, slug) == "team" and goal_team.leader_of(host.root, slug) == "product-manager" and goal_team.team_of(host.root, slug) == []
    note = ops_team.get(op_runs.root())
    assert note == {"project": str(fake_repo), "name": fake_repo.name, "party": slug}
    assert host.snapshot()["ops_team"] == {"name": fake_repo.name, "party": slug, "here": True}
    assert host.phone_snapshot()["ops_team"] == {"name": fake_repo.name, "party": slug, "here": True}
    goals = {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}
    assert goals[slug]["ops"] is True


def test_the_team_party_is_not_read_by_the_keeper_and_has_no_goals_of_its_own(host):
    slug = _team(host)
    assert host.ideas.goal_state(slug)["state"] == "raw"
    assert ideas.ideas(host.root, slug) == []


def test_a_second_team_party_is_refused_and_the_preset_is_offered_greyed(host):
    _team(host)
    with pytest.raises(Exception, match="Team is in this project"):
        _team(host)
    row = next(r for r in host.command("ideas.party_presets", {})["presets"] if r["id"] == "team")
    assert row["blocked"] == "Team is in this project"
    assert host.command("ideas.team", {}) == {"at": "here", "party": next(t["slug"] for t in ideas.tracks(host.root, make=False) if t["slug"] != "general"), "name": host.repo_root.name}


def test_team_in_another_project_is_offered_greyed_there_and_refused(host, tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    ops_team.set(op_runs.root(), other, "elsewhere", "team")
    assert host.snapshot()["ops_team"] == {"name": "elsewhere", "party": "team", "here": False}
    row = next(r for r in host.command("ideas.party_presets", {})["presets"] if r["id"] == "team")
    assert row["blocked"] == "Team is in elsewhere"
    with pytest.raises(Exception, match="Team is in elsewhere"):
        _team(host)
    assert not [t for t in ideas.tracks(host.root, make=False) if t["slug"] != "general"]          # nothing was made


def test_removing_the_team_party_gives_operations_back_and_a_note_about_a_gone_project_reads_as_none(host, tmp_path):
    slug = _team(host)
    host.command("ideas.track_drop", {"slug": slug})
    assert ops_team.get(op_runs.root()) is None and host.snapshot()["ops_team"] is None
    assert next(r for r in host.command("ideas.party_presets", {})["presets"] if r["id"] == "team")["blocked"] == ""
    gone = tmp_path / "gone"
    gone.mkdir()
    ops_team.set(op_runs.root(), gone, "gone", "team")
    gone.rmdir()
    assert ops_team.get(op_runs.root()) is None and ops_team.where(op_runs.root(), host.repo_root) == ""


def test_removing_another_party_leaves_the_note_alone(host):
    slug = _team(host)
    other = host.command("ideas.goal_save", {"title": "Tech", "about": "Code.", "leader": "architect", "team": [], "every": []})["slug"]
    host.command("ideas.track_drop", {"slug": other})
    assert ops_team.get(op_runs.root())["party"] == slug


def test_operations_stay_the_persons_whatever_the_team_party_does(host):
    before = host.command("ops.list", {})
    _team(host)
    after = host.command("ops.list", {})
    assert [t["name"] for t in after["templates"]] == [t["name"] for t in before["templates"]] and after["runs"] == before["runs"]
    assert str(op_runs.root()).endswith("ops") and not (host.repo_root / ".orkcraft" / "ops").exists()          # still the person's folder, never the repository's


# -- recurring goals --------------------------------------------------------------------------------------------------------------------------------------------------------

def _idle(host, seconds=5.0):
    """The keeper has stopped drafting the goals just added (it has no model here and says so): what the test writes to their state is not written over."""
    end = time.monotonic() + seconds
    while time.monotonic() < end and any(host.ideas.keeper.busy(i["slug"]) for i in ideas.ideas(host.root)):
        time.sleep(0.02)
    time.sleep(0.05)


def _run_party(host, picked):
    run = party_presets.listed("code")[4]
    assert run["id"] == "code-liveops"
    full = run["sizes"]["standard"]
    slug = host.command("ideas.goal_save", {"title": "Run", "about": "", "leader": full["leader"], "team": full["team"], "every": [], "size": "standard", "proposal": run["id"], "routines": picked})["slug"]
    _idle(host)
    return slug


def test_the_recurring_goals_the_person_kept_are_added_to_the_new_party_with_their_repeat(host):
    slug = _run_party(host, ["deps", "builds"])
    mine = ideas.ideas(host.root, slug)
    assert sorted(i["title"] for i in mine) == ["Look at the failing builds", "Weekly dependency check"]
    assert {i["title"]: recurring.every_of(host.root, i["slug"]) for i in mine} == {"Look at the failing builds": "week", "Weekly dependency check": "week"}
    assert goal_team.recipe_of(host.root, slug) == "code-liveops"
    assert "dependencies" in ideas.idea_page(host.root, mine[0]["slug"]).section("Gist") or "dependencies" in ideas.idea_page(host.root, mine[1]["slug"]).section("Gist")


def test_a_party_with_no_routines_picked_has_no_goals_and_an_unknown_one_is_refused_before_anything_is_made(host):
    assert ideas.ideas(host.root, _run_party(host, [])) == []
    with pytest.raises(Exception, match="No recurring goal nope"):
        _run_party(host, ["nope"])
    assert len([t for t in ideas.tracks(host.root, make=False) if t["slug"] != "general"]) == 1


def test_a_goal_that_is_done_comes_back_after_its_period_with_the_same_words_and_the_repeat_moves_to_it(host):
    slug = _run_party(host, ["deps"])
    first = ideas.ideas(host.root, slug)[0]["slug"]
    now = dt.datetime(2026, 10, 26, 9, 0)
    assert recurring.due(host.root, host.ideas.state_dir, now) == []                              # not done: nothing is due, nothing is stamped
    ideas.save_state(host.ideas.state_dir, first, state="done")
    assert recurring.due(host.root, host.ideas.state_dir, now) == []                              # first seen done: the day is kept
    assert recurring.due(host.root, host.ideas.state_dir, now + dt.timedelta(days=6)) == []
    assert recurring.due(host.root, host.ideas.state_dir, now + dt.timedelta(days=7)) == [first]
    again = host.ideas.routines_renew(first)
    assert again and again != first
    _idle(host)
    assert recurring.every_of(host.root, first) == "" and recurring.every_of(host.root, again) == "week"
    page = ideas.idea_page(host.root, again)
    assert page.get("track") == slug and page.title == "Weekly dependency check" and "dependencies" in page.section("Gist")
    assert recurring.words_of(host.root, again) == recurring.text_of(recurring.get("code-liveops", "deps"))        # the next round is written from the first words, not a drafted spec
    assert recurring.due(host.root, host.ideas.state_dir, now + dt.timedelta(days=30)) == []     # the new one is not done


def test_a_goal_reopened_forgets_the_day_it_was_done(host):
    slug = _run_party(host, ["deps"])
    first = ideas.ideas(host.root, slug)[0]["slug"]
    now = dt.datetime(2026, 10, 26, 9, 0)
    ideas.save_state(host.ideas.state_dir, first, state="done")
    recurring.due(host.root, host.ideas.state_dir, now)
    ideas.save_state(host.ideas.state_dir, first, state="working")
    recurring.due(host.root, host.ideas.state_dir, now + dt.timedelta(days=2))
    ideas.save_state(host.ideas.state_dir, first, state="done")
    assert recurring.due(host.root, host.ideas.state_dir, now + dt.timedelta(days=8)) == []        # the week counts from the second time it was done


def test_the_hosts_clock_renews_a_due_goal_at_most_once_a_minute_and_a_party_that_is_gone_ends_the_repeat(host):
    slug = _run_party(host, ["deps"])
    first = ideas.ideas(host.root, slug)[0]["slug"]
    ideas.save_state(host.ideas.state_dir, first, state="done")
    ideas.set_meta(host.root, first, repeat_from=(dt.datetime.now() - dt.timedelta(days=8)).isoformat(timespec="seconds"))
    host.ideas.routines_tick(1000.0)
    assert len(ideas.ideas(host.root, slug)) == 2 and recurring.every_of(host.root, first) == ""
    _idle(host)
    new = next(i["slug"] for i in ideas.ideas(host.root, slug) if i["slug"] != first)
    ideas.save_state(host.ideas.state_dir, new, state="done")
    ideas.set_meta(host.root, new, repeat_from=(dt.datetime.now() - dt.timedelta(days=8)).isoformat(timespec="seconds"))
    host.ideas.routines_tick(1030.0)                                                            # under a minute later: it waits
    assert len(ideas.ideas(host.root, slug)) == 2
    ideas.drop_track(host.root, slug, "move", host.ideas.state_dir, set())                      # the party goes; its goals move to General
    ideas.save_state(host.ideas.state_dir, new, state="done")
    ideas.set_meta(host.root, new, repeat_from=(dt.datetime.now() - dt.timedelta(days=8)).isoformat(timespec="seconds"))
    host.ideas.routines_tick(1100.0)
    assert recurring.every_of(host.root, new) == "" and len(ideas.ideas(host.root)) == 2


def test_a_repeat_is_set_and_stopped_by_the_person(host):
    slug = _run_party(host, [])
    got = host.command("ideas.add", {"text": "Read the logs", "track": slug})["slug"]
    assert host.command("ideas.repeat", {"slug": got, "every": "month"}) == {"ok": True, "every": "month"}
    assert recurring.every_of(host.root, got) == "month"
    assert host.command("ideas.page", {"slug": got})["repeat"] == "month"                    # the goal's drawer says it comes back, with a way to stop it
    assert host.command("ideas.repeat", {"slug": got, "every": ""})["every"] == "" and host.command("ideas.page", {"slug": got})["repeat"] == ""
    with pytest.raises(Exception, match="day, week or month"):
        host.command("ideas.repeat", {"slug": got, "every": "hour"})
    with pytest.raises(Exception, match="gone"):
        host.command("ideas.repeat", {"slug": "nothing", "every": "week"})


# -- the Team party holds Operations, not goals; a note that lost its party; a host with no Operations -----------------------------------------------------------------------------

def test_no_goal_goes_to_the_team_party_not_by_add_not_by_move_and_no_pitch_is_offered_it(host):
    slug = _team(host)
    other = host.command("ideas.goal_save", {"title": "Tech", "about": "Code.", "leader": "architect", "team": [], "every": []})["slug"]
    with pytest.raises(Exception, match="Team holds your Operations"):
        host.command("ideas.add", {"text": "Call the bank", "track": slug})
    goal = host.command("ideas.add", {"text": "Fix the login", "track": other})["slug"]
    with pytest.raises(Exception, match="Team holds your Operations"):
        host.command("ideas.move", {"slug": goal, "track": slug})
    offers = pitches.offers(host.root, host.ideas.state_dir)
    assert slug not in offers and other in offers


def test_a_team_party_removed_by_hand_gives_operations_back_but_a_board_still_being_made_keeps_the_note(host):
    slug = _team(host)
    other = host.command("ideas.goal_save", {"title": "Tech", "about": "Code.", "leader": "architect", "team": [], "every": []})["slug"]
    assert host.snapshot()["ops_team"]["party"] == slug
    (host.root / ideas.TRACKS / f"{slug}.md").unlink()
    assert host.snapshot()["ops_team"] is None and ops_team.get(op_runs.root()) is None
    assert other in {t["slug"] for t in ideas.tracks(host.root, make=False)}
    ops_team.set(op_runs.root(), host.repo_root, host.repo_root.name, "team")                     # a note about a party that was never here...
    (host.root / ideas.TRACKS / f"{other}.md").unlink()
    assert host.snapshot()["ops_team"] is not None                                              # ...while the Board has no party at all: left alone


def test_a_host_with_no_operations_is_not_offered_team(host):
    assert any(r["id"] == "team" for r in party_presets.listed("code"))
    assert not any(r["id"] == "team" for r in party_presets.listed("code", ops=False))
    ops, host.ops = host.ops, None                                                                # Orkline's page has none
    try:
        assert host.ideas.team_at() == "" and not any(r["id"] == "team" for r in host.command("ideas.party_presets", {})["presets"])
    finally:
        host.ops = ops
