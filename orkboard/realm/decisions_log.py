"""📖 The project's decisions file, read by code (no model): its next number, an entry, the last headings (spec 97 §5).

    decisions_log.path(root, chosen="")      the decisions file: the person's chosen path, else docs/decisions.md; never outside root
    decisions_log.found(root)                the logs of decisions the project keeps already (≤ 5), to be offered as the path
    decisions_log.is_folder(root, chosen)    whether the decisions' place is a folder of ADR files (MADR or Nygard; spec 126 D), not one file
    decisions_log.next_number(text)          the last `## N.` heading plus one; 1 when there is none
    decisions_log.entry(text, n)             the section `## n.` up to the next `## ` heading ("" when there is none)
    decisions_log.headings(text, last=10)    the last headings, each "N. Title" (then ` (changed by 205)` where a later entry's `Changes:` names it; spec 127 B.3)
    decisions_log.numbers(text, last=10)     the numbers of those headings
    decisions_log.changes_of(rec)            the numbers a record of a folder says it changes (`ork-changes`, or a `Changes:` line at the top of its Decision)
    decisions_log.context(root, n, chosen)   the text a leader's call is given: the last ten headings and goal n's entry

`next_number`, `entry` and `headings` also take the folder (a `Path`) in place of the file's text: its records' numbers and titles (`doc_formats.records`), a
record's text for an entry. The place is a folder when the person chose one, or when no file was chosen, `docs/decisions.md` is not there and the only log `found`
finds is a folder; **a new project** (nothing chosen, no `docs/decisions.md`, no log `found`) gets the MADR folder `docs/decisions`, made by its first decision (spec 127 B.4).

A heading is read at a line's start (`## 158. Title`); lines between ``` fences are never read, so a `## 12.` in an
entry's code block misleads nothing. A file over 2 MB is read from its end.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import doc_formats
from orkboard.realm.code_map import SKIP

DEFAULT = "docs/decisions.md"
NEW = "docs/decisions"                    # the folder a project with no log at all gets (spec 127 B.4)
ENTRY_MAX = 4000
TITLE_MAX = 160
FOUND_MAX = 5
DEPTH_MAX = 3
READ_MAX = 2 * 1024 * 1024
CUT = "… (cut: read the file for the rest)"
_NAMES = {"decisions.md", "DECISIONS.md"}
_ADR = ("docs/adr", "doc/adr")
_ADR_RECORDS = ("docs/decisions", "docs/architecture/decisions")           # found when they hold NNNN-*.md records
_NUMBERED = re.compile(r"^## (\d+)\.[ \t]*(.*)$")
_CHANGES = re.compile(r"^\s*Changes:\s*(.+?)\s*$", re.I)


def path(root, chosen: str = "") -> Path:
    """The decisions file of the project at `root`: `chosen` when it lies inside the root, else `DEFAULT`; the only log the project keeps when it is a folder of
    ADR files and `DEFAULT` is not there (spec 126 D); the folder `NEW` where the project keeps no log at all (spec 127 B.4)."""
    base = Path(root)
    chosen = str(chosen or "").strip()
    if chosen:
        try:
            real = base.resolve()
            cand = (base / chosen).resolve()
            if cand != real and cand.is_relative_to(real):
                return base / cand.relative_to(real)
        except (OSError, ValueError, RuntimeError):
            pass
    elif not (base / DEFAULT).exists():
        only = found(base)
        if len(only) == 1 and (base / only[0]).is_dir():
            return base / only[0]
        if not only and not (base / NEW).is_file():
            return base / NEW
    return base / DEFAULT


def is_folder(root, chosen: str = "") -> bool:
    """Whether the decisions' place is a folder of ADR files, not one file (spec 126 D)."""
    got = path(root, chosen)
    if got.is_dir() and not got.is_symlink():
        return True
    return got == Path(root) / NEW and not got.exists() and not got.is_symlink() and not str(chosen or "").strip()      # the new project's, not made yet


def found(root) -> list[str]:
    """The decisions logs the project keeps already (paths from the root, ≤ 5, shallowest first): `docs/adr`, `doc/adr`, `docs/decisions` and
    `docs/architecture/decisions` holding ADR records, `decisions.md`."""
    base = Path(root)
    out: list[tuple[int, str]] = []
    for rel in _ADR:
        if (base / rel).is_dir() and not (base / rel).is_symlink():
            out.append((rel.count("/") + 1, rel))
    for rel in _ADR_RECORDS:
        if (base / rel).is_dir() and not (base / rel).is_symlink() and doc_formats.records(base / rel):
            out.append((rel.count("/") + 1, rel))
    level = [base]
    for depth in range(DEPTH_MAX + 1):
        nxt: list[Path] = []
        for d in level:
            try:
                entries = sorted(d.iterdir())
            except OSError:
                continue
            for e in entries:
                if e.is_symlink():
                    continue
                if e.is_dir():
                    if e.name not in SKIP and depth < DEPTH_MAX:
                        nxt.append(e)
                elif e.name in _NAMES:
                    out.append((depth, e.relative_to(base).as_posix()))
        level = nxt
        if not level:
            break
    out.sort()
    return [rel for _, rel in out][:FOUND_MAX]


def _lines(text: str):
    """The lines of `text` outside ``` fences, each with its index."""
    fenced = False
    for i, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield i, line


def next_number(text: "str | Path") -> int:
    """The last heading `## N.` plus one; 1 when there is none. A folder (a `Path`): the highest `NNNN` of its files plus one."""
    if isinstance(text, Path):
        return doc_formats.next_number(text)
    last = 0
    for _, line in _lines(text):
        m = _NUMBERED.match(line)
        if m:
            last = int(m.group(1))
    return last + 1


def _record(folder: Path, n: int) -> str:
    """Record `n` of a folder as the entry a leader reads: its heading and its text, cut at ENTRY_MAX; "" when there is none."""
    rec = next((r for r in doc_formats.records(folder) if r["number"] == n), None)
    if rec is None:
        return ""
    body = f"## {rec['number']}. {rec['title']}\n\n{rec['body']}".strip()
    return body[:ENTRY_MAX] + CUT if len(body) > ENTRY_MAX else body


def entry(text: "str | Path", n: int) -> str:
    """The section `## n.` up to the next `## ` heading, cut at ENTRY_MAX; "" when there is none. A folder (a `Path`): record `n`'s text."""
    if isinstance(text, Path):
        return _record(text, n)
    start = end = None
    for i, line in _lines(text):
        if start is None:
            m = _NUMBERED.match(line)
            if m and int(m.group(1)) == n:
                start = i
        elif line.startswith("## "):
            end = i
            break
    if start is None:
        return ""
    body = "\n".join(text.splitlines()[start:end]).strip()
    return body[:ENTRY_MAX] + CUT if len(body) > ENTRY_MAX else body


def changes_of(rec: dict) -> list[int]:
    """The numbers a record of a folder says it changes: MADR's `ork-changes` front matter, else a `Changes: 110, 183.` line at the top of its Decision (a Nygard record)."""
    got = (rec.get("extra") or {}).get("ork-changes")
    if got:
        return [int(x) for x in re.findall(r"\d+", " ".join(got) if isinstance(got, list) else str(got))]
    for line in str(rec.get("decision") or "").splitlines()[:3]:
        if m := _CHANGES.match(line):
            return [int(x) for x in re.findall(r"\d+", m.group(1))]
    return []


def _changed_by(rows: list[tuple[int, list[int]]]) -> dict[int, list[int]]:
    """`{n: [the later entries whose Changes name n]}`, from `[(number, its changes)]`."""
    out: dict[int, list[int]] = {}
    for number, names in rows:
        for n in names:
            if n < number and number not in out.setdefault(n, []):
                out[n].append(number)
    return out


def _heading(number: int, title: str, by: dict[int, list[int]]) -> str:
    out = f"{number}. {title[:TITLE_MAX].rstrip()}"
    return out + f" (changed by {', '.join(str(x) for x in sorted(by[number]))})" if by.get(number) else out


def headings(text: "str | Path", last: int = 10) -> list[str]:
    """The last `last` numbered headings, each `N. Title` (the title cut at 160 characters), then ` (changed by 205)` for a heading a later entry's `Changes:` names (spec 127 B.3).
    A folder (a `Path`): its records' (`ork-changes`)."""
    if last <= 0:
        return []
    if isinstance(text, Path):
        recs = doc_formats.records(text)
        by = _changed_by([(r["number"], changes_of(r)) for r in recs])
        return [_heading(r["number"], r["title"], by) for r in recs][-last:]
    rows = []
    for _, line in _lines(text):
        m = _NUMBERED.match(line)
        if m:
            rows.append((int(m.group(1)), m.group(2).strip()))
    changes = {r["number"]: r["extra"].get("changes") or [] for r in doc_formats.parse_log(text)} if "Changes:" in text else {}
    by = _changed_by([(n, changes.get(n, [])) for n, _t in rows])
    return [_heading(n, t, by) for n, t in rows][-last:]


def numbers(text: "str | Path", last: int = 10) -> list[int]:
    """The numbers of the last `last` headings: what a decision can say it changes."""
    return [int(h.split(".", 1)[0]) for h in headings(text, last)]


def _read(file: Path) -> tuple[str, bool]:
    """The file's text (its last 2 MB, from a whole line, when larger) and whether it was cut at its start."""
    with file.open("rb") as f:
        size = f.seek(0, 2)
        if size <= READ_MAX:
            f.seek(0)
            return f.read().decode("utf-8", "replace"), False
        f.seek(size - READ_MAX)
        raw = f.read()
    cut = raw.find(b"\n")
    return (raw[cut + 1:] if cut >= 0 else b"").decode("utf-8", "replace"), True


def context(root, n=None, chosen: str = "") -> str:
    """The text a leader's call is given: the last ten headings, and goal `n`'s entry when `n` is given; "" when the file is missing."""
    base = Path(root)
    file = path(base, chosen)
    if is_folder(base, chosen):
        if not file.exists():
            return ""
        last, got = headings(file), entry(file, n) if n is not None else ""
        out = f"The project's decisions ({file.relative_to(base).as_posix()}): "
        out += "the last ten:\n" + "\n".join(last) if last else "none numbered yet."
        return out + ("\n\nThis goal's decision:\n" + got if got else "")
    try:
        if not file.is_file():
            return ""
        text, tail = _read(file)
        got = entry(text, n) if n is not None else ""
        if n is not None and not got and tail:
            got = entry(file.read_text("utf-8", errors="replace"), n)
    except OSError:
        return ""
    last = headings(text)
    out = f"The project's decisions ({file.relative_to(base).as_posix()}): "
    out += "the last ten:\n" + "\n".join(last) if last else "none numbered yet."
    if got:
        out += "\n\nThis goal's decision:\n" + got
    return out
