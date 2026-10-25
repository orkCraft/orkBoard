"""Spec 35 §0, §1, §6: the Target's matrix, a role's own model, the CLI's flags (a fake `--help` both ways), the night
window and the reserve."""
from __future__ import annotations

import datetime as dt
import stat
import sys

import pytest

from orkboard.realm import harnesses, idea_target, jobs
from orkboard.sources.limits import Limit

EXPECTED = {
    "goal": {"thrift": ("elder", "medium"), "balance": ("elder", "high"), "quality": ("elder", "xhigh")},
    "draft": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "answer": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "collide": {"thrift": ("warrior", "low"), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "talk": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "plan": {"thrift": ("elder", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "refresh": {"thrift": None, "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "propose": {"thrift": None, "balance": ("elder", "low"), "quality": ("elder", "medium")},
}


@pytest.mark.parametrize("step", sorted(EXPECTED))
@pytest.mark.parametrize("target", idea_target.TARGETS)
def test_every_keeper_step_and_target_gives_its_tier_and_effort(step, target):
    assert idea_target.pick(step, target) == EXPECTED[step][target]


@pytest.mark.parametrize("tier,target,want", [
    ("warrior", "thrift", ("laborer", "low")), ("warrior", "balance", ("warrior", "medium")),
    ("warrior", "quality", ("elder", "high")), ("laborer", "thrift", ("laborer", "low")),
    ("elder", "quality", ("elder", "high")), ("elder", "thrift", ("warrior", "low"))])
def test_a_tasks_tier_shifts_by_the_target_never_past_the_ends(tier, target, want):
    assert idea_target.pick("task", target, tier) == want
    assert idea_target.task_pick(tier, target, "") == want                  # Grunt ("") runs on the shifted tier


def test_a_roles_own_model_wins_and_keeps_the_targets_effort():
    assert idea_target.task_pick("warrior", "thrift", "opus") == ("opus", "low")
    assert idea_target.keeper_pick("draft", "quality", "haiku") == ("haiku", "high")
    assert idea_target.keeper_pick("draft", "quality", "elder") == ("elder", "high")    # the default is not a pick
    assert idea_target.keeper_pick("refresh", "thrift", "haiku") is None


def test_the_budget_is_halved_in_thrift_and_doubled_in_quality_and_the_caps_hold():
    assert idea_target.budget("draft", "balance") == 0.6 and idea_target.budget("draft", "thrift") == 0.3      # above their floors
    assert idea_target.budget("goal", "quality") == 2.0 and idea_target.budget("task", "balance") is None
    got = idea_target.cut([("A", "x" * 50), ("B", "y" * 5000), ("C", "never")], 1000)
    assert len(got) <= 1000 and "x" * 50 in got and "never" not in got


def _fake_cli(tmp_path, monkeypatch, help_text: str):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    cli = bindir / "claude"
    cli.write_text(f"#!{sys.executable}\nimport sys\nprint({help_text!r})\n")
    cli.chmod(cli.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("ORKCRAFT_CLAUDE_BIN", str(cli))
    harnesses._HELP.clear()
    return harnesses.get("claude")


def test_effort_budget_and_no_session_are_on_the_command_only_when_the_cli_lists_them(tmp_path, monkeypatch):
    h = _fake_cli(tmp_path, monkeypatch, "--effort <level>  --max-budget-usd <x>  --no-session-persistence")
    read = h.read("p", tmp_path, "elder", effort="high", budget=0.6, one_shot=True)
    assert read[read.index("--effort") + 1] == "high" and read[read.index("--max-budget-usd") + 1] == "0.60"
    assert "--no-session-persistence" in read
    work = h.work("p", tmp_path, "warrior", effort="medium")
    assert work[work.index("--effort") + 1] == "medium"
    assert "--effort" not in h.read("p", tmp_path, "laborer", effort="high")          # never on the laborer tier
    assert "--effort" not in h.work("p", tmp_path, "haiku", effort="high")
    h = _fake_cli(tmp_path, monkeypatch, "Usage: claude [options]  --model <m>")
    read = h.read("p", tmp_path, "elder", effort="high", budget=0.6, one_shot=True)
    assert "--effort" not in read and "--max-budget-usd" not in read and "--no-session-persistence" not in read
    assert harnesses.get("agy").read("p", tmp_path, "elder", effort="high")[-1] != "high"   # other tools ignore it


def test_propose_reads_nothing(tmp_path, monkeypatch):
    h = _fake_cli(tmp_path, monkeypatch, "")
    cmd = h.read("p", tmp_path, "elder", tools=False)
    last = max(i for i, a in enumerate(cmd) if a == "--disallowedTools")
    assert "Read" in cmd[last + 1].split(",") and "Grep" in cmd[last + 1].split(",")


def test_a_read_ended_on_its_budget_uses_its_answer_or_says_so(tmp_path, monkeypatch):
    import json
    h = _fake_cli(tmp_path, monkeypatch, "--max-budget-usd")
    out = {"result": '{"ok": 1}', "subtype": "error_max_budget_usd", "total_cost_usd": 0.6}
    script = tmp_path / "bin" / "claude"
    script.write_text(f"#!{sys.executable}\nimport sys\nif '--help' in sys.argv: print('--max-budget-usd'); sys.exit(0)\n"
                      f"print({json.dumps(out)!r}); sys.exit(1)\n")
    import threading
    text, cost, _t, _s = jobs.run_read("claude", "p", tmp_path, threading.Event(), "elder", budget=0.6)
    assert text == '{"ok": 1}' and cost == 0.6
    script.write_text(f"#!{sys.executable}\nimport sys\nif '--help' in sys.argv: print('--max-budget-usd'); sys.exit(0)\n"
                      "print('{\"subtype\": \"error_max_budget_usd\"}'); sys.exit(1)\n")
    with pytest.raises(jobs.BudgetSpent, match="ran out of its budget"):
        jobs.run_read("claude", "p", tmp_path, threading.Event(), "elder", budget=0.6)
    assert h is not None


def test_the_night_window_crosses_midnight_and_is_local_time():
    at = lambda h, m=0: dt.datetime(2026, 10, 18, h, m)                       # noqa: E731
    assert idea_target.in_night("01:00-07:00", at(3)) and not idea_target.in_night("01:00-07:00", at(7))
    assert idea_target.night_start("22:00-06:00", at(2)) == dt.datetime(2026, 10, 17, 22, 0)
    assert idea_target.in_night("22:00-06:00", at(23)) and not idea_target.in_night("22:00-06:00", at(12))


def test_the_reserve_by_day_and_at_night_and_none_without_limits():
    noon_at = dt.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    reset = noon_at + dt.timedelta(hours=20)                                  # after both moments below
    noon, night = noon_at.timestamp(), (noon_at + dt.timedelta(hours=15)).timestamp()   # 12:00 and 03:00 the next day
    rows = lambda left: [Limit("claude", "", "session", left, reset)]          # noqa: E731
    s = {"night": "01:00-07:00", "reserve_day": 0.3, "reserve_night": 0.1}
    assert idea_target.reserve_held(rows(0.25), s, noon) == pytest.approx(reset.timestamp())   # day: 0.25 ≤ 0.30
    assert idea_target.reserve_held(rows(0.35), s, noon) is None
    assert idea_target.reserve_held(rows(0.25), s, night) is None                             # night: 0.25 > 0.10
    assert idea_target.reserve_held(rows(0.08), s, night) is not None
    assert idea_target.reserve_held([], s, noon) is None


def test_a_partys_size_is_its_target_and_the_kind_step_is_the_cheaper_tier_of_the_judge():
    """Spec 75 §3, §4.2: `target_for` (a size's Target, else the setting's); the Orkmaster's `kind` step runs as its `collide` judge does."""
    assert idea_target.SIZES == ("lean", "standard", "full") and idea_target.SIZE_TARGET == {"lean": "thrift", "standard": "balance", "full": "quality"}
    assert [idea_target.target_for({"target": "thrift"}, {"size": s}) for s in idea_target.SIZES] == ["thrift", "balance", "quality"]
    assert idea_target.target_for({"target": "quality"}, {"size": ""}) == idea_target.target_for({"target": "quality"}, None) == "quality"
    assert idea_target.target_for({}, {"size": "huge"}) == idea_target.DEFAULT
    assert idea_target.pick("kind", "balance") == idea_target.pick("collide", "balance") == ("warrior", "low")
    assert idea_target.pick("kind", "thrift") == ("laborer", "") and "kind" in idea_target.STEPS
    assert set(idea_target.MATRIX) >= set(idea_target.STEPS) and idea_target.budget("kind", "balance") == 0.15 and idea_target.CONTEXT["kind"] == 1_500


# -- the floor (spec 86 §5) -------------------------------------------------------------------------------------

@pytest.fixture
def fresh_floors():
    idea_target._FLOORS.clear()
    yield
    idea_target._FLOORS.clear()


def keeper_calls(root, costs, model="opus", day="2026-10-25", **more):
    import json
    folder = root / ".orkcraft" / "logs" / day / "board"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "calls.jsonl").open("a", encoding="utf-8") as f:
        for i, cost in enumerate(costs):
            line = {"n": i, "at": f"{day}T10:{i:02d}:00", "side": "", "who": "", "purpose": "plan", "mode": "read",
                    "tool": "claude", "model": model, "code": 0, "cost": cost, "usage": {"output_tokens": 50}}
            f.write(json.dumps({**line, **more}) + "\n")


def test_the_floor_is_the_table_when_no_calls_are_kept(fresh_floors, tmp_path):
    from orkboard.realm import call_log
    assert idea_target.FLOOR == {"elder": 0.25, "warrior": 0.10, "laborer": 0.03}
    assert [idea_target.floor(t) for t in ("elder", "warrior", "laborer")] == [0.25, 0.10, 0.03]
    with call_log.of_project(tmp_path):                                  # a project with no calls yet
        assert idea_target.floor("elder", "claude") == 0.25
        assert idea_target.floor("elder", "codex") == 0.25


def test_the_floor_is_the_median_of_the_last_ten_one_turn_calls_of_that_tier_on_that_tool(fresh_floors, tmp_path):
    from orkboard.realm import call_log
    keeper_calls(tmp_path, [9.0, 9.0, 9.0], day="2026-10-20")                              # older than the last ten
    keeper_calls(tmp_path, [0.20, 0.18, 0.22, 0.19, 0.21, 0.20, 0.18, 0.22, 0.20, 0.30])
    keeper_calls(tmp_path, [5.0], usage={"output_tokens": 5000})                           # wrote a lot: not a floor
    keeper_calls(tmp_path, [7.0], model="haiku")                                           # another tier
    keeper_calls(tmp_path, [6.0], tool="codex")                                            # another tool
    with call_log.of_project(tmp_path):
        assert idea_target.floor("elder", "claude") == 0.20
        assert idea_target.floor("laborer", "claude") == idea_target.FLOOR["laborer"]      # 1 call of it: too few to measure


def test_a_budget_is_never_under_one_and_a_half_floors(fresh_floors, tmp_path):
    from orkboard.realm import call_log
    # Lean's collision judge ran out at $0.025: it is now a Seasoned call, with 1.5 x $0.10
    assert idea_target.pick("collide", "thrift") == ("warrior", "low")
    assert idea_target.budget("collide", "thrift") == 0.15 and idea_target.budget("collide", "balance") == 0.15
    assert idea_target.budget("answer", "thrift") == 0.20 and idea_target.budget("talk", "thrift") == 0.15    # talk: 0.10 -> 0.15
    assert idea_target.budget("pitch_view", "thrift") == 0.05                   # a laborer call: 1.5 x 0.03, rounded up
    assert idea_target.pick("refresh", "thrift") is None and idea_target.budget("refresh", "thrift") == 0.25    # skipped: its cap alone
    assert idea_target.budget("task", "balance") is None
    for step in idea_target.CAPS:
        for target in idea_target.TARGETS:
            got = idea_target.pick(step, target) if step in idea_target.MATRIX else None
            if got:
                assert idea_target.budget(step, target) >= 1.5 * idea_target.floor(got[0]) - 0.01, (step, target)
    keeper_calls(tmp_path, [0.40] * 5)                                                     # a dearer measure raises it
    with call_log.of_project(tmp_path):
        assert idea_target.budget("goal", "thrift") == 0.6 and idea_target.budget("plan", "thrift") == 0.6


def test_lean_runs_its_draft_answer_talk_and_judge_on_the_seasoned_tier_and_its_goal_and_plan_on_the_veteran():
    for step in ("draft", "answer", "talk", "collide"):
        assert idea_target.pick(step, "thrift") == ("warrior", "low")
    for step in ("goal", "plan"):
        assert idea_target.pick(step, "thrift")[0] == "elder"
