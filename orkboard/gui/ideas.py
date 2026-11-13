"""The board's host commands (spec 29a §6): tracks and ideas from the Wiki, the keeper, the runner.

    ideas = Ideas(host)
    host.commands.update(ideas.commands())     # ideas.board, ideas.page, ideas.add, … (the phone may call them all)
    ideas.tick(now)                            # the host's clock: the keeper's batch, the runner's tick
    ideas.snapshot()                           # focus, ideas_rev, needs_you, review_count, limits, reserve: in the snapshot
    ideas.stop_all()                           # Stop all

The pages live in the Wiki joined to the board (`realm/ideas.py`), what runs on them in `.orkcraft/ideas/`. The
keeper (`core/idea_keeper.py`) reads, talks and plans in the background; the runner (`core/idea_runner.py`, spec 29a
part B) carries a passed plan's tasks to `main`. Every change bumps `ideas_rev`, so the board and the phone know to
look again.

Spec 33 adds Review: the results waiting for the person (`ideas.review_list`, `ideas.diff`), their three answers
(`ideas.merge`, `ideas.back`, `ideas.drop_task`), `ideas.stop_task`, the Agents window (`ideas.agents`), one task
with its log (`ideas.task`) and the branch results merge into (`ideas.into`).

Spec 35: an idea needs a goal and is drafted at once (or kept on `hold`); the board, Needs you, autostart
and the Board's own commands are in gui/ideas_board.py; a file to-do's file is kept beside the secrets.

Spec 49: the gate, dev → main (`ideas.gate`, `ideas.gate_merge`: gui/ideas_gate.py), today's events (`ideas.today`:
gui/ideas_recap.py) and the reserve in the snapshot.

Spec 65: a goal of an Ideation party is a pitch, judged and never built (`ideas.judge`, `ideas.pitch_send`, `ideas.pitch_again`,
`ideas.pitch_pass`: gui/ideas_pitch.py); the plan's commands refuse it.

Spec 68: a goal's route (`ideas.move` only before its work starts), a release (`ideas.release_out`, `ideas.release_candidates`, `goes_in` of
`ideas.add`) and the faces' party switch (`ideas.shown`): gui/ideas_release.py.

Spec 70: the Orkmaster's suggestion of a goal's party (`ideas.party_for`): gui/ideas_project.py; its deal is in `ideas.map`'s `project`.

Spec 71: the Orkmaster keeps the parties from colliding (`ideas.collide_answer`; a plan made or a spec changed is compared with the other parties'
open goals; a goal's `depends_on` across parties holds its start until a flag): gui/ideas_project.py, realm/collide.py, core/idea_collide.py.

Spec 115 §5: a mark on the live product (`ideas.play_events`, `ideas.play_place`, `ideas.play_hints`, `ideas.play_mark`, `ideas.play_mark_offer`): gui/ideas_play_mark.py.

Spec 78: what the AI tools drew outside the code, its canvases (`ideas.canvases`, `ideas.canvas_seen`, `ideas.canvas_open`,
`ideas.canvas_file`; `canvases_new` and `canvases_rev` in the snapshot): gui/ideas_canvases.py.

Spec 37 §8: the Board's settings are the project's (`BoardHost.board_settings`: `<repo>/.orkcraft/board.json` over the
machine's `ideas`), read through `settings_now()` and written with `save_settings()`.
"""
from __future__ import annotations

import base64
import datetime as dt
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable

from orkboard import settings
from orkboard.core import idea_keeper
from orkboard.realm import board_ask, board_in_code, board_map, event_log, first_open, goal_team, goal_mentions, idea_checks, idea_element, idea_lens, idea_photos, idea_route, idea_secrets, idea_target, ideas, journal_notes, party_recipes, pitches, recurring, wiki
from orkboard.gui.ideas_args import VIA, IdeasError, _device, _opt, _text
from orkboard.gui.ideas_board import BoardMixin
from orkboard.gui.ideas_halt import STARTS, HaltMixin
from orkboard.gui.ideas_in_code import InCodeMixin, in_code_commands
from orkboard.gui.ideas_assets import AssetsMixin, asset_commands
from orkboard.gui.ideas_system import SystemMixin, system_commands
from orkboard.gui.ideas_canvases import CanvasesMixin, canvas_commands
from orkboard.gui.ideas_concerns import ConcernsMixin, concerns_commands
from orkboard.gui.ideas_decide import DecideMixin, decide_commands
from orkboard.gui.ideas_gate import GateMixin, gate_commands
from orkboard.gui.ideas_goals import GoalsMixin
from orkboard.gui.ideas_hearing import hearing_commands
from orkboard.gui.ideas_say import say_commands
from orkboard.gui.ideas_mats import mats_commands, played
from orkboard.gui.ideas_battle import battle_commands
from orkboard.gui.ideas_map import MapMixin
from orkboard.gui.ideas_party import PartyMixin, stage_commands
from orkboard.gui.ideas_pick import PickMixin
from orkboard.gui.ideas_pickables import PickablesMixin, pickables_commands
from orkboard.gui.ideas_pitch import PitchMixin
from orkboard.gui.ideas_play_mark import PlayMarkMixin, play_mark_commands
from orkboard.gui.ideas_project import ProjectMixin
from orkboard.gui.ideas_reach import ReachMixin, reach_commands
from orkboard.gui.ideas_recap import RecapMixin
from orkboard.gui.ideas_release import ReleaseMixin
from orkboard.gui.ideas_review import ReviewMixin
from orkboard.gui.ideas_night import NightMixin, night_commands
from orkboard.gui.ideas_route import RouteMixin, route_commands
from orkboard.gui.ideas_running import RunningMixin
from orkboard.gui.ideas_sketch import SketchMixin, sketch_commands
from orkboard.gui.ideas_talk import TalkMixin, talk_commands
from orkboard.gui.ideas_project_q import ProjectQMixin as ProjectQFace, project_q_commands
from orkboard.gui.ideas_ask import AskMixin as AskFace, ask_commands
from orkboard.gui.ideas_pass import PassMixin as PassFace, pass_commands
from orkboard.gui.ideas_cascade import CascadeMixin as CascadeFace, cascade_commands
from orkboard.gui.ideas_groups import GroupsMixin as GroupsFace, groups_commands
from orkboard.gui.ideas_change import ChangeMixin, change_commands
from orkboard.gui.ideas_look import LookMixin
from orkboard.gui.ideas_phase import PhaseMixin
from orkboard.gui.ideas_spec_change import SpecChangeFace, spec_change_commands
from orkboard.gui.ideas_findings import FindingsMixin as FindingsFace, findings_commands
from orkboard.gui.ideas_chronicle import ChronicleMixin, chronicle_commands
from orkboard.gui.ideas_conflict import ConflictMixin, conflict_commands
from orkboard.gui.ideas_refine import RefineMixin, refine_commands
from orkboard.gui.ideas_facts import FactsMixin, facts_commands
from orkboard.gui.ideas_loop import LoopMixin as LoopFace, loop_commands
from orkboard.gui.ideas_hypotheses import HypothesesMixin, hypotheses_commands
from orkboard.gui.ideas_journal import JournalMixin as JournalFace, journal_commands
from orkboard.gui.ideas_read_in import ReadInMixin, read_in_commands
from orkboard.gui.ideas_tree import TreeMixin as TreeFace, tree_commands
from orkboard.gui.ideas_goalview import GoalViewMixin, goalview_commands
from orkboard.gui.ideas_maps import MapsMixin, maps_commands
from orkboard.gui.ideas_stall import StallMixin, stall_commands
from orkboard.gui.ideas_screens import ScreensMixin, screens_commands
from orkboard.gui.ideas_revise import ReviseMixin
from orkboard.gui.ideas_lens import LensMixin
from orkboard.gui.ideas_limits import LimitsMixin
from orkboard.gui.ideas_mana import ManaMixin, mana_commands
from orkboard.gui.ideas_usage import usage_commands
from orkboard.gui.ideas_roles import RolesMixin
from orkboard.gui.ideas_track import TrackMixin
from orkboard.gui.ideas_types import TypesMixin

WORDS_CHARS = 2000                # the most a file to-do described instead may say (spec 54 §1.1)
RUNNER_TICK_S = 3.0               # how often the runner looks at its tasks
SNAPSHOT_S = 10.0                 # the most a cached Needs you count is kept without a change
PHONE_ZIP_MAX = 8 * 1024 * 1024   # a zip the phone is handed in a message: larger waits for the computer
OPENED = ("idea", "plan", "todo", "task", "result", "tab", "map", "recap", "flag", "week", "push", "party", "gate", "today", "pick")


class _Settings:
    """The settings as the runner reads them (`ideas.<key>`): the project's Board settings, read when asked."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ideas(self) -> dict:
        return self.host.board_settings()


class _Hop:
    """The bus as the runner gets it: a publish from its thread is made on the host's (`BoardHost.call`)."""

    def __init__(self, host) -> None:
        self.host = host

    def publish(self, topic: str, **data: Any) -> None:
        self.host.call(lambda: self.host.publish(topic, **data))


class Ideas(ReachMixin, NightMixin, PhaseMixin,LookMixin, SpecChangeFace, RefineMixin, HaltMixin, GoalViewMixin, ChangeMixin, CascadeFace, GroupsFace, FindingsFace, ChronicleMixin, ConflictMixin, InCodeMixin, SketchMixin, PlayMarkMixin, JournalFace, ReadInMixin, FactsMixin, LoopFace, TreeFace, HypothesesMixin, ConcernsMixin, MapsMixin, StallMixin, ScreensMixin, RouteMixin, TalkMixin, ProjectQFace, AskFace, PassFace, DecideMixin, LensMixin, LimitsMixin, ManaMixin, GateMixin, GoalsMixin, MapMixin, PartyMixin, PickMixin, PickablesMixin, PitchMixin, ProjectMixin, RecapMixin, ReleaseMixin, RolesMixin, RunningMixin, TrackMixin, ReviewMixin, ReviseMixin,
            TypesMixin, CanvasesMixin, AssetsMixin, SystemMixin, BoardMixin):
    def __init__(self, host) -> None:
        """`host`: what the Board needs of whoever runs it, a `gui/board_host.py` `BoardHost` (spec 37 §4): Orkline's
        host makes one from its town, Orkboard its own."""
        self.host = host
        self.state_dir = Path(self.host.repo_root) / ".orkcraft"
        self.rev = 0
        self._cache: tuple[int, float, dict] | None = None
        self._runner: Any = None
        self._runner_error = ""
        self._runner_at = 0.0
        self._limits: list[dict] = []
        self._limits_at = float("-inf")
        self._limits_busy = False
        self._seen: dict[str, tuple[str, float]] = {}     # slug → (state, when it began): keeper_state
        self._what: dict[str, str] = {}                   # slug → what its next Board commit says (spec 35 §13)
        self._limits_logged = float("-inf")
        self._main_checks: dict[str, dict] = {}           # slug → the last checks on its way into main: {key, checks, running, stop} (gui/ideas_gate.py)
        self._main_lock = threading.Lock()
        self._passing: dict[str, dict] = {}               # slug → what its plan_passed says of a join (gui/ideas_types.py)
        self.keeper = idea_keeper.IdeaKeeper(
            self.host.repo_root, self.state_dir, self.keeper_root, self.settings_now, self._publish,
            demo=bool(self.host.demo), budget_ok=lambda: self.host.budget_ok(), limits=lambda: list(self.host.limits() or []),
            on_plan=self._on_plan, events=not self.host.demo,
            sign_ins=getattr(self.host, "sign_ins", None), follow=self.follow)
        self.board_held = ""                  # spec 137 B (gui/board_sync.py): the words while another worker holds the Board; nothing that writes runs then
        self.keeper.index_root = self.wiki
        self.keeper.board_held = lambda: self.board_held
        self.keeper.fix_tasks = lambda slug, change: self.runner(True).revise_tasks(slug, change)       # a leader's fix tasks for its step run as any added task (spec 152 B.3)
        self.host.bus.subscribe(idea_keeper.CHANGED, self._changed)

    # -- the project's Board settings (spec 37 §8) --------------------------------------------------------------

    def settings_now(self) -> dict:
        """The Board's settings of this project: its `board.json` over the machine's `ideas`."""
        return self.host.board_settings()

    def save_settings(self, values: dict) -> dict:
        """The Board's settings written for this project (never the machine's); what is kept."""
        return self.host.save_board_settings(values)

    # -- where the pages are --------------------------------------------------------------------------------

    def root(self, make: bool = True) -> Path:
        """Where the Board's pages are: its own tree on the work branch (spec 35 §13, gui/ideas_board.py), else the Wiki
        joined to the board. `make`: the tree is made (and the pages moved into it) when missing; the snapshot only reads."""
        root = self.tree_root(self.wiki(), make)
        seated = self.__dict__.setdefault("_seated", set())
        if root not in seated:                               # a Board in the code names its leaders; their roles are made here, once a root (spec 155 F.2)
            seated.add(root)
            try:
                goal_team.seat_leaders(root, self.state_dir)
            except (OSError, ValueError):
                pass
        return root

    def keeper_root(self) -> Path:
        """The keeper's (its clock): the Board's tree is made only for a Board that has pages already."""
        wiki = self.wiki()
        used = any((wiki / f).is_dir() and any((wiki / f).glob("*.md")) for f in (ideas.TRACKS, ideas.IDEAS))
        return self.tree_root(wiki, make=used)

    def wiki(self) -> Path:
        """The Wiki joined to the board: `ideas.wiki` (a folder in the repository) when it is set, else the one the
        host finds (Orkline's: the Task board's `wiki`, else the camp's first Wiki, `BoardHost.wiki_of`), else
        `llm-wiki/general/` in the repository (spec 37 §3.5). The keeper reads its index here."""
        repo = Path(self.host.repo_root)
        own = str(self.settings_now().get("wiki") or "")
        if own:
            return repo / own
        found = self.host.wiki_of() if self.host.wiki_of is not None else None
        return Path(found) if found is not None else wiki.root_of(repo, None, "general")

    # -- the bus, the clock, the snapshot ------------------------------------------------------------------

    def _publish(self, slug: str) -> None:
        """From the keeper's thread: `ideas.changed` on the host's."""
        self.host.call(lambda: self.host.publish(idea_keeper.CHANGED, slug=slug))

    def _changed(self, event) -> None:
        self.rev += 1
        slug = str((getattr(event, "data", None) or {}).get("slug") or "")
        if slug:
            try:
                if slug.startswith("goal:"):
                    self.goal_event(slug[5:])
                else:
                    self._state_event(slug)
                    self.settle_change(slug)    # a plan change that cannot be taken any more goes (spec 62 §3.3)
            except Exception:                   # a log never stops the board
                pass
        self.tree_note(slug)

    # -- the event log (spec 33 §9): every action of the shell, for the day's analysis ------------------------

    def _ev(self, event: str, args: dict | None = None, **fields: Any) -> None:
        """One line of `.orkcraft/usage/events.jsonl`; none in the demo. `device`: "phone" (put there by the listener) or "desktop";
        `goal_saved` and `plan_passed` with spec 52 §2.7's fields (gui/ideas_types.py `type_fields`)."""
        if not self.host.demo:
            if args is not None:
                fields["device"] = _device(args)
            fields.update(self.type_fields(event, fields))
            event_log.record(Path(self.host.repo_root), event, **fields)

    def _state_event(self, slug: str) -> None:
        """`keeper_state` when an idea's state changed, and `plan_made` when it reaches `plan`."""
        state = str(ideas.state(self.state_dir, slug).get("state") or "")
        now = time.monotonic()
        was, since = self._seen.get(slug, ("", None))
        if state == was:
            return
        self._seen[slug] = (state, now)
        what = {"plan": "planned", "proposed": "proposed"}.get(state) or ("drafted" if was == "reading" and state in ("asks", "ready") else "")
        if what:
            self._what.setdefault(slug, what)
        self._ev(event_log.KEEPER_STATE, idea=slug, state=state, was=was, seconds=round(now - since, 1) if since else None)
        if state == "done" and was and was != "done":
            self._flag_when_done(slug)             # a goal done where there is no gate, or with its commits in main already (spec 50 §2.2)
        if state == "plan":
            plan = ideas.plan(self.state_dir, slug) or {}
            est = plan.get("estimate") or {}
            m = ideas.state(self.state_dir, slug).get("measure") or {}
            self._ev(event_log.PLAN_MADE, idea=slug, tasks=len(plan.get("tasks") or []), todos=len(plan.get("todos") or []),
                     usd_low=est.get("usd_low"), usd_high=est.get("usd_high"),
                     **{k: m.get(k) for k in ("step", "prompt_chars", "tokens", "cost")} if m.get("step") == "plan" else
                     {"step": "plan", "prompt_chars": None, "tokens": None, "cost": None})
            self.collide_plan(slug)                # what it touches against the open goals of other parties (spec 71 §2)

    def _since(self, iso: object) -> float | None:
        try:
            return round(max(0.0, time.time() - dt.datetime.fromisoformat(str(iso)).timestamp()), 1)
        except ValueError:
            return None

    def changed(self, slug: str) -> None:
        self.host.publish(idea_keeper.CHANGED, slug=slug)

    def runner(self, need: bool = False):
        """The runner (spec 29a part B), made once; None while this build has none (`need`: say so instead)."""
        if self._runner is None and not self._runner_error:
            try:
                from orkboard.core.idea_runner import IdeaRunner
                self._runner = IdeaRunner(self.host.repo_root, self.state_dir, _Settings(self.host), _Hop(self.host),
                                          events=not self.host.demo, on_held=lambda: self.log_limits(force=True),
                                          rank=self.rank, size_of=self.size_of_idea, party_of=self.party_of_idea,
                                          sign_ins=getattr(self.host, "sign_ins", None), follow=self.follow)
                self._runner.board_held = lambda: self.board_held
                self._runner.on_dev = lambda slug: self.host.call(lambda: self._dev_landed(slug))
            except ImportError:
                self._runner_error = "The runner is not in this build yet: plans cannot start"
            except Exception as e:              # a runner that cannot start never stops the board
                self._runner_error = f"The runner could not start: {e}"
        if self._runner is None and need:
            raise IdeasError(self._runner_error)
        return self._runner

    def tick(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self.tree_flush()
        stopped = self.stopped()                # spec 139 B.2: while stopped nothing starts by itself (gui/ideas_halt.py lists the places)
        try:
            if not stopped:
                self.keeper.tick()
        except Exception as e:                  # the keeper's batch never stops the clock
            self.host.toast(f"{type(e).__name__}: {e}", title="The keeper", severity="error")
        if not stopped and now - self._runner_at >= RUNNER_TICK_S:
            self._runner_at = now
            runner = self.runner() if self._ever_passed() else self._runner
            if runner is not None:
                try:
                    self.older_night_plans()          # a plan passed before the night went: it waits for the reserve, not for a night (spec 99 §3)
                except Exception as e:
                    self.host.toast(f"{type(e).__name__}: {e}", title="The runner", severity="error")
                try:
                    runner.tick()
                except Exception as e:
                    self.host.toast(f"{type(e).__name__}: {e}", title="The runner", severity="error")
        try:
            self.mana_tick()                    # the tool now changed: said once (spec 105 §2.5)
        except Exception as e:                  # a tool that cannot be read never stops the clock
            self.host.toast(f"{type(e).__name__}: {e}", title="The tools", severity="error")
        self.route_tick(now)                    # a route waiting for its call, a goal put off to the reset (spec 99 §4)
        self.ripe_tick(now)                     # the wait of a goal the leaders agreed on, while a face is open (spec 120 §3.5)
        try:
            self.look_tick()                    # a spec's look ended: its plan is decided again, with no face open too (spec 144 A.3)
        except Exception as e:                  # a plan that cannot be decided never stops the clock
            self.host.toast(f"{type(e).__name__}: {e}", title="The Board", severity="error")
        if not stopped:
            self.routines_tick(now)                 # a recurring goal that was done a period ago comes back (spec 92 §2)
        self.canvas_tick(now)                   # what the AI tools drew outside the code (spec 78)
        self.play_tick(now)                     # Play stops after ten minutes with no face asking (spec 88 §5)

    def _ever_passed(self) -> bool:
        folder = self.state_dir / "ideas"
        return folder.is_dir() and any((p / "plan.json").exists() for p in folder.iterdir() if p.is_dir())

    def running(self) -> int:
        """How many of the project's tasks are running now (Close project asks first when some are)."""
        return len(getattr(self._runner, "_runs", {}) or {})

    def working(self) -> bool:
        """The keeper is at work or a task runs (spec 47: the computer is kept awake meanwhile); a runner not built
        is not at work."""
        return bool(self.keeper.at_work() or (self._runner is not None and self._runner.busy()))

    def stop_all(self, device: str = "desktop") -> None:
        self._ev(event_log.STOP_ALL, count=self.running(), device=device or "desktop")
        self.keeper.stop_all()
        self.ripe_stop_all()                    # no agreed goal starts after it (spec 120 §3.5)
        if self._runner is not None:
            try:
                self._runner.stop_all()
            except Exception:
                pass

    def snapshot(self) -> dict[str, Any]:
        """What the page's snapshot carries of the board: the rev, how many ideas need the person, and each idea's
        state."""
        now = time.monotonic()
        if self._cache is None or self._cache[0] != self.rev or now - self._cache[1] > SNAPSHOT_S:
            try:
                b = self.board(make=False)       # reads only: no tree is made for a snapshot
                waiting = self.results()
                data = {"needs_you": sum(1 for n in b["needs_you"] if n["kind"] not in ("proposal", "party", "pitch", "project_q", "hypothesis", "quality", "finding", "cascade", "groups")),     # a judged pitch holds nothing (spec 65 §5), nor the project's questions (spec 99 §8.2), nor a hypothesis to judge (spec 116 §4.1), nor a quality card (spec 132 D.3, decisions §237.8: never urgent); the Orkmaster's *Go on paid?* is a card of the hand and counts (decisions §178.5)
                        "idea_states": [{"slug": i["slug"], "title": i["title"], "state": i["state"]} for i in b["ideas"]],
                        "review_count": len(waiting),
                        "review_results": [{k: r[k] for k in ("idea", "task", "title")} for r in waiting],
                        "preview": self.preview_kind(),                  # whether the project has a preview to play (spec 113 §2)
                        "laid": first_open.laid(self.state_dir, self.root(False)),
                        "keep_off_offered": board_in_code.keepable(self.host.repo_root, self.state_dir)}      # whether the new goal's card offers *Keep off the repository*: a public or unreadable repository with the yes (spec 151 F.4)
            except Exception:                   # a broken page never breaks the host's snapshot
                data = {"needs_you": 0, "idea_states": [], "review_count": 0, "review_results": [], "preview": "", "laid": True, "keep_off_offered": False}      # a broken page never hides the table
            self._cache = (self.rev, now, data)
        return {"ideas_rev": self.rev, **self._cache[2], "main_checks": self.main_checks_now(),
                "play_face": self.play_face(),                   # what the die's up face says: Play's state changes without the Board's rev (spec 118 §3)
                "new_n": self.new_n(),                           # …and how many goals landed in dev since Play last tried it: the pips of the up face (decisions §200.5)
                "limits": self.limits(), "mana": self.mana(), "ask": board_ask.record(self.state_dir), "passing": self.passing_rows(), "reserve": self.reserve(), "canvases_new": self.canvas_store.new_count(),
                "canvases_rev": self.canvas_store.rev}

    def passing_rows(self) -> list[dict[str, Any]]:
        """The snapshot's `passing` (spec 128 D.2, `realm/idea_pass.row`): the leaders' questions waiting to be passed on, read at each snapshot (the clock moves `left_s`, not a change)."""
        try:
            return self.keeper.passing_rows()
        except Exception:                       # a question that cannot be read never breaks the snapshot
            return []

    def reserve(self) -> dict[str, Any]:
        """`{share, night}` (spec 49 §2.3): the part of the AI tool's window the Board keeps from work that starts by
        itself right now (the day's, inside the night window the night's), and whether the night window holds now. It is
        read at each snapshot: the clock moves it, not a change."""
        s = self.settings_now()
        night = idea_target.in_night(str(s.get("night") or settings.IDEAS["night"]))
        return {"share": idea_target.reserve(s, night), "night": night}

    # -- reading -------------------------------------------------------------------------------------------

    def _state(self, slug: str) -> dict:
        st = ideas.state(self.state_dir, slug)
        if st["state"] == "raw" and ideas.queue_of(st) == "night":
            st["queue"] = "hold"                  # a state of before the night went: held, never drafted at night (spec 99 §3)
        if st["state"] in ("reading", "planning") and not self.keeper.busy(slug):
            st["state"] = "raw" if st["state"] == "reading" else "ready"     # a run the host lost (it closed)
        elif st["state"] == "working" and self.keeper.busy(slug) == "accepting":
            st["busy"] = "accepting"              # its leader accepts the step now (spec 152 B.5): a busy run, not a state, so the node's `state` stays `working`
        elif st["state"] == "judging" and not self.keeper.busy(slug):
            st.update(state="failed", error=st["error"] or "stopped")          # a pitch's run the host lost: Try again (spec 65 §2)
        return st

    def page(self, slug: str) -> dict[str, Any]:
        root = self.root()
        page = ideas.idea_page(root, slug)
        if page is None:
            raise IdeasError("That goal is gone")
        names = list(ideas.SECTIONS) + [n for n, _t in page.sections if n not in ideas.SECTIONS]
        st = self._state(slug)
        plan = ideas.plan(self.state_dir, slug)
        checks = idea_checks.status(self.keeper.idea_checks(root, slug), self.keeper.team_checks(root, slug),
                                    (plan or {}).get("tasks") or [])
        return {"slug": slug, "title": page.title or slug, "track": page.get("track") or ideas.GENERAL, "checks": checks,
                "state": st["state"], "size": page.get("size") if page.get("size") in ideas.SIZES else "",
                "sections": [{"name": n, "thesis": ideas.thesis(page.section(n)), "text": page.section(n)}
                             for n in names],
                "talk": ideas.talk(self.state_dir, slug), "sketching": self.sketching(slug),      # who is sketching it now (spec 121 §2.2)
                "plan": {**self._with_heads(plan), "missing": self.plan_missing(slug, plan),         # read now (spec 52 §2.6)
                         "todo_lines": board_map.todo_lines(plan)} if plan else plan,                 # *Before <task>: <to-do>* (spec 87 §4.2)
                "busy": bool(self.keeper.busy(slug)) or st["state"] in ("reading", "planning"), "repeat": recurring.every_of(root, slug),        # a recurring goal (spec 92 §2)
                "state_error": st.get("error", ""), "proposed_track": page.get("proposed_track"),
                "lens": idea_lens.read(self.state_dir, slug), **self.after_start(slug, plan, st),      # spec 62 §1.5
                "pitch": self.pitch_of(root, slug, st["state"]),                                        # a pitch's views, case and decision (spec 65)
                "route": idea_route.route(root, self.state_dir, slug)}                                  # its way across parties (spec 68 §2); [] with only its party

    # -- writing -------------------------------------------------------------------------------------------

    def add(self, args: dict, pitch: str = "") -> dict:
        """An idea: a text, its party (`track`, or `party`; none, or General, and the Orkmaster routes it by code) and a priority (default the party's). It makes
        **no model call** (spec 99 §4): it waits as `routed` with its route until `ideas.talk` (gui/ideas_route.py); only a goal kept on `hold`, a pitch, a
        release or a goal sent from a pitch is drafted at once, whatever its priority (spec 99 §3: the night is gone, so there is no `night` and
        Low waits for nothing). `element`: the rune the person chose in the field (one of `idea_element.ELEMENTS`, else refused in words; decisions §187.3, spec 111 B): the goal is
        given it at once; without it the goal is given the shape the project's goals use least (spec 128 G). The answer's `element` (its shape) and `hue` (its colour) are the rune it wears (the + card's seal plays its rite in it). `marks`: the places of its party's map the goal points at, `[{map, id, name, group?}]` or `[{map, group, name}]` (spec 102 §6): kept in its state as `marks`
        (realm/idea_lens.py `clean_marks`), read into its calls' prompts (`idea_lens.attached`), and the parts of System among them offer Tech on its route. `photos`
        (the phone's, base64) are kept beside it for the Taskmaster to read (realm/idea_photos.py), and `lens`, what the
        person pointed at with the lens of the goal's party (realm/idea_lens.py). Spec 52 §2.3: `type` (one of the party's
        leader's), its `asks` (written after the text) and `join` (who joins the party first: gui/ideas_types.py). `hold`: kept, nothing
        drafts it till the person does. Spec 65: in Ideation it is a pitch (at most 2 000 characters), judged; `pitch`: the one it is sent from.
        Spec 135 A (decisions §242): the new-goal field sends `match: true`; a goal that looks like part of a face-down one (`realm/goal_match.py`, by code, no call) is **not added**: the answer
        is `{slug: "", match: {idea, title, party, state, score, why, shared, adds, reworded, cost}}` for the field's line (`ideas.add_to_goal` is *Add to it*); `apart: true` (and `with`, the goal it was
        offered) adds it as any goal. Spec 150 F.2 (decisions §254.9): `now: true` (the new goal's **Now**) starts Talk once routed only when the limits allow and the route's cost fits the window
        (`route_auto(fit=True)`), else its route card stays; `later: true` (**Later**) lays it in line at the Board's hour whatever the limits (`route_laid`).
        Spec 151 F.4: `keep_off: true` (the card's **Keep off the repository**) keeps the goal off the repository (`board_in_code.keep_off`): stored whatever the repository, in force in a public or unreadable one with the yes."""
        text, files =goal_mentions.files(Path(self.host.repo_root), _text(args, "text", ideas.SECTION_CHARS))      # spec 107 K: each `@path` that exists is the path in backticks, before the route reads it
        track = _opt(args, "track") or _opt(args, "party")
        goals = {t["slug"]: t for t in ideas.tracks(self.root(), make=False)}
        routed = self.route_plan(args, text, track, pitch)      # spec 99 §4 (gui/ideas_route.py): its route by code, no call; None: drafted at once as before
        track = routed["home"] if routed else track
        if not track or track == ideas.GENERAL:
            raise IdeasError("A goal needs a party")
        if track not in goals:
            raise IdeasError("That party is gone")
        if party_recipes.is_team(goals[track]):
            raise IdeasError("Team holds your Operations, not goals: add the goal to another party")          # spec 92 §3
        priority = _opt(args, "priority").lower() or goals[track]["priority"]
        if priority not in ideas.PRIORITIES:
            raise IdeasError("Priority is High, Normal or Low")
        chosen = _opt(args, "element")                          # the rune the person picked in the field (decisions §187.3); never named: five runes, one of them
        if chosen and chosen not in idea_element.ELEMENTS:
            raise IdeasError("Pick one of the five runes")
        try:
            photos = idea_photos.decode(args.get("photos"))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        pointed = self._lens_args(args)
        picked = idea_lens.clean_marks(args.get("marks"))       # spec 102 §6: the places of the party's map it points at, kept in its state as `marks`, read into its calls (idea_lens.attached)
        typed = self.typed(args, track, goals[track]["title"])
        rel = self.release_args(args, track, typed)          # a release's version and what goes in, checked before the goal exists (spec 68 §3)
        routed = None if typed["key"] == "release" else routed
        hold = args.get("hold") is True
        queue = "hold" if hold else "now"                      # a goal sent from a pitch: Now (spec 65 §5)
        text = text[:pitches.PITCH_CHARS] if pitches.is_ideation(self.root(), track) else text
        if args.get("match") is True and args.get("apart") is not True and routed is not None and not typed["key"]:          # spec 135 A: the new-goal field asks whether it looks like part of a face-down goal; nothing is written
            if found := self.goal_matched(args, text, routed, track, picked):
                return {"slug": "", "match": found}
        if args.get("apart") is True and _opt(args, "with"):
            self._ev(event_log.GOAL_KEPT_APART, args, **{"with": _opt(args, "with")})
        with ideas.LOCK:                        # the party changes before the goal, under the same lock; never for a goal kept on hold (spec 52 §2.3)
            joined = self.join_goal(track, typed, args) if not hold else None
            slug = ideas.add_idea(self.root(), self.with_asks(text, typed), track, self.state_dir, priority, "hold" if routed else queue)
            if chosen:                          # the person's rune, before any read of the Map can give the goal its own (decisions §187.3)
                idea_element.give(self.root(), self.state_dir, slug, want=chosen)
            if routed:
                self.route_save(slug, routed)         # waits as `routed`, nothing drafts it (spec 99 §4)
                if args.get("later") is True:         # the new goal's **Later** (spec 150 F.2): laid in line at the Board's hour, whatever the limits
                    self.route_laid(slug)
            if typed["key"] or pitch:
                ideas.save_state(self.state_dir, slug, type=typed["key"], from_pitch=pitch)
            if args.get("keep_off") is True:        # spec 151 F.4: the person keeps this goal off the repository (its card's line, offered where the Board is public with the yes); its page enters `info/exclude` at the next flush
                board_in_code.keep_off(self.state_dir, slug, True)
            if args.get("via") == "inbox" and re.fullmatch(r"[A-Za-z0-9_-]{8,40}", str(args.get("inbox_id") or "")):
                ideas.save_state(self.state_dir, slug, via="inbox", inbox_id=str(args["inbox_id"]))     # laid from the phone's inbox: once (spec 136 B.4)
            if rel is not None:
                self.release_made(args, slug, track, rel)
        if joined:
            self.changed(f"goal:{track}")
        for raw in photos:
            idea_photos.put(self.state_dir, slug, raw)
        idea_lens.save(self.state_dir, slug, pointed or (idea_lens.read(self.state_dir, pitch) if pitch else []))
        if picked:
            ideas.save_state(self.state_dir, slug, marks=picked)
            self.hypothesis_marked(slug, picked, typed["key"] == "experiment")      # spec 116 E: a hypothesis among them: an experiment tests it, any other goal rests on it
        element = self.element_for(slug, pitch, chosen)    # the mark of every card of it (spec 50 §2.3); the one chosen, else a sent pitch's where it is free (spec 68 §2.3)
        ideas.add_turn(self.state_dir, slug, "you", self.with_asks(text, typed), "Gist")     # the person's own words, kept
        self._ev(event_log.IDEA_ADDED, args, idea=slug, track=track, chars=len(text), now=queue == "now",
                 priority=priority, queue=queue, photos=len(photos), files=files, lens=[a["kind"] for a in pointed], type=typed["key"],
                 asks=typed["answered"], refs=len(photos) if typed["type"] and typed["type"].refs else 0,
                 joined=(joined or {}).get("add", ""), out=(joined or {}).get("out", ""))
        out = {"slug": slug, "queue": queue, "element": element, "hue": idea_element.hue_of(self.state_dir, slug), "type": typed["key"], "joined": joined}
        try:
            self.brief_more()                   # the brief's other half, once the first start's questions are done (spec 124 A); never troubles the goal
        except Exception:
            pass
        try:
            digest = getattr(self.keeper, "journal_digest_for", None)       # the digest of each leader of the route whose journal is due (spec 125 D), quietly
            if digest is not None:
                digest([r["party"] for r in (routed or {}).get("route") or []] or [track])
        except Exception:
            pass
        if routed:
            out["route"] = [r["party"] for r in routed["route"]]
            if not routed["route"]:
                self.route_call(slug, text)     # code found no party: the one call on the cheaper tier, in the background
            else:
                out["talk"] = self.route_auto(slug, fit=args.get("now") is True)     # nothing stops it: it goes to Talk by itself (spec 120 §2.1); the new goal's **Now** only when its cost fits the window (spec 150 F.2); else its route card, as before
                if args.get("later") is True:
                    out["held_until"] = ideas.state(self.state_dir, slug)["held_until"]
        elif queue == "now":                    # drafted at once, in the background (held in a spent window)
            try:
                self.keeper.draft(slug)
            except idea_keeper.KeeperError as e:
                ideas.save_state(self.state_dir, slug, error=str(e))
                out["error"] = str(e)
        self.changed(slug)
        return out

    def say(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        text = _text(args, "text", ideas.SECTION_CHARS)
        if args.get("goal") is True or (ideas.idea_page(self.root(), slug) is None and ideas.track_page(self.root(), slug)):
            self._read_goal(slug, text)         # the answer to a goal's questions: the same talk, on the goal
            self._ev(event_log.IDEA_SAID, args, idea=f"goal:{slug}", section="", chars=len(text), text=text)
            self.changed(f"goal:{slug}")
            return {"ok": True}
        self.keeper.say(slug, text, _opt(args, "section"), _device(args))     # its `idea_said` is the keeper's, measured
        self.changed(slug)
        return {"ok": True}

    def plan(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        self.keeper.plan(slug)
        self.changed(slug)
        return {"ok": True}

    def start(self, args: dict) -> dict:
        """The person passes the plan (`passed_by: "person"`): it is the runner's from now on, and it starts. `join: {add}`
        (Add and start, spec 52 §2.6): the agent the plan misses joins the party first (gui/ideas_types.py)."""
        if (answered := self.route_answer(args)) is not None:        # the `start` row's answer: a route that grew after Talk (spec 99 §4.6)
            return answered
        slug = _text(args, "slug", 100)
        if ideas.plan(self.state_dir, slug) is None:
            raise IdeasError("This goal has no plan yet: Take it to work first")
        st = self._state(slug)["state"]
        if st not in ("plan", "failed", "working"):
            raise IdeasError("Its plan is not ready")
        self.runner(need=True)                  # a build with no runner changes no party
        self._passing[slug] = self.start_join(slug, args)
        try:
            self.pass_plan(slug, "person", args=args)
        finally:
            self._passing.pop(slug, None)
        self.changed(slug)
        return {"ok": True}

    def stop(self, args: dict) -> dict:
        """The person stops a plan's work: from then on it waits for them (autostart never starts it again)."""
        slug = _text(args, "slug", 100)
        self.runner(need=True).stop(slug)
        if ideas.plan(self.state_dir, slug) is not None:
            ideas.edit_plan(self.state_dir, slug, lambda p: p.update(stopped=True))
        self.changed(slug)
        return {"ok": True}

    def edit(self, args: dict) -> dict:
        """A section written by hand, or (`priority` without a section) the idea's priority: a plan waiting is then
        decided again (spec 35 §5)."""
        slug = _text(args, "slug", 100)
        if "priority" in args and "section" not in args:
            priority = _opt(args, "priority").lower()
            if priority not in ideas.PRIORITIES or ideas.idea_page(self.root(), slug) is None:
                raise IdeasError("Priority is High, Normal or Low")
            ideas.set_meta(self.root(), slug, priority=priority)
            self.autostart(slug)
            self.changed(slug)
            return {"ok": True}
        if self.keeper.busy(slug):
            raise IdeasError("The keeper is writing this goal: a moment")
        self.edited(args, slug)                 # the text set, `changed` kept, `idea_edited` (gui/ideas_revise.py)
        self.changed(slug)
        return {"ok": True}

    def track_add(self, args: dict) -> dict:
        slug = ideas.add_track(self.root(), _text(args, "title", ideas.TITLE_CHARS))
        self.changed("")
        return {"slug": slug}

    def track_set(self, args: dict) -> dict:
        criteria = args.get("criteria")
        if criteria is not None and not isinstance(criteria, list):
            raise IdeasError("Success criteria are a list")
        about, deadline = args.get("about"), args.get("deadline")
        ideas.set_track(self.root(), _text(args, "slug", 100),
                        about=str(about)[:ideas.SECTION_CHARS] if isinstance(about, str) else None,
                        criteria=criteria, deadline=str(deadline) if isinstance(deadline, str) else None)
        self.changed("")
        return {"ok": True}

    def todo(self, args: dict) -> dict:
        """A to-do of a plan ticked (or unticked). A secret's value goes to the machine's secret store; the plan
        says only "stored". This is the one write to a passed plan: the runner reads the to-do as done."""
        slug, tid = _text(args, "idea", 100), _text(args, "id", 20)
        plan = ideas.plan(self.state_dir, slug)
        todo = next((t for t in (plan or {}).get("todos") or [] if t.get("id") == tid), None)
        if todo is None:
            raise IdeasError("That to-do is gone")
        done, value = bool(args.get("done")), args.get("value")
        skip, words, described = done and args.get("skip") is True, args.get("words"), False
        sent = isinstance(args.get("file"), dict)
        kept: Any = todo.get("value")
        if skip:                                # gone without it (spec 54 §1.1): done, no value; a secret's stored value stays
            kept = kept if todo.get("kind") == "secret" and kept == "stored" else None
        elif done and todo.get("kind") == "file" and words is not None and not sent:   # described instead (§1.1)
            kept = words.strip()[:WORDS_CHARS] if isinstance(words, str) else ""
            if not kept:
                raise IdeasError("Say what it should look like")
            described = True
        elif done and todo.get("kind") == "file":     # a file sent later replaces the words; ticked again, they stay
            described = bool(todo.get("words")) and not sent
            kept = todo["value"] if described else self._todo_file(args, slug, todo)
        elif done and todo.get("kind") == "secret":
            if not isinstance(value, str) or not value.strip():
                if todo.get("value") != "stored":
                    raise IdeasError("A secret needs its value")
            else:
                idea_secrets.put(self.state_dir, slug, tid, value.strip())
                kept = "stored"
        elif done and todo.get("kind") == "choice":
            if value not in (todo.get("choices") or []):
                raise IdeasError("Pick one of its choices")
            kept = value
        elif isinstance(value, str) and value.strip():
            kept = value.strip()[:500]

        def tick(p: dict) -> None:
            for t in p.get("todos") or []:
                if t.get("id") == tid:
                    t["done"], t["value"] = done, kept
                    for key, on in (("skipped", skip), ("words", described)):
                        if on:
                            t[key] = True
                        else:
                            t.pop(key, None)
            if not p.get("passed_at"):
                idea_keeper.readiness(p)

        ideas.edit_plan(self.state_dir, slug, tick)
        if done:                                # a secret's value (or a file) is never logged: only that it was done
            self._ev(event_log.TODO_DONE, args, idea=slug, todo=tid, kind=todo.get("kind"), seconds=self._since(plan.get("made_at")),
                     skipped=skip, words=described)
        self.changed(slug)
        return {"ok": True}

    def drop(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        if self.keeper.busy(slug):
            raise IdeasError("The keeper is busy with this goal: a moment")
        plan = ideas.plan(self.state_dir, slug) or {}
        if self._runner is not None and plan.get("passed_at"):
            self._runner.stop(slug)
        secrets = [t["id"] for t in plan.get("todos") or [] if t.get("kind") == "secret" and t.get("id")]
        journal_notes.dropped(self.state_dir, self.root(), slug, args.get("why") if isinstance(args.get("why"), str) else "")     # the project's journal, before the page is gone (spec 125 B)
        self._drop_branch(slug)                # dropped before dev: its branch goes, dev is as it was (decisions §283.26)
        ideas.drop(self.root(), slug, self.state_dir)
        idea_secrets.forget(self.state_dir, slug, secrets)
        idea_secrets.forget_files(self.state_dir, slug)
        self.changed(slug)
        return {"ok": True}

    def log(self, args: dict) -> dict:
        """`ideas.log`: the shell's one event, `opened` — a preview or a tab the person opened. Any other event is refused."""
        if args.get("event") != event_log.OPENED:
            raise IdeasError("Only `opened` can be logged from here")
        what, ref = _opt(args, "what"), _opt(args, "ref")
        if what not in OPENED:
            raise IdeasError(f"`what` is one of {', '.join(OPENED)}")
        via = _opt(args, "via")
        if via and via not in VIA:
            raise IdeasError(f"`via` is one of {', '.join(VIA)}")
        self._ev(event_log.OPENED, args, what=what, ref=ref, via=via)
        return {"ok": True}

    def logs(self, args: dict) -> dict:
        """The day's logs (or the last `days`) as the analytics zip, for a phone: {"name", "data": base64}. The computer's
        gear downloads the same zip from `/api/analytics`."""
        days = args.get("days")
        got = self.host.day_logs.pack_period(days if isinstance(days, int) and not isinstance(days, bool) and days > 0 else 1)
        if got is None:
            raise IdeasError("No logs yet")
        name, data = got
        if len(data) > PHONE_ZIP_MAX:
            raise IdeasError("The logs are too large for the phone: download them on the computer")
        return {"name": name, "data": base64.b64encode(data).decode("ascii")}

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        def guarded(name, fn):
            def run(args: dict) -> Any:
                try:
                    self.refuse_pitch(name, args)       # the plan's commands refuse a pitch (spec 65 §2)
                    if name in STARTS and not (name == "ideas.add" and args.get("hold") is True):
                        self.wake()                     # a goal started by hand: the orks are back at work (spec 139 B.2)
                    return fn(args)
                except (ValueError, idea_keeper.KeeperError) as e:
                    raise IdeasError(str(e)) from None
                except Exception as e:
                    if type(e).__name__ != "RunnerError":      # the runner is loaded on demand: no import here
                        raise
                    raise IdeasError(str(e)) from None
            return run

        table = {"ideas.board": lambda a: self.board(), "ideas.map": self.map, "ideas.recap": self.recap, "ideas.flags": self.flags, "ideas.week_work": self.week_work, "ideas.week": self.week, "ideas.party": self.party, "ideas.seat_price": self.seat_price, "ideas.party_price": self.party_price, "ideas.party_answer": self.party_answer, "ideas.parties": self.parties, "ideas.party_save": self.party_save, "ideas.party_drop": self.party_drop, "ideas.page": lambda a: self.page(_text(a, "slug", 100)),
                 "ideas.add": self.add, "ideas.say": self.say, "ideas.plan": self.plan, "ideas.revise": self.revise, "ideas.revise_answer": self.revise_answer, "ideas.start": self.start,
                 "ideas.move": self.move, "ideas.edit": self.edit, "ideas.track_add": self.track_add,
                 "ideas.track_set": self.track_set, "ideas.track_drop": self.track_drop, "ideas.todo": self.todo, "ideas.drop": self.drop,
                 "ideas.stop": self.stop, "ideas.review_list": self.review_list, "ideas.diff": self.diff,
                 "ideas.merge": self.merge, "ideas.back": self.back, "ideas.regate": self.regate, "ideas.drop_task": self.drop_task,
                 "ideas.stop_task": self.stop_task, "ideas.agents": self.agents, "ideas.task": self.task, "ideas.task_log": self.task_log,
                 "ideas.into": self.into, "ideas.branch_set": self.branch_set, "ideas.log": self.log, "ideas.logs": self.logs, "ideas.goal_save": self.goal_save,
                 "ideas.words": self.words, "ideas.goal_accept": self.goal_accept,
                 "ideas.goal": self.goal, "ideas.read_now": self.read_now, "ideas.doc": self.doc, "ideas.roles": self.roles,
                 "ideas.role_save": self.role_save, "ideas.role_add": self.role_add, "ideas.role_drop": self.role_drop,
                 "ideas.kind_set": self.kind_set,
                 "ideas.queue": self.queue, "ideas.night_allow": self.night_allow, "ideas.read_stop": self.read_stop, "ideas.seen": self.seen, "ideas.start_now": self.start_now,
                 "ideas.proposal": self.proposal, "ideas.board_set": self.board_set, "ideas.answer": self.answer,
                 "ideas.spend": self.spend, "ideas.lens": self.lens, "ideas.lens_code": self.lens_code,
                 "ideas.lens_screen": self.lens_screen, "ideas.check_skip": self.check_skip,
                 "ideas.gate": self.gate, "ideas.gate_merge": self.gate_merge, "ideas.today": self.today, "ideas.pick": self.pick}
        table.update({"ideas.judge": self.judge, "ideas.pitch_send": self.pitch_send, "ideas.pitch_again": self.pitch_again,
                      "ideas.pitch_pass": self.pitch_pass,
                      "ideas.release_out": self.release_out, "ideas.release_candidates": self.release_candidates, "ideas.shown": self.shown,
                      "ideas.party_for": self.party_for, "ideas.kind_for": self.kind_for, "ideas.collide_answer": self.collide_answer,
                      "ideas.repeat": self.repeat, "ideas.proposals": self.proposals, "ideas.tools": self.tools, "ideas.party_sizes": self.party_sizes, "ideas.party_presets": self.party_presets, **canvas_commands(self), **asset_commands(self), **system_commands(self), **usage_commands(self), **mana_commands(self), **route_commands(self), **night_commands(self), **talk_commands(self), **decide_commands(self), **stage_commands(self), **project_q_commands(self), **ask_commands(self), **pass_commands(self), **change_commands(self), **spec_change_commands(self), **findings_commands(self), **chronicle_commands(self), **conflict_commands(self), **in_code_commands(self), **refine_commands(self), **cascade_commands(self), **groups_commands(self), **goalview_commands(self), **facts_commands(self), **loop_commands(self), **maps_commands(self), **stall_commands(self), **screens_commands(self), **pickables_commands(self), **concerns_commands(self), **reach_commands(self),**tree_commands(self), **hypotheses_commands(self), **journal_commands(self), **read_in_commands(self), **gate_commands(self), **play_mark_commands(self), **hearing_commands(self), **say_commands(self), **mats_commands(self), **battle_commands(self)})
        table.update(sketch_commands(self))                # spec 121 A: *Sketch it first*, *No sketch* (gui/ideas_sketch.py)
        table["ideas.night"] = self.night                  # spec 121 D: what the night did, for the morning's card (gui/ideas_recap.py)
        table["ideas.feed"] = self.feed                    # goal 169 E: the phone's feed, what waits first, then the leaders' posts (gui/ideas_recap.py)
        return {name: played(self, name, guarded(name, fn)) for name, fn in table.items()}

