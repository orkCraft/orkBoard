"""A picture of what a task changed (docs/specs/85-the-elf-asks-and-shows.md §3, decisions §102). A task whose diff touches what people see
(pages, components, styles, assets) gets a picture after its tests: the project's own preview is opened on the task's worktree, the screen
drawn in a headless Chromium, the preview closed. No model. A task that changed nothing people see gets none; one whose project has no preview
that opens says so (*no picture: no preview*, realm/idea_shots.py `NONE`). The picture stays in the goal's state folder, with the candidates.

    idea_shot.sees(["src/App.css", "tests/x.py"])                # True: a stylesheet is what people see
    idea_shot.preview_of(state_dir, worktree)                    # how the preview opens: static · a command ("npm run dev"), else None
    ok, why = idea_shot.make(state_dir, worktree, dest, "/")     # the PNG written to `dest`, or the reason there is none (`no preview`, `no browser`)
    runner.shoot(slug, tid, worktree, start_sha, rnd)            # the runner's: the task keeps `shot` (a mixin of IdeaRunner)

The preview is, in this order: the `preview` line of `.orkcraft/checks.toml` (`preview = "npm run dev"`; `preview_port`, `preview_path`,
`preview_size = "390x844"` beside it), a static `index.html` at the worktree's root (served by Python on a port of its own), the project's
`package.json` script `dev`, `preview` or `start`. The command runs in the worktree with `PORT` set; the port is the one it prints or the
one asked. Time-boxed: up to `OPEN_S` seconds for the port, `DRAW_S` for the picture, then the preview is killed with its process group.
The browser is `$ORKCRAFT_CHROMIUM`, the preinstalled one (`/opt/pw-browsers/chromium`), one on the PATH, else Playwright's own.
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import tomllib
from pathlib import Path
from typing import Iterator

from orkboard.realm import event_log, idea_shots

OPEN_S, DRAW_S = 20.0, 25.0
SIZE = (1280, 800)
SEEN = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".vue", ".svelte",
        ".jsx", ".tsx", ".astro", ".ejs", ".hbs", ".njk", ".jinja", ".j2"}
SEEN_DIRS = ("components", "pages", "views", "screens", "templates", "static", "public", "assets", "styles", "ui")
NOT_SEEN = ("tests", "test", "__tests__", "node_modules", "docs", "design", ".orkcraft")        # `design/` holds a look picked, not the product
SCRIPTS = ("dev", "preview", "start")
URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]):(\d{2,5})")
BROWSERS = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome")


def sees(touched: list[str]) -> bool:
    """Whether a task's diff touches what people see: a page, a stylesheet, a component, a picture (not a test, a document or a look picked)."""
    for name in touched:
        parts = Path(name).parts
        if not parts or any(p in NOT_SEEN for p in parts[:-1]):
            continue
        if Path(name).suffix.lower() in SEEN or any(p in SEEN_DIRS for p in parts[:-1]):
            return True
    return False


def _config(state_dir: Path) -> dict:
    try:
        data = tomllib.loads((Path(state_dir) / "checks.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def preview_of(state_dir: Path, worktree: Path) -> dict | None:
    """How the project's preview opens on a worktree: `{"how": "command", "run": [argv], "port": n | None}` or `{"how": "static"}`; None with none."""
    conf = _config(state_dir)
    port = conf.get("preview_port") if isinstance(conf.get("preview_port"), int) and not isinstance(conf.get("preview_port"), bool) else None
    if isinstance(conf.get("preview"), str) and conf["preview"].strip():
        try:
            return {"how": "command", "run": shlex.split(conf["preview"]), "port": port}
        except ValueError:
            return None
    if (Path(worktree) / "index.html").is_file():
        return {"how": "static"}
    try:
        scripts = json.loads((Path(worktree) / "package.json").read_text(encoding="utf-8")).get("scripts")
    except (OSError, ValueError, AttributeError):
        return None
    name = next((s for s in SCRIPTS if isinstance(scripts, dict) and isinstance(scripts.get(s), str)), "")
    return {"how": "command", "run": ["npm", "run", name], "port": port} if name else None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def _kill(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (OSError, ProcessLookupError):
        pass
    try:
        proc.wait(5)
    except (subprocess.TimeoutExpired, OSError):
        pass


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        pass


@contextlib.contextmanager
def opened(how: dict, worktree: Path, seconds: float = OPEN_S, env: dict[str, str] | None = None) -> Iterator[int | None]:
    """The preview open on a worktree: the port it listens on, or None when it did not open in `seconds`. It is closed on leaving.
    `env`: more for the command's environment (Play asks `HOST=127.0.0.1`, spec 88 §5); a static page is served on 127.0.0.1 always."""
    if how["how"] == "static":
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(worktree)))
        threading.Thread(target=server.serve_forever, daemon=True, name="idea-shot-static").start()
        try:
            yield server.server_address[1]
        finally:
            server.shutdown()
            server.server_close()
        return
    port = how.get("port") or _free_port()
    seen: list[int] = []
    try:
        proc = subprocess.Popen(how["run"], cwd=str(worktree), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", start_new_session=os.name == "posix", env={**os.environ, **(env or {}), "PORT": str(port), "BROWSER": "none", "CI": "1"})
    except (OSError, ValueError):
        yield None
        return

    def read() -> None:
        for line in proc.stdout or ():
            for m in URL.finditer(line):
                seen.append(int(m.group(1)))

    threading.Thread(target=read, daemon=True, name="idea-shot-out").start()
    found: int | None = None
    try:
        end = time.monotonic() + seconds
        while time.monotonic() < end and found is None and proc.poll() is None:
            found = next((p for p in [*seen, port] if _listening(p)), None)
            if found is None:
                time.sleep(0.25)
        yield found
    finally:
        _kill(proc)


def browser() -> str | None:
    """The Chromium to draw with, else None."""
    for path in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium"):
        if path and Path(path).exists():
            return path
    if found := next((p for n in BROWSERS if (p := shutil.which(n))), None):
        return found
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            own = p.chromium.executable_path
        return own if own and Path(own).exists() else None
    except Exception:
        return None


def draw(url: str, dest: Path, size: tuple[int, int] = SIZE, seconds: float = DRAW_S) -> bool:
    """The page at `url` drawn into the PNG `dest`; False when the browser failed or wrote nothing."""
    exe = browser()
    if exe is None:
        return False
    cmd = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--disable-extensions",
           f"--window-size={size[0]},{size[1]}", "--virtual-time-budget=4000", f"--screenshot={dest}", url]
    if hasattr(os, "geteuid") and os.geteuid() == 0:                 # Chromium refuses to run as root otherwise
        cmd.insert(2, "--no-sandbox")
    try:
        subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=seconds, check=False,
                       start_new_session=os.name == "posix")
    except (OSError, subprocess.TimeoutExpired):
        return False
    try:
        return dest.stat().st_size > 0
    except OSError:
        return False


def _size(conf: dict) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{3,4})x(\d{3,4})", str(conf.get("preview_size") or ""))
    return (int(m.group(1)), int(m.group(2))) if m else SIZE


def _path(screen: str, conf: dict) -> str:
    text = screen if screen.startswith("/") else str(conf.get("preview_path") or "/")
    return text if text.startswith("/") and re.fullmatch(r"/[A-Za-z0-9_./#?=&%-]{0,200}", text) else "/"


def make(state_dir: Path, worktree: Path, dest: Path, screen: str = "") -> tuple[bool, str]:
    """The picture of the screen `screen` (a path, else the preview's own, else "/") of the project on `worktree`, into the PNG `dest`:
    (True, "") or (False, why) with why `no preview` (nothing opens) or `no browser`."""
    how = preview_of(state_dir, worktree)
    if how is None:
        return False, "no preview"
    if browser() is None:
        return False, "no browser"
    conf = _config(state_dir)
    with opened(how, worktree, OPEN_S) as port:
        if port is None:
            return False, "no preview"
        if not draw(f"http://127.0.0.1:{port}{_path(screen, conf)}", dest, _size(conf)):
            return False, "no picture"
    return True, ""


class ShotMixin:
    """On `IdeaRunner` (core/idea_runner.py): `shoot` after a task's tests. Needs its `state_dir`, `settings`, `git`, `_task`, `_set_task`, `_emit`."""

    def shoot(self, slug: str, tid: str, path: Path, start_sha: str, rnd: int) -> None:
        """The task keeps `shot`: its picture, `{"none": true}` when what it changed is seen but no preview opens, None when it changed nothing
        people see (or the setting `ideas.shots` is off). Never raises: a picture is a nicety, the work goes on without it."""
        from orkboard.core import idea_runner
        task = self._task(slug, tid)
        try:
            if idea_runner.setting(self.settings, "shots", True) is False or not sees(self.git.touched(path, start_sha)):
                return self._set_task(slug, tid, shot=None)
            began = time.monotonic()
            with tempfile.TemporaryDirectory(prefix="orkboard-shot-") as tmp:
                ok, why = make(self.state_dir, path, Path(tmp) / "shot.png", str(task.get("screen") or ""))
                kept = idea_shots.store(self.state_dir, slug, tid, rnd, Path(tmp) / "shot.png") if ok else None
            self._set_task(slug, tid, shot=kept or {"none": True})
            self._emit(event_log.SHOT_TAKEN, idea=slug, task=tid, ok=kept is not None, why="" if kept else (why if not ok else "no picture"),
                       seconds=round(time.monotonic() - began, 1), round=rnd)
        except Exception:
            self._set_task(slug, tid, shot=None)
