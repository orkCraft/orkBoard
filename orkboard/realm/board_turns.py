"""The moves that wait for the person, read from the Board's pages (docs/specs/171, decisions §301, §302): one turn a goal, by what its page says and nothing else.
Pure code over parsed pages: no git, no model, no write, no face.

    turns(pages, parties, at)       # [{goal, kind, at, questions?}], in the pages' order

A goal's page waits for the person when:

- `asks: person` (`kind: "asks"`): `questions` lists each open question of *Open questions* (an answered one is left out) with its `ways`;
- `phase: talk` with every party of its `route` having said its `### Talk` (`kind: "talk"`): the leaders have spoken, the person decides;
- `phase: spec` with every party of its `route` having written its section, *Why* and *Done when* (`kind: "spec"`).

A goal at `work` or `done`, on Hold (`queue: hold`), or with nothing waiting has no turn. `parties`: `[{slug, title}]` (a route names a slug, a section a title);
`at`: when each goal last changed, `{slug: iso text}` (the caller reads it).
"""
from __future__ import annotations

from typing import Any, Mapping

from orkboard.realm import idea_page, idea_questions, page_talk, spec_sections

KINDS = ("asks", "talk", "spec")
WRITTEN = ("Why", "Done when")                      # a party's section is written when it holds these parts


def route_of(page: idea_page.Page) -> list[str]:
    """The slugs of the page's `route`, in order."""
    return [s for s in (x.strip() for x in page.get("route").split(",")) if s]


def questions(page: idea_page.Page) -> list[dict]:
    """The open questions of a page, each `{ask, ways}` (`ways`: its choices, none for a free question)."""
    out = []
    for line in idea_page.items(page.section("Open questions")):
        q = idea_questions.parse(line)
        if q["ask"]:
            out.append({"ask": q["ask"], "ways": list(q["choices"])})
    return out


def _title(parties: list[dict], slug: str) -> str:
    return next((str(p.get("title") or "") for p in parties if p.get("slug") == slug), "") or slug


def talked(page: idea_page.Page, route: list[str], parties: list[dict]) -> bool:
    """Every party of the route has its `### Talk`."""
    return bool(route) and all(page_talk.read_talk(page, _title(parties, s)) is not None for s in route)


def written(page: idea_page.Page, route: list[str], parties: list[dict]) -> bool:
    """Every party of the route has written its section (its *Why* and *Done when*)."""
    if not route:
        return False
    found = {s.party: s for s in spec_sections.read(page, parties)["sections"] if not s.older}
    return all(s in found and all(found[s].parts.get(w, "").strip() for w in WRITTEN) for s in route)


def turn_of(slug: str, page: idea_page.Page, parties: list[dict], at: str = "") -> dict | None:
    """The goal's turn, or None when nothing waits for the person."""
    if page.get("queue").strip().lower() == "hold":
        return None
    phase = page.get("phase").strip().lower()
    if phase in ("work", "done"):
        return None
    if page.get("asks").strip().lower() == "person":
        return {"goal": slug, "kind": "asks", "at": at, "questions": questions(page)}
    route = route_of(page)
    if phase == "talk" and talked(page, route, parties):
        return {"goal": slug, "kind": "talk", "at": at}
    if phase == "spec" and written(page, route, parties):
        return {"goal": slug, "kind": "spec", "at": at}
    return None


def turns(pages: Mapping[str, Any], parties: list[dict], at: Mapping[str, str] | None = None) -> list[dict]:
    """The turns of every page given, in its order."""
    at = at or {}
    got = (turn_of(slug, page, parties, at.get(slug, "")) for slug, page in pages.items())
    return [t for t in got if t]
