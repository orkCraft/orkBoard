#!/usr/bin/env python3
"""Canvas hook (docs/specs/78-canvases.md §5): a PostToolUse hook that tells Orkboard at once when a tool drew a canvas.

    .claude/settings.json → hooks.PostToolUse, matcher `Artifact|mcp__Claude_Docs__batch|mcp__Figma__create_new_file`
                            → python3 -m orkboard.hooks.canvas                      (`orkcraft hooks install`)
    .codex/hooks.json     → hooks.PostToolUse, matcher `mcp__(figma|tldraw|canva)__.*`
                            → python3 -m orkboard.hooks.canvas codex
    .agents/hooks.json    → orkcraft.PostToolUse, matcher `generate_image`
                            → python3 -m orkboard.hooks.canvas agy                  (or ~/.gemini/config/hooks.json)

Reads the payload on stdin (Claude Code and Codex: `tool_name`, `tool_input`, `tool_response`, `cwd`, `session_id`,
Codex's `model`; agy: `toolCall {name, args}`, the answer under `toolResult` / `result` / `output`, `workspacePaths`,
`conversationId`, `modelName`), maps the call with `sources.canvases.from_call` (the one table of §1, never copied
here) and, when it is a canvas, appends `Canvas.line()` to `<project>/.orkcraft/canvases.jsonl`. The project is the
nearest folder above `cwd` (agy: the first of `workspacePaths`) with a `.orkcraft` folder or a `.git`; a git worktree
counts as its main checkout, where the Board reads. None found: nothing is written.

It never blocks and never decides: it prints `{}` (agy reads every hook's stdout as its answer and fails closed on
anything else), exits 0, gives up after TIMEOUT seconds (reading stdin is its only wait) and swallows every error.
It imports nothing but `orkboard.sources.canvases` and the standard library. The reader (§1) still runs every 30 s:
this is the fast path, so a missed hook loses nothing. The Warder guards this file as its own (`warder.SELF`).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import threading
from pathlib import Path
from typing import IO, Any

from orkboard.sources.canvases import Canvas, from_call

TIMEOUT = 5.0                                  # seconds: reading stdin is the only wait
FILE = Path(".orkcraft") / "canvases.jsonl"    # core/canvases.py's store (kept in step with its `path`)
AGY_RESULT_KEYS = ("toolResult", "result", "output", "toolOutput", "response")   # where agy may put the answer


def _main_repo(root: Path) -> Path:
    """The main checkout when `root` is a git worktree (its `.git` file names `<main>/.git/worktrees/<name>`)."""
    try:
        if (root / ".git").is_file():
            target = (root / ".git").read_text(encoding="utf-8").strip().removeprefix("gitdir:").strip()
            gitdir = (root / target).resolve()
            if gitdir.parent.name == "worktrees" and gitdir.parents[1].name == ".git":
                return gitdir.parents[2]
    except (OSError, ValueError, IndexError):
        pass
    return root


def project_of(cwd: str) -> Path | None:
    """The project a session works in: the nearest folder at or above `cwd` with `.orkcraft` or `.git`, else None."""
    if not cwd:
        return None
    try:
        here = Path(cwd).resolve()
    except (OSError, RuntimeError):
        return None
    for folder in (here, *here.parents):
        if (folder / ".orkcraft").is_dir() or (folder / ".git").exists():
            return _main_repo(folder)
    return None


def _first(payload: dict, *keys: str) -> str:
    return next((str(payload[k]) for k in keys if payload.get(k) and isinstance(payload[k], (str, int))), "")


def read_call(tool: str, payload: dict) -> tuple[str, Any, Any, str, str, str]:
    """(name, args, result, cwd, session, model) of a payload: Claude Code's and Codex's shape, or agy's."""
    if tool == "agy":
        call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
        roots = [w for w in payload.get("workspacePaths") or [] if isinstance(w, str) and w]
        result = next((payload[k] for k in AGY_RESULT_KEYS if payload.get(k) not in (None, "")), None)
        return (str(call.get("name") or ""), call.get("args"), result, roots[0] if roots else "",
                _first(payload, "conversationId"), _first(payload, "modelName"))
    return (str(payload.get("tool_name") or ""), payload.get("tool_input"), payload.get("tool_response"),
            _first(payload, "cwd"), _first(payload, "session_id"), _first(payload, "model"))


def canvas_of(tool: str, payload: Any, now: str) -> tuple[Canvas, str] | None:
    """The canvas a PostToolUse payload drew and the cwd it came from, or None."""
    if not isinstance(payload, dict):
        return None
    name, args, result, cwd, session, model = read_call(tool, payload)
    if isinstance(result, dict) and result.get("is_error"):      # a call that failed is no canvas
        return None
    canvas = from_call(tool, name, args, result, now, session, model)
    return (canvas, cwd) if canvas else None


def record(canvas: Canvas, project: Path) -> None:
    """Appends the canvas's line to the project's store: one write, so two hooks never mix their lines."""
    path = project / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(canvas.line(), ensure_ascii=False) + "\n")


def handle(tool: str, raw: str, now: str | None = None) -> bool:
    """One payload (the stdin's text): True when a canvas was written. Raises on an error (`main` swallows it)."""
    found = canvas_of(tool, json.loads(raw or "{}"),
                      now or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    if not found:
        return False
    canvas, cwd = found
    project = project_of(cwd)
    if project is None:
        return False
    record(canvas, project)
    return True


def _read(stdin: IO[str], timeout: float) -> str | None:
    """The stdin's text, or None when it did not end within `timeout` (the reader is left behind, a daemon)."""
    got: list[str] = []
    reader = threading.Thread(target=lambda: got.append(stdin.read()), daemon=True)
    reader.start()
    reader.join(timeout)
    return got[0] if got else None


def main(argv: list[str] | None = None, stdin: IO[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    tool = argv[0] if argv and argv[0] in ("claude", "codex", "agy") else "claude"
    try:
        raw = _read(stdin or sys.stdin, TIMEOUT)
        if raw is not None:
            handle(tool, raw)
    except Exception:                          # never block the tool, never crash: it only tells
        pass
    try:
        print("{}", flush=True)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    code = main()
    os._exit(code)                             # a reader left on a stdin that never ended must not hold the exit
