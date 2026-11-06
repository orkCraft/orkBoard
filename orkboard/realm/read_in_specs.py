"""A folder of numbered specs read in as goals (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part H.1; a shape of `read_in`, spec 126 B), for any project.

    goals_from_specs(root, folder, wiki_rel, done_through=None, parts=PARTS, log=None)   # [{slug, title, phase, stages, decisions, spec, party, exists}], nothing written
    lay(root, wiki_rel, planned, party="tech")                                             # the pages that are not there yet, written; the slugs written
    line(planned_page), counts(planned)                                                    # the dry run's words

Each `<folder>/<n>-<slug>.md` (`<n>` a number, a letter after it allowed: `29a`) is one goal whose page is `<wiki>/pages/ideas/<the file's stem>.md`. Its stages are the rows of the spec's first table
that has any, whose first cell is `**<id>. <name>**` (`E1`); a part is built when a commit's subject starts `Spec <n> <id>:`. A spec with no such table is one stage. Reading is files and
`git log`; `lay` never writes over a page that is there and never commits. No face, no model.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orkboard.realm import goal_phase, ideas
from orkboard.realm.idea_page import Page
from orkboard.realm.idea_words import short_of

PARTS = r"^Spec {n} {id}:"                      # this repository's way: a commit `Spec 150 E2: …` built part E2 of spec 150 (`{n}` and `{id}` are filled in)
ONE = r"^Spec {n}(?::| )"                       # a spec of no parts: a commit `Spec 7: …` or `Spec 7 …`
PARTY = "tech"
_FILE = re.compile(r"^(\d+)([a-z]?)-(.+)\.md$")
_HEAD = re.compile(r"^#[ \t]+(?:(\d+[a-z]?)\.[ \t]+)?(.+?)[ \t]*$")
_ROW = re.compile(r"^\|[ \t]*\*\*([A-Z]\d?)\.[ \t]+(.+?)\*\*[ \t]*\|")
_DECISION = re.compile(r"§(\d+)")
TITLE_CHARS = 120


def commits(root: Path) -> list[str]:
    """Every commit's subject (`git log --format=%s`), read once; [] where there is no git history."""
    done = subprocess.run(["git", "log", "--format=%s"], cwd=root, capture_output=True, text=True)
    return done.stdout.splitlines() if done.returncode == 0 else []


def _title(heading: str) -> str:
    """The heading without its number, cut where its subtitle starts (`Title: what it builds`, `Title; and more`)."""
    head = re.split(r": |; ", heading, maxsplit=1)[0]
    title = head if len(head) >= 3 else heading
    return title if len(title) <= TITLE_CHARS else title[:TITLE_CHARS - 1].rsplit(" ", 1)[0]


def _read(path: Path) -> tuple[str, list[tuple[str, str]], list[int]]:
    """(title, the first table with parts as (id, name), the decisions named on the line under the heading)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        lines = []
    heading = next((ln for ln in lines if ln.strip()), "")
    m = _HEAD.match(heading)
    title = _title(m.group(2)) if m else ""
    if not title:
        title = _title(re.sub(r"^\d+[a-z]?-", "", path.stem).replace("-", " ")).capitalize()
    after = next((ln for ln in lines[1:] if ln.strip()), "")
    decisions: list[int] = []
    if after.startswith("Decisions"):
        for n in _DECISION.findall(after.split("**", 1)[0]):
            if int(n) not in decisions:
                decisions.append(int(n))
    parts: list[tuple[str, str]] = []
    for ln in lines[1:]:
        if ln.lstrip().startswith("|"):
            row = _ROW.match(ln.strip())
            if row:
                parts.append((row.group(1), " ".join(row.group(2).replace("*", "").split())))
        elif parts:
            break                                                # the first table that has parts ends here
    return title, parts, decisions


def goals_from_specs(root: Path, folder: str, wiki_rel: str, done_through: int | None = None, parts: str | None = PARTS,
                     log: list[str] | None = None, party: str = PARTY) -> list[dict]:
    """The pages that would be laid for the specs in `root/folder`, in the specs' order: `{slug, title, phase, stages: [(id, name, built)], decisions, spec, party, exists}`. `parts` is the
    pattern of a part's commit subject (`{n}` the spec's number, `{id}` the part's), None for a project whose commits say nothing; `log` the subjects (else `git log` of `root`, read once)."""
    root = Path(root)
    folder = folder.strip("/")
    subjects = commits(root) if log is None else list(log)
    files = [(int(m.group(1)), m.group(2), p) for p in (root / folder).glob("*.md") if (m := _FILE.match(p.name))]
    out = []
    for n, letter, path in sorted(files, key=lambda f: f[:2]):
        title, found, decisions = _read(path)

        def built(pattern: str) -> bool:
            return any(re.match(pattern, s) for s in subjects)

        number = re.escape(f"{n}{letter}")
        if found:
            stages = [(i, name, bool(parts) and built(parts.format(n=number, id=i))) for i, name in found]
        else:
            stages = [("", title, bool(parts) and built(ONE.format(n=number)))]
        if done_through is not None and n <= done_through:
            phase, stages = "done", [(i, name, True) for i, name, _b in stages]
        else:
            nb = sum(1 for _i, _n, b in stages if b)
            phase = "done" if nb == len(stages) else "work" if nb else "spec"
        out.append({"slug": path.stem, "title": title, "phase": phase, "stages": stages, "decisions": decisions,
                    "spec": f"{folder}/{path.name}" if folder not in ("", ".") else path.name, "party": party,
                    "exists": (root / wiki_rel / ideas.IDEAS / f"{path.stem}.md").exists()})
    return out


def _stage_line(stage: tuple[str, str, bool]) -> str:
    i, name, built = stage
    return f"- [{'x' if built else ' '}] {i + '. ' if i else ''}{name}"


def lay(root: Path, wiki_rel: str, planned: list[dict], party: str = PARTY) -> list[str]:
    """The planned pages written into `<root>/<wiki_rel>/pages/ideas/<stem>.md`, those that are not there already (never written over); the slugs written. Nothing is committed."""
    wiki = Path(root) / wiki_rel if wiki_rel else Path(root)
    todo = [p for p in planned if not (wiki / ideas.IDEAS / f"{p['slug']}.md").exists()]
    if not todo:
        return []
    written = []
    with ideas.LOCK:
        known = {t["slug"]: t for t in ideas.tracks(wiki)}
        for p in todo:
            track = p.get("party") or party
            if track not in known:
                track = ideas.add_track(wiki, track.replace("-", " ").title())
                known = {t["slug"]: t for t in ideas.tracks(wiki, make=False)}
            order = max((i["order"] for i in ideas.ideas(wiki, track)), default=0) + 1
            page = Page([("owner", ideas.OWNER), ("kind", "idea"), ("track", track), ("order", str(order)), ("size", ""),
                         ("priority", known[track]["priority"]), ("short", short_of(p["title"])), ("phase", p["phase"]), ("spec", p["spec"]),
                         ("decisions", ", ".join(str(d) for d in p["decisions"])), ("by", goal_phase.PERSON), ("schema", goal_phase.SCHEMA)],
                        p["title"], "", [("Gist", p["title"]), ("Stages", "\n".join(_stage_line(s) for s in p["stages"]))])
            ideas._write(wiki / ideas.IDEAS / f"{p['slug']}.md", page.text())
            written.append(p["slug"])
        ideas._reindex(wiki)
    return written


def line(p: dict) -> str:
    """One planned page as the dry run says it: `151 · The Board in the repository for any AI tool · spec · 0/8 parts · tech`."""
    n = re.match(r"\d+[a-z]?", p["slug"]).group(0)                  # type: ignore[union-attr]
    done = sum(1 for _i, _n, b in p["stages"] if b)
    return f"{n} · {p['title']} · {p['phase']} · {done}/{len(p['stages'])} parts · {p['party']}" + (" · laid already" if p["exists"] else "")


def counts(planned: list[dict]) -> str:
    laid = sum(1 for p in planned if p["exists"])
    by = {ph: sum(1 for p in planned if p["phase"] == ph) for ph in ("done", "work", "spec")}
    return f"{len(planned)} goals: {by['done']} done, {by['work']} work, {by['spec']} spec; {laid} already laid"
