"""Spec 168 G3 (decisions §283.16.14–15, §277): the three days the history book dates a goal by, `agreed` (default), `done` and `in main`, and the history the host reads for the grid. Real git in a temporary repository, no model."""
from __future__ import annotations

from pathlib import Path

import pytest

from orkboard.realm import chronicle, history_day, ideas, spec_sections
from tests.test_chronicle import LOG, tag, through  # noqa: F401
from tests.test_commit_goal import git, repo, state  # noqa: F401  (the fixture)


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


def test_a_goal_is_dated_by_each_of_the_three_days():
    got = history_day.dates("2026-11-01T09:00:00", "2026-10-30", ["2026-11-03T10:00:00", "2026-11-04T08:00:00"], {"at": "2026-11-06T12:00:00", "by": "gate"})
    assert got == {"agreed": "2026-11-01", "done": "2026-11-04", "main": "2026-11-06"}, "agreed by the confirmation, done by the newest merged task, in main by the flag"


def test_a_goal_missing_one_date_keeps_the_others_and_says_none_for_it():
    assert history_day.dates("", "", [], None) == {"agreed": "", "done": "", "main": ""}
    only_flag = history_day.dates("", "2026-10-30", [None, "not a day"], {"at": "2026-11-06T12:00:00", "by": "gate"})
    assert only_flag == {"agreed": "2026-10-30", "done": "", "main": "2026-11-06"}, "the decision's log day stands in for the confirmation; a gate flag is not a done day"
    assert history_day.dates("", "", ["2026-11-03"], None) == {"agreed": "", "done": "2026-11-03", "main": ""}


def test_a_goal_done_where_there_is_no_gate_is_done_the_day_of_its_flag():
    got = history_day.dates("", "2026-10-26", [], {"at": "2026-10-26T00:00:00", "by": "done"})
    assert got == {"agreed": "2026-10-26", "done": "2026-10-26", "main": "2026-10-26"}


def test_the_history_gives_each_goal_its_three_days_its_gist_and_the_versions(repo, pages):
    tag(repo, "v0.1", "2026-10-12")
    a = through(pages, repo, "Seat kept", "2026-10-21", 2)
    b = through(pages, repo, "No decision", "2026-10-22")
    rec = spec_sections.record(state(repo), a)
    rec["decision"] = {**rec["decision"], "confirmed": True, "confirmed_at": "2026-10-11T08:00:00"}
    spec_sections.save_record(state(repo), a, rec)
    log = repo / "d.md"
    log.write_text(LOG)
    got = chronicle.history(state(repo), pages, repo, log, "")
    by = {g["idea"]: g for g in got["goals"]}
    assert got["kind"] == "tag" and got["versions"] == [{"id": "v:v0.1", "name": "v0.1", "day": "2026-10-12"}]
    assert by[a]["dates"]["agreed"] == "2026-10-11" and by[a]["dates"]["main"] == "2026-10-21" and by[a]["title"] == "Seat kept" and by[a]["gist"]
    assert by[b]["dates"] == {"agreed": "", "done": "", "main": "2026-10-22"}, "a goal with no decision has no agreed day"
    assert [g["idea"] for g in got["goals"]] == [b, a], "newest in main first"


def test_the_history_through_a_party_keeps_the_goals_its_party_worked_on(repo, pages):
    a = through(pages, repo, "Plain", "2026-10-21")
    log = repo / "d.md"
    log.write_text(LOG)
    assert [g["idea"] for g in chronicle.history(state(repo), pages, repo, log, "general")["goals"]] == [a]
    assert chronicle.history(state(repo), pages, repo, log, "design")["goals"] == []
