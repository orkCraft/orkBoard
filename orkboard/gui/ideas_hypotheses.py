"""Hypotheses on Product's map (docs/specs/116-hypotheses-on-products-tree.md §4; decisions §194), as `gui/ideas.py`'s `Ideas` has them: the commands the person keeps, tests and judges
them by. The record is `realm/hypotheses.py`'s; the row *Did it hold?* that asks for a verdict is `realm/board_rows.py`'s (`hypothesis`).

    ideas.hypotheses {}                       # → {items: [item], party, proposing, status}; an item is the record's with `state` as shown (`testing` while a test is in line or at work)
                                              #    and `tests`/`rests` as [{slug, title, element, place}] ("line" | "work" | "done"; a goal gone from the Board is left out)
    ideas.hypothesis_set {id?, text, signal, axis?, on?, refuted?, if_holds?}   # the person's: no `id`, a new one, `open` at once; with an `id`, the words changed (those given) → {ok, item}
                                              #    `signal` is *Holds when*; `refuted` a list of `{name, when, change?}` (one to three ways it is refuted), `if_holds` what changes if it holds (spec 133 A)
    ideas.hypothesis_keep {id}                # a proposed one becomes open → {ok, item}
    ideas.hypothesis_drop {id}                # the hypothesis gone → {ok}
    ideas.hypothesis_attach {id, goal?, test?}   # `goal` rests on it, `test` tests it (a goal tests one hypothesis at most: it moves); an empty `id` detaches the goal / the test → {ok, item | null}
    ideas.hypothesis_evidence {id, text, ref?}   # a line of what was found → {ok, item}
    ideas.hypothesis_judge {id, state, why?, way?, draft?}  # `state` held | refuted | unsure → {ok, item, decision?, way?}. Held and refuted write a decision (`keeper.write_decision`: `Hypothesis held: <text>`,
                                              #    its body the draft (`draft`, the person's own words, else `hypotheses.draft`: what changes if it holds / if it is refuted this way), then the signal, the evidence,
                                              #    the tests' titles and the why; a refuted one with a way opens with `Refuted: <name> — <when>`) and keep its number in the verdict; `way` the way it is
                                              #    refuted that was met (spec 133 A.1); unsure keeps it open, the why its evidence
    ideas.hypotheses_propose {}               # the leaders' proposal (core/idea_hypotheses.py) → {ok, asked: bool, why?}

**The project's own hypotheses file** (spec 133 C): where the project keeps one (`<state>/project.json` `hypotheses`, else `docs/hypotheses.md`, read in the Board's tree as the decisions file is) it is the source:
every command below that changes a hypothesis writes it into the file and commits it with the Board's pages (`BoardTree.edit_file`), and `ideas.hypotheses` says its path as `file` ("" with none).

`hypotheses` is data only: `party` is Product's party (or ""), `proposing` true while a proposal runs, `status` the last proposal's ("" · asking · done · failed, `core/idea_hypotheses.py`) with its `error` when it has one. Every command but `hypotheses_propose`
refuses in plain words (`IdeasError`): a hypothesis gone or judged already, no words, a bound passed (seven open, twelve waiting, forty in all), a job or a goal that is gone, a verdict on a
hypothesis not yet kept, a decision that could not be written (then the hypothesis stays as it was). `hypotheses_propose` is never a refusal: a call that cannot be made is `asked: false` with
why. The host returns keys and data, never interface words.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from orkboard.core.idea_decide import TITLE_CHARS
from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str
from orkboard.realm import board_rows, event_log, findings, findings_gather, hypotheses, hypotheses_bind, hypotheses_file, idea_element, ideas, journal_notes, opportunity_tree as tree

DRAFT_WORDS = 6000                          # the person's own words for the decision, at most (as the decision card's text)
NO_PROPOSAL = "Proposing hypotheses is not in this build yet"
_JUDGING = threading.Lock()                 # one verdict at a time: the decision is written once, then the hypothesis is judged with its number


class HypothesesMixin:
    # -- as shown -------------------------------------------------------------------------------------------------------------------------------

    def _hyp_goals(self, slugs: list[str]) -> dict[str, dict]:
        """`{slug: {slug, title, element, place}}` of the goals among `slugs` that the Board's pages still have."""
        pages = self.root(False)
        out: dict[str, dict] = {}
        for slug, place in board_rows.places_of(self.state_dir, pages, slugs).items():
            page = ideas.idea_page(Path(pages), slug)
            out[slug] = {"slug": slug, "title": " ".join(((page.title if page else "") or slug).split())[:80], "element": idea_element.of(self.state_dir, slug), "hue": idea_element.hue_of(self.state_dir, slug), "place": place}
        return out

    def _hyp_shown(self, items: list[dict]) -> list[dict]:
        """The items with `state` as shown and each goal of `tests` and `rests` with its title, element and place."""
        known = self._hyp_goals([s for i in items for s in (*i["tests"], *i["rests"])])
        places = {s: g["place"] for s, g in known.items()}
        return [{**i, "state": hypotheses.state_of(i, places), "tests": [known[s] for s in i["tests"] if s in known], "rests": [known[s] for s in i["rests"] if s in known]} for i in items]

    def _hyp_item(self, id: str) -> dict:
        return self._hyp_shown([next(i for i in hypotheses.read(self.state_dir)["items"] if i["id"] == id)])[0]

    # -- the project's file ---------------------------------------------------------------------------------------------------------------------

    def _hyp_ready(self) -> None:
        """The record knows where the project's hypotheses file is and how it is written (the Board's tree: one commit with its pages): found as the decisions file is, bound the first time (the
        record's own items are taken into it), the writer given again at every command. IdeasError in plain words when the file cannot be taken."""
        tree_ = self._decision_tree()
        hypotheses.set_writer(self.state_dir, self._hyp_put(tree_) if tree_ is not None else None)
        chosen = (ideas._json(self.state_dir / "project.json") or {}).get("hypotheses")
        rel = hypotheses_file.find(hypotheses_bind.base(self.state_dir), chosen.strip() if isinstance(chosen, str) else "")
        if rel and hypotheses_bind.file(self.state_dir) != rel:
            try:
                hypotheses.bind(self.state_dir, rel)
            except ValueError as e:
                raise IdeasError(str(e)) from None

    def _hyp_put(self, tree_):
        def put(rel: str, edit, message) -> None:
            began = time.monotonic()
            out = tree_.edit_file(rel, edit, message)
            if out.get("commit"):
                self._ev(event_log.BOARD_COMMITTED, commit=out["commit"], pages=out.get("pages") or 0, what="hypothesis", seconds=round(time.monotonic() - began, 2))
            if out.get("held"):
                self._ev(event_log.BOARD_HELD, why=out["held"])
        return put

    def hypotheses(self, args: dict) -> dict:
        try:
            self._hyp_ready()
        except IdeasError:
            pass                                                           # the list is still shown (from the record); the next change says why
        party = self.keeper.tree_party() if hasattr(self.keeper, "tree_party") else ""
        prop = self.keeper.hypotheses_proposal() if hasattr(self.keeper, "hypotheses_proposal") else {"status": "", "error": ""}     # core/idea_hypotheses.py: a run lost with the process reads as none
        out = {"items": self._hyp_shown(hypotheses.read(self.state_dir)["items"]), "party": party, "proposing": prop.get("status") == "asking", "status": prop.get("status") or "",
               "file": hypotheses_bind.file(self.state_dir) or ""}
        return {**out, "error": prop["error"]} if prop.get("error") else out

    # -- the person's ---------------------------------------------------------------------------------------------------------------------------

    def _hyp_on(self, on: str) -> None:
        rec = tree.read(self.state_dir)
        if on and on not in {*(j["id"] for j in rec["jobs"]), *(o["id"] for o in rec["outcomes"])}:
            raise IdeasError("That job is gone")

    def hypothesis_set(self, args: dict) -> dict:
        self._hyp_ready()
        id = _str(args, "id", 60).strip()
        words: dict = {k: _str(args, k, 400) for k in ("text", "signal", "axis", "on", "if_holds") if k in args}
        if "refuted" in args:
            if not isinstance(args["refuted"], list):
                raise IdeasError("refuted is not a list of ways")
            words["refuted"] = args["refuted"]
        if "on" in words:
            words["on"] = words["on"].strip()
            self._hyp_on(words["on"])
        try:
            if id:
                item = hypotheses.edit(self.state_dir, id, **words)
            else:
                item = hypotheses.add(self.state_dir, words.get("text", ""), words.get("signal", ""), axis=words.get("axis", ""), on=words.get("on", ""), refuted=words.get("refuted", ()),
                                      if_holds=words.get("if_holds", ""))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "item": self._hyp_item(item["id"])}

    def hypothesis_keep(self, args: dict) -> dict:
        self._hyp_ready()
        try:
            item = hypotheses.keep(self.state_dir, _str(args, "id", 60).strip())
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "item": self._hyp_item(item["id"])}

    def hypothesis_drop(self, args: dict) -> dict:
        self._hyp_ready()
        try:
            hypotheses.drop(self.state_dir, _str(args, "id", 60).strip())
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True}

    def _hyp_goal(self, slug: str) -> None:
        try:
            page = ideas.idea_page(self.root(False), slug)
        except (OSError, ValueError):
            page = None
        if page is None:
            raise IdeasError("That goal is gone")

    def hypothesis_attach(self, args: dict) -> dict:
        id, goal, test = (_str(args, k, 80).strip() for k in ("id", "goal", "test"))
        self._hyp_ready()
        try:
            for slug in (goal, test) if id else ():
                if slug:
                    self._hyp_goal(slug)
            item = hypotheses.attach(self.state_dir, id, goal=goal, test=test)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "item": self._hyp_item(item["id"]) if item else None}

    def hypothesis_evidence(self, args: dict) -> dict:
        self._hyp_ready()
        try:
            item = hypotheses.evidence(self.state_dir, _str(args, "id", 60).strip(), _str(args, "text", 400), _str(args, "ref", 80).strip())
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "item": self._hyp_item(item["id"])}

    # -- the verdict ----------------------------------------------------------------------------------------------------------------------------

    def _hyp_body(self, item: dict, why: str, state: str = "", way: str = "", draft: str = "") -> str:
        """The decision's body: the draft (the person's own words, else what the item says changes), a refuted way's line, then the signal, the evidence's lines, the tests' titles and the why
        (each part only when there is one; with no draft and no way it is as it was before spec 133)."""
        titles = [g["title"] for g in self._hyp_goals(item["tests"]).values()]
        parts = [draft.strip() or hypotheses.draft(item, state, way)] if state else []
        ways = {w["name"]: w for w in item["refuted"]}
        if state == "refuted" and way in ways:
            parts.append(f"Refuted: {way + ' — ' if way else ''}{ways[way]['when']}")
        parts = [p for p in parts if p]
        parts.append(f"Signal: {item['signal']}")
        if item["evidence"]:
            parts.append("Evidence:\n" + "\n".join(f"- {e['text']}" + (f" ({e['ref']})" if e["ref"] else "") for e in item["evidence"]))
        if titles:
            parts.append("Tests: " + "; ".join(titles))
        if why:
            parts.append(f"Why: {why}")
        return "\n\n".join(parts)

    def hypothesis_judge(self, args: dict) -> dict:
        id, state = _str(args, "id", 60).strip(), _str(args, "state", 20).strip()
        why = " ".join(_str(args, "why", 400).split())[:hypotheses.TEXT_CHARS]
        way, draft = _str(args, "way", 80).strip(), _str(args, "draft", DRAFT_WORDS)
        self._hyp_ready()
        if state not in hypotheses.VERDICTS:
            raise IdeasError("A hypothesis held, was refuted or is not sure yet")
        with _JUDGING:
            item = next((i for i in hypotheses.read(self.state_dir)["items"] if i["id"] == id), None)
            if item is None:
                raise IdeasError("That hypothesis is gone")
            if item["state"] == "proposed":                                     # refused here too, before a decision is written that no verdict would follow
                raise IdeasError("Keep the hypothesis before judging it")
            if item["state"] in hypotheses.JUDGED:
                raise IdeasError("That hypothesis is judged already")
            try:                                                               # a way that does not fit is refused before any decision is written
                way = hypotheses._pick_way(item, state, way)
            except ValueError as e:
                raise IdeasError(str(e)) from None
            out: dict = {}
            if state != "unsure":
                began = time.monotonic()
                try:
                    out = self.keeper.write_decision(f"Hypothesis {state}: {item['text']}"[:TITLE_CHARS], self._hyp_body(item, why, state, way, draft), self._decision_tree())
                except KeeperError as e:
                    raise IdeasError(str(e)) from None
                if out.get("commit"):
                    self._ev(event_log.BOARD_COMMITTED, commit=out["commit"], pages=out.get("pages") or 0, what="decision", seconds=round(time.monotonic() - began, 2))
                if out.get("held"):
                    self._ev(event_log.BOARD_HELD, why=out["held"])
                try:                                                            # a decision with no goal is cut into the leaders' slices too (spec 131 §A.2)
                    getattr(self.keeper, "slices_cut", lambda n: False)(out.get("number") or 0)
                except Exception:
                    pass
            try:
                judged = hypotheses.judge(self.state_dir, id, state, why, out.get("number") or 0, way)
            except ValueError as e:
                raise IdeasError(str(e)) from None
        if state != "unsure":
            journal_notes.hypothesis(self.state_dir, "", item["text"], state, why, out.get("number") or 0)      # the project's journal (spec 125 B)
        finding = self._hyp_finding(judged) if state == "refuted" else ""
        self.changed("")
        return {"ok": True, "item": self._hyp_item(judged["id"]), **({"finding": finding} if finding else {}), **({"decision": {k: out.get(k) for k in ("number", "path", "commit", "held")}} if out else {}), **({"way": way} if state == "refuted" else {})}

    def _hyp_finding(self, item: dict) -> str:
        """A refuted hypothesis is a finding (spec 133 D; decisions §235.5): one finding of no goal naming the goals that rested on it, the outcome kept in the quality record of each goal that tested it, the
        run that has Product's leader tell it and the Orkmaster sort it begun. Never fails the verdict: "" when nothing could be kept. → the finding's id."""
        try:
            party = self.keeper.tree_party() if hasattr(self.keeper, "tree_party") else ""
            rests = self._hyp_goals(item["rests"])
            got = findings_gather.hypothesis(self.state_dir, item, party, [(s, g["title"]) for s, g in rests.items()])
            if not got:
                return ""
            hypotheses.set_finding(self.state_dir, item["id"], got["id"])
            for slug in self._hyp_goals(item["tests"]):
                findings.save_record(self.state_dir, slug, hypothesis={"id": item["id"], "text": item["text"], "state": "refuted", "way": item["verdict"].get("way") or "", "why": item["verdict"].get("why") or "",
                                                                       "at": item["verdict"].get("at") or ""})
            getattr(self.keeper, "findings_begin", lambda slug: False)("")
            return got["id"]
        except Exception:
            return ""

    # -- a goal sent with a hypothesis as a mark ------------------------------------------------------------------------------------------------

    def hypothesis_marked(self, slug: str, marks: list[dict], experiment: bool) -> None:
        """A new goal sent with the mark of a hypothesis (`{map: "product", id: "hyp:<id>"}`: the tree's *Test it*, or a pick of its card): an experiment becomes the first hypothesis marked's
        test, any other goal rests on each hypothesis marked. A hypothesis gone or full is left out: a mark is never a reason for the goal not to be added."""
        ids = list(dict.fromkeys(str(m["id"])[4:] for m in marks if m.get("map") == "product" and str(m.get("id") or "").startswith("hyp:")))
        tested = not experiment
        for id in ids:
            try:
                hypotheses.attach(self.state_dir, id, **({"goal": slug} if tested else {"test": slug}))
            except ValueError:
                continue
            tested = True

    # -- the leaders' proposal ------------------------------------------------------------------------------------------------------------------

    def hypotheses_propose(self, args: dict) -> dict:
        ask = getattr(self.keeper, "hypotheses_propose", None)
        if ask is None:
            return {"ok": True, "asked": False, "why": NO_PROPOSAL}
        try:
            asked = bool(ask())
        except KeeperError as e:                                  # the keeper's refusals are plain words; none fails the caller
            return {"ok": True, "asked": False, "why": str(e)}
        self.changed("")
        return {"ok": True, "asked": asked}


def hypotheses_commands(ideas_: Any) -> dict:
    """The hypotheses' commands by name (`gui/ideas.py` adds them to its table: `**hypotheses_commands(self)`)."""
    return {"ideas.hypotheses": ideas_.hypotheses, "ideas.hypothesis_set": ideas_.hypothesis_set, "ideas.hypothesis_keep": ideas_.hypothesis_keep, "ideas.hypothesis_drop": ideas_.hypothesis_drop,
            "ideas.hypothesis_attach": ideas_.hypothesis_attach, "ideas.hypothesis_evidence": ideas_.hypothesis_evidence, "ideas.hypothesis_judge": ideas_.hypothesis_judge,
            "ideas.hypotheses_propose": ideas_.hypotheses_propose}
