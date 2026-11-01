"""The memory bank of a project, in Cline's six files, written by code (docs/specs/126-read-in-and-write-out.md §C; decisions §204): a short Markdown page each, the
project's brief and parties, whom it is for, what Tech keeps, the goals in work and what came of the rest. No model, no network. `realm/write_out.py` writes them.

    write_out_bank.pages(root, state_dir, board)     # {"projectbrief.md": text, "productContext.md": text, ...}: the six, whole

A part with nothing says *Nothing yet*. Every page carries a line that says Orkboard wrote it (`MARK`), so a file of the person's with the same name is never
taken for one of these.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_team, ideas, journals, library, project_facts, roles

MARK = "Written by Orkboard (orkboard export); the next export writes it again, so keep your own edits elsewhere."
NOTHING = "Nothing yet."
LAST = 10                    # the entries of a journal in systemPatterns and activeContext
PROGRESS = 40                # the entries of progress, at most
GOALS = 40                   # the goals in work, at most
FILES = ("projectbrief.md", "productContext.md", "systemPatterns.md", "techContext.md", "activeContext.md", "progress.md")


def _day(e: dict) -> str:
    return str(e.get("at") or "")[:10]


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {x}" for x in lines) if lines else NOTHING


def _entries(rows: list[dict]) -> list[str]:
    return [f"{_day(e)} · {e['text']}" for e in rows]


def leader_name(state_dir: Path, slug: str) -> str:
    """A leader's name: the project's role, else the library's, else its slug."""
    try:
        r = roles.role(state_dir, slug)
    except Exception:
        r = None
    a = library.get(slug)
    return str((r or {}).get("name") or (a.name if a else "") or slug)


def parties(board: Path) -> list[dict]:
    """The parties of the Board, in order (none when the Board has no pages)."""
    try:
        return ideas.tracks(board, make=False)
    except Exception:
        return []


def of_craft(board: Path, craft: str) -> list[str]:
    """The slugs of the parties of a craft (`goal_team.craft_of`: tech, product, design …)."""
    out = []
    for t in parties(board):
        try:
            if goal_team.craft_of(board, t["slug"]) == craft:
                out.append(t["slug"])
        except Exception:
            continue
    return out


def _digests(state_dir: Path, slugs: list[str]) -> list[str]:
    return [d["text"] for s in slugs for d in [journals.digest(state_dir, s)] if d]


def _brief(state_dir: Path, board: Path) -> str:
    got = project_facts._read(state_dir)["common"]
    brief = [f"{project_facts.LABELS[k]}: {got[k]}" for k in project_facts.COMMON_KEYS if k in got]
    team = [f"{t['title']}, led by {leader_name(state_dir, t['leader'] or 'taskmaster')}" for t in parties(board)]
    return f"# Project brief\n\n<!-- {MARK} -->\n\n## The brief\n\n{_bullets(brief)}\n\n## The parties\n\n{_bullets(team)}\n"


def _product(state_dir: Path, board: Path) -> str:
    got = project_facts._read(state_dir)["common"]
    out = [f"# Product context\n\n<!-- {MARK} -->"]
    for key, head in (("for_whom", "Whom it is for"), ("hurts", "What hurts them"), ("why_us", "Why this, not what they use now"),
                      ("pillars", "What it must always be")):
        out.append(f"## {head}\n\n{got.get(key) or NOTHING}")
    digest = _digests(state_dir, of_craft(board, "product"))
    if digest:
        out.append("## Product's digest\n\n" + "\n\n".join(digest))
    return "\n\n".join(out) + "\n"


def _patterns(state_dir: Path, board: Path) -> str:
    tech = of_craft(board, "tech")
    rows = sorted((e for s in tech for e in journals.read(state_dir, s)), key=_day)[-LAST:]
    digest = _digests(state_dir, tech)
    return (f"# System patterns\n\n<!-- {MARK} -->\n\n## Tech's digest\n\n" + ("\n\n".join(digest) if digest else NOTHING)
            + f"\n\n## The last {LAST} entries of Tech's journal\n\n{_bullets(_entries(rows))}\n")


def _tech(state_dir: Path, board: Path) -> str:
    facts = [r["text"] for s in of_craft(board, "tech") for r in project_facts.of(state_dir, s)]
    return f"# Tech context\n\n<!-- {MARK} -->\n\n## What Tech knows of the project\n\n{_bullets(facts)}\n"


def _active(state_dir: Path, board: Path) -> str:
    work = []
    try:
        for g in ideas.ideas(board):
            st = ideas.state(state_dir, g["slug"])["state"]
            if st != "done":
                work.append(f"{g['title']} ({st})")
    except Exception:
        pass
    last = journals.read(state_dir, journals.PROJECT)[-LAST:]
    return (f"# Active context\n\n<!-- {MARK} -->\n\n## Goals in work\n\n{_bullets(work[:GOALS])}\n\n"
            f"## The project's journal, the last {LAST}\n\n{_bullets(_entries(last))}\n")


def _progress(state_dir: Path) -> str:
    rows = [e for e in journals.read(state_dir, journals.PROJECT) if e["kind"] in ("done", "dropped")][::-1][:PROGRESS]
    return (f"# Progress\n\n<!-- {MARK} -->\n\n## What was done and what was dropped, newest first\n\n"
            + _bullets([f"{_day(e)} · {e['kind']} · {e['text']}" for e in rows]) + "\n")


def pages(root: Path, state_dir: Path, board: Path) -> dict[str, str]:
    """The six files, each whole: `{name: text}`, in Cline's order."""
    return {"projectbrief.md": _brief(state_dir, board), "productContext.md": _product(state_dir, board),
            "systemPatterns.md": _patterns(state_dir, board), "techContext.md": _tech(state_dir, board),
            "activeContext.md": _active(state_dir, board), "progress.md": _progress(state_dir)}
