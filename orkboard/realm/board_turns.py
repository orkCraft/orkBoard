"""The moves that wait for the person, read from the Board's pages (docs/specs/171, decisions §301, §302): one turn a goal, by what its page says and nothing else.
Pure code over parsed pages: no git, no model, no write, no face.

    turns(pages, parties, at)       # [{goal, kind, at, questions?}], in the pages' order

A goal's page waits for the person when:

- `asks: person` (`kind: "asks"`): `questions` lists each open question of *Open questions* (an answered one is left out) with its `ways`, then the cards the keeper's record holds for the person
  that the page does not ask yet (`waiting`: a Talk leader's question, a bug's case question and its guess); a party whose reading asks (`asking_parties`) has one too, `party: true`;
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


def asking(page: idea_page.Page, waiting: Any = ()) -> list[dict]:
    """The questions that wait for the person, in the order a way answers them: each open question of the page's *Open questions* (`{ask, ways, n}`, `n` its place there), then each card
    of `waiting` (a Talk leader's question to the person, a bug's case question and its guess: the keeper's record holds them, the page does not yet) that the page does not ask
    (`{ask, ways, line}`, `line` the page line it is written as). `ask` and `ways` are what the card shows."""
    text = page.section("Open questions")
    out = [{"ask": p["ask"], "ways": list(p["choices"]), "n": n} for n, q in idea_questions.open_of(text) if (p := idea_questions.parse(q))["ask"]]
    have = {idea_questions.parse(q)["ask"] for q in idea_questions.questions_of(text)}
    for c in waiting or ():
        ask = " ".join(str(c.get("q") or "").split())
        if ask and ask not in have and c.get("choices"):
            have.add(ask)
            out.append({"ask": ask, "ways": list(c["choices"]), "line": idea_questions.card_line(c)})
    return out


def questions(page: idea_page.Page, waiting: Any = ()) -> list[dict]:
    """What a turn lists: each question that waits, `{ask, ways}` (`ways`: its choices, none for a free question)."""
    return [{"ask": q["ask"], "ways": q["ways"]} for q in asking(page, waiting)]


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


def turn_of(slug: str, page: idea_page.Page, parties: list[dict], at: str = "", waiting: Any = ()) -> dict | None:
    """The goal's turn, or None when nothing waits for the person. `waiting`: the cards the keeper's record holds for it (a Talk question to the person, a bug's cause)."""
    if page.get("queue").strip().lower() == "hold":
        return None
    phase = page.get("phase").strip().lower()
    if phase in ("work", "done"):
        return None
    if page.get("asks").strip().lower() == "person" and (asked := questions(page, waiting)):      # a question answered on the page waits no longer, though the record still holds its card
        return {"goal": slug, "kind": "asks", "at": at, "questions": asked}
    route = route_of(page)
    if phase == "talk" and talked(page, route, parties):
        return {"goal": slug, "kind": "talk", "at": at}
    if phase == "spec" and written(page, route, parties):
        return {"goal": slug, "kind": "spec", "at": at}
    return None


def party_turn(slug: str, page: idea_page.Page, at: str = "") -> dict | None:
    """A party's turn: the questions its own page asks the person (its keeper's reading asked them), `party: True`; none when it has no question open."""
    asked = questions(page)
    return {"goal": slug, "kind": "asks", "party": True, "at": at, "questions": asked} if asked else None


def turns(pages: Mapping[str, Any], parties: list[dict], at: Mapping[str, str] | None = None, waiting: Mapping[str, Any] | None = None,
          asking_parties: Mapping[str, Any] | None = None) -> list[dict]:
    """The turns of every page given, in its order, then each party in `asking_parties` (`{slug: its page}`, those whose reading asks the person) that has a question open."""
    at, waiting = at or {}, waiting or {}
    got = [turn_of(slug, page, parties, at.get(slug, ""), waiting.get(slug, ())) for slug, page in pages.items()]
    got += [party_turn(slug, page, at.get(f"party:{slug}", "")) for slug, page in (asking_parties or {}).items()]
    return [t for t in got if t]
