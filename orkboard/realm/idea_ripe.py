"""A goal the leaders agreed on, and the wait before it starts by itself (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §3.3–§3.6; decisions §198.4–§198.5). Pure code, no model,
no face; `core/idea_verdict.py` begins the wait, `gui/ideas_route.py` ticks it, `core/idea_decide.py` writes the decision when it ends.

    weight(stances, how, gist="")          # {priority, risk}: Product's priority (none: normal); the risk Tech gave, raised by `idea_risk`'s rules that no model talks down
    outcome(rec, has_product)              # what the verdicts of a Talk's record make: "hearing" (any no or doubt) · "agreed" · "decision" (all go, but nobody could weigh it)
    wait_s(priority, risk)                 # the seconds the wait lasts (60 or 600), None for no wait: the decision's card as it always was
    begin(state_dir, slug, priority, risk) # the wait written beside the goal's decision (`way.json` `ripe`), None when there is none to wait for
    hold(state_dir, slug, by, why)         # the wait stopped: the time gone, the goal waits for the person's Start (`ideas.ripe_hold`); the time that was left, None with no wait
    tick(state_dir, slugs, dt)             # `dt` seconds taken from each running wait; the slugs whose wait has ended
    done(state_dir, slug) / drop(...)      # the wait ended by the leaders, written · forgotten (the decision was confirmed by the person, or the goal went)

The wait is `ripe` in `way.json` (`spec_sections.record`): `{left_s, seconds, risk, priority, held, by, why}`; `by` is "" while it runs, "leaders" once it ended, "person" once held.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import idea_risk, ideas, spec_sections

HURRY_S, USUAL_S = 60, 600        # a high priority at low risk waits a minute; what the plan's autostart would start waits ten (spec 120 §3.5)


def _craft_of(s: dict, key: str, craft: str) -> bool:
    return s.get("craft") == craft or (not s.get("craft") and bool(s.get(key)))


def weight(stances: list[dict], how: dict | None, gist: str = "") -> dict:
    """The goal's weight (spec 120 §3.3): `priority` is Product's (none gave one: `normal`); `risk` is `idea_risk.assess(touches=how.touched, texts=[the gist, Tech's against],
    risk_model=Tech's risk or "low")`, so the rules no model talks down (secrets, data, CI, a public API, wide) still raise it."""
    stances = [s for s in stances or [] if isinstance(s, dict)]
    priority = next((s["priority"] for s in stances if _craft_of(s, "priority", "product") and s.get("priority") in ideas.PRIORITIES), "normal")
    tech = next((s for s in stances if _craft_of(s, "risk", "tech") and (s.get("risk") or s.get("against"))), {})
    got = idea_risk.assess(touches=[str(t) for t in (how or {}).get("touched") or []], texts=[gist or "", str(tech.get("against") or "")], risk_model=tech.get("risk") or "low")
    return {"priority": priority, "risk": got.risk}


def outcome(rec: dict, has_product: bool) -> str:
    """What a Talk's verdicts make (spec 120 §3.4), from its record: any `no` or `doubt` is a **hearing**; all `go` with Product's word (`has_product`: Product was on the route or weighed
    the goal) is **agreed**, and so is a goal nobody could ask Product about when its risk is `low` only; all `go` and the risk above `low` with no word of Product's is the **decision**,
    with its card as it always was (*Confirm and start*). A record with no stance (a bug's diagnosis, a Talk not begun) is the decision."""
    stances = [s for s in rec.get("stances") or [] if isinstance(s, dict)]
    if not stances:
        return "decision"
    if any(s.get("verdict") in ("no", "doubt") for s in stances):
        return "hearing"
    risk = (rec.get("weight") or weight(stances, None))["risk"]
    return "agreed" if has_product or risk == "low" else "decision"


def wait_s(priority: str, risk: str, night: bool = False) -> int | None:
    """The seconds the wait lasts (spec 120 §3.5): `idea_risk.decide` says `start` or `night`, a minute for high priority at low risk and ten minutes otherwise; `wait` (the plan would wait for
    the person anyway): None, no wait."""
    priority = priority if priority in ideas.PRIORITIES else "normal"          # a priority nobody knows reads as normal
    if idea_risk.decide(risk, priority, night) == "wait":
        return None
    return HURRY_S if idea_risk.level(risk) == "low" and priority == "high" else USUAL_S


# -- the wait, kept beside the decision ------------------------------------------------------------------------------------------------

def of(state_dir: Path, slug: str) -> dict | None:
    """The goal's wait as it is kept, None with none (or one that is not a wait)."""
    got = spec_sections.record(state_dir, slug).get("ripe")
    return got if isinstance(got, dict) and isinstance(got.get("left_s"), (int, float)) and not isinstance(got.get("left_s"), bool) else None


def _keep(state_dir: Path, slug: str, ripe: dict | None) -> None:
    with ideas.LOCK:
        way = spec_sections.record(state_dir, slug)
        if ripe is None:
            way.pop("ripe", None)
        else:
            way["ripe"] = ripe
        spec_sections.save_record(state_dir, slug, way)


def begin(state_dir: Path, slug: str, priority: str, risk: str) -> dict | None:
    """The wait begun beside the goal's decision: `{left_s, seconds, risk, priority, held: False, by: "", why: ""}`; None when the plan would not start it by itself (no wait)."""
    seconds = wait_s(priority, risk)
    if seconds is None:
        return None
    ripe = {"left_s": float(seconds), "seconds": seconds, "risk": idea_risk.level(risk), "priority": str(priority), "held": False, "by": "", "why": ""}
    _keep(state_dir, slug, ripe)
    return ripe


def running(state_dir: Path, slug: str) -> bool:
    """The goal's wait counts down: not held, not ended."""
    r = of(state_dir, slug)
    return r is not None and not r.get("held") and not r.get("by")


def hold(state_dir: Path, slug: str, by: str = "person", why: str = "") -> float | None:
    """**Hold** (`ideas.ripe_hold`): the wait stopped, the time gone; the goal's top card is its decision with *Start* (`ideas.confirm`, by the person). Returns the time that was left,
    None when there was no wait to hold (or it was held already)."""
    r = of(state_dir, slug)
    if r is None or r.get("held"):
        return None
    left = float(r["left_s"])
    _keep(state_dir, slug, {**r, "left_s": 0.0, "held": True, "by": by, "why": why[:200]})
    return left


def tick(state_dir: Path, slugs: list[str], dt: float) -> list[str]:
    """`dt` seconds taken from the time left of each of `slugs` that counts down (a held or ended wait keeps its time); the slugs whose wait has run out, in the order given."""
    out = []
    for slug in slugs:
        r = of(state_dir, slug)
        if r is None or r.get("held") or r.get("by"):
            continue
        left = max(float(r["left_s"]) - max(float(dt), 0.0), 0.0)
        _keep(state_dir, slug, {**r, "left_s": round(left, 1)})
        if left <= 0:
            out.append(slug)
    return out


def done(state_dir: Path, slug: str) -> None:
    """The wait ended and the leaders confirmed: it stays as it was, `by` "leaders" (the decision's heading says so too)."""
    r = of(state_dir, slug)
    if r is not None:
        _keep(state_dir, slug, {**r, "left_s": 0.0, "by": "leaders"})


def drop(state_dir: Path, slug: str) -> None:
    """The wait forgotten (the decision was worded again, or the goal left its decision)."""
    if of(state_dir, slug) is not None:
        _keep(state_dir, slug, None)
