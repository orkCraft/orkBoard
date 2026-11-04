"""🛑 Halt All for everything the camp runs: agents, model calls, scripts, tests and browsers.

Every child process orkcraft starts for work is registered here (`started` / `ended`, or the
`running` context), with who runs it (`who`: "<building>/<ork>" or the tool) and whether it is an agent
(a model at work: `agent=True`). It is the one list of what runs: `live()` and `agents()` read it (the
HUD's agent count), `halt_all` kills them all — the whole process group, so a harness's own
children go too — and moves the halt count on, so a loop that was between two steps (a browser
scout, a repair, a batch of judgements) sees `stopped_since` and gives up instead of starting the
next one. A process killed by the halt raises `Halted` (an InterruptedError) in its caller, never a
plain failure, so nothing reads a halt as "the model failed".

**What a halt stopped is kept** (docs/specs/139-the-die-the-door-and-the-bug.md B.1, decisions §246.3): `halt_all(again=…)` records each killed run's owner (`who`) and what the caller says
to start it again (a task's `(slug, tid)`, or whatever the caller can start from: an opaque tuple), `stopped()` lists them (and is true after any halt until `resume()`), `resume()` clears the list and
returns it. The list is this process's; the host keeps the *project* stopped in its state dir so a restart keeps it (gui/ideas_halt.py).
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
from contextlib import contextmanager
from typing import Iterator

_LOCK = threading.Lock()
_LIVE: dict[subprocess.Popen, tuple[str, bool]] = {}     # a process → (who runs it, is it an agent)
_KILLED: set[int] = set()            # pids the halt killed (their callers raise Halted)
_COUNT = 0                           # how many halts so far
_STOPPED: list[dict] = []            # what the halts since the last resume stopped: {"who", "again"} (again: what starts it anew, or None)
_HALTED = False                      # a halt came and no resume since


class Halted(InterruptedError):
    """The work was stopped by 🛑 Halt All."""

    def __init__(self, what: str = "stopped by Halt All") -> None:
        super().__init__(what)


class Stopped(RuntimeError):
    """A short model call (`claude -p`) the halt killed: callers that read RuntimeError as "the model
    failed" stay safe; those that must not mistake it (the Lookout) catch it first."""

    def __init__(self) -> None:
        super().__init__("stopped by Halt All")


def count() -> int:
    with _LOCK:
        return _COUNT


def stopped_since(seen: int) -> bool:
    """A halt came after `seen` (a `count()` taken when the work started)."""
    return count() != seen


def check(seen: int) -> None:
    """Between two steps of a long job: raise `Halted` when a halt came since `seen`."""
    if stopped_since(seen):
        raise Halted()


def started(proc: subprocess.Popen, who: str = "", agent: bool = False) -> subprocess.Popen:
    with _LOCK:
        _LIVE[proc] = (who, agent)
    return proc


def ended(proc: subprocess.Popen) -> None:
    """Forget the process; raise `Halted` when the halt is what ended it."""
    with _LOCK:
        _LIVE.pop(proc, None)
        killed = proc.pid in _KILLED
        _KILLED.discard(proc.pid)
    if killed:
        raise Halted()


@contextmanager
def running(proc: subprocess.Popen, who: str = "", agent: bool = False) -> Iterator[subprocess.Popen]:
    """`with halt.running(Popen(...)) as proc:` — registered while it runs; `Halted` if the halt killed it."""
    started(proc, who, agent)
    try:
        yield proc
    except BaseException:
        with _LOCK:
            _LIVE.pop(proc, None)
            killed = proc.pid in _KILLED
            _KILLED.discard(proc.pid)
        if killed:
            raise Halted() from None
        raise
    ended(proc)


def live() -> list[tuple[str, bool]]:
    """(who, agent) of every registered process that still runs."""
    with _LOCK:
        return [entry for p, entry in _LIVE.items() if p.poll() is None]


def agents() -> int:
    """How many agents run now (a model at work), whoever started them."""
    return sum(1 for _who, agent in live() if agent)


def _kill(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix" and os.getpgid(proc.pid) == proc.pid:      # its own session: the whole group
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (OSError, ProcessLookupError):
        pass


def halt_all(again: list | tuple = ()) -> int:
    """Kill every registered process that still runs; the number killed. Each killed run's owner is kept (`stopped()`), and so is each of `again` (what to start anew: a task's
    `(slug, tid)`) the caller gives; a second halt before a resume adds to the list."""
    global _COUNT, _HALTED
    with _LOCK:
        _COUNT += 1
        _HALTED = True
        live = [p for p in _LIVE if p.poll() is None]
        _KILLED.update(p.pid for p in live)
        _STOPPED.extend({"who": _LIVE[p][0], "again": None} for p in live)
        _STOPPED.extend({"who": "", "again": tuple(a) if isinstance(a, (list, tuple)) else a} for a in again if a not in [e["again"] for e in _STOPPED])
    for p in live:
        _kill(p)
    return len(live)


def stopped() -> list[dict]:
    """What the halts since the last `resume()` stopped: `{"who", "again"}` each; empty when nothing was stopped (a halt with nothing running leaves it empty, and `halted()` true)."""
    with _LOCK:
        return [dict(e) for e in _STOPPED]


def halted() -> bool:
    """A halt came and no `resume()` since."""
    with _LOCK:
        return _HALTED


def resume() -> list[dict]:
    """Clear what the halts stopped and return it (to start each `again` anew)."""
    global _HALTED
    with _LOCK:
        got = [dict(e) for e in _STOPPED]
        _STOPPED.clear()
        _HALTED = False
    return got


def run(argv: list[str], *, input: str | None = None, timeout: float | None = None,
        who: str = "", agent: bool = False, **popen: object) -> subprocess.CompletedProcess:
    """`subprocess.run(..., capture_output=True, text=True)` that Halt All can stop (its own process
    group). Raises subprocess.TimeoutExpired like it, and `Halted` when the halt killed it."""
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE if input is not None else None, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True, **popen)
    with running(proc, who, agent):
        try:
            out, err = proc.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(proc)
            proc.communicate()
            raise
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def reset() -> None:
    """Tests: forget everything."""
    global _COUNT, _HALTED
    with _LOCK:
        _LIVE.clear()
        _KILLED.clear()
        _STOPPED.clear()
        _HALTED = False
        _COUNT = 0
