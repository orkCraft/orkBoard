"""The living specs (docs/specs/127-the-fields-best-in-our-formats.md §C; decisions §205): what the product does now, kept a capability a file, in OpenSpec's shape with front matter,
folded from the goals that reached main (`core/idea_fold.py`) and read by the leaders. No model, no face.

    living_specs.read(board, cap)                       # {capability, title, purpose, parties, goals, updated, requirements: [{name, text, scenarios: [{name, when, then}]}]} or None
    living_specs.list_(board)                           # [{capability, title, purpose, parties, requirements: [names]}], by capability
    living_specs.render(spec)                           # the file's text
    living_specs.apply(board, cap, delta, goal, party, title="", purpose="")   # the spec after OpenSpec's archive semantics; written
    living_specs.text(board, party, chars=2500)         # *How the product works now*: every capability one line, then the party's capabilities' requirements
    living_specs.slug(text)                             # a capability's slug: `[a-z0-9-]`, 60 at most

`board` is the Board's pages root (where `pages/tracks` and `pages/ideas` are), so the specs, `<board>/specs/<capability>.md`, are committed with the Board's pages (`realm/idea_git.py`
`BoardTree.pages`). A file is:

    ---
    capability: Sign-in
    parties: [design, tech]
    goals: [add-lobby, magic-link]
    updated: 2026-11-01
    ---

    # Sign-in

    ## Purpose

    How a player gets into a game.

    ## Requirements

    ### Requirement: Magic link

    The product SHALL send a link that signs the player in.

    #### Scenario: A link is asked for

    - **WHEN** a player types their address and presses Send
    - **THEN** a link arrives within a minute

**OpenSpec's archive semantics** (`apply`): the delta's `removed` drops a requirement by its name, `modified` replaces the requirement of that name whole (one not there is added), `added`
appends (a name already there is *modified*, in its place); a name is compared without case or extra spaces. A file is the person's too: what is read is what is there, front matter or none.
"""
from __future__ import annotations

import datetime as dt
import re
import threading
from pathlib import Path

from orkboard.realm import doc_formats

DIR = "specs"
SLUG_CHARS = 60
LINE_CHARS = 300
TEXT_CHARS = 2500                  # what a leader's call is given of the specs
LOCK = threading.RLock()           # every write of a spec, from the keeper's thread or the importer's
_SLUG = re.compile(r"[a-z0-9-]+")
_HEAD = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
_REQ = re.compile(r"^Requirement[ \t]*:[ \t]*(.*)$", re.I)
_SCENARIO = re.compile(r"^Scenario[ \t]*:[ \t]*(.*)$", re.I)
_STEP = re.compile(r"^\s*[-*+]\s+\**(WHEN|THEN|AND|GIVEN)\**[ \t]*:?[ \t]*(.*)$", re.I)


def slug(text: object) -> str:
    """A capability's slug: its words lower case joined by `-`, `[a-z0-9-]` and 60 at most; "" for words with none."""
    return re.sub(r"[^a-z0-9]+", "-", " ".join(str(text or "").split()).lower()).strip("-")[:SLUG_CHARS].strip("-")


def _words(v: object, n: int = LINE_CHARS) -> str:
    return " ".join(str(v or "").split())[:n]


def _title(v: object) -> str:
    """A title on one line that front matter keeps whole: no `#`, quote or bracket."""
    return " ".join(re.sub(r"[#\"\[\]]", " ", str(v or "")).split())[:120]


def _same(a: str, b: str) -> bool:
    return _words(a, 400).lower() == _words(b, 400).lower()


def _file(board: Path, cap: str) -> Path | None:
    return Path(board) / DIR / f"{cap}.md" if _SLUG.fullmatch(cap or "") and len(cap) <= SLUG_CHARS else None


def _list(v: object) -> list[str]:
    got = v if isinstance(v, list) else [v] if v else []
    return [s for s in dict.fromkeys(str(x).strip() for x in got) if _SLUG.fullmatch(s)]


# -- reading ---------------------------------------------------------------------------------------------------------------------------------

def parse(text: str, cap: str = "") -> dict | None:
    """A spec file's text as a spec; None for a text that is no spec (no front matter with a `capability` and no *Requirements* section). `cap`: its capability (the file's name)."""
    meta, rest = doc_formats.front_matter(text)
    title, purpose, reqs, section = "", [], [], ""
    cur: dict | None = None
    scenario: dict | None = None
    last = ""
    fenced = has_reqs = False
    for raw in rest.replace("\r\n", "\n").split("\n"):
        if raw.lstrip().startswith("```"):
            fenced = not fenced
        m = None if fenced else _HEAD.match(raw)
        if m:
            level, head = len(m.group(1)), m.group(2).strip()
            if level == 1 and not title:
                title = _words(head, 120)
                continue
            if level == 2:
                section, cur, scenario = head.lower(), None, None
                has_reqs = has_reqs or section == "requirements"
                continue
            if section == "requirements" and level == 3:
                r = _REQ.match(head)
                cur = {"name": _words(r.group(1) if r else head), "text": [], "scenarios": []}
                reqs.append(cur)
                scenario = None
                continue
            if cur is not None and level == 4 and (s := _SCENARIO.match(head)):
                scenario = {"name": _words(s.group(1)), "when": "", "then": ""}
                cur["scenarios"].append(scenario)
                last = ""
                continue
        if section == "purpose":
            purpose.append(raw)
        elif cur is not None and scenario is not None:
            if step := _STEP.match(raw):
                word = step.group(1).lower()
                key = {"when": "when", "given": "when", "then": "then"}.get(word, last or "then")
                last = key
                scenario[key] = _words(f"{scenario[key]} {'and ' if word == 'and' and scenario[key] else ''}{step.group(2)}")
        elif cur is not None:
            cur["text"].append(raw)
    if not meta.get("capability") and not has_reqs:
        return None
    capability = cap or slug(meta.get("capability") or title)
    cap_title = _title(title or (meta.get("capability") if isinstance(meta.get("capability"), str) else "") or capability)
    return {"capability": capability, "title": cap_title, "purpose": _words("\n".join(purpose), 600), "parties": _list(meta.get("parties")),
            "goals": _list(meta.get("goals")), "updated": _words(meta.get("updated"), 20),
            "requirements": [{"name": r["name"], "text": "\n".join(r["text"]).strip(), "scenarios": [s for s in r["scenarios"] if s["name"] or s["when"] or s["then"]]}
                             for r in reqs if r["name"]]}


def read(board: Path, cap: str) -> dict | None:
    """The spec of a capability, or None (a capability that is none, no file, a file that cannot be read or is no spec)."""
    file = _file(board, cap)
    if file is None or file.is_symlink():
        return None
    try:
        return parse(file.read_text("utf-8", errors="replace"), cap)
    except OSError:
        return None


def list_(board: Path) -> list[dict]:
    """The capabilities the product has, by their names: `[{capability, title, purpose, parties, requirements: [names]}]`."""
    folder = Path(board) / DIR
    try:
        names = sorted(p.stem for p in folder.glob("*.md") if p.is_file() and not p.is_symlink() and _file(board, p.stem) is not None)
    except OSError:
        return []
    out = []
    for cap in names:
        spec = read(board, cap)
        if spec is not None:
            out.append({"capability": cap, "title": spec["title"], "purpose": spec["purpose"], "parties": spec["parties"], "requirements": [r["name"] for r in spec["requirements"]]})
    return out


# -- rendering and writing -------------------------------------------------------------------------------------------------------------------

def render(spec: dict) -> str:
    """A spec as its file's text (the module's docstring has the shape)."""
    title = _title(spec.get("title")) or _title(spec.get("capability")) or "Capability"
    head = ["---", f"capability: {title}", f"parties: [{', '.join(_list(spec.get('parties')))}]", f"goals: [{', '.join(_list(spec.get('goals')))}]",
            f"updated: {_words(spec.get('updated'), 20) or dt.date.today().isoformat()}", "---", "", f"# {title}", "", "## Purpose", "", _words(spec.get("purpose"), 600), "",
            "## Requirements"]
    for r in spec.get("requirements") or []:
        head += ["", f"### Requirement: {_words(r['name'])}", "", str(r.get("text") or "").strip()]
        for s in r.get("scenarios") or []:
            head += ["", f"#### Scenario: {_words(s.get('name'))}", "", f"- **WHEN** {_words(s.get('when'))}", f"- **THEN** {_words(s.get('then'))}"]
    return "\n".join(head).rstrip() + "\n"


def write(board: Path, spec: dict) -> Path:
    """The spec kept whole (the folder made); ValueError for a capability that is no slug."""
    file = _file(board, spec.get("capability") or "")
    if file is None:
        raise ValueError(f"{spec.get('capability')!r} is no capability's name")
    with LOCK:
        file.parent.mkdir(parents=True, exist_ok=True)
        tmp = file.with_name(f".{file.name}.tmp")
        tmp.write_text(render(spec), "utf-8")
        tmp.replace(file)
    return file


def _req(r: dict) -> dict:
    return {"name": _words(r.get("name")), "text": str(r.get("text") or "").strip(),
            "scenarios": [{"name": _words(s.get("name")), "when": _words(s.get("when")), "then": _words(s.get("then"))} for s in r.get("scenarios") or [] if isinstance(s, dict)]}


def apply(board: Path, cap: str, delta: dict, goal: str, party: str, title: str = "", purpose: str = "") -> dict:
    """The capability's spec after a goal's delta (OpenSpec's archive semantics: the module's docstring), written. `delta`: `{added: [requirement], modified: [requirement], removed: [name]}`.
    `title` and `purpose` are for a capability that has none yet (a title or purpose it has is kept, a missing one filled). The goal and the party join the spec's; `updated` is today. A new
    capability that ends with no requirement is not written. ValueError for a capability that is no slug."""
    if _file(board, cap) is None:
        raise ValueError(f"{cap!r} is no capability's name")
    with LOCK:
        spec = read(board, cap) or {"capability": cap, "title": "", "purpose": "", "parties": [], "goals": [], "updated": "", "requirements": []}
        existed = bool(spec["requirements"]) or (_file(board, cap).is_file())
        reqs = [dict(r) for r in spec["requirements"]]
        for name in (delta or {}).get("removed") or []:
            reqs = [r for r in reqs if not _same(r["name"], str(name))]
        for r in [*((delta or {}).get("modified") or []), *((delta or {}).get("added") or [])]:      # a name there is replaced in its place; a name not there is appended
            r = _req(r)
            at = next((i for i, x in enumerate(reqs) if _same(x["name"], r["name"])), None)
            if at is None:
                reqs.append(r)
            else:
                reqs[at] = r
        spec.update(requirements=reqs, updated=dt.date.today().isoformat(), title=spec["title"] or _title(title) or _title(cap.replace("-", " ").capitalize()),
                    purpose=spec["purpose"] or _words(purpose, 600), goals=_list([*spec["goals"], goal]), parties=_list([*spec["parties"], party]))
        if reqs or existed:
            write(board, spec)
        return spec


# -- what a call is given ---------------------------------------------------------------------------------------------------------------------

def _block(spec: dict) -> str:
    lines = [f"{spec['title']}:"]
    for r in spec["requirements"]:
        lines.append(f"- {r['name']}: {_words(r['text'], 400)}")
        lines += [f"  - WHEN {s['when']} THEN {s['then']}" for s in r["scenarios"]]
    return "\n".join(lines)


def text(board: Path, party: str, chars: int = TEXT_CHARS) -> str:
    """*How the product works now* for a party's leader, `chars` at most: every capability on one line (`Title: purpose`), then the requirements (with their scenarios) of the capabilities that
    party's goals reached, the latest updated first. "" where the product has no spec."""
    rows = list_(board)
    if not rows:
        return ""
    index = "\n".join(f"- {r['title']}: {r['purpose']}" if r["purpose"] else f"- {r['title']}" for r in rows)
    out, used = index[:chars], len(index) + 2
    mine = [s for s in (read(board, r["capability"]) for r in rows if party and party in r["parties"]) if s is not None]
    for spec in sorted(mine, key=lambda s: (s["updated"], s["capability"]), reverse=True):
        block = _block(spec)
        if used + len(block) + 2 > chars:
            left = chars - used - 2
            if left > 80:
                out += "\n\n" + block[:left - 1].rstrip() + "…"
            break
        out += "\n\n" + block
        used += len(block) + 2
    return out
