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
