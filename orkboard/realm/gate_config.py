"""The gate's command and files for a repository (docs/specs/37-board-and-line.md §5).

    gate = read(repo_root)                       # orkcraft.toml `[gate]`, else the project's own (spec 86 §3), else none
    files = gate_files(gate, touched, worktree)  # `always`, then the touched files' tests that exist
    argv = test_argv(command)                    # words, or `sh -c` when the command needs a shell

`orkcraft.toml` is tracked at the repository's root; an unknown key is ignored, a bad file is said in `Gate.error`
and the gate runs as with no file. With no file or no `[gate]` the gate is the project's own (`derive`): Orkboard's
critical tests when the project has them (today's gate), else `npm test` / pytest / `go test ./...` / `cargo test`,
else none (`Gate.none`: the project has no tests, and a result is never green for want of them)."""
from __future__ import annotations

import dataclasses
import json
import re
import shlex
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

FILE = "orkcraft.toml"
CRITICAL_TESTS = ("tests/test_architecture.py", "tests/test_cli.py", "tests/test_updates.py")
DEFAULT_MAP = ("tests/test_{stem}.py",)
_SHELL = ("&&", "||", "|", ";", "$(", "`", ">", "<", "*", "~")   # what only a shell reads in a command line


def test_argv(cmd: str) -> list[str]:
    """The operator's test command as a process to start: as words, or through `sh -c` when it needs a shell
    (`pytest -q && ruff check .`: split into words, `&&` reached pytest as an argument and every run failed)."""
    if any(mark in cmd for mark in _SHELL):
        return ["sh", "-c", cmd]
    return shlex.split(cmd)


@dataclass(frozen=True)
class Gate:
    run: str = ""                                  # "" = today's gate: pytest on the files
    always: tuple[str, ...] = CRITICAL_TESTS
    map: tuple[str, ...] = DEFAULT_MAP
    timeout_min: float | None = None               # None = the caller's default
    error: str = field(default="", compare=False)  # a bad file, in words
    none: bool = False                             # the project has no tests at all: nothing to run (`derive`)

    @property
    def custom(self) -> bool:
        return bool(self.run)


def _strings(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"[gate] {key} must be a list of strings")
    return tuple(value)


SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "dist", "build", "__pycache__"}
_NO_TEST = re.compile(r"no test specified")       # `npm init`'s placeholder script is no test
MAX_FOLDERS = 3                                   # package.json folders a derived gate runs


def package_dirs(root: Path, depth: int = 2) -> list[Path]:
    """The folders under `root` (itself first) that hold a `package.json`, down to `depth` levels, none inside
    `node_modules` or a hidden folder."""
    out: list[Path] = []

    def walk(folder: Path, level: int) -> None:
        if (folder / "package.json").is_file():
            out.append(folder)
        if level >= depth:
            return
        try:
            subs = sorted(p for p in folder.iterdir() if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith("."))
        except OSError:
            return
        for sub in subs:
            walk(sub, level + 1)

    walk(Path(root), 0)
    return out


def scripts_of(folder: Path) -> dict[str, str]:
    """A folder's `package.json` `scripts` (a bad file: none)."""
    try:
        data = json.loads((Path(folder) / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    got = data.get("scripts") if isinstance(data, dict) else None
    return {k: v for k, v in got.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(got, dict) else {}


def has_test(script: str) -> bool:
    """A `test` script that tests something (`npm init`'s `echo "Error: no test specified" && exit 1` does not)."""
    return bool(script.strip()) and not _NO_TEST.search(script)


def derive(root: Path) -> Gate:
    """The project's own gate, when it names none (spec 86 §3): Orkboard's way (its critical tests that exist, run by pytest on
    them and on the touched modules' tests) when the project has those files; else `npm test` (in each folder with a
    `package.json` whose `test` script tests something, three at most, `--prefix` for a folder below the root), else
    `python -m pytest -q` (a `pyproject.toml` or `tests/`), `go test ./...`, `cargo test`; none of them: `Gate(none=True)`."""
    root = Path(root)
    critical = tuple(f for f in CRITICAL_TESTS if (root / f).is_file())
    if critical:
        return Gate(always=critical)
    folders = [f for f in package_dirs(root) if has_test(scripts_of(f).get("test", ""))][:MAX_FOLDERS]
    if folders:
        runs = ["npm test" if f == root else f"npm test --prefix {shlex.quote(f.relative_to(root).as_posix())}" for f in folders]
        return Gate(run=" && ".join(runs), always=())
    for marker, run in ((("pyproject.toml", "tests"), "python -m pytest -q"), (("go.mod",), "go test ./..."),
                        (("Cargo.toml",), "cargo test")):
        if any((root / m).exists() for m in marker):
            return Gate(run=run, always=())
    return Gate(always=(), none=True)


def read(repo_root: Path) -> Gate:
    """The repository's `[gate]`; with no file or no `[gate]`, and with a bad file (`error` says why), the project's own
    (`derive`)."""
    path = Path(repo_root) / FILE
    if not path.is_file():
        return derive(repo_root)
    try:
        table = tomllib.loads(path.read_text(encoding="utf-8")).get("gate")
        if table is None:
            return derive(repo_root)
        if not isinstance(table, dict):
            raise ValueError("[gate] must be a table")
        run = table.get("run", "")
        if not isinstance(run, str):
            raise ValueError("[gate] run must be a string")
        minutes = table.get("timeout_min")
        if minutes is not None and (isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes <= 0):
            raise ValueError("[gate] timeout_min must be a number of minutes above 0")
        return Gate(run=run.strip(), always=_strings(table.get("always", list(CRITICAL_TESTS)), "always"),
                    map=_strings(table.get("map", list(DEFAULT_MAP)), "map"), timeout_min=minutes)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as e:
        return dataclasses.replace(derive(repo_root), error=f"{FILE} is not usable ({' '.join(str(e).split())[:200]}): the gate ran as with no file")


def gate_files(gate: Gate, touched: list[str], root: Path) -> list[str]:
    """`always`, then each touched file's tests by `map` (`{stem}`, `{name}`, `{dir}`); only those that exist. With no
    `run` (today's gate) a touched test file counts as its own test."""
    out = [a for a in gate.always]
    for name in touched:
        p = Path(name)
        if not gate.custom and p.parts[:1] == ("tests",) and p.suffix == ".py" and p.name.startswith("test_"):
            out.append(p.as_posix())
            continue
        if p.stem == "__init__":
            continue
        if not gate.custom and p.suffix != ".py":
            continue
        for pattern in gate.map:
            out.append(pattern.replace("{stem}", p.stem).replace("{name}", p.name).replace("{dir}", p.parent.as_posix()))
    seen: list[str] = []
    for f in out:
        if f not in seen and (Path(root) / f).is_file():
            seen.append(f)
    return seen


def command(gate: Gate, files: list[str]) -> str | None:
    """The custom command with `{files}` filled in (quoted); as is without `{files}`. None: it needs files and has none."""
    if "{files}" not in gate.run:
        return gate.run
    if not files:
        return None
    return gate.run.replace("{files}", " ".join(shlex.quote(f) for f in files))
