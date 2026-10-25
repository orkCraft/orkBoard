"""The picture of what a task changed, kept (docs/specs/85-the-elf-asks-and-shows.md §3, decisions §102): the file and how the Map reads it.
The picture itself is drawn by core/idea_shot.py (the project's preview, a browser, no model).

    idea_shots.store(state_dir, "dark-mode", "k2", 1, png_path)      # {"id": "k2-shot-r1", "file": "shot.png", "w", "h", "at"}
    idea_shots.map_of(task)                  # what the Map says of a task's picture: {"id", "file", "w", "h"}, or {"none": NONE}, or None
    idea_shots.NONE                          # "no picture: no preview"

A picture is kept as a one-file pick beside the task's candidates, `<state>/ideas/<goal>/picks/<task>-shot-r<round>/` (`pick.json` with
`"shot": true` and one variant, `shot.png`): the one signed route that serves a pick's files (gui/media.py) serves it, and nothing else
of Pick one lists it (`idea_pick.history` and `current` look for `<task>-r<round>`). It stays on this machine. No face, no model.
"""
from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

from orkboard.realm import idea_pick, media_sniff

NONE = "no picture: no preview"                    # said where a task that changed what people see has no picture
FILE = "shot.png"
MAX_BYTES = 8 * 1024 * 1024


def pick_id(task_id: str, rnd: int) -> str:
    return f"{task_id}-shot-r{max(1, int(rnd or 1))}"


def store(state_dir: Path, slug: str, task_id: str, rnd: int, source: Path) -> dict | None:
    """The PNG at `source` kept as the task's picture of this round, a round's before it replaced; what the task keeps of it
    (`{"id", "file", "w", "h", "at"}`). None for a file that is not a PNG, empty or over MAX_BYTES (nothing is kept)."""
    try:
        size = source.stat().st_size
    except OSError:
        return None
    if not 0 < size <= MAX_BYTES or media_sniff.sniff(source) != "image/png":
        return None
    pid = pick_id(task_id, rnd)
    folder = idea_pick.folder_of(state_dir, slug, pid)
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    shutil.copyfile(source, folder / FILE)
    got = media_sniff.measure(folder / FILE, "image/png")
    at = dt.datetime.now().isoformat(timespec="seconds")
    idea_pick._write(folder / "pick.json", {"id": pid, "task": task_id, "round": rnd, "shot": True, "at": at, "kind": "image",
                                            "variants": [{"key": "A", "name": "What it looks like", "file": FILE, "mime": "image/png",
                                                          "bytes": size, "w": got.get("w"), "h": got.get("h"), "seconds": None, "why": ""}]})
    return {"id": pid, "file": FILE, "w": got.get("w"), "h": got.get("h"), "at": at}


def map_of(task: dict) -> dict | None:
    """A task's picture as the Map carries it (the host adds its signed `url`): `{"id", "file", "w", "h"}`, `{"none": NONE}` for a task
    that changed what people see and had no preview to draw, None for any other task."""
    got = task.get("shot") if isinstance(task, dict) else None
    if not isinstance(got, dict):
        return None
    if got.get("none"):
        return {"none": NONE}
    if not isinstance(got.get("id"), str) or not isinstance(got.get("file"), str):
        return None
    return {"id": got["id"], "file": got["file"], "w": got.get("w"), "h": got.get("h")}
