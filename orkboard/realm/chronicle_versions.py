"""The versions of the past (docs/specs/134-release-keeps-the-chronicle.md A.1, decisions §238.5): the project's own, read by code. No model, no face.

    chronicle_versions.read(repo)       # {kind: "tag" | "changelog" | "week", versions: [{id, name, day}]}, oldest first
    chronicle_versions.week_of(day)     # the Monday of `day`'s week, "YYYY-MM-DD"

**tag** (first): the tags that read as a version (`v0.3`, `1.2.0`, `2.0-rc1`), dated by `git for-each-ref` (an annotated tag's tagger day, a lightweight tag's commit day). **changelog**
(else): the repository's top file `CHANGELOG*`, `CHANGES*`, `HISTORY*` or `NEWS*`, each `## [1.2.0] - 2026-10-10` heading (a `v` and the brackets optional, the day `YYYY-MM-DD` or `17 October
2026`); a heading with no version (*Unreleased*) or no day is not one. **week** (neither): `versions` is empty, the chapters are the weeks the past has. A git that fails or a folder that is
none has no tags; nothing here raises.
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
from pathlib import Path

from orkboard.realm import doc_formats

GIT_TIMEOUT_S = 10
READ_MAX = 1_000_000
VERSIONS_MAX = 300
CHANGELOGS = ("changelog", "changes", "history", "news")
_SUFFIXES = ("", ".md", ".txt", ".rst")
_VERSION = r"\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.]+)?"
_TAG = re.compile(rf"^[vV]?{_VERSION}$")
_HEAD = re.compile(rf"^##\s+\[?[vV]?({_VERSION})\]?(.*)$")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def _day(text: object) -> str:
    """`text` as a real day `YYYY-MM-DD`, else ""."""
    try:
        return dt.date.fromisoformat(str(text or "").strip()[:10]).isoformat()
    except ValueError:
        return ""


def week_of(day: str) -> str:
    """The Monday of the week `day` is in; "" for a day that is none."""
    got = _day(day)
    if not got:
        return ""
    d = dt.date.fromisoformat(got)
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def _key(name: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", re.split(r"[-+]", name.lstrip("vV"), maxsplit=1)[0]))


def _tags(repo: Path) -> list[tuple[str, str]]:
    try:
        got = subprocess.run(["git", "for-each-ref", "refs/tags", "--format=%(refname:short)%09%(creatordate:short)"], cwd=repo,
                             capture_output=True, text=True, timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for line in got.stdout.splitlines() if got.returncode == 0 else []:
        name, _tab, day = line.partition("\t")
        if _TAG.match(name) and _day(day):
            out.append((name, _day(day)))
    return out


def _changelog(repo: Path) -> list[tuple[str, str]]:
    try:
        files = sorted(p for p in Path(repo).iterdir() if p.is_file() and not p.is_symlink() and p.stem.lower() in CHANGELOGS and p.suffix.lower() in _SUFFIXES)
        if not files:
            return []
        with files[0].open("rb") as f:
            text = f.read(READ_MAX).decode("utf-8", "replace")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        m = _HEAD.match(line)
        if m:
            found = _DAY.search(m.group(2))
            day = _day(found.group(0)) if found else doc_formats.day_of(m.group(2))
            if day:
                out.append((m.group(1), day))
    return out


def read(repo: Path) -> dict:
    """See the module."""
    repo = Path(repo)
    kind, found = "week", []
    for k, got in (("tag", _tags(repo)), ("changelog", _changelog(repo))):
        if got:
            kind, found = k, got
            break
    days: dict[str, str] = {}
    for name, day in found:
        days.setdefault(name, day)
    rows = sorted((d, _key(n), n) for n, d in days.items())[-VERSIONS_MAX:]
    return {"kind": kind, "versions": [{"id": f"v:{n}", "name": n, "day": d} for d, _k, n in rows]}
