"""The treasury: 🪙 this run's spend and 🪵 each session's context against the project's limits, and the subscription
quota. The check of the spend against its cap (`over`), the HUD's words (`words`) and the quota's (`quota`);
`budget(repo_root)` reads the cap from the project's `.orkcraft.json` (spec 37 §4).
"""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.sources import telemetry

GOLD_LIMIT_USD = 20.0           # the defaults, when `.orkcraft.json` names none
LUMBER_LIMIT_TOKENS = 131072


def budget(repo_root: Path) -> tuple[float, int]:
    """(🪙 limit in USD, 🪵 limit in tokens) the repository's `.orkcraft.json` sets (`budget`), read as plain JSON; the
    defaults when there is none."""
    try:
        raw = json.loads((Path(repo_root) / ".orkcraft.json").read_text(encoding="utf-8")).get("budget") or {}
    except (OSError, ValueError, AttributeError):
        raw = {}
    gold, lumber = raw.get("gold_session_limit_usd"), raw.get("lumber_context_limit_tokens")
    ok = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0   # noqa: E731
    return (float(gold) if ok(gold) else GOLD_LIMIT_USD), (int(lumber) if ok(lumber) else LUMBER_LIMIT_TOKENS)


def over(spent: float, limit: float) -> bool:
    """Whether this run's spend reached the 🪙 limit (none when the limit is 0): no new work."""
    return limit > 0 and spent >= limit


def words(snap: telemetry.Snapshot, gold_limit_usd: float, lumber_limit_tokens: int,
          active: str | None = None) -> tuple[str, str, str, str]:
    """(gold, gold level, lumber, lumber level) for the HUD; "—" until a session reports. Lumber is
    the `active` session's context, else the fullest one's."""
    gold_limit = f"${gold_limit_usd:.2f}"
    if snap.sessions or snap.unpriced or snap.side_usd:
        # Unknown is not zero (spec 143 G.2): with nothing priced the gold says no price is known, never `$0.00+`; with some, `+` marks what
        # could not be priced (agy, or a model with no published price).
        if snap.unpriced and not snap.spent_usd:
            gold = f"no price known / {gold_limit}"
        else:
            gold = f"${snap.spent_usd:.2f}{'+' if snap.unpriced else ''} / {gold_limit}"
    else:
        gold = f"$— / {gold_limit}"
    gold_level = telemetry.level(snap.spent_usd, gold_limit_usd)
    ctx = snap.context_by_terminal.get(active) if active else None
    if ctx is None and snap.context_by_terminal:
        ctx = max(snap.context_by_terminal.values())
    lumber_limit = telemetry.fmt_tokens(lumber_limit_tokens)
    lumber = f"{telemetry.fmt_tokens(ctx)} / {lumber_limit}" if ctx is not None else f"— / {lumber_limit}"
    lumber_level = telemetry.level(ctx or 0, lumber_limit_tokens)
    return gold, gold_level, lumber, lumber_level


def subscriptions(machine) -> list[str]:
    """The enabled tools billed by subscription (settings.py): their quota is what runs out."""
    return [t for t, c in machine.tools.items() if c.enabled and c.billing == "subscription"]


def quota(machine, limits: list) -> tuple[str, str, bool]:
    """(quota, its level, whether 🪙 shows): the HUD corner follows each tool's billing — the used
    share still left of the tightest window for a subscription, 🪙 for an API (its level follows what is used)."""
    on = [t for t, c in machine.tools.items() if c.enabled]
    subs = subscriptions(machine)
    if not subs:
        return "", "ok", True
    parts, worst = [], 0.0
    for t in subs:
        left = [x.remaining for x in limits if x.provider == t and x.remaining is not None]
        if left:
            used = round((1 - min(left)) * 100)
            worst = max(worst, used)
            parts.append(f"{t} {100 - used}%")
        else:
            parts.append(f"{t} —")
    return " · ".join(parts), telemetry.level(worst, 100), len(subs) < len(on)
