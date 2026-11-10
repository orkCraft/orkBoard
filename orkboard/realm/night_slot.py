"""The night's slot (docs/specs/168 H2, decisions §283.31, §283.32): the rungs of *The night* as the Orkmaster's slot draws them, read and written
through the ladder's own settings (`orkboard/settings.py` `night_rung`, `night_values`: spec 168 H3), so the slot and the night's engine say one thing.

    WAYS                       # (value, word, line): "off", "ideas", "builds", "proposals", in the ladder's order
    way(settings)              # the rung the settings say now (`settings.night_rung`: the old `work_at_night` read with it)
    keys(value, leaders=None)  # the settings a rung writes (`settings.night_values`: `night_rung`, `work_at_night` in step, the leaders picked)
"""
from __future__ import annotations

from orkboard import settings as _settings

WAYS = (
    ("off", "Off", "Nothing runs at night"),
    ("ideas", "Ideas and specs", "Talk and the specs of the goals in line; nothing is built"),
    ("builds", "And the builds", "What was agreed by day is built in the night's window"),
    ("proposals", "And the leaders' proposals", "The leaders you pick may propose a goal each, to a ready spec; nothing is built without your press"),
)
VALUES = tuple(v for v, _w, _l in WAYS)
assert VALUES == _settings.NIGHT_RUNGS, "the slot's rungs are the ladder's"
REFUSED = "The night is off, ideas and specs, and the builds, or and the leaders' proposals"


def way(settings: dict) -> str:
    """The rung now, as the night's engine reads it."""
    return _settings.night_rung(settings)


def keys(value: str, leaders: object = None) -> dict:
    """What a rung writes: the rung, `work_at_night` kept in step (true from the builds up) and, when given, the leaders picked."""
    if value not in VALUES:
        raise ValueError(REFUSED)
    return _settings.night_values(value, leaders)
