"""The writers of the journals (docs/specs/125-the-journals.md §B; decisions §203): each a line of words for one thing that has happened and been kept, written with `journals.add`
at the place where it happened (`core/idea_decide.py`, `core/idea_talk.py`, `core/idea_objection.py`, `core/idea_concerns.py`, `gui/ideas*.py`). No model, no face. **A journal never
fails what it records**: every function here swallows what goes wrong (a scope that is none, a disk that refuses), so a place calls one in a single line.

    journal_notes.decision(state_dir, root, slug, number, title, overruled)   # project · decision: `Decision 12: title (against Tech: why)`
    journal_notes.stances(state_dir, root, slug, stances)                     # each leader's party · stance, after Talk's first round
    journal_notes.answered(state_dir, root, slug, party, answer, why)         # that party · heeded | overruled, after the person's answer to its no
    journal_notes.at_review(state_dir, root, slug, decision, why)             # the parties that doubted or said no · came_back | went_through, once a goal
    journal_notes.concern_goal(...) / concern_dismissed(...) / since(...)     # a leader's concerns and its evening line
    journal_notes.done(...) / dropped(...) / hypothesis(...) / pitch_passed(...) / brief(...)   # the project's own

The words are the product's (a goal is "a goal"), the second person in a leader's journal, the third in the project's.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import idea_questions, ideas, journals, project_facts

TITLE_CHARS = 80                      # a goal's title in a line
OVER_CHARS = 160                      # the leaders the person overruled, said in a decision's line
HEEDED = {"drop": "dropped it", "smaller": "made it smaller", "later": "put it later"}
VERDICTS = ("no", "doubt")            # the stances Review answers for


def note(state_dir: Path, scope: str, kind: str, text: str, *, idea: str = "", on: object = (), ref: str = "") -> dict | None:
    """One entry; the entry, or None for nothing kept. Whatever goes wrong is passed over: a journal never troubles what it records."""
    try:
        return journals.add(state_dir, scope, kind, text, idea=idea, on=on, ref=ref)
    except Exception:
        return None


def title_of(root: Path, slug: str) -> str:
    """A goal's title in a line (its slug when it has no page)."""
    try:
        page = ideas.idea_page(root, slug)
    except Exception:
        page = None
    return " ".join(((page.title if page is not None else "") or slug).split())[:TITLE_CHARS]


def marks_of(state_dir: Path, slug: str) -> list[str]:
    """The ids of the places on its party's map a goal points at (`marks`)."""
    try:
        return [str(m["id"]) for m in ideas.state(state_dir, slug).get("marks") or [] if isinstance(m, dict) and m.get("id")]
    except Exception:
        return []


def _fit(text: str, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def _kinds(state_dir: Path, scope: str, slug: str) -> set[str]:
    try:
        return {e["kind"] for e in journals.of_goal(state_dir, scope, slug)}
    except Exception:
        return set()


# -- the project's --------------------------------------------------------------------------------------------------------------------

def decision(state_dir: Path, root: Path, slug: str, number: int, title: str, overruled: list[str]) -> None:
    """A decision confirmed: `Decision <n>: <title>` and, when the person overruled leaders, ` (against <Leader>: <why>; …)`. `overruled`: `idea_objections.lines`' first list."""
    try:
        over = "; ".join(o[:1].lower() + o[1:] for o in overruled if o)
        note(state_dir, journals.PROJECT, "decision", f"Decision {number}: {_fit(title, 120)}" + (f" ({_fit(over, OVER_CHARS)})" if over else ""), idea=slug, ref=str(number))
    except Exception:
        pass


def hypothesis(state_dir: Path, slug: str, text: str, state: str, why: str, number: int = 0) -> None:
    """A hypothesis judged held or refuted by the person (`slug` none: a hypothesis is no goal's)."""
    try:
        verb = "held" if state == "held" else "was refuted"
        note(state_dir, journals.PROJECT, "hypothesis", f"“{_fit(text, 120)}” {verb}" + (f": {why}" if why else ""), idea=slug, ref=str(number or ""))
    except Exception:
        pass


def done(state_dir: Path, root: Path, slug: str) -> None:
    """A goal reached main (once a goal)."""
    try:
        if "done" not in _kinds(state_dir, journals.PROJECT, slug):
            note(state_dir, journals.PROJECT, "done", f"“{title_of(root, slug)}” is in main", idea=slug)
    except Exception:
        pass


def dropped(state_dir: Path, root: Path, slug: str, why: str = "") -> None:
    """A goal the person dropped; to be called before its page is gone."""
    try:
        note(state_dir, journals.PROJECT, "dropped", f"“{title_of(root, slug)}” was dropped" + (f": {_fit(why, 160)}" if str(why or "").strip() else ""), idea=slug)
    except Exception:
        pass


def pitch_passed(state_dir: Path, root: Path, slug: str, why: str) -> None:
    try:
        note(state_dir, journals.PROJECT, "pitch_passed", f"Pitch “{title_of(root, slug)}” passed" + (f": {why}" if why else ""), idea=slug)
    except Exception:
        pass


def brief(state_dir: Path, key: str, text: str, dropped_: bool = False) -> None:
    """A line of the brief the person answered or changed (`key` one of `project_facts.COMMON_KEYS`; the others are no part of it)."""
    try:
        if key in project_facts.COMMON_KEYS:
            note(state_dir, journals.PROJECT, "brief", f"{project_facts.LABELS[key]}: " + ("dropped" if dropped_ else text))
    except Exception:
        pass


# -- a leader's -----------------------------------------------------------------------------------------------------------------------

def stances(state_dir: Path, root: Path, slug: str, rows: list[dict]) -> None:
    """Talk's first round: each leader's party, what it said of the goal."""
    try:
        title, on = title_of(root, slug), marks_of(state_dir, slug)
        for s in rows:
            if isinstance(s, dict) and s.get("party") and s.get("verdict"):
                note(state_dir, str(s["party"]), "stance", f"On “{title}” you said {s['verdict']}: {s.get('why') or s.get('stance') or '—'}", idea=slug, on=on)
    except Exception:
        pass


def answered(state_dir: Path, root: Path, slug: str, party: str, answer: str, why: str, title: str = "") -> None:
    """The person's answer to `party`'s leader's no: heeded (drop · smaller · later) or overruled (go). Called before a dropped goal's page is gone; `title` the goal's as the leader knew it
    (*Do the smaller one* words the goal anew)."""
    try:
        title = title or title_of(root, slug)
        if answer in HEEDED:
            note(state_dir, party, "heeded", f"Your no to “{title}” was heeded: the person {HEEDED[answer]}", idea=slug)
        elif answer == "go":
            note(state_dir, party, "overruled", f"The person went on with “{title}” against your no: {why or '—'}", idea=slug)
    except Exception:
        pass


def at_review(state_dir: Path, root: Path, slug: str, decision_: str, why: str = "") -> None:
    """A result decided at Review (`merge` · `back` · `drop`), for each party whose leader said no or doubt on the goal in Talk: `came_back` on the first send back or drop, `went_through` on a merge
    with no `came_back` before; each once a goal."""
    try:
        title = title_of(root, slug)
        for s in idea_questions.record(state_dir, slug).get("stances") or []:
            if not (isinstance(s, dict) and s.get("party") and s.get("verdict") in VERDICTS):
                continue
            party, said = str(s["party"]), ("which you said no to" if s["verdict"] == "no" else "which you doubted")
            had = _kinds(state_dir, party, slug)
            if decision_ in ("back", "fix", "drop"):
                if "came_back" not in had:
                    note(state_dir, party, "came_back", f"“{title}”, {said}, came back at Review: {why or ('it was dropped' if decision_ == 'drop' else 'it was sent back')}", idea=slug)
            elif decision_ == "merge" and not had & {"came_back", "went_through"}:
                note(state_dir, party, "went_through", f"“{title}”, {said}, went through at Review the first time", idea=slug)
    except Exception:
        pass


def concern_goal(state_dir: Path, root: Path, party: str, part: str, name: str, slug: str) -> None:
    try:
        note(state_dir, party, "concern_goal", f"Your concern on {name} became the goal “{title_of(root, slug)}”", idea=slug, on=[part])
    except Exception:
        pass


def concern_dismissed(state_dir: Path, party: str, part: str, name: str, what: str) -> None:
    try:
        note(state_dir, party, "concern_dismissed", f"The person said your concern on {name} is not a problem: {what}", on=[part])
    except Exception:
        pass


def since(state_dir: Path, party: str, map_name: str, way: str, line: str) -> None:
    """The evening line a leader kept (`way`: toward · away · unclear)."""
    try:
        if way in ("toward", "away"):
            text = f"Since your last look the {map_name} map went {'toward' if way == 'toward' else 'away from'} what you keep: {line}"
        else:
            text = f"Since your last look the {map_name} map changed; it is unclear which way: {line}"
        note(state_dir, party, "since", text)
    except Exception:
        pass
