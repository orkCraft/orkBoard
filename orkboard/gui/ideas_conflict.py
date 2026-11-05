"""A conflict answered (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E1.3, decisions §254.6), as `gui/ideas.py`'s `Ideas` has it: the command the `conflict` card of the hand is answered by.

    ideas.conflict {idea, number, choice, text?}   # the conflict of the goal's decision with the earlier decision `number`, answered by `choice`:
                                                   #   `replace`: the decision keeps §N in its `changes`, so its cut of slices replaces §N's (§233.2); nothing is worded again;
                                                   #   `keep`: §N is dropped from `changes` and the decision is worded again within §N (`keeper.reword`, the line *Keep §N: <point>*);
                                                   #   `other`: the decision is worded again with the person's `text`, kept as the words to take in.
                                                   #   {ok, idea, number, choice, reworded, left, cost?}; `left` the conflicts still waiting (0: *Confirm and start* shows)

The conflict leaves the hand once answered (the row `conflict` is not made for it, realm/board_map.py). A decision confirmed already, a goal that is not at its decision, a conflict answered or none,
a choice that is none or `other` with no words is refused in plain words (`IdeasError`); a reword the keeper refuses puts the conflict back as it was. The host returns keys and data, never interface words.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import decision_conflicts, event_log, ideas, lexicon, spec_sections

CHOICES = ("replace", "keep", "other")
TEXT_CHARS = ideas.SECTION_CHARS


class ConflictMixin:
    """Needs `keeper`, `state_dir`, `root()`, `changed()` and `_ev()` (gui/ideas.py), and `_cost_of_word` (gui/ideas_refine.py)."""

    def conflict(self, args: dict) -> dict:
        slug = _text(args, "idea", 100)
        number, choice = args.get("number"), args.get("choice")
        if not isinstance(number, int) or isinstance(number, bool):
            raise IdeasError("number is not a number")
        if choice not in CHOICES:
            raise IdeasError("The choice is replace, keep or other")
        words = _str(args, "text", TEXT_CHARS).strip()
        if choice == "other" and not words:
            raise IdeasError("Write what you want instead")
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        if self.keeper.busy(slug):
            raise IdeasError("The keeper is busy with this goal: a moment")
        before = self._conflict_answered(slug, number, choice)
        say = ""
        if choice != "replace":
            point = next(c["point"] for c in decision_conflicts.kept(before) if c["number"] == number)
            say = f"{lexicon.term('keep_decision').replace('<n>', str(number))}: {point}" if choice == "keep" else words
        out: dict[str, Any] = {"ok": True, "idea": slug, "number": number, "choice": choice, "reworded": False}
        try:
            if say:
                self.keeper.reword(slug, say)
                out.update(reworded=True, cost=self._cost_of_word(slug))
            else:
                self.keeper.ripe_begin(slug)                      # the leaders' wait begins when the last conflict is answered (nothing starts by itself before)
        except KeeperError as e:
            self._conflict_restore(slug, before)
            raise IdeasError(str(e)) from None
        out["left"] = len(decision_conflicts.open_of(spec_sections.record(self.state_dir, slug).get("decision")))
        self._ev(event_log.CONFLICT_ANSWERED, args, idea=slug, number=number, choice=choice)
        self.changed(slug)
        return out

    def _conflict_answered(self, slug: str, number: int, choice: str) -> dict:
        """The conflict marked answered and §N put in or out of the decision's `changes`; the decision as it was is returned (to be put back). IdeasError for what cannot be answered now."""
        with ideas.LOCK:
            way = spec_sections.record(self.state_dir, slug)
            d = way.get("decision") if isinstance(way.get("decision"), dict) else None
            if ideas.state(self.state_dir, slug)["state"] != "decided" or d is None:
                raise IdeasError("This goal has no decision to answer now")
            if d.get("confirmed"):
                raise IdeasError("This goal is agreed: ask its leader for a change")
            mine = decision_conflicts.kept(d)
            if not any(c["number"] == number and not c["answer"] for c in mine):
                raise IdeasError("That conflict is answered, or there is none")
            changes = [n for n in d.get("changes") or [] if isinstance(n, int) and not isinstance(n, bool)]
            if choice == "replace" and number not in changes:
                changes.append(number)
            if choice == "keep":
                changes = [n for n in changes if n != number]
            way["decision"] = {**d, "changes": changes, "conflicts": [{**c, "answer": choice} if c["number"] == number else c for c in mine]}
            spec_sections.save_record(self.state_dir, slug, way)
            return d

    def _conflict_restore(self, slug: str, before: dict) -> None:
        with ideas.LOCK:
            way = spec_sections.record(self.state_dir, slug)
            if isinstance(way.get("decision"), dict) and not way["decision"].get("confirmed"):
                way["decision"] = before
                spec_sections.save_record(self.state_dir, slug, way)


def conflict_commands(c: Any) -> dict:
    """The conflict's command by name (`gui/ideas.py` adds it to its table: `**conflict_commands(self)`)."""
    return {"ideas.conflict": c.conflict}
