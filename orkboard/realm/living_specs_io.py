"""The living specs out and in (docs/specs/127-the-fields-best-in-our-formats.md §C.4; decisions §205): `realm/living_specs.py`'s specs written as OpenSpec's, and OpenSpec's and Kiro's read
into them. No model, no face; `realm/write_out.py` and `realm/read_in.py` call it.

    living_specs_io.export(board, to, skipped)      # each living spec as `to/openspec/specs/<capability>/spec.md`, the text as kept: how many were written
    living_specs_io.take(root, board=None, dry=False)   # OpenSpec's (`openspec/specs/*/spec.md`) and Kiro's (`.kiro/specs/*/requirements.md`) specs read in: how many were kept
    living_specs_io.parse_kiro(text, name)          # a Kiro requirements file as a spec (its `### Requirement N` or user stories the requirements, its `WHEN … SHALL …` lines the scenarios)

**Out**: a file at that path that Orkboard did not write (its front matter has no `capability` and `updated`) is never touched (named in `skipped`); one it wrote that no longer belongs is removed.
**In**: only where no living spec of that capability is kept, never over one (so a file of Orkboard's own export is the spec it was and is never read twice); a link, a secret and a file over
1 MB are never read. The capability is the folder's name as a slug.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import doc_formats, living_specs

MAX_BYTES = 1_000_000
MAX_REQUIREMENTS = 40
_STORY = re.compile(r"^\s*(?:\*\*)?(?:User Story:?(?:\*\*)?\s*)?(As an? .+)$", re.I)
_REQ_HEAD = re.compile(r"^#{2,4}[ \t]+Requirement\b[ \t]*(\d+(?:\.\d+)*)?[ \t]*[:.\-–—]?[ \t]*(.*?)[ \t]*#*[ \t]*$", re.I)
_MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_WHEN = re.compile(r"\b(?:WHEN|IF)\b\s+(.+)$")


# -- out -------------------------------------------------------------------------------------------------------------------------------------

def _ours(file: Path) -> bool:
    try:
        meta, _rest = doc_formats.front_matter(file.read_text("utf-8", errors="replace")[:4000])
    except OSError:
        return False
    return bool(meta.get("capability")) and "updated" in meta


def export(board: Path, to: Path, skipped: list[str]) -> int:
    """Each living spec of the Board as `to/openspec/specs/<capability>/spec.md`, its text as it is kept; the number written."""
    folder = Path(to) / "openspec" / "specs"
    keep: set[str] = set()
    n = 0
    for row in living_specs.list_(board):
        cap = row["capability"]
        source = Path(board) / living_specs.DIR / f"{cap}.md"
        file = folder / cap / "spec.md"
        keep.add(cap)
        if file.is_symlink() or (file.exists() and not _ours(file)):
            skipped.append(str(file))
            continue
        try:
            text = source.read_text("utf-8")
        except OSError:
            continue
        file.parent.mkdir(parents=True, exist_ok=True)
        tmp = file.with_name(f".{file.name}.tmp")
        tmp.write_text(text, "utf-8")
        tmp.replace(file)
        n += 1
    try:
        for d in sorted(folder.iterdir()) if folder.is_dir() else []:                  # one Orkboard wrote that no longer belongs
            f = d / "spec.md"
            if d.name not in keep and d.is_dir() and not d.is_symlink() and f.is_file() and not f.is_symlink() and _ours(f):
                f.unlink()
                if not any(d.iterdir()):
                    d.rmdir()
    except OSError:
        pass
    return n


# -- in --------------------------------------------------------------------------------------------------------------------------------------

def _plain(root: Path, rel: str) -> Path | None:
    p = Path(root)
    for part in rel.split("/"):
        p = p / part
        if p.is_symlink():
            return None
    return p


def _text(root: Path, rel: str) -> str | None:
    p = _plain(root, rel)
    try:
        if p is None or not p.is_file() or is_secret(rel) or p.stat().st_size > MAX_BYTES:
            return None
        return p.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return None


def _folders(root: Path, rel: str) -> list[str]:
    p = _plain(root, rel)
    try:
        return sorted(e.name for e in p.iterdir() if e.is_dir() and not e.is_symlink()) if p is not None and p.is_dir() else []
    except OSError:
        return []


def _scenario(line: str) -> dict | None:
    """A Kiro acceptance criterion (`WHEN a user presses Send THEN the system SHALL send a link`; `WHEN x, the system SHALL y`) as a scenario; None for a line that has no `WHEN`/`IF` and
    no `SHALL`."""
    m = _WHEN.search(_MARK.sub("", line.strip()))
    if not m or "SHALL" not in m.group(1):
        return None
    rest = m.group(1).strip()
    if re.search(r"\bTHEN\b", rest):
        when, _, then = re.split(r"\s+(THEN)\s+", rest, maxsplit=1)
    else:
        head, sep, tail = rest.partition("SHALL")
        cut = head.rfind(",")
        when, then = (head[:cut], head[cut + 1:] + sep + tail) if cut > 0 else (head, sep + tail)
    when, then = living_specs._words(when.strip(" ,")), living_specs._words(then.strip())
    return {"name": living_specs._words(when, 60), "when": when, "then": then} if when and then else None


def _wanted(story: str) -> str:
    """What a user story wants (`As a player, I want to see the rooms, so that I can join` → `see the rooms`), as a requirement's name."""
    want = re.sub(r"^As an? .*?,?\s*I (?:want|need|would like)( to)?\s*", "", story, flags=re.I).split(", so that")[0]
    return living_specs._words(want, 80)


def parse_kiro(text: str, name: str) -> dict | None:
    """A Kiro `requirements.md` as a spec: each `### Requirement N` (or, with none, each user story) a requirement, its `WHEN … SHALL …` lines its scenarios; None with no requirement. The
    capability is `name` (the folder's) as a slug."""
    cap = living_specs.slug(name)
    reqs: list[dict] = []
    cur: dict | None = None
    intro, section = [], ""
    for line in text.replace("\r\n", "\n").split("\n"):
        if h := re.match(r"^##[ \t]+(.+?)\s*$", line):
            section, cur = h.group(1).lower(), None
        elif r := _REQ_HEAD.match(line):
            cur = {"name": living_specs._words(r.group(2) or (f"Requirement {r.group(1)}" if r.group(1) else "Requirement")), "text": "", "scenarios": [], "bare": not r.group(2)}
            reqs.append(cur)
        elif story := _STORY.match(line):
            if cur is None or cur["text"]:                                        # a user story with no heading above it, or a second one: a requirement of its own
                cur = {"name": _wanted(story.group(1)) or "Requirement", "text": "", "scenarios": []}
                reqs.append(cur)
            cur["text"] = living_specs._words(story.group(1), 600)
            if cur.get("bare"):                                                   # a heading with no title of its own is named by what the story wants
                cur["name"] = _wanted(story.group(1)) or cur["name"]
                cur["bare"] = False
        elif cur is not None and (sc := _scenario(line)):
            cur["scenarios"].append(sc)
        elif cur is None and section in ("introduction", "overview") and line.strip():
            intro.append(line.strip())
    out = []
    for r in reqs[:MAX_REQUIREMENTS]:
        out.append({"name": r["name"], "text": r["text"] or living_specs._words(r["name"]), "scenarios": r["scenarios"][:4]})
    if not out or not cap:
        return None
    title = living_specs._title(re.sub(r"[-_]+", " ", name).strip().capitalize()) or cap
    return {"capability": cap, "title": title, "purpose": living_specs._words(" ".join(intro), 300), "parties": [], "goals": [], "updated": "", "requirements": out}


def _openspec(root: Path, name: str) -> dict | None:
    text = _text(root, f"openspec/specs/{name}/spec.md")
    spec = living_specs.parse(text, living_specs.slug(name)) if text is not None else None
    if spec is not None:
        spec["title"] = re.sub(r"\s+Specification$", "", spec["title"], flags=re.I).strip() or spec["title"]
    return spec if spec is not None and spec["capability"] else None


def target(root: Path, board: Path | None = None) -> Path:
    """Where the specs read in are kept: the Board's pages root; for a project with no Board, the Wiki's default place (never the project's own `specs/`, which Spec Kit keeps its features in)."""
    if board is not None and Path(board) != Path(root):
        return Path(board)
    try:
        from orkboard.realm import wiki
        return wiki.root_of(Path(root), None, "general")
    except Exception:
        return Path(root) / "llm-wiki" / "general"


def take(root: Path, board: Path | None = None, dry: bool = False) -> int:
    """OpenSpec's and Kiro's specs of the project kept as living specs where none of that capability is kept (never over one, nor over a file there that is no spec): how many were kept
    (`dry`: how many would be, nothing written)."""
    root, board = Path(root), target(root, board)
    n = 0
    for source, get in (("openspec/specs", _openspec),
                        (".kiro/specs", lambda r, name: parse_kiro(_text(r, f".kiro/specs/{name}/requirements.md") or "", name))):
        for name in _folders(root, source):
            try:
                spec = get(root, name)
                file = Path(board) / living_specs.DIR / f"{spec['capability']}.md" if spec else None
                if spec is None or file.exists() or file.is_symlink() or living_specs.read(board, spec["capability"]) is not None:
                    continue
                if not dry:
                    living_specs.write(board, {**spec, "updated": spec.get("updated") or dt.date.today().isoformat()})
                n += 1
            except (OSError, ValueError):
                continue
    return n
