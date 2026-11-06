"""Write out (docs/specs/126-read-in-and-write-out.md §C; decisions §204): the Board's out in common formats, for any tool or person that reads Markdown: the project's
decisions as MADR (or Nygard's) files, Cline's memory bank, and each journal as a Markdown file `read_in` reads back. No model, no network, no face.

    write_out.write(root, state_dir, to=None, fmt="madr")   # {"decisions": n, "journals": n, "memory_bank": n, "specs": n, "path": to, "skipped": [...]}
    write_out.run_cli(root, to, fmt)                        # `orkboard export`: (0, "Wrote 14 decisions, 6 memory bank files and 5 journals to <to>")

`to` is `<root>/.orkcraft/export` unless given. Only files inside it are written (`decisions/`, `memory-bank/`, `journals/`, and the living specs as `openspec/specs/<capability>/spec.md`: spec 127 C.4,
`realm/living_specs_io.py`; each made when missing), each whole, and each says
that Orkboard wrote it (a front matter key or the first line): **a file there that Orkboard did not write is never touched** (it is named in `skipped`), and one it wrote
that no longer belongs (a decision gone, a title changed) is removed. Never into the project's own decisions folder (`docs/decisions`, `docs/adr` …): that is refused.

**A journal file** (`journals/<scope>.md`; the project's is `project.md`, a party named "project" `party-project.md`):

    ---
    orkboard-journal: tech            # the scope: a party's slug, `_project` for the project's
    party: Tech
    leader: Archie
    digest: "the leader's own summary"      # its quotes become ', its backslashes /; left out with none
    exported: 2026-11-01T12:00:00
    ---

    # Tech's journal

    - 2026-11-01 · overruled · You said no to “Add a lobby” … <!-- id=1a2b3c4d5e6f idea=add-lobby on=a,b ref=12 -->

One line an entry, the comment after one space; `ref` is last and may hold spaces; a struck entry is left out; only the day is written, so a read back has the day.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from orkboard.realm import decisions_log, doc_formats, journals, living_specs_io, write_out_bank

DIR = ".orkcraft"
EXPORT = "export"
FORMATS = ("madr", "nygard")
MARK = write_out_bank.MARK
PROTECTED = ("docs/decisions", "docs/adr", "doc/adr", "docs/architecture/decisions", "adr", "decisions")      # the project's own ADR folders: never written into
_OURS = ("ork-source:", "orkboard-journal:", "Written by Orkboard")
_NESTED = re.compile(r"^#{2,3}(?=[ \t])", re.M)


def _read_json(file: Path) -> dict:
    try:
        got = json.loads(file.read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def board_root(root: Path, state_dir: Path) -> Path:
    """Where the Board's pages are: the Board's own tree on the work branch when it stands, else the project's folder (`llm-wiki/<topic>/pages/…`); the project's folder
    when there are none (no parties then)."""
    for base in (Path(state_dir) / "board", Path(root)):
        found = [p.parent.parent for pat in ("llm-wiki/*/pages/tracks", "*/pages/tracks", "pages/tracks") for p in base.glob(pat) if p.is_dir()]
        if found:
            return max(found, key=lambda p: (p / "pages" / "tracks").stat().st_mtime)
    return Path(root)


# -- the files ---------------------------------------------------------------------------------------------------------------------------

def _ours(file: Path) -> bool:
    try:
        with file.open("r", encoding="utf-8", errors="replace") as f:
            head = f.read(1200)
    except OSError:
        return False
    return any(m in head for m in _OURS)


def ours(text: str) -> bool:
    """Whether a file's first part says Orkboard wrote it."""
    return any(m in text[:1200] for m in _OURS)


def _put(file: Path, text: str, out: dict) -> bool:
    """One file written whole (a file Orkboard did not write is left as it is, and named in `skipped`); whether it was written."""
    if file.exists() and not _ours(file):
        out["skipped"].append(str(file))
        return False
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_name(f".{file.name}.tmp")
    tmp.write_text(text, "utf-8")
    tmp.replace(file)
    return True


def _tidy(folder: Path, keep: set[str], pattern: str) -> None:
    """The files Orkboard wrote earlier that no longer belong (`pattern`, not in `keep`) removed; a file it did not write stays."""
    for f in sorted(folder.glob(pattern)) if folder.is_dir() else []:
        if f.name not in keep and f.is_file() and not f.is_symlink() and _ours(f):
            f.unlink()


def _guard(root: Path, state_dir: Path, to: Path) -> None:
    """ValueError when a folder written here is, or lies in, or holds one of the project's own decisions folders."""
    chosen = str(_read_json(state_dir / "project.json").get("decisions") or "")
    folders = [Path(root) / rel for rel in PROTECTED] + [decisions_log.path(root, chosen)] + [Path(root) / rel for rel in decisions_log.found(root)]
    for sub in (to / "decisions", to / "memory-bank", to / "journals"):
        mine = sub.resolve()
        for f in folders:
            there = f.resolve()
            if mine == there or mine.is_relative_to(there) or there.is_relative_to(mine):
                raise ValueError(f"{to} is in the project's own decisions folder ({f.name}): name another folder")


# -- the decisions -----------------------------------------------------------------------------------------------------------------------

def kept_decisions(root: Path, state_dir: Path) -> list[dict]:
    """Every decision the project keeps, as records (`doc_formats`) with `source` the file they are in from the root: the Board's one file or the project's ADR folder."""
    chosen = str(_read_json(state_dir / "project.json").get("decisions") or "")
    file = decisions_log.path(root, chosen)
    rel = file.relative_to(Path(root)).as_posix()
    tree = Path(state_dir) / "board"
    base = tree if (tree / ".git").exists() and (tree / rel).exists() else Path(root)
    if (base / rel).is_dir():
        return [{**r, "source": f"{rel}/{r['path']}"} for r in doc_formats.records(base / rel)]
    try:
        text = (base / rel).read_text("utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for r in doc_formats.parse_log(text, rel):
        when, _, who = r["date"].partition(", ")
        r["date"] = r.get("day") or when.strip()                         # the ISO day when the entry names its year (spec 127 A)
        r["deciders"] = ["the leaders"] if who.startswith("the leaders") else ["the person"] if who.startswith("the person") else [who.strip()] if who.strip() else []
        r["decision"] = _NESTED.sub("####", r["body"])                       # a heading of the entry never splits the record's sections
        out.append({**r, "source": rel})
    return out


def _decision_file(rec: dict, fmt: str) -> tuple[str, str]:
    rec = {**rec, "extra": {**(rec.get("extra") or {}), "ork-source": rec["source"]}}
    if fmt == "nygard":
        text = f"<!-- {MARK} ork-source: {rec['source']} -->\n" + doc_formats.render_nygard(rec)
    else:
        text = doc_formats.render_madr(rec)
    return doc_formats.file_name(rec["number"], rec["title"]), text


def _readme(rows: list[tuple[str, dict]], fmt: str) -> str:
    lines = [f"- {r['number']:04d} · [{r['title']}]({name})" for name, r in rows]
    return (f"<!-- {MARK} -->\n# Decisions\n\nThe decisions of this project, written by Orkboard as {'Nygard-style' if fmt == 'nygard' else 'MADR'} files, one a decision.\n\n"
            + ("\n".join(lines) if lines else "Nothing yet.") + "\n")


def _decisions(root: Path, state_dir: Path, to: Path, fmt: str, out: dict) -> int:
    folder = to / "decisions"
    rows, names = [], set()
    for rec in kept_decisions(root, state_dir):
        name, text = _decision_file(rec, fmt)
        if name in names:                                                    # two records of one number and title: the first stays
            continue
        names.add(name)
        if _put(folder / name, text, out):
            rows.append((name, rec))
    _put(folder / "README.md", _readme(rows, fmt), out)
    _tidy(folder, names, "[0-9]*-*.md")
    return len(rows)


# -- the memory bank ---------------------------------------------------------------------------------------------------------------------

def _bank(root: Path, state_dir: Path, to: Path, out: dict) -> int:
    pages = write_out_bank.pages(root, state_dir, board_root(root, state_dir))
    return sum(1 for name, text in pages.items() if _put(to / "memory-bank" / name, text, out))


# -- the journals ------------------------------------------------------------------------------------------------------------------------

def _scopes(state_dir: Path, parties: list[dict]) -> list[tuple[str, str, str]]:
    """`[(scope, party title, leader's name)]`: the project's, each party's, and each journal kept for a party that is gone."""
    out = [(journals.PROJECT, "The project", "the Orkmaster")]
    seen = set()
    for t in parties:
        seen.add(t["slug"])
        out.append((t["slug"], t["title"], write_out_bank.leader_name(state_dir, t["leader"] or "taskmaster")))
    try:
        stems = sorted(f.stem for f in (Path(state_dir) / journals.DIR).glob("*.jsonl"))
    except OSError:
        stems = []
    for s in stems:
        try:
            journals.kind_of(s)
        except ValueError:
            continue
        if s != journals.PROJECT and s not in seen:
            out.append((s, s, ""))
    return out


def _quoted(text: str) -> str:
    return '"' + " ".join(text.replace('"', "'").replace("\\", "/").split()) + '"'


def _comment(e: dict) -> str:
    on = ",".join(p.replace(",", " ").strip() for p in e["on"])
    return f"<!-- id={e['id']} idea={e['idea']} on={on} ref={str(e['ref']).replace('-->', '').strip()} -->"


def journal_file(state_dir: Path, scope: str, title: str, leader: str, now: str) -> str:
    """A journal as its Markdown file (the module's docstring has the shape)."""
    head = ["---", f"orkboard-journal: {scope}", f"party: {title}"]
    if leader:
        head.append(f"leader: {leader}")
    d = journals.digest(state_dir, scope)
    if d:
        head.append(f"digest: {_quoted(d['text'])}")
    head += [f"exported: {now}", "---", "", f"# {title}'s journal", ""]
    rows = [f"- {e['at'][:10]} · {e['kind']} · {e['text']} {_comment(e)}" for e in journals.read(state_dir, scope)]
    return "\n".join(head + rows) + "\n"


def _journals(state_dir: Path, parties: list[dict], to: Path, out: dict) -> int:
    folder, names, n = to / "journals", set(), 0
    now = dt.datetime.now().isoformat(timespec="seconds")
    for scope, title, leader in _scopes(state_dir, parties):
        if scope != journals.PROJECT and not journals.read(state_dir, scope) and not journals.digest(state_dir, scope):
            continue                                                         # a party with nothing in its journal has no file
        name = journals.file_name(scope)
        names.add(name)
        n += _put(folder / name, journal_file(state_dir, scope, title, leader, now), out)
    _tidy(folder, names, "*.md")
    return n


def journals_into(state_dir: Path, parties: list[dict], folder: Path) -> int:
    """Every journal's Markdown written into `folder` for the Board's tree (`<wiki>/journals/`: spec 151 B.1), the files that changed counted. A party with nothing in its journal has no file;
    the `.jsonl` stays the truth. `parties`: `write_out_bank.parties(wiki)`."""
    n = 0
    for scope, title, leader in _scopes(state_dir, parties):
        if scope != journals.PROJECT and not journals.read(state_dir, scope) and not journals.digest(state_dir, scope):
            continue
        n += journals.mirror_into(state_dir, scope, folder, title, leader)
    return n


def brief_into(root: Path, state_dir: Path, board: Path, folder: Path) -> bool:
    """`projectbrief.md`'s text written as `<folder>/project.md` when it differs (spec 151 B.3: read by a tool, never back by Orkboard), and not at all while every part of the brief is empty (spec 155 G.3); whether it was written."""
    f = Path(folder) / "project.md"
    if not f.is_file() and write_out_bank.brief_is_empty(state_dir, board):     # nothing to say: no file (spec 155 G.3)
        return False
    text = write_out_bank.pages(root, state_dir, board)["projectbrief.md"]
    try:
        if f.is_file():
            old = f.read_text("utf-8")
            if old == text or not ours(old):
                return False
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(".project.md.tmp")
        tmp.write_text(text, "utf-8")
        tmp.replace(f)
    except OSError:
        return False
    return True


# -- the whole ---------------------------------------------------------------------------------------------------------------------------

def write(root, state_dir, to=None, fmt: str = "madr") -> dict:
    """The decisions, the memory bank, the journals and the living specs of the project at `root` written into `to` (`<root>/.orkcraft/export`): `{decisions, journals, memory_bank, specs, path, skipped}`.
    ValueError for a format that is none, a `to` that is a file or lies in the project's own decisions folder; OSError where the disk refuses."""
    root, state_dir = Path(root), Path(state_dir)
    if fmt not in FORMATS:
        raise ValueError(f"No format {fmt!r}: {' or '.join(FORMATS)}")
    to = Path(to) if to else root / DIR / EXPORT
    if to.exists() and not to.is_dir():
        raise ValueError(f"{to} is a file, not a folder")
    _guard(root, state_dir, to)
    out = {"skipped": []}
    got = {"decisions": _decisions(root, state_dir, to, fmt, out), "journals": 0, "memory_bank": _bank(root, state_dir, to, out)}
    board = board_root(root, state_dir)
    got["journals"] = _journals(state_dir, write_out_bank.parties(board), to, out)
    got["specs"] = living_specs_io.export(board, to, out["skipped"])                 # the living specs as OpenSpec's (spec 127 C.4)
    return {**got, "path": to, "skipped": out["skipped"]}


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def run_cli(root, to, fmt: str = "madr") -> tuple[int, str]:
    """`orkboard export`: (0, the line to print); ValueError (a format or a folder that is none) is the caller's to say."""
    root = Path(root)
    got = write(root, root / DIR, to, fmt or "madr")
    parts = [_count(got["decisions"], "decision", "decisions"), _count(got["memory_bank"], "memory bank file", "memory bank files"), _count(got["journals"], "journal", "journals")]
    if got["specs"]:                                                         # the living specs (spec 127 C.4) are said when there are any
        parts.append(_count(got["specs"], "spec", "specs"))
    text = f"Wrote {', '.join(parts[:-1])} and {parts[-1]} to {got['path']}"
    if got["skipped"]:
        text += f"\nLeft as they were (Orkboard did not write them): {', '.join(got['skipped'][:5])}"
    return 0, text
