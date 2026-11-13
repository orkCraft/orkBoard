"""Every wait with why, until when and how to skip it (docs/design/ork-console.md §19).

    w = status.timer(240, skip=status.Skip("start", "Start now", {"task": "t1"}))
    w.line                         # "starts on its own in 4 min"
    w.as_dict(now)                 # {why, line, until, in_s, skip: {act, label, args}}

    status.held("Claude Code", reset, by=status.BY_TOOL, skip=…)   # ⏳ held for a limit's reset
    status.reset_of(town.limits, "claude", now)       # when the tool's spent window comes back (epoch s) | None

The words are the plain ones (CLAUDE.md, Wording). Pure module, no face.
"""
from __future__ import annotations

import datetime as dt
import time
from dataclasses import asdict, dataclass, field

# Why something waits (§19). Each has its line; a wait with no line here is a bug (§19).
APPROVAL = "approval"      # its plan / draft / new persona waits for the person's yes
ANSWER = "answer"          # its ork asked: waits for the person's answer
TIMER = "timer"            # starts (or is decided) on its own after a while (Autonomy)
AFTER = "after"            # another task first
AREA = "area"              # an older task works on the same files
ORK = "ork"                # its own ork (a follow-up) is busy
SLOT = "slot"              # no free ork slot
HIRING = "hiring"          # an ork is being hired for it
LIMIT = "limit"            # held for a limit's reset, or the budget is spent
STEWARD = "steward"        # the steward sorts or plans it
QUIET = "quiet"            # quiet hours
PAUSED = "paused"          # the person paused the building
QUEUE = "queue"            # next in line, nothing else holds it
WAITS = (APPROVAL, ANSWER, TIMER, AFTER, AREA, ORK, SLOT, HIRING, LIMIT, STEWARD, QUIET, PAUSED, QUEUE)


@dataclass
class Skip:
    """The way past a wait: a building's act (`act` with `args`) under a plain label (Approve, Start now…)."""
    act: str
    label: str
    args: dict = field(default_factory=dict)


@dataclass
class Wait:
    why: str                         # one of WAITS
    line: str                        # what the person reads: "after «Fix the login»"
    until: float | None = None       # epoch seconds when it ends by itself; None: it does not
    skip: Skip | None = None

    def as_dict(self, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        return {"why": self.why, "line": self.line, "until": self.until,
                "in_s": max(round(self.until - now), 0) if self.until is not None else None,
                "skip": asdict(self.skip) if self.skip else None}


def when(seconds: float, now: float | None = None) -> str:
    """"in 4 min" for a short while, "at 14:00" for a longer one (today), "on Oct 15, 08:00" past today."""
    seconds = max(seconds, 0)
    if seconds < 60:
        return "in under a minute"
    if seconds < 3600:
        return f"in {round(seconds / 60)} min"
    now = time.time() if now is None else now
    at = dt.datetime.fromtimestamp(now + seconds)
    today = dt.datetime.fromtimestamp(now).date()
    return f"at {at:%H:%M}" if at.date() == today else f"on {at:%b} {at.day}, {at:%H:%M}"


def timer(seconds: float, what: str = "starts on its own", skip: Skip | None = None, now: float | None = None) -> Wait:
    now = time.time() if now is None else now
    return Wait(TIMER, f"{what} {when(seconds, now)}", now + max(seconds, 0), skip)


# Held for a limit (§19, town-time.md §4): who held it, and the way past it.
BY_TOOL, BY_TOWN = "tool", "town"     # the AI tool said its limit is hit · the town held it, the window nearly spent
SPENT = 0.02                          # a window with this share or less left is spent
NEARLY = 0.05                         # … this or less: the town holds new work until it resets
UNKNOWN_RESET_S = 15 * 60             # a reset nobody can read: the work is tried again after this


def _reset_s(lim) -> float | None:
    reset = getattr(lim, "reset", None)
    if reset is None:
        return None
    return reset.timestamp() if isinstance(reset, dt.datetime) else float(reset)


def reset_of(limits, provider: str, now: float | None = None, below: float = SPENT) -> float | None:
    """When `provider`'s window comes back (epoch seconds), from the quota readers' last read (`town.limits`): the
    latest reset among its windows with `below` or less left (all of them must come back), else None — nothing read
    as spent, or no reset read."""
    now = time.time() if now is None else now
    resets = [r for lim in limits or () if getattr(lim, "provider", "") == provider
              and getattr(lim, "remaining", None) is not None and lim.remaining <= below
              and (r := _reset_s(lim)) is not None and r > now]
    return max(resets) if resets else None


def held(tool: str, until: float | None, by: str = BY_TOOL, skip: Skip | None = None, now: float | None = None,
         known: bool = True) -> Wait:
    """The wait of work held for a limit, in plain words, with until when. A reset nobody could read (`known`
    False, or no `until`) is said so: the work is tried again at `until` (UNKNOWN_RESET_S from now when None)."""
    now = time.time() if now is None else now
    if until is None:
        until, known = now + UNKNOWN_RESET_S, False
    if by == BY_TOWN:
        line = f"held by the Treasurer until the {_clock(until, now)} reset: {tool}'s window is nearly spent"
    elif known:
        line = f"held: {tool} hit its usage limit · it resets {when(until - now, now)}"
    else:
        line = f"held: {tool} hit its usage limit · when it resets is not known, tried again {when(until - now, now)}"
    return Wait(LIMIT, line, until, skip)


def _clock(at: float, now: float) -> str:
    then = dt.datetime.fromtimestamp(at)
    return f"{then:%H:%M}" if then.date() == dt.datetime.fromtimestamp(now).date() else f"{then:%b} {then.day}, {then:%H:%M}"

