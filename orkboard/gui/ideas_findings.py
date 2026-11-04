"""A goal's findings and its quality record (docs/specs/132-four-levels-the-way-down-and-findings.md D.3, D.4; decisions §234.3–§234.4, §237.1–§237.2), as `gui/ideas.py`'s `Ideas` has it: the commands the
quality card in the hand and the *Quality* page send. The record is `realm/findings.py`'s; the card's rows are gathered by `ideas.board` (`kind: "quality"`, `kind: "finding"`); the leaders' calls are
`core/idea_findings.py`'s.

    ideas.finding_fix {id}                 # *Fix it there*, by the finding's level: work → a fix goal on the finding's route, a bug (§158.3) whose diagnosis is the finding's content (no `diagnose` call), titled
                                           #   *Fix: <what>* and marked `fixes: <slug>`; spec → the same, its party's section written again from the finding before its plan (the cause the section's
                                           #   leader is given is the finding's); decision → a proposal into spec 131's cascade (`keeper.cascade_propose`, `from_step: "finding"`), refused in words
                                           #   while the keeper has no cascade. `{ok, level, fix}`; the finding is answered `fix`
    ideas.finding_fix_all {idea}           # *Fix all there*: each finding of the goal's card, in the card's order; `{ok, fixed: [{id, level, fix}], refused: [{id, why}]}`
    ideas.finding_later {id}               # *Not now*: answered `later`; it stays on the goal's quality record and leaves the hand; `{ok}`
    ideas.finding_move {id, level}         # *Another level…*: the level moved by the person, its pulls said again; `{ok, level, pulls}`
    ideas.quality {idea}                   # the record: `{idea, title, state, at, result (goal_result's), verdict, checks, lenses, hypothesis, findings}`; "" for `idea`: the findings of no goal
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import findings, goal_route, idea_questions, ideas, spec_sections

NO_CASCADE = "The decision's change comes with the cascade"
GONE = "That finding is gone"
DONE = "That finding is answered already"
TITLE_CHARS = 80


def _short(text: str, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


class FindingsMixin:
    """Needs `keeper`, `state_dir`, `root()`, `host`, `add()`, `changed()`, `_state()`, `_seam()`, `settings_now()` (gui/ideas.py and its mixins)."""

    # -- reading ------------------------------------------------------------------------------------------------------------------

    def _finding(self, args: dict) -> dict:
        f = findings.get(self.state_dir, _text(args, "id", 40))
        if f is None:
            raise IdeasError(GONE)
        return f

    def _open_finding(self, args: dict) -> dict:
        f = self._finding(args)
        if f["status"] == "answered":
            raise IdeasError(DONE)
        return f

    def quality(self, args: dict) -> dict:
        slug = args.get("idea") if isinstance(args.get("idea"), str) else ""
        root = self.root(make=False)
        page = ideas.idea_page(root, slug) if slug else None
        if slug and page is None:
            raise IdeasError("That goal is gone")
        rec = findings.record(self.state_dir, slug)
        result = None
        if slug and ideas.state(self.state_dir, slug)["state"] == "done":
            try:
                result = self.goal_result({"idea": slug})                # the verdict against the spec as the *Done* page showed it: ✓ ≠ + ✗ by *Done when*
            except Exception:
                result = None
        order = {lv: n for n, lv in enumerate(findings.LEVELS)}
        rows = sorted(rec["findings"], key=lambda f: (order.get(f["level"], len(order)), f["at"]))
        return {"idea": slug, "title": page.title if page is not None else "", "state": ideas.state(self.state_dir, slug)["state"] if slug else "", "at": rec["at"], "result": result,
                "verdict": rec["verdict"], "checks": rec["checks"], "lenses": [f for f in rows if f["source"] in ("lens", "concern")], "hypothesis": rec["hypothesis"],
                "findings": [{**f, "pulls": findings.pulls_of(self.state_dir, self.root(), f)} for f in rows]}

    # -- answering ----------------------------------------------------------------------------------------------------------------

    def _fix_goal(self, f: dict, level: str) -> str:
        """The fix goal of a finding at the Work or Spec level (see the module): held at first, then put on the short way of a bug with the finding's content as its diagnosis, and begun at its sections."""
        root = self.root()
        party = f["party"] or goal_route.tech_party(root)
        if not party or ideas.track_page(root, party) is None:
            raise IdeasError("This project has no party to fix it")
        what = f["what"] or f["found"]
        lines = [f"Fix: {_short(what, TITLE_CHARS)}", ""]
        lines += [f"{label}: {f[k]}" for label, k in (("What shows it", "shows"), ("What was promised", "promised"), ("The cause", "cause"), ("What would change", "change")) if f[k]]
        if f["idea"]:
            origin = ideas.idea_page(root, f["idea"])
            lines.append(f"Found in the goal: {origin.title if origin is not None else f['idea']}")
        slug = self.add({"text": "\n".join(lines).strip(), "party": party, "hold": True})["slug"]
        cause = f["cause"] or what
        if level == "spec":
            cause = f"The spec said the wrong thing or left it out: {cause}. Write your section again from this." if f["cause"] else f"The spec is at fault: {what}. Write your section again from this."
        with ideas.LOCK:
            page = ideas.idea_page(root, slug)
            if page is not None and f["idea"]:
                page.set("fixes", f["idea"])                                # marked as the fix of the goal it was found in
                ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
            rec = idea_questions.record(self.state_dir, slug)
            idea_questions.save_record(self.state_dir, slug, {**rec, "mode": "bug", "round": 1, "waiting": [], "done": True,
                                                              "cause": {"text": cause, "where": [f["on"]] if f["on"] and f["source"] == "verdict" else [], "by": "finding", "pending": False,
                                                                        "guesses": 1, "confirmed": True}})
            route = [goal_route.entry(root, party)]
            how = {"by": "finding", "kind": "bug", "short": True, "reproduces": True, "failure": bool(f["shows"]), "touched": [], "offer": []}
            ideas.save_state(self.state_dir, slug, state="routed", queue="", route=route, route_how=how, held_until="", held_for="", error="")
            st = self._state(slug)
            ideas.save_state(self.state_dir, slug, state="sections", route_how={**how, "said": goal_route.cost_of(root, self.state_dir, st, self.settings_now()), "said_route": route, "changed": False})
        self._seam(slug, "sections")                                         # the sections of the route's party, then its plan; a call that cannot be made puts the goal back at its route card
        return slug

    def _fix(self, f: dict) -> tuple[str, dict]:
        """One finding fixed at its level: `(level, fix)`; the finding is answered. A refusal leaves it as it was."""
        level = f["level"] or "work"
        if level == "decision":
            propose = getattr(self.keeper, "cascade_propose", None)
            if not callable(propose):
                raise IdeasError(NO_CASCADE)
            d = spec_sections.record(self.state_dir, f["idea"]).get("decision") if f["idea"] else None
            number = d.get("number") if isinstance(d, dict) else None
            got = propose(f["party"], "", f["change"] or f["what"], f["cause"] or f["found"], [str(number)] if number else [], from_step="finding", idea=f["idea"])
            fix = {"cascade": str(got.get("id") if isinstance(got, dict) else got or "")}
        else:
            fix = {"idea": self._fix_goal(f, level)}
        findings.answer(self.state_dir, f["id"], "fix", fix)
        return level, fix

    def finding_fix(self, args: dict) -> dict:
        f = self._open_finding(args)
        level, fix = self._fix(f)
        self.changed(f["idea"])
        if fix.get("idea"):
            self.changed(fix["idea"])
        return {"ok": True, "level": level, "fix": fix}

    def finding_fix_all(self, args: dict) -> dict:
        slug = args.get("idea") if isinstance(args.get("idea"), str) else ""
        waiting = [f for f in findings.of_goal(self.state_dir, slug) if f["status"] == "sorted"]
        if not waiting:
            raise IdeasError("No finding waits for this goal")
        order = {lv: n for n, lv in enumerate(findings.LEVELS)}
        fixed, refused = [], []
        for f in sorted(waiting, key=lambda f: (order.get(f["level"], len(order)), f["at"])):
            try:
                level, fix = self._fix(f)
                fixed.append({"id": f["id"], "level": level, "fix": fix})
            except IdeasError as e:
                refused.append({"id": f["id"], "why": str(e)})
        if not fixed:
            raise IdeasError(refused[0]["why"])
        self.changed(slug)
        for x in fixed:
            if x["fix"].get("idea"):
                self.changed(x["fix"]["idea"])
        return {"ok": True, "fixed": fixed, "refused": refused}

    def finding_later(self, args: dict) -> dict:
        f = self._open_finding(args)
        findings.answer(self.state_dir, f["id"], "later")
        self.changed(f["idea"])
        return {"ok": True}

    def finding_move(self, args: dict) -> dict:
        f = self._open_finding(args)
        level = _text(args, "level", 20)
        if level not in findings.LEVELS:
            raise IdeasError("A level is decision, spec or work")
        got = findings.move(self.state_dir, f["id"], level)
        self.changed(f["idea"])
        return {"ok": True, "level": level, "pulls": findings.pulls_of(self.state_dir, Path(self.root()), got or f, level)}


def findings_commands(ideas_: Any) -> dict:
    """The findings' commands by name (`gui/ideas.py` adds them to its table: `**findings_commands(self)`)."""
    return {"ideas.finding_fix": ideas_.finding_fix, "ideas.finding_fix_all": ideas_.finding_fix_all, "ideas.finding_later": ideas_.finding_later,
            "ideas.finding_move": ideas_.finding_move, "ideas.quality": ideas_.quality}
