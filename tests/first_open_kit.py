"""What the first open's browser tests share (docs/specs/130-the-first-open-is-the-orkmasters.md §*Order of building*: the faces' tests never call a real tool): Orkboard's real host on a folder of the test's, `tools.detect` and the request's `ask` faked,
the machine's settings fresh, and the page in the module's browser."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard import tools
from orkboard.gui.board_host import Orkboard
from orkboard.gui.server import Server


def found(*ids: str, signed_out: tuple[str, ...] = ()) -> list[tools.ToolStatus]:
    return [tools.ToolStatus(t, found=t.id in ids, version="2.0" if t.id in ids else "", logged_in=False if t.id in signed_out else True) for t in tools.TOOLS]


def git_repo(path: Path, name: str = "app.py", text: str = "print('hello')\n") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text, encoding="utf-8")
    run = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run([*run, "add", "-A"], cwd=path, check=True)
    subprocess.run([*run, "commit", "-qm", "init"], cwd=path, check=True)
    return path


class Desk:
    """The host, the server and the page of one test. `asked`: the tools the faked request went to; `fail[tool]`: an exception it raises."""

    def __init__(self, browser, root: Path | None, status, width=1280, height=800):
        self.asked: list[str] = []
        self.fail: dict[str, Exception] = {}
        tools.detect = lambda *a, **k: status()
        tools.detect_others = lambda *a, **k: []
        self.host = Orkboard(root) if root is not None else Orkboard()
        self.host.tools_host._ask = self._ask
        self.server = Server(self.host)
        self.thread = self.server.start_thread()
        self.errors: list[str] = []
        self.pg = browser.new_page(viewport={"width": width, "height": height})
        self.pg.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))

    def _ask(self, tool, prompt, model=None):
        self.asked.append(tool)
        if tool in self.fail:
            raise self.fail[tool]
        return "ok"

    def open(self):
        self.pg.goto(self.server.url)
        return self.pg

    def close(self):
        self.pg.close()
        self.server.stop()
        self.thread.join(10)
        sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def desk(gui, tmp_path, monkeypatch):
    """`make(root=None, status=...)`: a fresh machine (no settings file: an empty hand) and a state of the test's own. The env is the `gui` fixture's."""
    _server, browser = gui
    monkeypatch.setenv("ORKCRAFT_SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.setenv("ORKCRAFT_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(tools, "detect", tools.detect)
    monkeypatch.setattr(tools, "detect_others", tools.detect_others)
    made: list[Desk] = []

    def make(root=None, status=lambda: found("claude", "codex", "agy"), **more):
        d = Desk(browser, root, status, **more)
        made.append(d)
        return d

    yield make
    for d in made:
        d.close()
    os.environ.pop("ORKCRAFT_TEST_NOTHING", None)
