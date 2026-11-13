"""A word of the product's glossary (realm/lexicon.py `TERMS`): its key, its word, its plural and the spelling it had before. Pure module."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    key: str        # the concept: what it is (`track`, `phase.talk`), or the code's id of an ork (`orc.fields`)
    word: str       # its word (singular)
    many: str = ""  # its plural, when it has one
    was: str = ""   # the spelling it had before, when that differs ("" when the same)
    was_many: str = ""


def _t(key: str, word: str, many: str = "", was: str = "", was_many: str = "") -> Term:
    return Term(key, word, many, was, was_many)
