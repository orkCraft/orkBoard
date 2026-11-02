"""Passing a leader's question on (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md §D; decisions §206.6): a leader's question that another leader's map or
the code answers does not go to the person: it goes through the Orkmaster to that party's leader, which answers it in one cheap call. Pure code, no model, no face; the keeper's
`core/idea_pass.py` waits and asks, `gui/ideas_pass.py` takes the two commands, the snapshot's `passing` is `row`.

    idea_pass.target_of(card, parties)          # the party a card may be passed to (its `for`), "" when it is the person's
    idea_pass.person_only(card)                 # money, safety, anything that cannot be undone, or a secret: the person's whatever its `for` says (code, never the model)
    idea_pass.answer_of(got, card)              # the answering call's JSON → (text, how) as a person's answer would be (`idea_questions.answer_of`), None when it cannot answer
    idea_pass.id_of(idea, card_id) / split_id(id)   # a question's id on the Board: `<idea>~<card id>`
    idea_pass.row(idea, card, left_s, answering)    # one row of the snapshot's `passing`: {id, idea, task, by, to, q, left_s, answering}

A question carries `for` (`idea_questions.for_of`): a party's slug, or the person's. A question about money, safety or anything that cannot be undone is the person's whatever
its `for` says: `person_only` reads the words the rules already read for a paid or an outward task (`idea_risk`), and a few of money's and of safety's own.
"""
from __future__ import annotations

from orkboard.realm import idea_questions, idea_risk

PASS_S = 10                         # how long a passing question waits for the person to take it or pass it now, in seconds
SEP = "~"                           # between a goal's slug and its card's id in a passing question's id (a slug holds no ~)

# What the rules already read for a paid or an outward task (`idea_risk.TRIGGERS`): secrets and payments, data deleted, outward and irreversible.
_RISKS = (idea_risk.SECRETS, idea_risk.DATA, idea_risk.OUTWARD)
_WORDS = idea_risk._words("cost", "costs", "price", "pricing", "budget", "spend", "spending", "money", "paid", "pay", "paying", "usd", "dollar", "dollars", "euro", "euros",
                          "subscription", "irreversible", "undone", "undo", "permanent", "permanently", "delete", "deleted", "erase", "safety", "unsafe", "security", "privacy",
                          "legal", "licence", "license", "cannot be reverted")


def person_only(card: dict) -> bool:
    """A question about money, safety or anything that cannot be undone is the person's, whatever its `for` says: the card's ask, choices and why are read as the rules read a
    task's words (`idea_risk.assess`), and for the words of money and safety above. A safe-side check: a question held back by mistake only goes to the person."""
    text = "\n".join([str(card.get("q") or ""), *[str(c) for c in card.get("choices") or []], str(card.get("why") or "")])
    return bool(set(idea_risk.assess(texts=[text]).triggers) & set(_RISKS)) or _WORDS.search(text) is not None


def target_of(card: dict, parties: dict[str, str]) -> str:
    """The party a card may be passed to: its `for`, when that is a party that exists other than the one asking (`parties`: slug → title; a title in any case is its slug too), the
    question is not about the project (a project question is kept as a fact: it is the person's) and `person_only` does not hold it back. "" means the person's."""
    want = str(card.get("for") or "").strip().lower()
    if not want or want == idea_questions.PERSON or card.get("project") or person_only(card):
        return ""
    to = next((s for s, t in parties.items() if want in (s.lower(), str(t).strip().lower())), "")
    return "" if to == card.get("by") else to


def answer_of(got: object, card: dict) -> tuple[str, str] | None:
    """What the answering party said, `{can, pick|text}`, as a person's answer to the card would be: `(text, how)` ("pick" or "text"); None when it says it cannot, says nothing that is
    a choice of the card's or any words, or is no object. `can` must be true: an answer without it is not one."""
    if not isinstance(got, dict) or got.get("can") is not True:
        return None
    pick = got.get("pick")
    if isinstance(pick, str):
        pick = next((n for n, c in enumerate(card.get("choices") or []) if c.lower() == " ".join(pick.split()).lower()), None)
    said = {"pick": pick, "text": got.get("text") if isinstance(got.get("text"), str) else ""}
    return idea_questions.answer_of(card, said) if card.get("choices") else None


def id_of(idea: str, card_id: str) -> str:
    return f"{idea}{SEP}{card_id}"


def split_id(value: object) -> tuple[str, str]:
    """`(idea, card id)` of a passing question's id; ("", "") for anything else."""
    idea, sep, card_id = str(value or "").partition(SEP)
    return (idea, card_id) if sep and idea and card_id else ("", "")


def row(idea: str, card: dict, left_s: int, answering: bool = False) -> dict:
    """One row of the snapshot's `passing`: `{id, idea, task, by, to, q, left_s, answering}`. `by` is the party that asked, `to` the party it is passed to; `task` is "" for a Talk's
    question; `left_s` the seconds left to take it or pass it now (0 once it is being answered, `answering`)."""
    return {"id": id_of(idea, str(card.get("id") or "")), "idea": idea, "task": "", "by": str(card.get("by") or ""), "to": str(card.get("to") or ""), "q": str(card.get("q") or ""),
            "left_s": max(0, int(left_s)), "answering": bool(answering)}
