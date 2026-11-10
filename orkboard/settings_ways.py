"""The ways of a project's settings that are words, not switches: how it pushes (spec 168 F3, decisions §283.31) and the night's ladder
(spec 168 H3, decisions §283.32). Pure; `orkboard/settings.py` says them as its own (it was past 600 lines: CLAUDE.md, *Where code goes*)."""
from __future__ import annotations

import re

PUSH_WAYS = ("no", "main", "both")        # spec 168 F3 (decisions §283.31): *no*, *main only*, *dev and main*. Stored as a boolean where it can be: False = no, True = both (what the old boolean pushed: dev after a landing, main after To main), "main" = main only


def push_way(value: object) -> str:
    """The way the project pushes: "no", "main" or "both". The old boolean reads as it always did (True = dev and main, False = no); anything else is no."""
    if value is True or value == "both":
        return "both"
    return "main" if value == "main" else "no"


def clean_push_way(value: object) -> object:
    """A push value as it is kept: False, True or "main"; None for a value that is none of the three ways (a boolean, "no", "main", "both")."""
    if isinstance(value, bool):
        return value
    return {"no": False, "both": True, "main": "main"}.get(value) if isinstance(value, str) else None


def pushes_dev(value: object) -> bool:
    return push_way(value) == "both"


def pushes_main(value: object) -> bool:
    return push_way(value) in ("main", "both")


NIGHT_RUNGS = ("off", "ideas", "builds", "proposals")      # spec 168 H3 (decisions §283.32): the night is a ladder, each rung doing what the one below does


# -- the night's ladder (spec 168 H3, decisions §283.32) -----------------------------------------------------------------------------------------

def clean_night_leaders(value: object) -> list[str] | None:
    """The parties whose leaders the night asks for a proposal (slugs, at most 20, no repeats); None when `value` is no list."""
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for v in value:
        if isinstance(v, str) and re.fullmatch(r"[a-z0-9-]{1,100}", v.strip()) and v.strip() not in out:
            out.append(v.strip())
    return out[:20]


def night_rung(settings: dict | None) -> str:
    """The rung of the night's ladder: "off" | "ideas" | "builds" | "proposals". The old `work_at_night` is read as it always was: on means the builds
    (at least); off takes the builds away (a stored "builds" or "proposals" with the old key off reads "ideas": the person turned the builds off by
    the old key). With neither key set the night is off."""
    s = settings or {}
    rung = s.get("night_rung") if s.get("night_rung") in NIGHT_RUNGS else "off"
    old = s.get("work_at_night") is True
    if old and rung in ("off", "ideas"):
        return "builds"
    if not old and rung in ("builds", "proposals"):
        return "ideas"
    return rung


def night_leaders(settings: dict | None) -> list[str]:
    """The parties whose leaders the night asks for a proposal; only the rung "proposals" asks them."""
    got = clean_night_leaders((settings or {}).get("night_leaders"))
    return got if got and night_rung(settings) == "proposals" else []


def night_values(rung: str, leaders: object = None) -> dict:
    """The settings one choice of the ladder writes: the rung, the leaders picked, and the old `work_at_night` kept in step (true from "builds" up)."""
    if rung not in NIGHT_RUNGS:
        raise ValueError("The night is off, ideas and specs, and the builds, or and the leaders' proposals")
    out: dict = {"night_rung": rung, "work_at_night": rung in ("builds", "proposals")}
    if leaders is not None:
        picked = clean_night_leaders(leaders)
        if picked is None:
            raise ValueError("The leaders picked are a list of parties")
        out["night_leaders"] = picked
    return out
