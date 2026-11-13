"""The battle and the gate, asked when their mat opens (goal "The battle and the gate", stages D and F; decisions §303). Read only: no model, no lease, no file written; neither
answer is in the snapshot (`ideas.board`). And a red gate's Fix it, by where the goal is (stages G and H; decisions §303.5): two commands, the page sends the one that fits, the host
refuses the other in words.

    ideas.battle {idea}        # {idea, against: [{number, title, point, rests: {goals, decisions, tests}}], cost: {calls, usd_high}}: one entry for each conflict of the goal's decision not answered
    ideas.gate_guards {idea}   # {idea, way: "dev" | "main", failing: [{number, title, ids}], files: [{file, ids}], agreeing: [{number, title}], cost}: the decisions the gate's tests name;
                               #   `cost` on the way to dev what its stage again is capped at (core/idea_fix_stage.py `COST`: not known yet), None on the way to main.
                               #   The §N are the ones the gate's record kept, read in the tree the gate ran in (`named`, stage N3); a record written before that is read here
                               #   in the person's checkout
    ideas.gate_fix_goal {idea, from}            # a goal done in dev whose way to main went red: a new goal *Fix: <the failing tests>* marked `fixes: <idea>`, routed to Tech, laid as
                                                #   `ideas.add` lays one, no model; one press, its Undo (`ideas.undo {idea}`) removes it while it is as laid. The done page is never touched
    ideas.gate_fix_stage {idea, sealed, from}   # a goal unmerged on its own branch whose way to dev went red: its stage again (core/idea_fix_stage.py), only on its seal, its cost said
                                                #   before (`ideas.gate_guards`' `cost`); `{ok, idea, task, ids, cost}`
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.core import idea_fix_stage, idea_undo
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import chronicle_decisions, decision_conflicts, decision_refs, decisions_log, event_log, goal_branch, goal_phase, goal_route, idea_element, ideas, lexicon, spec_sections

NAMED_MAX = 3          # the §N one failing test is read for
TITLE_CHARS = 80       # a Fix goal's first line names its failing tests up to this; its Gist names every one


def _short(text: str, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip(", ") + "…"


def _titles(repo: Path) -> dict[int, str]:
    """The decisions log's titles by number; empty where the project keeps no log."""
    got = decisions_log.path(repo)
    try:
        if got.is_dir():
            rows = chronicle_decisions.read(got)
        elif got.is_file():
            rows = chronicle_decisions.read(got.read_text(encoding="utf-8", errors="replace"))
        else:
            return {}
    except (OSError, ValueError):
        return {}
    return {r["number"]: str(r.get("title") or "") for r in rows}


class Battle:
    """Over the Board's `Ideas`, as `gui/ideas_mats.py`'s `Mats`."""

    def __init__(self, ideas_: Any) -> None:
        self.i = ideas_

    def _goal(self, args: dict) -> str:
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.i.root(make=False), slug) is None:
            raise IdeasError(f"No goal {slug!r}")
        return slug

    def battle(self, args: dict) -> dict:
        slug = self._goal(args)
        repo = Path(self.i.host.repo_root)
        titles = _titles(repo)
        decision = spec_sections.record(self.i.state_dir, slug).get("decision")
        against = [{"number": c["number"], "title": titles.get(c["number"], ""), "point": c["point"], "rests": decision_refs.rests_on(repo, c["number"])}
                   for c in decision_conflicts.open_of(decision)]
        return {"idea": slug, "against": against, "cost": self.i._cost_of_word(slug)}

    def _last_gate(self, slug: str) -> tuple[str, list[str], list[str], dict | None]:
        """(way, the failing test ids, the test files the run ran, what they name read where it ran) of the goal's last gate: on its branch unmerged, the way to dev
        (stage E's record); else the way to main (the checks' records). The last is None for a record written before the §N were kept with it (stage N3)."""
        if goal_branch.in_use(self.i.state_dir, slug):
            rec = goal_branch.read(self.i.state_dir, slug)
            named = rec.get("named") if isinstance(rec.get("named"), dict) else None
            return "dev", [str(x) for x in rec.get("failing") or []], [str(x) for x in rec.get("files") or []], named
        with self.i._main_lock:
            steps = [s for s in (self.i._main_checks.get(slug) or {}).get("checks") or [] if s.get("failures") or s.get("files")]
        ids = [str(f["id"]) for s in steps for f in s.get("failures") or [] if isinstance(f, dict) and f.get("id")]
        files = [str(x) for s in steps for x in s.get("files") or []]
        kept = [s.get("named") for s in steps]
        named = None if not all(isinstance(k, dict) for k in kept) else {
            "failing": [g for k in kept for g in k.get("failing") or []], "files": sorted({n for k in kept for n in k.get("files") or []}),
            "titles": {t: v for k in kept for t, v in (k.get("titles") or {}).items()}}
        return "main", list(dict.fromkeys(ids)), list(dict.fromkeys(files)), named

    def gate_guards(self, args: dict) -> dict:
        slug = self._goal(args)
        way, ids, ran, named = self._last_gate(slug)
        repo = Path(self.i.host.repo_root)
        titles = _titles(repo)
        if named is None:                                     # a record written before the §N were kept where the gate ran: read in the person's checkout, as before
            named = {"failing": decision_refs.guards(repo, ids, limit=NAMED_MAX), "files": decision_refs.named_by(repo, ran), "titles": {}}
        titles.update({int(k): str(v) for k, v in (named.get("titles") or {}).items() if str(k).isdigit() and v})     # the titles where the gate ran win
        read = {str(g.get("id")): g for g in named.get("failing") or [] if isinstance(g, dict)}
        by_number: dict[int, list[str]] = {}
        by_file: dict[str, list[str]] = {}
        for tid in ids:
            got = read.get(tid) or {}
            if got.get("decisions"):
                for n in got["decisions"]:
                    by_number.setdefault(int(n), []).append(tid)
            else:
                by_file.setdefault(str(got.get("file") or tid.split("::")[0]), []).append(tid)
        cost = dict(idea_fix_stage.COST) if way == "dev" else None           # what its stage again is capped at: the runner gives a task's run no cap, so not known yet
        return {"idea": slug, "way": way,
                "failing": [{"number": n, "title": titles.get(n, ""), "ids": v} for n, v in sorted(by_number.items())],
                "files": [{"file": f, "ids": v} for f, v in sorted(by_file.items())],
                "agreeing": [{"number": n, "title": titles.get(n, "")} for n in sorted({int(x) for x in named.get("files") or []}) if n not in by_number],
                "cost": cost}


    # -- a red gate's Fix it, by where the goal is (decisions §303.5) -------------------------------------------------------------

    def gate_fix_goal(self, args: dict) -> dict:
        """After dev: a goal done whose way to main went red lays a new Fix goal, one press, no model. Its Undo is kept on the done goal (`core/idea_undo.py` `fix_goal`)
        and `move_played` logged with its `from`; the done goal's page and state are never touched. Refused in words, nothing written, on a goal not done in dev
        (its stage runs again: `ideas.gate_fix_stage`) and on one whose way to main named no failing test."""
        slug, i = self._goal(args), self.i
        if goal_branch.in_use(i.state_dir, slug) or ideas.state(i.state_dir, slug)["state"] != "done":
            raise IdeasError(lexicon.term("fix_not_done"))
        _way, ids, _ran, _named = self._last_gate(slug)
        if not ids:
            raise IdeasError(lexicon.term("fix_not_red").replace("<way>", "main"))
        root = i.root()
        party = goal_route.tech_party(root)
        if not party:
            raise IdeasError(lexicon.term("fix_no_party"))
        done, named = ideas.idea_page(root, slug), ", ".join(ids)
        text = "\n".join([lexicon.term("fix_goal_title").replace("<tests>", _short(named, TITLE_CHARS)), "",
                          lexicon.term("fix_goal_named").replace("<tests>", named),
                          lexicon.term("fix_goal_of").replace("<goal>", done.title if done is not None else slug)])
        origin = args["from"] if args.get("from") in ("hand", "mat") else ""
        with ideas.LOCK:
            fix = ideas.add_idea(root, text, party, i.state_dir, queue="hold")
            page = ideas.idea_page(root, fix)
            page.set("fixes", slug)                                              # marked as the fix of the goal whose gate went red
            ideas._write(root / ideas.IDEAS / f"{fix}.md", page.text())
            i.route_save(fix, goal_route.route(i.state_dir, root, text, party))   # it waits as `routed` on Tech's route, as `ideas.add` leaves a goal: nothing drafts it
        idea_element.give(root, i.state_dir, fix)
        goal_phase.mirror(root, i.state_dir, lambda g, st, plan, asks: i._idea_needs(g, st, plan, asks, root), only=fix)      # its keys written now: the Board's commit leaves it as laid
        idea_undo.keep(i.state_dir, slug, "fix_goal", {"page": None, "state": None}, idea_undo.snapshot(root, i.state_dir, fix), i.host.publish, origin, laid=fix)
        i._ev(event_log.MOVE_PLAYED, args, idea=slug, kind="fix_goal", **{"from": origin})
        i._what[fix] = "laid"
        i.changed(fix)
        i.changed(slug)
        return {"ok": True, "idea": slug, "fix": fix, "ids": ids}

    def gate_fix_stage(self, args: dict) -> dict:
        """Before dev: a goal unmerged on its own branch whose way to dev went red runs its stage again (core/idea_fix_stage.py). Sealed: `gui/ideas_mats.py`'s `played`
        refuses it without `sealed: true` and logs `move_played` once it goes. Refused in words on a goal done in dev (a new Fix goal there: `ideas.gate_fix_goal`)."""
        slug = self._goal(args)
        if not goal_branch.in_use(self.i.state_dir, slug):
            raise IdeasError(lexicon.term("fix_in_dev"))
        runner = self.i.runner(need=True)
        self.i.wake()                                    # a goal set to work by hand: the orks are back at work first, as `ideas.start` wakes them (gui/ideas_halt.py)
        got = runner.fix_stage(slug)
        self.i.changed(slug)
        return {"ok": True, "idea": slug, **got, "cost": dict(idea_fix_stage.COST)}


def battle_commands(ideas_: Any) -> dict:
    """The battle's commands by name (`gui/ideas.py` adds them to its table: `**battle_commands(self)`)."""
    b = Battle(ideas_)
    return {"ideas.battle": b.battle, "ideas.gate_guards": b.gate_guards, "ideas.gate_fix_goal": b.gate_fix_goal, "ideas.gate_fix_stage": b.gate_fix_stage}
