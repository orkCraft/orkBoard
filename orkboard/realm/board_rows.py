"""The Needs you rows that sit on no goal (docs/specs/99-a-goals-way.md §8.2; decisions §157.1): a stack of its own among the stacks, laid after the others. A pure read of what the
Board keeps: it writes nothing, starts nothing and words nothing. `realm/board_map.py` lays them in `build`, `gui/ideas_board.py` in the Board's Needs you.

    board_rows.project_q(state_dir)   # [] or [{kind: "project_q", party, leader, questions: [card], text, blocks, priority, at}]
    board_rows.rows(state_dir)        # every such row, in the order they are laid

`project_q`: the project's questions at the first start (core/idea_project_q.py asks them, `ideas.project_answer` answers them): the stack of its party's leader (Product's, in a
game Game design's; with neither, the Orkmaster: `party` "" and `leader` "orkmaster"), its cards the leader's (`idea_questions.card`, `project: true`; the Orkmaster's has no choices).
It holds nothing back (`blocks` false: the first goal is sent with it unanswered) and is a question the work does not wait for, so it lies after the others; answered or let go
(*Let … decide*), it leaves the hand. `text` is the top card's question, as a stop of an unknown kind is drawn until the face draws this one (spec 100).
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import project_questions


def project_q(state_dir: Path) -> list[dict]:
    rec = project_questions.record(state_dir)
    cards = [c for c in rec.get("questions") or [] if isinstance(c, dict)]
    if rec.get("status") != "waiting" or not cards:
        return []
    return [{"kind": "project_q", "party": str(rec.get("party") or ""), "leader": str(rec.get("leader") or ""), "questions": cards, "text": str(cards[0].get("q") or ""),
             "blocks": False, "priority": "normal", "at": str(rec.get("at") or "")}]


def rows(state_dir: Path) -> list[dict]:
    return [*project_q(state_dir)]
