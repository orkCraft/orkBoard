"""Spec 99 A (docs/specs/99-a-goals-way.md §1.2, decisions §122.5, §137.1, §151.7): the project's stage (kept in `<state_dir>/project.json`, read from the project when unset), the crafts each
stage offers, Release offered at every stage (a craft as any, not locked, Lean, its leader alone), the commands `ideas.stage` and `ideas.stage_set`. Code, no model."""
from __future__ import annotations

import json

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_party import stage_commands
from orkboard.realm import idea_target, party_recipes, project_kind, project_stage


def test_a_stage_is_kept_in_project_json_and_read_back_and_a_stage_that_is_none_is_refused(tmp_path):
    assert project_stage.kept(tmp_path) == ""
    (tmp_path / "project.json").write_text(json.dumps({"other": 1}), encoding="utf-8")
    assert project_stage.keep(tmp_path, "live") == "live" and project_stage.kept(tmp_path) == "live"
    assert json.loads((tmp_path / "project.json").read_text(encoding="utf-8")) == {"other": 1, "stage": "live"}      # the file's other keys stay
    with pytest.raises(ValueError, match="idea, being_made or live"):
        project_stage.keep(tmp_path, "done")
    (tmp_path / "project.json").write_text("not json", encoding="utf-8")
    assert project_stage.kept(tmp_path) == ""
    (tmp_path / "project.json").write_text(json.dumps({"stage": "nonsense"}), encoding="utf-8")
    assert project_stage.kept(tmp_path) == ""


def test_the_stage_read_from_the_project_no_code_is_idea_code_alone_being_made_a_store_page_or_a_deploy_live(tmp_path):
    def project(name, *files):
        root = tmp_path / name
        root.mkdir()
        for f in files:
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            (root / f).write_text("x", encoding="utf-8")
        return root
    assert project_stage.read(project("empty")) == "idea"
    assert project_stage.read(project("docs", "README.md", "docs/plan.md")) == "idea"                       # words, no code
    assert project_stage.read(project("code", "main.py", "util.py")) == "being_made"
    assert project_stage.read(project("store", "main.py", "fastlane/metadata/en-US/name.txt")) == "live"     # a store page
    assert project_stage.read(project("deploy", "main.py", "fly.toml")) == "live"
    assert project_stage.read(project("flow", "main.py", ".github/workflows/deploy-prod.yml")) == "live"
    assert project_stage.read(project("ci", "main.py", ".github/workflows/tests.yml")) == "being_made"        # a test workflow is no deploy


@pytest.mark.parametrize("kind", project_kind.KINDS)
def test_release_and_live_wait_no_chair_offers_them_but_release_s_card_stays_lean_with_its_engineer_and_notes_and_its_leader_on_the_cheaper_tier(kind):
    release = project_stage.card(party_recipes.CRAFTS[party_recipes.RELEASE])      # §283.29: a Release already seated is read by its card
    assert (release["locked"], release["size"], release["squad"], release["leader"]) == (False, "lean", ["release-engineer", "release-notes"], "release-manager")
    assert release["tiers"] == {"release-manager": "warrior", "release-engineer": "warrior", "release-notes": "warrior"}
    for stage in project_stage.STAGES:
        ids = {c["id"] for c in project_stage.crafts(kind, stage)}
        assert not ids & {"release", "run", "liveops"}
        assert not any(c["locked"] for c in project_stage.crafts(kind, stage))
    assert release["id"] == "release"


# -- the commands ----------------------------------------------------------------------------------------------------------------------------------------------


def test_ideas_stage_set_keeps_the_stage_answers_it_and_refuses_one_that_is_none(fake_repo):
    h = Orkboard(fake_repo)
    got = h.ideas.stage_set({"stage": "live"})
    assert got["stage"] == "live" and got["read"] == "being_made" and got["kept"] is True
    assert project_stage.kept(h.ideas.state_dir) == "live" and h.ideas.stage({})["stage"] == "live"
    with pytest.raises(Exception, match="idea, being_made or live"):
        h.ideas.stage_set({"stage": "done"})
    with pytest.raises(Exception, match="stage is missing"):
        h.ideas.stage_set({})
    assert project_stage.kept(h.ideas.state_dir) == "live"
    assert set(stage_commands(h.ideas)) == {"ideas.stage", "ideas.stage_set"}


def test_the_proposals_take_the_stage_and_offer_only_the_crafts_of_the_stages_reached(fake_repo):
    from orkboard.realm import orkmaster
    h = Orkboard(fake_repo)
    kind = {"id": "web", "words": "a web app", "signs": []}
    ids = lambda stage: [p["id"] for p in orkmaster.proposals(h.ideas.root(), h.ideas.state_dir, {}, kind, None, [], stage=stage)]
    assert ids("idea") == ["product", "design"] and ids("being_made") == ["product", "design", "tech"] and ids("live") == ["product", "design", "tech", "marketing"] and len(ids(None)) == 6     # Release and Run wait (§283.29)
    release = [p for p in orkmaster.proposals(h.ideas.root(), h.ideas.state_dir, {}, kind, None, [], stage=None) if p["id"] == "release"][0]
    assert release["locked"] is False and release["squad"] == ["release-engineer", "release-notes"] and release["sizes"]["full"]["heads"] == [{"race": "lich", "tier": "warrior"}, {"race": "skeleton", "tier": "warrior"}, {"race": "skeleton", "tier": "warrior"}]


