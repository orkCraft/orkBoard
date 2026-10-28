"""The spec's format (docs/specs/99-a-goals-way.md §7.1; decisions §117.3, §118.3, §118.5): a page is a **common part**, the Orkmaster's and the person's — *Asked*, *Gist*,
*Route*, *Depends on*, *Decisions* — and **a section a party on the route**, `## <Party>`, its leader's, with its `###` parts. Pure code, no model, no face.

    spec_sections.read(page, parties=(), home="")      # {common: {name: text}, sections: [Section(party, title, parts, older)]}: a page of before is one section of its party
    spec_sections.is_party(name, text)                 # a `##` section that is a party's: not a common or an old name, and it holds a known `###` part
    spec_sections.split(text) / join(parts)            # a section's `###` parts by name / in the order they are written
    spec_sections.clean_section(answer, defaults)      # a leader's answer, strictly: ({part: text}, risk) or None (no Why, or no Done when)
    spec_sections.will_be(text)                        # a section's *Will be* as [{kind: new|changed|gone, id, note}]
    spec_sections.arrange(page, common, sections)      # the page's sections as the format has them: common, then a section a party, nothing known lost
    spec_sections.folded(page, "Done when")            # a page of the new format read as the old one (the plan of today reads Done when, Out, Risks)
    spec_sections.decided_by(page, part_id)            # who decided a change on a map: "person" · "leader" · "member" ("" for a page of before)
    spec_sections.record(state_dir, slug)              # what the decision and the sections keep beside a goal's state (way.json)

A section's parts, in the order they are written: *Why*, *Done when* (at most five theses), *Checks*, *Will be* (a line a part of the leader's map, `new <id>` ·
`changed <id>` · `gone <id>`, the id as the map names it), *Out*, *Risks*, *Defaults* (the questions closed by a default, seen), *Questions* (open), *Plan* (after *Start*).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, NamedTuple

COMMON = ("Asked", "Gist", "Route", "Depends on", "Decisions")
PARTS = ("Why", "Done when", "Checks", "Will be", "Out", "Risks", "Defaults", "Questions", "Plan")
OLD = ("Gist", "Why", "Done when", "Out", "Risks", "Depends on", "Stages", "Open questions", "Decisions")          # realm/idea_page.py `SECTIONS`
RESERVED = {n.lower() for n in (*COMMON, *OLD, *PARTS)}
FOLDED = ("Why", "Done when", "Out", "Risks")                          # an old section a page of the new format answers for (its first section's, Done when all of them)
WHY_CHARS, LINE_CHARS, MAX_DONE, MAX_CHECKS, MAX_WILL, MAX_OUT, MAX_RISKS, MAX_ASSUMED = 1200, 240, 5, 5, 12, 3, 4, 4
ID_CHARS = 200
FILE = "way.json"
_HEAD = re.compile(r"^###[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
_WILL = re.compile(r"^(?:[-*]\s*)?(new|changed|gone)\s+(?:part\s+)?([A-Za-z0-9_./@:\\-]+)(?:\s*[—–-]+\s*(.*))?$", re.I)
_FORK = re.compile(r"\bFork\b.*?\[sections:\s*([^\]]*)\]", re.I)
LEVELS = ("low", "medium", "high")


class Section(NamedTuple):
    party: str                  # the party's slug ("" where the page names none we know)
    title: str                  # the `##` heading as written
    parts: dict                 # {part name: text}, in the order written
    older: bool = False         # read from a page of before (Gist, Why, Done when, Out, Risks under its party's heading)


# -- a section's parts ----------------------------------------------------------------------------------------------------------------------

def split(text: str) -> dict[str, str]:
    """A section's `###` parts by name (as written, in order); what stands before the first `###` is kept under `""`."""
    text = str(text or "").replace("\r\n", "\n")
    found = list(_HEAD.finditer(text))
    out: dict[str, str] = {}
    if found and text[:found[0].start()].strip():
        out[""] = text[:found[0].start()].strip()
    elif not found and text.strip():
        out[""] = text.strip()
    for n, m in enumerate(found):
        end = found[n + 1].start() if n + 1 < len(found) else len(text)
        out[m.group(1).strip()] = text[m.end():end].strip()
    return out


def join(parts: dict[str, str]) -> str:
    """A section's text: the parts that have words, the known ones in `PARTS` order, the others after them, each under a `###` heading."""
    names = [n for n in PARTS if str(parts.get(n) or "").strip()] + [n for n in parts if n and n not in PARTS and str(parts[n]).strip()]
    body = "\n\n".join(f"### {n}\n{str(parts[n]).strip()}" for n in names)
    head = str(parts.get("") or "").strip()
    return f"{head}\n\n{body}" if head and body else (head or body)


def is_party(name: str, text: str) -> bool:
    """A `##` section of a party: its name is no common or old one, and it holds at least one known `###` part."""
    if str(name or "").strip().lower() in RESERVED:
        return False
    return any(k.lower() in {p.lower() for p in PARTS} for k in split(text) if k)


def section_name(title: str, taken: set[str] = frozenset()) -> str:
    """A party's `##` heading: its title on one line; where it would be a common or an old section's name, *(party)* after it."""
    name = " ".join(re.sub(r"[#\n\r]+", " ", str(title or "")).split())[:60] or "Party"
    if name.lower() in RESERVED or name.lower() in {t.lower() for t in taken}:
        name = f"{name} (party)"
    return name


# -- reading a page --------------------------------------------------------------------------------------------------------------------------

def sections_of(page: Any) -> list[tuple[str, str]]:
    """The party sections a page has, in the order they are written: `[(heading, text)]`."""
    return [(n, t) for n, t in page.sections if is_party(n, t)]


def read(page: Any, parties: Any = (), home: str = "") -> dict:
    """`{common: {name: text}, sections: [Section]}`. `parties`: `[{slug, title}]` (a section is a party's by its heading, a title or a slug). A page with no party
    section is one of before: **one section of its party** (`home`: the goal's party), its Gist kept as the common Gist, its Why, Done when, Out and Risks its
    parts; nothing is rewritten."""
    by = {}
    for p in parties or ():
        by[str(p.get("slug") or "").lower()] = p["slug"]
        by[str(p.get("title") or "").lower()] = p["slug"]
    common = {n: next((t for k, t in page.sections if k.lower() == n.lower()), "") for n in COMMON}
    found = [Section(by.get(n.lower(), ""), n, split(t)) for n, t in sections_of(page)]
    if found:
        return {"common": common, "sections": found}
    title = next((str(p.get("title") or "") for p in parties or () if p.get("slug") == home), "") or home
    parts = {n: v for n in ("Why", "Done when", "Out", "Risks") if (v := next((t for k, t in page.sections if k.lower() == n.lower()), "").strip())}
    return {"common": common, "sections": [Section(home, title, parts, True)] if parts or home else []}


def folded(page: Any, name: str) -> str:
    """A page of the new format read as the old one (`Page.section` falls back to it where an old section is empty): *Why*, *Out*, *Risks* of the first section (the
    first step's party), *Done when* of every section, the first's lines first (the others' under their party's name). "" where the page has no section of a party."""
    found = [(n, split(t)) for n, t in sections_of(page)]
    if not found or name not in FOLDED:
        return ""
    if name != "Done when":
        return found[0][1].get(name, "")
    lines = [found[0][1].get("Done when", "")] if found[0][1].get("Done when") else []
    for n, parts in found[1:]:
        lines += [f"{n}: {x}" for x in items(parts.get("Done when", ""))]
    return "\n".join(lines)


def items(text: str) -> list[str]:
    """A part's list (`- x`), or its lines."""
    lines = [ln.strip() for ln in str(text or "").split("\n") if ln.strip()]
    return [re.sub(r"^([-*+]|\d+[.)])\s+", "", ln) for ln in lines]


# -- *Will be* and who decided -------------------------------------------------------------------------------------------------------------

def will_be(text: str) -> list[dict]:
    """A section's *Will be* as `[{kind, id, note}]`: the lines that are `new|changed|gone <id>` (an id is a part of the leader's map: its path); any other line is no change."""
    out = []
    for ln in str(text or "").split("\n"):
        m = _WILL.match(ln.strip())
        if m and ".." not in m.group(2).split("/"):
            out.append({"kind": m.group(1).lower(), "id": m.group(2).strip("/") or ".", "note": (m.group(3) or "").strip()})
    return out


def same_part(a: str, b: str) -> bool:
    """Two ids name the same part, or one is inside the other (a path of a part's file is that part's)."""
    a, b = str(a).strip("/"), str(b).strip("/")
    return bool(a and b) and (a == b or a.startswith(b + "/") or b.startswith(a + "/") or a == "." or b == ".")


def forks_answered(page: Any) -> set[str]:
    """The headings of the sections a fork answered in *Decisions* changed (`Fork — <about>: <answer> [sections: Tech, Art]`)."""
    names: set[str] = set()
    for ln in str(next((t for n, t in page.sections if n.lower() == "decisions"), "")).split("\n"):
        m = _FORK.search(ln)
        if m:
            names |= {x.strip().lower() for x in m.group(1).split(",") if x.strip()}
    return names


def decided_by(page: Any, part_id: str) -> str:
    """Who decided a change on a map (decisions §112.6), read from the goal's sections with no model: `person` where a section whose *Will be* names the part was changed by
    an answer of theirs (a fork), `leader` where one names it and its leader wrote it, `member` where none does (made by a task and promised nowhere). "" for a page of before
    (it has no *Will be*)."""
    found = [(n, split(t)) for n, t in sections_of(page)]
    if not found:
        return ""
    answered = forks_answered(page)
    hit = [n for n, parts in found if any(same_part(w["id"], part_id) for w in will_be(parts.get("Will be", "")))]
    if not hit:
        return "member"
    return "person" if any(n.lower() in answered for n in hit) else "leader"


# -- a leader's answer, strictly ---------------------------------------------------------------------------------------------------------

def _line(value: object, limit: int = LINE_CHARS) -> str:
    return " ".join(value.split())[:limit].rstrip() if isinstance(value, str) else ""


def _list(value: object, limit: int, each: int = LINE_CHARS) -> list[str]:
    out: list[str] = []
    for v in value if isinstance(value, list) else []:
        if (s := _line(v, each)) and s not in out and len(out) < limit:
            out.append(s)
    return out


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {s}" for s in lines)


def clean_will(value: object) -> list[str]:
    """The *Will be* lines of an answer, strictly: `new|changed|gone <id>` (and a note after a dash), an id a path (no `..`, `ID_CHARS` at most); any other line is dropped."""
    out: list[str] = []
    for ln in _list(value, MAX_WILL * 2, ID_CHARS + 120):
        m = _WILL.match(ln)
        if m and len(m.group(2)) <= ID_CHARS and ".." not in m.group(2).split("/"):
            line = f"{m.group(1).lower()} {m.group(2).strip('/') or '.'}" + (f" — {_line(m.group(3), 120)}" if m.group(3) else "")
            if line not in out and len(out) < MAX_WILL:
                out.append(line)
    return out


def clean_section(answer: Any, defaults: list[str] = ()) -> tuple[dict[str, str], str] | None:
    """A leader's answer as its section's parts, strictly: `{"why", "done_when": [≤5], "checks", "will_be", "out", "risks", "risk", "assumed"}` → `({part: text}, risk)`.
    None when the answer has no *Why* or no thesis. *Defaults* is the Talk's defaults for this party (`defaults`, code's) and what the leader assumed; *Questions* is never
    written (a leader asks nothing more at this step: it decides, and says what it assumed)."""
    if not isinstance(answer, dict):
        return None
    why = _line(answer.get("why"), WHY_CHARS)
    done = _list(answer.get("done_when"), MAX_DONE)
    if not why or not done:
        return None
    assumed = [f"Assumed: {x}" for x in _list(answer.get("assumed"), MAX_ASSUMED)]
    parts = {"Why": why, "Done when": _bullets(done), "Checks": _bullets(_list(answer.get("checks"), MAX_CHECKS)),
             "Will be": _bullets(clean_will(answer.get("will_be"))), "Out": _bullets(_list(answer.get("out"), MAX_OUT)),
             "Risks": _bullets(_list(answer.get("risks"), MAX_RISKS)), "Defaults": _bullets([*list(defaults), *assumed])}
    risk = str(answer.get("risk") or "").strip().lower()
    return {k: v for k, v in parts.items() if v}, risk if risk in LEVELS else "low"


# -- the page ----------------------------------------------------------------------------------------------------------------------------------

def arrange(page: Any, common: dict[str, str], sections: list[tuple[str, str]]) -> None:
    """The page's sections as the format has them (under `ideas.LOCK`, the caller writes the page): the common part in its order (`common` gives a name's new text; a
    name it lacks keeps what the page has), then a section a party in the route's order (`sections`: `[(heading, text)]`, a heading the page has already is replaced), then
    what else the page holds. An empty old section (Why, Done when, Out, Risks, Stages, Open questions) goes: the parties' sections say it."""
    have = {n.lower(): (n, t) for n, t in page.sections}
    out: list[tuple[str, str]] = []
    used: set[str] = set()
    for name in COMMON:
        text = common[name] if name in common else (have.get(name.lower(), ("", ""))[1])
        if name in common or name.lower() in have:
            out.append((name, str(text or "").strip()))
            used.add(name.lower())
    for heading, text in sections:
        out.append((heading, str(text or "").strip()))
        used.add(heading.lower())
    for n, t in page.sections:
        if n.lower() not in used and not (n.lower() in {o.lower() for o in OLD} and not t.strip()):
            out.append((n, t))
    page.sections = out


# -- what the decision and the sections keep: <state_dir>/ideas/<slug>/way.json --------------------------------------------------------------

def record(state_dir: Path, slug: str) -> dict:
    """`{decision: {title, text, number, at, confirmed, commit, held, path} | None, texts: {party: {leader, parts, risk}}, joined, forks: [{id, about, sides, status, answer,
    changes}], wait}`; {} before E has begun."""
    from orkboard.realm import ideas
    return ideas._json(ideas.state_folder(state_dir, slug) / FILE) or {}


def save_record(state_dir: Path, slug: str, rec: dict) -> dict:
    """The record replaced whole (a caller that read it first holds `ideas.LOCK` for both)."""
    from orkboard.realm import ideas
    with ideas.LOCK:
        ideas._write_json(ideas.state_folder(state_dir, slug) / FILE, rec)
    return rec
