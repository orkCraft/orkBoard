"""A gate that could not run is not red (docs/specs/107-what-the-owners-day-said.md §1.1, decisions §182.1).

    why = could_not_run(out, code)                 # "" or the sentence: *The tests could not run: `vitest` is not installed.*
    rows = missing(root, what)                     # [{"dir": "prototypes/ar", "command": "npm ci"}]: what install would make it run (none for a Python tool: `kind_of`)
    kind_of(what)                                  # "python" · "node" · "": which kind of tool the run lacked (spec 143 C.1)
    python_setup(root)                             # the command that would make Python's tests run, for the person to run (spec 143 C.2)
    ok, out = install(root, rows, cancel, 900)     # the rows' commands, one after another, in the main checkout

A red run whose output says a command or a package is not there tested nothing: the code was never reached, and a session
sent back for it can only say it may not install (a task never may: realm/task_commands.py). So the run is told apart
(`could_not_run`), and the person decides: Orkboard installs in the main checkout by each folder's lock (`install`), where
`realm/dep_links.py` then lays the result into the task's worktree. Python is never installed here (a `.venv` is the
person's): for a Python tool that is missing there are no rows, and the card names the command to run (`python_setup`). No face, no model.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import threading
import tomllib
from pathlib import Path
from typing import Callable

from orkboard.realm import gate_config, jobs

OUT_KEEP = 4000
NOT_INSTALLED = "The tests could not run: {what} not installed."
LOCKS = (("package-lock.json", "npm ci"), ("npm-shrinkwrap.json", "npm ci"), ("pnpm-lock.yaml", "pnpm install --frozen-lockfile"),
         ("yarn.lock", "yarn install --frozen-lockfile"), ("bun.lock", "bun install"), ("bun.lockb", "bun install"))
NO_LOCK = "npm install"
_SHELLS = r"(?:/\S*/)?(?:sh|bash|dash|zsh|ksh|fish)"
_NAME = r"[^\s:'\"`]+"
_NOT_FOUND = (                                                  # a shell's *not found*: the name is the second group of each
    re.compile(rf"(?m)^{_SHELLS}(?::\s*(?:line\s+)?\d+)?:\s+(?:\d+:\s+)?({_NAME}):\s+(?:command\s+)?not found"),   # sh: vitest: command not found · sh: 1: vitest: not found
    re.compile(rf"(?m)^{_SHELLS}:\s+(?:command\s+)?not found:\s+({_NAME})"),                                          # zsh: command not found: vitest
    re.compile(r"(?m)^['\"]?([^\s'\"]+)['\"]?\s+is not recognized as an internal or external command"),              # Windows
    re.compile(r"Cannot find (?:module|package) ['\"]([^'\"]+)['\"]"),                                                # Node
    re.compile(r"No module named ['\"]?([\w.\-]+)['\"]?"),                                                            # Python
)


def _package(name: str) -> str:
    """The package a module path names: `vitest/package.json` -> `vitest`, `@scope/pkg/x` -> `@scope/pkg`; "" for a file of the project
    (`./foo`, `/abs/path`, `../x`): its absence is the code's."""
    if not name or name[0] in "./\\" or re.match(r"[A-Za-z]:[\\/]", name):
        return ""
    parts = name.split("/")
    return "/".join(parts[:2]) if name.startswith("@") else parts[0]


def could_not_run(out: str, code: int | None) -> str:
    """"" when the run tested the code (green, or red by its own tests); else the sentence naming what is missing. The earliest sign in
    `out` wins; exit code 127 (*command not found*) is one with no name. A missing file of the project (`Cannot find module './foo'`) is the code's."""
    if code == 0:
        return ""
    text = str(out or "")
    found: tuple[int, str] | None = None
    for rx in _NOT_FOUND:
        for m in rx.finditer(text):
            name = m.group(1)
            if rx is _NOT_FOUND[3]:
                name = _package(name)
                if not name:
                    continue                                     # a file of the project: keep looking for a real sign
            elif rx is _NOT_FOUND[4]:
                name = name.split(".")[0]
            if found is None or m.start() < found[0]:
                found = (m.start(), name)
            break
    if found is not None:
        return NOT_INSTALLED.format(what=f"`{found[1]}` is")
    if code == 127:
        return NOT_INSTALLED.format(what="a command they need is")
    return ""


def _has_deps(folder: Path) -> bool:
    try:
        data = json.loads((folder / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return isinstance(data, dict) and any(isinstance(data.get(k), dict) and data[k] for k in ("dependencies", "devDependencies"))


def _hoisted(root: Path, folder: Path) -> bool:
    """A workspace member whose workspace root (a folder above it, below or at `root`) is installed: its packages lie there."""
    for up in folder.parents:
        if (up / "node_modules").is_dir() and (up / "package.json").is_file():
            try:
                if json.loads((up / "package.json").read_text(encoding="utf-8")).get("workspaces"):
                    return True
            except (OSError, UnicodeDecodeError, ValueError, AttributeError):
                pass
        if up == root:
            break
    return False


PYTHON_TOOLS = frozenset({"pytest", "py.test", "python", "python3", "pip", "pip3", "uv", "ruff", "mypy", "black", "flake8", "coverage", "tox", "nox", "pylint"})
NODE_TOOLS = frozenset({"npm", "npx", "node", "pnpm", "yarn", "bun", "vitest", "jest", "tsc", "eslint", "mocha", "playwright", "vite", "webpack"})


_PATH_PYTHON: dict[str, str] = {}        # PATH -> the Python on it that imports pytest ("" none): asked once per process


def path_python() -> str:
    """The first `python3`, then `python`, on the `PATH` that imports pytest; "" with none. One short run each, kept for the process (spec 143 C.4)."""
    key = os.environ.get("PATH", "")
    if key not in _PATH_PYTHON:
        found = ""
        for name in ("python3", "python"):
            exe = shutil.which(name)
            if not exe:
                continue
            try:
                ok = subprocess.run([exe, "-c", "import pytest"], capture_output=True, timeout=20).returncode == 0
            except (OSError, subprocess.SubprocessError):
                ok = False
            if ok:
                found = exe
                break
        _PATH_PYTHON[key] = found
    return _PATH_PYTHON[key]


def kind_of(what: str) -> str:
    """Which kind of tool a run lacked, from `could_not_run`'s sentence (with the run's output after it, when it is at hand): `python` for pytest and the
    like and for a `No module named` of a Python run, `node` for what Node's tools and `Cannot find module` name, "" when it cannot tell."""
    text = str(what or "")
    name = (re.search(r"`([^`]+)`", text) or re.search(r"^\s*(\S+)\s*$", text) or [None, ""])[1].strip().lower()
    if name in PYTHON_TOOLS:
        return "python"
    if name in NODE_TOOLS or name.startswith("@"):
        return "node"
    if re.search(r"No module named", text):
        return "python"
    if re.search(r"Cannot find (?:module|package)", text):
        return "node"
    return ""


def _dev_extra(root: Path) -> bool:
    try:
        data = tomllib.loads((Path(root) / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    extras = (data.get("project") or {}).get("optional-dependencies") if isinstance(data, dict) else None
    return isinstance(extras, dict) and "dev" in extras


def python_setup(root: Path) -> str:
    """The command that makes a project's Python tests run, read by code and never run here (decisions §182.1): `uv sync --extra dev` for a `uv.lock` and
    a `dev` extra; a `dev` extra with no lock: a `.venv` and the project installed with it; else a `.venv` with pytest."""
    root = Path(root)
    if _dev_extra(root):
        return "uv sync --extra dev" if (root / "uv.lock").is_file() else "python -m venv .venv && .venv/bin/pip install -e '.[dev]'"
    return "python -m venv .venv && .venv/bin/pip install pytest"


def missing(root: Path, what: str = "") -> list[dict]:
    """What install would make the gate run (none when `what`, the sentence of `could_not_run`, names a Python tool: `npm ci` never runs for pytest): each package folder of `root` that lists dependencies and has no `node_modules` in the main
    checkout (a workspace member under an installed workspace root has them), with the command its lock names (none: `npm install`).
    `dir` is `"."` for the root."""
    root = Path(root)
    rows = []
    if kind_of(what) == "python":
        return rows
    for folder in gate_config.package_dirs(root):
        if (folder / "node_modules").is_dir() or not _has_deps(folder) or _hoisted(root, folder):
            continue
        command = next((c for lock, c in LOCKS if (folder / lock).is_file()), NO_LOCK)
        rows.append({"dir": folder.relative_to(root).as_posix() or ".", "command": command})
    return rows


def install(root: Path, rows: list[dict], cancel: threading.Event, timeout_s: int = jobs.TEST_TIMEOUT_S,
            log: Callable[[str], None] | None = None) -> tuple[bool, str]:
    """Run each row's command (words, `cwd` its folder of `root`, no shell) one after another; stop at the first that fails. `(ok, the output's
    last OUT_KEEP characters)`. A command this computer lacks is `(False, "npm is not installed on this computer")`. `log` is told each row's
    heading (`== installing: <dir>: <command>`) before it runs and its output after. Stopped (`cancel`): InterruptedError."""
    out = ""
    for row in rows:
        words = shlex.split(str(row.get("command") or ""))
        head = f"== installing: {row.get('dir') or '.'}: {row.get('command')}\n"
        if log:
            log(head)
        if not words:
            continue
        try:
            proc = subprocess.Popen(words, cwd=Path(root) / str(row.get("dir") or "."), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, start_new_session=True)
        except OSError as e:
            say = f"{words[0]} is not installed on this computer" if isinstance(e, FileNotFoundError) else f"{words[0]} could not start: {e}"
            return False, say
        box: list[str] = []
        reader = threading.Thread(target=lambda: box.append(proc.stdout.read() if proc.stdout else ""), daemon=True)
        reader.start()
        try:
            jobs._wait(proc, cancel, timeout_s, "ideas/install")
        except RuntimeError:
            reader.join(5)
            return False, f"{row.get('command')} took longer than {timeout_s // 60} minutes"
        reader.join(5)
        got = box[0] if box else ""
        if log:
            log(got if got.endswith("\n") or not got else got + "\n")
        out = (out + head + got)[-OUT_KEEP:]
        if proc.returncode != 0:
            return False, out
    return True, out
