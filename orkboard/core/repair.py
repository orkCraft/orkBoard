"""Fix Orkboard (spec 119, decisions §197): Claude Code started on Orkboard's own code, with the logs, to fix it and push to `main`;
then the update, checked before the restart and rolled back when the new code does not come up. No face: the host (gui/repair.py)
says it, nothing here imports `gui/`. Every git or process call takes `run=subprocess.run` (and `popen=subprocess.Popen`), so a test
passes a fake or a real temporary repository.

    ok, why = repair.can()                       # a git checkout on main, an origin, Claude Code on the PATH (cached a minute)
    state = repair.start(said, logs_zip)         # the worktree at origin/main, the brief, the logs; Remote Control detached there
    repair.alive() · repair.stop()               # the process of the state's pid; its group stopped
    found = repair.landed(state["base"])         # [{"sha", "subject"}], newest first: what came to main since the fix started
    result = repair.update()                     # pull, install, then the new code imported and asked its version; else reset
    repair.remember_good(old)                    # the sha the restart comes from (board_host.main sets ORKCRAFT_REPAIRED to it)
    repair.rollback(old)                         # git reset --keep <old> and the install step again (board_host.main)

The place is `~/.orkcraft/repair/` (the state folder's name stays Orkline's): `worktree/` (one fixed folder, so Claude Code asks
once whether to trust it), `state.json`, `claude.log` and `last-good.json`. The worktree is a git worktree of the checkout this copy
runs from: `CLAUDE.local.md` is the brief (Claude Code reads it by itself), `.orkcraft-repair/logs/` the logs; both are kept out of git
through the repository's `info/exclude`. The launched process outlives Orkboard's restart, so the person follows it in the Claude app.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from orkboard import brand, settings
from orkboard.core import updates
from orkboard.orkget import profile
from orkboard.orkget.updates import _dirty

REPAIRED_ENV = "ORKCRAFT_REPAIRED"     # set on the process a fix's update restarted into: the sha it came from (spec 119 §3.4)
CAN_EVERY_S = 60.0                     # `can()` is read at most this often
SETTLE_S = 3.0                         # a launched process that exits within this long failed to start
STOP_WAIT_S = 5.0                      # SIGTERM, then SIGKILL after this long
GIT_TIMEOUT_S = 180.0
CHECK_TIMEOUT_S = 60.0
FRESH_S = 600.0                        # a `last-good.json` older than this is not the restart that just happened
SAID_CHARS = 4000                      # the person's line in the brief (the whole of it is in the logs' on-screen.txt)
EXCLUDES = ("CLAUDE.local.md", ".orkcraft-repair/")
CHECK_IMPORT = "import orkboard.gui.board_host, orkboard.gui.server"


class RepairError(Exception):
    """Said to the person as it is."""


# -- the place -------------------------------------------------------------------------------------------------

def repair_dir() -> Path:
    return Path.home() / ".orkcraft" / "repair"


def worktree_dir() -> Path:
    return repair_dir() / "worktree"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_state() -> dict:
    """`state.json` of the fix started last: {"started_at", "base", "said", "pid"}; {} when there is none."""
    return _read_json(repair_dir() / "state.json")


def clear_state() -> None:
    try:
        (repair_dir() / "state.json").unlink()
    except OSError:
        pass


# -- git -------------------------------------------------------------------------------------------------------

def _git(root: Path | str, *args: str, run: Callable = subprocess.run, timeout: float = GIT_TIMEOUT_S):
    return run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=timeout)


def _said(done) -> str:
    return ((done.stderr or "") + (done.stdout or "")).strip() or "git failed"


def _out(root: Path | str, *args: str, run: Callable = subprocess.run) -> str:
    """What a git read prints, "" when it fails."""
    try:
        done = _git(root, *args, run=run, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (done.stdout or "").strip() if done.returncode == 0 else ""


def checkout(way: updates.Method | None = None) -> Path | None:
    """The git checkout this copy runs from (`core.updates.method()`'s `cwd` when it is a git one), else None."""
    way = way or updates.method()
    return Path(way.cwd) if way.kind == "git" and way.cwd else None


def head(root: Path | str | None = None, run: Callable = subprocess.run) -> str:
    """The checkout's HEAD sha, "" when it cannot be read."""
    root = root or checkout()
    return _out(root, "rev-parse", "HEAD", run=run) if root else ""


_can_seen: tuple[float, tuple[bool, str]] | None = None


def forget_can() -> None:
    global _can_seen
    _can_seen = None


def can(run: Callable = subprocess.run, which: Callable[[str], str | None] = shutil.which, way: updates.Method | None = None,
        now: float | None = None, fresh: bool = False) -> tuple[bool, str]:
    """Whether Fix it is offered here and, when not, why in plain words: a git checkout of Orkboard on `main`, with a remote `origin`,
    and Claude Code (the first word of the machine's `repair_command`) on the PATH. Read once a minute at most."""
    global _can_seen
    now = time.monotonic() if now is None else now
    if not fresh and _can_seen is not None and 0 <= now - _can_seen[0] < CAN_EVERY_S:
        return _can_seen[1]
    answer = _can(run, which, way)
    _can_seen = (now, answer)
    return answer


def _can(run: Callable, which: Callable[[str], str | None], way: updates.Method | None) -> tuple[bool, str]:
    name = brand.name()
    try:
        root = checkout(way)
        if root is None:
            return False, f"{name} was not installed from git"
        branch = _out(root, "rev-parse", "--abbrev-ref", "HEAD", run=run)
        if branch != "main":
            return False, f"the checkout is on {branch or 'no branch'}, not main"
        if not _out(root, "remote", "get-url", "origin", run=run):
            return False, "the checkout has no remote origin"
        if not which(command()[0]):
            return False, "Claude Code is not on the PATH"
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"{type(e).__name__}: {e}"
    return True, ""


def command() -> list[str]:
    """What starts the fix: the machine's `repair_command`."""
    return list(settings.load().repair_command)


# -- the brief -------------------------------------------------------------------------------------------------

def brief(said: str, base: str, product: str) -> str:
    """`CLAUDE.local.md` of the worktree (spec 119 §2.3): what the session knows before the person says go."""
    line = (said or "").strip()[:SAID_CHARS] or "nothing; read the logs"
    return f"""# Fix {product}

The person pressed Fix in {product} and wrote: "{line}".
The logs since {product} last started are in `.orkcraft-repair/logs/` (about.json, app.log, crashes/, page.json, the
Board's analytics). You are in a git worktree of {product}'s own repository at origin/main ({base}).

1. Find the cause in the logs and the code; say it in a sentence before you change anything.
2. Fix it the smallest way that fixes it, following CLAUDE.md, with a test that fails without the fix.
3. Run the critical tests: `python -m pytest -q tests/test_architecture.py tests/test_board_alone.py tests/test_updates.py`
   and the test files of the modules you touched. Never skip or delete a test to make it pass.
4. Commit (a message that says what broke and why), then `git push origin HEAD:main`. If main moved meanwhile:
   `git pull --rebase origin main`, test again, push.
5. Say in the session what you fixed. {product} sees main move and offers Update and restart; the person presses it.

If you cannot find or fix it, say so in the session and push nothing.
"""


# -- the process -----------------------------------------------------------------------------------------------

def _alive(pid: int) -> bool:
    """Whether the process `pid` runs. A child of this process that ended is reaped here (it would stay a zombie that answers
    to `kill 0` for as long as Orkboard runs); the pid of a fix started before a restart is still this process's child."""
    if pid <= 0:
        return False
    try:
        if os.waitpid(pid, os.WNOHANG)[0] == pid:
            return False
    except ChildProcessError:
        pass
    except OSError:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def alive() -> bool:
    """Whether the process of the fix started last still runs."""
    return _alive(int(read_state().get("pid") or 0))


def stop(wait: float = STOP_WAIT_S) -> None:
    """SIGTERM to the process group of the state's pid (it was started as a session of its own), SIGKILL after `wait` seconds; the state's
    `pid` becomes 0. The worktree stays: the person may want what Claude left."""
    state = read_state()
    pid = int(state.get("pid") or 0)
    if pid > 0 and _alive(pid):
        _signal(pid, signal.SIGTERM)
        end = time.monotonic() + wait
        while _alive(pid) and time.monotonic() < end:
            time.sleep(0.05)
        if _alive(pid):
            _signal(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
            end = time.monotonic() + 2.0
            while _alive(pid) and time.monotonic() < end:
                time.sleep(0.05)
    if state:
        _write_json(repair_dir() / "state.json", {**state, "pid": 0})


def _signal(pid: int, sig: int) -> None:
    try:
        if hasattr(os, "killpg"):
            os.killpg(pid, sig)
        else:
            os.kill(pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


# -- the start -------------------------------------------------------------------------------------------------

def _exclude(root: Path, run: Callable) -> None:
    """`CLAUDE.local.md` and `.orkcraft-repair/` are appended (once) to the repository's `info/exclude`."""
    common = _out(root, "rev-parse", "--git-common-dir", run=run)
    if not common:
        raise RepairError("the checkout's git folder cannot be found")
    folder = Path(common) if Path(common).is_absolute() else root / common
    file = folder / "info" / "exclude"
    file.parent.mkdir(parents=True, exist_ok=True)
    have = file.read_text(encoding="utf-8").splitlines() if file.is_file() else []
    missing = [line for line in EXCLUDES if line not in have]
    if missing:
        text = file.read_text(encoding="utf-8") if file.is_file() else ""
        file.write_text(text + ("" if not text or text.endswith("\n") else "\n") + "\n".join(missing) + "\n", encoding="utf-8")


def _fresh_worktree(root: Path, run: Callable) -> str:
    """`origin/main` fetched, an older worktree removed, a new one made there; returns the sha it is at."""
    fetched = _git(root, "fetch", "origin", "main", run=run)
    if fetched.returncode != 0:
        raise RepairError(f"git fetch origin main failed: {_said(fetched)}"[-1500:])
    wt = worktree_dir()
    if wt.exists():
        _git(root, "worktree", "remove", "--force", str(wt), run=run)
        if wt.exists():                                   # not (any longer) a worktree of this checkout
            shutil.rmtree(wt, ignore_errors=True)
    _git(root, "worktree", "prune", run=run)
    wt.parent.mkdir(parents=True, exist_ok=True)
    made = _git(root, "worktree", "add", "--detach", str(wt), "origin/main", run=run)
    if made.returncode != 0:
        raise RepairError(f"git worktree add failed: {_said(made)}"[-1500:])
    return _out(wt, "rev-parse", "HEAD", run=run) or _out(root, "rev-parse", "origin/main", run=run)


def _unzip(data: bytes, into: Path) -> None:
    """The logs' zip unpacked under `into`; a name that leaves the folder is dropped."""
    into.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            for info in z.infolist():
                parts = Path(info.filename).parts
                if info.is_dir() or not parts or Path(info.filename).is_absolute() or ".." in parts:
                    continue
                target = into.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(info))
    except zipfile.BadZipFile:
        (into / "README.txt").write_text("The logs could not be packed this time.\n", encoding="utf-8")


def start(said: str, logs_zip: bytes, now: float | None = None, run: Callable = subprocess.run,
          popen: Callable = subprocess.Popen, cmd: list[str] | None = None, way: updates.Method | None = None,
          settle: float = SETTLE_S) -> dict:
    """The fix started (spec 119 §2.2, §2.4): a fix already running is stopped, the worktree made at origin/main with the brief and the
    logs, and the machine's `repair_command` started in it, detached (a session of its own, no stdin, its output in `claude.log`), so it
    outlives Orkboard's restart. Returns the state. `RepairError` says why not, and a process that exits within `settle` seconds fails."""
    root = checkout(way)
    if root is None:
        raise RepairError(f"{brand.name()} was not installed from git")
    argv = list(cmd or command())
    try:
        stop()
        base = _fresh_worktree(root, run)
        _exclude(root, run)
        wt = worktree_dir()
        (wt / "CLAUDE.local.md").write_text(brief(said, base, brand.name()), encoding="utf-8")
        _unzip(logs_zip, wt / ".orkcraft-repair" / "logs")
    except (OSError, subprocess.SubprocessError) as e:
        raise RepairError(f"The fix could not be prepared: {type(e).__name__}: {e}") from None
    clear_state()
    log = repair_dir() / "claude.log"
    try:
        with log.open("wb") as out:
            proc = popen(argv, cwd=str(worktree_dir()), stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                         start_new_session=True)
    except OSError as e:
        raise RepairError(f"Claude Code could not be started ({argv[0]}): {e.strerror or e}") from None
    try:
        proc.wait(timeout=settle)
    except subprocess.TimeoutExpired:
        pass                                              # it runs: that is what it should do
    else:
        try:
            tail = log.read_text(encoding="utf-8", errors="replace").strip()[-1500:]
        except OSError:
            tail = ""
        raise RepairError((tail + "\n\n" if tail else "") + f"Run `{' '.join(argv[:2])}` once in {worktree_dir()} to answer its "
                          "questions, then Try again")
    state = {"started_at": time.time() if now is None else now, "base": base, "said": (said or "").strip()[:SAID_CHARS],
             "pid": int(proc.pid)}
    _write_json(repair_dir() / "state.json", state)
    return state


# -- main moved ------------------------------------------------------------------------------------------------

def landed(base: str = "", run: Callable = subprocess.run, way: updates.Method | None = None) -> list[dict]:
    """What came to `origin/main` since the fix started and this copy does not have yet: `[{"sha", "subject"}]`, newest first (empty when
    main has not moved past this copy's HEAD, or past `base`, the sha main was at when the fix started). Asked only while a fix runs, on
    the host's clock; a failure (no network) is no news."""
    root = checkout(way)
    if root is None:
        return []
    try:
        if _git(root, "fetch", "origin", "main", run=run).returncode != 0:
            return []
        known = ["^HEAD"] + ([f"^{base}"] if base and _out(root, "cat-file", "-t", base, run=run) == "commit" else [])
        done = _git(root, "log", "--format=%H%x09%s", "origin/main", *known, run=run, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if done.returncode != 0:
        return []
    found = []
    for line in (done.stdout or "").splitlines():
        sha, _, subject = line.partition("\t")
        if sha.strip():
            found.append({"sha": sha.strip(), "subject": subject.strip()})
    return found


def applied(base: str, run: Callable = subprocess.run, way: updates.Method | None = None) -> bool:
    """Whether this copy has moved on past `base` (the restart on the fix came up): HEAD is not `base` and `base` is behind it."""
    root = checkout(way)
    if root is None or not base:
        return False
    now = _out(root, "rev-parse", "HEAD", run=run)
    if not now or now == base:
        return False
    try:
        return _git(root, "merge-base", "--is-ancestor", base, "HEAD", run=run, timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


# -- the update, checked ---------------------------------------------------------------------------------------

def rollback(old: str, run: Callable = subprocess.run, way: updates.Method | None = None) -> updates.Result:
    """The checkout back on `old` (`git reset --keep`) and the install step again, so the running code and the checkout agree."""
    way = way or updates.method()
    root = checkout(way)
    if root is None or not old:
        return updates.Result(False, "there is nothing to go back to")
    out: list[str] = []
    ok = True
    try:
        done = _git(root, "reset", "--keep", old, run=run)
        out.append(f"$ git reset --keep {old[:12]}\n{_said(done) if done.returncode else ''}".strip())
        ok = done.returncode == 0
        if ok:
            for step in way.steps[1:]:                    # the install step; the first is the pull
                done = run(list(step), capture_output=True, text=True, timeout=updates.INSTALL_TIMEOUT_S)
                out.append(f"$ {' '.join(step)}\n{(done.stdout or '').strip()}\n{(done.stderr or '').strip()}".strip())
                ok = ok and done.returncode == 0
    except (OSError, subprocess.SubprocessError) as e:
        out.append(f"{type(e).__name__}: {e}")
        ok = False
    return updates.Result(ok, "\n".join(out)[-4000:])


def update(run: Callable = subprocess.run, way: updates.Method | None = None) -> updates.Result:
    """The git method's steps (`git pull --ff-only`, then the install), then the new code **checked before anything restarts**, with
    the Python the restart will use: its modules imported and `--version` asked (60 s each). A step or the check that fails sends the
    checkout back to the sha it was at and installs that again; the result says what failed. Never raises. The version does not
    have to grow (unlike `updates.install`)."""
    way = way or updates.method()
    try:
        if way.kind != "git" or not way.can:
            return updates.Result(False, way.why or f"{brand.name()} was not installed from git")
        why = _dirty(way.cwd, run)
        if why:
            return updates.Result(False, why)
        old = head(way.cwd, run)
        if not old:
            return updates.Result(False, "the checkout's HEAD cannot be read")
        out: list[str] = []
        failed = ""
        for step in way.steps:
            done = run(list(step), capture_output=True, text=True, timeout=updates.INSTALL_TIMEOUT_S)
            out.append(f"$ {' '.join(step)}\n{(done.stdout or '').strip()}\n{(done.stderr or '').strip()}".strip())
            if done.returncode != 0:
                failed = "the update did not install"
                break
        python = way.python or sys.executable
        if not failed:
            for check in ([python, "-c", CHECK_IMPORT], [python, "-m", profile.current().entry, "--version"]):
                done = run(check, capture_output=True, text=True, timeout=CHECK_TIMEOUT_S, cwd=way.cwd)
                out.append(f"$ {' '.join(check[:2])} …\n{(done.stdout or '').strip()}\n{(done.stderr or '').strip()}".strip())
                if done.returncode != 0:
                    failed = f"{brand.name()} does not start on the new code"
                    break
        if failed:
            back = rollback(old, run, way)
            out.append(f"{failed}; the checkout went back to {old[:7]}" + ("" if back.ok else " (and the reset itself failed)"))
            out.append(back.output)
            return updates.Result(False, "\n".join(x for x in out if x)[-4000:])
        return updates.Result(True, "\n".join(out)[-4000:], updates.installed_version(run, way.python))
    except (OSError, subprocess.SubprocessError) as e:
        return updates.Result(False, f"{type(e).__name__}: {e}")


# -- the sha a restart comes from ------------------------------------------------------------------------------

def good_path() -> Path:
    return repair_dir() / "last-good.json"


def remember_good(old: str, now: float | None = None) -> None:
    """The restart that follows comes from `old`: `board_host.main` hands it to the new process as ORKCRAFT_REPAIRED."""
    _write_json(good_path(), {"sha": old, "at": time.time() if now is None else now, "rolled_back": False, "told": False})


def last_good(now: float | None = None, fresh: float | None = FRESH_S) -> dict:
    """`last-good.json`, {} when there is none (or it is older than `fresh` seconds, when `fresh` is given)."""
    data = _read_json(good_path())
    if not data.get("sha"):
        return {}
    if fresh is not None and (time.time() if now is None else now) - float(data.get("at") or 0) > fresh:
        return {}
    return data


def pending(old: str) -> bool:
    """Whether the restart on a fix has not come up yet: `last-good.json` still names `old`."""
    data = _read_json(good_path())
    return bool(old) and data.get("sha") == old and not data.get("rolled_back")


def mark_rolled_back(old: str) -> None:
    """The new code did not start and the checkout went back to `old`; the file stays so the host can say it once."""
    data = _read_json(good_path())
    _write_json(good_path(), {**data, "sha": old, "rolled_back": True, "told": False})


def came_up() -> None:
    """The server is serving: a restart that was waiting to be proven is. Takes the file away, unless it says a rollback not told yet."""
    data = _read_json(good_path())
    if data and (not data.get("rolled_back") or data.get("told")):
        try:
            good_path().unlink()
        except OSError:
            pass


def rolled_back() -> str:
    """The sha the checkout went back to, when the last restart on a fix did not start and the person has not been told; else ""."""
    data = _read_json(good_path())
    return str(data.get("sha") or "") if data.get("rolled_back") and not data.get("told") else ""


def told() -> None:
    data = _read_json(good_path())
    if data:
        _write_json(good_path(), {**data, "told": True})


def fall_back(old: str, why: BaseException, argv: list[str], restart: Callable | None = None) -> int:
    """The restart on a fix did not come up (`board_host.main`: `run` raised before the server served): the checkout goes back to `old`,
    the install step runs again, and Orkboard opens on the old code with the same arguments (the same port), so the phone comes
    back (spec 119 §3.4). The next start says it once (gui/repair.py). Returns 1 where `restart` returns (a test's)."""
    sys.stderr.write(f"orkboard: it did not start on the fix ({type(why).__name__}: {why}); going back to {old[:7]}\n")
    result = rollback(old)
    mark_rolled_back(old)
    if not result.ok:
        sys.stderr.write(f"orkboard: the way back did not finish cleanly:\n{result.output}\n")
    os.environ.pop(REPAIRED_ENV, None)
    (restart or updates.restart)(argv)
    return 1


def guard_environment(env: dict[str, str] | None = None) -> dict[str, str]:
    """The environment of the process a restart makes: ORKCRAFT_REPAIRED=<old sha> when a fix's update was just remembered."""
    env = os.environ if env is None else env
    good = last_good()
    if good and not good.get("rolled_back"):
        env[REPAIRED_ENV] = str(good["sha"])
    return env  # type: ignore[return-value]
