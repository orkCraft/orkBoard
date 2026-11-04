"""A leader's proposal and the cascade it ran (docs/specs/131-a-leaders-slices-and-the-cascade.md §B.3; decisions §233.8–§233.9, §237.6), as `gui/ideas.py`'s `Ideas` has it: the commands the decision card in the hand sends. The record
(`realm/cascades.py`) waits in the project's state folder; its Needs you row is `kind: "cascade"` (`realm/board_rows.py` lays it, a row of no goal's); the keeper made it (`core/idea_cascade.py`). Nothing changes until Confirm.

    ideas.cascades {}                              # the rows of the cascades ready, for the hand
    ideas.cascade_confirm {id, fork_answers?, text?}   # *Confirm and start*: refused while a fork has no answer (*Answer the fork first*); the entry written and committed (`keeper.write_decision`, by the person, its `changes` the record's);
                                                   # cut by the chain's slices, with no call (each changed slice replaces its old one, its *was* set); then the sections that rest on the changed decisions written again,
                                                   # a goal at work having its leaders re-plan what is left. `fork_answers`: `{slice id: "keep" | "change" | the person's words}`; `text`: the person's own wording of the decision
                                                   # (a first line that is a heading is its title). `{ok, number, title, slices, sections, left}`
    ideas.cascade_back {id}                        # *Put it back*: nothing changed, every slice stands. `{ok}`
"""
from __future__ import annotations

import re
import threading
import time
from typing import Any

from orkboard.core.idea_decide import CHANGES_MAX, POINT_CHARS, corrected, _line
from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _text, _via
from orkboard.realm import cascades as store
from orkboard.realm import event_log, journal_notes, lexicon, slices, way_down

TEXT_CHARS = 6000
_CONFIRMING = threading.Lock()                 # one Confirm at a time: the decision is written once
_CHANGES_AT_TOP = re.compile(r"\A\s*Changes:", re.I)
_POINT = re.compile(r"^\d+\.", re.M)


class CascadeMixin:
    def cascades(self, args: dict) -> dict:
        return {"cascades": store.rows(self.state_dir, self.root())}

    def _cascade_ready(self, cid: str) -> dict:
        rec = store.get(self.state_dir, cid)
        if rec is None or rec["status"] != "ready":
            raise IdeasError("No change of a decision waits here")
        return rec

    def _cascade_forks(self, rec: dict, answers: Any) -> list[tuple[dict, str, str]]:
        """`[(fork, how, words)]` for every fork of the card: `how` is `keep` (the slice stays), `change` (it takes the leader's words) or `words` (the person's own). IdeasError in plain words while a fork has no
        answer, or when `change` has no words to take."""
        answers = answers if isinstance(answers, dict) else {}
        out = []
        for f in rec.get("forks") or []:
            a = answers.get(f["slice"])
            a = " ".join(a.split())[:slices.SAYS_CHARS] if isinstance(a, str) else ""
            if not a:
                raise IdeasError(lexicon.term("answer_the_fork_first"))
            if a == "keep":
                out.append((f, "keep", ""))
            elif a == "change":
                if not f.get("says"):
                    raise IdeasError("That leader gave no words for its slice: keep it or write them")
                out.append((f, "change", f["says"]))
            else:
                out.append((f, "words", a))
        return out

    def _cascade_cut(self, rec: dict, number: int, forks: list[tuple[dict, str, str]]) -> dict:
        """The cut's answer from the chain, with no call: `{party: {says, points, replaces}}`, the proposer's slice and each agreeing step's, and each fork answered with `change` or words. One slice a party a decision
        (`slices.add_cut`): a party with several changed slices says them together and replaces them all."""
        by_id = {s["id"]: s for s in slices.read(self.state_dir)["slices"]}
        changed = [(c["party"], c["slice"], c["after"]) for c in store.chain(rec)]
        changed += [(f["party"], f["slice"], words) for f, how, words in forks if how != "keep"]
        out: dict[str, dict] = {}
        for party, sid, says in changed:
            old = by_id.get(sid)
            if old is None or old["replaced_by"]:
                continue
            got = out.setdefault(party, {"says": [], "points": [str(number)], "replaces": []})
            got["says"].append(says.rstrip("."))
            got["points"] += [p for p in old["points"] if p not in got["points"]]
            got["replaces"].append(sid)
        return {p: {"says": ". ".join(g["says"]) + ".", "points": g["points"][:slices.POINTS_MAX], "replaces": g["replaces"]} for p, g in out.items()}

    def cascade_confirm(self, args: dict) -> dict:
        cid, text = _text(args, "id", 40), args.get("text", "")
        if not isinstance(text, str):
            raise IdeasError("text is not text")
        with _CONFIRMING:
            rec = self._cascade_ready(cid)
            forks = self._cascade_forks(rec, args.get("fork_answers"))
            d = rec.get("decision") if isinstance(rec.get("decision"), dict) else {}
            title, body = corrected(text[:TEXT_CHARS], d.get("title") or rec["says"]) if text.strip() else (d.get("title") or rec["says"], d.get("text") or "")
            changes = [n for n in d.get("changes") or [] if isinstance(n, int)]
            if _CHANGES_AT_TOP.match(body):                            # the person wrote their own Changes line: theirs are the decision's
                first, _, rest = body.lstrip().partition("\n")
                changes, body = [int(x) for x in re.findall(r"\d+", first)][:CHANGES_MAX], rest.strip()
            n = len(_POINT.findall(body))
            more = [_line(f"{self._title_of(f['party'])} {lexicon.term('disagrees').lower()}: {f['why']}; " + {"keep": "its slice stays", "change": "its slice changes", "words": "the person worded it"}[how], POINT_CHARS)
                    for f, how, _w in forks]
            body = body.rstrip() + "".join(f"\n{n + k}. {p}" for k, p in enumerate(more, start=1))
            began = time.monotonic()
            try:
                out = self.keeper.write_decision(title, body, self._decision_tree(), "person", "", changes)
            except KeeperError as e:
                raise IdeasError(str(e)) from None
            if out.get("commit"):
                self._ev(event_log.BOARD_COMMITTED, args, commit=out["commit"], pages=out.get("pages") or 0, what="decision", seconds=round(time.monotonic() - began, 2))
            if out.get("held"):
                self._ev(event_log.BOARD_HELD, args, why=out["held"])
            number = out["number"]
            try:                                                       # the cut with no call: the chain's slices replace their old ones, the other parties are none (spec 131 §B.3)
                cut = self._cascade_cut(rec, number, forks)
                added = slices.add_cut(self.state_dir, number, cut)
            except Exception:
                cut, added = {}, []
            journal_notes.decision(self.state_dir, self.root(), "", number, title, [], changes)
            parties = list(dict.fromkeys(c["party"] for c in store.chain(rec) if c["party"] in cut))
            try:
                sections = way_down.pulls(self.state_dir, self.root(), "decision", changes=changes, parties=parties + [f["party"] for f, how, _w in forks if how != "keep"])["sections"]
            except Exception:
                sections = [s for s in rec.get("sections") or [] if isinstance(s, dict)]
            store.save(self.state_dir, {**rec, "status": "confirmed", "decision": {**d, "title": title, "text": body, "changes": changes, "number": number}})
        try:
            getattr(self.keeper, "slices_fold_for", lambda p: 0)([s["party"] for s in added])
        except Exception:
            pass
        after = self.keeper.cascade_after(rec, number, title, sections)
        self._ev(event_log.CASCADE_CONFIRMED, args, party=rec["party"], decision=number, slices=len(added), forks=len(forks), sections=len(after["started"]), left=len(after["left"]), via=_via(args))
        self.changed("")
        return {"ok": True, "number": number, "title": title, "slices": len(added), "sections": after["started"], "left": after["left"]}

    def cascade_back(self, args: dict) -> dict:
        cid = _text(args, "id", 40)
        with _CONFIRMING:
            rec = store.get(self.state_dir, cid)
            if rec is None or rec["status"] not in ("ready", "failed"):
                raise IdeasError("No change of a decision waits here")
            store.save(self.state_dir, {**rec, "status": "put_back"})
        self._ev(event_log.CASCADE_PUT_BACK, args, party=rec["party"], forks=len(rec.get("forks") or []), via=_via(args))
        self.changed("")
        return {"ok": True}


def cascade_commands(ideas_: Any) -> dict:
    """The cascade's commands by name (`gui/ideas.py` adds them to its table: `**cascade_commands(self)`)."""
    return {"ideas.cascades": ideas_.cascades, "ideas.cascade_confirm": ideas_.cascade_confirm, "ideas.cascade_back": ideas_.cascade_back}
