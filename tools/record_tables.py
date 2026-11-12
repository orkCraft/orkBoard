#!/usr/bin/env python3
"""Record the leaders' tables for the page on mocks (goal 170, stage T): `orkboard/gui/static/mock/tables.json`.

    uv run python tools/record_tables.py

**Architecture** (Tech's table) is read from this repository's real code: `orkboard/`'s packages, each module's line count,
the imports between the packages, the realm modules that reach up into core, the rule `tests/test_architecture.py` keeps
(core, realm and design never import gui) and the `~600 lines` rule of CLAUDE.md. **Jobs to be done** (Product's table) is
proposed: this repository has no personas, so what it holds are examples (the page marks each " · example", js/mock/parts/tables.js).
The contract is `ideas.tables`, proposed: the host does not answer it yet; the mock lays this file as that reply."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orkboard.realm import code_layers

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "orkboard"
OUT = PKG / "gui" / "static" / "mock" / "tables.json"


def main() -> None:
    arch_tests = (ROOT / "tests" / "test_architecture.py").read_text(encoding="utf-8")
    for name in ("test_no_face_in", "test_every_import_of_the_package_is_one_of_its_modules", "test_orkboard_starts_alone", "test_the_terminal_ui_stays_gone"):
        if f"def {name}" not in arch_tests:
            sys.exit(f"tests/test_architecture.py no longer holds {name}: the rules code_layers names it")
    arch = code_layers.architecture(ROOT)
    jtbd = {
        "title": "Jobs to be done", "line": "Who hires Orkboard, for what job", "party": "product",
        "personas": [
            {"id": "solo", "title": "Solo developer", "line": "Runs AI tools on their own project and wants the work to go on while they look away."},
            {"id": "lead", "title": "The reviewing lead", "line": "Reads what the orks made and decides what goes into main."},
        ],
        "job": {"id": "main", "when": "I have several AI tools going on my project", "want": "one place where each tool's work is a goal I can see and answer",
                "so": "I stay the one who decides, not the one who watches terminals", "persona": "solo"},
        "forces": [
            {"dir": "in", "kind": "Push", "text": "terminals scroll past and I lose what each tool did"},
            {"dir": "in", "kind": "Pull", "text": "one Board, a card a goal, a gate before main"},
            {"dir": "out", "kind": "Anxiety", "text": "will the orks break main?"},
            {"dir": "out", "kind": "Habit", "text": "I just talk to one tool in a terminal"},
        ],
        "jobs": [
            {"id": "waits", "title": "Know what waits for me", "line": "One look says what asks, what is ready."},
            {"id": "changed", "title": "See what changed before main", "line": "The gate's tests and the diff, then my yes."},
            {"id": "stop", "title": "Stop a tool that runs away", "line": ""},
        ],
        "hired": {"id": "orkboard", "title": "Orkboard", "line": "One Board for the goals: the orks do them, you decide what goes into main."},
        "fired": [
            {"id": "tabs", "title": "A terminal tab per tool", "line": "Each tool alone; nothing says what is done or what waits."},
            {"id": "todo", "title": "A TODO file", "line": "Written once, never read; the tools do not take it."},
        ],
    }
    out = {"recorded": datetime.now(timezone.utc).isoformat(timespec="seconds"), "folder": ROOT.name,
           "tables": {"tech": {"architecture": arch}, "product": {"jtbd": jtbd}}}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {', '.join(code_layers.PACKAGES)}")


if __name__ == "__main__":
    main()
