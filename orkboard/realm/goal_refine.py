"""A goal in analysis, by code (docs/specs/132-four-levels-the-way-down-and-findings.md §A; decisions §234.5, §242.3): the goals the person can still add words to, before the
decision is confirmed and the sections are written. Pure code, no model, no face.

    goal_refine.in_analysis(state_dir, slug)             # True while the goal is `raw`, `routed`, `talk`, or `decided` with its entry not confirmed
    goal_refine.words(page)                              # the goal's own words: its *Asked* section when it has one, else its Gist
    goal_refine.added(text)                              # the line a person's added words are kept as: `Added: <text>`
    goal_refine.in_answer(root, state_dir, sources)      # the slug of the first goal in analysis a quick question's sources name by its title, "" for none
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import ideas, spec_sections

ANALYSIS = ("raw", "routed", "talk", "decided")       # before the sections: a goal here takes words in with one `decide` call at most
ADDED = "Added: "


def in_analysis(state_dir: Path, slug: str) -> bool:
    """True while the goal can take words in: its state is one of `ANALYSIS`, and a `decided` one has not been confirmed (its sections may be failing)."""
    state = ideas.state(state_dir, slug)["state"]
    if state not in ANALYSIS:
        return False
    if state == "decided":
        d = spec_sections.record(state_dir, slug).get("decision")
        return isinstance(d, dict) and not d.get("confirmed")
    return True


def words(page: "ideas.Page") -> str:
    """The person's words of a goal: *Asked* when the page has the section, else its Gist."""
    return page.section("Asked") or page.section("Gist")


def added(text: str) -> str:
    """One line for words added to a goal, as the person wrote them (line breaks kept)."""
    return ADDED + str(text or "").strip()


def in_answer(root: Path, state_dir: Path, sources: list[str]) -> str:
    """The goal in analysis a question's answer is about: the first of its `sources` that is a goal's title (as the call is told to name a goal), else ''."""
    wanted = {" ".join(str(s).split()).lower() for s in sources or [] if str(s).strip()}
    if not wanted:
        return ""
    for i in ideas.ideas(root):
        if " ".join(str(i["title"]).split()).lower() in wanted and in_analysis(state_dir, i["slug"]):
            return i["slug"]
    return ""
