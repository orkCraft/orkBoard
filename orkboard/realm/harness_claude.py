"""How orks call Claude Code: its argv builders and flags (split from harnesses.py).

Read-only and web tool lists, what a reading call may not read and the floor it runs on, the one-shot, reading,
working and tool-limited calls, `--add-dir` for read folders, the reader of its output and of the files it read,
and `_claude_run`, the run flags the installed CLI lists (effort, budget, no session persistence; `cli_has`, which
reads its `--help`, is in realm/harness_tools.py with the other process this package starts). The
registry that wires them to a `Harness` stays in realm/harnesses.py, which re-exports every name here.
"""
from __future__ import annotations

import json
from pathlib import Path

from orkboard.realm.harness_tools import EFFORTS, _HELP, _model, cli_has, effort_supported, json_lines  # noqa: F401


# Claude Code ---------------------------------------------------------------------------------------

CLAUDE_READ_ONLY = ["--allowedTools", "Read,Grep,Glob",
                    "--disallowedTools", "Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch"]
CLAUDE_READ_WEB = ["--allowedTools", "Read,Grep,Glob,WebSearch,WebFetch",
                   "--disallowedTools", "Bash,Edit,Write,MultiEdit,NotebookEdit"]


# What a read-only call may not read (spec 97 §1): gitignore patterns relative to its folder, in its one --disallowedTools.
READ_LOCKFILES = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb", "uv.lock",
                  "poetry.lock", "Pipfile.lock", "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum", "Podfile.lock",
                  "pubspec.lock", "mix.lock", "flake.lock", "packages.lock.json")
READ_VENDORED = ("node_modules", "bower_components", "vendor", "third_party", "Pods", ".venv", "venv", "site-packages")
READ_GENERATED = ("dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".turbo", ".parcel-cache", "coverage",
                  "storybook-static", "__pycache__")
READ_DENIED = ([f"Read(**/{name})" for name in READ_LOCKFILES] + [f"Read(**/{name}/**)" for name in READ_VENDORED + READ_GENERATED]
               + ["Read(**/*.min.js)", "Read(**/*.min.css)", "Read(**/*.map)", "Read(**/*.pyc)"]
               + ["Read(**/decisions.md)", "Read(**/DECISIONS.md)"])     # a leader gets its goal's entry by code (spec 97 §5)
NO_MCP = '{"mcpServers":{}}'


def _claude_mcp() -> list[str]:
    """A Test bench run's MCP servers only (realm/cassette.py): its configuration, and none of the person's own."""
    from orkboard.env import getenv
    path = getenv("MCP_CONFIG")
    return ["--mcp-config", path, "--strict-mcp-config"] if path else []


def claude_floor(h) -> tuple[list[str], list[str]]:
    """(argv, names) of the floor of a read-only call (spec 97 §2): none of the person's MCP servers (unless a bench run
    names its own) and no skills, each only when the installed CLI lists its flag; the names are what it added, as
    its line in the call log says them (`bare`)."""
    args: list[str] = []
    names: list[str] = []
    if _claude_mcp():
        args += _claude_mcp()
    elif cli_has(h, "--strict-mcp-config") and cli_has(h, "--mcp-config"):
        args += ["--strict-mcp-config", "--mcp-config", NO_MCP]
        names.append("mcp")
    if cli_has(h, "--disable-slash-commands"):
        args.append("--disable-slash-commands")
        names.append("skills")
    return args, names


def _claude_ask(h, prompt, folder, model):
    return [h.bin, "-p", prompt, "--output-format", "json", *_model("--model", model), *_claude_mcp()]


def _claude_read_tools(web: bool) -> list[str]:
    """The read-only (or web) tool lists with `READ_DENIED` in their one --disallowedTools."""
    tools = list(CLAUDE_READ_WEB if web else CLAUDE_READ_ONLY)
    tools[tools.index("--disallowedTools") + 1] += "," + ",".join(READ_DENIED)
    return tools


def _claude_read(h, prompt, workdir, model, web):
    """Its tool calls are in the output (stream-json, spec 97 §3), so what it read is counted."""
    return [h.bin, "-p", prompt, "--output-format", "stream-json", "--verbose", *_claude_read_tools(web),
            *_model("--model", model), *claude_floor(h)[0]]


# Every built-in tool a carrier must not have; MCP tools not in --allowedTools are refused in -p (their schemas are
# still shown: an operation's prepare writes its action's arguments from one, spec 38 §4). None allowed: no list.
CLAUDE_NO_TOOLS = "Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch,Read,Grep,Glob,Task,TodoWrite"


def _claude_call(h, prompt, workdir, model, allow):
    return [h.bin, "-p", prompt, "--output-format", "stream-json", "--verbose",
            *(["--allowedTools", ",".join(allow)] if allow else []), "--disallowedTools", CLAUDE_NO_TOOLS, *_model("--model", model),
            *_claude_mcp()]


def claude_envelope(stdout: str) -> dict | None:
    """The result of a run of Claude Code, from either output: the last `result` event of stream-json, else the one JSON
    object of `--output-format json` (a recorded call of before, any other caller); None when it prints neither."""
    try:
        env = json.loads(stdout.strip())
    except ValueError:
        env = None
    if isinstance(env, dict) and env.get("type", "result") == "result":
        return env
    return next((e for e in reversed(json_lines(stdout)) if e.get("type") == "result"), None)


def claude_events(stdout: str) -> list[dict]:
    """The events of a stream-json output ([] for the one JSON object of `--output-format json`, or no JSON at all)."""
    events = json_lines(stdout)
    return [] if len(events) == 1 and events[0].get("type", "result") == "result" else events


def claude_reads(stdout: str, folder: str | Path = "") -> dict:
    """What a read-only call looked at, from its stream-json: {"files": distinct files its `Read` tool uses named,
    "searches": its `Grep` and `Glob` uses, "paths": the first 30 files (relative to `folder` when under it), "denied":
    the `Read`, `Grep` and `Glob` uses its result envelope says were refused} (spec 97 §3)."""
    paths: list[str] = []
    uses: set[str] = set()
    searches = 0
    for event in claude_events(stdout):
        message = event.get("message") if event.get("type") == "assistant" else None
        for part in (message.get("content") if isinstance(message, dict) else None) or []:
            if not isinstance(part, dict) or part.get("type") != "tool_use" or (part.get("id") and part["id"] in uses):
                continue
            uses.add(part.get("id"))
            given = part.get("input") if isinstance(part.get("input"), dict) else {}
            if part.get("name") == "Read" and given.get("file_path"):
                path = str(given["file_path"])
                try:
                    path = Path(path).relative_to(folder).as_posix() if folder else path
                except ValueError:
                    pass
                if path not in paths:
                    paths.append(path)
            elif part.get("name") in ("Grep", "Glob"):
                searches += 1
    refused = (claude_envelope(stdout) or {}).get("permission_denials")
    denied = sum(1 for d in refused if isinstance(d, dict) and (d.get("tool_name") or d.get("tool")) in ("Read", "Grep", "Glob")) \
        if isinstance(refused, list) else 0
    return {"files": len(paths), "searches": searches, "paths": paths[:30], "denied": denied}


def claude_error(stdout: str) -> str:
    """Why a run of Claude Code failed, from its result envelope (`--output-format json`, or stream-json's last
    `result` event): its own words ("Not logged in · Please run /login") when it is an error, else "". The envelope
    puts `is_error` and `result` after `usage`, so a line cut from the raw JSON never says why."""
    try:
        events = [json.loads(stdout.strip())]
    except ValueError:
        events = json_lines(stdout)
    for event in reversed(events):
        if not isinstance(event, dict) or event.get("type", "result") != "result":
            continue
        subtype = str(event.get("subtype") or "")
        if event.get("is_error") is True or subtype.startswith("error"):
            for key in ("result", "error"):
                if isinstance(event.get(key), str) and event[key].strip():
                    return event[key].strip()
            return subtype or str(event.get("terminal_reason") or "") or "error"
    return ""


def _claude_read_dirs(dirs: list[str]) -> list[str]:
    """`--add-dir` for each folder, and no edit there (`//` makes a rule's path absolute)."""
    out = [a for d in dirs for a in ("--add-dir", d)]
    rules = [f"{tool}(/{Path(d).as_posix()}/**)" for d in dirs if Path(d).is_absolute()
             for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit")]
    return out + (["--disallowedTools", ",".join(rules)] if rules else [])


def _claude_work_rules(allow: list[str], deny: list[str]) -> list[str]:
    """The commands a working task may run (realm/task_commands.py): in `-p` a command not allowed is refused, and a
    denied one is refused whatever is allowed."""
    return [*(["--allowedTools", ",".join(allow)] if allow else []), *(["--disallowedTools", ",".join(deny)] if deny else [])]


def _claude_work(h, prompt, workdir, model, resume):
    return [h.bin, "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits",
            *_model("--model", model), *(["--resume", resume] if resume else []), *_claude_mcp()]


def _claude_run(h, model, effort="", budget=None, one_shot=False):
    """`--effort <level>` (a known level, never on the laborer tier), `--max-budget-usd <x>`, `--no-session-persistence`:
    each only when the installed CLI lists it."""
    from orkboard.realm.harnesses import tier_of_model
    out = []
    if effort in EFFORTS and (h.tier_for(model) or tier_of_model(model)) != "laborer" and cli_has(h, "--effort"):
        out += ["--effort", effort]
    if isinstance(budget, (int, float)) and budget > 0 and cli_has(h, "--max-budget-usd"):
        out += ["--max-budget-usd", f"{budget:.2f}"]
    if one_shot and cli_has(h, "--no-session-persistence"):
        out.append("--no-session-persistence")
    return out
