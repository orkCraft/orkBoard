"""Spec 127 C.2–C.4 (docs/specs/127-the-fields-best-in-our-formats.md; decisions §205): the fold of a goal that reached main into the product's living specs (one call of the goal's party's leader, step
`fold`, no tools), its trigger where the flag is raised, the event `spec_folded`, the specs in Talk's and the sections' prompts, and the specs out as OpenSpec and in from OpenSpec and Kiro.
The model call is stubbed (`keeper.call`), as `tests/test_idea_journal.py` does.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from orkboard.core import idea_fold, idea_keeper
from orkboard.core.idea_fold import FoldMixin
from orkboard.gui.board_host import Orkboard
from orkboard.realm import (event_log, goal_team, idea_spend, idea_target, ideas, journals, library, living_specs, living_specs_io, read_in, spec_sections, write_out)

MAP = "THE MAP TEXT"
ANSWER = {"capability": "sign-in", "title": "Sign-in", "purpose": "How a player gets into a game.",
          "added": [{"name": "Magic link", "text": "The product SHALL send a link that signs the player in.",
                     "scenarios": [{"name": "A link is asked for", "when": "a player types their address and presses Send", "then": "a link arrives within a minute"}]}],
          "modified": [], "removed": []}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.keeper._map = lambda party: MAP
    assert isinstance(h.ideas.keeper, FoldMixin) and idea_keeper.FoldMixin is FoldMixin
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer", ["artist"], "design")


def _goal(host, party, text="add a magic link", done="- A player types an address and gets a link\n- The link signs them in", **more):
    slug = ideas.add_idea(host.ideas.root(), text, party, host.ideas.state_dir, "normal", "hold")
    root = host.ideas.root()
    for name, value in {"Why": "Players forget passwords.", "Done when": done, "Out": "- Social sign-in", **more}.items():
        if value:
            ideas.set_section(root, slug, name, value)
    return slug


@pytest.fixture
def goal(host, tech):
    return _goal(host, tech)


class Model:
    """The keeper's call stubbed: `answer` the JSON (or text, or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=ANSWER):
        self.host, self.calls, self.answer = host, [], answer
        host.ideas.keeper.call = self

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", "")})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        if isinstance(answer, Exception):
            raise answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy(f"goal:{party}"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _events(host):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == event_log.SPEC_FOLDED]


def _specs(host):
    return living_specs.list_(host.ideas.root())


# -- the call ----------------------------------------------------------------------------------------------------------------------------

def test_the_fold_is_one_call_of_the_goals_partys_leader_on_the_cheaper_tier_with_no_tools_and_no_file_read(host, tech, goal, model):
    assert host.ideas.keeper.fold(goal) is True
    _wait(host, tech)
    (call,) = model.calls
    assert call["step"] == "fold" and call["tools"] is False and call["key"] == f"goal:{tech}"
    assert (call["tier"], call["effort"]) == idea_target.pick("fold", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("fold", "balance")
    p = call["prompt"]
    assert p.startswith("You are Architect, the leader of this goal's party")                                       # its leader's voice
    assert "Read no file" in p and '"capability"' in p and "SHALL" in p
    assert "add a magic link" in p and "Players forget passwords." in p and "A player types an address and gets a link" in p and "Social sign-in" in p
    assert "The capabilities the product has, as specs:\n(none)" in p


def test_the_call_is_given_the_capabilities_the_product_has_and_the_sections_of_each_party(host, tech, design, model):
    living_specs.apply(host.ideas.root(), "lobby", {"added": [{"name": "Rooms", "text": "The product SHALL list rooms.", "scenarios": []}]}, "g", "tech", title="Lobby", purpose="Where players meet.")
    slug = _goal(host, tech, done="")
    page = ideas.idea_page(host.ideas.root(), slug)
    page.sections += [("Tech", spec_sections.join({"Why": "Tech's why.", "Done when": "- The link is one-time", "Will be": "changed src/auth — the link", "Out": "- Nothing else"})),
                      ("Design", spec_sections.join({"Why": "Design's why.", "Done when": "- The screen says where the link went"}))]
    ideas._write(host.ideas.root() / ideas.IDEAS / f"{slug}.md", page.text())
    host.ideas.keeper.fold(slug)
    _wait(host, tech)
    p = model.calls[0]["prompt"]
    assert "- lobby — Lobby: Where players meet. (requirements: Rooms)" in p
    assert "Tech's why." in p and "The link is one-time" in p and "changed src/auth — the link" in p and "The screen says where the link went" in p and "Design's why." in p


# -- what is kept ------------------------------------------------------------------------------------------------------------------------

def test_the_answer_is_cleaned_and_applied_and_the_event_has_no_word_of_it(host, tech, goal, model):
    assert host.ideas.keeper.fold(goal) is True
    _wait(host, tech)
    spec = living_specs.read(host.ideas.root(), "sign-in")
    assert (spec["title"], spec["purpose"], spec["parties"], spec["goals"]) == ("Sign-in", "How a player gets into a game.", [tech], [goal])
    assert spec["requirements"] == ANSWER["added"]
    assert (host.ideas.root() / "specs" / "sign-in.md").is_file()
    (ev,) = _events(host)
    assert (ev["idea"], ev["capability"], ev["added"], ev["modified"], ev["removed"], ev["cost"]) == (goal, "sign-in", 1, 0, 0, 0.01)
    assert "Magic link" not in json.dumps(ev) and "player" not in json.dumps(ev)
    assert event_log.SPEC_FOLDED in event_log.EVENTS and event_log.SPEC_FOLDED == "spec_folded"


def test_a_second_fold_modifies_and_removes_by_name(host, tech, goal, model):
    host.ideas.keeper.fold(goal)
    _wait(host, tech)
    again = _goal(host, tech, "drop the link")
    model.answer = {"capability": "sign-in", "added": [{"name": "Password", "text": "The product SHALL ask for a password."}],
                    "modified": [{"name": "magic link", "text": "The product SHALL send a one-time link.", "scenarios": [{"when": "a link is used twice", "then": "the second use is refused"}]}],
                    "removed": ["Nothing here"]}
    host.ideas.keeper.fold(again)
    _wait(host, tech)
    spec = living_specs.read(host.ideas.root(), "sign-in")
    assert [r["name"] for r in spec["requirements"]] == ["magic link", "Password"] and spec["goals"] == [goal, again] and spec["title"] == "Sign-in"
    assert spec["requirements"][0]["scenarios"] == [{"name": "a link is used twice", "when": "a link is used twice", "then": "the second use is refused"}]
    assert [(e["added"], e["modified"], e["removed"]) for e in _events(host)] == [(1, 0, 0), (1, 1, 1)]


def test_the_answer_is_cleaned_strictly():
    clean = idea_fold.clean
    assert clean("text") is None and clean([]) is None and clean(None) is None
    got = clean({"capability": " Sign In! ", "title": "Sign [in] #1", "purpose": "x " * 300,
                 "added": [{"name": "A", "text": "The product SHALL a.", "scenarios": [{"when": "w", "then": "t"}] * 6 + [{"when": "only when"}, "junk", {"then": "only then"}]},
                           {"name": "No text"}, {"text": "No name"}, "junk", {"name": "L" * 400, "text": "T" * 400}],
                 "modified": [{"name": "M", "text": "The product SHALL m."}], "removed": ["R", "R", 5, "  ", "S"]})
    assert got["capability"] == "sign-in" and got["title"] == "Sign in 1" and len(got["purpose"]) == 300
    assert [r["name"] for r in got["added"]] == ["A", "L" * 300] and len(got["added"][0]["scenarios"]) == 4 and got["added"][1]["text"] == "T" * 300
    assert got["added"][0]["scenarios"][0] == {"name": "w", "when": "w", "then": "t"}
    assert [r["name"] for r in got["modified"]] == ["M"] and got["removed"] == ["R", "S"]
    many = clean({"capability": "x", "added": [{"name": f"A{i}", "text": "t"} for i in range(6)], "modified": [{"name": f"M{i}", "text": "t"} for i in range(6)], "removed": [f"R{i}" for i in range(12)]})
    assert len(many["added"]) + len(many["modified"]) == 8 and len(many["added"]) == 6 and len(many["removed"]) == 8      # eight requirements in all, the added first
    assert clean({"capability": "", "added": [{"name": "A", "text": "t"}]}) is None and clean({"capability": 5, "removed": ["A"]}) is None       # requirements and no capability: no answer
    assert clean({"added": [], "modified": [], "removed": []}) == {"capability": "", "title": "", "purpose": "", "added": [], "modified": [], "removed": []}      # nothing to fold


def test_an_answer_with_nothing_to_fold_is_one_call_keeping_nothing(host, tech, goal, model):
    model.answer = {"capability": "sign-in", "added": [], "modified": [], "removed": []}
    assert host.ideas.keeper.fold(goal) is True
    _wait(host, tech)
    assert len(model.calls) == 1 and _specs(host) == [] and _events(host) == []


@pytest.mark.parametrize("answer", ["not json", {"capability": "", "added": [{"name": "A", "text": "t"}]}, ["x"], RuntimeError("the tool failed")])
def test_a_call_that_fails_keeps_nothing(host, tech, goal, model, answer):
    model.answer = answer
    assert host.ideas.keeper.fold(goal) is True
    _wait(host, tech)
    assert len(model.calls) == 2                                                          # asked once more
    assert _specs(host) == [] and _events(host) == [] and not (host.ideas.root() / "specs").exists()


def test_a_stop_and_a_disk_that_refuses_keep_nothing(host, tech, goal, model, monkeypatch):
    def stopped(call):
        host.ideas.keeper._tls.cancel.set()
        return ANSWER
    model.answer = stopped
    host.ideas.keeper.fold(goal)
    _wait(host, tech)
    assert _specs(host) == [] and _events(host) == []
    model.answer = ANSWER
    monkeypatch.setattr(living_specs, "write", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    host.ideas.keeper.fold(goal)
    _wait(host, tech)
    assert _specs(host) == [] and _events(host) == []


def test_a_goal_with_nothing_to_fold_is_not_called(host, tech, model):
    keeper = host.ideas.keeper
    assert keeper.fold(_goal(host, tech, done="")) is False                               # no Done when
    assert keeper.fold("no-such-goal") is False
    bare = ideas.add_idea(host.ideas.root(), "a goal of no party's page", tech, host.ideas.state_dir, "normal", "hold")
    ideas.set_meta(host.ideas.root(), bare, track="ghost")
    ideas.set_section(host.ideas.root(), bare, "Done when", "- It works")
    assert keeper.fold(bare) is False and model.calls == []


def test_nothing_is_begun_for_a_call_that_cannot_be_made_or_a_party_that_is_busy_never_an_error(host, tech, goal, model):
    keeper = host.ideas.keeper
    keeper.budget_ok = lambda: False                                          # today's spend limit: no call, no error
    assert keeper.fold(goal) is False and model.calls == []
    keeper.budget_ok = lambda: True
    keeper.demo = True
    assert keeper.fold(goal) is False and model.calls == []
    keeper.demo = False
    keeper.window_until = lambda: time.time() + 3600                          # a spent window
    assert keeper.fold(goal) is False and model.calls == []
    del keeper.window_until
    keeper._claim(f"goal:{tech}", "looking")                                  # busy with the party
    assert keeper.fold(goal) is False and model.calls == []
    keeper._busy.pop(f"goal:{tech}")
    assert keeper.fold(goal) is True
    _wait(host, tech)
    assert len(_specs(host)) == 1


def test_the_fold_runs_as_its_partys_step_in_the_specs_stage_of_its_partys_ledger(host, tech, goal, model):
    host.ideas.keeper.fold(goal)
    _wait(host, tech)
    spent = idea_spend.of_goal(host.ideas.state_dir, tech)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01


def test_the_step_has_its_tables_and_its_tier():
    assert "fold" in idea_target.STEPS and idea_spend.STEP_STAGE["fold"] == "spec" and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("fold", target) == idea_target.pick("journal", target)
    assert idea_target.pick("fold", "thrift") == ("laborer", "") and idea_target.pick("fold", "quality") == ("warrior", "medium")
    assert idea_target.READS["fold"] == 0 and idea_target.CONTEXT["fold"] == 12_000 and idea_target.CAPS["fold"] == 0.05
    assert idea_target.budget("fold", "balance") == 0.15
    assert [idea_target.CONTEXT[s] for s in ("talk_round", "section_first", "section")] == [8_000 + 3_000 + 2_500, 12_000 + 3_000 + 2_500, 12_000 + 3_000 + 2_500]


# -- the trigger ---------------------------------------------------------------------------------------------------------------------------

def test_the_flag_a_goal_gets_at_main_folds_it(host, tech, goal, model):
    assert host.ideas._raise_flag(goal, "done") is True
    _wait(host, tech)
    assert [c["key"] for c in model.steps("fold")] == [f"goal:{tech}"] and living_specs.read(host.ideas.root(), "sign-in") is not None
    assert host.ideas._raise_flag(goal, "gate") is False                              # a goal is flagged once, and folded once
    time.sleep(0.05)
    assert len(model.steps("fold")) == 1


def test_a_fold_that_breaks_never_troubles_the_flag(host, tech, goal, model, monkeypatch):
    def boom(self, slug):
        raise RuntimeError("no")
    monkeypatch.setattr(FoldMixin, "fold", boom)
    assert host.ideas._raise_flag(goal, "done") is True and model.calls == []


def test_a_goal_at_main_with_no_done_when_is_flagged_and_not_folded(host, tech, model):
    slug = _goal(host, tech, done="")
    assert host.ideas._raise_flag(slug, "done") is True and model.calls == []


# -- the part in the leaders' calls -------------------------------------------------------------------------------------------------------

def _specs_made(host, tech):
    root = host.ideas.root()
    living_specs.apply(root, "sign-in", {"added": [{"name": "Magic link", "text": "The product SHALL send a link.", "scenarios": [{"name": "a", "when": "w1", "then": "t1"}]}]}, "g", tech,
                       title="Sign-in", purpose="How a player gets in.")
    living_specs.apply(root, "billing", {"added": [{"name": "Invoice", "text": "The product SHALL invoice.", "scenarios": []}]}, "g2", "someone-else", title="Billing", purpose="How people pay.")


def _route(tech):
    return [{"party": tech, "leader": "architect"}]


def test_talks_round_has_the_specs_after_the_journals_and_before_the_map(host, tech, goal):
    _specs_made(host, tech)
    journals.add(host.ideas.state_dir, journals.PROJECT, "decision", "Decision 12: no accounts in the first release.", idea=goal, ref="12")
    p = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    assert "How the product works now:\n- Billing: How people pay.\n- Sign-in: How a player gets in." in p
    assert "Magic link: The product SHALL send a link." in p and "WHEN w1 THEN t1" in p and "Invoice" not in p.split("How the product works now:")[1].split("Your party")[0]          # Billing is not this party's
    assert p.index("Decision 12") < p.index("How the product works now") < p.index(f"Your party's map:\n{MAP}")


@pytest.mark.parametrize("first", [True, False])
def test_the_sections_prompt_has_the_specs_after_the_journals_and_before_the_map(host, tech, goal, first):
    _specs_made(host, tech)
    journals.add(host.ideas.state_dir, journals.PROJECT, "decision", "Decision 12: no accounts in the first release.", idea=goal, ref="12")
    p = host.ideas.keeper.section_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), first)
    assert "How the product works now:\n- Billing: How people pay." in p and "Magic link: The product SHALL send a link." in p
    assert p.index("Decision 12") < p.index("How the product works now") < p.index(f"Your party's map:\n{MAP}")


def test_a_product_with_no_specs_adds_no_part_and_a_spec_that_cannot_be_read_never_stops_a_call(host, tech, goal, monkeypatch):
    p = host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())
    assert "How the product works now" not in p and idea_fold.parts(host.ideas.root(), tech) == []
    _specs_made(host, tech)
    monkeypatch.setattr(living_specs, "text", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    assert idea_fold.parts(host.ideas.root(), tech) == []
    assert "Your party's map" in host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())


def test_only_the_leaders_calls_ask_for_the_specs():
    """No module of a member's call (a task's prompt, the Taskmaster's runner) reads `idea_fold`."""
    users = sorted(p.name for p in Path(idea_fold.__file__).parent.glob("*.py") if p.name != "idea_fold.py" and "idea_fold" in p.read_text(encoding="utf-8"))
    assert users == ["idea_keeper.py", "idea_sections.py", "idea_talk.py"]


# -- out: OpenSpec -------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    (root / ".orkcraft").mkdir(parents=True)
    return root


def _kept(board):
    living_specs.apply(board, "sign-in", {"added": [{"name": "Magic link", "text": "The product SHALL send a link.", "scenarios": [{"name": "a", "when": "w", "then": "t"}]}]}, "g", "tech",
                       title="Sign-in", purpose="How a player gets in.")
    living_specs.apply(board, "billing", {"added": [{"name": "Invoice", "text": "The product SHALL invoice.", "scenarios": []}]}, "g2", "product", title="Billing", purpose="How people pay.")


def test_each_living_spec_is_written_as_openspecs_text_as_kept_and_counted(project, tmp_path):
    ideas.add_track(project / "llm-wiki" / "general", "Tech")                                  # the Board's pages: where the specs are
    board = project / "llm-wiki" / "general"
    _kept(board)
    got = write_out.write(project, project / ".orkcraft", tmp_path / "out")
    assert got["specs"] == 2 and got["skipped"] == []
    for cap in ("sign-in", "billing"):
        assert (tmp_path / "out" / "openspec" / "specs" / cap / "spec.md").read_text("utf-8") == (board / "specs" / f"{cap}.md").read_text("utf-8")
    code, text = write_out.run_cli(project, tmp_path / "out2", "madr")
    assert code == 0 and text == f"Wrote 0 decisions, 6 memory bank files, 1 journal and 2 specs to {tmp_path / 'out2'}"


def test_an_export_leaves_a_file_it_did_not_write_removes_what_no_longer_belongs_and_says_none_without_specs(project, tmp_path):
    ideas.add_track(project / "llm-wiki" / "general", "Tech")
    board = project / "llm-wiki" / "general"
    _kept(board)
    out = tmp_path / "out"
    (out / "openspec" / "specs" / "billing").mkdir(parents=True)
    (out / "openspec" / "specs" / "billing" / "spec.md").write_text("# Billing Specification\n\n## Purpose\nThe person's own.\n", "utf-8")
    got = write_out.write(project, project / ".orkcraft", out)
    assert got["specs"] == 1 and got["skipped"] == [str(out / "openspec" / "specs" / "billing" / "spec.md")]
    assert (out / "openspec" / "specs" / "billing" / "spec.md").read_text("utf-8").startswith("# Billing Specification")
    (board / "specs" / "sign-in.md").unlink()
    assert write_out.write(project, project / ".orkcraft", out)["specs"] == 0 and not (out / "openspec" / "specs" / "sign-in").exists()
    assert (out / "openspec" / "specs" / "billing" / "spec.md").exists()
    (board / "specs" / "billing.md").unlink()
    code, text = write_out.run_cli(project, tmp_path / "none", "madr")
    assert text == f"Wrote 0 decisions, 6 memory bank files and 1 journal to {tmp_path / 'none'}"                  # no specs: the line as before


# -- in: OpenSpec and Kiro --------------------------------------------------------------------------------------------------------------

OPENSPEC = """# Auth Specification

## Purpose
Who may come in.

## Requirements
### Requirement: Password
The system SHALL check the password.

#### Scenario: Wrong password
- **WHEN** the password is wrong
- **THEN** the door stays shut
"""

KIRO = """# Requirements Document

## Introduction

The lobby is where players meet before a match.

## Requirements

### Requirement 1

**User Story:** As a player, I want to see the open rooms, so that I can join one

#### Acceptance Criteria

1. WHEN a player opens the lobby THEN the system SHALL list the open rooms
2. WHEN a room fills up, the system SHALL remove it from the list
3. IF the server is down THEN the system SHALL say so
4. The list SHOULD be pretty

### Requirement 2: Rooms stay open

**User Story:** As a host, I want my room kept for ten minutes

1. WHEN the host leaves THEN the system SHALL keep the room for ten minutes
"""


def _w(root, rel, text):
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, "utf-8")


def test_openspecs_specs_are_read_into_living_specs_where_none_is_kept(project):
    _w(project, "openspec/specs/auth/spec.md", OPENSPEC)
    board = project / "llm-wiki" / "general"
    got = read_in.take(project, project / ".orkcraft")
    assert got["specs_read"] == 1
    spec = living_specs.read(board, "auth")
    assert (spec["title"], spec["purpose"], spec["parties"], spec["goals"]) == ("Auth", "Who may come in.", [], [])
    assert spec["requirements"] == [{"name": "Password", "text": "The system SHALL check the password.",
                                     "scenarios": [{"name": "Wrong password", "when": "the password is wrong", "then": "the door stays shut"}]}]
    assert spec["updated"]
    assert read_in.take(project, project / ".orkcraft")["specs_read"] == 0             # read in once


def test_kiros_requirements_are_read_each_requirement_or_user_story_a_requirement_its_when_shall_lines_scenarios(project):
    _w(project, ".kiro/specs/lobby/requirements.md", KIRO)
    assert read_in.take(project, project / ".orkcraft")["specs_read"] == 1
    spec = living_specs.read(project / "llm-wiki" / "general", "lobby")
    assert (spec["title"], spec["purpose"]) == ("Lobby", "The lobby is where players meet before a match.")
    first, second = spec["requirements"]
    assert first["name"] == "see the open rooms" and first["text"].startswith("As a player, I want to see the open rooms")
    assert first["scenarios"] == [{"name": "a player opens the lobby", "when": "a player opens the lobby", "then": "the system SHALL list the open rooms"},
                                  {"name": "a room fills up", "when": "a room fills up", "then": "the system SHALL remove it from the list"},
                                  {"name": "the server is down", "when": "the server is down", "then": "the system SHALL say so"}]
    assert second["name"] == "Rooms stay open" and second["scenarios"][0]["then"] == "the system SHALL keep the room for ten minutes"
    assert living_specs_io.parse_kiro("# Nothing here\n\nJust words.\n", "x") is None


def test_a_spec_that_is_kept_is_never_read_over_and_a_file_there_that_is_no_spec_stays(project):
    board = project / "llm-wiki" / "general"
    ideas.add_track(board, "Tech")
    living_specs.apply(board, "auth", {"added": [{"name": "Mine", "text": "The product SHALL be mine.", "scenarios": []}]}, "g", "tech", title="Auth", purpose="Kept.")
    _w(board, "specs/lobby.md", "# My own notes\n\nNot a spec.\n")
    _w(project, "openspec/specs/auth/spec.md", OPENSPEC)
    _w(project, ".kiro/specs/lobby/requirements.md", KIRO)
    assert read_in.take(project, project / ".orkcraft")["specs_read"] == 0
    assert [r["name"] for r in living_specs.read(board, "auth")["requirements"]] == ["Mine"] and (board / "specs" / "lobby.md").read_text("utf-8").startswith("# My own notes")


def test_a_files_of_orkboards_own_export_is_the_same_spec_and_is_not_read_twice(project, tmp_path):
    ideas.add_track(project / "llm-wiki" / "general", "Tech")
    board = project / "llm-wiki" / "general"
    _kept(board)
    before = {cap: (board / "specs" / f"{cap}.md").read_text("utf-8") for cap in ("sign-in", "billing")}
    write_out.write(project, project / ".orkcraft", tmp_path / "out")                         # exported, and committed in the project as its own `openspec/specs`
    shutil.copytree(tmp_path / "out" / "openspec", project / "openspec")
    assert (project / "openspec" / "specs" / "sign-in" / "spec.md").is_file()
    assert read_in.take(project, project / ".orkcraft")["specs_read"] == 0
    assert {cap: (board / "specs" / f"{cap}.md").read_text("utf-8") for cap in before} == before


def test_an_export_read_into_another_project_is_the_same_specs(project, tmp_path):
    ideas.add_track(project / "llm-wiki" / "general", "Tech")
    board = project / "llm-wiki" / "general"
    _kept(board)
    other = tmp_path / "other"
    (other / ".orkcraft").mkdir(parents=True)
    write_out.write(project, project / ".orkcraft", other)
    assert read_in.take(other, other / ".orkcraft")["specs_read"] == 2
    for cap in ("sign-in", "billing"):
        assert living_specs.read(other / "llm-wiki" / "general", cap) == living_specs.read(board, cap)


def test_a_link_a_secret_and_a_large_file_are_never_read(project, tmp_path):
    outside = tmp_path / "elsewhere.md"
    outside.write_text(OPENSPEC, "utf-8")
    (project / "openspec" / "specs" / "linked").mkdir(parents=True)
    (project / "openspec" / "specs" / "linked" / "spec.md").symlink_to(outside)
    _w(project, "openspec/specs/big/spec.md", OPENSPEC + "x" * 1_100_000)
    assert read_in.take(project, project / ".orkcraft")["specs_read"] == 0


def test_the_cli_says_how_many_living_specs_it_read_and_a_dry_run_writes_none(project, capsys):
    _w(project, "openspec/specs/auth/spec.md", OPENSPEC)
    code, text = read_in.run_cli(project, dry=True)
    assert code == 0 and text.splitlines()[-1].endswith("1 living spec") and not (project / "llm-wiki").exists()
    code, text = read_in.run_cli(project)
    assert text.splitlines()[-1].endswith("1 living spec") and living_specs.read(project / "llm-wiki" / "general", "auth") is not None
    assert read_in.run_cli(project)[1].splitlines()[-1].endswith("0 releases")


def test_the_gui_reads_in_to_the_boards_pages(host):
    board = host.ideas.root()                                                           # the Board's tree, made
    root = Path(host.repo_root)
    _w(root, "openspec/specs/auth/spec.md", OPENSPEC)
    got = host.command("ideas.read_in_take", {})
    assert got["specs_read"] == 1 and living_specs.read(board, "auth") is not None
