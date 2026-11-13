"""Spec 168 G2 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.16.11): every error of a goal's work, by code: a task that failed, one sent back, a red test (not one red before the goal), a finding left."""
from __future__ import annotations

from orkboard.realm import goal_errors


def task(tid, state="merged", **more):
    return {"id": tid, "title": f"Task {tid}", "state": state, **more}


def test_a_failed_task_a_task_sent_back_and_a_red_test_are_errors_of_the_party_whose_work_it_was():
    got = goal_errors.of([task("a", "failed", party="tech", error="npm test: 2 failed"), task("b", round=3, party="design"),
                          task("c", party="tech", tests={"failing": ["t::one", "t::old"], "red_before": ["t::old"]})], "tech")
    assert [(e["party"], e["kind"], e["task"], e["line"]) for e in got] == [
        ("tech", "failed", "a", "npm test: 2 failed"), ("design", "sent_back", "b", "sent back 2 times"), ("tech", "test", "c", "t::one")]


def test_a_finding_left_is_an_error_a_fixed_one_is_not_an_env_one_says_so_and_the_homes_party_is_the_default():
    got = goal_errors.of([task("c", kind="review", findings=[{"where": "src/a.py", "what": "leaks", "fixed": False, "kind": "code"},
                                                             {"where": "x", "what": "fixed one", "fixed": True},
                                                             {"where": "ci", "what": "no device", "fixed": False, "kind": "env"}])], "tech")
    assert [(e["party"], e["kind"], e["line"], e.get("env", False)) for e in got] == [("tech", "finding", "src/a.py: leaks", False), ("tech", "finding", "ci: no device", True)]


