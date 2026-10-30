"""A goal's element (docs/specs/50-parties-and-goals.md §2.3, decisions §63.4): the mark every card of the goal wears, one of orkUI's
five (`design-system/orkui/office/elements/`: a pixel symbol and a muted colour). Given once, to the goal that has none, as the one
used least among its party's open goals, and kept in its `state.json`; a goal moved to another party keeps its own. The faces draw it
and never name it.

    idea_element.pick(["ice", "ice", "dust"])                  # "meadow": the one used least, ties in ELEMENTS' order
    idea_element.of(state_dir, "dark-mode")                    # "" before one is given
    idea_element.give(root, state_dir, "dark-mode")            # the one it has, else the one it is given now (stored)
    idea_element.next_for(root, state_dir, "tech")             # the one a new goal of that party would be given (the + card's seal shows it)
    idea_element.free_for(root, state_dir, "tech")             # the ones none of its open goals has, in ELEMENTS' order; [] when none is free (the + card's free runes)
    idea_element.give(root, state_dir, "dark-mode", want="void")   # the one chosen, when the goal has none yet

No face, no model.
"""
from __future__ import annotations

import os
from pathlib import Path

from orkboard.realm import ideas

ELEMENTS = ("meadow", "ice", "dust", "void", "lava")


def pick(used: list[str]) -> str:
    """The element used least in `used`, ties by `ELEMENTS`' order (a word that is no element counts for none)."""
    return min(ELEMENTS, key=lambda e: (list(used).count(e), ELEMENTS.index(e)))


def of(state_dir: Path, slug: str) -> str:
    """The goal's element; "" when it has none yet."""
    element = ideas.state(state_dir, slug).get("element")
    return element if element in ELEMENTS else ""


def open_elements(root: Path, state_dir: Path, party: str, besides: str = "") -> list[str]:
    """The elements of the party's open goals (not done; a dropped goal is gone), without `besides`."""
    out = []
    for i in ideas.ideas(root, party):
        if i["slug"] == besides:
            continue
        st = ideas.state(state_dir, i["slug"])
        if st["state"] != "done" and st.get("element") in ELEMENTS:
            out.append(st["element"])
    return out


def next_for(root: Path, state_dir: Path, party: str) -> str:
    """The element a new goal of the party would be given now (decisions §186.3): the rule `give` uses, so the rune the + card's seal shows
    is the one the goal gets. Reads, stores nothing."""
    return pick(open_elements(root, state_dir, party))


def free(used: list[str]) -> list[str]:
    """The elements `used` does not hold, in `ELEMENTS`' order; empty when all five are used (the face then shows all of them)."""
    return [e for e in ELEMENTS if e not in used]


def free_for(root: Path, state_dir: Path, party: str) -> list[str]:
    """The elements none of the party's open goals has (decisions §187.3): the runes the + card's seal and field offer first. Reads, stores nothing."""
    return free(open_elements(root, state_dir, party))


def give(root: Path, state_dir: Path, slug: str, used: list[str] | None = None, want: str = "") -> str:
    """The goal's element: the one it has, else `want` when it is one of `ELEMENTS` (the one the person chose, decisions §187.3), else the one picked
    against its party's open goals and stored in its state (one write, ever). `used`: those elements when the caller has them already (a map that gives to many goals in a row). The write is not a
    change of the goal: its `state.json` keeps its modification time (`ideas.touched_at` says when the goal last changed)."""
    with ideas.LOCK:
        have = of(state_dir, slug)
        if have:
            return have
        if used is None:
            page = ideas.idea_page(root, slug)
            used = open_elements(root, state_dir, (page.get("track") if page is not None else "") or ideas.GENERAL, besides=slug)
        element = want if want in ELEMENTS else pick(used)
        path = ideas.state_folder(state_dir, slug) / "state.json"
        try:
            before = path.stat()
        except OSError:
            before = None
        ideas.save_state(state_dir, slug, element=element)
        if before is not None:
            try:
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            except OSError:
                pass
        return element
