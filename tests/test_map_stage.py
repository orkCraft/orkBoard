"""Spec 48 A (docs/specs/48-map-ideas.md §1.1): an idea's stage, round and waves, and a task's role: pure, no board."""
from __future__ import annotations

import pytest

from orkboard.realm import idea_checks, map_stage, roles

CHECK = idea_checks.TAGS[0]


def _t(tid, state, after=(), kind="code", **more):
    return {"id": tid, "state": state, "after": list(after), "kind": kind, **more}


def test_a_passed_plan_is_implementation_until_its_build_tasks_are_merged():
    tasks = [_t("k1", "merged"), _t("k2", "running", after=["k1"]), _t("k3", "waiting", kind=CHECK)]
    assert map_stage.stage_of("working", tasks, True) == "implementation"
    assert map_stage.stage_of("failed", [_t("k1", "failed")], True) == "implementation"
    assert map_stage.stage_of("working", [_t("k1", "ready")], False) == "planning"      # not passed yet


def test_a_build_task_sent_back_takes_the_idea_back_to_implementation_round_2():
    tasks = [_t("k1", "merged"), _t("k2", "review", round=2), _t("k3", "waiting", kind=CHECK)]
    assert (map_stage.stage_of("working", tasks, True), map_stage.round_of(tasks)) == ("implementation", 2)
    assert map_stage.round_of([]) == 1


def test_waves_are_the_depth_by_after_and_a_cycle_reads_as_none():
    tasks = [_t("a", "ready"), _t("b", "ready", after=["a"]), _t("c", "ready", after=["a", "b"]), _t("d", "ready")]
    assert map_stage.waves_of(tasks) == {"a": 1, "b": 2, "c": 3, "d": 1}
    assert map_stage.waves_of([_t("a", "ready", after=["b"]), _t("b", "ready", after=["a"])]) == {"a": 2, "b": 1}
    assert map_stage.waves_of([_t("a", "ready", after=["gone"])]) == {"a": 1}


def test_rows_a_chain_goes_down_one_row_a_step_and_rows_past_three_are_three():
    chain = [_t("a", "running"), _t("b", "waiting", ["a"]), _t("c", "waiting", ["b"]), _t("d", "waiting", ["c"]), _t("e", "waiting", ["d"])]
    assert map_stage.row_of(chain) == {"a": 1, "b": 2, "c": 3, "d": 3, "e": 3}
    assert map_stage.row_of([]) == {}


def test_rows_a_held_task_is_row_one_and_the_task_waiting_for_it_row_two_a_cycle_reads_as_none():
    tasks = [_t("a", "merged"), _t("h", "held", ["a"]), _t("w", "waiting", ["h"]), _t("f", "failed"), _t("p", "picking"), _t("r", "review"), _t("t", "testing")]
    assert map_stage.row_of(tasks) == {"a": 1, "h": 1, "w": 2, "f": 1, "p": 1, "r": 1, "t": 1}
    assert map_stage.row_of([_t("a", "waiting", ["b"]), _t("b", "waiting", ["a"])]) == {"a": 2, "b": 1}

