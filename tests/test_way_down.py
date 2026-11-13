"""Spec 132 C (docs/specs/132-four-levels-the-way-down-and-findings.md; decisions §234.2, §237.7): what a change pulls below its level and its price (realm/way_down.py),
the levels open on a goal, and the `level` and `pulls` each change's row carries. No model is called."""
from __future__ import annotations

import json
import sys

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, ideas, leader_change, library, spec_sections, way_down


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
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
    return _party(host, "Design", "product-designer", ["ui-kit"], "design")


ROWS = (("k1", "merged", [], ""), ("k2", "ready", ["k1"], "grunt"), ("k3", "waiting", ["k2"], "grunt"), ("k4", "review", ["k1"], "grunt"), ("k5", "ready", [], "ui-kit"))


def _goal(host, party, *, number=0, changes=(), state="working", rows=ROWS, others=(), checks=0):
    """A goal in `party`, its plan passed (`rows`: id, state, after, role), a section in each of `party` and `others`, its decision `number` (it changes `changes`)."""
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, "show the winner", party, st)
    page = ideas.idea_page(root, slug)
    secs = [(ideas.track_page(root, p).title, spec_sections.join({"Will be": "- changed Results — plain list", "Done when": "- The winner shows"})) for p in (party, *others)]
    spec_sections.arrange(page, {}, secs)
    if checks:
        page.set("checks", json.dumps([{"by": f"c{n}", "applies": True, "why": ""} for n in range(checks)] + [{"by": "off", "applies": False, "why": "no"}]))
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    tasks = []
    for tid, tstate, after, role in rows:
        t = idea_keeper._task(tid, f"Task {tid}", f"Do {tid}", "code", "warrior", list(after))
        t.update(state=tstate, role=role, **({"started": "2026-10-23T10:00:00"} if tstate not in ("waiting", "ready", "held") else {}))
        tasks.append(t)
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", {"idea": slug, "made_at": "2026-10-23T09:00:00", "passed_at": "2026-10-23T09:30:00", "passed_by": "person",
                                                                  "estimate": idea_keeper.estimate(tasks), "todos": [], "tasks": tasks})
    ideas.save_state(st, slug, state=state)
    if number:
        spec_sections.save_record(st, slug, {"decision": {"title": "D", "text": "t", "number": number, "confirmed": True, "changes": list(changes)}})
    return slug


def _pulls(host, level, **kw):
    return way_down.pulls(host.ideas.state_dir, host.ideas.root(), level, **kw)


# -- the decision level -------------------------------------------------------------------------------------------------------------------

def test_a_decision_changed_pulls_the_goals_not_done_that_rest_on_it_and_only_the_changed_partys_sections(host, tech, design):
    a = _goal(host, tech, number=5, others=(design,))
    b = _goal(host, tech, number=9, changes=(5,), others=(design,))
    done = _goal(host, tech, number=5, state="done")
    elsewhere = _goal(host, tech, number=7)
    got = _pulls(host, "decision", changes=[5], parties=[tech])
    assert got["level"] == "decision"
    assert {s["idea"] for s in got["sections"]} == {a, b} and {s["idea"] for s in got["sections"]}.isdisjoint({done, elsewhere})
    assert all(s["party"] == tech for s in got["sections"])                                  # Design's section did not change
    assert sorted(t["id"] for t in got["tasks"] if t["idea"] == a) == ["k2", "k3"]            # Tech's tasks not started: not k1 (merged), k4 (at review), k5 (Design's)
    both = _pulls(host, "decision", changes=[5], parties=[tech, design])
    assert len(both["sections"]) == 4 and {t["id"] for t in both["tasks"] if t["idea"] == a} == {"k2", "k3", "k5"}
    assert _pulls(host, "decision", changes=[42], parties=[tech])["sections"] == []
    assert _pulls(host, "decision", changes=[5], parties=[])["sections"] == []


# -- the spec level -----------------------------------------------------------------------------------------------------------------------

# -- the work level -----------------------------------------------------------------------------------------------------------------------

# -- the levels open on a goal ------------------------------------------------------------------------------------------------------------

def test_open_levels_for_each_kind(host, tech):
    st = host.ideas.state_dir
    slug = _goal(host, tech, rows=(("k1", "ready", [], "grunt"),))
    assert way_down.open_levels(st, slug) == []
    # decision: worded and not confirmed
    ideas.save_state(st, slug, state="decided")
    spec_sections.save_record(st, slug, {"decision": {"title": "D", "text": "t", "number": 3, "confirmed": False}})
    assert way_down.open_levels(st, slug) == ["decision"]
    ideas.save_state(st, slug, state="working")
    assert way_down.open_levels(st, slug) == []
    # decision: a cascade ready whose sections name it (read from cascades.json)
    (st / "cascades.json").write_text(json.dumps({"cascades": [{"status": "ready", "sections": [{"idea": slug, "party": tech}]}]}), encoding="utf-8")
    assert way_down.open_levels(st, slug) == ["decision"]
    (st / "cascades.json").write_text(json.dumps({"cascades": [{"status": "asking", "sections": [{"idea": slug, "party": tech}]}, {"status": "ready", "sections": [{"idea": "other"}]}]}), encoding="utf-8")
    assert way_down.open_levels(st, slug) == []
    (st / "cascades.json").write_text("not json", encoding="utf-8")
    assert way_down.open_levels(st, slug) == []
    # spec: a fork open, a leader's change ready
    spec_sections.save_record(st, slug, {"forks": [{"id": "f1", "status": "open"}]})
    assert way_down.open_levels(st, slug) == ["spec"]
    spec_sections.save_record(st, slug, {"forks": [{"id": "f1", "status": "answered"}]})
    leader_change.put(st, slug, {"id": "c1", "party": tech, "status": "ready"})
    assert way_down.open_levels(st, slug) == ["spec"]
    leader_change.drop(st, slug, "c1")
    # work: a plan change live, a task failed
    plan = ideas.plan(st, slug)
    plan["tasks"][0]["state"] = "failed"
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", plan)
    assert way_down.open_levels(st, slug) == ["work"]
    plan["tasks"][0]["state"] = "ready"
    plan["tasks"][0]["role"] = "grunt"
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", plan)
    from orkboard.realm import idea_change
    idea_change.write(st, slug, {"made_at": "2026-10-23T10:00:00", "why": "w", "change": [{"id": "k1", "title": "T"}], "drop": [], "add": []})
    assert way_down.open_levels(st, slug) == ["work"]
    # quality: a finding not answered
    (ideas.state_folder(st, slug) / "quality.json").write_text(json.dumps({"findings": [{"id": "f1", "status": "told"}]}), encoding="utf-8")
    assert way_down.open_levels(st, slug) == ["work", "quality"]
    (ideas.state_folder(st, slug) / "quality.json").write_text(json.dumps({"findings": [{"id": "f1", "status": "answered"}]}), encoding="utf-8")
    assert way_down.open_levels(st, slug) == ["work"]
    assert way_down.open_levels(st, "gone") == []


# -- the rows ----------------------------------------------------------------------------------------------------------------------------

def test_a_plan_changes_stop_carries_its_level_and_what_it_pulls_and_the_goals_row_its_levels(host, tech):
    st = host.ideas.state_dir
    slug = _goal(host, tech, checks=1)
    from orkboard.realm import idea_change
    idea_change.write(st, slug, {"made_at": "2026-10-23T10:00:00", "why": "w", "change": [{"id": "k2", "title": "T"}], "drop": ["k3", "k4"],
                                 "add": [{"title": "New", "tier": "laborer"}], "estimate": {"usd_low": 0.1, "usd_high": 0.2}})
    board = host.command("ideas.board")
    row = next(n for n in board["needs_you"] if n["kind"] == "change" and n["idea"] == slug)
    assert row["level"] == "work" and [t["id"] for t in row["pulls"]["tasks"]] == ["k2", "k3", ""] and row["pulls"]["checks"] == 1      # k4 has started: not pulled
    assert row["pulls"]["estimate"]["usd_high"] > 0
    goal = next(i for i in board["ideas"] if i["slug"] == slug)
    assert goal["levels"] == ["work"]
    other = _goal(host, tech)
    assert next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == other)["levels"] == []
