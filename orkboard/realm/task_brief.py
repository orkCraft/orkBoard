"""What a plan and a task read of a spec of the new format (docs/specs/99-a-goals-way.md §9.3; decisions §118.5, §156.13): the **common part** (*Asked*, *Gist*, *Route*,
*Depends on*, *Decisions*), its **party's section whole**, and of every other party's section only its **contract**: *Done when* and *Will be*. A task's prompt names
those, never the whole page. A page of before (one section of its party, nothing rewritten) has none of this: it is read as it was. Pure code, no model, no face.

    reading(page, heading)            # {common: {name: text}, own: (heading, text), others: [(heading, contract)]} · None for a page with no party section
    contract(text)                    # a section's *Done when* and *Will be*, as its leader wrote them ("" when it has neither)
    note(page, heading)               # the sentence a task's prompt says of the spec's reading ("" for a page of before, or a task with no section)
    page_of(repo_root, state_dir, path)  # the spec's page as a task's worktree holds it (`idea_git.spec_paths` gives the path), None when it is not there
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import idea_page, spec_sections

CONTRACT = ("Done when", "Will be")                      # of another party's section, what is read: the contract this one must not break


def contract(text: str) -> str:
    """A section's contract: its *Done when* and *Will be*, each under its `###` heading, as the leader wrote them."""
    parts = spec_sections.split(text)
    return spec_sections.join({n: parts[n] for n in CONTRACT if str(parts.get(n) or "").strip()})


def reading(page: idea_page.Page, heading: str) -> dict | None:
    """What the section `heading` of `page` reads: the common part (the names the page has, with their text), its own section whole and the contract of each other
    section, in the order the page has them. None for a page with no party section, or one with no section of that heading (the caller reads the page as before)."""
    found = spec_sections.sections_of(page)
    own = next(((n, t) for n, t in found if n.lower() == str(heading or "").lower()), None)
    if own is None:
        return None
    have = {n.lower(): t for n, t in page.sections}
    return {"common": {n: have[n.lower()].strip() for n in spec_sections.COMMON if have.get(n.lower(), "").strip()}, "own": own,
            "others": [(n, contract(t)) for n, t in found if n != own[0]]}


def note(page: idea_page.Page, heading: str) -> str:
    """What a task is told of the spec it may read, to follow "Its spec is at … in this worktree: ": its common part, its party's section whole (`## <heading>`), and of the others
    only *Done when* and *Will be*."""
    got = reading(page, heading)
    if got is None:
        return ""
    names = ", ".join(f"`## {n}`" for n in got["common"])
    others = ", ".join(f"`## {n}`" for n, _text in got["others"])
    return (f"read the common part ({names}), your party's section `## {got['own'][0]}` whole"
            + (f", and of the other sections ({others}) only their `### Done when` and `### Will be`: they are the contract your work must not break" if others else "")
            + ". Read nothing else of it: the other parties' sections are theirs.")


def page_of(repo_root: Path, state_dir: Path, path: str) -> idea_page.Page | None:
    """The spec's page as `path` (relative, from `idea_git.spec_paths`) holds it: the Board's own worktree first, else the repository's."""
    for base in (Path(state_dir) / "board", Path(repo_root)):
        try:
            return idea_page.parse((base / path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return None
