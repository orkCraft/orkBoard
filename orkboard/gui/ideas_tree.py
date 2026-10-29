"""Product's opportunity tree (docs/specs/102-the-other-maps-and-picking-on-them.md §8, realm/opportunity_tree.py), as `gui/ideas.py`'s `Ideas` has them: the commands its outcome and jobs
are read, kept, tied to goals and proposed by.

    ideas.tree {}                          # → {outcomes: [{id, text}], jobs: [{id, when, want, so, segment, by, at}], serves: [{job, goal, title, element, place}],
                                           #    tests: [{goal, experiment, title, element, place}], proposing: bool, status: "" | "asking" | "done" | "failed", error?, party}
    ideas.tree_set {outcomes?, jobs?}      # the person's (one or two outcomes `[{id?, text}]`, three to seven jobs `[{id?, when, want, so, segment}]`), kept `by: "person"`; a part not
                                           # given stays → {ok, outcomes, jobs, serves}
    ideas.tree_attach {job, goal}          # the goal serves the job (one job at most: it moves); an empty `job` detaches it → {ok, serves}
    ideas.tree_attach {goal, experiment}   # the experiment (a goal) tests the goal (one goal at most); an empty `experiment` takes the goal's off → {ok, tests}
    ideas.tree_propose {}                  # the first proposal (core/idea_tree.py) → {ok, asked: bool, why?}

A served goal's `title`, `element` and `place` ("line" | "work" | "done") are the Board's; a goal gone from the Board is left out of `serves` and `tests` (its row stays in the record until it is
detached). `tree` is data only: `party` is Product's party (or ""), `status` the first proposal's, `proposing` true while its call runs. `tree_set` and `tree_attach` refuse in plain words a
count outside the bounds, a part missing, a job or a goal that is gone; `tree_propose` is never a refusal: a call that cannot be made (no Product party, no model, a spent limit) is
`asked: false` with why. The host returns keys and data, never interface words.
"""
from __future__ import annotations

from typing import Any

from orkboard.core.idea_keeper import KeeperError
from orkboard.gui.ideas_args import IdeasError, _str
from orkboard.realm import ideas, opportunity_tree as tree


class TreeMixin:
    def _tree_goals(self) -> dict[str, dict]:
        return tree.goals(self.state_dir, self.root(False))

    def _tree_rows(self, rec: dict) -> dict:
        """The record's `serves` and `tests` with each goal's title, element and place from the Board; a goal the Board no longer has is left out."""
        known = self._tree_goals()
        serves = [{**s, **{k: known[s["goal"]][k] for k in ("title", "element", "place")}} for s in rec["serves"] if s["goal"] in known]
        tests = [{**t, **{k: known[t["experiment"]][k] for k in ("title", "element", "place")}} for t in rec["tests"] if t["goal"] in known and t["experiment"] in known]
        return {"serves": serves, "tests": tests}

    def tree(self, args: dict) -> dict:
        party = self.keeper.tree_party() if hasattr(self.keeper, "tree_party") else ""
        prop = tree.proposal(self.state_dir)
        asking = prop["status"] == "asking" and bool(party) and bool(self.keeper.busy_goal(party))      # a call lost with the process is no longer asked: the next press asks again
        status = prop["status"] if prop["status"] != "asking" or asking else ""
        rec = tree.read(self.state_dir)
        out = {"outcomes": rec["outcomes"], "jobs": rec["jobs"], **self._tree_rows(rec), "proposing": asking, "status": status, "party": party}
        return {**out, "error": prop["error"]} if prop["status"] == "failed" else out

    def tree_set(self, args: dict) -> dict:
        outcomes, jobs = args.get("outcomes"), args.get("jobs")
        if outcomes is None and jobs is None:
            raise IdeasError("Say the outcomes or the jobs")
        try:
            rec = tree.keep(self.state_dir, outcomes, jobs, "person")
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "outcomes": rec["outcomes"], "jobs": rec["jobs"], "serves": self._tree_rows(rec)["serves"]}

    def _tree_goal(self, slug: str) -> None:
        try:
            page = ideas.idea_page(self.root(False), slug)
        except (OSError, ValueError):
            page = None
        if page is None:
            raise IdeasError("That goal is gone")

    def tree_attach(self, args: dict) -> dict:
        goal = _str(args, "goal", 80).strip()
        try:
            if "experiment" in args:
                experiment = _str(args, "experiment", 80).strip()
                if goal and experiment:
                    self._tree_goal(goal)
                    self._tree_goal(experiment)
                tree.test(self.state_dir, goal, experiment)
                self.changed("")
                return {"ok": True, "tests": self._tree_rows(tree.read(self.state_dir))["tests"]}
            job = _str(args, "job", 80).strip()
            if job:
                self._tree_goal(goal)
            tree.attach(self.state_dir, job, goal)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.changed("")
        return {"ok": True, "serves": self._tree_rows(tree.read(self.state_dir))["serves"]}

    def tree_propose(self, args: dict) -> dict:
        ask = getattr(self.keeper, "tree_propose", None)
        if ask is None:
            return {"ok": True, "asked": False}
        try:
            asked = ask()
        except KeeperError as e:                                  # the keeper's refusals are plain words; none fails the caller
            return {"ok": True, "asked": False, "why": str(e)}
        self.changed("")
        return {"ok": True, "asked": asked}


def tree_commands(ideas_: Any) -> dict:
    """Product's opportunity tree's commands by name (`gui/ideas.py` adds them to its table: `**tree_commands(self)`)."""
    return {"ideas.tree": ideas_.tree, "ideas.tree_set": ideas_.tree_set, "ideas.tree_attach": ideas_.tree_attach, "ideas.tree_propose": ideas_.tree_propose}
