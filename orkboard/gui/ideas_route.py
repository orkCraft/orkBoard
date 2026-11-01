"""A goal's route (docs/specs/99-a-goals-way.md §4), as `gui/ideas.py`'s `Ideas` has it: `ideas.route_set`, `ideas.talk`, `ideas.route_later`,
`ideas.route_start`, and the answer of the `start` row (`ideas.start {idea}`).

    ideas.add {text, track|party?, general?, photos?, marks?}   # no model call: the goal waits as `routed` with its `route` (realm/goal_route.py)
    ideas.route_set {idea, route: [party]}                      # a party off, one added, any of the project's but Release; the cost answered again, no call
    ideas.talk {idea}                                           # Talk: the state is `talk`; D's `keeper.talk(slug)` takes it from there
    ideas.route_later {idea}                                    # *Later, by itself*, only when the week's limits run low: `held_until` at the reset
    ideas.route_start {idea}                                    # the short way's Start: no Talk, no decision (E's `keeper.sections(slug)`); a bug whose report
                                                                #   holds no failure goes to Talk, which is its diagnosis (D)
    ideas.start {idea}                                          # answers the `start` row (a route that changed after Talk, or a later step held for it: decisions §169.3); the plan's start otherwise

**Talk by itself** (spec 120 §2.1, decisions §198.2): `ideas.add` of a routed goal calls `route_auto`, which sends it to Talk as **Talk** would when nothing stops it (`route_stop`: the keeper may run, the
Claude window is not spent, the week's limits are not low, nothing is paid, and it is not the short way); else its route card is dealt as before. **The wait of an agreed goal** (§3.5): `ripe_tick`
counts it down only while a face is open and has the leaders confirm the decision at its end; `ripe_hold_goal` is **Hold** (D's `ideas.ripe_hold` calls it).

**The seams.** Until Talk (part D) and the sections (part E) are built, `ideas.talk` and `ideas.route_start` hand the goal to today's draft, so it still moves:
`getattr(self.keeper, "talk" | "sections")` is called when the keeper has it, with the state already set (`talk` / `sections`); the route is in
`state.route`, its facts in `state.route_how` (`short`, `kind`, `reproduces`: D tells a bug's diagnosis by them).

A goal that is not routed (kept on `hold`, a pitch, a release, a goal sent from a pitch or by a recurring goal) is drafted at once as before.
Split from ideas.py to keep it under ~600 lines.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Any

from orkboard.core import idea_keeper
from orkboard.gui.ideas_args import IdeasError, _opt, _text
from orkboard.realm import board_map, event_log, goal_route, idea_ripe, idea_route, idea_target, ideas, orkmaster, pitches

ROUTE_S = 30.0                    # how often a route waiting for its call, or put off to the reset, is looked at
CONTEXT_S = 5.0                   # how long the Orkmaster's line is kept without a change (the limits move it)
AUTO_TALK = True                  # a routed goal goes to Talk by itself when nothing stops it (spec 120 §2.1); False: every routed goal waits for its route card's Talk, as before
RIPE_SCAN_S = 5.0                 # how often the goals whose wait counts down are looked for (an agreed goal's decision is worded in the background)
RIPE_MAX_DT = 5.0                 # the most a tick takes from a wait: a computer that slept does not start a goal when it wakes
RIPE_PUBLISH_S = 15.0             # how often the faces are told the time left of a wait that counts down


def _iso(at: float) -> str:
    return dt.datetime.fromtimestamp(at).isoformat(timespec="seconds")


class RouteMixin:
    _route_at = float("-inf")                       # the clock of `route_tick`
    _route_line: tuple[int, float, dict] | None = None

    # -- the route of a goal sent (ideas.add) ------------------------------------------------------------------------------------

    def route_plan(self, args: dict, text: str, track: str, pitch: str = "") -> dict | None:
        """Before `ideas.add` adds a goal: its route by code and the party it lies in (`home`: the party it was addressed to, else the first of its
        route); None for a goal that is drafted at once as before (kept on `hold`, a pitch, a goal sent from a pitch, a recurring goal's
        round: decided once, it takes no route card, decisions §136.4). No write."""
        if args.get("hold") is True or args.get("recurring") is True or pitch:
            return None
        root = self.root()
        addressed = bool(track) and track != ideas.GENERAL and args.get("general") is not True
        if addressed and pitches.is_ideation(root, track):
            return None
        marks = args.get("marks") if isinstance(args.get("marks"), list) else []
        got = goal_route.route(self.state_dir, root, text, track if addressed else "", marks)
        return {**got, "home": track if addressed else goal_route.home(root, got), "addressed": addressed}

    def route_save(self, slug: str, routed: dict) -> None:
        """The goal waits as `routed` with its route (under `ideas.LOCK`, right after its page is added): no call is made."""
        how = {k: routed[k] for k in ("by", "kind", "short", "reproduces", "failure", "touched", "offer")}
        ideas.save_state(self.state_dir, slug, state="routed", queue="", route=routed["route"], route_how=how, held_until="", held_for="", error="")

    def route_call(self, slug: str, text: str) -> None:
        """Code found no party: the one call on the cheaper tier (step `route`, no tools, no reads) names them, in the background. A call that cannot be made
        (the demo, today's spend limit, a spent window) or that names none leaves the goal on the project's first party, which the person can change."""
        k = self.keeper
        if k._may_run() or k.window_until() is not None or k.busy(slug):
            return self._route_default(slug)
        try:
            k._start(slug, "routing", lambda: self._route_run(slug, text))
        except idea_keeper.KeeperError:
            self._route_default(slug)

    def _route_run(self, slug: str, text: str) -> None:
        ps = goal_route.parties(self.root())
        names: list[str] = []
        try:
            orkmaster.install(self.state_dir)
            got, *_rest = self.keeper.ask("route", goal_route.prompt(text, ps), tools=False, as_role=orkmaster.ROLE)
            names = goal_route.read_answer(got, ps)
        except Exception:                           # a call that cannot be made, or was stopped: the default route
            names = []
        self._route_found(slug, names, "call" if names else "default")

    def _route_default(self, slug: str) -> None:
        self._route_found(slug, [], "default")
        self.changed(slug)

    def _route_found(self, slug: str, names: list[str], by: str) -> None:
        """The route a call found (else the project's first party) is kept, unless the person set one meanwhile."""
        root = self.root()
        with ideas.LOCK:
            st = ideas.state(self.state_dir, slug)
            if st["state"] != "routed" or st["route"]:
                return
            first = goal_route.home(root, {"route": []})                          # the project's first party, when the call named none
            route = [goal_route.entry(root, s) for s in names] or ([goal_route.entry(root, first)] if first else [])
            how = {**st["route_how"], "by": by if route else "default"}
            how.update(goal_route.shape(root, how, route))
            ideas.save_state(self.state_dir, slug, route=route, route_how=how)
        self._auto_set.add(slug)                    # the route is found: the goal goes to Talk by itself at the next tick, once this run has ended (spec 120 §2.1)

    # -- the Needs you rows ------------------------------------------------------------------------------------------------------------

    def _idea_needs(self, i: dict, st: dict, plan: dict | None, asks: list[str], root) -> list[dict]:
        """BoardMixin's, with the route rows: their place in the Orkmaster's line and whether the limits run low are read once for the Board."""
        line = self._route_ctx(root) if st["state"] in goal_route.ROUTE_STATES else None
        return board_map.idea_needs(root, self.state_dir, i, st, plan, asks, line=line, settings=self.settings_now()) + self.pick_rows(i, plan)

    def _route_ctx(self, root) -> dict:
        now = time.monotonic()
        got = self._route_line
        if got is None or got[0] != self.rev or now - got[1] > CONTEXT_S:
            found = ideas.ideas(root)
            ctx = goal_route.context(found, {i["slug"]: self._state(i["slug"]) for i in found}, self.settings_now(), self._raw_limits(), time.time())
            got = self._route_line = (self.rev, now, ctx)
        return got[2]

    def _raw_limits(self) -> list:
        try:
            return list(self.keeper.limits() or [])
        except Exception:                           # a quota never stops the board
            return []

    # -- the commands ----------------------------------------------------------------------------------------------------------------------

    def _routed(self, args: dict, states: tuple[str, ...] = ("routed",)) -> tuple[str, dict]:
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        st = self._state(slug)
        if st["state"] not in states:
            raise IdeasError("This goal has no route to answer now")
        return slug, st

    def _answer(self, slug: str, st: dict) -> dict:
        """The row as the face has it again after an edit: the route, its cost, whether it is the short way."""
        how = st["route_how"]
        return {"ok": True, "route": goal_route.steps_of(self.root(), self.state_dir, st, self.settings_now()),
                "cost": goal_route.cost_of(self.root(), self.state_dir, st, self.settings_now()), "short": bool(how.get("short")),
                "reproduces": bool(how.get("reproduces")), "offer": list(how.get("offer") or []), "changed": bool(how.get("changed"))}

    def route_set(self, args: dict) -> dict:
        """`{idea, route: [party]}`: the route edited (a party off, one added, any of the project's but Release), the cost answered again; no call. Before
        Talk it is the route card's edit; after it (until the work starts) a route that differs from the one the person was told brings the `start` row."""
        slug, st = self._routed(args, goal_route.ROUTE_STATES)
        root = self.root()
        try:
            route = goal_route.edit(root, st["route"], args.get("route"))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        how = {**st["route_how"], "by": "person"}
        how.update(goal_route.shape(root, how, route))
        said = [s["party"] for s in how.get("said_route") or []]
        if st["state"] != "routed" and isinstance(how.get("said"), dict):
            how["changed"] = [s["party"] for s in route] != said
        ideas.save_state(self.state_dir, slug, route=route, route_how=how)
        self.changed(slug)
        return self._answer(slug, {**st, "route": route, "route_how": how})

    def route_talk(self, args: dict) -> dict:
        """`{idea}`: **Talk**. The cost is said as the person was told it, the state is `talk`, and D's `keeper.talk(slug)` takes the goal from there (a bug's Talk
        is its diagnosis, by `route_how`). On the short way that holds a failure, it is *The long way*."""
        slug, st = self._routed(args)
        if not st["route"]:
            raise IdeasError("The Orkmaster is still routing this goal: a moment")
        how = {**st["route_how"], "said": goal_route.cost_of(self.root(), self.state_dir, st, self.settings_now()),
               "said_route": st["route"], "changed": False}
        if how.get("short") and how.get("reproduces"):
            how.update(short=False, reproduces=False)                # the long way, by the person's choice
        ideas.save_state(self.state_dir, slug, state="talk", route_how=how, held_until="", held_for="", error="")
        self._seam(slug, "talk")
        self.changed(slug)
        return {"ok": True}

    def route_start(self, args: dict) -> dict:
        """`{idea}`: the short way's **Start**: no Talk and no decision, E's `keeper.sections(slug)` with the route's one step. A bug whose report holds no failure has
        nothing to start from: its Talk is the diagnosis, which is `ideas.talk`."""
        slug, st = self._routed(args)
        how = st["route_how"]
        if not how.get("short") or not st["route"]:
            raise IdeasError("Only the short way starts without Talk")
        if how.get("kind") == "bug" and not how.get("reproduces"):
            return self.route_talk(args)
        said = goal_route.cost_of(self.root(), self.state_dir, st, self.settings_now())
        ideas.save_state(self.state_dir, slug, state="sections", route_how={**how, "said": said, "said_route": st["route"], "changed": False},
                         held_until="", held_for="", error="")
        self._seam(slug, "sections")
        self.changed(slug)
        return {"ok": True}

    def route_later(self, args: dict) -> dict:
        """`{idea}`: *Later, by itself*, only when the week's limits run low: the goal waits in the deck with `held_until` at the reset, and Talk starts by itself
        then (`route_tick`) if the reserve is not spent again."""
        slug, _st = self._routed(args)
        until = idea_target.reserve_held(self._raw_limits(), self.settings_now(), time.time())
        if until is None:
            raise IdeasError("Later, by itself is offered only when the limits run low")
        ideas.save_state(self.state_dir, slug, held_until=_iso(until), held_for="")
        self.changed(slug)
        return {"ok": True, "held_until": _iso(until)}

    def route_answer(self, args: dict) -> dict | None:
        """The answer of the `start` row (`ideas.start {idea}`): the person agrees to the new cost. None when `args` is no such answer (the plan's start)."""
        slug = args.get("idea")
        if not isinstance(slug, str) or ideas.idea_page(self.root(), slug) is None:
            return None
        st = self._state(slug)
        how = st["route_how"]
        if st["state"] == "working" and idea_route.waits(ideas.plan(self.state_dir, slug)) is not None:      # a later step planned and held for the person's Start (decisions §169.3)
            def lift(p: dict) -> None:
                p.pop("waits", None)
                idea_keeper.readiness(p)                        # its tasks are ready; the runner starts them at its next tick

            ideas.edit_plan(self.state_dir, slug, lift)
            self.runner(need=True).start(slug)
            self.changed(slug)
            return {"ok": True}
        if st["state"] not in goal_route.ROUTE_STATES[1:] or not how.get("changed"):
            return None
        said = goal_route.cost_of(self.root(), self.state_dir, st, self.settings_now())
        ideas.save_state(self.state_dir, slug, route_how={**how, "said": said, "said_route": st["route"], "changed": False})
        self.changed(slug)
        return {"ok": True}

    def _seam(self, slug: str, way: str) -> None:
        """The goal goes on: D's `keeper.talk(slug)` / E's `keeper.sections(slug)` when the keeper has them; else (until they are built) today's draft, so it still moves."""
        go = getattr(self.keeper, way, None)
        try:
            if callable(go):
                go(slug)
                return
            ideas.save_state(self.state_dir, slug, state="raw", queue="now", error="")
            self.keeper.draft(slug)
        except idea_keeper.KeeperError as e:
            ideas.save_state(self.state_dir, slug, error=str(e))

    # -- Talk by itself (spec 120 §2.1) --------------------------------------------------------------------------------------------------

    @property
    def _auto_set(self) -> set:
        """The goals whose route a call found, which go to Talk by themselves at the next tick."""
        return self.__dict__.setdefault("_auto_pending", set())

    def route_paid(self) -> bool:
        """The work would be billed by an API: every subscription is out, or the work has moved onto a tool billed by its API (spec 105: *Go on paid?*). A Main tool billed by its API by
        the person's own choice is not that."""
        machine = getattr(self.host, "machine", None)
        got = self.tool_now() if machine is not None else {}
        if not got.get("main"):
            return False
        return got.get("now") is None or (got["now"] != got["main"] and getattr(machine.tools.get(got["now"]), "billing", "") == "api")

    def route_stop(self, slug: str) -> str:
        """Why a routed goal does not go to Talk by itself, in a few words ("" when nothing stops it): the keeper may not run (a demo, today's spend limit), the Claude window is spent,
        the week's limits run low, the route is paid, the goal is put off, or the short way (a bug's way is the person's choice: its route card keeps *Start* and *Talk*)."""
        st, k = self._state(slug), self.keeper
        if st["state"] != "routed" or not st["route"]:
            return "it has no route to talk through"
        if st["route_how"].get("short"):
            return "the short way keeps its card"
        if st["held_until"]:
            return "it is put off"
        if why := k._may_run():
            return why
        if k.window_until() is not None or k.busy(slug):
            return "the keeper cannot talk it through now"
        if idea_target.reserve_held(self._raw_limits(), self.settings_now(), time.time()) is not None:
            return "the week's limits run low"
        return "every AI tool is out or paid" if self.route_paid() else ""

    def route_auto(self, slug: str) -> bool:
        """The goal goes to Talk by itself when nothing stops it (`route_stop`), as the route card's **Talk** would send it (`route_talk`); else its route card is dealt as before,
        which says why. True when it is at Talk now."""
        if not AUTO_TALK or self.route_stop(slug):
            return False
        try:
            self.route_talk({"idea": slug})
        except IdeasError:
            return False
        st = self._state(slug)
        if st["state"] == "talk":
            ideas.save_state(self.state_dir, slug, route_how={**st["route_how"], "auto": True})
        return st["state"] == "talk"

    # -- the wait of an agreed goal (spec 120 §3.5) -------------------------------------------------------------------------------------

    def ripe_tick(self, now: float) -> None:
        """The host's clock: the wait of each goal the leaders all agreed on counts down, **only while a face is open** (a goal never starts unseen: with no face the time left is kept).
        A wait that runs out has the leaders confirm the decision (`confirm(by="leaders")`)."""
        last, self.__dict__["_ripe_clock"] = self.__dict__.get("_ripe_clock"), now
        if last is None or not self.host.faces():
            return
        if now - self.__dict__.get("_ripe_scan", float("-inf")) >= RIPE_SCAN_S:
            self.__dict__["_ripe_scan"] = now
            self.__dict__["_ripening"] = {i["slug"] for i in ideas.ideas(self.root(False)) if self._state(i["slug"])["state"] == "decided" and idea_ripe.running(self.state_dir, i["slug"])}
        ripening = self.__dict__.get("_ripening") or set()
        if not ripening:
            return
        for slug in idea_ripe.tick(self.state_dir, sorted(ripening), min(max(now - last, 0.0), RIPE_MAX_DT)):
            ripening.discard(slug)
            self.ripe_end(slug)
        if now - self.__dict__.get("_ripe_told", float("-inf")) >= RIPE_PUBLISH_S:
            self.__dict__["_ripe_told"] = now
            for slug in ripening:
                self.changed(slug)

    def ripe_end(self, slug: str) -> None:
        """The wait ran out: the leaders confirm the decision (the entry's heading says *the leaders, all agreed*) and the sections follow. A spent window, a stop or a tool that is out or paid holds
        the goal instead, with why: it waits for the person's **Start** and is never started on paid."""
        try:
            if self.state_of(slug) != "decided" or not idea_ripe.running(self.state_dir, slug):
                return
            if self.route_paid():
                raise IdeasError("Every AI tool is out of room or paid: start it when you are ready")
            self.confirm_as(slug, "", "leaders")
        except (idea_keeper.KeeperError, IdeasError) as e:
            if "is busy" not in str(e):                  # a keeper busy for a moment is tried again at the next tick; any other reason holds the goal
                self.ripe_hold_goal(slug, "stopped", str(e))

    def state_of(self, slug: str) -> str:
        return self._state(slug)["state"] if ideas.idea_page(self.root(False), slug) is not None else ""

    def ripe_hold_goal(self, slug: str, by: str = "person", why: str = "") -> float | None:
        """**Hold**: the wait of the goal stopped (`idea_ripe.hold`), the event `ripe_held`, the faces told. The time that was left; None when there was no wait to hold. `ideas.ripe_hold`
        calls it for the person (`by` "person"); a window spent, a stop or a paid tool call it with the reason."""
        left = idea_ripe.hold(self.state_dir, slug, by, why)
        if left is not None:
            self._ev(event_log.RIPE_HELD, idea=slug, left_s=left, why=by if not why else why)
            self.changed(slug)
        return left

    def ripe_stop_all(self) -> None:
        """Stop all: every wait that counts down is held, so no agreed goal starts after it."""
        for i in ideas.ideas(self.root(False)):
            if idea_ripe.running(self.state_dir, i["slug"]):
                self.ripe_hold_goal(i["slug"], "stopped", "Stopped: start it when you are ready")

    # -- the clock -----------------------------------------------------------------------------------------------------------------------------

    def route_tick(self, now: float) -> None:
        """The host's clock: a route that waits for its call (the process closed meanwhile) is made; a goal put off with *Later, by itself* talks by itself at the
        reset, unless the reserve is spent again (then it waits for the next reset). Looked at every ROUTE_S. A goal whose route a call found goes to Talk by itself first."""
        for slug in list(self._auto_set):
            if not self.keeper.busy(slug):
                self._auto_set.discard(slug)
                self.route_auto(slug)
        if now - self._route_at < ROUTE_S:
            return
        self._route_at = now
        root, wall = self.root(False), time.time()
        for i in ideas.ideas(root):
            st = ideas.state(self.state_dir, i["slug"])
            if st["state"] != "routed" or self.keeper.busy(i["slug"]):
                continue
            slug = i["slug"]
            if not st["route"]:
                page = ideas.idea_page(root, slug)
                self.route_call(slug, page.section("Gist") if page else "")
            elif st["held_until"] and self._passed(st["held_until"], wall):
                until = idea_target.reserve_held(self._raw_limits(), self.settings_now(), wall)
                if until is not None:
                    ideas.save_state(self.state_dir, slug, held_until=_iso(until))
                    self.changed(slug)
                elif not self.keeper.window_until():
                    self.route_talk({"idea": slug})

    @staticmethod
    def _passed(iso: str, now: float) -> bool:
        try:
            return dt.datetime.fromisoformat(iso).timestamp() <= now
        except ValueError:
            return True


def route_commands(ideas_: Any) -> dict:
    """The route's commands by name (`gui/ideas.py` adds them to its table)."""
    return {"ideas.route_set": ideas_.route_set, "ideas.talk": ideas_.route_talk, "ideas.route_later": ideas_.route_later,
            "ideas.route_start": ideas_.route_start}
