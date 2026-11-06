"""Orkboard as a taker of goals (spec 151 D.2, decisions §255.8): the host's tick keeps `orkboard/taken` (realm/goal_take.py) in step with what Orkboard runs.

    goal_take_host.tick(host)        # each open project whose root `AGENTS.md` holds the rules: one thread a project, never blocking the clock
    goal_take_host.close(host)       # the host's quit: every goal Orkboard holds is given back

**Nothing runs until the rules are written** (`goal_take.rules_written`, part C): before, no other tool works the Board, so no thread, no git, no file.

At each tick (at most every `FETCH_S`), one fetch: who holds what is kept (`goal_take.cache_set`). The places that start a goal's Talk or its work
ask that cache only (`goal_take.refusal`), so no network call sits in the path of a press. Then the goals Orkboard runs (in Talk or at work, not waiting for
the person) are taken or renewed; the goals it held that now wait for the person or are done are given back; a goal that was held by another and is free
now is tried again (its plan's autostart). A hold of Orkboard's own that no goal runs any more (the host was closed) is given back too.
"""
from __future__ import annotations

import datetime as dt
import socket
import threading
import time
from typing import Any

from orkboard.realm import goal_take, ideas

FETCH_S = 60             # the remote is asked at most this often
RENEW_LEFT_S = 20 * 60   # a hold of Orkboard's own is renewed only when less than this is left of it: a push an hour or so a goal, not one a tick
HOURS = 1                # a take runs this long; the tick renews it long before
RUNNING = ("talk", "planning", "working")       # the states Orkboard works a goal in; a plan waiting for Start, a failed or finished goal waits for the person or ends


def me() -> str:
    return f"Orkboard on {socket.gethostname() or 'this computer'}"


class _State:
    def __init__(self) -> None:
        self.next_fetch = 0.0
        self.mine: set[str] = set()              # the goals this host holds
        self.waited: set[str] = set()            # the goals another held at the last tick
        self.thread: threading.Thread | None = None


class GoalTakeHost:
    def __init__(self, host: Any, name: str = "") -> None:
        self.host = host
        self.me = name or me()
        self._states: dict[str, _State] = {}

    def _state(self, p: Any) -> _State:
        return self._states.setdefault(p.path, _State())

    def tick(self) -> None:
        try:
            for p in list(getattr(self.host.projects, "open_ones", None) or []):
                if self.host.demo:
                    continue
                if not goal_take.rules_written(p.root):
                    goal_take.cache_clear(p.root)             # the rules were taken out: nothing of D any more
                    continue
                st = self._state(p)
                if st.thread is not None and st.thread.is_alive():
                    continue
                st.thread = threading.Thread(target=self.run, args=(p, st), daemon=True, name="orkboard-taken")
                st.thread.start()
        except Exception:                                     # a goal that cannot be taken troubles no work
            pass

    def running(self, p: Any) -> set[str]:
        """The goals Orkboard works now: in Talk or at work, not waiting for the person."""
        root, state_dir = p.ideas.root(make=False), p.ideas.state_dir
        return {i["slug"] for i in ideas.ideas(root) if ideas.state(state_dir, i["slug"])["state"] in RUNNING}

    def run(self, p: Any, st: _State, now: dt.datetime | None = None, mono: float | None = None) -> None:
        """One tick of one project. Never raises."""
        try:
            if not goal_take.rules_written(p.root):
                return
            mono = time.monotonic() if mono is None else mono
            if mono < st.next_fetch:
                return
            st.next_fetch = mono + FETCH_S
            now = now or dt.datetime.now(dt.timezone.utc)
            holds = goal_take.read_all(p.root, now)
            if holds is None:
                return                                        # offline: the cache stays as it was, the host goes on
            goal_take.cache_set(p.root, holds, self.me)
            wanted = self.running(p)
            for slug in sorted(wanted):                       # taken or renewed
                if goal_take.blocked(p.root, slug, now):
                    continue                                  # another holds it: not ours to take
                if slug in st.mine and _left(holds.get(slug), self.me, now) > RENEW_LEFT_S:
                    continue                                  # ours, and long enough still: no push for nothing
                got = (goal_take.renew if slug in st.mine else goal_take.take)(p.root, slug, self.me, goal_take.ORKBOARD, now, HOURS)
                if got["taken"]:
                    st.mine.add(slug)
                else:
                    st.mine.discard(slug)
            for slug in sorted((st.mine | {s for s, h in holds.items() if h["by"] == self.me}) - wanted):
                if goal_take.give_back(p.root, slug, self.me, now).get("given"):      # waits for the person, or done (or a hold left by a host that closed)
                    st.mine.discard(slug)
            freed = st.waited - {s for s in holds if goal_take.blocked(p.root, s, now)}
            st.waited = {s for s in holds if goal_take.blocked(p.root, s, now)}
            for slug in sorted(freed):                        # held by another before, free now: tried again
                try:
                    p.ideas.autostart(slug)
                except Exception:
                    pass
        except Exception:
            pass

    def close(self, now: dt.datetime | None = None) -> None:
        """Every goal this host holds is given back (a failure leaves it to run out)."""
        now = now or dt.datetime.now(dt.timezone.utc)
        for p in list(getattr(self.host.projects, "open_ones", None) or []):
            st = self._states.get(p.path)
            for slug in sorted(st.mine if st else ()):
                try:
                    if goal_take.give_back(p.root, slug, self.me, now).get("given"):
                        st.mine.discard(slug)                 # type: ignore[union-attr]
                except Exception:
                    pass


def _left(hold: dict | None, me: str, now: dt.datetime) -> float:
    """The seconds left of a hold of `me`'s (0 for none, another's, or one that cannot be read)."""
    if not hold or hold.get("by") != me:
        return 0.0
    try:
        return (dt.datetime.fromisoformat(str(hold["until"])) - now).total_seconds()
    except (KeyError, ValueError, TypeError):
        return 0.0


def tick(host: Any) -> None:
    taker = getattr(host, "goal_take", None)
    if taker is not None:
        taker.tick()


def close(host: Any) -> None:
    taker = getattr(host, "goal_take", None)
    if taker is not None:
        taker.close()
