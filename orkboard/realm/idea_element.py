"""A goal's rune (docs/specs/50-parties-and-goals.md §2.3, decisions §63.4; spec 128 G, decisions §206.10): the mark every card of the goal wears. A rune
is a **shape** (`element`, one of orkUI's five: `design-system/orkui/elements/`, a pixel symbol) in a **colour** (`hue`, one of the same five names: orkUI's
`--ork-elem-<hue>`), 25 together. Given once, to the goal that has none, against the project's goals that hold a rune: its open goals and its done goals whose
result is not yet seen (a done goal seen frees its rune). The shape used least, then, among the goals of that shape, the hue used least, ties in ELEMENTS' order;
kept in its `state.json`. A goal with an element and no hue wears its element as its hue (every goal of before keeps its look); a goal moved to another party keeps
its own. The faces draw it and never name it.

    idea_element.pick(["ice", "ice", "dust"])                  # "meadow": the shape used least, ties in ELEMENTS' order
    idea_element.pick_rune([("meadow", "meadow"), ("meadow", "ice")])   # ("ice", "meadow"): the shape, then its hue
    idea_element.of(state_dir, "dark-mode")                    # "" before one is given
    idea_element.hue_of(state_dir, "dark-mode")                # its colour; its element when it has no hue of its own; "" before one is given
    idea_element.give(root, state_dir, "dark-mode")            # the shape it has, else the one it is given now (stored with its hue)
    idea_element.next_rune_for(root, state_dir)                # (shape, hue) a new goal would be given (the + card's seal shows it)
    idea_element.free(idea_element.open_elements(root, state_dir))   # the shapes no goal holds, in ELEMENTS' order; [] when none is free (the + card's free runes)
    idea_element.give(root, state_dir, "dark-mode", want="void")   # the shape chosen, when the goal has none yet; its hue is picked

No face, no model.
"""
from __future__ import annotations

import os
from pathlib import Path

from orkboard.realm import ideas

ELEMENTS = ("meadow", "ice", "dust", "void", "lava")

Rune = tuple[str, str]       # (shape, hue)


def pick(used: list[str]) -> str:
    """The shape used least in `used`, ties by `ELEMENTS`' order (a word that is no element counts for none)."""
    return min(ELEMENTS, key=lambda e: (list(used).count(e), ELEMENTS.index(e)))


def pick_hue(used: list[Rune], shape: str) -> str:
    """The hue used least among the runes of `used` that are of `shape`, ties by `ELEMENTS`' order."""
    mine = [h for s, h in used if s == shape]
    return min(ELEMENTS, key=lambda h: (mine.count(h), ELEMENTS.index(h)))


def pick_rune(used: list[Rune], want: str = "") -> Rune:
    """The rune a new goal is given against the runes `used`: the shape used least (`want`, when it is one of `ELEMENTS`: the shape chosen), then its hue."""
    shape = want if want in ELEMENTS else pick([s for s, _h in used])
    return shape, pick_hue(used, shape)


def hue_in(st: dict) -> str:
    """The hue of a goal's state: its own, else its element (a goal of before wears its element's colour); "" with neither."""
    hue, element = st.get("hue"), st.get("element")
    return hue if hue in ELEMENTS else (element if element in ELEMENTS else "")


def of(state_dir: Path, slug: str) -> str:
    """The goal's element (its shape); "" when it has none yet."""
    element = ideas.state(state_dir, slug).get("element")
    return element if element in ELEMENTS else ""


def hue_of(state_dir: Path, slug: str) -> str:
    """The goal's hue (its colour): its own, else its element; "" when it has no rune yet."""
    return hue_in(ideas.state(state_dir, slug))


def holds(st: dict) -> bool:
    """Whether a goal's state holds its rune: it has one and it is open, or done and its result not yet seen (a done goal seen frees it)."""
    return st.get("element") in ELEMENTS and (st["state"] != "done" or not st.get("seen_at"))


def open_runes(root: Path, state_dir: Path, besides: str | tuple[str, ...] = "") -> list[Rune]:
    """The runes the project's goals hold (`holds`), without those of the goal `besides` (or of the goals, a tuple of slugs)."""
    skip = (besides,) if isinstance(besides, str) else besides
    out = []
    for i in ideas.ideas(root):
        if i["slug"] in skip:
            continue
        st = ideas.state(state_dir, i["slug"])
        if holds(st):
            out.append((st["element"], hue_in(st)))
    return out


def open_elements(root: Path, state_dir: Path, besides: str | tuple[str, ...] = "") -> list[str]:
    """The shapes the project's goals hold, without `besides`'s."""
    return [s for s, _h in open_runes(root, state_dir, besides)]


def next_rune_for(root: Path, state_dir: Path) -> Rune:
    """The rune a new goal would be given now (decisions §186.3, §206.10): the rule `give` uses, so the rune the + card's seal shows is the one the goal gets. Reads, stores nothing."""
    return pick_rune(open_runes(root, state_dir))


def free(used: list[str]) -> list[str]:
    """The shapes `used` does not hold, in `ELEMENTS`' order; empty when all five are used (the face then shows all of them)."""
    return [e for e in ELEMENTS if e not in used]


def give(root: Path, state_dir: Path, slug: str, used: list[Rune] | None = None, want: str = "", want_hue: str = "") -> str:
    """The goal's element (its shape): the one it has, else `want` when it is one of `ELEMENTS` (the one the person chose, decisions §187.3), else the one picked
    against the project's runes and stored in its state with its hue (`want_hue`, when it is one of `ELEMENTS`, else the hue used least among the goals of that shape;
    one write, ever). `used`: those runes when the caller has them already (a map that gives to many goals in a row). The write is not a
    change of the goal: its `state.json` keeps its modification time (`ideas.touched_at` says when the goal last changed). A goal with a shape and no hue
    is given none: it wears its shape's colour (`hue_of`)."""
    with ideas.LOCK:
        have = of(state_dir, slug)
        if have:
            return have
        if used is None:
            used = open_runes(root, state_dir, besides=slug)
        element, hue = pick_rune(used, want)
        if want_hue in ELEMENTS:
            hue = want_hue
        path = ideas.state_folder(state_dir, slug) / "state.json"
        try:
            before = path.stat()
        except OSError:
            before = None
        ideas.save_state(state_dir, slug, element=element, hue=hue)
        if before is not None:
            try:
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            except OSError:
                pass
        return element
