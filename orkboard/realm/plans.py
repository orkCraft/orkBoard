"""🧭 What the Board reads of a plan's parts, by rules (design: docs/design/barracks-planning.md §3–4):

    shift(tier, by)            one tier lighter (-1) or heavier (+1), within the three
    DEFAULT_COST               $ a run of each tier, before the project has a record of its own
    overlap(a, b)              two parts touch the same files
"""
from __future__ import annotations

from orkboard.realm import tiers

DEFAULT_COST = {"elder": 1.0, "warrior": 0.3, "laborer": 0.05}   # $ a run, before the barracks has a record


def shift(tier: str, by: int) -> str:
    """One tier lighter (-1) or heavier (+1), within the three."""
    i = tiers.TIERS.index(tier) if tier in tiers.TIERS else tiers.TIERS.index("warrior")
    return tiers.TIERS[max(0, min(len(tiers.TIERS) - 1, i - by))]       # TIERS runs heaviest first


def overlap(a: list[str], b: list[str]) -> bool:
    """Two parts touch the same files: a path of one is the other's, or inside it."""
    def norm(p: str) -> str:
        return p.strip().lstrip("./").rstrip("/")
    return any(x == y or x.startswith(y + "/") or y.startswith(x + "/") or not x or not y
               for x in map(norm, a) for y in map(norm, b))
