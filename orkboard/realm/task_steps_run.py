"""The look at a task's steps while it works (docs/specs/129-a-tasks-steps.md H1.2–H1.4): every few seconds the worker's steps
file (its mtime first: no read when it did not change), the tool's own list from the output as it streams (`feed`), and
what it is doing, merged by realm/task_steps.py and kept beside the task's log, `<state_dir>/ideas/<slug>/<tid>.steps.json`,
so the snapshot reads them without touching the worktree. No model call.

    watch = Watch("codex", worktree, task_steps.kept_path(dir, tid), gate="make check", on_change=lambda steps: ...)
    watch.start()                       # the stale file of an earlier round is cleared, the thread looks every EVERY_S
    jobs.run_work(..., on_output=watch.feed)
    watch.stop()                        # one last look, the thread ends (the run's end, or Stop all)
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Callable

from orkboard.realm import task_steps

EVERY_S = 3.0


class Watch:
    def __init__(self, harness: str, worktree: Path, kept: Path, gate: str = "", every: float | None = None,
                 on_change: Callable[[dict], None] | None = None) -> None:
        self.worktree, self.kept, self.gate, self.every, self.on_change = Path(worktree), Path(kept), gate, EVERY_S if every is None else every, on_change
        self.reader = task_steps.reader_for(harness)
        self._lock = threading.Lock()
        self._end = threading.Event()
        self._thread: threading.Thread | None = None
        self._todo: list[dict] | None = None          # the tool's own list, the newest
        self._file: list[dict] | None = None          # the worker's file as last read
        self._seen: tuple[int, int] | None = None     # its (mtime, size): read again only when it changed
        self._last: dict | None = None                # what is kept now

    @property
    def path(self) -> Path:
        return self.worktree / task_steps.FILE

    def start(self) -> None:
        """A round begins: what an earlier round left (its file in the worktree, its kept steps) is cleared, so a list of before
        is not shown as this round's."""
        for stale in (self.path, self.kept):
            try:
                stale.unlink()
            except OSError:
                pass
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"steps-{self.kept.stem}")
        self._thread.start()

    def stop(self) -> None:
        self._end.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(10)
        self.poll()

    def feed(self, text: str) -> None:
        """A chunk of the tool's output, as it was written."""
        with self._lock:
            got = self.reader.feed(text)
            if got:
                self._todo = got

    def _loop(self) -> None:
        while not self._end.wait(self.every):
            self.poll()

    def _read_file(self) -> None:
        try:
            st = os.stat(self.path)
        except OSError:
            return
        mark = (st.st_mtime_ns, st.st_size)
        if mark != self._seen:
            self._seen = mark
            got = task_steps.read_file(self.path)
            if got is not None:                       # a file half written is read again at the next look
                self._file = got
            else:
                self._seen = None

    def poll(self) -> dict | None:
        """One look: the steps now (the snapshot's shape), kept when they changed. Never raises."""
        try:
            with self._lock:
                self._read_file()
                doing = task_steps.activity(self.worktree, self.reader.command, self.reader.command_at, self.gate)
                steps = task_steps.merge(self._file, self._todo, doing)
                if steps is None or steps == self._last:
                    return steps
                self._last = steps
            self._keep(steps)
            if self.on_change is not None:
                self.on_change(steps)
            return steps
        except Exception:
            return None

    def _keep(self, steps: dict) -> None:
        try:
            self.kept.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.kept.with_name(self.kept.name + ".tmp")
            tmp.write_text(json.dumps(steps, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.kept)
        except OSError:
            pass
