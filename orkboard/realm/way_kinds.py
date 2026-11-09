"""The kind of a way (docs/specs/168 J1; decisions §283.34–36, §287): every call that offers ways to the person says each way's `way_kind`, one of `KINDS`, so the page can draw the
owner's picture of it (`docs/mockups/table-template/pictures/`, one file a kind; `PICTURE` names the file). Pure: no model, no face.

    way_kinds.clean("Go on")           # "go_on": a word of the list, spelled any way; anything else, or nothing, reads `other`
    way_kinds.of(raw, n)               # n kinds from a model's `kinds` (a list in the ways' order): the missing and the unknown are `other`
    way_kinds.of_card(card)            # the kinds of a card or a question that has `choices` (an old record has no `kinds`: every way reads `other`)
    way_kinds.of_side(kind)            # a hearing's side or an objection's answer as a kind (go → go_on; drop, smaller, later)
    way_kinds.KINDS_RULE               # the one sentence that asks a model for them, said wherever ways are asked for

A way the person wrote (*Your own words*) is `other`; its picture is `own-words`.
"""
from __future__ import annotations

KINDS = ("replace", "keep", "smaller", "later", "drop", "split", "go_on", "mitigate", "accept_risk", "ask_more", "leader_decides",
         "start_again", "take", "not_a_problem", "make_it_a_goal", "other")
OTHER = "other"

PICTURE = {k: k.replace("_", "-") for k in KINDS} | {OTHER: "own-words"}      # the file of a kind in `pictures/` (without `.png`)

# A hearing's side (`realm/idea_hearing.py` KINDS) and an objection's answer (`realm/idea_objections.py` ANSWERS) as a way's kind.
_SIDES = {"go": "go_on", "drop": "drop", "smaller": "smaller", "later": "later"}

KINDS_RULE = ("`kinds` is one word for each way, in the ways' order, the kind it is: "
              + ", ".join(k for k in KINDS if k != OTHER) + " or other (none of these); name only what the way really is.")


def clean(value: object) -> str:
    """A way's kind from what a model or a record gave: a word of `KINDS` (case, spaces and hyphens do not matter), else `other`."""
    if not isinstance(value, str):
        return OTHER
    key = "_".join(value.lower().replace("-", " ").split())
    return key if key in KINDS else OTHER


def of(raw: object, n: int) -> list[str]:
    """`n` kinds, one for each way in the ways' order, from a list the model gave; a way it gave none for, or an unknown one, is `other`."""
    got = raw if isinstance(raw, list) else []
    return [clean(got[i]) if i < len(got) else OTHER for i in range(max(0, n))]


def of_card(card: object) -> list[str]:
    """The kinds of a card's or a question's `choices`, in order (a record written before kinds has none: every way reads `other`)."""
    if not isinstance(card, dict):
        return []
    return of(card.get("kinds"), len(card.get("choices") or []))


def with_kinds(card: dict) -> dict:
    """The card (or question) with its `kinds` filled to one a choice, so a row never holds a way with no kind; a card with no choices is as it was."""
    return {**card, "kinds": of_card(card)} if card.get("choices") else card


def of_side(kind: object) -> str:
    """A hearing's side or an objection's answer as a kind (`go` is *go on*); anything else is `other`."""
    return _SIDES.get(kind, OTHER) if isinstance(kind, str) else OTHER
