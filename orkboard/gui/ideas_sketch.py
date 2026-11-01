"""A goal's sketch (docs/specs/121-the-day-the-morning-and-the-night.md §2; core/idea_sketch.py) as `gui/ideas.py`'s `Ideas` has it: the Needs you row of a sketch that waits for the person, and the commands that
turn one on or off for a goal. Its answers are `ideas.pick`'s (gui/ideas_pick.py), the pick's `task` being `sketch`.

    ideas.sketch_now {idea}        # *Sketch it first*: the goal gets a sketch before its spec, though it would get none (before its spec is written)
    ideas.sketch_skip {idea}       # *No sketch*: it gets none; on a goal being sketched it is *No sketch: go on*
    ideas.pick {slug, task: "sketch", key, note, skip?, now?, via?}
                                   # key a variant's letter = *Pick this one* (`now: true`: *Pick and build now*, the plan passed at once when it is made);
                                   # key null with a note = *Sketch again* (at most three rounds); `skip: true` = *No sketch: go on* (no key, no note)

**The row** (kind `pick`, `sketch: true`, `task: "sketch"`) is a pick's row with its variants (signed addresses, gui/media.py; a page's `mime` is `text/html` and it comes with no inline text: the faces put its
`url` in an `iframe sandbox="allow-scripts"`), plus `craft`, `party`, `by` (the leader: `{slug, name, head}`), `kind` (`page` · `image` · `audio`), `rounds` (the most: 3), `rounds_left`, `now` (*Work at night* is on: *Pick
and build now* is offered beside *Pick this one*), `error` (why a new round could not be made; the round before is open again), `text` (*<Leader> sketched it*). While the sketch is made there is no row: the goal's
back says *<Leader> is sketching* (`sketching` on its row of the Board: `{craft, party, leader, round}`).
"""
from __future__ import annotations

from orkboard.gui.ideas_args import IdeasError, _device, _text
from orkboard.realm import goal_team, idea_pick, ideas, roles, sketches


class SketchMixin:
    def sketch_pick(self, args: dict, slug: str, key: str | None, note: str, via: str) -> dict:
        """`ideas.pick` for the task `sketch`: the answer goes to the keeper (core/idea_sketch.py). `skip: true` is *No sketch: go on*; `now: true` (with a key) keeps *Pick and build now* with the goal, as a pick in
        the work does (gui/ideas_board.py `keep_build_now`), and drops it again when the answer is refused."""
        skip, now = args.get("skip", False), args.get("now", False)
        if not isinstance(skip, bool) or not isinstance(now, bool):
            raise IdeasError("skip and now are on or off")
        kept = now and key is not None and not skip and self.keep_build_now(slug, args)
        try:
            got = self.keeper.sketch_answer(slug, key, note[:idea_pick.NOTE_MAX], skip, device=_device(args), via=via)
        except Exception:
            if kept:
                self.drop_build_now(slug)
            raise
        if kept and got.get("answer") != "picked":
            self.drop_build_now(slug)
        self.changed(slug)
        return {"ok": True, **got}

    def sketch_now(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        self.keeper.sketch_prefer(slug, "yes")
        self.changed(slug)
        return {"ok": True}

    def sketch_skip(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        self.keeper.sketch_prefer(slug, "no")
        self.changed(slug)
        return {"ok": True}

    def sketching(self, slug: str) -> dict | None:
        """`{craft, party, leader, name, round}` while the goal's sketch is being made (the goal's back says *<Leader> is sketching*), else None."""
        rec = sketches.record(self.state_dir, slug)
        if rec.get("status") != "making" or ideas.state(self.state_dir, slug)["state"] != "sketch":
            return None
        role = roles.role(self.state_dir, str(rec.get("leader") or "")) or {}
        return {"craft": rec.get("craft"), "party": rec.get("party"), "leader": rec.get("leader"), "name": role.get("name") or rec.get("leader"), "round": int(rec.get("round") or 1)}

    def sketch_rows(self, i: dict) -> list[dict]:
        """The Needs you row of a goal's sketch that waits for the person (see the module); [] while it is made or when the goal has none."""
        slug = i["slug"]
        rec = sketches.record(self.state_dir, slug)
        if rec.get("status") != "asked" or ideas.state(self.state_dir, slug)["state"] != "sketch":
            return []
        rnd = int(rec.get("round") or 1)
        pick = idea_pick.load(self.state_dir, slug, idea_pick.pick_id("sketch", rnd))
        if pick is None or idea_pick.answered(pick):
            return []
        root, party = self.root(False), str(rec.get("party") or "")
        leader = str(rec.get("leader") or goal_team.leader_of(root, party))
        role = roles.role(self.state_dir, leader) or {}
        name = str(role.get("name") or leader)
        head = goal_team.head_in(root, party, role, self.target_of_idea(slug), goal_team.tiers_of(root, party)) if party else {}
        return [{"kind": "pick", "sketch": True, "slug": slug, "idea": slug, "goal": i["track"], "task": "sketch", "title": f"{name} sketched it", "short": "Sketch", "text": f"{name} sketched it",
                 "idea_title": i["title"], "priority": i["priority"], "blocks": True, "craft": rec.get("craft"), "party": party,
                 "by": {"slug": leader, "name": name, "head": head}, "ask": pick.get("ask") or "", "n": len(pick["variants"]), "media": pick.get("kind"),
                 "variants": [self._variant_row(slug, pick, v) for v in pick["variants"] if isinstance(v, dict)], "round": rnd, "rounds": sketches.ROUNDS, "rounds_left": sketches.left(rnd),
                 "now": self.settings_now().get("work_at_night") is True, "error": str(rec.get("error") or ""), "at": str(pick.get("at") or rec.get("asked_at") or "")}]


def sketch_commands(ideas_) -> dict:
    """The sketch's commands by name (`gui/ideas.py` adds them to its table)."""
    return {"ideas.sketch_now": ideas_.sketch_now, "ideas.sketch_skip": ideas_.sketch_skip}
