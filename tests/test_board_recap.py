"""Spec 42 A (docs/specs/42-coming-back.md §1.1, Tests → A): `board_recap.build` on a fixture log and ledgers, and
`idea_spend.between`. Code, no model."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from orkboard.realm import board_recap, event_log, idea_spend, ideas
from tests.test_commit_goal import repo  # noqa: F401  (the fixture of the night's tests: a project on `dev`)

NOW = dt.datetime(2026, 10, 20, 12, 0).astimezone()
SINCE = NOW - dt.timedelta(hours=9)


def _at(hours_ago: float) -> dt.datetime:
    return NOW - dt.timedelta(hours=hours_ago)


def _log(root: Path, event: str, hours_ago: float, **fields) -> None:
    row = event_log.line(event, at=_at(hours_ago), **fields)
    target = event_log.path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _ledger(state: Path, slug: str, hours_ago: float, cost, naive: bool = True) -> None:
    folder = state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    at = _at(hours_ago)
    row = {"at": (at.replace(tzinfo=None) if naive else at).isoformat(timespec="seconds"), "step": "task", "task": "k1", "round": 1,
           "role": "grunt", "cost": cost}
    with (folder / idea_spend.FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _rows(*items, goals=("offline",)):
    return {"ideas": [{"slug": s, "short": s.title(), "title": f"Title of {s}", "track": "offline", "state": st} for s, st in items],
            "tracks": [{"slug": g, "short": g.title(), "title": f"{g.title()} goal"} for g in goals]}


def _plan(state: Path, slug: str, *tasks) -> None:
    folder = state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "tasks": [{"id": i, "title": t, "state": s} for i, t, s in tasks]}))


@pytest.fixture
def where(tmp_path):
    root, state = tmp_path / "wiki", tmp_path / "state"
    root.mkdir()
    state.mkdir()
    return root, state


def test_each_list_comes_from_its_events(where):
    root, state = where
    _log(root, "task_state", 8, idea="queue", task="k1", state="merged", was="review", round=1)
    _log(root, "task_state", 7, idea="queue", task="k2", state="merged", was="review", round=2)
    _log(root, "task_state", 6, idea="csv", task="k1", state="merged", was="review", round=1)
    _log(root, "task_state", 12, idea="csv", task="k2", state="merged", was="review", round=1)           # before the period
    _log(root, "task_state", 5, idea="gone", task="k1", state="merged", was="review", round=1)           # a deleted idea
    _log(root, "goal_accepted", 4, goal="offline", met=False, by="Product manager")
    _log(root, "goal_accepted", 3, goal="offline", met=True, by="Product manager")                        # the last per goal
    _log(root, "goal_accepted", 3, goal="deleted", met=True, by="Growth")
    _log(root, "night_run", 5, drafted=2, started=1, refreshed=0, proposed=1)
    _log(root, "night_run", 4, drafted=0, started=0, refreshed=0, proposed=1)
    _log(root, "proposal_made", 4, idea="retry", goal="offline")
    _log(root, "proposal_made", 4, idea="taken", goal="offline")
    _log(root, "task_state", 2, idea="table", task="k1", state="failed", was="running", round=1)
    _log(root, "task_state", 2, idea="fixed", task="k1", state="failed", was="running", round=1)
    _plan(state, "table", ("k1", "The table", "failed"))
    _plan(state, "fixed", ("k1", "Fixed since", "review"))
    rows = _rows(("queue", "working"), ("csv", "done"), ("retry", "proposed"), ("taken", "ready"), ("table", "working"), ("fixed", "working"))
    got = board_recap.build(root, state, SINCE, NOW, rows)
    assert got["hours"] == 9 and got["into"] == "dev" and got["nights"] == 0 and got["waits"] == {"you": 0, "review": 0}
    assert got["merged"]["tasks"] == 4 and got["merged"]["first_time"] == 3          # the deleted idea's merge is counted, not listed
    assert got["merged"]["ideas"] == [
        {"slug": "queue", "short": "Queue", "title": "Title of queue", "goal": "offline", "done": False},
        {"slug": "csv", "short": "Csv", "title": "Title of csv", "goal": "offline", "done": True}]
    assert got["flags"] == [{"goal": "offline", "short": "Offline", "title": "Offline goal", "met": True, "by": "Product manager"}]
    assert got["night"] == {"drafted": 2, "started": 1, "refreshed": 0, "proposed": 2}
    assert got["proposed"] == [{"slug": "retry", "short": "Retry", "title": "Title of retry", "goal": "offline"}]
    assert got["failed"] == [{"slug": "table", "short": "Table", "title": "Title of table", "task": "The table"}]
    assert got["empty"] is False


def test_a_goals_flag_reads_in_main_beside_a_partys_old_flag_and_a_flag_alone_makes_a_card_spec_50(where):
    root, state = where
    rows = _rows(("queue", "working"), ("csv", "done"))
    assert board_recap.build(root, state, SINCE, NOW, rows)["empty"] is True
    _log(root, "idea_flagged", 5, idea="csv", goal="offline", by="gate", tasks=3, first_time=2, usd=None, days=2)
    _log(root, "idea_flagged", 4, idea="csv", goal="offline", by="done", tasks=3, first_time=2, usd=None, days=2)       # never twice, but a log may say so
    _log(root, "idea_flagged", 4, idea="deleted", goal="offline", by="gate", tasks=1, first_time=1, usd=None, days=1)   # a goal the Board lost
    _log(root, "idea_flagged", 12, idea="queue", goal="offline", by="gate", tasks=1, first_time=1, usd=None, days=1)    # before the period
    got = board_recap.build(root, state, SINCE, NOW, rows)
    assert got["flags"] == [{"goal": "offline", "idea": "csv", "short": "Csv", "title": "Title of csv", "met": True, "by": "gate"}]
    assert got["empty"] is False
    _log(root, "goal_accepted", 3, goal="offline", met=True, by="Product manager")
    old, new = board_recap.build(root, state, SINCE, NOW, rows)["flags"]
    assert old == {"goal": "offline", "short": "Offline", "title": "Offline goal", "met": True, "by": "Product manager"}      # the old line keeps its fields
    assert new["idea"] == "csv" and "idea" not in old


# -- Spec 121 D: the night (docs/specs/121-the-day-the-morning-and-the-night.md §5.2) --------------------------------------------------------------

def _night_app(repo: Path) -> None:
    from tests.test_commit_goal import commit
    commit(repo, "package.json", json.dumps({"dependencies": {"react-router-dom": "6"}}))
    commit(repo, "src/App.jsx", 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\n'
                                'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /></Routes>;\n')
    commit(repo, "src/Home.jsx", 'export default () => <Link to="/cart">Cart</Link>;\n')
    commit(repo, "src/Cart.jsx", "export default () => null;\n")


def _clock(repo: Path, hours_ago: float, now: dt.datetime, event: str, **fields) -> None:
    row = event_log.line(event, at=now - dt.timedelta(hours=hours_ago), **fields)
    target = event_log.path(repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def test_the_night_is_the_recap_cut_to_the_window_goals_with_their_screens_failures_with_reasons_reverts_and_red_checks(repo):
    from tests.test_commit_goal import commit, land, state
    _night_app(repo)
    s, now = state(repo), dt.datetime.now().astimezone() + dt.timedelta(minutes=1)
    since = now - dt.timedelta(hours=8)
    land(repo, "cart-total", "k1", {"src/Cart.jsx": "export default () => <b>total</b>;\n"})
    land(repo, "dark-mode", "k1", {"notes/dark.md": "words\n"})                                  # a goal that changed no screen
    commit(repo, "src/Home.jsx", 'export default () => <Link to="/cart">Cart!</Link>;\n', 'Revert "the cart link"')
    _clock(repo, 6, now, "task_state", idea="cart-total", task="k1", state="merged", was="review", round=1)
    _clock(repo, 5, now, "task_state", idea="dark-mode", task="k1", state="merged", was="review", round=1)
    _clock(repo, 30, now, "task_state", idea="old-goal", task="k1", state="merged", was="review", round=1)       # before the window
    _clock(repo, 4, now, "task_state", idea="export", task="k1", state="failed", was="running", round=1, error="Tests would not pass")
    _clock(repo, 3, now, "task_state", idea="mended", task="k1", state="failed", was="running", round=1)
    _clock(repo, 3.5, now, "gate_ran", idea="table", task="k1", round=1, attempt=1, command="npm test", exit=1, verdict="red")
    _clock(repo, 2, now, "result_ready", idea="landed", task="k1", round=1, passed=0, failed=2, verdict="red")
    _clock(repo, 1, now, "gate_ran", idea="landed", task="k1", round=2, attempt=1, command="npm test", exit=0, verdict="green")      # its last gate stands
    for slug, tasks in (("export", [("k1", "Export", "failed")]), ("mended", [("k1", "Mended", "review")]),
                        ("table", [("k1", "The table", "review")]), ("landed", [("k1", "Landed", "merged")])):
        _plan(s, slug, *tasks)
    plan = ideas.plan(s, "export")
    plan["tasks"][0]["error"] = "Tests would not pass"
    (s / "ideas" / "export" / "plan.json").write_text(json.dumps(plan))
    rows = _rows(("cart-total", "working"), ("dark-mode", "done"), ("old-goal", "done"), ("export", "working"), ("mended", "working"), ("table", "working"), ("landed", "working"))
    got = board_recap.night(repo, s, since, now, rows)
    assert got["into"] == "dev" and got["hours"] == 8 and got["empty"] is False and got["play"] is None
    assert got["goals"] == [{"slug": "cart-total", "short": "Cart-Total", "title": "Title of cart-total", "goal": "offline", "done": False,
                             "screens": [{"screen": "cart", "name": "Cart", "path": "/cart"}]},
                            {"slug": "dark-mode", "short": "Dark-Mode", "title": "Title of dark-mode", "goal": "offline", "done": True, "screens": []}]
    assert got["failed"] == [{"slug": "export", "short": "Export", "title": "Title of export", "task": "Export", "why": "Tests would not pass"}]
    assert got["checks"] == [{"slug": "table", "short": "Table", "title": "Title of table", "task": "The table", "check": "npm test"}]
    assert [r["subject"] for r in got["reverts"]] == ['Revert "the cart link"'] and len(got["reverts"][0]["sha"]) == 7


def test_the_night_starts_at_the_last_windows_open_or_the_devices_last_look_whichever_is_later():
    window = {"night": "01:00-07:00"}
    morning = dt.datetime(2026, 10, 21, 9, 0).astimezone()
    one = dt.datetime(2026, 10, 21, 1, 0).astimezone()
    assert board_recap.night_start(window, morning) == one
    assert board_recap.night_start(window, dt.datetime(2026, 10, 21, 3, 0).astimezone()) == one, "the night in progress counts"
    assert board_recap.night_start(window, dt.datetime(2026, 10, 21, 0, 30).astimezone()) == dt.datetime(2026, 10, 20, 1, 0).astimezone()
    assert board_recap.night_since(window, morning) == one
    assert board_recap.night_since(window, morning, dt.datetime(2026, 10, 21, 6, 0).astimezone()) == dt.datetime(2026, 10, 21, 6, 0).astimezone()      # a look after the window opened
    assert board_recap.night_since(window, morning, dt.datetime(2026, 10, 20, 23, 0).astimezone()) == one                                             # a look before it
    crossing = {"night": "22:00-06:00"}
    assert board_recap.night_start(crossing, dt.datetime(2026, 10, 21, 9, 0).astimezone()) == dt.datetime(2026, 10, 20, 22, 0).astimezone()
    assert board_recap.night_start(crossing, dt.datetime(2026, 10, 21, 23, 0).astimezone()) == dt.datetime(2026, 10, 21, 22, 0).astimezone()
    assert board_recap.night_start({"night": "bad"}, morning) is None and board_recap.night_start({}, morning) is None
    assert board_recap.night_since({}, morning) == morning - board_recap.NO_WINDOW
