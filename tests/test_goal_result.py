"""Spec 128 F (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.4, §206.8): the data a goal picked is drawn from. The snapshot's tasks carry the party they are the
work of and the tasks they wait for (the Orkmaster's tab draws the plan with its arrows); `ideas.goal_result` judges what a goal done changed against what its spec promised (by code, no model):
each part As promised, Not quite, Not done, or More than promised, and the *Done when* lines met."""
from __future__ import annotations

import json
import sys

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import goal_result, goal_team, ideas, library, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    assert "ideas.goal_result" in h.commands
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


def _goal(host, home, sections, rows, state="working"):
    """An idea of the party `home`, its spec the sections `{party: {part: text}}`, its plan the tasks `rows` (id, state, after, party)."""
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, "show the winner", home, st)
    page = ideas.idea_page(root, slug)
    arranged = [(ideas.track_page(root, party).title, spec_sections.join(parts)) for party, parts in sections.items()]
    spec_sections.arrange(page, {}, arranged)
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    tasks = []
    for tid, tstate, after, party in rows:
        t = idea_keeper._task(tid, f"Task {tid}", f"Do {tid}", "code", "warrior", list(after))
        t.update(state=tstate, party=party, step=1 if party == home else 2)
        tasks.append(t)
    data = {"idea": slug, "made_at": "2026-10-23T09:00:00", "passed_at": "2026-10-23T09:30:00", "passed_by": "person", "estimate": idea_keeper.estimate(tasks), "todos": [], "tasks": tasks}
    ideas._write_json(ideas.state_folder(st, slug) / "plan.json", data)
    ideas.save_state(st, slug, state=state)
    runner = host.ideas.runner(need=True)
    runner._launch = lambda s, t: None
    return slug


def _node(host, slug):
    return next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == slug)


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer", ["ui-kit"], "design")


# -- the plan's data -------------------------------------------------------------------------------------------------------------------

def test_the_snapshots_tasks_carry_their_party_their_step_and_the_tasks_they_wait_for(host, tech, design):
    slug = _goal(host, tech, {tech: {"Done when": "- It works"}}, [("k1", "merged", [], tech), ("k2", "ready", ["k1"], design), ("k3", "waiting", ["k1", "k2"], tech)])
    tasks = {t["id"]: t for t in _node(host, slug)["tasks"]}
    assert [(tasks[k]["party"], tasks[k]["step"], tasks[k]["after"]) for k in ("k1", "k2", "k3")] == [(tech, 1, []), (design, 2, ["k1"]), (tech, 1, ["k1", "k2"])]
    json.dumps(tasks)


def test_a_plan_of_before_names_no_party_and_no_step(host, tech):
    slug = _goal(host, tech, {tech: {"Done when": "- It works"}}, [("k1", "ready", [], "")])
    plan = ideas.plan(host.ideas.state_dir, slug)
    plan["tasks"][0].pop("party"), plan["tasks"][0].pop("step")
    ideas._write_json(ideas.state_folder(host.ideas.state_dir, slug) / "plan.json", plan)
    (t,) = _node(host, slug)["tasks"]
    assert t["party"] == "" and t["step"] == 0


# -- judging a part against its promise ------------------------------------------------------------------------------------------------

WILL = [{"kind": "new", "id": "src/lobby", "note": "a lobby"}, {"kind": "changed", "id": "src/results", "note": "the winner first"}, {"kind": "changed", "id": "src/score", "note": ""}]


def _verdicts(got):
    return {(p["id"], p["verdict"]) for p in got}


def test_a_part_touched_is_as_promised_one_whose_tasks_landed_but_that_nothing_changed_is_not_quite_and_one_not_landed_is_not_done():
    touch = {"parts": ["src/lobby", "src/results/list", "src/extra"], "screens": [], "files": 3}
    merged = [{"id": "a", "state": "merged"}, {"id": "b", "state": "merged"}]
    got = goal_result.judge(WILL, touch, merged, "tech")
    assert _verdicts(got) == {("src/lobby", "ok"), ("src/results", "ok"), ("src/score", "differs"), ("src/extra", "extra")}, "a file inside a promised part touches it; a part changed that no line names is more"
    assert next(p for p in got if p["id"] == "src/lobby")["line"] == "a lobby" and next(p for p in got if p["id"] == "src/extra")["line"].startswith("changed, and its spec did not say")
    half = [{"id": "a", "state": "merged"}, {"id": "b", "state": "ready"}]
    assert _verdicts(goal_result.judge(WILL, touch, half, "tech")) == {("src/lobby", "ok"), ("src/results", "ok"), ("src/score", "missing"), ("src/extra", "extra")}
    assert {p["verdict"] for p in goal_result.judge(WILL, {"parts": [], "screens": [], "files": 0}, [{"id": "a", "state": "ready"}], "tech")} == {"missing"}


def test_the_projects_top_touches_only_itself_and_a_dropped_task_is_not_counted():
    will = [{"kind": "changed", "id": "src/lobby", "note": ""}]
    assert _verdicts(goal_result.judge(will, {"parts": ["."], "screens": [], "files": 1}, [{"id": "a", "state": "merged"}], "tech")) == {("src/lobby", "differs")}
    tasks = [{"id": "a", "state": "merged"}, {"id": "b", "state": "dropped"}]
    assert _verdicts(goal_result.judge(will, {"parts": [], "screens": [], "files": 0}, tasks, "tech")) == {("src/lobby", "differs")}


def test_a_screen_is_promised_by_its_id_its_name_or_its_path_and_a_screen_changed_that_no_line_names_is_more():
    will = [{"kind": "changed", "id": "Results", "note": "the winner first"}, {"kind": "new", "id": "/podium", "note": ""}]
    touch = {"parts": [], "screens": [{"screen": "results", "name": "Results", "path": "/results"}, {"screen": "lobby", "name": "Lobby", "path": "/lobby"}], "files": 2}
    got = goal_result.judge(will, touch, [{"id": "a", "state": "merged"}], "design")
    assert _verdicts(got) == {("Results", "ok"), ("/podium", "differs"), ("Lobby", "extra")}


def test_a_craft_whose_map_is_not_read_from_the_files_is_judged_by_its_tasks_alone_and_has_no_more_than_promised():
    will = [{"kind": "new", "id": "Pain: slow rounds", "note": ""}]
    for states, want in ((["merged", "merged"], "ok"), (["merged", "ready"], "differs"), (["ready"], "missing")):
        tasks = [{"id": str(i), "state": s} for i, s in enumerate(states)]
        assert _verdicts(goal_result.judge(will, {"parts": ["src/x"], "screens": [], "files": 1}, tasks, "product")) == {("Pain: slow rounds", want)}
    assert goal_result.judge([], {"parts": ["src/x"], "screens": [], "files": 1}, [], "tech") == [], "nothing promised: nothing to be more than"


# -- the command -----------------------------------------------------------------------------------------------------------------------

def test_goal_result_judges_each_partys_section_and_checks_its_done_when_only_when_it_all_landed(host, tech, design, monkeypatch):
    slug = _goal(host, tech, {tech: {"Done when": "- Rounds keep their score\n- The lobby opens", "Will be": "- new src/lobby — a lobby\n- changed src/score"},
                              design: {"Done when": "- The winner shows first", "Will be": "- changed Results — the winner first"}},
                 [("k1", "merged", [], tech), ("k2", "merged", ["k1"], tech), ("k3", "ready", ["k1"], design)], state="done")
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": ["src/lobby", "src/other"], "screens": [], "files": 4})
    got = host.command("ideas.goal_result", {"idea": slug})
    assert got["idea"] == slug and got["state"] == "done" and got["files"] == 4
    by = {p["party"]: p for p in got["parties"]}
    assert set(by) == {tech, design}
    assert {(p["id"], p["verdict"]) for p in by[tech]["parts"]} == {("src/lobby", "ok"), ("src/score", "differs"), ("src/other", "extra")}
    assert [(x["text"], x["state"]) for x in by[tech]["done_when"]] == [("Rounds keep their score", "ok"), ("The lobby opens", "ok")], "its tasks all landed and no check left a finding"
    assert [(p["id"], p["verdict"]) for p in by[design]["parts"]] == [("Results", "missing")]
    assert [x["state"] for x in by[design]["done_when"]] == [""], "its task did not land: nothing says it is met"
    json.dumps(got)


def test_a_goal_not_done_reads_no_commits_and_a_gone_goal_is_refused(host, tech, monkeypatch):
    slug = _goal(host, tech, {tech: {"Will be": "- changed src/score"}}, [("k1", "ready", [], tech)])

    def boom(*a, **k):
        raise AssertionError("a goal not done has no commits to read")
    monkeypatch.setattr(goal_result, "touched", boom)
    got = host.command("ideas.goal_result", {"idea": slug})
    assert got["state"] == "working" and [(p["id"], p["verdict"]) for p in got["parties"][0]["parts"]] == [("src/score", "missing")]
    with pytest.raises(CommandError, match="That goal is gone"):
        host.command("ideas.goal_result", {"idea": "nope"})
