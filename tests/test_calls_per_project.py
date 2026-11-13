"""Each model call is kept and charged where it belongs (docs/specs/37-board-and-line.md §8): a project's keeper and runner
in that project's day log and ledger whether it is shown or not, concurrent calls of two projects each in their own place."""
from __future__ import annotations

import datetime as dt
import threading
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import call_log
from orkboard.sources import telemetry
from tests.claude_stub import Stub, stream


@pytest.fixture
def stub(tmp_path, monkeypatch):
    return Stub(tmp_path, monkeypatch)


@pytest.fixture
def two(tmp_path, fake_repo, stub):
    import shutil
    a, b = fake_repo, tmp_path / "other"
    shutil.copytree(fake_repo, b)
    host = Orkboard(a)
    host.projects.open(b, show=False)
    yield host, a, b
    host.close()


def _logged(root: Path) -> list[dict]:
    return [line for path in sorted((root / call_log.DAYS).rglob(call_log.LINES)) for line in call_log.read(path.parent)]


def test_two_projects_calling_at_once_each_keep_their_own(two, stub):
    host, a, b = two
    assert host.repo_root == a                                   # `a` is shown; `b` is open, not shown
    result = stream([], text="{}", cost=0.25)[-1:]                # one JSON envelope: a read, a work, a call
    stub.answer(result, sleep=0.6, keep=True)                    # every call answers, slowly: they overlap
    keeper_a = host.projects._find(a).ideas.keeper
    runner_b = host.projects._find(b).ideas.runner(need=True)
    calls = [
        threading.Thread(target=lambda: keeper_a._claude("laborer", "sort the Board of a")),
        threading.Thread(target=lambda: runner_b._session("idea", "t1", b, threading.Event(), "",
                                                          {"ORKCRAFT_ORC": "ideas/idea-t1", "ORKCRAFT_TASK": "t1"},
                                                          "work in b", "", {"cost": None, "tokens": None})),
    ]
    for t in calls:
        t.start()
    for t in calls:
        t.join(15)
    assert len(stub.calls()) == 2

    in_a, in_b = _logged(a), _logged(b)
    assert [(x["who"], x["mode"]) for x in in_a] == [("keeper", "read")]
    assert [(x["who"], x["mode"]) for x in in_b] == [("idea-t1", "work")]
    today = dt.date.today().isoformat()
    assert call_log.read(call_log.day_folder(b, today, "ideas"))[0]["task"] == "t1"

    assert [(x["building"], x["usd"]) for x in telemetry.calls(a)] == [("board", 0.25)]
    assert [(x["building"], x["usd"]) for x in telemetry.calls(b)] == [("ideas", 0.25)]


def test_a_call_no_one_placed_goes_to_the_shown_project_and_a_kept_block_wins(tmp_path):
    a, b, bench = tmp_path / "a", tmp_path / "b", tmp_path / "bench"
    call_log.keep_days(a)
    telemetry.keep_ledger(a)
    try:
        call_log.record({"ORKCRAFT_ORC": "board/keeper"}, "read", "claude", "", "p", "", "", 0, 1.0)
        telemetry.charge(0.1, "claude reader")
        with call_log.of_project(b):
            call_log.record({"ORKCRAFT_ORC": "board/keeper"}, "read", "claude", "", "p", "", "", 0, 1.0)
            telemetry.charge(0.2, "claude reader")
            with call_log.kept(bench / "calls", "building"):      # a kept block: every call is its own
                call_log.record({"ORKCRAFT_ORC": "board/keeper"}, "read", "claude", "", "p", "", "", 0, 1.0)
            seen = []
            other = threading.Thread(target=lambda: seen.append(telemetry.ledger_now()))   # another thread: not placed
            other.start()
            other.join()
    finally:
        call_log.keep_days(None)
    assert len(_logged(a)) == 1 and len(_logged(b)) == 1 and len(call_log.read(bench / "calls")) == 1
    assert [x["usd"] for x in telemetry.calls(a)] == [0.1] and [x["usd"] for x in telemetry.calls(b)] == [0.2]
    assert seen == [telemetry.ledger_of(a)]
