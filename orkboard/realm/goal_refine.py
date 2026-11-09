"""A goal in analysis, by code (docs/specs/132-four-levels-the-way-down-and-findings.md §A; decisions §234.5, §242.3): the goals the person can still add words to, before the
decision is confirmed and the sections are written. Pure code, no model, no face.

    goal_refine.in_analysis(state_dir, slug)             # True while the goal is `raw`, `routed`, `talk`, or `decided` with its entry not confirmed
    goal_refine.words(page)                              # the goal's own words: its *Asked* section when it has one, else its Gist
    goal_refine.added(text)                              # the line a person's added words are kept as: `Added: <text>`
    goal_refine.split(gist)                              # (the person's words, the added words): the added words from the first `Added: ` paragraph to the end (spec 168 C2)
    goal_refine.rewritten(gist, base)                    # the Gist with `base` for the person's words and the added words as they were; '' for no words
    goal_refine.in_answer(root, state_dir, sources)      # the slug of the first goal in analysis a quick question's sources name by its title, "" for none
    goal_refine.add_record(state_dir, slug, text, element="", via="")   # one row of the goal's added words (spec 135 §A.3): <state>/ideas/<slug>/added.json
    goal_refine.added_rows(state_dir, slug)              # those rows, oldest first: [{at, text, element, via}]; a broken file reads [] (the file is `{"rows": [...]}`)
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import ideas, spec_sections

FILE = "added.json"
VIAS = ("match", "bubble", "groups")

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


def added_rows(state_dir: Path, slug: str) -> list[dict]:
    """The words added to a goal, oldest first: `[{at, text, element, via}]` (the text as written, the rune the person chose for that idea, "" for none, and how it came: the new-goal
    field's match, the leader's bubble, the backlog's groups); a missing or broken file reads `[]`."""
    got = (ideas._json(ideas.state_folder(state_dir, slug) / FILE) or {}).get("rows")
    return [{k: str(r.get(k) or "") for k in ("at", "text", "element", "via")} for r in got if isinstance(r, dict) and str(r.get("text") or "").strip()] if isinstance(got, list) else []


def add_record(state_dir: Path, slug: str, text: str, element: str = "", via: str = "") -> list[dict]:
    """One row more of a goal's added words (decisions §242.2: marked as the second idea's, its time and its rune kept for a Split); the rows."""
    with ideas.LOCK:
        rows = added_rows(state_dir, slug)
        rows.append({"at": ideas._now(), "text": str(text).strip(), "element": element, "via": via if via in VIAS else ""})
        ideas._write_json(ideas.state_folder(state_dir, slug) / FILE, {"rows": rows})
    return rows


# -- a Gist rewritten with its added words kept (spec 168 C2, decisions §283.24) ------------------------------------------------------------

def split(gist: str) -> tuple[str, str]:
    """A Gist as `(the person's words, the added words)`: the added words are everything from the first paragraph that begins `Added: ` to the end (`add_words` only ever appends them), kept byte for byte."""
    m = re.search(r"(?m)^" + re.escape(ADDED.rstrip()) + r" ", gist or "")
    return ((gist[:m.start()].rstrip(), gist[m.start():]) if m else ((gist or "").rstrip(), ""))


def rewritten(gist: str, base: str) -> str:
    """The Gist with its words `base` in place of the person's and every *Added:* line as it was; '' where `base` says nothing."""
    base = str(base or "").strip()
    _was, tail = split(gist)
    if not base:
        return ""
    return f"{base}\n\n{tail}" if tail else base
