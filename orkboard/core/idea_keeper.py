"""The board's keeper (spec 29a §4, decisions §43, §47; docs/specs/35-goals-window.md): it reads goals, drafts each
idea straight into its spec, talks a spec through with the person, and turns a spec into a plan.

    keeper = IdeaKeeper(repo_root, state_dir, wiki_root=lambda: root, settings=lambda: machine.ideas,
                        publish=lambda slug: ..., limits=lambda: town.limits, on_plan=autostart)
    keeper.draft(slug)                # an idea → its spec (core/idea_draft.py), then its plan when it asks nothing
    keeper.answer(slug, ["…", "…"])   # the person answers the spec's questions at once: the rest is written, then the plan
    keeper.say(slug, "Why not a toggle?", "Risks")    # an edit of one section, in the background
    keeper.plan(slug)                 # Re-plan: the page → plan.json, with its estimate (the first step's; the next steps are planned by `tick`, core/idea_plan.py)
    keeper.revise(slug)               # Re-plan what is left, after the start: a plan change for the tasks not started (core/idea_revise.py)
    keeper.judge(slug)                # a pitch (a goal of Ideation): its four views, the case against, the Investor's decision (core/idea_judge.py)
    keeper.read_stop(slug)            # this idea's run stops (its own cancel); its queue is `hold`
    keeper.tick()                     # the host's clock: what the limits held runs again

- **The Target** (realm/idea_target.py) picks each step's tier and effort: goal, draft, answer, talk, plan. The
  Taskmaster's own model, when it is not its default `elder`, replaces the tier; the Target still gives the effort.
- **Goal** (read-only, core/idea_goals.py): a goal saved is read at once: its title, Summary, Metrics, links, questions.
- **Draft** and **answer** (read-only, core/idea_draft.py): an idea straight to its spec; its questions answered at once.
- **One call, one job** (spec 35 §0): every call is a fresh `claude -p` (never `--resume`, no session kept), given only
  what its step needs, cut to `idea_target.CONTEXT`, with its budget (`--max-budget-usd`). The page is the memory; the
  talk is archived in `talk.jsonl` and never read back into a model. One round of questions: the `answer` call asks
  nothing more. Each call is measured (`step`, `prompt_chars`, `tokens`, `cost`) on the keeper's events, and its line
  goes to the ledger (realm/idea_spend.py, spec 36 §1).
- **Plan**: the page → `plan.json` (at most 8 tasks), its Stages and its risk written by code, the estimate from the
  tiers the tasks will run on, at what the board's last tasks on each cost (spec 36 §6); then `on_plan(slug)` (the face decides whether it starts by itself, spec 35 §5).
  **By steps** (spec 99 §9, core/idea_plan.py `PlanMixin`): a goal's route is its steps; the first step's party plans its own step (its section whole, of the others only *Done when*
  and *Will be*); when its tasks are merged in dev `tick` has the next step's party plan its step (`plan_next`), and so on.
- **The window** (spec 35 §6): in a spent window a call is not made; what runs by itself waits with `held_until`, a
  call the person asks for is refused in plain words.

Every model call goes through `realm/jobs.py` on the `claude` harness; its answer is untrusted: it is parsed
strictly and only known sections are written. Each change is published (`publish(slug)`: the face puts
`ideas.changed` on the bus). The keeper never commits: the pages stay in the working tree. No face.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable

from orkboard.core.idea_decide import DecideMixin
from orkboard.core.idea_draft import DraftMixin
from orkboard.core.idea_sign_in import SignInMixin
from orkboard.core.idea_goals import GoalMixin
from orkboard.core.idea_judge import JudgeMixin
from orkboard.core.idea_lead import LeadMixin
from orkboard.core.idea_revise import ReviseMixin
from orkboard.core.idea_sections import SectionsMixin
from orkboard.core.idea_objection import ObjectionMixin
from orkboard.core.idea_talk import TalkMixin
from orkboard.core.idea_project_q import ProjectQMixin
from orkboard.core.idea_ask import AskMixin
from orkboard.core.idea_loop import LoopMixin
from orkboard.core.idea_tree import TreeMixin
from orkboard.core.idea_plan import PlanMixin, _task, _why, estimate, readiness  # noqa: F401  (the plan's small helpers: the callers and tests use them from here)
from orkboard.realm import (call_log, event_log, goal_team, idea_change, idea_checks, idea_look, idea_pick, idea_spend, idea_target, ideas,
                            roles, status, tool_errors)
from orkboard.realm.idea_words import short_said, title_of

CHANGED = "ideas.changed"          # the bus's topic: slug
HARNESS = "claude"                 # the tool when a step's party has none and the machine names none (spec 81: the Main tool is the default)
MAX_TASKS, MAX_TODOS, MAX_QUESTIONS = 8, 5, 3
INDEX_CHARS, PAGE_CHARS, REPLY_CHARS = 6000, 30_000, 4000
TIERS = ("elder", "warrior", "laborer")
KINDS = ("secret", "choice", "confirm", "instructions", "file")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
TICK_S = 20.0                      # how often the clock looks for what the limits held

Call = Callable[[str, str, str, Any], tuple[str, Any, Any, str]]   # (tier, prompt, effort, budget) → (text, cost, tokens, session)
BUDGET_LINE = "the keeper ran out of its budget for this step"
PITCH_NOT_BUILT = "A pitch is judged, not built: send it to a party first"      # spec 65 §2


class KeeperError(Exception):
    """What the keeper refuses, in plain words."""


def first_json(text: str) -> dict | None:
    """The first JSON object in a model's answer (it may wrap it in prose or a code fence); None when there is none."""
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", text or ""):
        try:
            value, _end = decoder.raw_decode(text, m.start())
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _words(value: object, limit: int) -> str:
    return str(value).strip()[:limit] if isinstance(value, (str, int, float)) and not isinstance(value, bool) else ""


def _strings(value: object, limit: int, each: int = 500) -> list[str]:
    if not isinstance(value, list):
        return []
    return [s for s in (_words(v, each) for v in value) if s][:limit]


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {' '.join(q.split())}" for q in lines)


def _iso(at: float) -> str:
    return dt.datetime.fromtimestamp(at).isoformat(timespec="seconds")


class IdeaKeeper(SignInMixin, TalkMixin, ObjectionMixin, ProjectQMixin, AskMixin, LoopMixin, TreeMixin, DecideMixin, SectionsMixin, PlanMixin, DraftMixin, GoalMixin, LeadMixin, ReviseMixin, JudgeMixin):
    def __init__(self, repo_root: Path, state_dir: Path, wiki_root: Callable[[], Path],
                 settings: Callable[[], dict], publish: Callable[[str], None] = lambda slug: None,
                 demo: bool = False, budget_ok: Callable[[], bool] = lambda: True,
                 taskmaster: Callable[[], str] | None = None, limits: Callable[[], list] | None = None,
                 on_plan: Callable[[str], None] | None = None,
                 events: bool = True, sign_ins: Any = None, follow: Callable[[], str | None] | None = None) -> None:
        """`sign_ins`: the host's sign-ins (core/sign_ins.py): what runs by itself waits while Claude Code needs its
        sign-in (`held_for` "sign_in", spec 45 §6). `limits`: the quota readers' last read (spent windows hold the keeper); `on_plan(slug)`: a plan was made
        or its risk changed (the face's autostart); `events`: the keeper's own events go to the local event log (spec 35 §12).
        `follow()`: the tool now (spec 105 §2, realm/tool_now.py): where a step that follows the Main tool goes when the Main tool is out; None, or no `follow`: the Main tool."""
        self.repo_root, self.state_dir = Path(repo_root), Path(state_dir)
        self.follow = follow
        self.taskmaster = taskmaster or (lambda: (roles.role(self.state_dir, roles.TASKMASTER) or {}).get("model") or "elder")
        self._again: set[str] = set()                # a busy key asked again while it ran
        self.wiki_root, self.settings, self.publish = wiki_root, settings, publish
        self.index_root = wiki_root                  # where the Wiki's index is read (the person's Wiki, spec 35 §13)
        self.demo, self.budget_ok, self.events, self.sign_ins = demo, budget_ok, events, sign_ins
        self.limits = limits or (lambda: [])
        self.on_plan = on_plan or (lambda slug: None)
        self.call: Call = self._claude                # tests swap the model call here
        self.cancel = threading.Event()
        self._tls = threading.local()               # the idea a model call is for (its record in realm/call_log.py names it)
        self._lock = threading.Lock()
        self._busy: dict[str, str] = {}             # key → drafting | talking | planning | goal
        self._cancels: dict[str, threading.Event] = {}   # key → its run's own cancel (read_stop)
        self._tick_at = float("-inf")

    # -- the model call -------------------------------------------------------------------------------------

    def _claude(self, tier: str, prompt: str, effort: str = "", budget: float | None = None) -> tuple[str, Any, Any, str]:
        """One shot (spec 35 §0): a fresh read-only run, no session kept."""
        from orkboard.realm import harnesses, jobs
        from orkboard.sources import telemetry
        tool = self.tool_now()
        self._tls.tool = tool                                                  # the call's tool, for its ledger line even if the tool now moves while it runs
        h = harnesses.get(tool)
        purpose = {"laborer": "sort", "elder": "plan"}.get(tier, "plan")      # the Taskmaster's own model is a plan
        cancel = getattr(self._tls, "cancel", None) or self.cancel
        with telemetry.tagged(purpose, "board"), call_log.of_project(self.repo_root):     # its log and spend: ours
            got = jobs.run_read(tool, prompt, self.repo_root, cancel, h.pick(tier) if h else tier,
                                env={"ORKCRAFT_ORC": "board/keeper", "ORKCRAFT_IDEA": getattr(self._tls, "slug", "")},
                                effort=effort, budget=budget, one_shot=True, tools=getattr(self._tls, "tools", True))
        self._tls.usage, self._tls.capped = jobs.last_usage(), bool(getattr(jobs.LAST, "capped", False))
        return got

    def tool_now(self) -> str:
        """The AI tool the running step goes to: its goal's leader's seat's, else its party's (set on purpose, never moved), else the Main tool, or the tool
        now while the Main tool is out (spec 81 §1.2, spec 91 §6, spec 105 §2.3); a step of no goal's, the same."""
        from orkboard.realm import harnesses
        goal = self.goal_of_key(getattr(self._tls, "key", "") or getattr(self._tls, "slug", "") or "")
        tool = goal_team.tool_for(self.wiki_root(), goal, goal_team.leader_of(self.wiki_root(), goal)) if goal else ""
        if harnesses.get(tool) is not None:
            return tool
        from orkboard import settings as machine
        main = machine.main_tool() or HARNESS
        try:
            return (self.follow(reserve=False) if self.follow is not None else None) or main      # a keeper's step is the person's: it may spend the reserve (decisions §177.10)
        except Exception:                              # a host that cannot say leaves the step on the Main tool
            return main

    def target(self) -> str:
        """The Target the running step works at: its goal's party's size, else the setting (spec 75 §3); a step of no goal's, the setting."""
        goal = self.goal_of_key(getattr(self._tls, "key", "") or getattr(self._tls, "slug", "") or "")
        return idea_target.target_for(self.settings(), ideas.track_page(self.wiki_root(), goal) if goal else None)

    def pick(self, step: str) -> tuple[str, str] | None:
        """The (model or tier, effort) a keeper step runs on: by the Target, its goal's leader's own model (else the
        Taskmaster's) winning."""
        lead = self.leader()
        return idea_target.keeper_pick(step, self.target(), (lead.get("model") or idea_target.TIER_ROLE) if lead else self.taskmaster())

    def ask(self, step: str, prompt: str, tools: bool = True, as_role: str = "") -> tuple[str, Any, Any, str]:
        """One model call on a step, measured; a run stopped meanwhile (its own cancel or Stop all) raises
        InterruptedError; one that ran out of its budget with nothing to use raises KeeperError with BUDGET_LINE.
        `as_role`: a role's slug the call speaks as, not the goal's leader (a pitch's views: core/idea_judge.py)."""
        got = self.pick_as(step, as_role) if as_role else self.pick(step)
        if got is None:
            raise KeeperError(f"The Target {self.target()} makes no {step} call")
        if as_role:
            prompt = self.speak_as(as_role) + prompt
        elif lead := self.leader():                  # the goal's leader: its voice and instruction first
            prompt = self.voice(lead) + prompt
        elif told := str((roles.role(self.state_dir, roles.TASKMASTER) or {}).get("instruction") or "").strip():
            prompt = f"{told}\n\n{prompt}"            # the person's words for the Taskmaster (spec 41 §8)
        self._tls.picked, self._tls.tools, self._tls.usage, self._tls.capped, self._tls.as_role = got, tools, None, False, as_role
        self._tls.tool = ""                                                    # set by the call that runs (`_claude`), read by its ledger line
        self._tls.measure = {"step": step, "prompt_chars": len(prompt), "tokens": None, "cost": None}
        try:
            with call_log.bounded(idea_target.READS.get(step)):       # the files its prompt names: its line says if it read more
                text, cost, tokens, session = self.call(got[0], prompt, got[1], idea_target.budget(step, self.target()))
        except Exception as e:
            if "budget" in str(e).lower() and not isinstance(e, InterruptedError):
                raise KeeperError(BUDGET_LINE) from None
            raise
        finally:
            self._tls.tools = True
        usage = getattr(self._tls, "usage", None)
        self._tls.measure.update(tokens=usage or ({"total": tokens} if isinstance(tokens, int) else None),
                                 cost=cost if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None)
        self._spent(step, got, usage, tokens, cost)
        cancel = getattr(self._tls, "cancel", None)
        if (cancel is not None and cancel.is_set()) or self.cancel.is_set():
            raise InterruptedError("stopped")
        return text, cost, tokens, session

    def _spent(self, step: str, got: tuple[str, str], usage: Any, tokens: Any, cost: Any) -> None:
        """The call's line in the ledger (spec 36 §1): its idea's, its goal's, or the board's own."""
        from orkboard.realm import harnesses
        tool = getattr(self._tls, "tool", "") or self.tool_now()             # the tool the call ran on, not the tool now
        h, tier = harnesses.get(tool), idea_target.tier_of(got[0])
        key = getattr(self._tls, "key", "") or getattr(self._tls, "slug", "") or ""
        where = {} if step == "kind" or (step == "ask" and not key.startswith("goal:")) else ({"goal": key[5:]} if key.startswith("goal:") else {"idea": key})
        idea_spend.append(self.state_dir, idea_spend.line(step, getattr(self._tls, "as_role", "") or roles.TASKMASTER, tool, (h.pick(got[0]) if h else "") or got[0],
                                                          tier, got[1], idea_spend.tokens_of(usage, tokens), cost), **where)

    def parse(self, text: str) -> dict:
        """The call's JSON, strictly; a run cut by its budget with no JSON says so."""
        answer = first_json(text)
        if answer is None:
            raise KeeperError(BUDGET_LINE if getattr(self._tls, "capped", False)
                              else "the keeper's answer was not the JSON it was asked for")
        return answer

    def picked(self) -> tuple[str, str]:
        return getattr(self._tls, "picked", ("", ""))

    def measure(self) -> dict:
        """The last call's measure on this thread (spec 35 §0): step, prompt_chars, tokens, cost."""
        return dict(getattr(self._tls, "measure", None) or {"step": "", "prompt_chars": 0, "tokens": None, "cost": None})

    def reads(self, step: str, files: list[str]) -> str:
        """Bounded reading (§0): the files to start from and how many it may read."""
        n = idea_target.READS.get(step, 0)
        if not n:
            return "Read no file: answer from what is here."
        start = ", ".join(files[:n]) if files else "none named"
        return f"Start from these files: {start}. Read at most {n} files in all; search only for what they don't cover."

    def _ev(self, event: str, **fields: Any) -> None:
        if self.events and not self.demo:
            event_log.record(self.repo_root, event, **fields)

    # -- what the host asks ------------------------------------------------------------------------------

    def busy(self, slug: str) -> str:
        """What the keeper does on this idea now ("" nothing)."""
        return self._busy.get(slug, "")

    def busy_goal(self, slug: str) -> str:
        return self._busy.get(f"goal:{slug}", "")

    def stop_all(self) -> None:
        """Stop all: every run is stopped (its call raises), the next calls run again."""
        stopping, self.cancel = self.cancel, threading.Event()
        stopping.set()
        with self._lock:
            runs = list(self._cancels.values())
        for ev in runs:
            ev.set()

    def read_stop(self, slug: str) -> bool:
        """The person stops the keeper's run on this idea (its own cancel, not Stop all's); its queue is `hold`, so
        nothing drafts it by itself again. True when a run was going."""
        with self._lock:
            ev = self._cancels.get(slug)
        if ev is not None:
            ev.set()
        ideas.save_state(self.state_dir, slug, queue="hold", held_until="", held_for="")
        self._ev(event_log.KEEPER_STOPPED, idea=slug)
        self.publish(slug)
        return ev is not None

    def at_work(self) -> bool:
        """The keeper is at work: a draft, a plan, a read or a check (spec 47 §3: keeping the computer awake)."""
        with self._lock:
            return bool(self._busy)

    def _may_run(self) -> str:
        if self.demo:
            return "The demo runs no model: the keeper only reads goals in a real town"
        if not self.budget_ok():
            return "Today's spend limit is reached: the keeper waits"
        return ""

    def window_until(self) -> float | None:
        """When the Claude window comes back, while it is (nearly) spent: as the runner reads it."""
        try:
            limits = list(self.limits() or [])
        except Exception:                            # a quota never stops the board
            limits = []
        return status.reset_of(limits, HARNESS, time.time(), status.NEARLY)

    def refuse_spent(self) -> None:
        """A call the person asks for (a talk, Process now, Re-plan) in a spent window: refused in plain words."""
        until = self.window_until()
        if until is not None:
            raise KeeperError(f"Claude's window is spent: try again after {dt.datetime.fromtimestamp(until):%H:%M}")

    def hold(self, slug: str) -> bool:
        """What runs by itself, in a spent window or while Claude Code needs its sign-in: not made; the idea waits with
        `held_until` (the reset; for a sign-in, a day from the hold, with `held_for`)."""
        until = self.window_until()
        if until is None:
            return self.hold_sign_in(slug)
        ideas.save_state(self.state_dir, slug, held_until=_iso(until), held_for="")
        self.publish(slug)
        return True

    def tick(self, now: float | None = None) -> bool:
        """The host's clock: an idea the limits held (or whose run the host lost) runs again once the window is
        back. True when something started."""
        now = time.time() if now is None else now
        if now - self._tick_at < TICK_S or self._may_run():
            return False
        self._tick_at = now
        started = False
        if self.window_until() is None:
            for i in ideas.ideas(self.wiki_root()):
                slug = i["slug"]
                st = ideas.state(self.state_dir, slug)
                if st["state"] == "working" and not st["error"] and not self.busy(slug) and not self.signed_out():
                    started |= self._quiet(lambda: self.plan_next(slug))      # its step is merged in dev and the route has another: that party plans it (spec 99 §9.1)
                    continue
                if self.busy(slug) or (not st["held_until"] and (st["error"] or st["state"] != "raw")):
                    continue
                if st["held_for"] == "sign_in" and st["held_until"] and not self._release(slug, st, now):
                    continue                          # waits for the sign-in (spec 45 §6)
                if self.signed_out():
                    continue
                if st["state"] == "raw" and ideas.queue_of(st) == "now":
                    started |= self._quiet(lambda: self.draft(slug))
                elif st["state"] == "ready" and st["held_until"] and ideas.plan(self.state_dir, slug) is None:
                    started |= self._quiet(lambda: self.plan(slug, auto=True))
        return started

    def _quiet(self, fn: Callable[[], Any]) -> bool:
        try:
            return fn() is not False
        except KeeperError:
            return False

    def _run(self, key: str, what: str, fn: Callable[[], None], slug: str = "") -> None:
        """Run `fn` as the keeper's run on `key` (a goal's is `goal:<slug>`), with its own cancel, on this thread."""
        cancel = threading.Event()
        with self._lock:
            self._cancels[key] = cancel
        self._tls.cancel, self._tls.slug, self._tls.key = cancel, slug or key, key
        try:
            with tool_errors.doing({"drafting": "draft", "planning": "plan"}.get(what, "ask")):
                fn()
        finally:
            with self._lock:
                self._busy.pop(key, None)
                if self._cancels.get(key) is cancel:
                    self._cancels.pop(key)
            self._tls.cancel = self._tls.key = None
            self.publish(key)

    def _claim(self, key: str, what: str) -> None:
        with self._lock:
            if self._busy.get(key):
                raise KeeperError(f"The keeper is busy with this {'party' if key.startswith('goal:') else 'goal'}: a moment")
            self._busy[key] = what

    def _start(self, slug: str, what: str, fn: Callable[[], None], key: str = "") -> None:
        """`key`: the busy key (a goal's is `goal:<slug>`); what is published is the key, or the idea's slug."""
        key = key or slug
        self._claim(key, what)
        threading.Thread(target=self._run, args=(key, what, fn, slug if key == slug else f"goal-{slug}"),
                         daemon=True, name=f"idea-{what}").start()

    def _place(self, root: Path, slug: str, before: str) -> None:
        """The keeper's proposal of an idea's place among its goal's ideas; the person's own drag is never undone."""
        page = ideas.idea_page(root, slug)
        if not before or page is None or page.get("placed") == "person":
            return
        target = ideas.idea_page(root, before)
        if target is None or before == slug or target.get("track") != page.get("track"):
            return
        ideas.move(root, slug, before=before)

    def read_now(self, slug: str) -> None:
        """Process now: a `raw` idea drafted at once, in the background (`ideas.read_now`, `ideas.queue` now)."""
        if ideas.idea_page(self.wiki_root(), slug) is None:
            raise KeeperError("That goal is gone")
        if ideas.state(self.state_dir, slug)["state"] != "raw":
            raise KeeperError("The keeper has read this goal already")
        self.draft(slug, person=True)

    # -- the talk: an edit of one section, one shot ------------------------------------------------------

    def say(self, slug: str, text: str, section: str = "", device: str = "desktop") -> None:
        root = self.wiki_root()
        text = str(text or "").strip()[:ideas.SECTION_CHARS]
        if ideas.idea_page(root, slug) is None:
            raise KeeperError("That goal is gone")
        if not text:
            raise KeeperError("Say something to the keeper")
        if section and section not in ideas.SECTIONS:
            raise KeeperError(f"A goal has no section {section!r}")
        if why := self._may_run():
            raise KeeperError(why)
        if self.busy(slug):
            raise KeeperError("The keeper is busy with this goal: a moment")
        self.refuse_spent()
        ideas.add_turn(self.state_dir, slug, "you", text, section)
        self._start(slug, "talking", lambda: self.talk_one(slug, text, section, device))

    def talk_prompt(self, root: Path, slug: str, text: str, section: str) -> str:
        """A talk turn is an edit (§0): the one section pointed at (Gist and Open questions when none), the last 10
        lines of Decisions, the person's words. No earlier turn."""
        page = ideas.idea_page(root, slug)
        names = [section] if section else ["Gist", "Open questions"]
        parts = [(f"The section {n}", page.section(n)) for n in names]
        parts += [("The last decisions", "\n".join(page.section("Decisions").splitlines()[-10:])), ("The person says", text)]
        context = idea_target.cut(parts, idea_target.CONTEXT["talk"])
        return f"""You are the keeper of one idea on this project's Task board: {page.title}. The person says what to change on
a section of its spec, or asks about it. Rewrite only that section (and name what was decided), and reply in at most
three lines. {self.reads("talk", [])} You may read the repository (read only).

{context}Answer with one JSON object and nothing else:
{{"reply": "at most three lines to the person",
 "sections": {{"{names[0]}": "its whole new text, only when it changes"}},
 "decisions": ["one line for each thing decided in this turn, and why"]}}"""

    def talk_one(self, slug: str, text: str, section: str = "", device: str = "desktop") -> None:
        root = self.wiki_root()
        allowed = {section} if section else {"Gist", "Open questions"}
        try:
            try:
                out, *_rest = self.ask("talk", self.talk_prompt(root, slug, text, section))
            except Exception as e:
                ideas.add_turn(self.state_dir, slug, "keeper", f"I could not answer: {_why(e)}", section)
                ideas.save_state(self.state_dir, slug, error=_why(e))
                return
            answer = first_json(out) or {"reply": out}           # plain words: kept as the reply, nothing written
            sections = answer.get("sections") if isinstance(answer.get("sections"), dict) else {}
            written = {n: _words(v, ideas.SECTION_CHARS) for n, v in sections.items()
                       if n in allowed and n not in ("Decisions", "Stages") and isinstance(v, str)}
            decisions = _strings(answer.get("decisions"), 10)
            if written or decisions:
                idea_change.update(root, self.state_dir, slug, written, decisions)      # and the plan-making sections it changed are kept (spec 62 §1.2)
            reply = "\n".join((_words(answer.get("reply"), REPLY_CHARS) or "(the keeper wrote the page and said nothing)").splitlines()[:3])
            ideas.add_turn(self.state_dir, slug, "keeper", reply, section)
            changes: dict[str, Any] = {"error": "", "measure": self.measure()}
            state = ideas.state(self.state_dir, slug)["state"]
            page = ideas.idea_page(root, slug)
            if state in ("raw", "asks", "ready"):
                changes["state"] = "asks" if page and ideas.items(page.section("Open questions")) else "ready"
            ideas.save_state(self.state_dir, slug, **changes)
            plan = ideas.plan(self.state_dir, slug)
            if written and plan is not None and not plan.get("passed_at") and self.assess(slug) is not None:
                self.on_plan(slug)                   # the risk changed: whether it starts is decided again
        finally:
            self._ev(event_log.IDEA_SAID, idea=slug, section=section, chars=len(text), text=text, device=device,
                     **self.measure())

    # -- the plan: the spec → plan.json -------------------------------------------------------------------

    def plan(self, slug: str, auto: bool = False) -> bool:
        """Re-plan (the person's: refused in a spent window), or a plan that follows by itself (`auto`: it waits
        with `held_until`). False when it was held."""
        root = self.wiki_root()
        if ideas.idea_page(root, slug) is None:
            raise KeeperError("That goal is gone")
        if self.is_pitch(slug):
            raise KeeperError(PITCH_NOT_BUILT)
        old = ideas.plan(self.state_dir, slug)
        if old and old.get("passed_at"):
            raise KeeperError("Its plan is passed already: the tasks are in work")
        if why := self._may_run():
            raise KeeperError(why)
        if self.busy(slug):
            raise KeeperError("The keeper is busy with this goal: a moment")
        if not auto:
            self.refuse_spent()
        elif self.hold(slug):
            return False
        was = ideas.state(self.state_dir, slug)["state"]
        ideas.save_state(self.state_dir, slug, state="planning", error="", held_until="", held_for="")
        try:
            self._start(slug, "planning", lambda: self.plan_one(slug, was))
        except KeeperError:
            ideas.save_state(self.state_dir, slug, state=was)
            raise
        return True


def make_plan(slug: str, answer: dict | None, made_at: str = "", look: str = "") -> dict:
    """plan.json from the model's answer, strictly: at most 8 tasks with their ids renamed k1…, `after` only to an
    earlier task, known tiers and kinds; the estimate from the tiers' default cost, ±50 %. `look`: the title of a screen's goal (spec 85 §2):
    its plan begins with a pick of the screen's look, every other task after it."""
    if not isinstance(answer, dict) or not isinstance(answer.get("tasks"), list):
        raise KeeperError("the keeper's answer was not a plan")
    names: dict[str, str] = {}
    tasks: list[dict] = []
    for raw in idea_look.with_pick(answer["tasks"], look, slug, MAX_TASKS) if look else answer["tasks"]:
        if not isinstance(raw, dict) or len(tasks) >= MAX_TASKS:
            continue
        title, brief = title_of(raw.get("title")), _words(raw.get("brief"), 6000)
        if not title or not brief:
            continue
        tid = f"k{len(tasks) + 1}"
        after = [names[a] for a in _strings(raw.get("after"), MAX_TASKS, 20) if a in names]
        names[_words(raw.get("id"), 20) or tid] = tid
        tier = raw.get("tier") if raw.get("tier") in TIERS else "warrior"
        kind = raw.get("kind") if raw.get("kind") in roles.TASK_KINDS else roles.DEFAULT_KIND
        pick = idea_pick.clean_ask(raw.get("pick")) if kind not in idea_checks.TAGS else None      # a plan written before has none (spec 51 §2.1)
        tasks.append({**_task(tid, title, brief, kind, tier, list(dict.fromkeys(after))),
                      "short": short_said(raw.get("short"), title), **({"pick": pick} if pick else {}),
                      **({"screen": screen} if (screen := idea_look.clean_screen(raw.get("screen"))) else {})})
    if not tasks:
        raise KeeperError("the plan had no task")
    todos: list[dict] = []
    for raw in answer.get("todos") if isinstance(answer.get("todos"), list) else []:
        if not isinstance(raw, dict) or len(todos) >= MAX_TODOS or raw.get("kind") not in KINDS:
            continue
        title = _words(raw.get("title"), 200)
        if raw["kind"] == "secret":
            title = re.sub(r"[^A-Z0-9_]+", "_", title.upper()).strip("_")
            if not ENV_NAME.match(title):
                continue
        if not title:
            continue
        for_ = [names[f] for f in _strings(raw.get("for"), MAX_TASKS, 20) if f in names]
        todo = {"id": f"t{len(todos) + 1}", "title": title, "kind": raw["kind"],
                "why": _words(raw.get("why"), 500),
                "choices": _strings(raw.get("choices"), 8, 200) if raw["kind"] == "choice" else [],
                "steps": _strings(raw.get("steps"), 12, 500),         # steps on any kind (spec 35 §9)
                "for": list(dict.fromkeys(for_)), "done": False, "value": None}
        if raw["kind"] == "file":
            todo["accept"] = [re.sub(r"[^a-z0-9]", "", a.lower())[:10] for a in _strings(raw.get("accept"), 8, 20)
                              if re.sub(r"[^a-z0-9]", "", a.lower())]
        todos.append(todo)
    data = {"idea": slug, "made_at": made_at or dt.datetime.now().isoformat(timespec="seconds"), "passed_at": None,
            "estimate": estimate(tasks), "todos": todos, "tasks": tasks}
    readiness(data)
    return data
