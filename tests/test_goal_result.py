"""Spec 128 F (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.4, §206.8): the data a goal picked is drawn from. The snapshot's tasks carry the party they are the
work of and the tasks they wait for (the Orkmaster's tab draws the plan with its arrows); `ideas.goal_result` judges what a goal done changed against what its spec promised (by code, no model):
each part As promised, Not quite, Not done, or More than promised, and the *Done when* lines met."""
from __future__ import annotations

import datetime as dt
import json
import sys

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import goal_result, goal_team, idea_spend, ideas, library, spec_sections


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


# -- the command -----------------------------------------------------------------------------------------------------------------------

def _sections(parties):
    return [spec_sections.Section(party, party, {"Done when": "- [test] A\n- B\n- C\n- D"}) for party in parties]


def test_a_done_when_line_is_ok_only_where_the_acceptance_said_met_unseen_and_unlooked_say_not_checked():
    tasks = [{"id": "k1", "state": "merged", "party": "tech", "step": 1}]
    accepts = {"1": {"round": 1, "verdict": "accepted", "done_when": [{"n": 1, "met": True, "why": "x"}, {"n": 2, "met": "unseen", "why": "the four-file limit"}, {"n": 3, "met": False, "why": "y"}]}}
    row = goal_result.of(_sections(["tech"]), tasks, None, True, {"tech": "tech"}, "tech", accepts)["parties"][0]["done_when"]
    assert [d["state"] for d in row] == ["ok", "unchecked", "unmet", "unchecked"]       # met · unseen · not met · nobody looked
    assert [d.get("word") for d in row] == [None, "not checked", "not met", "not checked"]
    assert all(d["landed"] for d in row), "every task landed, which no longer makes a line ok"
    none = goal_result.of(_sections(["tech"]), tasks, None, True, {"tech": "tech"}, "tech")["parties"][0]["done_when"]
    assert {d["state"] for d in none} == {"unchecked"}, "all landed, no acceptance: never ok by default"
    failed = goal_result.of(_sections(["tech"]), tasks, None, True, {"tech": "tech"}, "tech", {"1": {"round": 1, "verdict": "gone_on", "done_when": []}})["parties"][0]["done_when"]
    assert {d["state"] for d in failed} == {"unchecked"}, "an acceptance whose call failed saw nothing"
    base = {"1:k1": {"verdict": "accepted", "done_when": [{"n": 4, "met": True, "why": ""}]}}
    assert [d["state"] for d in goal_result.of(_sections(["tech"]), tasks, None, True, {"tech": "tech"}, "tech", base)["parties"][0]["done_when"]] == ["unchecked"] * 3 + ["ok"], "a base's acceptance counts for its step"
    other = {"2": accepts["1"]}
    assert {d["state"] for d in goal_result.of(_sections(["tech"]), tasks, None, True, {"tech": "tech"}, "tech", other)["parties"][0]["done_when"]} == {"unchecked"}, "another party's step is not this party's"
    notdone = goal_result.of(_sections(["tech"]), tasks, None, False, {"tech": "tech"}, "tech", accepts)["parties"][0]["done_when"]
    assert {d["state"] for d in notdone} == {"unchecked"}, "a goal not done has no ok line"


def test_goal_result_judges_each_partys_section_and_checks_its_done_when_only_when_it_all_landed(host, tech, design, monkeypatch):
    slug = _goal(host, tech, {tech: {"Done when": "- [test] Rounds keep their score\n- The lobby opens", "Will be": "- new src/lobby — a lobby\n- changed src/score"},
                              design: {"Done when": "- The winner shows first", "Will be": "- changed Results — the winner first"}},
                 [("k1", "merged", [], tech), ("k2", "merged", ["k1"], tech), ("k3", "ready", ["k1"], design)], state="done")
    monkeypatch.setattr(goal_result, "touched", lambda *a, **k: {"parts": ["src/lobby", "src/other"], "screens": [], "files": 4})
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p.update(accepts={"1": {"round": 1, "verdict": "accepted", "done_when": [{"n": 1, "met": True, "why": ""}, {"n": 2, "met": "unseen", "why": "no file"}]}}))
    got = host.command("ideas.goal_result", {"idea": slug})
    assert got["idea"] == slug and got["state"] == "done" and got["files"] == 4
    by = {p["party"]: p for p in got["parties"]}
    assert set(by) == {tech, design}
    assert {(p["id"], p["verdict"]) for p in by[tech]["parts"]} == {("src/lobby", "ok"), ("src/score", "differs"), ("src/other", "extra")}
    assert [(x["text"], x["state"]) for x in by[tech]["done_when"]] == [("Rounds keep their score", "ok"), ("The lobby opens", "unchecked")], "the acceptance said met of the first and unseen of the second"
    assert [x["proof"] for x in by[tech]["done_when"]] == ["test", ""], "a line's mark is apart from its words (decisions §257.4)"
    assert [(p["id"], p["verdict"]) for p in by[design]["parts"]] == [("Results", "missing")]
    assert [x["state"] for x in by[design]["done_when"]] == ["unchecked"], "its task did not land and nobody accepted it: nothing says it is met"
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


# -- spec 149 H.1: what a goal made, beside what it promised -----------------------------------------------------------------------------------

def test_spend_gives_the_tokens_of_a_goal_and_the_share_the_reads_show(host, tech):
    from orkboard.realm import event_log as ev
    slug = _goal(host, tech, {tech: {"Why": "x", "Done when": "- one"}}, [("t1", "merged", [], tech)])
    state = host.ideas.state_dir
    now = dt.datetime.now().astimezone()
    idea_spend.append(state, idea_spend.line("task", "grunt", "codex", "gpt-sol", "warrior", "", idea_spend.tokens_of(None, 3_000_000), None, "t1", 1,
                                             (now - dt.timedelta(hours=1)).isoformat(timespec="seconds")), idea=slug)
    for hours, left in ((-2, 0.90), (0, 0.88)):
        ev.record(host.ideas.host.repo_root, ev.LIMITS_READ, at=now + dt.timedelta(hours=hours), provider="codex", left=left, window="week")
    got = host.command("ideas.spend", {"idea": slug})
    assert got["usd"] is None and got["tokens"] == 3_000_000
    assert got["share"]["tool"] == "codex" and got["share"]["name"] == "Codex" and got["share"]["window"] == "week" and got["share"]["share"] == 2.0

