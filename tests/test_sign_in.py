"""A tool's own sign-in (docs/specs/45-sign-in.md, Tests → A): each tool's way (`realm/harnesses.py`), `tools.signed_in`,
a sign-in run with a fake process and clock (`realm/sign_in.py`), when a sign-in helps (`realm/tool_errors.py`), the host's
service (`core/sign_ins.py`), the work held for it and run again, the Map's wait and need, the Check row, the events and the
desktop-only commands. Nothing here starts a real tool, a browser or a terminal."""
from __future__ import annotations

import datetime as dt
import io
import json
import subprocess
import time
from types import SimpleNamespace

import pytest

from orkboard import settings, tools
from orkboard.core import bus as b
from orkboard.core.idea_keeper import IdeaKeeper
from orkboard.core.idea_runner import IdeaRunner
from orkboard.core.sign_ins import HOLD_H, SignInError, SignIns
from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import board_map, event_log, ideas, jobs, sign_in, tool_errors
from orkboard.realm.sign_in import CHECK_PROMPT, Outcome
from tests.test_idea_runner import plan_of, tasks_of, town  # noqa: F401  (the runner's repository and stub claude)

LOGIN = "Not logged in · Please run /login"


def login_error(harness: str = "claude", said: str = LOGIN) -> tool_errors.ToolError:
    return tool_errors.ToolError(harness, said, 1)


# -- each tool's own sign-in (§1) ---------------------------------------------------------------------------------


def fake_run(version="2.1.304", status=None, codex="Not logged in"):
    def run(argv, **kw):
        tail = argv[1:]
        if tail == ["--version"]:
            return subprocess.CompletedProcess(argv, 0, f"{version} (Claude Code)\n", "")
        if tail == ["auth", "status"]:
            if status is None:
                raise AssertionError("auth status asked")
            return subprocess.CompletedProcess(argv, 0 if status["loggedIn"] else 1, json.dumps(status), "")
        if tail == ["login", "status"]:
            return subprocess.CompletedProcess(argv, 1, "", codex)
        return subprocess.CompletedProcess(argv, 0, "", "")
    return run


def test_signed_in_tells_each_tool_without_a_model_call(tmp_path):
    home, which = tmp_path, lambda name: f"/bin/{name}"
    # Claude Code: `auth status` from 2.1.41 on, else its files
    assert tools.signed_in("claude", {}, fake_run(status={"loggedIn": True}), home, which) is True
    assert tools.signed_in("claude", {}, fake_run(status={"loggedIn": False}), home, which) is False
    assert tools.signed_in("claude", {}, fake_run("2.1.30"), home, which) is None            # too old to ask, no files
    (home / ".claude").mkdir()
    (home / ".claude" / ".credentials.json").write_text("{}")
    assert tools.signed_in("claude", {}, fake_run("2.1.30"), home, which) is True
    # Codex: auth.json, else `login status`
    assert tools.signed_in("codex", {}, fake_run(), home, which) is False
    (home / ".codex").mkdir()
    (home / ".codex" / "auth.json").write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {}}))
    assert tools.signed_in("codex", {}, fake_run(), home, which) is True
    # pi, Hermes Agent and Cursor read their files; Antigravity and an unknown tool cannot be told
    assert tools.signed_in("pi", {}, fake_run(), home, which) is None
    (home / ".pi" / "agent").mkdir(parents=True)
    (home / ".pi" / "agent" / "auth.json").write_text(json.dumps({"anthropic": {"type": "oauth"}}))
    assert tools.signed_in("pi", {}, fake_run(), home, which) is True
    assert tools.signed_in("hermes", {}, fake_run(), home, which) is None
    assert tools.signed_in("cursor", {"CURSOR_API_KEY": "k"}, fake_run(), home, which) is True
    assert tools.signed_in("agy", {}, fake_run(), home, which) is None
    assert tools.signed_in("nobody", {}, fake_run(), home, which) is None


# -- a sign-in run (§2) --------------------------------------------------------------------------------------------

class Proc:
    """A fake process: it says `lines`, and ends with `code` (None: still going) once polled `ends` times."""

    def __init__(self, argv, lines=(), code=None, **kw) -> None:
        self.argv, self.kw, self.stdout = argv, kw, io.StringIO("".join(f"{ln}\n" for ln in lines))
        self.returncode, self.pid, self.terminated = code, 99999, False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated, self.returncode = True, -15

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9


class Spawner:
    """`popen`: remembers every process it was asked to start."""

    def __init__(self, lines=(), code=None, fail=False) -> None:
        self.lines, self.code, self.fail, self.procs = lines, code, fail, []

    def __call__(self, argv, **kw):
        if self.fail:
            raise OSError("no such file")
        self.procs.append(Proc(argv, self.lines, self.code, **kw))
        return self.procs[-1]


class Clock:
    def __init__(self, now=1000.0) -> None:
        self.now = now

    def __call__(self):
        return self.now


def begin(tid, tmp_path, popen, platform="linux", signed=None, asked=None, clock=None, env=None, which=None):
    asked = [] if asked is None else asked

    def ask(harness, prompt, model=None):
        asked.append((harness, prompt, model))
        if isinstance(signed, Exception):
            raise signed

    return sign_in.start(tid, {"PATH": "/usr/bin", "HOME": str(tmp_path)} if env is None else env, tmp_path / "state",
                         platform, which or (lambda name: f"/bin/{name}"), popen, clock=clock or Clock(),
                         signed_in=lambda h, e=None: signed if isinstance(signed, bool) or signed is None else None,
                         ask=ask, home=tmp_path), asked


def test_the_browser_way_runs_the_tools_own_sign_in_in_the_home_folder_with_stdin_closed(tmp_path):
    spawn = Spawner(["Opening your browser…"])
    env = {"PATH": "/opt/bin:/usr/bin", "CLAUDE_CONFIG_DIR": "/work/claude"}
    run, _ = begin("claude", tmp_path, spawn, signed=True, env=env)
    proc = spawn.procs[0]
    assert proc.argv == ["/bin/claude", "auth", "login"] and proc.kw["cwd"] == str(tmp_path)
    assert proc.kw["stdin"] == subprocess.DEVNULL and proc.kw["env"]["CLAUDE_CONFIG_DIR"] == "/work/claude"
    assert proc.kw["env"]["PATH"] == "/opt/bin:/usr/bin" and run.by == "browser"
    assert run.poll() is None
    proc.returncode = 0
    assert run.poll() == Outcome("done")                             # exit 0 and signed in: told
    assert run.poll() == Outcome("done")                             # and the same afterwards


def test_the_log_holds_no_url_past_its_host(tmp_path):
    spawn = Spawner(["Open https://claude.com/cai/oauth/authorize?code=true&state=SECRETSTATE in a browser",
                     "callback http://localhost:5555/callback?code=abc123"], code=0)
    run, _ = begin("claude", tmp_path, spawn, signed=True)
    assert run.poll() == Outcome("done")
    text = (tmp_path / "state" / "sign-in" / "claude.log").read_text()
    assert "https://claude.com" in text and "http://localhost:5555" in text
    assert "SECRETSTATE" not in text and "abc123" not in text and "/callback" not in text
    assert sign_in.cut_urls("go https://a.example/x?y=1 now") == "go https://a.example now"


def test_told_by_signed_in_true_false_or_the_check(tmp_path):
    run, asked = begin("claude", tmp_path, Spawner(code=0), signed=False)
    assert run.poll() == Outcome("failed", "refused") and asked == []
    run, asked = begin("claude", tmp_path, Spawner(code=0), signed=None)                    # cannot be told: the Check
    assert run.poll() == Outcome("done") and asked == [("claude", CHECK_PROMPT, "laborer")]
    words = tool_errors.ToolError("claude", "401 unauthorized", 1)
    run, _ = begin("claude", tmp_path, Spawner(code=0), signed=words)
    out = run.poll()
    assert out.state == "failed" and out.why.startswith("Claude Code is not signed in")


def test_the_terminal_way_writes_a_script_and_opens_it_in_a_window(tmp_path):
    spawn = Spawner()
    env = {"PATH": "/opt/bin:/usr/bin", "PI_CODING_AGENT_DIR": "/work/pi", "SECRET_TOKEN": "t0ken"}
    run, _ = begin("pi", tmp_path, spawn, signed=None, env=env)
    script = tmp_path / "state" / "sign-in" / "pi.command"
    assert (script.stat().st_mode & 0o777) == 0o700
    text = script.read_text()
    assert text.splitlines()[:2] == ["#!/bin/sh", "cd ~ || exit 1"]
    assert "export PATH=/opt/bin:/usr/bin" in text and "export PI_CODING_AGENT_DIR=/work/pi" in text
    assert text.rstrip().endswith("exec /bin/pi") and "t0ken" not in text and "SECRET" not in text
    assert spawn.procs[0].argv == ["x-terminal-emulator", "-e", str(script)] and run.by == "terminal"
    assert run.poll() is None                                          # cannot be told: only the person's Done
    assert run.told() == Outcome("done") and run.poll() == Outcome("done")      # the Check answered


# -- when a sign-in helps (§3) --------------------------------------------------------------------------------------

def test_helps_unless_a_key_is_set_or_another_claude_renews_or_only_weak_words_and_signed_in():
    never = lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked"))           # noqa: E731
    err = login_error()
    assert tool_errors.helps(err, {}, never) is True
    assert tool_errors.helps(err, {"ANTHROPIC_API_KEY": "k"}, never) is False
    assert tool_errors.helps(err, {"ANTHROPIC_AUTH_TOKEN": "k"}, never) is False
    assert tool_errors.helps(login_error("codex", "401 unauthorized"), {"CODEX_API_KEY": "k"}, never) is False
    assert tool_errors.helps(login_error("codex", "401 unauthorized"), {}, never) is True
    assert tool_errors.helps(login_error("cursor", "401 unauthorized"), {"CURSOR_API_KEY": "k"}, never) is False
    renewing = login_error(said="Not logged in: another Claude Code process is refreshing the token")
    assert tool_errors.helps(renewing, {}, never) is False
    weak = login_error(said="Failed to authenticate with the OAuth server")
    assert tool_errors.helps(weak, {}, lambda h, e=None: True) is False
    assert tool_errors.helps(weak, {}, lambda h, e=None: False) is True
    assert tool_errors.helps(weak, {}, lambda h, e=None: None) is True
    assert tool_errors.helps(tool_errors.ToolError("claude", "429 rate limit", 1), {}, never) is False   # not a login


# -- the host's service (§4) ----------------------------------------------------------------------------------------

def fresh(tmp_path, env=None, signed=None, root=None, **kw):
    """A SignIns that watches, with a fake process per start and a clock of its own."""
    spawn, clock, bus = Spawner(), Clock(), b.Bus()
    seen = []
    bus.subscribe(b.ANY, seen.append)
    state = {"signed": signed}

    def start(harness, env_, state_dir, platform="linux", which=None, **k):
        return sign_in.start(harness, env_, state_dir, platform, which or (lambda n: f"/bin/{n}"), spawn, clock=clock,
                             signed_in=lambda h, e=None: state["signed"], ask=lambda *a: None, home=tmp_path,
                             by=k.get("by"))

    s = SignIns(bus, {} if env is None else env, tmp_path / "state", clock, start=start, which=lambda n: f"/bin/{n}",
                signed_in=lambda h, e=None: state["signed"], port_busy=lambda: False, threaded=False, root=root, **kw)
    s.watch()
    s.spawn, s.clock_, s.events, s.state = spawn, clock, seen, state
    return s, bus


def topics(s, topic):
    return [e.data for e in s.events if e.topic == topic]


def test_a_failure_a_sign_in_helps_begins_an_episode_with_auto(tmp_path):
    s, _ = fresh(tmp_path)
    assert s.snapshot() == [] and not s.blocked("claude")
    login_error()
    [e] = s.snapshot()
    assert e["harness"] == "claude" and e["tool"] == "Claude Code" and e["state"] == "needed" and e["by"] == "browser"
    assert e["auto"] is True and e["where"] == "ask" and e["waiting"] == 0 and s.blocked("claude")
    assert topics(s, b.SIGN_IN)[-1]["state"] == "needed"
    login_error()                                                # a second failure: the same episode
    assert len(topics(s, b.SIGN_IN)) == 1
    tool_errors.ToolError("claude", "429 rate limit", 1)         # a failure a sign-in does not help is never kept
    assert [x["harness"] for x in s.snapshot()] == ["claude"]


def test_start_opens_one_run_per_tool_and_auto_is_taken_once(tmp_path):
    s, _ = fresh(tmp_path)
    login_error()
    first = s.start("claude", auto=True)
    assert first["state"] == "open" and first["auto"] is False and len(s.spawn.procs) == 1
    assert s.spawn.procs[0].argv == ["/bin/claude", "auth", "login"]
    assert s.start("claude")["state"] == "open" and len(s.spawn.procs) == 1          # never a second
    s.cancel("claude")
    assert s.entry("claude")["state"] == "failed" and s.entry("claude")["why"] == "cancelled"
    assert s.start("claude", auto=True)["state"] == "failed" and len(s.spawn.procs) == 1     # auto only once
    assert s.start("claude")["state"] == "open" and len(s.spawn.procs) == 2                  # Sign in again, any time
    login_error()                                                  # a second failure opens nothing by itself
    assert s.entry("claude")["auto"] is False


def test_the_run_ending_well_is_done_and_publishes_signed_in(tmp_path):
    s, _ = fresh(tmp_path, signed=True)
    login_error()
    s.start("claude")
    s.spawn.procs[0].returncode = 0
    s.clock_.now += 7
    s.tick()
    assert s.snapshot() == [] and not s.blocked("claude")
    assert topics(s, b.SIGNED_IN) == [{"harness": "claude"}]
    assert topics(s, b.SIGN_IN)[-1]["state"] == "done"


def test_done_is_the_persons_word_for_a_tool_that_cannot_be_told(tmp_path):
    s, _ = fresh(tmp_path)
    login_error("agy", "Not logged in")
    s.start("agy")
    assert s.entry("agy")["by"] == "terminal" and s.entry("agy")["state"] == "open"
    s.tick()
    assert s.entry("agy")["state"] == "open"                         # nothing tells it
    s.done("agy")
    assert s.entry("agy")["state"] == "done" and topics(s, b.SIGNED_IN) == [{"harness": "agy"}]
    with pytest.raises(SignInError):
        s.done("agy")


def test_the_events_are_written_to_the_shown_projects_log_only(tmp_path):
    root = tmp_path / "project"
    s, _ = fresh(tmp_path, signed=True, root=lambda: root)
    login_error()
    s.start("claude")
    s.clock_.now += 12
    tool_errors.ran("claude")
    rows = event_log.read(root)
    assert [r["event"] for r in rows] == ["sign_in_needed", "signed_in"]
    assert rows[0]["harness"] == "claude" and rows[0]["where"] == "ask"
    assert rows[1]["by"] == "elsewhere" and rows[1]["s"] == 12
    none, _ = fresh(tmp_path / "other")
    login_error("codex", "401 unauthorized")
    assert not (tmp_path / "other" / ".orkcraft").exists() and none.blocked("codex")


# -- the work waits for it (§6) -------------------------------------------------------------------------------------

def runner_with(town, signins):
    events = []
    bus = SimpleNamespace(publish=lambda topic, **data: events.append((topic, data)))
    cfg = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": False, "review": False})
    return IdeaRunner(town.repo, town.state, cfg, bus, sign_ins=signins)


def until(fn, timeout=30.0):
    end = time.time() + timeout
    while time.time() < end:
        if (got := fn()):
            return got
        time.sleep(0.05)
    raise AssertionError("never happened")


def refuse_login(monkeypatch, said=LOGIN):
    real = jobs.run_work
    state = {"refuse": True}

    def run_work(*a, **k):
        if state["refuse"]:
            raise tool_errors.ToolError("claude", said, 1)
        return real(*a, **k)

    monkeypatch.setattr(jobs, "run_work", run_work)
    return state


def test_a_task_that_hit_a_refused_sign_in_is_held_and_runs_again_once_signed_in(town, tmp_path, monkeypatch):
    signins, _ = fresh(tmp_path / "cfg")
    refuse = refuse_login(monkeypatch)
    plan_of(town, [{"id": "k1"}])
    runner = runner_with(town, signins)
    runner.start("demo")
    task = until(lambda: (t := tasks_of(town)["k1"])["state"] == "held" and t)
    assert task["held_for"] == "sign_in" and task["harness"] == "claude" and task["error"] == ""
    assert "Claude Code is not signed in" in task["held_line"]
    due = dt.datetime.fromisoformat(task["held_until"]).timestamp()
    assert abs(due - (time.time() + HOLD_H * 3600)) < 120
    assert signins.entry("claude")["where"] == "task" and runner.held_for("claude") == 1
    until(lambda: not runner.busy())
    runner.tick()
    assert tasks_of(town)["k1"]["state"] == "held"                 # still signed out: it waits
    refuse["refuse"] = False
    tool_errors.ran("claude")                                      # signed in again
    end = time.time() + 60
    while time.time() < end and tasks_of(town)["k1"]["state"] != "merged":
        runner.tick()
        time.sleep(0.1)
    assert tasks_of(town)["k1"]["state"] == "merged" and not tasks_of(town)["k1"].get("held_for")


def test_a_task_that_starts_while_the_tool_needs_its_sign_in_is_held_at_once(town, tmp_path, monkeypatch):
    signins, _ = fresh(tmp_path / "cfg")
    login_error()                                                    # the episode began elsewhere
    called = []
    monkeypatch.setattr(jobs, "run_work", lambda *a, **k: called.append(1))
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner = runner_with(town, signins)
    runner.start("demo")
    runner.tick()
    states = {k: t["state"] for k, t in tasks_of(town).items()}
    assert states["k1"] == "held" and called == [] and tasks_of(town)["k1"]["held_for"] == "sign_in"


@pytest.fixture
def keeper(tmp_path):
    root, state = tmp_path / "wiki", tmp_path / ".orkcraft"
    signins, _ = fresh(tmp_path / "cfg")
    settings_ = {"batch_minutes": 30, "idle_hours": 24}
    k = IdeaKeeper(tmp_path, state, lambda: root, lambda: settings_, lambda slug: None, sign_ins=signins)
    k.root, k.state, k.signins = root, state, signins
    return k


class Answers:
    def __init__(self, *answers) -> None:
        self.answers = list(answers)

    def __call__(self, tier, prompt, effort="", budget=None):
        got = self.answers.pop(0)
        if isinstance(got, Exception):
            raise got
        return json.dumps(got), 0.01, 1000, "s"


NOON = dt.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).timestamp()      # outside the night

DRAFT = {"gist": "Dark mode.\nAt night it glares.", "why": "calm", "size": "m", "questions": []}


def test_a_draft_that_hit_a_refused_sign_in_waits_and_the_clock_drafts_it_once_signed_in(keeper):
    slug = ideas.add_idea(keeper.root, "dark mode", state_dir=keeper.state)
    ideas.save_state(keeper.state, slug, queue="now")
    keeper.call = Answers(login_error())
    keeper.draft_one(slug)
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "raw" and st["error"] == "" and st["held_for"] == "sign_in" and st["held_until"]
    assert keeper.signins.entry("claude")["where"] == "ask"       # (draft_one on this thread; a run says "draft")
    assert keeper.held_for("claude") == 1
    assert keeper.tick(now=NOON) is False and ideas.state(keeper.state, slug)["held_for"] == "sign_in"
    keeper.call = Answers(DRAFT, {"tasks": []})
    tool_errors.ran("claude")
    keeper.tick(now=NOON + 100)
    until(lambda: not keeper.busy(slug) and ideas.state(keeper.state, slug)["state"] != "raw")
    st = ideas.state(keeper.state, slug)
    assert st["held_for"] == "" and st["held_until"] == "" and st["state"] != "raw"       # the hold lifted, drafted
    assert ideas.idea_page(keeper.root, slug).section("Gist").startswith("Dark mode.")


# -- the Map, the needs, the Check row (§7) -------------------------------------------------------------------------

def test_the_map_says_a_task_or_an_idea_waits_for_the_sign_in():
    until_ = "2026-10-21T10:00:00"
    held = {"needs_you": "", "held_until": "", "queue": "", "start_at": ""}
    task = {"state": "held", "held_for": "sign_in", "harness": "claude", "held_until": until_}
    got = board_map._waits(held, [task], {}, [])
    assert got == {"kind": "sign_in", "ref": "claude", "title": "Claude Code", "tool": "Claude Code", "until": until_}
    idea = {**held, "held_for": "sign_in", "held_until": until_}
    assert board_map._waits(idea, [], {}, [])["kind"] == "sign_in"
    limit = {**held, "held_until": until_}
    assert board_map._waits(limit, [], {}, [])["kind"] == "limits"                 # a window is as it was


def test_a_check_that_fails_for_the_sign_in_says_so_on_its_row(tmp_path):
    from orkboard.gui.onboarding import Onboarding
    s, _ = fresh(tmp_path)
    town = SimpleNamespace(machine=settings.load(), demo=False, call=lambda fn, *a: fn(*a))
    status = tools.ToolStatus(tools.TOOLS[0], found=True)
    asked = []

    def ask(tool, prompt, model=None):
        asked.append((tool, prompt, model))
        raise login_error(tool)

    ob = Onboarding(SimpleNamespace(town=town, on_change=lambda: None), detect=lambda: [status],
                    detect_others=lambda: [])
    ob._ask = ask
    ob.checks["claude"] = {"state": "running"}
    ob._check_run("claude")
    assert asked == [("claude", CHECK_PROMPT, "laborer")]
    row = ob.checks["claude"]
    assert row["state"] == "failed" and row["sign_in"] is True and row["kind"] == "login"
    assert s.entry("claude")["where"] == "check"                    # and no need: the Check adds none (no work waits)
    assert board_map.sign_in_needs(s.snapshot()) == []
    ob.checks["claude"] = {"state": "running"}
    ob._ask = lambda *a: (_ for _ in ()).throw(tool_errors.ToolError("claude", "429 rate limit", 1))
    ob._check_run("claude")
    assert ob.checks["claude"]["sign_in"] is False


# -- the commands, desktop only (§5) ---------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    h.close()


def test_the_commands_are_the_desktops_and_never_the_phones(host):
    for name in ("tools.sign_in", "tools.sign_in_cancel", "tools.sign_in_done"):
        assert name in host.commands and not BoardPhone.allowed(host, name, {"harness": "claude"})
    assert "sign_in" not in host.phone_snapshot()


def test_the_command_opens_the_tools_sign_in_and_refuses_an_unknown_or_missing_tool(host, tmp_path):
    spawn = Spawner()
    host.sign_ins._start = lambda harness, env, state_dir, **k: sign_in.start(
        harness, env, state_dir, "linux", lambda n: f"/bin/{n}", spawn, home=tmp_path)
    host.sign_ins._which = lambda n: f"/bin/{n}"
    assert host.snapshot()["sign_in"] == []
    login_error()
    [e] = host.snapshot()["sign_in"]
    assert e["state"] == "needed" and e["auto"] is True
    got = host.command("tools.sign_in", {"harness": "claude", "auto": True})
    assert got["state"] == "open" and got["auto"] is False and spawn.procs[0].argv == ["/bin/claude", "auth", "login"]
    again = host.command("tools.sign_in", {"harness": "claude", "auto": True})     # the second page: the entry as it is
    assert again["state"] == "open" and len(spawn.procs) == 1
    assert host.command("tools.sign_in_cancel", {"harness": "claude"})["why"] == "cancelled"
    with pytest.raises(CommandError, match="not one of the AI tools"):
        host.command("tools.sign_in", {"harness": "nobody"})
    host.sign_ins._which = lambda n: None
    with pytest.raises(CommandError, match="not found on this computer"):
        host.command("tools.sign_in", {"harness": "codex"})
    with pytest.raises(CommandError, match="Say which"):
        host.command("tools.sign_in", {})
    with pytest.raises(CommandError, match="true or false"):
        host.command("tools.sign_in", {"harness": "claude", "auto": "yes"})


def test_stop_all_cancels_an_open_sign_in_and_the_need_counts_what_waits(host, tmp_path):
    spawn = Spawner()
    host.sign_ins._start = lambda harness, env, state_dir, **k: sign_in.start(
        harness, env, state_dir, "linux", lambda n: f"/bin/{n}", spawn, home=tmp_path)
    host.sign_ins._which = lambda n: f"/bin/{n}"
    login_error()
    host.command("tools.sign_in", {"harness": "claude"})
    host.command("halt", {})
    assert spawn.procs[0].terminated and host.sign_ins.entry("claude")["why"] == "cancelled"
    host.sign_ins._waiting = lambda harness: 2
    board = host.command("ideas.board", {})
    need = next(n for n in board["needs_you"] if n["kind"] == "sign_in")
    assert need["waiting"] == 2 and need["blocks"] is True
    assert host.snapshot()["needs_you"] >= 1


