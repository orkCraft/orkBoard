"""A proposal about a party (docs/specs/43-party-measured.md §4.2): a checker that found nothing in the last eight check tasks of a
goal was proposed to leave that goal's party; the person takes it out or keeps it. The night that wrote these proposals is gone (spec
99 §3): none is written now, one already waiting is still shown and answered.

    party_proposals.waiting(state_dir, goal)              # {"by", "runs", "usd", "at"} | None
    party_proposals.rows(root, state_dir, goals)          # Needs you's `party` rows
    party_proposals.answer(root, state_dir, goal, take)   # the party without the checker, or a decline; the file goes

A goal has one proposal waiting (`<state_dir>/goals/<slug>/party-proposal.json`); a decline is kept in `party-declined.jsonl` and holds
until eight new clean checks come after it. No face, no model.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from orkboard.realm import goal_team, ideas, library, party_work, roles

PROPOSAL, DECLINED = "party-proposal.json", "party-declined.jsonl"


def _folder(state_dir: Path, goal: str) -> Path:
    return ideas.goal_folder(state_dir, goal)


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def waiting(state_dir: Path, goal: str) -> dict | None:
    got = ideas._json(_folder(state_dir, goal) / PROPOSAL)
    return got if isinstance(got, dict) and isinstance(got.get("by"), str) else None


def declines(state_dir: Path, goal: str) -> list[dict]:
    try:
        lines = (_folder(state_dir, goal) / DECLINED).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and isinstance(row.get("by"), str):
            out.append(row)
    return out


def drop_left(root: Path, state_dir: Path, goal: str) -> None:
    """The goal's waiting proposal removed when its checker is no longer in the goal's party."""
    p = waiting(state_dir, goal)
    if p is not None and p["by"] not in goal_team.team_of(root, goal):
        try:
            (_folder(state_dir, goal) / PROPOSAL).unlink()
        except OSError:
            pass


def _name(state_dir: Path, slug: str) -> str:
    r = roles.role(state_dir, slug)
    a = library.get(slug)
    return (r or {}).get("name") or (a.name if a else slug)


def rows(root: Path, state_dir: Path, goals: list[dict]) -> list[dict[str, Any]]:
    """Needs you's `party` rows, one a goal that has a proposal waiting (the checker must still be in its party)."""
    out = []
    for g in goals:
        p = waiting(state_dir, g["slug"])
        if p is None or p["by"] not in goal_team.team_of(root, g["slug"]):
            continue
        usd = p.get("usd")
        out.append({"idea": "", "goal": g["slug"], "kind": "party", "by": p["by"],
                    "title": f"Take {_name(state_dir, p['by'])} out of {g['title']}'s party?",
                    "text": f"It found nothing in the last {int(p.get('runs') or party_work.QUIET_RUN)} goals"
                            + (f"; a check costs about ${usd:.2f}." if isinstance(usd, (int, float)) else "."),
                    "priority": g["priority"], "blocks": False, "at": str(p.get("at") or "")})
    return out


def answer(root: Path, state_dir: Path, goal: str, take: bool, reason: str = "") -> str:
    """Take the checker out of the goal's party (its `every` too; the goal is not read again) or keep it (a decline row); the proposal's
    file goes either way. The checker's slug."""
    p = waiting(state_dir, goal)
    if p is None:
        raise ValueError("That proposal is gone")
    by = p["by"]
    if take:
        team = goal_team.team_of(root, goal)
        goal_team.set_team(root, goal, [s for s in team if s != by], [s for s in goal_team.every_of(root, goal) if s != by])
    else:
        row = {"by": by, "at": now_iso(), "reason": " ".join(str(reason or "").split())[:300]}
        path = _folder(state_dir, goal) / DECLINED
        with ideas.LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    try:
        (_folder(state_dir, goal) / PROPOSAL).unlink()
    except OSError:
        pass
    return by
