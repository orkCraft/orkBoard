"""The look's wait (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md A; decisions §224.3, §225.1): the one setting *Give me time to look*, and the clock time a spec
made waits until before its plan is passed by itself. Pure: no file, no model, no face.

    CHOICES                              # ("30m", "2h", "tonight", "none")
    DEFAULT                              # "2h"
    clean(choice)                        # a choice as it reads: an unknown value is "2h"
    until(choice, now, night)            # when the look ends, epoch seconds (`now`: epoch seconds; `night`: the night window "01:00-07:00"); None for "none"
    iso(epoch)                           # the clock time as the faces read it, local time, "2026-11-04T13:40:00"
    LINES                                # the line under the setting, for each choice
    BUILD_STARTS                         # ("now", "30m", "2h", "tonight", "hand"): *The build starts*, `autostart` and `look_wait` as one setting (spec 168 H2, decisions §283.31)
    build_start(autostart, look)         # the one value the two stored keys say: autostart off is "hand"; on, the look's wait ("none" is "now")
    build_start_keys(value, look)        # the two stored keys a value writes (the Board keeps `autostart` and `look_wait`); "hand" leaves the look as it was
"""
from __future__ import annotations

import datetime as dt

CHOICES = ("30m", "2h", "tonight", "none")
DEFAULT = "2h"
SECONDS = {"30m": 30 * 60, "2h": 2 * 3600}
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


# -- *The build starts*: autostart and the look's wait as one setting (spec 168 H2, decisions §283.31) ----------------------------------------------------------
BUILD_STARTS = ("now", "30m", "2h", "tonight", "hand")
BUILD_LABELS = {"now": "At once", "30m": "In 30 min", "2h": "In 2 h", "tonight": "Tonight", "hand": "By hand"}
BUILD_LINES = {"now": "A plan that may start by itself starts as soon as its spec is made",
               "30m": "A spec waits 30 minutes for your look, then its plan starts by itself",
               "2h": "A spec waits 2 hours for your look, then its plan starts by itself",
               "tonight": "A spec waits until tonight's night window, then its plan starts by itself",
               "hand": "Nothing is built until you press Start"}
BUILD_REFUSED = "The build starts at once, in 30 min, in 2 h, tonight or by hand"


def build_start(autostart: object = True, look: object = None) -> str:
    """The value the two stored keys say. `autostart` False is *by hand* whatever the look; else the look's wait, *do not wait* being *at once*."""
    if autostart is False:
        return "hand"
    choice = clean(look)
    return "now" if choice == "none" else choice


def build_start_keys(value: object, look: object = None) -> dict:
    """The keys a value writes: `{"autostart": bool, "look_wait": str}`. *By hand* turns the start off and keeps the look as it was; an unknown value is None."""
    if value == "hand":
        return {"autostart": False, "look_wait": clean(look)}
    if value == "now":
        return {"autostart": True, "look_wait": "none"}
    if value in SECONDS or value == "tonight":
        return {"autostart": True, "look_wait": value}
    return {}
