"""Where the person's Team party is (docs/specs/92-running-and-the-team.md §3, decisions §108): Operations are the person's, one for all projects (decisions §51.1), and the
Team party is the way to them. It is put in one project the person chooses, and there is one across all of them; this file is the person's own note of which, kept beside Operations'
state (`~/.config/orkcraft/ops/team.json`, mode 600, never in a repository).

    team = ops_team.get(base)                       # {"project": "/path", "name": "harbor", "party": "team"} or None
    ops_team.set(base, "/path", "harbor", "team")   # the Team party was made there
    ops_team.clear(base, "/path", "team")           # it was removed (nothing happens when it is another's)
    ops_team.where(base, "/path")                   # "" when there is none, "here" in that project, else the other project's name (the words of *Team is in <project>*)

A note whose project folder is gone reads as none. The party itself is a party of the project's Board (`recipe` `team`, realm/party_recipes.py `TEAM`); this note only lets another
project and the left column know that it exists. No face, no model.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from orkboard.realm import op_runs

FILE = "team.json"
_LOCK = threading.RLock()


def _path(base: Path) -> Path:
    return Path(base) / FILE


def get(base: Path) -> dict | None:
    """The note, or None: missing, of another shape, or about a project folder that is gone."""
    try:
        data = json.loads(_path(base).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) and data[k] for k in ("project", "party")):
        return None
    if not Path(data["project"]).is_dir():
        return None
    return {"project": data["project"], "name": str(data.get("name") or Path(data["project"]).name), "party": data["party"]}


def set(base: Path, project: str | Path, name: str, party: str) -> None:  # noqa: A001 — the spec's name
    with _LOCK:
        op_runs.write(_path(base), json.dumps({"project": str(project), "name": name, "party": party}, ensure_ascii=False) + "\n")


def clear(base: Path, project: str | Path | None = None, party: str = "") -> bool:
    """The note removed when it is `project`'s and `party`'s (any, with none given); True when it was."""
    with _LOCK:
        got = get(base)
        if got is None and not _path(base).exists():
            return False
        if got is not None and ((project is not None and got["project"] != str(project)) or (party and got["party"] != party)):
            return False
        _path(base).unlink(missing_ok=True)
        return True


def where(base: Path, project: str | Path | None) -> str:
    """"" with no Team party; "here" when it is in `project`; else the name of the project it is in."""
    got = get(base)
    if got is None:
        return ""
    return "here" if project is not None and got["project"] == str(project) else got["name"]
