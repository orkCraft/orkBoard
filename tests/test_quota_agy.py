"""
tests/test_agy_quota.py

Tests for orkboard.quota.agy_quota using pytest.
All tests use fixtures or mock runners; real CLI commands are never executed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from orkboard.quota.agy_quota import get_agy_quota

_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_AGY_FIXTURE = _FIXTURES_DIR / "agy_usage.json"


def test_agy_quota_from_fixture() -> None:
    raw_fixture = _AGY_FIXTURE.read_text(encoding="utf-8")
    statuses = get_agy_quota(runner=lambda cmd, **kwargs: raw_fixture)

    assert len(statuses) == 4
    for s in statuses:
        assert s.provider == "agy"
        assert s.error is None

    gemini_weekly = next(s for s in statuses if s.group == "Gemini Models" and s.window == "weekly")
    assert gemini_weekly.remaining_fraction == pytest.approx(0.865365, rel=1e-4)
    assert gemini_weekly.reset_time == datetime(2026, 10, 3, 6, 49, 49, tzinfo=timezone.utc)

    gemini_5h = next(s for s in statuses if s.group == "Gemini Models" and s.window == "5h")
    assert gemini_5h.remaining_fraction == pytest.approx(0.393406, rel=1e-4)
    assert gemini_5h.reset_time == datetime(2026, 9, 26, 14, 9, 4, tzinfo=timezone.utc)

    claude_weekly = next(s for s in statuses if s.group == "Claude and GPT models" and s.window == "weekly")
    assert claude_weekly.remaining_fraction == 1.0
    assert claude_weekly.reset_time == datetime(2026, 10, 3, 6, 49, 15, tzinfo=timezone.utc)

    claude_5h = next(s for s in statuses if s.group == "Claude and GPT models" and s.window == "5h")
    assert claude_5h.remaining_fraction == 1.0
    assert claude_5h.reset_time == datetime(2026, 9, 26, 18, 35, 26, tzinfo=timezone.utc)


def test_agy_cli_not_found() -> None:
    def runner(cmd, **kwargs):
        raise FileNotFoundError("No such file or directory: agy")

    statuses = get_agy_quota(runner=runner)
    assert len(statuses) == 1
    s = statuses[0]
    assert s.provider == "agy"
    assert s.error is not None
    assert "CLI not found" in s.error
    assert s.remaining_fraction is None
    assert s.reset_time is None


def test_agy_runner_receives_correct_args() -> None:
    captured = {}

    def runner(cmd, timeout=None):
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        return _AGY_FIXTURE.read_text(encoding="utf-8")

    get_agy_quota(agy_bin="/custom/agy", timeout=45, runner=runner)
    assert captured["cmd"] == ["/custom/agy", "-p", "/usage", "--output-format", "json"]
    assert captured["timeout"] == 45
