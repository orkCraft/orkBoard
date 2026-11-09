"""A quick question (docs/specs/106-a-quick-question.md §1.1–§1.2; decisions §181): the one question asked on the open tab and its answer, kept
as a record, and the Board as text for the Orkmaster's call. Pure code, no model, no face; `core/idea_ask.py` asks, `gui/ideas_ask.py` answers
the page's commands and shows the record in the snapshot (`town.ask`).

    board_ask.record(state_dir)            # <state_dir>/ask.json: the question and its answer, None when there is none (or the file is broken)
    board_ask.save(state_dir, rec) / clear(state_dir)
    board_ask.clean(got)                   # the call's JSON made safe: {answer, sources, goal}, None when it has no answer
    board_ask.board_text(root, state_dir)  # the Orkmaster's context: the parties and the goals in line, as plain text, about 3,000 characters
    board_ask.goal_lines(root, state_dir, party)   # a party's goals as lines (the whole Board's with no party)

    board_ask.route(root, tab, q)          # who answers a question asked on `tab` (spec 168 D3, decisions §283.20): `(party, hop)`; the tab's own, or on the Orkmaster's tab the one party named in it
    board_ask.WAYS                         # the answer card's ways as their `way_kind`s (realm/way_kinds.py): *Make it a goal*, *Ask more*, *Got it*

The record is `{status: "asking"|"answered"|"failed", party: ""|<party slug>, tab, hop, ways, q, answer, sources: [..], goal, goal_in_analysis, at, error}`: one question at a time, no
history. `tab` is where it was asked (`ORKMASTER` "" for the Orkmaster's tab), `party` who answers it (the same, unless the Orkmaster passed it on: `hop`). `ways` are the kinds of the
three ways of the card it comes back as in the hand (its answer on the table); the words are the page's. A quick question is the card of the kind **?** (decisions §283.20): no goal, no
phase, no file, no rune and no place in the column; it is kept in the answering leader's journal (`asked`, `journal_notes.asked`) and not shown on the Board.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import goal_phase, goal_team, ideas, map_text, roles, way_kinds

FILE = "ask.json"
ORKMASTER = ""                    # the `party` of a question asked on the Orkmaster's tab
STATUSES = ("asking", "answered", "failed")
Q_CHARS = 500                     # the question, cut
ANSWER_CHARS = 1200
SOURCES, SOURCE_CHARS = 4, 80     # at most four, each cut
GOAL_CHARS = 200                  # the goal the answer suggests
BOARD_CHARS = 3000                # the Board as text, at most
PARTIES_CHARS = 1000              # of BOARD_CHARS, the parties' lines at most
TITLE_CHARS = 60
WAYS = ("make_it_a_goal", "ask_more", "take")          # *Make it a goal*, *Ask more*, *Got it* (a thing taken in: `take`), as realm/way_kinds.py `KINDS` has them
PHASES = goal_phase.words()          # a fine state in the word of its phase (realm/goal_phase.py: the one table)


def record(state_dir: Path) -> dict | None:
    """The question kept (`ask.json`), None when there is none."""
    got = ideas._json(Path(state_dir) / FILE)
    return got if isinstance(got, dict) and got.get("status") in STATUSES else None


def save(state_dir: Path, rec: dict) -> dict:
    """The record replaced whole."""
    with ideas.LOCK:
        ideas._write_json(Path(state_dir) / FILE, rec)
    return rec


def clear(state_dir: Path) -> None:
    """The record removed."""
    with ideas.LOCK:
        try:
            (Path(state_dir) / FILE).unlink()
        except OSError:
            pass


def _line(v: object, n: int) -> str:
    return " ".join(v.split())[:n] if isinstance(v, str) else ""


def route(root: Path, tab: str, q: str) -> tuple[str, bool]:
    """Who answers a question asked on `tab` (decisions §283.20), `(party, hop)`, by code, with no call: on a party's tab its leader; on the Orkmaster's tab the Orkmaster, unless the question
    names one party (its slug or its title as words), whose part it is: one hop to that party's leader. Two named, or none, stay with the Orkmaster."""
    if tab:
        return tab, False
    text = " " + " ".join(str(q or "").lower().split()) + " "
    named = [t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != ideas.GENERAL
             and any(re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", text) for w in {str(t["slug"]).lower(), " ".join(str(t.get("title") or "").lower().split())} if w)]
    return (named[0], True) if len(named) == 1 else (ORKMASTER, False)


def clean(got: dict | None) -> dict | None:
    """The call's JSON, safe to keep: `answer` a non-empty string (line breaks kept, cut), else None; `sources` strings only, at most `SOURCES`, each cut; `goal` one line
    cut to `GOAL_CHARS`, "" when it is none."""
    if not isinstance(got, dict) or not isinstance(got.get("answer"), str) or not got["answer"].strip():
        return None
    sources = [s for s in (_line(x, SOURCE_CHARS) for x in got.get("sources") if isinstance(x, str)) if s] if isinstance(got.get("sources"), list) else []
    return {"answer": got["answer"].strip()[:ANSWER_CHARS], "sources": sources[:SOURCES], "goal": _line(got.get("goal"), GOAL_CHARS)}


# -- the Board as text ------------------------------------------------------------------------------------------------------------------

def _phase(state_dir: Path, slug: str) -> str:
    """A goal's phase in a word by its state, with *n of m tasks merged* when it has a plan."""
    phase = PHASES.get(ideas.state(state_dir, slug)["state"], "Idea")
    tasks = (ideas.plan(state_dir, slug) or {}).get("tasks")
    tasks = [t for t in tasks if isinstance(t, dict) and t.get("state") != "dropped"] if isinstance(tasks, list) else []
    return f"{phase}; {sum(1 for t in tasks if t.get('state') == 'merged')} of {len(tasks)} tasks merged" if tasks else phase


def goal_lines(root: Path, state_dir: Path, party: str = "") -> list[str]:
    """The goals in line, a line each, in the Board's order (a party's alone when `party` is given): its title (cut), its party, its phase."""
    titles = {t["slug"]: t["title"] for t in ideas.tracks(root, make=False)}
    out = []
    for i in ideas.ideas(root, party or None):
        where = "" if party else f" ({titles.get(i['track']) or i['track']})"
        out.append(f"- {_line(i['title'], TITLE_CHARS)}{where}: {_phase(state_dir, i['slug'])}")
    return out


def board_text(root: Path, state_dir: Path) -> str:
    """The Board as plain text for the Orkmaster's call, about `BOARD_CHARS` at most: the parties with their leaders' roles, then the goals in line (past the bound,
    *and n more goals*)."""
    parties = []
    for t in ideas.tracks(root, make=False):
        leader = roles.role(state_dir, goal_team.leader_of(root, t["slug"])) or {}
        parties.append(f"- {_line(t['title'], TITLE_CHARS)}, led by {leader.get('name') or 'the Taskmaster'}")
    head = "The parties:\n" + "\n".join(map_text._fit(parties, PARTIES_CHARS, "- and {n} more parties") or ["(none)"])
    goals = goal_lines(root, state_dir)
    room = BOARD_CHARS - len(head) - len("\n\nThe goals, in line:\n")
    return f"{head}\n\nThe goals, in line:\n" + "\n".join(map_text._fit(goals, room, "- and {n} more goals") if goals else ["(none)"])
