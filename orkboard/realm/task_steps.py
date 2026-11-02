"""A task's steps (docs/specs/129-a-tasks-steps.md H1, decisions §207): what its worker is on now, read one way whatever
tool it runs on. Pure: no process, no clock but the one it is given.

    clean(items)                       # at most 6 steps, each text at most 40 characters, one `now`, an unknown state `next`
    read_file(path)                    # the worker's `.ork-steps.json`, cleaned; None when it is not there or not readable
    reader_for("claude").feed(text)    # the tool's own list from a chunk of its streaming output; None when the chunk holds none
    activity(worktree, command)        # "edits lobby.ts" / "runs the tests": what it is doing, with no list at all
    merge(file, todo, doing)           # the snapshot's `steps`: the file wins, then the tool's list, then what it is doing

The worker keeps its steps in a file of its worktree (`RULE`, told in every working prompt) — one rule on Claude Code, Codex
and Antigravity alike. Where a tool streams its own to-do list (Claude Code's `TodoWrite` in stream-json, Codex's `todo_list`
item in `exec --json`) it is read too, and fills in while the file is missing. Antigravity prints one envelope at the end:
its reader has nothing to read, the file is its source. The run that reads them while a task works is realm/task_steps_run.py.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

FILE = ".ork-steps.json"            # at the worktree's root; put in its .git/info/exclude when the worktree is made, and never landed
KEPT = ".steps.json"                # beside a task's log: <state_dir>/ideas/<slug>/<tid>.steps.json
MAX_STEPS = 6
MAX_TEXT = 40
STATES = ("done", "now", "next")
SOURCES = ("file", "todo", "activity")

RULE = ("# Your steps\n\n"
        f"Keep your steps in `{FILE}` at the worktree's root: a JSON list of at most six "
        '`{"step": "<a few words>", "state": "done" | "now" | "next"}`; write it before you start and again whenever a step '
        "changes. It is not part of your work: never commit it.")

_DONE = {"done", "completed", "complete", "finished", "x", "true"}
_NOW = {"now", "in_progress", "in progress", "doing", "active", "current", "running"}


def state_of(value: object) -> str:
    """`done`, `now` or `next` for any tool's word for it (a boolean `completed` too); anything else is `next`."""
    if value is True:
        return "done"
    word = str(value or "").strip().lower()
    return "done" if word in _DONE else "now" if word in _NOW else "next"


def cut(text: object, limit: int = MAX_TEXT) -> str:
    """One line of at most `limit` characters, cut on a word with an ellipsis when it was longer."""
    line = " ".join(str(text or "").split())
    if len(line) <= limit:
        return line
    head = line[:limit - 1]
    if line[limit - 1] != " " and " " in head:
        head = head.rsplit(" ", 1)[0]
    return head.rstrip(" ,;:.-") + "…"


def clean(items: object) -> list[dict]:
    """[{text, state}] of what a worker or a tool listed: at most six, text cut to 40 characters on a word, at most one `now`
    (the first; a later one is `next`), an unknown state `next`, an empty text left out. An item is a dict (`step`, `text`,
    `content` or `title` for the words; `state`, `status` or `completed` for the state) or a bare string (`next`)."""
    out: list[dict] = []
    if not isinstance(items, list):
        return out
    now = False
    for item in items:
        if isinstance(item, str):
            text, state = item, "next"
        elif isinstance(item, dict):
            text = next((item[k] for k in ("step", "text", "content", "title") if isinstance(item.get(k), str) and item[k].strip()), "")
            raw = item.get("state", item.get("status", item.get("completed")))
            state = state_of(raw)
        else:
            continue
        text = cut(text)
        if not text:
            continue
        if state == "now":
            state, now = ("next", True) if now else ("now", True)
        out.append({"text": text, "state": state})
        if len(out) == MAX_STEPS:
            break
    return out


def read_file(path: Path) -> list[dict] | None:
    """The steps the worker wrote (a list, or an object with its list under `steps`), cleaned; None when the file is not
    there or is not JSON of that shape (a half-written file is read again at the next look)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(data, dict):
        data = data.get("steps", data.get("items"))
    return clean(data) if isinstance(data, list) else None


# -- the tools' own lists ----------------------------------------------------------------------------

def _command(text: object) -> str:
    """A command as the person would say it: a shell wrapper (`/bin/zsh -lc '…'`) taken off."""
    line = " ".join(str(text or "").split())
    wrapped = re.match(r"^(?:\S*/)?(?:ba|z|da|fi)?sh\s+-l?c\s+(.+)$", line)
    if wrapped:
        line = wrapped.group(1).strip()
        if len(line) > 1 and line[0] == line[-1] and line[0] in "'\"":
            line = line[1:-1]
    return line


class Reader:
    """What a tool's streaming output says of its steps, fed chunk by chunk (a line cut in two by a chunk is kept until its
    end comes). `feed` gives the newest list of the chunk, cleaned, or None; `command` is the last command the tool ran and
    `command_at` the time it was seen."""
    tool = ""

    def __init__(self) -> None:
        self.command = ""
        self.command_at = 0.0
        self._rest = ""

    def feed(self, text: str, now: float | None = None) -> list[dict] | None:
        got: list[dict] | None = None
        lines = (self._rest + text).split("\n")
        self._rest = lines.pop()                  # the last piece has no end yet
        for line in lines:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                found = self.event(event, time.time() if now is None else now)
                if found:
                    got = found
        return got

    def event(self, event: dict, now: float) -> list[dict] | None:
        return None

    def ran(self, command: object, now: float) -> None:
        if command := _command(command):
            self.command, self.command_at = command, now


class ClaudeReader(Reader):
    """Claude Code's stream-json: an `assistant` event whose content holds a `tool_use` of `TodoWrite`, its
    `input.todos` being `[{content, status: pending | in_progress | completed, activeForm}]`; the step now reads by its
    `activeForm` (*Running the tests*). A `Bash` tool_use is the command."""
    tool = "claude"

    def event(self, event: dict, now: float) -> list[dict] | None:
        message = event.get("message") if event.get("type") == "assistant" else None
        got = None
        for part in (message.get("content") if isinstance(message, dict) else None) or []:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            given = part.get("input") if isinstance(part.get("input"), dict) else {}
            if part.get("name") == "TodoWrite" and isinstance(given.get("todos"), list):
                got = clean([{"text": t.get("activeForm") if state_of(t.get("status")) == "now" and t.get("activeForm") else t.get("content"),
                              "state": t.get("status")} for t in given["todos"] if isinstance(t, dict)])
            elif part.get("name") == "Bash":
                self.ran(given.get("command"), now)
        return got


def _plan_in(value: object) -> list[dict] | None:
    """An `update_plan` call's `plan: [{step, status}]`, wherever Codex prints it: on the item, or in its arguments (an object or a JSON string)."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("plan"), list):
        return clean([{"text": p.get("step"), "state": p.get("status")} for p in value["plan"] if isinstance(p, dict)])
    for key in ("arguments", "input", "args"):
        if key in value and (got := _plan_in(value[key])):
            return got
    return None


class CodexReader(Reader):
    """`codex exec --json`: an `item.started | item.updated | item.completed` event whose item is a `todo_list`
    (`items: [{text, completed}]`: the first not completed is the one now), or an `update_plan` call's `plan: [{step,
    status}]` where a version prints it. A `command_execution` item starting is the command."""
    tool = "codex"

    def event(self, event: dict, now: float) -> list[dict] | None:
        item = event.get("item")
        if not str(event.get("type")).startswith("item.") or not isinstance(item, dict):
            return None
        if item.get("type") == "todo_list" and isinstance(item.get("items"), list):
            rows = [i for i in item["items"] if isinstance(i, dict)]
            first = next((n for n, i in enumerate(rows) if not i.get("completed")), -1)
            return clean([{"text": i.get("text"), "state": "done" if i.get("completed") else "now" if n == first else "next"}
                          for n, i in enumerate(rows)])
        if item.get("type") == "command_execution" and event.get("type") == "item.started":
            self.ran(item.get("command"), now)
            return None
        return _plan_in(item)


class NoReader(Reader):
    """A tool whose output is not a stream of events (Antigravity's `--output-format json` is one envelope at the end): the
    steps file is its source."""


def reader_for(harness: str) -> Reader:
    """The reader of a tool's output; one that reads nothing for a tool that streams no list."""
    return {"claude": ClaudeReader, "codex": CodexReader}.get(harness, NoReader)()


# -- what it is doing --------------------------------------------------------------------------------

TEST_COMMAND = re.compile(r"\b(pytest|py\.test|unittest|tox|nox|jest|vitest|mocha|rspec|phpunit|npm (?:run )?test|yarn test|pnpm (?:run )?test|"
                          r"bun test|cargo test|go test|dotnet test|gradle test|mvn test|make (?:test|check)|ctest)\b")


def doing_command(command: str, gate: str = "") -> str:
    """*runs the tests* for a test command (the common runners, or the project's own gate), else *runs <its first word>*; a
    path or a variable before the command is taken off its name."""
    command = _command(command)
    if not command:
        return ""
    if TEST_COMMAND.search(command) or (gate and gate.strip() and gate.strip() in command):
        return "runs the tests"
    words = [w for w in command.split() if "=" not in w.split("/")[-1] or w.startswith(("-", "./", "/"))]
    first = Path(words[0] if words else command.split()[0]).name
    return cut(f"runs {first}") if first else ""


def changed_files(worktree: Path) -> list[tuple[float, str]]:
    """(mtime, path) of each file `git status` says is changed or new in the worktree, the steps file left out."""
    try:
        proc = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=worktree, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for line in proc.stdout.splitlines() if proc.returncode == 0 else []:
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if not path or path == FILE or line[:2].strip() == "D":
            continue
        try:
            out.append((os.stat(Path(worktree) / path).st_mtime, path))
        except OSError:
            continue
    return sorted(out)


def activity(worktree: Path | None, command: str = "", command_at: float = 0.0, gate: str = "") -> str:
    """What the worker is doing with no list at all, in a few words: the last command it ran (where the output streams) or
    the file changed last in the worktree, whichever came later: *runs the tests*, *edits lobby.ts*; "" when neither is known."""
    files = changed_files(Path(worktree)) if worktree else []
    file_at, path = files[-1] if files else (0.0, "")
    said = doing_command(command, gate)
    if said and (not path or command_at >= file_at):
        return said
    return cut(f"edits {Path(path).name}") if path else ""


# -- the snapshot's `steps` --------------------------------------------------------------------------

def merge(file: list[dict] | None, todo: list[dict] | None, doing: str = "") -> dict | None:
    """The steps of the shape the snapshot carries (spec 129): {items, now, done, total, source, doing}. The worker's file
    wins when it holds steps, then the tool's own list; with neither, `doing` alone (`source: "activity"`, no items). None
    when nothing is known."""
    doing = cut(doing, 60)
    items, source = (file, "file") if file else (todo, "todo") if todo else ([], "activity")
    items = [dict(i) for i in items or []]
    if not items and not doing:
        return None
    return {"items": items, "now": next((n for n, i in enumerate(items) if i["state"] == "now"), -1),
            "done": sum(1 for i in items if i["state"] == "done"), "total": len(items), "source": source, "doing": doing}


def finished(steps: dict | None) -> dict | None:
    """A task done keeps its last steps, all `done` (no step now); a task that only had what it was doing keeps nothing."""
    if not steps or not steps.get("items"):
        return None
    items = [{"text": i["text"], "state": "done"} for i in steps["items"]]
    return {**steps, "items": items, "now": -1, "done": len(items), "total": len(items), "doing": ""}


def valid(steps: object) -> dict | None:
    """A kept steps file as the snapshot may carry it (read back from disk): cleaned again, None when it is not of the shape."""
    if not isinstance(steps, dict) or steps.get("source") not in SOURCES:
        return None
    items = clean(steps.get("items"))
    got = merge(items or None, None, str(steps.get("doing") or ""))
    return {**got, "source": steps["source"] if items else "activity"} if got else None


def kept_path(slug_dir: Path, tid: str) -> Path:
    return Path(slug_dir) / f"{tid}{KEPT}"


def read_kept(slug_dir: Path, tid: str) -> dict | None:
    """The steps kept beside a task, in the snapshot's shape; None when there are none."""
    try:
        return valid(json.loads(kept_path(slug_dir, tid).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None
