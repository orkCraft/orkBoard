"""A goal looked at from a leader's tab (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.3; decisions §206.8), as `gui/ideas.py`'s `Ideas` has it: what a goal that is done
changed against what its spec promised, by code (realm/goal_result.py), with no model.

    ideas.goal_result {idea}      # {idea, state, parties: [{party, title, parts: [{id, kind, verdict, line, note}], done_when: [{text, state}]}], files, screens: [{screen, name, path}]}
                                  # `verdict`: ok (As promised) · differs (Not quite) · missing (Not done) · extra (More than promised); a *Done when* line `state` "ok" or ""
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import goal_result, goal_team, ideas, spec_sections


class GoalViewMixin:
    """Needs `host`, `state_dir`, `root()`, `_ref()` (gui/ideas.py, gui/ideas_assets.py)."""

    def goal_result(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        root = self.root(make=False)
        page = ideas.idea_page(root, slug)
        if page is None:
            raise IdeasError("That goal is gone")
        state = str(ideas.state(self.state_dir, slug).get("state") or "")
        tracks = ideas.tracks(root, make=False)
        home = str(page.get("track") or ideas.GENERAL)
        sections = spec_sections.read(page, [{"slug": t["slug"], "title": t["title"]} for t in tracks], home)["sections"]
        plan = ideas.plan(self.state_dir, slug) or {}
        crafts = {t["slug"]: goal_team.craft_of(root, t["slug"]) for t in tracks}
        touch = goal_result.touched(self.state_dir, Path(self.host.repo_root), slug, self._ref()) if state == "done" else None
        return {"idea": slug, "state": state, **goal_result.of(sections, plan.get("tasks") or [], touch, state == "done", crafts, home)}


def goalview_commands(ideas_: Any) -> dict:
    """The goal's view by name (`gui/ideas.py` adds it to its table: `**goalview_commands(self)`)."""
    return {"ideas.goal_result": ideas_.goal_result}
