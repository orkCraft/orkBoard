"""The computer's tick for the Board's branch (spec 137 B.2, decisions §244.2–4): holds the Board, renews and pushes it, gives it back.

    board_sync.tick(host)          # each open project with a `[board]` in orkcraft.toml: one thread a project, never blocking the clock
    board_sync.close(host)         # the host's quit: every lease this computer holds is given back
    host.board_sync.holds(p)       # whether this computer holds p's Board (the inbox is taken only by the holder)
    host.board_sync.status(p)      # {} · {"board_held": {by, kind, until}} · {"board_aside": {since, path}}: the host's status, for Settings' face (E)

**Nothing runs without `[board]`** (realm/board_branch.py `read_config`): no thread, no git, no file.

At the start, and then every `RENEW_S`: not holding, `take` (realm/board_lease.py). Taken: the host goes on on the unpacked Board. Held by
another (a cloud run): the Board is read from the branch's files (`follow`) and nothing that writes runs (`Ideas.board_held` is set; the
keeper and the runner refuse in the words *A cloud run has the Board: it gives it back when it ends (at most 30 min)*); tried again at the next
tick. Holding: `renew` every `RENEW_S`, and the Board pushed at most every `PUSH_S` while it changes, at once when a card for the person
comes to the hand (`phone_journal.came_at`). Offline: the host goes on working; back online, the lease's rules decide (the push, or the
changes kept aside in `<state_dir>/board-aside/<at>/`, said once). No face of its own: a toast now and then, the rest is in `status`.
"""
from __future__ import annotations

import datetime as dt
import socket
import threading
import time
from pathlib import Path
from typing import Any

from orkboard.realm import board_branch, board_lease

PUSH_S = 120             # the Board is pushed at most this often while it changes
LOOK_S = 10              # the Board's files are looked at for a change this often, at most
CLOUD_HELD = "A cloud run has the Board: it gives it back when it ends (at most 30 min)"
COMPUTER_HELD = "Another computer has the Board: it gives it back when Orkboard is closed there (at most 10 min)"
ASIDE_LINE = "Another worker had the Board while you were offline: your changes since {since} are kept aside"


class _State:
    def __init__(self) -> None:
        self.holding = False
        self.next_take = 0.0                      # monotonic: not before
        self.last_renew = 0.0
        self.last_push = 0.0
        self.last_look = 0.0
        self.held: dict | None = None             # {by, kind, until} while another holds it
        self.aside: dict | None = None            # {since, path}
        self.offline = ""
        self.thread: threading.Thread | None = None


def machine_name() -> str:
    return socket.gethostname() or "this computer"


class BoardSync:
    def __init__(self, host: Any, me: str = "") -> None:
        self.host = host
        self.me = me or machine_name()
        self._states: dict[str, _State] = {}

    # -- what others read ------------------------------------------------------------------------------------

    def _state(self, p: Any) -> _State:
        return self._states.setdefault(p.path, _State())

    def holds(self, p: Any) -> bool:
        st = self._states.get(p.path)
        return bool(st and st.holding)

    def status(self, p: Any) -> dict:
        st = self._states.get(p.path)
        out: dict = {}
        if st and st.held:
            out["board_held"] = dict(st.held)
        if st and st.aside:
            out["board_aside"] = dict(st.aside)
        return out

    # -- the clock -------------------------------------------------------------------------------------------

    def tick(self) -> None:
        try:
            for p in list(getattr(self.host.projects, "open_ones", None) or []):
                if self.host.demo or board_branch.read_config(p.root) is None:
                    continue                      # no [board]: nothing of this runs
                st = self._state(p)
                if st.thread is not None and st.thread.is_alive():
                    continue
                st.thread = threading.Thread(target=self.run, args=(p, st), daemon=True, name="orkboard-board")
                st.thread.start()
        except Exception:                         # a Board that cannot be kept troubles no work
            pass

    def _args(self, p: Any, config: board_branch.BoardConfig) -> tuple:
        """What `board_lease` takes for this project: the root, the state folder, the config, who, the Board's tree (made when missing)."""
        try:
            p.ideas.root()                        # the Board's tree is made when the repository can hold one
            tree = p.ideas._tree(p.ideas.wiki())
        except Exception:
            tree = None
        return p.root, Path(p.ideas.state_dir), config, self.me, board_lease.COMPUTER, tree

    def run(self, p: Any, st: _State, now: dt.datetime | None = None, mono: float | None = None) -> None:
        """One tick of one project. Never raises."""
        try:
            config = board_branch.read_config(p.root)
            if config is None:
                return
            mono = time.monotonic() if mono is None else mono
            now = now or dt.datetime.now(dt.timezone.utc)
            if not st.holding:
                if mono >= st.next_take:
                    self._take(p, st, config, now, mono)
            else:
                self._hold(p, st, config, now, mono)
        except Exception:
            pass

    def _take(self, p: Any, st: _State, config: board_branch.BoardConfig, now: dt.datetime, mono: float) -> None:
        st.next_take = mono + board_lease.RENEW_S
        root, state, cfg, me, kind, tree = self._args(p, config)
        got = board_lease.take(root, state, cfg, me, kind, now, tree=tree)
        if got.get("held"):
            st.holding, st.held, st.offline = True, None, ""
            st.last_renew = st.last_push = st.last_look = mono
            p.ideas.board_held = ""
            if got.get("aside"):
                self._aside(p, st, {"since": "", "path": got["aside"]})
            self._changed(p)
        elif got.get("offline"):
            st.held, st.offline = None, got.get("why", "")
            p.ideas.board_held = ""               # the person is at it: the host goes on as it was
        else:
            st.held = {"by": got.get("by", ""), "kind": got.get("kind", ""), "until": got.get("until", "")}
            p.ideas.board_held = CLOUD_HELD if st.held["kind"] == board_lease.CLOUD_RUN else COMPUTER_HELD
            seen = board_lease.follow(root, state, cfg, me, now, tree=tree)       # read from the branch's files, as a reader
            if seen.get("followed"):
                if seen.get("aside"):
                    self._aside(p, st, {"since": seen.get("since", ""), "path": seen["aside"]})
                self._changed(p)

    def _hold(self, p: Any, st: _State, config: board_branch.BoardConfig, now: dt.datetime, mono: float) -> None:
        due = mono - st.last_renew >= board_lease.RENEW_S
        root, state, cfg, me, kind, tree = self._args(p, config)
        if not due:
            if mono - st.last_look < LOOK_S:
                return
            st.last_look = mono
            came = getattr(getattr(self.host, "phone_journal", None), "came_at", lambda q: 0.0)(p)
            urgent = came > st.last_push
            if not (urgent or (mono - st.last_push >= PUSH_S and board_lease.changed(state, getattr(tree, "wiki_rel", "") or ""))):
                return
        got = board_lease.renew(root, state, cfg, me, kind, now, tree=tree)
        st.last_renew = st.last_push = st.last_look = mono
        if got.get("lost"):
            st.holding = False
            st.next_take = 0.0                    # looked at again at the next tick: who holds it now
            self._aside(p, st, {"since": got.get("since", ""), "path": got.get("aside", "")})
            self._changed(p)
        elif got.get("offline"):
            st.offline = got.get("why", "")       # keep working: the person is at it
        else:
            st.offline = ""

    def _aside(self, p: Any, st: _State, info: dict) -> None:
        """Another worker had the Board while this one was away: said once, in words."""
        st.aside = info
        since = str(info.get("since") or "")
        try:
            when = dt.datetime.fromisoformat(since).astimezone().strftime("%H:%M") if since else "the last push"
        except ValueError:
            when = "the last push"
        try:
            p.toast(ASIDE_LINE.format(since=when), title="The Board", severity="warning")
        except Exception:
            pass

    def _changed(self, p: Any) -> None:
        """The Board's files changed under the host (a taken Board): the faces read it again."""
        try:
            p.ideas._publish("")
        except Exception:
            pass

    # -- the quit ----------------------------------------------------------------------------------------------

    def close(self, now: dt.datetime | None = None) -> None:
        """Every lease this computer holds is given back, with the Board pushed (a failure leaves it to run out: at most ten minutes)."""
        now = now or dt.datetime.now(dt.timezone.utc)
        for p in list(getattr(self.host.projects, "open_ones", None) or []):
            st = self._states.get(p.path)
            if not st or not st.holding:
                continue
            try:
                config = board_branch.read_config(p.root)
                if config is not None:
                    p.ideas.tree_flush(force=True)
                    root, state, cfg, me, kind, tree = self._args(p, config)
                    board_lease.give_back(root, state, cfg, me, kind, now, tree=tree)
            except Exception:
                pass
            st.holding = False


def tick(host: Any) -> None:
    sync = getattr(host, "board_sync", None)
    if sync is not None:
        sync.tick()


def close(host: Any) -> None:
    sync = getattr(host, "board_sync", None)
    if sync is not None:
        sync.close()
