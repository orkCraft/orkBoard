"""Today's events (docs/specs/49-one-window.md §2.2): `board_today.rows` on fixture log lines, and `ideas.today` on the log."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.realm import board_today, event_log, ideas

NOW = dt.datetime(2026, 10, 21, 15, 30).astimezone()
TITLES = {"ideas": {"sync": {"title": "Sync the queue", "goal": "offline"}, "csv": {"title": "CSV export", "goal": "reports"}},
          "goals": {"offline": "Work offline"},
          "tasks": {"sync": {"k1": "Queue writes", "k2": "Retry"}}}


def line(event: str, hours_ago: float = 1, **fields) -> dict:
    return event_log.line(event, at=NOW - dt.timedelta(hours=hours_ago), **fields)


def one(event: str, **fields) -> dict:
    (got,) = board_today.rows([line(event, 1, **fields)], TITLES)
    return got


def test_each_event_is_one_row_with_its_mark_tone_words_and_what_a_click_opens():
    k1 = {"idea": "sync", "task": "k1"}
    assert one("task_state", **k1, state="merged", was="review") == {
        "at": "14:30", "mark": "✓", "tone": "ok", "words": "merged into dev", "title": "Queue writes", "goal": "offline",
        "idea": "sync", "task": "k1", "open": {"kind": "result", "slug": "sync", "task": "k1"}}
    assert one("task_state", **k1, state="failed", was="running") == {
        "at": "14:30", "mark": "✗", "tone": "danger", "words": "failed", "title": "Queue writes", "goal": "offline",
        "idea": "sync", "task": "k1", "open": {"kind": "task", "slug": "sync", "task": "k1"}}
    for decision in ("back", "fix"):
        got = one("result_decided", **k1, decision=decision)
        assert (got["mark"], got["tone"], got["words"], got["title"]) == ("↺", "muted", "sent back", "Queue writes")
        assert got["open"] == {"kind": "result", "slug": "sync", "task": "k1"}
    got = one("task_state", **k1, state="dropped", was="failed")          # a failed task dropped has this row; one dropped at Review has `result_decided`'s
    assert (got["mark"], got["tone"], got["words"], got["open"]["kind"]) == ("✗", "muted", "dropped", "task")
    assert board_today.rows([line("task_state", **k1, state="dropped", was="review")], TITLES) == []
    got = one("result_decided", **k1, decision="drop")
    assert (got["mark"], got["tone"], got["words"], got["open"]["kind"]) == ("✗", "muted", "dropped", "task")
    assert one("plan_passed", idea="sync", tasks=2) == {
        "at": "14:30", "mark": "▸", "tone": "ink", "words": "the work started", "title": "Sync the queue", "goal": "offline",
        "idea": "sync", "task": "", "open": {"kind": "idea", "slug": "sync"}}
    got = one("idea_answered", idea="csv", answers=1)
    assert (got["mark"], got["tone"], got["words"], got["title"], got["goal"]) == ("·", "muted", "you answered", "CSV export", "reports")
    got = one("goal_answered", goal="offline", answers=2)
    assert (got["mark"], got["tone"], got["words"], got["title"], got["goal"], got["idea"]) == (
        "·", "muted", "you answered", "Work offline", "offline", "")
    assert got["open"] == {"kind": "goal", "slug": "offline"}
    taken, left = one("proposal_answered", idea="csv", take=True), one("proposal_answered", idea="csv", take=False)
    assert (taken["mark"], taken["words"], left["mark"], left["words"]) == ("+", "taken", "·", "left out")
    assert taken["tone"] == left["tone"] == "muted" and taken["open"] == {"kind": "idea", "slug": "csv"}
    assert one("gate_merged", commits=3, ideas=2, files=5, how="merge") == {
        "at": "14:30", "mark": "✓", "tone": "ok", "words": "dev merged into main", "title": "dev → main", "goal": "", "idea": "",
        "task": "", "open": {"kind": "gate", "slug": ""}}


# -- ideas.today ----------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_ideas_today_reads_the_log_since_midnight_and_joins_the_titles_from_the_board(host):
    root = host.ideas.root()
    goal = ideas.add_track(root, "Work offline")
    slug = host.command("ideas.add", {"text": "Sync the queue\nwith the server", "track": goal, "hold": True})["slug"]
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "tasks": [{"id": "k1", "title": "Queue writes", "state": "failed"}]})
    repo = Path(host.repo_root)
    now = dt.datetime.now().astimezone()
    old = event_log.line("task_state", at=board_today.midnight(now) - dt.timedelta(minutes=1), idea=slug, task="k1", state="failed")
    with event_log.path(repo).open("a", encoding="utf-8") as f:
        f.write(json.dumps(old) + "\n")
    event_log.record(repo, event_log.PLAN_PASSED, idea=slug, tasks=1)
    event_log.record(repo, event_log.TASK_STATE, idea=slug, task="k1", state="failed", was="running")
    event_log.record(repo, event_log.GOAL_ANSWERED, goal=goal, answers=1)
    event_log.record(repo, event_log.KEEPER_STATE, idea=slug, state="plan", was="planning")      # not a row
    event_log.record(repo, event_log.PLAN_PASSED, idea="gone", tasks=1)
    got = host.command("ideas.today")
    assert list(got) == ["events"]
    assert [(r["words"], r["title"], r["goal"]) for r in got["events"]] == [
        ("the work started", "gone", ""), ("you answered", "Work offline", goal), ("failed", "Queue writes", goal),
        ("the work started", "Sync the queue", goal)]                                  # newest first; yesterday's failure is not here
    assert all(len(r["at"]) == 5 and r["at"][2] == ":" for r in got["events"]) and BoardPhone.allowed(host, "ideas.today", {})


def test_a_goals_flag_is_a_row_that_opens_the_goal_spec_50():
    titles = {**TITLES, "ideas": {**TITLES["ideas"], "sync": {**TITLES["ideas"]["sync"], "short": "Sync queue"}}}
    (got,) = board_today.rows([line("idea_flagged", 1, idea="sync", goal="offline", by="gate", tasks=3, first_time=2, usd=None, days=2)], titles)
    assert got == {"at": "14:30", "mark": "⚑", "tone": "ok", "words": "is in main", "title": "Sync queue", "goal": "offline",
                   "idea": "sync", "task": "", "open": {"kind": "idea", "slug": "sync"}}
    assert one("idea_flagged", idea="csv", goal="reports", by="done")["title"] == "CSV export"          # no short name: its title
    gone = one("idea_flagged", idea="gone", goal="elsewhere", by="gate")
    assert (gone["title"], gone["goal"], gone["open"]) == ("gone", "elsewhere", {"kind": "idea", "slug": "gone"})   # a goal the Board lost reads as its slug
    assert board_today.rows([line("idea_flagged", 1, goal="offline", by="gate")], TITLES) == []        # no goal named: no row


def test_a_pick_asked_is_in_the_alert_tone_and_its_answer_is_what_was_picked_or_new_ones_spec_51():
    k1 = {"idea": "sync", "task": "k1"}
    assert one("pick_asked", **k1, n=3, media="image", round=1) == {
        "at": "14:30", "mark": "!", "tone": "alert", "words": "Pick one", "title": "Queue writes", "goal": "offline",
        "idea": "sync", "task": "k1", "open": {"kind": "pick", "slug": "sync", "task": "k1"}}
    got = one("pick_answered", **k1, key="B", note_chars=0, via="hand", seconds=12.0)
    assert (got["mark"], got["tone"], got["words"], got["title"]) == ("✓", "ok", "Picked B", "Queue writes")
    got = one("pick_answered", **k1, key=None, note_chars=14, via="drawer", seconds=40.0)
    assert (got["mark"], got["tone"], got["words"]) == ("↺", "muted", "New ones asked")
    assert board_today.rows([line("pick_asked", 1, idea="sync", n=2, media="text", round=1)], TITLES) == []        # no task, no row
