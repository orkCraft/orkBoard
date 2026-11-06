"""`orkboard check`: what is wrong in the Board's files of a checkout, in words (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part E.2, E.3; decisions §255.9).

    board_check.wiki_of(root)       # the Board's folder from the checkout, with no app: "llm-wiki/general"; ValueError (in words) when it cannot tell
    board_check.run(root)           # [{path, line, what}] for every fault of E.2; [] for a clean Board (`line` 0 when the fault is a whole file's)
    board_check.say(finding)        # "<path>:<line>: <what>"
    board_check.workflow(wiki)      # the text of .github/workflows/orkboard-check.yml (E.3)
    board_check.write_workflow(root, wiki)   # …written; False when the person's own file is there

The faults: a page Orkboard cannot read; a phase it does not know; a `done` with no green gate record; a `phase` that skips one without its sections (a `spec` with no *Done when*, a `work` with no
stages); a secret's shape in the Board's files (`plumbing.scrub`, never echoed); a rules block or an Orkboard file whose hash is not the package's, or whose schema is older; a journal line of
an unknown kind (`read_in.outside`). Pure reading: nothing is written, nothing committed, no app and no model, and a clone with no `.orkcraft/` is read as well as any.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from orkboard.realm import agent_rules, agent_rules_text as T, goal_phase, idea_page, living_specs, page_talk, plumbing, read_in, spec_sections

DEFAULT_WIKI = "llm-wiki/general"
WORKFLOW = ".github/workflows/orkboard-check.yml"
STAMP = "# Written by Orkboard (orkboard init --ci)."
INIT = f"run {T.RUN} init"
GREEN = re.compile(r"^[0-9a-f]{4,40}\s*·\s*\d+\s+files?\s*·\s*green$")        # `goal_phase.gate_of`'s line
_NAMED = re.compile(r"the goals `([^`\n]*?)/?pages/ideas/<slug>\.md`")
_SKIP = ("index.md", "CLAUDE.md", "AGENTS.md", "BOARD.md")
_FENCE_OPEN = re.compile(r"\A---\r?\n")
_FENCE_CLOSED = re.compile(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", re.S)

WORDS = {agent_rules.MISSING: "is missing: {init}",
         agent_rules.OUTDATED: "is not the text this Orkboard writes: {init}",
         agent_rules.CHANGED: "was changed by hand, so its hash is not its text's: {init} to write Orkboard's own back",
         agent_rules.BROKEN: "has Orkboard's begin marker with no end: {init}",
         agent_rules.NOT_OURS: "stands at an Orkboard path but carries no Orkboard stamp (it is left as the person's own)"}
OLD_SCHEMA = "The Board's rules are v{had}, this Orkboard writes v{now}: {init}"
NO_RULES = "The Board's rules are not written in this project: {init}"
MANY = "More than one folder holds a Board ({found}) and the root AGENTS.md block names none of them"


# -- where the Board is --------------------------------------------------------------------------------------------------------------

def _wiki_clean(rel: object) -> str | None:
    """A folder from the project's root as `agent_rules` wants it: no `..`, not absolute; "" for the root itself; None for anything else."""
    if not isinstance(rel, str):
        return None
    rel = rel.strip().strip("/")
    if rel in (".", ""):
        return "" if rel == "." else None
    return None if ".." in Path(rel).parts or Path(rel).is_absolute() or "\\" in rel else rel


def _named(root: Path) -> str | None:
    """The Board's folder the root `AGENTS.md` block names (*the goals `<wiki>/pages/ideas/<slug>.md`*)."""
    try:
        text = (root / agent_rules.AGENTS).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    block = agent_rules.find_block(text)
    got = _NAMED.search(block[4]) if block else None
    return _wiki_clean(got.group(1)) if got else None


def _own(root: Path) -> str | None:
    """The `wiki` the project's Board settings name (`.orkcraft/board.json`, the app's own choice), when the checkout has that file."""
    try:
        data = json.loads((root / ".orkcraft" / "board.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _wiki_clean(data.get("wiki")) if isinstance(data, dict) else None


def _found(root: Path) -> list[str]:
    """The folders that hold a Board's pages, as the Board's tree looks for them (`llm-wiki/*/pages/…`, `*/pages/…`, `pages/…`)."""
    out = set()
    for pat in ("llm-wiki/*/pages/ideas", "llm-wiki/*/pages/tracks", "*/pages/ideas", "*/pages/tracks", "pages/ideas", "pages/tracks"):
        out |= {p.parent.parent.relative_to(root).as_posix() for p in root.glob(pat) if p.is_dir()}
    return sorted("" if x == "." else x for x in out)


def wiki_of(root: Path) -> str:
    """Where the Board is, from the checkout alone, as the app finds it: the project's own `wiki` setting, else the folder the root `AGENTS.md` names, else the one folder that holds
    pages, else `llm-wiki/general`. ValueError in words when more than one holds pages and the block names none."""
    root = Path(root)
    own = _own(root)
    if own is not None:
        return own
    named = _named(root)
    if named is not None:
        return named
    found = _found(root)
    if len(found) > 1:
        raise ValueError(MANY.format(found=", ".join(found)))
    return found[0] if found else DEFAULT_WIKI


# -- the findings --------------------------------------------------------------------------------------------------------------------

def _f(path: str, line: int, what: str) -> dict:
    return {"path": path, "line": line, "what": what}


def say(finding: dict) -> str:
    """One finding as a line: `path:line: what`, `path: what` for a whole file's."""
    return f"{finding['path']}{':' + str(finding['line']) if finding.get('line') else ''}: {finding['what']}"


def _line_of(text: str, key: str) -> int:
    """The line (from 1) of a front matter key; 1 where it is not there."""
    for n, ln in enumerate(text.splitlines(), 1):
        if ln.startswith(f"{key}:"):
            return n
        if n > 1 and ln.strip() == "---":
            break
    return 1


def has_done_when(page: idea_page.Page, root: Path) -> bool:
    if page.section("Done when").strip() or any(spec_sections.split(t).get("Done when", "").strip() for _n, t in spec_sections.sections_of(page)):
        return True
    return bool(re.search(r"^#{1,3}\s+Done when\b", _spec_file(page, root), re.M | re.I))


def has_stages(page: idea_page.Page, root: Path) -> bool:
    if page.section("Stages").strip() or any(spec_sections.split(t).get("Plan", "").strip() for _n, t in spec_sections.sections_of(page)):
        return True
    return bool(_spec_file(page, root).strip())          # a goal whose spec is a file of its own: the spec's parts are its stages (spec 151 H.1)


def _spec_file(page: idea_page.Page, root: Path) -> str:
    rel = page.get("spec").strip()
    if not rel or ".." in Path(rel).parts or Path(rel).is_absolute():
        return ""
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# -- an answer by a reference (decisions §259) ---------------------------------------------------------------------------------------------

REFERENCE = re.compile(r"^(?:§(\d+)(?:\.\d+[a-z]?)*|spec (\d+[a-z]?)(?: [A-Z]\d?(?:\.\d+)?)?)$")
_DECIDED = re.compile(r"\(decided by ([^(),]+),\s*\d{4}-\d{2}-\d{2}\)\s*$")


def reference_exists(root: Path, ref: str) -> bool:
    """Whether `ref` names a decision of the project's log (`§258`, `§258.7`: its `## 258.` heading, or an ADR file numbered 258) or one of its specs (`spec 154`,
    `spec 154 C.1`: a file `<n>-*.md` in `docs/specs/` or a `specs/` folder at the top). A part's letter or a point's number is not looked up: the decision or the spec is."""
    m = REFERENCE.match(" ".join(str(ref or "").split()))
    if not m:
        return False
    root = Path(root)
    if m.group(1):
        try:
            place = root / agent_rules.decisions_of(root)
        except (OSError, ValueError):
            return False
        n = int(m.group(1))
        if place.is_dir():
            return any(re.match(rf"0*{n}-", p.name) for p in place.glob("*.md"))
        try:
            return re.search(rf"^## {n}\.", place.read_text(encoding="utf-8"), re.M) is not None
        except (OSError, UnicodeDecodeError):
            return False
    n = m.group(2)
    return any(any(base.glob(f"{n}-*.md")) for base in (root / "docs" / "specs", root / "specs", *root.glob("*/specs")) if base.is_dir())


def _decided(root: Path, rel: str, text: str, page: idea_page.Page, out: list[dict]) -> None:
    """An answer under *Open questions* said decided by a reference (`(decided by §258.7, 2026-11-06)`) must name one the project holds."""
    for ln in page.section("Open questions").splitlines():
        m = idea_page.ANSWERED.match(ln)
        d = _DECIDED.search(m.group(1)) if m else None
        if d and not reference_exists(root, d.group(1).strip()):
            out.append(_f(rel, _line_of(text, ln.strip()), f"the answer is decided by {d.group(1).strip()}, which this project's decisions and specs do not hold"))


def _page(root: Path, rel: str, path: Path, out: list[dict]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        out.append(_f(rel, 0, "this page cannot be read as text"))
        return
    if _FENCE_OPEN.match(text) and not _FENCE_CLOSED.match(text):
        out.append(_f(rel, 1, "its front matter is not closed with a second ---"))
        return
    page = idea_page.parse(text)
    word = page.get("phase").strip()
    schema = page.get("schema").strip()
    if schema.isdigit() and int(schema) < int(goal_phase.SCHEMA_FLOOR):
        out.append(_f(rel, _line_of(text, "schema"), f"this page is schema {schema}, this Orkboard writes {goal_phase.SCHEMA}: open the Board once with this Orkboard"))
    _talk(rel, text, page, out)
    _decided(root, rel, text, page, out)
    if not word:
        return                                           # a page of before this spec: it has no phase to be wrong
    line = _line_of(text, "phase")
    if word.lower() not in goal_phase.PHASES:
        out.append(_f(rel, line, f"the phase {word!r} is not one Orkboard knows ({', '.join(goal_phase.PHASES)})"))
        return
    phase = word.lower()
    history = page.get("laid") == "history"           # a goal laid from the project's history (spec 151 H.1): its spec was written, and done, before the Board's format
    if phase == "done" and not GREEN.match(page.get("gate").strip()) and not history:
        out.append(_f(rel, _line_of(text, "gate") if page.get("gate") else line, "the phase is done but the page has no green gate record (gate: <short commit> · <n> files · green)"))
    if phase in ("spec", "work", "done") and not has_done_when(page, root) and not history:
        out.append(_f(rel, line, f"the phase is {phase} but the page has no *Done when*"))
    if phase in ("work", "done") and not has_stages(page, root):
        out.append(_f(rel, line, f"the phase is {phase} but the page has no stages (*Stages*, or *Plan* in a party's section)"))


_H2 = re.compile(r"^##[ \t]+(.*?)[ \t]*#*[ \t]*$")
_H3 = re.compile(r"^###[ \t]+(.+?)[ \t]*#*[ \t]*$")


def _talk(rel: str, text: str, page: idea_page.Page, out: list[dict]) -> None:
    """A `### Talk` or `### Accepted` Orkboard cannot read, a verdict it does not know, an `Accepted` line that names no line of the section's *Done when* (spec 154 B.5)."""
    lines = text.replace("\r\n", "\n").split("\n")
    heading, part, first = "", "", 0
    for n, ln in enumerate([*lines, "## "]):
        m2, m3 = _H2.match(ln), _H3.match(ln)
        if not (m2 or m3):
            continue
        if part:
            body = lines[first + 1:n]
            if part == page_talk.TALK.lower():
                found = page_talk.talk_problems(body)
            else:
                section = next((t for h, t in page.sections if h == heading), "")
                found = page_talk.accepted_problems(body, spec_sections.items(spec_sections.split(section).get("Done when", "")))
            out.extend(_f(rel, first + 2 + i if i >= 0 else first + 1, what) for i, what in found)
        part = ""
        if m2:
            heading = m2.group(1).strip()
        elif m3.group(1).strip().lower() in (page_talk.TALK.lower(), page_talk.ACCEPTED.lower()):
            part, first = m3.group(1).strip().lower(), n


def _secrets(root: Path, wiki: str, out: list[dict]) -> None:
    base = root / wiki if wiki else root
    files = [*sorted((base / "pages").glob("**/*.md")), *sorted((base / "journals").glob("*.md")), base / "project.md"]
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, ln in enumerate(text.splitlines(), 1):
            if plumbing.scrub(ln)[1]:
                out.append(_f(path.relative_to(root).as_posix(), n, "this line has a secret's shape; take it out of the Board (its history keeps it until it is rewritten)"))


def _rules(root: Path, wiki: str, out: list[dict]) -> None:
    decisions = agent_rules.decisions_of(root)
    found = agent_rules.check(root, wiki, decisions=decisions)
    if not agent_rules.has_rules(root) and found and all(f["what"] == agent_rules.MISSING for f in found):
        out.append(_f(agent_rules.AGENTS, 0, NO_RULES.format(init=INIT)))
        return
    for f in found:
        had = _schema_of(root / f["path"]) if f["what"] == agent_rules.OUTDATED else None
        what = OLD_SCHEMA.format(had=had, now=T.SCHEMA, init=INIT) if had is not None and had < T.SCHEMA else f"Orkboard's {'block' if f['path'].endswith(('AGENTS.md', 'CLAUDE.md')) else 'file'} " + WORDS[f["what"]].format(init=INIT)
        out.append(_f(f["path"], 0, what))


def _schema_of(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = T.BEGIN_RE.search(text) or T.FILE_RE.search(text) or agent_rules.SCHEMA_LINE.search(text)
    return int(m.group(1)) if m else None


def _journals(root: Path, wiki: str, out: list[dict]) -> None:
    folder = root / wiki if wiki else root
    if not (folder / "journals").is_dir():
        return
    try:
        left = read_in.outside(folder, root / ".orkcraft")[1]          # a clone has no `.orkcraft/`: the lines are read all the same
    except (OSError, ValueError):
        return
    for row in left:
        rel = f"{wiki + '/' if wiki else ''}{row['path']}"
        try:
            lines = (root / rel).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            lines = []
        n = next((i for i, ln in enumerate(lines, 1) if row["text"][:40] in ln and row["kind"] in ln), 0)
        out.append(_f(rel, n, f"a journal line of the kind {row['kind']!r}, which the {row['scope']} journal does not take; Orkboard leaves the line where it is"))


def run(root: Path) -> list[dict]:
    """Every fault of the Board in the checkout `root`, `[{path, line, what}]` in the order of the path and the line. ValueError (in words) when the Board's folder cannot be told."""
    root = Path(root)
    wiki = wiki_of(root)
    out: list[dict] = []
    base = root / wiki if wiki else root
    for sub in ("ideas", "tracks"):
        folder = base / "pages" / sub
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            if path.name in _SKIP or path.name.startswith("."):
                continue
            rel = path.relative_to(root).as_posix()
            if not re.fullmatch(r"[a-z0-9-]+", path.stem):
                what = "a goal's" if sub == "ideas" else "a party's"
                out.append(_f(rel, 0, f"`{path.name}`: {what} file name is its slug: rename it `{living_specs.slug(path.stem) or 'a-slug'}.md`"))
            _page(root, rel, path, out)
    _secrets(root, wiki, out)
    _rules(root, wiki, out)
    _journals(root, wiki, out)
    return sorted(out, key=lambda f: (f["path"], f["line"], f["what"]))


# -- the CI step (E.3) ---------------------------------------------------------------------------------------------------------------

def workflow(wiki: str) -> str:
    """`.github/workflows/orkboard-check.yml`: on a pull request that touches the Board's folder, `AGENTS.md` or `CLAUDE.md`, Orkboard's `check` run from git (`agent_rules_text.RUN`). It has no `push` trigger, so a Board commit
    starts nothing; the project's own tests stay its own CI's."""
    folder = f"{wiki.strip('/')}/**" if wiki.strip("/") else "pages/**"
    return f"""{STAMP}
# Checks the Board on each pull request; your tests stay your CI's.
name: Orkboard check

on:
  pull_request:
    paths:
      - "{folder}"
      - "AGENTS.md"
      - "CLAUDE.md"

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: {T.RUN} check
"""


def write_workflow(root: Path, wiki: str) -> bool:
    """The workflow written into the working tree (never committed). False when a file of the same name that Orkboard did not write is there: it is the person's and stays."""
    path = Path(root) / WORKFLOW
    try:
        old = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        old = None
    if old is not None and not old.startswith(STAMP):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(workflow(wiki), encoding="utf-8")
    return True
