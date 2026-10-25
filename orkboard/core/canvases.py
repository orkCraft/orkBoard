"""The project's canvases (docs/specs/78-canvases.md §2): what an AI tool drew outside the code, kept and told.

    store = Canvases(repo_root, publish)        # publish(topic, **data): the bus's (core/bus.py), on the host's thread
    store.add(canvas)                           # a canvas made or drawn again: True when it is new or moved
    store.refresh(agy_sessions)                 # the readers' canvases (sources/canvases.py), added; how many came
    store.shown()                               # (not seen, newest first; the last SEEN_SHOWN seen, newest first)
    store.seen(key)                             # folds it into Seen; False for a key it does not hold
    store.get(key) · store.rev                  # one canvas · one up at each change

`<project>/.orkcraft/canvases.jsonl`: a line per canvas made or drawn again (`Canvas.line()`), `{"key", "seen"}` per
canvas seen; a key's last canvas line wins, and a canvas drawn again after it was seen is new again. The hook
(hooks/canvas.py) appends lines too: the file is read again when it changed. At most KEEP canvases: older ones go at the
next rewrite. It shows no toast and no dialog.
"""
from __future__ import annotations

import datetime as dt
import json
import threading
from pathlib import Path
from typing import Any, Callable

from orkboard.sources.canvases import Canvas, read_all

FILE = "canvases.jsonl"
KEEP = 200
SEEN_SHOWN = 20
MADE, SEEN = "canvas.made", "canvas.seen"


def path(repo_root: Path) -> Path:
    return Path(repo_root) / ".orkcraft" / FILE


class Canvases:
    def __init__(self, repo_root: Path, publish: Callable[..., Any] | None = None) -> None:
        self.repo_root = Path(repo_root)
        self.publish = publish or (lambda topic, **data: None)
        self.rev = 0
        self._lock = threading.Lock()
        self._by: dict[str, Canvas] = {}
        self._seen: dict[str, str] = {}
        self._stamp: tuple[int, int] | None = None
        self._lines = 0

    # -- the file --------------------------------------------------------------------------------------------

    def _load(self) -> None:
        """The file read again when its size or mtime changed (the hook appends to it)."""
        p = path(self.repo_root)
        try:
            st = p.stat()
        except OSError:
            self._by, self._seen, self._stamp, self._lines = {}, {}, None, 0
            return
        stamp = (st.st_size, st.st_mtime_ns)
        if stamp == self._stamp:
            return
        by: dict[str, Canvas] = {}
        seen: dict[str, str] = {}
        lines = 0
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            lines += 1
            c = Canvas.from_line(d)
            if c is not None:
                if c.key in by and c.at < by[c.key].at:
                    continue
                by.pop(c.key, None)
                by[c.key] = c
                if seen.get(c.key, "") < c.at:
                    seen.pop(c.key, None)          # drawn again after it was seen: new again
            elif isinstance(d, dict) and isinstance(d.get("key"), str) and isinstance(d.get("seen"), str):
                seen[d["key"]] = d["seen"]
        if stamp != self._stamp and self._stamp is not None and (by.keys() != self._by.keys() or seen != self._seen or
                                                                 any(by[k] != self._by.get(k) for k in by)):
            self.rev += 1
        self._by, self._seen, self._stamp, self._lines = by, seen, stamp, lines

    def _append(self, lines: list[dict]) -> None:
        p = path(self.repo_root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            for d in lines:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        self._stamp = None
        self._load()
        if len(self._by) > KEEP or self._lines > 4 * KEEP:
            self._rewrite()

    def _rewrite(self) -> None:
        keep = sorted(self._by.values(), key=lambda c: c.at)[-KEEP:]
        out = [c.line() for c in keep] + [{"key": k, "seen": v} for k, v in self._seen.items()
                                          if any(c.key == k for c in keep)]
        p = path(self.repo_root)
        tmp = p.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out), encoding="utf-8")
        tmp.replace(p)
        self._stamp = None
        self._load()

    # -- what changes it -------------------------------------------------------------------------------------

    def add(self, canvas: Canvas) -> bool:
        """A canvas made or drawn again: kept (True) unless the store holds it already at that time or later."""
        return self._add([canvas]) > 0

    def _add(self, found: list[Canvas]) -> int:
        with self._lock:
            self._load()
            new = []
            for c in found:
                was = self._by.get(c.key)
                if was is not None and was.at >= c.at:
                    continue
                new.append(c)
            if not new:
                return 0
            self._append([c.line() for c in new])
            self.rev += 1
        for c in new:
            self.publish(MADE, key=c.key, tool=c.tool, kind=c.kind, session=c.session)
        return len(new)

    def refresh(self, agy_sessions: list[str] = ()) -> int:
        """The readers' canvases added; how many were new or moved. Never raises."""
        try:
            return self._add(read_all(self.repo_root, list(agy_sessions)))
        except OSError:
            return 0

    def seen(self, key: str) -> bool:
        with self._lock:
            self._load()
            if key not in self._by:
                return False
            if key not in self._seen:
                self._append([{"key": key, "seen": dt.datetime.now().astimezone().isoformat(timespec="seconds")}])
                self.rev += 1
        self.publish(SEEN, key=key)
        return True

    # -- what it holds ---------------------------------------------------------------------------------------

    def get(self, key: str) -> Canvas | None:
        with self._lock:
            self._load()
            return self._by.get(key)

    def shown(self) -> tuple[list[Canvas], list[Canvas]]:
        """(the canvases not seen, newest first; the last SEEN_SHOWN seen, newest first)."""
        with self._lock:
            self._load()
            newest = sorted(self._by.values(), key=lambda c: c.at, reverse=True)
            return ([c for c in newest if c.key not in self._seen],
                    [c for c in newest if c.key in self._seen][:SEEN_SHOWN])

    def new_count(self) -> int:
        return len(self.shown()[0])
