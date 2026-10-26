"""The Architect's *System* as `gui/ideas.py`'s `Ideas` has it (docs/specs/89-the-tech-lens-system.md §4, decisions §104.1): the project's
parts laid out as columns of cards (*Feature modules*, spec 90), the architecture beside them (`overview`: containers, links, shared;
realm/system_overview.py), and what changed since the device's last look with the goals that changed it. Read from the code and git
(realm/project_map.py), no model.

    ideas.system {party?, since?}            # dev's head: its parts by column, its overview, what changed since `since`, the goals: map_opened
    ideas.system_part {path, since?}         # one part: its files, uses, used by, and its changes since with their goals and What it made
    ideas.system_rearrange {party?, since?}  # *Rearrange*: laid out anew (the gone parts' places taken away), answered as ideas.system
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from orkboard.gui.ideas_args import IdeasError, _opt, _str, _text
from orkboard.realm import board_map, commit_goal, event_log, ideas, project_map, system_overview

LENS = "system"
PATH_MAX = 300


class SystemMixin:
    """Needs `host`, `state_dir`, `_ref()` and `_goals()` (gui/ideas_assets.py), `_ev` (gui/ideas.py)."""

    def _map_since(self, args: dict) -> str:
        return _str(args, "since", 100).strip() if args.get("since") is not None else ""

    def _system(self, args: dict, rearrange: bool = False) -> tuple[dict, dict]:
        """(the answer, what changed) of `ideas.system`; `rearrange`: the layout laid out anew first."""
        root, ref = Path(self.host.repo_root), self._ref()
        snap = project_map.ensure(self.state_dir, root, ref)
        if snap is None:
            return ({"commit": "", "short": "", "at": "", "ref": ref, "since": "", "columns": [], "changed": {}, "uses_changed": [],
                     "goals": {}, "overview": {**system_overview.empty(), "parts": {}}}, project_map.nothing())
        since = self._map_since(args)
        changes = project_map.changed(self.state_dir, root, since, ref) if since else project_map.nothing(snap["commit"])
        now = {p["path"]: p for p in snap["parts"]}
        before = project_map.read(self.state_dir, changes["since"]) if changes["since"] else None
        gone = {p["path"]: {**p, "gone": True} for p in (before or {}).get("parts") or []
                if changes["parts"].get(p["path"], {}).get("kind") == "gone"}
        lay = project_map.rearrange(self.state_dir, list(now)) if rearrange else project_map.place(self.state_dir, list(now))
        shown = {**gone, **now}                  # a part gone since the last look is shown where it still has a place, to crumble in
        big = any(sum(1 for p, v in lay["parts"].items() if v["column"] == c and p in shown) > project_map.CARDS for c in lay["columns"])
        recent = self._map_recent(root, ref) if big else {}
        cols = project_map.table(lay, shown, set(changes["parts"]), recent, root.name)
        marks = {p: {k: c[k] for k in ("kind", "goal", "task", "at")} for p, c in changes["parts"].items()}
        uses = [{k: u[k] for k in ("from", "to", "kind", "goal", "task", "at")} for u in changes["uses"]]
        slugs = {m["goal"] for m in marks.values()} | {u["goal"] for u in uses}
        return ({"commit": snap["commit"], "short": snap["commit"][:7], "at": snap.get("at") or "", "ref": ref, "since": changes["since"],
                 "columns": cols, "changed": marks, "uses_changed": uses, "goals": self._goals(slugs),
                 "overview": self._map_overview(snap, gone, root.name)}, changes)

    @staticmethod
    def _map_overview(snap: dict, gone: dict[str, dict], project: str) -> dict:
        """The architecture (spec 90 §6, As built (E1)): the snapshot's overview with each container's gone parts, and every part's card
        by path (`changed` marks them by the same paths)."""
        ov = snap.get("overview") or system_overview.empty()
        ids = [c["path"] for c in ov["containers"]]
        out = {p: [] for p in ids}
        for path in sorted(gone):
            at = system_overview.owner(path, ids)
            if at is not None:
                out[at].append(path)
        cards = {p["path"]: {**p, "gone": False} for p in snap["parts"]}
        cards.update({p: g for p, g in gone.items() if system_overview.owner(p, ids) is not None})
        return {"containers": [{**c, "gone": out[c["path"]]} for c in ov["containers"]], "links": ov["links"], "shared": ov["shared"],
                "parts": {p: {"path": p, "name": project_map.name_of(p, project), "count": int(c.get("count") or 0),
                              "uses": list(c.get("uses") or []), "used_by": list(c.get("used_by") or []), "gone": bool(c.get("gone"))}
                          for p, c in sorted(cards.items())}}

    @staticmethod
    def _map_recent(root: Path, ref: str) -> dict[str, str]:
        """`{part: the time a file of it last changed}`, for the stacks."""
        out: dict[str, str] = {}
        for path, row in commit_goal.last_touch(root, ref).items():
            part = project_map._part_of(path)
            out[part] = max(out.get(part, ""), row["at"])
        return out

    def _map_hours(self, since: str, root: Path, ref: str) -> float | None:
        """Hours since the device's last look: `since` as a time, else its commit's time; None for none."""
        if not since:
            return None
        text = since
        if commit_goal.SHA.fullmatch(since):
            sha = commit_goal.resolve(root, since, ref)
            text = project_map._at(root, sha) if sha else ""
        try:
            at = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        at = at if at.tzinfo else at.astimezone()
        return round((dt.datetime.now(dt.timezone.utc) - at).total_seconds() / 3600, 1)

    def system(self, args: dict) -> dict:
        """`{party?, since?}` (`since`: the device's last look, a commit or a time): the System of dev's head (As built, spec 89)."""
        got, changes = self._system(args)
        root, ref = Path(self.host.repo_root), self._ref()
        self._ev(event_log.MAP_OPENED, args, lens=LENS, party=_opt(args, "party"), parts=sum(len(c["parts"]) + len(c["stack"]) for c in got["columns"]),
                 changed=len(got["changed"]), hours=self._map_hours(self._map_since(args), root, ref))
        return got

    def system_rearrange(self, args: dict) -> dict:
        """*Rearrange*: the parts laid out anew, answered as `ideas.system`."""
        return self._system(args, rearrange=True)[0]

    def system_part(self, args: dict) -> dict:
        """`{path, since?}`: `{path, name, count, files, uses, used_by, gone, kind, changes: [{goal, task, at, made}], goals}`."""
        path = _text(args, "path", PATH_MAX)
        root, ref = Path(self.host.repo_root), self._ref()
        snap = project_map.ensure(self.state_dir, root, ref)
        since = self._map_since(args)
        changes = project_map.changed(self.state_dir, root, since, ref) if since and snap else project_map.nothing()
        before = project_map.read(self.state_dir, changes["since"]) if changes["since"] else None
        part = next((p for p in (snap or {}).get("parts") or [] if p["path"] == path), None)
        gone = part is None
        part = part or next((p for p in (before or {}).get("parts") or [] if p["path"] == path), None)
        if part is None:
            raise IdeasError("That part is not in the project")
        kind = changes["parts"].get(path, {}).get("kind", "")
        rows = []
        if kind and before is not None:
            files = project_map.files_under(root, before["commit"], changes["commit"], path)
            index = commit_goal.index(self.state_dir, root, ref)
            seen: dict[tuple[str, str], dict] = {}
            for c in project_map.commits_of(root, ref, before["commit"], files):
                g = index.get(c["sha"]) or {}
                key = (g.get("goal", ""), g.get("task", ""))
                if key in seen:
                    seen[key]["at"] = c["at"]
                    continue
                seen[key] = {"goal": key[0], "task": key[1], "at": c["at"], "made": self._map_made(*key)}
                rows.append(seen[key])
        self._ev(event_log.MAP_PART_PRESSED, args, lens=LENS, party=_opt(args, "party"), changed=kind, goals=len({r["goal"] for r in rows}))
        return {"path": path, "name": project_map.name_of(path, root.name), "count": int(part.get("count") or 0),
                "files": list(part.get("files") or [])[:60], "uses": list(part.get("uses") or []), "used_by": list(part.get("used_by") or []),
                "gone": gone, "kind": kind, "since": changes["since"], "changes": rows, "goals": self._goals({r["goal"] for r in rows})}

    def _map_made(self, goal: str, task: str) -> str:
        """The task's *What it made* (spec 85 §4); "" for the person's own commits."""
        if not goal or not task:
            return ""
        try:
            t = next((t for t in (ideas.plan(self.state_dir, goal) or {}).get("tasks") or [] if isinstance(t, dict) and t.get("id") == task), None)
        except ValueError:
            return ""
        return board_map.made_of(t) if t else ""


def system_commands(m: SystemMixin) -> dict:
    return {"ideas.system": m.system, "ideas.system_part": m.system_part, "ideas.system_rearrange": m.system_rearrange}
