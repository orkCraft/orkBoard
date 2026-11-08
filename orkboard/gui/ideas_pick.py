"""Pick one (docs/specs/51-pick-one.md §2.3, §2.4) as `gui/ideas.py`'s `Ideas` has it: `ideas.pick`, the person's answer to a task that
made variants, and the Needs you row such a task puts on the Board. Split from ideas.py to keep it under ~600 lines.

    ideas.pick {slug, task, key, note, via, now?}    # key: a variant's letter, or null for none of them (then a note is required)
                                                       # task `sketch`: a goal's sketch before its spec (spec 121 §2.5, gui/ideas_sketch.py): `skip: true` = *No sketch: go on*

The row (kind `pick`) carries the variants with their signed addresses (gui/media.py); a text's words come inline. Its tasks are
the runner's (core/idea_picking.py): the Board only reads them and says what the person answered.
"""
from __future__ import annotations

from orkboard.gui import media
from orkboard.gui.ideas_args import VIA, IdeasError, _device, _text
from orkboard.realm import craft_tools, idea_pick, idea_shots, ideas, roles
from orkboard.realm.board_map import task_short

PICK_VIA = ("hand", "front", "drawer", "screen")           # where a pick was answered: the stops along the bottom, the drawer, the phone's own screen
TEXT_INLINE = idea_pick.KINDS["text"].limit       # a text variant's words, inline in the row, at most this many bytes


class PickMixin:

    def pick(self, args: dict) -> dict:
        """`{"slug", "task", "key", "note"?, "via"?}`: the person's answer to a task that waits for a pick. `key`: the variant's letter,
        or null for none of them, which asks for new ones and needs a `note` (at most 2 000 characters). `via`: `hand` (the stop's card),
        `drawer` or `screen` (the phone's own screen); another is read as the idea's screen. `now: true` (spec 121 §4.5, *Pick and build now* on a
        sketch): kept with the answer, so the goal's plan is passed at once when it is made, unless `AUTOSTART` makes it wait for the person
        (gui/ideas_board.py `autostart`); a goal whose plan is passed already keeps nothing."""
        slug, tid = _text(args, "slug", 100), _text(args, "task", 40)
        key, note = args.get("key"), args.get("note", "")
        if key is not None and not isinstance(key, str):
            raise IdeasError("key is a variant's letter, or null for none of them")
        if not isinstance(note, str):
            raise IdeasError("note is not text")
        via = args.get("via")
        via = via if isinstance(via, str) and via in (*VIA, *PICK_VIA) else "idea"
        if tid == "sketch":                                         # a goal's sketch (spec 121 §2.5), not a task of a plan: the keeper answers it (gui/ideas_sketch.py)
            return self.sketch_pick(args, slug, key, note, via)
        now = args.get("now", False)
        if not isinstance(now, bool):
            raise IdeasError("now is on or off")
        kept = now and key is not None and self.keep_build_now(slug, args)      # before the answer: the plan may be made at once; none for a pick of new ones
        try:
            self.runner(need=True).pick(slug, tid, key, note[:idea_pick.NOTE_MAX], device=_device(args), via=via)
        except Exception:
            if kept:
                self.drop_build_now(slug)               # a refused answer builds nothing
            raise
        self.changed(slug)
        return {"ok": True}

    def _variant_row(self, slug: str, pick: dict, v: dict) -> dict:
        """One variant as a face reads it: `{key, name, why, url, mime, w, h, seconds, text?}`."""
        row = {"key": v["key"], "name": v["name"], "why": v.get("why") or "", "url": media.url(slug, str(pick["id"]), str(v["file"])),
               "mime": v["mime"], "w": v.get("w"), "h": v.get("h"), "seconds": v.get("seconds")}
        if v["mime"] in ("text/plain", "text/markdown"):            # a page (`text/html`, a sketch's) is never inline: its `url` goes in a sandboxed frame
            try:
                raw = (idea_pick.folder_of(self.state_dir, slug, str(pick["id"])) / str(v["file"])).read_bytes()[:TEXT_INLINE]
                row["text"] = raw.decode("utf-8", "replace")
            except OSError:
                row["text"] = ""
        return row

    @staticmethod
    def shot_of(slug: str, task: dict) -> dict | None:
        """A task's picture as a face reads it (spec 85 §3): `{url, w, h}` with its signed address, `{none}` for a task that changed what people
        see and had no preview to draw, None for a task with none."""
        got = idea_shots.map_of(task)
        return got if got is None or got.get("none") else {**got, "url": media.url(slug, got["id"], got["file"])}

    def pick_rows(self, i: dict, plan: dict | None) -> list[dict]:
        """The Needs you rows of a goal's tasks that wait for a pick, in the plan's order (realm/idea_pick.py `current`): kind `pick`,
        `slug` (the goal) and `task`, `title` (the task's), the member it ran as, the ask, the variants, the round and when it was asked.
        It blocks the goal's work in progress, so it sorts first."""
        out, slug = self.sketch_rows(i), i["slug"]                  # a goal's sketch that waits for the person (spec 121 §2.5: gui/ideas_sketch.py)
        waiting =[t for t in (plan or {}).get("tasks") or [] if isinstance(t, dict) and t.get("state") == "picking"]
        if not waiting:
            return out
        read, target = roles.known(self.state_dir), self.target_of_idea(slug)
        for t in waiting:
            pick = idea_pick.current(self.state_dir, slug, t)
            if pick is None or idea_pick.answered(pick):
                continue
            who = read[0].get(roles.task_slug(t, read)) or read[0].get(roles.GRUNT) or {}
            out.append({"kind": "pick", "slug": slug, "idea": slug, "goal": i["track"], "task": t.get("id"), "title": t.get("title") or "",
                        "short": task_short(t), "idea_title": i["title"], "priority": i["priority"], "blocks": True,
                        "by": {"slug": who.get("slug") or "", "name": who.get("name") or "", "head": roles.task_head(self.state_dir, t, target, read, self.tiers_of_idea(slug))},
                        "ask": pick.get("ask") or "", "n": len(pick["variants"]), "media": pick.get("kind"),
                        "variants": [self._variant_row(slug, pick, v) for v in pick["variants"] if isinstance(v, dict)],
                        **({"maker": {"id": pick["tool"], "word": craft_tools.get(pick["tool"]).maker,
                                     "cost": pick.get("cost"), "cap": pick.get("cap")}}
                           if craft_tools.get(pick.get("tool")) else {}),
                        "round": int(pick.get("round") or 1), "at": str(pick.get("at") or t.get("finished") or "")})
        return out
