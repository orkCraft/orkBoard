"""What each step of a goal's route needs of its seats' tools, and which seat's tool cannot (docs/specs/168 C4, decisions §283.16.6). Pure code, no model, no face: the Board's map reads it into each idea's `steps`.

    step_needs.of_kinds(["tests", "code"])             # ["git", "browser"]: what the work of those kinds needs, in a stable order
    step_needs.steps(node, goals)                      # [{party, leader, own, needs, seats: [{slug, name, head, tool, needs, lacks, marked}], marked}] for the route's steps

A task's kind decides what it needs: work that changes files commits (git's index), a test or a look at a screen starts a browser, finding out or publishing reaches the network. A step with no task yet
(a spec's steps) takes the kinds its party's craft makes. `lacks` is what the seat's tool cannot do (`harnesses.lacking`); `marked` says the page draws a **!** on the seat. A seat on the Main tool (no tool
named yet) lacks nothing: nothing is said of what is not known.
"""
from __future__ import annotations

from orkboard.realm import harnesses, roles

NEEDS_OF = {"code": ("git",), "tests": ("git", "browser"), "docs": ("git",), "text": ("git",), "art": ("git",), "design": ("git", "browser"), "uikit": ("git", "browser"),
            "a11y": ("browser",), "playtest": ("browser",), "artcheck": ("browser",), "research": ("network",), "seo": ("network",), "aso": ("network",), "campaign": ("network",),
            "community": ("network",), "experiment": ("network",), "metrics": ("network",)}
CRAFT_KINDS = {"engineering": ("code", "tests"), "design": ("design",), "art": ("art",), "data": ("data", "query"), "marketing": ("campaign",), "product": ("docs",)}
ORDER = ("git", "browser", "network")
_KIND_OF = {label: kind for kind, label in roles.KIND_LABELS.items()}       # a task row carries its kind's label (`tag`)


def of_kinds(kinds) -> list[str]:
    """What the work of these task kinds needs of a tool, in `ORDER`."""
    got = {n for k in kinds for n in NEEDS_OF.get(k, ())}
    return [n for n in ORDER if n in got]


def _kind(task: dict) -> str:
    return str(task.get("kind") or _KIND_OF.get(str(task.get("tag") or ""), ""))


def _parties(node: dict) -> list[str]:
    """The route's parties in order (a goal with none is a goal of its own party's one step)."""
    out: list[str] = []
    for s in node.get("route") or []:
        p = s.get("party") if isinstance(s, dict) and s.get("step") in (None, "party") else None
        if isinstance(p, str) and p and p not in out:
            out.append(p)
    return out or [str(node.get("goal") or "")]


def steps(node: dict, goals: list[dict]) -> list[dict]:
    """The steps of the idea `node` (a row of the map) over the parties `goals`: each party's seats with their tools, what the step's work needs and what each seat's tool lacks."""
    by = {g["slug"]: g for g in goals}
    out = []
    for party in _parties(node):
        g = by.get(party)
        if g is None:
            continue
        mine = [t for t in node.get("tasks") or [] if (t.get("party") or node.get("goal")) == party and t.get("state") != "dropped"]
        step = of_kinds([_kind(t) for t in mine]) if mine else of_kinds(CRAFT_KINDS.get(g.get("party_craft") or g.get("craft") or "", ()))
        lead = g.get("leader") or {}
        seats = []
        for s in [*([{"slug": lead.get("slug", ""), "name": lead.get("name", ""), "head": lead.get("head"), "checks": False}] if lead else []), *(g.get("team") or [])]:
            did = [t for t in mine if ((t.get("by") or {}).get("slug") or "") == s["slug"]]
            tool = (g.get("tools") or {}).get(s["slug"]) or g.get("tool") or ""
            needs = of_kinds([_kind(t) for t in did]) if did else step
            lacks = harnesses.lacking(tool, needs)
            seats.append({"slug": s["slug"], "name": s["name"], "head": s.get("head"), "tool": tool, "tool_name": harnesses.title(tool) if tool else "", "checks": bool(s.get("checks")),
                          "needs": needs, "lacks": lacks, "marked": bool(lacks)})
        out.append({"party": party, "name": g.get("short") or g.get("title") or party, "leader": lead.get("head"), "own": party == node.get("goal"), "needs": step, "seats": seats,
                    "marked": any(s["marked"] for s in seats)})
    return out
