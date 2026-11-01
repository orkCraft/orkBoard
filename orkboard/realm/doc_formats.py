"""The common formats a project's decisions are kept in, read and written by code (docs/specs/126-read-in-and-write-out.md §A; decisions §204): MADR 4
(`docs/decisions/NNNN-title.md`, YAML front matter), Michael Nygard's ADRs (adr-tools: `doc/adr/NNNN-title.md`, `## Status`), and the Board's own one file
(`docs/decisions.md`, `## N. Title (date, who)`). No model, no face, no dependency: the front matter is read as the flat YAML these files use.

    doc_formats.front_matter(text)            # ({key: str | [str]}, the text after it); ({}, text) when there is none
    doc_formats.parse_record(text, path)      # one ADR file → a record (MADR or Nygard, told by its shape); None for a file that is not one
    doc_formats.parse_log(text, path)         # the Board's one file → [record], one an entry
    doc_formats.folder_format(folder)         # "madr" | "nygard" | "": the format the records in a folder are kept in (the most of them)
    doc_formats.next_number(folder)           # the highest NNNN of the folder's records, plus one
    doc_formats.file_name(n, title)           # "0012-no-accounts-in-the-first-release.md"
    doc_formats.render_madr(rec) / render_nygard(rec)   # a record as a new file's text

**A record** is `{number, title, status, date, deciders, context, decision, consequences, body, path, format, extra}`: `number` an int (0 when the file has
none), `status` lower case (`proposed` · `accepted` · `rejected` · `deprecated` · `superseded` …, "" when unsaid), `date` as written (`YYYY-MM-DD` in
MADR, free in the Board's own file), `deciders` a list, `context` / `decision` / `consequences` the sections' text (each cut to `PART_CHARS`), `body` the
whole text after the title (cut to `BODY_CHARS`), `format` `madr` · `nygard` · `log`, `extra` the front matter's other keys (an `ork-*` key is the Board's).
"""
from __future__ import annotations

import re
from pathlib import Path

PART_CHARS = 2000
BODY_CHARS = 8000
TITLE_CHARS = 160
FILE = re.compile(r"^(\d{1,5})-[^/]*\.md$", re.I)
_HEAD = re.compile(r"^#\s+(?:(\d+)\.\s*)?(.+?)\s*$")
_LOG_HEAD = re.compile(r"^## (\d+)\.[ \t]*(.*?)\s*$")
_LOG_WHEN = re.compile(r"\s*\(([^()]*)\)\s*$")
_SECTION = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
_DATE = re.compile(r"^\s*Date:\s*(.+?)\s*$", re.I | re.M)
STATUSES = ("proposed", "accepted", "rejected", "deprecated", "superseded")
MADR_SECTIONS = {"context": ("context and problem statement", "context"), "decision": ("decision outcome", "decision"),
                 "consequences": ("consequences",)}


def _words(v: object, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _cut(text: str, n: int) -> str:
    text = text.strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def _unquote(v: str) -> str:
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def front_matter(text: str) -> tuple[dict, str]:
    """The flat YAML front matter between two `---` lines at the top: `key: value`, `key: [a, b]` and `key:` followed by `- item` lines; comments and
    anything nested are skipped. `({}, text)` when the text has none."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() in ("---", "..."))
    except StopIteration:
        return {}, text
    out: dict = {}
    key = ""
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s+(.*)$", raw) or re.match(r"^-\s+(.*)$", raw)
        if item and key:
            if not isinstance(out.get(key), list):
                out[key] = []
            out[key].append(_unquote(item.group(1)))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", raw)
        if not m:
            key = ""
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            out[key] = [_unquote(x) for x in value[1:-1].split(",") if x.strip()]
        elif value and not value.startswith("#"):
            out[key] = _unquote(value.split(" #")[0])
        else:
            out[key] = []
    return out, "\n".join(lines[end + 1:])


def _sections(text: str) -> list[tuple[str, str]]:
    """`[(heading lower case, text)]` of the `##` / `###` sections, outside ``` fences."""
    out: list[tuple[str, list[str]]] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        m = None if fenced else _SECTION.match(line)
        if m:
            out.append((m.group(2).strip().lower(), []))
        elif out:
            out[-1][1].append(line)
    return [(h, "\n".join(body).strip()) for h, body in out]


def _find(sections: list[tuple[str, str]], names: tuple[str, ...]) -> str:
    return next((body for h, body in sections if h in names), "")


def _status(v: object) -> str:
    """A status as a word: its first word lower case (`Superseded by ADR-0005` → `superseded`), "" when unsaid."""
    text = _words(v[0] if isinstance(v, list) and v else v, 200).lower()
    return text.split(" ")[0].strip(".,:;") if text else ""


def _as_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [_words(x, 120) for x in v if _words(x, 120)]
    return [_words(x, 120) for x in str(v or "").split(",") if _words(x, 120)]


def _number(path: str) -> int:
    m = FILE.match(Path(path).name)
    return int(m.group(1)) if m else 0


def parse_record(text: str, path: str = "") -> dict | None:
    """One ADR file → a record: MADR when it has front matter or a *Decision Outcome* section, Nygard when it has a `## Status` section; None when it has
    no `# Title` (not a record: a README, an index, a template)."""
    meta, rest = front_matter(text)
    lines = rest.splitlines()
    head = next(((i, _HEAD.match(line)) for i, line in enumerate(lines) if _HEAD.match(line)), None)
    if head is None:
        return None
    i, m = head
    title = _words(m.group(2), TITLE_CHARS)
    body = "\n".join(lines[i + 1:]).strip()
    secs = _sections(body)
    names = {h for h, _ in secs}
    nygard = "status" in names and not meta
    if nygard:
        status = _status(_find(secs, ("status",)).splitlines()[0] if _find(secs, ("status",)) else "")
        date = (_DATE.search("\n".join(lines[:i + 6])) or _DATE.search(body))
        rec = {"status": status, "date": date.group(1) if date else "", "deciders": [], "format": "nygard",
               "context": _find(secs, ("context",)), "decision": _find(secs, ("decision",)), "consequences": _find(secs, ("consequences",))}
    else:
        if not meta and "decision outcome" not in names and "decision" not in names:
            return None
        status = _status(meta.get("status")) or _status(next((line.split(":", 1)[1] for line in body.splitlines()
                                                                 if line.lower().startswith(("* status:", "- status:", "status:"))), ""))
        rec = {"status": status, "date": _words(meta.get("date"), 40), "deciders": _as_list(meta.get("decision-makers") or meta.get("deciders")),
               "format": "madr", "context": _find(secs, MADR_SECTIONS["context"]), "decision": _find(secs, MADR_SECTIONS["decision"]),
               "consequences": _find(secs, MADR_SECTIONS["consequences"])}
    rec.update(number=int(m.group(1)) if m.group(1) else _number(path), title=title, body=_cut(body, BODY_CHARS), path=path,
               extra={k: v for k, v in meta.items() if k not in ("status", "date", "decision-makers", "deciders")})
    for k in ("context", "decision", "consequences"):
        rec[k] = _cut(rec[k], PART_CHARS)
    return rec


def parse_log(text: str, path: str = "") -> list[dict]:
    """The Board's own decisions file (`## N. Title (when, who)`) → a record an entry, in the file's order; the date is the heading's parenthesis as written."""
    out: list[dict] = []
    fenced = False
    cur: dict | None = None
    body: list[str] = []

    def close():
        if cur is not None:
            text_ = "\n".join(body).strip()
            cur.update(body=_cut(text_, BODY_CHARS), decision=_cut(text_, PART_CHARS))
            out.append(cur)

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        m = None if fenced else _LOG_HEAD.match(line)
        if m:
            close()
            title, when = m.group(2), ""
            w = _LOG_WHEN.search(title)
            if w:
                when, title = w.group(1).strip(), title[:w.start()].strip()
            cur = {"number": int(m.group(1)), "title": _words(title, TITLE_CHARS), "status": "accepted", "date": _words(when, 80), "deciders": [],
                   "context": "", "decision": "", "consequences": "", "body": "", "path": path, "format": "log", "extra": {}}
            body = []
        elif cur is not None and not (not fenced and line.startswith("# ")):
            body.append(line)
    close()
    return out


def records(folder: Path) -> list[dict]:
    """The records of a folder of ADR files (`NNNN-*.md`, not links), by number."""
    out = []
    try:
        files = sorted(p for p in Path(folder).iterdir() if p.is_file() and not p.is_symlink() and FILE.match(p.name))
    except OSError:
        return []
    for f in files:
        try:
            rec = parse_record(f.read_text(encoding="utf-8", errors="replace"), f.name)
        except OSError:
            continue
        if rec is not None:
            out.append(rec)
    return sorted(out, key=lambda r: r["number"])


def folder_format(folder: Path) -> str:
    """The format most of a folder's records are kept in: "madr" or "nygard"; "" for a folder with none."""
    got = [r["format"] for r in records(folder)]
    if not got:
        return ""
    return "nygard" if got.count("nygard") > got.count("madr") else "madr"


def next_number(folder: Path) -> int:
    """The highest NNNN of the folder's `NNNN-*.md` files, plus one (1 for none)."""
    try:
        nums = [_number(p.name) for p in Path(folder).iterdir() if FILE.match(p.name)]
    except OSError:
        nums = []
    return max(nums, default=0) + 1


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", _words(title, TITLE_CHARS).lower()).strip("-")
    return s[:60].rstrip("-") or "decision"


def file_name(n: int, title: str) -> str:
    return f"{n:04d}-{slug(title)}.md"


def _yaml(v: object) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_yaml(x) for x in v) + "]"
    s = str(v)
    return f'"{s}"' if re.search(r"[:#\[\]{},\"']|^\s|\s$|^$", s) else s


def render_madr(rec: dict) -> str:
    """A record as a MADR 4 file: front matter (`status`, `date`, `decision-makers`, then `extra`), `# Title`, *Context and Problem Statement*, *Decision
    Outcome* (with *Consequences* under it). A part with no words is left out."""
    meta = {"status": rec.get("status") or "accepted", "date": rec.get("date") or ""}
    if rec.get("deciders"):
        meta["decision-makers"] = list(rec["deciders"])
    meta.update({k: v for k, v in (rec.get("extra") or {}).items() if k not in meta})
    head = "---\n" + "".join(f"{k}: {_yaml(v)}\n" for k, v in meta.items() if v not in ("", [])) + "---\n\n"
    out = [f"# {_words(rec.get('title'), TITLE_CHARS)}"]
    if (rec.get("context") or "").strip():
        out += ["", "## Context and Problem Statement", "", rec["context"].strip()]
    out += ["", "## Decision Outcome", "", (rec.get("decision") or rec.get("body") or "").strip()]
    if (rec.get("consequences") or "").strip():
        out += ["", "### Consequences", "", rec["consequences"].strip()]
    return head + "\n".join(out).rstrip() + "\n"


def render_nygard(rec: dict) -> str:
    """A record as an adr-tools file: `# N. Title`, `Date:`, *Status*, *Context*, *Decision*, *Consequences* (a part with no words says so)."""
    out = [f"# {int(rec.get('number') or 0)}. {_words(rec.get('title'), TITLE_CHARS)}", "", f"Date: {rec.get('date') or ''}", "",
           "## Status", "", (rec.get("status") or "accepted").capitalize(), "", "## Context", "", (rec.get("context") or "").strip() or "(not said)",
           "", "## Decision", "", (rec.get("decision") or rec.get("body") or "").strip(), "", "## Consequences", "", (rec.get("consequences") or "").strip() or "(not said)"]
    return "\n".join(out).rstrip() + "\n"
