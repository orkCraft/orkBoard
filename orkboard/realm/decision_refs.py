"""📖 What names a decision, read from files (goal "The battle and the gate", stage C; decisions §303.2, §303.3). Pure: it reads the files it is given, writes nothing, runs no git and no model.

    decision_refs.rests_on(root, n)                what rests on §n: {"goals": [slug], "decisions": [n], "tests": [path]}, each counted once, §n itself never
    decision_refs.guards(root, failing, limit=3)   the §N each failing test guards: [{"id", "file", "decisions": [N], "from": "function"|"module"|"file"}]
    decision_refs.named_by(root, files)            the §N the given test files name (the gate's other, agreeing pile), the log's numbers only

A test names decision N where it writes `decisions §N` (and any §M listed right after: `decisions §2, §3`); `§N.k` names N. A `spec <n> §k` and a
`<file>.md §k` are a spec's points, never a decision. A number the log lacks is left out. A failing test's own function text is read first, else its
file's module docstring; a test naming none lies as its file. A goal's page and another decision name §N by a bare `§N` too.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from orkboard.realm import decisions_log

PAGES = "llm-wiki/general/pages/ideas"
TESTS = "tests"
READ_MAX = 2 * 1024 * 1024
_HEAD = re.compile(r"^## (\d+)\.")
_NUM = r"§(\d+)(?:\.\d+)?"
_GROUP = re.compile(r"(?P<lead>(?:spec\s+\d+(?:\s+part\s+\w+)?|\S+\.md|decisions?)?)[ \t]*(?P<body>" + _NUM
                    + r"(?:[ \t]*(?:,|;|and|–|-|/)[ \t]*" + _NUM + r")*)", re.I)
_ONE = re.compile(_NUM)
_CHANGES = re.compile(r"^\s*Changes:[ \t]*(.*?)(?:\n[ \t]*\n|\Z)", re.I | re.M | re.S)
_ITEM_N = re.compile(r"\s*§?(\d+)(?:\.\d+)?\b")


def _read(path: Path) -> str:
    try:
        with path.open("rb") as f:
            return f.read(READ_MAX).decode("utf-8", "replace")
    except OSError:
        return ""


def _named(text: str, bare: bool) -> set[int]:
    """The decisions `text` names: after `decision(s)`, or (when `bare`) after nothing; never after `spec <n>` or `<file>.md`."""
    out: set[int] = set()
    for m in _GROUP.finditer(text):
        lead = m.group("lead").lower()
        if lead.startswith("decision") or (bare and not lead):
            out |= {int(x) for x in _ONE.findall(m.group("body"))}
    return out


def _sections(text: str) -> dict[int, str]:
    out: dict[int, list[str]] = {}
    cur, fenced = 0, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        m = None if fenced else _HEAD.match(line)
        if m:
            cur = int(m.group(1))
            out.setdefault(cur, [])
        if cur:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def _log(root) -> dict[int, str]:
    p = decisions_log.path(root)
    return _sections(_read(p)) if p.is_file() else {}


def _files(root, rel: str, pattern: str) -> list[Path]:
    base = Path(root) / rel
    try:
        return sorted(p for p in base.rglob(pattern) if p.is_file() and not p.is_symlink())
    except OSError:
        return []


def _changed(text: str) -> set[int]:
    """The decisions a *Changes:* paragraph (up to its blank line) replaces: each comma- or semicolon-separated item's N (`N` or `N.k`); an item that starts `spec` is a spec's, never a decision."""
    out: set[int] = set()
    for para in _CHANGES.findall(text):
        for item in re.split(r"[,;]", para):
            m = _ITEM_N.match(item)
            if m:
                out.add(int(m.group(1)))
    return out


def rests_on(root, n: int) -> dict:
    """The goals whose pages name §n, the other decisions whose text names it and the test files naming `decisions §n`, each once, §n itself never."""
    root = Path(root)
    log = _log(root)
    if n not in log:
        return {"goals": [], "decisions": [], "tests": []}
    goals = sorted({p.stem for p in _files(root, PAGES, "*.md") if n in _named(_read(p), True)})
    decisions = sorted(k for k, text in log.items() if k != n and (
        n in _named(text, True) or n in _changed(text)))
    tests = sorted(p.relative_to(root).as_posix() for p in _files(root, TESTS, "*.py") if n in _named(_read(p), False))
    return {"goals": goals, "decisions": decisions, "tests": tests}


def _function_text(source: str, tid: str) -> str:
    """The text of the test a pytest id names (`file::Class::name[param]`): "" when it is not found."""
    parts = [re.sub(r"\[.*$", "", s) for s in tid.split("::")[1:]]
    if not parts:
        return ""
    try:
        node: ast.AST = ast.parse(source)
    except SyntaxError:
        return ""
    for name in parts:
        found = next((c for c in getattr(node, "body", []) if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and c.name == name), None)
        if found is None:
            return ""
        node = found
    return ast.get_source_segment(source, node) or ""


def _module_doc(source: str) -> str:
    try:
        return ast.get_docstring(ast.parse(source), clean=False) or ""
    except SyntaxError:
        return ""


def guards(root, failing, limit: int = 3) -> list[dict]:
    """For each failing test id: the §N it guards (the log's numbers, at most `limit`), read from its function's text first, else its file's module
    docstring; `from` says which, `file` when it names none (it lies as its file)."""
    root = Path(root)
    known = set(_log(root))
    out = []
    for tid in failing or []:
        file = str(tid).split("::")[0]
        p = (root / file).resolve()
        source = _read(p) if p.is_file() and p.is_relative_to(root.resolve()) else ""
        found = sorted(_named(_function_text(source, str(tid)), False) & known)
        kind = "function"
        if not found:
            found, kind = sorted(_named(_module_doc(source), False) & known), "module"
        if not found:
            kind = "file"
        out.append({"id": str(tid), "file": file, "decisions": found[:limit], "from": kind})
    return out


def named_by(root, files) -> list[int]:
    """The §N the given test files name, whole text, in the log only."""
    root = Path(root)
    known = set(_log(root))
    found: set[int] = set()
    for f in files or []:
        p = (root / str(f)).resolve()
        if p.is_file() and p.is_relative_to(root.resolve()):
            found |= _named(_read(p), False)
    return sorted(found & known)
