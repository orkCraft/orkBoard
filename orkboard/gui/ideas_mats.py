"""The cards' commands, over the Board's `Ideas` (docs/specs/171; decisions §301): what the table of cards asks of the host, read from the Board's own pages.

    ideas.turns {}      # the moves that wait for the person (`realm/board_turns.py`): {turns: [{goal, kind, at, questions?}]}; read only, no model, no write
    ideas.verdicts {}   # each goal's tokens: {<goal>: [{leader, verdict, why, stance, for, against, instead, assumes}]}, one for each leader of its route that has said its `### Talk`
    ideas.tables {}     # each party's framework: {<party>: {architecture | jtbd: its cards}}; what is not laid is empty and says who fills it, never an example
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.realm import board_turns, code_layers, ideas, opportunity_tree, page_talk


class Mats:
    """The cards' commands, as `gui/ideas_say.py`'s `Say` is the say's."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def turns(self, args: dict) -> dict:
        root = self.i.root(make=False)
        found, pages = ideas.ideas_and_pages(root)
        parties = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
        at = {i["slug"]: ideas.touched_at(root, self.i.state_dir, i["slug"]) for i in found}
        return {"turns": board_turns.turns({i["slug"]: pages[i["slug"]] for i in found}, parties, at)}


    def verdicts(self, args: dict) -> dict:
        root = self.i.root(make=False)
        found, pages = ideas.ideas_and_pages(root)
        parties = ideas.tracks(root, make=False)
        out: dict[str, list] = {}
        for i in found:
            page, seen = pages[i["slug"]], []
            for slug in board_turns.route_of(page):
                say = page_talk.read_talk(page, board_turns._title(parties, slug))
                if say is not None:
                    seen.append({"leader": slug, **say})
            if seen:
                out[i["slug"]] = seen
        return out

    def tables(self, args: dict) -> dict:
        root = self.i.root(make=False)
        have = {t["slug"] for t in ideas.tracks(root, make=False)}
        out: dict[str, dict] = {}
        if "tech" in have:
            arch = code_layers.architecture(Path(self.i.host.repo_root))
            if arch is not None:
                out["tech"] = {"architecture": arch}
        if "product" in have:
            out["product"] = {"jtbd": jobs_to_be_done(opportunity_tree.read(self.i.state_dir))}
        return out


ASKS_JOBS = "Product lays its jobs"
ASKS_PEOPLE = "Product asks the person who the people are"


def jobs_to_be_done(rec: dict) -> dict:
    """Product's Jobs to be done from the tree's record: its jobs when kept, else every zone empty and `fills` saying who lays it; no example."""
    jobs = rec.get("jobs") or []
    segments = list(dict.fromkeys(j["segment"] for j in jobs if j.get("segment")))
    main = jobs[0] if jobs else None
    return {
        "personas": [{"id": f"persona-{n}", "title": s, "line": ""} for n, s in enumerate(segments)],
        "job": {"id": main["id"], "when": main["when"], "want": main["want"], "so": main["so"], "persona": main.get("segment", "")} if main else None,
        "forces": [], "hired": None, "fired": [],
        "jobs": [{"id": j["id"], "title": j["want"], "line": j["when"]} for j in jobs[1:]],
        "fills": {"personas": "" if segments else ASKS_PEOPLE, "job": "" if main else ASKS_JOBS, "jobs": "" if len(jobs) > 1 else ASKS_JOBS,
                  "forces": ASKS_JOBS, "hired": ASKS_JOBS, "fired": ASKS_JOBS},
    }


def mats_commands(ideas_: Any) -> dict:
    """The cards' commands by name (`gui/ideas.py` adds them to its table: `**mats_commands(self)`)."""
    m = Mats(ideas_)
    return {"ideas.turns": m.turns, "ideas.verdicts": m.verdicts, "ideas.tables": m.tables}
