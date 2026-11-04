"""The look's wait (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md A; decisions §224.3, §225.1): the one setting *Give me time to look*, and the clock time a spec
made waits until before its plan is passed by itself. Pure: no file, no model, no face.

    CHOICES                              # ("30m", "2h", "tonight", "none")
    DEFAULT                              # "2h"
    clean(choice)                        # a choice as it reads: an unknown value is "2h"
    until(choice, now, night)            # when the look ends, epoch seconds (`now`: epoch seconds; `night`: the night window "01:00-07:00"); None for "none"
    iso(epoch)                           # the clock time as the faces read it, local time, "2026-11-04T13:40:00"
    LINES                                # the line under the setting, for each choice
"""
from __future__ import annotations

import datetime as dt

CHOICES = ("30m", "2h", "tonight", "none")
DEFAULT = "2h"
SECONDS = {"30m": 30 * 60, "2h": 2 * 3600}
LABELS = {"30m": "30 min", "2h": "2 h", "tonight": "until tonight", "none": "do not wait"}
LINES = {"30m": "If you do not look, it starts: you give every spec 30 minutes",
         "2h": "If you do not look, it starts: you give every spec 2 hours",
         "tonight": "If you do not look, it starts: you give every spec until tonight",
         "none": "A spec starts as soon as it is made"}
REFUSED = "Give me time to look is 30 min, 2 h, until tonight or do not wait"


def clean(choice: object) -> str:
    return choice if isinstance(choice, str) and choice in CHOICES else DEFAULT


def _tonight(now: float, night: str) -> float:
    """The night window's next start (its first half, `HH:MM`), today or tomorrow, the person's local time."""
    try:
        h, m = (int(x) for x in str(night).split("-")[0].split(":"))
        dt.time(h, m)
    except (ValueError, IndexError):
        h, m = 1, 0
    here = dt.datetime.fromtimestamp(now)
    start = here.replace(hour=h, minute=m, second=0, microsecond=0)
    if start <= here:
        start += dt.timedelta(days=1)
    return start.timestamp()


def until(choice: object, now: float, night: str = "01:00-07:00") -> float | None:
    """When the look ends if it begins at `now`; None when there is no wait."""
    choice = clean(choice)
    if choice == "none":
        return None
    return now + SECONDS[choice] if choice in SECONDS else _tonight(now, night)


def iso(epoch: float) -> str:
    return dt.datetime.fromtimestamp(float(epoch)).strftime("%Y-%m-%dT%H:%M:%S")
