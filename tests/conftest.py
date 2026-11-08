"""Test fixtures: a plain git project, a home and settings of the test's own, and no real AI tool ever run."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _playwright_browsers() -> None:
    """Playwright looks for its browsers under the cache; every test moves HOME and XDG_CACHE_HOME to its own folder,
    so the machine's own place is pinned first, while the real environment is still there."""
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    if (base / "ms-playwright").is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(base / "ms-playwright")


_playwright_browsers()


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A plain git project, as Orkboard finds it anywhere: a README, some code, docs, loot."""
    repo = tmp_path / "project"
    (repo / "src").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "loot").mkdir()
    (repo / "README.md").write_text("# Demo project\n\nA small project for the tests.\n", encoding="utf-8")
    (repo / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "docs" / "notes.md").write_text("# Notes\n\n- first note\n", encoding="utf-8")
    (repo / "loot" / "report.md").write_text("# Report\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@orkcraft.local"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial test commit"], cwd=str(repo), check=True, capture_output=True)
    return repo


_quiet_path: list[str] = []


def _path_without_real_tools(factory: pytest.TempPathFactory) -> str:
    """$PATH with every folder that holds a real agent CLI or gh replaced by a copy of links to the rest."""
    if not _quiet_path:
        from orkboard.realm import harnesses
        tools = {h.default_bin for h in harnesses.REGISTRY.values()} | {"gh"}
        dirs = []
        for d in os.environ.get("PATH", "").split(os.pathsep):
            folder = Path(d)
            if d and any((folder / t).exists() for t in tools):
                copy = factory.mktemp("path")
                for entry in folder.iterdir():
                    if entry.name not in tools:
                        (copy / entry.name).symlink_to(entry)
                d = str(copy)
            dirs.append(d)
        _quiet_path.append(os.pathsep.join(dirs))
    return _quiet_path[0]


@pytest.fixture(autouse=True)
def isolated_layout_file(tmp_path: Path, tmp_path_factory: pytest.TempPathFactory,
                         monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every test on a home, a config and a cache of its own: the machine's settings, logins, keychain, update list
    and AI tools' folders are never read or written. Returns the layout file's path (the name is Orkline's)."""
    path = tmp_path / "orkcraft-layout.json"
    path_without_tools = _path_without_real_tools(tmp_path_factory)    # before HOME moves: it reads the real PATH
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("ORKCRAFT_LAYOUT_FILE", str(path))
    monkeypatch.setenv("ORKCRAFT_SETTINGS_FILE", str(tmp_path / "orkcraft-settings.json"))
    monkeypatch.setenv("ORKCRAFT_ONBOARDING", "0")      # the first screen's tests opt in
    monkeypatch.setenv("ORKCRAFT_LOGINS_FILE", str(tmp_path / "orkcraft-logins.json"))   # never the keychain
    monkeypatch.setenv("ORKCRAFT_ASSETS_DIR", str(tmp_path / "orkcraft-assets"))
    monkeypatch.setenv("ORKCRAFT_STATE_DIR", str(tmp_path / "orkcraft-state"))
    monkeypatch.delenv("ORKCRAFT_FOCUS", raising=False)
    monkeypatch.setenv("ORKCRAFT_LOOK", "camp")         # never by the shift: a test runs at any hour
    # No real model is asked anything: no limits read, no model list, no update list (test_updates.py opts in),
    # no usage stats or crash report sent.
    monkeypatch.setenv("ORKCRAFT_LIMITS", "0")
    monkeypatch.setenv("ORKCRAFT_MODEL_LIST", "0")
    monkeypatch.setenv("ORKCRAFT_NO_UPDATE", "1")
    monkeypatch.setenv("ORKCRAFT_NO_USAGE", "1")         # nothing is sent: test_crashes.py opts in, with no network
    monkeypatch.setenv("ORKCRAFT_CRASH_DIR", str(tmp_path / "crashes"))
    for name in ("ORKCRAFT_USAGE_URL", "ORKCRAFT_CRASH_URL", "ORKCRAFT_UPDATE_URL", "ORKCRAFT_USAGE_DEBUG", "DO_NOT_TRACK"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude-home"))   # never this machine's Claude Code plugins
    # No real agent CLI and no real gh, even on a machine that has them: a run a test does not fake finds no tool,
    # as on CI (tests/test_no_real_tools.py).
    monkeypatch.setenv("PATH", path_without_tools)
    from orkboard.realm import model_families
    model_families.forget()
    return path


@pytest.fixture(autouse=True)
def no_wait_to_look(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """*Give me time to look* is 2 h at first (spec 144 A.1): a spec made would wait two hours before its plan is passed. The tests of the Board's starts opt out of the wait (`do not wait`, as the
    Board started plans before the setting); the look's own tests (tests/test_look_wait*.py) and the settings' default keep the real default."""
    from orkboard import settings
    if "look_wait" not in request.module.__name__ and request.module.__name__ != "tests.test_settings":
        monkeypatch.setitem(settings.IDEAS, "look_wait", "none")


@pytest.fixture(autouse=True)
def fresh_spend_ledger():
    """The side 🪙 ledger is process-wide: every test starts from an empty one."""
    from orkboard.sources import telemetry
    telemetry.reset_charges()
    telemetry.keep_ledger(None)
    yield
    telemetry.reset_charges()
    telemetry.keep_ledger(None)


@pytest.fixture(autouse=True)
def fresh_halt_registry():
    """🛑 Stop all's registry is process-wide: every test starts with nothing running and no halt."""
    from orkboard.realm import halt
    halt.reset()
    yield
    halt.reset()


@pytest.fixture(autouse=True)
def fresh_tool_now():
    """The tool now the host last kept (realm/tool_now.py `keep`) is process-wide: every test starts with none, so `main` follows the Main tool."""
    from orkboard.realm import tool_now
    tool_now.keep(None)
    yield
    tool_now.keep(None)


@pytest.fixture(autouse=True)
def route_card_first(monkeypatch, request):
    """A routed goal waits at its route card until **Talk** is pressed, as the tests written before spec 120 have it: a goal sent goes to Talk by itself (`gui/ideas_route.py` `AUTO_TALK`)
    only in the tests that ask for it (the mark `talks_by_itself`, tests/test_gui_auto_talk.py); and Product weighs no goal it is not routed on (`goal_route.weigher_party`, spec 120 §2.4), so
    the tests that count the calls of a route's leaders keep counting them, unless a test asks (the mark `weighs`, tests/test_idea_verdict.py)."""
    if request.node.get_closest_marker("talks_by_itself") is None:
        monkeypatch.setattr("orkboard.gui.ideas_route.AUTO_TALK", False)
    if request.node.get_closest_marker("weighs") is None:
        monkeypatch.setattr("orkboard.realm.goal_route.weigher_party", lambda root, route, short=False: "")


@pytest.fixture(autouse=True)
def steps_accepted_at_once(monkeypatch, request):
    """A step that landed waits for its leader's acceptance before the next step is planned and before the goal ends (spec 152 B.1, `idea_route.due`). The tests written before run goals through
    their steps to `done` without a leader's look: there, every step reads as accepted, as if the leader's call had answered `accepted`; a test about the acceptance asks for the real one with
    the mark `accepts` (tests/test_idea_accept.py, and the route's, the runner's, the findings' that test it)."""
    if request.node.get_closest_marker("accepts") is None:
        monkeypatch.setattr("orkboard.realm.idea_route.accepted", lambda plan, n: True)


@pytest.fixture
def codex_limits(monkeypatch):
    """`codex_limits(billing=...)`: the real `fetch_limits`, with claude and agy answering a sample and
    Codex its recorded app-server reply (tests/fixtures/codex_app_server_rate_limits.jsonl) at 12:00 UTC."""
    return lambda billing="subscription": _codex_beside_claude_and_agy(monkeypatch, billing)


def _codex_beside_claude_and_agy(monkeypatch, billing: str) -> None:
    from datetime import datetime, timezone

    from orkboard import tools
    from orkboard.quota import codex_quota
    from orkboard.quota.models import QuotaStatus
    from orkboard.sources import limits

    soon = datetime.now(timezone.utc).replace(microsecond=0)
    raw = (Path(__file__).parent / "fixtures" / "codex_app_server_rate_limits.jsonl").read_text(encoding="utf-8")
    monkeypatch.setenv("ORKCRAFT_LIMITS", "1")
    monkeypatch.setattr("orkboard.quota.claude_quota.get_claude_quota",
                        lambda **k: [QuotaStatus("claude", "session", "session", 0.86, soon)])
    monkeypatch.setattr("orkboard.quota.agy_quota.get_agy_quota",
                        lambda **k: [QuotaStatus("agy", "pro", "daily", 0.4, soon)])
    monkeypatch.setattr(limits, "which", lambda name: "/usr/bin/codex" if name == "codex" else None)
    monkeypatch.setattr(tools, "codex_login", lambda path: (True, billing))
    monkeypatch.setattr(codex_quota, "_converse", lambda cmd, messages, timeout, cwd: raw)
    monkeypatch.setattr(codex_quota, "datetime", type("D", (datetime,), {"now": staticmethod(
        lambda tz=None: datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc))}))


class FakeAwake:
    """`gui/awake.py` `Awake` without a process: what a test's host holds with (spec 47 §7)."""

    def __init__(self, *a, **k) -> None:
        self.running, self.how, self.platform, self.applied = False, "", "linux", []

    def can(self) -> bool:
        return True

    def apply(self, want: bool) -> None:
        self.applied.append(want)
        self.how = "systemd-inhibit" if want and self.running else ""

    def stop(self) -> None:
        self.how = ""


@pytest.fixture(autouse=True)
def fake_awake(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test starts `caffeinate` or `systemd-inhibit`, nor reads the power: every host's `Awake` is a fake."""
    from orkboard.gui import awake
    monkeypatch.setattr(awake, "Awake", FakeAwake)


@pytest.fixture(autouse=True)
def _nothing_watches_the_tools():
    """A host that watches the AI tools' failures (core/sign_ins.py, spec 45) stops watching with its test."""
    yield
    from orkboard.realm import tool_errors
    tool_errors._WATCHERS.clear()
    tool_errors._OK_WATCHERS.clear()


@pytest.fixture(autouse=True)
def no_paid_tool_connections(monkeypatch):
    """Paid providers are always faked; keep the Board's localhost servers usable.

    Check before HTTP (including a proxy tunnel) and before DNS/socket connection,
    so a forgotten fake fails with the host's name before it can send a key.
    """
    import http.client
    import socket
    from orkboard.realm import craft_tools

    hosts = {tool.host.lower().rstrip('.') for tool in craft_tools.REGISTRY.values() if tool.kind == "api"}

    def check(host):
        if isinstance(host, bytes):
            host = host.decode("ascii", errors="replace")
        if isinstance(host, str) and host.lower().rstrip('.').split(':')[0] in hosts:
            pytest.fail(f"A test reached paid tool host {host}; inject a fake transport", pytrace=False)

    request = http.client.HTTPConnection.request
    resolve = socket.getaddrinfo
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def guarded_request(self, *args, **kwargs):
        check(self.host)
        check(getattr(self, "_tunnel_host", None))
        return request(self, *args, **kwargs)

    def guarded_resolve(host, *args, **kwargs):
        check(host)
        return resolve(host, *args, **kwargs)

    def guarded_connect(self, address):
        if isinstance(address, tuple):
            check(address[0])
        return connect(self, address)

    def guarded_connect_ex(self, address):
        if isinstance(address, tuple):
            check(address[0])
        return connect_ex(self, address)

    monkeypatch.setattr(http.client.HTTPConnection, "request", guarded_request)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_resolve)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
