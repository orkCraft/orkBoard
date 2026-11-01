"""What a goal's card at the Orkmaster says of its Talk, as data (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.3–§6.4; decisions §198.8): the goal's own card lies face down in the
Orkmaster's lane while it is talked over and while its wait runs, so the page needs the route's heads, who has said, a line of each stance that is in, and the wait. A pure read of
what the Board keeps (the goal's state, its Talk's record, the wait beside its decision): it writes nothing, starts nothing and words nothing.

    board_back.of(root, state_dir, slug, st, settings)    # None unless the goal is routed, in Talk or decided;
                                                         # else {route: [{party, leader, head}], cost, offer: [party], short, heard: [party], stances: [{party, leader, stance}], round, ripe}

`route` is the Talk's route (`goal_route.steps_of`: not the history of the goal's moves, which a node's `route` says) with its `cost`, the parties a **+** `offer`s and whether it is a `short` way, as the route card's row has them, so the route is edited on the card's face; `heard` the parties whose leader has answered, as each does (spec 120
§2.3); `stances` the leaders' lines once the round is whole; `ripe` the wait of an agreed goal as it is kept (`idea_ripe.of`: `{left_s, seconds, risk, priority, held, by, why}`), None with no wait.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_route, idea_questions, idea_ripe

STATES = ("routed", "talk", "decided")


def of(root: Path, state_dir: Path, slug: str, st: dict, settings: dict | None = None) -> dict | None:
    """The back of a goal's card (see the module's doc); None for a goal that is not before its sections."""
    if st.get("state") not in STATES:
        return None
    talk = idea_questions.talk_of(state_dir, slug)
    ripe = idea_ripe.of(state_dir, slug) if st["state"] == "decided" else None
    how = st.get("route_how") if isinstance(st.get("route_how"), dict) else {}
    return {"route": goal_route.steps_of(root, state_dir, st, settings), "cost": goal_route.cost_of(root, state_dir, st, settings), "offer": [str(p) for p in how.get("offer") or []], "short": bool(how.get("short")),
            "heard": talk["heard"], "round": talk["round"],
            "stances": [{"party": s["party"], "leader": s["leader"], "stance": s["stance"]} for s in talk["stances"] if s["stance"]],
            "ripe": {k: ripe.get(k) for k in ("left_s", "seconds", "risk", "priority", "held", "by", "why")} if ripe else None}
