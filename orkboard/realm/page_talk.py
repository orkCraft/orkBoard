"""A leader's say in Talk and its acceptance, written in the goal's page (docs/specs/154-a-leader-is-a-skill-in-claude-code.md part B; decisions §258.6): under the party's section
`## <Party title>`, two parts of their own, `### Talk` and `### Accepted`. Pure code over a `Page`, no model, no face.

    ### Talk
    - verdict: doubt — the cache adds a second caller to the store
    - stance: Tech can build it in a step if the store keeps one writer
    - for: one screen, no new service
    - against: a second writer to the store
    - instead: show the cached board only
    - assumes: players reload less than once a minute — shown by: the reload events of a week

    ### Accepted
    - met: the board shows the best three players
    - not met: a tie is ordered by the earlier score — the order is by name
    - cannot see: the board loads in under a second

    page_talk.read_talk(page, party)               # {verdict, why, stance, for, against, instead, assumes: {text, signal} | None} or None
    page_talk.write_talk(page, party, say)         # the part written into the party's section (made when the page has none); the cleaned say, or None
    page_talk.read_accepted(page, party)           # [{line, status: met|not met|cannot see, why}]
    page_talk.write_accepted(page, party, lines)   # …written; the lines kept, strictly
    page_talk.talk_problems(lines) / accepted_problems(lines, done)    # what `orkboard check` cannot read: [(index of the line, what)]

`party` is the party's title or its slug. Every other part and section of the page is kept byte for byte; the two parts are no spec part (`spec_sections`: never folded, never counted as
*Done when*). A leader's questions stay the page's *Open questions*.
"""
from __future__ import annotations

import re
from typing import Any

from orkboard.realm import idea_page, spec_sections

LINE_CHARS = 200                                   # a line of the say, at most (the call's own limit)
MAX_ACCEPTED = 20
VERDICTS = ("go", "doubt", "no")
STATUSES = ("met", "not met", "cannot see")
TALK, ACCEPTED = "Talk", "Accepted"
KEYS = ("verdict", "stance", "for", "against", "instead", "assumes")
DASH = " — "
SHOWN = f"{DASH}shown by: "
_TALK_LINE = re.compile(r"^[-*+][ \t]+(" + "|".join(KEYS) + r")[ \t]*:[ \t]*(.*)$", re.I)
_ACCEPTED_LINE = re.compile(r"^[-*+][ \t]+(met|not met|cannot see)[ \t]*:[ \t]*(.*)$", re.I)


# -- finding the section and the part -------------------------------------------------------------------------------------------------

def _plain(value: object, limit: int = LINE_CHARS) -> str:
    return " ".join(value.split())[:limit].rstrip() if isinstance(value, str) else ""


def _section(page: idea_page.Page, party: str) -> int | None:
    """The index of the party's section in `page.sections`: its heading is the party's title (as `spec_sections` names a section) or the party's slug."""
    party = str(party or "").strip()
    if not party:
        return None
    named = spec_sections.section_name(party).lower()
    slug = idea_page.slugify(party)
    for i, (heading, _text) in enumerate(page.sections):
        low = heading.strip().lower()
        if low == named or (low not in spec_sections.RESERVED and (low == party.lower() or idea_page.slugify(heading) == slug)):
            return i
    return None


def _title(party: str) -> str:
    """The heading a section is made with: the party's title as given, or a slug said as a title (`tech` → *Tech*, `game-design` → *Game design*), so a
    section made from a slug is the one an agent is told to write (`## <Party title>`, spec 154 A's frames)."""
    party = " ".join(str(party or "").split())
    if party and party == idea_page.slugify(party):
        words = party.replace("-", " ")
        return words[:1].upper() + words[1:]
    return party


def _parts(text: str) -> list[tuple[str, int, int]]:
    """A section's `###` parts as `(name, start of its heading, end of its text)` in the raw text."""
    found = list(spec_sections._HEAD.finditer(text))
    return [(m.group(1).strip(), m.start(), found[n + 1].start() if n + 1 < len(found) else len(text)) for n, m in enumerate(found)]


def part_text(section: str, name: str) -> str | None:
    """A named part's lines (without its heading), None when the section has none."""
    for n, start, end in _parts(section):
        if n.lower() == name.lower():
            return section[start:end].split("\n", 1)[1] if "\n" in section[start:end] else ""
    return None


def _put(section: str, name: str, body: str) -> str:
    """The section's text with the part `name` replaced by `body` (its lines), or added: *Talk* before an *Accepted*, any other at the end. Every other byte stays."""
    block = f"### {name}\n{body}"
    parts = _parts(section)
    for n, start, end in parts:
        if n.lower() == name.lower():
            tail = section[end:]
            return section[:start] + block + ("\n\n" + tail if tail else "")
    if name == TALK:
        for n, start, _end in parts:
            if n.lower() == ACCEPTED.lower():
                return section[:start] + block + "\n\n" + section[start:]
    return (section.rstrip("\n") + "\n\n" if section.strip() else "") + block


def _write(page: idea_page.Page, party: str, name: str, body: str) -> None:
    at = _section(page, party)
    if at is None:
        heading = spec_sections.section_name(_title(party), {h for h, _t in page.sections})
        last = max((i for i, (h, t) in enumerate(page.sections) if spec_sections.is_party(h, t)), default=len(page.sections) - 1)
        page.sections.insert(last + 1, (heading, _put("", name, body)))
        return
    heading, text = page.sections[at]
    page.sections[at] = (heading, _put(text, name, body))


# -- Talk ---------------------------------------------------------------------------------------------------------------------------------------

def _assumes(value: str) -> dict | None:
    text, _sep, signal = value.partition(SHOWN)
    text, signal = _plain(text), _plain(signal)
    return {"text": text, "signal": signal} if text and signal else None


def _verdict_of(value: str) -> tuple[str, str]:
    """`(verdict, why)` of a verdict line's value: the word, then a dash and why."""
    head, sep, why = value.partition(DASH)
    if not sep and " - " in value:
        head, sep, why = value.partition(" - ")
    return head.strip().lower(), why.strip()


def talk_problems(lines: list[str]) -> list[tuple[int, str]]:
    """What `orkboard check` cannot read in a *Talk* part's lines (the raw lines, blanks allowed): `[(index, in words)]`; a part with no verdict line is told at index -1."""
    out: list[tuple[int, str]] = []
    seen: set[str] = set()
    for i, raw in enumerate(lines):
        ln = raw.strip()
        if not ln:
            continue
        m = _TALK_LINE.match(ln)
        if not m:
            out.append((i, f"this Talk line is none Orkboard can read (it is `- verdict: …`, `- stance: …`, `- for: …`, `- against: …`, `- instead: …` or `- assumes: … — shown by: …`): {ln[:80]!r}"))
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        seen.add(key)
        if key == "verdict":
            word = _verdict_of(value)[0]
            if word not in VERDICTS:
                out.append((i, f"the verdict {word!r} is not one Orkboard knows ({', '.join(VERDICTS)})"))
        elif key == "assumes" and not _assumes(value):
            out.append((i, f"this assumes line has no `— shown by: <signal>`: {ln[:80]!r}"))
    if "verdict" not in seen and not out:
        out.append((-1, "this Talk has no `- verdict:` line"))
    return out


def read_talk(page: idea_page.Page, party: str) -> dict | None:
    """The party's say: `{verdict, why, stance, for, against, instead, assumes: {text, signal} | None}`; None when its section has no *Talk* or no verdict Orkboard knows. A `doubt` or `no` with no why reads as `go`."""
    at = _section(page, party)
    body = part_text(page.sections[at][1], TALK) if at is not None else None
    if body is None:
        return None
    say: dict[str, Any] = {"verdict": "", "why": "", "stance": "", "for": "", "against": "", "instead": "", "assumes": None}
    for raw in body.split("\n"):
        m = _TALK_LINE.match(raw.strip())
        if not m:
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        if key == "verdict":
            word, why = _verdict_of(value)
            say["verdict"], say["why"] = word, _plain(why)
        elif key == "assumes":
            say["assumes"] = _assumes(value)
        else:
            say[key] = _plain(value)
    if say["verdict"] not in VERDICTS:
        return None
    if say["verdict"] != "go" and not say["why"]:
        say["verdict"] = "go"
    return say


def clean_talk(say: Any) -> dict | None:
    """A say strictly: a `verdict` of `VERDICTS` (a `doubt` or `no` with no `why` is `go`), each line at most `LINE_CHARS` on one line; None where it has no verdict."""
    if not isinstance(say, dict):
        return None
    verdict = _plain(say.get("verdict")).lower()
    if verdict not in VERDICTS:
        return None
    why = _plain(say.get("why"))
    if verdict != "go" and not why:
        verdict = "go"
    out: dict[str, Any] = {"verdict": verdict, "why": why}
    for key in ("stance", "for", "against", "instead"):
        out[key] = _plain(say.get(key))
    a = say.get("assumes")
    text, signal = (_plain(a.get("text")).replace(SHOWN.strip(), "-"), _plain(a.get("signal"))) if isinstance(a, dict) else ("", "")
    out["assumes"] = {"text": text, "signal": signal} if text and signal else None
    return out


def write_talk(page: idea_page.Page, party: str, say: Any) -> dict | None:
    """The party's *Talk* written into its section (the section made, in `spec_sections`' format, when the page has none; the part replaced when it has one; every other part and section kept byte
    for byte). Returns the say as written, None (and nothing written) where it has no verdict."""
    clean = clean_talk(say)
    if clean is None:
        return None
    lines = [f"- verdict: {clean['verdict']}" + (f"{DASH}{clean['why']}" if clean["why"] else "")]
    lines += [f"- {k}: {clean[k]}" for k in ("stance", "for", "against", "instead") if clean[k]]
    if clean["assumes"]:
        lines.append(f"- assumes: {clean['assumes']['text']}{SHOWN}{clean['assumes']['signal']}")
    _write(page, party, TALK, "\n".join(lines))
    return clean


# -- Accepted ------------------------------------------------------------------------------------------------------------------------------------

def _norm(line: str) -> str:
    return " ".join(spec_sections.bare(line).lower().split())[:LINE_CHARS]


def _dones(section: str) -> list[str]:
    return [_norm(x) for x in spec_sections.items(spec_sections.split(section).get("Done when", ""))]


def _split(text: str, dones: list[str]) -> tuple[str, str, bool]:
    """`(line, why, names a Done when line)` of an Accepted line's text: the why is what follows a dash, found where the line before it is one of the section's."""
    text = text.strip()
    if _norm(text) in dones:
        return text, "", True
    at = text.find(DASH)
    while at != -1:
        if _norm(text[:at]) in dones:
            return text[:at].strip(), text[at + len(DASH):].strip(), True
        at = text.find(DASH, at + 1)
    head, _sep, why = text.partition(DASH)
    return head.strip(), why.strip(), False


def accepted_problems(lines: list[str], done: list[str]) -> list[tuple[int, str]]:
    """What `orkboard check` cannot read in an *Accepted* part's lines, `done` the section's *Done when* lines: `[(index, in words)]`."""
    out: list[tuple[int, str]] = []
    dones = [_norm(x) for x in done]
    for i, raw in enumerate(lines):
        ln = raw.strip()
        if not ln:
            continue
        m = _ACCEPTED_LINE.match(ln)
        if not m:
            out.append((i, f"this Accepted line is none Orkboard can read (it is `- met: <line>`, `- not met: <line> — <why>` or `- cannot see: <line>`): {ln[:80]!r}"))
        elif not _split(m.group(2), dones)[2]:
            out.append((i, f"this Accepted line names no line of the section's Done when: {m.group(2).strip()[:80]!r}"))
    return out


def read_accepted(page: idea_page.Page, party: str) -> list[dict]:
    """The party's acceptance: `[{line, status: met|not met|cannot see, why}]`, in the order written; a line Orkboard cannot read is left out; [] where there is none."""
    at = _section(page, party)
    body = part_text(page.sections[at][1], ACCEPTED) if at is not None else None
    if body is None:
        return []
    dones = _dones(page.sections[at][1])
    out = []
    for raw in body.split("\n"):
        m = _ACCEPTED_LINE.match(raw.strip())
        if m:
            line, why, _named = _split(m.group(2), dones)
            if line:
                out.append({"line": _plain(line), "status": m.group(1).lower(), "why": _plain(why)})
    return out


def write_accepted(page: idea_page.Page, party: str, lines: Any) -> list[dict]:
    """The party's *Accepted* written into its section (the part replaced, every other byte kept; the section made when there is none). `lines`: `[{line, status, why}]`; a line with no text or a
    status that is none of `STATUSES` is left out, a `[test]` mark on a line is dropped. Returns the lines written; nothing is written where none is left."""
    kept: list[dict] = []
    for x in lines if isinstance(lines, (list, tuple)) else []:
        if not isinstance(x, dict):
            continue
        status, line = _plain(x.get("status")).lower(), _plain(spec_sections.bare(_plain(x.get("line"))))
        if status in STATUSES and line and len(kept) < MAX_ACCEPTED:
            kept.append({"line": line, "status": status, "why": _plain(x.get("why"))})
    if not kept:
        return []
    _write(page, party, ACCEPTED, "\n".join(f"- {k['status']}: {k['line']}" + (f"{DASH}{k['why']}" if k["why"] else "") for k in kept))
    return kept
