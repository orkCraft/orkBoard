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


def test_outside_a_bench_run_no_call_is_kept(tmp_path, tool):
    jobs.run_work("claude", "do it", tmp_path, threading.Event())
    assert not list(tmp_path.rglob(call_log.LINES))


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


def test_a_call_that_fails_is_kept_too(tmp_path, tool):
    tool.update(code=1, out="not logged in")
    with call_log.kept(tmp_path / "calls", "bare"), pytest.raises(RuntimeError):
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
    [line] = call_log.read(tmp_path / "calls")
    assert (line["side"], line["who"], line["mode"], line["code"], line["tokens"]) == ("bare", "", "read", 1, None)


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


def test_the_usage_is_read_from_an_envelope_or_the_last_event():
    assert call_log.usage_of(ENVELOPE)["output_tokens"] == 100
    lines = "\n".join(json.dumps(e) for e in ({"type": "turn.completed", "usage": {"input_tokens": 1}},
                                              {"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 2}}))
    assert call_log.usage_of(lines) == {"input_tokens": 7, "output_tokens": 2}
    assert call_log.usage_of("plain text") == {}


# -- the day logs (realm/day_log.py; Orkboard's are gui/board_host.py `BoardLogs`) ------------------------------

@pytest.fixture(autouse=True)
def no_day_log():
    call_log.keep_days(None)
    yield
    call_log.keep_days(None)


def test_outside_a_bench_run_a_call_goes_to_its_buildings_day(tmp_path, tool):
    call_log.keep_days(tmp_path)
    jobs.run_work("claude", "fix it", tmp_path, threading.Event(), env={"ORKCRAFT_ORC": "pool/Grub"})
    jobs.run_read("claude", "nobody's", tmp_path, threading.Event())
    today = dt.date.today().isoformat()
    lines = call_log.read(call_log.day_folder(tmp_path, today, "pool"))
    assert [(x["who"], x["side"], x["mode"]) for x in lines] == [("Grub", "", "work")]
    assert [x["who"] for x in call_log.read(call_log.day_folder(tmp_path, today, call_log.TOWN))] == ["agent"]


def test_a_claude_call_keeps_how_it_worked_from_its_transcript(tmp_path, tool, monkeypatch):
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path / "claude"))
    from orkboard.sources import sessions
    work = tmp_path / "wt"
    work.mkdir()
    transcript = sessions.claude_projects_dir(work) / "s1.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text('{"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": "hmm"}]}}\n')
    with call_log.kept(tmp_path / "calls", "building"):
        jobs.run_work("claude", "fix it", work, threading.Event())                   # its session from the output
    [first] = call_log.read(tmp_path / "calls")
    assert first["session"] == "s1" and '"thinking": "hmm"' in call_log.raw(tmp_path / "calls", first)["trail"]
    assert call_log.trail("claude", "../s1", work) == ""                         # a session id, never a path
    assert call_log.trail("codex", "s1", work) == ""                             # its output holds how it went


def _day(root, day, building, asked=False):
    folder = call_log.day_folder(root, day, building)
    folder.mkdir(parents=True)
    (folder / call_log.LINES).write_text("{}\n")
    if asked:
        (folder / day_log.ASKED).touch()
    return folder


def test_a_day_nobody_asked_for_and_nobody_disliked_is_cleared_the_next_morning(tmp_path):
    today = dt.date(2026, 10, 12)
    kept = [_day(tmp_path, "2026-10-11", "asked", asked=True), _day(tmp_path, "2026-10-11", "disliked"),
            _day(tmp_path, "2026-10-12", "today")]
    gone = [_day(tmp_path, "2026-10-11", "plain"), _day(tmp_path, "2026-09-20", "old", asked=True)]
    removed = day_log.clear(tmp_path, today, lambda b, day: b == "disliked" and day == "2026-10-11")
    assert sorted(removed) == ["2026-09-20/old", "2026-10-11/plain"]
    assert all(f.is_dir() for f in kept) and not any(f.exists() for f in gone)
    assert not (tmp_path / call_log.DAYS / "2026-09-20").exists()
    assert day_log.days(tmp_path, "asked") == ["2026-10-11"]


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


def test_a_one_off_answer_is_kept_with_what_it_was_for(tmp_path, monkeypatch):
    import subprocess as sp
    from orkboard.sources import telemetry
    call = lambda h, prompt, model: sp.CompletedProcess([], 0, ENVELOPE, "")      # noqa: E731
    with call_log.kept(tmp_path / "calls", "building"), telemetry.tagged("sort", "tower"):
        assert tool_run.ask("claude", "sort these letters", "haiku", call=call)[0] == "done"
    [line] = call_log.read(tmp_path / "calls")
    assert (line["who"], line["purpose"], line["mode"], line["model"], line["tokens"]) == \
        ("claude -p", "sort", "ask", "haiku", 5000)
    assert call_log.raw(tmp_path / "calls", line)["prompt"] == "sort these letters"


# -- the logs kept for analysis, a period as one zip (realm/analytics.py) ------------------------------------------------

def test_kept_for_analysis_every_day_stays_a_month(tmp_path):
    today = dt.date(2026, 10, 12)
    kept = [_day(tmp_path, "2026-10-11", "plain"), _day(tmp_path, "2026-09-20", "older")]
    gone = _day(tmp_path, "2026-09-01", "too_old")
    assert day_log.clear(tmp_path, today, lambda b, day: False, keep=True) == ["2026-09-01/too_old"]
    assert all(f.is_dir() for f in kept) and not gone.exists()


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
    """Orkboard keeps the day logs always (gui/board_host.py `BoardLogs`) and its server gives a period as one zip;
    Orkline's switch for them and its clearing by dislikes are the town's (gui/town_settings.py, gui/day_logs.py)."""
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


def test_cost_once_takes_the_sessions_last_total_off_and_never_goes_below_nothing():
    assert tool_run.cost_once(0.77, 0.68) == 0.09
    assert tool_run.cost_once(0.30, None) == 0.30 and tool_run.cost_once(None, 0.5) is None
    assert tool_run.cost_once(0.5, 0.9) == 0.0


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


def test_a_call_that_is_not_a_claude_read_stream_has_no_reads_and_a_work_call_none_at_all(tmp_path, tool):
    with call_log.kept(tmp_path / "calls", "building"), call_log.bounded(2):
        jobs.run_read("claude", "a recording of before", tmp_path, threading.Event())       # one JSON object: no events to count
        tool["out"] = _stream("/a", "/b", "/c")
        jobs.run_work("claude", "work", tmp_path, threading.Event())
    old, work = call_log.read(tmp_path / "calls")
    assert "reads" not in old and old["bound"] == 2 and "over" not in old                   # the line is as it was, and says its bound
    assert not {"reads", "bound", "over", "bare"} & set(work)
    assert call_log.totals([old, work])[0]["calls"] == 2                                    # every reader of lines reads either


def test_a_claude_read_calls_line_names_the_flags_that_kept_the_persons_servers_and_skills_out(tmp_path, tool, monkeypatch):
    from orkboard.realm import harness_claude
    monkeypatch.setattr(harness_claude, "cli_has", lambda h, flag: flag in ("--strict-mcp-config", "--mcp-config", "--disable-slash-commands"))
    with call_log.kept(tmp_path / "calls", "building"):
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
        jobs.run_work("claude", "work", tmp_path, threading.Event())
    monkeypatch.setattr(harness_claude, "cli_has", lambda h, flag: False)
    with call_log.kept(tmp_path / "calls", "building"):
        jobs.run_read("claude", "read it", tmp_path, threading.Event())
    bare, work, before = call_log.read(tmp_path / "calls")
    assert bare["bare"] == ["mcp", "skills"] and "bare" not in work and "bare" not in before


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


def test_the_floor_command_prints_the_last_seven_days_of_a_project(tmp_path, capsys):
    today = dt.date.today()
    for ago, line in ((0, _kept(1, True, 0.04, 5_000)), (6, _kept(1, False, 0.20, 25_000)), (7, _kept(1, False, 9.0, 999_999))):
        folder = call_log.day_folder(tmp_path, (today - dt.timedelta(days=ago)).isoformat(), "board")
        folder.mkdir(parents=True)
        (folder / call_log.LINES).write_text(json.dumps(line) + "\n")
    assert call_log.main(["floor", str(tmp_path)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("before") and "1 calls" in out[0] and "25000 tokens" in out[0] and "$0.2000" in out[0]
    assert out[1].startswith("after") and "1 calls" in out[1] and "5000 tokens" in out[1] and "$0.0400" in out[1]
    assert call_log.main(["floor"]) == 2 and call_log.main([]) == 2
    assert len(call_log.week(tmp_path, 7)) == 2 and len(call_log.week(tmp_path, 8)) == 3 and call_log.week(tmp_path / "none") == []


def test_a_recorded_read_of_before_the_one_json_object_still_plays_back_and_reads(tmp_path):
    """A cassette recorded before spec 97 holds the single JSON envelope; the read argv now asks for stream-json, and the reader takes both."""
    calls = tmp_path / "calls"
    calls.mkdir()
    (calls / "building-1-keeper.json").write_text(json.dumps({"line": {"mode": "read", "purpose": "plan", "code": 0},
                                                              "prompt": "read it", "stdout": ENVELOPE, "stderr": ""}))
    with call_log.replaying(calls):
        got = jobs.run_read("claude", "read it", tmp_path, threading.Event())
    assert got == ("done", 0.03, 5000, "s1") and jobs.last_usage() == {"in": 900, "out": 100, "cache_read": 4000}
