"""The ledger and its rollup (docs/specs/36-agents-spend.md §1, §2, §4, §6): code, no model."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from orkboard.realm import idea_spend, ideas, plans


def _line(step, cost, task="", rnd=None, role="taskmaster", at="", tier="elder", tokens=None):
    return idea_spend.line(step, role, "claude", "opus", tier, "medium",
                           tokens or idea_spend.tokens_of({"in": 100, "out": 10, "cache_read": 50}), cost, task, rnd, at)


def _plan(state, slug, tasks):
    """A passed plan as the runner keeps it (its file written as the runner writes it)."""
    folder = state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "2026-10-18T09:00:00", "passed_at": "x",
                                                  "todos": [], "tasks": tasks}))


def _task(tid, state, rnd=1, role="grunt", finished="", cost=None, ran_tier="warrior"):
    return {"id": tid, "title": tid, "brief": "b", "tier": "warrior", "kind": "code", "after": [], "state": state,
            "round": rnd, "role": role, "finished": finished, "cost": cost, "ran_tier": ran_tier}


def _fixture(state, slug="dark-mode"):
    """goal (on the goal), draft, answer, plan, a task in round 1 and 2 with a fix, and a dropped task."""
    for row in (_line("draft", 0.5), _line("answer", 0.25), _line("talk", None), _line("plan", 0.2),
                _line("task", 1.0, "k1", 1, "grunt"), _line("task", 0.4, "k1", 2, "grunt"), _line("fix", 0.1, "k1", 2, "grunt"),
                _line("task", 0.3, "k2", 1, "grunt")):
        assert idea_spend.append(state, row, idea=slug)
    idea_spend.append(state, _line("goal", 0.4), goal="speed")
    _plan(state, slug, [_task("k1", "review", 2), _task("k2", "failed")])


def test_a_line_has_the_specs_fields_and_an_unpriced_call_is_null_never_0(tmp_path):
    row = _line("task", None, "k1", 2, "grunt", tokens=idea_spend.tokens_of(None, 1234))
    assert set(row) == {"at", "step", "task", "round", "role", "tool", "model", "tier", "effort", "tokens", "cost"}
    assert row["cost"] is None and row["round"] == 2
    assert row["tokens"] == {"in": None, "out": None, "cache_read": None, "cache_write": None, "total": 1234}
    keeper = _line("plan", 0.12)
    assert "task" not in keeper and "round" not in keeper and keeper["role"] == "taskmaster"
    assert keeper["tokens"] == {"in": 100, "out": 10, "cache_read": 50, "cache_write": None}


def test_each_line_goes_to_its_ledger(tmp_path):
    idea_spend.append(tmp_path, _line("draft", 0.1), idea="dark-mode")
    idea_spend.append(tmp_path, _line("goal", 0.1), goal="speed")
    idea_spend.append(tmp_path, _line("propose", 0.1))
    assert len(idea_spend.read(tmp_path / "ideas" / "dark-mode" / "spend.jsonl")) == 1
    assert len(idea_spend.read(tmp_path / "goals" / "speed" / "spend.jsonl")) == 1
    assert len(idea_spend.read(tmp_path / "ideas" / "spend-board.jsonl")) == 1
    assert idea_spend.append(tmp_path, _line("draft", 0.1), idea="../x") is False




def test_the_rollup_gives_each_stage_its_sum(tmp_path):
    _fixture(tmp_path)
    got = idea_spend.of_idea(tmp_path, "dark-mode")
    st = got["stages"]
    assert st["spec"] == {"usd": 0.75, "tokens": 480, "calls": 3}           # draft, answer, a talk unpriced
    assert st["plan"]["usd"] == 0.2 and st["work"]["usd"] == 1.0
    assert st["rework"]["usd"] == 0.5 and st["rework"]["calls"] == 2        # round 2 and the gate's fix
    assert st["dropped"] == {"usd": 0.3, "tokens": 160, "calls": 1}         # the failed task, out of work
    assert st["goal"]["calls"] == 0 and st["goal"]["usd"] == 0
    assert got["usd"] == pytest.approx(2.75) and got["unpriced"] == 1
    assert got["tasks"]["k1"] == {"usd": 1.5, "work": 1.0, "rework": 0.5}
    assert list(st) == list(idea_spend.STAGES)






def test_a_goal_sums_its_own_lines_and_its_ideas(tmp_path):
    _fixture(tmp_path)
    _plan(tmp_path, "dark-mode", [_task("k1", "merged", 2), _task("k2", "failed")])
    got = idea_spend.of_goal(tmp_path, "speed", ["dark-mode"])
    assert got["stages"]["goal"]["usd"] == 0.4 and got["stages"]["spec"]["usd"] == 0.75
    assert got["stages"]["dropped"]["usd"] == 0.3
    assert got["merged"] == 1 and got["usd"] == pytest.approx(3.15) and got["usd_per_merged"] == pytest.approx(3.15)
    assert idea_spend.of_goal(tmp_path, "speed")["usd"] == 0.4


def test_by_role_over_seven_days(tmp_path):
    idea_spend.forget()
    now = dt.datetime.now()
    recent, old = (now - dt.timedelta(days=1)).isoformat(timespec="seconds"), (now - dt.timedelta(days=9)).isoformat(timespec="seconds")
    tasks = [_task("k1", "merged", 1, finished=recent), _task("k2", "merged", 2, finished=recent),
             _task("k3", "failed", 1, finished=recent), _task("k4", "merged", 1, finished=old),
             _task("k5", "merged", 1, role="scribe", finished=recent), _task("k6", "review", 1)]
    _plan(tmp_path, "a", tasks)
    for tid, cost in (("k1", 0.3), ("k2", 0.5), ("k3", 0.2), ("k4", 9.0), ("k5", 0.1), ("k6", 1.0)):
        idea_spend.append(tmp_path, _line("task", cost, tid, 1, "grunt"), idea="a")
    idea_spend.append(tmp_path, _line("task", 0.25, "k2", 2, "grunt"), idea="a")
    idea_spend.append(tmp_path, _line("plan", 0.2, at=recent), idea="a")
    idea_spend.append(tmp_path, _line("plan", 5.0, at=old), idea="a")
    idea_spend.append(tmp_path, _line("propose", 0.05, at=recent))
    week = idea_spend.by_role(tmp_path)
    g = week["grunt"]
    assert (g["finished"], g["merged"], g["first_time"]) == (3, 2, 1) and g["spent"] == pytest.approx(1.25)
    assert g["usd_per_merged"] is None                                        # under 3 merged: too few to say
    assert week["scribe"]["merged"] == 1
    tm = week["taskmaster"]                                                   # every task of its plans, whoever did it
    assert (tm["finished"], tm["first_time"], tm["plans"]) == (4, 2, 1) and tm["spent"] == pytest.approx(0.25)
    _plan(tmp_path, "b", [_task("m1", "merged", 1, finished=recent), _task("m2", "merged", 1, finished=recent)])
    idea_spend.append(tmp_path, _line("task", 0.4, "m1", 1, "grunt"), idea="b")
    assert idea_spend.by_role(tmp_path)["grunt"]["merged"] == 2               # cached for 60 s
    idea_spend.forget()
    g = idea_spend.by_role(tmp_path)["grunt"]
    assert g["merged"] == 4 and g["usd_per_merged"] == pytest.approx(round(1.65 / 4, 4))


def test_a_deleted_ideas_lines_land_in_spend_gone_and_the_week_keeps_them(tmp_path):
    idea_spend.forget()
    root = tmp_path / "wiki"
    goal = ideas.add_track(root, "Speed")
    slug = ideas.add_idea(root, "dark mode", goal, state_dir=tmp_path)
    recent = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    _plan(tmp_path, slug, [_task("k1", "merged", 1, finished=recent)])
    idea_spend.append(tmp_path, _line("task", 0.7, "k1", 1, "grunt"), idea=slug)
    ideas.drop(root, slug, tmp_path)
    assert not (tmp_path / "ideas" / slug).exists()
    (gone,) = idea_spend.read(tmp_path / "ideas" / "spend-gone.jsonl")
    assert gone["idea"] == slug and gone["cost"] == 0.7 and gone["ended"] == "merged" and gone["last_round"] == 1
    g = idea_spend.by_role(tmp_path)["grunt"]
    assert g["merged"] == 1 and g["spent"] == 0.7




def test_the_estimate_learns_from_the_last_20_tasks_of_a_tier(tmp_path):
    assert idea_spend.tier_costs(tmp_path) == plans.DEFAULT_COST
    tasks = [_task(f"k{i}", "merged", finished=f"2026-10-{i + 1:02d}T10:00:00", cost=0.1) for i in range(5)]
    tasks += [_task(f"m{i}", "merged", finished=f"2026-10-{i + 10:02d}T10:00:00", cost=1.0) for i in range(20)]
    tasks += [_task("e1", "failed", finished="2026-10-11T10:00:00", cost=2.0, ran_tier="elder"),
              _task("e2", "review", cost=50.0, ran_tier="elder")]                 # not finished: not counted
    _plan(tmp_path, "a", tasks)
    costs = idea_spend.tier_costs(tmp_path)
    assert costs["warrior"] == pytest.approx(1.0)                           # the 20 newest, not the 5 older at 0.1
    assert costs["elder"] == pytest.approx(2.0) and costs["laborer"] == plans.DEFAULT_COST["laborer"]
    est = idea_spend.estimate_of({"ran_tier": "warrior"}, costs)
    assert est == {"low": 0.5, "high": 1.5}
    assert idea_spend.over(3.0, est) == 2.0 and idea_spend.over(1.4, est) is None and idea_spend.over(None, est) is None




def _calls(state, rows, slug="dark-mode"):
    for row in rows:
        assert idea_spend.append(state, row, idea=slug)


def test_task_session_is_none_under_too_few_and_the_median_of_round_one_task_calls_spec_153_a1(tmp_path):
    t = lambda n: idea_spend.tokens_of(None, n)       # noqa: E731
    _calls(tmp_path, [_line("task", 1.0, "k1", 1, "grunt", "2026-11-01T09:00:00", tokens=t(100)), _line("task", 2.0, "k2", 1, "grunt", "2026-11-02T09:00:00", tokens=t(300))])
    assert idea_spend.task_session(tmp_path) is None and idea_spend.TOO_FEW == 3
    _calls(tmp_path, [_line("task", 3.0, "k3", 1, "grunt", "2026-11-03T09:00:00", tokens=t(200))])
    assert idea_spend.task_session(tmp_path) == {"tokens": 200, "usd": 2.0, "n": 3}
    # a send back (round 2), a fix, a plan call and a check task are not counted
    _calls(tmp_path, [_line("task", 9.0, "k1", 2, "grunt", "2026-11-04T09:00:00", tokens=t(9000)), _line("fix", 9.0, "k1", 1, "grunt", "2026-11-04T09:00:00", tokens=t(9000)),
                      _line("plan", 9.0, at="2026-11-04T09:00:00", tokens=t(9000)), _line("task", 9.0, "k9", 1, "reviewer", "2026-11-04T09:00:00", tokens=t(9000))])
    _plan(tmp_path, "dark-mode", [_task("k1", "merged"), {**_task("k9", "merged"), "kind": "review"}])
    assert idea_spend.task_session(tmp_path) == {"tokens": 200, "usd": 2.0, "n": 3}




def _party_task(tid, state, party, kind="code"):
    return {**_task(tid, state, finished="2026-10-20T10:00:00"), "party": party, "kind": kind}


def _spent(state, tid, tool, cost, tokens):
    idea_spend.append(state, idea_spend.line("task", "grunt", tool, "m", "warrior", "", idea_spend.tokens_of(None, tokens), cost, tid, 1), idea="a")


def test_the_average_by_party_and_kind_is_over_merged_tasks_and_has_money_only_when_every_one_was_priced_spec_168_c5(tmp_path):
    idea_spend.forget()
    _plan(tmp_path, "a", [_party_task("m1", "merged", "tech"), _party_task("m2", "merged", "tech"), _party_task("m3", "merged", "tech", "bug"), _party_task("x1", "failed", "tech"),
                          _party_task("c1", "merged", "design"), _party_task("c2", "merged", "design"), _party_task("w1", "running", "tech")])
    _spent(tmp_path, "m1", "claude", 0.2, 1000)
    _spent(tmp_path, "m1", "claude", 0.1, 1000)                       # m1: two lines, 2000 tokens, $0.30
    _spent(tmp_path, "m2", "claude", 0.5, 4000)                       # m2: 4000 tokens, $0.50
    _spent(tmp_path, "m3", "claude", 9.0, 90000)                      # another kind: not in the average of code
    _spent(tmp_path, "x1", "claude", 7.0, 70000)                      # failed: not in it
    _spent(tmp_path, "w1", "claude", 0.4, 400)                        # still at work: not in it
    _spent(tmp_path, "c1", "codex", None, 6000)
    _spent(tmp_path, "c2", "codex", None, 10000)
    assert idea_spend.average(tmp_path, "tech", "code") == {"tokens": 3000, "usd": 0.4, "tool": "claude", "n": 2}
    assert idea_spend.average(tmp_path, "tech", "bug")["usd"] == 9.0
    assert idea_spend.average(tmp_path, "design", "code") == {"tokens": 8000, "usd": None, "tool": "codex", "n": 2}, "Codex has no price: tokens, no money"
    assert idea_spend.average(tmp_path, "art", "code") is None, "nothing finished of it: no average"


def test_a_cards_spend_is_what_it_spent_so_far_or_in_all_and_ahead_its_partys_average_spec_168_c5(tmp_path):
    idea_spend.forget()
    _plan(tmp_path, "a", [_party_task("m1", "merged", "tech"), _party_task("r1", "running", "tech"), _party_task("n1", "waiting", "tech"), _party_task("f1", "merged", "tech", "bug")])
    _spent(tmp_path, "m1", "claude", 0.5, 4000)
    _spent(tmp_path, "r1", "claude", 0.2, 1500)
    task = lambda tid, state, kind="code": {"id": tid, "state": state, "party": "tech", "kind": kind}  # noqa: E731
    assert idea_spend.card_of(tmp_path, "a", task("r1", "running")) == {"spend": {"tokens": 1500, "usd": 0.2, "tool": "claude"}}, "at work: so far"
    assert idea_spend.card_of(tmp_path, "a", task("m1", "merged")) == {"spend": {"tokens": 4000, "usd": 0.5, "tool": "claude"}}, "done: in all"
    assert idea_spend.card_of(tmp_path, "a", task("n1", "waiting")) == {"spend_est": {"tokens": 4000, "usd": 0.5, "tool": "claude", "n": 1}}, "ahead: its party's average for its kind"
    assert idea_spend.card_of(tmp_path, "a", task("n2", "waiting", "sound")) == {} and idea_spend.card_of(tmp_path, "a", task("f1", "merged", "bug")) == {}, "nothing known: nothing"
