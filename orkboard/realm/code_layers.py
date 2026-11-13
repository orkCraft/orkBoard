"""Tech's Architecture table, read from a project's own code (goal 171, stage C; `ideas.tables`): `orkboard/`'s packages, each module's line count, the
imports between the packages, the realm modules that reach up into core, the rule `tests/test_architecture.py` keeps (core, realm and design never
import gui) and the `~600 lines` rule of CLAUDE.md. Pure: it reads files and writes none; the recording of `ideas.tables` (gui/ideas_mats.py) is its host answer."""
from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from pathlib import Path

PACKAGES = ("gui", "core", "realm", "design")
LIMIT = 600                                                     # CLAUDE.md: split a module before it grows past ~600 lines
BIGGEST = 4                                                     # a pile spread shows its biggest modules


def top_of(path: Path, pkg: Path) -> str:
    parts = path.relative_to(pkg).parts
    return parts[0] if len(parts) > 1 else "top"


NOTES = {                                                       # what a big module is, in a few words where its docstring says it in none
    "gui/board_host.py": "the host", "gui/ideas.py": "the Board's commands", "gui/drive.py": "the command line's drive",
    "gui/ideas_board.py": "the Board as the page asks it", "core/op_runner.py": "an operation's run", "core/idea_runner.py": "a plan's run",
    "core/idea_plan.py": "a goal's plan", "core/idea_keeper.py": "the Board's keeper", "realm/ideas.py": "the goals and parties as files",
    "realm/hypotheses.py": "Product's hypotheses", "realm/loop.py": "a game's core loop", "realm/board_map.py": "the Board's map",
    "design/ui.py": "a UI document", "design/mark.py": "the mark", "design/tokens.py": "the tokens",
}


def what(path: Path, pkg: Path) -> str:
    """A note for a module, else the first sentence of its docstring, short; its own name's words when it has none."""
    if path.relative_to(pkg).as_posix() in NOTES:
        return NOTES[path.relative_to(pkg).as_posix()]
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    first = re.split(r"(?<=[.:;])\s|\n\n", doc.strip(), maxsplit=1)[0].replace("\n", " ").strip().rstrip(".:;")
    first = re.sub(r"^\*\*|\*\*$", "", first)
    first = re.sub(r"\s*\(.*?\)", "", first) or first
    if not first:
        return path.stem.replace("_", " ")
    return first if len(first) <= 46 else first[:43].rsplit(" ", 1)[0] + "…"


def imports(path: Path):
    """(module name, is lazy) of every `orkboard…` import in a file, a lazy one (inside a function) too."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lazy = {id(n) for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(f)}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 and node.module.startswith("orkboard"):
            yield node.module, id(node) in lazy
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("orkboard"):
                    yield a.name, id(node) in lazy


def walk(pkg: Path):
    files = sorted(pkg.rglob("*.py"))
    lines = {p: len(p.read_text(encoding="utf-8").splitlines()) for p in files}
    needs = defaultdict(Counter)                                # package -> package -> imports
    reach = defaultdict(list)                                   # (from, to) -> [(module, lazy, to-module)]
    for p in files:
        src = top_of(p, pkg)
        for mod, lazy in imports(p):
            seg = mod.split(".")
            dst = seg[1] if len(seg) > 1 and (pkg / seg[1]).is_dir() else "top"
            if dst != src:
                needs[src][dst] += 1
                reach[(src, dst)].append((p.relative_to(pkg).as_posix(), lazy, mod))
    return files, lines, needs, reach


def module_card(p: Path, pkg: Path, lines: dict, needs_of: dict):
    rel = p.relative_to(pkg).as_posix()
    return {"id": rel, "title": p.name, "line": what(p, pkg), "lines": lines[p], "past": lines[p] > LIMIT, "needs": needs_of.get(rel, {})}


def architecture(root: Path) -> dict | None:
    """Tech's Architecture table of the code under `root` (`<root>/orkboard/`); None when the project has no such package. Reads files only."""
    pkg = root / "orkboard"
    if not pkg.is_dir():
        return None
    files, lines, needs, reach = walk(pkg)
    sizes = {k: (sum(1 for p in files if top_of(p, pkg) == k), sum(v for p, v in lines.items() if top_of(p, pkg) == k)) for k in PACKAGES}
    per_module = defaultdict(Counter)
    for (src, dst), rows in reach.items():
        for mod, _, _ in rows:
            per_module[mod][dst] += 1
    big = lambda pk: [module_card(p, pkg, lines, per_module) for p in sorted((p for p in files if top_of(p, pkg) == pk), key=lambda p: -lines[p])[:BIGGEST]]
    pile = lambda pk, line: {"id": f"{pk}/", "title": f"{pk}/", "line": line, "kind": "pile", "modules": sizes[pk][0], "lines": sizes[pk][1],
                             "needs": {k: v for k, v in sorted(needs[pk].items(), key=lambda kv: -kv[1]) if k in PACKAGES}, "biggest": big(pk)}
    # realm modules that reach up into core: the layering the page draws runs gui > core > realm, and realm reaches up
    stray = []
    by_module = defaultdict(list)
    for mod, lazy, to in reach.get(("realm", "core"), []):
        by_module[mod].append((to, lazy))
    for mod, rows in sorted(by_module.items(), key=lambda kv: -len(kv[1])):
        p = pkg / mod
        stray.append({"id": mod, "title": p.name, "line": "reaches up into core" + (", lazily" if all(z for _, z in rows) else ""), "lines": lines[p], "past": lines[p] > LIMIT,
                      "needs": {"core": len(rows)}, "lazy": all(z for _, z in rows), "imports": sorted({t for t, _ in rows})})
    past = sorted(((p, n) for p, n in lines.items() if n > LIMIT), key=lambda kv: -kv[1])
    vs = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in sorted((root / "vscode" / "src").rglob("*.ts"))) if (root / "vscode" / "src").is_dir() else 0
    arch = {
        "title": "Architecture", "line": "Its architecture · this repository's modules", "party": "tech", "limit": LIMIT,
        "layers": [
            {"id": "outside", "name": "Outside", "line": "imports Orkboard", "cards": [
                {"id": "orkline", "title": "Orkline", "line": "imports Orkboard's modules, never the other way round", "kind": "ext", "needs": {}}]},
            {"id": "faces", "name": "Faces", "line": "the page is the one face", "cards": [
                pile("gui", "the page, its server"),
                {"id": "vscode/", "title": "vscode/", "line": "a frame: it starts the page", "kind": "frame", "lines": vs, "needs": {"gui": 1}}]},
            {"id": "engine", "name": "Engine", "line": "no face", "cards": [pile("core", "the bus, a tool's run, the gate"), pile("design", "orkUI's copy, the UI rules")]},
            {"id": "words", "name": "Words", "line": "the Board's own", "cards": [pile("realm", "the lexicon, a goal's way")], "stray": stray},
        ],
        "rules": [
            {"view": "for", "text": "Nothing under core/, realm/ or design/ imports gui/", "where": "tests/test_architecture.py · test_no_face_in"},
            {"view": "for", "text": "Orkline imports Orkboard, never back; Orkboard starts with none of Orkline's", "where": "tests/test_architecture.py · test_orkboard_starts_alone"},
            {"view": "for", "text": "Nothing imports Textual or Rich", "where": "tests/test_architecture.py · test_the_terminal_ui_stays_gone"},
            {"view": "risk", "text": f"realm/ reaches up into core/ ({len(by_module)} modules" + (", lazily" if stray and all(s["lazy"] for s in stray) else "") + ")",
             "where": ", ".join(s["id"] for s in stray) or "none", "card": stray[0]["id"] if stray else ""},
            {"view": "risk", "text": f"{len(past)} modules are past the ~{LIMIT} lines a module may grow to", "where": ", ".join(f"{p.relative_to(pkg).as_posix()} {n}" for p, n in past[:3]) + ("…" if len(past) > 3 else ""),
             "card": past[0][0].relative_to(pkg).as_posix() if past else ""},
        ],
        "tech_tokens": [{"card": s["id"], "view": "risk"} for s in stray[:1]],
    }
    return arch
