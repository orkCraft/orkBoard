"""The goals in line (docs/specs/108 §4.2; decisions §183.2): the goals that lie in the **deck** (`goal_place.place_of`: not started, asking nothing), the Board's own line
the table draws (`lineNow` on the page), read by code from the pages and the states so a call that has no snapshot can be told them. Pure code, no model, no face.

    line(root, state_dir, limit=10)      # [{slug, title, party, party_title}], the party's order then the goal's, at most `limit`
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_place, ideas
from orkboard.realm.board_map import list_of

LIMIT = 10                       # a leader is told this many goals in line, at most
TITLE_CHARS = 80


def line(root: Path, state_dir: Path, limit: int = LIMIT) -> list[dict]:
    """The goals in the deck, in the Board's order, `{slug, title, party, party_title}`; a goal at Talk, at work or done is not in line."""
    titles = {t["slug"]: t["title"] for t in ideas.tracks(root, make=False)}
    found, pages = ideas.ideas_and_pages(root)
    states = {i["slug"]: ideas.state(state_dir, i["slug"]) for i in found}
    out = []
    for i in found:
        slug, st = i["slug"], states[i["slug"]]
        waits = [d for d in list_of(pages[slug].get("depends_on")) if states.get(d, {}).get("state") != "done"]
        plan = ideas.plan(state_dir, slug) if st["state"] == "plan" else None
        row = {"state": st["state"], "queue": ideas.queue_of(st), "held_until": st["held_until"], "start_at": str((plan or {}).get("start_at") or ""), "waits_on": waits}
        if goal_place.place_of(row, [])["place"] == "deck":
            out.append({"slug": slug, "title": " ".join(i["title"].split())[:TITLE_CHARS], "party": i["track"], "party_title": titles.get(i["track"], i["track"])})
        if len(out) >= limit:
            break
    return out
