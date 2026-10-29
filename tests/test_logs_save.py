"""Save logs (gui/logs_save.py, realm/diagnostics.py; the owner's notes of 19 October): an error's Save logs and the
gear's day logs go to the Downloads folder as one zip with where Orkboard runs, never an environment's value."""
from __future__ import annotations

import io
import json
import logging
import logging.handlers
import os
import re
import time
import types
import zipfile

import pytest

from orkboard import tools
from orkboard.gui import logs_save
from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.realm import diagnostics, event_log

ABOUT = {"orkboard": "x", "tools": [], "env": {}}


def _zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


def _host(packed):
    return types.SimpleNamespace(day_logs=types.SimpleNamespace(pack_period=lambda days: packed), machine=None)


def _names(data: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist()}


def test_the_days_zip_gains_where_orkboard_runs_and_the_words_on_the_screen(tmp_path):
    got = _names(logs_save.pack(_host(("a.zip", _zip({"README.md": "# The day", "2026-10-19/board/calls.jsonl": "{}\n"}))),
                                said="Claude Code is not signed in", about=ABOUT))
    assert got["README.md"] == "# The day" and "2026-10-19/board/calls.jsonl" in got
    assert json.loads(got["about.json"]) == ABOUT and got["on-screen.txt"] == "Claude Code is not signed in\n"
    empty = _names(logs_save.pack(_host(None), about=ABOUT))                  # nothing kept yet: about.json still
    assert "No model call is kept" in empty["README.md"] and "about.json" in empty and "on-screen.txt" not in empty


def test_saved_in_the_downloads_folder_and_shown_only_there(tmp_path):
    (tmp_path / "Downloads").mkdir()
    assert logs_save.folder(tmp_path) == tmp_path / "Downloads"
    assert logs_save.folder(tmp_path / "nowhere") == tmp_path / "nowhere"                # no Downloads: the home folder
    where = tmp_path / "Downloads"
    got = logs_save.save(_host(None), where=where, about=ABOUT)
    path = where / got["name"]
    assert got["path"] == str(path) and path.is_file() and got["name"].startswith("orkboard-logs-")
    started = []
    assert logs_save.show(str(path), where, start=lambda cmd, **kw: started.append(cmd)) == {"ok": True}
    assert started == [logs_save.reveal_cmd(path)]
    (tmp_path / "secret.zip").write_bytes(b"x")
    for other in (tmp_path / "secret.zip", where / "notes.txt", where / "orkboard-logs-gone.zip"):
        with pytest.raises(logs_save.LogsError, match="Only logs saved by Orkboard"):
            logs_save.show(str(other), where, start=lambda cmd, **kw: started.append(cmd))
    assert len(started) == 1


def test_the_systems_way_to_show_a_file():
    assert logs_save.reveal_cmd(logs_save.Path("/u/Downloads/a.zip"), "darwin") == ["open", "-R", "/u/Downloads/a.zip"]
    assert logs_save.reveal_cmd(logs_save.Path("/u/Downloads/a.zip"), "linux") == ["xdg-open", "/u/Downloads"]
    assert logs_save.reveal_cmd(logs_save.Path("C:/u/a.zip"), "win32")[0] == "explorer"


def test_an_environments_values_are_never_written():
    env = {"ANTHROPIC_API_KEY": "sk-ant-secret", "CLAUDE_CODE_OAUTH_TOKEN": "tok", "PATH": "/opt/homebrew/bin:/usr/bin",
           "CLAUDE_CONFIG_DIR": "/Users/me/.claude-work", "SECRET_OTHER": "x", "ORKBOARD_FROM": "app"}
    got = diagnostics.env_of(env)
    assert got == {"ANTHROPIC_API_KEY": "set", "CLAUDE_CODE_OAUTH_TOKEN": "set", "PATH": "/opt/homebrew/bin:/usr/bin",
                   "CLAUDE_CONFIG_DIR": "/Users/me/.claude-work", "ORKBOARD_FROM": "app"}
    claude = next(t for t in tools.TOOLS if t.id == "claude")
    seen = [tools.ToolStatus(claude, found=True, path="/usr/local/bin/claude", version="1.0.3", logged_in=True)]
    machine = types.SimpleNamespace(tools={"claude": types.SimpleNamespace(enabled=True, billing="subscription")})
    said = {"code": 1, "loggedIn": False, "authMethod": "none", "configDirectory": "/Users/me/.claude-work"}
    about = diagnostics.about(machine, detect=lambda: seen, env=env, auth=lambda path: said)
    text = json.dumps(about)
    assert "sk-ant-secret" not in text and "tok\"" not in text and about["launched"] == "app"
    assert about["tools"] == [{"id": "claude", "found": True, "path": "/usr/local/bin/claude", "version": "1.0.3",
                               "signed_in": True, "billing_seen": "subscription", "turned_on": True, "billing": "subscription",
                               "auth_status": said}]


def test_claude_says_its_sign_in_as_this_process_sees_it_and_names_no_person():
    import subprocess as sp
    asked = []

    def run(cmd, **kw):
        asked.append((cmd, kw["env"].get("CLAUDE_CONFIG_DIR")))
        return sp.CompletedProcess(cmd, 1, json.dumps({"loggedIn": False, "authMethod": "none", "email": "me@x.org",
                                                       "configDirectory": "/Users/me/.claude", "orgName": "Mine"}), "")
    got = tools.claude_auth("/usr/local/bin/claude", run, env={"CLAUDE_CONFIG_DIR": "/Users/me/.claude"})
    assert got == {"code": 1, "loggedIn": False, "authMethod": "none", "configDirectory": "/Users/me/.claude"}
    assert asked == [(["/usr/local/bin/claude", "auth", "status"], "/Users/me/.claude")]
    assert tools.claude_auth("/x", lambda cmd, **kw: sp.CompletedProcess(cmd, 1, "Not logged in\nRun claude", "")) == \
        {"code": 1, "said": "Not logged in"}

    def gone(cmd, **kw):
        raise OSError("no such file")
    assert tools.claude_auth("/x", gone) == {}


def test_the_commands_are_the_desktops_and_never_a_phones(fake_repo, tmp_path, monkeypatch):
    monkeypatch.setattr(logs_save, "folder", lambda home=None: tmp_path)
    monkeypatch.setattr(diagnostics, "about", lambda machine=None, **kw: ABOUT)
    host = Orkboard(fake_repo)
    got = host.command("logs.save", {"said": "it failed", "days": 1})
    assert (tmp_path / got["name"]).is_file() and _names((tmp_path / got["name"]).read_bytes())["on-screen.txt"] == "it failed\n"
    assert host.command("logs.show", {"path": "/etc/passwd"}) == {"error": "Only logs saved by Orkboard are shown"}
    assert not BoardPhone.allowed(host, "logs.save", {}) and not BoardPhone.allowed(host, "logs.show", {})


# -- spec 107 §2: the logs say the whole day -------------------------------------------------------------------------

def _crash(folder, name, text, age_days=0):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    then = time.time() - age_days * 86400
    os.utime(path, (then, then))
    return path


def test_the_crash_files_of_the_period_go_in_newest_first_and_at_most_two_megabytes(tmp_path):
    from orkboard.core import crashes
    folder = crashes.log_dir()
    _crash(folder, "crash-orkboard-20261029-100000-000001.txt", "old crash", age_days=5)
    _crash(folder, "crash-orkboard-20261029-110000-000001.txt", "first today", age_days=0.01)
    _crash(folder, "crash-orkboard-20261029-120000-000001.txt", "second today")
    _crash(folder, "session-orkboard-abc.json", "{}")                                   # a session's marker is no crash
    got = _names(logs_save.pack(_host(None), about=ABOUT))
    assert sorted(n for n in got if n.startswith("crashes/")) == ["crashes/crash-orkboard-20261029-110000-000001.txt",
                                                                  "crashes/crash-orkboard-20261029-120000-000001.txt"]
    assert [n for n, _ in logs_save.crash_files(1)] == ["crash-orkboard-20261029-120000-000001.txt", "crash-orkboard-20261029-110000-000001.txt"]
    assert len(logs_save.crash_files(7)) == 3                                             # a week takes the old one too
    big = _crash(folder, "crash-orkboard-20261029-130000-000001.txt", "x" * 3_000_000)
    capped = logs_save.crash_files(1)
    assert [n for n, _ in capped] == [big.name] and sum(len(d) for _, d in capped) == logs_save.CRASHES_MAX
    assert len(_names(logs_save.pack(_host(None), about=ABOUT))["crashes/" + big.name]) == logs_save.CRASHES_MAX


def test_without_the_mac_apps_log_the_servers_own_end_goes_in_as_app_log(tmp_path):
    from orkboard.gui import server_log
    assert "app.log" not in _names(logs_save.pack(_host(None), about=ABOUT))                # nothing logged yet
    assert server_log.install(demo=True) is None                                              # not in the demo
    where = server_log.install()
    try:
        assert where == tmp_path / "home" / ".orkcraft" / "logs" / "orkboard.log"
        logging.getLogger("orkboard.test").info("not a warning")
        logging.getLogger("orkboard.test").warning("the gate could not run")
        try:
            raise KeyError("x")
        except KeyError as e:
            logging.getLogger("orkboard.test").error("caught", exc_info=e)
        got = _names(logs_save.pack(_host(None), about=ABOUT))
        assert "the gate could not run" in got["app.log"] and "KeyError: 'x'" in got["app.log"] and "not a warning" not in got["app.log"]
        server_log.install()                                                                    # again: no second handler
        logging.getLogger("orkboard.test").warning("once")
        assert _names(logs_save.pack(_host(None), about=ABOUT))["app.log"].count("once") == 1
        mac = tmp_path / "home" / "Library" / "Logs" / "Orkboard.log"
        mac.parent.mkdir(parents=True)
        mac.write_text("the app's own\n", encoding="utf-8")
        assert _names(logs_save.pack(_host(None), about=ABOUT))["app.log"] == "the app's own\n"      # the Mac app's log wins
    finally:
        server_log.uninstall()
    assert not [h for h in logging.getLogger().handlers if isinstance(h, logging.handlers.RotatingFileHandler)]


def test_the_server_log_rotates_at_a_megabyte_and_keeps_three_files(tmp_path):
    from orkboard.gui import server_log
    server_log.install()
    try:
        for _ in range(40):
            logging.getLogger("orkboard.test").warning("w" * 100_000)
    finally:
        server_log.uninstall()
    folder = server_log.path().parent
    assert sorted(p.name for p in folder.iterdir()) == ["orkboard.log", "orkboard.log.1", "orkboard.log.2"]
    assert all(p.stat().st_size <= 1_100_000 for p in folder.iterdir())
    assert len(server_log.tail(256 * 1024)) == 256 * 1024


def test_the_page_says_its_window_and_its_last_errors_and_nothing_else(tmp_path):
    page = {"w": 1200, "h": 800, "dpr": 2, "face": "vscode", "tab": "orkmaster", "over": "result", "lens": "modules",
            "errors": [f"TypeError: e{i} @ at f (x.js:1:2)" for i in range(30)], "secret": "never", "token": "no"}
    got = json.loads(_names(logs_save.pack(_host(None), about=ABOUT, page=page))["page.json"])
    assert got == {"w": 1200, "h": 800, "dpr": 2, "face": "vscode", "tab": "orkmaster", "over": "result", "lens": "modules",
                   "errors": page["errors"][-20:]}
    odd = json.loads(_names(logs_save.pack(_host(None), about=ABOUT, page={"w": "wide", "errors": "no", "tab": 4}))["page.json"])
    assert odd == {"w": None, "h": None, "dpr": None, "face": "", "tab": "", "over": "", "lens": "", "errors": []}
    assert "page.json" not in _names(logs_save.pack(_host(None), about=ABOUT))
    assert "page.json" not in _names(logs_save.pack(_host(None), about=ABOUT, page="x"))


def test_the_project_says_its_gate_its_installs_and_its_build(fake_repo):
    (fake_repo / "orkcraft.toml").write_text('[gate]\nrun = "npm test --prefix app"\n', encoding="utf-8")
    for name, installed in (("app", True), ("server", False)):
        (fake_repo / name).mkdir()
        (fake_repo / name / "package.json").write_text('{"scripts": {"test": "vitest run"}}', encoding="utf-8")
        (fake_repo / name / "package-lock.json").write_text("{}", encoding="utf-8")
        if installed:
            (fake_repo / name / "node_modules").mkdir()
    got = diagnostics.project_of(fake_repo)
    assert got["gate"]["run"] == "npm test --prefix app" and got["gate"]["from"] == "orkcraft.toml" and "error" not in got["gate"]
    assert got["packages"] == [{"dir": "app", "node_modules": True, "lock": "package-lock.json"},
                               {"dir": "server", "node_modules": False, "lock": "package-lock.json"}]
    assert got["venv"] is False and "board" not in got
    (fake_repo / ".venv").mkdir()
    (fake_repo / "orkcraft.toml").unlink()
    derived = diagnostics.project_of(fake_repo, lambda root: {"target": "balance"})
    assert derived["gate"]["from"] == "derived" and derived["gate"]["run"] == "npm test --prefix app && npm test --prefix server"
    assert derived["venv"] is True and derived["board"] == {"target": "balance"}
    assert diagnostics.project_of(fake_repo / "src")["gate"]["from"] == "none"
    about = diagnostics.about(types.SimpleNamespace(tools={}), detect=lambda: [], env={}, root=fake_repo)
    assert about["project"]["gate"]["from"] == "derived" and about["project"]["board"]["target"] == "balance"
    assert "project" not in diagnostics.about(None, detect=lambda: [], env={}) and about["build"]["version"] == about["orkboard"]
    assert re.fullmatch(r"[0-9a-f]{12}", diagnostics.build_of(fake_repo / "orkboard")["git"])      # a source checkout: its git head
    assert diagnostics.build_of(fake_repo / "src" / "orkboard")["git"] == ""                        # an install: only the version


def test_the_saved_logs_carry_the_page_the_project_and_the_build(fake_repo, tmp_path, monkeypatch):
    monkeypatch.setattr(logs_save, "folder", lambda home=None: tmp_path)
    host = Orkboard(fake_repo)
    got = host.command("logs.save", {"page": {"w": 900, "tab": "orkmaster", "errors": ["Error: x"]}})
    files = _names((tmp_path / got["name"]).read_bytes())
    about = json.loads(files["about.json"])
    assert json.loads(files["page.json"])["errors"] == ["Error: x"] and about["project"]["gate"]["from"] in ("derived", "none", "orkcraft.toml")
    assert about["build"]["version"] == about["orkboard"] and "board" in about["project"]
    assert "page.json" in files["README.md"] and "command_refused" in files["README.md"]      # the zip says what each new file and event is


def _event(root, name):
    return [e for e in event_log.read(root) if e["event"] == name]


def test_a_refused_command_and_a_broken_one_are_events_but_not_the_logs_own(fake_repo):
    from orkboard.core import crashes
    from orkboard.gui.board_host import CommandError
    from orkboard.gui.server import Server
    host = Orkboard(fake_repo)
    server = Server(host)

    def refuse(args):
        raise CommandError("no logs")
    host.commands["logs.refuse"] = host.commands["crash.refuse"] = refuse
    host.commands["boom"] = lambda a: 1 / 0

    def call(name, **args):
        return server._handle(json.dumps({"t": "cmd", "id": 1, "name": name, "args": args}))
    assert call("nonesuch", secret="word")["ok"] is False
    assert call("ideas.add", text="")["ok"] is False
    assert call("boom")["error"] == "ZeroDivisionError: division by zero"
    for silent in ("logs.refuse", "crash.refuse"):
        assert call(silent)["ok"] is False
    assert call("watch", ids=["x"])["ok"] is True
    refused, empty, broken = _event(fake_repo, "command_refused")
    assert (refused["command"], refused["error"], refused["device"], refused["kind"]) == ("nonesuch", "Unknown command: nonesuch", "desktop", "refused")
    assert empty["command"] == "ideas.add" and empty["kind"] == "refused"
    assert (broken["command"], broken["error"], broken["kind"]) == ("boom", "ZeroDivisionError: division by zero", "broken")
    assert "word" not in json.dumps(event_log.read(fake_repo))                         # a command's arguments are never written
    assert "ZeroDivisionError" in next(crashes.log_dir().glob("crash-orkboard-*.txt")).read_text()      # and its traceback is kept


def test_a_phones_refusals_say_phone(fake_repo):
    from orkboard.gui.server import Server
    host = Orkboard(fake_repo)
    listener = Server(host).phones
    listener.pairing.known = lambda device: True
    listener.pairing.seen = lambda device: None
    phone = types.SimpleNamespace(id="p1", name="Phone", bucket=types.SimpleNamespace(take=lambda: True))
    host.commands["ideas.boom"] = lambda a: 1 / 0

    def call(name):
        return listener.handle(phone, json.dumps({"t": "cmd", "id": 1, "name": name, "args": {}}))
    assert call("tools.sign_in")["error"] == "Not from a phone: tools.sign_in"
    assert call("ideas.nonesuch")["ok"] is False and call("ideas.boom")["ok"] is False and call("logs.save")["ok"] is False
    assert [(r["command"], r["device"], r["kind"]) for r in _event(fake_repo, "command_refused")] == [
        ("tools.sign_in", "phone", "refused"), ("ideas.nonesuch", "phone", "refused"), ("ideas.boom", "phone", "broken")]


def test_a_red_toast_is_an_event_once_whoever_raised_it_and_a_calm_one_is_not(fake_repo):
    host = Orkboard(fake_repo)
    host.projects.current().toast("The gate could not run", title="Review", severity="error")      # a project's own
    host.toast("Town clock broke", title="Town clock", severity="error")                              # the host's (the server's clock)
    host.projects.current().toast("Saved", title="Board", severity="information")
    host.toast("Careful", severity="warning")
    assert [(e["title"], e["text"]) for e in _event(fake_repo, "error_shown")] == [
        ("Review", "The gate could not run"), ("Town clock", "Town clock broke")]
    Orkboard(fake_repo, demo=True).toast("Nothing is written in the demo", severity="error")
    assert len(_event(fake_repo, "error_shown")) == 2
