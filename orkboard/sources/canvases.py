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

import datetime as dt
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from orkboard.sources import sessions as _sessions
from orkboard.sources import transcripts

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
MAX_LINE = 4 * 1024 * 1024            # a single line beyond this is skipped, not parsed
CODEX_SCANNED = 300                   # rollouts looked at (newest first) to find MAX_LOCAL of the project's
AGY_PER_SESSION = 50                  # pictures read from one conversation's folder
# What agy's brain folder holds that is not a drawing: a screenshot or a browser recording says how the work went.
_AGY_NOT_DRAWN = re.compile(r"screen[-_ ]?shot|recording|click[-_ ]?feedback|scroll|browser|video", re.IGNORECASE)
_AGY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_ROLLOUT_ID = re.compile(r"^rollout-\d{4}-\d\d-\d\dT\d\d-\d\d-\d\d-(.+)$")


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


# -- the readers' shared ground: a file read from where it was last read -------------------------------------------

@dataclass
class _Tail:
    """One transcript or rollout as far as it was read: where (`offset`), what it said so far (`found`, the calls still
    waiting for their answer in `pending`), and the stamp it had then. A file that only grew is read on from `offset`;
    one that shrank or changed in place is read again; an unchanged one is not opened."""
    root: str = ""                                   # the project it was read for (a rollout's `cwd` is checked against it)
    offset: int = 0
    size: int = 0
    mtime: int = 0
    session: str = ""
    model: str = ""
    skip: bool = False                               # a rollout of another project: never read on
    found: list[Canvas] = field(default_factory=list)
    pending: dict[str, tuple] = field(default_factory=dict)
    sids: list[str] = field(default_factory=list)    # the names a Codex session's picture folder may have
    images: dict[str, dict] = field(default_factory=dict)
    done: set[str] = field(default_factory=set)


_CLAUDE: dict[str, _Tail] = {}
_CODEX: dict[str, _Tail] = {}


def _feed(tail: _Tail, path: Path, line) -> None:
    """The new complete lines of `path` (at most `transcripts.MAX_BYTES` of it), each parsed and given to `line`."""
    if tail.offset >= transcripts.MAX_BYTES:
        return
    with path.open("rb") as f:
        f.seek(tail.offset)
        data = f.read(min(tail.size, transcripts.MAX_BYTES) - tail.offset)
    end = data.rfind(b"\n") + 1
    rest = data[end:].strip()
    if rest:
        try:
            json.loads(rest)                         # a last line written whole without its newline is a line
            end = len(data)
        except ValueError:
            pass                                     # one still being written: read on the next pass
    tail.offset += end
    for raw in data[:end].splitlines():
        if len(raw) > MAX_LINE or not raw.strip():
            continue
        try:
            d = json.loads(raw)
        except ValueError:
            continue                                 # a broken line is skipped, the file goes on
        if isinstance(d, dict):
            line(tail, d)
            if tail.skip:
                return


def _read(cache: dict[str, _Tail], path: Path, root: str, line) -> _Tail | None:
    """`path`'s tail, read as far as the file goes now; None for a file that cannot be read."""
    try:
        st = path.stat()
        tail = cache.get(str(path))
        if tail is not None and tail.root == root and (tail.skip or (tail.size, tail.mtime) == (st.st_size, st.st_mtime_ns)):
            return tail
        if tail is None or tail.root != root or st.st_size <= tail.size:     # new, another project, shrunk or edited
            tail = cache[str(path)] = _Tail(root=root, session=path.stem)
        tail.size, tail.mtime = st.st_size, st.st_mtime_ns
        _feed(tail, path, line)
        return tail
    except (OSError, ValueError):
        return None


def _prune(cache: dict[str, _Tail], keep: set[str]) -> None:
    if len(cache) > 8 * _sessions.MAX_LOCAL:
        for k in [k for k in cache if k not in keep]:
            del cache[k]


def _newest(paths: list[Path], n: int) -> list[Path]:
    stamped = []
    for p in paths:
        try:
            stamped.append((p.stat().st_mtime, p))
        except OSError:
            continue
    return [p for _, p in sorted(stamped, key=lambda s: s[0], reverse=True)[:n]]


def _iso(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat(timespec="seconds")


def _dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


# -- Claude Code ------------------------------------------------------------------------------------------------------

def _claude_line(tail: _Tail, d: dict) -> None:
    """A transcript line: an assistant message's `tool_use` waits for the user message's `tool_result` of its id."""
    msg = _dict(d.get("message"))
    content = msg.get("content")
    if d.get("type") not in ("assistant", "user") or not isinstance(content, list):
        return
    for b in content:
        if not isinstance(b, dict):
            continue
        name = b.get("name")
        if b.get("type") == "tool_use" and isinstance(name, str) and (name == "Artifact" or name.startswith("mcp__")):
            tail.pending[str(b.get("id"))] = (name, _dict(b.get("input")), str(msg.get("model") or ""))
        elif b.get("type") == "tool_result":
            call = tail.pending.pop(str(b.get("tool_use_id")), None)
            at = d.get("timestamp")
            if call is None or b.get("is_error") or not isinstance(at, str) or not at:
                continue                             # a call that failed is no canvas
            c = from_call("claude", call[0], call[1], b.get("content"), at, tail.session, call[2])
            if c is not None:
                tail.found.append(c)


def read_claude(repo_root: Path) -> list[Canvas]:
    """§1.1: `Artifact`, `mcp__Claude_Docs__batch` with `container.create`, `mcp__Figma__create_new_file`, from the
    project's transcripts and its worktrees' (the newest `sessions.MAX_LOCAL`)."""
    out: list[Canvas] = []
    try:
        folders = [_sessions.claude_projects_dir(repo_root)]
        trees = Path(repo_root) / ".orkcraft" / "worktrees"
        if trees.is_dir():
            folders += [_sessions.claude_projects_dir(w) for w in sorted(trees.glob("*")) if w.is_dir()]
        files = _newest([p for f in folders if f.is_dir() for p in f.glob("*.jsonl")], _sessions.MAX_LOCAL)
        for path in files:
            tail = _read(_CLAUDE, path, "", _claude_line)
            out += tail.found if tail is not None else []
        _prune(_CLAUDE, {str(p) for p in files})
    except OSError:
        pass
    return out


# -- Codex ------------------------------------------------------------------------------------------------------------

def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _under(cwd: Any, root: str) -> bool:
    try:
        return isinstance(cwd, str) and bool(cwd) and Path(cwd).resolve().is_relative_to(root)
    except (OSError, ValueError, RuntimeError):
        return False


def _safe(name: str) -> str:
    """Codex's file name for a session or a call (`ext/image-generation/src/artifact.rs`): all but [A-Za-z0-9_-] is `_`."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name) or "generated_image"


def _codex_image(tail: _Tail, call_id: Any, at: Any, prompt: Any = None, saved: Any = None, status: Any = None,
                 failure: Any = None) -> None:
    """What one image generation says: the response item gives the call and its prompt, the end event (or the item
    completed of a paginated rollout) the saved path. They meet on the call's id; the picture is made on the way out."""
    if not isinstance(call_id, str) or not call_id:
        return
    img = tail.images.setdefault(call_id, {"at": "", "prompt": "", "saved": "", "failed": False})
    img["at"] = at if isinstance(at, str) and at else img["at"]
    img["prompt"] = prompt if isinstance(prompt, str) and prompt else img["prompt"]
    img["saved"] = saved if isinstance(saved, str) and saved else img["saved"]
    img["failed"] = img["failed"] or bool(failure) or (isinstance(status, str) and status not in ("completed", ""))


def _codex_mcp(tail: _Tail, call_id: Any, name: str, args: Any, result: Any, at: Any) -> None:
    """An MCP call that answered: the same call seen twice (its response items and its end event) counts once."""
    if not isinstance(at, str) or not at or str(call_id) in tail.done:
        return
    tail.done.add(str(call_id))
    c = from_call("codex", name, args, result, at, tail.session, tail.model)
    if c is not None:
        tail.found.append(c)


def _tool_result(r: Any) -> Any:
    """A CallToolResult's answer (`protocol/src/mcp.rs`), None for a call that failed: `{"Ok": {content, …}}` in an end
    event (a Rust `Result`), the bare result in a paginated rollout's item."""
    r = _dict(r)
    r = _dict(r.get("Ok")) if "Ok" in r else {} if "Err" in r else r
    if not r or r.get("is_error") or r.get("isError"):
        return None
    return [r.get("content"), r.get("structured_content") or r.get("structuredContent")]


def _mcp_name(name: str, namespace: str) -> str:
    """`mcp__<server>__<tool>` from a `function_call`: the name as it is, or the namespace (`mcp__<server>__`) and the name."""
    if name.startswith("mcp__"):
        return name
    return namespace.rstrip("_") + "__" + name if namespace.startswith("mcp__") else ""


def _codex_line(tail: _Tail, d: dict) -> None:
    """A rollout line `{timestamp, type, payload}`: `session_meta` (its `cwd` says whose it is), `turn_context` (the model),
    `response_item` (`image_generation_call`; `function_call` and its `function_call_output`), `event_msg`
    (`image_generation_end`, `mcp_tool_call_end`, and a paginated rollout's `item_completed`)."""
    p, at, kind = _dict(d.get("payload")), d.get("timestamp"), d.get("type")
    if kind == "session_meta":
        if not _under(p.get("cwd"), tail.root):
            tail.skip = True
            return
        tail.sids = list(dict.fromkeys(str(p[k]) for k in ("id", "session_id") if p.get(k)))
        tail.session = tail.sids[0] if tail.sids else tail.session
    elif kind == "turn_context":
        tail.model = str(p.get("model") or tail.model)
    elif kind == "response_item":
        t = p.get("type")
        if t == "image_generation_call":
            _codex_image(tail, p.get("id") or p.get("call_id"), at, p.get("revised_prompt"), None, p.get("status"))
        elif t == "function_call":
            full = _mcp_name(str(p.get("name") or ""), str(p.get("namespace") or ""))
            try:
                args = json.loads(p.get("arguments") or "{}")
            except ValueError:
                args = {}
            if full:
                tail.pending[str(p.get("call_id"))] = (full, args)
        elif t == "function_call_output":
            call = tail.pending.pop(str(p.get("call_id")), None)
            if call is not None and p.get("success") is not False:
                _codex_mcp(tail, p.get("call_id"), call[0], call[1], p.get("output"), at)
    elif kind == "event_msg":
        t = p.get("type")
        if t == "image_generation_end":
            _codex_image(tail, p.get("call_id"), at, p.get("revised_prompt"), p.get("saved_path"), p.get("status"),
                         p.get("failure"))
        elif t == "mcp_tool_call_end":
            inv, res = _dict(p.get("invocation")), _tool_result(p.get("result"))
            if res is not None and inv.get("server") and inv.get("tool"):
                _codex_mcp(tail, p.get("call_id"), f"mcp__{inv['server']}__{inv['tool']}", inv.get("arguments"), res, at)
        elif t == "item_completed":                  # a paginated rollout: the turn's items (`protocol/src/items.rs`)
            it = _dict(p.get("item"))
            what = str(it.get("kind") or it.get("type") or "").lower().replace("_", "")
            if what in ("imagegeneration", "imagegen.generation"):
                _codex_image(tail, it.get("id"), at, it.get("revisedPrompt") or it.get("revised_prompt"),
                             it.get("savedPath") or it.get("saved_path"), it.get("status"), it.get("failure"))
            elif what == "mcptoolcall" and it.get("server") and it.get("tool") and it.get("status") in ("completed", None):
                res = _tool_result(it.get("result"))
                if res is not None:
                    _codex_mcp(tail, it.get("id"), f"mcp__{it['server']}__{it['tool']}", it.get("arguments"), res, at)


def _codex_pictures(tail: _Tail) -> list[Canvas]:
    """A session's image generations as *Picture* canvases: the file `saved_path` says, else the one Codex keeps under
    `$CODEX_HOME/generated_images/<session>/<call>.png` when it is there; the title the revised prompt's first line."""
    out = []
    for call_id, img in tail.images.items():
        if img["failed"] or not img["at"]:
            continue
        file = img["saved"] if Path(img["saved"]).is_absolute() else ""
        for sid in () if file else tail.sids:
            kept = codex_home() / "generated_images" / _safe(sid) / f"{_safe(call_id)}.png"
            if kept.is_file():
                file = str(kept)
                break
        if file:
            title = next((l.strip() for l in img["prompt"].splitlines() if l.strip()), "") or Path(file).stem
            out.append(Canvas("codex", "picture", title[:TITLE_CHARS], img["at"], file=file, session=tail.session,
                              model=tail.model))
    return out


def read_codex(repo_root: Path) -> list[Canvas]:
    """§1.2: `image_generation_call` (a picture) and a canvas tool's MCP call that answered with a link, from the
    rollouts whose `session_meta.cwd` is under the project (the newest `sessions.MAX_LOCAL` of them)."""
    out: list[Canvas] = []
    try:
        root = str(Path(repo_root).resolve())
        listed = _newest(list((codex_home() / "sessions").glob("*/*/*/rollout-*.jsonl")), CODEX_SCANNED)
        mine = 0
        for path in listed:
            tail = _read(_CODEX, path, root, _codex_line)
            if tail is None or tail.skip:
                continue
            out += tail.found + _codex_pictures(tail)
            mine += 1
            if mine >= _sessions.MAX_LOCAL:
                break
        _prune(_CODEX, {str(p) for p in listed})
    except OSError:
        pass
    return out


# -- agy --------------------------------------------------------------------------------------------------------------

def _agy_meta(image: Path) -> dict:
    """The `.metadata.json` beside a file of the brain folder (`<file>.metadata.json`), {} when it has none."""
    for name in (image.name + ".metadata.json", image.stem + ".metadata.json"):
        try:
            d = json.loads((image.parent / name).read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict):
            return d
    return {}


def read_agy(repo_root: Path, sessions: list[str]) -> list[Canvas]:
    """§1.3: the pictures `generate_image` wrote in the brain folders of the conversations `sessions`: each image
    directly in the folder (not in a hidden one, `.system_generated`), but a screenshot or a recording, which its name or
    its `.metadata.json` says. Written nowhere, the file only looked at: its time is the file's."""
    out: list[Canvas] = []
    try:
        brain = _sessions.agy_brain_dir()
        for sid in dict.fromkeys(sessions):
            if not isinstance(sid, str) or not _AGY_ID.match(sid) or ".." in sid:
                continue                             # a conversation id is a name, never a path
            try:
                files = sorted((p for p in (brain / sid).iterdir() if not p.name.startswith(".") and not p.is_symlink()
                                and p.suffix.lower() in IMAGE_SUFFIXES and p.is_file()), key=lambda p: p.name)
            except OSError:
                continue
            for p in files[:AGY_PER_SESSION]:
                meta = _agy_meta(p)
                said = " ".join(str(v) for k, v in meta.items() if k != "summary" and isinstance(v, (str, int)))
                if _AGY_NOT_DRAWN.search(p.name) or _AGY_NOT_DRAWN.search(said):
                    continue
                words = next((str(meta[k]) for k in ("summary", "description", "prompt", "title") if meta.get(k)), "")
                title = next((l.strip() for l in words.splitlines() if l.strip()), "") or p.stem.replace("_", " ")
                out.append(Canvas("agy", "picture", title[:TITLE_CHARS], _iso(p.stat().st_mtime), file=str(p), session=sid))
    except OSError:
        pass
    return out


def read_all(repo_root: Path, agy_sessions: list[str] = ()) -> list[Canvas]:
    """Every canvas of the project's sessions, oldest first; a reader that fails gives nothing, and a canvas drawn
    again is the one, at its last time."""
    found: list[Canvas] = []
    for read in (lambda: read_claude(repo_root), lambda: read_codex(repo_root),
                 lambda: read_agy(repo_root, list(agy_sessions))):
        try:
            found += read()
        except Exception:                # a tool's format that changed never stops the Board
            continue
    last: dict[str, Canvas] = {}
    for c in found:
        if c.key not in last or c.at >= last[c.key].at:
            last[c.key] = c
    return sorted(last.values(), key=lambda c: c.at)
