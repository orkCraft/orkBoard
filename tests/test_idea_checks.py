"""Spec 43 A (docs/specs/43-party-measured.md §1, Tests → A): a check says what it found. The findings file's shape, the ask in a check
task's prompt, and how a check task ends with a stub `claude` that writes its findings (the runner's fixtures)."""
from __future__ import annotations

import json
from types import SimpleNamespace


from orkboard.core.idea_task import FINDINGS_ASK
from orkboard.realm import event_log, idea_checks
from tests.test_idea_runner import calls, git, plan_of, reviewing, runner_of, tasks_of, town, wait_idle, wait_task  # noqa: F401


def text(*items, **more):
    return json.dumps({"findings": list(items), **more})


def finding(**over):
    return {"where": "a.py:1", "what": "a bug", "fixed": False, **over}


def test_clean_and_no_change_is_merged_with_no_commit_no_review_and_nothing_lands(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_clean")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = reviewing(town)                                   # Review is on: a clean check still does not wait there
    before = git(town.repo, "rev-parse", "main")
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    task = tasks_of(town)["k1"]
    assert task["state"] == "merged" and task["commit"] == "" and task["note"] == "clean" and task["findings"] == []
    assert git(town.repo, "rev-parse", "main") == before
    assert task["tests"]["ran"] is False and task["diff"] == {"files": 0, "added": 0, "removed": 0}
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("*"))
    assert not (town.repo / idea_checks.FINDINGS_FILE).exists()
    log = [r for r in event_log.read(town.repo) if r["event"] in ("task_state", "check_done")]
    merged = next(r for r in log if r["event"] == "task_state" and r["state"] == "merged")
    assert merged["check"] is True and merged["clean"] is True
    done = next(r for r in log if r["event"] == "check_done")
    assert (done["idea"], done["task"], done["found"], done["fixed"], done["left"], done["round"]) == ("demo", "k1", 0, 0, 0, 1)
    assert not [r for r in event_log.read(town.repo) if r["event"] == "result_ready"]


def test_findings_left_and_no_change_wait_at_review_even_with_review_off_and_the_file_is_never_committed(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_left")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = runner_of(town, review=False)                     # `ideas.review` off: findings left still go to Review
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["note"] == "2 left" and len(task["findings"]) == 2 and task["commit"] == ""
    assert task["diff"]["files"] == 0 and task["tests"]["green"] is True
    assert idea_checks.FINDINGS_FILE not in git(town.repo, "log", "--all", "--name-only", "--format=")
    done = next(r for r in event_log.read(town.repo) if r["event"] == "check_done")
    assert (done["found"], done["fixed"], done["left"]) == (2, 0, 2)
    assert next(r for r in event_log.read(town.repo) if r["event"] == "task_state" and r["state"] == "review")["check"] is True
    assert len(calls(town)) == 1


def test_no_findings_file_twice_fails_with_its_words_and_the_second_try_asks_again(town, monkeypatch):
    for mode in ("check_none", "check_bad"):
        monkeypatch.setenv("STUB_MODE", f"k1={mode}")
        plan_of(town, [{"id": "k1", "kind": "review"}])
        runner, _ = reviewing(town)
        runner.start("demo")
        state = wait_idle(runner)
        assert state["state"] == "failed" and "the check said nothing: no findings file" in state["error"], mode
        task = tasks_of(town)["k1"]
        assert task["state"] == "failed" and task["error"] == "the check said nothing: no findings file"
        assert len(calls(town)) >= 2
        assert FINDINGS_ASK in " ".join(calls(town)[1]["argv"])                # the retry asks for the file again
        town.log.unlink()


def test_fix_them_sends_back_and_the_check_runs_again_in_round_2(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_left")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.back("demo", "k1", "Fix the findings left:\na.py:1: a bug")
    monkeypatch.setenv("STUB_MODE", "k1=check_late")              # on the resume it finds nothing more
    task = wait_task(runner, "k1", "merged")
    assert task["round"] == 2 and task["note"] == "clean" and task["findings"] == []
    prompt = runner.log("demo", "k1")
    assert "The findings left from the last round:\n- a.py:1: a bug" in prompt and FINDINGS_ASK in prompt.split("== round 2")[1]
    decided = [r for r in event_log.read(town.repo) if r["event"] == "result_decided"]
    assert decided and decided[0]["decision"] == "back"


def test_leave_them_with_no_commit_merges_nothing_and_keeps_the_note(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_left")
    plan_of(town, [{"id": "k1", "kind": "review"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    dev = git(town.repo, "rev-parse", "dev")
    assert runner.merge("demo", "k1") == ""
    task = tasks_of(town)["k1"]
    assert task["state"] == "merged" and task["commit"] == "" and task["note"] == "2 left"
    assert git(town.repo, "rev-parse", "dev") == dev                # nothing landed
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("*k1*"))
    decided = [r for r in event_log.read(town.repo) if r["event"] == "result_decided"]
    assert decided[0]["decision"] == "merge" and decided[0]["pushed"] is False
    wait_task(runner, "k2", "review")                              # its dependant goes on


# -- spec 86 D: findings of the code and of the place -------------------------------------------------------------------------------

def test_the_findings_of_the_place_are_kept_with_their_kind_and_wait_at_review(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_env")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = runner_of(town, review=False)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert [f["kind"] for f in task["findings"]] == ["env"] and task["look"] == "findings left" and task["same_as_before"] is False


def test_all_fixed_with_changes_takes_todays_path_and_lands_when_review_is_off(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_fixed")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = runner_of(town, review=False)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    task = tasks_of(town)["k1"]
    assert task["state"] == "merged" and task["commit"] and task["note"] == "" and task["findings"][0]["fixed"] is True
    assert (town.repo / "k1.txt").read_text() == "fixed by k1\n"
    assert not (town.repo / idea_checks.FINDINGS_FILE).exists()
    assert idea_checks.FINDINGS_FILE not in git(town.repo, "log", "--all", "--name-only", "--format=")


def test_the_review_list_carries_the_kind_the_reason_and_the_flag(town, monkeypatch):
    """What the faces read: `findings[].kind`, `look`, `same`, `tests.none` (gui/ideas_review.py)."""
    from orkboard.gui.ideas_review import ReviewMixin
    monkeypatch.setenv("STUB_MODE", "k1=check_env")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = runner_of(town, review=False)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    row = ReviewMixin._check_of(SimpleNamespace(state_dir=town.state), task)
    assert row["findings"][0]["kind"] == "env" and row["same"] is False


def test_the_checks_a_plan_holds_follow_the_partys_size_spec_152_a_4(tmp_path):
    """Lean none, Standard the first check that applies in the squad's order, Full every one that applies, no size (a party of before) every one."""
    checks = idea_checks.of_team(tmp_path, ["grunt", "reviewer", "security-reviewer"], [])
    assert [c["by"] for c in checks] == ["reviewer", "security-reviewer"]
    tasks = [{"id": "k1", "title": "Do", "kind": "code", "after": []}]
    make = lambda i, title, brief, tag, tier, after: {"id": i, "kind": tag, "after": after}          # noqa: E731
    both = idea_checks.kept(None, checks)
    ids = lambda size, kept_: [t["kind"] for t in idea_checks.with_check_tasks(tasks, kept_, checks, make, size)[1:]]          # noqa: E731
    assert ids("lean", both) == []
    assert ids("standard", both) == ["review"]
    assert ids("full", both) == ["review", "security"] and ids("", both) == ["review", "security"]
    assert idea_checks.with_check_tasks(tasks, both, checks, make) == idea_checks.with_check_tasks(tasks, both, checks, make, "")
    only_second = [{"by": "reviewer", "applies": False, "why": "small"}, {"by": "security-reviewer", "applies": True, "why": ""}]
    assert ids("standard", only_second) == ["security"]                                                # the first that applies, not the first of the squad
    skipped = [{"by": "reviewer", "applies": True, "why": "", "skipped": True}, {"by": "security-reviewer", "applies": True, "why": ""}]
    assert ids("standard", skipped) == ["security"] and ids("lean", skipped) == []


def test_a_task_that_has_files_starts_its_prompt_with_where_to_start_a_check_and_a_pick_too_spec_153_b3(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "kind": "review", "after": ["k1"]},
                   {"id": "k3"}, {"id": "k4"}])
    path = town.state / "ideas" / "demo" / "plan.json"                       # plan_of keeps no `files`, `pick`: they are put in as the plan keeps them
    data = json.loads(path.read_text())
    for t, more in zip(data["tasks"], ({"files": ["a.py", "b/c.py"]}, {"files": ["a.py"]}, {"files": ["d.py"], "pick": {"n": 2, "kind": "text", "ask": "A name", "target": "n.txt"}}, {})):
        t.update(more)
    path.write_text(json.dumps(data))
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    work, check, pick, plain = (runner._prompt("demo", plan, plan["tasks"][i]) for i in range(4))
    assert "\n\nStart at: `a.py`, `b/c.py` (its planner read them; read more as you need)\n\n# The idea" in work, "just before the spec's part"
    assert not work.startswith("Start at:"), "the role and the rules stay the prompt's stable head (spec 36 §6)"
    assert "Start at: `a.py` (its planner read it" in check and "Start at: `d.py`" in pick
    assert "Start at:" not in plain
