"""The frame each craft's senior reviews its map by (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §2.1–§2.2; decisions §184): a few *aspects* a leader looks at, each with the question it asks
and the kinds of hints of code (`realm/map_signals.py`; for tech and design also the live product's, `realm/play_signals.py`: `error` and `failed` in *safety*, `slow` in *hotspots*, `dead_press` in *flow*, `again` in *status*) that ground it. Pure data and code; no face, no model.

    lens_rubrics.RUBRICS[craft] = {"framework": str, "short": str, "aspects": ({"id", "name", "ask", "signals": (kind, …)}, …)}     # the crafts: tech, design, product, game-design, art, release, marketing, run, liveops
    lens_rubrics.rubric(craft, hero=None)            # the craft's rubric, or None (a craft with none); a non-default hero of the craft (realm/heroes.py) gives its frame
    lens_rubrics.aspect_of(craft, kind)              # the aspect (its id) a hint's kind belongs to, "" for none
    lens_rubrics.prompt_lines(craft)                 # the rubric as lines for a model: "How a senior of <craft> reviews this map: <framework>." then "- <id>: <name>. <ask>"; "" for none
    lens_rubrics.scorecard(craft, rec)               # [{id, name, ask, state, n, hints: [words]}] in the rubric's order, from a concerns record (`realm/concerns.py`); [] for none

`framework` is a line for the model, `short` the few words the strip shows. The ids are code's; the names and asks are the interface's and the model's. Every kind of hint of a craft is in exactly one
of its aspects. An aspect's `state` in the scorecard: `alert` (an open concern of the aspect at alert), else `note` (an open one at note), else `hint` (code noticed something on the aspect and the
leader let it be), else `clear` (a look was made: nothing), else `unlooked` (no look yet: `rec.at` empty). `n` is the open concerns of the aspect (a concern made into a goal is not open, as
`concerns.counts`); `hints` the words of the aspect's hints, three at most. Run and LiveOps have no map: their rubrics judge in Talk only (`realm/idea_objections.py`) and name no signals.
"""
from __future__ import annotations

from orkboard.realm.seat_rubric_rules import _a, RUBRICS

HINT_WORDS = 3                       # the words of an aspect's hints the scorecard gives, at most


def _hero(craft: str, hero: object) -> object:
    """The hero (`realm/heroes.py`, or its id) whose frame replaces the craft's: a hero of that craft that is not its default; None else (today's rubric)."""
    from orkboard.realm import heroes
    h = heroes.get(hero) if isinstance(hero, str) else hero
    return h if h is not None and h.craft == craft and not h.default else None


def rubric(craft: str, hero: object = None) -> dict | None:
    """The craft's rubric (see the module), or None for a craft with none. `hero`: a non-default hero of the craft (a `Hero` or its id) gives its own frame
    (`{framework, short, aspects}`, the aspects without signals: spec 157 A.3); none, a default hero or one of another craft gives today's."""
    h = _hero(craft, hero)
    if h is None:
        return RUBRICS.get(craft)
    return {"framework": h.framework, "short": h.short, "aspects": tuple({**a, "signals": ()} for a in h.aspects)}


def aspect_of(craft: str, kind: str) -> str:
    """The id of the aspect a hint's `kind` belongs to in the craft's rubric; "" for none."""
    for a in (RUBRICS.get(craft) or {}).get("aspects", ()):
        if kind in a["signals"]:
            return a["id"]
    return ""


def prompt_lines(craft: str, hero: object = None) -> str:
    """The rubric as lines for a model: how a senior of the craft reviews the map, then one line an aspect (`- <id>: <name>. <ask>`); "" for a craft with none. `hero`: as `rubric`."""
    r = rubric(craft, hero)
    if r is None:
        return ""
    return "\n".join([f"How a senior of {craft} reviews this map: {r['framework']}.", *[f"- {a['id']}: {a['name']}. {a['ask']}" for a in r["aspects"]]])


def scorecard(craft: str, rec: dict, hero: object = None) -> list[dict]:
    """Each aspect of the craft's rubric in its state (see the module) from a concerns record: `[{id, name, ask, state, n, hints}]` in the rubric's order; [] for a craft with none.
    `hero`: as `rubric` (a hint of code is in a hero's aspect only when it names that aspect: code's kinds belong to the craft's default rubric)."""
    r = rubric(craft, hero)
    if r is None:
        return []
    open_ = [c for c in rec.get("concerns") or [] if not c.get("idea")]
    hints = rec.get("hints") or []
    out = []
    for a in r["aspects"]:
        mine = [c for c in open_ if c.get("aspect") == a["id"]]
        words = [h["words"] for h in hints if (h.get("aspect") or aspect_of(craft, h.get("kind") or "")) == a["id"] and h.get("words")][:HINT_WORDS]
        if any(c["level"] == "alert" for c in mine):
            state = "alert"
        elif mine:
            state = "note"
        elif words:
            state = "hint"
        else:
            state = "clear" if rec.get("at") else "unlooked"
        out.append({"id": a["id"], "name": a["name"], "ask": a["ask"], "state": state, "n": len(mine), "hints": words})
    return out
