"""The chronicle's search (docs/specs/134-release-keeps-the-chronicle.md A.6, decisions §238.3): over the goals' titles, the decisions and the sections. No model, nothing written.

    chronicle_find.find(state_dir, pages, repo, log, query, party="")      # `party` (spec 150 E1.4): the search over that party's past only
        # {query, found, more, chapters: [{id, kind, name, day, goals: [{idea, title, in}], decisions: [{number, title, day, in}]}], unreleased: {goals, decisions} | None}

The query is cut at `QUERY_MAX` and split in at most `WORDS_MAX` words (lower case); an item is found when **every** word is in its text. A goal's text is its title, its spec (every section's parts)
and its decision's title and entry; `in` says where a word was found: `title`, `spec`, `decision`. A decision of no goal: its title and entry (`in` `decision`).
Chapters with no find are left out, the rest are by chapter, newest first; at most `FIND_MAX` items, `more` the number left out. An empty query finds nothing.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import chronicle, ideas

QUERY_MAX = 80
WORDS_MAX = 6
FIND_MAX = 60
TEXT_MAX = 40_000


def words(query: object) -> list[str]:
    return str(query or "")[:QUERY_MAX].lower().split()[:WORDS_MAX]


def _hit(want: list[str], text: str) -> bool:
    low = text.lower()
    return all(w in low for w in want)


def _spec_text(pages: Path, slug: str) -> str:
    page = ideas.idea_page(pages, slug)
    if page is None:
        return ""
    return "\n".join(f"{n}\n{t}" for n, t in page.sections)[:TEXT_MAX]


def _goal(want: list[str], pages: Path, g: dict, decisions: dict) -> dict | None:
    dec = decisions.get(g["decision"]) if g["decision"] else None
    parts = {"title": g["title"], "spec": _spec_text(pages, g["idea"]), "decision": f"{dec['title']}\n{dec.get('text', '')}" if dec else ""}
    if not _hit(want, "\n".join(parts.values())):
        return None
    return {"idea": g["idea"], "title": g["title"], "in": [k for k, v in parts.items() if any(w in v.lower() for w in want)]}


def find(state_dir: Path, pages: Path, repo: Path, log: "str | Path", query: object, party: str = "") -> dict:
    """See the module."""
    want = words(query)
    out = {"query": " ".join(want), "found": 0, "more": 0, "chapters": [], "unreleased": None}
    if not want:
        return out
    got = chronicle.read(state_dir, pages, repo, log, text=True, party=party)
    left = FIND_MAX
    seen = 0

    def pick(c: dict) -> dict | None:
        nonlocal left, seen
        gs = [x for g in c["goals"] if (x := _goal(want, pages, g, got["decisions"])) is not None]
        ds = [{"number": d["number"], "title": d["title"], "day": d["day"], "in": ["decision"]} for d in c["decisions"] if _hit(want, f"{d['title']}\n{d.get('text', '')}")]
        seen += len(gs) + len(ds)
        gs, ds = gs[:left], ds[:max(0, left - len(gs[:left]))]
        left -= len(gs) + len(ds)
        return {"id": c.get("id", ""), "kind": c.get("kind", ""), "name": c.get("name", ""), "day": c.get("day", ""), "goals": gs, "decisions": ds} if gs or ds else None

    out["chapters"] = [x for c in got["chapters"] if (x := pick(c)) is not None]
    if got["unreleased"] is not None:
        mine = pick({"goals": got["unreleased"]["goals"], "decisions": got["unreleased"]["decisions"]})
        out["unreleased"] = {"goals": mine["goals"], "decisions": mine["decisions"]} if mine else None
    shown = sum(len(c["goals"]) + len(c["decisions"]) for c in out["chapters"]) + (len(out["unreleased"]["goals"]) + len(out["unreleased"]["decisions"]) if out["unreleased"] else 0)
    out["found"], out["more"] = shown, seen - shown
    return out
