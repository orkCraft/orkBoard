"""Spec 171 F: the page reads the host, `proposed()` gone (docs/specs/171 Tech: *Off ?mock=1 the page imports nothing of js/mock/*): js/link.js has no `proposed(`, nothing in js/ or pwa/
reads a part from it, and nothing but `?mock=1`'s own door reaches js/mock/."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static"
SOURCES = [p for root in (STATIC / "js", STATIC / "pwa") for p in root.rglob("*.js")]
MOCK = STATIC / "js" / "mock"


def text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_link_js_has_no_proposed():
    assert "proposed" not in text(STATIC / "js" / "link.js")


def test_no_face_reads_a_proposed_part_from_link_js():
    """`proposed(` as a call: the pwa's own `proposed(core)` (pwa/shell-proposals.js) is another thing and stays."""
    calls = re.compile(r"(?<![\w.])proposed\(\s*[\"']")
    found = [str(p.relative_to(STATIC)) for p in SOURCES if MOCK not in p.parents and calls.search(text(p))]
    assert not found, found
    importing = [str(p.relative_to(STATIC)) for p in SOURCES if MOCK not in p.parents and re.search(r"import\s*\{[^}]*\bproposed\b[^}]*\}\s*from\s*[\"'][./]*(?:js/)?link\.js", text(p))]
    assert not importing, importing


def code(p: Path) -> str:
    """The file without its `//` comments (a comment may name js/mock/; a string that reaches it may not)."""
    return "\n".join(re.sub(r"^\s*//.*$|\s//\s.*$", "", line) for line in text(p).splitlines())


def test_nothing_off_mocks_reaches_js_mock():
    """Only link.js's and board.js's `?mock=1` doors name js/mock/ in a string (a module or a sheet fetched); js/mock/ itself aside."""
    reach = re.compile(r"[\"'`][^\"'`\n]*\bmock/[^\"'`\n]*[\"'`]")
    found = [str(p.relative_to(STATIC)) for p in SOURCES if MOCK not in p.parents and p.name not in ("link.js",) and p.parent != STATIC and reach.search(code(p))]
    assert not found, found
    for door in (STATIC / "js" / "link.js", STATIC / "board.js"):
        lines = [ln for ln in code(door).splitlines() if re.search(r"mock/", ln)]
        assert lines and all("MOCK" in ln or "onMocks" in ln or "plate" in ln or "sheet" in ln for ln in lines), (door, lines)


def test_gui_and_js_hold_no_battle_settle_and_no_sp_ring():
    """Goal "The battle and the gate", stage N: `ideas.battle_settle` and the gate's ring are gone from the page, its sheets and the host."""
    root = STATIC.parent
    found = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.suffix in {".js", ".css", ".py", ".html"} and "vendor" not in p.parts
             and ("battle_settle" in text(p) or "sp-ring" in text(p))]
    assert not found, found


def test_off_mocks_js_cards_draws_no_battle_and_no_gate_from_js_mock():
    """Neither mat imports js/mock/ or reads a recording: they ask the host (`ideas.battle`, `ideas.gate_guards`)."""
    for name in ("battle.js", "gate.js"):
        src = code(STATIC / "js" / "cards" / "spreads" / name)
        assert "mock" not in src.lower(), name
    assert "ideas.battle" in text(STATIC / "js" / "cards" / "spreads" / "battle.js") and "ideas.gate_guards" in text(STATIC / "js" / "cards" / "spreads" / "gate.js")
