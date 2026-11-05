"""What a project's model calls spent, read from its day logs (realm/spend_report.py, decisions §228), and `orkboard drive spend`."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.gui import drive
from orkboard.realm import spend_report


def _log(root: Path, day: str, building: str, lines: list[dict]) -> None:
    folder = root / ".orkcraft" / "logs" / day / building
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "calls.jsonl").open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")


CLAUDE_TALK = {"at": "2026-11-03T08:16:28", "tool": "claude", "model": "sonnet", "code": 0, "cost": 0.15, "tokens": 35479, "seconds": 15,
               "usage": {"input_tokens": 2, "cache_creation_input_tokens": 34637, "cache_read_input_tokens": 0, "output_tokens": 840},
               "idea": "jump", "step": "talk_round"}
CODEX_WORK = {"at": "2026-11-03T09:00:00", "tool": "codex", "model": "gpt-sol", "code": 0, "cost": None, "tokens": 90000, "seconds": 300,
              "usage": {"input_tokens": 80000, "cached_input_tokens": 60000, "output_tokens": 10000}, "idea": "jump", "step": "task"}
FAILED = {"at": "2026-11-03T09:10:00", "tool": "agy", "model": "gemini-pro-high", "code": 1, "cost": 0.02, "tokens": 70000, "seconds": 4,
          "usage": {"input_tokens": 70000, "output_tokens": 12}, "idea": "menu", "step": "section"}


def test_the_calls_add_up_by_tool_step_and_goal_and_the_unpriced_are_apart(tmp_path):
    _log(tmp_path, "2026-11-03", "board", [CLAUDE_TALK, CODEX_WORK, FAILED])
    _log(tmp_path, "2026-11-01", "board", [dict(CLAUDE_TALK, at="2026-11-01T10:00:00")])
    r = spend_report.report(spend_report.lines_of(tmp_path, since="2026-11-02"))
    t = r["total"]
    assert t["calls"] == 3 and t["cost"] == 0.17 and t["unpriced"] == 1 and t["tokens"] == 35479 + 90000 + 70000
    assert t["cache_read"] == 60000 and t["cache_write"] == 34637 and t["in"] == 2 + 20000 + 70000
    assert {row["tool"] for row in r["by_tool"]} == {"claude", "codex", "agy"}
    assert {row["goal"]: row["calls"] for row in r["by_goal"]} == {"jump": 2, "menu": 1}
    assert r["dearest"][0]["step"] == "talk_round"
    assert len(spend_report.lines_of(tmp_path)) == 4


def test_what_is_worth_a_look_is_named_by_rule(tmp_path):
    _log(tmp_path, "2026-11-03", "board", [CLAUDE_TALK, FAILED, *[dict(CODEX_WORK, at=f"2026-11-03T1{i}:00:00") for i in range(3)]])
    w = spend_report.report(spend_report.lines_of(tmp_path))["waste"]
    assert w["failed"] == {"calls": 1, "cost": 0.02}
    assert w["cache_rewritten"]["calls"] == 1 and w["cache_rewritten"]["tokens"] == 34637
    assert w["heavy_reads"]["calls"] == 1                     # 70 000 in, 12 out
    assert w["asked_again"] == [{"goal": "jump", "step": "task", "calls": 3}]


def test_one_goal_alone_and_the_text_says_it_plainly(tmp_path):
    _log(tmp_path, "2026-11-03", "board", [CLAUDE_TALK, FAILED])
    r = spend_report.report(spend_report.lines_of(tmp_path), goal="menu")
    assert r["total"]["calls"] == 1
    text = spend_report.text(r)
    assert text.startswith("1 calls for menu") and "failed calls: 1" in text and "at API prices" in text


def test_unknown_is_not_zero_in_the_totals(tmp_path):
    _log(tmp_path, "2026-11-03", "board", [dict(CODEX_WORK, at=f"2026-11-03T1{i}:00:00") for i in range(2)])
    text = spend_report.text(spend_report.report(spend_report.lines_of(tmp_path)))
    assert "no price known for these models" in text and "$0.00" not in text.split("Worth a look")[0]
    _log(tmp_path, "2026-11-04", "board", [CLAUDE_TALK])
    text = spend_report.text(spend_report.report(spend_report.lines_of(tmp_path)))
    assert "$0.15 + 2 calls with no price known" in text and "unpriced" not in text


def test_the_top_bars_gold_never_says_zero_plus_alone():
    from orkboard.core import treasury
    from orkboard.sources import telemetry
    snap = telemetry.Snapshot(sessions=1, unpriced={"gpt-6-luna"})
    assert treasury.words(snap, 20.0, 1000)[0] == "no price known / $20.00"
    snap = telemetry.Snapshot(spent_usd=1.2, sessions=1, unpriced={"gpt-6-luna"})
    assert treasury.words(snap, 20.0, 1000)[0] == "$1.20+ / $20.00"


def test_no_logs_is_nothing_spent(tmp_path):
    r = spend_report.report(spend_report.lines_of(tmp_path))
    assert r["total"]["calls"] == 0 and r["total"]["cache_share"] is None and r["dearest"] == []


def test_drive_spend_reads_the_project_it_is_in_with_no_server(tmp_path, capsys, monkeypatch):
    (tmp_path / ".git").mkdir()
    _log(tmp_path, "2026-11-03", "board", [CLAUDE_TALK])
    monkeypatch.chdir(tmp_path)
    assert drive.main(["spend", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["total"]["calls"] == 1
    assert drive.main(["spend"]) == 0
    assert "a big cache written and none read: 1 calls" in capsys.readouterr().out


# -- spec 149 H.4: work done twice, sent back --------------------------------------------------------------------------------------------------

def _work(at, task, session, cost, tokens=100_000, idea="rune"):
    return {"at": at, "tool": "codex", "model": "gpt-sol", "code": 0, "cost": cost, "tokens": tokens, "seconds": 100, "mode": "work", "idea": idea,
            "task": task, "step": "task", "session": session, "usage": {"input_tokens": tokens, "output_tokens": 10}}


def test_work_done_twice_and_work_sent_back_are_named_apart(tmp_path):
    _log(tmp_path, "2026-11-05", "board", [
        _work("2026-11-05T10:00:00", "k2", "s1", 0.5), _work("2026-11-05T10:05:00", "k2", "s1", 0.4),               # k2: sent back once, in the session it had
        _work("2026-11-05T10:07:00", "k3", "s2", 0.3, 428_000), _work("2026-11-05T10:45:00", "k3", "s3", 0.2, 326_000),      # k3: the branch reset, the work made again in a new session
        _work("2026-11-05T11:00:00", "k4", "s4", 0.1),                                                                # k4: once, nothing to say
        dict(_work("2026-11-05T11:10:00", "", "s5", 0.1), task=None)])
    w = spend_report.report(spend_report.lines_of(tmp_path))["waste"]
    assert w["sent_back"] == [{"goal": "rune", "task": "k2", "calls": 1, "tokens": 100_000, "cost": 0.4}]
    assert w["done_twice"] == [{"goal": "rune", "task": "k3", "runs": 2, "calls": 1, "tokens": 428_000, "cost": 0.3}]
    text = spend_report.text(spend_report.report(spend_report.lines_of(tmp_path)))
    assert "work done twice: rune · task k3, 2 runs, the first 1 calls (428,000 tokens, $0.30) thrown away" in text
    assert "sent back: rune · task k2, 1 calls after a red gate (100,000 tokens, $0.40)" in text
    assert "no step asked again" not in text


def test_nothing_done_twice_nor_sent_back_says_no_step_asked_again(tmp_path):
    _log(tmp_path, "2026-11-05", "board", [_work("2026-11-05T10:00:00", "k1", "s1", 0.5), _work("2026-11-05T10:30:00", "k2", "s2", 0.5)])
    r = spend_report.report(spend_report.lines_of(tmp_path))
    assert r["waste"]["done_twice"] == [] and r["waste"]["sent_back"] == []
    assert "no step asked again" in spend_report.text(r)
