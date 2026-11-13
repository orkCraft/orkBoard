"""📖 What names a decision, read from files (goal "The battle and the gate", stage C; decisions §303.2, §303.3). Pure: it reads the files it is given, writes nothing, runs no git and no model.

    decision_refs.rests_on(root, n)                what rests on §n: {"goals": [slug], "decisions": [n], "tests": [path]}, each counted once, §n itself never
    decision_refs.guards(root, failing, limit=3)   the §N each failing test guards: [{"id", "file", "decisions": [N], "from": "function"|"module"|"file"}]
    decision_refs.named_by(root, files)            the §N the given test files name (the gate's other, agreeing pile), the log's numbers only
    decision_refs.of_run(root, failing, files)     both of a gate's run, read in the tree it ran in while that tree is there, with their titles: what its record keeps

A test names decision N where it writes `decisions §N` (and any §M listed right after: `decisions §2, §3`, a line break between them too); `§N.k` names N.
A `spec <n> §k` (and every §m listed right after it) and a `<file>.md §k` are a spec's points, never a decision. A number the log lacks is left out. A
failing test's own function text is read first, else its file's module docstring; a test naming none lies as its file. A goal's page and another decision
name §N by a bare `§N` too. A *Changes:* item names each N it joins with *and* (`176.3 and 167`); an item that starts with `§` is a spec's point.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from orkboard.realm import decisions_log, doc_formats

PAGES = "llm-wiki/general/pages/ideas"
TESTS = "tests"
READ_MAX = 2 * 1024 * 1024
_HEAD = re.compile(r"^## (\d+)\.")
_NUM = r"§(\d+)(?:\.\d+)*"                                     # §N, §N.k, §N.k.j: names N
_GROUP = re.compile(r"(?P<lead>(?:spec\s+\d+(?:\s+part\s+\w+)?|\S+\.md|decisions?)?)\s*(?P<body>" + _NUM
                    + r"(?:\s*(?:,|;|and|–|-|/)\s*" + _NUM + r")*)", re.I)
_ONE = re.compile(_NUM)
_CHANGES = re.compile(r"^\s*Changes:[ \t]*(.*?)(?:\n[ \t]*\n|\Z)", re.I | re.M | re.S)
_ITEM_NUM = r"\d+(?:\.\w+)*(?:[–-]\d+(?:\.\w+)*)?(?!\w)"        # N, N.k, N.k.j, N.12a, N.k–m: its N is the number before the first dot
_ITEM = re.compile(r"\s*(?P<first>" + _ITEM_NUM + r")(?P<more>(?:\s+and\s+" + _ITEM_NUM + r")*)")
_AND_N = re.compile(r"and\s+(\d+)")


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
    """The decisions a *Changes:* paragraph (up to its blank line) replaces: each comma- or semicolon-separated item's N (`N` or `N.k`) and every N it joins
    to it with *and* (`176.3 and 167`, a line break around the *and* too). An item that starts `spec` or `§` (`spec 99 §6.1, §7.2`: the §7.2 is spec 99's) is a
    spec's, never a decision; an *and* followed by anything but a number ends the item's numbers (`199.4 and spec 99 §3`)."""
    out: set[int] = set()
    for para in _CHANGES.findall(text):
        for item in re.split(r"[,;]", para):
            m = _ITEM.match(item)
            if m:
                out.add(int(re.match(r"\d+", m.group("first")).group()))
                out |= {int(x) for x in _AND_N.findall(m.group("more"))}
    return out


def _spec_items(text: str) -> str:
    """`text` with each `§k` list that starts an item of a *Changes:* paragraph (`Changes: §4.1`, `…, 12; §7.2`) blanked: a spec's point, never a decision,
    which `_named` would read bare. A `§k` inside an item's words (`The frame is unchanged (§104.0, §145)`) is left: a decision named in passing."""
    out = list(text)
    for para in _CHANGES.finditer(text):
        for m in _GROUP.finditer(text, para.start(1), para.end(1)):
            before = text[para.start():m.start()].rstrip().lower()
            if not m.group("lead") and before.endswith(("changes:", ",", ";")):
                out[m.start():m.end()] = " " * (m.end() - m.start())
    return "".join(out)


def rests_on(root, n: int) -> dict:
    """The goals whose pages name §n, the other decisions whose text names it and the test files naming `decisions §n`, each once, §n itself never."""
    root = Path(root)
    log = _log(root)
    if n not in log:
        return {"goals": [], "decisions": [], "tests": []}
    goals = sorted({p.stem for p in _files(root, PAGES, "*.md") if n in _named(_read(p), True)})
    decisions = sorted(k for k, text in log.items() if k != n and (
        n in _named(_spec_items(text), True) or n in _changed(text)))
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


def of_run(root, failing, files, limit: int = 3) -> dict:
    """What a gate's run names, read in the tree it ran in (`root`) while that tree is there (the way to dev and the way to main each remove theirs after),
    for its record to keep beside `failing` and `files`: `{"failing": guards(…), "files": named_by(…), "titles": {"N": title}}`, the titles those §N have in
    that tree's log (a decision the goal itself wrote is there and nowhere else yet)."""
    got = {"failing": guards(root, failing, limit), "files": named_by(root, files)}
    numbers = {n for g in got["failing"] for n in g["decisions"]} | set(got["files"])
    log = decisions_log.path(Path(root))
    heads = {r["number"]: r["title"] for r in doc_formats.parse_log(_read(log))} if numbers and log.is_file() else {}
    return {**got, "titles": {str(n): heads.get(n, "") for n in sorted(numbers)}}
