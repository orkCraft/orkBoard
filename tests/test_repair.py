"""Fix Orkboard (spec 119, decisions §197): the checkout, the worktree, the brief, the launch, `main` moved, the update checked and
rolled back (core/repair.py), the host's commands and snapshot (gui/repair.py), the phone's allowlist and the guarded restart
(gui/board_host.py). Real temporary git repositories with a bare `origin`; a fake `popen` (the real `claude` is never launched); the
state folder is the test's own (`repair_dir`)."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard import settings
from orkboard.core import repair, updates
from orkboard.gui import board_host
from orkboard.gui import repair as gui_repair
from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import lexicon


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def commit(repo: Path, name: str, text: str = "x\n", subject: str | None = None) -> str:
    (repo / name).write_text(text, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "-c", "user.email=t@t", "-c", "user.name=T", "commit", "-q", "-m", subject or f"add {name}")
    return git(repo, "rev-parse", "HEAD")


class World:
    """A bare `origin`, the checkout Orkboard runs from (a clone, on main) and another clone that plays Claude pushing."""

    def __init__(self, root: Path) -> None:
        self.origin = root / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.checkout = root / "checkout"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.checkout)], check=True)
        git(self.checkout, "remote", "add", "origin", str(self.origin))
        self.first = commit(self.checkout, "README.md", "# Orkboard\n", "first")
        git(self.checkout, "push", "-q", "origin", "main")
        git(self.checkout, "branch", "-q", "--set-upstream-to=origin/main", "main")
        self.claude = root / "claude"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.claude)], check=True)
        self.way = updates.Method("git", (("git", "-C", str(self.checkout), "pull", "--ff-only"),), cwd=str(self.checkout))

    def push(self, name: str, subject: str) -> str:
        """What Claude does in its worktree: a commit, then `git push origin HEAD:main`."""
        git(self.claude, "pull", "-q", "--ff-only", "origin", "main")
        sha = commit(self.claude, name, subject=subject)
        git(self.claude, "push", "-q", "origin", "HEAD:main")
        return sha


@pytest.fixture
def world(tmp_path, monkeypatch) -> World:
    w = World(tmp_path)
    monkeypatch.setattr(updates, "method", lambda *a, **k: w.way)
    monkeypatch.setattr(repair, "repair_dir", lambda: tmp_path / "state" / "repair")
    repair.forget_can()
    yield w
    repair.forget_can()


class Proc:
    """A launched process that runs until it is stopped (or `exits` at once, with `said` in the log)."""

    def __init__(self, pid: int = 4242, exits: bool = False) -> None:
        self.pid, self.exits = pid, exits

    def wait(self, timeout=None):
        if self.exits:
            return 1
        raise subprocess.TimeoutExpired("claude", timeout)


class Popen:
    """subprocess.Popen as a script: every launch kept."""

    def __init__(self, proc: Proc | None = None, said: str = "", fail: OSError | None = None) -> None:
        self.calls: list[tuple[list[str], dict]] = []
        self.proc, self.said, self.fail = proc or Proc(), said, fail

    def __call__(self, cmd, **kw):
        self.calls.append((list(cmd), kw))
        if self.fail:
            raise self.fail
        if self.said:
            kw["stdout"].write(self.said.encode())
        return self.proc


def logs(**files: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name.replace("__", "/"), text)
    return buf.getvalue()


def begin(w: World, said: str = "the Board froze", popen=None, **kw) -> dict:
    return repair.start(said, logs(**{"about.json": "{}", "crashes__c1.txt": "boom"}), now=1000.0, popen=popen or Popen(), **kw)


# -- can it (§2.1) ----------------------------------------------------------------------------------------------

def test_a_git_checkout_on_main_with_claude_can_be_fixed(world):
    assert repair.can(which=lambda name: "/usr/bin/claude", fresh=True) == (True, "")


def test_it_says_in_plain_words_why_it_cannot(world, monkeypatch):
    seen = lambda: repair.can(which=lambda name: "/usr/bin/claude", fresh=True)      # noqa: E731
    assert repair.can(which=lambda name: None, fresh=True) == (False, "Claude Code is not on the PATH")
    git(world.checkout, "checkout", "-q", "-b", "work")
    assert seen() == (False, "the checkout is on work, not main")
    git(world.checkout, "checkout", "-q", "main")
    git(world.checkout, "remote", "remove", "origin")
    assert seen() == (False, "the checkout has no remote origin")
    monkeypatch.setattr(updates, "method", lambda *a, **k: updates.Method("pipx", (("pipx", "upgrade", "orkboard"),)))
    assert seen() == (False, "Orkboard was not installed from git")


def test_it_looks_for_the_first_word_of_the_machines_command(world, monkeypatch):
    looked = []
    monkeypatch.setattr(settings, "load", lambda *a: settings.MachineSettings.from_dict({"repair_command": ["my-claude", "rc"]}))
    repair.can(which=lambda name: looked.append(name) or "/x", fresh=True)
    assert looked == ["my-claude"]


def test_the_answer_is_read_once_a_minute(world):
    asked = []
    which = lambda name: asked.append(name) or None      # noqa: E731
    assert repair.can(which=which, now=100.0, fresh=True)[0] is False
    assert repair.can(which=which, now=130.0)[0] is False and len(asked) == 1
    repair.can(which=which, now=161.0)
    assert len(asked) == 2


# -- the start (§2.2 to §2.4) -----------------------------------------------------------------------------------

def test_start_makes_the_worktree_the_brief_the_logs_and_launches_detached(world):
    popen = Popen()
    state = begin(world, "the Board froze", popen)
    wt = repair.worktree_dir()
    assert git(wt, "rev-parse", "HEAD") == world.first == state["base"]            # at origin/main, detached
    assert git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    text = (wt / "CLAUDE.local.md").read_text(encoding="utf-8")
    assert text.startswith("# Fix Orkboard\n") and '"the Board froze"' in text and world.first in text
    assert "git push origin HEAD:main" in text and "Never skip or delete a test" in text
    assert (wt / ".orkcraft-repair" / "logs" / "about.json").read_text() == "{}"
    assert (wt / ".orkcraft-repair" / "logs" / "crashes" / "c1.txt").read_text() == "boom"
    assert git(wt, "status", "--porcelain") == ""                                   # both kept out of git
    cmd, kw = popen.calls[0]
    assert cmd == list(settings.REPAIR_COMMAND) and cmd[:2] == ["claude", "remote-control"]
    assert kw["cwd"] == str(wt) and kw["start_new_session"] is True and kw["stdin"] is subprocess.DEVNULL
    assert kw["stderr"] is subprocess.STDOUT
    assert json.loads((repair.repair_dir() / "state.json").read_text()) == state
    assert state == {"started_at": 1000.0, "base": world.first, "said": "the Board froze", "pid": 4242}
    assert repair.read_state() == state


def test_the_brief_with_nothing_said_tells_to_read_the_logs():
    assert '"nothing; read the logs"' in repair.brief("  ", "abc", "Orkboard")
    assert repair.brief("x", "abc", "Elsewhere").splitlines()[0] == "# Fix Elsewhere"      # the product's name, never a fixed one


def test_the_excludes_are_written_once_and_an_older_worktree_is_removed(world):
    begin(world)
    wt = repair.worktree_dir()
    (wt / "left-by-claude.txt").write_text("old\n", encoding="utf-8")
    newer = world.push("fix.py", "fix the freeze")
    state = begin(world, "again")
    assert not (wt / "left-by-claude.txt").exists() and (wt / "fix.py").exists()
    assert git(wt, "rev-parse", "HEAD") == newer == state["base"]                  # fetched again: the base is main as it is now
    exclude = (world.checkout / ".git" / "info" / "exclude").read_text(encoding="utf-8").splitlines()
    assert exclude.count("CLAUDE.local.md") == 1 and exclude.count(".orkcraft-repair/") == 1
    assert git(world.checkout, "worktree", "list").count("\n") == 1                # the checkout and one worktree, not two


def test_a_zip_cannot_write_outside_the_logs_folder(world):
    repair.start("", logs(**{"about.json": "{}", "..__evil.txt": "no", "ok__x.txt": "y"}), popen=Popen())
    assert not (repair.worktree_dir() / ".orkcraft-repair" / "evil.txt").exists() and not (repair.worktree_dir() / "evil.txt").exists()
    assert (repair.worktree_dir() / ".orkcraft-repair" / "logs" / "ok" / "x.txt").exists()


def test_a_bad_zip_still_starts_the_fix(world):
    repair.start("", b"not a zip", popen=Popen())
    assert (repair.worktree_dir() / ".orkcraft-repair" / "logs" / "README.txt").is_file()


def test_a_process_that_exits_at_once_is_said_with_the_end_of_its_log(world):
    popen = Popen(Proc(exits=True), said="Remote Control is not enabled for this account\n")
    with pytest.raises(repair.RepairError) as e:
        begin(world, popen=popen)
    assert "Remote Control is not enabled" in str(e.value)
    assert f"Run `claude remote-control` once in {repair.worktree_dir()} to answer its questions, then Try again" in str(e.value)
    assert repair.read_state() == {}                                                 # no fix is followed


def test_claude_missing_or_origin_unreachable_is_said(world, tmp_path):
    with pytest.raises(repair.RepairError, match="could not be started"):
        begin(world, popen=Popen(fail=FileNotFoundError(2, "No such file or directory")))
    git(world.checkout, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(repair.RepairError, match="git fetch origin main failed"):
        begin(world)


def test_a_non_git_copy_cannot_start(world, monkeypatch):
    monkeypatch.setattr(updates, "method", lambda *a, **k: updates.Method("brew", (("brew", "upgrade", "x"),)))
    with pytest.raises(repair.RepairError, match="not installed from git"):
        begin(world)


def test_stop_ends_the_process_group_and_keeps_the_worktree(world):
    def really(cmd, **kw):
        return subprocess.Popen(["sleep", "60"], cwd=kw["cwd"], stdin=kw["stdin"], stdout=kw["stdout"], stderr=kw["stderr"],
                                start_new_session=True)
    state = repair.start("", logs(), popen=really, settle=0.2)
    assert repair.alive() and state["pid"] > 0
    repair.stop()
    assert not repair.alive() and repair.read_state()["pid"] == 0
    assert (repair.worktree_dir() / "CLAUDE.local.md").is_file()
    repair.stop()                                                                    # nothing running: nothing happens


def test_a_new_start_stops_the_fix_that_runs(world):
    procs = []

    def really(cmd, **kw):
        procs.append(subprocess.Popen(["sleep", "60"], cwd=kw["cwd"], stdin=kw["stdin"], stdout=kw["stdout"],
                                      stderr=kw["stderr"], start_new_session=True))
        return procs[-1]
    repair.start("", logs(), popen=really, settle=0.2)
    repair.start("", logs(), popen=really, settle=0.2)
    assert procs[0].poll() is not None and procs[1].poll() is None
    repair.stop()


# -- main moved (§2.5) ------------------------------------------------------------------------------------------

def test_landed_lists_what_came_to_main_newest_first(world):
    state = begin(world)
    assert repair.landed(state["base"]) == []
    first = world.push("a.py", "fix the freeze")
    second = world.push("b.py", "and its test")
    assert repair.landed(state["base"]) == [{"sha": second, "subject": "and its test"}, {"sha": first, "subject": "fix the freeze"}]
    git(world.checkout, "pull", "-q", "--ff-only", "origin", "main")
    assert repair.landed(state["base"]) == []                                       # this copy has them: nothing more to update to


def test_what_main_had_before_the_fix_started_is_not_the_fix(world):
    world.push("early.py", "someone else's commit")
    state = begin(world)                                                              # the checkout is behind main: base is main's head
    assert repair.landed(state["base"]) == []
    late = world.push("late.py", "the fix")
    assert [c["sha"] for c in repair.landed(state["base"])] == [late]


def test_landed_is_no_news_when_git_fails(world):
    state = begin(world)
    git(world.checkout, "remote", "set-url", "origin", "/nowhere.git")
    assert repair.landed(state["base"]) == []


def test_applied_tells_a_restart_on_the_fix(world):
    state = begin(world)
    assert not repair.applied(state["base"])
    world.push("a.py", "fix")
    git(world.checkout, "pull", "-q", "--ff-only", "origin", "main")
    assert repair.applied(state["base"]) and not repair.applied("") and not repair.applied(world.checkout.name)


# -- the update, checked (§2.6) ---------------------------------------------------------------------------------

class Script:
    """subprocess.run that runs everything for real except the Python checks, which answer `check_rc`; the install step is recorded."""

    def __init__(self, check_rc: int = 0) -> None:
        self.check_rc, self.calls = check_rc, []

    def __call__(self, cmd, **kw):
        self.calls.append(list(cmd))
        if cmd[0] == sys.executable:
            return subprocess.CompletedProcess(cmd, self.check_rc, "", "ImportError: broken" if self.check_rc else "")
        if cmd[0] == "install-step":
            return subprocess.CompletedProcess(cmd, 0, "installed", "")
        return subprocess.run(cmd, **kw)


def with_install(w: World) -> None:
    w.way = updates.Method("git", (*w.way.steps, ("install-step",)), cwd=str(w.checkout))


def test_the_update_fast_forwards_and_checks_the_new_code_for_real(world):
    new = world.push("a.py", "the fix")
    result = repair.update()
    assert result.ok, result.output
    assert git(world.checkout, "rev-parse", "HEAD") == new


def test_the_new_code_is_imported_and_asked_its_version_with_the_restarts_python(world):
    with_install(world)
    world.push("a.py", "the fix")
    run = Script()
    assert repair.update(run=run).ok
    checks = [c for c in run.calls if c[0] == sys.executable]
    assert checks[0][1:] == ["-c", "import orkboard.gui.board_host, orkboard.gui.server"]
    assert checks[1][1:] == ["-m", "orkboard.gui.board_host", "--version"]
    assert run.calls.index(["install-step"]) < run.calls.index(checks[0])           # installed, then checked, then restarted


def test_a_check_that_fails_sends_the_checkout_back_and_installs_the_old_code_again(world):
    with_install(world)
    old = git(world.checkout, "rev-parse", "HEAD")
    world.push("a.py", "the fix that breaks")
    run = Script(check_rc=1)
    result = repair.update(run=run)
    assert not result.ok and "does not start on the new code" in result.output and old[:7] in result.output
    assert "ImportError: broken" in result.output
    assert git(world.checkout, "rev-parse", "HEAD") == old and not (world.checkout / "a.py").exists()
    assert run.calls.count(["install-step"]) == 2                                    # once on the new code, once on the old


def test_a_pull_that_fails_leaves_the_checkout_where_it_was(world):
    old = commit(world.checkout, "mine.py", subject="a local commit")                 # diverges from origin once main moves
    world.push("theirs.py", "the fix")
    result = repair.update()
    assert not result.ok and git(world.checkout, "rev-parse", "HEAD") == old


def test_a_checkout_with_changes_is_refused_in_the_updates_words(world):
    (world.checkout / "README.md").write_text("changed\n", encoding="utf-8")
    result = repair.update()
    assert not result.ok and "the checkout has changes of its own" in result.output


def test_update_never_raises(world):
    def broken(cmd, **kw):
        raise OSError("no git here")
    result = repair.update(run=broken)
    assert not result.ok and "no git here" in result.output
    assert not repair.update(way=updates.Method("none", why="brew is not on PATH")).ok


def test_the_sha_a_restart_comes_from_is_kept_and_proven(world):
    assert repair.last_good() == {} and not repair.pending("abc") and repair.rolled_back() == ""
    repair.remember_good("abc")
    assert repair.pending("abc") and not repair.pending("other") and repair.last_good()["sha"] == "abc"
    assert repair.last_good(now=10**10) == {}                                         # not the restart that just happened
    env = repair.guard_environment({})
    assert env == {repair.REPAIRED_ENV: "abc"}
    repair.came_up()                                                                  # the server served: proven
    assert repair.last_good() == {} and repair.guard_environment({}) == {}


def test_a_rollback_is_kept_until_the_person_is_told_once(world):
    repair.remember_good("abc")
    repair.mark_rolled_back("abc")
    assert repair.rolled_back() == "abc" and not repair.pending("abc") and repair.guard_environment({}) == {}
    repair.came_up()
    assert repair.rolled_back() == "abc"                                              # the start on the old code does not forget it
    repair.told()
    assert repair.rolled_back() == ""
    repair.came_up()
    assert repair.last_good() == {}


def test_fall_back_resets_installs_and_restarts_with_the_same_arguments(world, monkeypatch):
    world.way = updates.Method("git", (*world.way.steps, ("true",)), cwd=str(world.checkout))      # `true`: an install step that works
    old = git(world.checkout, "rev-parse", "HEAD")
    world.push("a.py", "the fix")
    git(world.checkout, "pull", "-q", "--ff-only", "origin", "main")
    repair.remember_good(old)
    monkeypatch.setenv(repair.REPAIRED_ENV, old)
    restarts = []
    assert repair.fall_back(old, RuntimeError("no window"), ["--repo", "/p", "--port", "8765"], restarts.append) == 1
    assert git(world.checkout, "rev-parse", "HEAD") == old
    assert restarts == [["--repo", "/p", "--port", "8765"]] and repair.REPAIRED_ENV not in os.environ
    assert repair.rolled_back() == old


# -- main's guarded restart (§3.4) ------------------------------------------------------------------------------

def run_main(monkeypatch, fake_repo, run):
    monkeypatch.setattr(board_host, "run", run)
    return board_host.main(["--repo", str(fake_repo), "--browser", "--port", "8765"])


def test_a_restart_on_a_fix_that_does_not_come_up_goes_back_and_opens_the_old_code(world, fake_repo, monkeypatch):
    old = git(world.checkout, "rev-parse", "HEAD")
    world.push("a.py", "the fix")
    git(world.checkout, "pull", "-q", "--ff-only", "origin", "main")
    repair.remember_good(old)
    monkeypatch.setenv(repair.REPAIRED_ENV, old)
    restarts = []
    monkeypatch.setattr(board_host.core_updates, "restart", restarts.append)
    code = run_main(monkeypatch, fake_repo, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("the window did not come up")))
    assert code == 1 and git(world.checkout, "rev-parse", "HEAD") == old
    assert restarts == [["--repo", str(fake_repo.resolve()), "--browser", "--port", "8765"]]      # the same port
    assert repair.REPAIRED_ENV not in os.environ and repair.rolled_back() == old


def test_a_crash_after_the_server_came_up_is_not_a_rollbacks(world, fake_repo, monkeypatch):
    monkeypatch.setenv(repair.REPAIRED_ENV, "abc")                                   # `last-good.json` was taken away when it came up
    with pytest.raises(RuntimeError, match="later"):
        run_main(monkeypatch, fake_repo, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("later")))


def test_an_ordinary_crash_is_raised_as_before(world, fake_repo, monkeypatch):
    monkeypatch.delenv(repair.REPAIRED_ENV, raising=False)
    with pytest.raises(RuntimeError, match="boom"):
        run_main(monkeypatch, fake_repo, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))


def test_the_restart_after_a_fix_names_the_sha_it_comes_from(world, fake_repo, monkeypatch):
    repair.remember_good("abc123")
    seen = []
    monkeypatch.setattr(board_host.core_updates, "restart", lambda argv: seen.append(os.environ.get(repair.REPAIRED_ENV)))
    monkeypatch.delenv(repair.REPAIRED_ENV, raising=False)
    assert run_main(monkeypatch, fake_repo, lambda *a, **k: updates.RESTART) == updates.RESTART
    assert seen == ["abc123"]
    monkeypatch.delenv(repair.REPAIRED_ENV, raising=False)


def test_a_plain_update_restart_names_nothing(world, fake_repo, monkeypatch):
    seen = []
    monkeypatch.setattr(board_host.core_updates, "restart", lambda argv: seen.append(os.environ.get(repair.REPAIRED_ENV)))
    monkeypatch.delenv(repair.REPAIRED_ENV, raising=False)
    run_main(monkeypatch, fake_repo, lambda *a, **k: updates.RESTART)
    assert seen == [None]


def test_the_server_coming_up_takes_the_proof_away(world, fake_repo, monkeypatch):
    from orkboard.gui import extension, folder_dialog, mac_app, server, server_log
    repair.remember_good("abc")

    class Quiet:
        def __init__(self, *a, **k): ...
        url = "http://x"
        def start_thread(self): return SimpleNamespace(join=lambda *a: None)
        def stop(self): ...
    monkeypatch.setattr(server, "Server", Quiet)
    monkeypatch.setattr(server_log, "install", lambda **k: None)
    monkeypatch.setattr(board_host, "show", lambda *a, **k: None)
    monkeypatch.setattr(Orkboard, "opened", lambda self: None)
    assert board_host.run(fake_repo) == 0
    assert repair.last_good() == {}


# -- the settings -----------------------------------------------------------------------------------------------

def test_the_machines_command_is_a_setting_with_a_default_that_survives_a_round_trip(tmp_path):
    file = tmp_path / "s.json"
    s = settings.MachineSettings()
    assert s.repair_command == list(settings.REPAIR_COMMAND) and s.repair_command[0] == "claude"
    s.repair_command = ["claude", "remote-control", "--name", "Mine"]
    settings.save(s, file)
    assert settings.load(file).repair_command == ["claude", "remote-control", "--name", "Mine"]
    for broken in ("claude", [], [1, 2], ["claude", ""], ["a\nb"], None):
        assert settings.clean_repair_command(broken) == list(settings.REPAIR_COMMAND)


def test_the_glossary_has_the_fix():
    assert lexicon.term("fix") == "Fix" and lexicon.term("fix", many=True) == "Fixes"
    assert "Claude Code" in Path(lexicon.__file__).read_text(encoding="utf-8").split('_t("fix"')[1].splitlines()[0]


# -- the host (§3.1 to §3.3) ------------------------------------------------------------------------------------

class Engine:
    """core/repair.py as the host sees it, with nothing run: what it is asked is kept, what it answers is set."""

    RepairError = repair.RepairError
    updates = updates

    def __init__(self) -> None:
        self.ok, self.why = True, ""
        self.state: dict = {}
        self.asked: list = []
        self.landed_now: list[dict] = []
        self.runs = True
        self.result = updates.Result(True, "pulled", "9.9.9")
        self.fail: str | None = None

    def can(self): return self.ok, self.why
    def forget_can(self): ...
    def read_state(self): return dict(self.state)
    def clear_state(self): self.asked.append("clear"); self.state = {}
    def applied(self, base): return base == "applied"
    def alive(self): return self.runs
    def head(self): return "old-sha"
    def rolled_back(self): return ""
    def told(self): self.asked.append("told")
    def remember_good(self, old): self.asked.append(("good", old))
    def stop(self): self.asked.append("stop")

    def start(self, said, zipped, now=None, cmd=None, **kw):
        self.asked.append(("start", said, zipped, cmd))
        if self.fail:
            raise repair.RepairError(self.fail)
        self.state = {"started_at": now, "base": "base-sha", "said": said, "pid": 77}
        return dict(self.state)

    def landed(self, base):
        self.asked.append(("landed", base))
        return list(self.landed_now)

    def update(self):
        self.asked.append("update")
        return self.result


@pytest.fixture
def fix(fake_repo, monkeypatch):
    host = Orkboard(fake_repo)
    engine = Engine()
    host.repair = gui_repair.Repair(host, engine)
    host.commands.update(host.repair.commands())
    monkeypatch.setattr(gui_repair.Repair, "_spawn", staticmethod(lambda fn, name: fn()))      # the threads run at once
    host.toasts = []
    host.toast = lambda message, title="", severity="information", timeout=None, **kw: host.toasts.append((message, severity))
    host.quits = []
    host.updates.quit = lambda: host.quits.append(1)
    yield host, engine
    host.close()


def test_the_snapshot_says_whether_and_why_and_the_state(fix):
    host, engine = fix
    assert host.snapshot()["repair"] == {"can": True, "why": "", "state": "idle", "started_at": None, "landed": [], "error": ""}
    engine.ok, engine.why = False, "the checkout is on work, not main"
    assert host.snapshot()["repair"]["can"] is False and host.snapshot()["repair"]["why"] == "the checkout is on work, not main"
    json.dumps(host.snapshot())


def test_the_project_less_snapshot_has_it_too(tmp_path):
    host = Orkboard(None)
    assert set(host.snapshot()["repair"]) == {"can", "why", "state", "started_at", "landed", "error"}
    host.close()


def test_start_packs_the_logs_and_hands_them_in_with_the_machines_command(fix):
    host, engine = fix
    snap = host.command("repair.start", {"said": "it froze", "page": {"tab": "Board"}})
    assert snap["state"] == "working" and snap["started_at"] is not None
    kind, said, zipped, cmd = next(a for a in engine.asked if a[0] == "start")
    assert said == "it froze" and cmd == list(settings.REPAIR_COMMAND)
    names = zipfile.ZipFile(io.BytesIO(zipped)).namelist()
    assert "about.json" in names and "on-screen.txt" in names and "page.json" in names
    assert any("Claude Code started" in m and "Fix Orkboard" in m for m, _ in host.toasts)
    assert host.snapshot()["repair"]["state"] == "working"


def test_start_is_refused_in_words_when_it_cannot(fix):
    host, engine = fix
    engine.ok, engine.why = False, "Claude Code is not on the PATH"
    with pytest.raises(CommandError, match="Claude Code is not on the PATH"):
        host.command("repair.start", {})
    assert "start" not in [a[0] for a in engine.asked if isinstance(a, tuple)]


def test_a_start_that_fails_turns_the_bug_to_failed_with_the_error_as_it_is(fix):
    host, engine = fix
    engine.fail = "Run `claude remote-control` once in /x to answer its questions, then Try again"
    host.command("repair.start", {"said": "x"})
    snap = host.snapshot()["repair"]
    assert snap["state"] == "failed" and snap["error"] == engine.fail
    engine.fail = None
    assert host.command("repair.start", {"said": "x"})["state"] == "working"         # Try again


def test_main_moving_turns_working_into_ready_with_the_commits(fix):
    host, engine = fix
    host.command("repair.start", {})
    host.repair.tick(100.0)
    assert ("landed", "base-sha") in engine.asked and host.snapshot()["repair"]["state"] == "working"
    engine.landed_now = [{"sha": "b", "subject": "second"}, {"sha": "a", "subject": "first"}]
    host.repair.tick(131.0)
    snap = host.snapshot()["repair"]
    assert snap["state"] == "ready" and snap["landed"] == engine.landed_now and snap["started_at"] is not None


def test_main_is_asked_every_thirty_seconds_and_only_while_a_fix_runs(fix):
    host, engine = fix
    asks = lambda: len([a for a in engine.asked if isinstance(a, tuple) and a[0] == "landed"])      # noqa: E731
    host.repair.tick(0.0)
    assert asks() == 0                                                                # idle: never
    host.command("repair.start", {})
    host.repair.tick(10.0)
    host.repair.tick(25.0)
    assert asks() == 1
    host.repair.tick(41.0)
    assert asks() == 2
    host.command("repair.stop")
    host.repair.tick(500.0)
    assert asks() == 2


def test_a_process_that_ended_with_nothing_landed_is_a_fix_that_did_not_come_in(fix):
    host, engine = fix
    host.command("repair.start", {})
    engine.runs = False
    host.repair.tick(100.0)
    snap = host.snapshot()["repair"]
    assert snap["state"] == "failed" and "nothing came in to main" in snap["error"]


def test_a_fix_that_landed_and_then_ended_is_still_ready(fix):
    host, engine = fix
    host.command("repair.start", {})
    engine.runs, engine.landed_now = False, [{"sha": "a", "subject": "the fix"}]
    host.repair.tick(100.0)
    assert host.snapshot()["repair"]["state"] == "ready"


def test_stop_ends_the_fix_and_the_bug_is_idle(fix):
    host, engine = fix
    host.command("repair.start", {})
    snap = host.command("repair.stop")
    assert snap["state"] == "idle" and "stop" in engine.asked and "clear" in engine.asked


def test_update_runs_the_checked_update_then_asks_for_the_restart(fix):
    host, engine = fix
    with pytest.raises(CommandError, match="no fix to update to"):
        host.command("repair.update")
    host.command("repair.start", {})
    engine.landed_now = [{"sha": "a", "subject": "the fix"}]
    host.repair.tick(100.0)
    snap = host.command("repair.update")
    assert "update" in engine.asked and ("good", "old-sha") in engine.asked
    assert host.updates.restart_wanted and host.quits == [1]
    assert snap["state"] == "updating" and host.snapshot()["repair"]["state"] == "updating"


def test_an_update_that_does_not_pass_the_check_fails_and_nothing_restarts(fix):
    host, engine = fix
    host.command("repair.start", {})
    engine.landed_now = [{"sha": "a", "subject": "the fix"}]
    host.repair.tick(100.0)
    engine.result = updates.Result(False, "Orkboard does not start on the new code")
    host.command("repair.update")
    snap = host.snapshot()["repair"]
    assert snap["state"] == "failed" and snap["error"] == "Orkboard does not start on the new code"
    assert not host.updates.restart_wanted and host.quits == [] and ("good", "old-sha") not in engine.asked
    assert any(sev == "error" for _, sev in host.toasts)


def test_a_fix_started_before_a_restart_is_followed_again(fake_repo):
    host = Orkboard(fake_repo)
    engine = Engine()
    engine.state = {"started_at": 55.0, "base": "base-sha", "pid": 9}
    fixing = gui_repair.Repair(host, engine)
    assert fixing.snapshot()["state"] == "working" and fixing.snapshot()["started_at"] == 55.0
    engine.state = {"started_at": 55.0, "base": "applied", "pid": 9}                  # this copy is already on the fix
    done = gui_repair.Repair(host, engine)
    assert done.snapshot()["state"] == "idle" and "clear" in engine.asked
    engine.state = {"started_at": 55.0, "base": "base-sha", "pid": 0}                 # stopped before the restart
    assert gui_repair.Repair(host, engine).snapshot()["state"] == "idle"
    host.close()


def test_a_rollback_is_said_once_and_the_bug_is_failed(fake_repo):
    host = Orkboard(fake_repo)
    engine = Engine()
    engine.rolled_back = lambda: "0123456789abcdef"
    toasts = []
    host.toast = lambda message, title="", severity="information", timeout=None, **kw: toasts.append((message, severity))
    fixing = gui_repair.Repair(host, engine)
    snap = fixing.snapshot()
    assert snap["state"] == "failed" and snap["error"] == "Orkboard did not start on the fix: it went back to 0123456"
    fixing.tick(1.0)
    fixing.tick(2.0)
    assert toasts == [("Orkboard did not start on the fix: it went back to 0123456", "error")] and engine.asked.count("told") == 1
    host.close()


def test_nothing_is_offered_or_asked_in_the_demo(fake_repo):
    host = Orkboard(fake_repo, demo=True)
    snap = host.snapshot()["repair"]
    assert snap["can"] is False and snap["state"] == "idle"
    host.repair.tick(1.0)
    host.close()


def test_a_phone_may_start_stop_and_update_a_fix_and_sees_its_state(fix):
    host, engine = fix
    for name in ("repair.start", "repair.stop", "repair.update"):
        assert name in BoardPhone.COMMANDS and BoardPhone.allowed(host, name, {}) and name in host.commands
    assert "repair" not in Orkboard.COMPUTER_ONLY and host.phone_snapshot()["repair"]["state"] == "idle"
    host.command("repair.start", BoardPhone.guard("repair.start", {"said": "from the phone"}, {"id": "d1"}))
    assert host.phone_snapshot()["repair"]["state"] == "working"
    assert host.command("mobile.snapshot")["repair"]["state"] == "working"


def test_claude_code_is_found_where_it_installs_when_the_apps_path_does_not_reach_it(tmp_path):
    """An app started from the Dock has a short PATH: Claude Code is looked for where it installs (spec 119 §2.1, `PLACES`)."""
    place = tmp_path / "bin"
    place.mkdir()
    assert repair.find("claude", which=lambda name: None, places=(str(place),)) is None
    (place / "claude").write_text("#!/bin/sh\n")
    assert repair.find("claude", which=lambda name: None, places=(str(place),)) is None        # not executable
    (place / "claude").chmod(0o755)
    assert repair.find("claude", which=lambda name: None, places=(str(place),)) == str(place / "claude")
    assert repair.find("claude", which=lambda name: "/on/path/claude", places=(str(place),)) == "/on/path/claude"
