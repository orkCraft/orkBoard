"""Read in (docs/specs/126-read-in-and-write-out.md §B; decisions §204): a project's own decisions, specs and notes, found by their shapes and read into the journals,
once. No model, no network, no face.

    read_in.scan(root)                         # {found, decisions, specs, context, releases, journals}: what the project keeps, read from its files
    read_in.take(root, state_dir, scan=None)   # {decisions, leaders, done, releases, journals, specs_read}: the journals gain what is not in them yet (by `ref`), any number of times
    read_in.first_start(root, state_dir)       # `take`, once for a project (a marker beside the journals): the first start's call
    read_in.start_context(root)                # the context files the brief's first reading is given (`project_facts.start_files`)
    read_in.run_cli(root, dry=False)           # `orkboard import`: (exit code, the lines to print)

The shapes (spec 126 §B.1): ADR folders (MADR, Nygard), the Board's own decisions file, GitHub Spec Kit, Kiro, OpenSpec, BMAD, Cline's memory bank, AGENTS.md and
CLAUDE.md, Keep a Changelog, and an Orkboard export (`journals/*.md`, spec 126 §C). A link, a secret and a file over 1 MB are never read. Every entry kept carries
a `ref` (its source's path, `#<number>` for one entry of the Board's file, `#<version>` for a release; an export's entry its own id), and an entry whose ref a
journal holds already (a struck one too) is skipped, so nothing is read in twice.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import decisions_log, doc_formats, goal_team, ideas, journals, living_specs_io
from orkboard.realm.code_map import SKIP

MAX_BYTES = 1_000_000                # a file over this is never read
CONTEXT_CHARS = 2000                 # the first part of a context file kept
LINE_CHARS = journals.TEXT_CHARS
MARKER = "read_in.json"              # in the state folder: the first start has read in
STATE = ".orkcraft"
EXPORT_DIR = ".orkcraft/export"
ADR_DIRS = ("docs/decisions", "docs/adr", "doc/adr", "docs/architecture/decisions", "adr", "decisions")
CRAFT_WORDS = {"design": "design", "ui": "design", "ux": "design", "art": "art", "release": "release", "deploy": "release", "marketing": "marketing",
               "growth": "marketing", "product": "product", "pricing": "product", "game": "game-design", "loop": "game-design", "level": "game-design"}
KIRO, SPECKIT, OPENSPEC, BMAD, CLINE, AGENTS = "Kiro", "GitHub Spec Kit", "OpenSpec", "BMAD", "Cline's memory bank", "agents' files"
CONTEXT = ((SPECKIT, (".specify/memory/constitution.md",)),
           (KIRO, (".kiro/steering/product.md", ".kiro/steering/tech.md", ".kiro/steering/structure.md")),
           (OPENSPEC, ("openspec/project.md",)),
           (BMAD, ("docs/prd.md", "docs/architecture.md")),
           (CLINE, tuple(f"memory-bank/{n}.md" for n in ("projectbrief", "productContext", "systemPatterns", "techContext", "activeContext", "progress"))),
           (AGENTS, ("AGENTS.md", "CLAUDE.md")))
START_PATHS = {".specify/memory/constitution.md", ".kiro/steering/product.md", "memory-bank/projectbrief.md", "memory-bank/productContext.md",
               "openspec/project.md", "docs/prd.md", "AGENTS.md"}     # what speaks of the product (CLAUDE.md speaks to agents)
LOOKED_FOR = "ADR folders (MADR or Nygard), the Board's decisions file, GitHub Spec Kit, Kiro, OpenSpec, BMAD, Cline's memory bank, AGENTS.md or CLAUDE.md, a CHANGELOG.md or an Orkboard export"
NOUNS = {"decisions": ("decision", "decisions"), "specs": ("spec", "specs"), "context": ("file", "files"), "releases": ("release", "releases"),
         "journals": ("journal entry", "journal entries")}
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_TITLE = re.compile(r"^# +(.+?)\s*#*\s*$", re.M)
_BOX = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\[([ xX\-])\]", re.M)
_RELEASE = re.compile(r"^##\s+\[?v?(\d[^\]\s]*)\]?(?:\([^)]*\))?\s+[-–—]\s+(\d{4}-\d{2}-\d{2})\b")
_ENTRY = re.compile(r"^- (\d{4}-\d{2}-\d{2}) · ([a-z_]+) · (.+?)\s*$")
_META = re.compile(r"^<!--\s*(.*?)\s*-->\s*$")
_INLINE = re.compile(r"\s*<!--\s*(id=.*?)\s*-->\s*$")
_KEY = re.compile(r"(?:^|\s)(id|idea|on|ref)=")


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


# -- reading files: never a link, never a secret, never a large file -----------------------------------------------------------------------

def _plain(root: Path, rel: str) -> Path | None:
    """`root/rel` when no part of it below the root is a link."""
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


def _names(root: Path, rel: str, dirs: bool) -> list[str]:
    """The names in the folder `rel` that are folders (`dirs`) or files, none a link, sorted."""
    p = _plain(root, rel) if rel else Path(root)
    try:
        if p is None or not p.is_dir():
            return []
        return sorted(e.name for e in p.iterdir() if not e.is_symlink() and (e.is_dir() if dirs else e.is_file()))
    except OSError:
        return []


def _day(root: Path, rel: str) -> str:
    """The day of the file's last commit, quietly "" where there is none."""
    try:
        got = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=str(root), capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    out = got.stdout.strip() if got.returncode == 0 else ""
    return out if _DAY.fullmatch(out) else ""


# -- decisions -----------------------------------------------------------------------------------------------------------------------------

def craft_of_record(rec: dict, default: str = "tech") -> str:
    """The craft a decision belongs to: the one its front matter's `tags`, else its title, name (`CRAFT_WORDS`); else `default`."""
    tags = (rec.get("extra") or {}).get("tags")
    for text in (" ".join(tags) if isinstance(tags, list) else str(tags or ""), rec.get("title") or ""):
        for w in re.findall(r"[a-z]+", text.lower()):
            got = CRAFT_WORDS.get(w) or (CRAFT_WORDS.get(w[:-1]) if w.endswith("s") else None)
            if got:
                return got
    return default


def _adr(root: Path, rel: str) -> list[dict]:
    out = []
    for name in _names(root, rel, dirs=False):
        if not doc_formats.FILE.match(name):
            continue
        text = _text(root, f"{rel}/{name}")
        rec = doc_formats.parse_record(text, f"{rel}/{name}") if text is not None else None
        if rec is not None:
            out.append({**rec, "craft": craft_of_record(rec)})
    return sorted(out, key=lambda r: r["number"])


def _board_files(root: Path, state_dir: Path) -> dict[str, list[dict]]:
    """`{path: entries}` of the Board's own decisions files, only for a project whose journal holds no decision yet (one whose decisions were kept before the journals)."""
    if any(e["kind"] == "decision" for e in journals.read(state_dir, journals.PROJECT, struck=True)):
        return {}
    out = {}
    for rel in decisions_log.found(root):
        text = _text(root, rel) if rel.lower().endswith(".md") else None
        recs = [{**r, "path": rel, "craft": craft_of_record(r, "")} for r in doc_formats.parse_log(text, rel)] if text is not None else []
        if recs:
            out[rel] = recs
    return out


# -- specs ---------------------------------------------------------------------------------------------------------------------------------

def _tasks_done(root: Path, folder: str) -> bool:
    boxes = _BOX.findall(_text(root, f"{folder}/tasks.md") or "")
    return bool(boxes) and all(b in "xX" for b in boxes)


def _status_done(text: str) -> bool:
    """A BMAD story's `Status: Done` (on the line, or the line after a `## Status` heading)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*(?:#{1,6}\s*)?\**status\**\s*:?\**\s*(.*)$", line, re.I)
        if m:
            rest = m.group(1).strip() or next((x.strip() for x in lines[i + 1:] if x.strip()), "")
            return rest.strip("*_ ").lower().startswith("done")
    return False


def _spec(root: Path, framework: str, name: str, rel: str, done: bool | None, text: str) -> dict:
    m = _TITLE.search(text)
    return {"framework": framework, "name": name, "title": _words(m.group(1), 120) if m else name, "done": bool(done), "path": rel, "date": _day(root, rel)}


def _specs(root: Path) -> list[tuple[str, str, dict]]:
    """`[(framework, folder, spec)]`: every spec of every framework the project keeps."""
    out = []
    for fw, base, file, tasks, always in ((SPECKIT, "specs", "spec.md", True, None), (SPECKIT, ".specify/specs", "spec.md", True, None),
                                          (KIRO, ".kiro/specs", "requirements.md", True, None), (OPENSPEC, "openspec/specs", "spec.md", False, True),
                                          (OPENSPEC, "openspec/changes/archive", "proposal.md", False, True)):
        for name in _names(root, base, dirs=True):
            rel = f"{base}/{name}/{file}"
            text = _text(root, rel)
            if text is not None:
                out.append((fw, base, _spec(root, fw, name, rel, _tasks_done(root, f"{base}/{name}") if tasks else always, text)))
    for name in _names(root, "openspec/changes", dirs=True):
        rel = f"openspec/changes/{name}/proposal.md"
        text = _text(root, rel) if name != "archive" else None
        if text is not None:
            out.append((OPENSPEC, "openspec/changes", _spec(root, OPENSPEC, name, rel, False, text)))
    for name in _names(root, "docs/stories", dirs=False):
        text = _text(root, f"docs/stories/{name}") if name.endswith(".story.md") else None
        if text is not None:
            out.append((BMAD, "docs/stories", _spec(root, BMAD, name[:-len(".story.md")], f"docs/stories/{name}", _status_done(text), text)))
    return out


# -- context, releases, exports ------------------------------------------------------------------------------------------------------------

def _context(root: Path) -> list[dict]:
    out = []
    for fw, paths in CONTEXT:
        for rel in paths:
            text = _text(root, rel)
            if text is not None and text.strip():
                out.append({"framework": fw, "path": rel, "text": text.strip()[:CONTEXT_CHARS]})
    return out


def start_context(root: Path) -> list[dict]:
    """The context files that speak of the product (not CLAUDE.md, not the code's own notes), in the table's order, for the brief's first reading."""
    return [c for c in _context(Path(root)) if c["path"] in START_PATHS]


def _releases(root: Path) -> list[dict]:
    text = _text(root, "CHANGELOG.md")
    out: list[dict] = []
    for line in (text or "").splitlines():
        m = _RELEASE.match(line)
        if m:
            out.append({"version": m.group(1), "date": m.group(2), "bullet": "", "path": "CHANGELOG.md"})
        elif line.startswith("## "):
            out.append(None)                     # another section ends the one before
        elif out and out[-1] is not None and not out[-1]["bullet"] and re.match(r"^\s*[-*+]\s+\S", line):
            out[-1]["bullet"] = re.sub(r"^\s*[-*+]\s+", "", line).strip()
    return [r for r in out if r]


def _meta(inner: str) -> dict:
    marks = list(_KEY.finditer(inner))
    return {m.group(1): inner[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(inner))].strip() for i, m in enumerate(marks)}


def parse_export(text: str, path: str = "") -> dict | None:
    """One journal file of an Orkboard export (spec 126 §C) → `{scope, path, entries: [{at, kind, text, idea, on, id, ref}], digest, digest_at, digest_read}` (the leader's view, spec 167 E); None for a file that is none."""
    meta, rest = doc_formats.front_matter(text)
    scope = meta.get("orkboard-journal")
    if not isinstance(scope, str) or not scope.strip():
        return None
    lines = rest.splitlines()
    entries = []
    for i, line in enumerate(lines):
        m = _ENTRY.match(line)
        if not m:
            continue
        said, inline = m.group(3), _INLINE.search(m.group(3))                 # the writer's comment on the entry's own line (spec 126 C), or on the next
        if inline:
            said, got = said[:inline.start()].rstrip(), _meta(inline.group(1))
        else:
            got = _meta(c.group(1)) if (c := _META.match(lines[i + 1].strip() if i + 1 < len(lines) else "")) else {}
        key = got.get("id") or hashlib.sha1(f"{scope}|{m.group(1)}|{m.group(2)}|{said}".encode()).hexdigest()[:12]
        entries.append({"at": m.group(1), "kind": m.group(2), "text": said, "idea": got.get("idea", ""), "id": got.get("id", ""),
                        "on": [p.strip() for p in got.get("on", "").split(",") if p.strip()], "ref": key})
    read = meta.get("digest_read", "")
    read = read if isinstance(read, list) else [x.strip() for x in str(read).split(",")]
    return {"scope": scope.strip(), "path": path, "entries": entries, "digest": str(meta.get("digest") or ""),
            "digest_at": str(meta.get("digest_at") or ""), "digest_read": [x for x in read if x]}


def _journal_dirs(root: Path) -> list[str]:
    """Folders called `journals` under `docs/` (four levels down at most) and `.orkcraft/export/`."""
    out = [f"{EXPORT_DIR}/journals"]
    level = ["docs"]
    for _depth in range(5):
        nxt = []
        for rel in level:
            for name in _names(root, rel, dirs=True):
                if name in SKIP:
                    continue
                (out if name == "journals" else nxt).append(f"{rel}/{name}")
        level = nxt
    return out


def _exports(root: Path) -> list[dict]:
    out = []
    for rel in _journal_dirs(root):
        for name in _names(root, rel, dirs=False):
            got = parse_export(_text(root, f"{rel}/{name}") or "", f"{rel}/{name}") if name.endswith(".md") else None
            if got is not None:
                out.append(got)
    return out


def _tree_exports(folder: Path) -> list[dict]:
    return [got for name in _names(folder, "journals", dirs=False) if name.endswith(".md")
            for got in [parse_export(_text(folder, f"journals/{name}") or "", f"journals/{name}")] if got is not None]


def outside(folder: Path, state_dir: Path) -> tuple[list[dict], list[dict]]:
    """The journals of the Board's tree (`<wiki>/journals/*.md`, spec 151 B.2) read, nothing written: `(rows, left)`. `rows` are the lines no journal holds yet (an `id` Orkboard does not know,
    or no `id` at all: the plan's rows, once by `ref`); `left` the lines whose `kind` is not one of their scope's (or whose scope is none), `[{scope, path, at, kind, text}]`, for `orkboard check`."""
    folder = Path(folder)
    exports = _tree_exports(folder)
    left = []
    for exp in exports:
        scope = journals.PROJECT if exp["scope"] in ("_project", "project") else exp["scope"]
        try:
            kinds = journals.KINDS[journals.kind_of(scope)]
        except ValueError:
            kinds = ()
        left += [{"scope": scope, "path": exp["path"], "at": e["at"], "kind": e["kind"], "text": e["text"]} for e in exp["entries"] if e["kind"] not in kinds]
    return plan(folder, Path(state_dir), {"journals": exports}, board=folder), left


def take_outside(folder: Path, state_dir: Path) -> dict:
    """The lines added outside taken into the journals, each once (its `ref` is kept): `{journals: n, left: [...]}` (`outside`'s `left`), and `views: n` when a newer view of a leader's was kept."""
    rows, left = outside(folder, state_dir)
    n = 0
    for r in rows:
        try:
            n += journals.add(state_dir, r["scope"], r["kind"], r["text"], idea=r["idea"], on=r["on"], ref=r["ref"], at=r["at"]) is not None
        except ValueError:
            continue
    views = 0
    for exp in _tree_exports(Path(folder)):                 # a leader's view, newest kept (spec 167 E); a file with a view and no entry is read too
        if exp["digest"] and exp["scope"] not in ("_project", "project"):
            try:
                views += journals.take_view(state_dir, exp["scope"], exp["digest"], exp["digest_at"], exp["digest_read"])
            except ValueError:
                continue
    return {"journals": n, "left": left, **({"views": views} if views else {})}


# -- scan ----------------------------------------------------------------------------------------------------------------------------------

def _where(paths: list[str]) -> str:
    return paths[0] if len(paths) == 1 else str(Path(paths[0]).parent.as_posix())


def scan(root: Path, state_dir: Path | None = None) -> dict:
    """What the project keeps, by shape (spec 126 §B.1): `{found: [{framework, kind, path, n}], decisions, specs, context, releases, journals}`. The Board's own decisions file
    counts only while the project's journal (`state_dir`, default `<root>/.orkcraft`) holds no decision."""
    root = Path(root)
    state_dir = Path(state_dir) if state_dir else root / STATE
    found: list[dict] = []
    decisions: list[dict] = []
    for rel in ADR_DIRS:
        recs = _adr(root, rel)
        if recs:
            fmt = "Nygard" if sum(r["format"] == "nygard" for r in recs) > len(recs) / 2 else "MADR"
            decisions += recs
            found.append({"framework": f"ADRs ({fmt})", "kind": "decisions", "path": rel, "n": len(recs)})
    for rel, recs in _board_files(root, state_dir).items():
        decisions += recs
        found.append({"framework": "The Board's decisions file", "kind": "decisions", "path": rel, "n": len(recs)})
    specs = _specs(root)
    for fw, base in dict.fromkeys((fw, base) for fw, base, _s in specs):
        found.append({"framework": fw, "kind": "specs", "path": base, "n": sum(1 for f, b, _s in specs if (f, b) == (fw, base))})
    context = _context(root)
    for fw in dict.fromkeys(c["framework"] for c in context):
        paths = [c["path"] for c in context if c["framework"] == fw]
        found.append({"framework": fw, "kind": "context", "path": _where(paths), "n": len(paths)})
    releases = _releases(root)
    if releases:
        found.append({"framework": "Keep a Changelog", "kind": "releases", "path": "CHANGELOG.md", "n": len(releases)})
    exports = _exports(root)
    for folder in dict.fromkeys(str(Path(e["path"]).parent.as_posix()) for e in exports):
        found.append({"framework": "An Orkboard export", "kind": "journals", "path": folder,
                      "n": sum(len(e["entries"]) for e in exports if str(Path(e["path"]).parent.as_posix()) == folder)})
    return {"found": found, "decisions": decisions, "specs": [s for _f, _b, s in specs], "context": context, "releases": releases, "journals": exports}


# -- take ----------------------------------------------------------------------------------------------------------------------------------

def _board_root(root: Path) -> Path:
    """Where the Board's pages (its parties) are for a project folder: the Wiki's default place, else the folder itself."""
    try:
        from orkboard.realm import wiki
        cand = wiki.root_of(root, None, "general")
    except Exception:
        return root
    return cand if (cand / ideas.TRACKS).is_dir() else root


def _parties(board: Path) -> dict[str, str]:
    """`{craft: the slug of the project's first party of it}`."""
    out: dict[str, str] = {}
    try:
        for t in ideas.tracks(board, make=False):
            craft = goal_team.craft_of(board, t["slug"]) if t["slug"] != ideas.GENERAL else ""
            if craft:
                out.setdefault(craft, t["slug"])
    except Exception:
        pass
    return out


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        line = re.sub(r"^[\s#>*+\-]+", "", line).replace("**", "").strip()
        if line and not line.startswith("```"):
            return line
    return ""


def decision_line(rec: dict) -> str:
    """`Decision 12: Title (superseded): the first line of its decision`, `LINE_CHARS` at most."""
    n = int(rec.get("number") or 0)
    head = f"Decision {n}: {rec.get('title') or ''}" if n else f"Decision: {rec.get('title') or ''}"
    if rec.get("status") and rec["status"] != "accepted":
        head += f" ({rec['status']})"
    first = _first_line(rec.get("decision") or "")
    return _cut(" ".join((head + (f": {first}" if first else "")).split()), LINE_CHARS)


def _day_of(text: object) -> str:
    m = _DAY.search(str(text or ""))
    return m.group(0) if m else ""


def plan(root: Path, state_dir: Path, scan_: dict | None = None, board: Path | None = None) -> list[dict]:
    """The entries `take` would add, none whose ref a journal holds already: `[{bucket, scope, kind, text, at, idea, on, ref}]`."""
    root, state_dir = Path(root), Path(state_dir)
    got = scan_ if scan_ is not None else scan(root, state_dir)
    parties = _parties(Path(board) if board else _board_root(root))
    known: dict[str, set[str]] = {}
    ids: dict[str, set[str]] = {}
    out: list[dict] = []

    def want(bucket: str, scope: str, kind: str, text: str, ref: str, at: str = "", idea: str = "", on: object = (), uid: str = "") -> None:
        if scope not in known:
            known[scope] = journals.refs(state_dir, scope)
            ids[scope] = {e["id"] for e in journals.read(state_dir, scope, struck=True)}
        if not text or ref in known[scope] or (uid and uid in ids[scope]):
            return
        known[scope].add(ref)
        out.append({"bucket": bucket, "scope": scope, "kind": kind, "text": text, "at": at, "idea": idea, "on": list(on), "ref": ref})

    boards = {e["ref"] for e in journals.read(state_dir, journals.PROJECT, struck=True) if e["kind"] == "decision" and e["ref"].isdigit()}
    for rec in got.get("decisions", []):
        if rec.get("format") != "log" and ("ork-goal" in (rec.get("extra") or {}) or str(rec.get("number") or "") in boards):
            continue                     # a record the Board wrote into the project's ADR folder (spec 126 D): its journal has it under its number already
        ref = f"{rec['path']}#{rec['number']}" if rec.get("format") == "log" else rec["path"]
        line, at = decision_line(rec), rec.get("day") or _day_of(rec.get("date"))
        want("decisions", journals.PROJECT, "decision", line, ref, at)
        leader = parties.get(rec.get("craft") or "")
        if leader:
            want("leaders", leader, "decision", line, ref, at)
    for spec in got.get("specs", []):
        if spec.get("done"):
            want("done", journals.PROJECT, "done", f"Spec “{_cut(spec['title'], 120)}” ({spec['framework']}) was done", spec["path"], spec.get("date") or "")
    for rel in got.get("releases", []):
        text = f"Version {rel['version']} was released" + (f": {rel['bullet']}" if rel.get("bullet") else "")
        want("releases", journals.PROJECT, "done", _cut(text, LINE_CHARS), f"{rel['path']}#{rel['version']}", rel.get("date") or "")
    for exp in got.get("journals", []):
        scope = journals.PROJECT if exp["scope"] in ("_project", "project") else exp["scope"]
        try:
            kinds = journals.KINDS[journals.kind_of(scope)]
        except ValueError:
            continue
        for e in exp["entries"]:
            if e["kind"] in kinds:
                want("journals", scope, e["kind"], e["text"], e["ref"], e["at"], e["idea"], e["on"], e["id"])
    return out


def _counts(rows: list[dict]) -> dict:
    n = {"decisions": 0, "leaders": 0, "done": 0, "releases": 0, "journals": 0}
    for r in rows:
        n[r["bucket"]] += 1
    return n


def take(root: Path, state_dir: Path, scan: dict | None = None, board: Path | None = None) -> dict:
    """The journals gain what the project's documents say (spec 126 §B.2): a decision into the project's journal and its craft's leader's, a spec done, a release, an export's
    entry as it was. `board`: where the Board's pages are, when not the folder's own. `{decisions, leaders, done, releases, journals, specs_read}`: the entries added, and the OpenSpec and Kiro
    specs kept as living specs where none of that capability was kept (spec 127 C.4: `realm/living_specs_io.py`)."""
    kept = []
    for r in plan(root, state_dir, scan, board):
        try:
            if journals.add(state_dir, r["scope"], r["kind"], r["text"], idea=r["idea"], on=r["on"], ref=r["ref"], at=r["at"]) is not None:
                kept.append(r)
        except ValueError:
            continue
    try:
        specs_read = living_specs_io.take(Path(root), Path(board) if board else _board_root(Path(root)))
    except Exception:                    # a spec that cannot be read in never stops the journals
        specs_read = 0
    return {**_counts(kept), "specs_read": specs_read}


def first_start(root: Path, state_dir: Path, board: Path | None = None) -> dict | None:
    """`take`, once for a project: a marker in the state folder says it has been done (the counts, or None when it was). Never again by itself."""
    marker = Path(state_dir) / MARKER
    if marker.exists():
        return None
    got = take(root, state_dir, board=board)
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"at": dt.datetime.now().isoformat(timespec="seconds"), **got}), encoding="utf-8")
    except OSError:
        pass
    return got


# -- the terminal --------------------------------------------------------------------------------------------------------------------------

def _plural(n: int, kind: str) -> str:
    one, many = NOUNS[kind]
    return f"{n} {one if n == 1 else many}"


def run_cli(root: Path, dry: bool = False) -> tuple[int, str]:
    """`orkboard import [folder] [--dry-run]`: the shapes found, one line each, then what was read in (or, with `dry`, what would be: nothing written)."""
    root = Path(root)
    state_dir = root / STATE
    got = scan(root, state_dir)
    if not got["found"]:
        return 0, f"Nothing to read in: looked in {root} for {LOOKED_FOR}."
    rows = plan(root, state_dir, got)
    n = {**_counts(rows), "specs_read": living_specs_io.take(root, _board_root(root), dry=True)} if dry else take(root, state_dir, got)
    lines = [f"{f['framework']} · {f['path']} · {_plural(f['n'], f['kind'])}" for f in got["found"]]
    parts = [_plural(n["decisions"], "decisions") + (f" ({n['leaders']} also into leaders' journals)" if n["leaders"] else ""),
             f"{_plural(n['done'], 'specs')} done", _plural(n["releases"], "releases")]
    if n["journals"]:
        parts.append(_plural(n["journals"], "journals"))
    if n["specs_read"]:
        parts.append(f"{n['specs_read']} living {'spec' if n['specs_read'] == 1 else 'specs'}")
    return 0, "\n".join(lines + [("Would read in: " if dry else "Read in: ") + ", ".join(parts)])
