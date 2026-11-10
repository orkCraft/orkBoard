"""A goal that is a night's proposal still waiting, on the map (docs/specs/168 H3; decisions §283.32): its row carries `proposed` (the night's key), so the column lays it in *Specs* marked *proposed*."""
from __future__ import annotations

from pathlib import Path


def of(state_dir: Path, slug: str) -> dict:
    """`{"proposed": <night key>}` while the goal's proposal waits for the person's Take or Drop, else `{}`."""
    from orkboard.core import idea_night
    row = idea_night.of_goal(state_dir, slug)
    return {"proposed": row.get("night") or "yes"} if row else {}
