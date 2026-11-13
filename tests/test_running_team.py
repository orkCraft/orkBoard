"""Spec 92 (docs/specs/92-running-and-the-team.md, decisions §108), the host's part, as spec 99 §1 changed it: running the project is the Run party (a game's LiveOps) with the recurring goals of its
kind it proposes when it is made; the Team party is not offered. Code, no model."""
from __future__ import annotations

import datetime as dt
import time

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, ideas, library, party_presets, party_recipes, party_recipes_before, project_kind, recurring

RUNNING = [(k, party_recipes.get(f"{k}-liveops")) for k in project_kind.KINDS if k != "empty"]


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.root = h.ideas.root()
    yield h
    h.close()


# -- the project's running, by the project's kind ------------------------------------------------------------------------------------------------------------------

def test_the_running_party_is_liveops_for_a_game_and_run_for_every_other_kind_and_proposes_its_kinds_recurring_goals():
    for kind in project_kind.KINDS:
        want = "liveops" if kind == "game" else "run"
        assert [r["id"] for r in party_recipes.for_kind(kind) if r["id"] in ("run", "liveops")] == [want]
        assert party_recipes.routines_of(want, kind) == (f"{kind}-liveops" if want == "run" else "game-liveops")
    assert party_recipes.get("run")["name"] == "Run" and party_recipes.get("liveops")["name"] == "LiveOps"
    for kind, recipe in RUNNING:                                                       # the recipes of before are found still, and their names too
        assert recipe["id"] == f"{kind}-liveops" and recipe["name"] == party_recipes_before.running_name(kind)
    assert {k: party_recipes_before.running_name(k) for k in project_kind.KINDS}["wiki"] == "Upkeep"


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


def test_the_presets_of_a_kind_carry_the_recurring_goals_of_its_running_party_and_team_is_no_row(host):
    rows = {r["id"]: r for r in party_presets.listed("wiki")}
    assert [r["id"] for r in rows["run"]["routines"]] == ["stale", "links", "sources"] and rows["run"]["name"] == "Run"        # a wiki's running: the recurring goals of wiki-liveops
    assert rows["tech"]["routines"] == [] and rows["product"]["routines"] == [] and rows["release"]["routines"] == []
    assert not any(r["id"] == "team" for k in project_kind.KINDS for r in party_presets.listed(k))             # Team is not offered on any kind (decisions §122.2)
    assert [r["id"] for r in party_presets.listed("game")[:6]][4] == "liveops" and party_presets.listed("game")[4]["routines"]


# -- recurring goals --------------------------------------------------------------------------------------------------------------------------------------------------------

def _idle(host, seconds=5.0):
    """The keeper has stopped drafting the goals just added (it has no model here and says so): what the test writes to their state is not written over."""
    end = time.monotonic() + seconds
    while time.monotonic() < end and any(host.ideas.keeper.busy(i["slug"]) for i in ideas.ideas(host.root)):
        time.sleep(0.02)
    time.sleep(0.05)


def _run_party(host, picked):
    run = next(r for r in party_presets.listed("code") if r["id"] == "run")
    full = run["sizes"]["standard"]
    slug = host.command("ideas.goal_save", {"title": "Run", "about": "", "leader": full["leader"], "team": full["team"], "every": [], "size": "standard", "proposal": run["id"], "routines": picked})["slug"]
    _idle(host)
    return slug


def test_the_recurring_goals_the_person_kept_are_added_to_the_new_party_with_their_repeat(host):
    slug = _run_party(host, ["deps", "builds"])
    mine = ideas.ideas(host.root, slug)
    assert sorted(i["title"] for i in mine) == ["Look at the failing builds", "Weekly dependency check"]
    assert {i["title"]: recurring.every_of(host.root, i["slug"]) for i in mine} == {"Look at the failing builds": "week", "Weekly dependency check": "week"}
    assert goal_team.recipe_of(host.root, slug) == "run"
    assert "dependencies" in ideas.idea_page(host.root, mine[0]["slug"]).section("Gist") or "dependencies" in ideas.idea_page(host.root, mine[1]["slug"]).section("Gist")


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
