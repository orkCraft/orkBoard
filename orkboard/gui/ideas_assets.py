"""Assets and Play as `gui/ideas.py`'s `Ideas` has them (docs/specs/88-assets-and-play.md §1–§5, decisions §104.11): what the project is
made of, seen and touched, and its own preview of dev. Read from the files, git and the picks (realm/assets.py): no model.

    ideas.assets {since?}             # the assets of dev's head by kind, each with its signed address and, since `since`, what changed and its goal
    ideas.asset_before {path, since}  # the signed address of the file as it was at `since`; url "" when it was added since
    ideas.play {fresh?, peek?}        # the project's preview of dev's head on 127.0.0.1: starting {stage, command, ports, since} → playing {url, commit} or failed {error, tail}
    ideas.play_stop {}                # it stops and its worktree goes

While it starts and plays, `logo` is the address of the project's logo in dev's head (realm/assets.py `logo`, served as an asset of that commit), "" with none:
Play's start screen shows it (docs/specs/107-what-the-owners-day-said.md §9.2).

**Play** opens the preview core/idea_shot.py opens for a picture (`preview_of`, `opened`: checks.toml's `preview`, a static `index.html`,
the package's `dev|preview|start` script) in a worktree of dev's head, `<state_dir>/play/` (its dependencies linked as a task's are,
realm/dep_links.py), on a port of its own on the machine's own address. While it starts it says its **stage** (spec 91 §5): `worktree` (making it), `command` (the command started, `command` as words:
`npm run dev`), `page` (something listens and no page has answered; `ports` asked so far), and `since` (seconds since the start); a failure says the
last `idea_shot.TAIL_LINES` lines of the command's output (`tail`, colour codes out). Its wait for a page is `PLAY_OPEN_S`, not the picture's.
One Play a project: a second `ideas.play` while it starts or
plays answers the same (and says dev's head now, `dev`); `fresh: true` starts it anew when dev moved. `ideas.play_stop`, closing the
project (`play_close`), quitting, its command ending, or IDLE_S with no face asking (`ideas.play`, `peek` too) stops it and removes the
worktree. The phones never get it: the commands refuse a phone, and the listener never serves the preview's port.
"""
from __future__ import annotations

import atexit
import shutil
import subprocess
import threading
import time
import weakref
from pathlib import Path
from typing import Any

from orkboard.core import idea_shot
from orkboard.gui import media
from orkboard.gui.ideas_args import IdeasError, _device, _str, _text
from orkboard.realm import assets, commit_goal, dep_links, event_log, idea_element, idea_git, ideas

IDLE_S = 600.0                       # ten minutes with no face asking: Play stops
PLAY_OPEN_S = 60.0                   # Play's wait for a page (a dev server's first build is slow); the picture's stays `idea_shot.OPEN_S`
ALIVE_S = 15.0                      # how often a playing preview is looked at (its command may have ended)
PLAY_DIR = "play"
TOPIC = "play.changed"               # on the bus when Play started, failed or stopped (the snapshot follows)
NO_PREVIEW = "no preview"
NO_PAGE = "nopage"                   # it started and listens, but no port it printed (nor PORT) answers a page (spec 90 §1)
NO_PAGE_WORDS = "The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or preview_path."
_LIVE: "weakref.WeakSet[Play]" = weakref.WeakSet()


def _stop_live() -> None:
    for play in list(_LIVE):
        play.stop("quit", wait=True)


atexit.register(_stop_live)


class Play:
    """One project's Play: its thread holds the preview open (`idea_shot.opened`) until it is told to stop."""

    def __init__(self, repo_root: Path, state_dir: Path, emit, publish) -> None:
        self.root, self.state_dir = Path(repo_root), Path(state_dir)
        self.path = self.state_dir / PLAY_DIR
        self._emit, self._publish = emit, publish
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._why = ""
        self.state, self.commit, self.url, self.error, self.none = "", "", "", "", False
        self.logo = ""                                   # the project's logo in dev's head, the address its start screen shows (spec 107 §9.2); "" when it has none
        self.ports: list[int] = []                       # the ports asked so far (stage `page`); a start that gave no page (`nopage`): the ports it asked (spec 90 §1)
        self.stage, self.command = "", ""                # while it starts: worktree · command · page (spec 91 §5), and the command as words
        self.tail: list[str] = []                        # the command's output, its last lines (`idea_shot.opened`'s `tail`)
        self.began = 0.0
        self.port: int | None = None
        self.seen_at = self._alive_at = 0.0
        _LIVE.add(self)

    # -- the answer ------------------------------------------------------------------------------------------

    def answer(self, ref: str) -> dict:
        if self.state == "playing":
            return {"state": "playing", "url": self.url, "commit": self.commit, "short": self.commit[:7], "dev": commit_goal.head(self.root, ref), "logo": self.logo}
        if self.state == "starting":
            return {"state": "starting", "commit": self.commit, "short": self.commit[:7], "stage": self.stage, "command": self.command,
                    "ports": list(self.ports), "since": round(max(0.0, time.monotonic() - self.began), 1), "logo": self.logo}
        if self.state == "failed":
            if self.error == NO_PAGE:
                return {"state": "failed", "why": NO_PAGE, "error": NO_PAGE_WORDS, "ports": list(self.ports), "tail": list(self.tail)}
            if self.none:
                return {"state": "failed", "error": self.error, "none": True}
            return {"state": "failed", "error": self.error, "tail": list(self.tail)}
        return {"state": "stopped"}                  # never started, stopped, or stopping

    # -- start and stop --------------------------------------------------------------------------------------

    def start(self, ref: str, fresh: bool = False) -> dict:
        """Starts the preview of `ref`'s head unless it starts or plays already (`fresh`: anew, when `ref` moved since)."""
        self.seen_at = time.monotonic()
        with self._lock:
            busy = self.state in ("starting", "playing")
        tip = commit_goal.head(self.root, ref)
        if busy and fresh and tip and tip != self.commit:
            self.stop("again", wait=True)
            busy = False
        if busy:
            return self.answer(ref)
        self._join()
        if not tip:
            self._set("failed", error=f"There is no {ref} branch yet")
            return self.answer(ref)
        with self._lock:
            self._stop = threading.Event()
            self.state, self.commit, self.url, self.error, self.none, self.port, self._why = "starting", tip, "", "", False, None, ""
            self.logo = self._logo_of(tip)
            self.ports, self.tail, self.stage, self.command, self.began = [], [], "worktree", "", time.monotonic()
            self._thread =threading.Thread(target=self._run, args=(tip, self._stop), name="play", daemon=True)
            self._thread.start()
        return self.answer(ref)

    def _logo_of(self, tip: str) -> str:
        """The signed address of the project's logo in `tip`'s tree (realm/assets.py `logo`), served as an asset of that commit; "" when it has none."""
        try:
            path = assets.logo(self.root, tip)
            return media.asset_url(tip, path) if path else ""
        except (OSError, subprocess.SubprocessError, ValueError):
            return ""

    def stop(self, why: str, wait: bool = False) -> bool:
        """Tells it to stop (`why`: stopped · idle · closed · quit · again · exited) and answers at once: its thread kills the preview and
        removes the worktree (`wait`: and this waits for it). False when nothing ran."""
        with self._lock:
            running = self.state in ("starting", "playing") and self._thread is not None
            if running:
                self._why, self.state = why, "stopping"
                self._stop.set()
        if running and wait:
            self.wait()
        return running

    def wait(self, seconds: float | None = None) -> None:
        """Waits for its thread (a start still opening the preview takes up to `PLAY_OPEN_S`)."""
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(PLAY_OPEN_S + 10 if seconds is None else seconds)

    def _join(self) -> None:
        self.wait()

    def tick(self, now: float | None = None) -> None:
        """Ten minutes with no face asking stops it; a preview whose command ended is stopped too."""
        now = time.monotonic() if now is None else now
        if self.state in ("starting", "playing") and now - self.seen_at > IDLE_S:
            self.stop("idle")
        elif self.state == "playing" and self.port and now - self._alive_at >= ALIVE_S:
            self._alive_at = now
            if not idea_shot._listening(self.port):
                self.stop("exited")

    # -- its thread ------------------------------------------------------------------------------------------

    def _set(self, state: str, **values: Any) -> None:
        with self._lock:
            if self.state != "stopping" or state == "":       # told to stop: only its end changes what it says
                self.state = state
            for k, v in values.items():
                setattr(self, k, v)
        self._publish()

    def _stage(self, stage: str, command: str = "", ports: list[int] | None = None) -> None:
        """Where the start is (`worktree` · `command` · `page`); the bus is told when it changed."""
        with self._lock:
            if self.state != "starting":
                return
            before = (self.stage, self.command, self.ports)
            self.stage, self.command, self.ports = stage, command, list(ports or [])
            changed = before != (self.stage, self.command, self.ports)
        if changed:
            self._publish()

    def _run(self, commit: str, stop: threading.Event) -> None:
        began = time.monotonic()
        try:
            self._worktree(commit)
            how = idea_shot.preview_of(self.state_dir, self.path)
            if how is None:
                return self._failed(began, stop, NO_PREVIEW, none=True)
            if stop.is_set():
                return self._failed(began, stop, "stopped")
            command = " ".join(how["run"]) if how["how"] == "command" else ""
            self._stage("command" if command else "page", command)             # a static page has no command: it waits for its page at once
            path, tried = idea_shot._path("", idea_shot._config(self.state_dir)), []
            with idea_shot.opened(how, self.path, PLAY_OPEN_S, env={"HOST": "127.0.0.1"}, path=path, tried=tried, tail=self.tail,
                                  asking=lambda ports: self._stage("page", command, ports)) as port:
                if port is None or stop.is_set():
                    return self._failed(began, stop, NO_PAGE if tried else "did not open", ports=tried)
                self._alive_at = time.monotonic()
                self._set("playing", port=port, url=idea_shot.url_of(port, path))
                self._emit(event_log.PLAY_STARTED, seconds=round(time.monotonic() - began, 1), ok=True, why="")
                stop.wait()
            self._remove()
            self._emit(event_log.PLAY_STOPPED, why=self._why or "stopped")
            self._set("", url="", port=None)
        except Exception as e:                       # Play never troubles the host: it says why it did not start
            self._failed(began, stop, " ".join(str(e).split())[:300] or type(e).__name__)

    def _failed(self, began: float, stop: threading.Event, why: str, none: bool = False, ports: list[int] | None = None) -> None:
        """It did not start: the worktree goes, `play_started` says why (or `play_stopped`, when it was told to stop meanwhile)."""
        self._remove()
        if stop.is_set():
            self._emit(event_log.PLAY_STOPPED, why=self._why or "stopped")
            return self._set("", url="", port=None)
        self._emit(event_log.PLAY_STARTED, seconds=round(time.monotonic() - began, 1), ok=False, why=why)
        self._set("failed", error=why, none=none, url="", port=None, ports=list(ports or []))

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, timeout=idea_git.GIT_TIMEOUT_S)

    def _worktree(self, commit: str) -> None:
        """A detached worktree of `commit` at `<state_dir>/play/`, made as a task's is (a leftover removed, the dependencies linked)."""
        with idea_git.lock_of(self.root):
            self._remove()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            got = self._git("worktree", "add", "--detach", str(self.path), commit)
            if got.returncode != 0:
                raise RuntimeError("could not make its worktree: " + (got.stderr or got.stdout).strip()[:200])
            dep_links.link(self.root, self.path)

    def _remove(self) -> None:
        with idea_git.lock_of(self.root):
            if self.path.exists() or self.path.is_symlink():
                self._git("worktree", "remove", "--force", str(self.path))
                if self.path.is_symlink():
                    self.path.unlink()
                elif self.path.exists():
                    shutil.rmtree(self.path, ignore_errors=True)
            self._git("worktree", "prune")


class AssetsMixin:
    """Needs `host`, `state_dir`, `root()`, `settings_now()`, `_ev` (gui/ideas.py)."""

    _play: Play | None = None

    def _ref(self) -> str:
        ref = str(self.settings_now().get("merge_into") or "dev")
        return ref if commit_goal.REF.fullmatch(ref) and ".." not in ref else "dev"

    def _goals(self, slugs: set[str]) -> dict[str, dict]:
        root = self.root(make=False)
        out = {}
        for slug in sorted(s for s in slugs if s):
            try:
                page = ideas.idea_page(root, slug)
                out[slug] = {"title": (page.title if page else "") or slug, "element": idea_element.of(self.state_dir, slug)}
            except ValueError:
                continue
        return out

    @staticmethod
    def _signed(row: dict, commit: str) -> dict:
        shot = row.pop("shot", None)
        row["url"] = media.url(shot["goal"], shot["id"], shot["file"]) if shot else media.asset_url(commit, row["id"])
        if row.get("others"):
            o = row["others"]
            row["others"] = {**o, "variants": [{**{k: v.get(k) for k in ("key", "name", "mime", "w", "h", "seconds")},
                                                "url": media.url(o["goal"], o["pick"], str(v["file"]))} for v in o["variants"]]}
        return row

    def assets(self, args: dict) -> dict:
        """`{since?}` (a commit, or a time: the device's last look): `{commit, short, ref, since, assets, removed, stacks, goals}`
        (As built, spec 88)."""
        root, ref = Path(self.host.repo_root), self._ref()
        since = _str(args, "since", 100).strip() if args.get("since") is not None else ""
        commit = commit_goal.head(root, ref)
        changes = assets.changed(self.state_dir, root, since, ref) if since else {"since": "", "added": [], "changed": [], "removed": []}
        rows = assets.listed(self.state_dir, root, ref, changes)
        stacks = assets.stacks(rows)
        rows = [self._signed(r, commit) for r in rows]
        removed = changes["removed"]
        return {"commit": commit, "short": commit[:7], "ref": ref, "since": changes["since"], "assets": rows, "removed": removed,
                "stacks": stacks, "goals": self._goals({r.get("goal") or "" for r in rows + removed})}

    def asset_before(self, args: dict) -> dict:
        """`{path, since}`: `{path, since, url, bytes, w, h, seconds}` of the file as it was at `since`; `url` "" when it was added since."""
        path, since = _text(args, "path", assets.PATH_MAX), _text(args, "since", 100)
        if not assets.allowed(path):
            raise IdeasError("That is not one of the project's assets")
        root = Path(self.host.repo_root)
        got = assets.before(self.state_dir, root, path, since, self._ref())
        if got is None:
            return {"path": path, "since": commit_goal.resolve(root, since, self._ref()), "url": ""}
        return {"path": path, "since": got["commit"], "url": media.asset_url(got["commit"], path),
                **{k: got[k] for k in ("bytes", "w", "h", "seconds")}}

    # -- Play ------------------------------------------------------------------------------------------------

    @property
    def player(self) -> Play:
        if self._play is None:
            def publish() -> None:
                self.host.call(lambda: self.host.publish(TOPIC))
            self._play = Play(Path(self.host.repo_root), self.state_dir, lambda e, **f: self._ev(e, **f), publish)
        return self._play

    def play(self, args: dict) -> dict:
        """`{fresh?, peek?}`: the preview of dev's head (`peek`: only what it is now). The phone is refused: it is the machine's own address."""
        if _device(args) == "phone":
            raise IdeasError("Play on the computer")
        if args.get("peek") is True:
            self.player.seen_at = time.monotonic()
            return self.player.answer(self._ref())
        return self.player.start(self._ref(), fresh=args.get("fresh") is True)

    def play_stop(self, args: dict) -> dict:
        if _device(args) == "phone":
            raise IdeasError("Play on the computer")
        return {"ok": True, "stopped": self.player.stop("stopped") if self._play is not None else False}

    def play_tick(self, now: float) -> None:
        if self._play is not None:
            self._play.tick(now)

    def play_close(self) -> None:
        """The project closes: its Play stops."""
        if self._play is not None:
            self._play.stop("closed")


def asset_commands(m: AssetsMixin) -> dict:
    return {"ideas.assets": m.assets, "ideas.asset_before": m.asset_before, "ideas.play": m.play, "ideas.play_stop": m.play_stop}
