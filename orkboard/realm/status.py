"""When a spent AI tool window comes back: the limits the quota readers last read, as epoch seconds.

    status.reset_of(limits, "claude", now)       # when the tool's spent window comes back (epoch s) | None

The words are the plain ones (CLAUDE.md, Wording). Pure module, no face.
"""
from __future__ import annotations

import datetime as dt
import time

SPENT = 0.02                          # a window with this share or less left is spent
NEARLY = 0.05                         # … this or less: the Board holds new work until it resets
UNKNOWN_RESET_S = 15 * 60             # a reset nobody can read: the work is tried again after this


def _reset_s(lim) -> float | None:
    reset = getattr(lim, "reset", None)
    if reset is None:
        return None
    return reset.timestamp() if isinstance(reset, dt.datetime) else float(reset)


def reset_of(limits, provider: str, now: float | None = None, below: float = SPENT) -> float | None:
    """When `provider`'s window comes back (epoch seconds), from the quota readers' last read: the
    latest reset among its windows with `below` or less left (all of them must come back), else None — nothing read
    as spent, or no reset read."""
    now = time.time() if now is None else now
    resets = [r for lim in limits or () if getattr(lim, "provider", "") == provider
              and getattr(lim, "remaining", None) is not None and lim.remaining <= below
              and (r := _reset_s(lim)) is not None and r > now]
    return max(resets) if resets else None
