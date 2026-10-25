"""Spec 84 (docs/specs/84-the-next-task-goes-on.md) and spec 86 A, C: a result lands in dev by itself when it holds, with the reason it waits when
it does not; the slots by party size, one task per member, never on the same files; a cost counted once. A temp repository, a stub `claude`
on PATH (tests/test_idea_runner.py)."""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from orkboard.core import idea_landing, idea_runner
from orkboard.core.idea_runner import IdeaRunner
from orkboard.realm import idea_git
from tests.test_idea_runner import calls, git, plan_of, reviewing, runner_of, tasks_of, town, wait_idle, wait_task  # noqa: F401


def amend(town, tid: str, slug: str = "demo", **fields) -> None:
    """Fields of a plan's task the fixture does not write (`role`, `files`)."""
    path = town.state / "ideas" / slug / "plan.json"
    plan = json.loads(path.read_text())
    next(t for t in plan["tasks"] if t["id"] == tid).update(fields)
    path.write_text(json.dumps(plan))


def page(town, slug: str = "demo", **front) -> None:
    folder = town.repo / "llm-wiki" / "general" / "pages" / "ideas"
    folder.mkdir(parents=True, exist_ok=True)
    head = "".join(f"{k}: {v}\n" for k, v in {"owner": "board", **front}.items())
    (folder / f"{slug}.md").write_text(f"---\n{head}---\n# {slug.title()}\n\n## Gist\nA demo idea.\n")


def spans(town) -> dict:
    return {c["tid"]: (c["start"], c["end"]) for c in calls(town)}


def overlap(a, b) -> bool:
    return a[0] < b[1] and b[0] < a[1]


# -- the default ----------------------------------------------------------------------------------------------------------------

def test_review_is_off_by_default_in_the_runner_and_a_result_that_holds_lands(town):
    assert idea_runner.DEFAULTS["review"] is False
    plan_of(town, [{"id": "k1"}])
    bare = SimpleNamespace(ideas={"merge_into": "main", "push": False})                  # a settings object that names no `review`
    runner = IdeaRunner(town.repo, town.state, bare, None, limits=lambda: [])
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    task = tasks_of(town)["k1"]
    assert task["state"] == "merged" and task["look"] == ""
    assert (town.repo / "k1.txt").read_text() == "done by k1\n"


# -- each condition of §1 alone keeps the result for the look -----------------------------------------------------------------------

def test_review_on_keeps_every_result_and_says_so(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "you asked to look at each result" and task["tests"]["ran"] and task["tests"]["green"]


def test_tests_that_did_not_run_wait_for_the_look(town, monkeypatch):
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    monkeypatch.setattr(runner.git, "gate_run", lambda *a, **k: idea_git.GateRun(True, "no tests ran", False, "pytest"))
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "tests did not run" and task["tests"]["ran"] is False and "none" not in task["tests"]


def test_a_project_with_no_tests_at_all_never_lands_by_itself_and_says_why(town, monkeypatch):
    """Spec 86 §3 (the runner's side): the gate says `none`, and the result waits with *no tests in this project*. Works with a `Gate` that has no `none` yet."""
    from orkboard.core import idea_task
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    monkeypatch.setattr(runner.git, "gate_run", lambda *a, **k: idea_git.GateRun(True, "no tests ran", False, ""))
    monkeypatch.setattr(idea_task.gate_config, "read", lambda root: SimpleNamespace(none=True, error=""))
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "no tests in this project" and task["tests"]["none"] is True


def test_findings_left_wait_for_the_look(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=check_left")
    plan_of(town, [{"id": "k1", "kind": "review"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_task(runner, "k1", "review")["look"] == "findings left"


def test_a_risk_path_its_goals_risk_left_out_waits_and_names_the_path(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=risk")
    plan_of(town, [{"id": "k1"}])
    page(town, risk="low", risk_triggers="[]")
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_task(runner, "k1", "review")["look"] == "touches auth/login.py"


def test_a_risk_path_its_goals_risk_named_lands(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=risk")
    plan_of(town, [{"id": "k1"}])
    page(town, risk="medium", risk_triggers=json.dumps(["secrets, sign-in, payments"]))
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done" and tasks_of(town)["k1"]["state"] == "merged"


def test_the_repositorys_own_risk_paths_count_too(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town, risk_paths=["k1.txt"])
    runner.start("demo")
    assert wait_task(runner, "k1", "review")["look"] == "touches k1.txt"


def test_pictures_wait_for_the_look(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=pictures")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_task(runner, "k1", "review")["look"] == "holds pictures"


def test_media_and_risk_helpers():
    assert idea_landing.media_in(["a.py", "docs/shot.PNG"]) == "docs/shot.PNG" and idea_landing.media_in(["a.py", "b.md"]) == ""
    assert idea_landing.risky_path(["src/x.py", "infra/main.tf"], set(), []) == "infra/main.tf"
    assert idea_landing.risky_path(["infra/main.tf"], {"CI and deploy"}, []) == ""


def test_red_tests_wait_for_the_look_with_review_off(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_always")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "the tests are red" and task["tests"]["green"] is False


def test_a_task_never_starts_from_a_result_that_waits_and_goes_on_when_it_is_merged(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=pictures")
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = runner_of(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    for _ in range(5):
        runner.tick()
        time.sleep(0.1)
    assert tasks_of(town)["k2"]["state"] == "waiting" and [c["tid"] for c in calls(town)] == ["k1"]
    runner.merge("demo", "k1")
    assert wait_idle(runner)["state"] == "done"
    assert [c["tid"] for c in calls(town)] == ["k1", "k2"] and tasks_of(town)["k2"]["state"] == "merged"


# -- the slots (§2) --------------------------------------------------------------------------------------------------------------

def sized(runner, size: str):
    runner.size_of = lambda slug: size
    return runner


@pytest.mark.parametrize("size, together", [("lean", 1), ("standard", 2), ("full", 3), ("", 1)])
def test_a_party_runs_as_many_tasks_at_once_as_its_size_gives(town, monkeypatch, size, together):
    monkeypatch.setenv("STUB_SLEEP", "2.5")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}, {"id": "k3"}])
    runner, _ = runner_of(town)                                    # the Board's own `max_parallel` is 1
    sized(runner, size).start("demo")
    assert wait_idle(runner)["state"] == "done"
    s = spans(town)
    most = max(sum(1 for t in s.values() if t[0] <= probe < t[1]) for probe in (x[0] + 0.01 for x in s.values()))
    assert most == together


def test_one_task_per_member_of_a_party_at_a_time(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "1.5")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}, {"id": "k3"}])
    for tid, role in (("k1", "grunt"), ("k2", "grunt"), ("k3", "taskmaster")):
        amend(town, tid, role=role)
    runner, _ = runner_of(town)
    sized(runner, "full").start("demo")
    assert wait_idle(runner)["state"] == "done"
    s = spans(town)
    assert not overlap(s["k1"], s["k2"])                           # the same member: one after the other
    assert overlap(s["k3"], s["k1"]) or overlap(s["k3"], s["k2"])  # another member goes beside


def test_never_two_tasks_whose_files_meet(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "1.5")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}, {"id": "k3"}])
    amend(town, "k1", files=["pkg/core/a.py"])
    amend(town, "k2", files=["pkg/core/"])
    amend(town, "k3", files=["docs/b.md"])
    runner, _ = runner_of(town)
    sized(runner, "full").start("demo")
    assert wait_idle(runner)["state"] == "done"
    s = spans(town)
    assert not overlap(s["k1"], s["k2"])                           # a file and its folder meet
    assert overlap(s["k3"], s["k1"]) or overlap(s["k3"], s["k2"])


def test_paths_come_from_a_tasks_files_and_its_brief_cut_to_folders():
    assert idea_landing.paths_of({"files": ["orkboard/gui/static/*", "README.md"], "brief": "Edit `orkboard/realm/x.py` and `y`"}) \
        == ["orkboard/gui/static", "README.md", "orkboard/realm/x.py"]
    assert idea_landing.paths_of({"brief": "no paths here"}) == []


def test_goals_that_touch_the_same_files_do_not_run_beside_each_other(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "1.5")
    plan_of(town, [{"id": "k1"}])
    plan_of(town, [{"id": "o1"}], slug="other")
    page(town, touches=json.dumps(["pkg/core/"]))
    page(town, slug="other", touches=json.dumps(["pkg/core/a.py"]))
    runner, _ = runner_of(town, max_parallel=2)
    runner.start("demo")
    runner.start("other")
    wait_idle(runner, "demo")
    wait_idle(runner, "other")
    runs = sorted((c["start"], c["end"]) for c in calls(town))
    assert len(runs) == 2 and runs[1][0] >= runs[0][1] - 0.05      # the second goal waited for the first


def test_goals_that_touch_nothing_in_common_run_together_where_the_board_allows(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "2.5")
    plan_of(town, [{"id": "k1"}])
    plan_of(town, [{"id": "o1"}], slug="other")
    page(town, touches=json.dumps(["pkg/core/"]))
    page(town, slug="other", touches=json.dumps(["docs/guide/"]))
    runner, _ = runner_of(town, max_parallel=2)
    runner.start("demo")
    runner.start("other")
    wait_idle(runner, "demo")
    wait_idle(runner, "other")
    a, b = sorted((c["start"], c["end"]) for c in calls(town))
    assert b[0] < a[1]


# -- a cost counted once (spec 86 §1) ---------------------------------------------------------------------------------------------

def test_a_resumed_sessions_total_is_added_as_its_difference(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fix_conflict")           # a send back resumes: the stub reports 0.01, then its running total 0.02, 0.03
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    first = wait_task(runner, "k1", "review")
    assert first["cost"] == pytest.approx(0.01) and first["session_total"] == pytest.approx(0.01)
    runner.back("demo", "k1", "once more")
    second = wait_task(runner, "k1", "review")
    assert second["cost"] == pytest.approx(0.02) and second["session_total"] == pytest.approx(0.02)       # not 0.03
    runner.back("demo", "k1", "and again")
    third = wait_task(runner, "k1", "review")
    assert third["cost"] == pytest.approx(0.03) and third["session_total"] == pytest.approx(0.03)         # not 0.06
    from orkboard.realm import idea_spend
    rows = idea_spend.read(town.state / "ideas" / "demo" / "spend.jsonl")
    assert [r["cost"] for r in rows] == pytest.approx([0.01, 0.01, 0.01])


def test_a_fresh_sessions_whole_cost_is_added_and_a_fix_in_the_same_session_adds_its_difference(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_once")              # the gate's one fix resumes the session
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert [c["resume"] for c in calls(town)] == [False, True]
    assert task["cost"] == pytest.approx(0.02) and task["session_total"] == pytest.approx(0.02)


# -- a send back past 150 k tokens starts a fresh session (spec 86 §4) ---------------------------------------------------------------

def test_a_send_back_whose_last_call_read_more_than_150k_tokens_starts_a_fresh_session(town, monkeypatch):
    monkeypatch.setenv("STUB_BIG", "k1")
    monkeypatch.setenv("STUB_MODE", "k1=rewrite")
    plan_of(town, [{"id": "k1", "brief": "write the file k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    first = wait_task(runner, "k1", "review")
    assert first["last_tokens"] > 150_000
    runner.back("demo", "k1", "name it better")
    second = wait_task(runner, "k1", "review")
    assert [c["resume"] for c in calls(town)] == [False, False]              # no --resume
    log = runner.log("demo", "k1", 400).split("== round 2")[1]
    assert "write the file k1" in log and "name it better" in log             # the task's prompt, and the why
    assert "```diff" in log and "k1.txt" in log and "done by k1" in log       # the diff so far
    assert second["cost"] == pytest.approx(0.02) and second["session_total"] == pytest.approx(0.01)     # a fresh session: its whole cost


def test_a_send_back_of_a_small_session_resumes_it(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fix_conflict")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.back("demo", "k1", "name it better")
    wait_task(runner, "k1", "review")
    assert [c["resume"] for c in calls(town)] == [False, True]
    assert "```diff" not in runner.log("demo", "k1", 400)
