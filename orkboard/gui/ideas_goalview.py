"""A goal looked at from a leader's tab (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.3; decisions §206.8), as `gui/ideas.py`'s `Ideas` has it: what a goal that is done
changed against what its spec promised, by code (realm/goal_result.py), with no model.

    ideas.goal_result {idea}      # {idea, state, parties: [{party, title, parts: [{id, kind, verdict, line, note}], done_when: [{text, state}]}], files, screens: [{screen, name, path}], made: [{task, title, files, added, removed, gate}]}
                                  # `verdict`: ok (As promised) · differs (Not quite) · missing (Not done) · extra (More than promised); a *Done when* line `state` "ok" or ""
                                  # `made` (spec 149 H.1): each merged task with the files and lines it changed and its gate in words (*97 passed*), for the result to set beside the *Done when* lines; no model matches them
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import goal_result, goal_team, ideas, spec_sections


def gate_words(tests: object) -> str:
    """A task's gate in a few plain words, as the result's tests line says it (`shell/review.js` `testsWords`): *97 passed*, *2 / 99 failed*, *no tests ran*, *could not run*."""
    t = tests if isinstance(tests, dict) else {}
    passed, failed = t.get("passed"), t.get("failed")
    if t.get("none"):
        return "no tests in this project"
    if t.get("ran") is False:
        return "no tests ran"
    if t.get("env"):
        return "could not run"
    if not isinstance(passed, int) and not isinstance(failed, int):
        code = t.get("exit")
        return "" if code is None else f"passed (exit {code})" if code == 0 else f"failed (exit {code})"
    passed, failed = passed or 0, failed or 0
    if failed:
        return f"{failed} / {passed + failed} failed"
    return f"{passed} passed" if passed else "no tests ran"


def made_of(plan: dict) -> list[dict]:
    """What each merged task of the plan made, `[{task, title, files, added, removed, gate}]` (`files` and its lines left out when the plan kept none)."""
    out = []
    for t in plan.get("tasks") or []:
        if not isinstance(t, dict) or t.get("state") != "merged":
            continue
        d = t.get("diff") if isinstance(t.get("diff"), dict) else {}
        out.append({"task": t.get("id"), "title": str(t.get("title") or ""), **{k: int(d[k]) for k in ("files", "added", "removed") if isinstance(d.get(k), (int, float))},
                    "gate": gate_words(t.get("tests"))})
    return out


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
        return {"idea": slug, "state": state, **goal_result.of(sections, plan.get("tasks") or [], touch, state == "done", crafts, home), "made": made_of(plan)}


def goalview_commands(ideas_: Any) -> dict:
    """The goal's view by name (`gui/ideas.py` adds it to its table: `**goalview_commands(self)`)."""
    return {"ideas.goal_result": ideas_.goal_result}
