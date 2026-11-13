"""The project's LLM wiki: the folder the Board's pages live in (`pages/ideas/`, `pages/tracks/`), with its rules.

A wiki is one topic: `codebase` (modules, flows, decisions of the code), `team` (people and ownership, processes,
product, decisions), `design` or `general`. Each lives in its own folder (default `llm-wiki/<topic>/`) with its own
rules:

    WIKI.md            the schema: sections, kinds of pages, front matter, links, conflicts
    index.md           the map: every section with one line and its key pages (agents read it first)
    pages/<section>/   the pages; each section has its own index.md (the map stays short as it grows)
    log.md             one entry per change, newest first
    raw/               snapshots of sources outside the project (git-ignored)

A page whose front matter says `owner: human` is the people's, one that says `owner: board` the Board's.
`root_of` finds the folder; `scaffold` makes it and its starting files where they are missing. The topics' rules and
the files a wiki starts with are in realm/wiki_rules.py. Pure module, no face.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import shelves
from orkboard.realm.wiki_rules import (INDEX_TEMPLATE, LOG_TEMPLATE, POINTER, SCHEMA_TEMPLATE, SECTION_INDEX, SECTION_RULES,
                                       SECTIONS, TOPIC_ABOUT)

WIKI_HOME = "llm-wiki"
SCHEMA, INDEX, LOG = "WIKI.md", "index.md", "log.md"
PAGES, RAW = "pages", "raw"
RAW_IGNORE = "*\n!.gitignore\n!manifest.json\n"


def default_dir(topic: str) -> str:
    return f"{WIKI_HOME}/{topic}"


def root_of(repo_root: Path, rel: str | None, topic: str = "general") -> Path:
    return shelves.inside(repo_root, (rel or "").strip() or default_dir(topic))


def schema_text(topic: str) -> str:
    sections = SECTIONS.get(topic, SECTIONS["general"])
    return SCHEMA_TEMPLATE.format(topic=topic, about=TOPIC_ABOUT.get(topic, topic), first=sections[0][0],
                                  sections="\n".join(f"- **{name}** — {what}" for name, what in sections))


def scaffold(root: Path, topic: str = "general") -> list[str]:
    """Make the wiki's folder and its starting files where they are missing; the ones made."""
    made = []
    files = [(SCHEMA, schema_text(topic)), (INDEX, INDEX_TEMPLATE.format(topic=topic)), (LOG, LOG_TEMPLATE),
             (f"{RAW}/.gitignore", RAW_IGNORE), ("CLAUDE.md", POINTER.format(topic=topic)),
             ("AGENTS.md", POINTER.format(topic=topic))]
    for name, what in SECTIONS.get(topic, SECTIONS["general"]):
        files += [(f"{PAGES}/{name}/{INDEX}", SECTION_INDEX.format(title=name.replace("-", " ").capitalize(), what=what)),
                  (f"{PAGES}/{name}/CLAUDE.md", SECTION_RULES.format(name=name, topic=topic, what=what))]
    for name, text in files:
        path = root / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            made.append(name)
    (root / PAGES).mkdir(parents=True, exist_ok=True)
    return made
