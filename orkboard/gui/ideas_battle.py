"""The battle and the gate, asked when their mat opens (goal "The battle and the gate", stages D and F; decisions §303). Read only: no model, no lease, no file written; neither
answer is in the snapshot (`ideas.board`).

    ideas.battle {idea}        # {idea, against: [{number, title, point, rests: {goals, decisions, tests}}], cost: {calls, usd_high}}: one entry for each conflict of the goal's decision not answered
    ideas.gate_guards {idea}   # {idea, way: "dev" | "main", failing: [{number, title, ids}], files: [{file, ids}], agreeing: [{number, title}], cost}: the decisions the gate's tests name
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import chronicle_decisions, decision_conflicts, decision_refs, decisions_log, goal_branch, idea_target, ideas, spec_sections

NAMED_MAX = 3          # the §N one failing test is read for


def _titles(repo: Path) -> dict[int, str]:
    """The decisions log's titles by number; empty where the project keeps no log."""
    got = decisions_log.path(repo)
    try:
        if got.is_dir():
            rows = chronicle_decisions.read(got)
        elif got.is_file():
            rows = chronicle_decisions.read(got.read_text(encoding="utf-8", errors="replace"))
        else:
            return {}
    except (OSError, ValueError):
        return {}
    return {r["number"]: str(r.get("title") or "") for r in rows}


class Battle:
    """Over the Board's `Ideas`, as `gui/ideas_mats.py`'s `Mats`."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def _goal(self, args: dict) -> str:
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.i.root(make=False), slug) is None:
            raise IdeasError(f"No goal {slug!r}")
        return slug

    def battle(self, args: dict) -> dict:
        slug = self._goal(args)
        repo = Path(self.i.host.repo_root)
        titles = _titles(repo)
        decision = spec_sections.record(self.i.state_dir, slug).get("decision")
        against = [{"number": c["number"], "title": titles.get(c["number"], ""), "point": c["point"], "rests": decision_refs.rests_on(repo, c["number"])}
                   for c in decision_conflicts.open_of(decision)]
        return {"idea": slug, "against": against, "cost": self.i._cost_of_word(slug)}

    def _last_gate(self, slug: str) -> tuple[str, list[str], list[str]]:
        """(way, the failing test ids, the test files the run ran) of the goal's last gate: on its branch unmerged, the way to dev (stage E's record); else the way to main (the Tests step's record)."""
        if goal_branch.in_use(self.i.state_dir, slug):
            rec = goal_branch.read(self.i.state_dir, slug)
            return "dev", [str(x) for x in rec.get("failing") or []], [str(x) for x in rec.get("files") or []]
        with self.i._main_lock:
            steps = list((self.i._main_checks.get(slug) or {}).get("checks") or [])
        ids = [str(f["id"]) for s in steps for f in s.get("failures") or [] if isinstance(f, dict) and f.get("id")]
        files = [str(x) for s in steps for x in s.get("files") or []]
        return "main", list(dict.fromkeys(ids)), list(dict.fromkeys(files))

    def gate_guards(self, args: dict) -> dict:
        slug = self._goal(args)
        way, ids, ran = self._last_gate(slug)
        repo = Path(self.i.host.repo_root)
        titles = _titles(repo)
        by_number: dict[int, list[str]] = {}
        by_file: dict[str, list[str]] = {}
        for g in decision_refs.guards(repo, ids, limit=NAMED_MAX):
            if g["decisions"]:
                for n in g["decisions"]:
                    by_number.setdefault(n, []).append(g["id"])
            else:
                by_file.setdefault(g["file"], []).append(g["id"])
        cost = {"calls": 1, "usd_high": idea_target.budget("task", idea_target.target_for(self.i.settings_now()))} if way == "dev" else None
        return {"idea": slug, "way": way,
                "failing": [{"number": n, "title": titles.get(n, ""), "ids": v} for n, v in sorted(by_number.items())],
                "files": [{"file": f, "ids": v} for f, v in sorted(by_file.items())],
                "agreeing": [{"number": n, "title": titles.get(n, "")} for n in decision_refs.named_by(repo, ran) if n not in by_number],
                "cost": cost}


def battle_commands(ideas_: Any) -> dict:
    """The battle's commands by name (`gui/ideas.py` adds them to its table: `**battle_commands(self)`)."""
    b = Battle(ideas_)
    return {"ideas.battle": b.battle, "ideas.gate_guards": b.gate_guards}
