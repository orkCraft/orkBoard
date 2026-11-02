"""A task's steps (docs/specs/129-a-tasks-steps.md H1, decisions §207): the same on Claude Code, Codex and Antigravity. The readers of
each tool on recorded output (tests/fixtures/steps/), the cleaning, the merge, the rule in every working prompt, the exclude line, a
landing that never takes the steps file, the snapshot's shape, Claude Code's result still read from stream-json, the look at a
running task and the check command. No real tool runs here."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from orkboard.realm import board_map, harnesses, jobs, steps_check, task_steps, task_steps_run, tool_run
from orkboard.realm.idea_git import IdeaGit

from tests.test_idea_runner import git, plan_of, runner_of, town, wait_idle  # noqa: F401  (the fixture repository)

FIX = Path(__file__).parent / "fixtures" / "steps"


def text(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def texts(items: list[dict]) -> list[tuple[str, str]]:
    return [(i["text"], i["state"]) for i in items]


# -- cleaning and the file ------------------------------------------------------------------------

def test_clean_keeps_six_cuts_text_on_a_word_and_lets_one_step_be_now():
    got = task_steps.read_file(FIX / "ork_steps_messy.json")
    assert len(got) == task_steps.MAX_STEPS
    assert all(len(i["text"]) <= task_steps.MAX_TEXT for i in got)
    assert got[0] == {"text": "Read the whole of the project's sources…", "state": "done"}      # cut on a word, with an ellipsis
    assert [i["state"] for i in got] == ["done", "now", "next", "next", "next", "next"]     # a second `now`, an unknown state: next
    assert texts(got)[1:4] == [("a", "now"), ("b", "next"), ("c", "next")] and "" not in [i["text"] for i in got]


def test_clean_takes_the_other_tools_words_for_a_state():
    got = task_steps.clean([{"content": "x", "status": "completed"}, {"text": "y", "completed": False}, {"step": "z", "status": "in_progress"},
                            {"text": "w", "completed": True}, 5, None])
    assert texts(got) == [("x", "done"), ("y", "next"), ("z", "now"), ("w", "done")]
    assert task_steps.clean("not a list") == [] and task_steps.cut("a" * 100).endswith("…") and len(task_steps.cut("a" * 100)) == 40


def test_the_file_is_read_cleaned_and_a_half_written_one_is_not_a_list():
    assert texts(task_steps.read_file(FIX / "ork_steps_midway.json"))[1] == ("Add double() to calc.py", "now")
    assert task_steps.read_file(FIX / "ork_steps_half.json") is None
    assert task_steps.read_file(FIX / "no-such-file.json") is None


# -- the readers, per tool ---------------------------------------------------------------------------

def feed_in_pieces(reader, raw: str, size: int = 37) -> list[list[dict]]:
    """The updates a reader gives when the output arrives in arbitrary pieces (a line cut in two by a chunk)."""
    got = []
    for n in range(0, len(raw), size):
        found = reader.feed(raw[n:n + size], now=100.0 + n)
        if found:
            got.append(found)
    return got


def test_claude_todowrite_events_give_the_steps_and_the_step_now_reads_by_its_active_form():
    reader = task_steps.reader_for("claude")
    got = feed_in_pieces(reader, text("claude_stream.jsonl"))
    assert [sum(1 for i in g if i["state"] == "done") for g in got] == [0, 1, 2, 3, 4]
    assert texts(got[0])[0] == ("Reading calc.py and test_calc.py", "now")       # activeForm for the one now
    assert texts(got[1])[:2] == [("Read calc.py and test_calc.py", "done"), ("Adding double() to calc.py", "now")]
    assert all(i["state"] == "done" for i in got[-1]) and len(got[-1]) == 4
    assert reader.command == "python -m pytest -q test_calc.py" and reader.command_at > 0


def test_codex_todo_list_items_give_the_steps_from_started_through_completed():
    reader = task_steps.reader_for("codex")
    got = feed_in_pieces(reader, text("codex_exec_todo.jsonl"))
    assert [sum(1 for i in g if i["state"] == "done") for g in got] == [0, 1, 2, 3, 4]
    assert texts(got[0]) == [("Read calc.py and test_calc.py", "now"), ("Add double() to calc.py", "next"),
                             ("Write a test for double()", "next"), ("Run the tests", "next")]
    assert texts(got[2])[2] == ("Write a test for double()", "now") and all(i["state"] == "done" for i in got[-1])
    assert reader.command == "python -m pytest -q"                                  # the shell wrapper is taken off


def test_codex_update_plan_is_read_where_a_version_prints_it():
    got = task_steps.reader_for("codex").feed(text("codex_exec_plan.jsonl"))
    assert texts(got) == [("Add double() to calc.py", "done"), ("Write its test", "now"), ("Run the tests", "next")]


def test_agy_prints_one_envelope_at_the_end_so_there_is_nothing_to_read_but_the_file():
    reader = task_steps.reader_for("agy")
    assert reader.feed(text("agy_envelope.json")) is None and reader.command == ""
    assert task_steps.reader_for("claude").feed(text("agy_envelope.json")) is None and task_steps.reader_for("codex").feed(text("agy_envelope.json")) is None
    assert harnesses.get("agy").outcome(text("agy_envelope.json"))[0].startswith("Added double()")        # and its result is read as before


def test_a_reader_ignores_what_is_not_an_event():
    for tool in ("claude", "codex"):
        assert task_steps.reader_for(tool).feed("not json\n{broken\n[1, 2]\n\n") is None


# -- what it is doing, and the merge -------------------------------------------------------------------

def make_worktree(tmp_path: Path) -> Path:
    steps_check.scratch(tmp_path / "w")
    return tmp_path / "w"


def test_the_doing_line_is_the_file_changed_last_or_the_command_run_last(tmp_path):
    repo = make_worktree(tmp_path)
    assert task_steps.activity(repo) == ""
    (repo / "lobby.ts").write_text("x")
    assert task_steps.activity(repo) == "edits lobby.ts"
    (repo / task_steps.FILE).write_text("[]")                                         # the steps file is never what it is doing
    assert task_steps.activity(repo) == "edits lobby.ts"
    later = time.time() + 5
    assert task_steps.activity(repo, "/bin/zsh -lc 'python -m pytest -q'", later) == "runs the tests"
    assert task_steps.activity(repo, "make build", later) == "runs make"
    assert task_steps.activity(repo, "make build", 1.0) == "edits lobby.ts"           # the file came after the command
    assert task_steps.activity(repo, "scripts/ci.sh --fast", later, gate="scripts/ci.sh") == "runs the tests"
    assert task_steps.activity(None, "FOO=1 npm test", later) == "runs the tests"


def test_the_merge_takes_the_file_then_the_tools_list_then_what_it_is_doing():
    file, todo = task_steps.read_file(FIX / "ork_steps_midway.json"), task_steps.reader_for("codex").feed(text("codex_exec_plan.jsonl"))
    got = task_steps.merge(file, todo, "edits calc.py")
    assert got == {"items": file, "now": 1, "done": 1, "total": 4, "source": "file", "doing": "edits calc.py"}
    assert task_steps.merge(None, todo, "")["source"] == "todo" and task_steps.merge([], todo, "")["source"] == "todo"       # an empty file fills in
    only = task_steps.merge(None, None, "runs the tests")
    assert only == {"items": [], "now": -1, "done": 0, "total": 0, "source": "activity", "doing": "runs the tests"}
    assert task_steps.merge(None, None, "") is None


def test_a_task_done_keeps_its_last_steps_all_done_and_one_with_only_a_doing_line_keeps_none():
    got = task_steps.finished(task_steps.merge(task_steps.read_file(FIX / "ork_steps_midway.json"), None, "runs the tests"))
    assert got["done"] == got["total"] == 4 and got["now"] == -1 and got["doing"] == "" and {i["state"] for i in got["items"]} == {"done"}
    assert task_steps.finished(task_steps.merge(None, None, "edits a.py")) is None and task_steps.finished(None) is None


# -- the rule in every working prompt ------------------------------------------------------------------

def test_every_tools_working_prompt_carries_the_steps_rule(town, tmp_path):
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    prompt = runner._prompt("demo", plan, plan["tasks"][0])
    rule = task_steps.RULE
    assert ".ork-steps.json" in rule and "at most six" in rule and '"state": "done" | "now" | "next"' in rule and "at the worktree's root" in rule
    assert rule in prompt
    claude = jobs.work_cmd("claude", prompt, tmp_path, root=town.repo)
    agy = jobs.work_cmd("agy", prompt, tmp_path, root=town.repo)
    assert prompt in claude and prompt in agy                                           # an argument of its argv
    assert tool_run.harness_stdin("codex", prompt) == prompt                           # Codex reads it on stdin
    assert "-" in jobs.work_cmd("codex", prompt, tmp_path, root=town.repo)[:4] and prompt not in jobs.work_cmd("codex", prompt, tmp_path, root=town.repo)
    for argv in (claude, agy):
        assert rule in argv[argv.index(prompt)]


def test_a_working_run_of_claude_code_streams_its_events(tmp_path):
    argv = jobs.work_cmd("claude", "p", tmp_path, root=tmp_path)
    assert argv[argv.index("--output-format") + 1] == "stream-json" and "--verbose" in argv
    assert harnesses.get("agy").work("p", tmp_path)[harnesses.get("agy").work("p", tmp_path).index("--output-format") + 1] == "json"       # agy has no stream


def test_claudes_result_is_still_read_from_a_stream_json_working_run():
    out = text("claude_stream.jsonl")
    got = tool_run.result_of("claude", out)
    assert got[0] == "Added double() and its test; both pass." and got[1] == pytest.approx(0.0412) and got[3] == "s-7"
    assert got[2] == 34 + 5200 + 18000 + 640
    assert harnesses.claude_error(out) == "" and harnesses.usage_split(out) == {"in": 5234, "out": 640, "cache_read": 18000}
    cut_off = "".join(out.splitlines(keepends=True)[:-1])                                # a stream that never reached its result
    assert tool_run.result_of("claude", cut_off)[0] == ""
    failed = out.replace('"is_error": false', '"is_error": true').replace('"subtype": "success"', '"subtype": "error_during_execution"')
    assert harnesses.claude_error(failed)


# -- the exclude line and the landing ------------------------------------------------------------------

def test_the_steps_file_is_in_the_worktrees_exclude_and_a_commit_of_what_is_left_leaves_it_out(town):
    ig = IdeaGit(town.repo)
    ig.ensure_branch("dev")
    path, _branch = ig.prepare("demo", "k1", "dev")
    exclude = Path(git(path, "rev-parse", "--git-path", "info/exclude"))
    exclude = exclude if exclude.is_absolute() else path / exclude
    assert exclude.read_text().splitlines().count(".ork-steps.json") == 1
    ig.prepare("demo", "k2", "dev")
    assert exclude.read_text().splitlines().count(".ork-steps.json") == 1             # said once
    (path / task_steps.FILE).write_text(text("ork_steps_done.json"))
    (path / "a.txt").write_text("a")
    assert ig.commit_left(path, "the work") is True
    assert git(path, "ls-files").splitlines().count("a.txt") == 1 and task_steps.FILE not in git(path, "ls-files")
    (path / task_steps.FILE).write_text("[]")
    assert ig.dirty(path) is False                                                       # the file alone is no change


def test_landing_never_takes_the_steps_file_not_the_stray_nor_the_committed_one(town):
    ig = IdeaGit(town.repo)
    ig.ensure_branch("dev")
    path, branch = ig.prepare("demo", "k1", "dev")
    (path / "a.txt").write_text("a")
    ig.commit_left(path, "k1: a")
    (path / task_steps.FILE).write_text(text("ork_steps_done.json"))
    git(path, "add", "-f", task_steps.FILE)                                             # the worker committed it anyway
    git(path, "-c", "user.name=W", "-c", "user.email=w@x", "commit", "-qm", "oops: the steps")
    assert task_steps.FILE in git(path, "ls-tree", "-r", "--name-only", "HEAD")
    ig.land(path, branch, "dev", push=False)
    assert task_steps.FILE not in git(town.repo, "ls-tree", "-r", "--name-only", "dev") and "a.txt" in git(town.repo, "ls-tree", "-r", "--name-only", "dev")
    assert not (path / task_steps.FILE).exists()
    path2, branch2 = ig.prepare("demo", "k2", "dev")                                    # a stray file where the exclude line is missing
    git(path2, "rev-parse", "--git-path", "info/exclude")
    exclude = Path(git(path2, "rev-parse", "--git-path", "info/exclude"))
    exclude = exclude if exclude.is_absolute() else path2 / exclude
    exclude.write_text("")
    (path2 / task_steps.FILE).write_text("[]")
    (path2 / "b.txt").write_text("b")
    git(path2, "add", "b.txt")
    git(path2, "-c", "user.name=W", "-c", "user.email=w@x", "commit", "-qm", "k2: b")
    ig.land(path2, branch2, "dev", push=False)                                          # not "left uncommitted changes"
    assert task_steps.FILE not in git(town.repo, "ls-tree", "-r", "--name-only", "dev")


def test_a_file_of_that_name_the_project_has_of_its_own_is_left_alone(town):
    (town.repo / task_steps.FILE).write_text('["its own"]')
    git(town.repo, "add", "-f", task_steps.FILE)
    git(town.repo, "commit", "-qm", "its own")
    ig = IdeaGit(town.repo)
    ig.ensure_branch("dev")
    path, branch = ig.prepare("demo", "k1", "dev")
    (path / "a.txt").write_text("a")
    ig.commit_left(path, "k1: a")
    ig.land(path, branch, "dev", push=False)
    assert task_steps.FILE in git(town.repo, "ls-tree", "-r", "--name-only", "dev")


# -- the snapshot --------------------------------------------------------------------------------------

def test_the_snapshot_gives_a_task_at_work_or_checked_its_steps_in_the_shape(tmp_path):
    d = tmp_path / "ideas" / "demo"
    d.mkdir(parents=True)
    kept = task_steps.merge(task_steps.read_file(FIX / "ork_steps_midway.json"), None, "edits calc.py")
    (d / "k1.steps.json").write_text(json.dumps(kept))
    (d / "k2.steps.json").write_text(json.dumps(task_steps.merge(None, None, "runs the tests")))
    (d / "k3.steps.json").write_text("{not json")
    for state in ("running", "testing", "review"):
        got = board_map.steps_of(tmp_path, "demo", {"id": "k1", "state": state})["steps"]
        assert got == kept and set(got) == {"items", "now", "done", "total", "source", "doing"}
        assert all(set(i) == {"text", "state"} for i in got["items"])
    done = board_map.steps_of(tmp_path, "demo", {"id": "k1", "state": "merged"})["steps"]
    assert done["done"] == done["total"] == 4 and done["now"] == -1 and {i["state"] for i in done["items"]} == {"done"}
    assert board_map.steps_of(tmp_path, "demo", {"id": "k2", "state": "running"})["steps"]["source"] == "activity"
    assert board_map.steps_of(tmp_path, "demo", {"id": "k2", "state": "merged"}) == {}              # what it was doing is not kept for a done task
    for t in ({"id": "k1", "state": "waiting"}, {"id": "k1", "state": "ready"}, {"id": "k1", "state": "failed"}, {"id": "k3", "state": "running"},
              {"id": "k9", "state": "running"}):
        assert board_map.steps_of(tmp_path, "demo", t) == {}                                       # absent when nothing is known


# -- the look at a running task ------------------------------------------------------------------------

def test_the_look_keeps_the_steps_the_file_first_and_clears_what_an_earlier_round_left(tmp_path):
    repo = make_worktree(tmp_path)
    kept = tmp_path / "k1.steps.json"
    (repo / task_steps.FILE).write_text(text("ork_steps_done.json"))                  # left by the round before
    kept.write_text("{}")
    seen = []
    watch = task_steps_run.Watch("claude", repo, kept, every=60, on_change=seen.append)
    watch.start()
    assert not (repo / task_steps.FILE).exists() and not kept.exists()
    watch.feed(text("claude_stream.jsonl").split("\n")[1] + "\n")                  # the tool's list: the first TodoWrite
    watch.poll()
    assert seen[-1]["source"] == "todo" and seen[-1]["total"] == 4 and json.loads(kept.read_text()) == seen[-1]
    (repo / task_steps.FILE).write_text(text("ork_steps_midway.json"))
    watch.poll()
    assert seen[-1]["source"] == "file" and seen[-1]["done"] == 1                       # the file wins
    count = len(seen)
    watch.poll()
    assert len(seen) == count                                                          # nothing changed: nothing kept again
    (repo / task_steps.FILE).write_text(text("ork_steps_half.json"))                   # half written: the last good list stays
    watch.poll()
    assert seen[-1]["source"] == "file" and seen[-1]["done"] == 1
    (repo / task_steps.FILE).write_text(text("ork_steps_done.json"))
    watch.stop()
    assert json.loads(kept.read_text())["done"] == 4 and task_steps.read_kept(tmp_path, "k1")["source"] == "file"


def test_the_file_is_read_only_when_its_mtime_changed(tmp_path, monkeypatch):
    repo = make_worktree(tmp_path)
    reads = []
    real = task_steps.read_file
    monkeypatch.setattr(task_steps, "read_file", lambda p: reads.append(p) or real(p))
    watch = task_steps_run.Watch("agy", repo, tmp_path / "k1.steps.json", every=60)
    (repo / task_steps.FILE).write_text(text("ork_steps_midway.json"))
    for _ in range(4):
        watch.poll()
    assert len(reads) == 1
    (repo / task_steps.FILE).write_text(text("ork_steps_done.json"))
    watch.poll()
    assert len(reads) == 2


def test_the_look_thread_polls_by_itself_and_ends_with_the_run(tmp_path):
    repo = make_worktree(tmp_path)
    seen = []
    watch = task_steps_run.Watch("agy", repo, tmp_path / "k1.steps.json", every=0.05, on_change=seen.append)
    watch.start()
    (repo / task_steps.FILE).write_text(text("ork_steps_midway.json"))
    end = time.time() + 5
    while not seen and time.time() < end:
        time.sleep(0.05)
    assert seen and seen[0]["source"] == "file"
    watch.stop()
    assert not any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate())


def test_a_tools_output_is_handed_on_as_it_is_written_not_at_the_end(tmp_path):
    got, times = [], []
    code = ("import sys, time\n"
            "print('{\"type\": \"thread.started\"}', flush=True)\n"
            "time.sleep(1.3)\n"
            "print('{\"type\": \"turn.completed\"}', flush=True)\n")
    started = time.monotonic()

    def waiting(proc):
        proc.wait()

    rc, out, _err = tool_run.run_proc([sys.executable, "-c", code], tmp_path, {}, None, waiting,
                                      on_output=lambda chunk: (got.append(chunk), times.append(time.monotonic() - started)))
    assert rc == 0 and "turn.completed" in out
    assert "".join(got) == out                                                          # all of it, once
    assert got[0].startswith('{"type": "thread.started"}') and times[0] < 1.2 < times[-1]


def test_a_reader_that_fails_never_stops_the_run(tmp_path):
    def boom(_chunk):
        raise RuntimeError("no")
    rc, out, _ = tool_run.run_proc([sys.executable, "-c", "print('x')"], tmp_path, {}, None, lambda p: p.wait(), on_output=boom)
    assert rc == 0 and out == "x\n"


# -- the runner ----------------------------------------------------------------------------------------

def test_a_task_that_runs_keeps_its_steps_beside_its_log_and_stop_all_ends_the_look(town, monkeypatch):
    monkeypatch.setattr(task_steps_run, "EVERY_S", 0.1)
    real = jobs.run_work

    def works(tool, prompt, workdir, cancel, **kw):
        (Path(workdir) / task_steps.FILE).write_text(text("ork_steps_midway.json"))      # the worker keeps its steps
        return real(tool, prompt, workdir, cancel, **kw)
    monkeypatch.setattr(jobs, "run_work", works)
    plan_of(town, [{"id": "k1"}])
    runner, events = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    kept = json.loads((town.state / "ideas" / "demo" / "k1.steps.json").read_text())
    assert kept["source"] == "file" and kept["total"] == 4
    assert not (town.repo / task_steps.FILE).exists() and task_steps.FILE not in git(town.repo, "ls-tree", "-r", "--name-only", "main")
    assert not any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate())
    node = board_map.steps_of(town.state, "demo", runner.plan("demo")["tasks"][0])["steps"]
    assert node["done"] == node["total"] == 4                                          # merged: all done


def test_stop_all_ends_the_look_at_a_task_that_is_running(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "*=slow")
    monkeypatch.setattr(task_steps_run, "EVERY_S", 0.1)
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    end = time.time() + 20
    while not any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate()) and time.time() < end:
        time.sleep(0.05)
    assert any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate())        # the look runs while the task does
    runner.stop_all()
    assert wait_idle(runner, timeout=30)["state"] == "failed"
    end = time.time() + 10
    while any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate()) and time.time() < end:
        time.sleep(0.05)
    assert not any(t.name.startswith("steps-") and t.is_alive() for t in threading.enumerate())


# -- orkboard steps-check -------------------------------------------------------------------------------

def fake_work(file_steps: list[list[dict]], tool: str = "claude"):
    """A stand-in for `jobs.run_work`: the worker rewrites its steps file once for each list, with a look between."""
    def work(_tool, _prompt, workdir, _cancel, **kw):
        for items in file_steps:
            (Path(workdir) / task_steps.FILE).write_text(json.dumps(items))
            time.sleep(0.25)
        return "done", None, None, ""
    return work


def says(**kw):
    out = []
    code = steps_check.run(kw.pop("tool", "claude"), out=out.append, every=0.05, **kw)
    return code, out


def test_steps_check_prints_each_update_and_says_ok_when_the_last_list_is_all_done():
    mid, done = json.loads(text("ork_steps_midway.json")), json.loads(text("ork_steps_done.json"))
    code, out = says(yes=True, work=fake_work([mid, done]))
    assert code == 0 and "ok" in out
    updates = [ln for ln in out if ln.startswith("  +")]
    assert len(updates) >= 2 and " file " in updates[0] and " 4/4 " in updates[-1]


def test_steps_check_is_not_ok_with_one_update_or_a_list_not_done():
    mid = json.loads(text("ork_steps_midway.json"))
    code, out = says(yes=True, work=fake_work([mid]))
    assert code == 1 and any(ln.startswith("not ok") and "fewer than two" in ln for ln in out)
    done = json.loads(text("ork_steps_done.json"))
    code, out = says(yes=True, work=fake_work([done[:1], mid]))
    assert code == 1 and any("not all" in ln for ln in out)


def test_steps_check_asks_before_spending_and_says_plainly_when_the_tool_is_missing(monkeypatch):
    out = []
    asked = []
    assert steps_check.run("claude", out=out.append, ask=lambda q: asked.append(q) or "n", work=fake_work([])) == 2
    assert asked and out[-1] == "not run"
    monkeypatch.setenv("PATH", "/nonexistent")
    out.clear()
    assert steps_check.run("codex", yes=True, out=out.append) == 2 and "not installed" in out[0] and "codex" in out[0]
    assert steps_check.run("pi", yes=True, out=out.append) == 2


def test_steps_check_says_when_the_tool_is_not_signed_in():
    from orkboard.realm import tool_errors

    def refuses(*_a, **_kw):
        raise tool_errors.ToolError("claude", "Not logged in · Please run /login", 1)
    code, out = says(yes=True, work=refuses)
    assert code == 2 and "could not run the task" in out[-1]


def test_the_command_is_on_the_command_line():
    from orkboard.gui import board_cli
    assert "steps-check" in board_cli.WORDS
    with pytest.raises(SystemExit):
        board_cli.run(["steps-check", "--tool", "nope"])
    with pytest.raises(SystemExit):
        board_cli.run(["steps-check"])
    seen = []
    import orkboard.realm.steps_check as sc
    orig = sc.run
    sc.run = lambda tool, yes=False, **kw: seen.append((tool, yes)) or 0
    try:
        assert board_cli.run(["steps-check", "--tool", "agy", "--yes"]) == 0
    finally:
        sc.run = orig
    assert seen == [("agy", True)]


def test_the_scratch_repository_is_a_tiny_project_with_a_commit(tmp_path):
    repo = steps_check.scratch(tmp_path / "r")
    assert sorted(git(repo, "ls-files").split()) == ["calc.py", "test_calc.py"] and git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=repo, capture_output=True).returncode == 0
