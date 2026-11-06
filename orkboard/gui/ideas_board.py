"""The Board as `gui/ideas.py`'s `Ideas` shows it (docs/specs/35-goals-window.md §5, §10–§12): `ideas.board` with Needs
you as one list, who passes a plan (autostart by risk and priority), and the Board's own commands — `ideas.queue`,
`ideas.read_stop`, `ideas.start_now`, `ideas.proposal`, `ideas.board_set`, `ideas.answer`, and a file to-do's file.
Split from ideas.py (its size).
"""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.core import idea_keeper
from orkboard.gui.ideas_args import IdeasError, _device, _opt, _text, _via
from orkboard.realm import (board_map, board_rows, collide, event_log, findings, idea_photos, idea_questions, idea_risk, idea_secrets, idea_target, ideas,
                            look_wait, night_order, way_down)
from orkboard.realm.idea_git import BoardTree

NEEDS_IDEA = ("asks", "plan", "failed", "proposed")

# The Board's *Work at night* (docs/specs/121-the-day-the-morning-and-the-night.md §1, §4): its words, as a face shows them.
WORK_AT_NIGHT = {"label": "Work at night",
                 "hint": "What you decide by day is built in the night's window ({night}). Talk, hearings and sketches still run by day. "
                         "A bug's short way, and anything you start with a press, starts at once.",
                 "error": "Work at night is on or off",
                 "waits": "Later, tonight {start}", "now": "Build it now", "now_sketch": "Pick and build now"}


def night_words(night: str) -> dict:
    """The setting's words with the night's window said (`01:00-07:00`), and the held plan's line with its start (`01:00`)."""
    return {**WORK_AT_NIGHT, "hint": WORK_AT_NIGHT["hint"].format(night=night.replace("-", "–")),
            "waits": WORK_AT_NIGHT["waits"].format(start=night.split("-")[0])}


class BoardMixin:
    # -- the Board's own tree on the work branch (§13) ----------------------------------------------------------

    def _tree(self, wiki: Path):
        """The Board's tree for this Wiki and work branch; None where it cannot be (the demo, a Wiki outside the
        repository, a folder with no git history): the pages stay in the Wiki then, as before spec 35."""
        if self.host.demo or getattr(self, "_tree_off", False):
            return None
        repo = Path(self.host.repo_root).resolve()
        try:
            rel = Path(wiki).resolve().relative_to(repo).as_posix()
        except ValueError:
            return None
        got = getattr(self, "_board_tree", None)
        if got is None or got.wiki_rel != rel:
            got = self._board_tree = BoardTree(repo, self.state_dir, rel, lambda: self._into())
            self.phase_watch()                  # a goal's new phase asks the tree for a write (gui/ideas_phase.py)
        return got

    def tree_root(self, wiki: Path, make: bool = True) -> Path:
        tree = self._tree(wiki)
        if tree is None:
            return wiki
        if tree.exists():
            return tree.root()
        if not make or not (Path(self.host.repo_root) / ".git").exists():
            return wiki
        try:
            tree.ensure()
            got = tree.move(wiki)
            if got and got["commit"]:
                self._ev(event_log.BOARD_COMMITTED, commit=got["commit"], pages=got["pages"], what="moved", seconds=None)
        except Exception as e:                  # a repository the tree cannot live in: the Wiki, as before
            self._tree_off = True
            self.host.toast(f"The Board keeps its pages in the Wiki: {' '.join(str(e).split())[:200]}", title="The Board",
                            severity="warning")
            return wiki
        return tree.root()

    def tree_note(self, slug: str, what: str = "") -> None:
        """A write of the Board's, for its next commit: the idea's or goal's title and what happened."""
        tree = getattr(self, "_board_tree", None)
        if tree is None or not tree.exists():
            return
        what = what or self._what.pop(slug, "") or "edited"
        key = slug[5:] if slug.startswith("goal:") else slug
        page = (ideas.track_page if slug.startswith("goal:") else ideas.idea_page)(tree.root(), key) if key else None
        tree.note((page.title if page else "") or key or "the Board", what, time.time())

    def tree_flush(self, force: bool = False) -> dict | None:
        """The Board's writes of the last 10 s as one commit, the work branch moved (or held: `board_held`)."""
        tree = getattr(self, "_board_tree", None)
        if tree is None:
            return None
        began = time.monotonic()
        try:
            self.phase_sync(tree, force)        # pages moved outside followed, a goal's phase and its keys written (spec 151 A.3, A.4)
            got = tree.flush(time.time(), force)
        except Exception as e:                  # a commit that cannot be made never stops the board
            got = {"commit": "", "pages": 0, "what": "", "held": str(e)[:300]}
        if got and got["commit"]:
            self._ev(event_log.BOARD_COMMITTED, commit=got["commit"], pages=got["pages"], what=got["what"],
                     seconds=round(time.monotonic() - began, 2))
        if got and got["held"]:
            self._ev(event_log.BOARD_HELD, why=got["held"])
        return got

    # -- the Board's settings (§1, §5, §7) ---------------------------------------------------------------------

    def board_settings(self) -> dict:
        s = self.settings_now()
        return {"target": s.get("target", settings.IDEAS["target"]), "autostart": bool(s.get("autostart", True)),
                "night": s.get("night", settings.IDEAS["night"]), "review": bool(s.get("review", settings.IDEAS["review"])),
                "review_notice": bool(getattr(getattr(self.host, "machine", None), "review_notice", False)),
                "night_low": s.get("night_low") if isinstance(s.get("night_low"), bool) else None,      # None: not asked yet (spec 83)
                "work_at_night": s.get("work_at_night") is True,                                         # spec 121 §4.1
                "look_wait": look_wait.clean(s.get("look_wait")),                                        # spec 144 A.1: Give me time to look
                "hours": list(s.get("hours") or [])}                                                     # spec 138 B.1: When I am at the computer

    def night_allow(self, args: dict) -> dict:
        """`{"allow": bool}`: the answer of the phone's and Orkline's *Low work may run at night*, stored as `night_low` and read by
        nothing here (spec 99 §3: the night is gone; Orkline reads the setting). Nothing moves, so `moved` is always 0."""
        if not isinstance(args.get("allow"), bool):
            raise IdeasError("Low work may run at night is on or off")
        self.save_settings({**self.settings_now(), "night_low": args["allow"]})
        self.changed("")
        return {"ok": True, "moved": 0}

    def board_set(self, args: dict) -> dict:
        mine = dict(self.settings_now())
        if args.get("review_notice") is False and getattr(getattr(self.host, "machine", None), "review_notice", False):      # said once (spec 84 §1)
            self.host.machine.review_notice = False
            settings.save(self.host.machine)
        for key in ("target", "autostart", "night", "review", "work_at_night", "look_wait"):
            if key not in args:
                continue
            got = settings.clean_ideas({key: args[key]})[key]
            if got != args[key]:
                raise IdeasError({"target": "The Target is thrift, balance or quality",
                                  "autostart": "Start plans by themselves is on or off",
                                  "night": "The night is HH:MM-HH:MM",
                                  "review": "Looking at each result is on or off",
                                  "work_at_night": WORK_AT_NIGHT["error"], "look_wait": look_wait.REFUSED}[key])
            mine[key] = got
        if "hours" in args:                                  # spec 138 B.1: rows of days and a span; a broken row is dropped, a lifted hold ends with the hours it was for
            if not isinstance(args["hours"], list):
                raise IdeasError("The hours are rows of days and a span")
            mine["hours"] = settings.clean_ideas({"hours": args["hours"]})["hours"]
            mine["presence"] = None
        self.save_settings(mine)
        out = self.board_settings()
        self._ev(event_log.BOARD_SET, args, **out)
        if "work_at_night" in args:
            self.night_tick()                  # turned off: what was held goes at once, as every plan did before
        self.changed("")
        return out

    # -- the board ------------------------------------------------------------------------------------------

    def board(self, make: bool = True) -> dict[str, Any]:
        """`make`: General (and the Wiki) written when missing; the snapshot only reads. A folder with no git yet (the first open's *Start git here*, spec 130 A.4) only reads
        too: the Board's pages go into its own tree once git is started, never into the folder, where they would be read as the project's own (a team's wiki)."""
        if make and not (Path(self.host.repo_root) / ".git").exists() and self._tree(self.wiki()) is not None:
            make = False
        root = self.root(make)
        goals = [self._goal_row(g) for g in ideas.tracks(root, make=make)]
        rows, needs = [], self.goal_needs(goals)
        found = ideas.ideas(root)
        states = {i["slug"]: self._state(i["slug"]) for i in found}
        asked = collide.rows(root, self.state_dir, state_of=self._state)        # the Orkmaster's questions (spec 71 §8.1)
        by_idea: dict[str, list[dict]] = {}
        for n in asked:
            by_idea.setdefault(n["idea"], []).append(n)
        for i in found:
            slug, st = i["slug"], states[i["slug"]]
            plan, page = ideas.plan(self.state_dir, slug), ideas.idea_page(root, slug)
            asks = ideas.items(page.section("Open questions")) if page else []
            mine = self._idea_needs(i, st, plan, asks, root)
            needs += mine
            rows.append({**board_map.row(root, self.state_dir, i, st, plan, page, asks, states, mine + by_idea.get(slug, [])), "levels": self._levels(slug),
                         **({"sketching": sk} if (sk := self.sketching(slug)) else {})})      # …on its goal's place too (spec 98 §2.1); a goal being sketched says by whom (spec 121 §2.2)
        needs += asked + board_rows.rows(self.state_dir, root, self.settings_now()) + self.paid_rows() + self._quality_rows(root)         # the stacks of no goal's: the project's questions (spec 99 §8.2), the hypotheses to judge (spec 116 §4.1), the Orkmaster's *Go on paid?* (spec 105 §3)
        settings_now = self.board_settings()
        return {"tracks": goals, "ideas": rows, "needs_you": sort_needs(needs), **settings_now, "night_words": night_words(str(settings_now["night"])),      # Work at night's words, the night's hour said (spec 121 §1)
                "rev": self.rev, "demo": bool(self.host.demo)}

    def _quality_rows(self, root) -> list[dict]:
        """The quality card of each goal with findings to answer and the findings of no goal (spec 132 D.3: realm/findings.py); none when a read fails. Never urgent."""
        try:
            return findings.rows(self.state_dir, root)
        except Exception:
            return []

    def _levels(self, slug: str) -> list[str]:
        """The levels that hold something open of the goal (spec 132 C.3: realm/way_down.py); none when a read fails."""
        try:
            return way_down.open_levels(self.state_dir, slug)
        except Exception:
            return []

    def _idea_needs(self, i: dict, st: dict, plan: dict | None, asks: list[str], root) -> list[dict]:
        """What of one idea needs the person (§10): realm/board_map.py, which the Map reads too; and the picks that wait (spec 51)."""
        return board_map.idea_needs(root, self.state_dir, i, st, plan, asks, log=self.keeper._log_text) + self.pick_rows(i, plan)

    def seen(self, args: dict) -> dict:
        """`{idea}` (spec 98 §2.2): a done goal's result opened from the discard. Its `seen_at` is kept (the first time), and the goal
        is in the history from then on."""
        slug = _text(args, "idea", 100)
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        st = self._state(slug)
        if st["state"] != "done":
            raise IdeasError("Only a goal that is done has a result to see")
        if not st.get("seen_at"):
            ideas.save_state(self.state_dir, slug, seen_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
            self._ev(event_log.RESULT_SEEN, args, idea=slug)
            self.changed(slug)
        return {"ok": True, "seen": ideas.state(self.state_dir, slug)["seen_at"]}

    # -- who passes the plan (§5) ----------------------------------------------------------------------------

    def rank(self, slug: str) -> tuple:
        """An idea's place: its priority, then the person's order (its goal's, then its own)."""
        root = self.root()
        page = ideas.idea_page(root, slug)
        if page is None:
            return (len(ideas.PRIORITIES), 0, 0)
        plan = ideas.plan(self.state_dir, slug) or {}
        if plan.get("ahead"):
            return (night_order.AHEAD, 0, 0)          # *Build it now* on a plan held for the night: ahead of the night's queue (spec 121 §4.5)
        place = {t["slug"]: n for n, t in enumerate(ideas.tracks(root, make=False))}
        prio = page.get("priority") if page.get("priority") in ideas.PRIORITIES else "normal"
        if plan.get("night_priority") in night_order.PRIORITIES:
            prio = plan["night_priority"]             # a plan the night held starts in Product's order (spec 121 §4.3)
        return (ideas.PRIORITIES.index(prio), place.get(page.get("track") or ideas.GENERAL, len(place)), ideas._int(page.get("order")))

    def autostart(self, slug: str) -> str:
        """A plan made, or its idea's priority or risk changed: the board decides (code, no model) whether it starts
        or waits for the person. What it did ("" nothing to decide; "night": held for the night's window, spec 121 §4.2)."""
        if not bool(self.settings_now().get("autostart", True)):
            return "wait"
        plan, page = ideas.plan(self.state_dir, slug), ideas.idea_page(self.root(), slug)
        if plan is None or page is None or plan.get("passed_at") or plan.get("stopped") \
                or ideas.state(self.state_dir, slug)["state"] != "plan":
            return ""
        if ideas.items(page.section("Open questions")) or collide.holds(self.root(), self.state_dir, slug):
            self._release_night(slug)
            return "wait"                      # …or it waits for another party's goal until that goal's flag (spec 71 §4)
        now = self._build_now_of(slug)          # *Pick and build now* on the goal's sketch: the day's case, a press (spec 121 §4.5)
        hold = now is None and self._holds_for_night(slug)
        what = idea_risk.decide(page.get("risk"), page.get("priority"), held_for_night=hold)
        if what != "wait" and now is None and self.look_begin(slug, plan):
            return "look"                      # a spec made waits for the person's look (spec 144 A.2); *Pick and build now* is a press and never waits
        if what == "night" and hold:
            self._hold_for_night(slug, plan)
            return "night"
        self._release_night(slug)               # decided anew: a hold that no longer holds is lifted
        if what != "wait":
            try:
                self.pass_plan(slug, "auto")
            except IdeasError:
                return "wait"
            if plan.get("held_for_night") and self.settings_now().get("work_at_night") is True:
                self._ev(event_log.NIGHT_STARTED, idea=slug)
            if now is not None:
                self._ev(event_log.BUILT_NOW, idea=slug, device=now.get("device") or "desktop", **{"from": "sketch"})
        return what

    # -- Work at night (docs/specs/121-the-day-the-morning-and-the-night.md §4) --------------------------------

    def _night_open(self) -> bool:
        return idea_target.in_night(str(self.settings_now().get("night") or settings.IDEAS["night"]))

    def _holds_for_night(self, slug: str) -> bool:
        """*Work at night* is on, the night's window is not open, and the goal is not a bug's short way (which starts at once, as a press does)."""
        if self.settings_now().get("work_at_night") is not True or self._night_open():
            return False
        how = ideas.state(self.state_dir, slug).get("route_how")
        return not (isinstance(how, dict) and how.get("kind") == "bug" and how.get("short"))

    def _hold_for_night(self, slug: str, plan: dict) -> None:
        """The plan waits for the night's window: it says so (`start_at: "night"`, which the Board's faces read as *starts tonight*) and keeps Product's
        priority, the night's order (§4.3). `night_held` once for each hold."""
        priority = night_order.priority_of(idea_questions.record(self.state_dir, slug))
        if not plan.get("held_for_night"):
            self._ev(event_log.NIGHT_HELD, idea=slug)
        if not (plan.get("held_for_night") and plan.get("night_priority") == priority):
            ideas.edit_plan(self.state_dir, slug, lambda p: p.update(held_for_night=True, start_at="night", night_priority=priority))
            self._publish(slug)

    def _release_night(self, slug: str) -> None:
        plan = ideas.plan(self.state_dir, slug)
        if plan and plan.get("held_for_night") and not plan.get("passed_at"):
            def lift(p: dict) -> None:
                p.pop("held_for_night", None)
                p["start_at"] = None
            ideas.edit_plan(self.state_dir, slug, lift)

    def _build_now_of(self, slug: str) -> dict | None:
        """The person's *Pick and build now* kept with the goal (`{device}`), until its plan is passed; None without."""
        got = (ideas._json(ideas.state_folder(self.state_dir, slug) / "state.json") or {}).get("build_now")
        return got if isinstance(got, dict) else None

    def keep_build_now(self, slug: str, args: dict) -> bool:
        """`ideas.pick` with `now: true`: kept with the pick's answer, so the goal's plan is passed at once when it is made (`autostart`), unless
        `AUTOSTART` says wait for the person. Nothing is kept for a goal whose plan is passed already (a task's pick in the work). Whether it was."""
        plan = ideas.plan(self.state_dir, slug)
        if plan is not None and plan.get("passed_at"):
            return False
        ideas.save_state(self.state_dir, slug, build_now={"device": _device(args)})
        return True

    def drop_build_now(self, slug: str) -> None:
        if self._build_now_of(slug) is not None:
            ideas.save_state(self.state_dir, slug, build_now=None)

    def night_tick(self) -> int:
        """The night's window is open (or *Work at night* is off): the plans it held are decided anew, in Product's priority and then their
        place in line (§4.3); the runner takes them in that order, as many at once as `max_parallel` lets it. How many were passed."""
        held = []
        for i in ideas.ideas(self.root(make=False)):
            plan = ideas.plan(self.state_dir, i["slug"])
            if plan and plan.get("held_for_night") and not plan.get("passed_at") and ideas.state(self.state_dir, i["slug"])["state"] == "plan":
                held.append((night_order.key(plan.get("night_priority"), self.rank(i["slug"])[1:]), i["slug"]))
        if not held or (self.settings_now().get("work_at_night") is True and not self._night_open()):
            return 0
        return sum(1 for _key, slug in sorted(held) if self.autostart(slug) not in ("", "wait", "night"))

    def _on_plan(self, slug: str) -> None:
        """From the keeper's thread: the plan's autostart (a refusal leaves it waiting for the person)."""
        try:
            self.autostart(slug)
        except Exception:                      # whether it starts never breaks the keeper
            pass
        self._publish(slug)

    def pass_plan(self, slug: str, by: str, args: dict | None = None) -> None:
        """A plan passed: by the person's press ("person") or the board ("auto"). From now on it is the runner's."""
        plan = ideas.plan(self.state_dir, slug)
        if plan is None:
            raise IdeasError("This goal has no plan yet: Take it to work first")
        runner = self.runner(need=True)
        if not plan.get("passed_at"):
            page = ideas.idea_page(self.root(), slug)

            def passing(p: dict) -> None:
                p.update(passed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), passed_by=by)
                p["start_at"] = None
                p.pop("start_at_by", None)
                p.pop("held_for_night", None)
                p.pop("stopped", None)
                p.pop("look_until", None)          # the look's wait is over, by the clock or by a press (spec 144 A.2)
                p.pop("look_done", None)
            ideas.edit_plan(self.state_dir, slug, passing)
            self._ev(event_log.PLAN_PASSED, args, idea=slug, tasks=len(plan.get("tasks") or []), seconds=self._since(plan.get("made_at")),
                     by=by, risk=idea_risk.level(page.get("risk")) if page else "", priority=page.get("priority") if page else "",
                     **({"via": _via(args)} if args is not None else {}))
        elif by == "person" and plan.get("start_at"):
            ideas.edit_plan(self.state_dir, slug, lambda p: p.update(start_at=None))
        self.drop_build_now(slug)
        ideas.save_state(self.state_dir, slug, state="working", error="", queue="")
        runner.start(slug)
        self._publish(slug)

    def runner_board(self) -> dict:
        """The Board's own settings as the runner reads them (target, night, reserves, autostart)."""
        s = self.settings_now()
        return {"night": s.get("night", settings.IDEAS["night"]), "autostart": bool(s.get("autostart", True)),
                "reserve_day": s.get("reserve_day", 0.3), "reserve_night": s.get("reserve_night", 0.1)}

    def older_night_plans(self) -> int:
        """A plan passed before the night went, with `start_at: "night"` still in `plan`, goes to the runner: its tasks wait for the
        reserve as a plan the Board passed by itself does (realm/idea_target.py `gate`), never for a night window. How many went."""
        started = 0
        for i in ideas.ideas(self.root(make=False)):
            plan = ideas.plan(self.state_dir, i["slug"])
            if plan and plan.get("passed_at") and plan.get("start_at") == "night" \
                    and ideas.state(self.state_dir, i["slug"])["state"] == "plan":
                ideas.save_state(self.state_dir, i["slug"], state="working", error="")
                self.runner(need=True).start(i["slug"])
                self._publish(i["slug"])
                started += 1
        return started + self.night_tick()          # what *Work at night* held goes when the window opens (spec 121 §4.3)

    def start_now(self, args: dict) -> dict:
        """Start now: a plan of before the night went, which starts at night, starts now; and a task the person's reserve or the week's pace holds (the owner, 26
        October: *now I have this state and I don't know what to do next*) goes on: the press is the person's, and the reserve is only for
        what starts by itself (realm/idea_target.py `gate`). A plan held by *Work at night* is **Build it now** (spec 121 §4.5): it is passed at once, as
        the person's, and runs ahead of the night's queue."""
        slug = _text(args, "slug", 100)
        plan = ideas.plan(self.state_dir, slug)
        held = [t for t in (plan or {}).get("tasks") or [] if isinstance(t, dict) and t.get("state") == "held"
                and str(t.get("note") or "").startswith(("reserve", "week"))]
        if plan and plan.get("look_until") and not plan.get("passed_at"):          # the look's wait (spec 144 A.2): a press passes the plan at once and drops the wait
            if ideas.state(self.state_dir, slug)["state"] != "plan":
                raise IdeasError("Its plan is not ready")
            self._ev(event_log.PLAN_STARTED_NOW, args, idea=slug, via=_via(args), held=0)
            self.pass_plan(slug, "person", args=args)
            self.changed(slug)
            return {"ok": True}
        if plan and plan.get("held_for_night") and not plan.get("passed_at"):
            if ideas.state(self.state_dir, slug)["state"] != "plan":
                raise IdeasError("Its plan is not ready")
            self.runner(need=True)
            ideas.edit_plan(self.state_dir, slug, lambda p: p.update(ahead=True))
            self._ev(event_log.PLAN_STARTED_NOW, args, idea=slug, via=_via(args), held=0)
            self.pass_plan(slug, "person", args=args)
            self._ev(event_log.BUILT_NOW, args, idea=slug, **{"from": "card"})
            self.changed(slug)
            return {"ok": True}
        if not plan or (plan.get("start_at") != "night" and not held):
            raise IdeasError("This plan does not wait for the night or for your reserve")
        ideas.edit_plan(self.state_dir, slug, lambda p: p.update(start_at=None, passed_by="person"))
        self._ev(event_log.PLAN_STARTED_NOW, args, idea=slug, via=_via(args), held=len(held))
        runner = self.runner(need=True)
        if held:
            runner.release_holds(slug)
        if ideas.state(self.state_dir, slug)["state"] == "plan":
            ideas.save_state(self.state_dir, slug, state="working", error="")
            runner.start(slug)
        else:
            runner.tick()
        self.changed(slug)
        return {"ok": True}

    # -- the queue, the keeper's own stop (§3, §12) ------------------------------------------------------------

    def queue(self, args: dict) -> dict:
        """Process now (`now`: drafted at once; refused in plain words in a spent window) or keep it (`hold`: nothing drafts it till the
        person does). `night`, the name of before the night went, is read as `hold` (spec 99 §3)."""
        slug, q = _text(args, "slug", 100), _opt(args, "queue")
        if q not in ("now", "hold", "night"):
            raise IdeasError("The queue is now or hold")
        q = "hold" if q == "night" else q
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        if q == "now":
            try:
                self.keeper.read_now(slug)
            except idea_keeper.KeeperError as e:
                raise IdeasError(str(e)) from None
        else:
            if self._state(slug)["state"] != "raw":
                raise IdeasError("Only a new goal can be kept on hold")
            ideas.save_state(self.state_dir, slug, queue="hold", held_until="", error="")
        self._ev(event_log.IDEA_QUEUED, args, idea=slug, queue=q, via=_via(args))
        self.changed(slug)
        return {"ok": True}

    def read_stop(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        self.keeper.read_stop(slug)
        self.changed(slug)
        return {"ok": True}

    # -- one round of questions (§0), a file to-do's file (§9) ---------------------------------------------------

    def answer(self, args: dict) -> dict:
        """The questions of a spec (or of a goal, `goal: true`) answered together, in their order: one round (§0).
        `decide: true` (spec 41 §9, Let the Taskmaster decide): each answered with its recommended choice."""
        slug = _text(args, "slug", 100)
        decide = args.get("decide") is True
        answers = args.get("answers", [] if decide else None)
        if not isinstance(answers, list) or not all(isinstance(a, str) for a in answers):
            raise IdeasError("answers are a list of text")
        if args.get("goal") is True:
            g = next((t for t in ideas.tracks(self.root(), make=False) if t["slug"] == slug), None)
            if g is None:
                raise IdeasError("That party is gone")
            if decide:
                answers = idea_questions.picks(g["questions"])
            said = "\n".join(f"{q} — {(answers[n] if n < len(answers) else '').strip() or '(no answer: decide)'}"
                             for n, q in enumerate(g["questions"]))      # a phone's quick answer may answer one
            self.keeper.read_goal(slug, said, answered=True)
            how = idea_questions.tally(g["questions"], [] if decide else answers)
            self._ev(event_log.GOAL_ANSWERED, args, goal=slug, answers=sum(1 for a in answers if a.strip()),
                     decided=decide, **how)
            self._what[f"goal:{slug}"] = "answered"
            self.changed(f"goal:{slug}")
            return {"ok": True}
        self._answer_photos(slug, args.get("photos"))
        self.keeper.answer(slug, answers, decide)
        self._what[slug] = "answered"
        self.changed(slug)
        return {"ok": True}

    def _answer_photos(self, slug: str, photos: object) -> None:
        """The pictures that came with an answer (*Pictures you like*, spec 85 §1), kept beside the goal for the keeper to read, as New goal's."""
        if not photos:
            return
        try:
            raws = idea_photos.decode(photos)
        except ValueError as e:
            raise IdeasError(str(e)) from None
        for raw in raws[:max(0, idea_photos.MAX_PHOTOS - len(idea_photos.listed(self.state_dir, slug)))]:
            idea_photos.put(self.state_dir, slug, raw)

    def _todo_file(self, args: dict, slug: str, todo: dict) -> str:
        """A file to-do's file (spec 35 §9): base64, at most 5 MB, kept beside the secrets (mode 600); plan.json says
        only its name. From a phone only over the paired link, as a secret."""
        got = args.get("file")
        if _device(args) == "phone" and args.get("link") != "paired":
            raise IdeasError("A file is given at the computer, or over the paired link")
        if not isinstance(got, dict):
            if todo.get("value"):
                return todo["value"]
            raise IdeasError("A file to-do needs its file")
        data = got.get("data")
        if not isinstance(data, str) or len(data) > idea_secrets.FILE_MAX * 4 // 3 + 8:
            raise IdeasError("The file is larger than 5 MB")
        try:
            raw = base64.b64decode(data, validate=True)
        except ValueError:
            raise IdeasError("The file did not arrive whole") from None
        path = idea_secrets.put_file(self.state_dir, slug, str(todo.get("id")), str(got.get("name") or ""), raw,
                                     todo.get("accept") or [])
        return path.name.split("-", 1)[1]

    # -- proposals (§8) -----------------------------------------------------------------------------------------

    def proposal(self, args: dict) -> dict:
        """A proposal that waits (one the night made before it went): Take (with a priority: the idea is drafted at once) or No (it is dropped;
        the optional reason is only counted in the event)."""
        slug = _text(args, "slug", 100)
        root = self.root()
        page = ideas.idea_page(root, slug)
        if page is None or self._state(slug)["state"] != "proposed":
            raise IdeasError("That proposal is gone")
        take = args.get("take") is True
        reason = args.get("reason") if isinstance(args.get("reason"), str) else ""
        if take:
            priority = _opt(args, "priority").lower() or next(
                (t["priority"] for t in ideas.tracks(root, make=False) if t["slug"] == page.get("track")), "normal")
            if priority not in ideas.PRIORITIES:
                raise IdeasError("Priority is High, Normal or Low")
            ideas.set_meta(root, slug, priority=priority)
            ideas.save_state(self.state_dir, slug, state="raw", queue="now", error="")
            try:
                self.keeper.draft(slug)
            except idea_keeper.KeeperError as e:
                ideas.save_state(self.state_dir, slug, error=str(e))
        else:
            ideas.drop(root, slug, self.state_dir)
            self._what[slug] = "declined"
        self._ev(event_log.PROPOSAL_ANSWERED, args, idea=slug, take=take, has_reason=bool(reason.strip()))
        self.changed(slug)
        return {"ok": True}


def sort_needs(needs: list[dict]) -> list[dict]:
    """What blocks work in progress first, then the priority, then the oldest; proposals last (§10), Operations' rules
    proposals with them (spec 38 §8). A plan change (spec 62 §4.2) sits as a plan does: it blocks nothing and is not last. A
    judged pitch (spec 65 §5) comes after the goals' own, before the proposals. A conflict (spec 150 E1.2) sits where its goal's
    `decision` does, and before it."""
    def key(n: dict) -> tuple:
        prio = n.get("priority") if n.get("priority") in ideas.PRIORITIES else "normal"
        last = 2 if n["kind"] in ("proposal", "op_rules", "party", "project_q", "hypothesis", "quality", "finding", "cascade", "groups") else 1 if n["kind"] == "pitch" else 0
        return last, not n.get("blocks"), ideas.PRIORITIES.index(prio), str(n.get("at") or ""), n["kind"] != "conflict"
    return sorted(needs, key=key)
