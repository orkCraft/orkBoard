"""🪙 / 🪵: prices from the official table, transcript metering, HUD and the budget gate."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from orkboard.sources import pricing, telemetry
from orkboard.sources import transcripts as tr


def test_usage_cost_cache_ttl_fast_and_geo():
    m = 1_000_000
    usage = {"input_tokens": m, "output_tokens": m, "cache_read_input_tokens": m,
             "cache_creation_input_tokens": 2 * m,
             "cache_creation": {"ephemeral_5m_input_tokens": m, "ephemeral_1h_input_tokens": m}}
    # Opus 5.5: 4 in + 20 out + 0.20 read + 5 (5m write) + 8 (1h write)
    assert pricing.usage_cost("claude-opus-5-5", usage) == pytest.approx(37.20)
    no_split = {"cache_creation_input_tokens": m}
    assert pricing.usage_cost("claude-sonnet-5-5", no_split) == pytest.approx(2.50)   # counts as 5-minute
    fast = {"input_tokens": m, "output_tokens": m, "cache_read_input_tokens": m, "speed": "fast"}
    assert pricing.usage_cost("claude-opus-5-5", fast) == pytest.approx(8 + 40 + 0.40)
    assert pricing.usage_cost("claude-opus-4-7", fast) == pytest.approx(5 + 25 + 0.50)  # no fast mode: standard
    geo = {"input_tokens": m, "inference_geo": "us"}
    assert pricing.usage_cost("claude-sonnet-4-6", geo) == pytest.approx(3.3)
    assert pricing.usage_cost("claude-sonnet-4-5", geo) == pytest.approx(3.0)            # pre-4.6: no multiplier
    assert pricing.usage_cost("gpt-9", {"input_tokens": m}) is None
    assert pricing.context_of({"input_tokens": 5, "cache_read_input_tokens": 90, "cache_creation_input_tokens": 10}) == 105


def _assistant(mid, model, usage, ts="2026-09-29T10:00:00Z"):
    return json.dumps({"type": "assistant", "timestamp": ts,
                       "message": {"id": mid, "model": model, "usage": usage, "content": []}}) + "\n"


def test_run_cost_and_last_turn_context(tmp_path: Path):
    path = tmp_path / "t.jsonl"
    u1 = {"input_tokens": 1000, "output_tokens": 100, "cache_read_input_tokens": 50_000}
    u2 = {"input_tokens": 2000, "output_tokens": 200, "cache_read_input_tokens": 90_000}
    path.write_text(_assistant("m1", "claude-opus-5-5", u1) + _assistant("m1", "claude-opus-5-5", u1)
                    + _assistant("m2", "claude-opus-5-5", u2)
                    + _assistant("m3", "<synthetic>", {"input_tokens": 0, "output_tokens": 0}), encoding="utf-8")
    run = tr.read_run(path)
    expected = (pricing.usage_cost("claude-opus-5-5", u1) + pricing.usage_cost("claude-opus-5-5", u2))
    assert run.cost == pytest.approx(expected)
    assert run.context_tokens == 0          # the synthetic last message read nothing
    path.write_text(_assistant("m1", "claude-opus-5-5", u1) + _assistant("m2", "claude-opus-5-5", u2), encoding="utf-8")
    assert tr.read_run(path).context_tokens == 92_000   # the last turn, not the 143k sum
    path.write_text(_assistant("x", "mystery-model", u1), encoding="utf-8")
    run = tr.read_run(path)
    assert run.cost is None and run.unpriced == {"mystery-model"}


def test_meter_counts_this_run_only_and_reads_incrementally(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / ".orkcraft").mkdir(parents=True)
    transcript = tmp_path / "s.jsonl"
    run_id = telemetry.new_run_id()
    started = dt.datetime(2026, 9, 29, 10, 0, tzinfo=dt.timezone.utc)
    u = {"input_tokens": 1_000_000, "output_tokens": 0, "cache_read_input_tokens": 0}
    transcript.write_text(
        _assistant("old", "claude-sonnet-5-5", u, ts="2026-09-29T09:00:00Z")   # resumed history: not this run
        + _assistant("new", "claude-sonnet-5-5", u, ts="2026-09-29T10:05:00Z"), encoding="utf-8")
    log = repo / ".orkcraft" / "sessions.jsonl"
    log.write_text(
        json.dumps({"harness": "claude", "session": "s", "run": run_id, "terminal": "new:claude:1",
                    "transcript": str(transcript)}) + "\n"
        + json.dumps({"harness": "claude", "session": "z", "run": "0" * 32, "terminal": "x",
                      "transcript": str(transcript)}) + "\n"                # another run
        + json.dumps({"harness": "agy", "session": "g", "run": run_id, "terminal": "new:agy:1"}) + "\n",
        encoding="utf-8")
    t = telemetry.Telemetry(repo, run_id, started)
    snap = t.refresh()
    assert snap.spent_usd == pytest.approx(2.0)          # one Sonnet 5.5 message, $2 / MTok
    assert snap.sessions == 1 and snap.unpriced == {"agy"}
    assert snap.context_by_terminal == {"new:claude:1": 1_000_000}
    with transcript.open("a", encoding="utf-8") as f:
        f.write(_assistant("more", "claude-sonnet-5-5", u, ts="2026-09-29T10:06:00Z"))
        f.write('{"type": "assistant", "partial')          # an unfinished line is left for later
    assert t.refresh().spent_usd == pytest.approx(4.0)
    assert t._meters[str(transcript)].offset < transcript.stat().st_size


# -- the ledger by purpose (docs/design/simplify.md §2) --------------------------------------------

def test_every_call_says_what_it_was_for_and_is_kept_on_disk(tmp_path: Path):
    telemetry.keep_ledger(tmp_path)
    telemetry.charge(0.02, "claude -p haiku", purpose="build", tokens=1200, building="hall", model="haiku")
    with telemetry.tagged("review", "board"):
        telemetry.charge(0.03, "claude agent")                   # the caller's purpose and building
        with telemetry.tagged("check"):
            telemetry.charge(None, "agy agent")                  # inner purpose, the outer building
    telemetry.charge(0.01, "codex worker", purpose="nonsense")   # not on the list: the caller's, else work
    lines = telemetry.calls(tmp_path)
    assert [(c["purpose"], c["building"]) for c in lines] == [
        ("build", "hall"), ("review", "board"), ("check", "board"), ("work", "")]
    assert lines[0]["tokens"] == 1200 and lines[0]["model"] == "haiku" and lines[0]["usd"] == 0.02
    assert lines[2]["usd"] is None and "transcript" not in lines[0]
    assert set(telemetry.PURPOSES) == {"work", "sort", "plan", "review", "check", "ingest", "answer", "look",
                                       "retro", "build", "chat"}


def test_by_purpose_sums_the_last_week_and_its_buildings(tmp_path: Path):
    telemetry.keep_ledger(tmp_path)
    old = {"at": (dt.datetime.now().astimezone() - dt.timedelta(days=8)).isoformat(), "purpose": "work",
           "building": "x", "usd": 9.0, "tokens": 9}
    (tmp_path / telemetry.CALLS).parent.mkdir(parents=True)
    (tmp_path / telemetry.CALLS).write_text(json.dumps(old) + "\nnot json\n", encoding="utf-8")
    telemetry.charge(0.2, "a", purpose="work", tokens=10, building="mill")
    telemetry.charge(0.5, "b", purpose="work", tokens=5, building="forge")
    telemetry.charge(0.1, "c", purpose="sort", building="mill")
    telemetry.charge(None, "d", purpose="sort", building="mill")
    week = telemetry.by_purpose(tmp_path)
    assert [(g["purpose"], round(g["usd"], 2), g["tokens"], g["calls"], g["unpriced"]) for g in week] == [
        ("work", 0.7, 15, 2, 0), ("sort", 0.1, 0, 2, 1)]
    assert [b["building"] for b in week[0]["buildings"]] == ["forge", "mill"]
    assert telemetry.by_purpose(tmp_path / "none") == []

