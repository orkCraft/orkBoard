"""The Needs you rows that sit on no goal (docs/specs/99-a-goals-way.md §8.2; decisions §157.1): a stack of its own among the stacks, laid after the others. A pure read of what the
Board keeps: it writes nothing, starts nothing and words nothing. `realm/board_map.py` lays them in `build`, `gui/ideas_board.py` in the Board's Needs you.

    board_rows.project_q(state_dir)           # [] or [{kind: "project_q", party, leader, questions: [card], text, blocks, priority, at}]
    board_rows.hypothesis(state_dir, pages)   # [{kind: "hypothesis", id, text, signal, evidence, tests: [{slug, title}], party, leader, blocks, priority, at, question}]
    board_rows.rows(state_dir, pages)         # every such row, in the order they are laid (`pages`: the Board's pages, where the tests' places are read; none, and no hypothesis is due)

`project_q`: the project's questions at the first start (core/idea_project_q.py asks them, `ideas.project_answer` answers them): the stack of its party's leader (Product's, in a
game Game design's; with neither, the Orkmaster: `party` "" and `leader` "orkmaster"), its cards the leader's (`idea_questions.card`, `project: true`; the Orkmaster's has no choices).
It holds nothing back (`blocks` false: the first goal is sent with it unanswered) and is a question the work does not wait for, so it lies after the others; answered or let go
(*Let … decide*), it leaves the hand. `text` is the top card's question, as a stop of an unknown kind is drawn until the face draws this one (spec 100).

`hypothesis` (docs/specs/116-hypotheses-on-products-tree.md §4.1; decisions §194): *Did it hold?*, one row for each open hypothesis that has a test and whose every test (a goal) is done
(`hypotheses.due`; the places are the goals' on the Board's pages). `text` is the hypothesis's own words, the top line a face that does not draw the kind shows (as `project_q`'s is its top
card's question); `question` is the plain question about it, for such a face to ask. `signal` and `evidence` ({text, ref, at}) are what would show it and what was found; `tests` the goals that
tested it, `[{slug, title}]`; `party` is the party that proposed it ("" the person's own) and `leader` that party's leader (the Orkmaster's for the person's). It holds nothing back (`blocks`
false) and lies after the others; judged (`ideas.hypothesis_judge`), it leaves the hand.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_team, hypotheses, ideas, opportunity_tree, project_questions


def project_q(state_dir: Path) -> list[dict]:
    rec = project_questions.record(state_dir)
    cards = [c for c in rec.get("questions") or [] if isinstance(c, dict)]
    if rec.get("status") != "waiting" or not cards:
        return []
    return [{"kind": "project_q", "party": str(rec.get("party") or ""), "leader": str(rec.get("leader") or ""), "questions": cards, "text": str(cards[0].get("q") or ""),
             "blocks": False, "priority": "normal", "at": str(rec.get("at") or "")}]


def places_of(state_dir: Path, pages: Path | None, slugs: list[str]) -> dict[str, str]:
    """`{slug: "line" | "work" | "done"}` of the goals among `slugs` that the Board's pages still have; empty without `pages` (a goal gone from the Board is not done)."""
    out: dict[str, str] = {}
    for slug in dict.fromkeys(slugs) if pages is not None else ():
        try:
            page = ideas.idea_page(Path(pages), slug)
        except (OSError, ValueError):
            page = None
        if page is not None:
            out[slug] = opportunity_tree.place_of(state_dir, slug)
    return out


def hypothesis(state_dir: Path, pages: Path | None = None) -> list[dict]:
    kept = hypotheses.read(state_dir)["items"]
    places = places_of(state_dir, pages, [t for i in kept for t in i["tests"]])
    out = []
    for item in hypotheses.due(state_dir, places):
        tests = [{"slug": t, "title": " ".join((ideas.idea_page(Path(pages), t).title or t).split())[:80]} for t in item["tests"]]      # `due` has every test in `places`: its page is there
        party = item["party"]
        out.append({"kind": "hypothesis", "id": item["id"], "text": item["text"], "signal": item["signal"], "evidence": item["evidence"], "tests": tests, "party": party,
                    "leader": goal_team.leader_of(Path(pages), party) if party else "orkmaster", "blocks": False, "priority": "normal", "at": item["at"],
                    "question": f"Did it hold? {item['text']}"})
    return out


def rows(state_dir: Path, pages: Path | None = None) -> list[dict]:
    return [*project_q(state_dir), *hypothesis(state_dir, pages)]
