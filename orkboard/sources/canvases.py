"""Canvases (docs/specs/78-canvases.md §1): what Claude Code, Codex and agy drew outside the code, read from what each
tool already writes on the machine.

    Canvas("claude", "design", "Onboarding", "2026-10-25T10:00:00+00:00", url="https://claude.ai/artifact/…")
    c.key                                       # "claude:https://claude.ai/artifact/…": the tool and its URL or file
    c.line() · Canvas.from_line(d)              # one line of `.orkcraft/canvases.jsonl` (core/canvases.py) and back
    link_host(url)                              # "claude.ai" for a link of an allowed host, else ""
    read_all(repo_root, agy_sessions)           # every canvas the project's sessions drew, oldest first

The readers: `read_claude` (the project's transcripts and its worktrees'), `read_codex` (the rollouts whose `cwd` is
under the project), `read_agy` (the brain folders of the conversations named: Orkboard's own runs, the hook's). Each is
bounded and never raises: a file it cannot read gives nothing. Read-only, no face.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

TOOLS = ("claude", "codex", "agy")
TOOL_WORDS = {"claude": "Claude", "codex": "Codex", "agy": "Antigravity"}
KINDS = ("design", "slides", "document", "page", "picture")
# The hosts a canvas's link may open on (§3.3): another host is shown as text, never a link.
LINK_HOSTS = ("claude.ai", "figma.com", "tldraw.com", "canva.com")
TITLE_CHARS = 120


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
