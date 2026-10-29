"""Where Orkboard runs, for whoever looks into an error (the owner's notes of 19 October): its version, the Python and
the machine, each AI tool as this process finds it (the path it runs, its version, whether it looks signed in) and
which of the environment's sign-in settings are set. Saved as `about.json` beside the day's logs (gui/logs_save.py).

The values of the environment are never written, only whether each is set, except for the few that hold no secret
(paths, the shell): a key's presence is what tells why a tool that is signed in in a terminal is not in Orkboard.

    about(machine, root=project)           # {"orkboard", "build", "python", "platform", "launched", "tools": [...], "env": {...}, "project"}
                                           # a tool's row: path, version, signed in; Claude's its `claude auth status`
                                           # build: the version and a source checkout's git head; project (spec 107 §2.4): the gate and
                                           # where it comes from, each package folder's installs, the venv, the Board's settings

No face, no model.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Callable

from orkboard import __version__
from orkboard.realm import gate_config

# What decides which account an AI tool runs on: shown as set or not, never their values.
SIGN_IN_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_BASE_URL",
               "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")
# What holds no secret and says where a tool looks: shown as they are.
SHOWN_ENV = ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "HOME", "SHELL", "PATH", "ORKBOARD_FROM")


def env_of(env: dict | None = None) -> dict[str, str]:
    """The environment's sign-in settings as "set" (never their values), and the few that hold no secret as they are."""
    env = dict(os.environ) if env is None else env
    out = {name: "set" for name in SIGN_IN_ENV if env.get(name)}
    out.update({name: str(env[name]) for name in SHOWN_ENV if env.get(name)})
    return out


LOCKS = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb")


def build_of(package: Path | None = None) -> dict:
    """The installed version and, from a source checkout (a `.git` beside the package), its git head ("" otherwise)."""
    package = Path(package) if package else Path(__file__).resolve().parents[1]
    head = ""
    if (package.parent / ".git").exists():
        try:
            got = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=package.parent, capture_output=True,
                                 text=True, timeout=5)
            head = got.stdout.strip() if got.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            pass
    return {"version": __version__, "git": head}


def _gate_from(root: Path, gate: gate_config.Gate) -> str:
    """Where the gate comes from: `orkcraft.toml` (a `[gate]` table), `derived` (the project's own, `gate_config.derive`) or `none`."""
    try:
        if "gate" in tomllib.loads((root / gate_config.FILE).read_text(encoding="utf-8")) and not gate.error:
            return gate_config.FILE
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        pass
    return "none" if gate.none else "derived"


def project_of(root: Path | str, board: Callable[[Path], dict] | None = None) -> dict:
    """What decides whether a task's gate can run in a project (spec 107 §2.4): the gate (`run`, `from`, `always`, an `error`),
    each folder with a `package.json` (`dir`, whether `node_modules` is installed, its `lock` file), whether a `venv` is there,
    and the Board's own settings (the target, the branch it merges into…) as `board` reads them."""
    root = Path(root)
    gate = gate_config.read(root)
    out: dict[str, Any] = {
        "gate": {"run": gate.run, "from": _gate_from(root, gate), "always": list(gate.always),
                 **({"error": gate.error} if gate.error else {})},
        "packages": [{"dir": f.relative_to(root).as_posix() or ".", "node_modules": (f / "node_modules").is_dir(),
                      "lock": next((n for n in LOCKS if (f / n).is_file()), "")} for f in gate_config.package_dirs(root)],
        "venv": any((root / n).is_dir() for n in (".venv", "venv"))}
    if board is not None:
        try:
            out["board"] = board(root)
        except Exception:                      # the settings of a broken file: the rest is still said
            pass
    return out


def about(machine: Any = None, detect: Callable[[], list] | None = None, env: dict | None = None,
          auth: Callable[[str], dict] | None = None, root: Path | str | None = None) -> dict:
    """Orkboard, its Python and machine, how it was started, each AI tool as this process finds it, and the
    environment as `env_of` says it. `detect`: tools.detect (it asks each tool found its version); `auth`:
    tools.claude_auth, Claude Code's own word on its sign-in here (a terminal's may differ: another config folder). `root`: the
    shown project (`project_of`), none without one."""
    from orkboard import tools
    env = dict(os.environ) if env is None else env
    auth = auth or (lambda path: tools.claude_auth(path, env=env))
    chosen = getattr(machine, "tools", None) or {}
    found = []
    for s in (detect or tools.detect)():
        choice = chosen.get(s.tool.id)
        found.append({"id": s.tool.id, "found": s.found, "path": s.path, "version": s.version,
                      "signed_in": s.logged_in, "billing_seen": s.billing,
                      "turned_on": bool(getattr(choice, "enabled", False)), "billing": getattr(choice, "billing", ""),
                      **({"auth_status": auth(s.path)} if s.tool.id == "claude" and s.found else {})})
    from orkboard import settings
    return {"orkboard": __version__, "build": build_of(), "python": sys.version.split()[0], "executable": sys.executable,
            "platform": platform.platform(), "launched": env.get("ORKBOARD_FROM") or "terminal",
            "cwd": os.getcwd(), "tools": found, "env": env_of(env),
            **({"project": project_of(root, lambda r: settings.board_of(r, getattr(machine, "ideas", None)))} if root else {})}
