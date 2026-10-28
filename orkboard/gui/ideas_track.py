"""A party removed (docs/specs/80-a-party-removed.md) as `gui/ideas.py`'s `Ideas` has it: `ideas.track_drop`. Split from ideas.py to keep it under ~600 lines."""
from __future__ import annotations

from orkboard.gui.ideas_args import IdeasError, _device, _opt, _text
from orkboard.realm import event_log, goal_team, ideas, party_recipes


class TrackMixin:
    def track_busy(self, slug: str) -> set[str]:
        """The goals of a party the keeper or a runner has in hand now (the realm adds those whose state is `working`)."""
        runs = {s for s, _tid in (getattr(self._runner, "_runs", {}) or {})}
        return {i["slug"] for i in ideas.ideas(self.root(False), slug) if self.keeper.busy(i["slug"]) or i["slug"] in runs}

    def track_drop(self, args: dict) -> dict:
        """`{"slug", "goals"?: "move"|"drop"}`: a party removed, its goals moved to General (the default) or removed with it (spec 80 §2)."""
        slug, goals = _text(args, "slug", 100), _opt(args, "goals") or "move"
        if goals not in ("move", "drop"):
            raise IdeasError("Goals move to General or are removed")
        if goal_team.craft_of(self.root(False), slug) == party_recipes.RELEASE:          # in every project, the one way into main (decisions §137.1, spec 99 §1.2)
            raise IdeasError("Release stays in every project: it is the one way into main")
        page = ideas.track_page(self.root(False), slug)
        title = (page.title or page.get("title") or slug) if page is not None else slug
        try:
            got = ideas.drop_track(self.root(), slug, goals, self.state_dir, self.track_busy(slug))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self._ev(event_log.PARTY_REMOVED, args, slug=slug, title=title, face=_device(args), **got)
        self.team_dropped(slug)                                   # the Team party removed: Operations are in the left column again (spec 92 §3)
        self.changed("")
        return {"ok": True, **got, "title": title}
