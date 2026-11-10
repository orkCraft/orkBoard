"""The night's slot (docs/specs/168 H2, decisions §283.31, §283.32): the rungs of *The night* as the Orkmaster's slot draws them. Pure: no file, no model, no face.

    WAYS                       # (value, word, line): "off", "ideas", "builds", "proposals", in the ladder's order
    way(settings)              # the rung the settings say now
    keys(value)                # the settings a rung writes: `{"night_way": value, "work_at_night": bool}`

**The one place the slot reads the night.** The ladder's engine (spec 168 H3, `core/idea_night.py`) plugs in here: it keeps the rung in `night_way`
and reads it from the settings; until it does, a setting with no `night_way` reads as today's `work_at_night` (on is *and the builds*, off is *off*),
and the rungs *ideas and specs* and *and the leaders' proposals* are stored, not yet run.
"""
from __future__ import annotations

WAYS = (
    ("off", "Off", "Nothing runs at night"),
    ("ideas", "Ideas and specs", "Talk and the specs of the goals in line; nothing is built"),
    ("builds", "And the builds", "What was agreed by day is built in the night's window"),
    ("proposals", "And the leaders' proposals", "The leaders you pick may propose a goal each, to a ready spec; nothing is built without your press"),
)
VALUES = tuple(v for v, _w, _l in WAYS)
REFUSED = "The night is off, ideas and specs, and the builds, or and the leaders' proposals"


def way(settings: dict) -> str:
    """The rung now: the setting's `night_way`, else what `work_at_night` said before the ladder."""
    got = settings.get("night_way")
    if got in VALUES:
        return got
    return "builds" if settings.get("work_at_night") is True else "off"


def keys(value: str) -> dict:
    """What a rung writes: the rung, and `work_at_night` as the builds' rungs say it (what the night's tick reads today)."""
    if value not in VALUES:
        raise ValueError(REFUSED)
    return {"night_way": value, "work_at_night": value in ("builds", "proposals")}
