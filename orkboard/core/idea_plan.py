"""The plan (core/idea_keeper.py re-exports its small helpers): a task as plan.json keeps it, the price range of its tasks, which of them are ready to start, an error as
the idea's state keeps it — and `PlanMixin`, the spec → plan.json, **by steps** (docs/specs/99-a-goals-way.md §9; decisions §117.4, §118.5, §156.13). Split from the
keeper to keep both under ~600 lines.

    keeper.plan_prompt(root, slug, step=0)   # the plan's context: a page of before, as it was; a page of the new format, the step's party's section whole, the common part and
                                             # of the other sections only *Done when* and *Will be* (realm/task_brief.py)
    keeper.plan_one(slug, was, step=0)       # the plan, one shot: the first step's (the goal's party plans it), or step `n`'s — appended to the passed plan, once the one before is merged in dev
    keeper.plan_next(slug)                   # the clock's: the goal's step is merged in dev and its route has another — its party plans that one, in the background
    keeper.write_stages(slug, plan)          # a page of before: a flat *Stages*; a page of the new format: each step's *Plan* in its party's section
    keeper.assess(slug)                      # the risk: a page of the new format keeps it in its front matter and writes no line onto a section

**A goal's route is its steps.** After the join the goal lies in its first step's party, which plans its own step; its tasks run on that party's seats (its role, tool and
tier: `goal_team`), each stamped with its `step`, `party`, `craft`, `leader` and `section` (the head it wears is its party's race: `roles.task_head`). When they are merged in
dev the goal moves into the next step's party, which plans its step and appends the tasks to the plan (their ids and to-dos numbered on); the goal is `done` when the last
step's tasks are in dev. Each step is recorded as history (`idea_route.begin`). A goal of one step, and a page of before, go as they always did.

`self` is the keeper: `ask`, `parse`, `measure`, `reads`, `target`, `role_of`, `team_lines`, `team_checks`, `idea_checks`, `sign_in_held`, `publish`, `on_plan`, `_map`, `_start`,
`_may_run`, `busy`, `wiki_root`, `state_dir`, `repo_root`, `settings`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from orkboard.realm import (collide, goal_team, goal_types, idea_change, idea_checks, idea_lens, idea_look, idea_risk, idea_route, idea_spend, idea_target, ideas, plans, releases, roles,
                            spec_sections, task_brief, tool_errors)
from orkboard.realm.idea_words import short_of

SUMMED = ("usd_low", "usd_high")
DONE_KEEP = 12                       # of the steps done, the tasks the next step's plan is told of


def _task(tid: str, title: str, brief: str, kind: str, tier: str, after: list[str]) -> dict:
    """A task of a plan as plan.json keeps it, waiting; its short name by code (the plan's answer may give its own)."""
    return {"id": tid, "title": title, "short": short_of(title),
            "brief": brief, "kind": kind, "tier": tier, "after": after, "state": "waiting",
            "branch": "", "commit": "", "session": "", "cost": None, "tokens": None, "started": "", "finished": "",
            "error": "", "note": ""}


def estimate(tasks: list[dict], tiers: list[str] | None = None, costs: dict[str, float] | None = None) -> dict:
    """The price range of the tasks, counted on the tiers they will run on (`tiers`, else their planned ones), at
    `costs` a task per tier (the board's own, `idea_spend.tier_costs`), else `plans.DEFAULT_COST`; ±50 %."""
    tiers = tiers if tiers is not None else [t.get("tier", "warrior") for t in tasks]
    costs = costs or plans.DEFAULT_COST
    base = sum(costs.get(tier, plans.DEFAULT_COST.get(tier, plans.DEFAULT_COST["warrior"])) for tier in tiers)
    return {"tasks": len(tasks), "usd_low": round(base * 0.5, 2), "usd_high": round(base * 1.5, 2)}


def readiness(data: dict) -> None:
    """A task not started yet is `ready` when what it waits for is done (its `after`, its to-dos), else `waiting`."""
    merged = {t["id"] for t in data.get("tasks") or [] if t.get("state") == "merged"}
    blocked = {f for td in data.get("todos") or [] if not td.get("done") for f in td.get("for") or []}
    for t in data.get("tasks") or []:
        if t.get("state") in ("waiting", "ready"):
            t["state"] = "ready" if set(t.get("after") or []) <= merged and t["id"] not in blocked and not idea_route.holds(data, t) else "waiting"


def _why(e: Exception) -> str:
    """An error as the idea's state keeps it (300 characters): an AI tool's failure in plain words, its own words and
    what to do (tool_errors.PLAIN_CHARS)."""
    if isinstance(e, InterruptedError):
        return "stopped"
    if isinstance(e, tool_errors.ToolError):
        return tool_errors.plainly(e)
    return (str(e) or type(e).__name__).strip()[:300]


def _kw():
    from orkboard.core import idea_keeper
    return idea_keeper


def _number(items: list[dict], prefix: str) -> int:
    """The highest number among the ids `<prefix><n>` of `items` (0 with none): the next step's ids go on from it."""
    return max((int(m.group(1)) for i in items if isinstance(i, dict) and (m := re.fullmatch(prefix + r"(\d+)", str(i.get("id") or "")))), default=0)


def shifted(data: dict, tasks: int, todos: int) -> dict:
    """A step's plan with its ids numbered on: tasks `k<n>` by `tasks`, to-dos `t<n>` by `todos`, every `after` and `for` with them."""
    def k(i: str) -> str:
        return f"k{int(i[1:]) + tasks}" if re.fullmatch(r"k\d+", i) else i

    return {**data,
            "tasks": [{**t, "id": k(t["id"]), "after": [k(a) for a in t.get("after") or []]} for t in data["tasks"]],
            "todos": [{**d, "id": f"t{int(d['id'][1:]) + todos}" if re.fullmatch(r"t\d+", str(d.get("id"))) else d.get("id"), "for": [k(f) for f in d.get("for") or []]}
                      for d in data.get("todos") or []]}


def sectioned(page: ideas.Page | None) -> bool:
    """The page is of the new format: it holds a section of a party (realm/spec_sections.py)."""
    return page is not None and bool(spec_sections.sections_of(page))


class PlanMixin:
    # -- which step, which party ------------------------------------------------------------------------------------------------------

    def _legs(self, slug: str) -> list[dict]:
        """The steps of a goal's work, `[{party, leader}]`: its route, for a page of the new format; [] for a page of before, which works as one step in its party."""
        return idea_route.way(self.wiki_root(), self.state_dir, slug) if sectioned(ideas.idea_page(self.wiki_root(), slug)) else []

    def _step_party(self, slug: str, n: int) -> str:
        """The party step `n` is the work of: the route's (the one the plan was made for, once it is), else the goal's own."""
        legs = idea_route.legs_of(ideas.plan(self.state_dir, slug)) if n > 1 else self._legs(slug)
        if legs:
            return legs[min(n, len(legs)) - 1]["party"]
        page = ideas.idea_page(self.wiki_root(), slug)
        return (page.get("track") if page is not None else "") or ideas.GENERAL

    def _into(self, slug: str, n: int) -> str:
        """The goal lies in the party of the step it is at (its leader plans, its seats do, its size is the Target): moved there before the step is planned. The party's slug."""
        party = self._step_party(slug, n)
        page = ideas.idea_page(self.wiki_root(), slug)
        if page is not None and (page.get("track") or ideas.GENERAL) != party:
            try:
                ideas.move(self.wiki_root(), slug, track=party)
            except ValueError as e:
                raise _kw().KeeperError(str(e)) from None
        return party

    def _heading(self, page: ideas.Page, party: str) -> str:
        """The `##` heading of a party's section on a page of the new format ("" on a page of before): by the party's title or slug, else the page's first section."""
        found = spec_sections.sections_of(page)
        if not found:
            return ""
        root = self.wiki_root()
        mine = spec_sections.read(page, [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)], party)["sections"]
        return next((s.title for s in mine if s.party == party and not s.older), found[0][0])

    # -- the prompt ---------------------------------------------------------------------------------------------------------------------

    def _spec_parts(self, root: Path, slug: str, page: ideas.Page, party: str, n: int) -> list[tuple[str, str]]:
        """What the plan is given of the spec: a page of before, its Gist, Done when, Out, Risks and Depends on; a page of the new format, the common part, the step's party's
        section whole, and of the other sections only their *Done when* and *Will be* (§118.5)."""
        heading = self._heading(page, party)
        got = task_brief.reading(page, heading) if heading else None
        if got is None:
            return [(name, page.section(name)) for name in idea_change.PLAN_SECTIONS]
        common = got["common"]
        parts = [("The goal, in the person's words", common.get("Asked") or common.get("Gist", "")), ("Gist", common.get("Gist", "")), ("The route", common.get("Route", "")),
                 (f"Your section, {got['own'][0]}, whole", got["own"][1])]
        parts += [(f"The section {h} of another party: only its Done when and Will be (the contract your work must not break)", text) for h, text in got["others"]]
        parts += [("Depends on", common.get("Depends on", "")), ("The last decisions", "\n".join(common.get("Decisions", "").splitlines()[-10:]))]
        return parts

    def _done_so_far(self, slug: str, n: int) -> str:
        """What the steps before `n` made, merged in dev: their tasks and what each landed (the next step's plan builds on it)."""
        plan = ideas.plan(self.state_dir, slug) or {}
        done = [t for t in plan.get("tasks") or [] if isinstance(t, dict) and idea_route.step_of(t) < n and t.get("state") == "merged"][:DONE_KEEP]
        return "\n".join(f"- {t.get('title', '')}" + (f" — {'; '.join(t.get('subjects') or [])}" if t.get("subjects") else "") for t in done)

    def plan_prompt(self, root: Path, slug: str, step: int = 0) -> str:
        """§0's `plan` context. A page of before: Gist, Done when, Out, Risks, Depends on and the goal's Summary, as it always was. A page of the new format (spec 99 §9.1, §9.3): the
        common part, the step's party's section whole (its *Will be* too), and of the other sections only *Done when* and *Will be*; for a step after the first, what the steps before
        made and the party's map at dev."""
        kw = _kw()
        n = step or 1
        page = ideas.idea_page(root, slug)
        party = self._step_party(slug, n)
        goal = next((t for t in ideas.tracks(root, make=False) if t["slug"] == party), None)
        parts = self._spec_parts(root, slug, page, party, n)
        new = sectioned(page)
        parts.append(("Its goal's summary", goal["summary"] if goal else ""))
        if told := collide.told_of(self.state_dir, slug):
            parts.append(("The Orkmaster tells you (another party's goal changed what this one rests on)", told))     # spec 71 §3
        if new:
            if n > 1 and (done := self._done_so_far(slug, n)):
                parts.append(("Made by the steps before yours (merged in dev)", done))
            if text := self._map(party):
                parts.append(("Your party's map", text))
        context = idea_target.cut(parts, idea_target.CONTEXT["plan"])
        touches = [t for t in json.loads(page.get("touches") or "[]") if isinstance(t, str)] if page.get("touches", "").startswith("[") else []
        kinds = "; ".join(f'"{k}" ({roles.KIND_LINES[k]})' for k in roles.TASK_KINDS)
        team_of = goal_team.team_of(root, party)
        if team_of:                                  # the leader does the tags it takes when no builder does
            team_of = [*team_of, goal_team.leader_of(root, party)]
        team = self.team_lines([s for s in dict.fromkeys(team_of) if s != roles.TASKMASTER])
        team += idea_look.instruction(self.state_dir, root, slug) if n == 1 else ""      # a screen's look is picked first, a task may name its screen (spec 85 §2, §3)
        checks = idea_checks.plan_lines(self.idea_checks(root, slug), self.team_checks(root, slug))
        legs = self._legs(slug)
        step_line = ""
        if new:
            title = (goal or {}).get("title") or party
            step_line = (f"\n- This is step {n} of {len(legs)} of the goal's route: plan only {title}'s own step, the tasks that make your section's Done when true and its Will be "
                         f"come about. Each party after you plans its step once yours is merged in dev: never a task for another party's section." if len(legs) > 1 else
                         "\n- Your section's Will be names the parts of your map the work changes: each task serves one of them or one of your Done when lines.")
        return f"""You are the keeper of this project's Task board. This spec goes to work: turn it into a plan. You may
read the repository (read only) to see what the work touches. {self.reads("plan", touches)}
{idea_lens.attached(self.state_dir, slug)}{goal_types.prompt_line(self.state_dir, slug)}{releases.prompt_lines(root, self.state_dir, slug)}{checks}
The spec: {page.title}
{context}
Rules:
- At most {kw.MAX_TASKS} tasks. Each is a brief another Claude session can do alone, in a worktree of the repository:
  what to change, where, and how it is tested; it names the Done when lines it proves. `after` only where a task
  needs another's result.{step_line}
- Each task's `title` is a name, 60 characters at most, the verb first (e.g. "Spawn enemies from the wave director"):
  the detail belongs in its brief.
- Each task's tag (`kind`), the kind of work it is, one of: {kinds}. Ordinary work is "code".{team}
- A task may end with two to six variants of one kind for the person to pick from instead of a change, only when the spec asks to
  choose by eye or by ear (a logo, an icon, a sound, a clip, a name or a tagline): give it `"pick": {{"n": 2 to 6, "kind": "image" |
  "audio" | "video" | "text", "ask": "<the question, one line>", "target": "<the repository path the picked one is written to>"}}`. At
  most one such task per goal at a time; never for code.
- Each task's tier, its complexity: "elder" (hard design or a wide change), "warrior" (ordinary code), "laborer"
  (small, mechanical).
- To-dos only for what a task cannot start without: a key ("secret": its title is the environment variable's name,
  e.g. API_KEY), a decision ("choice", with its choices), a yes ("confirm"), steps a person does ("instructions"), a
  file the person gives ("file": its title says what the file is, e.g. the Firebase config, google-services.json;
  `accept` the extensions it may have). Any kind may carry `steps` when the person has to do something first. Most
  plans need none. `for`: the tasks that wait for it.

Answer with one JSON object and nothing else:
{{"tasks": [{{"id": "k1", "title": "…", "short": "two or three words, 24 characters at most", "brief": "…", "kind": "code",
             "tier": "warrior", "after": []}}],
 "todos": [{{"id": "t1", "title": "…", "kind": "confirm", "why": "…", "choices": [], "steps": [], "accept": [], "for": ["k1"]}}]}}
"""

    # -- the plan ------------------------------------------------------------------------------------------------------------------------

    def plan_one(self, slug: str, was: str = "ready", step: int = 0) -> None:
        """The plan, one shot; its Stages and risk written (a page of before; a page of the new format keeps its step's *Plan* in its section and its risk in its front matter), its
        estimate by the tiers the tasks will run on; then whether it starts by itself is the face's (`on_plan`). `step` after the first (the clock's `plan_next`): the goal's route has
        another party, the plan is passed and its tasks are running: that party's tasks are appended to it, and the goal stays `working`."""
        kw = _kw()
        root = self.wiki_root()
        n = step or 1
        later = n > 1
        back = was if was in ("raw", "asks", "ready", "plan", "failed") else "ready"
        try:
            track = self._into(slug, n)
            text, *_rest = self.ask("plan", self.plan_prompt(root, slug, n))
            data = kw.make_plan(slug, self.parse(text), look="" if later else idea_look.screen_title(self.state_dir, root, slug))
            data["tasks"] = idea_checks.with_check_tasks(data["tasks"], self.idea_checks(root, slug), self.team_checks(root, slug), _task)
            team = goal_team.for_idea(root, slug)
            lead = goal_team.leader_of(root, track)
            if team and lead not in team:
                team = [*team, lead]                     # the leader does the tags it takes when no builder does
            lean = goal_team.lean_role(root, track) if track else ""         # a Lean party's leader does it all (spec 81 §2)
            for t in data["tasks"]:                      # who of the goal's team does it, by its tag (none: the project's)
                t["role"] = lean or (roles.role_for(self.state_dir, t["kind"], team)["slug"] if team else "")
            data["missing"] = goal_types.of_plan(self.state_dir, data["tasks"], team, lead) if team else []     # what no one of the party does (spec 52 §2.6)
            target = self.target()
            tiers = goal_team.tiers_of(root, track) if track else {}
            runs = [idea_target.tier_of(idea_target.task_pick(t["tier"], target, str((goal_team.seat_role(self.role_of(t), tiers) or {}).get("model") or ""))[0])
                    for t in data["tasks"]]
            data["estimate"] = estimate(data["tasks"], runs, idea_spend.tier_costs(self.state_dir))   # learned (spec 36 §6)
            self._stamp(slug, data, track, n, lead)
            if not later and len(legs := self._legs(slug)) > 1:
                data["route"] = legs                     # the steps this plan was made for: the runner and the clock read them from it, so a route is not read twice
            ids = self._save_step(slug, data, n, track)
        except Exception as e:
            if later:                                    # the plan is passed: the goal fails with why, and Start goes on from the step it was at
                ideas.save_state(self.state_dir, slug, state="failed", error="" if isinstance(e, InterruptedError) else f"No plan for the next step: {kw._why(e)}")
                self.publish(slug)
                return
            if self.sign_in_held(slug, e, back):         # it waits for the sign-in, then plans again (the clock)
                self.publish(slug)
                return
            stopped = isinstance(e, InterruptedError)
            ideas.save_state(self.state_dir, slug, state=back, error="" if stopped else f"No plan: {kw._why(e)}",
                             **({"queue": "hold"} if stopped else {}))
            return
        if self._legs(slug):
            idea_route.begin(self.state_dir, slug, n, track, lead, ids)
        if not later:
            idea_change.clear(self.state_dir, slug)      # nothing changed since this plan, and a plan change waiting was for the one before (spec 62 §1.4, §3.3)
            idea_change.drop(self.state_dir, slug)
        collide.clear_told(self.state_dir, slug)         # what the Orkmaster told it is used (spec 71 §3)
        self.write_stages(slug, {**data, "tasks": [t for t in (ideas.plan(self.state_dir, slug) or data)["tasks"] if idea_route.step_of(t) == n]} if later else data)
        self.assess(slug)
        if later:
            self._gate_step(slug, n)                     # its risk is read as the first step's: one that holds waits for the person's Start (decisions §169.3)
        ideas.save_state(self.state_dir, slug, state="working" if later else "plan", error="", held_until="", held_for="", measure=self.measure())
        self.publish(slug)
        if not later:
            self.on_plan(slug)

    def _stamp(self, slug: str, data: dict, party: str, n: int, lead: str) -> None:
        """Each task of the step is stamped with its step's party (spec 99 §9.2): `step`, `party`, and its party's `craft` and `leader` (the head it wears), `section` (the heading
        of the section it reads: realm/task_brief.py) for a page of the new format."""
        root = self.wiki_root()
        page = ideas.idea_page(root, slug)
        craft = goal_team.craft_of(root, party) if party else ""
        heading = self._heading(page, party) if sectioned(page) else ""
        for t in data["tasks"]:
            t.update(step=n, party=party, **({"craft": craft} if craft else {}), **({"leader": lead} if lead and lead != roles.TASKMASTER else {}),
                     **({"section": heading} if heading else {}))

    def _gate_step(self, slug: str, n: int) -> bool:
        """A later step was planned (its tasks lie in the plan under `plan.waits`, so the runner has not started them) and its risk assessed: `idea_risk.decide` is read as it is for the
        first step's plan. A step it holds (`wait`) stays under `waits`: the goal stays `working`, the `start` row is laid in the hand with the step's cost, and the person's *Start* lets it
        go on (`gui/ideas_route.py` `route_answer`); any other starts by itself, as before. Whether it waits."""
        page = ideas.idea_page(self.wiki_root(), slug)
        wait = page is not None and idea_risk.decide(page.get("risk"), page.get("priority")) == "wait"
        if not wait:
            def lift(p: dict) -> None:
                if (idea_route.waits(p) or {}).get("step") == n:
                    p.pop("waits", None)
                    readiness(p)                         # its tasks are ready now, as when they were appended before this gate

            ideas.edit_plan(self.state_dir, slug, lift)
        return wait

    def _save_step(self, slug: str, data: dict, n: int, party: str = "") -> list[str]:
        """The step's plan kept: the first step's replaces the plan (never a passed one), a later step's is appended to the passed plan under the lock (its ids numbered on, its
        to-dos too, the estimate summed, a task ready when what it waits for is done). The ids of the step's tasks."""
        if n == 1:
            ideas.save_plan(self.state_dir, slug, data)
            return [t["id"] for t in data["tasks"]]
        out: list[str] = []

        def add(plan: dict) -> None:
            more = shifted(data, _number(plan.get("tasks") or [], "k"), _number(plan.get("todos") or [], "t"))
            plan["tasks"] = [*(plan.get("tasks") or []), *more["tasks"]]
            plan["todos"] = [*(plan.get("todos") or []), *more["todos"]]
            plan["missing"] = more.get("missing") or []
            was = plan.get("estimate") if isinstance(plan.get("estimate"), dict) else {}
            plan["estimate"] = {"tasks": len(plan["tasks"]), **{k: round(float(was.get(k) or 0) + float(more["estimate"].get(k) or 0), 2) for k in SUMMED}}
            plan["waits"] = {"step": n, "party": party, "cost": {k: more["estimate"].get(k) for k in SUMMED}}      # held until `_gate_step` has read its risk: the runner starts none of its tasks before
            readiness(plan)
            out.extend(t["id"] for t in more["tasks"])

        ideas.edit_plan(self.state_dir, slug, add)
        return out

    # -- the next step -----------------------------------------------------------------------------------------------------------------

    def next_step(self, slug: str) -> dict | None:
        """The step to plan next for a goal at work, `{n, party, leader}`: its plan is passed, its step is merged in dev and its route has another (realm/idea_route.py)."""
        if ideas.state(self.state_dir, slug)["state"] != "working" or not sectioned(ideas.idea_page(self.wiki_root(), slug)):
            return None
        return idea_route.next_step(ideas.plan(self.state_dir, slug))

    def plan_next(self, slug: str) -> bool:
        """The goal's step is merged in dev and its route has another: that step's party plans its own step, in the background (the clock's; a window spent or a sign-in
        wanted is the clock's to wait for). False when there is nothing to plan or the keeper cannot now."""
        nxt = self.next_step(slug)
        if nxt is None or self._may_run() or self.busy(slug):
            return False
        self._start(slug, "planning", lambda: self.plan_one(slug, "working", nxt["n"]))
        return True

    # -- the page ------------------------------------------------------------------------------------------------------------------------

    def write_stages(self, slug: str, plan: dict) -> None:
        """A page of before: its flat *Stages*. A page of the new format: no flat *Stages* — each step's tasks are the *Plan* of the section they were planned for."""
        from orkboard.core.idea_draft import stages
        root = self.wiki_root()
        page = ideas.idea_page(root, slug)
        if not sectioned(page):
            ideas.update(root, slug, {"Stages": stages(plan)})
            return
        by: dict[str, list[dict]] = {}
        for t in plan.get("tasks") or []:
            if isinstance(t, dict) and t.get("section"):
                by.setdefault(str(t["section"]), []).append(t)
        with ideas.LOCK:
            page = ideas.idea_page(root, slug)
            for heading, tasks in by.items():
                text = next((x for h, x in spec_sections.sections_of(page) if h == heading), None)
                if text is None:
                    continue
                parts = spec_sections.split(text)
                parts["Plan"] = stages({"tasks": tasks})
                page.set_section(heading, spec_sections.join(parts))
            ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())

    def assess(self, slug: str) -> str | None:
        """The idea's risk from its page and plan. A page of before: written, as always (front matter `risk`, `risk_triggers`, and the Risks section's first line). A page of the new
        format: its front matter only — a section's *Risks* are its leader's words, and the line is not written onto it. The risk it had when it changed, else None."""
        root = self.wiki_root()
        page = ideas.idea_page(root, slug)
        if not sectioned(page):
            return super().assess(slug)
        with ideas.LOCK:
            page = ideas.idea_page(root, slug)
            plan = ideas.plan(self.state_dir, slug) or {}
            tasks = [t for t in plan.get("tasks") or [] if isinstance(t, dict)]
            texts = [page.title]
            for _heading, text in spec_sections.sections_of(page):
                parts = spec_sections.split(text)
                texts += [parts.get("Out", ""), parts.get("Risks", "")]
            texts += [f"{t.get('title', '')}\n{t.get('brief', '')}" for t in tasks]
            got = idea_risk.assess(ideas._json_list(page.get("touches")), texts, len(tasks), page.get("risk_model") or "low", (self.settings() or {}).get("risk_paths") or [])
            was = page.get("risk")
            page.set("risk", got.risk)
            page.set("risk_triggers", json.dumps(got.triggers, ensure_ascii=False))
            ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
        return was if was and was != got.risk else None
