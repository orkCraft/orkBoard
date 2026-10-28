"""Spec 99 A (docs/specs/99-a-goals-way.md §1.2, decisions §122.5, §137.1, §151.7): the project's stage (kept in `<state_dir>/project.json`, read from the project when unset), the crafts each
stage offers, Release in every project at every stage (locked, Lean, its leader alone), the commands `ideas.stage` and `ideas.stage_set`. Code, no model."""
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


def test_the_stage_the_person_set_wins_over_the_one_read(tmp_path):
    root, state = tmp_path / "p", tmp_path / "state"
    root.mkdir()
    (root / "main.py").write_text("x", encoding="utf-8")
    assert project_stage.current(state, root) == {"stage": "being_made", "read": "being_made", "kept": False}
    project_stage.keep(state, "live")
    assert project_stage.current(state, root) == {"stage": "live", "read": "being_made", "kept": True}


def test_the_crafts_by_stage_idea_the_concepts_lean_being_made_adds_tech_standard_live_adds_running_and_marketing():
    app = {s: [c["id"] for c in project_stage.crafts("web", s)] for s in project_stage.STAGES}
    assert app == {"idea": ["product", "design", "release"], "being_made": ["product", "design", "tech", "release"],
                   "live": ["product", "design", "tech", "release", "run", "marketing"]}
    game = {s: [c["id"] for c in project_stage.crafts("game", s)] for s in project_stage.STAGES}
    assert game == {"idea": ["game-design", "art", "release"], "being_made": ["game-design", "tech", "art", "release"],
                    "live": ["game-design", "tech", "art", "release", "liveops", "marketing"]}
    cards = {c["id"]: c for c in project_stage.crafts("web", "live")}
    assert {i: (c["from"], c["size"]) for i, c in cards.items()} == {"product": ("idea", "lean"), "design": ("idea", "lean"), "tech": ("being_made", "standard"),
                                                                      "release": ("idea", "lean"), "run": ("live", "standard"), "marketing": ("live", "standard")}
    assert project_stage.offered("web") == {s: project_stage.crafts("web", s) for s in project_stage.STAGES}
    with pytest.raises(ValueError, match="idea, being_made or live"):
        project_stage.crafts("web", "late")


@pytest.mark.parametrize("kind", project_kind.KINDS)
def test_release_is_in_every_kind_at_every_stage_locked_lean_and_its_leader_alone_on_the_cheaper_tier(kind):
    for stage in project_stage.STAGES:
        [release] = [c for c in project_stage.crafts(kind, stage) if c["id"] == "release"]
        assert (release["locked"], release["size"], release["squad"], release["leader"]) == (True, "lean", [], "release-manager")
        assert release["tiers"] == {"release-manager": "warrior"}
        assert not any(c["locked"] for c in project_stage.crafts(kind, stage) if c["id"] != "release")
    assert project_stage.release_card()["id"] == "release" and project_stage.leader_tier() == "warrior"


def test_a_card_says_its_squad_the_tiers_of_its_proposed_size_and_the_roles_to_tick_from():
    tech = next(c for c in project_stage.crafts("code", "being_made") if c["id"] == "tech")
    assert tech["squad"] == ["grunt", "tester", "reviewer"] and tech["build"] == ["grunt", "tester"] and tech["check"] == ["reviewer", "security-reviewer"]
    assert tech["tiers"] == party_recipes.sized(party_recipes.get("tech"), "standard")["tiers"] == {"architect": "elder", "grunt": "warrior"}
    assert all(c["because"] and c["name"] and c["line"] for c in project_stage.crafts("code", "live"))
    assert set(idea_target.SIZES) >= {c["size"] for s in project_stage.STAGES for c in project_stage.crafts("code", s)}


# -- the commands ----------------------------------------------------------------------------------------------------------------------------------------------

def test_ideas_stage_answers_the_stage_the_one_read_and_what_each_stage_offers_and_writes_nothing(fake_repo):
    h = Orkboard(fake_repo)
    got = h.ideas.stage({})
    assert got["stage"] == got["read"] == "being_made" and got["kept"] is False and got["kind"] == "code"      # the fake repo has code and no deploy
    assert got["offered"] == project_stage.offered("code") and set(got["offered"]) == {"idea", "being_made", "live"}
    assert not (h.ideas.state_dir / "project.json").exists()
    json.dumps(got)


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
    assert ids("idea") == ["product", "design", "release"] and ids("being_made") == ["product", "design", "tech", "release"] and len(ids("live")) == 6 == len(ids(None))
    release = [p for p in orkmaster.proposals(h.ideas.root(), h.ideas.state_dir, {}, kind, None, [], stage="idea") if p["id"] == "release"][0]
    assert release["locked"] is True and release["squad"] == [] and release["sizes"]["full"]["heads"] == [{"race": "lich", "tier": "warrior"}]
    assert orkmaster.proposal_ids("web", None, [], stage="idea") == ["product", "design", "release"]
