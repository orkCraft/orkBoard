"""A hero's kept table (docs/specs/157-the-inventory-a-merchants-stall.md §A.4; decisions §267.2): the cards a party's hero laid in its frame's places, `<wiki>/pages/tables/<party>.md`.

    hero_table.read(root, party)                     # {hero, laid, stale, places: [{name, ask, cards: [{title, line, goal, state}]}]}
    hero_table.write(root, party, hero, places)      # the file written whole; `places`: {place name: [card, …]} or [{name, cards}, …]; a card {title, line, goal?, state?}

The file: front matter `owner: board`, `kind: table`, `party`, `hero`, `laid` (an ISO date), `schema: 1`; then a `## <place>` section a place, its lines `- <title> — <line>` with an optional
trailing `{goal: <slug>, state: hot|bad|good|ghost}`. `read` gives every place of the party's hero (`goal_team.hero_of`), in the hero's order, empty when the file lacks it; a place the file
has and the hero does not is dropped; `stale` is true when the file's `hero` is not the party's now; with no file every place is empty and `laid` is "". Text only: a line is at most
`LINE_CHARS` characters, a place at most `MAX_CARDS` cards. No face, no model.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from orkboard.realm import goal_team, heroes, ideas
from orkboard.realm.idea_page import Page

TABLES = "pages/tables"
STATES = ("hot", "bad", "good", "ghost")
LINE_CHARS, TITLE_CHARS, MAX_CARDS = 160, 80, 12
_TAIL = re.compile(r"\s*\{([^{}]*)\}\s*$")
_SEP = " — "


def _one(text: object, cap: int) -> str:
    return " ".join(str(text or "").split())[:cap].strip()


def _path(root: Path, party: str) -> Path | None:
    return Path(root) / TABLES / f"{party}.md" if re.fullmatch(r"[a-z0-9-]+", party or "") else None


def _card(raw: object) -> dict | None:
    """A card as given ({title, line, goal, state}) cleaned; None for one with no title."""
    if not isinstance(raw, dict):
        return None
    title = _one(raw.get("title"), TITLE_CHARS).replace(_SEP, " - ")
    if not title:
        return None
    goal = str(raw.get("goal") or "").strip()
    state = str(raw.get("state") or "").strip()
    return {"title": title, "line": _one(raw.get("line"), LINE_CHARS).replace("{", "(").replace("}", ")"),
            "goal": goal if re.fullmatch(r"[a-z0-9-]+", goal) else "", "state": state if state in STATES else ""}


def _line(c: dict) -> str:
    text = f"- {c['title'].replace('{', '(').replace('}', ')')}" + (f"{_SEP}{c['line']}" if c["line"] else "")
    tail = ", ".join(p for p in (f"goal: {c['goal']}" if c["goal"] else "", f"state: {c['state']}" if c["state"] else "") if p)
    return f"{text} {{{tail}}}" if tail else text


def _parse_line(line: str) -> dict | None:
    line = line.strip()
    if not line.startswith("- "):
        return None
    line = line[2:]
    goal = state = ""
    m = _TAIL.search(line)
    if m:
        for part in m.group(1).split(","):
            k, _s, v = part.partition(":")
            if k.strip() == "goal":
                goal = v.strip()
            elif k.strip() == "state":
                state = v.strip()
        line = line[:m.start()]
    title, _s, rest = line.partition(_SEP)
    return _card({"title": title, "line": rest, "goal": goal, "state": state})


def _places(places: object) -> dict[str, list]:
    if isinstance(places, dict):
        return {str(k): list(v or []) for k, v in places.items()}
    return {str(p.get("name")): list(p.get("cards") or []) for p in places or [] if isinstance(p, dict)}


def read(root: Path, party: str) -> dict:
    """The party's kept table as the spec's object (see the module); a missing or unreadable file gives every place empty."""
    hero = goal_team.hero_of(root, party)
    path = _path(root, party)
    page = ideas._read(path) if path is not None and path.is_file() else None
    kept: dict[str, list[dict]] = {}
    if page is not None:
        for name, text in page.sections:
            kept[name] = [c for ln in text.split("\n") if (c := _parse_line(ln)) is not None][:MAX_CARDS]
    return {"hero": hero.id if hero is not None else "",
            "laid": (page.get("laid") if page is not None else "") or "",
            "stale": page is not None and page.get("hero") != (hero.id if hero is not None else ""),
            "places": [{"name": n, "ask": a, "cards": kept.get(n, [])} for n, a in (hero.places if hero is not None else ())]}


def write(root: Path, party: str, hero: object, places: object) -> None:
    """The party's table written whole for `hero` (a `Hero` or its id): a section a place of the hero's in its order, from `places` (a dict {place: cards} or a list of {name, cards});
    a place the hero does not have is left out. ValueError for an unknown hero or party name."""
    h = heroes.get(hero) if isinstance(hero, str) else hero
    path = _path(root, party)
    if h is None or path is None:
        raise ValueError("No such hero" if h is None else f"No party {party!r}")
    given = _places(places)
    sections = []
    for name, _ask in h.places:
        cards = [c for c in (_card(x) for x in given.get(name, [])) if c is not None][:MAX_CARDS]
        sections.append((name, "\n".join(_line(c) for c in cards)))
    page = Page([("owner", ideas.OWNER), ("kind", "table"), ("party", party), ("hero", h.id), ("laid", dt.date.today().isoformat()), ("schema", "1")], "", "", sections)
    with ideas.LOCK:
        ideas._write(path, page.text())
