"""The Test bench's log of model calls (realm/call_log.py): kept only inside a bench run, a line and the call each."""
from __future__ import annotations

import datetime as dt
import io
import json
import threading
import urllib.error
import urllib.request
import zipfile

import pytest

from orkboard.realm import call_log, day_log, jobs, tool_run

ENVELOPE = json.dumps({"result": "done", "total_cost_usd": 0.03, "session_id": "s1",
                       "usage": {"input_tokens": 900, "output_tokens": 100, "cache_read_input_tokens": 4000}})


@pytest.fixture
def tool(monkeypatch):
    seen = {}

    def run_proc(cmd, cwd, env, stdin, wait, harness=""):
        seen["env"] = env
        return seen.get("code", 0), seen.get("out", ENVELOPE), "a warning"

    monkeypatch.setattr(tool_run, "run_proc", run_proc)
    return seen


def test_a_call_in_a_bench_run_keeps_its_line_and_itself(tmp_path, tool):
    with call_log.kept(tmp_path / "calls", "building"):
        jobs.run_work("claude", "fix the tests", tmp_path, threading.Event(), "sonnet",
                      env={"ORKCRAFT_ORC": "pool/Grub", "SECRET_KEY": "x"})
    jobs.run_work("claude", "after the run", tmp_path, threading.Event())          # no longer kept
    [line] = call_log.read(tmp_path / "calls")
    assert (line["side"], line["who"], line["mode"], line["tool"], line["model"]) == \
        ("building", "Grub", "work", "claude", "sonnet")
    assert (line["code"], line["cost"], line["tokens"]) == (0, 0.03, 5000)
    assert line["usage"] == {"input_tokens": 900, "output_tokens": 100, "cache_read_input_tokens": 4000}
    raw = call_log.raw(tmp_path / "calls", line)
    assert raw["prompt"] == "fix the tests" and raw["stdout"] == ENVELOPE and raw["stderr"] == "a warning"
    assert "SECRET_KEY" not in (tmp_path / "calls" / call_log.LINES).read_text()


def test_the_calls_add_up_by_side_who_and_purpose(tmp_path, tool):
    with call_log.kept(tmp_path / "calls", "building"):
        for who in ("Grub", "Grub", "steward"):
            jobs.run_work("claude", "x", tmp_path, threading.Event(), env={"ORKCRAFT_ORC": f"pool/{who}"})
    with call_log.kept(tmp_path / "calls", "bare"):                   # a second block goes on numbering
        jobs.run_work("claude", "x", tmp_path, threading.Event())
    lines = call_log.read(tmp_path / "calls")
    assert [x["n"] for x in lines] == [1, 2, 3, 4] and len({x["raw"] for x in lines}) == 4
    rows = {(t["side"], t["who"]): t for t in call_log.totals(lines)}
    assert rows[("building", "Grub")]["calls"] == 2 and rows[("building", "Grub")]["tokens"] == 10000
    assert rows[("building", "Grub")]["usage"]["input_tokens"] == 1800
    assert rows[("bare", "")]["calls"] == 1


# -- the day logs (realm/day_log.py; Orkboard's are gui/board_host.py `BoardLogs`) ------------------------------

@pytest.fixture(autouse=True)
def no_day_log():
    call_log.keep_days(None)
    yield
    call_log.keep_days(None)


def _day(root, day, building, asked=False):
    folder = call_log.day_folder(root, day, building)
    folder.mkdir(parents=True)
    (folder / call_log.LINES).write_text("{}\n")
    if asked:
        (folder / day_log.ASKED).touch()
    return folder


def test_a_buildings_day_is_one_zip_and_asking_for_it_keeps_it(tmp_path, tool):
    call_log.keep_days(tmp_path)
    jobs.run_work("claude", "fix the tests", tmp_path, threading.Event(), env={"ORKCRAFT_ORC": "pool/Grub"})
    today = dt.date.today().isoformat()
    data = day_log.pack(tmp_path, "pool", today, "Agent pool",
                        [{"at": f"{today}T10:00:00", "action": "hire", "orc": "Grub", "why": "first"}])
    z = zipfile.ZipFile(io.BytesIO(data))
    assert sorted(z.namelist()) == ["README.md", "calls.jsonl", "calls/001-Grub.json", "decisions.jsonl"]
    readme = z.read("README.md").decode()
    assert "# Agent pool" in readme and "Grub · work: 1 call" in readme and "hire: Grub — first" in readme
    assert json.loads(z.read("calls/001-Grub.json"))["prompt"] == "fix the tests"
    assert (call_log.day_folder(tmp_path, today, "pool") / day_log.ASKED).exists()


# -- the logs kept for analysis, a period as one zip (realm/analytics.py) ------------------------------------------------

def test_a_period_is_one_zip_with_each_day_added_up(tmp_path, tool):
    from orkboard.realm import analytics
    call_log.keep_days(tmp_path)
    jobs.run_work("claude", "fix the tests", tmp_path, threading.Event(), env={"ORKCRAFT_ORC": "pool/Grub"})
    jobs.run_work("claude", "again", tmp_path, threading.Event(), env={"ORKCRAFT_ORC": "pool/Grub"})
    today = dt.date.today().isoformat()
    _day(tmp_path, "2026-01-02", "board")
    decided = {("pool", today): [{"at": f"{today}T10:00:00", "action": "follow-up", "orc": "Grub", "why": "tests red"}]}
    disliked = {("pool", today): [{"ts": f"{today}T11:00:00", "note": "too slow"}]}
    data = analytics.pack(tmp_path, [today, "2026-01-02"], {"pool": "Agent pool"},
                          lambda b, d: decided.get((b, d), []), lambda b, d: disliked.get((b, d), []))
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    assert {f"{today}/pool/calls.jsonl", f"{today}/pool/calls/001-Grub.json", f"{today}/pool/decisions.jsonl",
            f"{today}/pool/dislikes.jsonl", "2026-01-02/board/calls.jsonl", "README.md", "summary.json"} <= set(names)
    s = json.loads(z.read("summary.json"))
    [pool] = [r for d in s["days"] for r in d["buildings"] if r["id"] == "pool"]
    assert (pool["calls"], pool["reworks"], pool["dislikes"], pool["title"]) == (2, 1, 1, "Agent pool")
    assert s["by_building"]["pool"]["days"] == 1 and s["total"]["calls"] == 3     # the board's one line too
    readme = z.read("README.md").decode()
    assert "Agent pool (`pool`, 1 day): 2 calls" in readme and "1 rework, 1 👎" in readme
    assert "Grub · work: 2 calls" in readme and "decisions: follow-up 1" in readme
    assert (call_log.day_folder(tmp_path, today, "pool") / day_log.ASKED).exists()


def test_orkboard_keeps_its_logs_and_serves_a_period(fake_repo, tool):
    """Orkboard keeps the day logs always (gui/board_host.py `BoardLogs`) and its server gives a period as one zip."""
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    host = Orkboard()                                                    # the start screen: no project, no logs
    try:
        server = Server(host)
        thread = server.start_thread()
        try:
            url = f"{server.origin}/api/analytics?days=7&t={server.token}"
            with pytest.raises(urllib.error.HTTPError):                     # nothing kept yet
                urllib.request.urlopen(url, timeout=5)
            assert host.command("projects.open", {"path": str(fake_repo)}) == {"ok": True, "git": True}
            jobs.run_work("claude", "hall work", fake_repo, threading.Event(), env={"ORKCRAFT_ORC": "town_hall/Chief"})
            with urllib.request.urlopen(url, timeout=5) as r:
                assert "orkcraft-analytics-" in r.headers["Content-Disposition"]
                z = zipfile.ZipFile(io.BytesIO(r.read()))
            today = dt.date.today().isoformat()
            assert f"{today}/town_hall/calls/001-Chief.json" in z.namelist()
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(f"{server.origin}/api/analytics?days=7&t=nope", timeout=5)
        finally:
            server.stop()
            thread.join(10)                      # it closes the host: not at once with the test
    finally:
        host.close()


def test_a_resumed_sessions_line_keeps_the_tools_figure_and_its_own_cost(tmp_path, tool):
    """Spec 86 §1: a resumed Claude session reports its running total; the line keeps it and the call's own difference."""
    with call_log.kept(tmp_path / "calls", "building"):
        jobs.run_work("claude", "first", tmp_path, threading.Event())                                    # fresh: no `cost_own`
        jobs.run_work("claude", "again", tmp_path, threading.Event(), resume="s1", before_cost=0.02)     # total 0.03, 0.02 before
        jobs.run_work("claude", "once more", tmp_path, threading.Event(), resume="s1", before_cost=0.05)   # the tool said less: never below 0
    first, second, third = call_log.read(tmp_path / "calls")
    assert first["cost"] == 0.03 and "cost_own" not in first
    assert second["cost"] == 0.03 and second["cost_own"] == 0.01
    assert third["cost"] == 0.03 and third["cost_own"] == 0.0
    assert call_log.totals([first, second, third])[0]["cost"] == 0.04          # the sum counts each session once


# -- spec 97 part A: a read call's reads, its bound and its bare floor on its line; the floor measured ---------------------

def _stream(*files, searches=0):
    events = [{"type": "system", "subtype": "init", "session_id": "s2"}]
    for n, path in enumerate(files):
        events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"r{n}", "name": "Read",
                                                                     "input": {"file_path": path}}]}})
    for n in range(searches):
        events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"g{n}", "name": "Grep",
                                                                     "input": {"pattern": "x"}}]}})
    events.append({"type": "result", "subtype": "success", "result": "{}", "total_cost_usd": 0.05, "session_id": "s2",
                   "usage": {"input_tokens": 10, "output_tokens": 50, "cache_creation_input_tokens": 3000},
                   "permission_denials": [{"tool_name": "Read", "tool_input": {"file_path": "uv.lock"}}]})
    return "\n".join(json.dumps(e) for e in events)


def test_a_read_calls_line_says_what_it_read_its_bound_and_when_it_went_over(tmp_path, tool):
    tool["out"] = _stream(str(tmp_path / "a.py"), str(tmp_path / "src" / "b.py"), str(tmp_path / "a.py"), "/etc/hosts", searches=2)
    with call_log.kept(tmp_path / "calls", "building"), call_log.bounded(2):
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
    [line] = call_log.read(tmp_path / "calls")
    assert line["reads"] == {"files": 3, "searches": 2, "paths": ["a.py", "src/b.py", "/etc/hosts"], "denied": 1}
    assert (line["bound"], line["over"]) == (2, True)
    assert (line["session"], line["cost"], line["usage"]["cache_creation_input_tokens"]) == ("s2", 0.05, 3000)
    tool["out"] = _stream(str(tmp_path / "a.py"))
    with call_log.kept(tmp_path / "again", "building"), call_log.bounded(1):                # at the bound is not over
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
    with call_log.kept(tmp_path / "again", "building"):                                    # no bound set: none on the line
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
    first, second = call_log.read(tmp_path / "again")
    assert first["bound"] == 1 and "over" not in first and "bound" not in second and "over" not in second
    assert second["reads"]["files"] == 1


def _kept(n, bare, cost, made, purpose="plan", mode="read", tool_="claude", code=0, out=100):
    line = {"n": n, "mode": mode, "purpose": purpose, "tool": tool_, "code": code, "cost": cost,
            "usage": {"output_tokens": out, "cache_creation_input_tokens": made}}
    return {**line, "bare": ["mcp", "skills"]} if bare else line


def test_the_floor_splits_a_keepers_one_turn_read_calls_by_bare_and_takes_the_medians():
    lines = [_kept(1, False, 0.30, 30_000), _kept(2, False, 0.20, 20_000), _kept(3, False, 0.10, 40_000),
             _kept(4, True, 0.06, 4_000), _kept(5, True, 0.04, 6_000, purpose="sort"),
             _kept(6, True, 0.50, 9_000, purpose="draft"), _kept(7, True, 0.50, 9_000, mode="work"),       # not a keeper's read
             _kept(8, True, 0.50, 9_000, tool_="codex"), _kept(9, True, 0.50, 9_000, code=1),             # not Claude's, not ended well
             _kept(10, True, 0.50, 9_000, out=5_000)]                                                      # not one turn
    got = call_log.floor(lines)
    assert got["before"] == {"calls": 3, "cache_creation_input_tokens": 30_000, "cost": 0.2}
    assert got["after"] == {"calls": 2, "cache_creation_input_tokens": 5_000, "cost": 0.05}
    assert call_log.floor([]) == {"before": {"calls": 0, "cache_creation_input_tokens": None, "cost": None},
                                  "after": {"calls": 0, "cache_creation_input_tokens": None, "cost": None}}


# -- spec 120 part E: a leader's call in Talk, measured before it is changed -------------------------------------------------

def _talk(n, at, idea, party, made=0, read=0, step="talk_round", code=0):
    """A keeper's Talk line: `at` seconds past a fixed minute, the goal, the party, what the call wrote to and read from the cache."""
    stamp = dt.datetime(2026, 11, 1, 9, 0, 0) + dt.timedelta(seconds=at)
    return {"n": n, "at": stamp.isoformat(timespec="seconds"), "mode": "read", "tool": "claude", "step": step, "idea": idea, "party": party, "code": code,
            "usage": {"cache_creation_input_tokens": made, "cache_read_input_tokens": read}}


def test_the_talk_floor_groups_a_goals_calls_into_rounds_and_says_which_wrote_the_cache_anew():
    lines = [_talk(1, 0, "g1", "product", made=9000), _talk(2, 1, "g1", "design", made=8000), _talk(3, 2, "g1", "tech", made=8500),               # a round: the first writes, the rest write again
             _talk(4, 3, "g2", "product", made=9000), _talk(5, 4, "g2", "tech", made=7000, read=1000),
             _talk(6, 400, "g1", "product", made=500, read=8000),                                                                                   # a second round of g1, Product's next call
             _talk(7, 401, "g1", "tech", made=500, read=7000),
             _talk(8, 5, "g1", "x", made=1, step="plan"), _talk(9, 6, "g1", "tech", made=9, code=1)]                                                 # not Talk's, not ended well
    got = call_log.talk_floor(lines)
    assert (got["calls"], got["goals"], got["rounds"]) == (7, 2, 3)                                                  # g1's two rounds (a gap of minutes between them) and g2's
    assert got["first"]["calls"] == 3 and got["first"]["wrote"] == 2 and got["first"]["read"] == 1                  # g1's first round and g2's begin by writing; g1's second begins by reading
    assert got["rest"]["calls"] == 4 and got["rest"]["wrote"] == 2 and got["rest"]["read"] == 2 and got["rest"]["cache_creation_input_tokens"] == 7500
    assert got["again"]["calls"] == 2 and got["again"]["read"] == 1                                                  # g2's Product and Tech, each within five minutes of its own call on g1

