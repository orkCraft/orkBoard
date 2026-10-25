"""Canvases as `gui/ideas.py`'s `Ideas` has them (docs/specs/78-canvases.md §2–§4): `ideas.canvases`, the cards; `ideas.canvas_seen`,
one folded into Seen; `ideas.canvas_open`, its link in the person's browser; `ideas.canvas_file`, its local file for the preview.
The store is core/canvases.py, the readers sources/canvases.py; the readers run every REFRESH_S off the host's thread.
"""
from __future__ import annotations

import base64
import mimetypes
import os
import threading
import webbrowser
from pathlib import Path

from orkboard.core.canvases import MADE, Canvases
from orkboard.gui.ideas_args import IdeasError, _device, _str
from orkboard.realm import event_log, harnesses, ideas, roles
from orkboard.sources import sessions
from orkboard.sources.canvases import TOOL_WORDS, Canvas, link_host

REFRESH_S = 30.0
PICTURES = (".png", ".jpg", ".jpeg", ".gif", ".webp")
PAGES = (".html", ".htm", ".md", ".markdown")
PICTURE_MAX, PAGE_MAX = 8 * 1024 * 1024, 2 * 1024 * 1024


def codex_images_dir() -> Path:
    home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return Path(home) / "generated_images"


class CanvasesMixin:
    """Needs the host (`repo_root`, `call`, `publish`), `state_dir`, `root()`, `_ev` and `target_of_idea`."""

    _canvases: Canvases | None = None
    _canvas_at = float("-inf")
    _canvas_busy = False

    @property
    def canvas_store(self) -> Canvases:
        if self._canvases is None:
            self._canvases = Canvases(Path(self.host.repo_root), self._canvas_told)
        return self._canvases

    def _canvas_told(self, topic: str, **data) -> None:
        """A canvas made or seen: on the bus from the host's thread, and in the event log."""
        if topic == MADE:
            self._ev(event_log.CANVAS_MADE, tool=data.get("tool"), kind=data.get("kind"),
                     task=(self._canvas_tasks().get(str(data.get("session") or "")) or {}).get("task", ""))
        self.host.call(lambda: self.host.publish(topic, **data))

    def canvas_tick(self, now: float) -> None:
        """The readers, every REFRESH_S, on a thread of their own (a transcript is not read on the host's)."""
        if self.host.demo or self._canvas_busy or now - self._canvas_at < REFRESH_S:
            return
        self._canvas_at, self._canvas_busy = now, True
        agy = [c.session for c in self.canvas_store.shown()[0] + self.canvas_store.shown()[1] if c.tool == "agy" and c.session]

        def run() -> None:
            try:
                self.canvas_store.refresh(sorted(set(agy) | set(self._canvas_tasks())))
            finally:
                self._canvas_busy = False
        threading.Thread(target=run, name="canvases", daemon=True).start()

    # -- the cards -------------------------------------------------------------------------------------------

    def _canvas_tasks(self) -> dict[str, dict]:
        """{session: {idea, task, idea_title, head}} of the project's tasks that ran."""
        out: dict[str, dict] = {}
        folder = self.state_dir / "ideas"
        if not folder.is_dir():
            return out
        read = roles.known(self.state_dir)
        for d in folder.iterdir():
            plan = ideas.plan(self.state_dir, d.name) if d.is_dir() else None
            for t in (plan or {}).get("tasks") or []:
                if t.get("session"):
                    out[str(t["session"])] = {"idea": d.name, "task": str(t.get("id") or ""), "plan_task": t}
        for got in out.values():
            page = ideas.idea_page(self.root(make=False), got["idea"])
            got["idea_title"] = (page.title if page else "") or got["idea"]
            got["head"] = roles.task_head(self.state_dir, got.pop("plan_task"), self.target_of_idea(got["idea"]), read, self.tiers_of_idea(got["idea"]))
        return out

    @staticmethod
    def canvas_head(c: Canvas, task: dict | None) -> dict:
        """Design's race, the elf, at the tier of the model that drew it; a design role's own head when its task drew it."""
        head = (task or {}).get("head") or {}
        if head.get("craft") == "design":
            return head
        return {"craft": "design", "race": roles.RACES["design"], "tier": harnesses.tier_of_model(c.model) or "warrior"}

    def _canvas_card(self, c: Canvas, tasks: dict[str, dict]) -> dict:
        task = tasks.get(c.session) if c.session else None
        host = link_host(c.url)
        return {"key": c.key, "tool": c.tool, "tool_word": TOOL_WORDS.get(c.tool, c.tool), "kind": c.kind, "title": c.title,
                "at": c.at, "url": c.url if host else "", "host": host, "link_text": "" if host else c.url,
                "local": bool(self._canvas_path(c)), "session": c.session, "model": c.model,
                "idea": (task or {}).get("idea", ""), "idea_title": (task or {}).get("idea_title", ""),
                "task": (task or {}).get("task", ""), "head": self.canvas_head(c, task)}

    def canvases(self, args: dict) -> dict:
        """`{}`: `{canvases: [card], seen: [card]}`, the canvases not seen and the last seen, newest first (§3)."""
        new, seen = self.canvas_store.shown()
        tasks = self._canvas_tasks() if new or seen else {}
        return {"canvases": [self._canvas_card(c, tasks) for c in new], "seen": [self._canvas_card(c, tasks) for c in seen]}

    def canvas_seen(self, args: dict) -> dict:
        if not self.canvas_store.seen(_str(args, "key", 2000)):
            raise IdeasError("That canvas is not on the Board any more")
        self._ev(event_log.CANVAS_SEEN, args)
        return {"ok": True}

    def _canvas(self, args: dict) -> Canvas:
        c = self.canvas_store.get(_str(args, "key", 2000))
        if c is None:
            raise IdeasError("That canvas is not on the Board any more")
        return c

    def canvas_open(self, args: dict) -> dict:
        """Its link in the computer's browser, when its host is an allowed one (the phone opens the link itself)."""
        if _device(args) == "phone":
            raise IdeasError("The phone opens a canvas's link itself")
        c = self._canvas(args)
        if not link_host(c.url):
            raise IdeasError("This canvas has no link that opens here")
        webbrowser.open(c.url)
        return {"ok": True}

    # -- its local file --------------------------------------------------------------------------------------

    def _canvas_roots(self) -> list[Path]:
        return [Path(self.host.repo_root), codex_images_dir(), sessions.agy_brain_dir()]

    def _canvas_path(self, c: Canvas) -> Path | None:
        """Its file when it is a picture or a page under the project, Codex's pictures or agy's brain folder."""
        if not c.file:
            return None
        try:
            p = Path(c.file).resolve()
        except (OSError, RuntimeError):
            return None
        if p.suffix.lower() not in PICTURES + PAGES or not p.is_file():
            return None
        for root in self._canvas_roots():
            try:
                p.relative_to(root.resolve())
                return p
            except (ValueError, OSError):
                continue
        return None

    def canvas_file(self, args: dict) -> dict:
        """`{key}`: `{name, mime, data}` (base64) of its picture, or `{name, mime, text}` of its page, for the preview."""
        c = self._canvas(args)
        p = self._canvas_path(c)
        if p is None:
            raise IdeasError("This canvas has no file to show here")
        size = p.stat().st_size
        mime = mimetypes.guess_type(p.name)[0] or ("text/markdown" if p.suffix.lower() in (".md", ".markdown") else "text/plain")
        if p.suffix.lower() in PICTURES:
            if size > PICTURE_MAX:
                raise IdeasError("The picture is too large to show here")
            return {"name": p.name, "mime": mime, "data": base64.b64encode(p.read_bytes()).decode("ascii")}
        if size > PAGE_MAX:
            raise IdeasError("The page is too large to show here")
        return {"name": p.name, "mime": mime, "text": p.read_text(encoding="utf-8", errors="replace")}


def canvas_commands(m: CanvasesMixin) -> dict:
    return {"ideas.canvases": m.canvases, "ideas.canvas_seen": m.canvas_seen, "ideas.canvas_open": m.canvas_open,
            "ideas.canvas_file": m.canvas_file}

