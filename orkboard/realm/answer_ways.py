"""A leader's ways of answering (docs/specs/168 H4, decisions §266.5, §283.22, §283.33): how a leader asks what it must ask, one way a leader, set in its inventory.

    WAYS                       # ("pen", "choice", "fork", "silent")
    DEFAULT                    # "choice": a party that has said nothing asks as it always did
    lock_of(card)              # "" or why the question is §266.5's lock: it is asked, never decided by a leader (going into main, money above what was agreed, dropping or
                               # holding a goal, a decision against an earlier one)
    fork_price(target)         # {low, high} USD: what the Fork's one more call may cost a question, at the elder tier
    carries(card)              # the card said as the hand's veto card carries it

**Pen**: the leader asks and the person writes the answer each time. **Choice**: its ways, two to four, and the person picks (today's cards). **Fork**: one more call a question,
at the elder tier, lays two sides out with their gains, costs and risks (its price is said on the card). **Silent**: the leader decides by itself, says so with a card that can
be overruled (*Accepted*, *Replay*) and never for a lock: a question that is a lock is asked, whatever the way. No model, no face.
"""
from __future__ import annotations

import re
from typing import Any

from orkboard.realm import idea_target, lexicon

WAYS = ("pen", "choice", "fork", "silent")
DEFAULT = "choice"
WORDS = {w: lexicon.term(f"way.{w}") for w in WAYS}        # the glossary's words (realm/lexicon_table.py)
LINES = {"pen": "It asks, and you answer in your own words each time.",
         "choice": "It offers its ways; you pick one.",
         "fork": "Its ways worked out, with their gains, costs and risks: one more call a question, on the elder tier.",
         "silent": "It decides and lays a card you can overrule; going into main, money and dropping a goal are still asked."}
ACCEPTED, REPLAY = lexicon.term("way.accepted"), lexicon.term("way.replay")
ACCEPTED_LINE = "The decision stands as it is."
REPLAY_LINE = "The question comes back with its ways, and you answer it."
KIND_LOCKS = {"drop": "dropping a goal", "later": "holding a goal"}      # a way's kind (realm/way_kinds.py) that is a lock on its own
TEXT_LOCKS = (
    ("going into main", re.compile(r"\b(?:into|to|onto)\s+main\b|\bmain branch\b|\bmerge[sd]?\s+(?:it\s+)?(?:in)?to\s+main\b|\bpush(?:ed|ing)?\s+(?:it\s+)?to\s+(?:main|origin|the remote)\b", re.I)),
    ("money above what was agreed", re.compile(r"[$€£]\s?\d|\b\d+(?:[.,]\d+)?\s?(?:usd|eur|dollars?|euros?)\b|\bbudget\b|\bpaid\b|\bpay(?:ing|ment)?\b|\bmore money\b|\bcosts?\s+(?:more|above|over)\b", re.I)),
    ("dropping or holding a goal", re.compile(r"\bdrop(?:ping|ped)?\s+(?:the|this|that|a)\s+goal\b|\babandon\w*\b|\bcancel\w*\s+(?:the|this)\s+goal\b|\bon hold\b|\bhold(?:ing)?\s+(?:the|this)\s+goal\b|\bshelve\w*\b", re.I)),
    ("a decision against an earlier one", re.compile(r"§\s?\d+|\b(?:against|contradict\w*|overrul\w*|revers\w*|overrid\w*|replac\w*)\s+(?:an?\s+|the\s+)?(?:earlier\s+|previous\s+|written\s+)?decision\b", re.I)),
)


def way_of(raw: object) -> str:
    """A way as a page or a caller says it: one of `WAYS`, else `DEFAULT` (an old page, a word that is none)."""
    return raw if isinstance(raw, str) and raw in WAYS else DEFAULT


def _texts(card: dict) -> list[str]:
    return [str(x) for x in (card.get("q"), card.get("why"), *(card.get("choices") or []), *(card.get("lines") or [])) if x]


def lock_of(card: dict) -> str:
    """Why a leader's question is a lock (§266.5) and so is asked and never decided by a leader, in plain words; "" when it is no lock. Read from what the card says and from its ways'
    kinds (`drop`, `later`). It errs toward asking: a question that might be a lock is one."""
    for kind in card.get("kinds") or []:
        if kind in KIND_LOCKS:
            return KIND_LOCKS[kind]
    text = " ".join(_texts(card))
    for why, rx in TEXT_LOCKS:
        if rx.search(text):
            return why
    return ""


def may_decide(card: dict) -> bool:
    """Whether a Silent leader may decide this question by itself: it is no lock."""
    return not lock_of(card)


def fork_price(target: str, tool: str = "claude") -> dict[str, float]:
    """What the Fork's one more call may cost a question (spec 168 H4): the least a call of the elder tier costs (`idea_target.floor`) up to the cap its step has under `target`; USD."""
    cap = idea_target.budget("fork", target) or 0.0
    low = min(idea_target.floor("elder", tool), cap) if cap else idea_target.floor("elder", tool)
    return {"low": round(low, 2), "high": round(max(cap, low), 2)}


def carries(card: dict, party: str, round_: int, phase: str) -> dict[str, Any]:
    """A question a Silent leader decided, as the record keeps it for the veto card: the whole card (so *Replay* can ask it again), the answer taken (the leader's pick), why, and the goal's `phase`
    when it was decided (the card leaves the hand when the goal's phase is another)."""
    return {"id": card["id"], "party": party, "leader": card.get("leader", ""), "q": card["q"], "answer": card["choices"][card["pick"]], "why": card.get("why", ""),
            "round": round_, "phase": phase, "card": card}


def decided_of(state_dir: Any, slug: str) -> list[dict[str, Any]]:
    """The questions a Silent leader decided in a goal's Talk that are still the person's to overrule: the veto cards of the hand, `[{id, party, leader, q, answer, why, round}]`. A card leaves by itself when the goal moves to its next stage (its phase is no longer the one it was decided in)."""
    from orkboard.realm import goal_phase, idea_questions, ideas
    try:
        phase = goal_phase.of(ideas.state(state_dir, slug))
    except (OSError, ValueError):
        return []
    return [{k: d.get(k) for k in ("id", "party", "leader", "q", "answer", "why", "round")} for d in idea_questions.record(state_dir, slug).get("decided") or [] if isinstance(d, dict) and d.get("phase") == phase]
