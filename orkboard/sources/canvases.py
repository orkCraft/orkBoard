"""Canvases (docs/specs/78-canvases.md §1): what Claude Code, Codex and agy drew outside the code, read from what each
tool already writes on the machine.

    Canvas("claude", "design", "Onboarding", "2026-10-25T10:00:00+00:00", url="https://claude.ai/artifact/…")
    c.key                                       # "claude:https://claude.ai/artifact/…": the tool and its URL or file
    c.line() · Canvas.from_line(d)              # one line of `.orkcraft/canvases.jsonl` (core/canvases.py) and back
    link_host(url)                              # "claude.ai" for a link of an allowed host, else ""
    from_call("claude", "Artifact", args, result, at, session, model)   # one tool call as a canvas, or None (the readers', the hook's)
    read_all(repo_root, agy_sessions)           # every canvas the project's sessions drew, oldest first

The readers: `read_claude` (the project's transcripts and its worktrees'), `read_codex` (the rollouts whose `cwd` is
under the project), `read_agy` (the brain folders of the conversations named: Orkboard's own runs, the hook's). Each is
bounded and never raises: a file it cannot read gives nothing. Read-only, no face.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

TOOLS = ("claude", "codex", "agy")
TOOL_WORDS = {"claude": "Claude", "codex": "Codex", "agy": "Antigravity"}
KINDS = ("design", "slides", "document", "page", "picture")
# The hosts a canvas's link may open on (§3.3): another host is shown as text, never a link.
LINK_HOSTS = ("claude.ai", "figma.com", "tldraw.com", "canva.com")
TITLE_CHARS = 120
# A canvas tool reached through MCP (Codex's plugins, Claude's connectors): its server's name in `mcp__<server>__<tool>`.
KNOWN_MCP = ("figma", "tldraw", "canva")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
_ARTIFACT_URL = re.compile(r"https://claude\.ai/(?:code/)?artifact/[A-Za-z0-9_-]+")
_URL = re.compile(r"https://[^\s\"'<>)\]]+")
_IMAGE_PATH = re.compile(r"(?:[A-Za-z]:)?[/\\][^\s\"'<>]+?\.(?:png|jpe?g|webp|gif)\b", re.IGNORECASE)


@dataclass
class Canvas:
    tool: str                  # TOOLS
    kind: str                  # KINDS
    title: str                 # the tool's or the agent's words, cut to TITLE_CHARS
    at: str                    # when it was drawn (ISO 8601)
    url: str = ""              # an https link, when it has one
    file: str = ""             # a local file (absolute), when it has one
    session: str = ""          # the session that drew it
    model: str = ""            # the model that drew it, when the tool says

    @property
    def key(self) -> str:
        return f"{self.tool}:{self.url or self.file}"

    def line(self) -> dict:
        return {"key": self.key, **asdict(self)}

    @classmethod
    def from_line(cls, d: dict) -> Canvas | None:
        """A canvas from its line; None for a line that is not one (a `seen` line, a broken one)."""
        if not isinstance(d, dict) or d.get("tool") not in TOOLS or d.get("kind") not in KINDS:
            return None
        url, file = str(d.get("url") or ""), str(d.get("file") or "")
        if not (url.startswith("https://") or file):
            return None
        return cls(str(d["tool"]), str(d["kind"]), str(d.get("title") or "")[:TITLE_CHARS], str(d.get("at") or ""),
                   url if url.startswith("https://") else "", file, str(d.get("session") or ""), str(d.get("model") or ""))


def link_host(url: str) -> str:
    """The allowed host a link opens on ("claude.ai", "figma.com", …: a subdomain counts), else ""."""
    try:
        parts = urlparse(url)
    except ValueError:
        return ""
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        return ""
    return next((h for h in LINK_HOSTS if host == h or host.endswith("." + h)), "")


def text_of(result: Any) -> str:
    """A tool's answer as text: a string, a list of blocks (`{"type": "text", "text"}`), a dict (its JSON's strings)."""
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        return "\n".join(text_of(r) for r in result)
    if isinstance(result, dict):
        if isinstance(result.get("text"), str):
            return result["text"]
        return "\n".join(text_of(v) for v in result.values() if isinstance(v, (str, list, dict)))
    return ""


def _kind_of_type(type_url: str) -> str:
    t = type_url.lower()
    return "slides" if "slide" in t or "deck" in t else "document" if "doc" in t else "design" if "design" in t else "page"


def _first_link(text: str) -> str:
    return next((u.rstrip(".,;") for u in _URL.findall(text) if link_host(u.rstrip(".,;"))), "")


def from_call(tool: str, name: str, args: Any, result: Any, at: str, session: str = "", model: str = "") -> Canvas | None:
    """One tool call as the canvas it drew (§1), or None: `tool` is the AI tool (TOOLS), `name` its tool's name as the
    transcript or the hook says it, `args` its input, `result` its answer (a call that failed is not passed here)."""
    args = args if isinstance(args, dict) else {}
    text = text_of(result)
    made = lambda kind, title, url="", file="": Canvas(tool, kind, str(title or "")[:TITLE_CHARS], at, url, file, session, model)
    if name == "Artifact":
        if (args.get("action") or "publish") != "publish" or args.get("asset"):
            return None
        m = _ARTIFACT_URL.search(text) or _ARTIFACT_URL.search(str(args.get("url") or ""))
        if not m:
            return None
        file = str(args.get("file_path") or "")
        kind = _kind_of_type(str(args["type_url"])) if args.get("type_url") else "page"
        return made(kind, args.get("title") or (Path(file).stem if file else ""), m.group(0),
                    file if file.lower().endswith((".html", ".htm", ".md")) and Path(file).is_absolute() else "")
    if name == "mcp__Claude_Docs__batch":
        create = (args.get("container") or {}).get("create") if isinstance(args.get("container"), dict) else None
        m = _ARTIFACT_URL.search(text)
        if not isinstance(create, dict) or not m:
            return None
        return made("document", create.get("name") or "", m.group(0))
    server = name.split("__")[1].lower() if name.startswith("mcp__") and name.count("__") >= 2 else ""
    if server in KNOWN_MCP:
        if server == "figma" and not name.endswith("create_new_file"):
            return None
        url = _first_link(text)
        title = next((args[k] for k in ("fileName", "file_name", "name", "title") if isinstance(args.get(k), str)), "")
        return made("design", title, url) if url else None
    if name == "generate_image":
        found = _IMAGE_PATH.search(text) or next((m for v in args.values() if isinstance(v, str)
                                                  for m in [_IMAGE_PATH.search(v)] if m), None)
        if not found:
            return None
        title = next((args[k] for k in ("Prompt", "prompt", "ImageName", "Description") if isinstance(args.get(k), str)), "")
        return made("picture", title.splitlines()[0] if title else Path(found.group(0)).stem, file=found.group(0))
    return None


def read_claude(repo_root: Path) -> list[Canvas]:
    """§1.1: `Artifact`, `mcp__Claude_Docs__batch` with `container.create`, `mcp__Figma__create_new_file`."""
    return []


def read_codex(repo_root: Path) -> list[Canvas]:
    """§1.2: `image_generation_call` (a picture) and a canvas tool's MCP call that answered with a link."""
    return []


def read_agy(repo_root: Path, sessions: list[str]) -> list[Canvas]:
    """§1.3: the pictures `generate_image` wrote in the brain folders of `sessions`."""
    return []


def read_all(repo_root: Path, agy_sessions: list[str] = ()) -> list[Canvas]:
    """Every canvas of the project's sessions, oldest first; a reader that fails gives nothing."""
    out: list[Canvas] = []
    for read in (lambda: read_claude(repo_root), lambda: read_codex(repo_root),
                 lambda: read_agy(repo_root, list(agy_sessions))):
        try:
            out += read()
        except Exception:                # a tool's format that changed never stops the Board
            continue
    return sorted(out, key=lambda c: c.at)
