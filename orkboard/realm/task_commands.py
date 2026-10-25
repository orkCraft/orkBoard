"""The commands a task may run (docs/specs/86-what-the-logs-said.md §2, decisions §103.2): a list code gives it, never a model.

    allowed(root, task)    # ["Bash(ls)", "Bash(ls *)", …, "Bash(npm test)", …]: Claude Code's `--allowedTools` rules
    denied()               # ["Bash(git push *)", "Bash(sudo *)", …]: `--disallowedTools` (a denied rule wins over an allowed one)
    line(rules)            # the allowed commands as one line, for the task's log

In `-p` nobody can be asked, so a command not listed is refused, and each refusal is a turn that reads the whole context
again. Allowed: reading (`ls`, `cat`, `grep`, `find`, `head`, `tail`, `wc`, `git status|diff|log|show`), the project's own
test, build and lint commands (the gate's `run`, `package.json`'s scripts, a Makefile's `test|build|lint|check`, the
language's own), local git on the task's own branch, and for a pick task (`task["pick"]`) the media tools. Never: `git push`,
`rm -rf`, `sudo`, `curl`, `wget`, `ssh`, a package install: the worktree's dependencies are linked in by code
(realm/dep_links.py, called by `IdeaGit.prepare`). No face, no model.
"""
from __future__ import annotations

import re
import shlex
from pathlib import Path

from orkboard.realm import gate_config
from orkboard.realm.gate_config import has_test, package_dirs, scripts_of

READING = ("ls", "cat", "grep", "find", "head", "tail", "wc", "pwd", "cd",
           "git status", "git diff", "git log", "git show", "git branch", "git ls-files", "git rev-parse")
LOCAL_GIT = tuple(f"git {verb}" for verb in ("add", "commit", "checkout", "switch", "stash", "merge", "rebase"))
MEDIA = ("ffmpeg", "ffprobe", "sox", "soxi", "python3", "node")      # a pick task's, on its candidates' folder
NEVER = ("git push", "rm -rf", "rm -fr", "sudo", "curl", "wget", "ssh", "scp", "npm install", "npm i", "npm ci",
         "npm add", "pip install", "pip3 install", "python -m pip", "python3 -m pip", "yarn install", "yarn add",
         "pnpm install", "pnpm add", "pnpm i", "uv pip", "uv add", "uv sync")
NEVER_RULES = ("Bash(find * -delete*)", "Bash(find * -exec*)", "Bash(find * -execdir*)", "Bash(find * -ok*)")
SCRIPTS = re.compile(r"^(test|build|lint|check|typecheck)([:._-].+)?$")      # a package.json script a task may run
MAKE_TARGET = re.compile(r"^(test|build|lint|check)[ \t]*:(?!=)", re.MULTILINE)


def _rule(cmd: str) -> list[str]:
    """`Bash(cmd)` and `Bash(cmd *)`: the command alone and with arguments."""
    return [f"Bash({cmd})", f"Bash({cmd} *)"]


def _node(root: Path) -> list[str]:
    out: list[str] = []
    for folder in package_dirs(root):
        scripts = scripts_of(folder)
        if has_test(scripts.get("test", "")):
            out += _rule("npm test") + _rule("npm run test")
        for name in scripts:
            if name != "test" and SCRIPTS.match(name) and "," not in name:
                out += _rule(f"npm run {name}")
                if any((folder / lock).is_file() for lock in ("yarn.lock", "pnpm-lock.yaml")):
                    out += _rule(f"yarn {name}") + _rule(f"yarn run {name}") + _rule(f"pnpm {name}") + _rule(f"pnpm run {name}")
    if out:
        out += ["Bash(npm test --prefix *)", "Bash(npm run * --prefix *)"]
    return out


def _make(root: Path) -> list[str]:
    try:
        text = (Path(root) / "Makefile").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [r for target in dict.fromkeys(m.group(1) for m in MAKE_TARGET.finditer(text)) for r in _rule(f"make {target}")]


def _gate_run(root: Path) -> list[str]:
    """The gate's own `run`: each command of it (`pytest -q && ruff check .` is two) as a rule of its first words."""
    out: list[str] = []
    for part in re.split(r"&&|\|\||;|\|", gate_config.read(root).run):
        try:
            words = shlex.split(part)
        except ValueError:
            continue
        if words:
            out += _rule(" ".join(words[:3]) if words[0] in ("python", "python3", "uv") else
                         " ".join(words[:2]) if words[0] in ("npm", "go", "cargo", "make") else words[0])
    return out


def _languages(root: Path) -> list[str]:
    root = Path(root)
    out: list[str] = []
    if (root / "pyproject.toml").is_file() or (root / "tests").is_dir() or (root / "setup.py").is_file():
        for py in ("python", "python3", ".venv/bin/python", "uv run python"):
            out += _rule(f"{py} -m pytest")
        out += _rule("pytest") + _rule("ruff check") + _rule("uv run pytest") + _rule("uv run ruff")
    if (root / "go.mod").is_file():
        out += [r for verb in ("test", "build", "vet") for r in _rule(f"go {verb}")]
    if (root / "Cargo.toml").is_file():
        out += [r for verb in ("test", "build", "check", "clippy") for r in _rule(f"cargo {verb}")]
    return out


def allowed(root: Path, task: dict | None = None) -> list[str]:
    """The `--allowedTools` rules of a task of the project at `root` (the main checkout, or the task's worktree: the
    same files). `task["pick"]`: a pick of candidates, which also gets the media tools."""
    rules: list[str] = []
    for cmd in (*READING, *LOCAL_GIT):
        rules += _rule(cmd)
    rules += _node(root) + _make(root) + _gate_run(root) + _languages(root)
    if (task or {}).get("pick"):
        rules += [r for cmd in MEDIA for r in _rule(cmd)]
    return list(dict.fromkeys(rules))


def denied() -> list[str]:
    """The `--disallowedTools` rules of every task: what a person is never asked about, because it is never done."""
    return list(dict.fromkeys([r for cmd in NEVER for r in _rule(cmd)] + list(NEVER_RULES)))


def line(rules: list[str]) -> str:
    """The allowed commands as one line for the task's log (`commands allowed: ls, cat, …, npm test`)."""
    names = [r[len("Bash("):-1] for r in rules if r.startswith("Bash(") and r.endswith(")") and not r.endswith(" *)")]
    return "commands allowed: " + ", ".join(names)
