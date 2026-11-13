"""The core and the domain have no face: they never import the GUI, and nothing imports a terminal toolkit. Nothing
imports the old package, `orkcraft` (decisions §305).

Every import counts, a lazy one inside a function too."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "orkboard"
FACELESS = ["core", "realm", "design"]
FORBIDDEN = ("textual", "rich")


def _imports(path: Path) -> list[tuple[int, str]]:
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.append((node.lineno, node.module))
    return out


@pytest.mark.parametrize("package", FACELESS)
def test_no_face_in(package):
    bad = []
    for path in sorted((ROOT / package).rglob("*.py")):
        for line, module in _imports(path):
            top = module.split(".")[0]
            if top in FORBIDDEN or module.startswith("orkboard.gui"):
                bad.append(f"{path.relative_to(ROOT.parent)}:{line} imports {module}")
    assert not bad, "\n".join(bad)


def test_loading_the_core_loads_no_face():
    """Transitively too: importing every module of core/, realm/ and design/ pulls in no toolkit."""
    import subprocess
    import sys
    modules = [f"orkboard.{p.relative_to(ROOT).with_suffix('').as_posix().replace('/', '.')}"
               for package in FACELESS for p in sorted((ROOT / package).rglob("*.py"))]
    modules = [m.removesuffix(".__init__") for m in modules]
    code = ("import importlib, sys\n"
            f"for m in {modules!r}: importlib.import_module(m)\n"
            "print(sorted({n.split('.')[0] for n in sys.modules} & {'textual', 'rich'}))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]", out.stdout + out.stderr


def test_the_terminal_ui_stays_gone():
    """No module imports Textual or Rich, and the TUI's packages do not come back."""
    bad = [f"{path.relative_to(ROOT.parent)}:{line} imports {module}"
           for path in sorted(ROOT.rglob("*.py")) for line, module in _imports(path)
           if module.split(".")[0] in FORBIDDEN]
    bad += [f"orkboard/{name} is back" for name in ("tui", "screens", "widgets", "wm", "app.py", "theme.py")
            if (ROOT / name).is_file() or any((ROOT / name).rglob("*.py"))]
    assert not bad, "\n".join(bad)


# A module that knows the agent tools (`realm/harnesses.py`) and starts processes itself registers them in
# `realm/halt.py`, the one list of what runs: the HUD counts agents from it and 🛑 Stop all kills what is on it.
# These start only short commands that are not agents, or keep their own list (tech-debt T13).
STARTS_WITHOUT_HALT = {
    "gui/drive.py": "a browser for a picture of the page (Node's Playwright); it names the agent tools only to hide them",
    "realm/model_families.py": "asks a tool for its model list; no model runs",
    "tools.py": "a tool's version and login state",
}
_STARTS = {("subprocess", "Popen"), ("subprocess", "run"), ("subprocess", "call"), ("subprocess", "check_output"),
           ("pty", "fork"), ("os", "execvpe"), ("os", "execvp")}


def _starts_and_names(path: Path) -> tuple[bool, set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    starts = any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and (n.value.id, n.attr) in _STARTS
                 for n in ast.walk(tree))
    names = {m.split(".")[-1] for _line, m in _imports(path)}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            names |= {a.name for a in n.names}
    return starts, names


def test_whoever_starts_an_agent_registers_it_in_halt():
    bad = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "realm/halt.py":
            continue
        starts, names = _starts_and_names(path)
        if starts and "harnesses" in names and "halt" not in names and rel not in STARTS_WITHOUT_HALT:
            bad.append(f"{rel} starts processes and knows the agent tools, but never uses realm/halt.py")
    assert not bad, "\n".join(bad)
    assert all((ROOT / rel).is_file() for rel in STARTS_WITHOUT_HALT), "a listed module is gone: drop it from the list"


OLD = "orkcraft"                 # the package Orkboard was cut from: nothing here imports it


def modules(root: Path = ROOT) -> dict[str, Path]:
    """Every module of the package by dotted name (a package's `__init__` is the package's name)."""
    out = {}
    for path in sorted(root.rglob("*.py")):
        parts = list(path.relative_to(root.parent).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        out[".".join(parts)] = path
    return out


def test_nothing_imports_the_old_package():
    """The package imports nothing named `orkcraft`, a lazy import inside a function too, so nothing couples back."""
    bad = [f"{path.relative_to(ROOT.parent)}:{line} imports {module}"
           for path in sorted(ROOT.rglob("*.py")) for line, module in _imports(path) if module.split(".")[0] == OLD]
    assert not bad, "\n".join(bad)


def core_dependencies(starts: list[str], mods: dict[str, Path]) -> list[str]:
    """Follow local imports at every depth, including imports inside functions."""
    seen, bad = set(), []
    def visit(name, chain):
        if name == 'orkboard.core' or name.startswith('orkboard.core.'):
            bad.append(' -> '.join([*chain, name]))
            return
        if name in seen or name not in mods:
            return
        seen.add(name)
        path = mods[name]
        package = name if path.name == '__init__.py' else name.rpartition('.')[0]
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            targets = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ''
                if node.level:
                    base = '.'.join(package.split('.')[:len(package.split('.')) - node.level + 1] + ([base] if base else []))
                targets = [base, *(base + '.' + a.name for a in node.names)]
            for target in targets:
                visit(target, [*chain, name])
    for start in starts:
        visit(start, [])
    return bad


def test_seat_rules_never_reach_core():
    mods = modules()
    starts = ['orkboard.realm.seat_frames', 'orkboard.realm.agent_rules_text']
    starts += [m for m in mods if m.startswith('orkboard.realm.seat_') and m.endswith('_rules')]
    assert not (bad := core_dependencies(starts, mods)), '\n'.join(bad)


@pytest.mark.parametrize('statement', ['import orkboard.core.hidden', 'from orkboard.core import hidden', 'from ..core import hidden'])
def test_seat_dependency_check_catches_lazy_and_indirect_imports(tmp_path, statement):
    root = tmp_path / 'orkboard'
    (root / 'realm').mkdir(parents=True)
    consumer = root / 'realm/consumer.py'
    helper = root / 'realm/helper.py'
    consumer.write_text('from . import helper\n')
    helper.write_text('def lazy():\n    ' + statement + '\n')
    bad = core_dependencies(['orkboard.realm.consumer'], modules(root))
    assert bad and all('orkboard.realm.consumer -> orkboard.realm.helper -> orkboard.core' in x for x in bad)


def test_heat_and_reach_are_served_by_a_mixin_of_their_own():
    """Spec 165 F: the reach modules stay under 600 lines; gui/ideas.py only imports the mixin, takes it as a base and adds its commands."""
    for rel in ("realm/map_reach.py", "realm/map_reach_crafts.py", "gui/ideas_reach.py"):
        assert len((ROOT / rel).read_text().splitlines()) < 600, rel
    text = (ROOT / "gui/ideas.py").read_text()
    assert "from orkboard.gui.ideas_reach import ReachMixin, reach_commands" in text and "class Ideas(ReachMixin," in text and "**reach_commands(self)" in text
    assert "map_reach" not in text and text.count("ideas_reach") == 1


def test_the_one_post_imports_none_of_the_windows_state_the_store_or_the_phones_frame():
    """Goal 170 A: table/post.js is drawn by the desktop and the phone alike, so it reaches the Board only through `setPostWorld`."""
    import re
    text = (ROOT / "gui/static/js/table/post.js").read_text(encoding="utf-8")
    mods = re.findall(r'^import .* from "([^"]+)"', text, re.M)
    assert mods and not [m for m in mods if any(x in m for x in ("frame/", "shell/", "pwa/", "data.js", "board/"))], mods


def test_the_phone_has_one_face_the_frame_around_the_page():
    """Spec 94 §5.3: the phone's app is the desktop's page in its frame, so nothing lies under pwa/ but what its page (index.html), its worker
    and its manifest name and the modules frame.js imports; a face is under js/. The old face (old.html, board-app.js, shell-*.js, app.css) stays gone."""
    import json
    import re
    pwa = ROOT / "gui/static/pwa"
    reached = {"index.html", "sw.js", "manifest.webmanifest", *re.findall(r'(?:src|href)="([^"/:#]+)"', (pwa / "index.html").read_text(encoding="utf-8"))}
    reached |= {icon["src"] for icon in json.loads((pwa / "manifest.webmanifest").read_text(encoding="utf-8"))["icons"]}
    todo = [name for name in reached if name.endswith(".js")]
    while todo:
        for name in re.findall(r'(?:from|import)\s*\(?\s*"\./([^"/]+\.js)"', (pwa / todo.pop()).read_text(encoding="utf-8")):
            if name not in reached:
                reached.add(name)
                todo.append(name)
    assert sorted(p.name for p in pwa.iterdir() if p.is_file() and p.name not in reached) == []


def test_decision_refs_is_pure_and_short():
    """Goal "The battle and the gate" C (decisions §303): realm/decision_refs.py reads files only: no git, no model, no write, no gui; under 600 lines."""
    path = ROOT / "realm/decision_refs.py"
    text = path.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 600
    mods = {m for _l, m in _imports(path)}
    assert not {m for m in mods if m.split(".")[0] in {"subprocess", "os", "shutil", "socket", "urllib", "http", "requests"}
                or m.startswith(("orkboard.gui", "orkboard.core", "orkboard.realm.harnesses"))}, mods
    assert not any(w in text for w in ("write_text", "write_bytes", ".unlink(", ".mkdir(", "Popen"))


def test_the_stage_again_is_a_mixin_of_the_runner_which_grows_by_its_line_only():
    """Goal "The battle and the gate" H: core/idea_runner.py (618 lines, a hotspot) grows only by its mixin's import, the mixin named among its bases and nothing else of it there;
    core/idea_fix_stage.py and gui/ideas_battle.py stay under 600 lines, and gui/ideas.py registers the battle's commands by its one line."""
    text = (ROOT / "core/idea_runner.py").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 619
    assert "\nfrom orkboard.core.idea_fix_stage import FixStageMixin\n" in text and "\nclass IdeaRunner(FixStageMixin, GoalDevMixin, " in text
    assert text.count("FixStageMixin") == 2 and text.count("idea_fix_stage") == 1 and "fix_stage(" not in text
    for rel in ("core/idea_fix_stage.py", "gui/ideas_battle.py"):
        assert len((ROOT / rel).read_text(encoding="utf-8").splitlines()) < 600, rel
    ideas_py = (ROOT / "gui/ideas.py").read_text(encoding="utf-8")
    assert ideas_py.count("battle_commands") == 2 and "gate_fix" not in ideas_py           # its import and its one registering line
